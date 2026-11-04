from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping, Sequence

from .models import (
    ResolutionAction,
    ResolutionSubmission,
    ReviewError,
    ReviewResolution,
    ReviewerType,
    ReviewTask,
    TargetType,
)
from .queue import ReviewBaseBundle, _BaseContext


_ACTION_FIELD: dict[ResolutionAction, str] = {
    ResolutionAction.SET_PERIOD: "period",
    ResolutionAction.SET_UNIT: "unit",
    ResolutionAction.SET_SCOPE: "scope",
}


@dataclass(frozen=True, slots=True)
class TargetSelection:
    action: str
    target_type: str
    target: dict[str, Any]
    field: str | None
    raw_field: str | None
    table_id: str | None
    column_index: int | None
    selected_fact_ids: tuple[str, ...]
    affected_fact_ids: tuple[str, ...]
    already_explicit_fact_ids: tuple[str, ...]
    normalized_value: str | None
    submitted_value: str | None
    base_raw_values: dict[str, Any]
    current_effective_values: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ReviewIndexes:
    context: _BaseContext
    task_by_id: dict[str, ReviewTask]
    issue_by_id: dict[str, dict[str, Any]]


def _context_of(value: _BaseContext | ReviewIndexes | ReviewBaseBundle) -> _BaseContext:
    if isinstance(value, _BaseContext):
        return value
    if isinstance(value, ReviewIndexes):
        return value.context
    return value.context


def normalize_semantic(value: str) -> str:
    return " ".join(value.strip().split())


_SQL_IDENTIFIER = (
    r'(?:[A-Za-z_][A-Za-z0-9_$]*|'
    r'`[^`\r\n]+`|'
    r'"[^"\r\n]+"|'
    r'\[[^\]\r\n]+\])'
)
_SQL_OBJECT = rf"(?:{_SQL_IDENTIFIER})(?:\.(?:{_SQL_IDENTIFIER}))*"
_SQL_PROJECTION_ITEM = (
    rf"(?:\*|{_SQL_OBJECT}(?:\.\*)?|"
    rf"[A-Za-z_][A-Za-z0-9_$]*\([^()\r\n]{{0,120}}\))"
)
_SQL_PROJECTION = (
    rf"(?:distinct\s+)?{_SQL_PROJECTION_ITEM}"
    rf"(?:\s*,\s*{_SQL_PROJECTION_ITEM})*"
)
_SQL_TERMINATOR = (
    r"(?=\s*(?:$|;|"
    r"\b(?:where|join|group\s+by|order\s+by|having|limit|offset|union)\b))"
)

_FORBIDDEN_RESOLUTION_TEXT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:https?|ftp|file|ssh)://|\bwww\.", re.IGNORECASE),
    re.compile(
        r"(?<![A-Za-z0-9])(?:[A-Za-z]:[\\/]|\\\\[^\\\s]+\\[^\\\s]+)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?<![A-Za-z0-9_:])/[A-Za-z0-9._~-]+(?:/[A-Za-z0-9._~-]+)*"
    ),
    re.compile(r"(?:^|[\\/])\.\.(?:[\\/]|$)"),
    re.compile(
        r"(?:^|[\r\n;&|])\s*(?:"
        r"cmd(?:\.exe)?\s+/[ck]\b|"
        r"powershell(?:\.exe)?(?=\s|$|[\r\n;&|])|"
        r"pwsh(?:\.exe)?(?=\s|$|[\r\n;&|])|"
        r"bash(?:\.exe)?(?=\s|$|[\r\n;&|])|"
        r"sh\s+-c\b|"
        r"invoke-expression\b|"
        r"rm\s+-rf\b|"
        r"del\s+/[qsf]\b|"
        r"curl(?:\.exe)?(?=\s|$|[\r\n;&|])|"
        r"wget(?:\.exe)?(?=\s|$|[\r\n;&|])"
        r")",
        re.IGNORECASE | re.MULTILINE,
    ),
    re.compile(
        rf"\bselect\s+{_SQL_PROJECTION}\s+from\s+{_SQL_OBJECT}{_SQL_TERMINATOR}",
        re.IGNORECASE,
    ),
    re.compile(rf"\binsert\s+into\s+{_SQL_OBJECT}\b", re.IGNORECASE),
    re.compile(
        rf"\bupdate\s+{_SQL_OBJECT}\s+set\s+{_SQL_IDENTIFIER}\s*=",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\bdelete\s+from\s+{_SQL_OBJECT}{_SQL_TERMINATOR}",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b(?:drop|alter|create)\s+table\s+{_SQL_OBJECT}\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bunion\s+select\b|\bpragma\b", re.IGNORECASE),
    re.compile(
        r"(?:^|\n)\s*(?:"
        r"import\s+[A-Za-z_]|"
        r"from\s+[A-Za-z_][\w.]*\s+import\s+|"
        r"def\s+[A-Za-z_]\w*\s*\(|"
        r"class\s+[A-Za-z_]\w*\s*[:(]"
        r")|"
        r"\b(?:__import__|exec|eval|print)\s*\(|"
        r"\b(?:os|" r"sub" r"process)\.[A-Za-z_]\w*\s*\(",
        re.IGNORECASE | re.MULTILINE,
    ),
    re.compile(
        r"\b(?:password|passwd|secret|token|api[_-]?key|access[_-]?key|private[_-]?key)"
        r"\s*[:=]\s*\S+|\bbearer\s+[A-Za-z0-9._~+/=-]{8,}",
        re.IGNORECASE,
    ),
)


