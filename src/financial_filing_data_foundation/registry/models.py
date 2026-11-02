from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from financial_filing_data_foundation.identity import FilingIdentity, FilingSlotKey


class BindingStatus(StrEnum):
    DECLARED = "DECLARED"
    SOURCE_CONFIRMED = "SOURCE_CONFIRMED"
    CONFLICT = "CONFLICT"


class ValidationStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    BLOCKED = "BLOCKED"


class CompatibilityStatus(StrEnum):
    COMPATIBLE = "COMPATIBLE"
    INCOMPATIBLE = "INCOMPATIBLE"
    UNKNOWN = "UNKNOWN"


class LocalDocumentStatus(StrEnum):
    NONE = "NONE"
    RESOLVED = "RESOLVED"
    AMBIGUOUS = "AMBIGUOUS"
    CONFLICT = "CONFLICT"


@dataclass(frozen=True, slots=True)
class RegisteredDocument:
    document_sha256: str
    path: Path
    file_size: int
    mtime_ns: int
    page_count: int | None
    identity: FilingIdentity | None
    binding_status: BindingStatus | None


@dataclass(frozen=True, slots=True)
class ParsedDataRecord:
    parse_run_id: str
    slot: FilingSlotKey
    document_sha256: str
    parser_version: str
    schema_version: str
    validation_status: ValidationStatus
    blocking_issue_count: int
    compatibility_status: CompatibilityStatus
    artifact_path: str | None = None

    def __post_init__(self) -> None:
        if self.blocking_issue_count < 0:
            raise ValueError("blocking_issue_count must be >= 0")


@dataclass(frozen=True, slots=True)
class LocalDocumentState:
    status: LocalDocumentStatus
    slot: FilingSlotKey
    document_sha256: str | None = None
    canonical_path: Path | None = None
    location_count: int = 0
    distinct_sha_count: int = 0
    binding_statuses: tuple[BindingStatus, ...] = ()
