from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from financial_filing_data_foundation.us_sec.errors import P11Reason
from financial_filing_data_foundation.us_sec.discovery import SecDiscoveryObservation, discover_filings, parse_submissions
from financial_filing_data_foundation.us_sec.models import SecCompanyRef
from financial_filing_data_foundation.us_sec.package import (
    SecMemberRole,
    SecPackageMember,
    build_package,
)
from financial_filing_data_foundation.us_sec.validation import validate_sec_artifacts
from financial_filing_data_foundation.us_sec.parser import (
    VIRTUAL_HTML_NORMALIZER_VERSION,
    load_sec_artifacts,
    parse_sec_package,
)
from financial_filing_data_foundation.us_sec.path_policy import archive_member_url


def _sec_url(cik: str, accession: str, name: str) -> str:
    return archive_member_url(cik, accession, name)


def _observation(package: object) -> SecDiscoveryObservation:
    body = json.dumps(
        {
            "cik": package.cik,
            "fiscalYearEnd": "1231",
            "filings": {
                "recent": {
                    "accessionNumber": [
                        "0000320193-24-000100",
                        "0000320193-25-000100",
                        package.accession,
                        "0000320193-25-000101",
                        "0000320193-25-000102",
                    ],
                    "filingDate": ["2025-02-01", "2025-05-01", "2025-07-30", "2025-08-01", "2026-02-01"],
                    "reportDate": ["2024-12-31", "2025-03-31", "2025-06-30", "2025-09-30", "2025-12-31"],
                    "form": ["10-K", "10-Q", package.form, "10-Q", "10-K"],
                    "primaryDocument": ["prior.htm", "q1.htm", package.primary_document, "q3.htm", "annual.htm"],
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
    submissions = parse_submissions(
        json.loads(body.decode()),
        company=company,
        source_url="https://data.sec.gov/submissions/CIK0000320193.json",
    )
    candidates = discover_filings(submissions, fiscal_year=package.fiscal_year, period=package.period)
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


def _package() -> object:
    html = b"""
    <html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL" xmlns:xbrli="http://www.xbrl.org/2003/instance" xmlns:us-gaap="http://fasb.org/us-gaap/2025" xmlns:ex="http://example.test/ex"><head><title>Example</title></head><body>
      <div><h1>Condensed Statements</h1><p>Amounts in USD.</p></div>
      <ix:header>
        <xbrli:context id="c1"><xbrli:entity><xbrli:identifier scheme="http://www.sec.gov/CIK">0000320193</xbrli:identifier></xbrli:entity><xbrli:period><xbrli:instant>2025-06-30</xbrli:instant></xbrli:period></xbrli:context>
        <xbrli:unit id="USD"><xbrli:measure>iso4217:USD</xbrli:measure></xbrli:unit>
      </ix:header>
      <table><tr><th rowspan="2">Item</th><th colspan="2">2025</th></tr>
        <tr><th>Q2</th><th>YTD</th></tr>
        <tr><td>Revenue</td><td><ix:nonfraction name="us-gaap:Revenues" contextRef="c1" unitRef="USD" decimals="0">100</ix:nonfraction></td><td>200</td></tr>
        <tr><td>Custom</td><td><ix:nonfraction name="ex:CustomMetric" contextRef="missing" unitRef="USD" nil="true">-</ix:nonfraction></td><td><ix:nonnumeric name="ex:Note" contextRef="c1">See note</ix:nonnumeric></td></tr>
      </table>
    </body></html>
    """
    return build_package(
        cik="0000320193",
        accession="0000320193-25-000001",
        form="10-Q",
        fiscal_year=2025,
        period="Q2",
        members=(
            SecPackageMember(
                relative_name="example.htm",
                role=SecMemberRole.PRIMARY_DOCUMENT,
                content_type="text/html",
                source_url=_sec_url("0000320193", "0000320193-25-000001", "example.htm"),
                body=html,
            ),
        ),
    )


def test_html_parser_creates_stable_virtual_pages_dom_tables_and_evidence(tmp_path: Path) -> None:
    package = _package()
    result = parse_sec_package(package, tmp_path / "p11")
    assert result.parser_version == VIRTUAL_HTML_NORMALIZER_VERSION
    assert result.pages
    assert all(page["pagination_kind"] == "VIRTUAL_HTML" for page in result.pages)
    assert result.tables[0]["rows"][0]["cells"][0]["row_span"] == 2
    assert result.tables[0]["rows"][0]["cells"][1]["col_span"] == 2
    assert result.tables[0]["column_count"] == 3
    assert result.tables[0]["document_sha256"] == package.package_sha256
    assert result.tables[0]["source_member_sha256"] == package.members[0].member_sha256
    assert result.tables[0]["heading_context"]["title"] == "Condensed Statements"
    assert result.tables[0]["inline_xbrl_fact_present"] is True
    assert "INLINE_XBRL_FACT" in result.tables[0]["candidate_signals"]
    assert result.facts
    assert {fact["raw_qname"] for fact in result.facts} >= {"us-gaap:Revenues", "ex:CustomMetric", "ex:Note"}
    revenue = next(fact for fact in result.facts if fact["raw_qname"] == "us-gaap:Revenues")
    evidence = next(row for row in result.evidence if row["evidence_id"] == revenue["evidence_id"])
    assert evidence["source_member_relative_name"] == "example.htm"
    assert evidence["dom_locator"].startswith("/")
    assert evidence["block_id"] in {
        block["block_id"]
        for page in result.pages
        for block in page["blocks"]
    }
    assert evidence["block_dom_locator"]
    assert evidence["block_id"] != evidence["fragment_hash"]
    assert revenue["context_ref"] == "c1"
    assert any(issue["code"] == "P11_XBRL_CONTEXT_UNRESOLVED" for issue in result.issues)

    loaded = load_sec_artifacts(result.artifact_dir)
    assert loaded.package_sha256 == package.package_sha256
    assert loaded.facts == result.facts


def _hidden_fact_package() -> object:
    html = b"""
    <html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL" xmlns:xbrli="http://www.xbrl.org/2003/instance" xmlns:us-gaap="http://fasb.org/us-gaap/2025" xmlns:ex="http://example.test/ex"><head><title>Hidden facts</title></head><body>
      <ix:header>
        <xbrli:context id="c1"><xbrli:entity><xbrli:identifier>0000320193</xbrli:identifier></xbrli:entity><xbrli:period><xbrli:instant>2025-06-30</xbrli:instant></xbrli:period></xbrli:context>
        <xbrli:unit id="USD"><xbrli:measure>iso4217:USD</xbrli:measure></xbrli:unit>
        <ix:hidden>
          <ix:nonfraction name="us-gaap:Revenues" contextRef="c1" unitRef="USD" decimals="0">100</ix:nonfraction>
          <ix:nonnumeric name="ex:Note" contextRef="c1">Hidden note</ix:nonnumeric>
        </ix:hidden>
      </ix:header>
      <h1>Visible statement</h1>
      <p><ix:nonfraction name="us-gaap:Assets" contextRef="c1" unitRef="USD" decimals="0">200</ix:nonfraction></p>
    </body></html>
    """
    return build_package(
        cik="0000320193",
        accession="0000320193-25-000003",
        form="10-Q",
        fiscal_year=2025,
        period="Q2",
        members=(
            SecPackageMember(
                relative_name="hidden.htm",
                role=SecMemberRole.PRIMARY_DOCUMENT,
                content_type="text/html",
                source_url=_sec_url("0000320193", "0000320193-25-000003", "hidden.htm"),
                body=html,
            ),
        ),
    )


def test_hidden_inline_numeric_and_nonnumeric_facts_are_valid_source_evidence(tmp_path: Path) -> None:
    package = _hidden_fact_package()
    observation = _observation(package)
    result = parse_sec_package(package, tmp_path / "p11", discovery_observation=observation)

    hidden = [fact for fact in result.facts if fact["hidden"]]
    assert {fact["raw_qname"] for fact in hidden} == {"us-gaap:Revenues", "ex:Note"}
    assert all(fact["block_id"] is None for fact in hidden)
    assert all(fact["block_dom_locator"] is None for fact in hidden)
    assert all(fact["evidence_id"] for fact in hidden)
    hidden_evidence = [row for row in result.evidence if row["raw_fact_id"] in {fact["raw_fact_id"] for fact in hidden}]
    assert len(hidden_evidence) == 2
    assert all(row["locator_kind"] == "DOM_HIDDEN_FACT" for row in hidden_evidence)
    assert all(row["block_id"] is None for row in hidden_evidence)
    assert all(row["block_dom_locator"] is None for row in hidden_evidence)

    validation = validate_sec_artifacts(
        result,
        tmp_path / "p7",
        package=package,
        discovery_observation=observation,
    )
    assert validation.validation_status == "PASS"
    assert validation.blocking_issue_count == 0


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("dom_locator", "/html[1]/body[1]/ix:hidden[1]/ix:nonfraction[99]"),
        ("member_sha256", "1" * 64),
        ("fragment_hash", "2" * 64),
    ),
)
def test_hidden_fact_corrupt_locator_or_hash_is_blocked(
    tmp_path: Path,
    field: str,
    value: str,
) -> None:
    package = _hidden_fact_package()
    parsed = parse_sec_package(package, tmp_path / "p11")
    hidden_evidence_index = next(index for index, row in enumerate(parsed.evidence) if row["locator_kind"] == "DOM_HIDDEN_FACT")
    evidence = [dict(row) for row in parsed.evidence]
    evidence[hidden_evidence_index][field] = value

    validation = validate_sec_artifacts(replace(parsed, evidence=tuple(evidence)), tmp_path / "p7", package=package)

    assert validation.validation_status == "BLOCKED"
    assert any(issue["code"] == P11Reason.P11_EVIDENCE_LOCATOR_INVALID.value for issue in validation.issues) or any(
        issue["code"] == P11Reason.P11_MEMBER_HASH_MISMATCH.value for issue in validation.issues
    )


def test_visible_inline_fact_still_requires_a_block_anchor(tmp_path: Path) -> None:
    package = _hidden_fact_package()
    parsed = parse_sec_package(package, tmp_path / "p11")
    visible_index = next(index for index, row in enumerate(parsed.evidence) if row["locator_kind"] == "DOM_PATH")
    evidence = [dict(row) for row in parsed.evidence]
    evidence[visible_index]["block_id"] = None

    validation = validate_sec_artifacts(replace(parsed, evidence=tuple(evidence)), tmp_path / "p7", package=package)

    assert validation.validation_status == "BLOCKED"
    assert any(issue["code"] == P11Reason.P11_EVIDENCE_LOCATOR_INVALID.value for issue in validation.issues)


def test_pre_issue138_v5_v2_artifact_is_not_reused_by_v6_parser(tmp_path: Path) -> None:
    package = _hidden_fact_package()
    legacy_dir = tmp_path / "p11" / f"{package.package_sha256}.VIRTUAL_HTML_V6"
    legacy_dir.mkdir(parents=True)
    legacy_manifest = legacy_dir / "manifest.json"
    legacy_manifest.write_text(
        '{"schema_version":"p11-sec-artifacts-v2","parser_version":"VIRTUAL_HTML_V5","package_sha256":"legacy"}\n',
        encoding="utf-8",
    )
    before = legacy_manifest.read_bytes()

    result = parse_sec_package(package, tmp_path / "p11")

    assert VIRTUAL_HTML_NORMALIZER_VERSION == "VIRTUAL_HTML_V6"
    assert result.artifact_dir != legacy_dir
    assert result.artifact_dir.name == f"{package.package_sha256}.VIRTUAL_HTML_V6"
    assert result.artifact_dir.is_dir()
    assert legacy_manifest.read_bytes() == before


def test_current_v6_parser_reuses_only_its_distinct_v6_artifact_directory(tmp_path: Path) -> None:
    package = _hidden_fact_package()
    legacy_dir = tmp_path / "p11" / f"{package.package_sha256}.VIRTUAL_HTML_V5"
    legacy_dir.mkdir(parents=True)
    legacy_manifest = legacy_dir / "manifest.json"
    legacy_manifest.write_text(
        '{"schema_version":"p11-sec-artifacts-v2","parser_version":"VIRTUAL_HTML_V5","package_sha256":"legacy"}\n',
        encoding="utf-8",
    )
    before = legacy_manifest.read_bytes()

    first = parse_sec_package(package, tmp_path / "p11")
    second = parse_sec_package(package, tmp_path / "p11")

    assert VIRTUAL_HTML_NORMALIZER_VERSION == "VIRTUAL_HTML_V6"
    assert first.artifact_dir == second.artifact_dir
    assert first.artifact_dir.name == f"{package.package_sha256}.VIRTUAL_HTML_V6"
    assert first.facts == second.facts
    assert legacy_manifest.read_bytes() == before


def test_html5_header_is_visible_but_ix_header_remains_hidden(tmp_path: Path) -> None:
    html = b"""
    <html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL"><body>
      <header><p>Ordinary filing narrative in an HTML5 header.</p></header>
      <ix:header><p>Inline XBRL metadata is not ordinary narrative.</p></ix:header>
      <h1>Visible statement</h1>
    </body></html>
    """
    package = build_package(
        cik="0000320193",
        accession="0000320193-25-000005",
        form="10-Q",
        fiscal_year=2025,
        period="Q2",
        members=(
            SecPackageMember(
                relative_name="header.htm",
                role=SecMemberRole.PRIMARY_DOCUMENT,
                content_type="text/html",
                source_url=_sec_url("0000320193", "0000320193-25-000005", "header.htm"),
                body=html,
            ),
        ),
    )

    result = parse_sec_package(package, tmp_path / "p11")
    texts = [block["text"] for page in result.pages for block in page["blocks"]]

    assert any("Ordinary filing narrative" in text for text in texts)
    assert not any("Inline XBRL metadata" in text for text in texts)


def test_virtual_page_normalization_is_repeatable(tmp_path: Path) -> None:
    package = _package()
    first = parse_sec_package(package, tmp_path / "first")
    second = parse_sec_package(package, tmp_path / "second")
    assert first.pages == second.pages
    assert first.tables == second.tables
    assert first.facts == second.facts


def test_div_span_narrative_and_inline_fact_parent_are_preserved_without_duplicates(tmp_path: Path) -> None:
    html = b"""<html xmlns:ix='http://www.xbrl.org/2013/inlineXBRL' xmlns:xbrli='http://www.xbrl.org/2003/instance' xmlns:us-gaap='http://fasb.org/us-gaap/2025' xmlns:ex='http://example.test/ex'><body><div class='narrative'><span>Operating performance improved.</span></div>
    <div class='narrative'>Revenue <span>was</span> <span>strong.</span></div>
    <p>Revenue was <ix:nonfraction name='ex:Revenue' contextRef='c1' unitRef='USD'>100</ix:nonfraction> million.</p>
    <ix:nonfraction name='ex:TopLevelFact' contextRef='c1' unitRef='USD'><div>300</div></ix:nonfraction>
    <div style='display:none'><ix:nonfraction name='ex:HiddenStyleFact' contextRef='c1' unitRef='USD'>999</ix:nonfraction></div>
    <ix:header><xbrli:context id='c1'><xbrli:entity><xbrli:identifier>1</xbrli:identifier></xbrli:entity><xbrli:period><xbrli:instant>2025-06-30</xbrli:instant></xbrli:period></xbrli:context><xbrli:unit id='USD'><xbrli:measure>USD</xbrli:measure></xbrli:unit></ix:header>
    </body></html>"""
    package = build_package(
        cik="0000000001",
        accession="0000000001-25-000001",
        form="10-Q",
        fiscal_year=2025,
        period="Q2",
        members=(SecPackageMember(relative_name="rich.htm", role=SecMemberRole.PRIMARY_DOCUMENT, content_type="text/html", source_url=_sec_url("0000000001", "0000000001-25-000001", "rich.htm"), body=html),),
    )
    result = parse_sec_package(package, tmp_path / "p11")
    texts = [block["text"] for page in result.pages for block in page["blocks"]]
    assert any("Operating performance improved." in text for text in texts)
    assert any("Revenue was strong." in text for text in texts)
    assert any("Revenue was 100 million." in text for text in texts)
    assert any("300" == text for text in texts)
    assert sum("Operating performance improved." in text for text in texts) == 1
    hidden_style = next(fact for fact in result.facts if fact["raw_qname"] == "ex:HiddenStyleFact")
    assert hidden_style["hidden"] is True
    assert not any(issue["code"] == "P11_EVIDENCE_LOCATOR_INVALID" for issue in result.issues)


def test_visible_fact_in_empty_positioning_wrappers_gets_a_cell_source_block(tmp_path: Path) -> None:
    html = b"""<html xmlns:ix='http://www.xbrl.org/2013/inlineXBRL' xmlns:xbrli='http://www.xbrl.org/2003/instance' xmlns:us-gaap='http://fasb.org/us-gaap/2025'><body>
    <ix:header>
      <xbrli:context id="c1"><xbrli:entity><xbrli:identifier>1</xbrli:identifier></xbrli:entity><xbrli:period><xbrli:instant>2025-06-30</xbrli:instant></xbrli:period></xbrli:context>
      <xbrli:unit id="USD"><xbrli:measure>iso4217:USD</xbrli:measure></xbrli:unit>
    </ix:header>
    <table><tr><td><div style="display:inline;"></div>
      <ix:nonfraction name="us-gaap:Revenues" contextRef="c1" unitRef="USD">100</ix:nonfraction>
      <div style="display:inline;"></div></td></tr></table>
    </body></html>"""
    package = build_package(
        cik="0000000001",
        accession="0000000001-25-000004",
        form="10-Q",
        fiscal_year=2025,
        period="Q2",
        members=(
            SecPackageMember(
                relative_name="positioned.htm",
                role=SecMemberRole.PRIMARY_DOCUMENT,
                content_type="text/html",
                source_url=_sec_url("0000000001", "0000000001-25-000004", "positioned.htm"),
                body=html,
            ),
        ),
    )

    result = parse_sec_package(package, tmp_path / "p11")

    fact = next(row for row in result.facts if row["raw_qname"] == "us-gaap:Revenues")
    assert fact["block_id"]
    assert fact["block_dom_locator"].endswith("/td[1]")
    assert not any(issue["code"] == P11Reason.P11_EVIDENCE_LOCATOR_INVALID.value for issue in result.issues)


def test_visible_fact_with_inline_positioning_text_gets_the_outer_narrative_block(tmp_path: Path) -> None:
    html = b"""<html xmlns:ix='http://www.xbrl.org/2013/inlineXBRL' xmlns:xbrli='http://www.xbrl.org/2003/instance' xmlns:us-gaap='http://fasb.org/us-gaap/2025'><body>
    <ix:header>
      <xbrli:context id="c1"><xbrli:entity><xbrli:identifier>1</xbrli:identifier></xbrli:entity><xbrli:period><xbrli:instant>2025-06-30</xbrli:instant></xbrli:period></xbrli:context>
      <xbrli:unit id="USD"><xbrli:measure>iso4217:USD</xbrli:measure></xbrli:unit>
    </ix:header>
    <table><tr><td><div class="narrative">
      <div style="display:inline;"><div>Revenue was </div></div>
      <ix:nonfraction name="us-gaap:Revenues" contextRef="c1" unitRef="USD">100</ix:nonfraction>
      <div style="display:inline;"><div> million.</div></div>
    </div></td></tr></table>
    </body></html>"""
    package = build_package(
        cik="0000000001",
        accession="0000000001-25-000005",
        form="10-Q",
        fiscal_year=2025,
        period="Q2",
        members=(
            SecPackageMember(
                relative_name="inline-positioned.htm",
                role=SecMemberRole.PRIMARY_DOCUMENT,
                content_type="text/html",
                source_url=_sec_url("0000000001", "0000000001-25-000005", "inline-positioned.htm"),
                body=html,
            ),
        ),
    )

    result = parse_sec_package(package, tmp_path / "p11")

    fact = next(row for row in result.facts if row["raw_qname"] == "us-gaap:Revenues")
    assert fact["block_id"]
    assert fact["block_dom_locator"].endswith("/div[1]")
    assert any("Revenue was 100 million." in page["text"] for page in result.pages)
    assert not any(issue["code"] == P11Reason.P11_EVIDENCE_LOCATOR_INVALID.value for issue in result.issues)


def test_namespaced_nil_and_explicit_typed_dimensions_are_preserved(tmp_path: Path) -> None:
    xml = b'''<xbrli:xbrl xmlns:xbrli="http://www.xbrl.org/2003/instance" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:ex="http://example.test/ex" xmlns:dim="http://example.test/dim">
      <xbrli:context id="c1"><xbrli:entity><xbrli:identifier>1</xbrli:identifier></xbrli:entity><xbrli:period><xbrli:instant>2025-06-30</xbrli:instant></xbrli:period><xbrli:scenario><xbrldi:explicitMember xmlns:xbrldi="http://xbrl.org/2006/xbrldi" dimension="dim:RegionAxis">ex:North</xbrldi:explicitMember><xbrldi:typedMember xmlns:xbrldi="http://xbrl.org/2006/xbrldi" dimension="dim:CustomAxis"><ex:MemberText>North</ex:MemberText></xbrldi:typedMember></xbrli:scenario></xbrli:context>
      <ex:Amount contextRef="c1" xsi:nil="true"/>
    </xbrli:xbrl>'''
    package = build_package(cik="0000000001", accession="0000000001-25-000002", form="10-Q", fiscal_year=2025, period="Q2", members=(
        SecPackageMember(relative_name="nil.htm", role=SecMemberRole.PRIMARY_DOCUMENT, content_type="text/html", source_url=_sec_url("0000000001", "0000000001-25-000002", "nil.htm"), body=b"<html><body><p>source</p></body></html>"),
        SecPackageMember(relative_name="nil.xbrl", role=SecMemberRole.XBRL_INSTANCE, content_type="application/xml", source_url=_sec_url("0000000001", "0000000001-25-000002", "nil.xbrl"), body=xml),
    ))
    result = parse_sec_package(package, tmp_path / "p11")
    fact = result.facts[0]
    assert fact["nil"] is True
    assert fact["parsed_numeric_candidate"] is None
    dimensions = fact["dimensions"]
    assert {row["dimension_kind"] for row in dimensions} == {"EXPLICIT", "TYPED"}
    assert next(row for row in dimensions if row["dimension_kind"] == "EXPLICIT")["member_qname"] == "ex:North"
    typed = next(row for row in dimensions if row["dimension_kind"] == "TYPED")
    assert typed["member_qname"] is None
    assert "North" in typed["typed_value"]


def _xml_package() -> object:
    xml = b'''<?xml version="1.0" encoding="UTF-8"?>
    <xbrli:xbrl xmlns:xbrli="http://www.xbrl.org/2003/instance"
                xmlns:us-gaap="http://fasb.org/us-gaap/2025"
                xmlns:ex="http://example.test/ex"
                xmlns:iso4217="http://www.xbrl.org/2003/iso4217">
      <xbrli:context id="c1">
        <xbrli:entity><xbrli:identifier scheme="http://www.sec.gov/CIK">0000320193</xbrli:identifier></xbrli:entity>
        <xbrli:period><xbrli:instant>2025-06-30</xbrli:instant></xbrli:period>
      </xbrli:context>
      <xbrli:unit id="USD"><xbrli:measure>iso4217:USD</xbrli:measure></xbrli:unit>
      <us-gaap:Revenues contextRef="c1" unitRef="USD" decimals="0">100</us-gaap:Revenues>
      <ex:Comment contextRef="c1">hello</ex:Comment>
    </xbrli:xbrl>'''
    return build_package(
        cik="0000320193",
        accession="0000320193-25-000002",
        form="10-Q",
        fiscal_year=2025,
        period="Q2",
        members=(
            SecPackageMember(
                relative_name="example.htm",
                role=SecMemberRole.PRIMARY_DOCUMENT,
                content_type="text/html",
                source_url=_sec_url("0000320193", "0000320193-25-000002", "example.htm"),
                body=b"<html><body><p>XML instance source</p></body></html>",
            ),
            SecPackageMember(
                relative_name="example.xml",
                role=SecMemberRole.XBRL_INSTANCE,
                content_type="application/xml",
                source_url=_sec_url("0000320193", "0000320193-25-000002", "example.xml"),
                body=xml,
            ),
        ),
    )


def test_xml_instance_facts_preserve_source_qname_and_locator(tmp_path: Path) -> None:
    package = _xml_package()
    observation = _observation(package)
    result = parse_sec_package(package, tmp_path / "p11", discovery_observation=observation)

    assert {fact["raw_qname"] for fact in result.facts} == {"us-gaap:Revenues", "ex:Comment"}
    numeric = next(fact for fact in result.facts if fact["raw_qname"] == "us-gaap:Revenues")
    evidence = next(row for row in result.evidence if row["evidence_id"] == numeric["evidence_id"])
    assert numeric["parsed_numeric_candidate"] == "100"
    assert evidence["locator_kind"] == "XML_PATH"
    assert evidence["xml_locator"].startswith("/")
    assert evidence["member_sha256"] != package.members[0].member_sha256

    validation = validate_sec_artifacts(
        result,
        tmp_path / "p7",
        package=package,
        discovery_observation=observation,
    )
    assert validation.validation_status == "PASS"


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("block_id", "0" * 64),
        ("dom_locator", "/html[1]/body[1]/missing[1]"),
        ("member_sha256", "1" * 64),
        ("fragment_hash", "2" * 64),
    ),
)
def test_validation_blocks_corrupt_html_evidence_round_trip(
    tmp_path: Path,
    field: str,
    value: str,
) -> None:
    package = _package()
    parsed = parse_sec_package(package, tmp_path / "p11")
    evidence = dict(parsed.evidence[0])
    evidence[field] = value
    corrupted = replace(parsed, evidence=(evidence,))

    validation = validate_sec_artifacts(corrupted, tmp_path / "p7", package=package)

    assert validation.validation_status == "BLOCKED"
    assert any(
        issue["code"] in {
            P11Reason.P11_EVIDENCE_LOCATOR_INVALID.value,
            P11Reason.P11_MEMBER_HASH_MISMATCH.value,
        }
        for issue in validation.issues
    )

