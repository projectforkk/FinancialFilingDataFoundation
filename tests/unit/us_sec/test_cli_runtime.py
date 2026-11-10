from __future__ import annotations

import base64
import json
from pathlib import Path

import pytest

from financial_filing_data_foundation.us_sec.errors import P11Reason, SecError
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
from financial_filing_data_foundation.user_cli import _parser


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
    company, client = _us_company_and_client(args)
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
    company, client = _us_company_and_client(args)
    assert company.cik == "0000055067"
    assert company.ticker_source_sha256 == snapshot.source_sha256
    assert client is None


def test_market_period_validation_is_scoped_before_provider_dispatch() -> None:
    from financial_filing_data_foundation.user_cli import _validate_market_period

    cn_args = _parser().parse_args(["status", "--market", "CN", "--ticker", "000001", "--year", "2025", "--period", "Q2"])
    with pytest.raises(ValueError):
        _validate_market_period(cn_args)
    us_args = _parser().parse_args(["status", "--market", "US", "--cik", "320193", "--year", "2025", "--period", "H1"])
    with pytest.raises(ValueError):
        _validate_market_period(us_args)


def test_us_cli_planner_uses_local_package_and_parsed_data_without_network(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("FFDF_P11_US_DEV", "1")
    monkeypatch.delenv("FFDF_SEC_CONTACT_EMAIL", raising=False)
    monkeypatch.setenv("FFDF_ROOT", str(tmp_path))
    from financial_filing_data_foundation.registry import SQLiteRegistry
    from financial_filing_data_foundation.us_sec.package import SecMemberRole, SecPackageMember, SecPackageStore, build_package
    from financial_filing_data_foundation.us_sec.registry import register_sec_package, register_sec_slot
    from financial_filing_data_foundation.user_cli import _runtime_paths, _us_acquire_result, _us_plan_slot

    package = build_package(
        cik="0000320193", accession="0000320193-25-000079", form="10-K", fiscal_year=2025, period="FY",
        members=(SecPackageMember(relative_name="annual.htm", role=SecMemberRole.PRIMARY_DOCUMENT, content_type="text/html", source_url="https://www.sec.gov/Archives/edgar/data/320193/annual.htm", body=b'<html><body><ix:header><xbrli:context id="c1"><xbrli:entity><xbrli:identifier>0000320193</xbrli:identifier></xbrli:entity><xbrli:period><xbrli:instant>2025-09-27</xbrli:instant></xbrli:period></xbrli:context><xbrli:unit id="USD"><xbrli:measure>iso4217:USD</xbrli:measure></xbrli:unit></ix:header><h1>Annual</h1><p><ix:nonfraction name="us-gaap:Revenues" contextRef="c1" unitRef="USD" decimals="0">100</ix:nonfraction></p></body></html>'),),
    )
    paths = _runtime_paths(tmp_path)
    store = SecPackageStore(paths.raw_store)
    store.put(package)
    registry = SQLiteRegistry(paths.registry)
    register_sec_package(registry, package)
    register_sec_slot(registry, package, fiscal_year=2025, period="FY")
    args = _parser().parse_args(["acquire", "--market", "US", "--cik", "320193", "--year", "2025", "--period", "FY"])
    company, result, _ = _us_acquire_result(args)
    assert company.company_id == "US:CIK0000320193"
    assert result.plan_action == "PARSE_LOCAL"
    parsed = parse_sec_package(package, paths.ingest_root / "us" / "p11")
    validation = validate_sec_artifacts(parsed, paths.ingest_root / "us" / "p7", package=package)
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
            members=(SecPackageMember(relative_name="annual.htm", role=SecMemberRole.PRIMARY_DOCUMENT, content_type="text/html", source_url=f"https://www.sec.gov/Archives/edgar/data/320193/{accession}.htm", body=text),),
        )

    html = b'<html><body><h1>Annual</h1><p><ix:nonfraction name="us-gaap:Revenues" contextRef="c1" unitRef="USD">100</ix:nonfraction></p></body></html>'
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
            members=(SecPackageMember(relative_name="annual.htm", role=SecMemberRole.PRIMARY_DOCUMENT, content_type="text/html", source_url=f"https://www.sec.gov/Archives/edgar/data/320193/{accession}.htm", body=f"<html><body>{accession}</body></html>".encode()),),
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


