from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Mapping

from financial_filing_data_foundation.registry import ValidationStatus

REVIEW_SCHEMA_VERSION = "p9-review-overlay-v1"
TASK_SCHEMA_VERSION = "p9-review-task-v1"
RESOLUTION_SCHEMA_VERSION = "p9-review-resolution-v1"
RESOLVED_FACT_SCHEMA_VERSION = "p9-resolved-fact-v1"
RESOLUTION_REPORT_SCHEMA_VERSION = "p9-resolution-report-v1"
RESOLVED_VIEW_SCHEMA_VERSION = "p9-resolved-view-v1"
SNAPSHOT_MANIFEST_SCHEMA_VERSION = "p9-snapshot-manifest-v1"
POLICY_VERSION = "p9-review-policy-v1"
REVIEW_POLICY_VERSION = POLICY_VERSION
P9_VERSION = REVIEW_SCHEMA_VERSION


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def pretty_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class ReviewError(RuntimeError):
    def __init__(self, reason_code: str, message: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


class Reviewability(StrEnum):
    SUPPORTED = "SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"


class ReviewerType(StrEnum):
    CODEX = "CODEX"
    HUMAN = "HUMAN"


class ResolutionAction(StrEnum):
    SET_PERIOD = "SET_PERIOD"
    SET_UNIT = "SET_UNIT"
    SET_SCOPE = "SET_SCOPE"
    CLASSIFY_TABLE_STATEMENT = "CLASSIFY_TABLE_STATEMENT"
    ATTEST_ISSUE_RESOLVED = "ATTEST_ISSUE_RESOLVED"


class TargetType(StrEnum):
    FACT_FIELD = "FACT_FIELD"
    TABLE_COLUMN_FIELD = "TABLE_COLUMN_FIELD"
    TABLE_FIELD = "TABLE_FIELD"
    TABLE_STATEMENT_CLASS = "TABLE_STATEMENT_CLASS"
    ISSUE = "ISSUE"


class ResolvedIssueState(StrEnum):
    RESOLVED = "RESOLVED"
    UNRESOLVED = "UNRESOLVED"
    UNSUPPORTED = "UNSUPPORTED"
    CONFLICT = "CONFLICT"


@dataclass(frozen=True, slots=True)
class ReviewOverlayArtifact:
    review_dir: Path
    document_sha256: str
    task_count: int
    supported_task_count: int
    unsupported_task_count: int
    manifest_path: Path
    queue_path: Path

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": REVIEW_SCHEMA_VERSION,
            "policy_version": POLICY_VERSION,
            "review_dir": str(self.review_dir),
            "document_sha256": self.document_sha256,
            "task_count": self.task_count,
            "supported_task_count": self.supported_task_count,
            "unsupported_task_count": self.unsupported_task_count,
            "manifest_path": str(self.manifest_path),
            "queue_path": str(self.queue_path),
        }


@dataclass(frozen=True, slots=True)
class ReviewTask:
    review_task_id: str
    document_sha256: str
    base_validation_report_sha256: str
    issue_id: str
    reason_code: str
    message: str
    observed: dict[str, Any]
    reviewability: Reviewability
    supported_actions: tuple[str, ...]
    required_evidence_types: tuple[str, ...]
    scope: str = ""
    page_no: int | None = None
    table_id: str | None = None
    raw_fact_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "ReviewTask":
        try:
            reviewability = Reviewability(str(raw.get("reviewability") or ""))
        except ValueError as exc:
            raise ReviewError(
                "P9_ARTIFACT_INCOMPLETE_OR_CORRUPT",
                "invalid reviewability",
            ) from exc
        return cls(
            review_task_id=str(raw.get("review_task_id") or ""),
            document_sha256=str(raw.get("document_sha256") or ""),
            base_validation_report_sha256=str(
                raw.get("base_validation_report_sha256") or ""
            ),
            issue_id=str(raw.get("issue_id") or ""),
            reason_code=str(raw.get("reason_code") or ""),
            message=str(raw.get("message") or ""),
            observed=dict(raw.get("observed") or {}),
            reviewability=reviewability,
            supported_actions=tuple(str(x) for x in raw.get("supported_actions") or ()),
            required_evidence_types=tuple(
                str(x) for x in raw.get("required_evidence_types") or ()
            ),
            scope=str(raw.get("scope") or ""),
            page_no=(
                None
                if raw.get("page_no") is None
                else int(raw.get("page_no"))
            ),
            table_id=(
                None
                if raw.get("table_id") in (None, "")
                else str(raw.get("table_id"))
            ),
            raw_fact_ids=tuple(str(x) for x in raw.get("raw_fact_ids") or ()),
            evidence_ids=tuple(str(x) for x in raw.get("evidence_ids") or ()),
        )


