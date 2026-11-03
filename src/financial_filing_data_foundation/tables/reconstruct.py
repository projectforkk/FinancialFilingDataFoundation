from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
import statistics
import time
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from financial_filing_data_foundation.candidates.detector import is_numeric_token
from financial_filing_data_foundation.candidates.models import (
    DETECTOR_VERSION as P4_DETECTOR_VERSION,
)
from financial_filing_data_foundation.candidates import load_table_candidates
from financial_filing_data_foundation.native.models import (
    P3_PARSER_VERSION,
)
from financial_filing_data_foundation.native.parser import load_native_document

from .models import (
    RECONSTRUCTION_VERSION,
    SCHEMA_VERSION,
    ReconstructedTableArtifact,
    TableReconstructionError,
)


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
        raise TableReconstructionError(
            "P5_ARTIFACT_INCOMPLETE_OR_CORRUPT",
            f"cannot read JSONL {path.name}: {exc}",
        ) from exc
    return rows


def _bbox_values(raw: Any) -> list[float]:
    if not isinstance(raw, (list, tuple)) or len(raw) != 4:
        raise TableReconstructionError(
            "P5_INPUT_ARTIFACT_INVALID",
            "bbox must contain four values",
        )
    try:
        values = [float(value) for value in raw]
    except (TypeError, ValueError) as exc:
        raise TableReconstructionError(
            "P5_INPUT_ARTIFACT_INVALID",
            "bbox contains non-numeric value",
        ) from exc
    if (
        not all(math.isfinite(value) for value in values)
        or values[2] < values[0]
        or values[3] < values[1]
    ):
        raise TableReconstructionError(
            "P5_INPUT_ARTIFACT_INVALID",
            "bbox is non-finite or unordered",
        )
    return [round(value, 3) for value in values]


def _bbox_intersects(first: list[float], second: list[float]) -> bool:
    return (
        min(first[2], second[2]) >= max(first[0], second[0])
        and min(first[3], second[3]) >= max(first[1], second[1])
    )


def _bbox_union(values: list[list[float]]) -> list[float]:
    if not values:
        return [0.0, 0.0, 0.0, 0.0]
    return [
        round(min(value[0] for value in values), 3),
        round(min(value[1] for value in values), 3),
        round(max(value[2] for value in values), 3),
        round(max(value[3] for value in values), 3),
    ]


def _word_key(word: dict[str, Any]) -> tuple[int, int, int, int]:
    return (
        int(word["page_no"]),
        int(word["block_no"]),
        int(word["line_no"]),
        int(word["word_no"]),
    )


def _source_ref(word: dict[str, Any]) -> dict[str, Any]:
    return {
        "page_no": int(word["page_no"]),
        "block_no": int(word["block_no"]),
        "line_no": int(word["line_no"]),
        "word_no": int(word["word_no"]),
        "bbox": [round(float(value), 3) for value in word["bbox"]],
    }


def _source_ref_key(ref: dict[str, Any]) -> str:
    bbox = ",".join(f"{float(value):.3f}" for value in ref["bbox"])
    return (
        f"{int(ref['page_no'])}:"
        f"{int(ref['block_no'])}:"
        f"{int(ref['line_no'])}:"
        f"{int(ref['word_no'])}:"
        f"{bbox}"
    )


def _table_id(document_sha256: str, candidate_id: str) -> str:
    return _sha256_text(
        document_sha256
        + "\0"
        + candidate_id
        + "\0"
        + RECONSTRUCTION_VERSION
    )


def _row_id(table_id: str, row_index: int, bbox: list[float]) -> str:
    bbox_key = ",".join(f"{float(value):.3f}" for value in bbox)
    return _sha256_text(
        table_id + "\0" + str(row_index) + "\0" + bbox_key
    )


def _cell_id(
    table_id: str,
    row_index: int,
    column_index: int,
    source_words: list[dict[str, Any]],
) -> str:
    refs = "\0".join(_source_ref_key(ref) for ref in source_words)
    return _sha256_text(
        table_id
        + "\0"
        + str(row_index)
        + "\0"
        + str(column_index)
        + "\0"
        + refs
    )


