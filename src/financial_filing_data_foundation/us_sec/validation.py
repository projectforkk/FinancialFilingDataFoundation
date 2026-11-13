from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass
from datetime import date
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from .errors import P11Reason, SecError
from .compatibility import sec_artifact_compatibility
from .discovery import verify_sec_discovery_observation
from .parser import (
    SEC_ARTIFACT_SCHEMA,
    XBRL_INSTANCE_NAMESPACE,
    SecParseResult,
    verify_sec_evidence,
    verify_sec_fact_source_locator,
)


SEC_VALIDATION_SCHEMA = "p11-sec-validation-v3"
_VALID_FACT_SOURCE_MODES = frozenset(
    {"INLINE_XBRL_PRIMARY", "XBRL_INSTANCE_PRIMARY", "NO_STRUCTURED_FACTS"}
)


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
    fact_source_mode: str = "NO_STRUCTURED_FACTS"
    discovery_observation_sha256: str | None = None
    discovery_checked_at: str | None = None
    selected_accession: str | None = None
    discovery_state: str | None = None

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
            "fact_source_mode": self.fact_source_mode,
            "discovery_observation_sha256": self.discovery_observation_sha256,
            "discovery_checked_at": self.discovery_checked_at,
            "selected_accession": self.selected_accession,
            "discovery_state": self.discovery_state,
            "report_file": "validation.json",
            "issues_file": "issues.jsonl",
        }


def _issue(code: str, severity: str, message: str, **extra: Any) -> dict[str, Any]:
    return {"code": code, "severity": severity, "message": message, **extra}


def _authentic_xbrl_instance_member(member: Any) -> bool:
    if str(getattr(getattr(member, "role", None), "value", "")) != "XBRL_INSTANCE":
        return False
    try:
        root = ET.fromstring(bytes(member.body))
    except (ET.ParseError, TypeError, ValueError):
        return False
    tag = str(root.tag)
    if not (tag.startswith("{") and "}" in tag):
        return False
    namespace, local_name = tag[1:].split("}", 1)
    return namespace == XBRL_INSTANCE_NAMESPACE and local_name.casefold() == "xbrl"


