from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path

import pymupdf
import pytest

from financial_filing_data_foundation.native import (
    NativeParseError,
    P3_PARSER_VERSION,
    load_native_document,
    parse_native_document,
    search_pages,
    search_sections,
)
from financial_filing_data_foundation.sections import detect_sections


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _make_pdf(path: Path, *, blank_second: bool = False, rotated: bool = False) -> None:
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((72, 72), "1. Overview", fontsize=18)
    page.insert_text((72, 110), "Revenue increased in 2024.", fontsize=10)
    page.insert_text((72, 150), "1.1 Details", fontsize=14)
    page.insert_text((72, 185), "Detailed operating information.", fontsize=10)
    if rotated:
        page.set_rotation(90)
    page2 = doc.new_page(width=595, height=842)
    if not blank_second:
        page2.insert_text((72, 72), "2. Results", fontsize=18)
        page2.insert_text((72, 110), "Net profit improved.", fontsize=10)
    doc.save(path)
    doc.close()


def _synthetic_line(text: str, y: float, size: float = 12.0, bold: bool = False):
    return {
        "bbox": [50.0, y, 500.0, y + 20.0],
        "text": text,
        "spans": [
            {
                "text": text,
                "bbox": [50.0, y, 500.0, y + 20.0],
                "font": "Arial-Bold" if bold else "Arial",
                "size": size,
                "flags": 16 if bold else 0,
            }
        ],
        "repeated_header_footer": False,
    }


def _synthetic_pages():
    pages = []
    for page_no in range(1, 5):
        lines = [
            _synthetic_line("ACME ANNUAL REPORT 2024", 10, 9),
            _synthetic_line("body text " * 10, 200, 10),
        ]
        if page_no == 1:
            lines.insert(1, _synthetic_line("一、公司概况", 80, 16, True))
        if page_no == 2:
            lines.insert(1, _synthetic_line("（一）主营业务", 80, 14, True))
        if page_no == 3:
            lines.insert(1, _synthetic_line("2. Results", 80, 16, True))
        pages.append(
            {
                "page_no": page_no,
                "width": 595.0,
                "height": 842.0,
                "blocks": [
                    {
                        "block_no": 0,
                        "bbox": [50.0, 10.0, 500.0, 760.0],
                        "lines": lines,
                    }
                ],
            }
        )
    return pages


def test_parse_native_document_writes_complete_artifact(tmp_path: Path) -> None:
    source = tmp_path / "sample.pdf"
    _make_pdf(source)
    before = (source.read_bytes(), source.stat().st_mtime_ns)

    artifact = parse_native_document(source, tmp_path / "artifacts")

    assert artifact.parser_version == P3_PARSER_VERSION
    assert artifact.page_count == 2
    assert artifact.document_sha256 == _sha(source)
    assert artifact.pages_path.exists()
    assert artifact.sections_path.exists()
    assert artifact.search_db_path.exists()
    assert artifact.document_path.exists()
    assert source.read_bytes() == before[0]
    assert source.stat().st_mtime_ns == before[1]


def test_pages_have_words_blocks_spans_and_reading_order(tmp_path: Path) -> None:
    source = tmp_path / "sample.pdf"
    _make_pdf(source)
    artifact = parse_native_document(source, tmp_path / "artifacts")
    rows = [
        json.loads(line)
        for line in artifact.pages_path.read_text(encoding="utf-8").splitlines()
    ]

    first = rows[0]
    assert first["page_no"] == 1
    assert first["native_text_available"] is True
    assert first["word_count"] > 0
    assert first["block_count"] > 0
    assert first["span_count"] > 0
    assert all(word["bbox"][2] >= word["bbox"][0] for word in first["words"])
    order = [block["reading_order_index"] for block in first["blocks"]]
    assert order == list(range(len(order)))


def test_blank_page_is_explicit_warning(tmp_path: Path) -> None:
    source = tmp_path / "blank.pdf"
    _make_pdf(source, blank_second=True)
    artifact = parse_native_document(source, tmp_path / "artifacts")
    rows = [
        json.loads(line)
        for line in artifact.pages_path.read_text(encoding="utf-8").splitlines()
    ]
    assert rows[1]["native_text_available"] is False
    assert "PAGE_TEXT_EMPTY" in rows[1]["warnings"]


