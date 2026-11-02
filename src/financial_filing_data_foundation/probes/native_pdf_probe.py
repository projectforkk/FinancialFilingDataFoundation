from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import time
from pathlib import Path
from typing import Any, Iterable, Sequence

import pymupdf


SCHEMA_VERSION = "p0-native-pdf-probe-v1"

_NUMERIC_TOKEN = re.compile(
    r"^[+\-－−]?(?:[(（])?(?:\d{1,3}(?:[,，]\d{3})+|\d+)(?:\.\d+)?%?(?:[)）])?$"
)


def _elapsed_ms(start_ns: int, end_ns: int) -> float:
    return round((end_ns - start_ns) / 1_000_000.0, 3)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_numeric_token(text: str) -> bool:
    value = text.strip()
    if not value or value in {"-", "—", "－", "−"}:
        return False
    return bool(_NUMERIC_TOKEN.match(value))


def _bbox_is_valid(item: Sequence[Any]) -> bool:
    if len(item) < 4:
        return False
    try:
        x0, y0, x1, y1 = (float(item[0]), float(item[1]), float(item[2]), float(item[3]))
    except (TypeError, ValueError):
        return False
    return (
        all(math.isfinite(value) for value in (x0, y0, x1, y1))
        and x1 >= x0
        and y1 >= y0
    )


def _drawing_rule_counts(drawings: Iterable[dict[str, Any]]) -> tuple[int, int]:
    horizontal = 0
    vertical = 0

    for drawing in drawings:
        for item in drawing.get("items", ()):
            if not item:
                continue
            kind = item[0]

            if kind == "l" and len(item) >= 3:
                start, end = item[1], item[2]
                dx = abs(float(start.x) - float(end.x))
                dy = abs(float(start.y) - float(end.y))
                if dx >= 12.0 and dy <= 1.5:
                    horizontal += 1
                if dy >= 12.0 and dx <= 1.5:
                    vertical += 1

            elif kind == "re" and len(item) >= 2:
                rect = item[1]
                if float(rect.width) >= 12.0:
                    horizontal += 2
                if float(rect.height) >= 12.0:
                    vertical += 2

    return horizontal, vertical


def _numeric_x_clusters(
    words: Sequence[Sequence[Any]],
    tolerance: float = 14.0,
) -> tuple[int, int]:
    x_positions = sorted(
        float(word[0])
        for word in words
        if len(word) >= 5 and _is_numeric_token(str(word[4]))
    )
    if not x_positions:
        return 0, 0

    clusters: list[list[float]] = [[x_positions[0]]]
    for x_value in x_positions[1:]:
        current = clusters[-1]
        center = sum(current) / len(current)
        if abs(x_value - center) <= tolerance:
            current.append(x_value)
        else:
            clusters.append([x_value])

    stable = [cluster for cluster in clusters if len(cluster) >= 3]
    return len(stable), max((len(cluster) for cluster in stable), default=0)


