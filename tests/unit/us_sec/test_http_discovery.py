from __future__ import annotations

import io
import json
from urllib.error import HTTPError

import pytest

from financial_filing_data_foundation.us_sec.discovery import (
    discover_filings,
    parse_submissions,
    select_filing,
    select_history_chunks_for_slot,
)
from financial_filing_data_foundation.us_sec.errors import P11Reason, SecError
from financial_filing_data_foundation.us_sec.http import (
    _AllowlistedRedirectHandler,
    _network_transport,
    SecHttpClient,
    SecHttpConfig,
    SecRateLimiter,
    SecResponse,
    validate_sec_url,
)
from financial_filing_data_foundation.us_sec.identity import sec_company
from financial_filing_data_foundation.us_sec.models import SecIssuerKind


def _submissions() -> dict[str, object]:
    return {
        "name": "Example Corp",
        "cik": "123456789",
        "fiscalYearEnd": "1231",
        "tickers": ["EXM"],
        "exchanges": ["NASDAQ"],
        "filings": {
            "recent": {
                "accessionNumber": [
                    "0000123456-25-000001",
                    "0000123456-25-000002",
                    "0000123456-25-000003",
                    "0000123456-25-000004",
                    "0000123456-25-000005",
                ],
                "filingDate": [
                    "2025-02-20",
                    "2025-05-01",
                    "2025-05-02",
                    "2025-08-01",
                    "2025-11-20",
                ],
                "reportDate": [
                    "2025-03-31",
                    "2025-06-30",
                    "2025-06-30",
                    "2025-09-30",
                    "2025-12-31",
                ],
                "form": ["10-Q", "10-Q", "10-Q/A", "10-Q", "10-K"],
                "primaryDocument": ["q1.htm", "q2.htm", "q2-amend.htm", "q3.htm", "annual.htm"],
                "primaryDocDescription": ["Q1", "Q2", "Q2 amended", "Q3", "Annual"],
                "items": ["", "", "5.07", "", ""],
                "size": [100, 100, 100, 100, 100],
                "isXBRL": [1, 1, 1, 1, 1],
                "isInlineXBRL": [1, 1, 1, 1, 1],
            }
        },
    }


def test_sec_url_allowlist_rejects_arbitrary_hosts_and_paths() -> None:
    validate_sec_url("https://data.sec.gov/submissions/CIK0000123456.json")
    validate_sec_url("https://www.sec.gov/Archives/edgar/data/1/abc/filing.htm")

    with pytest.raises(SecError) as host:
        validate_sec_url("https://example.com/Archives/edgar/data/1/a.htm")
    assert host.value.reason_code == P11Reason.P11_ARCHIVE_HOST_REJECTED

    with pytest.raises(SecError) as path:
        validate_sec_url("https://www.sec.gov/private/filing.htm")
    assert path.value.reason_code == P11Reason.P11_ARCHIVE_HOST_REJECTED


def test_http_client_declares_user_agent_and_enforces_size_and_content_type() -> None:
    requests: list[dict[str, str]] = []

    def transport(url: str, headers: dict[str, str], timeout: float) -> SecResponse:
        requests.append(headers)
        return SecResponse(
            status=200,
            headers={"Content-Type": "application/json"},
            body=b'{"ok":true}',
            final_url=url,
        )

    client = SecHttpClient(
        SecHttpConfig(contact_email="ops@example.org"),
        transport=transport,
    )
    result = client.fetch(
        "https://data.sec.gov/submissions/CIK0000123456.json",
        expected_content_types=("application/json",),
        max_bytes=64,
    )
    assert result.body == b'{"ok":true}'
    assert "FFDF" in requests[0]["User-Agent"]
    assert "ops@example.org" in requests[0]["User-Agent"]
    assert "Accept-Encoding" not in requests[0]

    with pytest.raises(SecError) as content:
        client.fetch(
            "https://data.sec.gov/submissions/CIK0000123456.json",
            expected_content_types=("application/xml",),
        )
    assert content.value.reason_code == P11Reason.P11_CONTENT_TYPE_INVALID


