from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

from financial_filing_data_foundation.us_sec.acquisition import (
    SecAcquirer,
    _history_chunks_for_year,
    _select_archive_members,
)
from financial_filing_data_foundation.us_sec.compatibility import sec_artifact_compatibility
from financial_filing_data_foundation.us_sec.discovery import (
    SecDiscoveryObservation,
    SecHistoryChunk,
    SecSubmissions,
    discover_filings,
    parse_submissions,
    verify_sec_discovery_observation,
)
from financial_filing_data_foundation.us_sec.errors import P11Reason, SecError
from financial_filing_data_foundation.us_sec.http import SecResponse
from financial_filing_data_foundation.us_sec.models import SecCompanyRef, SecIssuerKind
from financial_filing_data_foundation.us_sec.package import (
    SecMemberRole,
    SecPackageMember,
    SecPackageStore,
    build_package,
)
from financial_filing_data_foundation.us_sec.parser import (
    SEC_ARTIFACT_SCHEMA,
    VIRTUAL_HTML_NORMALIZER_VERSION,
    parse_sec_package,
)
from financial_filing_data_foundation.us_sec.path_policy import archive_member_url
from financial_filing_data_foundation.us_sec.validation import validate_sec_artifacts
from financial_filing_data_foundation.registry import SQLiteRegistry
from financial_filing_data_foundation.us_sec.registry import register_sec_package, register_sec_parsed_run
from financial_filing_data_foundation.user_cli import _current_reusable_sec_artifacts, _runtime_paths


CIK = "0000320193"
COMPANY_ID = f"US:CIK{CIK}"
MAIN_URL = f"https://data.sec.gov/submissions/CIK{CIK}.json"
ACCESSION = "0000320193-25-000001"
AMENDED_ACCESSION = "0000320193-25-000002"


def _company() -> SecCompanyRef:
    return SecCompanyRef(
        cik=CIK,
        ticker="AAPL",
        company_id=COMPANY_ID,
        issuer_kind=SecIssuerKind.DOMESTIC,
    )


def _row(
    accession: str = ACCESSION,
    *,
    form: str = "10-K",
    filing_date: str = "2025-11-01",
    report_date: str = "2025-09-27",
    primary_document: str = "annual.htm",
) -> dict[str, str]:
    return {
        "accessionNumber": accession,
        "form": form,
        "filingDate": filing_date,
        "reportDate": report_date,
        "primaryDocument": primary_document,
    }


def _payload(
    rows: list[dict[str, str]],
    *,
    files: list[dict[str, str]] | None = None,
    fiscal_year_end: str = "0930",
) -> bytes:
    recent = {
        "accessionNumber": [row["accessionNumber"] for row in rows],
        "form": [row["form"] for row in rows],
        "filingDate": [row["filingDate"] for row in rows],
        "reportDate": [row["reportDate"] for row in rows],
        "primaryDocument": [row["primaryDocument"] for row in rows],
    }
    return json.dumps(
        {
            "cik": "320193",
            "fiscalYearEnd": fiscal_year_end,
            "filings": {"recent": recent, "files": files or []},
        },
        sort_keys=True,
    ).encode("utf-8")


def _observation(package: object) -> SecDiscoveryObservation:
    package_value = package
    body = _payload(
        [
            _row(
                accession=str(package_value.accession),
                form=str(package_value.form),
                primary_document=str(package_value.primary_document or "primary.htm"),
                report_date=str(package_value.report_period or "2025-09-27"),
            )
        ]
    )
    submissions = parse_submissions(json.loads(body), company=_company(), source_url=MAIN_URL)
    candidates = discover_filings(submissions, fiscal_year=2025, period="FY")
    return SecDiscoveryObservation.create(
        company=_company(),
        fiscal_year=2025,
        period="FY",
        source_documents=[{"url": MAIN_URL, "body": body}],
        candidates=candidates,
        selected_accession=str(package_value.accession),
        state="UNAMBIGUOUS",
        retrieved_at="2026-11-13T00:00:00+00:00",
    )


