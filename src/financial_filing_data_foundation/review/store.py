from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping, Sequence

from .evidence import (
    active_effective_assignments,
    build_before_after,
    build_indexes,
    resolve_target,
    validate_direct_evidence,
    validate_resolution_history,
    validate_reviewer,
)
from .models import (
    RESOLUTION_SCHEMA_VERSION,
    REVIEW_POLICY_VERSION,
    ResolutionAction,
    ResolutionSubmission,
    ReviewError,
    ReviewResolution,
    canonical_json_bytes,
    sha256_bytes,
)
from .queue import load_review_base


def _resolution_bytes(resolution: ReviewResolution) -> bytes:
    return canonical_json_bytes(resolution.to_dict()) + b"\n"


def _overlay_hash_before(
    document_sha256: str,
    base_validation_report_sha256: str,
    active_ids: Sequence[str],
) -> str:
    ordered = tuple(sorted(str(item) for item in active_ids))
    material = (
        document_sha256
        + "\0"
        + base_validation_report_sha256
        + "\0"
        + REVIEW_POLICY_VERSION
        + "\0"
        + "\0".join(ordered)
    )
    return sha256_bytes(material.encode("utf-8"))


def _validate_prior_state_contract(resolutions: Sequence[ReviewResolution]) -> None:
    by_id = {item.resolution_id: item for item in resolutions}
    dependencies: dict[str, set[str]] = {}
    for item in resolutions:
        prior = tuple(item.base_active_resolution_ids)
        if prior != tuple(sorted(set(prior))):
            raise ReviewError(
                "P9_RESOLUTION_STORE_CORRUPT",
                "base_active_resolution_ids must be sorted and unique",
            )
        if item.resolution_id in prior:
            raise ReviewError(
                "P9_RESOLUTION_STORE_CORRUPT",
                "resolution cannot appear in its own prior active set",
            )
        missing = [resolution_id for resolution_id in prior if resolution_id not in by_id]
        if missing:
            raise ReviewError(
                "P9_RESOLUTION_STORE_CORRUPT",
                "prior active resolution is missing: " + ",".join(missing),
            )
        expected_hash = _overlay_hash_before(
            item.document_sha256,
            item.base_validation_report_sha256,
            prior,
        )
        if item.base_overlay_set_hash_before != expected_hash:
            raise ReviewError(
                "P9_RESOLUTION_STORE_CORRUPT",
                "base_overlay_set_hash_before mismatch",
            )
        prior_set = set(prior)
        for prior_id in prior:
            parent = by_id[prior_id].supersedes_resolution_id
            if parent is not None and parent in prior_set:
                raise ReviewError(
                    "P9_RESOLUTION_STORE_CORRUPT",
                    "prior active set contains both superseding child and parent",
                )
        if (
            item.supersedes_resolution_id is not None
            and item.supersedes_resolution_id not in prior_set
        ):
            raise ReviewError(
                "P9_SUPERSESSION_INVALID",
                "superseded parent was not active in resolution prior state",
            )
        for support_id in item.supporting_resolution_ids:
            if support_id not in prior_set:
                raise ReviewError(
                    "P9_RESOLUTION_STORE_CORRUPT",
                    "attestation support was not active in prior state",
                )
        dependencies[item.resolution_id] = set(prior)

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            raise ReviewError(
                "P9_RESOLUTION_STORE_CORRUPT",
                "prior-state dependency cycle detected",
            )
        if node in visited:
            return
        visiting.add(node)
        for dep in dependencies.get(node, set()):
            visit(dep)
        visiting.remove(node)
        visited.add(node)

    for resolution_id in sorted(dependencies):
        visit(resolution_id)


