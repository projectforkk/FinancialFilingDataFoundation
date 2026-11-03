from __future__ import annotations

import json
import sqlite3
from dataclasses import replace
from pathlib import Path

import pytest

from financial_filing_data_foundation.candidates import detect_table_candidates
from financial_filing_data_foundation.facts import extract_raw_facts
from financial_filing_data_foundation.identity import (
    CompanyRef,
    FilingPolicy,
    FilingRequirement,
    FilingSlotKey,
)
from financial_filing_data_foundation.native.models import (
    P3_PARSER_VERSION,
    SCHEMA_VERSION as P3_SCHEMA_VERSION,
)
from financial_filing_data_foundation.planner import (
    IncrementalPlanner,
    PlannerAction,
    PlannerReusePolicy,
)
from financial_filing_data_foundation.registry import (
    CompatibilityStatus,
    SQLiteRegistry,
    ValidationStatus,
)
from financial_filing_data_foundation.tables import reconstruct_tables
from financial_filing_data_foundation.validation import (
    SCHEMA_VERSION,
    ValidationError,
    build_parsed_data_record,
    load_validation_result,
    validate_document_artifacts,
)
from financial_filing_data_foundation.validation import validate
from financial_filing_data_foundation.validation.policy import (
    IssueSeverity,
)


DOC_SHA = "d" * 64


def _issue(severity: IssueSeverity) -> dict:
    return {"severity": severity.value}


def _fact(
    metric: str,
    value: str,
    *,
    fact_id: str,
    page_no: int = 1,
    table_id: str = "t1",
    group_id: str | None = None,
    period: str | None = "2024",
    unit: str | None = "元",
    scope: str | None = "合并",
    column_index: int = 1,
) -> dict:
    return {
        "raw_fact_id": fact_id,
        "document_sha256": DOC_SHA,
        "raw_metric_name": metric,
        "raw_value": value,
        "parsed_numeric_value": value,
        "raw_unit": unit,
        "raw_period_label": period,
        "raw_scope": scope,
        "table_id": table_id,
        "table_group_id": group_id,
        "page_no": page_no,
        "row_id": f"row-{fact_id}",
        "row_index": int(fact_id.strip("f") or "0") if fact_id.startswith("f") and fact_id.strip("f").isdigit() else 0,
        "column_index": column_index,
        "label_cell_ids": [f"label-{fact_id}"],
        "value_cell_id": f"value-{fact_id}",
        "evidence_id": f"e-{fact_id}",
    }


def _evidence(fact: dict) -> dict:
    return {
        "evidence_id": fact["evidence_id"],
        "document_sha256": DOC_SHA,
        "extraction_version": "p6-raw-fact-extractor-v1",
        "page_no": fact["page_no"],
        "bbox": [10.0, 10.0, 20.0, 20.0],
        "raw_text": f"{fact['raw_metric_name']} | {fact['raw_value']}",
        "table_id": fact["table_id"],
        "row_id": fact["row_id"],
        "row_index": fact["row_index"],
        "column_index": fact["column_index"],
        "label_cell_ids": fact["label_cell_ids"],
        "value_cell_id": fact["value_cell_id"],
        "source_words": [
            {
                "page_no": fact["page_no"],
                "block_no": 0,
                "line_no": 0,
                "word_no": 0,
                "bbox": [10.0, 10.0, 20.0, 20.0],
            }
        ],
    }


def _evaluate(
    facts: list[dict],
    *,
    pages: list[dict] | None = None,
    tables: list[dict] | None = None,
    warnings: list[dict] | None = None,
):
    evidence = [_evidence(fact) for fact in facts]
    return validate._evaluate(
        DOC_SHA,
        page_count=1,
        pages=pages if pages is not None else [{"page_no": 1}],
        tables=tables if tables is not None else [{"table_id": "t1"}],
        groups=[],
        facts=facts,
        evidence=evidence,
        p6_warnings=warnings or [],
        compatibility_status=CompatibilityStatus.COMPATIBLE,
    )


def test_status_priority() -> None:
    assert validate._status_from_issues([]) == ValidationStatus.PASS
    assert validate._status_from_issues(
        [_issue(IssueSeverity.WARNING)]
    ) == ValidationStatus.PASS
    assert validate._status_from_issues(
        [_issue(IssueSeverity.REVIEW)]
    ) == ValidationStatus.REVIEW_REQUIRED
    assert validate._status_from_issues(
        [_issue(IssueSeverity.REVIEW), _issue(IssueSeverity.FAILURE)]
    ) == ValidationStatus.FAIL
    assert validate._status_from_issues(
        [_issue(IssueSeverity.FAILURE), _issue(IssueSeverity.BLOCKING)]
    ) == ValidationStatus.BLOCKED


