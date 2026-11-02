from __future__ import annotations

import inspect
from pathlib import Path

import pymupdf

from financial_filing_data_foundation.identity import (
    CompanyRef,
    FilingIdentity,
    FilingPolicy,
    FilingRequirement,
    FilingSlotKey,
)
from financial_filing_data_foundation.planner import (
    IncrementalPlanner,
    PlannerAction,
    PlannerReusePolicy,
    ReasonCode,
)
from financial_filing_data_foundation.registry import (
    CompatibilityStatus,
    ParsedDataRecord,
    SQLiteRegistry,
    ValidationStatus,
)


def _company() -> CompanyRef:
    return CompanyRef("CN", "CN:600519", "600519")


def _slot(year: int = 2024) -> FilingSlotKey:
    return FilingSlotKey("CN", "CN:600519", "ANNUAL_REPORT", year, "FY")


def _policy() -> FilingPolicy:
    return FilingPolicy((FilingRequirement("ANNUAL_REPORT", "FY"),))


def _reuse_policy(
    schemas: frozenset[str] = frozenset({"1.0"}),
    invalidated: frozenset[str] = frozenset(),
) -> PlannerReusePolicy:
    return PlannerReusePolicy(
        accepted_schema_versions=schemas,
        invalidated_parser_versions=invalidated,
    )


def _record(
    *,
    parse_run_id: str = "run-1",
    document_sha256: str = "a" * 64,
    parser_version: str = "1.0",
    schema_version: str = "1.0",
    validation_status: ValidationStatus = ValidationStatus.PASS,
    blocking_issue_count: int = 0,
    compatibility_status: CompatibilityStatus = CompatibilityStatus.COMPATIBLE,
) -> ParsedDataRecord:
    return ParsedDataRecord(
        parse_run_id=parse_run_id,
        slot=_slot(),
        document_sha256=document_sha256,
        parser_version=parser_version,
        schema_version=schema_version,
        validation_status=validation_status,
        blocking_issue_count=blocking_issue_count,
        compatibility_status=compatibility_status,
    )


def _make_pdf(path: Path, text: str) -> None:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()


def _planner(registry: SQLiteRegistry, reuse_policy: PlannerReusePolicy | None = None) -> IncrementalPlanner:
    return IncrementalPlanner(registry, reuse_policy or _reuse_policy())


def _only_item(planner: IncrementalPlanner):
    plan = planner.build_plan(_company(), 2024, 2024, _policy())
    assert len(plan.items) == 1
    return plan.items[0]


def test_reusable_parsed_data_reuses_without_local_file(tmp_path: Path) -> None:
    registry = SQLiteRegistry(tmp_path / "registry.sqlite")
    registry.register_parsed_data(_record())

    item = _only_item(_planner(registry))

    assert item.action == PlannerAction.REUSE_DATA
    assert item.reason_code == ReasonCode.VALIDATED_COMPATIBLE_PARSED_DATA
    assert item.document_sha256 == "a" * 64
    assert item.parse_run_id == "run-1"
    assert item.local_path is None


def test_non_pass_parsed_data_is_not_reused(tmp_path: Path) -> None:
    registry = SQLiteRegistry(tmp_path / "registry.sqlite")
    registry.register_parsed_data(
        _record(validation_status=ValidationStatus.REVIEW_REQUIRED)
    )

    item = _only_item(_planner(registry))

    assert item.action == PlannerAction.DOWNLOAD_AND_PARSE
    assert ReasonCode.PARSED_VALIDATION_NOT_PASS in item.blocking_reasons


def test_blocking_issues_prevent_reuse(tmp_path: Path) -> None:
    registry = SQLiteRegistry(tmp_path / "registry.sqlite")
    registry.register_parsed_data(_record(blocking_issue_count=1))

    item = _only_item(_planner(registry))

    assert item.action == PlannerAction.DOWNLOAD_AND_PARSE
    assert ReasonCode.PARSED_BLOCKING_ISSUES in item.blocking_reasons


def test_incompatible_parsed_data_is_not_reused(tmp_path: Path) -> None:
    registry = SQLiteRegistry(tmp_path / "registry.sqlite")
    registry.register_parsed_data(
        _record(compatibility_status=CompatibilityStatus.INCOMPATIBLE)
    )

    item = _only_item(_planner(registry))

    assert item.action == PlannerAction.DOWNLOAD_AND_PARSE
    assert ReasonCode.PARSED_SCHEMA_INCOMPATIBLE in item.blocking_reasons


def test_unknown_compatibility_is_not_reused(tmp_path: Path) -> None:
    registry = SQLiteRegistry(tmp_path / "registry.sqlite")
    registry.register_parsed_data(
        _record(compatibility_status=CompatibilityStatus.UNKNOWN)
    )

    item = _only_item(_planner(registry))

    assert item.action == PlannerAction.DOWNLOAD_AND_PARSE
    assert ReasonCode.PARSED_COMPATIBILITY_UNKNOWN in item.blocking_reasons


