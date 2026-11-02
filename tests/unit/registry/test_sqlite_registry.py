from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

import pymupdf
import pytest

from financial_filing_data_foundation.identity import (
    FilingIdentity,
    FilingSlotKey,
    SourceMetadata,
)
from financial_filing_data_foundation.registry import (
    BindingStatus,
    CompatibilityStatus,
    LocalDocumentStatus,
    ParsedDataRecord,
    RegistrySchemaUnsupported,
    SQLiteRegistry,
    ValidationStatus,
)


def _make_pdf(path: Path, text: str) -> None:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _slot(year: int = 2024) -> FilingSlotKey:
    return FilingSlotKey("CN", "CN:600519", "ANNUAL_REPORT", year, "FY")


def test_schema_initializes_to_version_one(tmp_path: Path) -> None:
    registry = SQLiteRegistry(tmp_path / "registry.sqlite")
    assert registry.schema_version() == 1


def test_newer_registry_schema_is_rejected(tmp_path: Path) -> None:
    db = tmp_path / "future.sqlite"
    conn = sqlite3.connect(db)
    conn.execute("PRAGMA user_version = 2")
    conn.close()

    with pytest.raises(RegistrySchemaUnsupported) as exc_info:
        SQLiteRegistry(db)

    assert exc_info.value.reason_code == "REGISTRY_SCHEMA_UNSUPPORTED"


def test_version_one_missing_required_table_is_rejected(tmp_path: Path) -> None:
    db = tmp_path / "incomplete-table.sqlite"
    SQLiteRegistry(db)

    conn = sqlite3.connect(db)
    conn.execute("DROP TABLE document_sources")
    conn.commit()
    conn.close()

    with pytest.raises(RegistrySchemaUnsupported) as exc_info:
        SQLiteRegistry(db)

    assert exc_info.value.reason_code == "REGISTRY_SCHEMA_UNSUPPORTED"
    assert "document_sources" in str(exc_info.value)