def test_us_cli_reuse_data_does_not_network_or_rerun_parser(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("FFDF_P11_US_DEV", "1")
    monkeypatch.delenv("FFDF_SEC_CONTACT_EMAIL", raising=False)
    monkeypatch.setenv("FFDF_ROOT", str(tmp_path))
    from financial_filing_data_foundation.user_cli import _us_ingest, _runtime_paths
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
                source_url="https://www.sec.gov/Archives/edgar/data/320193/annual.htm",
                body=b'<html><body><ix:header><xbrli:context id="c1"><xbrli:entity><xbrli:identifier>0000320193</xbrli:identifier></xbrli:entity><xbrli:period><xbrli:instant>2025-09-27</xbrli:instant></xbrli:period></xbrli:context><xbrli:unit id="USD"><xbrli:measure>iso4217:USD</xbrli:measure></xbrli:unit></ix:header><h1>Annual</h1><p><ix:nonfraction name="us-gaap:Revenues" contextRef="c1" unitRef="USD" decimals="0">100</ix:nonfraction></p></body></html>',
            ),
        ),
    )
    initial = ingest_sec_package(package, root=tmp_path, ticker="AAPL", period="FY")
    assert initial.research_ready is True
    paths = _runtime_paths(tmp_path)
    before = tuple(sorted(path.name for path in (paths.ingest_root / "us" / "p11").iterdir()))

    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("network or parser was invoked during REUSE_DATA")

    monkeypatch.setattr("financial_filing_data_foundation.us_sec.ingest.parse_sec_package", forbidden)
    monkeypatch.setattr("financial_filing_data_foundation.us_sec.acquisition.SecAcquirer.acquire", forbidden)
    monkeypatch.setattr("financial_filing_data_foundation.us_sec.http.SecHttpClient.fetch", forbidden)
    args = _parser().parse_args(
        ["ingest", "--market", "US", "--cik", "320193", "--ticker", "AAPL", "--year", "2025", "--period", "FY"]
    )

    assert _us_ingest(args) == 0
    after = tuple(sorted(path.name for path in (paths.ingest_root / "us" / "p11").iterdir()))
    output = json.loads(capsys.readouterr().out)
    assert output["planner_action"] == "REUSE_DATA"
    assert before == after


def test_us_cli_local_v3_upgrade_generates_v4_then_reuses_without_network(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("FFDF_P11_US_DEV", "1")
    monkeypatch.delenv("FFDF_SEC_CONTACT_EMAIL", raising=False)
    monkeypatch.setenv("FFDF_ROOT", str(tmp_path))
    from financial_filing_data_foundation.mcp.catalog import McpCatalog
    from financial_filing_data_foundation.mcp.service import McpQueryService
    from financial_filing_data_foundation.registry import SQLiteRegistry
    from financial_filing_data_foundation.us_sec.identity import sec_company
    from financial_filing_data_foundation.us_sec.package import SecMemberRole, SecPackageMember, SecPackageStore, build_package
    from financial_filing_data_foundation.us_sec.registry import register_sec_package, register_sec_slot
    from financial_filing_data_foundation.user_cli import _runtime_paths, _us_ingest, _us_plan_slot

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
                source_url="https://www.sec.gov/Archives/edgar/data/320193/annual.htm",
                body=b'<html><body><ix:header><xbrli:context id="c1"><xbrli:entity><xbrli:identifier>0000320193</xbrli:identifier></xbrli:entity><xbrli:period><xbrli:instant>2025-09-27</xbrli:instant></xbrli:period></xbrli:context><xbrli:unit id="USD"><xbrli:measure>iso4217:USD</xbrli:measure></xbrli:unit></ix:header><h1>Annual</h1><p><ix:nonfraction name="us-gaap:Revenues" contextRef="c1" unitRef="USD" decimals="0">100</ix:nonfraction></p></body></html>',
            ),
        ),
    )
    paths = _runtime_paths(tmp_path)
    SecPackageStore(paths.raw_store).put(package)
    registry = SQLiteRegistry(paths.registry)
    register_sec_package(registry, package)
    register_sec_slot(registry, package, fiscal_year=2025, period="FY")
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
        schema_version=SEC_ARTIFACT_SCHEMA,
        validation_status="PASS",
        blocking_issue_count=0,
        compatibility_status="COMPATIBLE",
        artifact_path=str(old_dir),
    )
    args = _parser().parse_args(
        ["ingest", "--market", "US", "--cik", "320193", "--ticker", "AAPL", "--year", "2025", "--period", "FY"]
    )

    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("network or acquisition was invoked during local V3 upgrade")

    monkeypatch.setattr("financial_filing_data_foundation.us_sec.acquisition.SecAcquirer.acquire", forbidden)
    monkeypatch.setattr("financial_filing_data_foundation.us_sec.http.SecHttpClient.fetch", forbidden)
    assert _us_plan_slot(
        sec_company(cik="320193", ticker="AAPL", allow_development=True), args, paths, registry
    )[0].action.value == "PARSE_LOCAL"
    assert _us_ingest(args) == 0
    first_output = json.loads(capsys.readouterr().out)

    new_dir = paths.ingest_root / "us" / "p11" / f"{package.package_sha256}.VIRTUAL_HTML_V4"
    assert first_output["planner_action"] == "PARSE_LOCAL"
    assert first_output["validation_status"] == "PASS"
    assert new_dir.is_dir()
    assert old_manifest.read_bytes() == old_bytes
    assert all(row["parser_version"] != "VIRTUAL_HTML_V3" or row["parse_run_id"] == "legacy-v3" for row in SQLiteRegistry(paths.registry).list_sec_parsed_data(company_id="US:CIK0000320193", fiscal_year=2025, period="FY"))
    rows = SQLiteRegistry(paths.registry).list_sec_parsed_data(company_id="US:CIK0000320193", fiscal_year=2025, period="FY")
    assert any(row["parser_version"] == VIRTUAL_HTML_NORMALIZER_VERSION and row["schema_version"] == SEC_ARTIFACT_SCHEMA for row in rows)

    second_registry = SQLiteRegistry(paths.registry)
    second_plan, _ = _us_plan_slot(
        sec_company(cik="320193", ticker="AAPL", allow_development=True), args, paths, second_registry
    )
    assert second_plan.action.value == "REUSE_DATA"
    document = McpQueryService(McpCatalog.load(tmp_path, paths.catalog)).get_document(package.package_sha256)
    assert document["data"]["validation_status"] == "PASS"