def test_empty_accepted_schema_set_means_no_reuse(tmp_path: Path) -> None:
    registry = SQLiteRegistry(tmp_path / "registry.sqlite")
    registry.register_parsed_data(_record())

    item = _only_item(_planner(registry, _reuse_policy(frozenset())))

    assert item.action == PlannerAction.DOWNLOAD_AND_PARSE
    assert ReasonCode.PARSED_SCHEMA_INCOMPATIBLE in item.blocking_reasons


def test_parser_version_change_alone_does_not_invalidate(tmp_path: Path) -> None:
    registry = SQLiteRegistry(tmp_path / "registry.sqlite")
    registry.register_parsed_data(_record(parser_version="9.9"))

    item = _only_item(_planner(registry))

    assert item.action == PlannerAction.REUSE_DATA


def test_explicit_invalidated_parser_version_prevents_reuse(tmp_path: Path) -> None:
    registry = SQLiteRegistry(tmp_path / "registry.sqlite")
    registry.register_parsed_data(_record(parser_version="bad-parser"))

    item = _only_item(
        _planner(registry, _reuse_policy(invalidated=frozenset({"bad-parser"})))
    )

    assert item.action == PlannerAction.DOWNLOAD_AND_PARSE
    assert ReasonCode.PARSER_DEFECT_INVALIDATED in item.blocking_reasons


def test_one_local_raw_without_reusable_data_parses_local(tmp_path: Path) -> None:
    registry = SQLiteRegistry(tmp_path / "registry.sqlite")
    pdf = tmp_path / "local.pdf"
    _make_pdf(pdf, "local")
    registered = registry.register_document(
        pdf, expected_identity=FilingIdentity(_slot())
    )

    item = _only_item(_planner(registry))

    assert item.action == PlannerAction.PARSE_LOCAL
    assert item.reason_code == ReasonCode.LOCAL_RAW_AVAILABLE
    assert item.document_sha256 == registered.document_sha256
    assert item.local_path == pdf.resolve()


def test_same_sha_local_and_parsed_reuses_data(tmp_path: Path) -> None:
    registry = SQLiteRegistry(tmp_path / "registry.sqlite")
    pdf = tmp_path / "local.pdf"
    _make_pdf(pdf, "same")
    registered = registry.register_document(
        pdf, expected_identity=FilingIdentity(_slot())
    )
    registry.register_parsed_data(
        _record(document_sha256=registered.document_sha256)
    )

    item = _only_item(_planner(registry))

    assert item.action == PlannerAction.REUSE_DATA
    assert item.document_sha256 == registered.document_sha256
    assert item.local_path == pdf.resolve()


def test_different_current_local_sha_blocks_stale_reuse_and_parses_local(
    tmp_path: Path,
) -> None:
    registry = SQLiteRegistry(tmp_path / "registry.sqlite")
    registry.register_parsed_data(_record(document_sha256="a" * 64))
    pdf = tmp_path / "new.pdf"
    _make_pdf(pdf, "new source")
    registered = registry.register_document(
        pdf, expected_identity=FilingIdentity(_slot())
    )
    assert registered.document_sha256 != "a" * 64

    item = _only_item(_planner(registry))

    assert item.action == PlannerAction.PARSE_LOCAL
    assert item.reason_code == ReasonCode.SOURCE_MATERIAL_CHANGE
    assert item.document_sha256 == registered.document_sha256
    assert ReasonCode.SOURCE_MATERIAL_CHANGE in item.blocking_reasons


def test_no_parsed_and_no_local_downloads(tmp_path: Path) -> None:
    registry = SQLiteRegistry(tmp_path / "registry.sqlite")

    item = _only_item(_planner(registry))

    assert item.action == PlannerAction.DOWNLOAD_AND_PARSE
    assert item.reason_code == ReasonCode.NO_REUSABLE_DATA_OR_LOCAL_RAW


def test_multiple_distinct_local_sha_requires_review(tmp_path: Path) -> None:
    registry = SQLiteRegistry(tmp_path / "registry.sqlite")
    first = tmp_path / "one.pdf"
    second = tmp_path / "two.pdf"
    _make_pdf(first, "one")
    _make_pdf(second, "two")
    identity = FilingIdentity(_slot())
    registry.register_document(first, expected_identity=identity)
    registry.register_document(second, expected_identity=identity)

    item = _only_item(_planner(registry))

    assert item.action == PlannerAction.REVIEW_REQUIRED
    assert item.reason_code == ReasonCode.LOCAL_DOCUMENT_AMBIGUOUS