def test_http_config_exposes_connect_read_and_total_timeouts() -> None:
    config = SecHttpConfig(
        contact_email="ops@example.org",
        connect_timeout_seconds=1.0,
        read_timeout_seconds=2.0,
        total_timeout_seconds=5.0,
    )
    assert (config.connect_timeout_seconds, config.read_timeout_seconds, config.total_timeout_seconds) == (1.0, 2.0, 5.0)
    with pytest.raises(ValueError):
        SecHttpConfig(contact_email="ops@example.org", connect_timeout_seconds=2.0, read_timeout_seconds=3.0, total_timeout_seconds=1.0)


def test_http_client_rejects_unhandled_content_encoding() -> None:
    def transport(url: str, headers: dict[str, str], timeout: float) -> SecResponse:
        return SecResponse(200, {"Content-Encoding": "gzip"}, b"compressed", url)

    client = SecHttpClient(SecHttpConfig(contact_email="ops@example.org"), transport=transport)
    with pytest.raises(SecError) as error:
        client.fetch("https://data.sec.gov/submissions/CIK0000123456.json")
    assert error.value.reason_code == P11Reason.P11_CONTENT_ENCODING_UNSUPPORTED


def test_rate_limiter_and_retry_after_are_deterministic() -> None:
    now = [0.0]
    sleeps: list[float] = []

    def clock() -> float:
        return now[0]

    def sleep(seconds: float) -> None:
        sleeps.append(seconds)
        now[0] += seconds

    limiter = SecRateLimiter(8.0, clock=clock, sleep=sleep)
    limiter.wait()
    limiter.wait()
    assert sleeps == [pytest.approx(0.125)]

    calls = [0]

    def transport(url: str, headers: dict[str, str], timeout: float) -> SecResponse:
        calls[0] += 1
        if calls[0] == 1:
            return SecResponse(429, {"Retry-After": "2"}, b"", url)
        return SecResponse(200, {"Content-Type": "application/json"}, b"{}", url)

    client = SecHttpClient(
        SecHttpConfig(contact_email="ops@example.org", max_attempts=2),
        transport=transport,
        limiter=SecRateLimiter(8.0, clock=clock, sleep=sleep),
        sleep=sleep,
    )
    client.fetch(
        "https://data.sec.gov/submissions/CIK0000123456.json",
        expected_content_types=("application/json",),
    )
    assert calls[0] == 2
    assert 2.0 in sleeps


def test_ticker_mapping_and_submission_discovery_are_fail_closed() -> None:
    mapping = json.dumps(
        {
            "0": {"cik_str": 123456789, "ticker": "EXM", "title": "Example Corp"},
            "1": {"cik_str": 987654321, "ticker": "EXM", "title": "Other Corp"},
        }
    ).encode()
    from financial_filing_data_foundation.us_sec.ticker_map import parse_ticker_map

    with pytest.raises(SecError) as ambiguous:
        parse_ticker_map(mapping, "EXM")
    assert ambiguous.value.reason_code == P11Reason.P11_TICKER_CIK_AMBIGUOUS

    company = sec_company(cik="123456789", ticker="EXM", allow_development=True)
    assert company.issuer_kind is SecIssuerKind.UNKNOWN
    result = parse_submissions(_submissions(), company=company)
    candidates = discover_filings(
        result,
        fiscal_year=2025,
        period="Q2",
    )
    assert len(candidates) == 2
    assert {item.amended for item in candidates} == {False, True}


def test_unrelated_nested_sec_primary_document_does_not_poison_periodic_discovery() -> None:
    payload = _submissions()
    filings = payload["filings"]["recent"]  # type: ignore[index]
    for key, value in {
        "accessionNumber": "0000123456-25-000006",
        "filingDate": "2025-12-01",
        "reportDate": "2025-12-01",
        "form": "4",
        "primaryDocument": "xslF345X06/form4.xml",
    }.items():
        filings[key].append(value)  # type: ignore[index]
    company = sec_company(cik="123456789", ticker="EXM", allow_development=True)
    submissions = parse_submissions(payload, company=company)
    candidates = discover_filings(submissions, fiscal_year=2025, period="Q2")
    assert len(candidates) == 2
    assert all(candidate.primary_document != "xslF345X06/form4.xml" for candidate in candidates)


