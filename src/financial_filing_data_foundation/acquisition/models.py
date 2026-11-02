from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from pathlib import Path
from typing import Any

from financial_filing_data_foundation.identity import CompanyRef, FilingSlotKey


PROTOCOL_VERSION = "ffdf-dayu-acquisition-v1"
DAYU_REPOSITORY = "https://github.com/noho/dayu-agent"
DAYU_PINNED_COMMIT = "2115c86d5a9027bb51cbbc8a4d0175080732e4e6"
DAYU_PACKAGE_VERSION = "0.1.4"


class AcquisitionStatus(StrEnum):
    REUSED_LOCAL = "REUSED_LOCAL"
    DOWNLOADED = "DOWNLOADED"
    NOT_FOUND = "NOT_FOUND"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    BLOCKED = "BLOCKED"


class AcquisitionReason(StrEnum):
    LOCAL_RAW_ALREADY_AVAILABLE = "LOCAL_RAW_ALREADY_AVAILABLE"
    NO_CANDIDATE = "NO_CANDIDATE"
    ACQUISITION_CANDIDATE_AMBIGUOUS = "ACQUISITION_CANDIDATE_AMBIGUOUS"
    ACQUISITION_CANDIDATE_METADATA_CONFLICT = (
        "ACQUISITION_CANDIDATE_METADATA_CONFLICT"
    )
    SOURCE_HOST_NOT_ALLOWED = "SOURCE_HOST_NOT_ALLOWED"
    DAYU_RUNTIME_UNAVAILABLE = "DAYU_RUNTIME_UNAVAILABLE"
    DAYU_SOURCE_COMMIT_MISMATCH = "DAYU_SOURCE_COMMIT_MISMATCH"
    DAYU_WORKTREE_DIRTY = "DAYU_WORKTREE_DIRTY"
    RUNNER_PROTOCOL_INVALID = "RUNNER_PROTOCOL_INVALID"
    RUNNER_TIMEOUT = "RUNNER_TIMEOUT"
    RUNNER_CWD_UNSAFE = "RUNNER_CWD_UNSAFE"
    DISCOVERY_FAILED = "DISCOVERY_FAILED"
    COMPANY_NOT_FOUND = "COMPANY_NOT_FOUND"
    DOWNLOAD_FAILED = "DOWNLOAD_FAILED"
    STAGING_WRITE_FAILED = "STAGING_WRITE_FAILED"
    PDF_VALIDATION_FAILED = "PDF_VALIDATION_FAILED"
    SHA_MISMATCH = "SHA_MISMATCH"
    RAW_STORE_FAILED = "RAW_STORE_FAILED"
    RAW_STORE_CORRUPTION = "RAW_STORE_CORRUPTION"
    REGISTRY_FAILED = "REGISTRY_FAILED"
    LOCAL_STATE_AMBIGUOUS = "LOCAL_STATE_AMBIGUOUS"
    LOCAL_STATE_CONFLICT = "LOCAL_STATE_CONFLICT"
    LOCAL_CONTENT_DRIFT = "LOCAL_CONTENT_DRIFT"
    ACQUISITION_COMPLETE = "ACQUISITION_COMPLETE"


class AcquisitionError(RuntimeError):
    def __init__(
        self,
        reason_code: AcquisitionReason | str,
        message: str,
        *,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.reason_code = (
            reason_code.value
            if isinstance(reason_code, AcquisitionReason)
            else str(reason_code)
        )
        self.retryable = retryable


@dataclass(frozen=True, slots=True)
class AcquisitionRequest:
    company: CompanyRef
    slot: FilingSlotKey
    window_start: str
    window_end: str

    def __post_init__(self) -> None:
        start = date.fromisoformat(self.window_start)
        end = date.fromisoformat(self.window_end)
        if start > end:
            raise ValueError("window_start must be <= window_end")
        if self.company.market != self.slot.market:
            raise ValueError("company.market must equal slot.market")
        if self.company.company_id != self.slot.company_id:
            raise ValueError("company.company_id must equal slot.company_id")
        if self.slot.market not in {"CN", "HK"}:
            raise ValueError(f"unsupported P2 market: {self.slot.market}")


@dataclass(frozen=True, slots=True)
class ProviderCompanyProfile:
    provider: str
    company_id: str
    company_name: str
    ticker: str


@dataclass(frozen=True, slots=True)
class AcquisitionCandidate:
    provider: str
    provider_company_id: str
    provider_company_name: str
    ticker: str
    source_id: str
    source_url: str
    source_title: str
    language: str
    filing_date: str
    fiscal_year: int
    fiscal_period: str
    amended: bool
    remote_content_length: int | None = None
    etag: str | None = None
    last_modified: str | None = None

    def __post_init__(self) -> None:
        if not self.provider.strip():
            raise ValueError("provider must not be empty")
        if not self.source_id.strip():
            raise ValueError("source_id must not be empty")
        if not self.source_url.strip():
            raise ValueError("source_url must not be empty")
        if not self.ticker.strip():
            raise ValueError("ticker must not be empty")
        if self.fiscal_period.upper() not in {"Q1", "H1", "Q3", "FY"}:
            raise ValueError(f"unsupported P2 fiscal period: {self.fiscal_period}")
        date.fromisoformat(self.filing_date)
        object.__setattr__(self, "provider", self.provider.strip())
        object.__setattr__(self, "ticker", self.ticker.strip())
        object.__setattr__(self, "fiscal_period", self.fiscal_period.upper())


@dataclass(frozen=True, slots=True)
class DiscoveryResult:
    profile: ProviderCompanyProfile
    candidates: tuple[AcquisitionCandidate, ...]


@dataclass(frozen=True, slots=True)
class RunnerDownloadedAsset:
    candidate: AcquisitionCandidate
    staging_path: Path
    sha256: str
    content_length: int
    downloaded_at: str
    request_id: str
    runner_version: str


@dataclass(frozen=True, slots=True)
class RawStoredDocument:
    document_sha256: str
    path: Path
    file_size: int
    reused_existing: bool


@dataclass(frozen=True, slots=True)
class AcquisitionReceiptRef:
    receipt_id: str
    path: Path


@dataclass(frozen=True, slots=True)
class AcquisitionResult:
    status: AcquisitionStatus
    reason_code: str
    slot: FilingSlotKey
    document_sha256: str | None = None
    raw_path: Path | None = None
    receipt_path: Path | None = None
    source_id: str | None = None
    provider: str | None = None


@dataclass(frozen=True, slots=True)
class DayuRuntimeDescriptor:
    dayu_repository: str
    dayu_commit: str
    dayu_package_version: str
    dayu_source_path: Path
    dayu_python_executable: Path
    dayu_python_version: str | None = None
    dayu_python_arch: str | None = None
    runtime_created_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "dayu_repository": self.dayu_repository,
            "dayu_commit": self.dayu_commit,
            "dayu_package_version": self.dayu_package_version,
            "dayu_source_path": str(self.dayu_source_path),
            "dayu_python_executable": str(self.dayu_python_executable),
            "dayu_python_version": self.dayu_python_version,
            "dayu_python_arch": self.dayu_python_arch,
            "runtime_created_at": self.runtime_created_at,
        }
