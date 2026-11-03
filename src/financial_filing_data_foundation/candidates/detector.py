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
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from financial_filing_data_foundation.native.models import (
    P3_PARSER_VERSION,
    SCHEMA_VERSION as P3_SCHEMA_VERSION,
)
from financial_filing_data_foundation.native.parser import load_native_document

from .models import (
    DETECTOR_VERSION,
    SCHEMA_VERSION,
    TableCandidateArtifact,
    TableCandidateError,
)


_NUMERIC_RE = re.compile(
    r"""^
    (?:
      [¥￥$€£]?
      [-−]?
      (?:
        \d{1,3}(?:[,，]\d{3})+|\d+
      )
      (?:\.\d+)?
      %?
      |
      \(
        [¥￥$€£]?
        (?:
          \d{1,3}(?:[,，]\d{3})+|\d+
        )
        (?:\.\d+)?
        %?
      \)
    )
    $""",
    re.VERBOSE,
)
_TOKEN_RE = re.compile(r"[^\s]+")
_DOTTED_RE = re.compile(r"(?:\.{3,}|…{2,}|·{3,})")

_FINANCIAL_KEYWORDS = (
    "资产",
    "负债",
    "权益",
    "收入",
    "营业",
    "利润",
    "现金流",
    "本期",
    "上期",
    "期末",
    "期初",
    "人民币",
    "港元",
    "合计",
    "项目",
    "assets",
    "liabilities",
    "equity",
    "revenue",
    "profit",
    "cash flow",
    "total",
    "year ended",
    "amount",
)

_SECTION_CONTEXT_KEYWORDS = (
    "财务报表",
    "财务报告",
    "合并资产负债表",
    "利润表",
    "现金流量表",
    "financial statements",
    "notes to financial statements",
)


def is_numeric_token(text: str) -> bool:
    token = text.strip().replace(" ", "")
    if not token or token in {"-", "−", "—", "–"}:
        return False
    return bool(_NUMERIC_RE.fullmatch(token))


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
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError(f"line {line_no} is not an object")
                rows.append(value)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
        raise TableCandidateError(
            "P4_ARTIFACT_INCOMPLETE_OR_CORRUPT",
            f"cannot read JSONL {path.name}: {exc}",
        ) from exc
    return rows


def _tokens(text: str) -> list[str]:
    return [match.group(0) for match in _TOKEN_RE.finditer(text) if match.group(0).strip()]


def _line_metrics(
    line: dict[str, Any],
    line_words: list[dict[str, Any]],
) -> dict[str, Any]:
    tokens = [str(word.get("text", "")).strip() for word in line_words]
    tokens = [token for token in tokens if token]
    if not tokens:
        tokens = _tokens(str(line.get("text", "")))

    numeric_words = [
        word
        for word in line_words
        if is_numeric_token(str(word.get("text", "")))
    ]
    numeric_count = len(numeric_words)
    if not line_words:
        numeric_count = sum(1 for token in tokens if is_numeric_token(token))

    density = numeric_count / len(tokens) if tokens else 0.0

    sorted_words = sorted(
        line_words,
        key=lambda word: (
            float((word.get("bbox") or [0, 0, 0, 0])[0]),
            int(word.get("word_no", 0)),
        ),
    )
    gaps: list[float] = []
    heights: list[float] = []
    for word in sorted_words:
        bbox = word.get("bbox") or [0, 0, 0, 0]
        heights.append(max(0.0, float(bbox[3]) - float(bbox[1])))
    for left, right in zip(sorted_words, sorted_words[1:]):
        left_bbox = left.get("bbox") or [0, 0, 0, 0]
        right_bbox = right.get("bbox") or [0, 0, 0, 0]
        gaps.append(max(0.0, float(right_bbox[0]) - float(left_bbox[2])))
    median_height = statistics.median(heights) if heights else 8.0
    significant_gap_count = sum(
        1 for gap in gaps if gap >= max(12.0, median_height * 1.5)
    )

    numeric_x = [
        round(float((word.get("bbox") or [0, 0, 0, 0])[0]), 3)
        for word in numeric_words
    ]
    text = str(line.get("text", ""))
    toc_like = bool(_DOTTED_RE.search(text)) and numeric_count <= 1

    return {
        "token_count": len(tokens),
        "numeric_count": numeric_count,
        "numeric_density": density,
        "numeric_x": numeric_x,
        "significant_gap_count": significant_gap_count,
        "toc_like": toc_like,
        "text_length": len(text.strip()),
    }


