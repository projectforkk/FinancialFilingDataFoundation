from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from financial_filing_data_foundation.registry import RegistrySchemaUnsupported, SQLiteRegistry
from financial_filing_data_foundation.us_sec.errors import P11Reason, SecError
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
from financial_filing_data_foundation.us_sec.path_policy import archive_member_url


def _sec_url(accession: str, name: str) -> str:
    return archive_member_url("0000320193", accession, name)


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
                source_url=_sec_url("0000320193-25-000001", "example.htm"),
                body=b"<html><body>filing</body></html>",
            ),
            SecPackageMember(
                relative_name="example.xsd",
                role=SecMemberRole.XBRL_SCHEMA,
                content_type="application/xml",
                source_url=_sec_url("0000320193-25-000001", "example.xsd"),
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

    drifted = build_package(
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
                source_url=_sec_url("0000320193-25-000001", "example.htm"),
                body=b"<html><body>changed</body></html>",
            ),
        ),
    )
    with pytest.raises(Exception) as drift:
        SecPackageStore(tmp_path / "raw-store-drift").put(package)
        SecPackageStore(tmp_path / "raw-store-drift").put(drifted)
    assert "drift" in str(drift.value).lower()


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

    assert SEC_REGISTRY_SCHEMA_VERSION == 4
    with sqlite3.connect(db) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        assert {"source_packages", "package_members", "sec_filing_bindings", "sec_parsed_data", "sec_discovery_observations"} <= tables
        row = conn.execute(
            "SELECT package_sha256, provider FROM source_packages"
        ).fetchone()
    assert row == (package.package_sha256, "sec")
    assert package_dir.exists()


_LEGACY_V1_DDL = """
CREATE TABLE documents (
    document_sha256 TEXT PRIMARY KEY,
    file_size INTEGER NOT NULL,
    page_count INTEGER,
    first_seen_at TEXT NOT NULL
);

CREATE TABLE document_locations (
    path TEXT PRIMARY KEY,
    document_sha256 TEXT NOT NULL,
    mtime_ns INTEGER NOT NULL,
    last_seen_at TEXT NOT NULL,
    exists_flag INTEGER NOT NULL CHECK (exists_flag IN (0, 1)),
    FOREIGN KEY(document_sha256) REFERENCES documents(document_sha256)
);

CREATE INDEX idx_locations_sha ON document_locations(document_sha256);

CREATE TABLE document_sources (
    document_sha256 TEXT NOT NULL,
    provider TEXT NOT NULL,
    source_id TEXT NOT NULL,
    source_url TEXT NOT NULL,
    source_title TEXT NOT NULL,
    filing_date TEXT,
    report_date TEXT,
    provider_company_id TEXT,
    acquired_at TEXT,
    created_at TEXT NOT NULL,
    PRIMARY KEY(document_sha256, provider, source_id),
    FOREIGN KEY(document_sha256) REFERENCES documents(document_sha256)
);

CREATE INDEX idx_document_sources_sha ON document_sources(document_sha256);

CREATE TABLE filing_bindings (
    binding_id TEXT PRIMARY KEY,
    document_sha256 TEXT NOT NULL,
    market TEXT NOT NULL,
    company_id TEXT NOT NULL,
    filing_type TEXT NOT NULL,
    fiscal_year INTEGER NOT NULL,
    raw_fiscal_period TEXT NOT NULL,
    amended INTEGER,
    binding_status TEXT NOT NULL,
    source_provider TEXT,
    source_id TEXT,
    source_url TEXT,
    source_title TEXT,
    filing_date TEXT,
    report_date TEXT,
    provider_company_id TEXT,
    acquired_at TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(document_sha256) REFERENCES documents(document_sha256)
);

CREATE INDEX idx_bindings_slot
    ON filing_bindings(market, company_id, filing_type, fiscal_year, raw_fiscal_period);

CREATE INDEX idx_bindings_sha ON filing_bindings(document_sha256);

CREATE TABLE parsed_data (
    parse_run_id TEXT PRIMARY KEY,
    market TEXT NOT NULL,
    company_id TEXT NOT NULL,
    filing_type TEXT NOT NULL,
    fiscal_year INTEGER NOT NULL,
    raw_fiscal_period TEXT NOT NULL,
    document_sha256 TEXT NOT NULL,
    parser_version TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    validation_status TEXT NOT NULL,
    blocking_issue_count INTEGER NOT NULL,
    compatibility_status TEXT NOT NULL,
    artifact_path TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX idx_parsed_slot
    ON parsed_data(market, company_id, filing_type, fiscal_year, raw_fiscal_period);
"""

