from __future__ import annotations

import hashlib
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

import pymupdf

from financial_filing_data_foundation.identity import (
    FilingIdentity,
    FilingSlotKey,
    SourceMetadata,
)
from financial_filing_data_foundation.registry.models import (
    BindingStatus,
    CompatibilityStatus,
    LocalDocumentState,
    LocalDocumentStatus,
    ParsedDataRecord,
    RegisteredDocument,
    ValidationStatus,
)


# The accepted CN/HK schema remains at v1 for backward compatibility.  P11's
# additive SEC extension has its own versioned table contract so opening an old
# registry never rewrites the legacy rows or changes their semantics.
REGISTRY_SCHEMA_VERSION = 1
SEC_REGISTRY_SCHEMA_VERSION = 3

_REQUIRED_SCHEMA_COLUMNS: dict[str, frozenset[str]] = {
    "documents": frozenset(
        {"document_sha256", "file_size", "page_count", "first_seen_at"}
    ),
    "document_locations": frozenset(
        {"path", "document_sha256", "mtime_ns", "last_seen_at", "exists_flag"}
    ),
    "document_sources": frozenset(
        {
            "document_sha256",
            "provider",
            "source_id",
            "source_url",
            "source_title",
            "filing_date",
            "report_date",
            "provider_company_id",
            "acquired_at",
            "created_at",
        }
    ),
    "filing_bindings": frozenset(
        {
            "binding_id",
            "document_sha256",
            "market",
            "company_id",
            "filing_type",
            "fiscal_year",
            "raw_fiscal_period",
            "amended",
            "binding_status",
            "source_provider",
            "source_id",
            "source_url",
            "source_title",
            "filing_date",
            "report_date",
            "provider_company_id",
            "acquired_at",
            "created_at",
        }
    ),
    "parsed_data": frozenset(
        {
            "parse_run_id",
            "market",
            "company_id",
            "filing_type",
            "fiscal_year",
            "raw_fiscal_period",
            "document_sha256",
            "parser_version",
            "schema_version",
            "validation_status",
            "blocking_issue_count",
            "compatibility_status",
            "artifact_path",
            "created_at",
        }
    ),
}


class RegistrySchemaUnsupported(RuntimeError):
    reason_code = "REGISTRY_SCHEMA_UNSUPPORTED"


_SEC_REQUIRED_SCHEMA_COLUMNS: dict[str, frozenset[str]] = {
    "sec_schema_metadata": frozenset({"key", "value"}),
    "source_packages": frozenset(
        {
            "package_sha256",
            "provider",
            "accession",
            "cik",
            "form",
            "filed_date",
            "accepted_at",
            "report_period",
            "primary_document",
            "manifest_schema_version",
            "first_seen_at",
        }
    ),
    "package_members": frozenset(
        {
            "package_sha256",
            "member_sha256",
            "relative_name",
            "role",
            "content_type",
            "byte_length",
            "source_url",
        }
    ),
    "sec_filing_bindings": frozenset(
        {
            "binding_id",
            "package_sha256",
            "company_id",
            "fiscal_year",
            "raw_fiscal_period",
            "accession",
            "form",
            "amended",
            "binding_status",
            "artifact_path",
            "created_at",
        }
    ),
    "sec_parsed_data": frozenset(
        {
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
        }
    ),
}

_SEC_CORE_TABLES = frozenset(
    {"source_packages", "package_members", "sec_filing_bindings", "sec_parsed_data"}
)
_SEC_SCHEMA_VERSION_KEY = "schema_version"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _binding_id(document_sha256: str, identity: FilingIdentity) -> str:
    amended = "UNKNOWN" if identity.amended is None else ("1" if identity.amended else "0")
    raw = f"{document_sha256}|{identity.slot.serialize()}|{amended}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


