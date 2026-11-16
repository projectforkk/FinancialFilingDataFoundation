from __future__ import annotations

import hashlib
import json
import sqlite3
from types import SimpleNamespace
from pathlib import Path

import pytest

from financial_filing_data_foundation.us_sec.errors import P11Reason, SecError
from financial_filing_data_foundation.us_sec.path_policy import archive_member_url, complete_submission_url
from financial_filing_data_foundation.us_sec.acquisition import SecAcquirer
from financial_filing_data_foundation.us_sec.http import SecHttpConfig, SecResponse
from financial_filing_data_foundation.us_sec.models import SecCompanyRef
from financial_filing_data_foundation.us_sec.package import SecMemberRole, SecPackageMember, SecPackageStore, build_package
from financial_filing_data_foundation.us_sec.source import (
    SEC_SOURCE_CONTAINER_SCHEMA,
    SEC_SOURCE_CONTAINER_KIND,
    SecPackageSourceProvenanceStore,
    SecSourceContainer,
    SecSourceContainerStore,
    build_package_source_provenance,
    parse_sec_submission,
    replay_package_source_provenance,
)
from financial_filing_data_foundation.registry import SQLiteRegistry


CIK = "0000320193"
ACCESSION = "0000320193-25-000001"


def _submission(primary: bytes = b"<html><body>  A\r\nB &amp; C  </body></html>\r\n") -> bytes:
    return (
        b"<SEC-DOCUMENT>0000320193-25-000001.txt : 20251101\r\n"
        b"<SEC-HEADER>\r\nHEADER\r\n</SEC-HEADER>\r\n"
        b"<DOCUMENT>\r\n"
        b"<TYPE>10-K\r\n"
        b"<SEQUENCE>1\r\n"
        b"<FILENAME>annual.htm\r\n"
        b"<TEXT>\r\n" + primary + b"</TEXT>\r\n"
        b"</DOCUMENT>\r\n"
        b"<DOCUMENT>\r\n"
        b"<TYPE>EX-101.INS\r\n"
        b"<SEQUENCE>2\r\n"
        b"<FILENAME>annual.xml\r\n"
        b"<TEXT>\r\n<XML>\r\n<root>\r\n  x\r\n</root>\r\n</XML>\r\n</TEXT>\r\n"
        b"</DOCUMENT>\r\n"
        b"</SEC-DOCUMENT>\r\n"
    )


def _package_source(body: bytes | None = None, *, include_xml: bool = False):
    source_body = _submission() if body is None else body
    container = SecSourceContainer.from_bytes(
        source_body,
        cik=CIK,
        accession=ACCESSION,
        source_url=complete_submission_url(CIK, ACCESSION),
    )
    inventory = parse_sec_submission(source_body, cik=CIK, accession=ACCESSION)
    primary = inventory.by_filename("annual.htm")
    members = [
        SecPackageMember(
            relative_name="annual.htm",
            role=SecMemberRole.PRIMARY_DOCUMENT,
            content_type="text/html",
            source_url=archive_member_url(CIK, ACCESSION, "annual.htm"),
            body=primary.payload(source_body),
        )
    ]
    if include_xml:
        xml = inventory.by_filename("annual.xml")
        members.append(
            SecPackageMember(
                relative_name="annual.xml",
                role=SecMemberRole.OTHER,
                content_type="application/xml",
                source_url=archive_member_url(CIK, ACCESSION, "annual.xml"),
                body=xml.payload(source_body),
            )
        )
    package = build_package(
        cik=CIK,
        accession=ACCESSION,
        form="10-K",
        fiscal_year=2025,
        period="FY",
        primary_document="annual.htm",
        members=members,
    )
    provenance = build_package_source_provenance(package, container, inventory)
    return package, container, inventory, provenance


def test_t148_01_complete_submission_url_is_exact() -> None:
    assert complete_submission_url(CIK, ACCESSION) == (
        "https://www.sec.gov/Archives/edgar/data/320193/"
        "000032019325000001/0000320193-25-000001.txt"
    )
    with pytest.raises(SecError):
        complete_submission_url(CIK, "bad-accession")