def test_compatibility_status() -> None:
    assert (
        validate._compatibility_status(
            "p3-native-page-section-v1",
            "p5-table-reconstruction-v1",
            "p6-raw-fact-extractor-v1",
        )
        == CompatibilityStatus.COMPATIBLE
    )
    assert (
        validate._compatibility_status(
            "future",
            "p5-table-reconstruction-v1",
            "p6-raw-fact-extractor-v1",
        )
        == CompatibilityStatus.INCOMPATIBLE
    )


def test_no_facts_is_failure_not_blocked() -> None:
    issues, metrics, status = _evaluate([])
    reasons = {row["reason_code"] for row in issues}
    assert "NO_RAW_FACTS" in reasons
    assert status == ValidationStatus.FAIL
    assert metrics["blocking_issue_count"] == 0
    assert metrics["failure_issue_count"] == 1


def test_invalid_page_sequence_is_blocked() -> None:
    fact = _fact("营业收入", "100", fact_id="f1")
    issues, _, status = _evaluate(
        [fact],
        pages=[{"page_no": 2}],
    )
    assert status == ValidationStatus.BLOCKED
    assert "PAGE_SEQUENCE_INVALID" in {
        row["reason_code"] for row in issues
    }


def test_balance_reconciliation_passes() -> None:
    facts = [
        _fact("资产总计", "3000", fact_id="f1"),
        _fact("负债合计", "1800", fact_id="f2"),
        _fact("所有者权益合计", "1200", fact_id="f3"),
    ]
    issues, metrics = validate._reconciliation_issues(DOC_SHA, facts)
    assert issues == []
    assert metrics["evaluated_rule_count"] == 1
    assert metrics["passed_rule_count"] == 1
    assert metrics["failed_rule_count"] == 0


def test_balance_reconciliation_failure_is_failure_issue() -> None:
    facts = [
        _fact("资产总计", "3000", fact_id="f1"),
        _fact("负债合计", "1700", fact_id="f2"),
        _fact("所有者权益合计", "1200", fact_id="f3"),
    ]
    issues, metrics = validate._reconciliation_issues(DOC_SHA, facts)
    assert metrics["failed_rule_count"] == 1
    assert [row["reason_code"] for row in issues] == [
        "BALANCE_SHEET_RECONCILIATION_FAILED"
    ]
    assert issues[0]["severity"] == "FAILURE"


def test_balance_reconciliation_skips_ambiguous_context() -> None:
    facts = [
        _fact("资产总计", "3000", fact_id="f1"),
        _fact("资产总计", "3000", fact_id="f2"),
        _fact("负债合计", "1800", fact_id="f3"),
        _fact("所有者权益合计", "1200", fact_id="f4"),
    ]
    issues, metrics = validate._reconciliation_issues(DOC_SHA, facts)
    assert issues == []
    assert metrics["evaluated_rule_count"] == 0
    assert metrics["skipped_rule_count"] == 1


def test_cash_reconciliation_pass_and_fail() -> None:
    passing = [
        _fact("期初现金及现金等价物余额", "100", fact_id="f1"),
        _fact("现金及现金等价物净增加额", "50", fact_id="f2"),
        _fact("期末现金及现金等价物余额", "150", fact_id="f3"),
    ]
    issues, metrics = validate._reconciliation_issues(DOC_SHA, passing)
    assert issues == []
    assert metrics["passed_rule_count"] == 1

    failing = [
        _fact("期初现金及现金等价物余额", "100", fact_id="f1"),
        _fact("现金及现金等价物净增加额", "40", fact_id="f2"),
        _fact("期末现金及现金等价物余额", "150", fact_id="f3"),
    ]
    issues, metrics = validate._reconciliation_issues(DOC_SHA, failing)
    assert metrics["failed_rule_count"] == 1
    assert issues[0]["reason_code"] == "CASH_RECONCILIATION_FAILED"


