from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any, Mapping, Sequence

from financial_filing_data_foundation.identity import FilingSlotKey
from financial_filing_data_foundation.registry.models import (
    CompatibilityStatus,
    ParsedDataRecord,
    ValidationStatus,
)
from financial_filing_data_foundation.validation.policy import (
    MIN_FACTS_FOR_SEMANTIC_COVERAGE,
    PERIOD_REVIEW,
    UNIT_REVIEW,
)

from .evidence import (
    _ACTION_FIELD,
    active_effective_assignments,
    build_before_after,
    build_indexes,
    resolve_target,
    validate_direct_evidence,
    validate_reviewer,
)
from .models import (
    P9_VERSION,
    RESOLUTION_REPORT_SCHEMA_VERSION,
    RESOLVED_FACT_SCHEMA_VERSION,
    RESOLVED_VIEW_SCHEMA_VERSION,
    REVIEW_POLICY_VERSION,
    SNAPSHOT_MANIFEST_SCHEMA_VERSION,
    ResolutionAction,
    ResolutionSubmission,
    ResolvedIssueState,
    ResolvedSnapshot,
    ReviewError,
    ReviewResolution,
    Reviewability,
    canonical_json_bytes,
    pretty_json_bytes,
    sha256_bytes,
    sha256_file,
)
from .queue import load_review_base
from .store import active_resolutions, list_resolutions


def _jsonl_bytes(rows: Sequence[Mapping[str, Any]]) -> bytes:
    if not rows:
        return b""
    return b"".join(canonical_json_bytes(dict(row)) + b"\n" for row in rows)


def _resolution_by_id(review_dir: Path) -> dict[str, ReviewResolution]:
    return {item.resolution_id: item for item in list_resolutions(review_dir)}


def _validate_resolution_semantics(
    resolution: ReviewResolution,
    indexes,
    task,
    all_by_id: Mapping[str, ReviewResolution],
) -> Any:
    prior: list[ReviewResolution] = []
    for resolution_id in resolution.base_active_resolution_ids:
        item = all_by_id.get(resolution_id)
        if item is None:
            raise ReviewError(
                "P9_ARTIFACT_INCOMPLETE_OR_CORRUPT",
                f"resolution prior state is missing: {resolution_id}",
            )
        prior.append(item)
    prior_effective = active_effective_assignments(prior)

    submission = ResolutionSubmission(
        review_task_id=resolution.review_task_id,
        action=resolution.action,
        target=resolution.target,
        value=resolution.value,
        reviewer_type=resolution.reviewer_type,
        reviewer_id=resolution.reviewer_id,
        reviewed_at=resolution.reviewed_at,
        justification=resolution.justification,
        evidence_refs=(
            ()
            if resolution.action is ResolutionAction.ATTEST_ISSUE_RESOLVED
            else resolution.evidence_refs
        ),
        evidence_pages=(
            None
            if resolution.action is ResolutionAction.ATTEST_ISSUE_RESOLVED
            else resolution.evidence_pages
        ),
        supersedes_resolution_id=resolution.supersedes_resolution_id,
        supporting_resolution_ids=resolution.supporting_resolution_ids,
        expected_observed_count=resolution.expected_observed_count,
    )
    validate_reviewer(submission)
    selection = resolve_target(indexes, task, submission, prior_effective)

    if resolution.action is ResolutionAction.ATTEST_ISSUE_RESOLVED:
        support: list[ReviewResolution] = []
        for support_id in resolution.supporting_resolution_ids:
            item = all_by_id.get(support_id)
            if item is None or support_id not in resolution.base_active_resolution_ids:
                raise ReviewError(
                    "P9_ARTIFACT_INCOMPLETE_OR_CORRUPT",
                    f"attestation support was not active in prior state: {support_id}",
                )
            if item.review_task_id != resolution.review_task_id or item.issue_id != resolution.issue_id:
                raise ReviewError(
                    "P9_ARTIFACT_INCOMPLETE_OR_CORRUPT",
                    "attestation support crosses task/issue",
                )
            if item.action is ResolutionAction.ATTEST_ISSUE_RESOLVED:
                raise ReviewError(
                    "P9_ARTIFACT_INCOMPLETE_OR_CORRUPT",
                    "attestation support cannot itself be attestation",
                )
            support.append(item)
        refs_by_key: dict[bytes, dict[str, Any]] = {}
        pages: set[int] = set()
        for item in support:
            for ref in item.evidence_refs:
                refs_by_key[canonical_json_bytes(ref)] = dict(ref)
            pages.update(int(page) for page in item.evidence_pages)
        expected_refs = tuple(refs_by_key[key] for key in sorted(refs_by_key))
        expected_pages = tuple(sorted(pages))
        if not expected_refs:
            raise ReviewError(
                "P9_ARTIFACT_INCOMPLETE_OR_CORRUPT",
                "attestation inherited evidence is empty",
            )
        if expected_refs != resolution.evidence_refs or expected_pages != resolution.evidence_pages:
            raise ReviewError(
                "P9_ARTIFACT_INCOMPLETE_OR_CORRUPT",
                "attestation inherited evidence/pages were tampered",
            )
        expected_before = {
            "target": selection.target,
            "base_observed": dict(indexes.issue_by_id[task.issue_id].get("observed") or {}),
            "supporting_resolution_ids": sorted(item.resolution_id for item in support),
        }
        expected_after = {
            "value": "RESOLVED",
            "expected_observed_count": resolution.expected_observed_count,
        }
        if resolution.before != expected_before or resolution.after != expected_after:
            raise ReviewError(
                "P9_ARTIFACT_INCOMPLETE_OR_CORRUPT",
                "attestation before/after state mismatch",
            )
        return selection

    refs, pages = validate_direct_evidence(indexes, selection, submission)
    if refs != resolution.evidence_refs or pages != resolution.evidence_pages:
        raise ReviewError(
            "P9_ARTIFACT_INCOMPLETE_OR_CORRUPT",
            "resolution evidence/pages semantic mismatch",
        )
    expected_before, expected_after = build_before_after(selection)
    if resolution.before != expected_before:
        raise ReviewError(
            "P9_ARTIFACT_INCOMPLETE_OR_CORRUPT",
            "resolution before-state does not match explicit prior overlay state",
        )
    if resolution.after != expected_after:
        raise ReviewError(
            "P9_ARTIFACT_INCOMPLETE_OR_CORRUPT",
            "resolution after-state mismatch",
        )
    return selection


