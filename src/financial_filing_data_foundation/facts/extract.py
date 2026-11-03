from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
import time
import uuid
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable

from financial_filing_data_foundation.native import load_native_document
from financial_filing_data_foundation.native.models import P3_PARSER_VERSION
from financial_filing_data_foundation.tables import load_reconstructed_tables
from financial_filing_data_foundation.tables.models import RECONSTRUCTION_VERSION

from .models import (
    EXTRACTOR_VERSION,
    SCHEMA_VERSION,
    RawFactArtifact,
    RawFactError,
)


_HEADER_MARKERS = {
    "项目",
    "科目",
    "项目 附注",
    "item",
    "items",
    "particulars",
    "item notes",
}

_PERIOD_RE = re.compile(
    r"^(?:"
    r"(?:19|20|21)\d{2}(?:年|年度)?"
    r"|本期|上期|本年|上年|期末|期初"
    r"|current\s+year|prior\s+year"
    r"|current\s+period|prior\s+period"
    r"|year\s+ended(?:\s+.+)?"
    r"|as\s+at(?:\s+.+)?"
    r")$",
    re.IGNORECASE,
)

_UNIT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("RMB_MILLION", re.compile(r"人民币\s*百万元|百万元", re.IGNORECASE)),
    ("RMB_TEN_THOUSAND", re.compile(r"人民币\s*万元|万元", re.IGNORECASE)),
    ("RMB_THOUSAND", re.compile(r"人民币\s*千元|千元", re.IGNORECASE)),
    ("HKD_THOUSAND", re.compile(r"千港元", re.IGNORECASE)),
    ("RMB_BASE", re.compile(r"人民币\s*元|\bRMB\b|\bCNY\b", re.IGNORECASE)),
    ("HKD_BASE", re.compile(r"港元|\bHKD\b", re.IGNORECASE)),
    ("USD_BASE", re.compile(r"美元|\bUSD\b", re.IGNORECASE)),
)

_SCOPE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("CONSOLIDATED", re.compile(r"合并|\bconsolidated\b", re.IGNORECASE)),
    (
        "PARENT",
        re.compile(
            r"母公司|\bparent\s+company\b|\bseparate\s+financial\s+statements\b",
            re.IGNORECASE,
        ),
    ),
)

_CURRENCY_PREFIXES = "¥￥$€£"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


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


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                row = json.loads(line)
                if not isinstance(row, dict):
                    raise ValueError(f"line {line_no} is not an object")
                rows.append(row)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise RawFactError(
            "P6_ARTIFACT_INCOMPLETE_OR_CORRUPT",
            f"cannot read JSONL {path.name}: {exc}",
        ) from exc
    return rows


def _normalize_space(value: str) -> str:
    return " ".join(value.strip().split())


def parse_numeric_value(raw: str) -> str | None:
    text = raw.strip()
    if not text or text in {"-", "−", "—", "–"}:
        return None

    negative_parentheses = text.startswith("(") and text.endswith(")")
    if negative_parentheses:
        text = text[1:-1].strip()

    if text and text[0] in _CURRENCY_PREFIXES:
        text = text[1:].strip()

    text = text.replace("−", "-").replace("，", ",")

    if re.search(r"\d\s+\d", text):
        return None

    percent = text.endswith("%")
    if percent:
        text = text[:-1].strip()

    text = text.replace(",", "")
    if not re.fullmatch(r"[+-]?\d+(?:\.\d+)?", text):
        return None

    try:
        value = Decimal(text)
    except InvalidOperation:
        return None

    if negative_parentheses:
        value = -abs(value)

    result = format(value, "f")
    if result == "-0":
        result = "0"
    return result


