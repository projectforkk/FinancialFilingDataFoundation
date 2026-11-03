from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
import time
import uuid
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable

from financial_filing_data_foundation.facts import load_raw_facts
from financial_filing_data_foundation.facts.models import EXTRACTOR_VERSION
from financial_filing_data_foundation.identity import FilingSlotKey
from financial_filing_data_foundation.native import load_native_document
from financial_filing_data_foundation.native.models import P3_PARSER_VERSION
from financial_filing_data_foundation.registry import (
    CompatibilityStatus,
    ParsedDataRecord,
    ValidationStatus,
)
from financial_filing_data_foundation.tables import load_reconstructed_tables
from financial_filing_data_foundation.tables.models import RECONSTRUCTION_VERSION

from .models import (
    POLICY_VERSION,
    SCHEMA_VERSION,
    ValidationArtifact,
    ValidationError,
)
from .policy import (
    BALANCE_ASSET_ALIASES,
    BALANCE_EQUITY_ALIASES,
    BALANCE_LIABILITY_ALIASES,
    CASH_BEGIN_ALIASES,
    CASH_END_ALIASES,
    CASH_INCREASE_ALIASES,
    CASH_OPERATING_ALIASES,
    INCOME_ALIASES,
    IssueScope,
    IssueSeverity,
    MIN_FACTS_FOR_CORE_STATEMENT_CHECK,
    MIN_FACTS_FOR_SEMANTIC_COVERAGE,
    PERIOD_REVIEW,
    PERIOD_WARNING,
    PROFIT_ALIASES,
    RECONCILIATION_ABSOLUTE_TOLERANCE,
    RECONCILIATION_RELATIVE_TOLERANCE,
    ROW_WITHOUT_LABEL_REVIEW,
    SEVERITY_RANK,
    TABLES_WITHOUT_FACTS_REVIEW,
    TABLES_WITHOUT_FACTS_WARNING,
    UNIT_REVIEW,
    UNIT_WARNING,
)


