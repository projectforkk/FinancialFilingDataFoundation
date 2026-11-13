from __future__ import annotations

import base64
import json
import sqlite3
from dataclasses import replace
from pathlib import Path

import pytest

from financial_filing_data_foundation.mcp.catalog import McpCatalog
from financial_filing_data_foundation.mcp.service import McpQueryService, McpServiceError
from financial_filing_data_foundation.us_sec.acquisition import (
    SecAcquirer,
    _candidate_from_record,
    _member_role,
)
from financial_filing_data_foundation.us_sec.discovery import (
    SecDiscoveryObservation,
    discover_filings,
    parse_submissions,
    verify_sec_discovery_observation,
)
from financial_filing_data_foundation.us_sec.errors import P11Reason, SecError
from financial_filing_data_foundation.us_sec.http import SecResponse
from financial_filing_data_foundation.us_sec.ingest import ingest_sec_package
from financial_filing_data_foundation.us_sec.models import SecCompanyRef, SecIssuerKind
from financial_filing_data_foundation.us_sec.package import (
    SecMemberRole,
    SecPackageMember,
    SecPackageStore,
    build_package,
)
from financial_filing_data_foundation.us_sec.parser import parse_sec_package
from financial_filing_data_foundation.us_sec.path_policy import archive_member_url
from financial_filing_data_foundation.us_sec.validation import validate_sec_artifacts
from financial_filing_data_foundation.user_cli import _parser, _validate_market_period


CIK = "0000320193"
COMPANY_ID = f"US:CIK{CIK}"
MAIN_URL = f"https://data.sec.gov/submissions/CIK{CIK}.json"
HISTORY_NAME = f"CIK{CIK}-submissions-001.json"
HISTORY_URL = f"https://data.sec.gov/submissions/{HISTORY_NAME}"
ACCESSION = "0000320193-25-000001"
AMENDED_ACCESSION = "0000320193-25-000002"


def _company() -> SecCompanyRef:
    return SecCompanyRef(
        cik=CIK,
        ticker="AAPL",
        company_id=COMPANY_ID,
        issuer_kind=SecIssuerKind.DOMESTIC,
    )


def _submission_row(
    accession: str,
    *,
    form: str = "10-K",
    filing_date: str = "2025-11-01",
    report_date: str = "2025-09-27",
    primary_document: str = "aapl-20250927.htm",
) -> dict[str, str]:
    return {
        "accessionNumber": accession,
        "form": form,
        "filingDate": filing_date,
        "reportDate": report_date,
        "primaryDocument": primary_document,
    }


def _submissions_payload(
    rows: list[dict[str, str]],
    *,
    history_files: list[dict[str, str]] | None = None,
) -> bytes:
    recent = {
        "accessionNumber": [row["accessionNumber"] for row in rows],
        "form": [row["form"] for row in rows],
        "filingDate": [row["filingDate"] for row in rows],
        "reportDate": [row["reportDate"] for row in rows],
        "primaryDocument": [row["primaryDocument"] for row in rows],
    }
    payload = {
        "cik": "320193",
        "fiscalYearEnd": "0930",
        "filings": {"recent": recent, "files": history_files or []},
    }
    return json.dumps(payload, sort_keys=True).encode("utf-8")


def _observation_from_bytes(
    main_body: bytes,
    *,
    history_body: bytes | None = None,
    candidates: tuple[object, ...] | None = None,
    state: str = "UNAMBIGUOUS",
    selected_accession: str | None = ACCESSION,
    period: str = "FY",
) -> SecDiscoveryObservation:
    source_documents: list[dict[str, object]] = [{"url": MAIN_URL, "body": main_body}]
    if history_body is not None:
        source_documents.append({"url": HISTORY_URL, "body": history_body})
    submissions = parse_submissions(main_body and json.loads(main_body), company=_company(), source_url=MAIN_URL)
    discovered = discover_filings(submissions, fiscal_year=2025, period=period)
    candidate_objects = (
        tuple(_candidate_from_record(row, _company()) for row in candidates)
        if candidates is not None
        else discovered
    )
    return SecDiscoveryObservation.create(
        company=_company(),
        fiscal_year=2025,
        period=period,
        source_documents=source_documents,
        candidates=candidate_objects,
        selected_accession=selected_accession,
        state=state,
        retrieved_at="2026-11-13T00:00:00+00:00",
    )


