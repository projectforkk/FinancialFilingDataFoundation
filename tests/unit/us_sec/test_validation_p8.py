from __future__ import annotations

import json
from pathlib import Path

import pytest

from financial_filing_data_foundation.mcp.catalog import McpCatalog
from financial_filing_data_foundation.mcp.service import McpQueryService, McpServiceError
from financial_filing_data_foundation.registry import SQLiteRegistry
from financial_filing_data_foundation.us_sec.package import (
    SecMemberRole,
    SecPackageMember,
    SecPackageStore,
    build_package,
)
from financial_filing_data_foundation.us_sec.discovery import SecDiscoveryObservation
from financial_filing_data_foundation.us_sec.models import SecCompanyRef, SecFilingCandidate, SecIssuerKind
from financial_filing_data_foundation.us_sec.parser import parse_sec_package
from financial_filing_data_foundation.us_sec.ingest import ingest_sec_package
from financial_filing_data_foundation.us_sec.validation import (
    SEC_VALIDATION_SCHEMA,
    load_sec_validation,
    validate_sec_artifacts,
)
from financial_filing_data_foundation.us_sec.path_policy import archive_member_url


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
                source_url=archive_member_url("0000320193", "0000320193-25-000001", "example.htm"),
                body=(
                    b'<html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL" xmlns:xbrli="http://www.xbrl.org/2003/instance" xmlns:us-gaap="http://fasb.org/us-gaap/2025"><body><ix:header>'
                    b'<xbrli:context id="c1"><xbrli:entity><xbrli:identifier>0000320193</xbrli:identifier>'
                    b'</xbrli:entity><xbrli:period><xbrli:instant>2025-06-30</xbrli:instant>'
                    b'</xbrli:period></xbrli:context>'
                    b'<xbrli:unit id="USD"><xbrli:measure>iso4217:USD</xbrli:measure></xbrli:unit>'
                    b'</ix:header><h1>Revenue</h1><p><ix:nonfraction name="us-gaap:Revenues" '
                    b'contextRef="c1" unitRef="USD" decimals="0">100</ix:nonfraction></p>'
                    b'<table><tr><th>Metric</th><th>Value</th></tr><tr><td>Revenue</td><td>100</td></tr></table></body></html>'
                ),
            ),
        ),
    )


def _empty_periodic_package() -> object:
    package = _package()
    member = package.members[0]
    return build_package(
        cik=package.cik,
        accession="0000320193-25-000099",
        form=package.form,
        fiscal_year=package.fiscal_year,
        period=package.period,
        members=(
            SecPackageMember(
                relative_name=member.relative_name,
                role=member.role,
                content_type=member.content_type,
                source_url=archive_member_url(
                    package.cik,
                    "0000320193-25-000099",
                    member.relative_name,
                ),
                body=b"<html><body><h1>Revenue</h1><p>Revenue was 100.</p></body></html>",
            ),
        ),
    )


def _observation(package: object) -> SecDiscoveryObservation:
    candidate = SecFilingCandidate(
        cik=package.cik,
        ticker="AAPL",
        accession=package.accession,
        normalized_accession=package.accession.replace("-", ""),
        form=package.form,
        filing_date="2025-07-30",
        report_period="2025-06-30",
        primary_document=package.primary_document,
        source_url=archive_member_url(package.cik, package.accession, package.primary_document),
        amended=False,
        issuer_kind=SecIssuerKind.DOMESTIC,
    )
    body = json.dumps(
        {
            "cik": package.cik,
            "fiscalYearEnd": "1231",
            "filings": {
                "recent": {
                    "accessionNumber": [
                        "0000320193-24-000100",
                        "0000320193-25-000100",
                        package.accession,
                        "0000320193-25-000101",
                        "0000320193-25-000102",
                    ],
                    "filingDate": ["2025-02-01", "2025-05-01", "2025-07-30", "2025-08-01", "2026-02-01"],
                    "reportDate": ["2024-12-31", "2025-03-31", "2025-06-30", "2025-09-30", "2025-12-31"],
                    "form": ["10-K", "10-Q", package.form, "10-Q", "10-K"],
                    "primaryDocument": ["prior.htm", "q1.htm", package.primary_document, "q3.htm", "annual.htm"],
                }
            },
        },
        sort_keys=True,
    ).encode()
    return SecDiscoveryObservation.create(
        company=SecCompanyRef(
            cik=package.cik,
            ticker="AAPL",
            company_id=f"US:CIK{package.cik}",
            issuer_kind=SecIssuerKind.DOMESTIC,
        ),
        fiscal_year=package.fiscal_year,
        period=package.period,
        source_documents=[
            {
                "url": "https://data.sec.gov/submissions/CIK0000320193.json",
                "body": body,
            }
        ],
        candidates=(candidate,),
        selected_accession=package.accession,
        state="UNAMBIGUOUS",
        retrieved_at="2026-11-12T00:00:00+00:00",
    )