def _anchor_bin(x: float) -> int:
    # 12pt bins are intentionally coarse: P4 needs stable alignment signals,
    # not cell/column reconstruction.
    return int(round(x / 12.0))


def _column_anchor_count(line_metrics: list[dict[str, Any]]) -> int:
    per_anchor_lines: dict[int, set[int]] = defaultdict(set)
    for line_index, metrics in enumerate(line_metrics):
        for x in metrics["numeric_x"]:
            per_anchor_lines[_anchor_bin(float(x))].add(line_index)
    return sum(1 for line_ids in per_anchor_lines.values() if len(line_ids) >= 2)


def _financial_keyword_hits(text: str) -> list[str]:
    lowered = text.lower()
    return sorted(
        {
            keyword
            for keyword in _FINANCIAL_KEYWORDS
            if keyword.lower() in lowered
        },
        key=lambda value: value.lower(),
    )


def _section_context(
    page_no: int,
    sections: list[dict[str, Any]],
) -> bool:
    for section in sections:
        if not (
            int(section.get("page_start", 0))
            <= page_no
            <= int(section.get("page_end", 0))
        ):
            continue
        title = str(section.get("raw_title", "")).lower()
        if any(keyword.lower() in title for keyword in _SECTION_CONTEXT_KEYWORDS):
            return True
    return False


def _block_metrics(
    page: dict[str, Any],
    block: dict[str, Any],
) -> dict[str, Any]:
    block_no = int(block["block_no"])
    words_by_line: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for word in page.get("words", ()):
        if int(word.get("block_no", -1)) == block_no:
            words_by_line[int(word.get("line_no", -1))].append(word)

    metrics: list[dict[str, Any]] = []
    lines = list(block.get("lines", ()))
    for line_index, line in enumerate(lines):
        metrics.append(_line_metrics(line, words_by_line.get(line_index, [])))

    numeric_line_count = sum(
        1
        for item in metrics
        if item["numeric_count"] >= 2 and item["numeric_density"] >= 0.20
    )
    strong_numeric_line_count = sum(
        1
        for item in metrics
        if item["numeric_count"] >= 2 and item["numeric_density"] >= 0.30
    )
    numeric_token_count = sum(int(item["numeric_count"]) for item in metrics)
    token_count = sum(int(item["token_count"]) for item in metrics)
    toc_line_count = sum(1 for item in metrics if item["toc_like"])
    text = str(block.get("text", ""))
    keyword_hits = _financial_keyword_hits(text)
    anchor_count = _column_anchor_count(metrics)
    gap_lines = sum(
        1 for item in metrics if int(item["significant_gap_count"]) >= 2
    )
    prose_lines = sum(
        1
        for item in metrics
        if int(item["text_length"]) >= 80 and float(item["numeric_density"]) < 0.15
    )

    seed = (
        numeric_line_count >= 2
        or (
            numeric_token_count >= 4
            and strong_numeric_line_count >= 1
            and anchor_count >= 2
        )
        or (
            bool(keyword_hits)
            and numeric_line_count >= 1
            and numeric_token_count >= 2
        )
    )

    return {
        "block": block,
        "lines": lines,
        "line_metrics": metrics,
        "seed": seed,
        "numeric_line_count": numeric_line_count,
        "strong_numeric_line_count": strong_numeric_line_count,
        "numeric_token_count": numeric_token_count,
        "token_count": token_count,
        "toc_line_count": toc_line_count,
        "keyword_hits": keyword_hits,
        "anchor_count": anchor_count,
        "gap_lines": gap_lines,
        "prose_lines": prose_lines,
    }


def _vertical_gap(first: dict[str, Any], second: dict[str, Any]) -> float:
    a = first["block"].get("bbox") or [0, 0, 0, 0]
    b = second["block"].get("bbox") or [0, 0, 0, 0]
    return max(0.0, float(b[1]) - float(a[3]))