def test_version_one_missing_required_column_is_rejected(tmp_path: Path) -> None:
    db = tmp_path / "incomplete-column.sqlite"
    SQLiteRegistry(db)

    conn = sqlite3.connect(db)
    conn.execute("ALTER TABLE document_sources RENAME TO document_sources_old")
    conn.execute(
        """
        CREATE TABLE document_sources (
            document_sha256 TEXT NOT NULL,
            provider TEXT NOT NULL,
            source_id TEXT NOT NULL,
            source_url TEXT NOT NULL,
            filing_date TEXT,
            report_date TEXT,
            provider_company_id TEXT,
            acquired_at TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()

    with pytest.raises(RegistrySchemaUnsupported) as exc_info:
        SQLiteRegistry(db)

    assert exc_info.value.reason_code == "REGISTRY_SCHEMA_UNSUPPORTED"
    assert "source_title" in str(exc_info.value)


def test_register_same_file_is_idempotent(tmp_path: Path) -> None:
    pdf = tmp_path / "a.pdf"
    _make_pdf(pdf, "same")
    registry = SQLiteRegistry(tmp_path / "registry.sqlite")
    identity = FilingIdentity(_slot(), amended=False)

    first = registry.register_document(pdf, expected_identity=identity)
    second = registry.register_document(pdf, expected_identity=identity)

    assert first.document_sha256 == second.document_sha256
    assert registry.count_documents() == 1
    assert registry.count_locations() == 1
    assert registry.count_bindings() == 1
    assert first.page_count == 1


def test_same_sha_multiple_paths_share_content_record(tmp_path: Path) -> None:
    first_path = tmp_path / "a.pdf"
    second_path = tmp_path / "b.pdf"
    _make_pdf(first_path, "same bytes")
    second_path.write_bytes(first_path.read_bytes())

    registry = SQLiteRegistry(tmp_path / "registry.sqlite")
    identity = FilingIdentity(_slot())
    registry.register_document(first_path, expected_identity=identity)
    registry.register_document(second_path, expected_identity=identity)

    state = registry.resolve_local_document(_slot())

    assert registry.count_documents() == 1
    assert registry.count_locations() == 2
    assert registry.count_bindings() == 1
    assert state.status == LocalDocumentStatus.RESOLVED
    assert state.location_count == 2
    assert state.canonical_path == min(first_path.resolve(), second_path.resolve())


def test_changed_path_content_updates_location_without_deleting_history(
    tmp_path: Path,
) -> None:
    pdf = tmp_path / "changing.pdf"
    registry = SQLiteRegistry(tmp_path / "registry.sqlite")
    identity = FilingIdentity(_slot())

    _make_pdf(pdf, "version one")
    first = registry.register_document(pdf, expected_identity=identity)

    _make_pdf(tmp_path / "replacement.pdf", "version two")
    pdf.write_bytes((tmp_path / "replacement.pdf").read_bytes())
    second = registry.register_document(pdf, expected_identity=identity)

    assert first.document_sha256 != second.document_sha256
    assert registry.count_documents() == 2
    assert registry.count_locations() == 1
    assert registry.location_sha(pdf) == second.document_sha256


def test_unbound_document_is_not_local_candidate(tmp_path: Path) -> None:
    pdf = tmp_path / "unbound.pdf"
    _make_pdf(pdf, "unbound")
    registry = SQLiteRegistry(tmp_path / "registry.sqlite")

    registry.register_document(pdf)

    assert registry.resolve_local_document(_slot()).status == LocalDocumentStatus.NONE



def test_source_metadata_without_identity_is_persisted(tmp_path: Path) -> None:
    pdf = tmp_path / "source-only.pdf"
    _make_pdf(pdf, "source-only")
    registry = SQLiteRegistry(tmp_path / "registry.sqlite")
    source = SourceMetadata(
        provider="cninfo",
        source_id="source-1",
        source_url="https://example.com/source-only.pdf",
        source_title="source only annual report",
        filing_date="2025-03-01",
        report_date="2024-12-31",
        provider_company_id="org-1",
        acquired_at="2026-11-02T00:00:00+00:00",
    )

    registered = registry.register_document(pdf, source=source)

    assert registered.identity is None
    assert registered.binding_status is None
    assert registry.count_bindings() == 0
    assert registry.count_sources() == 1
    assert registry.list_document_sources(registered.document_sha256) == (source,)
    assert registry.resolve_local_document(_slot()).status == LocalDocumentStatus.NONE


def test_repeated_same_source_provenance_is_idempotent(tmp_path: Path) -> None:
    pdf = tmp_path / "source-repeat.pdf"
    _make_pdf(pdf, "source-repeat")
    registry = SQLiteRegistry(tmp_path / "registry.sqlite")
    source = SourceMetadata(
        provider="cninfo",
        source_id="source-1",
        source_url="https://example.com/source-repeat.pdf",
        source_title="source repeat annual report",
    )

    first = registry.register_document(pdf, source=source)
    second = registry.register_document(pdf, source=source)

    assert first.document_sha256 == second.document_sha256
    assert registry.count_sources() == 1
    assert registry.list_document_sources(first.document_sha256) == (source,)


def test_source_metadata_marks_binding_source_confirmed(tmp_path: Path) -> None:
    pdf = tmp_path / "source.pdf"
    _make_pdf(pdf, "source")
    registry = SQLiteRegistry(tmp_path / "registry.sqlite")
    source = SourceMetadata(
        provider="cninfo",
        source_id="abc",
        source_url="https://example.invalid/a.pdf",
        source_title="annual report",
        acquired_at="2026-11-02T00:00:00+00:00",
    )

    registered = registry.register_document(
        pdf,
        source=source,
        expected_identity=FilingIdentity(_slot()),
    )

    assert registered.binding_status == BindingStatus.SOURCE_CONFIRMED


def test_same_sha_bound_to_different_slots_becomes_conflict(tmp_path: Path) -> None:
    pdf = tmp_path / "conflict.pdf"
    _make_pdf(pdf, "conflict")
    registry = SQLiteRegistry(tmp_path / "registry.sqlite")

    registry.register_document(pdf, expected_identity=FilingIdentity(_slot(2024)))
    registry.register_document(pdf, expected_identity=FilingIdentity(_slot(2023)))

    assert registry.resolve_local_document(_slot(2024)).status == LocalDocumentStatus.CONFLICT
    assert registry.resolve_local_document(_slot(2023)).status == LocalDocumentStatus.CONFLICT


def test_changed_bound_path_without_reregister_is_drifted(tmp_path: Path) -> None:
    pdf = tmp_path / "drift.pdf"
    replacement = tmp_path / "replacement.pdf"
    _make_pdf(pdf, "original")
    registry = SQLiteRegistry(tmp_path / "registry.sqlite")
    registry.register_document(pdf, expected_identity=FilingIdentity(_slot()))

    _make_pdf(replacement, "changed in place")
    pdf.write_bytes(replacement.read_bytes())

    state = registry.resolve_local_document(_slot())

    assert state.status == LocalDocumentStatus.DRIFTED
    assert state.location_count == 0
    assert state.drifted_location_count == 1


def test_one_drifted_duplicate_does_not_hide_verified_same_sha_copy(
    tmp_path: Path,
) -> None:
    first = tmp_path / "a.pdf"
    second = tmp_path / "b.pdf"
    replacement = tmp_path / "replacement.pdf"
    _make_pdf(first, "same source")
    second.write_bytes(first.read_bytes())
    registry = SQLiteRegistry(tmp_path / "registry.sqlite")
    identity = FilingIdentity(_slot())
    registered = registry.register_document(first, expected_identity=identity)
    registry.register_document(second, expected_identity=identity)

    _make_pdf(replacement, "different source")
    first.write_bytes(replacement.read_bytes())

    state = registry.resolve_local_document(_slot())

    assert state.status == LocalDocumentStatus.RESOLVED
    assert state.document_sha256 == registered.document_sha256
    assert state.canonical_path == second.resolve()
    assert state.location_count == 1
    assert state.drifted_location_count == 1


def test_missing_location_is_not_treated_as_live_local_candidate(tmp_path: Path) -> None:
    pdf = tmp_path / "gone.pdf"
    _make_pdf(pdf, "gone")
    registry = SQLiteRegistry(tmp_path / "registry.sqlite")
    registry.register_document(pdf, expected_identity=FilingIdentity(_slot()))
    pdf.unlink()

    state = registry.resolve_local_document(_slot())

    assert state.status == LocalDocumentStatus.NONE


def test_register_parsed_data_is_idempotent_for_identical_record(tmp_path: Path) -> None:
    registry = SQLiteRegistry(tmp_path / "registry.sqlite")
    record = ParsedDataRecord(
        parse_run_id="run-1",
        slot=_slot(),
        document_sha256="a" * 64,
        parser_version="1.0",
        schema_version="1.0",
        validation_status=ValidationStatus.PASS,
        blocking_issue_count=0,
        compatibility_status=CompatibilityStatus.COMPATIBLE,
    )

    registry.register_parsed_data(record)
    registry.register_parsed_data(record)

    assert registry.list_parsed_data(_slot()) == (record,)


def test_parse_run_id_cannot_be_reused_for_different_content(tmp_path: Path) -> None:
    registry = SQLiteRegistry(tmp_path / "registry.sqlite")
    first = ParsedDataRecord(
        parse_run_id="run-1",
        slot=_slot(),
        document_sha256="a" * 64,
        parser_version="1.0",
        schema_version="1.0",
        validation_status=ValidationStatus.PASS,
        blocking_issue_count=0,
        compatibility_status=CompatibilityStatus.COMPATIBLE,
    )
    second = ParsedDataRecord(
        parse_run_id="run-1",
        slot=_slot(),
        document_sha256="b" * 64,
        parser_version="1.0",
        schema_version="1.0",
        validation_status=ValidationStatus.PASS,
        blocking_issue_count=0,
        compatibility_status=CompatibilityStatus.COMPATIBLE,
    )

    registry.register_parsed_data(first)
    with pytest.raises(ValueError, match="different content"):
        registry.register_parsed_data(second)


def test_registration_does_not_modify_source_pdf(tmp_path: Path) -> None:
    pdf = tmp_path / "immutable.pdf"
    _make_pdf(pdf, "immutable")
    before_bytes = pdf.read_bytes()
    before_stat = pdf.stat()

    registry = SQLiteRegistry(tmp_path / "registry.sqlite")
    registered = registry.register_document(
        pdf, expected_identity=FilingIdentity(_slot())
    )

    after_stat = pdf.stat()
    assert pdf.read_bytes() == before_bytes
    assert after_stat.st_size == before_stat.st_size
    assert after_stat.st_mtime_ns == before_stat.st_mtime_ns
    assert registered.document_sha256 == _sha(pdf)
