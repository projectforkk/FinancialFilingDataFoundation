from __future__ import annotations

import json
from pathlib import Path

from financial_filing_data_foundation.us_sec.acquisition import SecAcquirer, _select_archive_members
from financial_filing_data_foundation.us_sec.http import SecHttpClient, SecHttpConfig, SecResponse
from financial_filing_data_foundation.us_sec.identity import sec_company
from financial_filing_data_foundation.us_sec.package import SecMemberRole, SecPackageStore
from financial_filing_data_foundation.us_sec.parser import parse_sec_package
from financial_filing_data_foundation.us_sec.path_policy import archive_member_url
from financial_filing_data_foundation.us_sec.validation import validate_sec_artifacts


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
    forbidden_names: set[str] | None = None,
) -> tuple[SecAcquirer, list[str]]:
    submissions_url = f"https://data.sec.gov/submissions/CIK{CIK}.json"
    index_url = archive_member_url(CIK, ACCESSION, "index.json")
    forbidden_names = forbidden_names or set()
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
    return SecAcquirer(client, SecPackageStore(tmp_path / "raw-store")), calls


def _acquire(
    tmp_path: Path,
    *,
    items: list[dict[str, object]],
    bodies: dict[str, bytes],
    forbidden_names: set[str] | None = None,
):
    acquirer, calls = _build_acquirer(
        tmp_path,
        items=items,
        bodies=bodies,
        forbidden_names=forbidden_names,
    )
    result = acquirer.acquire(
        sec_company(cik="320193", ticker="AAPL", allow_development=True),
        fiscal_year=2025,
        period="FY",
    )
    return result, calls


def test_t134_01_schema_ref_selects_generic_index_type_and_excludes_static_assets(tmp_path: Path) -> None:
    schema_name = "aapl-20250927.xsd"
    static_names = {
        "aapl-20250927_g1.jpg",
        "style.css",
        "script.js",
        "graphic.png",
        "graphic.gif",
        "font.woff2",
        "decorative.svg",
    }
    primary_body = (
        "<html><head>"
        "<link:schemaRef xlink:href='aapl-20250927.xsd'>"
        "<img src='aapl-20250927_g1.jpg'><link href='style.css'>"
        "<script src='script.js'></script><img src='graphic.png'>"
        "<img src='graphic.gif'><link href='font.woff2'><img src='decorative.svg'>"
        "</head><body>filing</body></html>"
    ).encode("utf-8")
    schema_body = b"<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema' />"
    items = [
        {"name": PRIMARY},
        {"name": schema_name, "type": "text.gif"},
        *({"name": name, "type": "text.gif"} for name in sorted(static_names)),
    ]
    bodies = {
        PRIMARY: primary_body,
        schema_name: schema_body,
        **{name: b"browser asset" for name in static_names},
    }

    result, calls = _acquire(
        tmp_path,
        items=items,
        bodies=bodies,
        forbidden_names=static_names,
    )

    names = {member.relative_name for member in result.package.members}
    assert names == {PRIMARY, schema_name}
    schema = next(member for member in result.package.members if member.relative_name == schema_name)
    assert schema.role is SecMemberRole.XBRL_SCHEMA
    assert schema.source_url == archive_member_url(CIK, ACCESSION, schema_name)
    assert calls.count(archive_member_url(CIK, ACCESSION, schema_name)) == 1
    for name in static_names:
        assert calls.count(archive_member_url(CIK, ACCESSION, name)) == 0

    stored = SecPackageStore(tmp_path / "raw-store").load(result.package.package_sha256)
    assert stored.manifest() == result.package.manifest()
    assert stored.package_sha256 == result.package.compute_package_sha256()


def test_t134_02_linkbase_ref_selects_generic_index_type_once(tmp_path: Path) -> None:
    linkbase_name = "aapl-20250927_pre.xml"
    static_name = "style.css"
    primary_body = (
        "<html><head>"
        "<link:linkbaseRef xlink:href='aapl-20250927_pre.xml'>"
        "<link href='style.css'>"
        "</head><body>filing</body></html>"
    ).encode("utf-8")
    linkbase_body = b"<link:linkbase xmlns:link='http://www.xbrl.org/2003/linkbase' />"
    items = [
        {"name": PRIMARY},
        {"name": linkbase_name, "type": "XML"},
        {"name": static_name, "type": "text.gif"},
    ]
    bodies = {PRIMARY: primary_body, linkbase_name: linkbase_body, static_name: b"css"}

    result, calls = _acquire(
        tmp_path,
        items=items,
        bodies=bodies,
        forbidden_names={static_name},
    )

    names = {member.relative_name for member in result.package.members}
    assert linkbase_name in names
    assert static_name not in names
    assert calls.count(archive_member_url(CIK, ACCESSION, linkbase_name)) == 1
    assert calls.count(archive_member_url(CIK, ACCESSION, static_name)) == 0


def test_t134_03_generic_xml_hyperlink_is_rejected(tmp_path: Path) -> None:
    generic_name = "unrelated.xml"
    primary_body = (
        f"<html><body><a href='{generic_name}'>attachment</a></body></html>"
    ).encode("utf-8")
    result, calls = _acquire(
        tmp_path,
        items=[{"name": PRIMARY}, {"name": generic_name, "type": "text.gif"}],
        bodies={PRIMARY: primary_body, generic_name: b"<attachment />"},
        forbidden_names={generic_name},
    )

    assert generic_name not in {member.relative_name for member in result.package.members}
    assert calls.count(archive_member_url(CIK, ACCESSION, generic_name)) == 0