def test_image_only_page_is_not_misclassified_as_native_text(
    tmp_path: Path,
) -> None:
    source = tmp_path / "image-only.pdf"
    pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 20, 20), False)
    pix.clear_with(255)
    image = pix.tobytes("png")
    doc = pymupdf.open()
    page = doc.new_page(width=300, height=200)
    page.insert_image(pymupdf.Rect(20, 20, 120, 120), stream=image)
    doc.save(source)
    doc.close()

    artifact = parse_native_document(source, tmp_path / "artifacts")
    first = json.loads(
        artifact.pages_path.read_text(encoding="utf-8").splitlines()[0]
    )

    assert first["image_count"] >= 1
    assert first["native_text_available"] is False
    assert first["block_count"] == 0
    assert "PAGE_TEXT_EMPTY" in first["warnings"]


def test_rotated_page_reports_rotation(tmp_path: Path) -> None:
    source = tmp_path / "rotated.pdf"
    _make_pdf(source, rotated=True)
    artifact = parse_native_document(source, tmp_path / "artifacts")
    first = json.loads(
        artifact.pages_path.read_text(encoding="utf-8").splitlines()[0]
    )
    assert first["rotation"] == 90


def test_section_engine_recognizes_hierarchy_and_suppresses_repeated_header() -> None:
    pages = _synthetic_pages()
    sections, repeated = detect_sections("a" * 64, pages)

    titles = [section["raw_title"] for section in sections]
    assert "ACME ANNUAL REPORT 2024" not in titles
    assert "一、公司概况" in titles
    assert "（一）主营业务" in titles
    assert "2. Results" in titles
    assert repeated

    by_title = {section["raw_title"]: section for section in sections}
    assert by_title["一、公司概况"]["level"] == 1
    assert by_title["（一）主营业务"]["level"] == 2
    assert (
        by_title["（一）主营业务"]["parent_section_id"]
        == by_title["一、公司概况"]["section_id"]
    )
    assert by_title["2. Results"]["level"] == 1


def test_section_ids_and_ranges_are_deterministic() -> None:
    pages = _synthetic_pages()
    first, _ = detect_sections("b" * 64, pages)
    second, _ = detect_sections("b" * 64, pages)

    assert first == second
    assert all(s["page_end"] >= s["page_start"] for s in first)


def test_fts_page_and_section_search(tmp_path: Path) -> None:
    source = tmp_path / "search.pdf"
    _make_pdf(source)
    artifact = parse_native_document(source, tmp_path / "artifacts")

    page_hits = search_pages(artifact.search_db_path, "Revenue", 5)
    section_hits = search_sections(artifact.search_db_path, "Overview", 5)

    assert page_hits
    assert page_hits[0]["page_no"] == 1
    assert section_hits
    assert section_hits[0]["page_start"] == 1


def test_page_fts_uses_external_page_content_and_survives_reopen(
    tmp_path: Path,
) -> None:
    import sqlite3

    source = tmp_path / "fts-schema.pdf"
    _make_pdf(source)
    artifact = parse_native_document(source, tmp_path / "artifacts")

    conn = sqlite3.connect(artifact.search_db_path)
    sql = conn.execute(
        "SELECT sql FROM sqlite_master WHERE name='page_fts'"
    ).fetchone()[0]
    page_rows = conn.execute("SELECT COUNT(*) FROM page_content").fetchone()[0]
    fts_rows = conn.execute("SELECT COUNT(*) FROM page_fts").fetchone()[0]
    conn.close()

    normalized = " ".join(sql.lower().split())
    assert "content='page_content'" in normalized
    assert "content_rowid='page_no'" in normalized
    assert page_rows == 2
    assert fts_rows == 2

    reopened_hits = search_pages(artifact.search_db_path, "Revenue", 5)
    assert reopened_hits
    assert reopened_hits[0]["page_no"] == 1