def test_t135_01_official_source_bytes_are_reparsed_not_only_rehashed() -> None:
    main_body = _submissions_payload([_submission_row(ACCESSION)])
    observation = _observation_from_bytes(main_body)
    empty_body = _submissions_payload([])
    forged = _observation_from_bytes(empty_body, candidates=observation.candidates)

    with pytest.raises(SecError) as exc_info:
        verify_sec_discovery_observation(forged)

    assert exc_info.value.reason_code in {
        P11Reason.P11_PROVENANCE_MISMATCH.value,
        P11Reason.P11_DISCOVERY_FRESHNESS_UNKNOWN.value,
    }


def test_t135_02_source_url_must_be_the_official_submissions_endpoint() -> None:
    main_body = _submissions_payload([_submission_row(ACCESSION)])
    observation = _observation_from_bytes(main_body)
    source = dict(observation.source_documents[0])
    source["url"] = "https://www.sec.gov/files/not-submissions.json"
    forged = replace(observation, source_documents=(source,))

    with pytest.raises(SecError):
        verify_sec_discovery_observation(forged)


def test_t135_03_state_and_selected_accession_are_derived_from_candidates() -> None:
    main_body = _submissions_payload([_submission_row(ACCESSION)])
    forged = _observation_from_bytes(
        main_body,
        selected_accession=AMENDED_ACCESSION,
    )

    with pytest.raises(SecError):
        verify_sec_discovery_observation(forged)


def test_t135_04_candidate_form_is_bound_to_reconstructed_filing() -> None:
    main_body = _submissions_payload([_submission_row(ACCESSION)])
    observation = _observation_from_bytes(main_body)
    candidate = dict(observation.candidates[0])
    candidate["form"] = "10-Q"
    forged = SecDiscoveryObservation.create(
        company=_company(),
        fiscal_year=2025,
        period="FY",
        source_documents=[{"url": MAIN_URL, "body": main_body}],
        candidates=(),
        selected_accession=ACCESSION,
        state="UNAMBIGUOUS",
        retrieved_at=observation.retrieved_at,
    )
    forged = replace(forged, candidates=(candidate,))

    with pytest.raises(SecError):
        verify_sec_discovery_observation(forged)


def test_t135_05_missing_official_history_source_is_not_accepted() -> None:
    main_body = _submissions_payload(
        [_submission_row(ACCESSION)],
        history_files=[{"name": HISTORY_NAME, "filingFrom": "2020-01-01", "filingTo": "2025-12-31"}],
    )
    observation = _observation_from_bytes(main_body)

    with pytest.raises(SecError):
        verify_sec_discovery_observation(observation)


def test_t135_06_extra_source_document_is_not_accepted() -> None:
    main_body = _submissions_payload([_submission_row(ACCESSION)])
    observation = _observation_from_bytes(main_body)
    extra = {"url": HISTORY_URL, "body": _submissions_payload([])}
    forged = replace(observation, source_documents=observation.source_documents + (extra,))

    with pytest.raises(SecError):
        verify_sec_discovery_observation(forged)


def test_t135_07_valid_observation_passes_independent_reconstruction() -> None:
    main_body = _submissions_payload([_submission_row(ACCESSION)])
    observation = _observation_from_bytes(main_body)

    verify_sec_discovery_observation(observation)


def test_t135_08_candidate_fingerprint_cannot_replace_source_reconstruction() -> None:
    main_body = _submissions_payload([_submission_row(ACCESSION)])
    observation = _observation_from_bytes(main_body)
    forged = replace(observation, candidates=())

    with pytest.raises(SecError):
        verify_sec_discovery_observation(forged)


