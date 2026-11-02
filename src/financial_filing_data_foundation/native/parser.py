from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import time
import uuid
from pathlib import Path
from typing import Any, Sequence

import pymupdf

from financial_filing_data_foundation.sections import detect_sections
from .models import (
    NativeDocumentArtifact,
    NativeParseError,
    P3_PARSER_VERSION,
    SCHEMA_VERSION,
)
from .search import build_search_db


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _bbox(
    raw: Sequence[Any] | None,
    width: float,
    height: float,
    warnings: list[str],
) -> list[float] | None:
    if raw is None or len(raw) < 4:
        warnings.append("INVALID_BBOX")
        return None
    try:
        x0, y0, x1, y1 = (float(raw[0]), float(raw[1]), float(raw[2]), float(raw[3]))
    except (TypeError, ValueError):
        warnings.append("INVALID_BBOX")
        return None
    values = (x0, y0, x1, y1)
    if not all(math.isfinite(value) for value in values) or x1 < x0 or y1 < y0:
        warnings.append("INVALID_BBOX")
        return None
    clamped = [
        max(0.0, min(width, x0)),
        max(0.0, min(height, y0)),
        max(0.0, min(width, x1)),
        max(0.0, min(height, y1)),
    ]
    if any(abs(a - b) > 1e-6 for a, b in zip(values, clamped)):
        warnings.append("BBOX_CLAMPED")
    return [round(value, 3) for value in clamped]


def _line_text(spans: list[dict[str, Any]]) -> str:
    return "".join(str(span.get("text", "")) for span in spans).strip()