@pytest.mark.parametrize("unsafe", ["../filing.htm", "/filing.htm", "C:/filing.htm", "x\\filing.htm", "https://evil.example/filing.htm", "%2e%2e/filing.htm"])
def test_supported_filing_primary_document_path_traversal_is_rejected(unsafe: str) -> None:
    payload = _submissions()
    payload["filings"]["recent"]["primaryDocument"][0] = unsafe  # type: ignore[index]
    company = sec_company(cik="123456789", ticker="EXM", allow_development=True)
    with pytest.raises(SecError) as exc_info:
        parse_submissions(payload, company=company)
    assert exc_info.value.reason_code == P11Reason.P11_SEC_DISCOVERY_FAILED.value


def test_history_chunk_ranges_are_preserved_and_only_complete_minimal_chunks_are_selected() -> None:
    payload = _submissions()
    payload["filings"]["files"] = [  # type: ignore[index]
        {"name": "CIK123456789-2018.json", "filingFrom": "2018-01-01", "filingTo": "2018-12-31"},
        {"name": "CIK123456789-2024.json", "filingFrom": "2024-01-01", "filingTo": "2024-12-31"},
        {"name": "CIK123456789-2026.json", "filingFrom": "2026-01-01", "filingTo": "2026-12-31"},
    ]
    company = sec_company(cik="123456789", ticker="EXM", allow_development=True)
    submissions = parse_submissions(payload, company=company)
    assert submissions.history_ranges[1].filing_from == "2024-01-01"
    selected = select_history_chunks_for_slot(submissions, 2025)
    assert [chunk.name for chunk in selected] == [
        "CIK123456789-2024.json",
        "CIK123456789-2026.json",
    ]


def test_history_selector_includes_missing_range_conservatively() -> None:
    payload = _submissions()
    payload["filings"]["files"] = [  # type: ignore[index]
        {"name": "CIK123456789-2018.json", "filingFrom": "2018-01-01", "filingTo": "2018-12-31"},
        {"name": "CIK123456789-unknown.json"},
        {"name": "CIK123456789-2026.json", "filingFrom": "2026-01-01", "filingTo": "2026-12-31"},
    ]
    company = sec_company(cik="123456789", ticker="EXM", allow_development=True)
    submissions = parse_submissions(payload, company=company)

    selected = select_history_chunks_for_slot(submissions, 2025)

    assert [chunk.name for chunk in selected] == [
        "CIK123456789-2026.json",
        "CIK123456789-unknown.json",
    ]


@pytest.mark.parametrize(
    "files",
    [
        [{"name": "bad.json", "filingFrom": "not-a-date", "filingTo": "2025-12-31"}],
        [{"name": "bad.json", "filingFrom": "2026-01-01", "filingTo": "2025-12-31"}],
    ],
)
def test_history_selector_rejects_malformed_or_reversed_ranges(files: list[dict[str, str]]) -> None:
    payload = _submissions()
    payload["filings"]["files"] = files  # type: ignore[index]
    company = sec_company(cik="123456789", ticker="EXM", allow_development=True)
    submissions = parse_submissions(payload, company=company)

    with pytest.raises(SecError) as exc_info:
        select_history_chunks_for_slot(submissions, 2025)

    assert exc_info.value.reason_code == P11Reason.P11_SEC_DISCOVERY_FAILED.value


def test_discovery_uses_fiscal_year_end_and_chronology_for_non_calendar_issuers() -> None:
    payload = {
        "cik": "0000123456",
        "fiscalYearEnd": "0930",
        "filings": {
            "recent": {
                "accessionNumber": [
                    "0000123456-25-000001",
                    "0000123456-25-000002",
                    "0000123456-25-000003",
                    "0000123456-25-000004",
                ],
                "filingDate": ["2025-02-01", "2025-05-01", "2025-08-01", "2025-11-20"],
                "reportDate": ["2024-12-28", "2025-03-29", "2025-06-28", "2025-09-27"],
                "form": ["10-Q", "10-Q", "10-Q", "10-K"],
                "primaryDocument": ["q1.htm", "q2.htm", "q3.htm", "annual.htm"],
            }
        },
    }
    company = sec_company(cik="123456", ticker="EXM", allow_development=True)
    submissions = parse_submissions(payload, company=company)

    assert discover_filings(submissions, fiscal_year=2025, period="Q1")[0].report_period == "2024-12-28"
    assert discover_filings(submissions, fiscal_year=2025, period="Q2")[0].report_period == "2025-03-29"
    assert discover_filings(submissions, fiscal_year=2025, period="Q3")[0].report_period == "2025-06-28"
    assert discover_filings(submissions, fiscal_year=2025, period="FY")[0].report_period == "2025-09-27"