_SEC_V2_DDL = """
CREATE TABLE source_packages (
    package_sha256 TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    accession TEXT NOT NULL,
    cik TEXT NOT NULL,
    form TEXT NOT NULL,
    filed_date TEXT,
    accepted_at TEXT,
    report_period TEXT,
    primary_document TEXT NOT NULL,
    manifest_schema_version TEXT NOT NULL,
    first_seen_at TEXT NOT NULL
);

CREATE TABLE package_members (
    package_sha256 TEXT NOT NULL,
    member_sha256 TEXT NOT NULL,
    relative_name TEXT NOT NULL,
    role TEXT NOT NULL,
    content_type TEXT NOT NULL,
    byte_length INTEGER NOT NULL,
    source_url TEXT NOT NULL,
    PRIMARY KEY(package_sha256, relative_name),
    FOREIGN KEY(package_sha256) REFERENCES source_packages(package_sha256)
);

CREATE INDEX idx_package_members_sha ON package_members(member_sha256);

CREATE TABLE sec_filing_bindings (
    binding_id TEXT PRIMARY KEY,
    package_sha256 TEXT NOT NULL,
    company_id TEXT NOT NULL,
    fiscal_year INTEGER NOT NULL,
    raw_fiscal_period TEXT NOT NULL,
    accession TEXT NOT NULL,
    form TEXT NOT NULL,
    amended INTEGER NOT NULL CHECK (amended IN (0, 1)),
    binding_status TEXT NOT NULL,
    artifact_path TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(package_sha256) REFERENCES source_packages(package_sha256)
);

CREATE INDEX idx_sec_bindings_slot
    ON sec_filing_bindings(company_id, fiscal_year, raw_fiscal_period);

CREATE TABLE sec_parsed_data (
    parse_run_id TEXT PRIMARY KEY,
    package_sha256 TEXT NOT NULL,
    company_id TEXT NOT NULL,
    fiscal_year INTEGER NOT NULL,
    raw_fiscal_period TEXT NOT NULL,
    parser_version TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    validation_status TEXT NOT NULL,
    blocking_issue_count INTEGER NOT NULL,
    artifact_path TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(package_sha256) REFERENCES source_packages(package_sha256)
);

CREATE INDEX idx_sec_parsed_slot
    ON sec_parsed_data(company_id, fiscal_year, raw_fiscal_period);
"""

# Exact late-v2 SEC extension DDL from candidate
# 362877244aa553ca4d76eb71318b116cde04c6a5.
_SEC_V2_LATE_DDL = """
CREATE TABLE source_packages (
    package_sha256 TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    accession TEXT NOT NULL,
    cik TEXT NOT NULL,
    form TEXT NOT NULL,
    filed_date TEXT,
    accepted_at TEXT,
    report_period TEXT,
    primary_document TEXT NOT NULL,
    manifest_schema_version TEXT NOT NULL,
    first_seen_at TEXT NOT NULL
);

CREATE TABLE package_members (
    package_sha256 TEXT NOT NULL,
    member_sha256 TEXT NOT NULL,
    relative_name TEXT NOT NULL,
    role TEXT NOT NULL,
    content_type TEXT NOT NULL,
    byte_length INTEGER NOT NULL,
    source_url TEXT NOT NULL,
    PRIMARY KEY(package_sha256, relative_name),
    FOREIGN KEY(package_sha256) REFERENCES source_packages(package_sha256)
);

CREATE INDEX idx_package_members_sha ON package_members(member_sha256);

CREATE TABLE sec_filing_bindings (
    binding_id TEXT PRIMARY KEY,
    package_sha256 TEXT NOT NULL,
    company_id TEXT NOT NULL,
    fiscal_year INTEGER NOT NULL,
    raw_fiscal_period TEXT NOT NULL,
    accession TEXT NOT NULL,
    form TEXT NOT NULL,
    amended INTEGER NOT NULL CHECK (amended IN (0, 1)),
    binding_status TEXT NOT NULL,
    artifact_path TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(package_sha256) REFERENCES source_packages(package_sha256)
);

CREATE INDEX idx_sec_bindings_slot
    ON sec_filing_bindings(company_id, fiscal_year, raw_fiscal_period);

CREATE TABLE sec_parsed_data (
    parse_run_id TEXT PRIMARY KEY,
    package_sha256 TEXT NOT NULL,
    company_id TEXT NOT NULL,
    fiscal_year INTEGER NOT NULL,
    raw_fiscal_period TEXT NOT NULL,
    parser_version TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    validation_status TEXT NOT NULL,
    compatibility_status TEXT NOT NULL DEFAULT 'INCOMPATIBLE',
    blocking_issue_count INTEGER NOT NULL,
    artifact_path TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(package_sha256) REFERENCES source_packages(package_sha256)
);

CREATE INDEX idx_sec_parsed_slot
    ON sec_parsed_data(company_id, fiscal_year, raw_fiscal_period);
"""