def _inline_html(*, value: str = "100", fact_name: str = "us-gaap:Revenues") -> bytes:
    return (
        '<html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL" '
        'xmlns:xbrli="http://www.xbrl.org/2003/instance" '
        'xmlns:us-gaap="http://fasb.org/us-gaap/2025">'
        "<body><ix:header>"
        "<xbrli:context id='c1'><xbrli:entity><xbrli:identifier>0000320193</xbrli:identifier>"
        "</xbrli:entity><xbrli:period><xbrli:instant>2025-09-27</xbrli:instant>"
        "</xbrli:period></xbrli:context>"
        "<xbrli:unit id='USD'><xbrli:measure>iso4217:USD</xbrli:measure></xbrli:unit>"
        "</ix:header><h1>Annual</h1><p>Revenue: "
        f"<ix:nonfraction name='{fact_name}' contextRef='c1' unitRef='USD'>{value}</ix:nonfraction>"
        "</p></body></html>"
    ).encode("utf-8")


def _instance_xml(*, value: str = "42", namespace: str = "http://www.xbrl.org/2003/instance") -> bytes:
    if namespace != "http://www.xbrl.org/2003/instance":
        return (
            f"<xbrl xmlns='{namespace}'><context id='c1'/><ex:Revenue "
            "xmlns:ex='http://example.test/ex' contextRef='c1'>1</ex:Revenue></xbrl>"
        ).encode("utf-8")
    return (
        b"<xbrli:xbrl xmlns:xbrli='http://www.xbrl.org/2003/instance' "
        b"xmlns:ex='http://example.test/ex'>"
        b"<xbrli:context id='c1'><xbrli:entity><xbrli:identifier>0000320193</xbrli:identifier>"
        b"</xbrli:entity><xbrli:period><xbrli:instant>2025-09-27</xbrli:instant>"
        b"</xbrli:period></xbrli:context>"
        b"<xbrli:unit id='USD'><xbrli:measure>iso4217:USD</xbrli:measure></xbrli:unit>"
        + f"<ex:Revenue contextRef='c1' unitRef='USD'>{value}</ex:Revenue>".encode()
        + b"</xbrli:xbrl>"
    )


def _package(
    *,
    primary_body: bytes,
    extra_members: tuple[SecPackageMember, ...] = (),
    accession: str = ACCESSION,
) -> object:
    primary = SecPackageMember(
        relative_name="primary.htm",
        role=SecMemberRole.PRIMARY_DOCUMENT,
        content_type="text/html",
        source_url=archive_member_url(CIK, accession, "primary.htm"),
        body=primary_body,
    )
    return build_package(
        cik=CIK,
        accession=accession,
        form="10-K",
        fiscal_year=2025,
        period="FY",
        filing_date="2025-11-01",
        report_period="2025-09-27",
        members=(primary, *extra_members),
    )


def _other_html(accession: str, name: str = "other.htm") -> SecPackageMember:
    return SecPackageMember(
        relative_name=name,
        role=SecMemberRole.OTHER,
        content_type="text/html",
        source_url=archive_member_url(CIK, accession, name),
        body=b"<html><body><p>other</p></body></html>",
    )


def _validate(parsed: object, package: object, observation: SecDiscoveryObservation, root: Path):
    return validate_sec_artifacts(
        parsed,
        root,
        package=package,
        discovery_observation=observation,
    )


