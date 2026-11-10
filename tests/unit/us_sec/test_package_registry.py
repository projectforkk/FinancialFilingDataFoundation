from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from financial_filing_data_foundation.registry import RegistrySchemaUnsupported, SQLiteRegistry
from financial_filing_data_foundation.us_sec.errors import P11Reason, SecError
from financial_filing_data_foundation.us_sec.package import (
    SecMemberRole,
    SecPackageMember,
    SecPackageStore,
    build_package,
)
from financial_filing_data_foundation.us_sec.registry import (
    SEC_REGISTRY_SCHEMA_VERSION,
    register_sec_package,
    register_sec_slot,
)
from financial_filing_data_foundation.us_sec.planner import SecPlanAction, plan_sec_slot


def _package() -> object:
    return build_package(
        cik="0000320193",
        accession="0000320193-25-000001",
        form="10-Q",
        fiscal_year=2025,
        period="Q2",
        members=(
            SecPackageMember(
                relative_name="example.htm",
                role=SecMemberRole.PRIMARY_DOCUMENT,
                content_type="text/html",
                source_url="https://www.sec.gov/Archives/edgar/data/1/example.htm",
                body=b"<html><body>filing</body></html>",
            ),
            SecPackageMember(
                relative_name="example.xsd",
                role=SecMemberRole.XBRL_SCHEMA,
                content_type="application/xml",
                source_url="https://www.sec.gov/Archives/edgar/data/1/example.xsd",
                body=b"<schema/>",
            ),
        ),
    )


