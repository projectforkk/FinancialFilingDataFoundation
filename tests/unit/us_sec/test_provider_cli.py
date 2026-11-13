from __future__ import annotations

import json
from pathlib import Path

import pytest

from financial_filing_data_foundation.us_sec.acquisition import SecAcquirer, _member_role
from financial_filing_data_foundation.us_sec.errors import P11Reason, SecError
from financial_filing_data_foundation.us_sec.http import SecHttpClient, SecHttpConfig, SecResponse
from financial_filing_data_foundation.us_sec.identity import sec_company
from financial_filing_data_foundation.us_sec.package import SecMemberRole, SecPackageMember, SecPackageStore, build_package
from financial_filing_data_foundation.us_sec.path_policy import archive_member_url


def test_generic_xml_is_not_misclassified_as_xbrl_instance() -> None:
    assert _member_role("attachment.xml", "primary.htm", b"<attachment />").value == "OTHER"
    assert _member_role("attachment.xbrl", "primary.htm", b"<attachment />").value == "OTHER"
    assert _member_role(
        "instance.xml",
        "primary.htm",
        b'<xbrli:xbrl xmlns:xbrli="http://www.xbrl.org/2003/instance" />',
    ).value == "XBRL_INSTANCE"
    assert _member_role("instance.xbrl", "primary.htm", b"<xbrl />").value == "OTHER"


def _valid_q2_submissions() -> dict[str, object]:
    return {
        "cik": "0000320193",
        "fiscalYearEnd": "1231",
        "filings": {
            "recent": {
                "accessionNumber": [
                    "0000320193-24-000001",
                    "0000320193-25-000000",
                    "0000320193-25-000001",
                ],
                "filingDate": ["2024-11-01", "2025-05-01", "2025-08-01"],
                "reportDate": ["2024-12-31", "2025-03-31", "2025-06-30"],
                "form": ["10-K", "10-Q", "10-Q"],
                "primaryDocument": ["fy.htm", "q1.htm", "example.htm"],
            }
        },
    }


def _acquirer_for_error_path(
    tmp_path: Path,
    *,
    submissions_body: bytes,
    archive_body: bytes,
    history_body: bytes | None = None,
) -> tuple[SecAcquirer, object]:
    submissions_url = "https://data.sec.gov/submissions/CIK0000320193.json"
    history_url = "https://data.sec.gov/submissions/CIK0000320193-2024.json"
    index_url = "https://www.sec.gov/Archives/edgar/data/320193/000032019325000001/index.json"

    def transport(url: str, headers: dict[str, str], timeout: float) -> SecResponse:
        if url == submissions_url:
            return SecResponse(200, {"Content-Type": "application/json"}, submissions_body, url)
        if url == history_url and history_body is not None:
            return SecResponse(200, {"Content-Type": "application/json"}, history_body, url)
        if url == index_url:
            return SecResponse(200, {"Content-Type": "application/json"}, archive_body, url)
        raise AssertionError(url)

    client = SecHttpClient(
        SecHttpConfig(contact_email="ops@example.org"),
        transport=transport,
        sleep=lambda _: None,
    )
    return (
        SecAcquirer(client, SecPackageStore(tmp_path / "raw-store")),
        sec_company(cik="320193", ticker="EXM", allow_development=True),
    )


@pytest.mark.parametrize(
    "archive_body",
    [
        pytest.param(json.dumps({}).encode(), id="directory-invalid"),
        pytest.param(
            json.dumps({"directory": {"item": {}}}).encode(),
            id="item-list-invalid",
        ),
        pytest.param(
            json.dumps({"directory": {"item": [{"name": 123}]}}).encode(),
            id="item-record-invalid",
        ),
        pytest.param(b"not-json", id="archive-json-invalid"),
    ],
)
def test_sec_acquirer_malformed_archive_index_raises_discovery_error(
    tmp_path: Path, archive_body: bytes
) -> None:
    acquirer, company = _acquirer_for_error_path(
        tmp_path,
        submissions_body=json.dumps(_valid_q2_submissions()).encode(),
        archive_body=archive_body,
    )

    with pytest.raises(SecError) as exc_info:
        acquirer.acquire(company, fiscal_year=2025, period="Q2")

    assert exc_info.value.reason_code == P11Reason.P11_SEC_DISCOVERY_FAILED.value


