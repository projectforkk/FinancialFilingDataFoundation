from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from financial_filing_data_foundation.registry import SQLiteRegistry
from financial_filing_data_foundation.us_sec.package import (
    SecMemberRole,
    SecPackageMember,
    SecPackageStore,
    build_package,
)
from financial_filing_data_foundation.us_sec.registry import (
    SEC_REGISTRY_SCHEMA_VERSION,
    register_sec_package,
    register_sec_slot,
)
from financial_filing_data_foundation.us_sec.planner import SecPlanAction, plan_sec_slot


def _package() -> object:
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
                source_url="https://www.sec.gov/Archives/edgar/data/1/example.htm",
                body=b"<html><body>filing</body></html>",
            ),
            SecPackageMember(
                relative_name="example.xsd",
                role=SecMemberRole.XBRL_SCHEMA,
                content_type="application/xml",
                source_url="https://www.sec.gov/Archives/edgar/data/1/example.xsd",
                body=b"<schema/>",
            ),
        ),
    )


def test_package_hash_is_canonical_and_store_is_immutable(tmp_path: Path) -> None:
    package = _package()
    expected = hashlib.sha256(
        json.dumps(
            [
                {
                    "role": "PRIMARY_DOCUMENT",
                    "relative_name": "example.htm",
                    "member_sha256": hashlib.sha256(b"<html><body>filing</body></html>").hexdigest(),
                    "byte_length": 32,
                },
                {
                    "role": "XBRL_SCHEMA",
                    "relative_name": "example.xsd",
                    "member_sha256": hashlib.sha256(b"<schema/>").hexdigest(),
                    "byte_length": 9,
                },
            ],
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    assert package.package_sha256 == expected

    store = SecPackageStore(tmp_path / "raw-store")
    first = store.put(package)
    second = store.put(package)
    assert first == second
    assert (first / "manifest.json").is_file()
    assert (first / "members" / "example.htm").read_bytes().startswith(b"<html")

    with pytest.raises(Exception) as exc_info:
        (first / "members" / "example.htm").write_bytes(b"changed")
        store.load(package.package_sha256)
    assert "hash" in str(exc_info.value).lower() or "immutable" in str(exc_info.value).lower()


def test_registry_adds_sec_tables_without_rewriting_legacy_rows(tmp_path: Path) -> None:
    db = tmp_path / "registry.sqlite"
    registry = SQLiteRegistry(db)
    package = _package()
    package_dir = SecPackageStore(tmp_path / "raw-store").put(package)
    register_sec_package(registry, package)
    register_sec_slot(
        registry,
        package,
        fiscal_year=2025,
        period="Q2",
        artifact_path="workspace/ingest/us/sec/p7/demo",
    )

    assert SEC_REGISTRY_SCHEMA_VERSION == 2
    with sqlite3.connect(db) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        assert {"source_packages", "package_members", "sec_filing_bindings", "sec_parsed_data"} <= tables
        row = conn.execute(
            "SELECT package_sha256, provider FROM source_packages"
        ).fetchone()
    assert row == (package.package_sha256, "sec")
    assert package_dir.exists()


def test_incremental_planner_is_reuse_first_and_conflict_safe() -> None:
    assert plan_sec_slot(parsed_available=True, package_available=True).action is SecPlanAction.REUSE_DATA
    assert plan_sec_slot(parsed_available=False, package_available=True).action is SecPlanAction.PARSE_LOCAL
    assert plan_sec_slot(parsed_available=False, package_available=False).action is SecPlanAction.DISCOVER_AND_ACQUIRE
    conflict = plan_sec_slot(parsed_available=True, package_available=True, amendment_conflict=True)
    assert conflict.action is SecPlanAction.REVIEW_REQUIRED