def test_t148_02_source_container_store_is_byte_immutable(tmp_path: Path) -> None:
    body = _submission()
    container = SecSourceContainer.from_bytes(
        body,
        cik=CIK,
        accession=ACCESSION,
        source_url=complete_submission_url(CIK, ACCESSION),
    )
    assert container.schema_version == SEC_SOURCE_CONTAINER_SCHEMA
    assert container.kind == SEC_SOURCE_CONTAINER_KIND
    assert container.source_container_sha256 == hashlib.sha256(body).hexdigest()
    store = SecSourceContainerStore(tmp_path / "raw-store")
    target = store.put(container)
    assert (target / "source.txt").read_bytes() == body
    assert store.put(container) == target
    (target / "source.txt").write_bytes(b"tampered")
    with pytest.raises(SecError) as exc_info:
        store.load(container.source_container_sha256)
    assert exc_info.value.reason_code == P11Reason.P11_SOURCE_DRIFT.value


def test_t148_03_to_05_inventory_and_payloads_preserve_bytes() -> None:
    body = _submission()
    inventory = parse_sec_submission(body, cik=CIK, accession=ACCESSION)
    assert [row.filename for row in inventory.documents] == ["annual.htm", "annual.xml"]
    html = inventory.by_filename("annual.htm")
    xml = inventory.by_filename("annual.xml")
    assert html.payload_envelope == "TEXT"
    assert html.payload(body) == b"<html><body>  A\r\nB &amp; C  </body></html>\r\n"
    assert xml.payload_envelope == "XML"
    assert xml.payload(body) == b"<root>\r\n  x\r\n</root>\r\n"
    assert body[html.payload_start : html.payload_end] == html.payload(body)
    assert body[xml.payload_start : xml.payload_end] == xml.payload(body)


def test_t148_06_active_content_is_rejected_only_as_canonical_payload() -> None:
    body = _submission(b"<html><body><SCRIPT>alert(1)</SCRIPT></body></html>\r\n")
    inventory = parse_sec_submission(body, cik=CIK, accession=ACCESSION)
    with pytest.raises(SecError) as exc_info:
        inventory.by_filename("annual.htm").validate_payload(body, primary=True)
    assert exc_info.value.reason_code == P11Reason.P11_CONTENT_TYPE_INVALID.value


def test_t148_07_to_08_acquisition_uses_only_complete_submission(tmp_path: Path) -> None:
    primary = (
        b'<html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL">'
        b"<body><h1>Annual</h1></body></html>\r\n"
    )
    body = (
        b"<SEC-DOCUMENT>0000320193-25-000001.txt : 20251101\r\n"
        b"<DOCUMENT>\r\n<TYPE>10-K\r\n<SEQUENCE>1\r\n<FILENAME>annual.htm\r\n<TEXT>\r\n"
        + primary
        + b"</TEXT>\r\n</DOCUMENT>\r\n"
        b"<DOCUMENT>\r\n<TYPE>EX-101.INS\r\n<SEQUENCE>2\r\n<FILENAME>annual.xml\r\n<TEXT>\r\n<XML>\r\n"
        b'<xbrl xmlns="http://www.xbrl.org/2003/instance"/>\r\n</XML>\r\n</TEXT>\r\n</DOCUMENT>\r\n'
        b"<DOCUMENT>\r\n<TYPE>EX-101.SCH\r\n<SEQUENCE>3\r\n<FILENAME>annual.xsd\r\n<TEXT>\r\n<XML>\r\n<schema/>\r\n</XML>\r\n</TEXT>\r\n</DOCUMENT>\r\n"
        b"<DOCUMENT>\r\n<TYPE>EX-99\r\n<SEQUENCE>4\r\n<FILENAME>unrelated.htm\r\n<TEXT>\r\n<html>unrelated</html>\r\n</TEXT>\r\n</DOCUMENT>\r\n"
        b"</SEC-DOCUMENT>\r\n"
    )
    url = complete_submission_url(CIK, ACCESSION)
    calls: list[str] = []

    class Client:
        config = SecHttpConfig(contact_email="ops@example.org")

        def fetch(self, request_url: str, **_: object) -> SecResponse:
            calls.append(request_url)
            assert request_url == url
            return SecResponse(200, {"Content-Type": "text/plain"}, body, request_url)

    observation = SimpleNamespace(
        state="UNAMBIGUOUS",
        selected_accession=ACCESSION,
        candidates=(
            {
                "accession": ACCESSION,
                "normalized_accession": ACCESSION.replace("-", ""),
                "form": "10-K",
                "filing_date": "2025-11-01",
                "report_period": "2025-09-27",
                "primary_document": "annual.htm",
                "source_url": "https://www.sec.gov/Archives/edgar/data/320193/000032019325000001/annual.htm",
                "amended": False,
                "issuer_kind": "DOMESTIC",
            },
        ),
    )
    result = SecAcquirer(Client(), SecPackageStore(tmp_path / "raw-store")).acquire(
        SecCompanyRef(cik=CIK, ticker="AAPL", company_id=f"US:CIK{CIK}"),
        fiscal_year=2025,
        period="FY",
        observation=observation,
    )
    assert calls == [url]
    assert {member.relative_name for member in result.package.members} == {"annual.htm", "annual.xml", "annual.xsd"}
    assert result.source_container.source_container_sha256 == hashlib.sha256(body).hexdigest()
    assert result.provenance.package_sha256 == result.package.package_sha256


