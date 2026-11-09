from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import P11Reason, SecError
from .parser import SEC_ARTIFACT_SCHEMA, SecParseResult, VIRTUAL_HTML_NORMALIZER_VERSION


SEC_VALIDATION_SCHEMA = "p11-sec-validation-v1"


@dataclass(frozen=True, slots=True)
class SecValidationResult:
    artifact_dir: Path
    package_sha256: str
    validation_status: str
    compatibility_status: str
    reuse_eligible: bool
    blocking_issue_count: int
    failure_issue_count: int
    review_issue_count: int
    warning_issue_count: int
    issue_count: int
    issues: tuple[dict[str, Any], ...]
    report_path: Path
    issues_path: Path

    @property
    def document_sha256(self) -> str:
        return self.package_sha256

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SEC_VALIDATION_SCHEMA,
            "package_sha256": self.package_sha256,
            "document_sha256": self.package_sha256,
            "validation_status": self.validation_status,
            "compatibility_status": self.compatibility_status,
            "reuse_eligible": self.reuse_eligible,
            "blocking_issue_count": self.blocking_issue_count,
            "failure_issue_count": self.failure_issue_count,
            "review_issue_count": self.review_issue_count,
            "warning_issue_count": self.warning_issue_count,
            "issue_count": self.issue_count,
            "report_file": "validation.json",
            "issues_file": "issues.jsonl",
        }


def _issue(code: str, severity: str, message: str, **extra: Any) -> dict[str, Any]:
    return {"code": code, "severity": severity, "message": message, **extra}


def _write(result: SecValidationResult) -> None:
    result.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.report_path.write_text(json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    with result.issues_path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in result.issues:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")


def _status(issues: list[dict[str, Any]]) -> tuple[str, int, int, int, int]:
    blocking_codes = {
        P11Reason.P11_PRIMARY_DOCUMENT_MISSING.value,
        P11Reason.P11_HTML_PARSE_FAILED.value,
        P11Reason.P11_MEMBER_HASH_MISMATCH.value,
        P11Reason.P11_SOURCE_DRIFT.value,
        P11Reason.P11_EVIDENCE_LOCATOR_INVALID.value,
        "P11_ARTIFACT_INCOMPLETE_OR_CORRUPT",
    }
    blocking = sum(1 for row in issues if str(row.get("code")) in blocking_codes or str(row.get("severity", "")).upper() == "BLOCKING")
    failures = sum(1 for row in issues if str(row.get("severity", "")).upper() in {"FAILURE", "FAIL"})
    review = sum(1 for row in issues if str(row.get("severity", "")).upper() in {"REVIEW", "REVIEW_REQUIRED"})
    warning = sum(1 for row in issues if str(row.get("severity", "")).upper() in {"WARNING", "WARN"})
    if blocking:
        status = "BLOCKED"
    elif failures:
        status = "FAIL"
    elif review:
        status = "REVIEW_REQUIRED"
    else:
        status = "PASS"
    return status, blocking, failures, review, warning


def validate_sec_artifacts(
    parsed: SecParseResult,
    validation_root: str | Path,
    *,
    amendment_conflict: bool = False,
) -> SecValidationResult:
    issues = [dict(row) for row in parsed.issues]
    if amendment_conflict:
        issues.append(_issue(P11Reason.P11_AMENDED_VARIANT_PRESENT.value, "REVIEW", "original and amended SEC variants are both present"))

    expected_pages = list(range(1, len(parsed.pages) + 1))
    actual_pages = [int(row.get("page_no", -1)) for row in parsed.pages]
    if actual_pages != expected_pages:
        issues.append(_issue("P11_ARTIFACT_INCOMPLETE_OR_CORRUPT", "BLOCKING", "virtual page sequence is not contiguous"))
    fact_ids = {str(row.get("raw_fact_id", "")) for row in parsed.facts}
    evidence_ids = {str(row.get("evidence_id", "")) for row in parsed.evidence}
    for fact in parsed.facts:
        if not fact.get("raw_fact_id") or not fact.get("evidence_id") or str(fact.get("evidence_id")) not in evidence_ids:
            issues.append(_issue("P11_ARTIFACT_INCOMPLETE_OR_CORRUPT", "BLOCKING", "raw fact does not resolve to evidence"))
    if len(fact_ids) != len(parsed.facts) or len(evidence_ids) != len(parsed.evidence):
        issues.append(_issue("P11_ARTIFACT_INCOMPLETE_OR_CORRUPT", "BLOCKING", "duplicate raw fact or evidence identity"))
    for evidence in parsed.evidence:
        locator = str(evidence.get("dom_locator", ""))
        if not locator.startswith("/") or not evidence.get("source_member_sha256"):
            issues.append(_issue(P11Reason.P11_EVIDENCE_LOCATOR_INVALID.value, "BLOCKING", "evidence DOM locator is not valid", evidence_id=evidence.get("evidence_id")))

    status, blocking, failures, review, warning = _status(issues)
    directory = Path(validation_root).expanduser().resolve() / parsed.package_sha256
    result = SecValidationResult(
        artifact_dir=directory,
        package_sha256=parsed.package_sha256,
        validation_status=status,
        compatibility_status="COMPATIBLE" if blocking == 0 else "UNKNOWN",
        reuse_eligible=blocking == 0,
        blocking_issue_count=blocking,
        failure_issue_count=failures,
        review_issue_count=review,
        warning_issue_count=warning,
        issue_count=len(issues),
        issues=tuple(issues),
        report_path=directory / "validation.json",
        issues_path=directory / "issues.jsonl",
    )
    _write(result)
    return result


def load_sec_validation(artifact_dir: str | Path) -> SecValidationResult:
    directory = Path(artifact_dir).expanduser().resolve()
    report_path = directory / "validation.json"
    issues_path = directory / "issues.jsonl"
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
        issues = tuple(json.loads(line) for line in issues_path.read_text(encoding="utf-8").splitlines() if line.strip())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC validation artifact is invalid") from exc
    if report.get("schema_version") != SEC_VALIDATION_SCHEMA:
        raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC validation schema mismatch")
    result = SecValidationResult(
        artifact_dir=directory,
        package_sha256=str(report.get("package_sha256", "")),
        validation_status=str(report.get("validation_status", "")),
        compatibility_status=str(report.get("compatibility_status", "")),
        reuse_eligible=bool(report.get("reuse_eligible")),
        blocking_issue_count=int(report.get("blocking_issue_count", -1)),
        failure_issue_count=int(report.get("failure_issue_count", -1)),
        review_issue_count=int(report.get("review_issue_count", -1)),
        warning_issue_count=int(report.get("warning_issue_count", -1)),
        issue_count=int(report.get("issue_count", -1)),
        issues=issues,
        report_path=report_path,
        issues_path=issues_path,
    )
    if result.issue_count != len(result.issues):
        raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC validation issue count mismatch")
    return result


__all__ = ["SEC_VALIDATION_SCHEMA", "SecValidationResult", "load_sec_validation", "validate_sec_artifacts"]