def _fact_source_semantic_issues(
    parsed: SecParseResult,
    package: Any,
    fact_source_mode: str,
    *,
    source_cache: dict[tuple[str, str], object] | None = None,
) -> list[dict[str, Any]]:
    """Prove the persisted logical-fact universe matches fact_source_mode."""

    issues: list[dict[str, Any]] = []
    primary_members = [
        member
        for member in package.members
        if str(getattr(getattr(member, "role", None), "value", "")) == "PRIMARY_DOCUMENT"
    ]
    instance_members = [
        member for member in package.members if _authentic_xbrl_instance_member(member)
    ]
    evidence_by_id = {
        str(row.get("evidence_id") or ""): row
        for row in parsed.evidence
        if str(row.get("evidence_id") or "")
    }

    def block(message: str, *, raw_fact_id: str | None = None) -> None:
        extra = {"raw_fact_id": raw_fact_id} if raw_fact_id else {}
        issues.append(
            _issue(
                P11Reason.P11_FACT_SOURCE_MODE_INVALID.value,
                "BLOCKING",
                message,
                **extra,
            )
        )

    if fact_source_mode == "NO_STRUCTURED_FACTS":
        return issues

    if fact_source_mode == "INLINE_XBRL_PRIMARY":
        if len(primary_members) != 1:
            block("SEC INLINE_XBRL_PRIMARY requires exactly one primary document")
            return issues
        logical_member_sha = str(primary_members[0].member_sha256)
        expected_locator_kinds = {"DOM_PATH", "DOM_HIDDEN_FACT"}
    elif fact_source_mode == "XBRL_INSTANCE_PRIMARY":
        if len(instance_members) != 1:
            block("SEC XBRL_INSTANCE_PRIMARY requires exactly one authentic XBRL instance")
            return issues
        logical_member_sha = str(instance_members[0].member_sha256)
        expected_locator_kinds = {"XML_PATH"}
    else:
        return issues

    for fact in parsed.facts:
        fact_id = str(fact.get("raw_fact_id") or "")
        fact_member = str(
            fact.get("source_member_sha256")
            or fact.get("member_sha256")
            or ""
        )
        if fact_member != logical_member_sha:
            block(
                f"SEC {fact_source_mode} fact points to a non-logical-source member",
                raw_fact_id=fact_id or None,
            )
        evidence_id = str(fact.get("evidence_id") or "")
        evidence = evidence_by_id.get(evidence_id)
        if evidence is None:
            block(
                f"SEC {fact_source_mode} fact has no resolving evidence row",
                raw_fact_id=fact_id or None,
            )
            continue
        evidence_member = str(
            evidence.get("source_member_sha256")
            or evidence.get("member_sha256")
            or ""
        )
        if evidence_member != logical_member_sha:
            block(
                f"SEC {fact_source_mode} evidence points to a non-logical-source member",
                raw_fact_id=fact_id or None,
            )
        locator_kind = str(evidence.get("locator_kind") or fact.get("locator_kind") or "")
        if locator_kind not in expected_locator_kinds:
            block(
                f"SEC {fact_source_mode} uses incompatible evidence locator kind {locator_kind or '<missing>'}",
                raw_fact_id=fact_id or None,
            )
        if fact_source_mode == "INLINE_XBRL_PRIMARY":
            if not str(fact.get("dom_locator") or "").startswith("/") or fact.get("xml_locator"):
                block(
                    "SEC INLINE_XBRL_PRIMARY fact is not a primary DOM fact",
                    raw_fact_id=fact_id or None,
                )
            if not str(evidence.get("dom_locator") or evidence.get("fact_dom_locator") or "").startswith("/") or evidence.get("xml_locator"):
                block(
                    "SEC INLINE_XBRL_PRIMARY evidence is not a primary DOM locator",
                    raw_fact_id=fact_id or None,
                )
        else:
            if not str(fact.get("xml_locator") or "").startswith("/") or fact.get("dom_locator"):
                block(
                    "SEC XBRL_INSTANCE_PRIMARY fact is not an XML-instance fact",
                    raw_fact_id=fact_id or None,
                )
            if not str(evidence.get("xml_locator") or "").startswith("/") or evidence.get("dom_locator"):
                block(
                    "SEC XBRL_INSTANCE_PRIMARY evidence is not an XML-path locator",
                    raw_fact_id=fact_id or None,
                )
        for fragment in fact.get("source_fragments") or ():
            fragment_member = str(fragment.get("source_member_sha256") or "")
            if fragment_member != logical_member_sha:
                block(
                    f"SEC {fact_source_mode} fact fragment points to a non-logical-source member",
                    raw_fact_id=fact_id or None,
                )
                break
        try:
            verify_sec_fact_source_locator(
                package,
                fact,
                fact_source_mode=fact_source_mode,
                source_cache=source_cache,
            )
        except SecError as exc:
            block(str(exc), raw_fact_id=fact_id or None)
    return issues


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
        P11Reason.P11_PROVENANCE_MISMATCH.value,
        P11Reason.P11_XBRL_INSTANCE_AMBIGUOUS.value,
        P11Reason.P11_INLINE_CONTINUATION_INVALID.value,
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
    discovery_observation: Any | None = None,
    registry: Any | None = None,
) -> SecValidationResult:
    issues = [dict(row) for row in parsed.issues]
    if package is not None:
        if registry is not None:
            try:
                registry.verify_sec_package_provenance(package)
            except Exception as exc:
                issues.append(
                    _issue(
                        P11Reason.P11_PROVENANCE_MISMATCH.value,
                        "BLOCKING",
                        f"SEC package/Registry provenance verification failed: {exc}",
                    )
                )
        if str(package.package_sha256) != parsed.package_sha256:
            issues.append(_issue(P11Reason.P11_SOURCE_DRIFT.value, "BLOCKING", "parsed artifact package identity differs from source package"))
        if not str(package.cik).isdigit() or len(str(package.cik)) != 10:
            issues.append(_issue(P11Reason.P11_INVALID_US_IDENTITY.value, "BLOCKING", "source package CIK is not normalized"))
        if not str(package.accession).strip() or not str(package.form).strip():
            issues.append(_issue(P11Reason.P11_PACKAGE_INVALID.value, "BLOCKING", "source package accession/form is missing"))
        if not any(member.role.value == "PRIMARY_DOCUMENT" for member in package.members):
            issues.append(_issue(P11Reason.P11_PRIMARY_DOCUMENT_MISSING.value, "BLOCKING", "source package primary document is missing"))
        primary_names = {
            member.relative_name
            for member in package.members
            if member.role.value == "PRIMARY_DOCUMENT"
        }
        if package.primary_document and str(package.primary_document) not in primary_names:
            issues.append(_issue(P11Reason.P11_PACKAGE_INVALID.value, "BLOCKING", "package primary_document does not resolve to the primary member"))
        if not re.fullmatch(r"\d{10}-\d{2}-\d{6}", str(package.accession)):
            issues.append(_issue(P11Reason.P11_PACKAGE_INVALID.value, "BLOCKING", "source package accession is invalid"))
        if package.report_period:
            try:
                report_period = date.fromisoformat(str(package.report_period)[:10])
            except ValueError:
                issues.append(_issue(P11Reason.P11_PACKAGE_INVALID.value, "REVIEW", "source package report_period is not an ISO date"))
            else:
                permitted_years = {int(package.fiscal_year)} if str(package.period).upper() == "FY" else {int(package.fiscal_year) - 1, int(package.fiscal_year)}
                if report_period.year not in permitted_years:
                    issues.append(_issue("P11_PERIOD_END_IMPLAUSIBLE", "REVIEW", "report period is not plausible for the requested fiscal slot", report_period=str(package.report_period)))
                if package.filing_date:
                    try:
                        filing_date = date.fromisoformat(str(package.filing_date)[:10])
                    except ValueError:
                        issues.append(_issue(P11Reason.P11_PACKAGE_INVALID.value, "REVIEW", "source package filing_date is not an ISO date"))
                    else:
                        if filing_date < report_period:
                            issues.append(_issue("P11_PERIOD_END_IMPLAUSIBLE", "REVIEW", "filing date precedes report period", filing_date=str(package.filing_date), report_period=str(package.report_period)))
        member_hashes = {member.member_sha256 for member in package.members}
        for evidence in parsed.evidence:
            if str(evidence.get("member_sha256") or evidence.get("source_member_sha256") or "") not in member_hashes:
                issues.append(_issue(P11Reason.P11_MEMBER_HASH_MISMATCH.value, "BLOCKING", "evidence member hash is not in source package", evidence_id=evidence.get("evidence_id")))
    if amendment_conflict:
        issues.append(_issue(P11Reason.P11_AMENDED_VARIANT_PRESENT.value, "REVIEW", "original and amended SEC variants are both present"))
    source_replay_cache: dict[tuple[str, str], object] = {}
    fact_source_mode = str(parsed.fact_source_mode or "").strip().upper()
    if fact_source_mode not in _VALID_FACT_SOURCE_MODES:
        issues.append(
            _issue(
                P11Reason.P11_FACT_SOURCE_MODE_INVALID.value,
                "BLOCKING",
                f"SEC fact_source_mode is unsupported: {fact_source_mode or '<missing>'}",
            )
        )
    elif fact_source_mode == "NO_STRUCTURED_FACTS" and parsed.facts:
        issues.append(
            _issue(
                P11Reason.P11_FACT_SOURCE_MODE_INVALID.value,
                "BLOCKING",
                "SEC NO_STRUCTURED_FACTS mode cannot contain persisted Raw Facts",
            )
        )
    elif fact_source_mode in {"INLINE_XBRL_PRIMARY", "XBRL_INSTANCE_PRIMARY"} and not parsed.facts:
        issues.append(
            _issue(
                P11Reason.P11_FACT_SOURCE_MODE_INVALID.value,
                "BLOCKING",
                f"SEC {fact_source_mode} mode has no persisted Raw Facts",
            )
        )
    if package is not None and fact_source_mode in _VALID_FACT_SOURCE_MODES:
        issues.extend(
            _fact_source_semantic_issues(
                parsed,
                package,
                fact_source_mode,
                source_cache=source_replay_cache,
            )
        )
    observation = discovery_observation
    observation_sha = getattr(observation, "observation_sha256", None) or parsed.discovery_observation_sha256
    discovery_checked_at = getattr(observation, "retrieved_at", None) or parsed.discovery_checked_at
    selected_accession = getattr(observation, "selected_accession", None) or parsed.selected_accession
    discovery_state = getattr(observation, "state", None) or parsed.discovery_state
    if observation is None:
        issues.append(
            _issue(
                P11Reason.P11_DISCOVERY_FRESHNESS_UNKNOWN.value,
                "BLOCKING",
                "SEC P7 validation requires an exact discovery observation",
            )
        )
    else:
        registry_row = None
        if registry is not None:
            try:
                registry_row = registry.get_sec_discovery_observation(
                    str(getattr(observation, "observation_sha256", ""))
                )
            except Exception as exc:
                issues.append(
                    _issue(
                        P11Reason.P11_PROVENANCE_MISMATCH.value,
                        "BLOCKING",
                        f"SEC discovery observation Registry lookup failed: {exc}",
                    )
                )
            if registry_row is None:
                issues.append(
                    _issue(
                        P11Reason.P11_PROVENANCE_MISMATCH.value,
                        "BLOCKING",
                        "SEC discovery observation is not present in the Registry",
                    )
                )
        try:
            verify_sec_discovery_observation(
                observation,
                package=package,
                registry_row=registry_row,
            )
        except SecError as exc:
            issues.append(_issue(exc.reason_code, "BLOCKING", str(exc)))


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
    table_ids = {str(table.get("table_id", "")) for table in parsed.tables}
    if len(table_ids) != len(parsed.tables) or "" in table_ids:
        issues.append(_issue("P11_TABLE_TRACE_INVALID", "BLOCKING", "table identity is missing or duplicated"))
    cell_ids: set[str] = set()
    for table in parsed.tables:
        if str(table.get("document_sha256", "")) != parsed.package_sha256:
            issues.append(_issue(P11Reason.P11_EVIDENCE_LOCATOR_INVALID.value, "BLOCKING", "table document identity does not match package", table_id=table.get("table_id")))
        source_member = str(table.get("source_member_sha256") or "")
        if package is not None and source_member not in {member.member_sha256 for member in package.members}:
            issues.append(_issue(P11Reason.P11_MEMBER_HASH_MISMATCH.value, "BLOCKING", "table source member is not in source package", table_id=table.get("table_id")))
        for row in table.get("rows") or ():
            for cell in row.get("cells") or ():
                cell_id = str(cell.get("cell_id") or "")
                if not cell_id or cell_id in cell_ids:
                    issues.append(_issue("P11_TABLE_TRACE_INVALID", "BLOCKING", "table cell identity is missing or duplicated", table_id=table.get("table_id")))
                cell_ids.add(cell_id)
                if source_member and not cell.get("source_member_sha256") == source_member:
                    issues.append(_issue("P11_TABLE_TRACE_INVALID", "BLOCKING", "table cell source member is inconsistent", cell_id=cell_id))
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
        table_cell_id = str(fact.get("table_cell_id") or "")
        if table_cell_id and table_cell_id not in cell_ids:
            issues.append(_issue("P11_TABLE_TRACE_INVALID", "BLOCKING", "raw fact table_cell_id does not resolve", raw_fact_id=fact.get("raw_fact_id")))
        fact_table_id = str(fact.get("table_id") or "")
        if fact_table_id and fact_table_id not in table_ids:
            issues.append(_issue("P11_TABLE_TRACE_INVALID", "BLOCKING", "raw fact table_id does not resolve", raw_fact_id=fact.get("raw_fact_id")))
    if len(fact_ids) != len(parsed.facts) or len(evidence_ids) != len(parsed.evidence):
        issues.append(_issue("P11_ARTIFACT_INCOMPLETE_OR_CORRUPT", "BLOCKING", "duplicate raw fact or evidence identity"))
    evidence_source_cache = source_replay_cache
    dom_targets: dict[str, set[str]] = {}
    for evidence in parsed.evidence:
        locator_kind = str(evidence.get("locator_kind") or "DOM_PATH").upper()
        member_sha = str(evidence.get("member_sha256") or evidence.get("source_member_sha256") or "")
        if locator_kind not in {"DOM_PATH", "DOM_HIDDEN_FACT"} or not member_sha:
            continue
        targets = dom_targets.setdefault(member_sha, set())
        locator = str(evidence.get("dom_locator") or "")
        if locator:
            targets.add(locator)
        block_locator = str(evidence.get("block_dom_locator") or "")
        if block_locator:
            targets.add(block_locator)
    for member_sha, targets in dom_targets.items():
        evidence_source_cache[("DOM_TARGETS", member_sha)] = targets
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
        evidence_table_id = str(evidence.get("table_id") or "")
        if evidence_table_id and evidence_table_id not in table_ids:
            issues.append(_issue("P11_TABLE_TRACE_INVALID", "BLOCKING", "evidence table_id does not resolve", evidence_id=evidence.get("evidence_id")))
        if package is not None:
            try:
                verify_sec_evidence(package, parsed.pages, evidence, source_cache=evidence_source_cache)
            except SecError as exc:
                issues.append(_issue(exc.reason_code, "BLOCKING", str(exc), evidence_id=evidence.get("evidence_id")))

    status, blocking, failures, review, warning = _status(issues)
    directory = Path(validation_root).expanduser().resolve() / parsed.package_sha256
    result = SecValidationResult(
        artifact_dir=directory,
        package_sha256=parsed.package_sha256,
        validation_status=status,
        compatibility_status=sec_artifact_compatibility(
            parser_version=parsed.parser_version,
            schema_version=SEC_ARTIFACT_SCHEMA,
        ),
        reuse_eligible=(
            status == "PASS"
            and sec_artifact_compatibility(
                parser_version=parsed.parser_version,
                schema_version=SEC_ARTIFACT_SCHEMA,
            )
            == "COMPATIBLE"
            and blocking == 0
        ),
        blocking_issue_count=blocking,
        failure_issue_count=failures,
        review_issue_count=review,
        warning_issue_count=warning,
        issue_count=len(issues),
        issues=tuple(issues),
        report_path=directory / "validation.json",
        issues_path=directory / "issues.jsonl",
        fact_source_mode=parsed.fact_source_mode,
        discovery_observation_sha256=observation_sha,
        discovery_checked_at=discovery_checked_at,
        selected_accession=selected_accession,
        discovery_state=discovery_state,
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
        fact_source_mode=str(report.get("fact_source_mode") or "NO_STRUCTURED_FACTS"),
        discovery_observation_sha256=str(report.get("discovery_observation_sha256") or "") or None,
        discovery_checked_at=str(report.get("discovery_checked_at") or "") or None,
        selected_accession=str(report.get("selected_accession") or "") or None,
        discovery_state=str(report.get("discovery_state") or "") or None,
    )
    if result.issue_count != len(result.issues):
        raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC validation issue count mismatch")
    expected_reuse = (
        result.validation_status == "PASS"
        and result.compatibility_status == "COMPATIBLE"
        and result.blocking_issue_count == 0
    )
    if result.reuse_eligible != expected_reuse:
        raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC validation reuse eligibility is inconsistent")
    return result


__all__ = ["SEC_VALIDATION_SCHEMA", "SecValidationResult", "load_sec_validation", "validate_sec_artifacts"]