def test_t140_01_v5_v2_is_incompatible_and_v6_reparses_without_mutating_legacy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    package = _package(primary_body=b"<html><body><foo:nonfraction xmlns:foo='urn:not-inline'>999</foo:nonfraction></body></html>")
    artifact_root = tmp_path / "p11"
    legacy_dir = artifact_root / f"{package.package_sha256}.VIRTUAL_HTML_V5"
    legacy_dir.mkdir(parents=True)
    legacy_manifest = legacy_dir / "manifest.json"
    legacy_manifest.write_text(
        json.dumps(
            {
                "schema_version": SEC_ARTIFACT_SCHEMA,
                "parser_version": "VIRTUAL_HTML_V5",
                "normalizer_version": "VIRTUAL_HTML_V5",
                "package_sha256": package.package_sha256,
                "fact_source_mode": "INLINE_XBRL_PRIMARY",
                "fact_count": 1,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    before = hashlib.sha256(legacy_manifest.read_bytes()).hexdigest()
    calls = 0
    from financial_filing_data_foundation.us_sec import parser as parser_module

    original_facts = parser_module._facts

    def counted_facts(*args: object, **kwargs: object):
        nonlocal calls
        calls += 1
        return original_facts(*args, **kwargs)

    monkeypatch.setattr(parser_module, "_facts", counted_facts)

    parsed = parse_sec_package(package, artifact_root)

    assert sec_artifact_compatibility(parser_version="VIRTUAL_HTML_V5", schema_version=SEC_ARTIFACT_SCHEMA) == "INCOMPATIBLE"
    assert sec_artifact_compatibility(parser_version=VIRTUAL_HTML_NORMALIZER_VERSION, schema_version=SEC_ARTIFACT_SCHEMA) == "COMPATIBLE"
    assert VIRTUAL_HTML_NORMALIZER_VERSION == "VIRTUAL_HTML_V6"
    assert parsed.artifact_dir.name == f"{package.package_sha256}.VIRTUAL_HTML_V6"
    assert calls > 0
    assert parsed.fact_source_mode == "NO_STRUCTURED_FACTS"
    assert hashlib.sha256(legacy_manifest.read_bytes()).hexdigest() == before

    store = SecPackageStore(tmp_path / "raw")
    store.put(package)
    client = _DiscoveryClient({MAIN_URL: _payload([_row(primary_document="primary.htm")])})
    acquired = SecAcquirer(client, store, discovery_root=tmp_path / "discovery")
    reused = acquired.acquire(_company(), fiscal_year=2025, period="FY")
    assert reused.reused is True
    assert reused.plan_action == "PARSE_LOCAL"
    assert client.calls == [MAIN_URL]


def test_t140_02_legacy_v5_v2_registry_row_cannot_select_reuse_data(tmp_path: Path) -> None:
    root = tmp_path / "planner"
    root.mkdir()
    paths = _runtime_paths(root)
    package = _package(primary_body=b"<html><body>Annual</body></html>")
    SecPackageStore(paths.raw_store).put(package)
    legacy_dir = paths.ingest_root / "us" / "p11" / f"{package.package_sha256}.VIRTUAL_HTML_V5"
    legacy_dir.mkdir(parents=True)
    (legacy_dir / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": SEC_ARTIFACT_SCHEMA,
                "parser_version": "VIRTUAL_HTML_V5",
                "package_sha256": package.package_sha256,
            }
        ),
        encoding="utf-8",
    )
    registry = SQLiteRegistry(paths.registry)
    register_sec_package(registry, package)
    register_sec_parsed_run(
        registry,
        parse_run_id="legacy-v5-v2",
        package_sha256=package.package_sha256,
        company_id=COMPANY_ID,
        fiscal_year=2025,
        period="FY",
        parser_version="VIRTUAL_HTML_V5",
        schema_version=SEC_ARTIFACT_SCHEMA,
        validation_status="PASS",
        blocking_issue_count=0,
        compatibility_status="COMPATIBLE",
        artifact_path=str(legacy_dir),
    )

    rows = registry.list_sec_parsed_data(company_id=COMPANY_ID, fiscal_year=2025, period="FY")

    assert _current_reusable_sec_artifacts(package=package, parsed_rows=rows, paths=paths) is None


def test_t141_01_authentic_standard_prefix_is_acquired() -> None:
    body = (
        "<html xmlns:link='http://www.xbrl.org/2003/linkbase' "
        "xmlns:xlink='http://www.w3.org/1999/xlink'><link:schemaRef "
        "xlink:href='schema.xsd'/></html>"
    ).encode()
    selected = _select_archive_members(
        {"primary.htm": {}, "schema.xsd": {}},
        primary_name="primary.htm",
        primary_body=body,
    )
    assert selected == ["primary.htm", "schema.xsd"]


def test_t141_02_authentic_alternate_prefix_is_acquired() -> None:
    body = (
        "<html xmlns:lb='http://www.xbrl.org/2003/linkbase' "
        "xmlns:xl='http://www.w3.org/1999/xlink'><lb:schemaRef "
        "xl:href='schema.xsd'/></html>"
    ).encode()
    selected = _select_archive_members(
        {"primary.htm": {}, "schema.xsd": {}},
        primary_name="primary.htm",
        primary_body=body,
    )
    assert selected == ["primary.htm", "schema.xsd"]


@pytest.mark.parametrize(
    "body",
    [
        b"<html xmlns:link='urn:not-xbrl' xmlns:xlink='http://www.w3.org/1999/xlink'><link:schemaRef xlink:href='schema.xsd'/></html>",
        b"<html><link:schemaRef xlink:href='schema.xsd'/></html>",
        b"<html xmlns:link='http://www.xbrl.org/2003/linkbase' xmlns:xlink='urn:not-xlink'><link:schemaRef xlink:href='schema.xsd'/></html>",
    ],
)
def test_t141_03_to_05_lookalike_or_wrong_xlink_is_not_acquired(body: bytes) -> None:
    selected = _select_archive_members(
        {"primary.htm": {}, "schema.xsd": {}},
        primary_name="primary.htm",
        primary_body=body,
    )
    assert selected == ["primary.htm"]


def test_t141_06_valid_chained_xbrl_dependency_is_acquired() -> None:
    primary = (
        "<html xmlns:link='http://www.xbrl.org/2003/linkbase' "
        "xmlns:xlink='http://www.w3.org/1999/xlink'><link:schemaRef "
        "xlink:href='a.xml'/></html>"
    ).encode()
    member = (
        b"<xbrl xmlns='http://www.xbrl.org/2003/instance' "
        b"xmlns:link='http://www.xbrl.org/2003/linkbase' "
        b"xmlns:xlink='http://www.w3.org/1999/xlink'><link:linkbaseRef "
        b"xlink:href='b.xml'/></xbrl>"
    )
    selected = _select_archive_members(
        {"primary.htm": {}, "a.xml": {}, "b.xml": {}},
        primary_name="primary.htm",
        primary_body=primary,
        accepted_member_bodies={"a.xml": (SecMemberRole.XBRL_INSTANCE, member)},
    )
    assert selected == ["a.xml", "b.xml", "primary.htm"]


def test_t142_01_to_06_history_selection_is_complete_but_minimal() -> None:
    submissions = SecSubmissions(
        company=_company(),
        candidates=(),
        fiscal_year_end="0930",
        history_ranges=(
            SecHistoryChunk("ancient.json", "2010-01-01", "2020-12-31"),
            SecHistoryChunk("eligible.json", "2024-01-01", "2025-01-01"),
            SecHistoryChunk("later-amendment.json", "2030-01-01", "2030-12-31"),
            SecHistoryChunk("unknown-range.json"),
        ),
    )
    selected = _history_chunks_for_year(submissions, 2025, period="FY")
    assert [chunk.name for chunk in selected] == [
        "eligible.json",
        "later-amendment.json",
        "unknown-range.json",
    ]


def test_t142_07_malformed_history_range_fails_closed() -> None:
    submissions = SecSubmissions(
        company=_company(),
        candidates=(),
        history_ranges=(SecHistoryChunk("bad.json", "not-a-date", "2030-01-01"),),
    )
    with pytest.raises(SecError):
        _history_chunks_for_year(submissions, 2025, period="FY")


def test_t142_08_duplicate_history_descriptor_fails_closed() -> None:
    submissions = SecSubmissions(
        company=_company(),
        candidates=(),
        history_ranges=(SecHistoryChunk("same.json"), SecHistoryChunk("same.json")),
    )
    with pytest.raises(SecError):
        _history_chunks_for_year(submissions, 2025, period="FY")


def test_t142_09_excessive_relevant_history_count_fails_closed() -> None:
    submissions = SecSubmissions(
        company=_company(),
        candidates=(),
        history_ranges=tuple(SecHistoryChunk(f"chunk-{index:03d}.json") for index in range(257)),
    )
    with pytest.raises(SecError):
        _history_chunks_for_year(submissions, 2025, period="FY")


class _DiscoveryClient:
    def __init__(self, bodies: dict[str, bytes]) -> None:
        self.bodies = bodies
        self.calls: list[str] = []
        self.config = type(
            "Config",
            (),
            {"submissions_max_bytes": 1024 * 1024, "member_max_bytes": 1024 * 1024},
        )()

    def fetch(self, url: str, **_: object) -> SecResponse:
        self.calls.append(url)
        return SecResponse(200, {"Content-Type": "application/json"}, self.bodies[url], url)


def test_t142_03_to_05_and_t142_10_online_source_set_matches_verifier(tmp_path: Path) -> None:
    history_name = f"CIK{CIK}-submissions-002.json"
    history_url = f"https://data.sec.gov/submissions/{history_name}"
    main_body = _payload(
        [],
        files=[
            {"name": f"CIK{CIK}-submissions-001.json", "filingFrom": "2010-01-01", "filingTo": "2020-12-31"},
            {"name": history_name, "filingFrom": "2026-01-01", "filingTo": "2030-12-31"},
        ],
    )
    history_body = _payload([_row()])
    client = _DiscoveryClient({MAIN_URL: main_body, history_url: history_body})
    acquirer = SecAcquirer(client, SecPackageStore(tmp_path / "raw"), discovery_root=tmp_path / "discovery")

    observation, candidates = acquirer._discover_with_candidates(_company(), fiscal_year=2025, period="FY")

    assert observation.state == "UNAMBIGUOUS"
    assert {row.accession for row in candidates} == {ACCESSION}
    assert client.calls == [MAIN_URL, history_url]
    assert [row["url"] for row in observation.source_documents] == [MAIN_URL, history_url]
    verify_sec_discovery_observation(observation)


def test_t142_11_ancient_incomplete_legacy_row_is_not_fetched(tmp_path: Path) -> None:
    ancient_name = f"CIK{CIK}-submissions-001.json"
    ancient_url = f"https://data.sec.gov/submissions/{ancient_name}"
    main_body = _payload(
        [_row()],
        files=[{"name": ancient_name, "filingFrom": "2010-01-01", "filingTo": "2020-12-31"}],
    )
    client = _DiscoveryClient({MAIN_URL: main_body})
    acquirer = SecAcquirer(client, SecPackageStore(tmp_path / "raw"), discovery_root=tmp_path / "discovery")

    observation, candidates = acquirer._discover_with_candidates(_company(), fiscal_year=2025, period="FY")

    assert observation.state == "UNAMBIGUOUS"
    assert candidates[0].accession == ACCESSION
    assert ancient_url not in client.calls


def test_t142_12_relevant_incomplete_periodic_row_fails_closed(tmp_path: Path) -> None:
    history_name = f"CIK{CIK}-submissions-002.json"
    history_url = f"https://data.sec.gov/submissions/{history_name}"
    main_body = _payload(
        [_row()],
        files=[{"name": history_name, "filingFrom": "2026-01-01", "filingTo": "2030-12-31"}],
    )
    history_body = json.dumps(
        {
            "cik": "320193",
            "accessionNumber": [AMENDED_ACCESSION],
            "filingDate": ["2028-01-01"],
            "reportDate": ["2025-09-27"],
            "form": ["10-K/A"],
            "primaryDocument": [""],
        },
        sort_keys=True,
    ).encode()
    client = _DiscoveryClient({MAIN_URL: main_body, history_url: history_body})
    acquirer = SecAcquirer(client, SecPackageStore(tmp_path / "raw"), discovery_root=tmp_path / "discovery")

    with pytest.raises(SecError):
        acquirer._discover_with_candidates(_company(), fiscal_year=2025, period="FY")


def test_t143_08_correct_inline_source_chain_passes(tmp_path: Path) -> None:
    package = _package(primary_body=_inline_html())
    observation = _observation(package)
    parsed = parse_sec_package(package, tmp_path / "p11", discovery_observation=observation)

    validation = _validate(parsed, package, observation, tmp_path / "p7")

    assert validation.validation_status == "PASS"
    assert validation.blocking_issue_count == 0


def test_t143_09_correct_instance_source_chain_passes(tmp_path: Path) -> None:
    instance = SecPackageMember(
        relative_name="instance.xml",
        role=SecMemberRole.XBRL_INSTANCE,
        content_type="application/xml",
        source_url=archive_member_url(CIK, ACCESSION, "instance.xml"),
        body=_instance_xml(),
    )
    package = _package(primary_body=b"<html><body><h1>Annual</h1></body></html>", extra_members=(instance,))
    observation = _observation(package)
    parsed = parse_sec_package(package, tmp_path / "p11", discovery_observation=observation)

    validation = _validate(parsed, package, observation, tmp_path / "p7")

    assert validation.validation_status == "PASS"
    assert validation.blocking_issue_count == 0


def test_t143_01_inline_mode_with_xml_source_facts_is_blocked(tmp_path: Path) -> None:
    instance = SecPackageMember(
        relative_name="instance.xml",
        role=SecMemberRole.XBRL_INSTANCE,
        content_type="application/xml",
        source_url=archive_member_url(CIK, ACCESSION, "instance.xml"),
        body=_instance_xml(),
    )
    package = _package(primary_body=b"<html><body>Annual</body></html>", extra_members=(instance,))
    observation = _observation(package)
    parsed = parse_sec_package(package, tmp_path / "p11", discovery_observation=observation)

    validation = _validate(replace(parsed, fact_source_mode="INLINE_XBRL_PRIMARY"), package, observation, tmp_path / "p7")

    assert validation.validation_status == "BLOCKED"
    assert any(issue["code"] == P11Reason.P11_FACT_SOURCE_MODE_INVALID.value for issue in validation.issues)


def test_t143_02_inline_mode_with_nonprimary_dom_source_is_blocked(tmp_path: Path) -> None:
    package = _package(primary_body=_inline_html(), extra_members=(_other_html(ACCESSION),))
    observation = _observation(package)
    parsed = parse_sec_package(package, tmp_path / "p11", discovery_observation=observation)
    other_sha = next(member.member_sha256 for member in package.members if member.relative_name == "other.htm")
    facts = [dict(row) for row in parsed.facts]
    evidence = [dict(row) for row in parsed.evidence]
    facts[0]["member_sha256"] = other_sha
    facts[0]["source_member_sha256"] = other_sha
    evidence[0]["member_sha256"] = other_sha
    evidence[0]["source_member_sha256"] = other_sha

    validation = _validate(replace(parsed, facts=tuple(facts), evidence=tuple(evidence)), package, observation, tmp_path / "p7")

    assert validation.validation_status == "BLOCKED"
    assert any(issue["code"] == P11Reason.P11_FACT_SOURCE_MODE_INVALID.value for issue in validation.issues)


def test_t143_03_instance_mode_with_dom_facts_is_blocked(tmp_path: Path) -> None:
    instance = SecPackageMember(
        relative_name="instance.xml",
        role=SecMemberRole.XBRL_INSTANCE,
        content_type="application/xml",
        source_url=archive_member_url(CIK, ACCESSION, "instance.xml"),
        body=_instance_xml(),
    )
    package = _package(primary_body=_inline_html(), extra_members=(instance,))
    observation = _observation(package)
    parsed = parse_sec_package(package, tmp_path / "p11", discovery_observation=observation)

    validation = _validate(replace(parsed, fact_source_mode="XBRL_INSTANCE_PRIMARY"), package, observation, tmp_path / "p7")

    assert validation.validation_status == "BLOCKED"
    assert any(issue["code"] == P11Reason.P11_FACT_SOURCE_MODE_INVALID.value for issue in validation.issues)


def test_t143_04_and_05_two_instance_sources_are_blocked(tmp_path: Path) -> None:
    first = SecPackageMember(
        relative_name="first.xml",
        role=SecMemberRole.XBRL_INSTANCE,
        content_type="application/xml",
        source_url=archive_member_url(CIK, ACCESSION, "first.xml"),
        body=_instance_xml(value="42"),
    )
    second = SecPackageMember(
        relative_name="second.xml",
        role=SecMemberRole.XBRL_INSTANCE,
        content_type="application/xml",
        source_url=archive_member_url(CIK, ACCESSION, "second.xml"),
        body=_instance_xml(value="43"),
    )
    package = _package(primary_body=b"<html><body>Annual</body></html>", extra_members=(first, second))
    observation = _observation(package)
    one_instance_package = _package(primary_body=b"<html><body>Annual</body></html>", extra_members=(first,))
    one_parsed = parse_sec_package(one_instance_package, tmp_path / "one", discovery_observation=observation)

    tampered_facts = [dict(row) for row in one_parsed.facts]
    tampered_facts[0]["package_sha256"] = package.package_sha256
    tampered_evidence = [dict(row) for row in one_parsed.evidence]
    tampered_evidence[0]["package_sha256"] = package.package_sha256
    parsed = replace(
        one_parsed,
        package_sha256=package.package_sha256,
        facts=tuple(tampered_facts),
        evidence=tuple(tampered_evidence),
        fact_source_mode="XBRL_INSTANCE_PRIMARY",
    )

    validation = _validate(parsed, package, observation, tmp_path / "p7")

    assert validation.validation_status == "BLOCKED"
    assert any(issue["code"] == P11Reason.P11_FACT_SOURCE_MODE_INVALID.value for issue in validation.issues)


def test_t143_06_instance_mode_without_authentic_instance_is_blocked(tmp_path: Path) -> None:
    wrong = SecPackageMember(
        relative_name="wrong.xml",
        role=SecMemberRole.XBRL_INSTANCE,
        content_type="application/xml",
        source_url=archive_member_url(CIK, ACCESSION, "wrong.xml"),
        body=_instance_xml(namespace="urn:not-xbrl"),
    )
    package = _package(primary_body=b"<html><body>Annual</body></html>", extra_members=(wrong,))
    observation = _observation(package)
    parsed = parse_sec_package(package, tmp_path / "p11", discovery_observation=observation)

    validation = _validate(replace(parsed, fact_source_mode="XBRL_INSTANCE_PRIMARY"), package, observation, tmp_path / "p7")

    assert validation.validation_status == "BLOCKED"
    assert any(issue["code"] == P11Reason.P11_FACT_SOURCE_MODE_INVALID.value for issue in validation.issues)


def test_t143_07_no_structured_facts_with_facts_is_blocked(tmp_path: Path) -> None:
    package = _package(primary_body=_inline_html())
    observation = _observation(package)
    parsed = parse_sec_package(package, tmp_path / "p11", discovery_observation=observation)

    validation = _validate(replace(parsed, fact_source_mode="NO_STRUCTURED_FACTS"), package, observation, tmp_path / "p7")

    assert validation.validation_status == "BLOCKED"
    assert any(issue["code"] == P11Reason.P11_FACT_SOURCE_MODE_INVALID.value for issue in validation.issues)
