from __future__ import annotations

import base64
import json
import sqlite3
from dataclasses import replace
from pathlib import Path

import pytest

from financial_filing_data_foundation.mcp.catalog import CatalogError, McpCatalog
from financial_filing_data_foundation.mcp.service import McpQueryService, McpServiceError
from financial_filing_data_foundation.registry import SQLiteRegistry
from financial_filing_data_foundation.us_sec.discovery import SecDiscoveryObservation
from financial_filing_data_foundation.us_sec.ingest import ingest_sec_package, reuse_sec_package
from financial_filing_data_foundation.us_sec.models import (
    SecCompanyRef,
    SecFilingCandidate,
    SecIssuerKind,
)
from financial_filing_data_foundation.us_sec.package import (
    SecMemberRole,
    SecPackageMember,
    build_package,
)
from financial_filing_data_foundation.us_sec.parser import parse_sec_package
from financial_filing_data_foundation.us_sec.path_policy import archive_member_url
from financial_filing_data_foundation.us_sec.validation import validate_sec_artifacts


CIK = "0000320193"
ACCESSION = "0000320193-25-000001"
SOURCE_URL = "https://data.sec.gov/submissions/CIK0000320193.json"


def _package(*, accession: str = ACCESSION):
    return build_package(
        cik=CIK,
        accession=accession,
        form="10-Q",
        fiscal_year=2025,
        period="Q2",
        members=(
            SecPackageMember(
                relative_name="example.htm",
                role=SecMemberRole.PRIMARY_DOCUMENT,
                content_type="text/html",
                source_url=archive_member_url(CIK, accession, "example.htm"),
                body=(
                    b"<html xmlns:ix='http://www.xbrl.org/2013/inlineXBRL' xmlns:xbrli='http://www.xbrl.org/2003/instance' xmlns:us-gaap='http://fasb.org/us-gaap/2025'><body><ix:header>"
                    b"<xbrli:context id='c1'><xbrli:entity><xbrli:identifier>0000320193</xbrli:identifier>"
                    b"</xbrli:entity><xbrli:period><xbrli:instant>2025-06-30</xbrli:instant>"
                    b"</xbrli:period></xbrli:context>"
                    b"<xbrli:unit id='USD'><xbrli:measure>iso4217:USD</xbrli:measure></xbrli:unit>"
                    b"</ix:header><h1>Revenue</h1><p><ix:nonfraction name='us-gaap:Revenues' "
                    b"contextRef='c1' unitRef='USD' decimals='0'>100</ix:nonfraction></p>"
                    b"</body></html>"
                ),
            ),
        ),
    )


def _candidate(*, accession: str = ACCESSION) -> SecFilingCandidate:
    return SecFilingCandidate(
        cik=CIK,
        ticker="AAPL",
        accession=accession,
        normalized_accession=accession.replace("-", ""),
        form="10-Q",
        filing_date="2025-07-30",
        report_period="2025-06-30",
        primary_document="example.htm",
        source_url=archive_member_url(CIK, accession, "example.htm"),
        amended=False,
        issuer_kind=SecIssuerKind.DOMESTIC,
    )


def _observation(
    *,
    state: str = "UNAMBIGUOUS",
    selected_accession: str | None = ACCESSION,
) -> SecDiscoveryObservation:
    body = json.dumps(
        {
            "cik": CIK,
            "fiscalYearEnd": "1231",
            "filings": {
                "recent": {
                    "accessionNumber": [
                        "0000320193-24-000100",
                        "0000320193-25-000100",
                        ACCESSION,
                        "0000320193-25-000101",
                        "0000320193-25-000102",
                    ],
                    "filingDate": ["2025-02-01", "2025-05-01", "2025-07-30", "2025-08-01", "2026-02-01"],
                    "reportDate": ["2024-12-31", "2025-03-31", "2025-06-30", "2025-09-30", "2025-12-31"],
                    "form": ["10-K", "10-Q", "10-Q", "10-Q", "10-K"],
                    "primaryDocument": ["prior.htm", "q1.htm", "example.htm", "q3.htm", "annual.htm"],
                }
            },
        },
        sort_keys=True,
    ).encode()
    return SecDiscoveryObservation.create(
        company=SecCompanyRef(
            cik=CIK,
            ticker="AAPL",
            company_id=f"US:CIK{CIK}",
            issuer_kind=SecIssuerKind.DOMESTIC,
        ),
        fiscal_year=2025,
        period="Q2",
        source_documents=[{"url": SOURCE_URL, "body": body}],
        candidates=(_candidate(),),
        selected_accession=selected_accession,
        state=state,
        retrieved_at="2026-11-12T00:00:00+00:00",
    )


