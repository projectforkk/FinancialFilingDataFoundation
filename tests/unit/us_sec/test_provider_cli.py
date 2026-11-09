from __future__ import annotations

import json
from pathlib import Path

import pytest

from financial_filing_data_foundation.us_sec.acquisition import SecAcquirer
from financial_filing_data_foundation.us_sec.errors import P11Reason, SecError
from financial_filing_data_foundation.us_sec.http import SecHttpClient, SecHttpConfig, SecResponse
from financial_filing_data_foundation.us_sec.identity import sec_company
from financial_filing_data_foundation.us_sec.package import SecPackageStore


def test_sec_acquirer_downloads_primary_and_xbrl_members_incrementally(tmp_path: Path) -> None:
    submissions_url = "https://data.sec.gov/submissions/CIK0000320193.json"
    index_url = "https://www.sec.gov/Archives/edgar/data/320193/000032019325000001/index.json"
    primary_url = "https://www.sec.gov/Archives/edgar/data/320193/000032019325000001/example.htm"
    schema_url = "https://www.sec.gov/Archives/edgar/data/320193/000032019325000001/example.xsd"
    calls: list[str] = []
    submissions = {
        "cik": "0000320193",
        "filings": {
            "recent": {
                "accessionNumber": ["0000320193-25-000001"],
                "filingDate": ["2025-08-01"],
                "reportDate": ["2025-06-30"],
                "form": ["10-Q"],
                "primaryDocument": ["example.htm"],
            }
        },
    }
    index = {"directory": {"item": [{"name": "example.htm"}, {"name": "example.xsd"}, {"name": "unrelated.pdf"}]}}

    def transport(url: str, headers: dict[str, str], timeout: float) -> SecResponse:
        calls.append(url)
        if url == submissions_url:
            return SecResponse(200, {"Content-Type": "application/json"}, json.dumps(submissions).encode(), url)
        if url == index_url:
            return SecResponse(200, {"Content-Type": "application/json"}, json.dumps(index).encode(), url)
        if url == primary_url:
            return SecResponse(200, {"Content-Type": "text/html"}, b"<html><body>filing</body></html>", url)
        if url == schema_url:
            return SecResponse(200, {"Content-Type": "application/xml"}, b"<schema/>", url)
        raise AssertionError(url)

    client = SecHttpClient(SecHttpConfig(contact_email="ops@example.org"), transport=transport, sleep=lambda _: None)
    acquirer = SecAcquirer(client, SecPackageStore(tmp_path / "raw-store"))
    company = sec_company(cik="320193", ticker="EXM", allow_development=True)
    first = acquirer.acquire(company, fiscal_year=2025, period="Q2")
    second = acquirer.acquire(company, fiscal_year=2025, period="Q2")
    assert first.package.package_sha256 == second.package.package_sha256
    assert first.reused is False
    assert second.reused is True
    assert calls.count(primary_url) == 1
    assert calls.count(schema_url) == 1


def test_sec_acquirer_does_not_silently_select_amendment(tmp_path: Path) -> None:
    def transport(url: str, headers: dict[str, str], timeout: float) -> SecResponse:
        payload = {
            "cik": "0000320193",
            "filings": {
                "recent": {
                    "accessionNumber": ["0000320193-25-000001", "0000320193-25-000002"],
                    "filingDate": ["2025-08-01", "2025-08-02"],
                    "reportDate": ["2025-06-30", "2025-06-30"],
                    "form": ["10-Q", "10-Q/A"],
                    "primaryDocument": ["example.htm", "example-amend.htm"],
                }
            },
        }
        return SecResponse(200, {"Content-Type": "application/json"}, json.dumps(payload).encode(), url)

    client = SecHttpClient(SecHttpConfig(contact_email="ops@example.org"), transport=transport, sleep=lambda _: None)
    acquirer = SecAcquirer(client, SecPackageStore(tmp_path / "raw-store"))
    company = sec_company(cik="320193", ticker="EXM", allow_development=True)
    with pytest.raises(SecError) as exc_info:
        acquirer.acquire(company, fiscal_year=2025, period="Q2")
    assert exc_info.value.reason_code == P11Reason.P11_AMENDED_VARIANT_PRESENT.value