def test_duplicate_conflict_is_review_for_same_source_lineage() -> None:
    first = _fact("营业收入", "100", fact_id="f1")
    second = _fact("营业收入", "101", fact_id="f2")
    second["row_id"] = first["row_id"]
    second["value_cell_id"] = first["value_cell_id"]
    issues = validate._duplicate_issues(DOC_SHA, [first, second])
    assert len(issues) == 1
    assert issues[0]["reason_code"] == "CONFLICTING_FACT_VALUES"
    assert issues[0]["severity"] == "REVIEW"


def test_duplicate_same_value_is_warning_for_same_source_lineage() -> None:
    first = _fact("营业收入", "100", fact_id="f1")
    second = _fact("营业收入", "100", fact_id="f2")
    second["row_id"] = first["row_id"]
    second["value_cell_id"] = first["value_cell_id"]
    issues = validate._duplicate_issues(DOC_SHA, [first, second])
    assert len(issues) == 1
    assert issues[0]["reason_code"] == "DUPLICATE_FACT_VALUES"
    assert issues[0]["severity"] == "WARNING"


def test_repeated_metric_name_across_distinct_rows_is_not_a_conflict() -> None:
    first = _fact("营业收入", "100", fact_id="f1")
    second = _fact("营业收入", "101", fact_id="f2")
    assert first["row_id"] != second["row_id"]
    assert validate._duplicate_issues(DOC_SHA, [first, second]) == []


def test_low_period_and_unit_coverage_require_review() -> None:
    facts = [
        _fact(
            f"指标{i}",
            str(i + 1),
            fact_id=f"f{i}",
            period=None,
            unit=None,
            scope=None,
        )
        for i in range(60)
    ]
    issues, _, status = _evaluate(facts)
    reasons = {row["reason_code"] for row in issues}
    assert "RAW_PERIOD_COVERAGE_LOW" in reasons
    assert "RAW_UNIT_COVERAGE_LOW" in reasons
    assert status == ValidationStatus.REVIEW_REQUIRED


def test_row_without_label_threshold() -> None:
    facts = [_fact("营业收入", "100", fact_id=f"f{i}") for i in range(10)]
    issues, _, status = _evaluate(
        facts,
        warnings=[{"reason_code": "ROW_WITHOUT_LABEL", "count": 4}],
    )
    reasons = {row["reason_code"] for row in issues}
    assert "ROW_WITHOUT_LABEL_HIGH" in reasons
    assert status == ValidationStatus.REVIEW_REQUIRED


def test_issue_id_is_stable() -> None:
    first = validate._issue(
        DOC_SHA,
        "TEST_REASON",
        IssueSeverity.REVIEW,
        "message",
        raw_fact_ids=["b", "a"],
    )
    second = validate._issue(
        DOC_SHA,
        "TEST_REASON",
        IssueSeverity.REVIEW,
        "message",
        raw_fact_ids=["a", "b"],
    )
    assert first["issue_id"] == second["issue_id"]


def _word(text: str, x0: float, y0: float, x1: float, y1: float, line: int, word: int) -> dict:
    return {
        "text": text,
        "bbox": [x0, y0, x1, y1],
        "block_no": 0,
        "line_no": line,
        "word_no": word,
    }


def _page() -> dict:
    raw_rows = [
        ("项目", "2024", "2023"),
        ("资产总计", "3000", "2800"),
        ("负债合计", "1800", "1700"),
        ("所有者权益合计", "1200", "1100"),
        ("营业收入", "1000", "900"),
        ("净利润", "200", "150"),
        ("经营活动产生的现金流量净额", "300", "250"),
        ("期初现金及现金等价物余额", "100", "80"),
        ("现金及现金等价物净增加额", "50", "20"),
        ("期末现金及现金等价物余额", "150", "100"),
    ]
    words = []
    lines = []
    for row_no, values in enumerate(raw_rows):
        y0 = 80 + row_no * 22
        row_words = []
        for word_no, (text, x0, x1) in enumerate(
            zip(values, (40.0, 300.0, 400.0), (220.0, 340.0, 440.0))
        ):
            word = _word(text, x0, y0, x1, y0 + 12, row_no, word_no)
            words.append(word)
            row_words.append(word)
        lines.append(
            {
                "line_no": row_no,
                "bbox": [40, y0, 440, y0 + 12],
                "text": " ".join(word["text"] for word in row_words),
                "spans": [],
                "repeated_header_footer": False,
            }
        )
    text = "\n".join(line["text"] for line in lines)
    return {
        "page_no": 1,
        "width": 595.0,
        "height": 842.0,
        "rotation": 0,
        "native_text_available": True,
        "native_char_count": len(text),
        "word_count": len(words),
        "block_count": 1,
        "line_count": len(lines),
        "span_count": 0,
        "image_count": 0,
        "drawing_count": 30,
        "text": text,
        "words": words,
        "blocks": [
            {
                "block_no": 0,
                "bbox": [40, 80, 440, 290],
                "type": "text",
                "text": text,
                "lines": lines,
                "reading_order_index": 0,
            }
        ],
        "warnings": [],
    }