def _rolling_53_week_submissions() -> dict[str, object]:
    rows = [
        ("0000123456-23-000001", "2023-11-03", "2023-09-30", "10-K", "fy23.htm"),
        ("0000123456-24-000001", "2024-02-01", "2023-12-30", "10-Q", "q1-24.htm"),
        ("0000123456-24-000002", "2024-05-01", "2024-03-30", "10-Q", "q2-24.htm"),
        ("0000123456-24-000003", "2024-08-01", "2024-06-29", "10-Q", "q3-24.htm"),
        ("0000123456-24-000004", "2024-11-01", "2024-09-28", "10-K", "fy24.htm"),
        ("0000123456-25-000001", "2025-02-01", "2024-12-28", "10-Q", "q1-25.htm"),
        ("0000123456-25-000002", "2025-05-01", "2025-03-29", "10-Q", "q2-25.htm"),
        ("0000123456-25-000003", "2025-08-01", "2025-06-28", "10-Q", "q3-25.htm"),
        ("0000123456-25-000004", "2025-10-31", "2025-09-27", "10-K", "fy25.htm"),
        ("0000123456-26-000001", "2026-10-30", "2026-09-26", "10-K", "fy26.htm"),
    ]
    return {
        "cik": "0000123456",
        "fiscalYearEnd": "0926",
        "filings": {
            "recent": {
                "accessionNumber": [row[0] for row in rows],
                "filingDate": [row[1] for row in rows],
                "reportDate": [row[2] for row in rows],
                "form": [row[3] for row in rows],
                "primaryDocument": [row[4] for row in rows],
            }
        },
    }


def test_discovery_uses_exact_historical_annual_end_for_53_week_fiscal_year() -> None:
    company = sec_company(cik="123456", ticker="ROLL", allow_development=True)
    submissions = parse_submissions(_rolling_53_week_submissions(), company=company)

    assert discover_filings(submissions, fiscal_year=2024, period="FY")[0].report_period == "2024-09-28"
    assert discover_filings(submissions, fiscal_year=2024, period="Q1")[0].report_period == "2023-12-30"
    assert discover_filings(submissions, fiscal_year=2024, period="Q2")[0].report_period == "2024-03-30"
    assert discover_filings(submissions, fiscal_year=2024, period="Q3")[0].report_period == "2024-06-29"
    assert discover_filings(submissions, fiscal_year=2025, period="FY")[0].report_period == "2025-09-27"


def test_discovery_resolves_historical_quarters_by_chronology_not_duration_ratio() -> None:
    company = sec_company(cik="123456", ticker="ROLL", allow_development=True)
    submissions = parse_submissions(_rolling_53_week_submissions(), company=company)

    resolved = [
        discover_filings(submissions, fiscal_year=2025, period=period)[0].report_period
        for period in ("Q1", "Q2", "Q3")
    ]
    assert resolved == ["2024-12-28", "2025-03-29", "2025-06-28"]


def test_discovery_handles_in_progress_non_calendar_fiscal_year_by_chronology() -> None:
    payload = {
        "cik": "0000123456",
        "fiscalYearEnd": "0925",
        "filings": {
            "recent": {
                "accessionNumber": [
                    "0000123456-26-000001",
                    "0000123456-27-000001",
                    "0000123456-27-000002",
                ],
                "filingDate": ["2026-10-30", "2027-02-01", "2027-05-01"],
                "reportDate": ["2026-09-26", "2026-12-26", "2027-03-27"],
                "form": ["10-K", "10-Q", "10-Q"],
                "primaryDocument": ["fy26.htm", "q1-27.htm", "q2-27.htm"],
            }
        },
    }
    company = sec_company(cik="123456", ticker="ROLL", allow_development=True)
    submissions = parse_submissions(payload, company=company)

    assert discover_filings(submissions, fiscal_year=2027, period="Q1")[0].report_period == "2026-12-26"
    assert discover_filings(submissions, fiscal_year=2027, period="Q2")[0].report_period == "2027-03-27"
    assert discover_filings(submissions, fiscal_year=2027, period="FY") == ()


