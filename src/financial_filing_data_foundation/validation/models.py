from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from financial_filing_data_foundation.registry.models import (
    CompatibilityStatus,
    ValidationStatus,
)

SCHEMA_VERSION = "p7-validation-v1"
POLICY_VERSION = "p7-quality-policy-v1"


class ValidationError(RuntimeError):
    def __init__(self, reason_code: str, message: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


@dataclass(frozen=True, slots=True)
class ValidationArtifact:
    artifact_dir: Path
    document_sha256: str
    validation_status: ValidationStatus
    compatibility_status: CompatibilityStatus
    reuse_eligible: bool
    blocking_issue_count: int
    failure_issue_count: int
    review_issue_count: int
    warning_issue_count: int
    issue_count: int
    issues_path: Path
    report_path: Path
    metrics: dict[str, Any]
    timings_ms: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "policy_version": POLICY_VERSION,
            "document_sha256": self.document_sha256,
            "validation_status": self.validation_status.value,
            "compatibility_status": self.compatibility_status.value,
            "reuse_eligible": self.reuse_eligible,
            "blocking_issue_count": self.blocking_issue_count,
            "failure_issue_count": self.failure_issue_count,
            "review_issue_count": self.review_issue_count,
            "warning_issue_count": self.warning_issue_count,
            "issue_count": self.issue_count,
            "artifact_dir": str(self.artifact_dir),
            "issues_path": str(self.issues_path),
            "report_path": str(self.report_path),
            "metrics": self.metrics,
            "timings_ms": self.timings_ms,
        }