def test_sec_acquirer_invalid_main_submissions_json_raises_discovery_error(
    tmp_path: Path,
) -> None:
    acquirer, company = _acquirer_for_error_path(
        tmp_path,
        submissions_body=b"not-json",
        archive_body=b"{}",
    )

    with pytest.raises(SecError) as exc_info:
        acquirer.acquire(company, fiscal_year=2025, period="Q2")

    assert exc_info.value.reason_code == P11Reason.P11_SEC_DISCOVERY_FAILED.value


def test_sec_acquirer_invalid_historical_submissions_json_raises_discovery_error(
    tmp_path: Path,
) -> None:
    submissions = {
        "cik": "0000320193",
        "filings": {
            "recent": {
                "accessionNumber": [],
                "filingDate": [],
                "reportDate": [],
                "form": [],
                "primaryDocument": [],
            },
            "files": [
                {
                    "name": "CIK0000320193-2024.json",
                    "filingFrom": "2024-01-01",
                    "filingTo": "2024-12-31",
                }
            ],
        },
    }
    acquirer, company = _acquirer_for_error_path(
        tmp_path,
        submissions_body=json.dumps(submissions).encode(),
        archive_body=b"{}",
        history_body=b"not-json",
    )

    with pytest.raises(SecError) as exc_info:
        acquirer.acquire(company, fiscal_year=2024, period="FY")

    assert exc_info.value.reason_code == P11Reason.P11_SEC_DISCOVERY_FAILED.value


def test_sec_acquirer_downloads_primary_and_xbrl_members_incrementally(tmp_path: Path) -> None:
    submissions_url = "https://data.sec.gov/submissions/CIK0000320193.json"
    index_url = "https://www.sec.gov/Archives/edgar/data/320193/000032019325000001/index.json"
    primary_url = "https://www.sec.gov/Archives/edgar/data/320193/000032019325000001/example.htm"
    schema_url = "https://www.sec.gov/Archives/edgar/data/320193/000032019325000001/example.xsd"
    calls: list[str] = []
    submissions = {
        "cik": "0000320193",
        "fiscalYearEnd": "1231",
        "filings": {
            "recent": {
                "accessionNumber": [
                    "0000320193-24-000001",
                    "0000320193-25-000000",
                    "0000320193-25-000001",
                ],
                "filingDate": ["2024-11-01", "2025-05-01", "2025-08-01"],
                "reportDate": ["2024-12-31", "2025-03-31", "2025-06-30"],
                "form": ["10-K", "10-Q", "10-Q"],
                "primaryDocument": ["fy.htm", "q1.htm", "example.htm"],
            }
        },
    }
    index = {"directory": {"item": [{"name": "example.htm"}, {"name": "example.xsd", "type": "EX-101.SCH"}, {"name": "unrelated.xml", "type": "XML"}, {"name": "unrelated.pdf"}]}}

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
    assert next(member for member in first.package.members if member.relative_name == "example.htm").content_type == "text/html"
    assert calls.count(primary_url) == 1
    assert calls.count(schema_url) == 1


def test_sec_acquirer_requires_fresh_discovery_before_local_package(tmp_path: Path) -> None:
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
                source_url=archive_member_url("0000320193", "0000320193-25-000079", "annual.htm"),
                body=b"<html><body><p>annual</p></body></html>",
            ),
        ),
    )
    store = SecPackageStore(tmp_path / "raw-store")
    store.put(package)
    company = sec_company(cik="320193", ticker="EXM", allow_development=True)

    with pytest.raises(SecError) as exc_info:
        SecAcquirer(object(), store).acquire(company, fiscal_year=2025, period="FY")
    assert exc_info.value.reason_code == P11Reason.P11_DISCOVERY_FRESHNESS_UNKNOWN.value