def _group_id(document_sha256: str, table_ids: list[str]) -> str:
    return _sha256_text(
        document_sha256 + "\0" + "\0".join(table_ids)
    )


def _word_height(word: dict[str, Any]) -> float:
    bbox = word["bbox"]
    return max(0.0, float(bbox[3]) - float(bbox[1]))


def _word_y_center(word: dict[str, Any]) -> float:
    bbox = word["bbox"]
    return (float(bbox[1]) + float(bbox[3])) / 2.0


def _candidate_words(
    page: dict[str, Any],
    candidate: dict[str, Any],
) -> list[dict[str, Any]]:
    candidate_bbox = _bbox_values(candidate["bbox"])
    block_nos = {int(value) for value in candidate.get("block_nos", ())}
    if not block_nos:
        raise TableReconstructionError(
            "P5_INPUT_ARTIFACT_INVALID",
            "candidate block_nos must not be empty",
        )

    selected: list[dict[str, Any]] = []
    page_no = int(page["page_no"])
    for word in page.get("words", ()):
        block_no = int(word.get("block_no", -1))
        if block_no not in block_nos:
            continue
        bbox = _bbox_values(word.get("bbox"))
        if not _bbox_intersects(bbox, candidate_bbox):
            continue
        selected.append(
            {
                "text": str(word.get("text", "")),
                "bbox": bbox,
                "page_no": page_no,
                "block_no": block_no,
                "line_no": int(word.get("line_no", -1)),
                "word_no": int(word.get("word_no", -1)),
            }
        )

    selected.sort(
        key=lambda word: (
            round(_word_y_center(word), 3),
            float(word["bbox"][0]),
            int(word["block_no"]),
            int(word["line_no"]),
            int(word["word_no"]),
        )
    )
    return selected


def _cluster_visual_rows(
    words: list[dict[str, Any]],
) -> list[list[dict[str, Any]]]:
    if not words:
        return []
    heights = [
        height
        for height in (_word_height(word) for word in words)
        if math.isfinite(height) and height > 0
    ]
    median_height = statistics.median(heights) if heights else 8.0
    tolerance = max(3.0, median_height * 0.60)

    by_y = sorted(
        words,
        key=lambda word: (
            _word_y_center(word),
            float(word["bbox"][0]),
            _word_key(word),
        ),
    )
    rows: list[list[dict[str, Any]]] = []
    centers: list[float] = []
    for word in by_y:
        center = _word_y_center(word)
        if not rows or abs(center - centers[-1]) > tolerance:
            rows.append([word])
            centers.append(center)
            continue
        rows[-1].append(word)
        centers[-1] = statistics.median(
            [_word_y_center(item) for item in rows[-1]]
        )

    for row in rows:
        row.sort(
            key=lambda word: (
                float(word["bbox"][0]),
                int(word["block_no"]),
                int(word["line_no"]),
                int(word["word_no"]),
            )
        )
    rows.sort(
        key=lambda row: (
            min(float(word["bbox"][1]) for word in row),
            min(float(word["bbox"][0]) for word in row),
            _word_key(row[0]),
        )
    )
    return rows


def _value_anchor_clusters(
    rows: list[list[dict[str, Any]]],
    page_width: float,
    candidate_numeric_token_count: int,
) -> list[float]:
    tolerance = max(8.0, page_width * 0.025)
    points: list[tuple[float, int]] = []
    for row_index, row in enumerate(rows):
        for word in row:
            if is_numeric_token(str(word["text"])):
                points.append((float(word["bbox"][2]), row_index))
    if not points:
        return []

    points.sort(key=lambda item: (item[0], item[1]))
    clusters: list[list[tuple[float, int]]] = []
    for point in points:
        if not clusters:
            clusters.append([point])
            continue
        anchor = statistics.median([value for value, _ in clusters[-1]])
        if abs(point[0] - anchor) <= tolerance:
            clusters[-1].append(point)
        else:
            clusters.append([point])

    anchors: list[float] = []
    for cluster in clusters:
        distinct_rows = {row_index for _, row_index in cluster}
        if len(distinct_rows) >= 2 or (
            candidate_numeric_token_count < 4 and len(cluster) >= 1
        ):
            anchors.append(
                round(
                    float(statistics.median([value for value, _ in cluster])),
                    3,
                )
            )
    return sorted(anchors)


