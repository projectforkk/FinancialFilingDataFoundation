from __future__ import annotations

import base64
import json
from pathlib import Path

import pytest

from financial_filing_data_foundation.us_sec.errors import P11Reason, SecError
from financial_filing_data_foundation.us_sec.discovery import SecDiscoveryObservation, parse_submissions
from financial_filing_data_foundation.us_sec.models import SecCompanyRef
from financial_filing_data_foundation.us_sec.runtime import (
    SecRuntimeDescriptor,
    SecSubprocessTransport,
    run_sec_runner,
)
from financial_filing_data_foundation.us_sec.parser import (
    SEC_ARTIFACT_SCHEMA,
    VIRTUAL_HTML_NORMALIZER_VERSION,
    parse_sec_package,
)
from financial_filing_data_foundation.us_sec.ingest import ingest_sec_package
from financial_filing_data_foundation.us_sec.validation import validate_sec_artifacts
from financial_filing_data_foundation.us_sec.path_policy import archive_member_url
from financial_filing_data_foundation.user_cli import _parser


def _sec_url(cik: str, accession: str, name: str) -> str:
    return archive_member_url(cik, accession, name)


def _observation(package: object) -> SecDiscoveryObservation:
    body = json.dumps(
        {
            "cik": package.cik,
            "fiscalYearEnd": "0927",
            "filings": {
                "recent": {
                    "accessionNumber": [package.accession],
                    "filingDate": ["2025-11-01"],
                    "reportDate": ["2025-09-27"],
                    "form": [package.form],
                    "primaryDocument": [package.primary_document],
                }
            },
        },
        sort_keys=True,
    ).encode()
    company = SecCompanyRef(
        cik=package.cik,
        ticker="AAPL",
        company_id=f"US:CIK{package.cik}",
    )
    candidates = parse_submissions(
        json.loads(body.decode()),
        company=company,
        source_url="https://data.sec.gov/submissions/CIK0000320193.json",
    ).candidates
    return SecDiscoveryObservation.create(
        company=company,
        fiscal_year=package.fiscal_year,
        period=package.period,
        source_documents=[
            {
                "url": "https://data.sec.gov/submissions/CIK0000320193.json",
                "body": body,
            }
        ],
        candidates=candidates,
        selected_accession=package.accession,
        state="UNAMBIGUOUS",
        retrieved_at="2026-11-12T00:00:00+00:00",
    )


