from __future__ import annotations

import base64
import json
import sqlite3
from dataclasses import replace
from pathlib import Path

import pytest

from financial_filing_data_foundation.registry import SQLiteRegistry
from financial_filing_data_foundation.us_sec.discovery import (
    SEC_DISCOVERY_SCHEMA,
    SecDiscoveryObservation,
)
from financial_filing_data_foundation.us_sec.errors import P11Reason, SecError
from financial_filing_data_foundation.us_sec.identity import sec_company
from financial_filing_data_foundation.us_sec.models import SecCompanyRef, SecFilingCandidate, SecIssuerKind
from financial_filing_data_foundation.us_sec.package import (
    SecMemberRole,
    SecPackageMember,
    build_package,
)
from financial_filing_data_foundation.us_sec.parser import (
    SEC_ARTIFACT_SCHEMA,
    VIRTUAL_HTML_NORMALIZER_VERSION,
    parse_sec_package,
    verify_sec_evidence,
)
from financial_filing_data_foundation.us_sec.ticker_map import snapshot_ticker_map
from financial_filing_data_foundation.us_sec.path_policy import archive_member_url
from financial_filing_data_foundation.us_sec.validation import validate_sec_artifacts


CIK = "0000320193"
ACCESSION = "0000320193-25-000001"


def _member(name: str, role: SecMemberRole, body: bytes, *, accession: str = ACCESSION) -> SecPackageMember:
    content_type = "text/html" if role is SecMemberRole.PRIMARY_DOCUMENT else "application/xml"
    return SecPackageMember(
        relative_name=name,
        role=role,
        content_type=content_type,
        source_url=archive_member_url(CIK, accession, name),
        body=body,
    )


def _package(html: bytes, *, extra: tuple[SecPackageMember, ...] = (), accession: str = ACCESSION):
    primary = _member("example.htm", SecMemberRole.PRIMARY_DOCUMENT, html, accession=accession)
    return build_package(
        cik=CIK,
        accession=accession,
        form="10-Q",
        fiscal_year=2025,
        period="Q2",
        members=(primary, *extra),
    )


def _observation(package) -> SecDiscoveryObservation:
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
    candidate = SecFilingCandidate(
        cik=package.cik,
        ticker="AAPL",
        accession=package.accession,
        normalized_accession=package.accession.replace("-", ""),
        form=package.form,
        filing_date="2025-07-30",
        report_period="2025-06-30",
        primary_document=package.primary_document,
        source_url=archive_member_url(package.cik, package.accession, package.primary_document),
        amended=False,
        issuer_kind=SecIssuerKind.DOMESTIC,
    )
    return SecDiscoveryObservation.create(
        company=SecCompanyRef(
            cik=package.cik,
            ticker="AAPL",
            company_id=f"US:CIK{package.cik}",
            issuer_kind=SecIssuerKind.DOMESTIC,
        ),
        fiscal_year=package.fiscal_year,
        period=package.period,
        source_documents=[
            {
                "url": "https://data.sec.gov/submissions/CIK0000320193.json",
                "body": body,
            }
        ],
        candidates=(candidate,),
        selected_accession=package.accession,
        state="UNAMBIGUOUS",
        retrieved_at="2026-11-12T00:00:00+00:00",
    )


def _inline_html(*, continuation: str = "", extra: str = "") -> bytes:
    return (
        "<html xmlns:ix='http://www.xbrl.org/2013/inlineXBRL' xmlns:xbrli='http://www.xbrl.org/2003/instance' xmlns:us-gaap='http://fasb.org/us-gaap/2025'><body><ix:header>"
        "<xbrli:context id='c1'><xbrli:entity><xbrli:identifier>0000320193</xbrli:identifier>"
        "</xbrli:entity><xbrli:period><xbrli:instant>2025-06-30</xbrli:instant>"
        "</xbrli:period></xbrli:context>"
        "<xbrli:unit id='USD'><xbrli:measure>iso4217:USD</xbrli:measure></xbrli:unit>"
        "</ix:header><h1>Revenue</h1><p>"
        f"<ix:nonfraction name='us-gaap:Revenues' contextRef='c1' unitRef='USD' decimals='0'{continuation}>10"
        "</ix:nonfraction>"
        f"{extra}</p></body></html>"
    ).encode()