def test_t148_09_provenance_is_replayable_and_external(tmp_path: Path) -> None:
    from financial_filing_data_foundation.us_sec.package import SecMemberRole, SecPackageMember, build_package

    body = _submission()
    container = SecSourceContainer.from_bytes(
        body,
        cik=CIK,
        accession=ACCESSION,
        source_url=complete_submission_url(CIK, ACCESSION),
    )
    inventory = parse_sec_submission(body, cik=CIK, accession=ACCESSION)
    package = build_package(
        cik=CIK,
        accession=ACCESSION,
        form="10-K",
        fiscal_year=2025,
        period="FY",
        primary_document="annual.htm",
        members=(
            SecPackageMember(
                relative_name="annual.htm",
                role=SecMemberRole.PRIMARY_DOCUMENT,
                content_type="text/html",
                source_url="https://www.sec.gov/Archives/edgar/data/320193/000032019325000001/annual.htm",
                body=inventory.by_filename("annual.htm").payload(body),
            ),
            SecPackageMember(
                relative_name="annual.xml",
                role=SecMemberRole.XBRL_INSTANCE,
                content_type="application/xml",
                source_url="https://www.sec.gov/Archives/edgar/data/320193/000032019325000001/annual.xml",
                body=inventory.by_filename("annual.xml").payload(body),
            ),
        ),
    )
    provenance = build_package_source_provenance(package, container, inventory)
    source_store = SecSourceContainerStore(tmp_path / "raw-store")
    provenance_store = SecPackageSourceProvenanceStore(tmp_path / "raw-store")
    source_store.put(container)
    path = provenance_store.put(provenance)
    assert path == provenance_store.provenance_dir(package.package_sha256, provenance.provenance_sha256)
    assert replay_package_source_provenance(package, source_store, provenance_store).provenance_sha256 == provenance.provenance_sha256