def _read_resolution_file(path: Path) -> ReviewResolution:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReviewError(
            "P9_RESOLUTION_STORE_CORRUPT",
            f"cannot read resolution {path}: {exc}",
        ) from exc
    if not isinstance(raw, dict):
        raise ReviewError("P9_RESOLUTION_STORE_CORRUPT", f"resolution root invalid: {path}")
    try:
        resolution = ReviewResolution.from_dict(raw)
    except ReviewError as exc:
        raise ReviewError("P9_RESOLUTION_STORE_CORRUPT", str(exc)) from exc
    if path.stem != resolution.resolution_id:
        raise ReviewError(
            "P9_RESOLUTION_STORE_CORRUPT",
            f"resolution filename/id mismatch: {path.name}",
        )
    expected_id = sha256_bytes(
        canonical_json_bytes(resolution.to_dict(include_id=False))
    )
    if resolution.resolution_id != expected_id:
        raise ReviewError(
            "P9_RESOLUTION_STORE_CORRUPT",
            f"resolution ID does not match canonical payload: {path.name}",
        )
    if path.read_bytes() != _resolution_bytes(resolution):
        raise ReviewError(
            "P9_RESOLUTION_STORE_CORRUPT",
            f"resolution file is not canonical: {path.name}",
        )
    return resolution


def list_resolutions(review_dir: str | Path) -> tuple[ReviewResolution, ...]:
    directory = Path(review_dir).expanduser().resolve()
    resolution_dir = directory / "resolutions"
    if not resolution_dir.is_dir():
        raise ReviewError("P9_ARTIFACT_INCOMPLETE_OR_CORRUPT", "resolutions directory missing")
    resolutions = tuple(
        _read_resolution_file(path)
        for path in sorted(resolution_dir.glob("*.json"), key=lambda item: item.name)
    )
    ids = [item.resolution_id for item in resolutions]
    if len(ids) != len(set(ids)):
        raise ReviewError("P9_RESOLUTION_STORE_CORRUPT", "duplicate resolution_id")
    _validate_graph(resolutions)
    _, bundle, tasks = load_review_base(directory)
    indexes = build_indexes(bundle, tasks)
    validate_resolution_history(indexes, resolutions)
    return resolutions


def _validate_graph(resolutions: Sequence[ReviewResolution]) -> tuple[ReviewResolution, ...]:
    _validate_prior_state_contract(resolutions)
    by_id = {item.resolution_id: item for item in resolutions}
    children: dict[str, list[str]] = {}
    for item in resolutions:
        parent_id = item.supersedes_resolution_id
        if parent_id is None:
            continue
        parent = by_id.get(parent_id)
        if parent is None:
            raise ReviewError(
                "P9_SUPERSESSION_INVALID",
                f"superseded resolution does not exist: {parent_id}",
            )
        if parent.document_sha256 != item.document_sha256:
            raise ReviewError("P9_SUPERSESSION_INVALID", "supersession crosses document")
        if parent.review_task_id != item.review_task_id or parent.issue_id != item.issue_id:
            raise ReviewError("P9_SUPERSESSION_INVALID", "supersession crosses review task/issue")
        if parent.action is not item.action:
            raise ReviewError("P9_SUPERSESSION_INVALID", "supersession action family changed")
        if parent.target != item.target:
            raise ReviewError("P9_SUPERSESSION_INVALID", "supersession target changed")
        children.setdefault(parent_id, []).append(item.resolution_id)

    competing = {parent: ids for parent, ids in children.items() if len(ids) > 1}
    if competing:
        raise ReviewError(
            "P9_RESOLUTION_CONFLICT",
            "multiple active children supersede one resolution: " + repr(competing),
        )

    for start in by_id:
        seen: set[str] = set()
        current = start
        while current in children:
            if current in seen:
                raise ReviewError("P9_SUPERSESSION_INVALID", "supersession cycle detected")
            seen.add(current)
            current = children[current][0]
            if current == start:
                raise ReviewError("P9_SUPERSESSION_INVALID", "supersession cycle detected")

    superseded = set(children)
    active = [item for item in resolutions if item.resolution_id not in superseded]
    active.sort(key=lambda item: item.resolution_id)
    return tuple(active)


def active_resolutions(review_dir: str | Path) -> tuple[ReviewResolution, ...]:
    return _validate_graph(list_resolutions(review_dir))