def _generate(
    review_dir: Path,
    selected: Sequence[ReviewResolution],
) -> tuple[
    str,
    tuple[dict[str, Any], ...],
    tuple[dict[str, Any], ...],
    dict[str, Any],
    dict[str, Any],
]:
    manifest, bundle, tasks = load_review_base(review_dir)
    indexes = build_indexes(bundle, tasks)
    task_by_id = indexes.task_by_id

    # Validate the complete immutable history first, even when materializing
    # a historical selected subset.
    active_resolutions(review_dir)
    all_by_id = _resolution_by_id(review_dir)

    selected_by_id = {item.resolution_id: item for item in selected}
    if len(selected_by_id) != len(selected):
        raise ReviewError("P9_RESOLUTION_CONFLICT", "duplicate selected resolution ID")
    if any(resolution_id not in all_by_id for resolution_id in selected_by_id):
        raise ReviewError(
            "P9_ARTIFACT_INCOMPLETE_OR_CORRUPT",
            "selected resolution is absent from immutable resolution store",
        )

    selections: dict[str, Any] = {}
    for resolution in selected:
        if resolution.document_sha256 != bundle.document_sha256:
            raise ReviewError("P9_ARTIFACT_INCOMPLETE_OR_CORRUPT", "resolution document mismatch")
        if resolution.base_validation_report_sha256 != bundle.base_validation_report_sha256:
            raise ReviewError("P9_BASE_ARTIFACT_CHANGED", "resolution base validation identity mismatch")
        task = task_by_id.get(resolution.review_task_id)
        if task is None or task.issue_id != resolution.issue_id or task.reason_code != resolution.reason_code:
            raise ReviewError("P9_ARTIFACT_INCOMPLETE_OR_CORRUPT", "resolution task/issue mismatch")
        selections[resolution.resolution_id] = _validate_resolution_semantics(
            resolution,
            indexes,
            task,
            all_by_id,
        )

    field_assignments: dict[tuple[str, str], tuple[str, set[str]]] = {}
    statement_assignments: dict[str, tuple[str, set[str]]] = {}
    attest_by_task: dict[str, set[str]] = {}

    for resolution in sorted(selected, key=lambda item: item.resolution_id):
        if resolution.action in _ACTION_FIELD:
            field = _ACTION_FIELD[resolution.action]
            value = str(resolution.value or "")
            selection = selections[resolution.resolution_id]
            for fact_id in selection.affected_fact_ids:
                key = (fact_id, field)
                prior = field_assignments.get(key)
                if prior is not None and prior[0] != value:
                    raise ReviewError(
                        "P9_RESOLUTION_CONFLICT",
                        f"conflicting active values for {fact_id}/{field}",
                    )
                if prior is None:
                    field_assignments[key] = (value, {resolution.resolution_id})
                else:
                    prior[1].add(resolution.resolution_id)
        elif resolution.action is ResolutionAction.CLASSIFY_TABLE_STATEMENT:
            table_id = str(resolution.target["table_id"])
            value = str(resolution.value)
            prior = statement_assignments.get(table_id)
            if prior is not None and prior[0] != value:
                raise ReviewError(
                    "P9_RESOLUTION_CONFLICT",
                    f"conflicting statement classes for table {table_id}",
                )
            if prior is None:
                statement_assignments[table_id] = (value, {resolution.resolution_id})
            else:
                prior[1].add(resolution.resolution_id)
        elif resolution.action is ResolutionAction.ATTEST_ISSUE_RESOLVED:
            attest_by_task.setdefault(resolution.review_task_id, set()).add(
                resolution.resolution_id
            )

    resolved_facts: list[dict[str, Any]] = []
    for raw in bundle.p6_facts:
        fact = dict(raw)
        fact_id = str(raw["raw_fact_id"])
        table_id = str(raw.get("table_id") or "")
        overlay_ids: set[str] = set()

        raw_period = raw.get("raw_period_label")
        raw_unit = raw.get("raw_unit")
        raw_scope = raw.get("raw_scope")

        period_assignment = field_assignments.get((fact_id, "period"))
        unit_assignment = field_assignments.get((fact_id, "unit"))
        scope_assignment = field_assignments.get((fact_id, "scope"))
        statement_assignment = statement_assignments.get(table_id)

        fact["effective_period_label"] = (
            raw_period
            if raw_period is not None
            else (period_assignment[0] if period_assignment is not None else None)
        )
        fact["effective_unit"] = (
            raw_unit
            if raw_unit is not None
            else (unit_assignment[0] if unit_assignment is not None else None)
        )
        fact["effective_scope"] = (
            raw_scope
            if raw_scope is not None
            else (scope_assignment[0] if scope_assignment is not None else None)
        )
        fact["effective_statement_class"] = (
            statement_assignment[0] if statement_assignment is not None else None
        )

        for assignment in (period_assignment, unit_assignment, scope_assignment, statement_assignment):
            if assignment is not None:
                overlay_ids.update(assignment[1])
        fact["overlay_resolution_ids"] = sorted(overlay_ids)
        fact["resolved_schema_version"] = RESOLVED_FACT_SCHEMA_VERSION
        resolved_facts.append(fact)

    fact_count = len(resolved_facts)
    def ratio(field: str) -> float:
        if not fact_count:
            return 0.0
        return round(
            sum(1 for fact in resolved_facts if fact.get(field) is not None) / fact_count,
            6,
        )

    period_ratio = ratio("effective_period_label")
    unit_ratio = ratio("effective_unit")
    scope_ratio = ratio("effective_scope")

    base_signals_raw = bundle.p7_report.get("metrics", {}).get("core_statement_signals") or {}
    core_signals = {
        "balance": bool(base_signals_raw.get("balance")),
        "income": bool(base_signals_raw.get("income")),
        "cashflow": bool(base_signals_raw.get("cashflow")),
    }
    for statement_class, _ids in statement_assignments.values():
        key = statement_class.lower()
        if key in core_signals:
            core_signals[key] = True
    core_signal_count = sum(1 for value in core_signals.values() if value)

    active_by_task: dict[str, list[str]] = {}
    for resolution in selected:
        active_by_task.setdefault(resolution.review_task_id, []).append(resolution.resolution_id)

    resolved_issues: list[dict[str, Any]] = []
    resolved_count = 0
    unresolved_count = 0
    unsupported_count = 0
    for task in tasks:
        reason = task.reason_code
        state = ResolvedIssueState.UNRESOLVED
        explanation = "supported review condition is not yet satisfied"
        metrics_after: dict[str, Any] = {}
        if task.reviewability is Reviewability.UNSUPPORTED:
            state = ResolvedIssueState.UNSUPPORTED
            explanation = "review reason is unsupported by P9 v1"
            unsupported_count += 1
        elif reason == "RAW_PERIOD_COVERAGE_LOW":
            metrics_after = {"period_nonnull_ratio": period_ratio}
            if fact_count < MIN_FACTS_FOR_SEMANTIC_COVERAGE or period_ratio >= PERIOD_REVIEW:
                state = ResolvedIssueState.RESOLVED
                explanation = "effective period coverage meets the P7 review threshold"
        elif reason == "RAW_UNIT_COVERAGE_LOW":
            metrics_after = {"unit_nonnull_ratio": unit_ratio}
            if fact_count < MIN_FACTS_FOR_SEMANTIC_COVERAGE or unit_ratio >= UNIT_REVIEW:
                state = ResolvedIssueState.RESOLVED
                explanation = "effective unit coverage meets the P7 review threshold"
        elif reason in {"RAW_PERIOD_AMBIGUOUS", "RAW_UNIT_AMBIGUOUS", "RAW_SCOPE_AMBIGUOUS"}:
            attested = bool(attest_by_task.get(task.review_task_id))
            metrics_after = {"attested": attested}
            if attested:
                state = ResolvedIssueState.RESOLVED
                explanation = "active evidence-grounded issue attestation is present"
        elif reason == "CORE_STATEMENT_COVERAGE_LOW":
            metrics_after = {
                "core_statement_signal_count": core_signal_count,
                "core_statement_signals": core_signals,
            }
            if core_signal_count >= 2:
                state = ResolvedIssueState.RESOLVED
                explanation = "base plus reviewed statement signals meet coverage"
        else:
            state = ResolvedIssueState.UNSUPPORTED
            explanation = "review reason is unsupported by P9 v1"
            unsupported_count += 1

        if state is ResolvedIssueState.RESOLVED:
            resolved_count += 1
        elif state is ResolvedIssueState.UNRESOLVED:
            unresolved_count += 1

        resolved_issues.append(
            {
                "issue_id": task.issue_id,
                "reason_code": task.reason_code,
                "base_state": "REVIEW",
                "resolved_state": state.value,
                "reviewability": task.reviewability.value,
                "active_resolution_ids": sorted(active_by_task.get(task.review_task_id, [])),
                "metrics_before": task.observed,
                "metrics_after": metrics_after,
                "explanation": explanation,
            }
        )

    base_status = str(bundle.p7_report.get("validation_status") or "")
    if base_status == "PASS":
        resolved_status = "PASS"
    elif base_status == "REVIEW_REQUIRED":
        resolved_status = (
            "PASS"
            if tasks
            and resolved_count == len(tasks)
            and unresolved_count == 0
            and unsupported_count == 0
            else "REVIEW_REQUIRED"
        )
    else:
        resolved_status = base_status

    compatibility = str(bundle.p7_report.get("compatibility_status") or "UNKNOWN")
    blocking = int(bundle.p7_report.get("blocking_issue_count") or 0)
    failures = int(bundle.p7_report.get("failure_issue_count") or 0)
    reuse_eligible = (
        resolved_status == "PASS"
        and compatibility == "COMPATIBLE"
        and blocking == 0
        and failures == 0
    )

    active_ids = tuple(sorted(selected_by_id))
    overlay_hash = sha256_bytes(
        (
            bundle.document_sha256
            + "\0"
            + bundle.base_validation_report_sha256
            + "\0"
            + REVIEW_POLICY_VERSION
            + "\0"
            + "\0".join(active_ids)
        ).encode("utf-8")
    )

    versions = dict(manifest.get("versions") or {})
    report = {
        "schema_version": RESOLUTION_REPORT_SCHEMA_VERSION,
        "policy_version": REVIEW_POLICY_VERSION,
        "document_sha256": bundle.document_sha256,
        "overlay_set_hash": overlay_hash,
        "base_validation_status": base_status,
        "base_compatibility_status": compatibility,
        "resolved_validation_status": resolved_status,
        "resolved_reuse_eligible": reuse_eligible,
        "base_review_issue_count": len(tasks),
        "resolved_review_issue_count": resolved_count,
        "unresolved_review_issue_count": unresolved_count,
        "unsupported_review_issue_count": unsupported_count,
        "conflict_issue_count": 0,
        "active_resolution_count": len(selected),
        "active_resolution_ids": list(active_ids),
        "effective_metrics": {
            "fact_count": fact_count,
            "period_nonnull_ratio": period_ratio,
            "unit_nonnull_ratio": unit_ratio,
            "scope_nonnull_ratio": scope_ratio,
            "core_statement_signal_count": core_signal_count,
            "core_statement_signals": core_signals,
        },
        "base_warning_issue_count": int(bundle.p7_report.get("warning_issue_count") or 0),
        "base_blocking_issue_count": blocking,
        "base_failure_issue_count": failures,
        "input_fingerprints": dict(manifest["input_fingerprints"]),
        "base_validation_report_sha256": bundle.base_validation_report_sha256,
        "versions": versions,
    }

    resolved_facts_tuple = tuple(resolved_facts)
    resolved_issues_tuple = tuple(sorted(resolved_issues, key=lambda item: item["issue_id"]))
    facts_bytes = _jsonl_bytes(resolved_facts_tuple)
    issues_bytes = _jsonl_bytes(resolved_issues_tuple)
    report_bytes = pretty_json_bytes(report)
    snapshot_manifest = {
        "schema_version": SNAPSHOT_MANIFEST_SCHEMA_VERSION,
        "policy_version": REVIEW_POLICY_VERSION,
        "document_sha256": bundle.document_sha256,
        "overlay_set_hash": overlay_hash,
        "base_validation_report_sha256": bundle.base_validation_report_sha256,
        "active_resolution_ids": list(active_ids),
        "input_fingerprints": dict(manifest["input_fingerprints"]),
        "files": {
            "resolved_facts.jsonl": sha256_bytes(facts_bytes),
            "resolved_issues.jsonl": sha256_bytes(issues_bytes),
            "resolution_report.json": sha256_bytes(report_bytes),
        },
    }
    return (
        overlay_hash,
        resolved_facts_tuple,
        resolved_issues_tuple,
        report,
        snapshot_manifest,
    )


