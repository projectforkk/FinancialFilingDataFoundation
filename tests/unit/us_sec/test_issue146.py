from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from financial_filing_data_foundation.registry import SQLiteRegistry
from financial_filing_data_foundation.us_sec.discovery import SecDiscoveryObservation, parse_submissions
from financial_filing_data_foundation.us_sec.errors import SecError
from financial_filing_data_foundation.us_sec.http import SecHttpConfig, SecResponse
from financial_filing_data_foundation.us_sec.models import SecCompanyRef
from financial_filing_data_foundation.us_sec.package import SecMemberRole, SecPackageMember, build_package
from financial_filing_data_foundation.us_sec.parser import VIRTUAL_HTML_NORMALIZER_VERSION
from financial_filing_data_foundation.us_sec.registry import register_sec_parsed_run
from financial_filing_data_foundation.us_sec.validation import load_sec_validation
from financial_filing_data_foundation.us_sec.planner import SecPlanAction, plan_sec_slot
from financial_filing_data_foundation.user_cli import _parser, _runtime_paths, _us_ingest


CIK = "0000320193"
COMPANY_ID = f"US:CIK{CIK}"
ACCESSION = "0000320193-25-000079"
SUBMISSIONS_URL = f"https://data.sec.gov/submissions/CIK{CIK}.json"


def _package() -> object:
    body = (
        '<html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL" '
        'xmlns:xbrli="http://www.xbrl.org/2003/instance" '
        'xmlns:us-gaap="http://fasb.org/us-gaap/2025">'
        "<body><ix:header>"
        "<xbrli:context id='c1'><xbrli:entity><xbrli:identifier>0000320193</xbrli:identifier>"
        "</xbrli:entity><xbrli:period><xbrli:instant>2025-09-27</xbrli:instant>"
        "</xbrli:period></xbrli:context>"
        "<xbrli:unit id='USD'><xbrli:measure>iso4217:USD</xbrli:measure></xbrli:unit>"
        "</ix:header><h1>Annual</h1><p>Revenue: "
        "<ix:nonfraction name='us-gaap:Revenues' contextRef='c1' unitRef='USD' decimals='0'>100</ix:nonfraction>"
        "</p></body></html>"
    ).encode("utf-8")
    return build_package(
        cik=CIK,
        accession=ACCESSION,
        form="10-K",
        fiscal_year=2025,
        period="FY",
        filing_date="2025-11-01",
        report_period="2025-09-27",
        members=(
            SecPackageMember(
                relative_name="annual.htm",
                role=SecMemberRole.PRIMARY_DOCUMENT,
                content_type="text/html",
                source_url=f"https://www.sec.gov/Archives/edgar/data/{int(CIK)}/{ACCESSION.replace('-', '')}/annual.htm",
                body=body,
            ),
        ),
    )


def _observation(package: object, *, retrieved_at: str) -> SecDiscoveryObservation:
    source = {
        "cik": CIK,
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
    }
    company = SecCompanyRef(cik=CIK, ticker="AAPL", company_id=COMPANY_ID)
    body = json.dumps(source, sort_keys=True).encode("utf-8")
    candidates = parse_submissions(source, company=company, source_url=SUBMISSIONS_URL).candidates
    return SecDiscoveryObservation.create(
        company=company,
        fiscal_year=2025,
        period="FY",
        source_documents=[{"url": SUBMISSIONS_URL, "body": body}],
        candidates=candidates,
        selected_accession=package.accession,
        state="UNAMBIGUOUS",
        retrieved_at=retrieved_at,
    )


def _args() -> object:
    return _parser().parse_args(
        [
            "ingest",
            "--market",
            "US",
            "--cik",
            "320193",
            "--ticker",
            "AAPL",
            "--year",
            "2025",
            "--period",
            "FY",
        ]
    )


def _freshness_client(monkeypatch: pytest.MonkeyPatch, submissions: dict[str, object]) -> list[str]:
    calls: list[str] = []
    body = json.dumps(submissions, sort_keys=True).encode("utf-8")

    class FreshnessClient:
        config = SecHttpConfig(contact_email="ops@example.org")

        def fetch(self, url: str, **_: object) -> SecResponse:
            calls.append(url)
            assert url == SUBMISSIONS_URL
            return SecResponse(200, {"Content-Type": "application/json"}, body, url)

    monkeypatch.setattr(
        "financial_filing_data_foundation.user_cli.SecHttpClient",
        lambda *_args, **_kwargs: FreshnessClient(),
    )
    return calls


def _submissions(package: object) -> dict[str, object]:
    return {
        "cik": CIK,
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
    }


def _tree_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file()
    }