def _bbox_values(raw: Any) -> list[float]:
    if not isinstance(raw, (list, tuple)) or len(raw) != 4:
        raise RawFactError(
            "P6_INPUT_EVIDENCE_INVALID",
            "bbox must contain four values",
        )
    try:
        values = [round(float(value), 3) for value in raw]
    except (TypeError, ValueError) as exc:
        raise RawFactError(
            "P6_INPUT_EVIDENCE_INVALID",
            "bbox contains non-numeric value",
        ) from exc
    if (
        not all(math.isfinite(value) for value in values)
        or values[2] < values[0]
        or values[3] < values[1]
    ):
        raise RawFactError(
            "P6_INPUT_EVIDENCE_INVALID",
            "bbox is non-finite or unordered",
        )
    return values


def _bbox_union(values: list[list[float]]) -> list[float]:
    if not values:
        raise RawFactError(
            "P6_INPUT_EVIDENCE_INVALID",
            "cannot build evidence bbox without cells",
        )
    return [
        round(min(value[0] for value in values), 3),
        round(min(value[1] for value in values), 3),
        round(max(value[2] for value in values), 3),
        round(max(value[3] for value in values), 3),
    ]


def _source_ref_key(ref: dict[str, Any]) -> tuple[int, int, int, int, str]:
    bbox = _bbox_values(ref.get("bbox"))
    bbox_key = ",".join(f"{value:.3f}" for value in bbox)
    return (
        int(ref["page_no"]),
        int(ref["block_no"]),
        int(ref["line_no"]),
        int(ref["word_no"]),
        bbox_key,
    )


def _fact_id(
    document_sha256: str,
    table_id: str,
    row_id: str,
    value_cell_id: str,
) -> str:
    return _sha256_text(
        document_sha256
        + "\0"
        + table_id
        + "\0"
        + row_id
        + "\0"
        + value_cell_id
        + "\0"
        + EXTRACTOR_VERSION
    )


def _evidence_id(raw_fact_id: str, refs: list[dict[str, Any]]) -> str:
    keys = [
        ":".join(
            [
                str(key[0]),
                str(key[1]),
                str(key[2]),
                str(key[3]),
                key[4],
            ]
        )
        for key in sorted(_source_ref_key(ref) for ref in refs)
    ]
    return _sha256_text(raw_fact_id + "\0" + "\0".join(keys))


def _is_period_label(text: str) -> bool:
    return bool(_PERIOD_RE.fullmatch(_normalize_space(text)))


def _is_period_header_row(row: dict[str, Any]) -> bool:
    cells = list(row.get("cells") or ())
    labels = [
        _normalize_space(str(cell.get("text", "")))
        for cell in cells
        if cell.get("role") == "LABEL" and str(cell.get("text", "")).strip()
    ]
    if not labels:
        return False
    marker = _normalize_space(" ".join(labels)).lower()
    if marker not in _HEADER_MARKERS:
        return False

    values = [
        cell
        for cell in cells
        if cell.get("role") == "VALUE" and str(cell.get("text", "")).strip()
    ]
    if not values:
        return False
    return all(_is_period_label(str(cell.get("text", ""))) for cell in values)