def _parse_and_validate(package: object, tmp_path: Path):
    observation = _observation(package)
    registry = SQLiteRegistry(tmp_path / "workspace" / "ingest" / "registry.sqlite")
    registry.register_sec_package(package)
    registry.register_sec_discovery_observation(observation)
    parsed = parse_sec_package(package, tmp_path / "p11", discovery_observation=observation)
    validation = validate_sec_artifacts(
        parsed,
        tmp_path / "p7",
        package=package,
        discovery_observation=observation,
        registry=registry,
    )
    return observation, parsed, validation, registry


def test_sec_p7_validation_is_source_aware_and_writes_report(tmp_path: Path) -> None:
    package = _package()
    _observation_value, parsed, validation, _registry = _parse_and_validate(package, tmp_path)
    assert validation.validation_status == "PASS"
    assert validation.blocking_issue_count == 0
    assert validation.reuse_eligible is True
    assert validation.artifact_dir == tmp_path / "p7" / package.package_sha256 / SEC_VALIDATION_SCHEMA
    assert (validation.artifact_dir / "validation.json").is_file()
    loaded = load_sec_validation(tmp_path / "p7" / package.package_sha256)
    assert loaded.artifact_dir == validation.artifact_dir


def test_sec_validation_v2_flat_files_are_not_a_v3_fallback(tmp_path: Path) -> None:
    package = _package()
    _observation_value, _parsed, validation, _registry = _parse_and_validate(package, tmp_path)
    legacy_dir = tmp_path / "legacy" / package.package_sha256
    legacy_dir.mkdir(parents=True)
    legacy_report = json.loads((validation.artifact_dir / "validation.json").read_text(encoding="utf-8"))
    legacy_report["schema_version"] = "p11-sec-validation-v2"
    (legacy_dir / "validation.json").write_text(json.dumps(legacy_report) + "\n", encoding="utf-8")
    (legacy_dir / "issues.jsonl").write_bytes((validation.artifact_dir / "issues.jsonl").read_bytes())

    with pytest.raises(Exception):
        load_sec_validation(legacy_dir)


def test_sec_validation_corrupt_v3_does_not_fall_back_to_valid_flat_v2(tmp_path: Path) -> None:
    package = _package()
    _observation_value, _parsed, validation, _registry = _parse_and_validate(package, tmp_path)
    legacy_dir = tmp_path / "legacy" / package.package_sha256
    legacy_dir.mkdir(parents=True)
    (legacy_dir / "validation.json").write_bytes((validation.artifact_dir / "validation.json").read_bytes())
    (legacy_dir / "issues.jsonl").write_bytes((validation.artifact_dir / "issues.jsonl").read_bytes())
    (validation.artifact_dir / "issues.jsonl").write_text("corrupt\n", encoding="utf-8")

    with pytest.raises(Exception):
        load_sec_validation(validation.artifact_dir)