_PIPELINE_VERSION = (
    f"{P3_PARSER_VERSION}|{RECONSTRUCTION_VERSION}|"
    f"{EXTRACTOR_VERSION}|{POLICY_VERSION}"
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError(f"line {line_no} is not an object")
                rows.append(value)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValidationError(
            "P7_ARTIFACT_INCOMPLETE_OR_CORRUPT",
            f"cannot read JSONL {path.name}: {exc}",
        ) from exc
    return rows


def _jsonl_record(row: dict[str, Any]) -> str:
    raw = json.dumps(
        row,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return (
        raw.replace("\u0085", "\\u0085")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(_jsonl_record(row) + "\n")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def _normalize_metric(value: str) -> str:
    text = " ".join(value.strip().lower().split())
    text = text.replace("’", "'")
    text = re.sub(r"[:：;；,，。()（）\[\]]", "", text)
    return " ".join(text.split())


def _matches_alias(value: str, aliases: tuple[str, ...]) -> bool:
    normalized = _normalize_metric(value)
    return any(normalized == _normalize_metric(alias) for alias in aliases)


def _issue_id(
    document_sha256: str,
    reason_code: str,
    scope: str,
    page_no: int | None,
    table_id: str | None,
    raw_fact_ids: list[str],
) -> str:
    return _sha256_text(
        document_sha256
        + "\0"
        + reason_code
        + "\0"
        + scope
        + "\0"
        + ("" if page_no is None else str(page_no))
        + "\0"
        + (table_id or "")
        + "\0"
        + "\0".join(sorted(raw_fact_ids))
        + "\0"
        + POLICY_VERSION
    )


def _issue(
    document_sha256: str,
    reason_code: str,
    severity: IssueSeverity,
    message: str,
    *,
    scope: IssueScope = IssueScope.DOCUMENT,
    page_no: int | None = None,
    table_id: str | None = None,
    raw_fact_ids: Iterable[str] = (),
    evidence_ids: Iterable[str] = (),
    observed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    fact_ids = sorted({str(value) for value in raw_fact_ids})
    evidence = sorted({str(value) for value in evidence_ids})
    return {
        "issue_id": _issue_id(
            document_sha256,
            reason_code,
            scope.value,
            page_no,
            table_id,
            fact_ids,
        ),
        "document_sha256": document_sha256,
        "reason_code": reason_code,
        "severity": severity.value,
        "scope": scope.value,
        "page_no": page_no,
        "table_id": table_id,
        "raw_fact_ids": fact_ids,
        "evidence_ids": evidence,
        "message": message,
        "observed": observed or {},
        "policy_version": POLICY_VERSION,
    }


def _issue_sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        SEVERITY_RANK[IssueSeverity(str(row["severity"]))],
        str(row["reason_code"]),
        -1 if row.get("page_no") is None else int(row["page_no"]),
        str(row.get("table_id") or ""),
        str(row["issue_id"]),
    )


def _status_from_issues(issues: list[dict[str, Any]]) -> ValidationStatus:
    severities = {IssueSeverity(str(row["severity"])) for row in issues}
    if IssueSeverity.BLOCKING in severities:
        return ValidationStatus.BLOCKED
    if IssueSeverity.FAILURE in severities:
        return ValidationStatus.FAIL
    if IssueSeverity.REVIEW in severities:
        return ValidationStatus.REVIEW_REQUIRED
    return ValidationStatus.PASS


def _compatibility_status(
    p3_version: str,
    p5_version: str,
    p6_version: str,
) -> CompatibilityStatus:
    if (
        p3_version == P3_PARSER_VERSION
        and p5_version == RECONSTRUCTION_VERSION
        and p6_version == EXTRACTOR_VERSION
    ):
        return CompatibilityStatus.COMPATIBLE
    return CompatibilityStatus.INCOMPATIBLE


def _input_fingerprints(
    native: Any,
    tables: Any,
    facts: Any,
) -> dict[str, str]:
    return {
        "p3_document_sha256": _sha256_file(native.document_path),
        "p3_pages_sha256": _sha256_file(native.pages_path),
        "p5_manifest_sha256": _sha256_file(tables.manifest_path),
        "p5_tables_sha256": _sha256_file(tables.tables_path),
        "p5_groups_sha256": _sha256_file(tables.groups_path),
        "p6_manifest_sha256": _sha256_file(facts.manifest_path),
        "p6_facts_sha256": _sha256_file(facts.facts_path),
        "p6_evidence_sha256": _sha256_file(facts.evidence_path),
        "p3_parser_version": P3_PARSER_VERSION,
        "p5_reconstruction_version": RECONSTRUCTION_VERSION,
        "p6_extractor_version": EXTRACTOR_VERSION,
        "p7_policy_version": POLICY_VERSION,
    }


def _bbox_valid(value: Any) -> bool:
    if not isinstance(value, list) or len(value) != 4:
        return False
    try:
        numbers = [float(item) for item in value]
    except (TypeError, ValueError):
        return False
    return (
        all(math.isfinite(item) for item in numbers)
        and numbers[2] >= numbers[0]
        and numbers[3] >= numbers[1]
    )


def _warning_map(warnings: Iterable[dict[str, Any]]) -> dict[str, int]:
    result: dict[str, int] = {}
    for row in warnings:
        reason = str(row.get("reason_code") or "")
        count = int(row.get("count", 0) or 0)
        if reason and count > 0:
            result[reason] = result.get(reason, 0) + count
    return dict(sorted(result.items()))


def _context_key(fact: dict[str, Any]) -> tuple[Any, ...]:
    parent = fact.get("table_group_id") or fact["table_id"]
    period = fact.get("raw_period_label")
    page_guard = int(fact["page_no"]) if period is None else None
    return (
        str(parent),
        period,
        fact.get("raw_unit"),
        fact.get("raw_scope"),
        page_guard,
    )


def _select_alias_facts(
    facts: list[dict[str, Any]],
    aliases: tuple[str, ...],
) -> list[dict[str, Any]]:
    return [
        fact
        for fact in facts
        if _matches_alias(str(fact["raw_metric_name"]), aliases)
    ]


def _reconciliation_tolerance(value: Decimal) -> Decimal:
    relative = abs(value) * Decimal(RECONCILIATION_RELATIVE_TOLERANCE)
    absolute = Decimal(RECONCILIATION_ABSOLUTE_TOLERANCE)
    return max(absolute, relative)


def _reconciliation_issues(
    document_sha256: str,
    facts: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    issues: list[dict[str, Any]] = []
    metrics = {
        "evaluated_rule_count": 0,
        "passed_rule_count": 0,
        "failed_rule_count": 0,
        "skipped_rule_count": 0,
    }

    contexts: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for fact in facts:
        contexts[_context_key(fact)].append(fact)

    for _, context_facts in sorted(contexts.items(), key=lambda item: repr(item[0])):
        assets = _select_alias_facts(context_facts, BALANCE_ASSET_ALIASES)
        liabilities = _select_alias_facts(context_facts, BALANCE_LIABILITY_ALIASES)
        equity = _select_alias_facts(context_facts, BALANCE_EQUITY_ALIASES)

        balance_present = bool(assets or liabilities or equity)
        if len(assets) == len(liabilities) == len(equity) == 1:
            metrics["evaluated_rule_count"] += 1
            a = Decimal(str(assets[0]["parsed_numeric_value"]))
            l = Decimal(str(liabilities[0]["parsed_numeric_value"]))
            e = Decimal(str(equity[0]["parsed_numeric_value"]))
            difference = abs(a - (l + e))
            tolerance = _reconciliation_tolerance(a)
            if difference <= tolerance:
                metrics["passed_rule_count"] += 1
            else:
                metrics["failed_rule_count"] += 1
                members = assets + liabilities + equity
                issues.append(
                    _issue(
                        document_sha256,
                        "BALANCE_SHEET_RECONCILIATION_FAILED",
                        IssueSeverity.FAILURE,
                        "Assets do not reconcile to liabilities plus equity.",
                        scope=IssueScope.TABLE,
                        page_no=int(members[0]["page_no"]),
                        table_id=str(members[0]["table_id"]),
                        raw_fact_ids=[str(row["raw_fact_id"]) for row in members],
                        evidence_ids=[str(row["evidence_id"]) for row in members],
                        observed={
                            "assets": str(a),
                            "liabilities": str(l),
                            "equity": str(e),
                            "difference": str(difference),
                            "tolerance": str(tolerance),
                        },
                    )
                )
        elif balance_present:
            metrics["skipped_rule_count"] += 1

        beginning = _select_alias_facts(context_facts, CASH_BEGIN_ALIASES)
        increase = _select_alias_facts(context_facts, CASH_INCREASE_ALIASES)
        ending = _select_alias_facts(context_facts, CASH_END_ALIASES)
        cash_present = bool(beginning or increase or ending)
        if len(beginning) == len(increase) == len(ending) == 1:
            metrics["evaluated_rule_count"] += 1
            b = Decimal(str(beginning[0]["parsed_numeric_value"]))
            i = Decimal(str(increase[0]["parsed_numeric_value"]))
            end = Decimal(str(ending[0]["parsed_numeric_value"]))
            difference = abs((b + i) - end)
            tolerance = _reconciliation_tolerance(end)
            if difference <= tolerance:
                metrics["passed_rule_count"] += 1
            else:
                metrics["failed_rule_count"] += 1
                members = beginning + increase + ending
                issues.append(
                    _issue(
                        document_sha256,
                        "CASH_RECONCILIATION_FAILED",
                        IssueSeverity.FAILURE,
                        "Beginning cash plus net increase does not reconcile to ending cash.",
                        scope=IssueScope.TABLE,
                        page_no=int(members[0]["page_no"]),
                        table_id=str(members[0]["table_id"]),
                        raw_fact_ids=[str(row["raw_fact_id"]) for row in members],
                        evidence_ids=[str(row["evidence_id"]) for row in members],
                        observed={
                            "beginning": str(b),
                            "increase": str(i),
                            "ending": str(end),
                            "difference": str(difference),
                            "tolerance": str(tolerance),
                        },
                    )
                )
        elif cash_present:
            metrics["skipped_rule_count"] += 1

    return issues, metrics


def _core_statement_signals(facts: list[dict[str, Any]]) -> dict[str, bool]:
    balance_aliases = (
        BALANCE_ASSET_ALIASES
        + BALANCE_LIABILITY_ALIASES
        + BALANCE_EQUITY_ALIASES
    )
    income_aliases = INCOME_ALIASES + PROFIT_ALIASES
    cash_aliases = (
        CASH_OPERATING_ALIASES
        + CASH_INCREASE_ALIASES
        + CASH_END_ALIASES
    )
    return {
        "balance": any(
            _matches_alias(str(fact["raw_metric_name"]), balance_aliases)
            for fact in facts
        ),
        "income": any(
            _matches_alias(str(fact["raw_metric_name"]), income_aliases)
            for fact in facts
        ),
        "cashflow": any(
            _matches_alias(str(fact["raw_metric_name"]), cash_aliases)
            for fact in facts
        ),
    }


def _duplicate_issues(
    document_sha256: str,
    facts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for fact in facts:
        key = (
            str(fact["table_id"]),
            str(fact["row_id"]),
            str(fact["value_cell_id"]),
            int(fact["column_index"]),
        )
        grouped[key].append(fact)

    issues: list[dict[str, Any]] = []
    for _, rows in sorted(grouped.items(), key=lambda item: repr(item[0])):
        if len(rows) <= 1:
            continue
        values = {str(row["parsed_numeric_value"]) for row in rows}
        severity = (
            IssueSeverity.REVIEW if len(values) > 1 else IssueSeverity.WARNING
        )
        reason = (
            "CONFLICTING_FACT_VALUES"
            if len(values) > 1
            else "DUPLICATE_FACT_VALUES"
        )
        issues.append(
            _issue(
                document_sha256,
                reason,
                severity,
                (
                    "Multiple facts in the same raw context have different values."
                    if len(values) > 1
                    else "Duplicate facts repeat the same raw value in one context."
                ),
                scope=IssueScope.TABLE,
                page_no=int(rows[0]["page_no"]),
                table_id=str(rows[0]["table_id"]),
                raw_fact_ids=[str(row["raw_fact_id"]) for row in rows],
                evidence_ids=[str(row["evidence_id"]) for row in rows],
                observed={
                    "fact_count": len(rows),
                    "distinct_values": sorted(values),
                },
            )
        )
    return issues


def _evaluate(
    document_sha256: str,
    *,
    page_count: int,
    pages: list[dict[str, Any]],
    tables: list[dict[str, Any]],
    groups: list[dict[str, Any]],
    facts: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    p6_warnings: Iterable[dict[str, Any]],
    compatibility_status: CompatibilityStatus,
) -> tuple[list[dict[str, Any]], dict[str, Any], ValidationStatus]:
    issues: list[dict[str, Any]] = []

    page_numbers = [int(row.get("page_no", -1)) for row in pages]
    if page_numbers != list(range(1, page_count + 1)):
        issues.append(
            _issue(
                document_sha256,
                "PAGE_SEQUENCE_INVALID",
                IssueSeverity.BLOCKING,
                "Physical page sequence is not contiguous.",
                observed={
                    "page_count": page_count,
                    "observed_count": len(page_numbers),
                },
            )
        )

    evidence_by_id = {
        str(row.get("evidence_id") or ""): row for row in evidence
    }
    valid_evidence_count = 0
    source_word_evidence_count = 0
    for fact in facts:
        row = evidence_by_id.get(str(fact.get("evidence_id") or ""))
        if row is None:
            continue
        valid_evidence_count += 1
        source_words = row.get("source_words")
        if isinstance(source_words, list) and source_words:
            source_word_evidence_count += 1

    evidence_coverage_ratio = (
        valid_evidence_count / len(facts) if facts else 1.0
    )
    source_word_coverage_ratio = (
        source_word_evidence_count / len(facts) if facts else 1.0
    )

    if len(facts) != len(evidence) or evidence_coverage_ratio < 1.0:
        issues.append(
            _issue(
                document_sha256,
                "FACT_EVIDENCE_INCOMPLETE",
                IssueSeverity.BLOCKING,
                "Every raw fact must have exactly one evidence record.",
                observed={
                    "fact_count": len(facts),
                    "evidence_count": len(evidence),
                    "coverage_ratio": round(evidence_coverage_ratio, 6),
                },
            )
        )

    invalid_evidence = 0
    for row in evidence:
        page_no = int(row.get("page_no", 0) or 0)
        if (
            row.get("document_sha256") != document_sha256
            or page_no < 1
            or page_no > page_count
            or not _bbox_valid(row.get("bbox"))
            or not isinstance(row.get("source_words"), list)
            or not row.get("source_words")
        ):
            invalid_evidence += 1
    if invalid_evidence:
        issues.append(
            _issue(
                document_sha256,
                "EVIDENCE_REFERENCE_INVALID",
                IssueSeverity.BLOCKING,
                "One or more evidence records have invalid document/page/bbox/source references.",
                observed={"invalid_evidence_count": invalid_evidence},
            )
        )

    if not facts:
        issues.append(
            _issue(
                document_sha256,
                "NO_RAW_FACTS",
                IssueSeverity.FAILURE,
                "No raw financial facts were extracted.",
                observed={"fact_count": 0},
            )
        )

    table_ids = {str(row["table_id"]) for row in tables}
    tables_with_facts = {str(row["table_id"]) for row in facts}
    tables_without_facts = len(table_ids - tables_with_facts)
    table_count = len(tables)
    tables_without_facts_ratio = (
        tables_without_facts / table_count if table_count else 0.0
    )

    if tables_without_facts_ratio > TABLES_WITHOUT_FACTS_REVIEW:
        issues.append(
            _issue(
                document_sha256,
                "TABLE_FACT_COVERAGE_LOW",
                IssueSeverity.REVIEW,
                "A high share of reconstructed tables contain no raw facts.",
                observed={
                    "tables_without_facts": tables_without_facts,
                    "table_count": table_count,
                    "ratio": round(tables_without_facts_ratio, 6),
                },
            )
        )
    elif tables_without_facts_ratio > TABLES_WITHOUT_FACTS_WARNING:
        issues.append(
            _issue(
                document_sha256,
                "TABLE_FACT_COVERAGE_WARN",
                IssueSeverity.WARNING,
                "A notable share of reconstructed tables contain no raw facts.",
                observed={
                    "tables_without_facts": tables_without_facts,
                    "table_count": table_count,
                    "ratio": round(tables_without_facts_ratio, 6),
                },
            )
        )

    warning_map = _warning_map(p6_warnings)
    row_without_label = warning_map.get("ROW_WITHOUT_LABEL", 0)
    row_denominator = len(facts) + row_without_label
    row_without_label_ratio = (
        row_without_label / row_denominator if row_denominator else 0.0
    )
    if row_without_label:
        issues.append(
            _issue(
                document_sha256,
                "ROW_WITHOUT_LABEL_HIGH"
                if row_without_label_ratio > ROW_WITHOUT_LABEL_REVIEW
                else "ROW_WITHOUT_LABEL_PRESENT",
                (
                    IssueSeverity.REVIEW
                    if row_without_label_ratio > ROW_WITHOUT_LABEL_REVIEW
                    else IssueSeverity.WARNING
                ),
                "P6 reported numeric rows without a deterministic label.",
                observed={
                    "count": row_without_label,
                    "ratio": round(row_without_label_ratio, 6),
                },
            )
        )

    for source_reason, reason_code, message in (
        (
            "AMBIGUOUS_RAW_UNIT",
            "RAW_UNIT_AMBIGUOUS",
            "P6 reported ambiguous raw units.",
        ),
        (
            "AMBIGUOUS_RAW_SCOPE",
            "RAW_SCOPE_AMBIGUOUS",
            "P6 reported ambiguous raw scopes.",
        ),
        (
            "AMBIGUOUS_RAW_PERIOD",
            "RAW_PERIOD_AMBIGUOUS",
            "P6 reported ambiguous raw periods.",
        ),
    ):
        count = warning_map.get(source_reason, 0)
        if count:
            issues.append(
                _issue(
                    document_sha256,
                    reason_code,
                    IssueSeverity.REVIEW,
                    message,
                    observed={"count": count},
                )
            )

    fact_count = len(facts)
    period_nonnull = sum(
        fact.get("raw_period_label") is not None for fact in facts
    )
    unit_nonnull = sum(fact.get("raw_unit") is not None for fact in facts)
    scope_nonnull = sum(fact.get("raw_scope") is not None for fact in facts)

    period_ratio = period_nonnull / fact_count if fact_count else 0.0
    unit_ratio = unit_nonnull / fact_count if fact_count else 0.0
    scope_ratio = scope_nonnull / fact_count if fact_count else 0.0

    if fact_count >= MIN_FACTS_FOR_SEMANTIC_COVERAGE:
        if period_ratio < PERIOD_REVIEW:
            issues.append(
                _issue(
                    document_sha256,
                    "RAW_PERIOD_COVERAGE_LOW",
                    IssueSeverity.REVIEW,
                    "Explicit raw period coverage is below review threshold.",
                    observed={"ratio": round(period_ratio, 6)},
                )
            )
        elif period_ratio < PERIOD_WARNING:
            issues.append(
                _issue(
                    document_sha256,
                    "RAW_PERIOD_COVERAGE_WARN",
                    IssueSeverity.WARNING,
                    "Explicit raw period coverage is below preferred threshold.",
                    observed={"ratio": round(period_ratio, 6)},
                )
            )

        if unit_ratio < UNIT_REVIEW:
            issues.append(
                _issue(
                    document_sha256,
                    "RAW_UNIT_COVERAGE_LOW",
                    IssueSeverity.REVIEW,
                    "Explicit raw unit coverage is below review threshold.",
                    observed={"ratio": round(unit_ratio, 6)},
                )
            )
        elif unit_ratio < UNIT_WARNING:
            issues.append(
                _issue(
                    document_sha256,
                    "RAW_UNIT_COVERAGE_WARN",
                    IssueSeverity.WARNING,
                    "Explicit raw unit coverage is below preferred threshold.",
                    observed={"ratio": round(unit_ratio, 6)},
                )
            )

        if scope_ratio == 0:
            issues.append(
                _issue(
                    document_sha256,
                    "RAW_SCOPE_COVERAGE_ZERO",
                    IssueSeverity.WARNING,
                    "No explicit raw scope was extracted.",
                    observed={"ratio": 0.0},
                )
            )

    core_signals = _core_statement_signals(facts)
    core_signal_count = sum(bool(value) for value in core_signals.values())
    if (
        fact_count >= MIN_FACTS_FOR_CORE_STATEMENT_CHECK
        and core_signal_count < 2
    ):
        issues.append(
            _issue(
                document_sha256,
                "CORE_STATEMENT_COVERAGE_LOW",
                IssueSeverity.REVIEW,
                "Fewer than two core financial statement signal classes were found.",
                observed={
                    "signal_count": core_signal_count,
                    "signals": core_signals,
                },
            )
        )

    issues.extend(_duplicate_issues(document_sha256, facts))
    recon_issues, recon_metrics = _reconciliation_issues(
        document_sha256, facts
    )
    issues.extend(recon_issues)

    if compatibility_status != CompatibilityStatus.COMPATIBLE:
        issues.append(
            _issue(
                document_sha256,
                "PIPELINE_VERSION_INCOMPATIBLE",
                IssueSeverity.BLOCKING,
                "Upstream artifact versions are not supported by this P7 policy.",
                observed={"compatibility_status": compatibility_status.value},
            )
        )

    issues.sort(key=_issue_sort_key)
    status = _status_from_issues(issues)

    pages_with_facts = len({int(row["page_no"]) for row in facts})
    unique_metric_count = len(
        {_normalize_metric(str(row["raw_metric_name"])) for row in facts}
    )

    severity_counts = Counter(str(row["severity"]) for row in issues)

    metrics: dict[str, Any] = {
        "page_count": page_count,
        "reconstructed_table_count": table_count,
        "table_group_count": len(groups),
        "raw_fact_count": fact_count,
        "evidence_count": len(evidence),
        "unique_metric_count": unique_metric_count,
        "pages_with_facts": pages_with_facts,
        "tables_with_facts": len(tables_with_facts),
        "tables_without_facts": tables_without_facts,
        "tables_without_facts_ratio": round(
            tables_without_facts_ratio, 6
        ),
        "fact_density_per_table": round(
            fact_count / table_count if table_count else 0.0, 6
        ),
        "evidence_coverage_ratio": round(evidence_coverage_ratio, 6),
        "source_word_coverage_ratio": round(
            source_word_coverage_ratio, 6
        ),
        "period_nonnull_ratio": round(period_ratio, 6),
        "unit_nonnull_ratio": round(unit_ratio, 6),
        "scope_nonnull_ratio": round(scope_ratio, 6),
        "row_without_label_count": row_without_label,
        "row_without_label_ratio": round(row_without_label_ratio, 6),
        "p6_warning_counts": warning_map,
        "core_statement_signals": core_signals,
        "core_statement_signal_count": core_signal_count,
        **recon_metrics,
        "blocking_issue_count": severity_counts.get(
            IssueSeverity.BLOCKING.value, 0
        ),
        "failure_issue_count": severity_counts.get(
            IssueSeverity.FAILURE.value, 0
        ),
        "review_issue_count": severity_counts.get(
            IssueSeverity.REVIEW.value, 0
        ),
        "warning_issue_count": severity_counts.get(
            IssueSeverity.WARNING.value, 0
        ),
        "info_issue_count": severity_counts.get(
            IssueSeverity.INFO.value, 0
        ),
    }
    return issues, metrics, status


def _load_inputs(
    native_artifact_dir: Path,
    reconstructed_table_dir: Path,
    raw_fact_dir: Path,
) -> tuple[
    Any,
    Any,
    Any,
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    try:
        native = load_native_document(native_artifact_dir)
        tables_artifact = load_reconstructed_tables(reconstructed_table_dir)
        facts_artifact = load_raw_facts(
            raw_fact_dir,
            native_artifact_dir,
            reconstructed_table_dir,
        )
    except Exception as exc:
        raise ValidationError(
            "P7_INPUT_ARTIFACT_INVALID",
            f"upstream artifact load failed: {exc}",
        ) from exc

    if not (
        native.document_sha256
        == tables_artifact.document_sha256
        == facts_artifact.document_sha256
    ):
        raise ValidationError(
            "P7_INPUT_ARTIFACT_INVALID",
            "P3/P5/P6 document SHA mismatch",
        )

    pages = _read_jsonl(native.pages_path)
    tables = _read_jsonl(tables_artifact.tables_path)
    groups = _read_jsonl(tables_artifact.groups_path)
    facts = _read_jsonl(facts_artifact.facts_path)
    evidence = _read_jsonl(facts_artifact.evidence_path)

    return (
        native,
        tables_artifact,
        facts_artifact,
        pages,
        tables,
        groups,
        facts,
        evidence,
    )


def _stable_report(
    *,
    document_sha256: str,
    status: ValidationStatus,
    compatibility_status: CompatibilityStatus,
    issues: list[dict[str, Any]],
    metrics: dict[str, Any],
    fingerprints: dict[str, str],
) -> dict[str, Any]:
    blocking = sum(
        row["severity"] == IssueSeverity.BLOCKING.value for row in issues
    )
    failure = sum(
        row["severity"] == IssueSeverity.FAILURE.value for row in issues
    )
    review = sum(
        row["severity"] == IssueSeverity.REVIEW.value for row in issues
    )
    warning = sum(
        row["severity"] == IssueSeverity.WARNING.value for row in issues
    )
    reuse_eligible = (
        status == ValidationStatus.PASS
        and blocking == 0
        and compatibility_status == CompatibilityStatus.COMPATIBLE
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "policy_version": POLICY_VERSION,
        "document_sha256": document_sha256,
        "validation_status": status.value,
        "compatibility_status": compatibility_status.value,
        "reuse_eligible": reuse_eligible,
        "blocking_issue_count": blocking,
        "failure_issue_count": failure,
        "review_issue_count": review,
        "warning_issue_count": warning,
        "issue_count": len(issues),
        "metrics": metrics,
        "input_fingerprints": fingerprints,
        "issues_file": "issues.jsonl",
    }


def _compute(
    native_artifact_dir: Path,
    reconstructed_table_dir: Path,
    raw_fact_dir: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    (
        native,
        tables_artifact,
        facts_artifact,
        pages,
        tables,
        groups,
        facts,
        evidence,
    ) = _load_inputs(
        native_artifact_dir,
        reconstructed_table_dir,
        raw_fact_dir,
    )

    compatibility = _compatibility_status(
        P3_PARSER_VERSION,
        RECONSTRUCTION_VERSION,
        EXTRACTOR_VERSION,
    )
    issues, metrics, status = _evaluate(
        native.document_sha256,
        page_count=native.page_count,
        pages=pages,
        tables=tables,
        groups=groups,
        facts=facts,
        evidence=evidence,
        p6_warnings=facts_artifact.warnings,
        compatibility_status=compatibility,
    )
    fingerprints = _input_fingerprints(
        native, tables_artifact, facts_artifact
    )
    report = _stable_report(
        document_sha256=native.document_sha256,
        status=status,
        compatibility_status=compatibility,
        issues=issues,
        metrics=metrics,
        fingerprints=fingerprints,
    )
    return report, issues


def load_validation_result(
    artifact_dir: str | Path,
    native_artifact_dir: str | Path,
    reconstructed_table_dir: str | Path,
    raw_fact_dir: str | Path,
) -> ValidationArtifact:
    directory = Path(artifact_dir).expanduser().resolve()
    native_dir = Path(native_artifact_dir).expanduser().resolve()
    table_dir = Path(reconstructed_table_dir).expanduser().resolve()
    fact_dir = Path(raw_fact_dir).expanduser().resolve()
    report_path = directory / "validation_report.json"
    issues_path = directory / "issues.jsonl"

    if not report_path.is_file() or not issues_path.is_file():
        raise ValidationError(
            "P7_ARTIFACT_INCOMPLETE_OR_CORRUPT",
            f"missing P7 artifact files under {directory}",
        )

    try:
        persisted_report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValidationError(
            "P7_ARTIFACT_INCOMPLETE_OR_CORRUPT",
            f"cannot read validation report: {exc}",
        ) from exc

    persisted_issues = _read_jsonl(issues_path)
    expected_report, expected_issues = _compute(
        native_dir, table_dir, fact_dir
    )

    document_sha256 = str(expected_report["document_sha256"])
    if directory.name != document_sha256:
        raise ValidationError(
            "P7_ARTIFACT_INCOMPLETE_OR_CORRUPT",
            "P7 artifact directory identity mismatch",
        )

    stable_persisted = {
        key: value
        for key, value in persisted_report.items()
        if key != "timings_ms"
    }
    if stable_persisted != expected_report:
        raise ValidationError(
            "P7_ARTIFACT_INCOMPLETE_OR_CORRUPT",
            "persisted validation report differs from deterministic validation",
        )
    if persisted_issues != expected_issues:
        raise ValidationError(
            "P7_ARTIFACT_INCOMPLETE_OR_CORRUPT",
            "persisted validation issues differ from deterministic validation",
        )

    status = ValidationStatus(str(expected_report["validation_status"]))
    compatibility = CompatibilityStatus(
        str(expected_report["compatibility_status"])
    )
    return ValidationArtifact(
        artifact_dir=directory,
        document_sha256=document_sha256,
        validation_status=status,
        compatibility_status=compatibility,
        reuse_eligible=bool(expected_report["reuse_eligible"]),
        blocking_issue_count=int(expected_report["blocking_issue_count"]),
        failure_issue_count=int(expected_report["failure_issue_count"]),
        review_issue_count=int(expected_report["review_issue_count"]),
        warning_issue_count=int(expected_report["warning_issue_count"]),
        issue_count=int(expected_report["issue_count"]),
        issues_path=issues_path,
        report_path=report_path,
        metrics=dict(expected_report["metrics"]),
        timings_ms=dict(persisted_report.get("timings_ms") or {}),
    )


def validate_document_artifacts(
    native_artifact_dir: str | Path,
    reconstructed_table_dir: str | Path,
    raw_fact_dir: str | Path,
    validation_root: str | Path,
) -> ValidationArtifact:
    native_dir = Path(native_artifact_dir).expanduser().resolve()
    table_dir = Path(reconstructed_table_dir).expanduser().resolve()
    fact_dir = Path(raw_fact_dir).expanduser().resolve()
    root = Path(validation_root).expanduser().resolve()

    start = time.perf_counter_ns()
    report, issues = _compute(native_dir, table_dir, fact_dir)
    document_sha256 = str(report["document_sha256"])
    final_dir = root / document_sha256

    if final_dir.exists():
        return load_validation_result(
            final_dir, native_dir, table_dir, fact_dir
        )

    root.mkdir(parents=True, exist_ok=True)
    temp_dir = root / f".{document_sha256}.{uuid.uuid4().hex}.tmp"
    temp_dir.mkdir(parents=False, exist_ok=False)
    try:
        persist_start = time.perf_counter_ns()
        issues_path = temp_dir / "issues.jsonl"
        report_path = temp_dir / "validation_report.json"
        _write_jsonl(issues_path, issues)
        persisted_report = dict(report)
        persisted_report["timings_ms"] = {
            "validation": round(
                (persist_start - start) / 1_000_000.0, 3
            ),
            "persist": 0.0,
            "total": 0.0,
        }
        _write_json(report_path, persisted_report)
        persist_end = time.perf_counter_ns()
        persisted_report["timings_ms"]["persist"] = round(
            (persist_end - persist_start) / 1_000_000.0, 3
        )
        persisted_report["timings_ms"]["total"] = round(
            (persist_end - start) / 1_000_000.0, 3
        )
        _write_json(report_path, persisted_report)
        os.replace(temp_dir, final_dir)
        return load_validation_result(
            final_dir, native_dir, table_dir, fact_dir
        )
    except Exception as exc:
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        if isinstance(exc, ValidationError):
            raise
        raise ValidationError("P7_PERSIST_FAILED", str(exc)) from exc


def _parse_run_id(document_sha256: str) -> str:
    return _sha256_text(
        document_sha256 + "\0" + _PIPELINE_VERSION
    )


def build_parsed_data_record(
    validation_artifact: ValidationArtifact,
    slot: FilingSlotKey,
    artifact_path: str,
) -> ParsedDataRecord:
    return ParsedDataRecord(
        parse_run_id=_parse_run_id(validation_artifact.document_sha256),
        slot=slot,
        document_sha256=validation_artifact.document_sha256,
        parser_version=_PIPELINE_VERSION,
        schema_version=SCHEMA_VERSION,
        validation_status=validation_artifact.validation_status,
        blocking_issue_count=validation_artifact.blocking_issue_count,
        compatibility_status=validation_artifact.compatibility_status,
        artifact_path=artifact_path,
    )