def _table_texts(table: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for row in table.get("rows") or ():
        for cell in row.get("cells") or ():
            text = str(cell.get("text", "")).strip()
            if text:
                values.append(text)
    return values


def _detect_unique_pattern(
    texts: list[str],
    patterns: tuple[tuple[str, re.Pattern[str]], ...],
) -> tuple[str | None, bool]:
    matches: list[tuple[str, str, int, int]] = []
    for text_index, text in enumerate(texts):
        for key, pattern in patterns:
            match = pattern.search(text)
            if match:
                matches.append((key, match.group(0), text_index, match.start()))

    keys = {item[0] for item in matches}
    if not matches:
        return None, False
    if len(keys) > 1:
        return None, True
    first = min(matches, key=lambda item: (item[2], item[3], item[1]))
    return first[1], False


def _table_scope_texts(table: dict[str, Any]) -> list[str]:
    values = [str(value) for value in table.get("candidate_keywords") or ()]
    for row in list(table.get("rows") or ())[:6]:
        for cell in row.get("cells") or ():
            text = str(cell.get("text", "")).strip()
            if text:
                values.append(text)
    return values


def _period_from_geometry(
    table: dict[str, Any],
    row_index: int,
    column_index: int,
) -> tuple[str | None, bool]:
    anchors = [float(value) for value in table.get("value_column_anchors") or ()]
    if column_index < 1 or column_index > len(anchors):
        return None, False
    target = anchors[column_index - 1]
    tolerance = max(8.0, float(table.get("page_width", 1.0)) * 0.08)

    candidates: list[tuple[int, float, str]] = []
    rows = list(table.get("rows") or ())
    for prior_index in range(row_index - 1, -1, -1):
        row = rows[prior_index]
        found_on_row: list[tuple[float, str]] = []
        for cell in row.get("cells") or ():
            text = _normalize_space(str(cell.get("text", "")))
            if not text or not _is_period_label(text):
                continue
            bbox = _bbox_values(cell.get("bbox"))
            x = float(bbox[2])
            distance = abs(x - target)
            if distance <= tolerance:
                found_on_row.append((distance, text))
        if found_on_row:
            for distance, text in found_on_row:
                candidates.append((prior_index, distance, text))
            break

    if not candidates:
        return None, False

    best_row = max(item[0] for item in candidates)
    same_row = [item for item in candidates if item[0] == best_row]
    min_distance = min(item[1] for item in same_row)
    nearest = [
        item for item in same_row if abs(item[1] - min_distance) <= 0.001
    ]
    unique_texts = {item[2] for item in nearest}
    if len(unique_texts) != 1:
        return None, True
    return nearest[0][2], False


def _build_word_index(
    pages: list[dict[str, Any]],
) -> dict[tuple[int, int, int, int], dict[str, Any]]:
    index: dict[tuple[int, int, int, int], dict[str, Any]] = {}
    for page in pages:
        page_no = int(page["page_no"])
        for word in page.get("words") or ():
            key = (
                page_no,
                int(word["block_no"]),
                int(word["line_no"]),
                int(word["word_no"]),
            )
            if key in index:
                raise RawFactError(
                    "P6_INPUT_EVIDENCE_INVALID",
                    f"duplicate P3 word identity: {key}",
                )
            index[key] = {
                "text": str(word.get("text", "")),
                "bbox": _bbox_values(word.get("bbox")),
            }
    return index


def _validate_and_merge_refs(
    cells: list[dict[str, Any]],
    word_index: dict[tuple[int, int, int, int], dict[str, Any]],
    expected_page: int,
) -> list[dict[str, Any]]:
    unique: dict[tuple[int, int, int, int, str], dict[str, Any]] = {}
    for cell in cells:
        refs = cell.get("source_words")
        if not isinstance(refs, list) or not refs:
            raise RawFactError(
                "P6_INPUT_EVIDENCE_INVALID",
                "fact source cell has no source_words",
            )
        for ref in refs:
            page_no = int(ref["page_no"])
            if page_no != expected_page:
                raise RawFactError(
                    "P6_INPUT_EVIDENCE_INVALID",
                    "source ref page differs from fact page",
                )
            key4 = (
                page_no,
                int(ref["block_no"]),
                int(ref["line_no"]),
                int(ref["word_no"]),
            )
            actual = word_index.get(key4)
            if actual is None:
                raise RawFactError(
                    "P6_INPUT_EVIDENCE_INVALID",
                    f"source word not found: {key4}",
                )
            bbox = _bbox_values(ref.get("bbox"))
            if bbox != actual["bbox"]:
                raise RawFactError(
                    "P6_INPUT_EVIDENCE_INVALID",
                    f"source word bbox mismatch: {key4}",
                )
            normalized = {
                "page_no": page_no,
                "block_no": key4[1],
                "line_no": key4[2],
                "word_no": key4[3],
                "bbox": bbox,
            }
            unique[_source_ref_key(normalized)] = normalized
    return [
        unique[key]
        for key in sorted(unique)
    ]


def _group_map(groups: list[dict[str, Any]]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for group in groups:
        group_id = str(group["group_id"])
        for table_id_raw in group.get("member_table_ids") or ():
            table_id = str(table_id_raw)
            existing = mapping.get(table_id)
            if existing is not None and existing != group_id:
                raise RawFactError(
                    "P6_INPUT_ARTIFACT_INVALID",
                    f"table appears in multiple groups: {table_id}",
                )
            mapping[table_id] = group_id
    return mapping


def _warning_rows(counter: Counter[str]) -> list[dict[str, Any]]:
    return [
        {"reason_code": reason, "count": int(counter[reason])}
        for reason in sorted(counter)
        if counter[reason] > 0
    ]


def _extract_records(
    document_sha256: str,
    pages: list[dict[str, Any]],
    tables: list[dict[str, Any]],
    groups: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    word_index = _build_word_index(pages)
    table_to_group = _group_map(groups)
    warning_counts: Counter[str] = Counter()
    facts: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []

    for table in tables:
        table_id = str(table["table_id"])
        page_no = int(table["page_no"])
        unit, unit_ambiguous = _detect_unique_pattern(
            _table_texts(table), _UNIT_PATTERNS
        )
        if unit_ambiguous:
            warning_counts["AMBIGUOUS_RAW_UNIT"] += 1

        scope, scope_ambiguous = _detect_unique_pattern(
            _table_scope_texts(table), _SCOPE_PATTERNS
        )
        if scope_ambiguous:
            warning_counts["AMBIGUOUS_RAW_SCOPE"] += 1

        column_periods: dict[int, str] = {}
        rows = list(table.get("rows") or ())
        for row_index, row in enumerate(rows):
            if _is_period_header_row(row):
                for cell in row.get("cells") or ():
                    if (
                        cell.get("role") == "VALUE"
                        and str(cell.get("text", "")).strip()
                    ):
                        column_periods[int(cell["column_index"])] = str(
                            cell["text"]
                        ).strip()
                continue

            label_cells = [
                cell
                for cell in row.get("cells") or ()
                if cell.get("role") == "LABEL"
                and str(cell.get("text", "")).strip()
            ]
            value_cells = [
                cell
                for cell in row.get("cells") or ()
                if cell.get("role") == "VALUE"
                and str(cell.get("text", "")).strip()
            ]

            numeric_values = [
                cell for cell in value_cells if bool(cell.get("numeric"))
            ]
            if numeric_values and not label_cells:
                warning_counts["ROW_WITHOUT_LABEL"] += 1
                continue
            if not label_cells:
                continue

            metric_name = _normalize_space(
                " ".join(
                    str(cell["text"])
                    for cell in sorted(
                        label_cells,
                        key=lambda cell: (
                            int(cell.get("column_index", 0)),
                            float(_bbox_values(cell.get("bbox"))[0]),
                            str(cell.get("cell_id", "")),
                        ),
                    )
                )
            )
            if not metric_name:
                continue

            for value_cell in sorted(
                numeric_values,
                key=lambda cell: (
                    int(cell["column_index"]),
                    str(cell.get("cell_id", "")),
                ),
            ):
                raw_value = str(value_cell["text"]).strip()
                parsed = parse_numeric_value(raw_value)
                if parsed is None:
                    warning_counts["VALUE_PARSE_FAILED"] += 1
                    continue

                column_index = int(value_cell["column_index"])
                raw_period = column_periods.get(column_index)
                if raw_period is None:
                    raw_period, period_ambiguous = _period_from_geometry(
                        table, row_index, column_index
                    )
                    if period_ambiguous:
                        warning_counts["AMBIGUOUS_RAW_PERIOD"] += 1

                row_id = str(row["row_id"])
                value_cell_id = str(value_cell["cell_id"])
                raw_fact_id = _fact_id(
                    document_sha256,
                    table_id,
                    row_id,
                    value_cell_id,
                )
                source_refs = _validate_and_merge_refs(
                    label_cells + [value_cell],
                    word_index,
                    page_no,
                )
                evidence_id = _evidence_id(raw_fact_id, source_refs)
                evidence_bbox = _bbox_union(
                    [
                        _bbox_values(cell.get("bbox"))
                        for cell in label_cells + [value_cell]
                    ]
                )

                label_ids = [
                    str(cell["cell_id"])
                    for cell in sorted(
                        label_cells,
                        key=lambda cell: (
                            int(cell.get("column_index", 0)),
                            str(cell.get("cell_id", "")),
                        ),
                    )
                ]
                fact = {
                    "raw_fact_id": raw_fact_id,
                    "document_sha256": document_sha256,
                    "raw_metric_name": metric_name,
                    "raw_value": raw_value,
                    "parsed_numeric_value": parsed,
                    "raw_unit": None if unit_ambiguous else unit,
                    "raw_period_label": raw_period,
                    "raw_scope": None if scope_ambiguous else scope,
                    "table_id": table_id,
                    "table_group_id": table_to_group.get(table_id),
                    "page_no": page_no,
                    "row_id": row_id,
                    "row_index": int(row["row_index"]),
                    "column_index": column_index,
                    "label_cell_ids": label_ids,
                    "value_cell_id": value_cell_id,
                    "evidence_id": evidence_id,
                }
                evidence_row = {
                    "evidence_id": evidence_id,
                    "document_sha256": document_sha256,
                    "extraction_version": EXTRACTOR_VERSION,
                    "page_no": page_no,
                    "bbox": evidence_bbox,
                    "raw_text": metric_name + " | " + raw_value,
                    "table_id": table_id,
                    "row_id": row_id,
                    "row_index": int(row["row_index"]),
                    "column_index": column_index,
                    "label_cell_ids": label_ids,
                    "value_cell_id": value_cell_id,
                    "source_words": source_refs,
                }
                facts.append(fact)
                evidence.append(evidence_row)

    facts.sort(
        key=lambda row: (
            int(row["page_no"]),
            str(row["table_id"]),
            int(row["row_index"]),
            int(row["column_index"]),
            str(row["raw_fact_id"]),
        )
    )
    evidence_by_id = {row["evidence_id"]: row for row in evidence}
    evidence = [evidence_by_id[fact["evidence_id"]] for fact in facts]
    return facts, evidence, _warning_rows(warning_counts)


def _load_inputs(
    native_artifact_dir: Path,
    table_artifact_dir: Path,
) -> tuple[Any, Any, list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    native = load_native_document(native_artifact_dir)
    table_artifact = load_reconstructed_tables(table_artifact_dir)
    if native.document_sha256 != table_artifact.document_sha256:
        raise RawFactError(
            "P6_INPUT_ARTIFACT_INVALID",
            "P3/P5 document SHA mismatch",
        )
    pages = _read_jsonl(native.pages_path)
    tables = _read_jsonl(table_artifact.tables_path)
    groups = _read_jsonl(table_artifact.groups_path)
    if len(pages) != native.page_count:
        raise RawFactError(
            "P6_INPUT_ARTIFACT_INVALID",
            "P3 page count mismatch",
        )
    return native, table_artifact, pages, tables, groups


def _input_fingerprints(native: Any, table_artifact: Any) -> dict[str, str]:
    return {
        "p3_pages_sha256": _sha256_file(native.pages_path),
        "p3_sections_sha256": _sha256_file(native.sections_path),
        "p5_tables_sha256": _sha256_file(table_artifact.tables_path),
        "p5_groups_sha256": _sha256_file(table_artifact.groups_path),
        "p5_manifest_sha256": _sha256_file(table_artifact.manifest_path),
        "p3_parser_version": P3_PARSER_VERSION,
        "p5_reconstruction_version": RECONSTRUCTION_VERSION,
        "p6_extractor_version": EXTRACTOR_VERSION,
    }


def load_raw_facts(
    artifact_dir: str | Path,
    native_artifact_dir: str | Path,
    reconstructed_table_dir: str | Path,
) -> RawFactArtifact:
    directory = Path(artifact_dir).expanduser().resolve()
    native_dir = Path(native_artifact_dir).expanduser().resolve()
    table_dir = Path(reconstructed_table_dir).expanduser().resolve()
    manifest_path = directory / "fact_manifest.json"
    facts_path = directory / "raw_facts.jsonl"
    evidence_path = directory / "evidence.jsonl"

    if not all(path.is_file() for path in (manifest_path, facts_path, evidence_path)):
        raise RawFactError(
            "P6_ARTIFACT_INCOMPLETE_OR_CORRUPT",
            f"missing P6 artifact files under {directory}",
        )

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RawFactError(
            "P6_ARTIFACT_INCOMPLETE_OR_CORRUPT",
            f"cannot read P6 manifest: {exc}",
        ) from exc

    native, table_artifact, pages, tables, groups = _load_inputs(
        native_dir, table_dir
    )
    document_sha256 = native.document_sha256
    if (
        manifest.get("schema_version") != SCHEMA_VERSION
        or manifest.get("extractor_version") != EXTRACTOR_VERSION
        or manifest.get("document_sha256") != document_sha256
        or directory.name != document_sha256
    ):
        raise RawFactError(
            "P6_ARTIFACT_INCOMPLETE_OR_CORRUPT",
            "P6 manifest identity/schema/version mismatch",
        )

    fingerprints = _input_fingerprints(native, table_artifact)
    if dict(manifest.get("input_fingerprints") or {}) != fingerprints:
        raise RawFactError(
            "P6_ARTIFACT_INCOMPLETE_OR_CORRUPT",
            "P6 input fingerprints changed",
        )

    facts = _read_jsonl(facts_path)
    evidence = _read_jsonl(evidence_path)
    if (
        int(manifest.get("fact_count", -1)) != len(facts)
        or int(manifest.get("evidence_count", -1)) != len(evidence)
        or len(facts) != len(evidence)
    ):
        raise RawFactError(
            "P6_ARTIFACT_INCOMPLETE_OR_CORRUPT",
            "P6 fact/evidence count mismatch",
        )

    seen_fact_ids: set[str] = set()
    seen_evidence_ids: set[str] = set()
    evidence_by_id: dict[str, dict[str, Any]] = {}
    for row in evidence:
        evidence_id = str(row.get("evidence_id") or "")
        if not evidence_id or evidence_id in seen_evidence_ids:
            raise RawFactError(
                "P6_ARTIFACT_INCOMPLETE_OR_CORRUPT",
                "duplicate/missing evidence_id",
            )
        seen_evidence_ids.add(evidence_id)
        evidence_by_id[evidence_id] = row

    for fact in facts:
        fact_id = str(fact.get("raw_fact_id") or "")
        if not fact_id or fact_id in seen_fact_ids:
            raise RawFactError(
                "P6_ARTIFACT_INCOMPLETE_OR_CORRUPT",
                "duplicate/missing raw_fact_id",
            )
        seen_fact_ids.add(fact_id)
        expected_fact_id = _fact_id(
            document_sha256,
            str(fact["table_id"]),
            str(fact["row_id"]),
            str(fact["value_cell_id"]),
        )
        if fact_id != expected_fact_id:
            raise RawFactError(
                "P6_ARTIFACT_INCOMPLETE_OR_CORRUPT",
                "raw_fact_id mismatch",
            )
        parsed = parse_numeric_value(str(fact["raw_value"]))
        if parsed is None or parsed != str(fact["parsed_numeric_value"]):
            raise RawFactError(
                "P6_ARTIFACT_INCOMPLETE_OR_CORRUPT",
                "parsed_numeric_value mismatch",
            )
        evidence_row = evidence_by_id.get(str(fact["evidence_id"]))
        if evidence_row is None:
            raise RawFactError(
                "P6_ARTIFACT_INCOMPLETE_OR_CORRUPT",
                "fact references missing evidence",
            )
        expected_evidence_id = _evidence_id(
            fact_id,
            list(evidence_row.get("source_words") or ()),
        )
        if expected_evidence_id != str(evidence_row["evidence_id"]):
            raise RawFactError(
                "P6_ARTIFACT_INCOMPLETE_OR_CORRUPT",
                "evidence_id mismatch",
            )

    expected_facts, expected_evidence, expected_warnings = _extract_records(
        document_sha256,
        pages,
        tables,
        groups,
    )
    if facts != expected_facts:
        raise RawFactError(
            "P6_ARTIFACT_INCOMPLETE_OR_CORRUPT",
            "persisted raw facts differ from deterministic extraction",
        )
    if evidence != expected_evidence:
        raise RawFactError(
            "P6_ARTIFACT_INCOMPLETE_OR_CORRUPT",
            "persisted evidence differs from deterministic extraction",
        )
    if list(manifest.get("warnings") or ()) != expected_warnings:
        raise RawFactError(
            "P6_ARTIFACT_INCOMPLETE_OR_CORRUPT",
            "P6 warning summary mismatch",
        )

    return RawFactArtifact(
        artifact_dir=directory,
        document_sha256=document_sha256,
        fact_count=len(facts),
        evidence_count=len(evidence),
        extractor_version=EXTRACTOR_VERSION,
        facts_path=facts_path,
        evidence_path=evidence_path,
        manifest_path=manifest_path,
        timings_ms=dict(manifest.get("timings_ms") or {}),
        warnings=tuple(expected_warnings),
    )


def extract_raw_facts(
    native_artifact_dir: str | Path,
    reconstructed_table_dir: str | Path,
    fact_root: str | Path,
) -> RawFactArtifact:
    native_dir = Path(native_artifact_dir).expanduser().resolve()
    table_dir = Path(reconstructed_table_dir).expanduser().resolve()
    root = Path(fact_root).expanduser().resolve()

    total_start = time.perf_counter_ns()
    native, table_artifact, pages, tables, groups = _load_inputs(
        native_dir, table_dir
    )
    final_dir = root / native.document_sha256

    if final_dir.exists():
        return load_raw_facts(final_dir, native_dir, table_dir)

    extract_start = time.perf_counter_ns()
    facts, evidence, warnings = _extract_records(
        native.document_sha256,
        pages,
        tables,
        groups,
    )
    extract_ms = round(
        (time.perf_counter_ns() - extract_start) / 1_000_000.0, 3
    )

    root.mkdir(parents=True, exist_ok=True)
    temp_dir = root / f".{native.document_sha256}.{uuid.uuid4().hex}.tmp"
    temp_dir.mkdir(parents=False, exist_ok=False)

    try:
        persist_start = time.perf_counter_ns()
        facts_path = temp_dir / "raw_facts.jsonl"
        evidence_path = temp_dir / "evidence.jsonl"
        manifest_path = temp_dir / "fact_manifest.json"
        _write_jsonl(facts_path, facts)
        _write_jsonl(evidence_path, evidence)
        timings = {
            "extract": extract_ms,
            "persist": round(
                (time.perf_counter_ns() - persist_start) / 1_000_000.0,
                3,
            ),
        }
        timings["total"] = round(
            (time.perf_counter_ns() - total_start) / 1_000_000.0,
            3,
        )
        _write_json(
            manifest_path,
            {
                "schema_version": SCHEMA_VERSION,
                "extractor_version": EXTRACTOR_VERSION,
                "document_sha256": native.document_sha256,
                "p3_artifact_dir": str(native_dir),
                "p5_artifact_dir": str(table_dir),
                "input_fingerprints": _input_fingerprints(
                    native, table_artifact
                ),
                "fact_count": len(facts),
                "evidence_count": len(evidence),
                "tables_with_facts": len(
                    {str(fact["table_id"]) for fact in facts}
                ),
                "facts_file": "raw_facts.jsonl",
                "evidence_file": "evidence.jsonl",
                "warnings": warnings,
                "timings_ms": timings,
            },
        )
        os.replace(temp_dir, final_dir)
        return load_raw_facts(final_dir, native_dir, table_dir)
    except Exception as exc:
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        if isinstance(exc, RawFactError):
            raise
        raise RawFactError("P6_PERSIST_FAILED", str(exc)) from exc