_SEC_V2_PARSED_COLUMNS = (
    "parse_run_id",
    "package_sha256",
    "company_id",
    "fiscal_year",
    "raw_fiscal_period",
    "parser_version",
    "schema_version",
    "validation_status",
    "blocking_issue_count",
    "artifact_path",
    "created_at",
)

_SEC_V2_LATE_PARSED_COLUMNS = (
    "parse_run_id",
    "package_sha256",
    "company_id",
    "fiscal_year",
    "raw_fiscal_period",
    "parser_version",
    "schema_version",
    "validation_status",
    "compatibility_status",
    "blocking_issue_count",
    "artifact_path",
    "created_at",
)


def _snapshot_registry(db: Path) -> dict[str, object]:
    with sqlite3.connect(db) as conn:
        tables = tuple(
            row[0]
            for row in conn.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
                """
            )
        )
        table_sql = tuple(
            conn.execute(
                "SELECT name, sql FROM sqlite_master WHERE type = 'table' AND name = ?",
                (table,),
            ).fetchone()
            for table in tables
        )
        columns = {
            table: tuple(
                tuple(row)
                for row in conn.execute(f'PRAGMA table_info("{table}")').fetchall()
            )
            for table in tables
        }
        indexes = tuple(
            tuple(row)
            for row in conn.execute(
                """
                SELECT name, tbl_name, sql FROM sqlite_master
                WHERE type = 'index' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
                """
            ).fetchall()
        )
        rows = {
            table: tuple(
                tuple(row)
                for row in conn.execute(f'SELECT * FROM "{table}"').fetchall()
            )
            for table in tables
        }
        user_version = int(conn.execute("PRAGMA user_version").fetchone()[0])
    return {
        "user_version": user_version,
        "tables": tables,
        "table_sql": table_sql,
        "columns": columns,
        "indexes": indexes,
        "rows": rows,
    }


def _snapshot_rows_for_columns(
    snapshot: dict[str, object], table: str, column_names: tuple[str, ...]
) -> tuple[tuple[object, ...], ...]:
    columns = snapshot["columns"]
    rows = snapshot["rows"]
    assert isinstance(columns, dict)
    assert isinstance(rows, dict)
    positions = {
        str(column[1]): index
        for index, column in enumerate(columns[table])
    }
    return tuple(
        tuple(row[positions[column_name]] for column_name in column_names)
        for row in rows[table]
    )


def _make_v2_registry(
    db: Path, *, late: bool = False
) -> tuple[object, dict[str, object]]:
    package = _package()
    with sqlite3.connect(db) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        sec_ddl = _SEC_V2_LATE_DDL if late else _SEC_V2_DDL
        conn.executescript(_LEGACY_V1_DDL + sec_ddl)
        conn.execute("PRAGMA user_version = 1")
        legacy_sha = "a" * 64
        conn.execute(
            """
            INSERT INTO documents(
                document_sha256, file_size, page_count, first_seen_at
            ) VALUES (?, ?, ?, ?)
            """,
            (legacy_sha, 123, 1, "2026-11-11T00:00:00+00:00"),
        )
        conn.execute(
            """
            INSERT INTO document_locations(
                path, document_sha256, mtime_ns, last_seen_at, exists_flag
            ) VALUES (?, ?, ?, ?, ?)
            """,
            ("D:/legacy-cn.pdf", legacy_sha, 1, "2026-11-11T00:00:00+00:00", 1),
        )
        conn.execute(
            """
            INSERT INTO document_sources(
                document_sha256, provider, source_id, source_url, source_title,
                filing_date, report_date, provider_company_id, acquired_at,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                legacy_sha,
                "cninfo",
                "legacy-source",
                "https://example.invalid/legacy-cn.pdf",
                "legacy CN filing",
                "2025-03-31",
                "2024-12-31",
                "000001",
                "2026-11-11T00:00:00+00:00",
                "2026-11-11T00:00:00+00:00",
            ),
        )
        conn.execute(
            """
            INSERT INTO filing_bindings(
                binding_id, document_sha256, market, company_id, filing_type,
                fiscal_year, raw_fiscal_period, amended, binding_status,
                source_provider, source_id, source_url, source_title,
                filing_date, report_date, provider_company_id, acquired_at,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "legacy-binding",
                legacy_sha,
                "CN",
                "CN:000001",
                "ANNUAL",
                2024,
                "FY",
                0,
                "SOURCE_CONFIRMED",
                "cninfo",
                "legacy-source",
                "https://example.invalid/legacy-cn.pdf",
                "legacy CN filing",
                "2025-03-31",
                "2024-12-31",
                "000001",
                "2026-11-11T00:00:00+00:00",
                "2026-11-11T00:00:00+00:00",
            ),
        )
        conn.execute(
            """
            INSERT INTO parsed_data(
                parse_run_id, market, company_id, filing_type, fiscal_year,
                raw_fiscal_period, document_sha256, parser_version,
                schema_version, validation_status, blocking_issue_count,
                compatibility_status, artifact_path, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "legacy-run",
                "CN",
                "CN:000001",
                "ANNUAL",
                2024,
                "FY",
                legacy_sha,
                "legacy-parser-v1",
                "legacy-artifacts-v1",
                "PASS",
                0,
                "COMPATIBLE",
                "legacy-artifact",
                "2026-11-11T00:00:00+00:00",
            ),
        )
        manifest = package.manifest()
        conn.execute(
            """
            INSERT INTO source_packages(
                package_sha256, provider, accession, cik, form, filed_date,
                accepted_at, report_period, primary_document,
                manifest_schema_version, first_seen_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                manifest["package_sha256"],
                "sec",
                manifest["accession"],
                manifest["cik"],
                manifest["form"],
                manifest["filing_date"],
                manifest["accepted_at"],
                manifest["report_period"],
                manifest["primary_document"],
                manifest["schema_version"],
                "2026-11-11T00:00:00+00:00",
            ),
        )
        for member in package.canonical_members():
            conn.execute(
                """
                INSERT INTO package_members(
                    package_sha256, member_sha256, relative_name, role,
                    content_type, byte_length, source_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    package.package_sha256,
                    member.member_sha256,
                    member.relative_name,
                    member.role.value,
                    member.content_type,
                    len(member.body),
                    member.source_url,
                ),
            )
        binding_id = hashlib.sha256(
            f"{package.package_sha256}|US:CIK0000320193|2025|Q2|0".encode()
        ).hexdigest()
        conn.execute(
            """
            INSERT INTO sec_filing_bindings(
                binding_id, package_sha256, company_id, fiscal_year,
                raw_fiscal_period, accession, form, amended, binding_status,
                artifact_path, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                binding_id,
                package.package_sha256,
                "US:CIK0000320193",
                2025,
                "Q2",
                manifest["accession"],
                manifest["form"],
                0,
                "SOURCE_CONFIRMED",
                "old-v2-artifact",
                "2026-11-11T00:00:00+00:00",
            ),
        )
        if late:
            conn.execute(
                """
                INSERT INTO sec_parsed_data(
                    parse_run_id, package_sha256, company_id, fiscal_year,
                    raw_fiscal_period, parser_version, schema_version,
                    validation_status, compatibility_status,
                    blocking_issue_count, artifact_path, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "old-run",
                    package.package_sha256,
                    "US:CIK0000320193",
                    2025,
                    "Q2",
                    "VIRTUAL_HTML_V2",
                    "p11-sec-artifacts-v1",
                    "PASS",
                    "COMPATIBLE",
                    0,
                    "old-v2-artifact",
                    "2026-11-11T00:00:00+00:00",
                ),
            )
        else:
            conn.execute(
                """
                INSERT INTO sec_parsed_data(
                    parse_run_id, package_sha256, company_id, fiscal_year,
                    raw_fiscal_period, parser_version, schema_version,
                    validation_status, blocking_issue_count, artifact_path,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "old-run",
                    package.package_sha256,
                    "US:CIK0000320193",
                    2025,
                    "Q2",
                    "VIRTUAL_HTML_V2",
                    "p11-sec-artifacts-v1",
                    "PASS",
                    0,
                    "old-v2-artifact",
                    "2026-11-11T00:00:00+00:00",
                ),
            )
        conn.commit()
    return package, _snapshot_registry(db)


def test_sec_registry_migrates_real_v2_to_v3_without_rewriting_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db = tmp_path / "v2.sqlite"
    _package_obj, before = _make_v2_registry(db)

    before_columns = before["columns"]
    assert isinstance(before_columns, dict)
    assert "sec_schema_metadata" not in before["tables"]
    assert "compatibility_status" not in {
        str(column[1]) for column in before_columns["sec_parsed_data"]
    }
    assert before["user_version"] == 1

    migration_calls: list[bool] = []
    original_migration = SQLiteRegistry._migrate_sec_v2_to_v3.__func__

    def wrapped_migration(cls: type[SQLiteRegistry], conn: sqlite3.Connection) -> None:
        migration_calls.append(True)
        original_migration(cls, conn)

    monkeypatch.setattr(
        SQLiteRegistry,
        "_migrate_sec_v2_to_v3",
        classmethod(wrapped_migration),
    )

    registry = SQLiteRegistry(db)

    assert registry.schema_version() == 1
    assert registry.sec_schema_version() == 4
    assert migration_calls == [True]
    with sqlite3.connect(db) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 1
        metadata = conn.execute(
            "SELECT value FROM sec_schema_metadata WHERE key = 'schema_version'"
        ).fetchone()
        assert metadata == ("4",)
        columns = {
            row[1] for row in conn.execute("PRAGMA table_info('sec_parsed_data')")
        }
        assert "compatibility_status" in columns
        assert conn.execute(
            "SELECT compatibility_status FROM sec_parsed_data WHERE parse_run_id = 'old-run'"
        ).fetchone() == ("INCOMPATIBLE",)
    after = _snapshot_registry(db)
    assert set(after["tables"]) == set(before["tables"]) | {"sec_schema_metadata", "sec_discovery_observations"}
    for table in (
        "documents",
        "document_locations",
        "document_sources",
        "filing_bindings",
        "parsed_data",
    ):
        assert after["rows"][table] == before["rows"][table]
        assert after["columns"][table] == before["columns"][table]
    for table in ("source_packages", "package_members", "sec_filing_bindings"):
        assert after["rows"][table] == before["rows"][table]
        assert after["columns"][table] == before["columns"][table]
    assert _snapshot_rows_for_columns(
        after, "sec_parsed_data", _SEC_V2_PARSED_COLUMNS
    ) == before["rows"]["sec_parsed_data"]
    assert set(before["indexes"]).issubset(set(after["indexes"]))
    assert after["user_version"] == before["user_version"] == 1
    assert after["rows"]["sec_schema_metadata"] == (("schema_version", "4"),)


def test_sec_registry_v3_reopen_after_real_v2_migration_is_idempotent(
    tmp_path: Path,
) -> None:
    db = tmp_path / "v2-reopen.sqlite"
    _make_v2_registry(db)
    SQLiteRegistry(db)
    before = _snapshot_registry(db)

    reopened = SQLiteRegistry(db)

    assert reopened.sec_schema_version() == 4
    after = _snapshot_registry(db)
    assert after == before


def test_sec_registry_migrates_explicit_v2_metadata_variant(tmp_path: Path) -> None:
    db = tmp_path / "explicit-v2.sqlite"
    _make_v2_registry(db)
    with sqlite3.connect(db) as conn:
        conn.execute(
            "CREATE TABLE sec_schema_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        conn.execute(
            "INSERT INTO sec_schema_metadata(key, value) VALUES ('schema_version', '2')"
        )
        conn.commit()

    registry = SQLiteRegistry(db)

    assert registry.sec_schema_version() == 4
    with sqlite3.connect(db) as conn:
        assert conn.execute(
            "SELECT value FROM sec_schema_metadata WHERE key = 'schema_version'"
        ).fetchone() == ("4",)
        assert conn.execute(
            "SELECT compatibility_status FROM sec_parsed_data WHERE parse_run_id = 'old-run'"
        ).fetchone() == ("INCOMPATIBLE",)


def test_sec_registry_migrates_late_v2_with_compatibility_column_to_v3(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db = tmp_path / "late-v2.sqlite"
    _package_obj, before = _make_v2_registry(db, late=True)

    before_columns = before["columns"]
    assert isinstance(before_columns, dict)
    assert "sec_schema_metadata" not in before["tables"]
    assert "compatibility_status" in {
        str(column[1]) for column in before_columns["sec_parsed_data"]
    }
    assert _snapshot_rows_for_columns(
        before, "sec_parsed_data", ("compatibility_status",)
    ) == (("COMPATIBLE",),)
    assert before["user_version"] == 1

    migration_calls: list[bool] = []
    original_migration = SQLiteRegistry._migrate_sec_v2_to_v3.__func__

    def wrapped_migration(cls: type[SQLiteRegistry], conn: sqlite3.Connection) -> None:
        migration_calls.append(True)
        original_migration(cls, conn)

    monkeypatch.setattr(
        SQLiteRegistry,
        "_migrate_sec_v2_to_v3",
        classmethod(wrapped_migration),
    )

    registry = SQLiteRegistry(db)

    assert registry.schema_version() == 1
    assert registry.sec_schema_version() == 4
    assert migration_calls == [True]
    after = _snapshot_registry(db)
    assert set(after["tables"]) == set(before["tables"]) | {"sec_schema_metadata", "sec_discovery_observations"}
    for table in (
        "documents",
        "document_locations",
        "document_sources",
        "filing_bindings",
        "parsed_data",
        "source_packages",
        "package_members",
        "sec_filing_bindings",
    ):
        assert after["rows"][table] == before["rows"][table]
        assert after["columns"][table] == before["columns"][table]
    assert _snapshot_rows_for_columns(
        after,
        "sec_parsed_data",
        tuple(column for column in _SEC_V2_LATE_PARSED_COLUMNS if column != "compatibility_status"),
    ) == _snapshot_rows_for_columns(
        before,
        "sec_parsed_data",
        tuple(column for column in _SEC_V2_LATE_PARSED_COLUMNS if column != "compatibility_status"),
    )
    assert _snapshot_rows_for_columns(
        after, "sec_parsed_data", ("compatibility_status",)
    ) == (("INCOMPATIBLE",),)
    assert after["columns"]["sec_parsed_data"] == before["columns"]["sec_parsed_data"]
    before_table_sql = {item[0]: item for item in before["table_sql"]}
    after_table_sql = {item[0]: item for item in after["table_sql"]}
    for table in (
        "source_packages",
        "package_members",
        "sec_filing_bindings",
        "sec_parsed_data",
    ):
        assert after_table_sql[table] == before_table_sql[table]
    assert set(before["indexes"]).issubset(set(after["indexes"]))
    assert after["user_version"] == before["user_version"] == 1
    assert after["rows"]["sec_schema_metadata"] == (("schema_version", "4"),)

    snapshot1 = _snapshot_registry(db)
    SQLiteRegistry(db)
    snapshot2 = _snapshot_registry(db)
    assert snapshot2 == snapshot1


def test_unversioned_unknown_sec_shape_is_not_guessed_as_v2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db = tmp_path / "unknown-unversioned-sec.sqlite"
    _make_v2_registry(db)
    with sqlite3.connect(db) as conn:
        conn.execute(
            "ALTER TABLE sec_parsed_data ADD COLUMN future_unknown_field TEXT"
        )
        conn.commit()
    before = _snapshot_registry(db)
    migration_calls: list[bool] = []
    original_migration = SQLiteRegistry._migrate_sec_v2_to_v3.__func__

    def wrapped_migration(cls: type[SQLiteRegistry], conn: sqlite3.Connection) -> None:
        migration_calls.append(True)
        original_migration(cls, conn)

    monkeypatch.setattr(
        SQLiteRegistry,
        "_migrate_sec_v2_to_v3",
        classmethod(wrapped_migration),
    )

    with pytest.raises(RegistrySchemaUnsupported) as exc_info:
        SQLiteRegistry(db)

    assert exc_info.value.reason_code == "REGISTRY_SCHEMA_UNSUPPORTED"
    assert migration_calls == []
    after = _snapshot_registry(db)
    assert after == before


def test_future_sec_schema_fails_closed_without_mutation(tmp_path: Path) -> None:
    db = tmp_path / "future-sec-shape.sqlite"
    _make_v2_registry(db)
    with sqlite3.connect(db) as conn:
        conn.execute(
            "CREATE TABLE sec_schema_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        conn.execute(
            "INSERT INTO sec_schema_metadata(key, value) VALUES ('schema_version', '99')"
        )
        conn.commit()
    before = _snapshot_registry(db)

    with pytest.raises(RegistrySchemaUnsupported) as exc_info:
        SQLiteRegistry(db)

    assert exc_info.value.reason_code == "REGISTRY_SCHEMA_UNSUPPORTED"
    after = _snapshot_registry(db)
    assert after == before


def test_fresh_registry_uses_legacy_v1_and_sec_extension_v3(tmp_path: Path) -> None:
    db = tmp_path / "fresh.sqlite"
    registry = SQLiteRegistry(db)

    assert registry.schema_version() == 1
    assert registry.sec_schema_version() == 4
    with sqlite3.connect(db) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 1
        assert conn.execute(
            "SELECT value FROM sec_schema_metadata WHERE key = 'schema_version'"
        ).fetchone() == ("4",)


def test_unknown_sec_extension_version_fails_closed(tmp_path: Path) -> None:
    db = tmp_path / "future-sec.sqlite"
    SQLiteRegistry(db)
    with sqlite3.connect(db) as conn:
        conn.execute(
            "UPDATE sec_schema_metadata SET value = '99' WHERE key = 'schema_version'"
        )
        conn.commit()

    with pytest.raises(RegistrySchemaUnsupported) as exc_info:
        SQLiteRegistry(db)

    assert exc_info.value.reason_code == "REGISTRY_SCHEMA_UNSUPPORTED"
    assert "SEC" in str(exc_info.value)


def test_sec_parsed_data_none_compatibility_defaults_to_incompatible(tmp_path: Path) -> None:
    db = tmp_path / "none-compat.sqlite"
    registry = SQLiteRegistry(db)
    package = _package()
    registry.register_sec_package(package)
    registry.register_sec_parsed_data(
        parse_run_id="none-compat",
        package_sha256=package.package_sha256,
        company_id="US:CIK0000320193",
        fiscal_year=2025,
        period="Q2",
        parser_version="VIRTUAL_HTML_V4",
        schema_version="p11-sec-artifacts-v1",
        validation_status="PASS",
        blocking_issue_count=0,
        compatibility_status=None,
        artifact_path=None,
    )

    row = registry.list_sec_parsed_data(
        company_id="US:CIK0000320193", fiscal_year=2025, period="Q2"
    )[0]
    assert row["compatibility_status"] == "INCOMPATIBLE"


def test_incremental_planner_is_reuse_first_and_conflict_safe() -> None:
    assert plan_sec_slot(parsed_available=True, package_available=True).action is SecPlanAction.REUSE_DATA
    assert plan_sec_slot(parsed_available=False, package_available=True).action is SecPlanAction.PARSE_LOCAL
    assert plan_sec_slot(parsed_available=False, package_available=False).action is SecPlanAction.DISCOVER_AND_ACQUIRE
    conflict = plan_sec_slot(parsed_available=True, package_available=True, amendment_conflict=True)
    assert conflict.action is SecPlanAction.REVIEW_REQUIRED


@pytest.mark.parametrize("name", ["C:/evil.txt", "../evil.txt", "x\\evil.txt", "%2e%2e/evil.txt", "https://evil.example/x"])
def test_package_member_path_is_canonical_and_windows_safe(name: str) -> None:
    with pytest.raises(SecError) as exc_info:
        SecMemberRole.OTHER  # keep enum import exercised for the negative fixture
        SecPackageMember(
            relative_name=name,
            role=SecMemberRole.OTHER,
            content_type="text/plain",
            source_url="https://www.sec.gov/Archives/edgar/data/1/member.txt",
            body=b"x",
        )
    assert exc_info.value.reason_code in {P11Reason.P11_PACKAGE_INVALID.value, P11Reason.P11_ARCHIVE_HOST_REJECTED.value}


def test_package_store_finds_local_slot_without_network(tmp_path: Path) -> None:
    package = _package()
    store = SecPackageStore(tmp_path / "raw-store")
    store.put(package)
    found = store.find_by_slot(cik="320193", fiscal_year=2025, period="Q2")
    assert found is not None
    assert found.package_sha256 == package.package_sha256

