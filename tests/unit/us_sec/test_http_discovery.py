from __future__ import annotations

import json

import pytest

from financial_filing_data_foundation.us_sec.discovery import (
    discover_filings,
    parse_submissions,
)
from financial_filing_data_foundation.us_sec.errors import P11Reason, SecError
from financial_filing_data_foundation.us_sec.http import (
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
        "tickers": ["EXM"],
        "exchanges": ["NASDAQ"],
        "filings": {
            "recent": {
                "accessionNumber": [
                    "0000123456-25-000001",
                    "0000123456-25-000002",
                    "0000123456-25-000003",
                    "0000123456-25-000004",
                ],
                "filingDate": ["2025-02-20", "2025-05-01", "2025-08-01", "2025-08-02"],
                "reportDate": ["2024-12-31", "2025-03-31", "2025-06-30", "2025-06-30"],
                "form": ["10-K", "10-Q", "10-Q", "10-Q/A"],
                "primaryDocument": ["annual.htm", "q1.htm", "q2.htm", "q2-amend.htm"],
                "primaryDocDescription": ["Annual", "Q1", "Q2", "Q2 amended"],
                "items": ["", "", "", "5.07"],
                "size": [100, 100, 100, 100],
                "isXBRL": [1, 1, 1, 1],
                "isInlineXBRL": [1, 1, 1, 1],
                "isXBRL": [1, 1, 1, 1],
                "isXBRL": [1, 1, 1, 1],
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

    with pytest.raises(SecError) as content:
        client.fetch(
            "https://data.sec.gov/submissions/CIK0000123456.json",
            expected_content_types=("application/xml",),
        )
    assert content.value.reason_code == P11Reason.P11_CONTENT_TYPE_INVALID


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