def test_sec_p8_reads_catalog_entry_without_network(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("FFDF_P11_US_DEV", raising=False)
    package = _package()
    observation, parsed, validation, registry = _parse_and_validate(package, tmp_path)
    SecPackageStore(tmp_path / "workspace" / "ingest" / "raw-store").put(package)
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
                        "company_id": f"US:CIK{package.cik}",
                        "provider_company_id": package.cik,
                        "cik": package.cik,
                        "discovery_observation_sha256": observation.observation_sha256,
                        "discovery_checked_at": observation.retrieved_at,
                        "selected_accession": observation.selected_accession,
                        "discovery_state": observation.state,
                        "fact_source_mode": parsed.fact_source_mode,
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
    assert service.list_sections(package.package_sha256)["data"]["returned"] >= 1
    tables = service.list_tables(package.package_sha256)["data"]["tables"]
    assert tables
    table = service.get_table(package.package_sha256, tables[0]["table_id"])["data"]
    assert table["document_sha256"] == package.package_sha256
    fact_rows = service.list_raw_facts(package.package_sha256, page_no=1, metric_contains="Revenues")["data"]["facts"]
    assert fact_rows
    fact_id = fact_rows[0]["raw_fact_id"]
    assert service.get_fact(package.package_sha256, fact_id)["data"]["raw_qname"] == "us-gaap:Revenues"
    evidence_id = fact_rows[0]["evidence_id"]
    assert service.get_evidence(package.package_sha256, evidence_id)["data"]["raw_fact_id"] == fact_id
    assert service.get_validation(package.package_sha256)["data"]["report"]["validation_status"] == "PASS"


def test_sec_ingest_publishes_only_nonblocking_package(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("FFDF_P11_US_DEV", raising=False)
    package = _package()
    result = ingest_sec_package(
        package,
        root=tmp_path,
        ticker="AAPL",
        period="Q2",
        discovery_observation=_observation(package),
    )
    assert result.research_ready is True
    assert result.catalog_status == "ADDED"
    assert result.catalog_path.is_file()


def test_periodic_zero_facts_is_review_required_and_not_research_ready(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("FFDF_P11_US_DEV", "1")
    package = _empty_periodic_package()
    observation, parsed, validation, _registry = _parse_and_validate(package, tmp_path)

    assert not parsed.facts
    assert validation.validation_status == "REVIEW_REQUIRED"
    assert any(issue["code"] == "P11_STRUCTURED_FACTS_MISSING" for issue in validation.issues)
    result = ingest_sec_package(
        package,
        root=tmp_path,
        ticker="AAPL",
        period="Q2",
        discovery_observation=observation,
    )
    assert result.research_ready is False
    assert result.catalog_status != "ADDED"
    assert validation.compatibility_status == "COMPATIBLE"
    assert validation.reuse_eligible is False


def test_facts_without_evidence_are_blocked(tmp_path: Path) -> None:
    package = _package()
    parsed = parse_sec_package(package, tmp_path / "p11")
    from dataclasses import replace

    validation = validate_sec_artifacts(replace(parsed, evidence=()), tmp_path / "p7", package=package)

    assert validation.validation_status == "BLOCKED"
    assert validation.blocking_issue_count > 0


@pytest.mark.parametrize("tamper", ["member", "delete", "manifest"])
def test_p8_revalidates_raw_sec_package_before_serving(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    tamper: str,
) -> None:
    monkeypatch.setenv("FFDF_P11_US_DEV", "1")
    package = _package()
    observation, parsed, validation, registry = _parse_and_validate(package, tmp_path)
    store = SecPackageStore(tmp_path / "workspace" / "ingest" / "raw-store")
    package_dir = store.put(package)
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
                        "ticker": "AAPL",
                        "company_id": f"US:CIK{package.cik}",
                        "provider_company_id": package.cik,
                        "cik": package.cik,
                        "discovery_observation_sha256": observation.observation_sha256,
                        "discovery_checked_at": observation.retrieved_at,
                        "selected_accession": observation.selected_accession,
                        "discovery_state": observation.state,
                        "fact_source_mode": parsed.fact_source_mode,
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
    service = McpQueryService(McpCatalog.load(tmp_path, catalog_path))
    fact_id = parsed.facts[0]["raw_fact_id"]
    assert service.get_fact(package.package_sha256, fact_id)["data"]["raw_fact_id"] == fact_id

    member_path = package_dir / "members" / "example.htm"
    if tamper == "member":
        member_path.write_bytes(b"changed")
    elif tamper == "delete":
        member_path.unlink()
    else:
        manifest = json.loads((package_dir / "manifest.json").read_text(encoding="utf-8"))
        manifest["package_sha256"] = "0" * 64
        (package_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(McpServiceError) as error:
        service.get_evidence(package.package_sha256, parsed.evidence[0]["evidence_id"])
    assert error.value.reason_code == "P8_UPSTREAM_ARTIFACT_INVALID"

