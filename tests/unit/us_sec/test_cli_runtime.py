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
        members=(SecPackageMember(relative_name="annual.htm", role=SecMemberRole.PRIMARY_DOCUMENT, content_type="text/html", source_url="https://www.sec.gov/Archives/edgar/data/320193/annual.htm", body=b"<html><body><p>annual</p></body></html>"),),
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
    (tmp_path / "parsed").mkdir()
    registry.register_sec_parsed_data(parse_run_id="run1", package_sha256=package.package_sha256, company_id=company.company_id, fiscal_year=2025, period="FY", parser_version="V3", schema_version="p11-sec-artifacts-v1", validation_status="PASS", blocking_issue_count=0, compatibility_status="INCOMPATIBLE", artifact_path=str(tmp_path / "parsed"))
    plan, _ = _us_plan_slot(company, args, paths, registry)
    assert plan.action.value == "PARSE_LOCAL"
    registry.register_sec_parsed_data(parse_run_id="run2", package_sha256=package.package_sha256, company_id=company.company_id, fiscal_year=2025, period="FY", parser_version="V3", schema_version="p11-sec-artifacts-v1", validation_status="PASS", blocking_issue_count=0, compatibility_status="COMPATIBLE", artifact_path=str(tmp_path / "parsed"))
    plan, _ = _us_plan_slot(company, args, paths, registry)
    assert plan.action.value == "REUSE_DATA"