def test_multiple_reusable_distinct_sha_without_local_requires_review(
    tmp_path: Path,
) -> None:
    registry = SQLiteRegistry(tmp_path / "registry.sqlite")
    registry.register_parsed_data(
        _record(parse_run_id="run-a", document_sha256="a" * 64)
    )
    registry.register_parsed_data(
        _record(parse_run_id="run-b", document_sha256="b" * 64)
    )

    item = _only_item(_planner(registry))

    assert item.action == PlannerAction.REVIEW_REQUIRED
    assert item.reason_code == ReasonCode.MULTIPLE_REUSABLE_DOCUMENTS_AMBIGUOUS


def test_multiple_reusable_runs_same_sha_select_lowest_parse_run_id(
    tmp_path: Path,
) -> None:
    registry = SQLiteRegistry(tmp_path / "registry.sqlite")
    registry.register_parsed_data(
        _record(parse_run_id="run-z", document_sha256="a" * 64)
    )
    registry.register_parsed_data(
        _record(parse_run_id="run-a", document_sha256="a" * 64)
    )

    item = _only_item(_planner(registry))

    assert item.action == PlannerAction.REUSE_DATA
    assert item.parse_run_id == "run-a"


def test_verified_duplicate_copy_is_used_when_other_location_drifts(
    tmp_path: Path,
) -> None:
    registry = SQLiteRegistry(tmp_path / "registry.sqlite")
    first = tmp_path / "a.pdf"
    second = tmp_path / "b.pdf"
    replacement = tmp_path / "replacement.pdf"
    _make_pdf(first, "same source")
    second.write_bytes(first.read_bytes())
    identity = FilingIdentity(_slot())
    registered = registry.register_document(first, expected_identity=identity)
    registry.register_document(second, expected_identity=identity)

    _make_pdf(replacement, "changed in place")
    first.write_bytes(replacement.read_bytes())

    item = _only_item(_planner(registry))

    assert item.action == PlannerAction.PARSE_LOCAL
    assert item.reason_code == ReasonCode.LOCAL_RAW_AVAILABLE
    assert item.document_sha256 == registered.document_sha256
    assert item.local_path == second.resolve()


def test_changed_bound_path_without_reregister_is_blocked(tmp_path: Path) -> None:
    registry = SQLiteRegistry(tmp_path / "registry.sqlite")
    pdf = tmp_path / "drift.pdf"
    replacement = tmp_path / "replacement.pdf"
    _make_pdf(pdf, "original")
    registered = registry.register_document(
        pdf, expected_identity=FilingIdentity(_slot())
    )
    registry.register_parsed_data(
        _record(document_sha256=registered.document_sha256)
    )

    _make_pdf(replacement, "changed in place")
    pdf.write_bytes(replacement.read_bytes())

    item = _only_item(_planner(registry))

    assert item.action == PlannerAction.BLOCKED
    assert item.reason_code == ReasonCode.LOCAL_CONTENT_DRIFT
    assert item.blocking_reasons == (ReasonCode.LOCAL_CONTENT_DRIFT,)


def test_conflicting_binding_is_blocked(tmp_path: Path) -> None:
    registry = SQLiteRegistry(tmp_path / "registry.sqlite")
    pdf = tmp_path / "conflict.pdf"
    _make_pdf(pdf, "conflict")
    registry.register_document(
        pdf, expected_identity=FilingIdentity(_slot(2024))
    )
    registry.register_document(
        pdf, expected_identity=FilingIdentity(_slot(2023))
    )

    item = _only_item(_planner(registry))

    assert item.action == PlannerAction.BLOCKED
    assert item.reason_code == ReasonCode.LOCAL_BINDING_CONFLICT


def test_plan_is_deterministic_across_repeated_calls_and_db_reopen(
    tmp_path: Path,
) -> None:
    db = tmp_path / "registry.sqlite"
    registry = SQLiteRegistry(db)
    registry.register_parsed_data(_record())

    first = _planner(registry).build_plan(_company(), 2024, 2024, _policy()).to_dict()
    second = _planner(registry).build_plan(_company(), 2024, 2024, _policy()).to_dict()

    reopened = SQLiteRegistry(db)
    third = _planner(reopened).build_plan(_company(), 2024, 2024, _policy()).to_dict()

    assert first == second == third


def test_planner_has_no_network_dayu_or_heavy_imports() -> None:
    import financial_filing_data_foundation.planner.incremental as incremental
    import financial_filing_data_foundation.registry.sqlite_registry as registry_module

    source = (inspect.getsource(incremental) + inspect.getsource(registry_module)).lower()

    forbidden = (
        "import dayu",
        "from dayu",
        "import httpx",
        "from httpx",
        "import requests",
        "from requests",
        "import urllib",
        "from urllib",
        "import socket",
        "from socket",
        "import docling",
        "from docling",
        "import torch",
        "from torch",
        "import openai",
        "from openai",
    )
    assert not any(token in source for token in forbidden)