def _canonical_inherited_evidence(
    supporting: Sequence[ReviewResolution],
) -> tuple[tuple[dict[str, Any], ...], tuple[int, ...]]:
    refs_by_key: dict[bytes, dict[str, Any]] = {}
    pages: set[int] = set()
    for item in supporting:
        if not item.evidence_refs:
            raise ReviewError("P9_EVIDENCE_INVALID", "supporting resolution has no evidence")
        for ref in item.evidence_refs:
            refs_by_key[canonical_json_bytes(ref)] = dict(ref)
        pages.update(int(page) for page in item.evidence_pages)
    if not refs_by_key:
        raise ReviewError("P9_EVIDENCE_INVALID", "supporting evidence union is empty")
    refs = tuple(refs_by_key[key] for key in sorted(refs_by_key))
    return refs, tuple(sorted(pages))


def _write_resolution(path: Path, resolution: ReviewResolution) -> None:
    data = _resolution_bytes(resolution)
    try:
        with path.open("xb") as handle:
            handle.write(data)
    except FileExistsError:
        try:
            existing = path.read_bytes()
        except OSError as exc:
            raise ReviewError("P9_RESOLUTION_STORE_CORRUPT", str(exc)) from exc
        if existing != data:
            raise ReviewError(
                "P9_RESOLUTION_STORE_CORRUPT",
                f"existing resolution bytes differ for {resolution.resolution_id}",
            )
        return
    except OSError as exc:
        raise ReviewError("P9_PERSIST_FAILED", f"cannot persist resolution: {exc}") from exc