def test_package_hash_is_canonical_and_store_is_immutable(tmp_path: Path) -> None:
    package = _package()
    expected = hashlib.sha256(
        json.dumps(
            [
                {
                    "role": "PRIMARY_DOCUMENT",
                    "relative_name": "example.htm",
                    "member_sha256": hashlib.sha256(b"<html><body>filing</body></html>").hexdigest(),
                    "byte_length": 32,
                },
                {
                    "role": "XBRL_SCHEMA",
                    "relative_name": "example.xsd",
                    "member_sha256": hashlib.sha256(b"<schema/>").hexdigest(),
                    "byte_length": 9,
                },
            ],
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    assert package.package_sha256 == expected

    store = SecPackageStore(tmp_path / "raw-store")
    first = store.put(package)
    second = store.put(package)
    assert first == second
    assert (first / "manifest.json").is_file()
    assert (first / "members" / "example.htm").read_bytes().startswith(b"<html")

    with pytest.raises(Exception) as exc_info:
        (first / "members" / "example.htm").write_bytes(b"changed")
        store.load(package.package_sha256)
    assert "hash" in str(exc_info.value).lower() or "immutable" in str(exc_info.value).lower()

    drifted = build_package(
        cik="0000320193",
        accession="0000320193-25-000001",
        form="10-Q",
        fiscal_year=2025,
        period="Q2",
        members=(
            SecPackageMember(
                relative_name="example.htm",
                role=SecMemberRole.PRIMARY_DOCUMENT,
                content_type="text/html",
                source_url="https://www.sec.gov/Archives/edgar/data/1/example.htm",
                body=b"<html><body>changed</body></html>",
            ),
        ),
    )
    with pytest.raises(Exception) as drift:
        SecPackageStore(tmp_path / "raw-store-drift").put(package)
        SecPackageStore(tmp_path / "raw-store-drift").put(drifted)
    assert "drift" in str(drift.value).lower()


def test_registry_adds_sec_tables_without_rewriting_legacy_rows(tmp_path: Path) -> None:
    db = tmp_path / "registry.sqlite"
    registry = SQLiteRegistry(db)
    package = _package()
    package_dir = SecPackageStore(tmp_path / "raw-store").put(package)
    register_sec_package(registry, package)
    register_sec_slot(
        registry,
        package,
        fiscal_year=2025,
        period="Q2",
        artifact_path="workspace/ingest/us/sec/p7/demo",
    )

    assert SEC_REGISTRY_SCHEMA_VERSION == 3
    with sqlite3.connect(db) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        assert {"source_packages", "package_members", "sec_filing_bindings", "sec_parsed_data"} <= tables
        row = conn.execute(
            "SELECT package_sha256, provider FROM source_packages"
        ).fetchone()
    assert row == (package.package_sha256, "sec")
    assert package_dir.exists()


def _make_v2_registry(db: Path, tmp_path: Path) -> tuple[object, dict[str, tuple[object, ...]]]:
    registry = SQLiteRegistry(db)
    package = _package()
    registry.register_sec_package(package)
    registry.register_sec_binding(
        package,
        company_id="US:CIK0000320193",
        fiscal_year=2025,
        period="Q2",
        artifact_path="old-v3-artifact",
    )
    registry.register_sec_parsed_data(
        parse_run_id="old-run",
        package_sha256=package.package_sha256,
        company_id="US:CIK0000320193",
        fiscal_year=2025,
        period="Q2",
        parser_version="VIRTUAL_HTML_V3",
        schema_version="p11-sec-artifacts-v1",
        validation_status="PASS",
        blocking_issue_count=0,
        compatibility_status="COMPATIBLE",
        artifact_path="old-v3-artifact",
    )
    with sqlite3.connect(db) as conn:
        conn.execute("ALTER TABLE sec_parsed_data DROP COLUMN compatibility_status")
        conn.commit()
        snapshots = {
            "source_packages": tuple(conn.execute("SELECT * FROM source_packages").fetchone()),
            "package_members": tuple(conn.execute("SELECT * FROM package_members ORDER BY relative_name").fetchone()),
            "sec_filing_bindings": tuple(conn.execute("SELECT * FROM sec_filing_bindings").fetchone()),
            "sec_parsed_data": tuple(conn.execute("SELECT * FROM sec_parsed_data").fetchone()),
        }
    return package, snapshots


def test_sec_registry_migrates_v2_to_v3_without_rewriting_legacy_rows(tmp_path: Path) -> None:
    db = tmp_path / "v2.sqlite"
    _package_obj, before = _make_v2_registry(db, tmp_path)

    registry = SQLiteRegistry(db)

    assert registry.schema_version() == 1
    assert registry.sec_schema_version() == 3
    with sqlite3.connect(db) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 1
        metadata = conn.execute(
            "SELECT value FROM sec_schema_metadata WHERE key = 'schema_version'"
        ).fetchone()
        assert metadata == ("3",)
        columns = {
            row[1] for row in conn.execute("PRAGMA table_info('sec_parsed_data')")
        }
        assert "compatibility_status" in columns
        assert conn.execute(
            "SELECT compatibility_status FROM sec_parsed_data WHERE parse_run_id = 'old-run'"
        ).fetchone() == ("INCOMPATIBLE",)
        for table, expected in before.items():
            columns_sql = "*"
            if table == "sec_parsed_data":
                columns_sql = "parse_run_id, package_sha256, company_id, fiscal_year, raw_fiscal_period, parser_version, schema_version, validation_status, blocking_issue_count, artifact_path, created_at"
            actual = tuple(conn.execute(f"SELECT {columns_sql} FROM {table}").fetchone())
            assert actual == expected


def test_sec_registry_v3_reopen_is_idempotent(tmp_path: Path) -> None:
    db = tmp_path / "v2-reopen.sqlite"
    _make_v2_registry(db, tmp_path)
    SQLiteRegistry(db)
    with sqlite3.connect(db) as conn:
        before = {
            "metadata": tuple(conn.execute("SELECT key, value FROM sec_schema_metadata ORDER BY key")),
            "packages": tuple(conn.execute("SELECT * FROM source_packages")),
            "members": tuple(conn.execute("SELECT * FROM package_members ORDER BY relative_name")),
            "bindings": tuple(conn.execute("SELECT * FROM sec_filing_bindings")),
            "parsed": tuple(conn.execute("SELECT * FROM sec_parsed_data")),
        }

    reopened = SQLiteRegistry(db)

    assert reopened.sec_schema_version() == 3
    with sqlite3.connect(db) as conn:
        after = {
            "metadata": tuple(conn.execute("SELECT key, value FROM sec_schema_metadata ORDER BY key")),
            "packages": tuple(conn.execute("SELECT * FROM source_packages")),
            "members": tuple(conn.execute("SELECT * FROM package_members ORDER BY relative_name")),
            "bindings": tuple(conn.execute("SELECT * FROM sec_filing_bindings")),
            "parsed": tuple(conn.execute("SELECT * FROM sec_parsed_data")),
        }
    assert after == before


def test_fresh_registry_uses_legacy_v1_and_sec_extension_v3(tmp_path: Path) -> None:
    db = tmp_path / "fresh.sqlite"
    registry = SQLiteRegistry(db)

    assert registry.schema_version() == 1
    assert registry.sec_schema_version() == 3
    with sqlite3.connect(db) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 1
        assert conn.execute(
            "SELECT value FROM sec_schema_metadata WHERE key = 'schema_version'"
        ).fetchone() == ("3",)


def test_unknown_sec_extension_version_fails_closed(tmp_path: Path) -> None:
    db = tmp_path / "future-sec.sqlite"
    SQLiteRegistry(db)
    with sqlite3.connect(db) as conn:
        conn.execute(
            "UPDATE sec_schema_metadata SET value = '99' WHERE key = 'schema_version'"
        )
        conn.commit()

    with pytest.raises(RegistrySchemaUnsupported) as exc_info:
        SQLiteRegistry(db)

    assert exc_info.value.reason_code == "REGISTRY_SCHEMA_UNSUPPORTED"
    assert "SEC" in str(exc_info.value)


def test_sec_parsed_data_none_compatibility_defaults_to_incompatible(tmp_path: Path) -> None:
    db = tmp_path / "none-compat.sqlite"
    registry = SQLiteRegistry(db)
    package = _package()
    registry.register_sec_package(package)
    registry.register_sec_parsed_data(
        parse_run_id="none-compat",
        package_sha256=package.package_sha256,
        company_id="US:CIK0000320193",
        fiscal_year=2025,
        period="Q2",
        parser_version="VIRTUAL_HTML_V4",
        schema_version="p11-sec-artifacts-v1",
        validation_status="PASS",
        blocking_issue_count=0,
        compatibility_status=None,
        artifact_path=None,
    )

    row = registry.list_sec_parsed_data(
        company_id="US:CIK0000320193", fiscal_year=2025, period="Q2"
    )[0]
    assert row["compatibility_status"] == "INCOMPATIBLE"


def test_incremental_planner_is_reuse_first_and_conflict_safe() -> None:
    assert plan_sec_slot(parsed_available=True, package_available=True).action is SecPlanAction.REUSE_DATA
    assert plan_sec_slot(parsed_available=False, package_available=True).action is SecPlanAction.PARSE_LOCAL
    assert plan_sec_slot(parsed_available=False, package_available=False).action is SecPlanAction.DISCOVER_AND_ACQUIRE
    conflict = plan_sec_slot(parsed_available=True, package_available=True, amendment_conflict=True)
    assert conflict.action is SecPlanAction.REVIEW_REQUIRED


@pytest.mark.parametrize("name", ["C:/evil.txt", "../evil.txt", "x\\evil.txt", "%2e%2e/evil.txt", "https://evil.example/x"])
def test_package_member_path_is_canonical_and_windows_safe(name: str) -> None:
    with pytest.raises(SecError) as exc_info:
        SecMemberRole.OTHER  # keep enum import exercised for the negative fixture
        SecPackageMember(
            relative_name=name,
            role=SecMemberRole.OTHER,
            content_type="text/plain",
            source_url="https://www.sec.gov/Archives/edgar/data/1/member.txt",
            body=b"x",
        )
    assert exc_info.value.reason_code in {P11Reason.P11_PACKAGE_INVALID.value, P11Reason.P11_ARCHIVE_HOST_REJECTED.value}


def test_package_store_finds_local_slot_without_network(tmp_path: Path) -> None:
    package = _package()
    store = SecPackageStore(tmp_path / "raw-store")
    store.put(package)
    found = store.find_by_slot(cik="320193", fiscal_year=2025, period="Q2")
    assert found is not None
    assert found.package_sha256 == package.package_sha256