def _horizontal_overlap_ratio(first: dict[str, Any], second: dict[str, Any]) -> float:
    a = first["block"].get("bbox") or [0, 0, 0, 0]
    b = second["block"].get("bbox") or [0, 0, 0, 0]
    overlap = max(0.0, min(float(a[2]), float(b[2])) - max(float(a[0]), float(b[0])))
    min_width = min(
        max(1.0, float(a[2]) - float(a[0])),
        max(1.0, float(b[2]) - float(b[0])),
    )
    return overlap / min_width


def _group_seed_blocks(
    page: dict[str, Any],
    block_metrics: list[dict[str, Any]],
) -> list[list[dict[str, Any]]]:
    seeds = [item for item in block_metrics if item["seed"]]
    if not seeds:
        return []

    height = max(1.0, float(page.get("height", 1.0)))
    groups: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = [seeds[0]]

    for item in seeds[1:]:
        previous = current[-1]
        gap_ok = _vertical_gap(previous, item) <= height * 0.04
        overlap_ok = _horizontal_overlap_ratio(previous, item) >= 0.20
        anchor_ok = (
            int(previous["anchor_count"]) >= 2
            or int(item["anchor_count"]) >= 2
        )
        if gap_ok and (overlap_ok or anchor_ok):
            current.append(item)
        else:
            groups.append(current)
            current = [item]
    groups.append(current)
    return groups