def _iter_string_leaves(value: Any):
    if isinstance(value, str):
        yield value
        return
    if isinstance(value, Mapping):
        for item in value.values():
            yield from _iter_string_leaves(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            yield from _iter_string_leaves(item)


def validate_resolution_payload_security(payload: Any) -> None:
    for text in _iter_string_leaves(payload):
        if any(pattern.search(text) for pattern in _FORBIDDEN_RESOLUTION_TEXT_PATTERNS):
            raise ReviewError(
                "P9_RESOLUTION_CONTENT_FORBIDDEN",
                "resolution payload contains forbidden content",
            )


def _trimmed_text(value: Any, label: str, max_len: int = 256) -> str:
    if not isinstance(value, str):
        raise ReviewError("P9_INVALID_RESOLUTION", f"{label} must be a string")
    trimmed = value.strip()
    if not trimmed or len(trimmed) > max_len:
        raise ReviewError(
            "P9_INVALID_RESOLUTION",
            f"{label} must contain 1..{max_len} non-whitespace characters",
        )
    return trimmed


def _required_text(value: Any, label: str, max_len: int = 256) -> str:
    if not isinstance(value, str):
        raise ReviewError("P9_INVALID_RESOLUTION", f"{label} must be a string")
    normalized = normalize_semantic(value)
    if not normalized or len(normalized) > max_len:
        raise ReviewError(
            "P9_INVALID_RESOLUTION",
            f"{label} must contain 1..{max_len} non-whitespace characters",
        )
    return normalized


def _fact(context: _BaseContext | ReviewIndexes | ReviewBaseBundle, raw_fact_id: Any) -> dict[str, Any]:
    base = _context_of(context)
    fact_id = _required_text(raw_fact_id, "raw_fact_id")
    fact = base.fact_by_id.get(fact_id)
    if fact is None:
        raise ReviewError("P9_TARGET_NOT_FOUND", f"raw fact not found: {fact_id}")
    return fact


def _table(context: _BaseContext | ReviewIndexes | ReviewBaseBundle, table_id_raw: Any) -> dict[str, Any]:
    base = _context_of(context)
    table_id = _required_text(table_id_raw, "table_id")
    table = base.table_by_id.get(table_id)
    if table is None:
        raise ReviewError("P9_TARGET_NOT_FOUND", f"table not found: {table_id}")
    return table


def _target_facts_for_table(context: _BaseContext | ReviewIndexes | ReviewBaseBundle, table_id: str) -> list[dict[str, Any]]:
    base = _context_of(context)
    return [
        fact
        for fact in base.facts
        if str(fact.get("table_id") or "") == table_id
    ]


def _fill_selection(
    context: _BaseContext | ReviewIndexes | ReviewBaseBundle,
    action: ResolutionAction,
    target: dict[str, Any],
    value: str,
    current_effective: Mapping[tuple[str, str], str] | None = None,
) -> TargetSelection:
    if action == ResolutionAction.SET_PERIOD:
        field = "period"
        raw_field = "raw_period_label"
        allowed = {TargetType.FACT_FIELD, TargetType.TABLE_COLUMN_FIELD}
    elif action == ResolutionAction.SET_UNIT:
        field = "unit"
        raw_field = "raw_unit"
        allowed = {TargetType.FACT_FIELD, TargetType.TABLE_FIELD}
    elif action == ResolutionAction.SET_SCOPE:
        field = "scope"
        raw_field = "raw_scope"
        allowed = {TargetType.FACT_FIELD, TargetType.TABLE_FIELD}
    else:
        raise ReviewError("P9_INVALID_RESOLUTION", f"unsupported fill action: {action}")

    try:
        target_type = TargetType(str(target.get("target_type") or ""))
    except ValueError as exc:
        raise ReviewError("P9_INVALID_RESOLUTION", "invalid target_type") from exc
    if target_type not in allowed:
        raise ReviewError(
            "P9_INVALID_RESOLUTION",
            f"{action.value} does not support target_type={target_type.value}",
        )
    target_field = str(target.get("field") or "")
    if target_field != field:
        raise ReviewError(
            "P9_INVALID_RESOLUTION",
            f"target field must be {field!r} for {action.value}",
        )

    table_id: str
    column_index: int | None = None
    facts: list[dict[str, Any]]
    normalized_target: dict[str, Any]

    if target_type == TargetType.FACT_FIELD:
        fact = _fact(context, target.get("raw_fact_id"))
        table_id = str(fact["table_id"])
        facts = [fact]
        normalized_target = {
            "target_type": target_type.value,
            "raw_fact_id": str(fact["raw_fact_id"]),
            "field": field,
        }
    elif target_type == TargetType.TABLE_COLUMN_FIELD:
        table = _table(context, target.get("table_id"))
        table_id = str(table["table_id"])
        raw_column = target.get("column_index")
        if isinstance(raw_column, bool) or not isinstance(raw_column, int) or raw_column < 0:
            raise ReviewError(
                "P9_INVALID_RESOLUTION",
                "column_index must be a non-negative integer",
            )
        column_index = int(raw_column)
        facts = [
            fact
            for fact in _target_facts_for_table(context, table_id)
            if int(fact.get("column_index", -1)) == column_index
        ]
        if not facts:
            raise ReviewError(
                "P9_TARGET_NOT_FOUND",
                f"no facts found for table={table_id} column={column_index}",
            )
        normalized_target = {
            "target_type": target_type.value,
            "table_id": table_id,
            "column_index": column_index,
            "field": field,
        }
    else:
        table = _table(context, target.get("table_id"))
        table_id = str(table["table_id"])
        facts = _target_facts_for_table(context, table_id)
        if not facts:
            raise ReviewError(
                "P9_TARGET_NOT_FOUND",
                f"no facts found for table={table_id}",
            )
        normalized_target = {
            "target_type": target_type.value,
            "table_id": table_id,
            "field": field,
        }

    affected: list[str] = []
    explicit: list[str] = []
    submitted = value.strip()
    wanted = normalize_semantic(submitted)
    effective = current_effective or {}
    base_raw_values: dict[str, Any] = {}
    current_effective_values: dict[str, Any] = {}
    for fact in facts:
        fact_id = str(fact["raw_fact_id"])
        base_raw_values[fact_id] = fact.get(raw_field)
        current_effective_values[fact_id] = effective.get((fact_id, field))

        fact_id = str(fact["raw_fact_id"])
        raw = fact.get(raw_field)
        if raw is None:
            affected.append(fact_id)
            continue
        raw_normalized = normalize_semantic(str(raw))
        if raw_normalized == wanted:
            explicit.append(fact_id)
            continue
        raise ReviewError(
            "P9_PATCH_CONFLICTS_WITH_RAW",
            f"{action.value} conflicts with explicit {raw_field} on fact {fact_id}",
        )

    if not affected:
        raise ReviewError(
            "P9_RESOLUTION_NO_EFFECT",
            f"{action.value} target has no null {raw_field} facts",
        )
    return TargetSelection(
        action=action.value,
        target_type=target_type.value,
        target=normalized_target,
        field=field,
        raw_field=raw_field,
        table_id=table_id,
        column_index=column_index,
        selected_fact_ids=tuple(sorted(str(row["raw_fact_id"]) for row in facts)),
        affected_fact_ids=tuple(sorted(affected)),
        already_explicit_fact_ids=tuple(sorted(explicit)),
        normalized_value=wanted,
        submitted_value=submitted,
        base_raw_values={key: base_raw_values[key] for key in sorted(base_raw_values)},
        current_effective_values={
            key: current_effective_values[key] for key in sorted(current_effective_values)
        },
    )


def resolve_target(
    indexes: ReviewIndexes | _BaseContext | ReviewBaseBundle,
    task_or_action: ReviewTask | ResolutionAction | str,
    submission_or_target: ResolutionSubmission | dict[str, Any],
    current_effective_or_value: Mapping[tuple[str, str], str] | str | None = None,
) -> TargetSelection:
    context = _context_of(indexes)
    task: ReviewTask | None
    if isinstance(submission_or_target, ResolutionSubmission):
        submission = submission_or_target
        action = submission.action
        target = submission.target
        value = submission.value
        current_effective = (
            current_effective_or_value
            if isinstance(current_effective_or_value, Mapping)
            else {}
        )
        task = task_or_action if isinstance(task_or_action, ReviewTask) else None
        if task is not None and action.value not in task.supported_actions:
            raise ReviewError(
                "P9_INVALID_RESOLUTION",
                f"{action.value} is not supported for review task {task.review_task_id}",
            )
    else:
        task = None
        try:
            action = (
                task_or_action
                if isinstance(task_or_action, ResolutionAction)
                else ResolutionAction(str(task_or_action))
            )
        except ValueError as exc:
            raise ReviewError(
                "P9_INVALID_RESOLUTION",
                f"unknown action: {task_or_action}",
            ) from exc
        target = dict(submission_or_target)
        value = (
            current_effective_or_value
            if isinstance(current_effective_or_value, str)
            else None
        )
        current_effective = {}

    if action in {
        ResolutionAction.SET_PERIOD,
        ResolutionAction.SET_UNIT,
        ResolutionAction.SET_SCOPE,
    }:
        text = _trimmed_text(value, "value") if value is not None else ""
        if not text:
            raise ReviewError("P9_INVALID_RESOLUTION", "fill action requires value")
        return _fill_selection(
            context,
            action,
            target,
            text,
            current_effective=current_effective,
        )

    if action == ResolutionAction.CLASSIFY_TABLE_STATEMENT:
        try:
            target_type = TargetType(str(target.get("target_type") or ""))
        except ValueError as exc:
            raise ReviewError("P9_INVALID_RESOLUTION", "invalid target_type") from exc
        if target_type != TargetType.TABLE_STATEMENT_CLASS:
            raise ReviewError(
                "P9_INVALID_RESOLUTION",
                "CLASSIFY_TABLE_STATEMENT requires TABLE_STATEMENT_CLASS target",
            )
        table = _table(context, target.get("table_id"))
        table_id = str(table["table_id"])
        classification = _required_text(value, "value").upper()
        if classification not in {"BALANCE", "INCOME", "CASHFLOW", "OTHER"}:
            raise ReviewError(
                "P9_INVALID_RESOLUTION",
                "statement class must be BALANCE/INCOME/CASHFLOW/OTHER",
            )
        fact_ids = tuple(
            sorted(
                str(row["raw_fact_id"])
                for row in _target_facts_for_table(context, table_id)
            )
        )
        current_statement = current_effective.get((table_id, "statement_class"))
        return TargetSelection(
            action=action.value,
            target_type=target_type.value,
            target={"target_type": target_type.value, "table_id": table_id},
            field="statement_class",
            raw_field=None,
            table_id=table_id,
            column_index=None,
            selected_fact_ids=fact_ids,
            affected_fact_ids=fact_ids,
            already_explicit_fact_ids=(),
            normalized_value=classification,
            submitted_value=classification,
            base_raw_values={},
            current_effective_values={"statement_class": current_statement},
        )

    if action == ResolutionAction.ATTEST_ISSUE_RESOLVED:
        try:
            target_type = TargetType(str(target.get("target_type") or ""))
        except ValueError as exc:
            raise ReviewError("P9_INVALID_RESOLUTION", "invalid target_type") from exc
        if target_type != TargetType.ISSUE:
            raise ReviewError(
                "P9_INVALID_RESOLUTION",
                "ATTEST_ISSUE_RESOLVED requires ISSUE target",
            )
        issue_id = _required_text(target.get("issue_id"), "issue_id")
        if task is not None and issue_id != task.issue_id:
            raise ReviewError(
                "P9_INVALID_RESOLUTION",
                "attestation issue_id must match review task",
            )
        expected = target.get("expected_observed_count")
        if expected is None and isinstance(submission_or_target, ResolutionSubmission):
            expected = submission_or_target.expected_observed_count
        if isinstance(expected, bool) or not isinstance(expected, int) or expected < 0:
            raise ReviewError(
                "P9_INVALID_RESOLUTION",
                "expected_observed_count must be a non-negative integer",
            )
        if (
            isinstance(submission_or_target, ResolutionSubmission)
            and submission_or_target.expected_observed_count is not None
            and submission_or_target.expected_observed_count != expected
        ):
            raise ReviewError(
                "P9_INVALID_RESOLUTION",
                "expected_observed_count differs between target and submission",
            )
        if task is not None:
            base_count = task.observed.get("count")
            if (
                isinstance(base_count, bool)
                or not isinstance(base_count, int)
                or base_count < 0
                or int(expected) != int(base_count)
            ):
                raise ReviewError(
                    "P9_INVALID_RESOLUTION",
                    "expected_observed_count differs from base issue observed.count",
                )
        return TargetSelection(
            action=action.value,
            target_type=target_type.value,
            target={
                "target_type": target_type.value,
                "issue_id": issue_id,
                "expected_observed_count": int(expected),
            },
            field=None,
            raw_field=None,
            table_id=None,
            column_index=None,
            selected_fact_ids=(),
            affected_fact_ids=(),
            already_explicit_fact_ids=(),
            normalized_value="RESOLVED",
            submitted_value="RESOLVED",
            base_raw_values={},
            current_effective_values={},
        )

    raise ReviewError("P9_INVALID_RESOLUTION", f"unsupported action: {action.value}")


def _bbox_valid(value: Any) -> bool:
    if not isinstance(value, list) or len(value) != 4:
        return False
    try:
        values = [float(item) for item in value]
    except (TypeError, ValueError):
        return False
    return (
        all(math.isfinite(item) for item in values)
        and values[2] >= values[0]
        and values[3] >= values[1]
    )


def _evidence_sort_key(ref: dict[str, Any]) -> str:
    return json.dumps(ref, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def validate_direct_evidence(
    context: _BaseContext | ReviewIndexes | ReviewBaseBundle,
    selection: TargetSelection,
    submission_or_refs: ResolutionSubmission | tuple[dict[str, Any], ...],
) -> tuple[tuple[dict[str, Any], ...], tuple[int, ...]]:
    base = _context_of(context)
    refs = (
        submission_or_refs.evidence_refs
        if isinstance(submission_or_refs, ResolutionSubmission)
        else submission_or_refs
    )
    if not refs:
        raise ReviewError("P9_EVIDENCE_INVALID", "resolution requires evidence")

    normalized: dict[str, dict[str, Any]] = {}
    own_fact_evidence = False
    has_p5_cell = False
    pages: set[int] = set()

    for raw in refs:
        if not isinstance(raw, dict):
            raise ReviewError("P9_EVIDENCE_INVALID", "evidence ref must be an object")
        ref_type = str(raw.get("type") or "")
        if ref_type == "P6_EVIDENCE":
            evidence_id = _required_text(raw.get("evidence_id"), "evidence_id")
            evidence = base.evidence_by_id.get(evidence_id)
            if evidence is None:
                raise ReviewError(
                    "P9_EVIDENCE_INVALID",
                    f"P6 evidence not found: {evidence_id}",
                )
            table_id = str(evidence.get("table_id") or "")
            if selection.table_id is not None and table_id != selection.table_id:
                raise ReviewError(
                    "P9_EVIDENCE_INVALID",
                    "P6 evidence belongs to a different table",
                )
            page_no = int(evidence.get("page_no", 0) or 0)
            pages.add(page_no)
            normalized_ref = {"type": "P6_EVIDENCE", "evidence_id": evidence_id}
            normalized[_evidence_sort_key(normalized_ref)] = normalized_ref
            if selection.target_type == TargetType.FACT_FIELD.value:
                target_fact_id = str(selection.target.get("raw_fact_id") or "")
                target_fact = base.fact_by_id[target_fact_id]
                if str(target_fact.get("evidence_id") or "") == evidence_id:
                    own_fact_evidence = True
        elif ref_type == "P5_CELL":
            table_id = _required_text(raw.get("table_id"), "table_id")
            cell_id = _required_text(raw.get("cell_id"), "cell_id")
            cell = base.cell_by_key.get((table_id, cell_id))
            if cell is None:
                raise ReviewError(
                    "P9_EVIDENCE_INVALID",
                    f"P5 cell not found: table={table_id} cell={cell_id}",
                )
            if selection.table_id is not None and table_id != selection.table_id:
                raise ReviewError(
                    "P9_EVIDENCE_INVALID",
                    "P5 cell belongs to a different table",
                )
            if not isinstance(cell.get("source_words"), list) or not cell.get("source_words"):
                raise ReviewError(
                    "P9_EVIDENCE_INVALID",
                    "P5 evidence cell has no source_words",
                )
            if not _bbox_valid(cell.get("bbox")):
                raise ReviewError(
                    "P9_EVIDENCE_INVALID",
                    "P5 evidence cell has invalid bbox",
                )
            page_no = int(cell.get("_page_no", 0) or 0)
            if page_no < 1:
                raise ReviewError("P9_EVIDENCE_INVALID", "P5 cell page is invalid")
            pages.add(page_no)
            normalized_ref = {
                "type": "P5_CELL",
                "table_id": table_id,
                "cell_id": cell_id,
            }
            normalized[_evidence_sort_key(normalized_ref)] = normalized_ref
            has_p5_cell = True
        else:
            raise ReviewError(
                "P9_EVIDENCE_INVALID",
                f"unsupported evidence ref type: {ref_type}",
            )

    result = [normalized[key] for key in sorted(normalized)]
    if selection.target_type == TargetType.FACT_FIELD.value:
        if not (own_fact_evidence or has_p5_cell):
            raise ReviewError(
                "P9_EVIDENCE_INVALID",
                "FACT_FIELD requires its own P6 evidence or a P5 cell in the same table",
            )
    elif selection.target_type == TargetType.TABLE_COLUMN_FIELD.value:
        if not has_p5_cell:
            raise ReviewError(
                "P9_EVIDENCE_INVALID",
                "TABLE_COLUMN_FIELD requires at least one P5 cell",
            )
    elif selection.target_type in {
        TargetType.TABLE_FIELD.value,
        TargetType.TABLE_STATEMENT_CLASS.value,
    }:
        if not result:
            raise ReviewError(
                "P9_EVIDENCE_INVALID",
                "table-scoped resolution requires table evidence",
            )

    derived_pages = tuple(sorted(pages))
    if isinstance(submission_or_refs, ResolutionSubmission):
        supplied_pages = submission_or_refs.evidence_pages
        if supplied_pages is not None and tuple(supplied_pages) != derived_pages:
            raise ReviewError(
                "P9_EVIDENCE_INVALID",
                "submitted evidence_pages differ from evidence-derived pages",
            )
    return tuple(result), derived_pages


def validate_resolution_semantics(
    resolution: ReviewResolution,
    indexes: ReviewIndexes,
    task: ReviewTask,
    all_by_id: Mapping[str, ReviewResolution],
) -> TargetSelection:
    context = indexes.context
    validate_resolution_payload_security(resolution.to_dict(include_id=False))
    if resolution.document_sha256 != str(context.document.document_sha256):
        raise ReviewError(
            "P9_ARTIFACT_INCOMPLETE_OR_CORRUPT",
            "resolution document identity mismatch",
        )
    if resolution.base_validation_report_sha256 != str(
        context.manifest["base_validation_report_sha256"]
    ):
        raise ReviewError(
            "P9_ARTIFACT_INCOMPLETE_OR_CORRUPT",
            "resolution base validation identity mismatch",
        )
    if resolution.review_task_id != task.review_task_id:
        raise ReviewError(
            "P9_ARTIFACT_INCOMPLETE_OR_CORRUPT",
            "resolution task identity mismatch",
        )
    if resolution.issue_id != task.issue_id or resolution.reason_code != task.reason_code:
        raise ReviewError(
            "P9_ARTIFACT_INCOMPLETE_OR_CORRUPT",
            "resolution issue/reason identity mismatch",
        )

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
            if (
                item.review_task_id != resolution.review_task_id
                or item.issue_id != resolution.issue_id
            ):
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
        if (
            expected_refs != resolution.evidence_refs
            or expected_pages != resolution.evidence_pages
        ):
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


def validate_resolution_history(
    indexes: ReviewIndexes,
    resolutions: Sequence[ReviewResolution],
) -> None:
    all_by_id = {item.resolution_id: item for item in resolutions}
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(resolution_id: str) -> None:
        if resolution_id in visiting:
            raise ReviewError(
                "P9_RESOLUTION_STORE_CORRUPT",
                "resolution semantic dependency cycle detected",
            )
        if resolution_id in visited:
            return
        resolution = all_by_id.get(resolution_id)
        if resolution is None:
            raise ReviewError(
                "P9_RESOLUTION_STORE_CORRUPT",
                f"resolution dependency is missing: {resolution_id}",
            )
        visiting.add(resolution_id)
        for prior_id in resolution.base_active_resolution_ids:
            visit(prior_id)
        task = indexes.task_by_id.get(resolution.review_task_id)
        if task is None:
            raise ReviewError(
                "P9_ARTIFACT_INCOMPLETE_OR_CORRUPT",
                f"resolution task is missing: {resolution.review_task_id}",
            )
        validate_resolution_semantics(resolution, indexes, task, all_by_id)
        visiting.remove(resolution_id)
        visited.add(resolution_id)

    for resolution_id in sorted(all_by_id):
        visit(resolution_id)


def build_indexes(
    bundle: ReviewBaseBundle,
    tasks: Sequence[ReviewTask | Mapping[str, Any]],
) -> ReviewIndexes:
    context = bundle.context
    typed_tasks = tuple(
        item if isinstance(item, ReviewTask) else ReviewTask.from_dict(item)
        for item in tasks
    )
    task_by_id = {item.review_task_id: item for item in typed_tasks}
    if len(task_by_id) != len(typed_tasks) or any(not key for key in task_by_id):
        raise ReviewError(
            "P9_ARTIFACT_INCOMPLETE_OR_CORRUPT",
            "review task IDs are missing or duplicated",
        )
    issue_by_id: dict[str, dict[str, Any]] = {}
    for issue in context.issues:
        issue_id = str(issue.get("issue_id") or "")
        if not issue_id or issue_id in issue_by_id:
            raise ReviewError(
                "P9_BASE_ARTIFACT_INVALID",
                "P7 issue IDs are missing or duplicated",
            )
        issue_by_id[issue_id] = issue
    for task in typed_tasks:
        issue = issue_by_id.get(task.issue_id)
        if issue is None:
            raise ReviewError(
                "P9_ARTIFACT_INCOMPLETE_OR_CORRUPT",
                f"review task issue is missing: {task.issue_id}",
            )
        if task.document_sha256 != bundle.document_sha256:
            raise ReviewError(
                "P9_ARTIFACT_INCOMPLETE_OR_CORRUPT",
                "review task document identity mismatch",
            )
        if task.reason_code != str(issue.get("reason_code") or ""):
            raise ReviewError(
                "P9_ARTIFACT_INCOMPLETE_OR_CORRUPT",
                "review task reason differs from P7 issue",
            )
    return ReviewIndexes(
        context=context,
        task_by_id=task_by_id,
        issue_by_id=issue_by_id,
    )


def validate_reviewer(submission: ResolutionSubmission) -> None:
    reviewer_id = normalize_semantic(submission.reviewer_id)
    if not reviewer_id or len(reviewer_id) > 128:
        raise ReviewError(
            "P9_INVALID_RESOLUTION",
            "reviewer_id must contain 1..128 non-whitespace characters",
        )
    lowered = reviewer_id.lower()
    if any(marker in lowered for marker in ("password=", "secret=", "token=")):
        raise ReviewError(
            "P9_INVALID_RESOLUTION",
            "reviewer_id must not contain secret material",
        )
    justification = submission.justification
    if (
        not isinstance(justification, str)
        or not justification.strip()
        or len(justification) > 4000
    ):
        raise ReviewError(
            "P9_INVALID_RESOLUTION",
            "justification must contain 1..4000 raw characters and non-whitespace text",
        )
    text = submission.reviewed_at.strip()
    if not text:
        raise ReviewError("P9_INVALID_RESOLUTION", "reviewed_at is required")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ReviewError(
            "P9_INVALID_RESOLUTION",
            "reviewed_at must be RFC3339/ISO8601",
        ) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ReviewError(
            "P9_INVALID_RESOLUTION",
            "reviewed_at must be timezone-aware",
        )
    if submission.reviewer_type not in {ReviewerType.CODEX, ReviewerType.HUMAN}:
        raise ReviewError("P9_INVALID_RESOLUTION", "unsupported reviewer_type")


def active_effective_assignments(
    resolutions: Sequence[ReviewResolution],
) -> dict[tuple[str, str], str]:
    assignments: dict[tuple[str, str], str] = {}
    for resolution in sorted(resolutions, key=lambda item: item.resolution_id):
        if resolution.action in {
            ResolutionAction.SET_PERIOD,
            ResolutionAction.SET_UNIT,
            ResolutionAction.SET_SCOPE,
        }:
            field = {
                ResolutionAction.SET_PERIOD: "period",
                ResolutionAction.SET_UNIT: "unit",
                ResolutionAction.SET_SCOPE: "scope",
            }[resolution.action]
            value = str(resolution.value or "")
            for fact_id in resolution.before.get("affected_fact_ids") or ():
                key = (str(fact_id), field)
                prior = assignments.get(key)
                if prior is not None and normalize_semantic(prior) != normalize_semantic(value):
                    raise ReviewError(
                        "P9_RESOLUTION_CONFLICT",
                        f"conflicting active values for {key[0]}/{field}",
                    )
                assignments[key] = value
        elif resolution.action is ResolutionAction.CLASSIFY_TABLE_STATEMENT:
            table_id = str(resolution.target.get("table_id") or "")
            key = (table_id, "statement_class")
            value = str(resolution.value or "")
            prior = assignments.get(key)
            if prior is not None and prior != value:
                raise ReviewError(
                    "P9_RESOLUTION_CONFLICT",
                    f"conflicting active statement classes for {table_id}",
                )
            assignments[key] = value
    return assignments


def build_before_after(
    selection: TargetSelection,
) -> tuple[dict[str, Any], dict[str, Any]]:
    before = {
        "target": dict(selection.target),
        "selected_fact_ids": list(selection.selected_fact_ids),
        "affected_fact_ids": list(selection.affected_fact_ids),
        "affected_count": len(selection.affected_fact_ids),
        "already_explicit_fact_ids": list(selection.already_explicit_fact_ids),
        "base_raw_values": dict(selection.base_raw_values),
        "current_effective_values": dict(selection.current_effective_values),
    }
    after = {
        "value": selection.submitted_value,
        "expected_affected_fact_count": len(selection.affected_fact_ids),
    }
    return before, after