def _extract_page(page: pymupdf.Page) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    width = float(page.rect.width)
    height = float(page.rect.height)
    page_warnings: list[str] = []

    text_flags = pymupdf.TEXTFLAGS_DICT & ~pymupdf.TEXT_PRESERVE_IMAGES
    text_page = page.get_textpage(flags=text_flags)
    layout = page.get_text("dict", textpage=text_page, sort=False)
    native_words = page.get_text("words", textpage=text_page, sort=False)

    words: list[dict[str, Any]] = []
    for word in native_words:
        bbox = _bbox(word[:4], width, height, page_warnings)
        if bbox is None or len(word) < 8:
            continue
        words.append(
            {
                "text": str(word[4]),
                "bbox": bbox,
                "block_no": int(word[5]),
                "line_no": int(word[6]),
                "word_no": int(word[7]),
            }
        )

    blocks: list[dict[str, Any]] = []
    line_count = 0
    span_count = 0
    for block_no, native_block in enumerate(layout.get("blocks", ())):
        if int(native_block.get("type", 0)) != 0:
            continue
        block_bbox = _bbox(
            native_block.get("bbox"),
            width,
            height,
            page_warnings,
        )
        if block_bbox is None:
            continue

        lines: list[dict[str, Any]] = []
        for line_index, native_line in enumerate(native_block.get("lines", ())):
            line_warnings: list[str] = []
            line_bbox = _bbox(
                native_line.get("bbox"),
                width,
                height,
                line_warnings,
            )
            page_warnings.extend(line_warnings)
            if line_bbox is None:
                continue

            spans: list[dict[str, Any]] = []
            for span_index, native_span in enumerate(native_line.get("spans", ())):
                span_warnings: list[str] = []
                span_bbox = _bbox(
                    native_span.get("bbox"),
                    width,
                    height,
                    span_warnings,
                )
                page_warnings.extend(span_warnings)
                if span_bbox is None:
                    continue
                origin = native_span.get("origin")
                origin_value = (
                    [round(float(origin[0]), 3), round(float(origin[1]), 3)]
                    if isinstance(origin, (list, tuple)) and len(origin) >= 2
                    else None
                )
                spans.append(
                    {
                        "span_no": span_index,
                        "text": str(native_span.get("text", "")),
                        "bbox": span_bbox,
                        "font": str(native_span.get("font", "")),
                        "size": round(float(native_span.get("size", 0.0)), 3),
                        "flags": int(native_span.get("flags", 0) or 0),
                        "color": int(native_span.get("color", 0) or 0),
                        "ascender": (
                            None
                            if native_span.get("ascender") is None
                            else round(float(native_span["ascender"]), 6)
                        ),
                        "descender": (
                            None
                            if native_span.get("descender") is None
                            else round(float(native_span["descender"]), 6)
                        ),
                        "origin": origin_value,
                    }
                )
            line_count += 1
            span_count += len(spans)
            lines.append(
                {
                    "line_no": line_index,
                    "bbox": line_bbox,
                    "text": _line_text(spans),
                    "spans": spans,
                    "repeated_header_footer": False,
                }
            )

        block_text = "\n".join(
            line["text"] for line in lines if line["text"]
        ).strip()
        blocks.append(
            {
                "block_no": block_no,
                "bbox": block_bbox,
                "type": "text",
                "text": block_text,
                "lines": lines,
                "reading_order_index": -1,
            }
        )

    blocks.sort(
        key=lambda block: (
            round(float(block["bbox"][1]) / 3.0),
            float(block["bbox"][1]),
            float(block["bbox"][0]),
            int(block["block_no"]),
        )
    )
    for index, block in enumerate(blocks):
        block["reading_order_index"] = index

    text = "\n".join(
        block["text"] for block in blocks if block["text"]
    ).strip()
    if not text:
        page_warnings.append("PAGE_TEXT_EMPTY")

    page_record = {
        "page_no": int(page.number) + 1,
        "width": round(width, 3),
        "height": round(height, 3),
        "rotation": int(page.rotation),
        "native_text_available": bool(text),
        "native_char_count": len(text),
        "word_count": len(words),
        "block_count": len(blocks),
        "line_count": line_count,
        "span_count": span_count,
        "image_count": len(page.get_images(full=True)),
        "drawing_count": len(page.get_cdrawings()),
        "text": text,
        "words": words,
        "blocks": blocks,
        "warnings": sorted(set(page_warnings)),
    }
    warnings = [
        {"page_no": int(page.number) + 1, "code": code}
        for code in sorted(set(page_warnings))
    ]
    return page_record, warnings


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def _jsonl_record(row: dict[str, Any]) -> str:
    serialized = json.dumps(
        row,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    # JSON permits these Unicode separators inside strings, but many line readers
    # (including Python str.splitlines) interpret them as record boundaries.
    return (
        serialized.replace("\u0085", "\\u0085")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(_jsonl_record(row) + "\n")


def load_native_document(artifact_dir: str | Path) -> NativeDocumentArtifact:
    directory = Path(artifact_dir).expanduser().resolve()
    manifest = directory / "document.json"
    if not manifest.is_file():
        raise NativeParseError("ARTIFACT_WRITE_FAILED", f"missing manifest: {manifest}")
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise NativeParseError(
            "ARTIFACT_WRITE_FAILED",
            f"unsupported native artifact schema: {payload.get('schema_version')}",
        )
    return NativeDocumentArtifact(
        artifact_dir=directory,
        document_sha256=str(payload["document_sha256"]),
        file_size=int(payload["file_size"]),
        page_count=int(payload["page_count"]),
        parser_version=str(payload["parser_version"]),
        pages_path=directory / "pages.jsonl",
        sections_path=directory / "sections.jsonl",
        search_db_path=directory / "search.sqlite",
        document_path=manifest,
        timings_ms=dict(payload.get("timings_ms") or {}),
        warnings=tuple(payload.get("warnings") or ()),
    )


def parse_native_document(
    pdf_path: str | Path,
    artifact_root: str | Path,
) -> NativeDocumentArtifact:
    source = Path(pdf_path).expanduser().resolve()
    root = Path(artifact_root).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    if source.suffix.lower() != ".pdf":
        raise ValueError("P3 input must be a PDF")

    total_start = time.perf_counter_ns()
    before = source.stat()
    sha_before = _sha256(source)
    final_dir = root / sha_before

    if final_dir.exists():
        existing = load_native_document(final_dir)
        if (
            existing.document_sha256 == sha_before
            and existing.parser_version == P3_PARSER_VERSION
            and existing.file_size == before.st_size
        ):
            return existing
        raise NativeParseError(
            "ARTIFACT_WRITE_FAILED",
            f"existing artifact is incompatible: {final_dir}",
        )

    root.mkdir(parents=True, exist_ok=True)
    temp_dir = root / f".{sha_before}.{uuid.uuid4().hex}.tmp"
    temp_dir.mkdir(parents=False, exist_ok=False)
    warnings: list[dict[str, Any]] = []
    timings: dict[str, float] = {}

    try:
        open_start = time.perf_counter_ns()
        try:
            document = pymupdf.open(source)
        except Exception as exc:
            raise NativeParseError("PDF_OPEN_FAILED", str(exc)) from exc
        timings["open"] = round(
            (time.perf_counter_ns() - open_start) / 1_000_000.0, 3
        )
        try:
            if document.needs_pass:
                raise NativeParseError(
                    "PDF_ENCRYPTED_UNSUPPORTED",
                    "password-protected PDF is unsupported in P3",
                )
            if document.is_repaired:
                warnings.append({"page_no": None, "code": "PDF_REPAIRED"})

            extract_start = time.perf_counter_ns()
            pages: list[dict[str, Any]] = []
            for page_no in range(document.page_count):
                page = document.load_page(page_no)
                page_record, page_warnings = _extract_page(page)
                pages.append(page_record)
                warnings.extend(page_warnings)
            timings["native_extract"] = round(
                (time.perf_counter_ns() - extract_start) / 1_000_000.0, 3
            )
            page_count = document.page_count
        finally:
            document.close()

        section_start = time.perf_counter_ns()
        sections, repeated_keys = detect_sections(sha_before, pages)
        for page in pages:
            page_no = int(page["page_no"])
            for block in page["blocks"]:
                block_no = int(block["block_no"])
                for line_index, line in enumerate(block["lines"]):
                    if (page_no, block_no, line_index) in repeated_keys:
                        line["repeated_header_footer"] = True
        timings["section"] = round(
            (time.perf_counter_ns() - section_start) / 1_000_000.0, 3
        )

        persist_start = time.perf_counter_ns()
        pages_path = temp_dir / "pages.jsonl"
        sections_path = temp_dir / "sections.jsonl"
        search_path = temp_dir / "search.sqlite"
        _write_jsonl(pages_path, pages)
        _write_jsonl(sections_path, sections)
        build_search_db(search_path, sha_before, pages, sections)

        after = source.stat()
        sha_after = _sha256(source)
        if (
            sha_after != sha_before
            or after.st_size != before.st_size
            or after.st_mtime_ns != before.st_mtime_ns
        ):
            raise NativeParseError(
                "SOURCE_CHANGED_DURING_PARSE",
                "source PDF changed during P3 extraction",
            )

        timings["persist"] = round(
            (time.perf_counter_ns() - persist_start) / 1_000_000.0, 3
        )
        timings["total"] = round(
            (time.perf_counter_ns() - total_start) / 1_000_000.0, 3
        )

        manifest_payload = {
            "schema_version": SCHEMA_VERSION,
            "document_sha256": sha_before,
            "file_size": before.st_size,
            "page_count": page_count,
            "parser_version": P3_PARSER_VERSION,
            "source_path": str(source),
            "pages_file": "pages.jsonl",
            "sections_file": "sections.jsonl",
            "search_db_file": "search.sqlite",
            "timings_ms": timings,
            "warnings": warnings,
            "section_count": len(sections),
        }
        _write_json(temp_dir / "document.json", manifest_payload)
        os.replace(temp_dir, final_dir)
        return load_native_document(final_dir)
    except Exception:
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        raise
