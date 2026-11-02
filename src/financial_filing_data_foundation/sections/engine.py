from __future__ import annotations

import hashlib
import math
import re
import statistics
from collections import Counter
from typing import Any


_CHINESE_NUM = "一二三四五六七八九十百千万"
_NUMBERING_RULES: tuple[tuple[re.Pattern[str], int, str], ...] = (
    (re.compile(rf"^第[{_CHINESE_NUM}0-9]+章"), 1, "CN_CHAPTER"),
    (re.compile(rf"^第[{_CHINESE_NUM}0-9]+节"), 2, "CN_SECTION"),
    (re.compile(rf"^[{_CHINESE_NUM}]+、"), 1, "CN_ENUM"),
    (re.compile(rf"^[（(][{_CHINESE_NUM}0-9]+[)）]"), 2, "PAREN_ENUM"),
    (re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:[\.、\s]|$)"), 3, "ARABIC_3"),
    (re.compile(r"^(\d+)\.(\d+)(?:[\.、\s]|$)"), 2, "ARABIC_2"),
    (re.compile(r"^(\d+)[\.、]\s*"), 1, "ARABIC_1"),
)
_BOLD_NAMES = ("bold", "black", "semibold", "demibold", "heavy")


def _clean_text(value: str) -> str:
    return " ".join(value.replace("\u3000", " ").split()).strip()


def _line_font_size(line: dict[str, Any]) -> float:
    sizes = [
        float(span.get("size", 0.0))
        for span in line.get("spans", ())
        if str(span.get("text", "")).strip()
        and math.isfinite(float(span.get("size", 0.0)))
    ]
    return max(sizes, default=0.0)


def _line_is_bold(line: dict[str, Any]) -> bool:
    for span in line.get("spans", ()):
        text = str(span.get("text", "")).strip()
        if not text:
            continue
        font = str(span.get("font", "")).lower()
        flags = int(span.get("flags", 0) or 0)
        if any(token in font for token in _BOLD_NAMES) or (flags & 16):
            return True
    return False


def _numbering(text: str) -> tuple[int | None, str | None]:
    for pattern, level, name in _NUMBERING_RULES:
        if pattern.match(text):
            return level, name
    return None, None


def _repeated_header_footer_texts(
    pages: list[dict[str, Any]],
) -> frozenset[str]:
    page_count = len(pages)
    if page_count < 3:
        return frozenset()
    threshold = max(3, math.ceil(page_count * 0.30))
    per_text_pages: dict[str, set[int]] = {}

    for page in pages:
        height = float(page["height"])
        for block in page.get("blocks", ()):
            for line in block.get("lines", ()):
                text = _clean_text(str(line.get("text", "")))
                if not text or len(text) > 100:
                    continue
                bbox = line.get("bbox") or [0, 0, 0, 0]
                y0, y1 = float(bbox[1]), float(bbox[3])
                in_margin = y1 <= height * 0.12 or y0 >= height * 0.88
                if not in_margin:
                    continue
                normalized = re.sub(r"\d+", "#", text)
                if not normalized:
                    continue
                per_text_pages.setdefault(normalized, set()).add(int(page["page_no"]))

    return frozenset(
        text for text, page_set in per_text_pages.items() if len(page_set) >= threshold
    )


def _body_font_size(pages: list[dict[str, Any]]) -> float:
    samples: list[float] = []
    for page in pages:
        for block in page.get("blocks", ()):
            for line in block.get("lines", ()):
                for span in line.get("spans", ()):
                    text = _clean_text(str(span.get("text", "")))
                    if not text:
                        continue
                    size = float(span.get("size", 0.0))
                    if math.isfinite(size) and size > 0:
                        samples.extend([size] * min(len(text), 20))
    return float(statistics.median(samples)) if samples else 10.0


def detect_sections(
    document_sha256: str,
    pages: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], set[tuple[int, int, int]]]:
    repeated = _repeated_header_footer_texts(pages)
    body_size = _body_font_size(pages)
    candidates: list[dict[str, Any]] = []
    repeated_line_keys: set[tuple[int, int, int]] = set()

    for page in pages:
        page_no = int(page["page_no"])
        height = float(page["height"])
        for block in page.get("blocks", ()):
            block_no = int(block["block_no"])
            for line_index, line in enumerate(block.get("lines", ())):
                raw_title = _clean_text(str(line.get("text", "")))
                if not raw_title:
                    continue

                bbox = line.get("bbox") or [0, 0, 0, 0]
                normalized_margin = re.sub(r"\d+", "#", raw_title)
                in_margin = (
                    float(bbox[3]) <= height * 0.12
                    or float(bbox[1]) >= height * 0.88
                )
                if in_margin and normalized_margin in repeated:
                    repeated_line_keys.add((page_no, block_no, line_index))
                    continue

                explicit_level, numbering_signal = _numbering(raw_title)
                max_size = _line_font_size(line)
                bold = _line_is_bold(line)
                short = len(raw_title) <= 80
                size_ratio = max_size / body_size if body_size > 0 else 1.0

                signals: list[str] = []
                score = 0.0
                if numbering_signal:
                    signals.append(numbering_signal)
                    score += 3.0
                if size_ratio >= 1.35:
                    signals.append("FONT_LARGE")
                    score += 1.5
                elif size_ratio >= 1.12:
                    signals.append("FONT_ABOVE_BODY")
                    score += 0.75
                if bold:
                    signals.append("BOLD")
                    score += 0.75
                if short:
                    signals.append("SHORT")
                    score += 0.25
                if raw_title in {"目录", "目錄", "CONTENTS", "Contents"}:
                    signals.append("STRUCTURAL_TITLE")
                    score += 3.0

                if score < 2.5:
                    continue

                if explicit_level is not None:
                    level = explicit_level
                elif size_ratio >= 1.55:
                    level = 1
                elif size_ratio >= 1.25:
                    level = 2
                else:
                    level = 3

                bbox_key = ",".join(f"{float(v):.3f}" for v in bbox)
                digest = hashlib.sha256(
                    (
                        document_sha256
                        + "\0"
                        + str(page_no)
                        + "\0"
                        + bbox_key
                        + "\0"
                        + raw_title
                    ).encode("utf-8")
                ).hexdigest()

                candidates.append(
                    {
                        "section_id": digest,
                        "parent_section_id": None,
                        "raw_title": raw_title,
                        "normalized_title": None,
                        "level": int(level),
                        "page_start": page_no,
                        "page_end": page_no,
                        "bbox": [round(float(v), 3) for v in bbox],
                        "heading_score": round(score, 3),
                        "heading_signals": signals,
                        "quality_signals": [],
                        "_sort_key": (
                            page_no,
                            float(bbox[1]),
                            float(bbox[0]),
                            block_no,
                            line_index,
                        ),
                    }
                )

    candidates.sort(key=lambda item: item["_sort_key"])

    stack: list[dict[str, Any]] = []
    for section in candidates:
        while stack and int(stack[-1]["level"]) >= int(section["level"]):
            stack.pop()
        if stack:
            section["parent_section_id"] = stack[-1]["section_id"]
        stack.append(section)

    page_count = len(pages)
    for index, section in enumerate(candidates):
        next_start: int | None = None
        for other in candidates[index + 1 :]:
            if int(other["level"]) <= int(section["level"]):
                next_start = int(other["page_start"])
                break
        if next_start is None:
            page_end = page_count
        else:
            page_end = max(int(section["page_start"]), next_start - 1)
        section["page_end"] = page_end
        section.pop("_sort_key", None)

    return candidates, repeated_line_keys