def test_runtime_uses_explicit_argv_without_shell_or_arbitrary_url(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: list[dict[str, object]] = []

    class Completed:
        returncode = 0
        stdout = json.dumps(
            {
                "status": 200,
                "headers": {"Content-Type": "application/json"},
                "body_b64": base64.b64encode(b"{}").decode(),
                "final_url": "https://data.sec.gov/submissions/CIK0000123456.json",
            }
        )
        stderr = ""

    def fake_run(argv: list[str], **kwargs: object) -> Completed:
        calls.append({"argv": argv, **kwargs})
        return Completed()

    monkeypatch.setattr("financial_filing_data_foundation.us_sec.runtime.subprocess.run", fake_run)
    descriptor = SecRuntimeDescriptor.for_project(tmp_path)
    response = run_sec_runner(
        descriptor,
        "fetch",
        {
            "url": "https://data.sec.gov/submissions/CIK0000123456.json",
            "headers": {"User-Agent": "FFDF/Test; contact: ops@example.org"},
            "timeout": 1,
            "max_bytes": 64,
        },
    )
    assert response["status"] == 200
    assert calls[0]["shell"] is False
    assert calls[0]["cwd"] == str(tmp_path.resolve())
    assert "--url" not in calls[0]["argv"]

    with pytest.raises(SecError) as exc_info:
        SecSubprocessTransport(descriptor).validate_url("https://example.com/file")
    assert exc_info.value.reason_code == P11Reason.P11_ARCHIVE_HOST_REJECTED.value


def test_us_cli_accepts_q2_and_explicit_cik_without_ticker() -> None:
    args = _parser().parse_args(
        ["acquire", "--market", "US", "--cik", "320193", "--year", "2025", "--period", "Q2"]
    )
    assert args.cik == "320193"
    assert args.ticker is None
    assert args.period == "Q2"


def test_explicit_cik_bypasses_current_ticker_map(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FFDF_P11_US_DEV", "1")
    monkeypatch.delenv("FFDF_SEC_CONTACT_EMAIL", raising=False)
    from financial_filing_data_foundation.user_cli import _us_company_and_client

    args = _parser().parse_args(
        ["acquire", "--market", "US", "--cik", "55067", "--ticker", "K", "--year", "2024", "--period", "FY"]
    )
    company, client = _us_company_and_client(args, online=False)
    assert company.company_id == "US:CIK0000055067"
    assert company.ticker == "K"
    assert client is None


def test_cached_ticker_map_supports_local_identity_resolution_without_network(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("FFDF_P11_US_DEV", "1")
    monkeypatch.delenv("FFDF_SEC_CONTACT_EMAIL", raising=False)
    monkeypatch.setenv("FFDF_ROOT", str(tmp_path))
    from financial_filing_data_foundation.us_sec.ticker_map import snapshot_ticker_map
    from financial_filing_data_foundation.user_cli import _persist_ticker_map_snapshot, _us_company_and_client

    snapshot = snapshot_ticker_map(
        json.dumps({"1": {"ticker": "OLD", "cik_str": 55067}}).encode(),
        source_url="https://www.sec.gov/files/company_tickers.json",
    )
    _persist_ticker_map_snapshot(tmp_path, snapshot)
    args = _parser().parse_args(["acquire", "--market", "US", "--ticker", "OLD", "--year", "2024", "--period", "FY"])
    company, client = _us_company_and_client(args, online=False)
    assert company.cik == "0000055067"
    assert company.ticker_source_sha256 == snapshot.source_sha256
    assert client is None


def test_local_status_with_uncached_ticker_does_not_fall_back_to_network(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("FFDF_P11_US_DEV", raising=False)
    monkeypatch.setenv("FFDF_ROOT", str(tmp_path))
    from financial_filing_data_foundation.user_cli import _us_company_and_client

    args = _parser().parse_args(
        ["status", "--market", "US", "--ticker", "MISSING", "--year", "2025", "--period", "FY"]
    )
    with pytest.raises(SecError) as exc_info:
        _us_company_and_client(args, online=False)
    assert exc_info.value.reason_code == P11Reason.P11_DISCOVERY_FRESHNESS_UNKNOWN.value


def test_us_status_is_local_only_and_reports_discovery_as_of(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("FFDF_P11_US_DEV", raising=False)
    monkeypatch.setenv("FFDF_ROOT", str(tmp_path))
    from financial_filing_data_foundation.registry import SQLiteRegistry
    from financial_filing_data_foundation.us_sec.discovery import SecDiscoveryObservation
    from financial_filing_data_foundation.us_sec.identity import sec_company
    from financial_filing_data_foundation.user_cli import _runtime_paths, _us_status

    company = sec_company(cik="320193", ticker=None)
    checked_at = "2026-11-11T01:02:03+00:00"
    observation = SecDiscoveryObservation.create(
        company=company,
        fiscal_year=2025,
        period="FY",
        source_documents=[{"url": "https://data.sec.gov/submissions/CIK0000320193.json", "body": b"{}"}],
        candidates=(),
        selected_accession=None,
        state="NOT_FOUND",
        retrieved_at=checked_at,
    )
    paths = _runtime_paths(tmp_path)
    SQLiteRegistry(paths.registry).register_sec_discovery_observation(observation)
    monkeypatch.setattr(
        "financial_filing_data_foundation.us_sec.http.SecHttpClient.fetch",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("status performed network I/O")),
    )
    args = _parser().parse_args(
        ["status", "--market", "US", "--cik", "320193", "--year", "2025", "--period", "FY"]
    )

    assert _us_status(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["discovery_as_of"]["discovery_checked_at"] == checked_at
    assert payload["discovery_as_of"]["discovery_state"] == "NOT_FOUND"


def test_market_period_validation_is_scoped_before_provider_dispatch() -> None:
    from financial_filing_data_foundation.user_cli import _validate_market_period

    cn_args = _parser().parse_args(["status", "--market", "CN", "--ticker", "000001", "--year", "2025", "--period", "Q2"])
    with pytest.raises(ValueError):
        _validate_market_period(cn_args)
    us_args = _parser().parse_args(["status", "--market", "US", "--cik", "320193", "--year", "2025", "--period", "H1"])
    with pytest.raises(ValueError):
        _validate_market_period(us_args)


def test_us_cli_planner_uses_current_local_package_and_parsed_data(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("FFDF_P11_US_DEV", "1")
    monkeypatch.delenv("FFDF_SEC_CONTACT_EMAIL", raising=False)
    monkeypatch.setenv("FFDF_ROOT", str(tmp_path))
    from financial_filing_data_foundation.registry import SQLiteRegistry
    from financial_filing_data_foundation.us_sec.package import SecMemberRole, SecPackageMember, SecPackageStore, build_package
    from financial_filing_data_foundation.us_sec.identity import sec_company
    from financial_filing_data_foundation.us_sec.registry import register_sec_package, register_sec_slot
    from financial_filing_data_foundation.user_cli import _runtime_paths, _us_plan_slot

    package = build_package(
        cik="0000320193", accession="0000320193-25-000079", form="10-K", fiscal_year=2025, period="FY",
        members=(SecPackageMember(relative_name="annual.htm", role=SecMemberRole.PRIMARY_DOCUMENT, content_type="text/html", source_url=_sec_url("0000320193", "0000320193-25-000079", "annual.htm"), body=b'<html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL" xmlns:xbrli="http://www.xbrl.org/2003/instance" xmlns:us-gaap="http://fasb.org/us-gaap/2025"><body><ix:header><xbrli:context id="c1"><xbrli:entity><xbrli:identifier>0000320193</xbrli:identifier></xbrli:entity><xbrli:period><xbrli:instant>2025-09-27</xbrli:instant></xbrli:period></xbrli:context><xbrli:unit id="USD"><xbrli:measure>iso4217:USD</xbrli:measure></xbrli:unit></ix:header><h1>Annual</h1><p><ix:nonfraction name="us-gaap:Revenues" contextRef="c1" unitRef="USD" decimals="0">100</ix:nonfraction></p></body></html>'),),
    )
    paths = _runtime_paths(tmp_path)
    store = SecPackageStore(paths.raw_store)
    store.put(package)
    registry = SQLiteRegistry(paths.registry)
    register_sec_package(registry, package)
    register_sec_slot(registry, package, fiscal_year=2025, period="FY")
    observation = _observation(package)
    registry.register_sec_discovery_observation(observation)
    args = _parser().parse_args(["acquire", "--market", "US", "--cik", "320193", "--year", "2025", "--period", "FY"])
    company = sec_company(cik="320193", ticker=None)
    plan, local_package = _us_plan_slot(
        company,
        args,
        paths,
        registry,
        selected_accession=package.accession,
        discovery_state="UNAMBIGUOUS",
    )
    assert company.company_id == "US:CIK0000320193"
    assert plan.action.value == "PARSE_LOCAL"
    assert local_package.package_sha256 == package.package_sha256
    parsed = parse_sec_package(package, paths.ingest_root / "us" / "p11", discovery_observation=observation)
    validation = validate_sec_artifacts(
        parsed,
        paths.ingest_root / "us" / "p7",
        package=package,
        discovery_observation=observation,
        registry=registry,
    )
    assert validation.validation_status == "PASS"
    registry.register_sec_parsed_data(parse_run_id="run1", package_sha256=package.package_sha256, company_id=company.company_id, fiscal_year=2025, period="FY", parser_version="VIRTUAL_HTML_V3", schema_version=SEC_ARTIFACT_SCHEMA, validation_status="PASS", blocking_issue_count=0, compatibility_status="COMPATIBLE", artifact_path=str(parsed.artifact_dir))
    plan, _ = _us_plan_slot(company, args, paths, registry)
    assert plan.action.value == "PARSE_LOCAL"
    registry.register_sec_parsed_data(parse_run_id="stale-schema", package_sha256=package.package_sha256, company_id=company.company_id, fiscal_year=2025, period="FY", parser_version=VIRTUAL_HTML_NORMALIZER_VERSION, schema_version="p11-sec-artifacts-v0", validation_status="PASS", blocking_issue_count=0, compatibility_status="COMPATIBLE", artifact_path=str(parsed.artifact_dir))
    plan, _ = _us_plan_slot(company, args, paths, registry)
    assert plan.action.value == "PARSE_LOCAL"
    registry.register_sec_parsed_data(parse_run_id="run2", package_sha256=package.package_sha256, company_id=company.company_id, fiscal_year=2025, period="FY", parser_version=VIRTUAL_HTML_NORMALIZER_VERSION, schema_version=SEC_ARTIFACT_SCHEMA, validation_status="PASS", blocking_issue_count=0, compatibility_status="COMPATIBLE", artifact_path=str(parsed.artifact_dir))
    plan, _ = _us_plan_slot(company, args, paths, registry)
    assert plan.action.value == "REUSE_DATA"


def test_us_cli_planner_rejects_parsed_row_for_wrong_package(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("FFDF_P11_US_DEV", "1")
    monkeypatch.delenv("FFDF_SEC_CONTACT_EMAIL", raising=False)
    monkeypatch.setenv("FFDF_ROOT", str(tmp_path))
    from financial_filing_data_foundation.registry import SQLiteRegistry
    from financial_filing_data_foundation.us_sec.package import SecMemberRole, SecPackageMember, SecPackageStore, build_package
    from financial_filing_data_foundation.us_sec.registry import register_sec_package, register_sec_slot
    from financial_filing_data_foundation.user_cli import _runtime_paths, _us_plan_slot

    def make_package(accession: str, text: bytes) -> object:
        return build_package(
            cik="0000320193", accession=accession, form="10-K", fiscal_year=2025, period="FY",
            members=(SecPackageMember(relative_name="annual.htm", role=SecMemberRole.PRIMARY_DOCUMENT, content_type="text/html", source_url=_sec_url("0000320193", accession, "annual.htm"), body=text),),
        )

    html = b'<html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL" xmlns:us-gaap="http://fasb.org/us-gaap/2025"><body><h1>Annual</h1><p><ix:nonfraction name="us-gaap:Revenues" contextRef="c1" unitRef="USD">100</ix:nonfraction></p></body></html>'
    local_package = make_package("0000320193-25-000079", html)
    wrong_package = make_package("0000320193-25-000080", html + b"<p>wrong identity</p>")
    paths = _runtime_paths(tmp_path)
    store = SecPackageStore(paths.raw_store)
    store.put(local_package)
    registry = SQLiteRegistry(paths.registry)
    register_sec_package(registry, local_package)
    register_sec_slot(registry, local_package, fiscal_year=2025, period="FY")
    register_sec_package(registry, wrong_package)
    parsed = parse_sec_package(local_package, paths.ingest_root / "us" / "p11")
    validate_sec_artifacts(parsed, paths.ingest_root / "us" / "p7", package=local_package)
    registry.register_sec_parsed_data(parse_run_id="wrong-package", package_sha256=wrong_package.package_sha256, company_id="US:CIK0000320193", fiscal_year=2025, period="FY", parser_version=VIRTUAL_HTML_NORMALIZER_VERSION, schema_version=SEC_ARTIFACT_SCHEMA, validation_status="PASS", blocking_issue_count=0, compatibility_status="COMPATIBLE", artifact_path=str(parsed.artifact_dir))
    args = _parser().parse_args(["acquire", "--market", "US", "--cik", "320193", "--year", "2025", "--period", "FY"])
    company = _us_plan_slot.__globals__["sec_company"](cik="320193", ticker=None, allow_development=True)

    plan, _ = _us_plan_slot(company, args, paths, registry)

    assert plan.action.value == "PARSE_LOCAL"


def test_us_cli_planner_marks_multiple_local_packages_for_review(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("FFDF_P11_US_DEV", "1")
    monkeypatch.setenv("FFDF_ROOT", str(tmp_path))
    from financial_filing_data_foundation.registry import SQLiteRegistry
    from financial_filing_data_foundation.us_sec.package import SecMemberRole, SecPackageMember, SecPackageStore, build_package
    from financial_filing_data_foundation.us_sec.registry import register_sec_package, register_sec_slot
    from financial_filing_data_foundation.user_cli import _runtime_paths, _us_plan_slot
    from financial_filing_data_foundation.us_sec.identity import sec_company

    def make_package(accession: str) -> object:
        return build_package(
            cik="0000320193", accession=accession, form="10-K", fiscal_year=2025, period="FY",
            members=(SecPackageMember(relative_name="annual.htm", role=SecMemberRole.PRIMARY_DOCUMENT, content_type="text/html", source_url=_sec_url("0000320193", accession, "annual.htm"), body=f"<html><body>{accession}</body></html>".encode()),),
        )

    first = make_package("0000320193-25-000079")
    second = make_package("0000320193-25-000080")
    paths = _runtime_paths(tmp_path)
    store = SecPackageStore(paths.raw_store)
    store.put(first)
    store.put(second)
    registry = SQLiteRegistry(paths.registry)
    for package in (first, second):
        register_sec_package(registry, package)
        register_sec_slot(registry, package, fiscal_year=2025, period="FY")
    args = _parser().parse_args(["acquire", "--market", "US", "--cik", "320193", "--year", "2025", "--period", "FY"])

    plan, _ = _us_plan_slot(sec_company(cik="320193", ticker=None, allow_development=True), args, paths, registry)

    assert plan.action.value == "REVIEW_REQUIRED"


def test_us_cli_reuse_data_refreshes_discovery_without_reparsing_or_redownloading(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("FFDF_P11_US_DEV", raising=False)
    monkeypatch.setenv("FFDF_SEC_CONTACT_EMAIL", "ops@example.org")
    monkeypatch.setenv("FFDF_ROOT", str(tmp_path))
    from financial_filing_data_foundation.user_cli import _us_ingest, _runtime_paths
    from financial_filing_data_foundation.us_sec.http import SecHttpConfig, SecResponse
    from financial_filing_data_foundation.us_sec.package import SecMemberRole, SecPackageMember, build_package

    package = build_package(
        cik="0000320193",
        accession="0000320193-25-000079",
        form="10-K",
        fiscal_year=2025,
        period="FY",
        members=(
            SecPackageMember(
                relative_name="annual.htm",
                role=SecMemberRole.PRIMARY_DOCUMENT,
                content_type="text/html",
                source_url=_sec_url("0000320193", "0000320193-25-000079", "annual.htm"),
                body=b'<html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL" xmlns:xbrli="http://www.xbrl.org/2003/instance" xmlns:us-gaap="http://fasb.org/us-gaap/2025"><body><ix:header><xbrli:context id="c1"><xbrli:entity><xbrli:identifier>0000320193</xbrli:identifier></xbrli:entity><xbrli:period><xbrli:instant>2025-09-27</xbrli:instant></xbrli:period></xbrli:context><xbrli:unit id="USD"><xbrli:measure>iso4217:USD</xbrli:measure></xbrli:unit></ix:header><h1>Annual</h1><p><ix:nonfraction name="us-gaap:Revenues" contextRef="c1" unitRef="USD" decimals="0">100</ix:nonfraction></p></body></html>',
            ),
        ),
    )
    initial = ingest_sec_package(
        package,
        root=tmp_path,
        ticker="AAPL",
        period="FY",
        discovery_observation=_observation(package),
    )
    assert initial.research_ready is True
    paths = _runtime_paths(tmp_path)
    before = tuple(sorted(path.name for path in (paths.ingest_root / "us" / "p11").iterdir()))

    submissions = {
        "cik": "0000320193",
        "fiscalYearEnd": "0927",
        "filings": {
            "recent": {
                "accessionNumber": ["0000320193-25-000079"],
                "filingDate": ["2025-11-01"],
                "reportDate": ["2025-09-27"],
                "form": ["10-K"],
                "primaryDocument": ["annual.htm"],
            }
        },
    }
    submissions_url = "https://data.sec.gov/submissions/CIK0000320193.json"
    discovery_calls: list[str] = []

    class FreshnessClient:
        config = SecHttpConfig(contact_email="ops@example.org")

        def fetch(self, url: str, **_: object) -> SecResponse:
            discovery_calls.append(url)
            assert url == submissions_url
            return SecResponse(
                200,
                {"Content-Type": "application/json"},
                json.dumps(submissions).encode(),
                url,
            )

    monkeypatch.setattr(
        "financial_filing_data_foundation.user_cli.SecHttpClient",
        lambda *_args, **_kwargs: FreshnessClient(),
    )

    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("parser or package acquisition was invoked during REUSE_DATA")

    monkeypatch.setattr("financial_filing_data_foundation.us_sec.ingest.parse_sec_package", forbidden)
    monkeypatch.setattr("financial_filing_data_foundation.us_sec.acquisition.SecAcquirer.acquire", forbidden)
    args = _parser().parse_args(
        ["ingest", "--market", "US", "--cik", "320193", "--ticker", "AAPL", "--year", "2025", "--period", "FY"]
    )

    assert _us_ingest(args) == 0
    after = tuple(sorted(path.name for path in (paths.ingest_root / "us" / "p11").iterdir()))
    output = json.loads(capsys.readouterr().out)
    assert output["planner_action"] == "REUSE_DATA"
    assert discovery_calls == [submissions_url]
    assert before == after

    assert _us_ingest(args) == 0
    second_output = json.loads(capsys.readouterr().out)
    assert second_output["planner_action"] == "REUSE_DATA"
    assert discovery_calls == [submissions_url, submissions_url]


def test_us_cli_local_old_artifact_is_incompatible_and_raw_package_is_reparsed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("FFDF_P11_US_DEV", "1")
    monkeypatch.delenv("FFDF_SEC_CONTACT_EMAIL", raising=False)
    monkeypatch.setenv("FFDF_ROOT", str(tmp_path))
    from financial_filing_data_foundation.registry import SQLiteRegistry
    from financial_filing_data_foundation.us_sec.identity import sec_company
    from financial_filing_data_foundation.us_sec.package import SecMemberRole, SecPackageMember, SecPackageStore, build_package
    from financial_filing_data_foundation.us_sec.registry import register_sec_package, register_sec_slot
    from financial_filing_data_foundation.user_cli import _runtime_paths, _us_plan_slot

    package = build_package(
        cik="0000320193",
        accession="0000320193-25-000079",
        form="10-K",
        fiscal_year=2025,
        period="FY",
        members=(
            SecPackageMember(
                relative_name="annual.htm",
                role=SecMemberRole.PRIMARY_DOCUMENT,
                content_type="text/html",
                source_url=_sec_url("0000320193", "0000320193-25-000079", "annual.htm"),
                body=b'<html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL" xmlns:xbrli="http://www.xbrl.org/2003/instance" xmlns:us-gaap="http://fasb.org/us-gaap/2025"><body><ix:header><xbrli:context id="c1"><xbrli:entity><xbrli:identifier>0000320193</xbrli:identifier></xbrli:entity><xbrli:period><xbrli:instant>2025-09-27</xbrli:instant></xbrli:period></xbrli:context><xbrli:unit id="USD"><xbrli:measure>iso4217:USD</xbrli:measure></xbrli:unit></ix:header><h1>Annual</h1><p><ix:nonfraction name="us-gaap:Revenues" contextRef="c1" unitRef="USD" decimals="0">100</ix:nonfraction></p></body></html>',
            ),
        ),
    )
    paths = _runtime_paths(tmp_path)
    SecPackageStore(paths.raw_store).put(package)
    registry = SQLiteRegistry(paths.registry)
    register_sec_package(registry, package)
    register_sec_slot(registry, package, fiscal_year=2025, period="FY")
    observation = _observation(package)
    registry.register_sec_discovery_observation(observation)
    old_dir = paths.ingest_root / "us" / "p11" / f"{package.package_sha256}.VIRTUAL_HTML_V3"
    old_dir.mkdir(parents=True)
    old_manifest = old_dir / "manifest.json"
    old_manifest.write_text(
        '{"schema_version":"p11-sec-artifacts-v1","parser_version":"VIRTUAL_HTML_V3","package_sha256":"%s"}\n' % package.package_sha256,
        encoding="utf-8",
    )
    old_bytes = old_manifest.read_bytes()
    registry.register_sec_parsed_data(
        parse_run_id="legacy-v3",
        package_sha256=package.package_sha256,
        company_id="US:CIK0000320193",
        fiscal_year=2025,
        period="FY",
        parser_version="VIRTUAL_HTML_V3",
        schema_version="p11-sec-artifacts-v1",
        validation_status="PASS",
        blocking_issue_count=0,
        compatibility_status="COMPATIBLE",
        artifact_path=str(old_dir),
    )
    args = _parser().parse_args(
        ["ingest", "--market", "US", "--cik", "320193", "--ticker", "AAPL", "--year", "2025", "--period", "FY"]
    )
    assert _us_plan_slot(
        sec_company(cik="320193", ticker="AAPL"),
        args,
        paths,
        registry,
        selected_accession=package.accession,
        discovery_state="UNAMBIGUOUS",
    )[0].action.value == "PARSE_LOCAL"

    parsed = parse_sec_package(package, paths.ingest_root / "us" / "p11", discovery_observation=observation)
    validation = validate_sec_artifacts(
        parsed,
        paths.ingest_root / "us" / "p7",
        package=package,
        discovery_observation=observation,
        registry=registry,
    )
    registry.register_sec_parsed_data(
        parse_run_id="current-v5",
        package_sha256=package.package_sha256,
        company_id="US:CIK0000320193",
        fiscal_year=2025,
        period="FY",
        parser_version=VIRTUAL_HTML_NORMALIZER_VERSION,
        schema_version=SEC_ARTIFACT_SCHEMA,
        validation_status=validation.validation_status,
        blocking_issue_count=validation.blocking_issue_count,
        compatibility_status=validation.compatibility_status,
        artifact_path=str(parsed.artifact_dir),
    )

    new_dir = paths.ingest_root / "us" / "p11" / f"{package.package_sha256}.{VIRTUAL_HTML_NORMALIZER_VERSION}"
    assert new_dir.is_dir()
    assert old_manifest.read_bytes() == old_bytes
    assert all(row["parser_version"] != "VIRTUAL_HTML_V3" or row["parse_run_id"] == "legacy-v3" for row in SQLiteRegistry(paths.registry).list_sec_parsed_data(company_id="US:CIK0000320193", fiscal_year=2025, period="FY"))
    rows = SQLiteRegistry(paths.registry).list_sec_parsed_data(company_id="US:CIK0000320193", fiscal_year=2025, period="FY")
    assert any(row["parser_version"] == VIRTUAL_HTML_NORMALIZER_VERSION and row["schema_version"] == SEC_ARTIFACT_SCHEMA for row in rows)

    second_registry = SQLiteRegistry(paths.registry)
    second_plan, _ = _us_plan_slot(
        sec_company(cik="320193", ticker="AAPL"),
        args,
        paths,
        second_registry,
        selected_accession=package.accession,
        discovery_state="UNAMBIGUOUS",
    )
    assert second_plan.action.value == "REUSE_DATA"