def _move_current_v3_to_legacy_v2(result: object) -> dict[str, bytes]:
    current_dir = result.validation.artifact_dir
    legacy_dir = current_dir.parent
    report = json.loads((current_dir / "validation.json").read_text(encoding="utf-8"))
    report["schema_version"] = "p11-sec-validation-v2"
    (legacy_dir / "validation.json").write_text(
        json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    shutil.copyfile(current_dir / "issues.jsonl", legacy_dir / "issues.jsonl")
    shutil.rmtree(current_dir)
    return {
        "validation.json": (legacy_dir / "validation.json").read_bytes(),
        "issues.jsonl": (legacy_dir / "issues.jsonl").read_bytes(),
    }


def _stale_registry_row(root: Path, result: object) -> None:
    registry = SQLiteRegistry(_runtime_paths(root).registry)
    parse_run_id = hashlib.sha256(
        f"{result.package.package_sha256}|{result.parsed.parser_version}".encode()
    ).hexdigest()
    register_sec_parsed_run(
        registry,
        parse_run_id=parse_run_id,
        package_sha256=result.package.package_sha256,
        company_id=COMPANY_ID,
        fiscal_year=2025,
        period="FY",
        parser_version=result.parsed.parser_version,
        schema_version="p11-sec-artifacts-v2",
        validation_status="REVIEW_REQUIRED",
        compatibility_status="INCOMPATIBLE",
        blocking_issue_count=7,
        artifact_path=str(result.parsed.artifact_dir),
    )


def test_t146_migration_revalidates_without_parser_and_preserves_legacy_bytes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("FFDF_P11_US_DEV", raising=False)
    monkeypatch.setenv("FFDF_ROOT", str(tmp_path))
    package = _package()
    initial_observation = _observation(package, retrieved_at="2026-11-13T00:00:00+00:00")
    from financial_filing_data_foundation.us_sec.ingest import ingest_sec_package

    initial = ingest_sec_package(
        package,
        root=tmp_path,
        ticker="AAPL",
        period="FY",
        discovery_observation=initial_observation,
    )
    paths = _runtime_paths(tmp_path)
    raw_hashes = _tree_hashes(paths.raw_store / "packages")
    parsed_hashes = _tree_hashes(initial.parsed.artifact_dir)
    legacy_hashes = _move_current_v3_to_legacy_v2(initial)
    _stale_registry_row(tmp_path, initial)
    parser_calls = 0

    def forbidden_parser(*_args: object, **_kwargs: object) -> object:
        nonlocal parser_calls
        parser_calls += 1
        raise AssertionError("REVALIDATE_LOCAL must not invoke parse_sec_package")

    monkeypatch.setattr("financial_filing_data_foundation.us_sec.ingest.parse_sec_package", forbidden_parser)
    calls = _freshness_client(monkeypatch, _submissions(package))

    assert _us_ingest(_args()) == 0
    output = json.loads(capsys.readouterr().out)
    current_dir = paths.ingest_root / "us" / "p7" / package.package_sha256 / "p11-sec-validation-v3"
    loaded = load_sec_validation(current_dir)
    registry = SQLiteRegistry(paths.registry)
    latest_observation = registry.latest_sec_discovery_observation(
        company_id=COMPANY_ID,
        fiscal_year=2025,
        period="FY",
    )
    row = next(
        row
        for row in registry.list_sec_parsed_data(
            company_id=COMPANY_ID,
            fiscal_year=2025,
            period="FY",
        )
        if row["package_sha256"] == package.package_sha256
    )
    catalog = json.loads(initial.catalog_path.read_text(encoding="utf-8"))

    assert output["planner_action"] == "REVALIDATE_LOCAL"
    assert parser_calls == 0
    assert calls == [SUBMISSIONS_URL]
    assert _tree_hashes(paths.raw_store / "packages") == raw_hashes
    assert _tree_hashes(initial.parsed.artifact_dir) == parsed_hashes
    assert {name: (current_dir.parent / name).read_bytes() for name in legacy_hashes} == legacy_hashes
    assert latest_observation is not None
    assert loaded.discovery_observation_sha256 == latest_observation["observation_sha256"]
    assert loaded.reuse_eligible is True
    assert row["parse_run_id"] == hashlib.sha256(
        f"{package.package_sha256}|{VIRTUAL_HTML_NORMALIZER_VERSION}".encode()
    ).hexdigest()
    assert row["validation_status"] == "PASS"
    assert row["compatibility_status"] == "COMPATIBLE"
    assert row["blocking_issue_count"] == 0
    assert row["artifact_path"] == str(initial.parsed.artifact_dir)
    assert catalog["documents"][0]["discovery_observation_sha256"] == latest_observation["observation_sha256"]
    assert output["research_ready"] is True


def test_t146_corrupt_current_v3_fails_closed_without_v2_fallback(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("FFDF_P11_US_DEV", raising=False)
    monkeypatch.setenv("FFDF_ROOT", str(tmp_path))
    package = _package()
    from financial_filing_data_foundation.us_sec.ingest import ingest_sec_package

    initial = ingest_sec_package(
        package,
        root=tmp_path,
        ticker="AAPL",
        period="FY",
        discovery_observation=_observation(package, retrieved_at="2026-11-13T00:00:00+00:00"),
    )
    paths = _runtime_paths(tmp_path)
    legacy_hashes = _move_current_v3_to_legacy_v2(initial)
    current_dir = paths.ingest_root / "us" / "p7" / package.package_sha256 / "p11-sec-validation-v3"
    current_dir.mkdir(parents=True)
    corrupt_report = current_dir / "validation.json"
    corrupt_report.write_bytes(b"not-json")
    before = corrupt_report.read_bytes()
    parser_calls = 0

    def forbidden_parser(*_args: object, **_kwargs: object) -> object:
        nonlocal parser_calls
        parser_calls += 1
        raise AssertionError("corrupt v3 must fail before parser execution")

    monkeypatch.setattr("financial_filing_data_foundation.us_sec.ingest.parse_sec_package", forbidden_parser)
    _freshness_client(monkeypatch, _submissions(package))

    with pytest.raises(SecError) as exc_info:
        _us_ingest(_args())

    assert exc_info.value.reason_code == "P11_PACKAGE_INVALID"
    assert parser_calls == 0
    assert corrupt_report.read_bytes() == before
    assert {name: (current_dir.parent / name).read_bytes() for name in legacy_hashes} == legacy_hashes


def test_t146_reuse_data_refreshes_registry_from_fresh_v3_without_parser(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("FFDF_P11_US_DEV", raising=False)
    monkeypatch.setenv("FFDF_ROOT", str(tmp_path))
    package = _package()
    from financial_filing_data_foundation.us_sec.ingest import ingest_sec_package

    initial = ingest_sec_package(
        package,
        root=tmp_path,
        ticker="AAPL",
        period="FY",
        discovery_observation=_observation(package, retrieved_at="2026-11-13T00:00:00+00:00"),
    )
    parsed_hashes = _tree_hashes(initial.parsed.artifact_dir)
    _stale_registry_row(tmp_path, initial)
    parser_calls = 0

    def forbidden_parser(*_args: object, **_kwargs: object) -> object:
        nonlocal parser_calls
        parser_calls += 1
        raise AssertionError("REUSE_DATA refresh must not invoke parse_sec_package")

    monkeypatch.setattr("financial_filing_data_foundation.us_sec.ingest.parse_sec_package", forbidden_parser)
    _freshness_client(monkeypatch, _submissions(package))

    assert _us_ingest(_args()) == 0
    output = json.loads(capsys.readouterr().out)
    paths = _runtime_paths(tmp_path)
    registry = SQLiteRegistry(paths.registry)
    latest_observation = registry.latest_sec_discovery_observation(
        company_id=COMPANY_ID,
        fiscal_year=2025,
        period="FY",
    )
    row = next(
        row
        for row in registry.list_sec_parsed_data(
            company_id=COMPANY_ID,
            fiscal_year=2025,
            period="FY",
        )
        if row["package_sha256"] == package.package_sha256
    )
    loaded = load_sec_validation(paths.ingest_root / "us" / "p7" / package.package_sha256)

    assert output["planner_action"] == "REUSE_DATA"
    assert output["research_ready"] is True
    assert parser_calls == 0
    assert _tree_hashes(initial.parsed.artifact_dir) == parsed_hashes
    assert latest_observation is not None
    assert loaded.discovery_observation_sha256 == latest_observation["observation_sha256"]
    assert row["validation_status"] == "PASS"
    assert row["compatibility_status"] == "COMPATIBLE"
    assert row["blocking_issue_count"] == 0


@pytest.mark.parametrize(
    ("parsed_available", "package_available", "validation_reuse_eligible", "expected"),
    [
        (True, True, True, SecPlanAction.REUSE_DATA),
        (True, True, False, SecPlanAction.REVALIDATE_LOCAL),
        (True, False, False, SecPlanAction.REVALIDATE_LOCAL),
        (False, True, False, SecPlanAction.PARSE_LOCAL),
        (False, False, False, SecPlanAction.DISCOVER_AND_ACQUIRE),
    ],
)
def test_t146_planner_separates_parsed_compatibility_from_v3_reuse(
    parsed_available: bool,
    package_available: bool,
    validation_reuse_eligible: bool,
    expected: SecPlanAction,
) -> None:
    plan = plan_sec_slot(
        parsed_available=parsed_available,
        package_available=package_available,
        validation_reuse_eligible=validation_reuse_eligible,
    )

    assert plan.action is expected


def test_t146_planner_preserves_amendment_conflict() -> None:
    plan = plan_sec_slot(
        parsed_available=True,
        package_available=True,
        validation_reuse_eligible=True,
        amendment_conflict=True,
    )

    assert plan.action is SecPlanAction.REVIEW_REQUIRED