def test_semantic_references_keep_archive_path_security_boundaries() -> None:
    body = (
        "<html><head>"
        "<link:schemaRef xlink:href='../escape.xsd'>"
        "<link:linkbaseRef xlink:href='/absolute.xml'>"
        "<link:schemaRef xlink:href='C:/drive.xsd'>"
        "<link:schemaRef xlink:href='..%2Fencoded.xsd'>"
        "<link:schemaRef xlink:href='https://evil.example/remote.xsd'>"
        "<link:schemaRef xlink:href='javascript:alert(1)'>"
        "<link:schemaRef xlink:href='data:text/plain,secret'>"
        "</head><body>filing</body></html>"
    ).encode("utf-8")

    selected = _select_archive_members(
        {
            "primary.htm": {"name": "primary.htm"},
            "escape.xsd": {"name": "escape.xsd", "type": "text.gif"},
            "absolute.xml": {"name": "absolute.xml", "type": "text.gif"},
            "drive.xsd": {"name": "drive.xsd", "type": "text.gif"},
            "encoded.xsd": {"name": "encoded.xsd", "type": "text.gif"},
        },
        primary_name="primary.htm",
        primary_body=body,
    )

    assert selected == ["primary.htm"]


def test_t134_05_generic_index_instance_reference_drives_xbrl_instance_primary(tmp_path: Path) -> None:
    instance_name = "aapl-20250927-instance.xml"
    primary_body = (
        "<html><head>"
        "<link:schemaRef xlink:href='aapl-20250927-instance.xml'>"
        "</head><body><p>narrative only</p></body></html>"
    ).encode("utf-8")
    instance_body = (
        b"<xbrl xmlns='http://www.xbrl.org/2003/instance' "
        b"xmlns:us-gaap='http://fasb.org/us-gaap/2024'>"
        b"<context id='c1'><entity><identifier>0000320193</identifier></entity>"
        b"<period><instant>2025-09-27</instant></period></context>"
        b"<unit id='USD'><measure>iso4217:USD</measure></unit>"
        b"<us-gaap:Revenues contextRef='c1' unitRef='USD'>42</us-gaap:Revenues>"
        b"</xbrl>"
    )
    result, calls = _acquire(
        tmp_path,
        items=[{"name": PRIMARY}, {"name": instance_name, "type": "text.gif"}],
        bodies={PRIMARY: primary_body, instance_name: instance_body},
    )

    assert calls.count(archive_member_url(CIK, ACCESSION, instance_name)) == 1
    instance = next(member for member in result.package.members if member.relative_name == instance_name)
    assert instance.role is SecMemberRole.XBRL_INSTANCE

    parsed = parse_sec_package(result.package, tmp_path / "artifacts")
    assert parsed.fact_source_mode == "XBRL_INSTANCE_PRIMARY"
    assert len(parsed.facts) == 1
    assert parsed.facts[0]["raw_value"] == "42"
    validation = validate_sec_artifacts(
        parsed,
        tmp_path / "validation",
        package=result.package,
        discovery_observation=result.observation,
    )
    assert validation.blocking_issue_count == 0


def test_t134_06_ex101_metadata_selects_without_semantic_reference(tmp_path: Path) -> None:
    schema_name = "aapl-20250927.xsd"
    result, calls = _acquire(
        tmp_path,
        items=[{"name": PRIMARY}, {"name": schema_name, "type": "EX-101.SCH"}],
        bodies={
            PRIMARY: b"<html><body>no semantic reference</body></html>",
            schema_name: b"<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema' />",
        },
    )

    assert schema_name in {member.relative_name for member in result.package.members}
    assert calls.count(archive_member_url(CIK, ACCESSION, schema_name)) == 1


def test_t134_07_semantic_dependency_cycle_is_bounded_and_deduplicated(tmp_path: Path) -> None:
    a_name = "a.xml"
    b_name = "b.xml"
    primary_body = (
        "<html><head>"
        "<link:schemaRef xlink:href='a.xml'><link:schemaRef xlink:href='a.xml'>"
        "</head><body>filing</body></html>"
    ).encode("utf-8")
    a_body = (
        b"<xbrl xmlns='http://www.xbrl.org/2003/instance' "
        b"xmlns:link='http://www.xbrl.org/2003/linkbase' "
        b"xmlns:xlink='http://www.w3.org/1999/xlink'>"
        b"<link:linkbaseRef xlink:href='b.xml'/><link:linkbaseRef xlink:href='b.xml'/>"
        b"</xbrl>"
    )
    b_body = (
        b"<xbrl xmlns='http://www.xbrl.org/2003/instance' "
        b"xmlns:link='http://www.xbrl.org/2003/linkbase' "
        b"xmlns:xlink='http://www.w3.org/1999/xlink'>"
        b"<link:schemaRef xlink:href='a.xml'/></xbrl>"
    )
    result, calls = _acquire(
        tmp_path,
        items=[
            {"name": PRIMARY},
            {"name": a_name, "type": "text.gif"},
            {"name": b_name, "type": "text.gif"},
        ],
        bodies={PRIMARY: primary_body, a_name: a_body, b_name: b_body},
    )

    names = {member.relative_name for member in result.package.members}
    assert names == {PRIMARY, a_name, b_name}
    assert calls.count(archive_member_url(CIK, ACCESSION, a_name)) == 1
    assert calls.count(archive_member_url(CIK, ACCESSION, b_name)) == 1