def test_t135_09_registry_identity_remains_an_independent_binding(tmp_path: Path) -> None:
    main_body = _submissions_payload([_submission_row(ACCESSION)])
    observation = _observation_from_bytes(main_body)
    registry_row = {
        "observation_sha256": observation.observation_sha256,
        "company_id": observation.company_id,
        "cik": observation.cik,
        "fiscal_year": observation.fiscal_year,
        "raw_fiscal_period": observation.period,
        "retrieved_at": observation.retrieved_at,
        "source_documents_json": json.dumps(list(observation.source_documents)),
        "candidates_json": json.dumps(list(observation.candidates)),
        "candidate_fingerprint": observation.candidate_fingerprint,
        "selected_accession": observation.selected_accession,
        "state": observation.state,
        "artifact_path": observation.artifact_path,
    }
    registry_row["candidates_json"] = json.dumps([])

    with pytest.raises(SecError):
        verify_sec_discovery_observation(observation, registry_row=registry_row)


def test_t135_10_package_identity_is_checked_against_reconstructed_candidate() -> None:
    main_body = _submissions_payload([_submission_row(ACCESSION)])
    observation = _observation_from_bytes(main_body)
    package = build_package(
        cik=CIK,
        accession=ACCESSION,
        form="10-Q",
        fiscal_year=2025,
        period="FY",
        members=(
            SecPackageMember(
                relative_name="aapl-20250927.htm",
                role=SecMemberRole.PRIMARY_DOCUMENT,
                content_type="text/html",
                source_url=archive_member_url(CIK, ACCESSION, "aapl-20250927.htm"),
                body=b"<html><body>Annual</body></html>",
            ),
        ),
    )

    with pytest.raises(SecError):
        verify_sec_discovery_observation(observation, package=package)


def test_t135_11_invalid_fact_source_mode_is_blocking_in_p7(tmp_path: Path) -> None:
    observation = _observation_from_bytes(_q2_submissions_body(), period="Q2")
    package = _html_package(
        _inline_html(
            "<ix:header><xbrli:context id='c1'><xbrli:entity><xbrli:identifier>1</xbrli:identifier></xbrli:entity><xbrli:period><xbrli:instant>2025-06-30</xbrli:instant></xbrli:period></xbrli:context><xbrli:unit id='USD'><xbrli:measure>USD</xbrli:measure></xbrli:unit></ix:header>"
            "<h1>Revenue</h1><p><ix:nonfraction name='us-gaap:Revenue' contextRef='c1' unitRef='USD'>100</ix:nonfraction></p>"
        )
    )
    parsed = parse_sec_package(package, tmp_path / "p11", discovery_observation=observation)

    validation = validate_sec_artifacts(
        replace(parsed, fact_source_mode="INVALID"),
        tmp_path / "p7",
        package=package,
        discovery_observation=observation,
    )

    assert validation.validation_status == "BLOCKED"
    assert any(issue["code"] == P11Reason.P11_FACT_SOURCE_MODE_INVALID.value for issue in validation.issues)


def test_t135_12_no_structured_mode_cannot_claim_persisted_facts(tmp_path: Path) -> None:
    observation = _observation_from_bytes(_q2_submissions_body(), period="Q2")
    package = _html_package(
        _inline_html(
            "<ix:header><xbrli:context id='c1'><xbrli:entity><xbrli:identifier>1</xbrli:identifier></xbrli:entity><xbrli:period><xbrli:instant>2025-06-30</xbrli:instant></xbrli></period></xbrli:context><xbrli:unit id='USD'><xbrli:measure>USD</xbrli:measure></xbrli:unit></ix:header>"
            "<p><ix:nonfraction name='us-gaap:Revenue' contextRef='c1' unitRef='USD'>100</ix:nonfraction></p>"
        )
    )
    parsed = parse_sec_package(package, tmp_path / "p11", discovery_observation=observation)

    validation = validate_sec_artifacts(
        replace(parsed, fact_source_mode="NO_STRUCTURED_FACTS"),
        tmp_path / "p7",
        package=package,
        discovery_observation=observation,
    )

    assert validation.validation_status == "BLOCKED"
    assert any(issue["code"] == P11Reason.P11_FACT_SOURCE_MODE_INVALID.value for issue in validation.issues)