def test_t148_10_provenance_tamper_fails_closed(tmp_path: Path) -> None:
    body = _submission()
    container = SecSourceContainer.from_bytes(body, cik=CIK, accession=ACCESSION, source_url=complete_submission_url(CIK, ACCESSION))
    inventory = parse_sec_submission(body, cik=CIK, accession=ACCESSION)
    from financial_filing_data_foundation.us_sec.package import SecMemberRole, SecPackageMember, build_package

    package = build_package(
        cik=CIK,
        accession=ACCESSION,
        form="10-K",
        fiscal_year=2025,
        period="FY",
        members=(SecPackageMember(
            relative_name="annual.htm",
            role=SecMemberRole.PRIMARY_DOCUMENT,
            content_type="text/html",
            source_url="https://www.sec.gov/Archives/edgar/data/320193/000032019325000001/annual.htm",
            body=inventory.by_filename("annual.htm").payload(body),
        ),),
    )
    provenance = build_package_source_provenance(package, container, inventory)
    source_store = SecSourceContainerStore(tmp_path / "raw-store")
    provenance_store = SecPackageSourceProvenanceStore(tmp_path / "raw-store")
    source_store.put(container)
    path = provenance_store.put(provenance)
    tampered = path / "provenance.json"
    payload = tampered.read_text(encoding="utf-8").replace('"payload_start":', '"payload_start":999, "_old_payload_start":', 1)
    tampered.write_text(payload, encoding="utf-8")
    with pytest.raises(SecError) as exc_info:
        replay_package_source_provenance(package, source_store, provenance_store)
    assert exc_info.value.reason_code in {P11Reason.P11_PROVENANCE_MISMATCH.value, P11Reason.P11_PACKAGE_INVALID.value}


def test_t148_15_registry_v5_source_chain_round_trips(tmp_path: Path) -> None:
    from financial_filing_data_foundation.us_sec.package import SecMemberRole, SecPackageMember, build_package

    body = _submission()
    container = SecSourceContainer.from_bytes(body, cik=CIK, accession=ACCESSION, source_url=complete_submission_url(CIK, ACCESSION))
    inventory = parse_sec_submission(body, cik=CIK, accession=ACCESSION)
    package = build_package(
        cik=CIK,
        accession=ACCESSION,
        form="10-K",
        fiscal_year=2025,
        period="FY",
        members=(SecPackageMember(
            relative_name="annual.htm",
            role=SecMemberRole.PRIMARY_DOCUMENT,
            content_type="text/html",
            source_url="https://www.sec.gov/Archives/edgar/data/320193/000032019325000001/annual.htm",
            body=inventory.by_filename("annual.htm").payload(body),
        ),),
    )
    provenance = build_package_source_provenance(package, container, inventory)
    registry = SQLiteRegistry(tmp_path / "registry.sqlite")
    registry.register_sec_package(package)
    registry.register_sec_source_container(container)
    registry.register_sec_package_source_provenance(provenance)
    registry.verify_sec_package_source_provenance(package, provenance)
    assert registry.sec_schema_version() == 5
    assert registry.list_sec_package_source_provenance(package.package_sha256)[0]["provenance_sha256"] == provenance.provenance_sha256


def test_t148_16_validation_v4_binds_package_and_provenance(tmp_path: Path) -> None:
    from financial_filing_data_foundation.us_sec.discovery import SecDiscoveryObservation, parse_submissions
    from financial_filing_data_foundation.us_sec.identity import sec_company
    from financial_filing_data_foundation.us_sec.ingest import ingest_sec_package
    from financial_filing_data_foundation.us_sec.package import SecMemberRole, SecPackageMember, build_package
    from financial_filing_data_foundation.us_sec.validation import SEC_VALIDATION_SCHEMA, load_sec_validation

    body = _submission()
    container = SecSourceContainer.from_bytes(body, cik=CIK, accession=ACCESSION, source_url=complete_submission_url(CIK, ACCESSION))
    inventory = parse_sec_submission(body, cik=CIK, accession=ACCESSION)
    package = build_package(
        cik=CIK,
        accession=ACCESSION,
        form="10-K",
        fiscal_year=2025,
        period="FY",
        members=(SecPackageMember(
            relative_name="annual.htm",
            role=SecMemberRole.PRIMARY_DOCUMENT,
            content_type="text/html",
            source_url="https://www.sec.gov/Archives/edgar/data/320193/000032019325000001/annual.htm",
            body=inventory.by_filename("annual.htm").payload(body),
        ),),
    )
    provenance = build_package_source_provenance(package, container, inventory)
    company = sec_company(cik=CIK, ticker="AAPL")
    submissions = {
        "cik": CIK,
        "fiscalYearEnd": "0927",
        "filings": {
            "recent": {
                "accessionNumber": [ACCESSION],
                "filingDate": ["2025-11-01"],
                "reportDate": ["2025-09-27"],
                "form": ["10-K"],
                "primaryDocument": ["annual.htm"],
            }
        },
    }
    source_url = f"https://data.sec.gov/submissions/CIK{CIK}.json"
    source_bytes = json.dumps(submissions, sort_keys=True).encode("utf-8")
    candidates = parse_submissions(submissions, company=company, source_url=source_url).candidates
    observation = SecDiscoveryObservation.create(
        company=company,
        fiscal_year=2025,
        period="FY",
        source_documents=[{"url": source_url, "body": source_bytes}],
        candidates=candidates,
        selected_accession=ACCESSION,
        state="UNAMBIGUOUS",
        retrieved_at="2026-11-16T00:00:00+00:00",
    )
    result = ingest_sec_package(
        package,
        root=tmp_path,
        ticker="AAPL",
        period="FY",
        discovery_observation=observation,
        source_container=container,
        source_provenance=provenance,
    )
    assert SEC_VALIDATION_SCHEMA == "p11-sec-validation-v4"
    assert result.validation.package_source_provenance_sha256 == provenance.provenance_sha256
    assert result.validation.artifact_dir.name == SEC_VALIDATION_SCHEMA
    loaded = load_sec_validation(result.validation.artifact_dir)
    assert loaded.package_source_provenance_sha256 == provenance.provenance_sha256