def test_corrected_target_versions_and_observation_are_deterministic(tmp_path: Path) -> None:
    assert SEC_DISCOVERY_SCHEMA == "p11-sec-discovery-v1"
    assert VIRTUAL_HTML_NORMALIZER_VERSION == "VIRTUAL_HTML_V6"
    assert SEC_ARTIFACT_SCHEMA == "p11-sec-artifacts-v2"
    company = SecCompanyRef(cik=CIK, ticker="AAPL", company_id=f"US:CIK{CIK}")
    observation = SecDiscoveryObservation.create(
        company=company,
        fiscal_year=2025,
        period="Q2",
        source_documents=[{"url": "https://data.sec.gov/submissions/CIK0000320193.json", "body": b"{}"}],
        candidates=(),
        selected_accession=None,
        state="NOT_FOUND",
        retrieved_at="2026-11-11T00:00:00+00:00",
    )
    assert observation.to_dict()["schema_version"] == SEC_DISCOVERY_SCHEMA
    assert observation.observation_sha256 == SecDiscoveryObservation.create(
        company=company,
        fiscal_year=2025,
        period="Q2",
        source_documents=[{"url": "https://data.sec.gov/submissions/CIK0000320193.json", "body": b"{}"}],
        candidates=(),
        selected_accession=None,
        state="NOT_FOUND",
        retrieved_at="2026-11-11T00:00:00+00:00",
    ).observation_sha256


def test_package_member_url_is_bound_to_cik_accession_and_name() -> None:
    with pytest.raises(SecError) as exc_info:
        build_package(
            cik=CIK,
            accession=ACCESSION,
            form="10-Q",
            fiscal_year=2025,
            period="Q2",
            members=(
                SecPackageMember(
                    relative_name="example.htm",
                    role=SecMemberRole.PRIMARY_DOCUMENT,
                    content_type="text/html",
                    source_url="https://www.sec.gov/Archives/edgar/data/320193/other-accession/example.htm",
                    body=b"<html></html>",
                ),
            ),
        )
    assert exc_info.value.reason_code == P11Reason.P11_PROVENANCE_MISMATCH.value


def test_inline_and_instance_do_not_create_two_logical_fact_sets(tmp_path: Path) -> None:
    xml = (
        b"<xbrl xmlns='http://www.xbrl.org/2003/instance' xmlns:us-gaap='http://fasb.org/us-gaap/2024'>"
        b"<context id='c1'><entity><identifier>0000320193</identifier></entity><period><instant>2025-06-30</instant></period></context>"
        b"<unit id='USD'><measure>iso4217:USD</measure></unit>"
        b"<us-gaap:Revenues contextRef='c1' unitRef='USD'>999</us-gaap:Revenues></xbrl>"
    )
    unrelated = _member("unrelated.xml", SecMemberRole.OTHER, xml)
    package = _package(
        _inline_html(),
        extra=(unrelated, _member("example.xml", SecMemberRole.XBRL_INSTANCE, xml)),
    )
    parsed = parse_sec_package(package, tmp_path / "p11")
    assert parsed.fact_source_mode == "INLINE_XBRL_PRIMARY"
    assert len(parsed.facts) == 1
    assert parsed.facts[0]["raw_value"] == "10"


def test_non_inline_uses_one_instance_and_multiple_instances_fail_closed(tmp_path: Path) -> None:
    html = (
        b"<html><body><xbrli:context id='c1'><xbrli:entity>WRONG-HTML-CONTEXT</xbrli:entity>"
        b"</xbrli:context><h1>Revenue</h1></body></html>"
    )
    xml = (
        b"<xbrl xmlns='http://www.xbrl.org/2003/instance' xmlns:us-gaap='http://fasb.org/us-gaap/2024'>"
        b"<context id='c1'><entity><identifier>0000320193</identifier></entity><period><instant>2025-06-30</instant></period></context>"
        b"<unit id='USD'><measure>iso4217:USD</measure></unit>"
        b"<us-gaap:Revenues contextRef='c1' unitRef='USD'>999</us-gaap:Revenues></xbrl>"
    )
    one = _package(html, extra=(_member("example.xml", SecMemberRole.XBRL_INSTANCE, xml),))
    parsed = parse_sec_package(one, tmp_path / "one")
    assert parsed.fact_source_mode == "XBRL_INSTANCE_PRIMARY"
    assert len(parsed.facts) == 1
    assert parsed.facts[0]["entity"] == "0000320193"
    two = _package(
        html,
        extra=(
            _member("example.xml", SecMemberRole.XBRL_INSTANCE, xml),
            _member("example-2.xml", SecMemberRole.XBRL_INSTANCE, xml),
        ),
    )
    with pytest.raises(SecError) as exc_info:
        parse_sec_package(two, tmp_path / "two")
    assert exc_info.value.reason_code == P11Reason.P11_XBRL_INSTANCE_AMBIGUOUS.value


def test_continuation_chain_exclude_and_fragment_evidence_round_trip(tmp_path: Path) -> None:
    html = _inline_html(
        continuation=" continuedAt='c1'",
        extra="<ix:continuation id='c1' continuedAt='c2'>20</ix:continuation><ix:continuation id='c2'>30<ix:exclude>ignored</ix:exclude></ix:continuation>",
    )
    package = _package(html)
    observation = _observation(package)
    parsed = parse_sec_package(package, tmp_path / "p11", discovery_observation=observation)
    assert parsed.facts[0]["raw_value"] == "10 20 30"
    fragments = parsed.evidence[0]["source_fragments"]
    assert len(fragments) == 3
    assert "ignored" not in parsed.facts[0]["raw_value"]
    verify_sec_evidence(package, parsed.pages, parsed.evidence[0])
    assert validate_sec_artifacts(
        parsed,
        tmp_path / "p7",
        package=package,
        discovery_observation=observation,
    ).validation_status == "PASS"