def _snapshot_bytes(
    facts: Sequence[Mapping[str, Any]],
    issues: Sequence[Mapping[str, Any]],
    report: Mapping[str, Any],
    manifest: Mapping[str, Any],
) -> dict[str, bytes]:
    return {
        "resolved_facts.jsonl": _jsonl_bytes(facts),
        "resolved_issues.jsonl": _jsonl_bytes(issues),
        "resolution_report.json": pretty_json_bytes(dict(report)),
        "snapshot_manifest.json": pretty_json_bytes(dict(manifest)),
    }


def _validate_existing_snapshot(snapshot_dir: Path, expected: Mapping[str, bytes]) -> None:
    for name, data in expected.items():
        path = snapshot_dir / name
        if not path.is_file():
            raise ReviewError(
                "P9_ARTIFACT_INCOMPLETE_OR_CORRUPT",
                f"snapshot file missing: {path}",
            )
        try:
            actual = path.read_bytes()
        except OSError as exc:
            raise ReviewError("P9_ARTIFACT_INCOMPLETE_OR_CORRUPT", str(exc)) from exc
        if actual != data:
            raise ReviewError(
                "P9_ARTIFACT_INCOMPLETE_OR_CORRUPT",
                f"snapshot semantic/tamper mismatch: {name}",
            )