class _DiscoveryClient:
    def __init__(self, bodies: dict[str, bytes]) -> None:
        self.bodies = bodies
        self.calls: list[str] = []
        self.config = type("Config", (), {"submissions_max_bytes": 1024 * 1024, "member_max_bytes": 1024 * 1024})()

    def fetch(self, url: str, **_: object) -> SecResponse:
        self.calls.append(url)
        return SecResponse(200, {"Content-Type": "application/json"}, self.bodies[url], url)


def test_t136_01_all_listed_history_chunks_are_processed_after_current_match(tmp_path: Path) -> None:
    main_body = _submissions_payload(
        [_submission_row(ACCESSION)],
        history_files=[{"name": HISTORY_NAME, "filingFrom": "2030-01-01", "filingTo": "2030-12-31"}],
    )
    history_body = _submissions_payload([_submission_row(AMENDED_ACCESSION, form="10-K/A", filing_date="2025-11-02")])
    client = _DiscoveryClient({MAIN_URL: main_body, HISTORY_URL: history_body})
    acquirer = SecAcquirer(client, SecPackageStore(tmp_path / "raw"), discovery_root=tmp_path / "discovery")

    observation, candidates = acquirer._discover_with_candidates(_company(), fiscal_year=2025, period="FY")

    assert HISTORY_URL in client.calls
    assert {row.accession for row in candidates} == {ACCESSION, AMENDED_ACCESSION}
    assert observation.state == "AMENDED_VARIANT_PRESENT"


def test_t136_02_history_enumeration_is_deterministic_and_includes_missing_ranges(tmp_path: Path) -> None:
    names = [
        "CIK0000320193-submissions-002.json",
        "CIK0000320193-submissions-001.json",
    ]
    main_body = _submissions_payload(
        [],
        history_files=[{"name": names[0]}, {"name": names[1], "filingFrom": "2020-01-01", "filingTo": "2020-12-31"}],
    )
    bodies = {MAIN_URL: main_body}
    for name in names:
        bodies[f"https://data.sec.gov/submissions/{name}"] = _submissions_payload([])
    client = _DiscoveryClient(bodies)
    acquirer = SecAcquirer(client, SecPackageStore(tmp_path / "raw"), discovery_root=tmp_path / "discovery")

    acquirer._discover_with_candidates(_company(), fiscal_year=2025, period="FY")

    assert client.calls[1:] == [
        "https://data.sec.gov/submissions/CIK0000320193-submissions-001.json",
        "https://data.sec.gov/submissions/CIK0000320193-submissions-002.json",
    ]


def test_t136_03_malformed_history_range_fails_closed_even_if_current_has_match(tmp_path: Path) -> None:
    main_body = _submissions_payload(
        [_submission_row(ACCESSION)],
        history_files=[{"name": HISTORY_NAME, "filingFrom": "not-a-date", "filingTo": "2030-12-31"}],
    )
    client = _DiscoveryClient({MAIN_URL: main_body, HISTORY_URL: _submissions_payload([])})
    acquirer = SecAcquirer(client, SecPackageStore(tmp_path / "raw"), discovery_root=tmp_path / "discovery")

    with pytest.raises(SecError):
        acquirer._discover_with_candidates(_company(), fiscal_year=2025, period="FY")