def _join_cell_text(words: list[dict[str, Any]]) -> str:
    values = [str(word["text"]).strip() for word in words]
    values = [value for value in values if value]
    text = " ".join(values)
    text = re.sub(r"\s+([,.;:，。；：%)）])", r"\1", text)
    text = re.sub(r"([（(¥￥$€£])\s+", r"\1", text)
    return text.strip()


def _build_cells(
    table_id: str,
    row_index: int,
    row: list[dict[str, Any]],
    anchors: list[float],
    page_width: float,
) -> list[dict[str, Any]]:
    tolerance = max(8.0, page_width * 0.025)
    assigned: dict[int, list[dict[str, Any]]] = defaultdict(list)
    first_anchor = anchors[0] if anchors else math.inf

    for word in row:
        text = str(word["text"]).strip()
        if is_numeric_token(text) and anchors:
            x1 = float(word["bbox"][2])
            nearest_index = min(
                range(len(anchors)),
                key=lambda index: (
                    abs(x1 - anchors[index]),
                    index,
                ),
            )
            if abs(x1 - anchors[nearest_index]) <= tolerance * 1.5:
                assigned[nearest_index + 1].append(word)
                continue

        if float(word["bbox"][0]) < first_anchor - tolerance:
            assigned[0].append(word)
        else:
            # Structural overflow cell. One deterministic column after values.
            assigned[len(anchors) + 1].append(word)

    cells: list[dict[str, Any]] = []
    for column_index in sorted(assigned):
        words = sorted(
            assigned[column_index],
            key=lambda word: (
                float(word["bbox"][0]),
                int(word["block_no"]),
                int(word["line_no"]),
                int(word["word_no"]),
            ),
        )
        refs = [_source_ref(word) for word in words]
        if column_index == 0:
            role = "LABEL"
        elif 1 <= column_index <= len(anchors):
            role = "VALUE"
        else:
            role = "UNASSIGNED"
        cells.append(
            {
                "cell_id": _cell_id(
                    table_id, row_index, column_index, refs
                ),
                "column_index": column_index,
                "role": role,
                "text": _join_cell_text(words),
                "bbox": _bbox_union(
                    [[float(value) for value in word["bbox"]] for word in words]
                ),
                "numeric": bool(words)
                and all(is_numeric_token(str(word["text"])) for word in words),
                "source_words": refs,
            }
        )
    return cells