def _candidate_id(
    document_sha256: str,
    page_no: int,
    bbox: list[float],
    block_nos: list[int],
) -> str:
    bbox_key = ",".join(f"{float(value):.3f}" for value in bbox)
    blocks_key = ",".join(str(value) for value in sorted(block_nos))
    payload = (
        document_sha256
        + "\0"
        + str(page_no)
        + "\0"
        + bbox_key
        + "\0"
        + blocks_key
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _bbox_overlap_ratio(first: list[float], second: list[float]) -> float:
    x0 = max(float(first[0]), float(second[0]))
    y0 = max(float(first[1]), float(second[1]))
    x1 = min(float(first[2]), float(second[2]))
    y1 = min(float(first[3]), float(second[3]))
    intersection = max(0.0, x1 - x0) * max(0.0, y1 - y0)
    first_area = max(1.0, float(first[2]) - float(first[0])) * max(
        1.0, float(first[3]) - float(first[1])
    )
    second_area = max(1.0, float(second[2]) - float(second[0])) * max(
        1.0, float(second[3]) - float(second[1])
    )
    return intersection / min(first_area, second_area)


def _distributed_page_candidate(
    document_sha256: str,
    page: dict[str, Any],
    block_metrics: list[dict[str, Any]],
    sections: list[dict[str, Any]],
    existing: list[dict[str, Any]],
) -> dict[str, Any] | None:
    numeric_blocks = [
        item for item in block_metrics if int(item["numeric_token_count"]) > 0
    ]
    numeric_token_count = sum(
        int(item["numeric_token_count"]) for item in numeric_blocks
    )
    if numeric_token_count < 12 or len(numeric_blocks) < 4:
        return None

    all_line_metrics = [
        metric for item in numeric_blocks for metric in item["line_metrics"]
    ]
    column_anchor_count = _column_anchor_count(all_line_metrics)
    if column_anchor_count < 2:
        return None

    page_no = int(page["page_no"])
    keyword_hits = _financial_keyword_hits(str(page.get("text", "")))
    section_context = _section_context(page_no, sections)
    if not keyword_hits and not section_context and numeric_token_count < 20:
        return None

    bboxes = [
        item["block"].get("bbox") or [0, 0, 0, 0]
        for item in numeric_blocks
    ]
    bbox = [
        round(min(float(value[0]) for value in bboxes), 3),
        round(min(float(value[1]) for value in bboxes), 3),
        round(max(float(value[2]) for value in bboxes), 3),
        round(max(float(value[3]) for value in bboxes), 3),
    ]
    block_nos = sorted(
        {int(item["block"]["block_no"]) for item in numeric_blocks}
    )

    # A strong local candidate already explains this region. Do not emit a
    # broader page fallback that would add no recall.
    if any(
        int(candidate["page_no"]) == page_no
        and _bbox_overlap_ratio(bbox, list(candidate["bbox"])) >= 0.70
        for candidate in existing
    ):
        return None

    numeric_line_count = sum(
        1
        for metric in all_line_metrics
        if int(metric["numeric_count"]) >= 1
    )
    word_count = sum(int(item["token_count"]) for item in numeric_blocks)
    drawing_count = int(page.get("drawing_count", 0) or 0)

    signals = ["DISTRIBUTED_NUMERIC_BLOCKS"]
    score = 3.0
    if numeric_token_count >= 20:
        score += 2.0
        signals.append("MANY_NUMERIC_TOKENS")
    if column_anchor_count >= 3:
        score += 2.0
        signals.append("MULTI_COLUMN_ALIGNMENT")
    if column_anchor_count >= 5:
        score += 1.0
        signals.append("MANY_COLUMN_ANCHORS")
    if keyword_hits:
        score += 1.5
        signals.append("FINANCIAL_KEYWORDS")
    if drawing_count >= 20:
        score += 0.5
        signals.append("DRAWING_DENSITY")
    if drawing_count >= 100:
        score += 0.5
        signals.append("HIGH_DRAWING_DENSITY")
    if section_context:
        score += 1.0
        signals.append("FINANCIAL_SECTION_CONTEXT")
    if column_anchor_count >= 2:
        score += 0.5
        signals.append("REPEATED_NUMERIC_ALIGNMENT")

    score = round(score, 3)
    return {
        "candidate_id": _candidate_id(
            document_sha256, page_no, bbox, block_nos
        ),
        "document_sha256": document_sha256,
        "page_no": page_no,
        "bbox": bbox,
        "block_nos": block_nos,
        "line_count": len(all_line_metrics),
        "word_count": word_count,
        "numeric_token_count": numeric_token_count,
        "numeric_line_count": numeric_line_count,
        "column_anchor_count": column_anchor_count,
        "drawing_count_page": drawing_count,
        "financial_keyword_hits": keyword_hits,
        "signals": sorted(set(signals)),
        "score": score,
        "candidate_class": "TABLE_LIKE" if score >= 4.0 else "REVIEW_CANDIDATE",
        "quality_signals": ["DISTRIBUTED_BLOCK_LAYOUT"],
    }


def _candidate_from_group(
    document_sha256: str,
    page: dict[str, Any],
    group: list[dict[str, Any]],
    sections: list[dict[str, Any]],
) -> dict[str, Any] | None:
    page_no = int(page["page_no"])
    bboxes = [item["block"].get("bbox") or [0, 0, 0, 0] for item in group]
    bbox = [
        round(min(float(item[0]) for item in bboxes), 3),
        round(min(float(item[1]) for item in bboxes), 3),
        round(max(float(item[2]) for item in bboxes), 3),
        round(max(float(item[3]) for item in bboxes), 3),
    ]
    block_nos = sorted(int(item["block"]["block_no"]) for item in group)
    line_metrics = [
        metric for item in group for metric in item["line_metrics"]
    ]
    line_count = len(line_metrics)
    word_count = sum(int(item["token_count"]) for item in group)
    numeric_token_count = sum(int(item["numeric_token_count"]) for item in group)
    numeric_line_count = sum(int(item["numeric_line_count"]) for item in group)
    strong_numeric_line_count = sum(
        int(item["strong_numeric_line_count"]) for item in group
    )
    keyword_hits = sorted(
        {keyword for item in group for keyword in item["keyword_hits"]},
        key=lambda value: value.lower(),
    )
    column_anchor_count = _column_anchor_count(line_metrics)
    gap_line_count = sum(int(item["gap_lines"]) for item in group)
    toc_line_count = sum(int(item["toc_line_count"]) for item in group)
    prose_lines = sum(int(item["prose_lines"]) for item in group)
    drawing_count = int(page.get("drawing_count", 0) or 0)
    section_context = _section_context(page_no, sections)

    score = 0.0
    signals: list[str] = []
    quality_signals: list[str] = []

    if numeric_line_count >= 3:
        score += 3.0
        signals.append("NUMERIC_DENSITY")
    if numeric_line_count >= 6:
        score += 2.0
        signals.append("MANY_NUMERIC_LINES")
    if strong_numeric_line_count >= 2 and "NUMERIC_DENSITY" not in signals:
        score += 1.5
        signals.append("NUMERIC_DENSITY")
    if column_anchor_count >= 3:
        score += 2.0
        signals.append("MULTI_COLUMN_ALIGNMENT")
    if column_anchor_count >= 5:
        score += 1.0
        signals.append("MANY_COLUMN_ANCHORS")
    if gap_line_count >= 2:
        score += 0.5
        signals.append("SPACING_GAPS")
    if keyword_hits:
        score += 1.5
        signals.append("FINANCIAL_KEYWORDS")
    if drawing_count >= 20:
        score += 0.5
        signals.append("DRAWING_DENSITY")
    if drawing_count >= 100:
        score += 0.5
        signals.append("HIGH_DRAWING_DENSITY")
    if section_context:
        score += 1.0
        signals.append("FINANCIAL_SECTION_CONTEXT")
    if column_anchor_count >= 2 and numeric_line_count >= 3:
        score += 0.5
        signals.append("REPEATED_NUMERIC_ALIGNMENT")

    if prose_lines > max(1, line_count // 2):
        score -= 2.0
        quality_signals.append("PROSE_DOMINANT")
    if toc_line_count > max(1, line_count // 2):
        score -= 1.0
        quality_signals.append("TOC_LIKE")
    if int(page.get("word_count", 0) or 0) < 10 and drawing_count >= 20:
        quality_signals.append("NON_TEXT_HEAVY_PAGE")

    score = round(score, 3)
    if score < 2.5:
        return None
    candidate_class = "TABLE_LIKE" if score >= 4.0 else "REVIEW_CANDIDATE"

    return {
        "candidate_id": _candidate_id(document_sha256, page_no, bbox, block_nos),
        "document_sha256": document_sha256,
        "page_no": page_no,
        "bbox": bbox,
        "block_nos": block_nos,
        "line_count": line_count,
        "word_count": word_count,
        "numeric_token_count": numeric_token_count,
        "numeric_line_count": numeric_line_count,
        "column_anchor_count": column_anchor_count,
        "drawing_count_page": drawing_count,
        "financial_keyword_hits": keyword_hits,
        "signals": sorted(set(signals)),
        "score": score,
        "candidate_class": candidate_class,
        "quality_signals": sorted(set(quality_signals)),
    }


def _load_p3_rows(native_artifact_dir: Path) -> tuple[Any, list[dict[str, Any]], list[dict[str, Any]]]:
    native = load_native_document(native_artifact_dir)
    pages = _read_jsonl(native.pages_path)
    sections = _read_jsonl(native.sections_path)
    if len(pages) != native.page_count:
        raise TableCandidateError(
            "P4_INPUT_ARTIFACT_INVALID",
            f"P3 page count mismatch: manifest={native.page_count}, rows={len(pages)}",
        )
    expected = list(range(1, native.page_count + 1))
    actual = [int(page.get("page_no", -1)) for page in pages]
    if actual != expected:
        raise TableCandidateError(
            "P4_INPUT_ARTIFACT_INVALID",
            "P3 pages.jsonl physical page sequence is invalid",
        )
    return native, pages, sections


def load_table_candidates(artifact_dir: str | Path) -> TableCandidateArtifact:
    directory = Path(artifact_dir).expanduser().resolve()
    manifest_path = directory / "candidate_manifest.json"
    candidates_path = directory / "candidates.jsonl"
    if not manifest_path.is_file() or not candidates_path.is_file():
        raise TableCandidateError(
            "P4_ARTIFACT_INCOMPLETE_OR_CORRUPT",
            f"missing P4 artifact files under {directory}",
        )
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TableCandidateError(
            "P4_ARTIFACT_INCOMPLETE_OR_CORRUPT",
            f"cannot read P4 manifest: {exc}",
        ) from exc

    document_sha256 = str(manifest.get("document_sha256") or "")
    if (
        manifest.get("schema_version") != SCHEMA_VERSION
        or manifest.get("detector_version") != DETECTOR_VERSION
        or manifest.get("p3_schema_version") != P3_SCHEMA_VERSION
        or manifest.get("p3_parser_version") != P3_PARSER_VERSION
        or directory.name != document_sha256
    ):
        raise TableCandidateError(
            "P4_ARTIFACT_INCOMPLETE_OR_CORRUPT",
            "P4 manifest identity/schema/version mismatch",
        )

    candidates = _read_jsonl(candidates_path)
    if int(manifest.get("candidate_count", -1)) != len(candidates):
        raise TableCandidateError(
            "P4_ARTIFACT_INCOMPLETE_OR_CORRUPT",
            "candidate_count does not match candidates.jsonl",
        )
    seen: set[str] = set()
    for row in candidates:
        candidate_id = str(row.get("candidate_id") or "")
        if (
            not candidate_id
            or candidate_id in seen
            or row.get("document_sha256") != document_sha256
            or int(row.get("page_no", 0)) < 1
        ):
            raise TableCandidateError(
                "P4_ARTIFACT_INCOMPLETE_OR_CORRUPT",
                "invalid candidate identity",
            )
        bbox = row.get("bbox")
        if not isinstance(bbox, list) or len(bbox) != 4:
            raise TableCandidateError(
                "P4_ARTIFACT_INCOMPLETE_OR_CORRUPT",
                "invalid candidate bbox",
            )
        seen.add(candidate_id)

    return TableCandidateArtifact(
        artifact_dir=directory,
        document_sha256=document_sha256,
        candidate_count=len(candidates),
        detector_version=DETECTOR_VERSION,
        candidates_path=candidates_path,
        manifest_path=manifest_path,
        timings_ms=dict(manifest.get("timings_ms") or {}),
        warnings=tuple(manifest.get("warnings") or ()),
    )


def detect_table_candidates(
    native_artifact_dir: str | Path,
    candidate_root: str | Path,
) -> TableCandidateArtifact:
    source_dir = Path(native_artifact_dir).expanduser().resolve()
    root = Path(candidate_root).expanduser().resolve()
    total_start = time.perf_counter_ns()

    native, pages, sections = _load_p3_rows(source_dir)
    final_dir = root / native.document_sha256

    if final_dir.exists():
        existing = load_table_candidates(final_dir)
        if existing.document_sha256 == native.document_sha256:
            return existing
        raise TableCandidateError(
            "P4_ARTIFACT_INCOMPLETE_OR_CORRUPT",
            f"existing P4 artifact incompatible: {final_dir}",
        )

    detect_start = time.perf_counter_ns()
    candidates: list[dict[str, Any]] = []
    for page in pages:
        block_metrics = [
            _block_metrics(page, block)
            for block in sorted(
                page.get("blocks", ()),
                key=lambda block: int(block.get("reading_order_index", 0)),
            )
        ]
        page_candidates: list[dict[str, Any]] = []
        for group in _group_seed_blocks(page, block_metrics):
            candidate = _candidate_from_group(
                native.document_sha256,
                page,
                group,
                sections,
            )
            if candidate is not None:
                page_candidates.append(candidate)

        distributed = _distributed_page_candidate(
            native.document_sha256,
            page,
            block_metrics,
            sections,
            page_candidates,
        )
        if distributed is not None:
            page_candidates.append(distributed)

        candidates.extend(page_candidates)

    candidates.sort(
        key=lambda row: (
            int(row["page_no"]),
            float(row["bbox"][1]),
            float(row["bbox"][0]),
            str(row["candidate_id"]),
        )
    )
    detect_ms = round((time.perf_counter_ns() - detect_start) / 1_000_000.0, 3)

    root.mkdir(parents=True, exist_ok=True)
    temp_dir = root / f".{native.document_sha256}.{uuid.uuid4().hex}.tmp"
    temp_dir.mkdir(parents=False, exist_ok=False)
    try:
        persist_start = time.perf_counter_ns()
        candidates_path = temp_dir / "candidates.jsonl"
        manifest_path = temp_dir / "candidate_manifest.json"
        _write_jsonl(candidates_path, candidates)
        timings = {
            "detect": detect_ms,
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
                "detector_version": DETECTOR_VERSION,
                "document_sha256": native.document_sha256,
                "p3_schema_version": P3_SCHEMA_VERSION,
                "p3_parser_version": P3_PARSER_VERSION,
                "p3_artifact_dir": str(source_dir),
                "page_count": native.page_count,
                "candidate_count": len(candidates),
                "candidates_file": "candidates.jsonl",
                "timings_ms": timings,
                "warnings": [],
            },
        )
        os.replace(temp_dir, final_dir)
        return load_table_candidates(final_dir)
    except Exception:
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        raise
