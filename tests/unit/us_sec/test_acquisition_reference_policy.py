from __future__ import annotations

import json
from pathlib import Path

from financial_filing_data_foundation.us_sec.acquisition import SecAcquirer, _select_archive_members
from financial_filing_data_foundation.us_sec.http import SecHttpClient, SecHttpConfig, SecResponse
from financial_filing_data_foundation.us_sec.identity import sec_company
from financial_filing_data_foundation.us_sec.package import SecMemberRole, SecPackageStore
from financial_filing_data_foundation.us_sec.path_policy import archive_member_url


CIK = "0000320193"
ACCESSION = "0000320193-25-000001"
PRIMARY = "aapl-20250927.htm"


def _submissions() -> dict[str, object]:
    return {
        "cik": CIK,
        "fiscalYearEnd": "0926",
        "filings": {
            "recent": {
                "accessionNumber": [ACCESSION],
                "filingDate": ["2025-10-31"],
                "reportDate": ["2025-09-27"],
                "form": ["10-K"],
                "primaryDocument": [PRIMARY],
            }
        },
    }


def _build_acquirer(
    tmp_path: Path,
    *,
    items: list[dict[str, object]],
    bodies: dict[str, bytes],
    forbidden_names: set[str],
) -> tuple[SecAcquirer, list[str]]:
    submissions_url = f"https://data.sec.gov/submissions/CIK{CIK}.json"
    index_url = archive_member_url(CIK, ACCESSION, "index.json")
    calls: list[str] = []

    def transport(url: str, headers: dict[str, str], timeout: float) -> SecResponse:
        calls.append(url)
        if url == submissions_url:
            return SecResponse(
                200,
                {"Content-Type": "application/json"},
                json.dumps(_submissions()).encode("utf-8"),
                url,
            )
        if url == index_url:
            return SecResponse(
                200,
                {"Content-Type": "application/json"},
                json.dumps({"directory": {"item": items}}).encode("utf-8"),
                url,
            )
        for name, body in bodies.items():
            member_url = archive_member_url(CIK, ACCESSION, name)
            if url == member_url:
                if name in forbidden_names:
                    raise AssertionError(f"forbidden browser/static member fetched: {name}")
                content_type = "text/html" if name == PRIMARY else "application/xml"
                return SecResponse(200, {"Content-Type": content_type}, body, url)
        raise AssertionError(f"unexpected SEC URL: {url}")

    client = SecHttpClient(
        SecHttpConfig(contact_email="ops@example.org"),
        transport=transport,
        sleep=lambda _: None,
    )
    return (
        SecAcquirer(client, SecPackageStore(tmp_path / "raw-store")),
        calls,
    )


def test_primary_browser_assets_are_not_fetched_but_semantic_reference_support_is_kept(
    tmp_path: Path,
) -> None:
    static_names = {
        "aapl-20250927_g1.jpg",
        "style.css",
        "script.js",
        "graphic.png",
        "graphic.gif",
        "font.woff2",
    }
    support_name = "aapl-20250927-instance.xml"
    schema_name = "aapl-20250927.xsd"
    summary_name = "FilingSummary.xml"
    primary_body = (
        "<html><head>"
        "<link:schemaRef xlink:href='aapl-20250927-instance.xml'>"
        "</head><body>"
        "<img src='aapl-20250927_g1.jpg'>"
        "<link href='style.css'>"
        "<script src='script.js'></script>"
        "<img src='graphic.png'><img src='graphic.gif'>"
        "<link href='font.woff2'>"
        "</body></html>"
    ).encode("utf-8")
    items = [
        {"name": PRIMARY},
        {"name": schema_name, "type": "EX-101.SCH"},
        {"name": summary_name},
        {"name": support_name, "type": "XBRL_INSTANCE"},
        *({"name": name} for name in sorted(static_names)),
    ]
    bodies = {
        PRIMARY: primary_body,
        schema_name: b"<schema />",
        summary_name: b"<Report />",
        support_name: b"<xbrl />",
        **{name: b"browser asset" for name in static_names},
    }
    acquirer, calls = _build_acquirer(
        tmp_path,
        items=items,
        bodies=bodies,
        forbidden_names=static_names,
    )

    result = acquirer.acquire(
        sec_company(cik="320193", ticker="AAPL", allow_development=True),
        fiscal_year=2025,
        period="FY",
    )

    names = {member.relative_name for member in result.package.members}
    assert PRIMARY in names
    assert schema_name in names
    assert summary_name in names
    assert support_name in names
    assert names.isdisjoint(static_names)
    for name in static_names:
        assert calls.count(archive_member_url(CIK, ACCESSION, name)) == 0
    assert calls.count(archive_member_url(CIK, ACCESSION, support_name)) == 1
    assert next(member for member in result.package.members if member.relative_name == support_name).role is SecMemberRole.XBRL_INSTANCE


def test_generic_xml_reference_is_not_selected_without_semantic_metadata(tmp_path: Path) -> None:
    generic_name = "unrelated.xml"
    primary_body = f"<html><body><a href='{generic_name}'>attachment</a></body></html>".encode("utf-8")
    items = [{"name": PRIMARY}, {"name": generic_name, "type": "XML"}]
    bodies = {PRIMARY: primary_body, generic_name: b"<attachment />"}
    acquirer, calls = _build_acquirer(
        tmp_path,
        items=items,
        bodies=bodies,
        forbidden_names={generic_name},
    )

    result = acquirer.acquire(
        sec_company(cik="320193", ticker="AAPL", allow_development=True),
        fiscal_year=2025,
        period="FY",
    )

    assert generic_name not in {member.relative_name for member in result.package.members}
    assert calls.count(archive_member_url(CIK, ACCESSION, generic_name)) == 0


def test_unsafe_primary_references_are_ignored_without_archive_fetch() -> None:
    body = (
        "<html><body>"
        "<a href='../escape.xml'>up</a>"
        "<a href='/absolute.xml'>absolute</a>"
        "<a href='https://evil.example/remote.xml'>remote</a>"
        "<a href='javascript:alert(1)'>script</a>"
        "<a href='data:text/plain,secret'>data</a>"
        "</body></html>"
    ).encode("utf-8")

    selected = _select_archive_members(
        {
            "primary.htm": {"name": "primary.htm"},
        },
        primary_name="primary.htm",
        primary_body=body,
    )

    assert selected == ["primary.htm"]