@dataclass(frozen=True, slots=True)
class ResolutionSubmission:
    review_task_id: str
    action: ResolutionAction
    target: dict[str, Any]
    value: str | None
    evidence_refs: tuple[dict[str, Any], ...]
    reviewer_type: ReviewerType
    reviewer_id: str
    reviewed_at: str
    justification: str
    supersedes_resolution_id: str | None = None
    supporting_resolution_ids: tuple[str, ...] = ()
    evidence_pages: tuple[int, ...] | None = None
    expected_observed_count: int | None = None

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "ResolutionSubmission":
        if not isinstance(raw, Mapping):
            raise ReviewError(
                "P9_INVALID_RESOLUTION",
                "resolution submission must be a JSON object",
            )
        target = raw.get("target")
        if not isinstance(target, Mapping):
            raise ReviewError("P9_INVALID_RESOLUTION", "resolution target must be an object")
        refs = raw.get("evidence_refs", [])
        supports = raw.get("supporting_resolution_ids", [])
        if not isinstance(refs, list) or not all(isinstance(x, Mapping) for x in refs):
            raise ReviewError("P9_INVALID_RESOLUTION", "evidence_refs must be a list of objects")
        if not isinstance(supports, list):
            raise ReviewError("P9_INVALID_RESOLUTION", "supporting_resolution_ids must be a list")
        pages_raw = raw.get("evidence_pages")
        if pages_raw is None:
            pages = None
        elif isinstance(pages_raw, list) and all(
            isinstance(x, int) and not isinstance(x, bool) for x in pages_raw
        ):
            pages = tuple(int(x) for x in pages_raw)
        else:
            raise ReviewError("P9_INVALID_RESOLUTION", "evidence_pages must be a list of integers")
        value = raw.get("value")
        if value is not None and not isinstance(value, str):
            raise ReviewError("P9_INVALID_RESOLUTION", "resolution value must be string or null")
        expected = raw.get("expected_observed_count")
        if expected is not None and (
            isinstance(expected, bool) or not isinstance(expected, int) or expected < 0
        ):
            raise ReviewError(
                "P9_INVALID_RESOLUTION",
                "expected_observed_count must be a non-negative integer",
            )
        try:
            action = ResolutionAction(str(raw.get("action") or ""))
            reviewer_type = ReviewerType(str(raw.get("reviewer_type") or ""))
        except ValueError as exc:
            raise ReviewError("P9_INVALID_RESOLUTION", "invalid enum value") from exc
        return cls(
            review_task_id=str(raw.get("review_task_id") or ""),
            action=action,
            target=dict(target),
            value=value,
            evidence_refs=tuple(dict(x) for x in refs),
            reviewer_type=reviewer_type,
            reviewer_id=str(raw.get("reviewer_id") or ""),
            reviewed_at=str(raw.get("reviewed_at") or ""),
            justification=str(raw.get("justification") or ""),
            supersedes_resolution_id=(
                None
                if raw.get("supersedes_resolution_id") in (None, "")
                else str(raw.get("supersedes_resolution_id"))
            ),
            supporting_resolution_ids=tuple(str(x) for x in supports),
            evidence_pages=pages,
            expected_observed_count=expected,
        )