def _reconstruct_candidate(
    document_sha256: str,
    page: dict[str, Any],
    candidate: dict[str, Any],
) -> dict[str, Any]:
    candidate_id = str(candidate["candidate_id"])
    table_id = _table_id(document_sha256, candidate_id)
    words = _candidate_words(page, candidate)
    rows = _cluster_visual_rows(words)
    page_width = float(page["width"])
    anchors = _value_anchor_clusters(
        rows,
        page_width,
        int(candidate.get("numeric_token_count", 0) or 0),
    )

    row_records: list[dict[str, Any]] = []
    unassigned_words = 0
    total_words = 0
    for row_index, row in enumerate(rows):
        bbox = _bbox_union(
            [[float(value) for value in word["bbox"]] for word in row]
        )
        cells = _build_cells(
            table_id, row_index, row, anchors, page_width
        )
        total_words += len(row)
        unassigned_words += sum(
            len(cell["source_words"])
            for cell in cells
            if cell["role"] == "UNASSIGNED"
        )
        numeric_values = sum(
            1
            for cell in cells
            if cell["role"] == "VALUE" and cell["numeric"]
        )
        if numeric_values == 0:
            row_signal = "NO_NUMERIC_VALUE"
        elif numeric_values == 1:
            row_signal = "HAS_NUMERIC_VALUE"
        else:
            row_signal = "MULTI_VALUE_ROW"

        row_records.append(
            {
                "row_id": _row_id(table_id, row_index, bbox),
                "row_index": row_index,
                "bbox": bbox,
                "cells": cells,
                "structural_signals": [row_signal],
            }
        )

    quality_signals: list[str] = []
    if not anchors:
        quality_signals.append("NO_VALUE_COLUMNS")
    if len(rows) < 3:
        quality_signals.append("LOW_ROW_COUNT")
    if rows and sum(
        1
        for record in row_records
        if "NO_NUMERIC_VALUE" in record["structural_signals"]
    ) > len(rows) // 2:
        quality_signals.append("SPARSE_ROWS")
    if total_words and unassigned_words / total_words > 0.25:
        quality_signals.append("MANY_UNASSIGNED_WORDS")
    if "DISTRIBUTED_NUMERIC_BLOCKS" in candidate.get("signals", ()):
        quality_signals.append("DISTRIBUTED_BLOCK_SOURCE")

    return {
        "table_id": table_id,
        "candidate_id": candidate_id,
        "document_sha256": document_sha256,
        "page_no": int(candidate["page_no"]),
        "page_width": round(float(page["width"]), 3),
        "page_height": round(float(page["height"]), 3),
        "bbox": _bbox_values(candidate["bbox"]),
        "source_block_nos": [int(value) for value in candidate["block_nos"]],
        "candidate_signals": sorted(
            {str(value) for value in candidate.get("signals", ())}
        ),
        "candidate_keywords": sorted(
            {
                str(value)
                for value in candidate.get("financial_keyword_hits", ())
            },
            key=lambda value: value.lower(),
        ),
        "value_column_count": len(anchors),
        "value_column_anchors": anchors,
        "row_count": len(row_records),
        "rows": row_records,
        "quality_signals": sorted(set(quality_signals)),
    }


def _anchors_compatible(first: dict[str, Any], second: dict[str, Any]) -> bool:
    first_anchors = [
        float(value) / max(1.0, float(first["page_width"]))
        for value in first["value_column_anchors"]
    ]
    second_anchors = [
        float(value) / max(1.0, float(second["page_width"]))
        for value in second["value_column_anchors"]
    ]
    if not first_anchors or len(first_anchors) != len(second_anchors):
        return False
    return all(
        abs(left - right) <= 0.04
        for left, right in zip(first_anchors, second_anchors)
    )


def _pair_continuation(
    first: dict[str, Any],
    second: dict[str, Any],
) -> tuple[float, list[str]] | None:
    if int(second["page_no"]) != int(first["page_no"]) + 1:
        return None
    if (
        int(first["value_column_count"]) <= 0
        or int(first["value_column_count"])
        != int(second["value_column_count"])
    ):
        return None
    if not _anchors_compatible(first, second):
        return None
    if float(first["bbox"][3]) < float(first["page_height"]) * 0.65:
        return None
    if float(second["bbox"][1]) > float(second["page_height"]) * 0.40:
        return None

    score = 3.0
    signals = [
        "ADJACENT_PAGES",
        "VALUE_COLUMNS_COMPATIBLE",
        "BOTTOM_TOP_CONTINUITY",
    ]
    first_keywords = {value.lower() for value in first["candidate_keywords"]}
    second_keywords = {value.lower() for value in second["candidate_keywords"]}
    if first_keywords and second_keywords and first_keywords & second_keywords:
        score += 0.5
        signals.append("KEYWORD_CONTINUITY")
    if len(first["value_column_anchors"]) >= 2:
        score += 0.5
        signals.append("REPEATED_NUMERIC_ANCHORS")
    return round(score, 3), signals