@pytest.mark.parametrize(
    "mutator",
    (
        lambda body: body.replace(b"</DOCUMENT>\r\n", b"", 1),
        lambda body: body.replace(b"annual.xml", b"annual.htm", 1),
        lambda body: body.replace(b"annual.xml", b"../annual.xml", 1),
    ),
)
def test_t148_03_malformed_duplicate_and_unsafe_sgml_fail_closed(mutator) -> None:
    with pytest.raises(SecError) as exc_info:
        parse_sec_submission(mutator(_submission()), cik=CIK, accession=ACCESSION)
    assert exc_info.value.reason_code in {
        P11Reason.P11_PACKAGE_INVALID.value,
        P11Reason.P11_PRIMARY_DOCUMENT_MISSING.value,
    }


def test_t148_04_lf_structural_framing_is_excluded_without_payload_normalization() -> None:
    body = _submission().replace(b"\r\n", b"\n")
    inventory = parse_sec_submission(body, cik=CIK, accession=ACCESSION)
    html = inventory.by_filename("annual.htm")
    assert html.payload(body) == b"<html><body>  A\nB &amp; C  </body></html>\n"
    assert body[html.text_start : html.text_end] == html.payload(body)


def test_t148_11_legacy_unattested_package_cannot_drive_local_planner(tmp_path: Path) -> None:
    from financial_filing_data_foundation.us_sec.identity import sec_company
    from financial_filing_data_foundation.us_sec.registry import register_sec_package, register_sec_slot
    from financial_filing_data_foundation.user_cli import _runtime_paths, _us_plan_slot

    package, _, _, _ = _package_source()
    paths = _runtime_paths(tmp_path)
    SecPackageStore(paths.raw_store).put(package)
    registry = SQLiteRegistry(paths.registry)
    register_sec_package(registry, package)
    register_sec_slot(registry, package, fiscal_year=2025, period="FY")
    args = SimpleNamespace(year=2025, period="FY")

    plan, local = _us_plan_slot(
        sec_company(cik=CIK, ticker=None, allow_development=True),
        args,
        paths,
        registry,
        selected_accession=ACCESSION,
        discovery_state="UNAMBIGUOUS",
    )

    assert plan.action.value == "DISCOVER_AND_ACQUIRE"
    assert local is None


