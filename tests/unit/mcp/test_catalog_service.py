from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from financial_filing_data_foundation.candidates import detect_table_candidates
from financial_filing_data_foundation.facts import extract_raw_facts
from financial_filing_data_foundation.mcp import (
    CatalogError,
    McpCatalog,
    McpQueryService,
    McpServiceError,
)
from financial_filing_data_foundation.mcp.report_safe import (
    find_table_rows,
    get_company_report_context,
    search_company,
)
from financial_filing_data_foundation.native.models import (
    P3_PARSER_VERSION,
    SCHEMA_VERSION as P3_SCHEMA_VERSION,
)
from financial_filing_data_foundation.native.search import build_search_db
from financial_filing_data_foundation.tables import reconstruct_tables
from financial_filing_data_foundation.validation import (
    validate_document_artifacts,
)


DOC_SHA = "d" * 64


def _word(
    text: str,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    line_no: int,
    word_no: int,
) -> dict:
    return {
        "text": text,
        "bbox": [x0, y0, x1, y1],
        "block_no": 0,
        "line_no": line_no,
        "word_no": word_no,
    }


def _page() -> dict:
    raw_rows = [
        ("项目", "2024", "2023"),
        ("营业收入", "1000", "900"),
        ("净利润", "200", "150"),
        ("资产总计", "5000", "4500"),
        ("负债合计", "2000", "1800"),
        ("所有者权益合计", "3000", "2700"),
        ("经营活动产生的现金流量净额", "300", "250"),
    ]
    words: list[dict] = []
    lines: list[dict] = []
    for row_no, values in enumerate(raw_rows):
        y0 = 100 + row_no * 24
        row_words: list[dict] = []
        for word_no, (text, x0, x1) in enumerate(
            zip(
                values,
                (50.0, 300.0, 400.0),
                (220.0, 340.0, 440.0),
            )
        ):
            word = _word(
                text,
                x0,
                y0,
                x1,
                y0 + 12,
                row_no,
                word_no,
            )
            words.append(word)
            row_words.append(word)
        lines.append(
            {
                "line_no": row_no,
                "bbox": [50, y0, 440, y0 + 12],
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
        "drawing_count": 40,
        "text": text,
        "words": words,
        "blocks": [
            {
                "block_no": 0,
                "bbox": [50, 100, 440, 100 + (len(lines) - 1) * 24 + 12],
                "type": "text",
                "text": text,
                "lines": lines,
                "reading_order_index": 0,
            }
        ],
        "warnings": [],
    }


def _write_native(root: Path) -> Path:
    page = _page()
    sections = [
        {
            "section_id": "section-1",
            "raw_title": "财务报表",
            "normalized_title": None,
            "level": 1,
            "page_start": 1,
            "page_end": 1,
            "parent_section_id": None,
            "bbox": [50, 80, 180, 92],
            "heading_score": 5.0,
            "heading_signals": ["TEST"],
            "quality_signals": [],
        }
    ]
    artifact = root / "p3" / DOC_SHA
    artifact.mkdir(parents=True)
    (artifact / "pages.jsonl").write_text(
        json.dumps(page, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (artifact / "sections.jsonl").write_text(
        json.dumps(sections[0], ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
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
    build_search_db(
        artifact / "search.sqlite",
        DOC_SHA,
        [page],
        sections,
    )
    return artifact


def _relative(root: Path, value: Path) -> str:
    return value.resolve().relative_to(root.resolve()).as_posix()


def _build_fixture(
    root: Path,
    *,
    document_sha256: str = DOC_SHA,
    ticker: str = "TEST",
    fiscal_year: int = 2024,
) -> tuple[Path, dict[str, Path]]:
    if document_sha256 != DOC_SHA:
        raise ValueError("synthetic pipeline currently uses DOC_SHA")
    p3 = _write_native(root)
    p4 = detect_table_candidates(p3, root / "p4").artifact_dir
    p5 = reconstruct_tables(p3, p4, root / "p5").artifact_dir
    p6 = extract_raw_facts(p3, p5, root / "p6").artifact_dir
    p7 = validate_document_artifacts(
        p3,
        p5,
        p6,
        root / "p7",
    ).artifact_dir

    catalog_path = root / "catalog.json"
    payload = {
        "schema_version": "p8-mcp-catalog-v1",
        "documents": [
            {
                "document_sha256": document_sha256,
                "market": "CN",
                "ticker": ticker,
                "fiscal_year": fiscal_year,
                "filing_type": "ANNUAL",
                "p3_artifact_dir": _relative(root, p3),
                "p5_artifact_dir": _relative(root, p5),
                "p6_artifact_dir": _relative(root, p6),
                "p7_artifact_dir": _relative(root, p7),
            }
        ],
    }
    catalog_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return catalog_path, {"p3": p3, "p4": p4, "p5": p5, "p6": p6, "p7": p7}


@pytest.fixture()
def service_fixture(tmp_path: Path):
    catalog_path, artifacts = _build_fixture(tmp_path)
    catalog = McpCatalog.load(tmp_path, catalog_path)
    service = McpQueryService(catalog)
    return tmp_path, catalog_path, artifacts, catalog, service


def test_catalog_loads_project_relative_artifacts(service_fixture) -> None:
    root, _, _, catalog, _ = service_fixture
    assert catalog.project_root == root.resolve()
    assert len(catalog.documents) == 1
    assert catalog.documents[0].document_sha256 == DOC_SHA


def test_catalog_rejects_absolute_artifact_path(tmp_path: Path) -> None:
    catalog_path, artifacts = _build_fixture(tmp_path)
    payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    payload["documents"][0]["p3_artifact_dir"] = str(
        artifacts["p3"].resolve()
    )
    catalog_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(CatalogError) as exc_info:
        McpCatalog.load(tmp_path, catalog_path)
    assert exc_info.value.reason_code == "P8_PATH_OUTSIDE_PROJECT_ROOT"


def test_catalog_rejects_traversal(tmp_path: Path) -> None:
    catalog_path, _ = _build_fixture(tmp_path)
    payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    payload["documents"][0]["p3_artifact_dir"] = "../outside"
    catalog_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(CatalogError) as exc_info:
        McpCatalog.load(tmp_path, catalog_path)
    assert exc_info.value.reason_code == "P8_PATH_OUTSIDE_PROJECT_ROOT"


def test_catalog_rejects_duplicate_sha(tmp_path: Path) -> None:
    catalog_path, _ = _build_fixture(tmp_path)
    payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    payload["documents"].append(dict(payload["documents"][0]))
    payload["documents"][1]["ticker"] = "TEST2"
    catalog_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(CatalogError) as exc_info:
        McpCatalog.load(tmp_path, catalog_path)
    assert exc_info.value.reason_code == "P8_CATALOG_INVALID"


def test_catalog_rejects_duplicate_filing_identity(tmp_path: Path) -> None:
    catalog_path, _ = _build_fixture(tmp_path)
    payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    duplicate = dict(payload["documents"][0])
    duplicate["document_sha256"] = "e" * 64
    payload["documents"].append(duplicate)
    catalog_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(CatalogError) as exc_info:
        McpCatalog.load(tmp_path, catalog_path)
    assert exc_info.value.reason_code == "P8_CATALOG_INVALID"


def test_list_and_get_document(service_fixture) -> None:
    _, _, _, _, service = service_fixture
    listed = service.list_documents()
    assert listed["tool"] == "ffdf_list_documents"
    assert listed["data"]["total"] == 1
    assert listed["data"]["documents"][0]["ticker"] == "TEST"
    assert "validation_status" not in listed["data"]["documents"][0]
    assert service._bundles == {}

    detail = service.get_document(DOC_SHA.upper())
    assert DOC_SHA in service._bundles
    assert detail["document_sha256"] == DOC_SHA
    assert detail["data"]["page_count"] == 1
    assert detail["data"]["table_count"] >= 1
    assert detail["data"]["raw_fact_count"] >= 1


def test_document_filters_and_missing_document(service_fixture) -> None:
    _, _, _, _, service = service_fixture
    assert service.list_documents(market="cn")["data"]["total"] == 1
    assert service.list_documents(ticker="missing")["data"]["total"] == 0
    assert service.list_documents(fiscal_year=2025)["data"]["total"] == 0

    with pytest.raises(McpServiceError) as exc_info:
        service.get_document("f" * 64)
    assert exc_info.value.reason_code == "P8_DOCUMENT_NOT_FOUND"


def test_search_read_pages_and_sections(service_fixture) -> None:
    _, _, _, _, service = service_fixture
    result = service.search_document(DOC_SHA, "营业收入", 10)
    assert result["data"]["returned"] >= 1
    assert result["data"]["results"][0]["page_no"] == 1

    pages = service.read_pages(DOC_SHA, [1])
    assert pages["data"]["returned"] == 1
    assert "营业收入" in pages["data"]["pages"][0]["text"]

    sections = service.list_sections(DOC_SHA)
    assert sections["data"]["sections"][0]["raw_title"] == "财务报表"


def test_page_argument_guards(service_fixture) -> None:
    _, _, _, _, service = service_fixture
    with pytest.raises(McpServiceError):
        service.read_pages(DOC_SHA, [1, 1])
    with pytest.raises(McpServiceError):
        service.read_pages(DOC_SHA, [2])
    with pytest.raises(McpServiceError):
        service.search_document(DOC_SHA, "", 10)
    with pytest.raises(McpServiceError):
        service.search_document(DOC_SHA, "x", 51)


def test_tables_list_and_detail(service_fixture) -> None:
    _, _, _, _, service = service_fixture
    listed = service.list_tables(DOC_SHA, page_no=1, limit=10)
    assert listed["data"]["total"] >= 1
    table_id = listed["data"]["tables"][0]["table_id"]

    table = service.get_table(DOC_SHA, table_id, max_rows=3)
    assert table["data"]["table_id"] == table_id
    assert table["data"]["returned_row_count"] <= 3

    with pytest.raises(McpServiceError) as exc_info:
        service.get_table(DOC_SHA, "missing")
    assert exc_info.value.reason_code == "P8_TABLE_NOT_FOUND"


def test_facts_and_evidence_relation(service_fixture) -> None:
    _, _, _, _, service = service_fixture
    listed = service.list_raw_facts(
        DOC_SHA,
        metric_contains="营业",
        limit=10,
    )
    assert listed["data"]["returned"] >= 1
    first = listed["data"]["facts"][0]

    fact = service.get_fact(DOC_SHA, first["raw_fact_id"])
    assert fact["data"]["evidence_id"] == first["evidence_id"]

    evidence = service.get_evidence(DOC_SHA, first["evidence_id"])
    assert evidence["data"]["raw_fact_id"] if "raw_fact_id" in evidence["data"] else True
    assert evidence["data"]["value_cell_id"] == first["value_cell_id"]
    assert evidence["data"]["source_words"]

    with pytest.raises(McpServiceError) as exc_info:
        service.get_fact(DOC_SHA, "missing")
    assert exc_info.value.reason_code == "P8_FACT_NOT_FOUND"

    with pytest.raises(McpServiceError) as exc_info:
        service.get_evidence(DOC_SHA, "missing")
    assert exc_info.value.reason_code == "P8_EVIDENCE_NOT_FOUND"


def test_validation_result_and_issue_filter(service_fixture) -> None:
    _, _, _, _, service = service_fixture
    result = service.get_validation(DOC_SHA)
    report = result["data"]["report"]
    assert report["document_sha256"] == DOC_SHA
    assert report["validation_status"] in {
        "PASS",
        "REVIEW_REQUIRED",
        "FAIL",
        "BLOCKED",
    }
    assert result["data"]["issues_total"] == report["issue_count"]

    warnings = service.get_validation(DOC_SHA, severity="WARNING")
    assert all(
        issue["severity"] == "WARNING"
        for issue in warnings["data"]["issues"]
    )


def test_upstream_tamper_is_execution_error(tmp_path: Path) -> None:
    catalog_path, artifacts = _build_fixture(tmp_path)
    report_path = artifacts["p7"] / "validation_report.json"
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    payload["validation_status"] = "BLOCKED"
    report_path.write_text(json.dumps(payload), encoding="utf-8")

    catalog = McpCatalog.load(tmp_path, catalog_path)
    service = McpQueryService(catalog)

    listed = service.list_documents()
    assert listed["data"]["total"] == 1
    assert service._bundles == {}

    with pytest.raises(McpServiceError) as exc_info:
        service.get_document(DOC_SHA)
    assert exc_info.value.reason_code == "P8_UPSTREAM_ARTIFACT_INVALID"
    assert service._bundles == {}


def test_service_calls_do_not_mutate_artifacts(service_fixture) -> None:
    _, catalog_path, artifacts, _, service = service_fixture
    paths = [catalog_path]
    for directory in artifacts.values():
        paths.extend(
            path
            for path in directory.iterdir()
            if path.is_file()
        )
    before = {
        path: (
            hashlib.sha256(path.read_bytes()).hexdigest(),
            path.stat().st_size,
            path.stat().st_mtime_ns,
        )
        for path in paths
    }

    docs = service.list_documents()
    service.get_document(DOC_SHA)
    service.search_document(DOC_SHA, "营业收入")
    service.read_pages(DOC_SHA, [1])
    service.list_sections(DOC_SHA)
    tables = service.list_tables(DOC_SHA)
    service.get_table(DOC_SHA, tables["data"]["tables"][0]["table_id"])
    facts = service.list_raw_facts(DOC_SHA)
    fact = facts["data"]["facts"][0]
    service.get_fact(DOC_SHA, fact["raw_fact_id"])
    service.get_evidence(DOC_SHA, fact["evidence_id"])
    service.get_validation(DOC_SHA)
    get_company_report_context(service, "CN", "TEST")
    search_company(service, "CN", "TEST", "营业收入")
    find_table_rows(
        service,
        "CN",
        "TEST",
        "营业收入",
        fiscal_year=2024,
        filing_type="ANNUAL",
    )
    assert docs["data"]["total"] == 1

    after = {
        path: (
            hashlib.sha256(path.read_bytes()).hexdigest(),
            path.stat().st_size,
            path.stat().st_mtime_ns,
        )
        for path in paths
    }
    assert before == after


def test_report_safe_company_context(service_fixture) -> None:
    _, _, _, _, service = service_fixture
    result = get_company_report_context(service, "CN", "TEST")
    assert result["tool"] == "ffdf_get_company_report_context"
    assert result["report_safe_version"] == "p8-report-safe-v1"
    assert result["data"]["total"] == 1
    assert result["data"]["latest_filing"]["document_sha256"] == DOC_SHA
    assert result["data"]["report_guardrails"]["direct_disclosure_preferred"] is True


def test_report_safe_company_search_includes_context(service_fixture) -> None:
    _, _, _, _, service = service_fixture
    result = search_company(
        service,
        "CN",
        "TEST",
        "营业收入",
        page_window=1,
    )
    assert result["tool"] == "ffdf_search_company"
    assert result["data"]["returned_hits"] >= 1
    first = result["data"]["results"][0]
    assert first["match_page"]["page_no"] == 1
    assert "营业收入" in first["match_page"]["text"]
    assert first["neighbor_pages"] == []


def test_report_safe_find_table_rows_preserves_source_label(service_fixture) -> None:
    _, _, _, _, service = service_fixture
    result = find_table_rows(
        service,
        "CN",
        "TEST",
        "营业收入",
        fiscal_year=2024,
        filing_type="ANNUAL",
    )
    assert result["tool"] == "ffdf_find_table_rows"
    assert result["data"]["returned"] >= 1
    first = result["data"]["matches"][0]
    assert first["disclosure_label"] == "营业收入"
    assert first["exact_match"] is True
    assert first["direct_disclosure"] is True


def test_manifest_summary_matches_full_document_summary(service_fixture) -> None:
    _, _, _, _, service = service_fixture
    docs = service.list_documents()["data"]["documents"]
    assert docs
    sha = docs[0]["document_sha256"]

    light = service.get_document_summary_internal(sha)
    full = service.get_document(sha)["data"]

    assert light == full


def test_company_context_uses_manifest_summary_not_full_bundle(
    service_fixture,
    monkeypatch,
) -> None:
    _, _, _, _, service = service_fixture

    def fail(*args, **kwargs):
        raise AssertionError("full get_document must not be used")

    monkeypatch.setattr(service, "get_document", fail)
    result = get_company_report_context(
        service,
        "CN",
        "TEST",
        None,
        None,
    )

    assert result["data"]["total"] >= 1


def test_report_safe_does_not_reach_private_bundle() -> None:
    source = Path(
        "src/financial_filing_data_foundation/mcp/report_safe.py"
    ).read_text(encoding="utf-8")
    assert "service._bundle" not in source
