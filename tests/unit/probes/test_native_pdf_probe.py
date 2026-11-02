from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path

import pymupdf
import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = REPO_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from financial_filing_data_foundation.probes import native_pdf_probe
from financial_filing_data_foundation.probes.native_pdf_probe import (
    SCHEMA_VERSION,
    probe_pdf,
    write_result_json,
)


REQUIRED_TOP_LEVEL = {
    "schema_version",
    "file",
    "sha256",
    "sha256_after",
    "source_unchanged",
    "file_size",
    "page_count",
    "environment",
    "document_signals",
    "constraints",
    "timings_ms",
    "totals",
    "summary",
    "warnings",
    "errors",
    "pages",
}

REQUIRED_TIMINGS = {
    "open",
    "text",
    "layout",
    "drawings_images",
    "table_candidate_signals",
    "hash_before",
    "hash_after",
    "total",
}

REQUIRED_TOTALS = {
    "native_chars",
    "words",
    "blocks",
    "drawings",
    "images",
}

REQUIRED_PAGE = {
    "page_no",
    "width",
    "height",
    "rotation",
    "native_char_count",
    "word_count",
    "block_count",
    "drawing_count",
    "image_count",
    "bbox",
    "cheap_table_candidate_signals",
    "warnings",
    "elapsed_ms",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _make_text_pdf(path: Path, *, rotation: int = 0) -> None:
    document = pymupdf.open()
    page = document.new_page(width=320, height=480)
    page.insert_text((30, 50), "Revenue 2024 1,234 2023 1,100")
    page.insert_text((30, 80), "Net income 2024 456 2023 400")
    if rotation:
        page.set_rotation(rotation)
    document.save(path)
    document.close()


def _make_image_only_pdf(path: Path) -> None:
    document = pymupdf.open()
    page = document.new_page(width=200, height=200)

    pixmap = pymupdf.Pixmap(
        pymupdf.csRGB,
        pymupdf.IRect(0, 0, 20, 20),
        False,
    )
    pixmap.clear_with(220)
    page.insert_image(pymupdf.Rect(20, 20, 180, 180), pixmap=pixmap)

    document.save(path)
    document.close()


def _schema_shape(result: dict) -> dict:
    return {
        "top": set(result),
        "timings": set(result["timings_ms"]),
        "totals": set(result["totals"]),
        "page": set(result["pages"][0]) if result["pages"] else set(),
        "table_signals": (
            set(result["pages"][0]["cheap_table_candidate_signals"])
            if result["pages"]
            else set()
        ),
    }


def test_valid_tiny_pdf(tmp_path: Path) -> None:
    source = tmp_path / "valid.pdf"
    _make_text_pdf(source)

    result = probe_pdf(source)

    assert result["schema_version"] == SCHEMA_VERSION
    assert result["page_count"] == 1
    assert result["source_unchanged"] is True
    assert result["totals"]["native_chars"] > 0
    assert result["totals"]["words"] > 0
    assert result["totals"]["blocks"] > 0
    assert result["pages"][0]["page_no"] == 1
    assert result["errors"] == []


def test_image_only_page_is_reported_without_ocr(tmp_path: Path) -> None:
    source = tmp_path / "image_only.pdf"
    _make_image_only_pdf(source)

    result = probe_pdf(source)

    assert result["page_count"] == 1
    assert result["pages"][0]["native_char_count"] == 0
    assert result["pages"][0]["image_count"] >= 1
    assert "NATIVE_TEXT_EMPTY" in result["pages"][0]["warnings"]
    assert result["constraints"]["ocr_used"] is False
    assert result["constraints"]["docling_used"] is False


def test_rotated_page_records_rotation(tmp_path: Path) -> None:
    source = tmp_path / "rotated.pdf"
    _make_text_pdf(source, rotation=90)

    result = probe_pdf(source)

    assert result["page_count"] == 1
    assert result["pages"][0]["rotation"] == 90


def test_malformed_but_openable_trailing_bytes(tmp_path: Path) -> None:
    source = tmp_path / "trailing_bytes.pdf"
    _make_text_pdf(source)

    with source.open("ab") as handle:
        handle.write(b"\n% FFDF P0 trailing malformed bytes\nBROKEN_TRAILER_TOKEN")

    result = probe_pdf(source)

    assert result["page_count"] == 1
    assert result["source_unchanged"] is True
    assert result["totals"]["native_chars"] > 0


def test_json_schema_is_deterministic(tmp_path: Path) -> None:
    source = tmp_path / "schema.pdf"
    _make_text_pdf(source)

    first = probe_pdf(source)
    second = probe_pdf(source)

    assert set(first) == REQUIRED_TOP_LEVEL
    assert set(first["timings_ms"]) == REQUIRED_TIMINGS
    assert set(first["totals"]) == REQUIRED_TOTALS
    assert set(first["pages"][0]) == REQUIRED_PAGE
    assert _schema_shape(first) == _schema_shape(second)


def test_source_pdf_is_immutable(tmp_path: Path) -> None:
    source = tmp_path / "immutable.pdf"
    _make_text_pdf(source)

    before_hash = _sha256(source)
    before_stat = source.stat()

    result = probe_pdf(source)

    after_hash = _sha256(source)
    after_stat = source.stat()

    assert result["source_unchanged"] is True
    assert result["sha256"] == before_hash == after_hash
    assert before_stat.st_size == after_stat.st_size
    assert before_stat.st_mtime_ns == after_stat.st_mtime_ns


def test_write_result_json_does_not_overwrite_source(tmp_path: Path) -> None:
    source = tmp_path / "source.pdf"
    _make_text_pdf(source)
    result = probe_pdf(source)

    with pytest.raises(ValueError, match="must not overwrite"):
        write_result_json(result, source)


def test_write_result_json_creates_machine_readable_artifact(tmp_path: Path) -> None:
    source = tmp_path / "source.pdf"
    output = tmp_path / "out" / "result.json"
    _make_text_pdf(source)

    result = probe_pdf(source)
    written = write_result_json(result, output, pretty=True)

    assert written == output.resolve()
    assert output.is_file()
    assert '"schema_version": "p0-native-pdf-probe-v1"' in output.read_text(
        encoding="utf-8"
    )


def test_heavy_paths_are_absent() -> None:
    assert importlib.util.find_spec("docling") is None
    assert importlib.util.find_spec("torch") is None
    assert importlib.util.find_spec("pypdf") is None

    source = Path(native_pdf_probe.__file__).read_text(encoding="utf-8").lower()
    forbidden_imports = (
        "import docling",
        "from docling",
        "import torch",
        "from torch",
        "import tableformer",
        "from tableformer",
        "import openai",
        "from openai",
        "import anthropic",
        "from anthropic",
        "import gemini",
        "from gemini",
    )
    for forbidden in forbidden_imports:
        assert forbidden not in source