def _write_p3(root: Path) -> Path:
    artifact = root / DOC_SHA
    artifact.mkdir(parents=True)
    page = _page()
    (artifact / "pages.jsonl").write_text(
        json.dumps(page, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (artifact / "sections.jsonl").write_text("", encoding="utf-8")
    (artifact / "document.json").write_text(
        json.dumps(
            {
                "schema_version": P3_SCHEMA_VERSION,
                "document_sha256": DOC_SHA,
                "file_size": 123,
                "page_count": 1,
                "parser_version": P3_PARSER_VERSION,
                "timings_ms": {},
                "warnings": [],
            }
        ),
        encoding="utf-8",
    )
    conn = sqlite3.connect(artifact / "search.sqlite")
    conn.execute(
        "CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL)"
    )
    conn.executemany(
        "INSERT INTO metadata(key,value) VALUES(?,?)",
        (
            ("document_sha256", DOC_SHA),
            ("schema_version", P3_SCHEMA_VERSION),
        ),
    )
    conn.commit()
    conn.close()
    return artifact


def _build_chain(tmp_path: Path) -> tuple[Path, Path, Path]:
    p3 = _write_p3(tmp_path / "p3")
    p4 = detect_table_candidates(p3, tmp_path / "p4").artifact_dir
    p5 = reconstruct_tables(p3, p4, tmp_path / "p5").artifact_dir
    p6 = extract_raw_facts(p3, p5, tmp_path / "p6").artifact_dir
    return p3, p5, p6


def test_preflight_missing_input_returns_execution_error_without_artifact(
    tmp_path: Path,
) -> None:
    missing = tmp_path / "missing"
    output = tmp_path / "p7"
    with pytest.raises(ValidationError) as exc_info:
        validate_document_artifacts(
            missing,
            missing,
            missing,
            output,
        )
    assert exc_info.value.reason_code == "P7_INPUT_ARTIFACT_INVALID"
    assert not output.exists()


def test_full_artifact_is_pass_and_reusable(tmp_path: Path) -> None:
    p3, p5, p6 = _build_chain(tmp_path)
    artifact = validate_document_artifacts(
        p3, p5, p6, tmp_path / "p7"
    )
    assert artifact.validation_status == ValidationStatus.PASS
    assert artifact.compatibility_status == CompatibilityStatus.COMPATIBLE
    assert artifact.reuse_eligible is True
    assert artifact.blocking_issue_count == 0
    assert artifact.failure_issue_count == 0
    assert artifact.review_issue_count == 0


def test_dual_root_issues_are_byte_identical(tmp_path: Path) -> None:
    p3, p5, p6 = _build_chain(tmp_path)
    first = validate_document_artifacts(p3, p5, p6, tmp_path / "a")
    second = validate_document_artifacts(p3, p5, p6, tmp_path / "b")
    assert first.issues_path.read_bytes() == second.issues_path.read_bytes()

    left = json.loads(first.report_path.read_text(encoding="utf-8"))
    right = json.loads(second.report_path.read_text(encoding="utf-8"))
    left.pop("timings_ms")
    right.pop("timings_ms")
    assert left == right


def test_valid_artifact_reuses_without_rewrite(tmp_path: Path) -> None:
    p3, p5, p6 = _build_chain(tmp_path)
    first = validate_document_artifacts(p3, p5, p6, tmp_path / "p7")
    before = first.report_path.stat().st_mtime_ns
    second = validate_document_artifacts(p3, p5, p6, tmp_path / "p7")
    assert second.report_path.stat().st_mtime_ns == before


def test_report_tamper_is_blocked(tmp_path: Path) -> None:
    p3, p5, p6 = _build_chain(tmp_path)
    artifact = validate_document_artifacts(p3, p5, p6, tmp_path / "p7")
    report = json.loads(artifact.report_path.read_text(encoding="utf-8"))
    report["validation_status"] = "REVIEW_REQUIRED"
    artifact.report_path.write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(ValidationError) as exc_info:
        load_validation_result(artifact.artifact_dir, p3, p5, p6)
    assert exc_info.value.reason_code == "P7_ARTIFACT_INCOMPLETE_OR_CORRUPT"


def test_issue_tamper_is_blocked(tmp_path: Path) -> None:
    p3, p5, p6 = _build_chain(tmp_path)
    artifact = validate_document_artifacts(p3, p5, p6, tmp_path / "p7")
    artifact.issues_path.write_text(
        json.dumps(
            {
                "issue_id": "tampered",
                "document_sha256": DOC_SHA,
                "reason_code": "FAKE",
                "severity": "WARNING",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValidationError):
        load_validation_result(artifact.artifact_dir, p3, p5, p6)


def test_build_record_and_planner_reuses_pass(tmp_path: Path) -> None:
    p3, p5, p6 = _build_chain(tmp_path)
    artifact = validate_document_artifacts(p3, p5, p6, tmp_path / "p7")
    slot = FilingSlotKey("CN", "CN:600519", "ANNUAL_REPORT", 2024, "FY")
    record = build_parsed_data_record(
        artifact, slot, str(artifact.artifact_dir)
    )
    assert record.validation_status == ValidationStatus.PASS
    assert record.blocking_issue_count == 0
    assert record.schema_version == SCHEMA_VERSION

    registry = SQLiteRegistry(tmp_path / "registry.sqlite")
    registry.register_parsed_data(record)
    planner = IncrementalPlanner(
        registry,
        PlannerReusePolicy(
            accepted_schema_versions=frozenset({SCHEMA_VERSION})
        ),
    )
    company = CompanyRef("CN", "CN:600519", "600519")
    policy = FilingPolicy((FilingRequirement("ANNUAL_REPORT", "FY"),))
    item = planner.build_plan(company, 2024, 2024, policy).items[0]
    assert item.action == PlannerAction.REUSE_DATA


def test_planner_does_not_reuse_review_record(tmp_path: Path) -> None:
    p3, p5, p6 = _build_chain(tmp_path)
    artifact = validate_document_artifacts(p3, p5, p6, tmp_path / "p7")
    review_artifact = replace(
        artifact,
        validation_status=ValidationStatus.REVIEW_REQUIRED,
        reuse_eligible=False,
        review_issue_count=1,
    )
    slot = FilingSlotKey("CN", "CN:600519", "ANNUAL_REPORT", 2024, "FY")
    record = build_parsed_data_record(
        review_artifact, slot, str(artifact.artifact_dir)
    )
    registry = SQLiteRegistry(tmp_path / "registry.sqlite")
    registry.register_parsed_data(record)
    planner = IncrementalPlanner(
        registry,
        PlannerReusePolicy(
            accepted_schema_versions=frozenset({SCHEMA_VERSION})
        ),
    )
    company = CompanyRef("CN", "CN:600519", "600519")
    policy = FilingPolicy((FilingRequirement("ANNUAL_REPORT", "FY"),))
    item = planner.build_plan(company, 2024, 2024, policy).items[0]
    assert item.action != PlannerAction.REUSE_DATA


def test_validation_does_not_open_pdf(monkeypatch, tmp_path: Path) -> None:
    p3, p5, p6 = _build_chain(tmp_path)

    import financial_filing_data_foundation.native.parser as native_parser

    monkeypatch.setattr(
        native_parser.pymupdf,
        "open",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("P7 must not open PDF")
        ),
    )

    artifact = validate_document_artifacts(
        p3, p5, p6, tmp_path / "p7"
    )
    assert artifact.validation_status == ValidationStatus.PASS


def test_upstream_artifacts_are_immutable(tmp_path: Path) -> None:
    p3, p5, p6 = _build_chain(tmp_path)
    paths = [
        p3 / "document.json",
        p3 / "pages.jsonl",
        p3 / "sections.jsonl",
        p3 / "search.sqlite",
        p5 / "table_manifest.json",
        p5 / "tables.jsonl",
        p5 / "table_groups.jsonl",
        p6 / "fact_manifest.json",
        p6 / "raw_facts.jsonl",
        p6 / "evidence.jsonl",
    ]
    before = {
        path: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in paths
    }
    validate_document_artifacts(p3, p5, p6, tmp_path / "p7")
    after = {
        path: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in paths
    }
    assert before == after