def test_t148_12_same_package_attestation_does_not_mutate_package_tree(tmp_path: Path) -> None:
    package, _, _, _ = _package_source(include_xml=True)
    paths = SimpleNamespace(raw_store=tmp_path / "raw-store", registry=tmp_path / "registry.sqlite")
    store = SecPackageStore(paths.raw_store)
    store.put(package)
    registry = SQLiteRegistry(paths.registry)
    registry.register_sec_package(package)

    class Client:
        config = SecHttpConfig(contact_email="ops@example.org")

        def fetch(self, request_url: str, **_: object) -> SecResponse:
            assert request_url == complete_submission_url(CIK, ACCESSION)
            return SecResponse(200, {"Content-Type": "text/plain"}, _submission(), request_url)

    package_dir = store.package_dir(package.package_sha256)
    before = {
        path.relative_to(package_dir).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in package_dir.rglob("*")
        if path.is_file()
    }
    result = SecAcquirer(Client(), store, registry=registry).acquire(
        SecCompanyRef(cik=CIK, ticker="AAPL", company_id=f"US:CIK{CIK}"),
        fiscal_year=2025,
        period="FY",
        observation=SimpleNamespace(
            state="UNAMBIGUOUS",
            selected_accession=ACCESSION,
            candidates=(
                {
                    "accession": ACCESSION,
                    "normalized_accession": ACCESSION.replace("-", ""),
                    "form": "10-K",
                    "filing_date": "2025-11-01",
                    "report_period": "2025-09-27",
                    "primary_document": "annual.htm",
                    "source_url": archive_member_url(CIK, ACCESSION, "annual.htm"),
                    "amended": False,
                    "issuer_kind": "DOMESTIC",
                },
            ),
        ),
    )

    after = {
        path.relative_to(package_dir).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in package_dir.rglob("*")
        if path.is_file()
    }
    assert result.reused is True
    assert result.package.package_sha256 == package.package_sha256
    assert before == after
    assert SecPackageSourceProvenanceStore(paths.raw_store).list_for_package(package.package_sha256)


def test_t148_13_legacy_and_current_packages_coexist_but_only_current_is_plannable(tmp_path: Path) -> None:
    from financial_filing_data_foundation.us_sec.identity import sec_company
    from financial_filing_data_foundation.us_sec.registry import register_sec_package, register_sec_slot
    from financial_filing_data_foundation.user_cli import _runtime_paths, _us_plan_slot

    legacy_body = _submission(b"<html><body>legacy delivery</body></html>\r\n")
    current_body = _submission(b"<html><body>current filed bytes</body></html>\r\n")
    legacy, _, _, _ = _package_source(legacy_body)
    current, container, inventory, _ = _package_source(current_body)
    current_provenance = build_package_source_provenance(current, container, inventory)
    paths = _runtime_paths(tmp_path)
    store = SecPackageStore(paths.raw_store)
    store.put(legacy)
    store.put(current, allow_accession_coexistence=True)
    registry = SQLiteRegistry(paths.registry)
    for package in (legacy, current):
        register_sec_package(registry, package)
        register_sec_slot(registry, package, fiscal_year=2025, period="FY")
    SecSourceContainerStore(paths.raw_store).put(container)
    SecPackageSourceProvenanceStore(paths.raw_store).put(current_provenance)
    registry.register_sec_source_container(container)
    registry.register_sec_package_source_provenance(current_provenance)

    plan, selected = _us_plan_slot(
        sec_company(cik=CIK, ticker=None, allow_development=True),
        SimpleNamespace(year=2025, period="FY"),
        paths,
        registry,
        selected_accession=ACCESSION,
        discovery_state="UNAMBIGUOUS",
    )

    assert legacy.package_sha256 != current.package_sha256
    assert {item.package_sha256 for item in store.find_all_by_accession(ACCESSION)} == {
        legacy.package_sha256,
        current.package_sha256,
    }
    assert plan.action.value == "PARSE_LOCAL"
    assert selected.package_sha256 == current.package_sha256