def _cheap_table_signals(
    words: Sequence[Sequence[Any]],
    drawings: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    numeric_word_count = sum(
        1
        for word in words
        if len(word) >= 5 and _is_numeric_token(str(word[4]))
    )
    word_count = len(words)
    horizontal_rules, vertical_rules = _drawing_rule_counts(drawings)
    numeric_x_clusters, max_cluster_size = _numeric_x_clusters(words)
    numeric_ratio = numeric_word_count / word_count if word_count else 0.0

    likely_table_page = bool(
        (numeric_word_count >= 12 and numeric_x_clusters >= 2)
        or (
            numeric_word_count >= 8
            and horizontal_rules >= 3
            and vertical_rules >= 2
        )
    )

    return {
        "numeric_word_count": numeric_word_count,
        "numeric_word_ratio": round(numeric_ratio, 6),
        "horizontal_rule_count": horizontal_rules,
        "vertical_rule_count": vertical_rules,
        "stable_numeric_x_cluster_count": numeric_x_clusters,
        "max_numeric_x_cluster_size": max_cluster_size,
        "likely_table_page": likely_table_page,
    }


def _read_mupdf_warnings() -> list[str]:
    try:
        raw = pymupdf.TOOLS.mupdf_warnings()
    except Exception:
        return []

    if not raw:
        return []
    if isinstance(raw, str):
        return [line.strip() for line in raw.splitlines() if line.strip()]
    if isinstance(raw, (list, tuple)):
        return [str(item).strip() for item in raw if str(item).strip()]
    return [str(raw).strip()]


def probe_pdf(file_path: str | Path) -> dict[str, Any]:
    path = Path(file_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a PDF file: {path}")

    total_start = time.perf_counter_ns()
    stat_before = path.stat()

    hash_before_start = time.perf_counter_ns()
    sha_before = _sha256(path)
    hash_before_end = time.perf_counter_ns()

    open_start = time.perf_counter_ns()
    document = pymupdf.open(path)
    open_end = time.perf_counter_ns()

    if document.needs_pass:
        document.close()
        raise ValueError("Password-protected PDF is unsupported by the P0 probe")

    page_count = int(document.page_count)
    repaired = bool(getattr(document, "is_repaired", False))

    pages: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    text_ns = 0
    layout_ns = 0
    drawings_images_ns = 0
    table_signals_ns = 0

    totals = {
        "native_chars": 0,
        "words": 0,
        "blocks": 0,
        "drawings": 0,
        "images": 0,
    }
    native_text_pages = 0
    empty_text_pages = 0
    likely_table_pages = 0

    try:
        for page_index in range(page_count):
            page_start = time.perf_counter_ns()
            page = document.load_page(page_index)

            text_start = time.perf_counter_ns()
            native_text = page.get_text("text", sort=False)
            text_end = time.perf_counter_ns()
            text_ns += text_end - text_start

            layout_start = time.perf_counter_ns()
            words = page.get_text("words", sort=False)
            blocks = page.get_text("blocks", sort=False)
            invalid_word_bboxes = sum(1 for word in words if not _bbox_is_valid(word))
            invalid_block_bboxes = sum(1 for block in blocks if not _bbox_is_valid(block))
            layout_end = time.perf_counter_ns()
            layout_ns += layout_end - layout_start

            drawing_start = time.perf_counter_ns()
            drawings = page.get_drawings()
            images = page.get_images(full=True)
            drawing_end = time.perf_counter_ns()
            drawings_images_ns += drawing_end - drawing_start

            table_start = time.perf_counter_ns()
            table_signals = _cheap_table_signals(words, drawings)
            table_end = time.perf_counter_ns()
            table_signals_ns += table_end - table_start

            char_count = len(native_text)
            word_count = len(words)
            block_count = len(blocks)
            drawing_count = len(drawings)
            image_count = len(images)

            totals["native_chars"] += char_count
            totals["words"] += word_count
            totals["blocks"] += block_count
            totals["drawings"] += drawing_count
            totals["images"] += image_count

            page_warnings: list[str] = []
            if native_text.strip():
                native_text_pages += 1
            else:
                empty_text_pages += 1
                page_warnings.append("NATIVE_TEXT_EMPTY")

            if invalid_word_bboxes:
                page_warnings.append("WORD_BBOX_INVALID")
            if invalid_block_bboxes:
                page_warnings.append("BLOCK_BBOX_INVALID")
            if table_signals["likely_table_page"]:
                likely_table_pages += 1

            for code in page_warnings:
                warnings.append({"page_no": page_index + 1, "code": code})

            page_end = time.perf_counter_ns()
            pages.append(
                {
                    "page_no": page_index + 1,
                    "width": round(float(page.rect.width), 3),
                    "height": round(float(page.rect.height), 3),
                    "rotation": int(page.rotation),
                    "native_char_count": char_count,
                    "word_count": word_count,
                    "block_count": block_count,
                    "drawing_count": drawing_count,
                    "image_count": image_count,
                    "bbox": {
                        "invalid_word_count": invalid_word_bboxes,
                        "invalid_block_count": invalid_block_bboxes,
                    },
                    "cheap_table_candidate_signals": table_signals,
                    "warnings": page_warnings,
                    "elapsed_ms": _elapsed_ms(page_start, page_end),
                }
            )
    finally:
        document.close()

    mupdf_warnings = _read_mupdf_warnings()
    for warning in mupdf_warnings:
        warnings.append({"page_no": None, "code": "MUPDF_WARNING", "detail": warning})

    stat_after = path.stat()

    hash_after_start = time.perf_counter_ns()
    sha_after = _sha256(path)
    hash_after_end = time.perf_counter_ns()

    source_unchanged = (
        sha_before == sha_after
        and stat_before.st_size == stat_after.st_size
        and stat_before.st_mtime_ns == stat_after.st_mtime_ns
    )

    total_end = time.perf_counter_ns()

    return {
        "schema_version": SCHEMA_VERSION,
        "file": str(path),
        "sha256": sha_before,
        "sha256_after": sha_after,
        "source_unchanged": source_unchanged,
        "file_size": stat_before.st_size,
        "page_count": page_count,
        "environment": {
            "python_executable": sys.executable,
            "python_version": sys.version.split()[0],
            "pymupdf_version": pymupdf.__version__,
        },
        "document_signals": {
            "mupdf_repaired": repaired,
            "mupdf_warning_count": len(mupdf_warnings),
        },
        "constraints": {
            "ocr_used": False,
            "torch_used": False,
            "docling_used": False,
            "tableformer_used": False,
            "external_ai_api_used": False,
            "codex_vision_used": False,
        },
        "timings_ms": {
            "open": _elapsed_ms(open_start, open_end),
            "text": round(text_ns / 1_000_000.0, 3),
            "layout": round(layout_ns / 1_000_000.0, 3),
            "drawings_images": round(drawings_images_ns / 1_000_000.0, 3),
            "table_candidate_signals": round(table_signals_ns / 1_000_000.0, 3),
            "hash_before": _elapsed_ms(hash_before_start, hash_before_end),
            "hash_after": _elapsed_ms(hash_after_start, hash_after_end),
            "total": _elapsed_ms(total_start, total_end),
        },
        "totals": totals,
        "summary": {
            "native_text_pages": native_text_pages,
            "empty_text_pages": empty_text_pages,
            "likely_table_pages": likely_table_pages,
            "warning_count": len(warnings),
        },
        "warnings": warnings,
        "errors": [],
        "pages": pages,
    }


def write_result_json(
    result: dict[str, Any],
    output_path: str | Path,
    *,
    pretty: bool = False,
) -> Path:
    output = Path(output_path).expanduser().resolve()
    source = Path(result["file"]).resolve()

    if output == source:
        raise ValueError("Output path must not overwrite the source PDF")

    output.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(
        result,
        ensure_ascii=False,
        indent=2 if pretty else None,
        sort_keys=False,
    )

    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(payload + "\n", encoding="utf-8")
    temporary.replace(output)
    return output


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="FFDF P0 lightweight native PDF feasibility probe"
    )
    parser.add_argument("pdf", type=Path, help="Source PDF to inspect")
    parser.add_argument(
        "--output",
        type=Path,
        help="Write full machine-readable JSON result to this path",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON",
    )
    args = parser.parse_args(argv)

    try:
        result = probe_pdf(args.pdf)
        if not result["source_unchanged"]:
            raise RuntimeError("Source PDF changed while probing")

        if args.output:
            output = write_result_json(result, args.output, pretty=args.pretty)
            print(
                json.dumps(
                    {
                        "output": str(output),
                        "sha256": result["sha256"],
                        "page_count": result["page_count"],
                        "total_ms": result["timings_ms"]["total"],
                        "warning_count": result["summary"]["warning_count"],
                        "source_unchanged": result["source_unchanged"],
                    },
                    ensure_ascii=False,
                )
            )
        else:
            print(
                json.dumps(
                    result,
                    ensure_ascii=False,
                    indent=2 if args.pretty else None,
                )
            )
    except Exception as exc:
        print(
            json.dumps(
                {
                    "status": "ERROR",
                    "type": type(exc).__name__,
                    "message": str(exc),
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