class SQLiteRegistry:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path).expanduser().resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
        finally:
            conn.close()

    def _initialize(self) -> None:
        with self._connect() as conn:
            version = int(conn.execute("PRAGMA user_version").fetchone()[0])
            if version > REGISTRY_SCHEMA_VERSION:
                raise RegistrySchemaUnsupported(
                    f"registry schema version {version} is newer than supported "
                    f"{REGISTRY_SCHEMA_VERSION}"
                )
            if version == 0:
                existing_user_tables = {
                    str(row["name"])
                    for row in conn.execute(
                        """
                        SELECT name FROM sqlite_master
                        WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
                        """
                    ).fetchall()
                }
                if existing_user_tables:
                    raise RegistrySchemaUnsupported(
                        "registry schema version 0 is non-empty; user tables: "
                        + ", ".join(sorted(existing_user_tables))
                    )
                self._create_schema(conn)
                self._create_sec_schema(conn)
                self._write_sec_schema_version(conn, SEC_REGISTRY_SCHEMA_VERSION)
                conn.execute(f"PRAGMA user_version = {REGISTRY_SCHEMA_VERSION}")
                conn.commit()
            elif version != REGISTRY_SCHEMA_VERSION:
                raise RegistrySchemaUnsupported(
                    f"unsupported registry schema version: {version}"
                )

            self._validate_schema_v1(conn)
            self._ensure_sec_schema(conn)
            self._validate_sec_schema(conn)

    @staticmethod
    def _validate_schema_v1(conn: sqlite3.Connection) -> None:
        rows = conn.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
            """
        ).fetchall()
        existing_tables = {str(row["name"]) for row in rows}
        missing_tables = sorted(set(_REQUIRED_SCHEMA_COLUMNS) - existing_tables)
        if missing_tables:
            raise RegistrySchemaUnsupported(
                "registry schema version 1 is incomplete; missing tables: "
                + ", ".join(missing_tables)
            )

        missing_columns: list[str] = []
        for table, required_columns in _REQUIRED_SCHEMA_COLUMNS.items():
            columns = {
                str(row["name"])
                for row in conn.execute(f'PRAGMA table_info("{table}")').fetchall()
            }
            for column in sorted(required_columns - columns):
                missing_columns.append(f"{table}.{column}")

        if missing_columns:
            raise RegistrySchemaUnsupported(
                "registry schema version 1 is incomplete; missing columns: "
                + ", ".join(missing_columns)
            )

    @staticmethod
    def _validate_sec_schema(conn: sqlite3.Connection) -> None:
        rows = conn.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
            """
        ).fetchall()
        existing_tables = {str(row["name"]) for row in rows}
        missing_tables = sorted(set(_SEC_REQUIRED_SCHEMA_COLUMNS) - existing_tables)
        if missing_tables:
            raise RegistrySchemaUnsupported(
                "SEC registry extension is incomplete; missing tables: "
                + ", ".join(missing_tables)
            )
        missing_columns: list[str] = []
        for table, required_columns in _SEC_REQUIRED_SCHEMA_COLUMNS.items():
            columns = {
                str(row["name"])
                for row in conn.execute(f'PRAGMA table_info("{table}")').fetchall()
            }
            for column in sorted(required_columns - columns):
                missing_columns.append(f"{table}.{column}")
        if missing_columns:
            raise RegistrySchemaUnsupported(
                "SEC registry extension is incomplete; missing columns: "
                + ", ".join(missing_columns)
            )

    @staticmethod
    def _sec_table_names(conn: sqlite3.Connection) -> set[str]:
        rows = conn.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
            """
        ).fetchall()
        return {str(row["name"]) for row in rows}

    @staticmethod
    def _read_sec_schema_version(conn: sqlite3.Connection) -> int | None:
        row = conn.execute(
            "SELECT value FROM sec_schema_metadata WHERE key = ?",
            (_SEC_SCHEMA_VERSION_KEY,),
        ).fetchone()
        if row is None:
            return None
        raw = str(row["value"])
        try:
            version = int(raw)
        except ValueError as exc:
            raise RegistrySchemaUnsupported(
                f"SEC registry schema version is invalid: {raw!r}"
            ) from exc
        if version <= 0:
            raise RegistrySchemaUnsupported(
                f"SEC registry schema version is invalid: {version}"
            )
        if version > SEC_REGISTRY_SCHEMA_VERSION:
            raise RegistrySchemaUnsupported(
                f"SEC registry schema version {version} is newer than supported "
                f"{SEC_REGISTRY_SCHEMA_VERSION}"
            )
        return version

    @staticmethod
    def _write_sec_schema_version(conn: sqlite3.Connection, version: int) -> None:
        conn.execute(
            """
            INSERT INTO sec_schema_metadata(key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (_SEC_SCHEMA_VERSION_KEY, str(int(version))),
        )

    @classmethod
    def _migrate_sec_v2_to_v3(cls, conn: sqlite3.Connection) -> None:
        if not conn.in_transaction:
            conn.execute("BEGIN")
        try:
            columns = {
                str(row["name"])
                for row in conn.execute("PRAGMA table_info('sec_parsed_data')").fetchall()
            }
            if "compatibility_status" not in columns:
                conn.execute(
                    "ALTER TABLE sec_parsed_data ADD COLUMN compatibility_status TEXT NOT NULL DEFAULT 'INCOMPATIBLE'"
                )
            # A v2 row has no independently persisted compatibility proof.  It
            # must remain fail-closed even when an older runtime had already
            # populated the additive column.
            conn.execute(
                "UPDATE sec_parsed_data SET compatibility_status = 'INCOMPATIBLE'"
            )
            cls._write_sec_schema_version(conn, SEC_REGISTRY_SCHEMA_VERSION)
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    @classmethod
    def _ensure_sec_schema(cls, conn: sqlite3.Connection) -> None:
        tables_before = cls._sec_table_names(conn)
        core_before = tables_before & _SEC_CORE_TABLES
        if core_before and core_before != _SEC_CORE_TABLES:
            missing = sorted(_SEC_CORE_TABLES - core_before)
            raise RegistrySchemaUnsupported(
                "SEC registry extension is incomplete; missing tables: "
                + ", ".join(missing)
            )
        if "sec_schema_metadata" in tables_before and not core_before:
            raise RegistrySchemaUnsupported(
                "SEC registry extension is incomplete; SEC core tables are missing"
            )

        cls._create_sec_schema(conn)
        stored_version = cls._read_sec_schema_version(conn)
        if not core_before:
            if stored_version is not None:
                raise RegistrySchemaUnsupported(
                    "SEC registry metadata exists without a legacy SEC schema"
                )
            cls._write_sec_schema_version(conn, SEC_REGISTRY_SCHEMA_VERSION)
            conn.commit()
            return
        if stored_version is None:
            # Existing SEC v2 databases did not persist their extension
            # version.  The old shape is inferred from the SEC core tables and
            # migrated without touching package/binding identity fields.
            cls._migrate_sec_v2_to_v3(conn)
            return
        if stored_version == 2:
            cls._migrate_sec_v2_to_v3(conn)
            return
        if stored_version != SEC_REGISTRY_SCHEMA_VERSION:
            raise RegistrySchemaUnsupported(
                f"unsupported SEC registry schema version: {stored_version}"
            )

    @staticmethod
    def _create_schema(conn: sqlite3.Connection) -> None:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS documents (
                document_sha256 TEXT PRIMARY KEY,
                file_size INTEGER NOT NULL,
                page_count INTEGER,
                first_seen_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS document_locations (
                path TEXT PRIMARY KEY,
                document_sha256 TEXT NOT NULL,
                mtime_ns INTEGER NOT NULL,
                last_seen_at TEXT NOT NULL,
                exists_flag INTEGER NOT NULL CHECK (exists_flag IN (0, 1)),
                FOREIGN KEY(document_sha256) REFERENCES documents(document_sha256)
            );

            CREATE INDEX IF NOT EXISTS idx_locations_sha
            ON document_locations(document_sha256);

            CREATE TABLE IF NOT EXISTS document_sources (
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

            CREATE INDEX IF NOT EXISTS idx_document_sources_sha
            ON document_sources(document_sha256);

            CREATE TABLE IF NOT EXISTS filing_bindings (
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

            CREATE INDEX IF NOT EXISTS idx_bindings_slot
            ON filing_bindings(
                market, company_id, filing_type, fiscal_year, raw_fiscal_period
            );

            CREATE INDEX IF NOT EXISTS idx_bindings_sha
            ON filing_bindings(document_sha256);

            CREATE TABLE IF NOT EXISTS parsed_data (
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

            CREATE INDEX IF NOT EXISTS idx_parsed_slot
            ON parsed_data(
                market, company_id, filing_type, fiscal_year, raw_fiscal_period
            );
            """
        )

    @staticmethod
    def _create_sec_schema(conn: sqlite3.Connection) -> None:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS source_packages (
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

            CREATE TABLE IF NOT EXISTS package_members (
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

            CREATE INDEX IF NOT EXISTS idx_package_members_sha
            ON package_members(member_sha256);

            CREATE TABLE IF NOT EXISTS sec_filing_bindings (
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

            CREATE INDEX IF NOT EXISTS idx_sec_bindings_slot
            ON sec_filing_bindings(company_id, fiscal_year, raw_fiscal_period);

            CREATE TABLE IF NOT EXISTS sec_parsed_data (
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

            CREATE INDEX IF NOT EXISTS idx_sec_parsed_slot
            ON sec_parsed_data(company_id, fiscal_year, raw_fiscal_period);

            CREATE TABLE IF NOT EXISTS sec_schema_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )
        sec_parsed_columns = {
            str(row["name"])
            for row in conn.execute("PRAGMA table_info('sec_parsed_data')").fetchall()
        }
        if "compatibility_status" not in sec_parsed_columns:
            # Existing v2 registries predate the explicit P7 compatibility
            # field.  Mark those rows incompatible until a new validation run
            # proves PASS + COMPATIBLE + zero blocking issues.
            conn.execute(
                "ALTER TABLE sec_parsed_data ADD COLUMN compatibility_status TEXT NOT NULL DEFAULT 'INCOMPATIBLE'"
            )

    def schema_version(self) -> int:
        with self._connect() as conn:
            return int(conn.execute("PRAGMA user_version").fetchone()[0])

    def sec_schema_version(self) -> int:
        """Return the additive P11 SEC extension version."""

        with self._connect() as conn:
            self._validate_sec_schema(conn)
            version = self._read_sec_schema_version(conn)
        if version != SEC_REGISTRY_SCHEMA_VERSION:
            raise RegistrySchemaUnsupported(
                f"unsupported SEC registry schema version: {version}"
            )
        return version

    def register_sec_package(self, package: object) -> None:
        manifest = package.manifest()
        package_sha = str(manifest["package_sha256"]).lower()
        now = _utc_now()
        members = tuple(package.canonical_members())
        with self._connect() as conn:
            existing = conn.execute(
                "SELECT * FROM source_packages WHERE package_sha256 = ?",
                (package_sha,),
            ).fetchone()
            package_values = (
                package_sha,
                "sec",
                str(manifest["accession"]),
                str(manifest["cik"]),
                str(manifest["form"]),
                manifest.get("filing_date"),
                manifest.get("accepted_at"),
                manifest.get("report_period"),
                str(manifest.get("primary_document") or ""),
                str(manifest["schema_version"]),
            )
            if existing is not None:
                existing_values = tuple(existing[key] for key in (
                    "package_sha256", "provider", "accession", "cik", "form",
                    "filed_date", "accepted_at", "report_period", "primary_document",
                    "manifest_schema_version",
                ))
                if existing_values != package_values:
                    raise ValueError("P11 source package identity drift")
            else:
                conn.execute(
                    """
                    INSERT INTO source_packages(
                        package_sha256, provider, accession, cik, form, filed_date,
                        accepted_at, report_period, primary_document,
                        manifest_schema_version, first_seen_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (*package_values, now),
                )

            for member in members:
                values = (
                    package_sha,
                    member.member_sha256,
                    member.relative_name,
                    member.role.value,
                    member.content_type,
                    len(member.body),
                    member.source_url,
                )
                prior = conn.execute(
                    """
                    SELECT package_sha256, member_sha256, relative_name, role,
                           content_type, byte_length, source_url
                    FROM package_members
                    WHERE package_sha256 = ? AND relative_name = ?
                    """,
                    (package_sha, member.relative_name),
                ).fetchone()
                if prior is not None and tuple(prior) != values:
                    raise ValueError("P11 source package member drift")
                if prior is None:
                    conn.execute(
                        """
                        INSERT INTO package_members(
                            package_sha256, member_sha256, relative_name, role,
                            content_type, byte_length, source_url
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        values,
                    )
            conn.commit()

    def register_sec_binding(
        self,
        package: object,
        *,
        company_id: str,
        fiscal_year: int,
        period: str,
        artifact_path: str | None = None,
        binding_status: str = "SOURCE_CONFIRMED",
    ) -> str:
        self.register_sec_package(package)
        manifest = package.manifest()
        package_sha = str(manifest["package_sha256"]).lower()
        accession = str(manifest["accession"])
        form = str(manifest["form"]).upper()
        amended = int(form.endswith("/A"))
        binding_id = hashlib.sha256(
            f"{package_sha}|{company_id}|{fiscal_year}|{period}|{amended}".encode()
        ).hexdigest()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO sec_filing_bindings(
                    binding_id, package_sha256, company_id, fiscal_year,
                    raw_fiscal_period, accession, form, amended,
                    binding_status, artifact_path, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(binding_id) DO UPDATE SET
                    binding_status = excluded.binding_status,
                    artifact_path = COALESCE(excluded.artifact_path, artifact_path)
                """,
                (
                    binding_id,
                    package_sha,
                    company_id,
                    int(fiscal_year),
                    period.upper(),
                    accession,
                    form,
                    amended,
                    binding_status,
                    artifact_path,
                    _utc_now(),
                ),
            )
            conn.commit()
        return binding_id

    def register_sec_parsed_data(
        self,
        *,
        parse_run_id: str,
        package_sha256: str,
        company_id: str,
        fiscal_year: int,
        period: str,
        parser_version: str,
        schema_version: str,
        validation_status: str,
        blocking_issue_count: int,
        artifact_path: str | None,
        compatibility_status: str | None = None,
    ) -> None:
        with self._connect() as conn:
            normalized_compatibility = (
                "INCOMPATIBLE"
                if compatibility_status is None
                else str(compatibility_status).upper()
            )
            conn.execute(
                """
                INSERT INTO sec_parsed_data(
                    parse_run_id, package_sha256, company_id, fiscal_year,
                    raw_fiscal_period, parser_version, schema_version,
                    validation_status, compatibility_status, blocking_issue_count,
                    artifact_path, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(parse_run_id) DO UPDATE SET
                    validation_status = excluded.validation_status,
                    compatibility_status = excluded.compatibility_status,
                    blocking_issue_count = excluded.blocking_issue_count,
                    artifact_path = excluded.artifact_path
                """,
                (
                    parse_run_id,
                    package_sha256.lower(),
                    company_id,
                    int(fiscal_year),
                    period.upper(),
                    parser_version,
                    schema_version,
                    validation_status,
                    normalized_compatibility,
                    int(blocking_issue_count),
                    artifact_path,
                    _utc_now(),
                ),
            )
            conn.commit()

    def list_sec_bindings(
        self,
        *,
        company_id: str,
        fiscal_year: int,
        period: str,
    ) -> tuple[sqlite3.Row, ...]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM sec_filing_bindings
                WHERE company_id = ? AND fiscal_year = ? AND raw_fiscal_period = ?
                ORDER BY amended ASC, accession ASC
                """,
                (company_id, int(fiscal_year), period.upper()),
            ).fetchall()
        return tuple(rows)

    def list_sec_parsed_data(
        self,
        *,
        company_id: str,
        fiscal_year: int,
        period: str,
    ) -> tuple[sqlite3.Row, ...]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM sec_parsed_data
                WHERE company_id = ? AND fiscal_year = ? AND raw_fiscal_period = ?
                ORDER BY validation_status ASC, package_sha256 ASC, parse_run_id ASC
                """,
                (company_id, int(fiscal_year), period.upper()),
            ).fetchall()
        return tuple(rows)

    def register_document(
        self,
        path: str | Path,
        source: SourceMetadata | None = None,
        expected_identity: FilingIdentity | None = None,
    ) -> RegisteredDocument:
        file_path = Path(path).expanduser().resolve()
        if not file_path.is_file():
            raise FileNotFoundError(file_path)

        before = file_path.stat()
        sha_before = _sha256_file(file_path)

        page_count: int | None = None
        if file_path.suffix.lower() == ".pdf":
            with pymupdf.open(file_path) as document:
                if document.needs_pass:
                    raise ValueError("password-protected PDF cannot be registered in P1")
                page_count = document.page_count

        after = file_path.stat()
        sha_after = _sha256_file(file_path)
        if (
            before.st_size != after.st_size
            or before.st_mtime_ns != after.st_mtime_ns
            or sha_before != sha_after
        ):
            raise RuntimeError("source file changed during registration")

        now = _utc_now()
        binding_status: BindingStatus | None = None

        with self._connect() as conn:
            conn.execute("BEGIN")
            conn.execute(
                """
                INSERT OR IGNORE INTO documents(
                    document_sha256, file_size, page_count, first_seen_at
                ) VALUES (?, ?, ?, ?)
                """,
                (sha_before, before.st_size, page_count, now),
            )
            existing_document = conn.execute(
                """
                SELECT file_size, page_count FROM documents
                WHERE document_sha256 = ?
                """,
                (sha_before,),
            ).fetchone()
            if existing_document is None:
                raise RuntimeError("document insert invariant failed")
            if int(existing_document["file_size"]) != before.st_size:
                raise RuntimeError("document SHA invariant violated by file size mismatch")

            conn.execute(
                """
                INSERT INTO document_locations(
                    path, document_sha256, mtime_ns, last_seen_at, exists_flag
                ) VALUES (?, ?, ?, ?, 1)
                ON CONFLICT(path) DO UPDATE SET
                    document_sha256 = excluded.document_sha256,
                    mtime_ns = excluded.mtime_ns,
                    last_seen_at = excluded.last_seen_at,
                    exists_flag = 1
                """,
                (str(file_path), sha_before, after.st_mtime_ns, now),
            )

            if source is not None:
                conn.execute(
                    """
                    INSERT INTO document_sources(
                        document_sha256, provider, source_id, source_url,
                        source_title, filing_date, report_date,
                        provider_company_id, acquired_at, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(document_sha256, provider, source_id) DO UPDATE SET
                        source_url = excluded.source_url,
                        source_title = excluded.source_title,
                        filing_date = COALESCE(excluded.filing_date, filing_date),
                        report_date = COALESCE(excluded.report_date, report_date),
                        provider_company_id = COALESCE(
                            excluded.provider_company_id, provider_company_id
                        ),
                        acquired_at = COALESCE(excluded.acquired_at, acquired_at)
                    """,
                    (
                        sha_before,
                        source.provider,
                        source.source_id,
                        source.source_url,
                        source.source_title,
                        source.filing_date,
                        source.report_date,
                        source.provider_company_id,
                        source.acquired_at,
                        now,
                    ),
                )

            if expected_identity is not None:
                different_slots = conn.execute(
                    """
                    SELECT binding_id, market, company_id, filing_type,
                           fiscal_year, raw_fiscal_period
                    FROM filing_bindings
                    WHERE document_sha256 = ? AND binding_status != ?
                    """,
                    (sha_before, BindingStatus.CONFLICT.value),
                ).fetchall()
                has_different_slot = any(
                    (
                        row["market"],
                        row["company_id"],
                        row["filing_type"],
                        int(row["fiscal_year"]),
                        row["raw_fiscal_period"],
                    )
                    != (
                        expected_identity.slot.market,
                        expected_identity.slot.company_id,
                        expected_identity.slot.filing_type,
                        expected_identity.slot.fiscal_year,
                        expected_identity.slot.raw_fiscal_period,
                    )
                    for row in different_slots
                )

                if has_different_slot:
                    conn.execute(
                        """
                        UPDATE filing_bindings
                        SET binding_status = ?
                        WHERE document_sha256 = ?
                        """,
                        (BindingStatus.CONFLICT.value, sha_before),
                    )
                    binding_status = BindingStatus.CONFLICT
                else:
                    binding_status = (
                        BindingStatus.SOURCE_CONFIRMED
                        if source is not None
                        else BindingStatus.DECLARED
                    )

                amended_db = (
                    None
                    if expected_identity.amended is None
                    else int(expected_identity.amended)
                )
                source_values = (
                    source.provider if source else None,
                    source.source_id if source else None,
                    source.source_url if source else None,
                    source.source_title if source else None,
                    source.filing_date if source else None,
                    source.report_date if source else None,
                    source.provider_company_id if source else None,
                    source.acquired_at if source else None,
                )
                bid = _binding_id(sha_before, expected_identity)
                conn.execute(
                    """
                    INSERT INTO filing_bindings(
                        binding_id, document_sha256, market, company_id,
                        filing_type, fiscal_year, raw_fiscal_period, amended,
                        binding_status, source_provider, source_id, source_url,
                        source_title, filing_date, report_date,
                        provider_company_id, acquired_at, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(binding_id) DO UPDATE SET
                        binding_status = excluded.binding_status,
                        source_provider = COALESCE(excluded.source_provider, source_provider),
                        source_id = COALESCE(excluded.source_id, source_id),
                        source_url = COALESCE(excluded.source_url, source_url),
                        source_title = COALESCE(excluded.source_title, source_title),
                        filing_date = COALESCE(excluded.filing_date, filing_date),
                        report_date = COALESCE(excluded.report_date, report_date),
                        provider_company_id = COALESCE(
                            excluded.provider_company_id, provider_company_id
                        ),
                        acquired_at = COALESCE(excluded.acquired_at, acquired_at)
                    """,
                    (
                        bid,
                        sha_before,
                        expected_identity.slot.market,
                        expected_identity.slot.company_id,
                        expected_identity.slot.filing_type,
                        expected_identity.slot.fiscal_year,
                        expected_identity.slot.raw_fiscal_period,
                        amended_db,
                        binding_status.value,
                        *source_values,
                        now,
                    ),
                )

            conn.commit()

        return RegisteredDocument(
            document_sha256=sha_before,
            path=file_path,
            file_size=before.st_size,
            mtime_ns=after.st_mtime_ns,
            page_count=page_count,
            identity=expected_identity,
            binding_status=binding_status,
        )

    def register_parsed_data(self, record: ParsedDataRecord) -> None:
        now = _utc_now()
        values = (
            record.parse_run_id,
            record.slot.market,
            record.slot.company_id,
            record.slot.filing_type,
            record.slot.fiscal_year,
            record.slot.raw_fiscal_period,
            record.document_sha256,
            record.parser_version,
            record.schema_version,
            record.validation_status.value,
            record.blocking_issue_count,
            record.compatibility_status.value,
            record.artifact_path,
        )
        with self._connect() as conn:
            existing = conn.execute(
                "SELECT * FROM parsed_data WHERE parse_run_id = ?",
                (record.parse_run_id,),
            ).fetchone()
            if existing is not None:
                existing_values = (
                    existing["parse_run_id"],
                    existing["market"],
                    existing["company_id"],
                    existing["filing_type"],
                    int(existing["fiscal_year"]),
                    existing["raw_fiscal_period"],
                    existing["document_sha256"],
                    existing["parser_version"],
                    existing["schema_version"],
                    existing["validation_status"],
                    int(existing["blocking_issue_count"]),
                    existing["compatibility_status"],
                    existing["artifact_path"],
                )
                expected = (
                    record.parse_run_id,
                    record.slot.market,
                    record.slot.company_id,
                    record.slot.filing_type,
                    record.slot.fiscal_year,
                    record.slot.raw_fiscal_period,
                    record.document_sha256,
                    record.parser_version,
                    record.schema_version,
                    record.validation_status.value,
                    record.blocking_issue_count,
                    record.compatibility_status.value,
                    record.artifact_path,
                )
                if existing_values != expected:
                    raise ValueError(
                        f"parse_run_id already exists with different content: "
                        f"{record.parse_run_id}"
                    )
                return

            conn.execute(
                """
                INSERT INTO parsed_data(
                    parse_run_id, market, company_id, filing_type, fiscal_year,
                    raw_fiscal_period, document_sha256, parser_version,
                    schema_version, validation_status, blocking_issue_count,
                    compatibility_status, artifact_path, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (*values, now),
            )
            conn.commit()

    def list_parsed_data(self, slot: FilingSlotKey) -> tuple[ParsedDataRecord, ...]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM parsed_data
                WHERE market = ? AND company_id = ? AND filing_type = ?
                  AND fiscal_year = ? AND raw_fiscal_period = ?
                ORDER BY document_sha256 ASC, parse_run_id ASC
                """,
                (
                    slot.market,
                    slot.company_id,
                    slot.filing_type,
                    slot.fiscal_year,
                    slot.raw_fiscal_period,
                ),
            ).fetchall()
        return tuple(
            ParsedDataRecord(
                parse_run_id=row["parse_run_id"],
                slot=slot,
                document_sha256=row["document_sha256"],
                parser_version=row["parser_version"],
                schema_version=row["schema_version"],
                validation_status=ValidationStatus(row["validation_status"]),
                blocking_issue_count=int(row["blocking_issue_count"]),
                compatibility_status=CompatibilityStatus(
                    row["compatibility_status"]
                ),
                artifact_path=row["artifact_path"],
            )
            for row in rows
        )

    def resolve_local_document(self, slot: FilingSlotKey) -> LocalDocumentState:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT b.document_sha256, b.binding_status, l.path,
                       l.exists_flag
                FROM filing_bindings AS b
                LEFT JOIN document_locations AS l
                  ON l.document_sha256 = b.document_sha256
                WHERE b.market = ? AND b.company_id = ? AND b.filing_type = ?
                  AND b.fiscal_year = ? AND b.raw_fiscal_period = ?
                ORDER BY b.document_sha256 ASC, l.path ASC
                """,
                (
                    slot.market,
                    slot.company_id,
                    slot.filing_type,
                    slot.fiscal_year,
                    slot.raw_fiscal_period,
                ),
            ).fetchall()

            live: list[tuple[str, BindingStatus, str]] = []
            drifted: list[tuple[str, BindingStatus, str]] = []
            for row in rows:
                if not row["path"] or not int(row["exists_flag"] or 0):
                    continue
                path = Path(row["path"])
                if not path.is_file():
                    conn.execute(
                        """
                        UPDATE document_locations
                        SET exists_flag = 0, last_seen_at = ?
                        WHERE path = ?
                        """,
                        (_utc_now(), str(path)),
                    )
                    continue

                registered_sha = str(row["document_sha256"])
                current_sha = _sha256_file(path)
                item = (
                    registered_sha,
                    BindingStatus(row["binding_status"]),
                    str(path),
                )
                if current_sha != registered_sha:
                    drifted.append(item)
                    continue
                live.append(item)
            conn.commit()

        if not live:
            if drifted:
                statuses = tuple(
                    sorted({item[1] for item in drifted}, key=lambda x: x.value)
                )
                return LocalDocumentState(
                    status=LocalDocumentStatus.DRIFTED,
                    slot=slot,
                    location_count=0,
                    distinct_sha_count=0,
                    drifted_location_count=len({item[2] for item in drifted}),
                    binding_statuses=statuses,
                )
            return LocalDocumentState(
                status=LocalDocumentStatus.NONE,
                slot=slot,
            )

        statuses = tuple(sorted({item[1] for item in live}, key=lambda x: x.value))
        drifted_count = len({item[2] for item in drifted})
        conflict_live = [item for item in live if item[1] == BindingStatus.CONFLICT]
        if conflict_live:
            return LocalDocumentState(
                status=LocalDocumentStatus.CONFLICT,
                slot=slot,
                location_count=len({item[2] for item in live}),
                distinct_sha_count=len({item[0] for item in live}),
                drifted_location_count=drifted_count,
                binding_statuses=statuses,
            )

        by_sha: dict[str, list[str]] = {}
        for sha, _, path in live:
            by_sha.setdefault(sha, []).append(path)

        if len(by_sha) > 1:
            return LocalDocumentState(
                status=LocalDocumentStatus.AMBIGUOUS,
                slot=slot,
                location_count=len({item[2] for item in live}),
                distinct_sha_count=len(by_sha),
                drifted_location_count=drifted_count,
                binding_statuses=statuses,
            )

        sha = next(iter(by_sha))
        paths = sorted(set(by_sha[sha]))
        return LocalDocumentState(
            status=LocalDocumentStatus.RESOLVED,
            slot=slot,
            document_sha256=sha,
            canonical_path=Path(paths[0]),
            location_count=len(paths),
            distinct_sha_count=1,
            drifted_location_count=drifted_count,
            binding_statuses=statuses,
        )

    def count_documents(self) -> int:
        with self._connect() as conn:
            return int(conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0])

    def count_locations(self) -> int:
        with self._connect() as conn:
            return int(
                conn.execute("SELECT COUNT(*) FROM document_locations").fetchone()[0]
            )

    def count_bindings(self) -> int:
        with self._connect() as conn:
            return int(
                conn.execute("SELECT COUNT(*) FROM filing_bindings").fetchone()[0]
            )

    def count_sources(self) -> int:
        with self._connect() as conn:
            return int(
                conn.execute("SELECT COUNT(*) FROM document_sources").fetchone()[0]
            )

    def list_document_sources(
        self, document_sha256: str
    ) -> tuple[SourceMetadata, ...]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT provider, source_id, source_url, source_title,
                       filing_date, report_date, provider_company_id, acquired_at
                FROM document_sources
                WHERE document_sha256 = ?
                ORDER BY provider ASC, source_id ASC
                """,
                (document_sha256,),
            ).fetchall()
        return tuple(
            SourceMetadata(
                provider=row["provider"],
                source_id=row["source_id"],
                source_url=row["source_url"],
                source_title=row["source_title"],
                filing_date=row["filing_date"],
                report_date=row["report_date"],
                provider_company_id=row["provider_company_id"],
                acquired_at=row["acquired_at"],
            )
            for row in rows
        )

    def location_sha(self, path: str | Path) -> str | None:
        resolved = str(Path(path).expanduser().resolve())
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT document_sha256 FROM document_locations WHERE path = ?
                """,
                (resolved,),
            ).fetchone()
        return None if row is None else str(row["document_sha256"])