def test_t136_04_duplicate_accessions_with_conflicting_metadata_fail_closed(tmp_path: Path) -> None:
    main_body = _submissions_payload(
        [_submission_row(ACCESSION)],
        history_files=[{"name": HISTORY_NAME}],
    )
    history_body = _submissions_payload([_submission_row(ACCESSION, filing_date="2025-11-03")])
    client = _DiscoveryClient({MAIN_URL: main_body, HISTORY_URL: history_body})
    acquirer = SecAcquirer(client, SecPackageStore(tmp_path / "raw"), discovery_root=tmp_path / "discovery")
    with pytest.raises(SecError):
        acquirer._discover_with_candidates(_company(), fiscal_year=2025, period="FY")


def test_t136_05_history_source_set_is_retained_for_reverification(tmp_path: Path) -> None:
    main_body = _submissions_payload(
        [],
        history_files=[{"name": HISTORY_NAME}],
    )
    history_body = _submissions_payload([_submission_row(ACCESSION)])
    client = _DiscoveryClient({MAIN_URL: main_body, HISTORY_URL: history_body})
    acquirer = SecAcquirer(client, SecPackageStore(tmp_path / "raw"), discovery_root=tmp_path / "discovery")

    observation, _ = acquirer._discover_with_candidates(_company(), fiscal_year=2025, period="FY")

    assert [row["url"] for row in observation.source_documents] == [MAIN_URL, HISTORY_URL]
    verify_sec_discovery_observation(observation)


def test_t136_06_history_chunks_have_a_deterministic_bound(tmp_path: Path) -> None:
    files = [{"name": f"CIK{CIK}-submissions-{index:03d}.json"} for index in range(300)]
    main_body = _submissions_payload([], history_files=files)
    bodies = {MAIN_URL: main_body}
    for item in files:
        bodies[f"https://data.sec.gov/submissions/{item['name']}"] = _submissions_payload([])
    client = _DiscoveryClient(bodies)
    acquirer = SecAcquirer(client, SecPackageStore(tmp_path / "raw"), discovery_root=tmp_path / "discovery")

    with pytest.raises(SecError):
        acquirer._discover_with_candidates(_company(), fiscal_year=2025, period="FY")


def _q2_submissions_body() -> bytes:
    return _submissions_payload(
        [
            _submission_row("0000320193-24-000001", filing_date="2024-11-01", report_date="2024-09-28"),
            _submission_row("0000320193-25-000010", form="10-Q", filing_date="2025-05-01", report_date="2025-03-29"),
            _submission_row(ACCESSION, form="10-Q", filing_date="2025-08-01", report_date="2025-06-30", primary_document="aapl.htm"),
        ]
    )


def _inline_html(body: str) -> bytes:
    return (
        "<html xmlns:ix='http://www.xbrl.org/2013/inlineXBRL' "
        "xmlns:i='http://www.xbrl.org/2013/inlineXBRL' "
        "xmlns:xbrli='http://www.xbrl.org/2003/instance' "
        "xmlns:xbrldi='http://xbrl.org/2006/xbrldi' "
        "xmlns:us-gaap='http://fasb.org/us-gaap/2024' "
        "xmlns:ex='http://example.test/ex'><body>"
        + body
        + "</body></html>"
    ).encode()


def _html_package(body: bytes, *, form: str = "10-Q", period: str = "Q2"):
    return build_package(
        cik=CIK,
        accession=ACCESSION,
        form=form,
        fiscal_year=2025,
        period=period,
        members=(
            SecPackageMember(
                relative_name="aapl.htm",
                role=SecMemberRole.PRIMARY_DOCUMENT,
                content_type="text/html",
                source_url=archive_member_url(CIK, ACCESSION, "aapl.htm"),
                body=body,
            ),
        ),
    )