def _persist_snapshot(
    review_dir: Path,
    overlay_hash: str,
    files: Mapping[str, bytes],
) -> Path:
    snapshots = review_dir / "snapshots"
    if not snapshots.is_dir():
        raise ReviewError("P9_ARTIFACT_INCOMPLETE_OR_CORRUPT", "snapshots directory missing")
    final = snapshots / overlay_hash
    if final.exists():
        if not final.is_dir():
            raise ReviewError("P9_ARTIFACT_INCOMPLETE_OR_CORRUPT", "snapshot path is not a directory")
        _validate_existing_snapshot(final, files)
        return final

    temp = snapshots / f".{overlay_hash}.tmp"
    if temp.exists():
        raise ReviewError("P9_PERSIST_FAILED", f"stale snapshot temp directory exists: {temp}")
    try:
        temp.mkdir()
        for name, data in files.items():
            path = temp / name
            with path.open("xb") as handle:
                handle.write(data)
        os.replace(temp, final)
    except Exception as exc:
        try:
            if temp.exists():
                shutil.rmtree(temp)
        except OSError:
            pass
        if isinstance(exc, ReviewError):
            raise
        raise ReviewError("P9_PERSIST_FAILED", f"cannot persist resolved snapshot: {exc}") from exc
    return final


def _snapshot_object(snapshot_dir: Path, report: dict[str, Any]) -> ResolvedSnapshot:
    return ResolvedSnapshot(
        snapshot_dir=snapshot_dir,
        document_sha256=str(report["document_sha256"]),
        overlay_set_hash=str(report["overlay_set_hash"]),
        resolved_facts_path=snapshot_dir / "resolved_facts.jsonl",
        resolved_issues_path=snapshot_dir / "resolved_issues.jsonl",
        report_path=snapshot_dir / "resolution_report.json",
        manifest_path=snapshot_dir / "snapshot_manifest.json",
        report=report,
    )