@pytest.mark.parametrize(
    "extra",
    [
        "<ix:continuation id='missing'>20</ix:continuation>",
        "<ix:continuation id='c1'>20</ix:continuation><ix:continuation id='c1'>30</ix:continuation>",
        "<ix:continuation id='c1' continuedAt='c1'>20</ix:continuation>",
    ],
)
def test_invalid_continuation_is_blocking_and_not_appended(tmp_path: Path, extra: str) -> None:
    html = _inline_html(continuation=" continuedAt='c1'", extra=extra)
    parsed = parse_sec_package(_package(html), tmp_path / "p11")
    assert parsed.facts[0]["raw_value"] == "10"
    assert any(issue["code"] == P11Reason.P11_INLINE_CONTINUATION_INVALID.value for issue in parsed.issues)


def test_sec_table_uses_occupied_grid_and_real_th_cells(tmp_path: Path) -> None:
    html = _inline_html(
        extra="<table><tr><td colspan='2'>body</td></tr><tr><th rowspan='2'>H</th><th>V</th></tr><tr><th>W</th></tr></table>"
    )
    parsed = parse_sec_package(_package(html), tmp_path / "p11")
    table = parsed.tables[0]
    assert table["column_count"] == 2
    assert table["value_column_count"] == 2
    assert table["rows"][0]["cells"][0]["role"] == "BODY"
    assert table["header_tree"]
    assert all(cell["text"] != "body" for row in table["header_tree"] for cell in row)


def test_registry_fresh_sec_schema_is_v4_and_legacy_user_version_is_one(tmp_path: Path) -> None:
    registry = SQLiteRegistry(tmp_path / "registry.sqlite")
    assert registry.schema_version() == 1
    assert registry.sec_schema_version() == 4
    with sqlite3.connect(tmp_path / "registry.sqlite") as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 1
        assert conn.execute("SELECT value FROM sec_schema_metadata WHERE key='schema_version'").fetchone()[0] == "4"


def test_registry_v3_to_v4_migration_is_additive_and_idempotent(tmp_path: Path) -> None:
    db = tmp_path / "v3.sqlite"
    SQLiteRegistry(db)
    with sqlite3.connect(db) as conn:
        conn.execute("DROP INDEX idx_sec_discovery_slot")
        conn.execute("DROP TABLE sec_discovery_observations")
        conn.execute("UPDATE sec_schema_metadata SET value='3' WHERE key='schema_version'")
        conn.commit()
    with sqlite3.connect(db) as conn:
        before_source_tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
    assert not any(row[0] == "sec_discovery_observations" for row in before_source_tables)

    assert SQLiteRegistry(db).sec_schema_version() == 4
    with sqlite3.connect(db) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 1
        assert conn.execute("SELECT value FROM sec_schema_metadata WHERE key='schema_version'").fetchone()[0] == "4"
        assert conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='sec_discovery_observations'"
        ).fetchone() == ("sec_discovery_observations",)
        after = conn.execute(
            "SELECT name, sql FROM sqlite_master WHERE type IN ('table', 'index') ORDER BY name"
        ).fetchall()
    snapshot = tuple(after)
    SQLiteRegistry(db)
    with sqlite3.connect(db) as conn:
        assert tuple(
            conn.execute(
                "SELECT name, sql FROM sqlite_master WHERE type IN ('table', 'index') ORDER BY name"
            ).fetchall()
        ) == snapshot


def test_ticker_snapshot_reparses_verified_source_bytes() -> None:
    source = b'{"0":{"ticker":"AAPL","cik_str":320193}}'
    snapshot = snapshot_ticker_map(source, source_url="https://www.sec.gov/files/company_tickers.json")
    tampered = replace(snapshot, mapping={"AAPL": ("0000000001",)})
    with pytest.raises(SecError) as exc_info:
        tampered.verify()
    assert exc_info.value.reason_code == P11Reason.P11_TICKER_SNAPSHOT_INVALID.value
    source_tampered = replace(snapshot, source_bytes_b64=base64.b64encode(b"{}").decode("ascii"))
    with pytest.raises(SecError) as exc_info:
        source_tampered.verify()
    assert exc_info.value.reason_code == P11Reason.P11_TICKER_SNAPSHOT_INVALID.value


def test_sec_company_is_available_without_development_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FFDF_P11_US_DEV", raising=False)
    assert sec_company(cik=CIK, ticker=None).company_id == "US:CIK0000320193"