def _ingested_sec_fixture(tmp_path: Path):
    body = _q2_submissions_body()
    observation = _observation_from_bytes(body, period="Q2")
    package = _html_package(
        _inline_html(
            "<ix:header><xbrli:context id='c1'><xbrli:entity><xbrli:identifier>1</xbrli:identifier></xbrli:entity><xbrli:period><xbrli:instant>2025-06-30</xbrli:instant></xbrli:period></xbrli:context><xbrli:unit id='USD'><xbrli:measure>USD</xbrli:measure></xbrli:unit></ix:header>"
            "<h1>Revenue</h1><p><ix:nonfraction name='us-gaap:Revenue' contextRef='c1' unitRef='USD'>100</ix:nonfraction></p>"
        )
    )
    result = ingest_sec_package(
        package,
        root=tmp_path,
        ticker="AAPL",
        period="Q2",
        discovery_observation=observation,
    )
    return result


def test_t137_01_company_context_summary_uses_the_verified_sec_bundle(tmp_path: Path) -> None:
    result = _ingested_sec_fixture(tmp_path)
    service = McpQueryService(McpCatalog.load(tmp_path, result.catalog_path))

    summary = service.get_document_summary_internal(result.package.package_sha256)

    assert summary["validation_status"] == "PASS"
    assert summary["raw_fact_count"] == 1


def test_t137_02_company_context_rejects_registry_source_tamper(tmp_path: Path) -> None:
    result = _ingested_sec_fixture(tmp_path)
    service = McpQueryService(McpCatalog.load(tmp_path, result.catalog_path))
    service.get_document_summary_internal(result.package.package_sha256)
    registry_path = tmp_path / "workspace" / "ingest" / "registry.sqlite"
    with sqlite3.connect(registry_path) as conn:
        row = conn.execute("SELECT observation_sha256, source_documents_json FROM sec_discovery_observations").fetchone()
        assert row is not None
        sources = json.loads(row[1])
        sources[0]["body_b64"] = base64.b64encode(b"tampered source").decode("ascii")
        conn.execute(
            "UPDATE sec_discovery_observations SET source_documents_json = ? WHERE observation_sha256 = ?",
            (json.dumps(sources), row[0]),
        )
        conn.commit()

    with pytest.raises(McpServiceError):
        service.get_document_summary_internal(result.package.package_sha256)


def test_t137_03_cached_company_context_reverifies_before_return(tmp_path: Path) -> None:
    result = _ingested_sec_fixture(tmp_path)
    service = McpQueryService(McpCatalog.load(tmp_path, result.catalog_path))
    service.get_document_summary_internal(result.package.package_sha256)
    registry_path = tmp_path / "workspace" / "ingest" / "registry.sqlite"
    with sqlite3.connect(registry_path) as conn:
        conn.execute(
            "UPDATE sec_discovery_observations SET state = ?",
            ("SLOT_CANDIDATE_CONFLICT",),
        )
        conn.commit()

    with pytest.raises(McpServiceError):
        service.get_document_summary_internal(result.package.package_sha256)


def test_t137_04_summary_and_document_paths_share_sec_identity(tmp_path: Path) -> None:
    result = _ingested_sec_fixture(tmp_path)
    service = McpQueryService(McpCatalog.load(tmp_path, result.catalog_path))

    summary = service.get_document_summary_internal(result.package.package_sha256)
    detail = service.get_document(result.package.package_sha256)

    assert summary["document_sha256"] == detail["data"]["document_sha256"]
    assert summary["blocking_issue_count"] == detail["data"]["blocking_issue_count"]


def test_t137_05_missing_registry_observation_blocks_company_context(tmp_path: Path) -> None:
    result = _ingested_sec_fixture(tmp_path)
    with sqlite3.connect(tmp_path / "workspace" / "ingest" / "registry.sqlite") as conn:
        conn.execute("DELETE FROM sec_discovery_observations")
        conn.commit()
    service = McpQueryService(McpCatalog.load(tmp_path, result.catalog_path))

    with pytest.raises(McpServiceError):
        service.get_document_summary_internal(result.package.package_sha256)