def materialize_resolved_view(review_dir: str | Path) -> ResolvedSnapshot:
    directory = Path(review_dir).expanduser().resolve()
    selected = active_resolutions(directory)
    overlay_hash, facts, issues, report, manifest = _generate(directory, selected)
    files = _snapshot_bytes(facts, issues, report, manifest)
    snapshot_dir = _persist_snapshot(directory, overlay_hash, files)
    return _snapshot_object(snapshot_dir, report)


def load_resolved_snapshot(
    snapshot_dir: str | Path,
    review_dir: str | Path,
) -> ResolvedSnapshot:
    directory = Path(review_dir).expanduser().resolve()
    snapshot = Path(snapshot_dir).expanduser().resolve()
    try:
        snapshot.relative_to((directory / "snapshots").resolve())
    except ValueError as exc:
        raise ReviewError("P9_ARTIFACT_INCOMPLETE_OR_CORRUPT", "snapshot lies outside review snapshots") from exc
    manifest_path = snapshot / "snapshot_manifest.json"
    try:
        stored_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReviewError("P9_ARTIFACT_INCOMPLETE_OR_CORRUPT", f"cannot read snapshot manifest: {exc}") from exc
    if not isinstance(stored_manifest, dict):
        raise ReviewError("P9_ARTIFACT_INCOMPLETE_OR_CORRUPT", "snapshot manifest root invalid")
    if stored_manifest.get("schema_version") != SNAPSHOT_MANIFEST_SCHEMA_VERSION:
        raise ReviewError("P9_ARTIFACT_INCOMPLETE_OR_CORRUPT", "snapshot schema unsupported")

    all_by_id = _resolution_by_id(directory)
    ids = tuple(str(x) for x in stored_manifest.get("active_resolution_ids") or ())
    try:
        selected = tuple(all_by_id[item_id] for item_id in ids)
    except KeyError as exc:
        raise ReviewError("P9_ARTIFACT_INCOMPLETE_OR_CORRUPT", "snapshot resolution missing") from exc

    overlay_hash, facts, issues, report, generated_manifest = _generate(directory, selected)
    if overlay_hash != snapshot.name or overlay_hash != stored_manifest.get("overlay_set_hash"):
        raise ReviewError("P9_ARTIFACT_INCOMPLETE_OR_CORRUPT", "snapshot overlay_set_hash mismatch")
    files = _snapshot_bytes(facts, issues, report, generated_manifest)
    _validate_existing_snapshot(snapshot, files)
    return _snapshot_object(snapshot, report)


