from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import P11Reason, SecError
from .parser import SecParseResult, verify_sec_evidence


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
    with result.issues_path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in result.issues:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
    payload = result.to_dict()
    payload["artifact_hashes"] = {
        "issues_file": hashlib.sha256(result.issues_path.read_bytes()).hexdigest(),
    }
    result.report_path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


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
    package: Any | None = None,
) -> SecValidationResult:
    issues = [dict(row) for row in parsed.issues]
    if package is not None:
        if str(package.package_sha256) != parsed.package_sha256:
            issues.append(_issue(P11Reason.P11_SOURCE_DRIFT.value, "BLOCKING", "parsed artifact package identity differs from source package"))
        if not str(package.cik).isdigit() or len(str(package.cik)) != 10:
            issues.append(_issue(P11Reason.P11_INVALID_US_IDENTITY.value, "BLOCKING", "source package CIK is not normalized"))
        if not str(package.accession).strip() or not str(package.form).strip():
            issues.append(_issue(P11Reason.P11_PACKAGE_INVALID.value, "BLOCKING", "source package accession/form is missing"))
        if not any(member.role.value == "PRIMARY_DOCUMENT" for member in package.members):
            issues.append(_issue(P11Reason.P11_PRIMARY_DOCUMENT_MISSING.value, "BLOCKING", "source package primary document is missing"))
        member_hashes = {member.member_sha256 for member in package.members}
        for evidence in parsed.evidence:
            if str(evidence.get("member_sha256") or evidence.get("source_member_sha256") or "") not in member_hashes:
                issues.append(_issue(P11Reason.P11_MEMBER_HASH_MISMATCH.value, "BLOCKING", "evidence member hash is not in source package", evidence_id=evidence.get("evidence_id")))
    if amendment_conflict:
        issues.append(_issue(P11Reason.P11_AMENDED_VARIANT_PRESENT.value, "REVIEW", "original and amended SEC variants are both present"))

    expected_pages = list(range(1, len(parsed.pages) + 1))
    actual_pages = [int(row.get("page_no", -1)) for row in parsed.pages]
    if actual_pages != expected_pages:
        issues.append(_issue("P11_ARTIFACT_INCOMPLETE_OR_CORRUPT", "BLOCKING", "virtual page sequence is not contiguous"))
    fact_ids = {str(row.get("raw_fact_id", "")) for row in parsed.facts}
    evidence_ids = {str(row.get("evidence_id", "")) for row in parsed.evidence}
    evidence_by_id = {str(row.get("evidence_id", "")): row for row in parsed.evidence}
    blocks_by_id = {
        str(block.get("block_id", "")): block
        for page in parsed.pages
        for block in (page.get("blocks") or [])
    }
    if not parsed.facts:
        issues.append(
            _issue(
                P11Reason.P11_STRUCTURED_FACTS_MISSING.value,
                "REVIEW",
                "periodic SEC filing has no structured XBRL Raw Facts",
            )
        )
    elif package is None:
        issues.append(
            _issue(
                P11Reason.P11_EVIDENCE_LOCATOR_INVALID.value,
                "BLOCKING",
                "source package is required to validate structured SEC evidence",
            )
        )
    elif not parsed.evidence:
        issues.append(
            _issue(
                P11Reason.P11_EVIDENCE_LOCATOR_INVALID.value,
                "BLOCKING",
                "structured SEC Raw Facts have no Evidence",
            )
        )
    for fact in parsed.facts:
        fact_evidence_id = str(fact.get("evidence_id", ""))
        if not fact.get("raw_fact_id") or not fact_evidence_id or fact_evidence_id not in evidence_ids:
            issues.append(_issue("P11_ARTIFACT_INCOMPLETE_OR_CORRUPT", "BLOCKING", "raw fact does not resolve to evidence"))
        evidence = evidence_by_id.get(fact_evidence_id)
        if evidence is not None and str(evidence.get("raw_fact_id", "")) != str(fact.get("raw_fact_id", "")):
            issues.append(_issue(P11Reason.P11_EVIDENCE_LOCATOR_INVALID.value, "BLOCKING", "Evidence does not point back to its Raw Fact", evidence_id=fact_evidence_id))
    if len(fact_ids) != len(parsed.facts) or len(evidence_ids) != len(parsed.evidence):
        issues.append(_issue("P11_ARTIFACT_INCOMPLETE_OR_CORRUPT", "BLOCKING", "duplicate raw fact or evidence identity"))
    for evidence in parsed.evidence:
        locator_kind = str(evidence.get("locator_kind") or "DOM_PATH").upper()
        locator = str(evidence.get("xml_locator" if locator_kind == "XML_PATH" else "dom_locator", ""))
        if not locator.startswith("/") or not evidence.get("source_member_sha256"):
            issues.append(_issue(P11Reason.P11_EVIDENCE_LOCATOR_INVALID.value, "BLOCKING", "evidence source locator is not valid", evidence_id=evidence.get("evidence_id")))
        if locator_kind == "DOM_PATH":
            if str(evidence.get("block_id") or "") not in blocks_by_id:
                issues.append(_issue(P11Reason.P11_EVIDENCE_LOCATOR_INVALID.value, "BLOCKING", "evidence block_id is not a normalized source block", evidence_id=evidence.get("evidence_id")))
            if not str(evidence.get("block_dom_locator") or "").startswith("/"):
                issues.append(_issue(P11Reason.P11_EVIDENCE_LOCATOR_INVALID.value, "BLOCKING", "visible evidence block locator is missing", evidence_id=evidence.get("evidence_id")))
        if package is not None:
            try:
                verify_sec_evidence(package, parsed.pages, evidence)
            except SecError as exc:
                issues.append(_issue(exc.reason_code, "BLOCKING", str(exc), evidence_id=evidence.get("evidence_id")))

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
    hashes = report.get("artifact_hashes")
    if not isinstance(hashes, dict) or str(hashes.get("issues_file", "")) != hashlib.sha256(issues_path.read_bytes()).hexdigest():
        raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC validation issue hash mismatch")
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