def _validated(tmp_path: Path):
    package = _package()
    observation = _observation()
    registry = SQLiteRegistry(tmp_path / "workspace" / "ingest" / "registry.sqlite")
    registry.register_sec_package(package)
    registry.register_sec_discovery_observation(observation)
    parsed = parse_sec_package(package, tmp_path / "workspace" / "ingest" / "us" / "p11", discovery_observation=observation)
    validation = validate_sec_artifacts(
        parsed,
        tmp_path / "workspace" / "ingest" / "us" / "p7",
        package=package,
        discovery_observation=observation,
        registry=registry,
    )
    return package, observation, parsed, validation


def test_t131_01_missing_discovery_observation_blocks_p7_and_reuse(tmp_path: Path) -> None:
    package = _package()
    parsed = parse_sec_package(package, tmp_path / "p11")
    validation = validate_sec_artifacts(parsed, tmp_path / "p7", package=package)

    assert validation.validation_status != "PASS"
    assert validation.reuse_eligible is False


def test_t131_02_ingest_without_observation_is_not_research_ready(tmp_path: Path) -> None:
    result = ingest_sec_package(_package(), root=tmp_path, ticker="AAPL", period="Q2")

    assert result.research_ready is False
    assert result.catalog_status != "ADDED"


def test_t131_03_reuse_without_observation_is_not_research_ready(tmp_path: Path) -> None:
    observation = _observation()
    first = ingest_sec_package(
        _package(),
        root=tmp_path,
        ticker="AAPL",
        period="Q2",
        discovery_observation=observation,
    )

    reused = reuse_sec_package(
        first.package,
        root=tmp_path,
        ticker="AAPL",
        period="Q2",
        parsed_artifact_dir=first.parsed.artifact_dir,
        discovery_observation=None,
    )

    assert reused.research_ready is False


def test_t131_04_catalog_missing_discovery_fields_fails_closed(tmp_path: Path) -> None:
    result = ingest_sec_package(
        _package(),
        root=tmp_path,
        ticker="AAPL",
        period="Q2",
        discovery_observation=_observation(),
    )
    catalog_path = result.catalog_path
    payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    payload["documents"][0].pop("discovery_state")
    catalog_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(CatalogError):
        McpCatalog.load(tmp_path, catalog_path)


def test_t131_05_fake_observation_sha_is_rejected(tmp_path: Path) -> None:
    package, observation, parsed, _ = _validated(tmp_path)
    tampered = replace(observation, observation_sha256="0" * 64)

    validation = validate_sec_artifacts(
        parsed,
        tmp_path / "p7-tampered",
        package=package,
        discovery_observation=tampered,
        registry=SQLiteRegistry(tmp_path / "workspace" / "ingest" / "registry.sqlite"),
    )

    assert validation.validation_status != "PASS"


def test_t131_06_source_bytes_hash_mismatch_is_rejected(tmp_path: Path) -> None:
    package, observation, parsed, _ = _validated(tmp_path)
    tampered_source = dict(observation.source_documents[0])
    tampered_source["body_b64"] = base64.b64encode(b"tampered source bytes").decode("ascii")
    tampered = replace(observation, source_documents=(tampered_source,))

    validation = validate_sec_artifacts(
        parsed,
        tmp_path / "p7-tampered",
        package=package,
        discovery_observation=tampered,
        registry=SQLiteRegistry(tmp_path / "workspace" / "ingest" / "registry.sqlite"),
    )

    assert validation.validation_status != "PASS"


def test_t131_07_candidate_fingerprint_mismatch_is_rejected(tmp_path: Path) -> None:
    package, observation, parsed, _ = _validated(tmp_path)
    candidate = dict(observation.candidates[0])
    candidate["filing_date"] = "2025-08-01"
    tampered = replace(observation, candidates=(candidate,))

    validation = validate_sec_artifacts(
        parsed,
        tmp_path / "p7-tampered",
        package=package,
        discovery_observation=tampered,
        registry=SQLiteRegistry(tmp_path / "workspace" / "ingest" / "registry.sqlite"),
    )

    assert validation.validation_status != "PASS"