def test_sec_acquirer_does_not_silently_select_amendment(tmp_path: Path) -> None:
    def transport(url: str, headers: dict[str, str], timeout: float) -> SecResponse:
        payload = {
            "cik": "0000320193",
            "fiscalYearEnd": "1231",
            "filings": {
                "recent": {
                    "accessionNumber": [
                        "0000320193-24-000001",
                        "0000320193-25-000000",
                        "0000320193-25-000001",
                        "0000320193-25-000002",
                    ],
                    "filingDate": ["2024-11-01", "2025-05-01", "2025-08-01", "2025-08-02"],
                    "reportDate": ["2024-12-31", "2025-03-31", "2025-06-30", "2025-06-30"],
                    "form": ["10-K", "10-Q", "10-Q", "10-Q/A"],
                    "primaryDocument": ["fy.htm", "q1.htm", "example.htm", "example-amend.htm"],
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


def test_sec_acquirer_fetches_all_retained_history_chunks_for_independent_discovery(tmp_path: Path) -> None:
    submissions_url = "https://data.sec.gov/submissions/CIK0000123456.json"
    relevant_history_url = "https://data.sec.gov/submissions/CIK0000123456-2024.json"
    irrelevant_history_url = "https://data.sec.gov/submissions/CIK0000123456-2018.json"
    index_url = "https://www.sec.gov/Archives/edgar/data/123456/000012345624000001/index.json"
    primary_url = "https://www.sec.gov/Archives/edgar/data/123456/000012345624000001/annual.htm"
    calls: list[str] = []
    submissions = {
        "cik": "0000123456",
        "filings": {
            "recent": {
                "accessionNumber": [],
                "filingDate": [],
                "reportDate": [],
                "form": [],
                "primaryDocument": [],
            },
            "files": [
                {"name": "CIK0000123456-2018.json", "filingFrom": "2018-01-01", "filingTo": "2018-12-31"},
                {"name": "CIK0000123456-2024.json", "filingFrom": "2024-01-01", "filingTo": "2024-12-31"},
            ],
        },
    }
    history = {
        "cik": "0000123456",
        "accessionNumber": ["0000123456-24-000001"],
        "filingDate": ["2025-02-01"],
        "reportDate": ["2024-12-31"],
        "form": ["10-K"],
        "primaryDocument": ["annual.htm"],
    }
    index = {"directory": {"item": [{"name": "annual.htm"}]}}

    def transport(url: str, headers: dict[str, str], timeout: float) -> SecResponse:
        calls.append(url)
        if url == submissions_url:
            body = json.dumps(submissions).encode()
            return SecResponse(200, {"Content-Type": "application/json"}, body, url)
        if url == relevant_history_url:
            return SecResponse(200, {"Content-Type": "application/json"}, json.dumps(history).encode(), url)
        if url == irrelevant_history_url:
            return SecResponse(
                200,
                {"Content-Type": "application/json"},
                json.dumps(
                    {
                        "cik": "0000123456",
                        "accessionNumber": ["0000123456-18-000001"],
                        "filingDate": ["2019-02-01"],
                        "reportDate": ["2018-12-31"],
                        "form": ["10-Q"],
                        "primaryDocument": [""],
                    }
                ).encode(),
                url,
            )
        if url == index_url:
            return SecResponse(200, {"Content-Type": "application/json"}, json.dumps(index).encode(), url)
        if url == primary_url:
            return SecResponse(200, {"Content-Type": "text/html"}, b"<html><body>annual</body></html>", url)
        raise AssertionError(url)

    client = SecHttpClient(SecHttpConfig(contact_email="ops@example.org"), transport=transport, sleep=lambda _: None)
    company = sec_company(cik="123456", ticker="EXM", allow_development=True)
    result = SecAcquirer(client, SecPackageStore(tmp_path / "raw-store")).acquire(company, fiscal_year=2024, period="FY")

    assert result.candidate.accession == "0000123456-24-000001"
    assert calls.count(relevant_history_url) == 1
    assert calls.count(irrelevant_history_url) == 1