def build_resolved_parsed_data_record(
    snapshot: ResolvedSnapshot,
    slot: FilingSlotKey,
    artifact_path: str,
) -> ParsedDataRecord:
    report = snapshot.report
    document_sha256 = str(report["document_sha256"])
    if not artifact_path:
        raise ValueError("artifact_path must not be empty")
    versions = report.get("versions") or {}
    aggregate = "|".join(
        str(versions.get(key) or "unknown")
        for key in (
            "p3_parser_version",
            "p5_reconstruction_version",
            "p6_extractor_version",
            "p7_policy_version",
        )
    )
    parser_version = aggregate + "|" + P9_VERSION
    parse_run_id = sha256_bytes(
        (
            document_sha256
            + "\0"
            + str(versions.get("p7_policy_version") or "unknown")
            + "\0"
            + snapshot.overlay_set_hash
            + "\0"
            + REVIEW_POLICY_VERSION
        ).encode("utf-8")
    )
    return ParsedDataRecord(
        parse_run_id=parse_run_id,
        slot=slot,
        document_sha256=document_sha256,
        parser_version=parser_version,
        schema_version=RESOLVED_VIEW_SCHEMA_VERSION,
        validation_status=ValidationStatus(str(report["resolved_validation_status"])),
        blocking_issue_count=int(report.get("base_blocking_issue_count") or 0),
        compatibility_status=CompatibilityStatus(str(report["base_compatibility_status"])),
        artifact_path=artifact_path,
    )