def test_t137_06_catalog_summary_cannot_bypass_verified_raw_package(tmp_path: Path) -> None:
    result = _ingested_sec_fixture(tmp_path)
    package_dir = result.package.package_sha256[:2]
    raw_manifest = next((tmp_path / "workspace" / "ingest" / "raw-store" / "packages" / "sha256" / package_dir / result.package.package_sha256).glob("manifest.json"))
    raw = json.loads(raw_manifest.read_text(encoding="utf-8"))
    raw["accession"] = AMENDED_ACCESSION
    raw_manifest.write_text(json.dumps(raw), encoding="utf-8")
    service = McpQueryService(McpCatalog.load(tmp_path, result.catalog_path))

    with pytest.raises(McpServiceError):
        service.get_document_summary_internal(result.package.package_sha256)


def test_t138_01_instance_role_requires_reviewed_xbrl_instance_namespace() -> None:
    assert _member_role("instance.xbrl", "primary.htm", b"<xbrli:xbrl xmlns:xbrli='http://www.xbrl.org/2003/instance'/>") is SecMemberRole.XBRL_INSTANCE
    assert _member_role("instance.xbrl", "primary.htm", b"<xbrl xmlns='http://example.test/lookalike'/>") is SecMemberRole.OTHER


def test_t138_02_unrelated_inline_local_names_do_not_create_facts(tmp_path: Path) -> None:
    package = _html_package(_inline_html("<foo:nonfraction xmlns:foo='http://example.test/foo' contextRef='c1'>999</foo:nonfraction>"))

    parsed = parse_sec_package(package, tmp_path / "p11")

    assert parsed.fact_source_mode == "NO_STRUCTURED_FACTS"
    assert parsed.facts == ()


def test_t138_03_context_unit_and_dimension_semantics_are_namespace_aware(tmp_path: Path) -> None:
    html = _inline_html(
        "<ix:header>"
        "<foo:context xmlns:foo='http://example.test/foo' id='bad'><foo:period><foo:instant>1900-01-01</foo:instant></foo:period></foo:context>"
        "<xbrli:context id='good'><xbrli:entity><xbrli:identifier>0000320193</xbrli:identifier></xbrli:entity><xbrli:period><xbrli:instant>2025-06-30</xbrli:instant></xbrli:period><xbrli:scenario><foo:explicitMember dimension='ex:Axis'>ex:Bad</foo:explicitMember></xbrli:scenario></xbrli:context>"
        "<xbrli:unit id='USD'><xbrli:measure>iso4217:USD</xbrli:measure></xbrli:unit>"
        "</ix:header><h1>Revenue</h1><p><ix:nonfraction name='us-gaap:Revenues' contextRef='bad' unitRef='USD'>100</ix:nonfraction></p>"
    )
    parsed = parse_sec_package(_html_package(html), tmp_path / "p11")

    assert parsed.facts[0]["context"] is None
    assert any(issue["code"] == P11Reason.P11_XBRL_CONTEXT_UNRESOLVED.value for issue in parsed.issues)


def test_t138_04_alternate_inline_prefix_and_namespace_are_supported(tmp_path: Path) -> None:
    parsed = parse_sec_package(
        _html_package(
            _inline_html(
                "<i:header><xbrli:context id='c1'><xbrli:entity><xbrli:identifier>1</xbrli:identifier></xbrli:entity><xbrli:period><xbrli:instant>2025-06-30</xbrli:instant></xbrli:period></xbrli:context><xbrli:unit id='USD'><xbrli:measure>USD</xbrli:measure></xbrli:unit></i:header>"
                "<p><i:nonfraction name='ex:Revenue' contextRef='c1' unitRef='USD'>100</i:nonfraction></p>"
            )
        ),
        tmp_path / "p11",
    )

    assert len(parsed.facts) == 1