@dataclass(frozen=True, slots=True)
class ReviewResolution:
    resolution_id: str
    document_sha256: str
    base_validation_report_sha256: str
    review_task_id: str
    issue_id: str
    reason_code: str
    action: ResolutionAction
    target: dict[str, Any]
    value: str | None
    evidence_refs: tuple[dict[str, Any], ...]
    evidence_pages: tuple[int, ...]
    before: dict[str, Any]
    after: dict[str, Any]
    reviewer_type: ReviewerType
    reviewer_id: str
    reviewed_at: str
    justification: str
    base_active_resolution_ids: tuple[str, ...]
    base_overlay_set_hash_before: str
    supersedes_resolution_id: str | None = None
    supporting_resolution_ids: tuple[str, ...] = ()
    expected_observed_count: int | None = None

    def to_dict(self, *, include_id: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema_version": RESOLUTION_SCHEMA_VERSION,
            "document_sha256": self.document_sha256,
            "base_validation_report_sha256": self.base_validation_report_sha256,
            "review_task_id": self.review_task_id,
            "issue_id": self.issue_id,
            "reason_code": self.reason_code,
            "action": self.action.value,
            "target": dict(self.target),
            "value": self.value,
            "evidence_refs": [dict(x) for x in self.evidence_refs],
            "evidence_pages": list(self.evidence_pages),
            "before": dict(self.before),
            "after": dict(self.after),
            "reviewer": {
                "reviewer_type": self.reviewer_type.value,
                "reviewer_id": self.reviewer_id,
            },
            "reviewed_at": self.reviewed_at,
            "justification": self.justification,
            "base_active_resolution_ids": list(self.base_active_resolution_ids),
            "base_overlay_set_hash_before": self.base_overlay_set_hash_before,
            "supersedes_resolution_id": self.supersedes_resolution_id,
            "supporting_resolution_ids": list(self.supporting_resolution_ids),
            "expected_observed_count": self.expected_observed_count,
        }
        if include_id:
            payload["resolution_id"] = self.resolution_id
        return payload

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "ReviewResolution":
        if raw.get("schema_version") != RESOLUTION_SCHEMA_VERSION:
            raise ReviewError("P9_RESOLUTION_STORE_CORRUPT", "resolution schema mismatch")
        reviewer = raw.get("reviewer")
        if not isinstance(reviewer, Mapping):
            raise ReviewError("P9_RESOLUTION_STORE_CORRUPT", "reviewer object missing")
        try:
            action = ResolutionAction(str(raw.get("action") or ""))
            reviewer_type = ReviewerType(str(reviewer.get("reviewer_type") or ""))
        except ValueError as exc:
            raise ReviewError("P9_RESOLUTION_STORE_CORRUPT", "invalid resolution enum") from exc
        refs = raw.get("evidence_refs")
        pages = raw.get("evidence_pages")
        active_ids = raw.get("base_active_resolution_ids")
        supports = raw.get("supporting_resolution_ids")
        if not isinstance(refs, list) or not all(isinstance(x, Mapping) for x in refs):
            raise ReviewError("P9_RESOLUTION_STORE_CORRUPT", "evidence_refs invalid")
        if not isinstance(pages, list):
            raise ReviewError("P9_RESOLUTION_STORE_CORRUPT", "evidence_pages invalid")
        if not isinstance(active_ids, list) or not isinstance(supports, list):
            raise ReviewError("P9_RESOLUTION_STORE_CORRUPT", "resolution dependency lists invalid")
        target = raw.get("target")
        before = raw.get("before")
        after = raw.get("after")
        if not isinstance(target, Mapping) or not isinstance(before, Mapping) or not isinstance(after, Mapping):
            raise ReviewError("P9_RESOLUTION_STORE_CORRUPT", "resolution object fields invalid")
        return cls(
            resolution_id=str(raw.get("resolution_id") or ""),
            document_sha256=str(raw.get("document_sha256") or ""),
            base_validation_report_sha256=str(
                raw.get("base_validation_report_sha256") or ""
            ),
            review_task_id=str(raw.get("review_task_id") or ""),
            issue_id=str(raw.get("issue_id") or ""),
            reason_code=str(raw.get("reason_code") or ""),
            action=action,
            target=dict(target),
            value=(None if raw.get("value") is None else str(raw.get("value"))),
            evidence_refs=tuple(dict(x) for x in refs),
            evidence_pages=tuple(int(x) for x in pages),
            before=dict(before),
            after=dict(after),
            reviewer_type=reviewer_type,
            reviewer_id=str(reviewer.get("reviewer_id") or ""),
            reviewed_at=str(raw.get("reviewed_at") or ""),
            justification=str(raw.get("justification") or ""),
            base_active_resolution_ids=tuple(str(x) for x in active_ids),
            base_overlay_set_hash_before=str(raw.get("base_overlay_set_hash_before") or ""),
            supersedes_resolution_id=(
                None
                if raw.get("supersedes_resolution_id") in (None, "")
                else str(raw.get("supersedes_resolution_id"))
            ),
            supporting_resolution_ids=tuple(str(x) for x in supports),
            expected_observed_count=(
                None
                if raw.get("expected_observed_count") is None
                else int(raw.get("expected_observed_count"))
            ),
        )


@dataclass(frozen=True, slots=True)
class ResolvedSnapshot:
    snapshot_dir: Path
    document_sha256: str
    overlay_set_hash: str
    resolved_facts_path: Path
    resolved_issues_path: Path
    report_path: Path
    manifest_path: Path
    report: dict[str, Any]

    @property
    def resolved_validation_status(self) -> ValidationStatus:
        return ValidationStatus(str(self.report["resolved_validation_status"]))

    @property
    def resolved_reuse_eligible(self) -> bool:
        return bool(self.report.get("resolved_reuse_eligible"))

    @property
    def fact_count(self) -> int:
        metrics = self.report.get("effective_metrics") or {}
        return int(metrics.get("fact_count") or 0)

    @property
    def active_resolution_count(self) -> int:
        return int(self.report.get("active_resolution_count") or 0)

    @property
    def facts_path(self) -> Path:
        return self.resolved_facts_path

    @property
    def issues_path(self) -> Path:
        return self.resolved_issues_path

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": RESOLUTION_REPORT_SCHEMA_VERSION,
            "policy_version": REVIEW_POLICY_VERSION,
            "snapshot_dir": str(self.snapshot_dir),
            "document_sha256": self.document_sha256,
            "overlay_set_hash": self.overlay_set_hash,
            "resolved_validation_status": self.resolved_validation_status.value,
            "resolved_reuse_eligible": self.resolved_reuse_eligible,
            "fact_count": self.fact_count,
            "active_resolution_count": self.active_resolution_count,
            "facts_path": str(self.resolved_facts_path),
            "issues_path": str(self.resolved_issues_path),
            "report_path": str(self.report_path),
            "manifest_path": str(self.manifest_path),
        }