def test_artifact_json_has_no_bom(tmp_path: Path) -> None:
    source = tmp_path / "encoding.pdf"
    _make_pdf(source)
    artifact = parse_native_document(source, tmp_path / "artifacts")

    for path in (artifact.document_path, artifact.pages_path, artifact.sections_path):
        assert not path.read_bytes().startswith(b"\xef\xbb\xbf")


def test_same_root_reuses_complete_artifact_without_touching_source(
    tmp_path: Path,
) -> None:
    source = tmp_path / "reuse.pdf"
    _make_pdf(source)
    root = tmp_path / "artifacts"
    first = parse_native_document(source, root)
    before = first.document_path.stat().st_mtime_ns
    second = parse_native_document(source, root)

    assert first.document_sha256 == second.document_sha256
    assert second.document_path.stat().st_mtime_ns == before


def test_fresh_artifact_roots_have_same_pages_and_sections(tmp_path: Path) -> None:
    source = tmp_path / "deterministic.pdf"
    _make_pdf(source)
    a = parse_native_document(source, tmp_path / "a")
    b = parse_native_document(source, tmp_path / "b")

    assert a.pages_path.read_bytes() == b.pages_path.read_bytes()
    assert a.sections_path.read_bytes() == b.sections_path.read_bytes()


def test_load_native_document_roundtrip(tmp_path: Path) -> None:
    source = tmp_path / "load.pdf"
    _make_pdf(source)
    artifact = parse_native_document(source, tmp_path / "artifacts")
    loaded = load_native_document(artifact.artifact_dir)

    assert loaded.document_sha256 == artifact.document_sha256
    assert loaded.page_count == artifact.page_count


def test_jsonl_record_escapes_unicode_line_separators(tmp_path: Path) -> None:
    from financial_filing_data_foundation.native.parser import _write_jsonl

    path = tmp_path / "rows.jsonl"
    rows = [
        {"text": "alpha\u0085beta\u2028gamma\u2029delta"},
        {"text": "second"},
    ]
    _write_jsonl(path, rows)

    raw = path.read_bytes()
    assert b"\xc2\x85" not in raw
    assert b"\xe2\x80\xa8" not in raw
    assert b"\xe2\x80\xa9" not in raw
    physical_lines = raw.split(b"\n")
    assert len([line for line in physical_lines if line]) == 2
    decoded = [
        json.loads(line.decode("utf-8"))
        for line in physical_lines
        if line
    ]
    assert decoded == rows


def test_existing_artifact_missing_core_file_is_rejected(
    tmp_path: Path,
) -> None:
    source = tmp_path / "missing-core.pdf"
    _make_pdf(source)
    root = tmp_path / "artifacts"
    artifact = parse_native_document(source, root)
    artifact.pages_path.unlink()

    with pytest.raises(NativeParseError) as exc_info:
        parse_native_document(source, root)

    assert exc_info.value.reason_code == "ARTIFACT_INCOMPLETE_OR_CORRUPT"


def test_existing_artifact_search_metadata_mismatch_is_rejected(
    tmp_path: Path,
) -> None:
    import sqlite3

    source = tmp_path / "bad-search-metadata.pdf"
    _make_pdf(source)
    root = tmp_path / "artifacts"
    artifact = parse_native_document(source, root)

    conn = sqlite3.connect(artifact.search_db_path)
    conn.execute(
        "UPDATE metadata SET value=? WHERE key='document_sha256'",
        ("0" * 64,),
    )
    conn.commit()
    conn.close()

    with pytest.raises(NativeParseError) as exc_info:
        load_native_document(artifact.artifact_dir)

    assert exc_info.value.reason_code == "ARTIFACT_INCOMPLETE_OR_CORRUPT"


def test_p3_source_has_no_heavy_path_imports() -> None:
    import financial_filing_data_foundation.native.parser as parser_module
    import financial_filing_data_foundation.sections.engine as section_module

    source = (inspect.getsource(parser_module) + inspect.getsource(section_module)).lower()
    for forbidden in (
        "import dayu",
        "from dayu",
        "import docling",
        "from docling",
        "import torch",
        "from torch",
        "ocr",
    ):
        assert forbidden not in source