def test_t138_05_continuation_and_exclude_require_inline_namespace(tmp_path: Path) -> None:
    parsed = parse_sec_package(
        _html_package(
            _inline_html(
                "<ix:header><xbrli:context id='c1'><xbrli:entity><xbrli:identifier>1</xbrli:identifier></xbrli:entity><xbrli:period><xbrli:instant>2025-06-30</xbrli:instant></xbrli:period></xbrli:context><xbrli:unit id='USD'><xbrli:measure>USD</xbrli:measure></xbrli:unit></ix:header>"
                "<p><ix:nonfraction name='ex:Revenue' contextRef='c1' unitRef='USD' continuedAt='c1'>10</ix:nonfraction></p>"
                "<ix:continuation id='c1'>20<ix:exclude>bad</ix:exclude></ix:continuation>"
            )
        ),
        tmp_path / "p11",
    )

    assert parsed.facts[0]["raw_value"] == "10 20"


def test_t138_06_valid_custom_taxonomy_fact_survives_xml_instance_path(tmp_path: Path) -> None:
    html = b"<html><body><h1>Annual</h1></body></html>"
    xml = (
        b"<xbrli:xbrl xmlns:xbrli='http://www.xbrl.org/2003/instance' xmlns:ex='http://example.test/ex'>"
        b"<xbrli:context id='c1'><xbrli:entity><xbrli:identifier>1</xbrli:identifier></xbrli:entity><xbrli:period><xbrli:instant>2025-06-30</xbrli:instant></xbrli:period></xbrli:context>"
        b"<xbrli:unit id='USD'><xbrli:measure>USD</xbrli:measure></xbrli:unit>"
        b"<ex:CustomMetric contextRef='c1' unitRef='USD'>123</ex:CustomMetric></xbrli:xbrl>"
    )
    package = build_package(
        cik=CIK,
        accession=ACCESSION,
        form="10-Q",
        fiscal_year=2025,
        period="Q2",
        members=(
            SecPackageMember("aapl.htm", SecMemberRole.PRIMARY_DOCUMENT, "text/html", archive_member_url(CIK, ACCESSION, "aapl.htm"), html),
            SecPackageMember("aapl.xml", SecMemberRole.XBRL_INSTANCE, "application/xml", archive_member_url(CIK, ACCESSION, "aapl.xml"), xml),
        ),
    )

    parsed = parse_sec_package(package, tmp_path / "p11")

    assert parsed.fact_source_mode == "XBRL_INSTANCE_PRIMARY"
    assert any(fact["raw_qname"] == "ex:CustomMetric" for fact in parsed.facts)


def test_t138_07_wrong_namespace_root_is_not_used_as_xbrl_fact_source(tmp_path: Path) -> None:
    html = b"<html><body><h1>Annual</h1></body></html>"
    wrong_xml = b"<xbrl xmlns='http://example.test/not-xbrl'><context id='c1'/><ex:Fact xmlns:ex='http://example.test/ex' contextRef='c1'>1</ex:Fact></xbrl>"
    package = build_package(
        cik=CIK,
        accession=ACCESSION,
        form="10-Q",
        fiscal_year=2025,
        period="Q2",
        members=(
            SecPackageMember("aapl.htm", SecMemberRole.PRIMARY_DOCUMENT, "text/html", archive_member_url(CIK, ACCESSION, "aapl.htm"), html),
            SecPackageMember("aapl.xml", SecMemberRole.XBRL_INSTANCE, "application/xml", archive_member_url(CIK, ACCESSION, "aapl.xml"), wrong_xml),
        ),
    )

    parsed = parse_sec_package(package, tmp_path / "p11")

    assert parsed.fact_source_mode == "NO_STRUCTURED_FACTS"
    assert parsed.facts == ()


@pytest.mark.parametrize("filing_type", ["6-K", "6-K/A"])
def test_t139_explicit_6k_is_rejected_before_us_provider_execution(filing_type: str) -> None:
    args = _parser().parse_args(
        [
            "acquire",
            "--market",
            "US",
            "--cik",
            CIK,
            "--year",
            "2025",
            "--period",
            "FY",
            "--filing-type",
            filing_type,
        ]
    )

    with pytest.raises(SecError) as exc_info:
        _validate_market_period(args)

    assert exc_info.value.reason_code == P11Reason.P11_UNSUPPORTED_EXPLICIT_6K.value