def submit_resolution(
    review_dir: str | Path,
    submission: ResolutionSubmission | Mapping[str, Any],
) -> ReviewResolution:
    directory = Path(review_dir).expanduser().resolve()
    if not isinstance(submission, ResolutionSubmission):
        submission = ResolutionSubmission.from_dict(submission)
    validate_reviewer(submission)

    manifest, bundle, tasks = load_review_base(directory)
    indexes = build_indexes(bundle, tasks)
    task = indexes.task_by_id.get(submission.review_task_id)
    if task is None:
        raise ReviewError("P9_TASK_NOT_FOUND", f"review task not found: {submission.review_task_id}")
    if task.document_sha256 != bundle.document_sha256:
        raise ReviewError("P9_TASK_NOT_FOUND", "review task belongs to another document")

    existing = list_resolutions(directory)
    active = _validate_graph(existing)
    base_active_ids = tuple(sorted(item.resolution_id for item in active))
    base_overlay_hash = _overlay_hash_before(
        bundle.document_sha256,
        str(manifest["base_validation_report_sha256"]),
        base_active_ids,
    )
    current_effective = active_effective_assignments(active)
    selection = resolve_target(indexes, task, submission, current_effective)

    if submission.action is ResolutionAction.ATTEST_ISSUE_RESOLVED:
        if submission.evidence_refs:
            raise ReviewError(
                "P9_EVIDENCE_INVALID",
                "attestation caller must not submit direct evidence",
            )
        if submission.evidence_pages not in (None, ()):
            raise ReviewError(
                "P9_EVIDENCE_INVALID",
                "attestation caller must not submit evidence_pages",
            )
        if not submission.supporting_resolution_ids:
            raise ReviewError(
                "P9_INVALID_RESOLUTION",
                "attestation requires supporting_resolution_ids",
            )
        active_by_id = {item.resolution_id: item for item in active}
        support: list[ReviewResolution] = []
        for support_id in submission.supporting_resolution_ids:
            item = active_by_id.get(support_id)
            if item is None:
                raise ReviewError(
                    "P9_INVALID_RESOLUTION",
                    f"supporting resolution is not active: {support_id}",
                )
            if item.review_task_id != task.review_task_id or item.issue_id != task.issue_id:
                raise ReviewError(
                    "P9_INVALID_RESOLUTION",
                    "supporting resolution belongs to another issue",
                )
            if item.action is ResolutionAction.ATTEST_ISSUE_RESOLVED:
                raise ReviewError(
                    "P9_INVALID_RESOLUTION",
                    "attestation cannot use another attestation as evidence support",
                )
            support.append(item)
        evidence_refs, evidence_pages = _canonical_inherited_evidence(support)
        before = {
            "target": selection.target,
            "base_observed": dict(indexes.issue_by_id[task.issue_id].get("observed") or {}),
            "supporting_resolution_ids": sorted(item.resolution_id for item in support),
        }
        after = {
            "value": "RESOLVED",
            "expected_observed_count": int(selection.target["expected_observed_count"]),
        }
    else:
        if submission.supporting_resolution_ids:
            raise ReviewError(
                "P9_INVALID_RESOLUTION",
                "supporting_resolution_ids are only valid for attestation",
            )
        evidence_refs, evidence_pages = validate_direct_evidence(indexes, selection, submission)
        before, after = build_before_after(selection)

    if submission.supersedes_resolution_id is not None:
        by_id = {item.resolution_id: item for item in existing}
        parent = by_id.get(submission.supersedes_resolution_id)
        if parent is None:
            raise ReviewError("P9_SUPERSESSION_INVALID", "supersedes_resolution_id not found")
        if parent.resolution_id not in {item.resolution_id for item in active}:
            raise ReviewError("P9_SUPERSESSION_INVALID", "can only supersede an active terminal resolution")
        if parent.review_task_id != task.review_task_id or parent.issue_id != task.issue_id:
            raise ReviewError("P9_SUPERSESSION_INVALID", "supersession crosses task/issue")
        if parent.action is not submission.action or parent.target != selection.target:
            raise ReviewError("P9_SUPERSESSION_INVALID", "supersession target/action family changed")

    reviewer_id = submission.reviewer_id.strip()
    justification = submission.justification
    supporting_ids = tuple(sorted(set(submission.supporting_resolution_ids)))
    provisional = ReviewResolution(
        resolution_id="",
        document_sha256=bundle.document_sha256,
        base_validation_report_sha256=str(manifest["base_validation_report_sha256"]),
        review_task_id=task.review_task_id,
        issue_id=task.issue_id,
        reason_code=task.reason_code,
        action=submission.action,
        target=selection.target,
        value=selection.submitted_value,
        evidence_refs=evidence_refs,
        evidence_pages=evidence_pages,
        before=before,
        after=after,
        reviewer_type=submission.reviewer_type,
        reviewer_id=reviewer_id,
        reviewed_at=submission.reviewed_at,
        justification=justification,
        base_active_resolution_ids=base_active_ids,
        base_overlay_set_hash_before=base_overlay_hash,
        supersedes_resolution_id=submission.supersedes_resolution_id,
        supporting_resolution_ids=supporting_ids,
        expected_observed_count=(
            int(selection.target["expected_observed_count"])
            if submission.action is ResolutionAction.ATTEST_ISSUE_RESOLVED
            else submission.expected_observed_count
        ),
    )
    resolution_id = sha256_bytes(canonical_json_bytes(provisional.to_dict(include_id=False)))
    resolution = ReviewResolution(
        resolution_id=resolution_id,
        document_sha256=provisional.document_sha256,
        base_validation_report_sha256=provisional.base_validation_report_sha256,
        review_task_id=provisional.review_task_id,
        issue_id=provisional.issue_id,
        reason_code=provisional.reason_code,
        action=provisional.action,
        target=provisional.target,
        value=provisional.value,
        evidence_refs=provisional.evidence_refs,
        evidence_pages=provisional.evidence_pages,
        before=provisional.before,
        after=provisional.after,
        reviewer_type=provisional.reviewer_type,
        reviewer_id=provisional.reviewer_id,
        reviewed_at=provisional.reviewed_at,
        justification=provisional.justification,
        base_active_resolution_ids=provisional.base_active_resolution_ids,
        base_overlay_set_hash_before=provisional.base_overlay_set_hash_before,
        supersedes_resolution_id=provisional.supersedes_resolution_id,
        supporting_resolution_ids=provisional.supporting_resolution_ids,
        expected_observed_count=provisional.expected_observed_count,
    )

    candidate_set = tuple(existing) + (resolution,)
    _validate_graph(candidate_set)

    resolution_dir = directory / "resolutions"
    if not resolution_dir.is_dir():
        raise ReviewError("P9_ARTIFACT_INCOMPLETE_OR_CORRUPT", "resolutions directory missing")
    _write_resolution(resolution_dir / f"{resolution.resolution_id}.json", resolution)
    return resolution