def test_t131_08_canonical_observation_sha_mismatch_is_rejected(tmp_path: Path) -> None:
    package, observation, parsed, _ = _validated(tmp_path)
    tampered = replace(observation, retrieved_at="2026-11-12T00:00:01+00:00")

    validation = validate_sec_artifacts(
        parsed,
        tmp_path / "p7-tampered",
        package=package,
        discovery_observation=tampered,
        registry=SQLiteRegistry(tmp_path / "workspace" / "ingest" / "registry.sqlite"),
    )

    assert validation.validation_status != "PASS"


def test_t131_09_slot_identity_mismatch_is_rejected(tmp_path: Path) -> None:
    package, observation, parsed, _ = _validated(tmp_path)
    tampered = replace(observation, company_id="US:CIK0000000000")

    validation = validate_sec_artifacts(
        parsed,
        tmp_path / "p7-tampered",
        package=package,
        discovery_observation=tampered,
        registry=SQLiteRegistry(tmp_path / "workspace" / "ingest" / "registry.sqlite"),
    )

    assert validation.validation_status != "PASS"


def test_t131_10_missing_selected_accession_is_rejected(tmp_path: Path) -> None:
    package, observation, parsed, _ = _validated(tmp_path)
    tampered = replace(observation, selected_accession=None)

    validation = validate_sec_artifacts(
        parsed,
        tmp_path / "p7-tampered",
        package=package,
        discovery_observation=tampered,
        registry=SQLiteRegistry(tmp_path / "workspace" / "ingest" / "registry.sqlite"),
    )

    assert validation.validation_status != "PASS"


def test_t131_11_non_unambiguous_state_is_not_research_ready(tmp_path: Path) -> None:
    package = _package()
    observation = _observation(state="NOT_FOUND", selected_accession=None)
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

    assert validation.validation_status != "PASS"
    assert validation.reuse_eligible is False


def test_t131_12_ticker_only_company_identity_is_rejected_from_p8(tmp_path: Path) -> None:
    result = ingest_sec_package(
        _package(),
        root=tmp_path,
        ticker="AAPL",
        period="Q2",
        discovery_observation=_observation(),
    )
    payload = json.loads(result.catalog_path.read_text(encoding="utf-8"))
    payload["documents"][0]["company_id"] = "US:AAPL"
    result.catalog_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(CatalogError):
        McpCatalog.load(tmp_path, result.catalog_path)


def test_t131_13_valid_observation_registry_package_and_catalog_serve(tmp_path: Path) -> None:
    result = ingest_sec_package(
        _package(),
        root=tmp_path,
        ticker="AAPL",
        period="Q2",
        discovery_observation=_observation(),
    )

    assert result.validation.validation_status == "PASS"
    assert result.research_ready is True
    assert result.catalog_status == "ADDED"
    service = McpQueryService(McpCatalog.load(tmp_path, result.catalog_path))
    detail = service.get_document(result.package.package_sha256)
    assert detail["data"]["validation_status"] == "PASS"
    assert detail["data"]["company_id"] == f"US:CIK{CIK}"


def test_t131_p8_missing_registry_observation_fails_closed(tmp_path: Path) -> None:
    result = ingest_sec_package(
        _package(),
        root=tmp_path,
        ticker="AAPL",
        period="Q2",
        discovery_observation=_observation(),
    )
    with sqlite3.connect(tmp_path / "workspace" / "ingest" / "registry.sqlite") as conn:
        conn.execute("DELETE FROM sec_discovery_observations")
        conn.commit()

    service = McpQueryService(McpCatalog.load(tmp_path, result.catalog_path))
    with pytest.raises(McpServiceError):
        service.get_document(result.package.package_sha256)


def test_t131_p8_registry_source_bytes_tamper_fails_closed(tmp_path: Path) -> None:
    result = ingest_sec_package(
        _package(),
        root=tmp_path,
        ticker="AAPL",
        period="Q2",
        discovery_observation=_observation(),
    )
    service = McpQueryService(McpCatalog.load(tmp_path, result.catalog_path))
    service.get_document(result.package.package_sha256)

    with sqlite3.connect(tmp_path / "workspace" / "ingest" / "registry.sqlite") as conn:
        row = conn.execute(
            "SELECT observation_sha256, source_documents_json FROM sec_discovery_observations"
        ).fetchone()
        assert row is not None
        sources = json.loads(row[1])
        sources[0]["body_b64"] = base64.b64encode(b"tampered Registry bytes").decode("ascii")
        conn.execute(
            "UPDATE sec_discovery_observations SET source_documents_json = ? WHERE observation_sha256 = ?",
            (json.dumps(sources), row[0]),
        )
        conn.commit()

    with pytest.raises(McpServiceError):
        service.get_document(result.package.package_sha256)