def test_historical_year_missing_target_annual_does_not_use_in_progress_fallback() -> None:
    payload = {
        "cik": "0000123456",
        "fiscalYearEnd": "0926",
        "filings": {
            "recent": {
                "accessionNumber": [
                    "0000123456-23-000001",
                    "0000123456-24-000001",
                    "0000123456-24-000002",
                    "0000123456-24-000003",
                    "0000123456-25-000001",
                ],
                "filingDate": [
                    "2023-11-03",
                    "2024-02-01",
                    "2024-05-01",
                    "2024-08-01",
                    "2025-10-31",
                ],
                "reportDate": [
                    "2023-09-30",
                    "2023-12-30",
                    "2024-03-30",
                    "2024-06-29",
                    "2025-09-27",
                ],
                "form": ["10-K", "10-Q", "10-Q", "10-Q", "10-K"],
                "primaryDocument": ["fy23.htm", "q1-24.htm", "q2-24.htm", "q3-24.htm", "fy25.htm"],
            }
        },
    }
    company = sec_company(cik="123456", ticker="ROLL", allow_development=True)
    submissions = parse_submissions(payload, company=company)

    for period in ("Q1", "Q2", "Q3", "FY"):
        assert discover_filings(submissions, fiscal_year=2024, period=period) == ()


def test_discovery_groups_amendment_with_same_report_period() -> None:
    payload = {
        "cik": "0000123456",
        "fiscalYearEnd": "1231",
        "filings": {
            "recent": {
                "accessionNumber": [
                    "0000123456-23-000001",
                    "0000123456-24-000001",
                    "0000123456-24-000002",
                    "0000123456-24-000003",
                    "0000123456-24-000004",
                    "0000123456-24-000005",
                ],
                "filingDate": [
                    "2023-11-01",
                    "2024-02-01",
                    "2024-05-01",
                    "2024-05-05",
                    "2024-08-01",
                    "2025-02-01",
                ],
                "reportDate": [
                    "2023-12-31",
                    "2024-03-31",
                    "2024-06-30",
                    "2024-06-30",
                    "2024-09-30",
                    "2024-12-31",
                ],
                "form": ["10-K", "10-Q", "10-Q", "10-Q/A", "10-Q", "10-K"],
                "primaryDocument": ["fy23.htm", "q1.htm", "q2.htm", "q2a.htm", "q3.htm", "fy24.htm"],
            }
        },
    }
    company = sec_company(cik="123456", ticker="CAL", allow_development=True)
    submissions = parse_submissions(payload, company=company)

    assert discover_filings(submissions, fiscal_year=2024, period="Q1")[0].report_period == "2024-03-31"
    candidates = discover_filings(submissions, fiscal_year=2024, period="Q2")
    assert len(candidates) == 2
    assert {candidate.report_period for candidate in candidates} == {"2024-06-30"}
    assert discover_filings(submissions, fiscal_year=2024, period="Q3")[0].report_period == "2024-09-30"
    assert discover_filings(submissions, fiscal_year=2024, period="FY")[0].report_period == "2024-12-31"
    with pytest.raises(SecError) as error:
        select_filing(candidates)
    assert error.value.reason_code == P11Reason.P11_AMENDED_VARIANT_PRESENT


def test_discovery_uses_exact_fpi_annual_endpoint_for_history() -> None:
    payload = {
        "cik": "0000000001",
        "fiscalYearEnd": "0627",
        "filings": {
            "recent": {
                "accessionNumber": [
                    "0000000001-23-000001",
                    "0000000001-24-000001",
                    "0000000001-25-000001",
                ],
                "filingDate": ["2023-09-01", "2024-09-01", "2025-09-01"],
                "reportDate": ["2023-06-30", "2024-06-29", "2025-06-28"],
                "form": ["20-F", "20-F", "20-F"],
                "primaryDocument": ["fy23.htm", "fy24.htm", "fy25.htm"],
            }
        },
    }
    company = sec_company(cik="1", ticker="FPI", allow_development=True)
    submissions = parse_submissions(payload, company=company)

    annual = discover_filings(submissions, fiscal_year=2024, period="FY")
    assert len(annual) == 1
    assert annual[0].report_period == "2024-06-29"


