from __future__ import annotations

import json
from pathlib import Path

import pytest

from financial_filing_data_foundation.mcp.catalog import McpCatalog
from financial_filing_data_foundation.mcp.service import McpQueryService
from financial_filing_data_foundation.us_sec.package import (
    SecMemberRole,
    SecPackageMember,
    build_package,
)
from financial_filing_data_foundation.us_sec.parser import parse_sec_package
from financial_filing_data_foundation.us_sec.ingest import ingest_sec_package
from financial_filing_data_foundation.us_sec.validation import validate_sec_artifacts


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
                source_url="https://www.sec.gov/Archives/edgar/data/320193/example.htm",
                body=b"<html><body><h1>Revenue</h1><p>Revenue was 100.</p></body></html>",
            ),
        ),
    )


def test_sec_p7_validation_is_source_aware_and_writes_report(tmp_path: Path) -> None:
    package = _package()
    parsed = parse_sec_package(package, tmp_path / "p11")
    validation = validate_sec_artifacts(parsed, tmp_path / "p7")
    assert validation.validation_status == "PASS"
    assert validation.blocking_issue_count == 0
    assert validation.reuse_eligible is True
    assert (validation.artifact_dir / "validation.json").is_file()


def test_sec_p8_reads_catalog_entry_without_network(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("FFDF_P11_US_DEV", "1")
    package = _package()
    parsed = parse_sec_package(package, tmp_path / "p11")
    validation = validate_sec_artifacts(parsed, tmp_path / "p7")
    catalog_path = tmp_path / "workspace" / "mcp" / "p8-live-catalog.json"
    catalog_path.parent.mkdir(parents=True)
    catalog_path.write_text(
        json.dumps(
            {
                "schema_version": "p8-mcp-catalog-v1",
                "documents": [
                    {
                        "document_sha256": package.package_sha256,
                        "package_sha256": package.package_sha256,
                        "source_kind": "SEC",
                        "market": "US",
                        "ticker": "CIK0000320193",
                        "fiscal_year": 2025,
                        "filing_type": "Q2",
                        "raw_fiscal_period": "Q2",
                        "sec_artifact_dir": parsed.artifact_dir.relative_to(tmp_path).as_posix(),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    catalog = McpCatalog.load(tmp_path, catalog_path)
    service = McpQueryService(catalog)
    listed = service.list_documents(market="US")
    assert listed["data"]["documents"][0]["source_kind"] == "SEC"
    detail = service.get_document(package.package_sha256)
    assert detail["data"]["page_count"] == len(parsed.pages)
    assert detail["data"]["validation_status"] == validation.validation_status
    assert service.read_pages(package.package_sha256, [1])["data"]["pages"][0]["pagination_kind"] == "VIRTUAL_HTML"
    assert service.search_document(package.package_sha256, "Revenue")["data"]["returned"] >= 1
    assert service.get_validation(package.package_sha256)["data"]["report"]["validation_status"] == "PASS"


def test_sec_ingest_publishes_only_nonblocking_package(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("FFDF_P11_US_DEV", "1")
    result = ingest_sec_package(_package(), root=tmp_path, ticker="AAPL", period="Q2")
    assert result.research_ready is True
    assert result.catalog_status == "ADDED"
    assert result.catalog_path.is_file()