def _build_groups(
    document_sha256: str,
    tables: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_page: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for table in tables:
        by_page[int(table["page_no"])].append(table)
    for page_tables in by_page.values():
        page_tables.sort(key=lambda table: str(table["table_id"]))

    links: list[tuple[float, str, str, list[str]]] = []
    for page_no in sorted(by_page):
        next_page = page_no + 1
        if next_page not in by_page:
            continue
        for first in by_page[page_no]:
            for second in by_page[next_page]:
                result = _pair_continuation(first, second)
                if result is None:
                    continue
                score, signals = result
                links.append(
                    (
                        score,
                        str(first["table_id"]),
                        str(second["table_id"]),
                        signals,
                    )
                )

    # One predecessor / successor per fragment. Highest-score pair wins,
    # deterministic IDs break ties.
    links.sort(key=lambda item: (-item[0], item[1], item[2]))
    successor: dict[str, tuple[str, float, list[str]]] = {}
    predecessor: dict[str, str] = {}
    for score, first_id, second_id, signals in links:
        if first_id in successor or second_id in predecessor:
            continue
        successor[first_id] = (second_id, score, signals)
        predecessor[second_id] = first_id

    table_by_id = {str(table["table_id"]): table for table in tables}
    groups: list[dict[str, Any]] = []
    for table_id in sorted(table_by_id):
        if table_id in predecessor or table_id not in successor:
            continue
        members = [table_id]
        pair_scores: list[float] = []
        all_signals: set[str] = set()
        current = table_id
        while current in successor:
            next_id, score, signals = successor[current]
            members.append(next_id)
            pair_scores.append(score)
            all_signals.update(signals)
            current = next_id
        if len(members) < 2:
            continue
        member_tables = [table_by_id[value] for value in members]
        groups.append(
            {
                "group_id": _group_id(document_sha256, members),
                "document_sha256": document_sha256,
                "member_table_ids": members,
                "page_start": min(
                    int(table["page_no"]) for table in member_tables
                ),
                "page_end": max(
                    int(table["page_no"]) for table in member_tables
                ),
                "continuation_signals": sorted(all_signals),
                "score": round(
                    statistics.mean(pair_scores) if pair_scores else 0.0,
                    3,
                ),
            }
        )

    groups.sort(
        key=lambda group: (
            int(group["page_start"]),
            int(group["page_end"]),
            str(group["group_id"]),
        )
    )
    return groups


def _fingerprints(
    native_artifact_dir: Path,
    candidate_artifact_dir: Path,
) -> dict[str, str]:
    return {
        "p3_pages_sha256": _sha256_file(
            native_artifact_dir / "pages.jsonl"
        ),
        "p3_sections_sha256": _sha256_file(
            native_artifact_dir / "sections.jsonl"
        ),
        "p4_candidates_sha256": _sha256_file(
            candidate_artifact_dir / "candidates.jsonl"
        ),
        "p4_manifest_sha256": _sha256_file(
            candidate_artifact_dir / "candidate_manifest.json"
        ),
    }


def _load_inputs(
    native_artifact_dir: Path,
    candidate_artifact_dir: Path,
) -> tuple[
    Any,
    Any,
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[int, dict[str, Any]],
]:
    native = load_native_document(native_artifact_dir)
    candidate_artifact = load_table_candidates(candidate_artifact_dir)
    if native.document_sha256 != candidate_artifact.document_sha256:
        raise TableReconstructionError(
            "P5_INPUT_IDENTITY_MISMATCH",
            "P3 and P4 artifacts refer to different documents",
        )
    pages = _read_jsonl(native.pages_path)
    candidates = _read_jsonl(candidate_artifact.candidates_path)
    page_by_no = {int(page["page_no"]): page for page in pages}
    if len(page_by_no) != native.page_count:
        raise TableReconstructionError(
            "P5_INPUT_ARTIFACT_INVALID",
            "P3 page records are incomplete",
        )
    for candidate in candidates:
        if int(candidate["page_no"]) not in page_by_no:
            raise TableReconstructionError(
                "P5_INPUT_ARTIFACT_INVALID",
                "P4 candidate page not present in P3 artifact",
            )
    return native, candidate_artifact, pages, candidates, page_by_no


def _validate_source_refs(
    table: dict[str, Any],
    candidate: dict[str, Any],
    page: dict[str, Any],
) -> None:
    allowed_blocks = {int(value) for value in candidate["block_nos"]}
    candidate_bbox = _bbox_values(candidate["bbox"])
    valid_words: dict[str, dict[str, Any]] = {}
    page_no = int(page["page_no"])
    for word in page.get("words", ()):
        block_no = int(word.get("block_no", -1))
        if block_no not in allowed_blocks:
            continue
        bbox = _bbox_values(word.get("bbox"))
        if not _bbox_intersects(bbox, candidate_bbox):
            continue
        ref = {
            "page_no": page_no,
            "block_no": block_no,
            "line_no": int(word.get("line_no", -1)),
            "word_no": int(word.get("word_no", -1)),
            "bbox": bbox,
        }
        valid_words[_source_ref_key(ref)] = ref

    for row in table.get("rows", ()):
        for cell in row.get("cells", ()):
            for ref in cell.get("source_words", ()):
                if _source_ref_key(ref) not in valid_words:
                    raise TableReconstructionError(
                        "P5_ARTIFACT_INCOMPLETE_OR_CORRUPT",
                        "cell source word is outside current candidate scope",
                    )


def load_reconstructed_tables(
    artifact_dir: str | Path,
) -> ReconstructedTableArtifact:
    directory = Path(artifact_dir).expanduser().resolve()
    manifest_path = directory / "table_manifest.json"
    tables_path = directory / "tables.jsonl"
    groups_path = directory / "table_groups.jsonl"
    if not all(path.is_file() for path in (manifest_path, tables_path, groups_path)):
        raise TableReconstructionError(
            "P5_ARTIFACT_INCOMPLETE_OR_CORRUPT",
            f"missing P5 artifact files under {directory}",
        )

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TableReconstructionError(
            "P5_ARTIFACT_INCOMPLETE_OR_CORRUPT",
            f"cannot read P5 manifest: {exc}",
        ) from exc

    document_sha256 = str(manifest.get("document_sha256") or "")
    if (
        manifest.get("schema_version") != SCHEMA_VERSION
        or manifest.get("reconstruction_version") != RECONSTRUCTION_VERSION
        or manifest.get("p3_parser_version") != P3_PARSER_VERSION
        or manifest.get("p4_detector_version") != P4_DETECTOR_VERSION
        or directory.name != document_sha256
    ):
        raise TableReconstructionError(
            "P5_ARTIFACT_INCOMPLETE_OR_CORRUPT",
            "P5 manifest identity/schema/version mismatch",
        )

    native_dir = Path(str(manifest.get("p3_artifact_dir", ""))).expanduser().resolve()
    candidate_dir = Path(str(manifest.get("p4_artifact_dir", ""))).expanduser().resolve()
    native, candidate_artifact, pages, candidates, page_by_no = _load_inputs(
        native_dir, candidate_dir
    )
    if native.document_sha256 != document_sha256:
        raise TableReconstructionError(
            "P5_ARTIFACT_INCOMPLETE_OR_CORRUPT",
            "P5 document SHA does not match current P3 artifact",
        )

    current_fingerprints = _fingerprints(native_dir, candidate_dir)
    if current_fingerprints != dict(manifest.get("input_fingerprints") or {}):
        raise TableReconstructionError(
            "P5_INPUT_FINGERPRINT_MISMATCH",
            "P3/P4 input fingerprints changed after reconstruction",
        )

    tables = _read_jsonl(tables_path)
    groups = _read_jsonl(groups_path)
    if (
        int(manifest.get("table_count", -1)) != len(tables)
        or int(manifest.get("group_count", -1)) != len(groups)
    ):
        raise TableReconstructionError(
            "P5_ARTIFACT_INCOMPLETE_OR_CORRUPT",
            "table/group count mismatch",
        )

    candidate_by_id = {
        str(candidate["candidate_id"]): candidate
        for candidate in candidates
    }
    table_by_id: dict[str, dict[str, Any]] = {}
    for table in tables:
        candidate_id = str(table.get("candidate_id") or "")
        candidate = candidate_by_id.get(candidate_id)
        if candidate is None:
            raise TableReconstructionError(
                "P5_ARTIFACT_INCOMPLETE_OR_CORRUPT",
                "table references unknown candidate",
            )
        expected_table_id = _table_id(document_sha256, candidate_id)
        if str(table.get("table_id") or "") != expected_table_id:
            raise TableReconstructionError(
                "P5_ARTIFACT_INCOMPLETE_OR_CORRUPT",
                "table_id mismatch",
            )
        if int(table.get("page_no", 0)) != int(candidate["page_no"]):
            raise TableReconstructionError(
                "P5_ARTIFACT_INCOMPLETE_OR_CORRUPT",
                "table page does not match candidate",
            )
        if _bbox_values(table.get("bbox")) != _bbox_values(candidate["bbox"]):
            raise TableReconstructionError(
                "P5_ARTIFACT_INCOMPLETE_OR_CORRUPT",
                "table bbox does not match candidate",
            )

        rows = table.get("rows")
        if not isinstance(rows, list) or int(table.get("row_count", -1)) != len(rows):
            raise TableReconstructionError(
                "P5_ARTIFACT_INCOMPLETE_OR_CORRUPT",
                "row count mismatch",
            )
        for expected_index, row in enumerate(rows):
            if int(row.get("row_index", -1)) != expected_index:
                raise TableReconstructionError(
                    "P5_ARTIFACT_INCOMPLETE_OR_CORRUPT",
                    "row ordering/index mismatch",
                )
            row_bbox = _bbox_values(row.get("bbox"))
            if str(row.get("row_id") or "") != _row_id(
                expected_table_id, expected_index, row_bbox
            ):
                raise TableReconstructionError(
                    "P5_ARTIFACT_INCOMPLETE_OR_CORRUPT",
                    "row_id mismatch",
                )
            cells = row.get("cells")
            if not isinstance(cells, list):
                raise TableReconstructionError(
                    "P5_ARTIFACT_INCOMPLETE_OR_CORRUPT",
                    "row cells must be a list",
                )
            seen_columns: set[int] = set()
            for cell in cells:
                column_index = int(cell.get("column_index", -1))
                if column_index < 0 or column_index in seen_columns:
                    raise TableReconstructionError(
                        "P5_ARTIFACT_INCOMPLETE_OR_CORRUPT",
                        "invalid/duplicate cell column index",
                    )
                seen_columns.add(column_index)
                role = str(cell.get("role") or "")
                if role not in {"LABEL", "VALUE", "UNASSIGNED"}:
                    raise TableReconstructionError(
                        "P5_ARTIFACT_INCOMPLETE_OR_CORRUPT",
                        "invalid structural cell role",
                    )
                refs = cell.get("source_words")
                if not isinstance(refs, list) or not refs:
                    raise TableReconstructionError(
                        "P5_ARTIFACT_INCOMPLETE_OR_CORRUPT",
                        "cell source_words are missing",
                    )
                if str(cell.get("cell_id") or "") != _cell_id(
                    expected_table_id,
                    expected_index,
                    column_index,
                    refs,
                ):
                    raise TableReconstructionError(
                        "P5_ARTIFACT_INCOMPLETE_OR_CORRUPT",
                        "cell_id mismatch",
                    )

        _validate_source_refs(
            table,
            candidate,
            page_by_no[int(candidate["page_no"])],
        )
        table_by_id[expected_table_id] = table

    seen_group_ids: set[str] = set()
    for group in groups:
        members = group.get("member_table_ids")
        if not isinstance(members, list) or len(members) < 2:
            raise TableReconstructionError(
                "P5_ARTIFACT_INCOMPLETE_OR_CORRUPT",
                "group must contain at least two tables",
            )
        if any(str(value) not in table_by_id for value in members):
            raise TableReconstructionError(
                "P5_ARTIFACT_INCOMPLETE_OR_CORRUPT",
                "group references unknown table",
            )
        member_ids = [str(value) for value in members]
        expected_group_id = _group_id(document_sha256, member_ids)
        group_id = str(group.get("group_id") or "")
        if group_id != expected_group_id or group_id in seen_group_ids:
            raise TableReconstructionError(
                "P5_ARTIFACT_INCOMPLETE_OR_CORRUPT",
                "group_id mismatch/duplicate",
            )
        pages_for_group = [
            int(table_by_id[table_id]["page_no"])
            for table_id in member_ids
        ]
        if pages_for_group != sorted(pages_for_group) or any(
            right != left + 1
            for left, right in zip(pages_for_group, pages_for_group[1:])
        ):
            raise TableReconstructionError(
                "P5_ARTIFACT_INCOMPLETE_OR_CORRUPT",
                "group pages are not strictly adjacent",
            )
        if (
            int(group.get("page_start", -1)) != pages_for_group[0]
            or int(group.get("page_end", -1)) != pages_for_group[-1]
        ):
            raise TableReconstructionError(
                "P5_ARTIFACT_INCOMPLETE_OR_CORRUPT",
                "group page range mismatch",
            )
        seen_group_ids.add(group_id)

    return ReconstructedTableArtifact(
        artifact_dir=directory,
        document_sha256=document_sha256,
        table_count=len(tables),
        group_count=len(groups),
        reconstruction_version=RECONSTRUCTION_VERSION,
        tables_path=tables_path,
        groups_path=groups_path,
        manifest_path=manifest_path,
        timings_ms=dict(manifest.get("timings_ms") or {}),
        warnings=tuple(manifest.get("warnings") or ()),
    )


def reconstruct_tables(
    native_artifact_dir: str | Path,
    candidate_artifact_dir: str | Path,
    table_root: str | Path,
) -> ReconstructedTableArtifact:
    native_dir = Path(native_artifact_dir).expanduser().resolve()
    candidate_dir = Path(candidate_artifact_dir).expanduser().resolve()
    root = Path(table_root).expanduser().resolve()

    total_start = time.perf_counter_ns()
    native, candidate_artifact, pages, candidates, page_by_no = _load_inputs(
        native_dir, candidate_dir
    )
    fingerprints = _fingerprints(native_dir, candidate_dir)
    final_dir = root / native.document_sha256

    if final_dir.exists():
        return load_reconstructed_tables(final_dir)

    reconstruct_start = time.perf_counter_ns()
    tables: list[dict[str, Any]] = []
    for candidate in candidates:
        page = page_by_no[int(candidate["page_no"])]
        tables.append(
            _reconstruct_candidate(
                native.document_sha256,
                page,
                candidate,
            )
        )
    tables.sort(
        key=lambda table: (
            int(table["page_no"]),
            float(table["bbox"][1]),
            float(table["bbox"][0]),
            str(table["table_id"]),
        )
    )
    groups = _build_groups(native.document_sha256, tables)
    reconstruct_ms = round(
        (time.perf_counter_ns() - reconstruct_start) / 1_000_000.0,
        3,
    )

    root.mkdir(parents=True, exist_ok=True)
    temp_dir = root / f".{native.document_sha256}.{uuid.uuid4().hex}.tmp"
    temp_dir.mkdir(parents=False, exist_ok=False)
    try:
        persist_start = time.perf_counter_ns()
        tables_path = temp_dir / "tables.jsonl"
        groups_path = temp_dir / "table_groups.jsonl"
        manifest_path = temp_dir / "table_manifest.json"
        _write_jsonl(tables_path, tables)
        _write_jsonl(groups_path, groups)

        timings = {
            "reconstruct": reconstruct_ms,
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
                "reconstruction_version": RECONSTRUCTION_VERSION,
                "document_sha256": native.document_sha256,
                "p3_parser_version": P3_PARSER_VERSION,
                "p4_detector_version": P4_DETECTOR_VERSION,
                "p3_artifact_dir": str(native_dir),
                "p4_artifact_dir": str(candidate_dir),
                "input_fingerprints": fingerprints,
                "table_count": len(tables),
                "group_count": len(groups),
                "tables_file": "tables.jsonl",
                "groups_file": "table_groups.jsonl",
                "timings_ms": timings,
                "warnings": [],
            },
        )
        os.replace(temp_dir, final_dir)
        return load_reconstructed_tables(final_dir)
    except Exception:
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        raise