def test_t148_14_registry_rejects_current_container_and_package_conflicts(tmp_path: Path) -> None:
    first, container, inventory, provenance = _package_source(include_xml=False)
    registry = SQLiteRegistry(tmp_path / "container-conflict.sqlite")
    registry.register_sec_package(first)
    registry.register_sec_package_source_provenance(provenance)

    changed_body = _submission(b"<html><body>changed source</body></html>\r\n")
    changed, changed_container, changed_inventory, changed_provenance = _package_source(changed_body)
    registry.register_sec_package(changed)
    with pytest.raises(ValueError, match="P11_SOURCE_DRIFT"):
        registry.register_sec_package_source_provenance(changed_provenance)

    same_source_package, _, _, same_source_provenance = _package_source(include_xml=True)
    registry2 = SQLiteRegistry(tmp_path / "package-conflict.sqlite")
    registry2.register_sec_package(first)
    registry2.register_sec_package_source_provenance(provenance)
    registry2.register_sec_package(same_source_package)
    with pytest.raises(ValueError, match="P11_PROVENANCE_MISMATCH"):
        registry2.register_sec_package_source_provenance(same_source_provenance)


def test_t148_15_registry_v4_to_v5_is_additive_idempotent_and_future_fails_before_mutation(tmp_path: Path) -> None:
    db = tmp_path / "migration.sqlite"
    SQLiteRegistry(db)
    with sqlite3.connect(db) as conn:
        conn.execute("PRAGMA foreign_keys = OFF")
        for table in ("sec_package_member_locators", "sec_package_source_provenance", "sec_source_containers"):
            conn.execute(f"DROP TABLE {table}")
        conn.execute("UPDATE sec_schema_metadata SET value = '4' WHERE key = 'schema_version'")
        conn.commit()
    migrated = SQLiteRegistry(db)
    assert migrated.sec_schema_version() == 5
    with sqlite3.connect(db) as conn:
        tables = {
            str(row[0])
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name LIKE 'sec_%'"
            )
        }
        assert {
            "sec_source_containers",
            "sec_package_source_provenance",
            "sec_package_member_locators",
        } <= tables
        before = conn.execute("SELECT name, sql FROM sqlite_master WHERE type IN ('table', 'index') ORDER BY name").fetchall()
        conn.execute("UPDATE sec_schema_metadata SET value = '6' WHERE key = 'schema_version'")
        conn.commit()
    with pytest.raises(Exception):
        SQLiteRegistry(db)
    with sqlite3.connect(db) as conn:
        after = conn.execute("SELECT name, sql FROM sqlite_master WHERE type IN ('table', 'index') ORDER BY name").fetchall()
        assert after == before
        conn.execute("UPDATE sec_schema_metadata SET value = '5' WHERE key = 'schema_version'")
        conn.commit()
    assert SQLiteRegistry(db).sec_schema_version() == 5


def test_t148_16_validation_v3_is_not_a_current_fallback(tmp_path: Path) -> None:
    package, _, _, _ = _package_source()
    legacy_dir = tmp_path / package.package_sha256 / "p11-sec-validation-v3"
    legacy_dir.mkdir(parents=True)
    (legacy_dir / "validation.json").write_text(
        json.dumps({"schema_version": "p11-sec-validation-v3", "package_sha256": package.package_sha256}),
        encoding="utf-8",
    )
    (legacy_dir / "issues.jsonl").write_text("", encoding="utf-8")
    from financial_filing_data_foundation.us_sec.validation import load_sec_validation

    with pytest.raises(SecError):
        load_sec_validation(legacy_dir)


def test_t148_17_and_18_local_source_chain_never_needs_direct_member_network(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    package, container, inventory, provenance = _package_source()
    raw_store = tmp_path / "raw-store"
    SecPackageStore(raw_store).put(package)
    SecSourceContainerStore(raw_store).put(container)
    SecPackageSourceProvenanceStore(raw_store).put(provenance)

    def forbidden(*args, **kwargs):
        raise AssertionError("P8/source replay must not fetch SEC network bytes")

    monkeypatch.setattr("financial_filing_data_foundation.us_sec.http.SecHttpClient.fetch", forbidden)
    assert replay_package_source_provenance(
        SecPackageStore(raw_store).load(package.package_sha256),
        SecSourceContainerStore(raw_store),
        SecPackageSourceProvenanceStore(raw_store),
    ).provenance_sha256 == provenance.provenance_sha256
