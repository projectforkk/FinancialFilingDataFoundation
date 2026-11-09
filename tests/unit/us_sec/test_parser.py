from __future__ import annotations

from pathlib import Path

from financial_filing_data_foundation.us_sec.package import (
    SecMemberRole,
    SecPackageMember,
    build_package,
)
from financial_filing_data_foundation.us_sec.parser import (
    VIRTUAL_HTML_NORMALIZER_VERSION,
    load_sec_artifacts,
    parse_sec_package,
)


def _package() -> object:
    html = b"""
    <html><head><title>Example</title></head><body>
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
                source_url="https://www.sec.gov/Archives/edgar/data/320193/example.htm",
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
    assert result.facts
    assert {fact["raw_qname"] for fact in result.facts} >= {"us-gaap:Revenues", "ex:CustomMetric", "ex:Note"}
    revenue = next(fact for fact in result.facts if fact["raw_qname"] == "us-gaap:Revenues")
    evidence = next(row for row in result.evidence if row["evidence_id"] == revenue["evidence_id"])
    assert evidence["source_member_relative_name"] == "example.htm"
    assert evidence["dom_locator"].startswith("/")
    assert revenue["context_ref"] == "c1"
    assert any(issue["code"] == "P11_XBRL_CONTEXT_UNRESOLVED" for issue in result.issues)

    loaded = load_sec_artifacts(result.artifact_dir)
    assert loaded.package_sha256 == package.package_sha256
    assert loaded.facts == result.facts


def test_virtual_page_normalization_is_repeatable(tmp_path: Path) -> None:
    package = _package()
    first = parse_sec_package(package, tmp_path / "first")
    second = parse_sec_package(package, tmp_path / "second")
    assert first.pages == second.pages
    assert first.tables == second.tables
    assert first.facts == second.facts