def test_discovery_supports_fpi_non_december_fiscal_year() -> None:
    payload = {
        "cik": "0000000001",
        "fiscalYearEnd": "0630",
        "filings": {
            "recent": {
                "accessionNumber": ["0000000001-25-000001"],
                "filingDate": ["2025-09-15"],
                "reportDate": ["2025-06-28"],
                "form": ["20-F"],
                "primaryDocument": ["annual20.htm"],
            }
        },
    }
    company = sec_company(cik="1", ticker="FPI", allow_development=True)
    submissions = parse_submissions(payload, company=company)

    annual = discover_filings(submissions, fiscal_year=2025, period="FY")
    assert len(annual) == 1
    assert annual[0].form == "20-F"


def test_redirect_handler_checks_each_hop_and_configures_redirect_limit() -> None:
    from urllib.request import Request

    handler = _AllowlistedRedirectHandler(max_redirects=1)
    request = Request("https://www.sec.gov/Archives/edgar/data/1/a.htm")
    assert handler.max_redirections == 1
    assert handler.redirect_request(
        request,
        None,
        302,
        "Found",
        {},
        "https://www.sec.gov/Archives/edgar/data/1/b.htm",
    ) is not None

    with pytest.raises(SecError) as rejected:
        handler.redirect_request(
            request,
            None,
            302,
            "Found",
            {},
            "https://example.com/Archives/edgar/data/1/b.htm",
        )
    assert rejected.value.reason_code == P11Reason.P11_ARCHIVE_HOST_REJECTED


def test_network_transport_enforces_redirect_limit_and_bounded_error_body(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[object] = []

    class Opener:
        def open(self, request: object, timeout: float) -> object:
            raise __import__("urllib.error", fromlist=["HTTPError"]).HTTPError(
                "https://www.sec.gov/Archives/edgar/data/1/a.htm",
                302,
                "redirect limit exceeded",
                {},
                __import__("io").BytesIO(b"too much error body"),
            )

    def build(handler: object) -> Opener:
        captured.append(handler)
        return Opener()

    monkeypatch.setattr("financial_filing_data_foundation.us_sec.http.build_opener", build)
    with pytest.raises(SecError) as redirected:
        _network_transport(
            "https://www.sec.gov/Archives/edgar/data/1/a.htm",
            {},
            1.0,
            max_bytes=4,
            max_redirects=2,
        )
    assert redirected.value.reason_code == P11Reason.P11_SEC_REDIRECT_LIMIT_EXCEEDED
    assert getattr(captured[0], "max_redirections") == 2


def test_network_transport_bounds_non_redirect_http_error_body(monkeypatch: pytest.MonkeyPatch) -> None:
    class Opener:
        def open(self, request: object, timeout: float) -> object:
            raise HTTPError(
                "https://www.sec.gov/Archives/edgar/data/1/a.htm",
                500,
                "server error",
                {},
                io.BytesIO(b"0123456789"),
            )

    monkeypatch.setattr(
        "financial_filing_data_foundation.us_sec.http.build_opener",
        lambda handler: Opener(),
    )
    with pytest.raises(SecError) as error:
        _network_transport(
            "https://www.sec.gov/Archives/edgar/data/1/a.htm",
            {},
            1.0,
            max_bytes=4,
        )
    assert error.value.reason_code == P11Reason.P11_SIZE_LIMIT_EXCEEDED


def test_fpi_20f_and_40f_are_annual_candidates_only() -> None:
    payload = {
        "cik": "0000000001",
        "filings": {
            "recent": {
                "accessionNumber": ["0000000001-25-000001", "0000000001-25-000002"],
                "filingDate": ["2025-03-01", "2025-03-02"],
                "reportDate": ["2024-12-31", "2024-12-31"],
                "form": ["20-F", "40-F"],
                "primaryDocument": ["annual20.htm", "annual40.htm"],
            }
        },
    }
    company = sec_company(cik="1", ticker="FPI", allow_development=True)
    submissions = parse_submissions(payload, company=company)
    annual = discover_filings(submissions, fiscal_year=2024, period="FY")
    assert {candidate.form for candidate in annual} == {"20-F", "40-F"}

