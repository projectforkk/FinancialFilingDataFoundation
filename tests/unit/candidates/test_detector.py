from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from financial_filing_data_foundation.candidates import (
    TableCandidateError,
    detect_table_candidates,
    load_table_candidates,
)
from financial_filing_data_foundation.candidates import detector
from financial_filing_data_foundation.native.models import (
    P3_PARSER_VERSION,
    SCHEMA_VERSION as P3_SCHEMA_VERSION,
)


DOC_SHA = "a" * 64


def _word(text: str, x0: float, y0: float, x1: float, y1: float, line: int, word: int):
    return {
        "text": text,
        "bbox": [x0, y0, x1, y1],
        "block_no": 0,
        "line_no": line,
        "word_no": word,
    }


def _table_page(page_no: int = 1) -> dict:
    line_texts = [
        ("项目 2024 2023", [("项目", 40, 90), ("2024", 300, 340), ("2023", 400, 440)]),
        ("营业收入 100 90", [("营业收入", 40, 110), ("100", 300, 340), ("90", 400, 440)]),
        ("利润 20 15", [("利润", 40, 130), ("20", 300, 340), ("15", 400, 440)]),
        ("资产 500 450", [("资产", 40, 150), ("500", 300, 340), ("450", 400, 440)]),
    ]
    lines = []
    words = []
    for line_no, (text, tokens) in enumerate(line_texts):
        y0 = 80 + line_no * 20
        line_words = []
        for word_no, (token, x0, x1) in enumerate(tokens):
            word = _word(token, x0, y0, x1, y0 + 12, line_no, word_no)
            words.append(word)
            line_words.append(word)
        lines.append(
            {
                "line_no": line_no,
                "bbox": [40, y0, 440, y0 + 12],
                "text": text,
                "spans": [],
                "repeated_header_footer": False,
            }
        )
    return {
        "page_no": page_no,
        "width": 595.0,
        "height": 842.0,
        "rotation": 0,
        "native_text_available": True,
        "native_char_count": 60,
        "word_count": len(words),
        "block_count": 1,
        "line_count": len(lines),
        "span_count": 0,
        "image_count": 0,
        "drawing_count": 30,
        "text": "\n".join(line["text"] for line in lines),
        "words": words,
        "blocks": [
            {
                "block_no": 0,
                "bbox": [40, 80, 440, 152],
                "type": "text",
                "text": "\n".join(line["text"] for line in lines),
                "lines": lines,
                "reading_order_index": 0,
            }
        ],
        "warnings": [],
    }




def _distributed_table_page(page_no: int = 1) -> dict:
    blocks = []
    words = []
    texts = ["綜合收益表", "收入"]
    block_no = 0
    for row_no in range(6):
        y0 = 100 + row_no * 28
        for col_no, x0 in enumerate((300.0, 400.0)):
            text = str(1000 + row_no * 10 + col_no)
            block = {
                "block_no": block_no,
                "bbox": [x0, y0, x0 + 45, y0 + 12],
                "type": "text",
                "text": text,
                "lines": [
                    {
                        "line_no": 0,
                        "bbox": [x0, y0, x0 + 45, y0 + 12],
                        "text": text,
                        "spans": [],
                        "repeated_header_footer": False,
                    }
                ],
                "reading_order_index": block_no,
            }
            blocks.append(block)
            words.append(
                {
                    "text": text,
                    "bbox": [x0, y0, x0 + 45, y0 + 12],
                    "block_no": block_no,
                    "line_no": 0,
                    "word_no": 0,
                }
            )
            texts.append(text)
            block_no += 1

    label = {
        "block_no": block_no,
        "bbox": [40, 70, 220, 90],
        "type": "text",
        "text": "綜合收益表 收入",
        "lines": [
            {
                "line_no": 0,
                "bbox": [40, 70, 220, 90],
                "text": "綜合收益表 收入",
                "spans": [],
                "repeated_header_footer": False,
            }
        ],
        "reading_order_index": block_no,
    }
    blocks.append(label)

    return {
        "page_no": page_no,
        "width": 595.0,
        "height": 842.0,
        "rotation": 0,
        "native_text_available": True,
        "native_char_count": 100,
        "word_count": len(words) + 2,
        "block_count": len(blocks),
        "line_count": len(blocks),
        "span_count": 0,
        "image_count": 0,
        "drawing_count": 0,
        "text": "\n".join(texts),
        "words": words,
        "blocks": blocks,
        "warnings": [],
    }


def _plain_page(text: str, page_no: int = 1, drawing_count: int = 0) -> dict:
    return {
        "page_no": page_no,
        "width": 595.0,
        "height": 842.0,
        "rotation": 0,
        "native_text_available": bool(text),
        "native_char_count": len(text),
        "word_count": len(text.split()),
        "block_count": 1 if text else 0,
        "line_count": 1 if text else 0,
        "span_count": 0,
        "image_count": 0,
        "drawing_count": drawing_count,
        "text": text,
        "words": [],
        "blocks": (
            [
                {
                    "block_no": 0,
                    "bbox": [40, 80, 500, 100],
                    "type": "text",
                    "text": text,
                    "lines": [
                        {
                            "line_no": 0,
                            "bbox": [40, 80, 500, 100],
                            "text": text,
                            "spans": [],
                            "repeated_header_footer": False,
                        }
                    ],
                    "reading_order_index": 0,
                }
            ]
            if text
            else []
        ),
        "warnings": [],
    }


def _write_p3_artifact(
    root: Path,
    pages: list[dict],
    sections: list[dict] | None = None,
) -> Path:
    artifact = root / DOC_SHA
    artifact.mkdir(parents=True)
    (artifact / "pages.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in pages),
        encoding="utf-8",
    )
    (artifact / "sections.jsonl").write_text(
        "".join(
            json.dumps(row, ensure_ascii=False) + "\n"
            for row in (sections or [])
        ),
        encoding="utf-8",
    )
    (artifact / "document.json").write_text(
        json.dumps(
            {
                "schema_version": P3_SCHEMA_VERSION,
                "document_sha256": DOC_SHA,
                "file_size": 123,
                "page_count": len(pages),
                "parser_version": P3_PARSER_VERSION,
                "timings_ms": {},
                "warnings": [],
            }
        ),
        encoding="utf-8",
    )
    conn = sqlite3.connect(artifact / "search.sqlite")
    conn.execute("CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    conn.executemany(
        "INSERT INTO metadata(key,value) VALUES(?,?)",
        (
            ("document_sha256", DOC_SHA),
            ("schema_version", P3_SCHEMA_VERSION),
        ),
    )
    conn.commit()
    conn.close()
    return artifact


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("1", True),
        ("1,234", True),
        ("-123.45", True),
        ("−123", True),
        ("(1,234)", True),
        ("12.5%", True),
        ("￥1,234.00", True),
        ("—", False),
        ("-", False),
        ("2024年", False),
        ("abc", False),
    ],
)
def test_numeric_token_classifier(value: str, expected: bool) -> None:
    assert detector.is_numeric_token(value) is expected


def test_table_page_creates_deterministic_candidate(tmp_path: Path) -> None:
    p3 = _write_p3_artifact(tmp_path / "p3", [_table_page()])
    artifact = detect_table_candidates(p3, tmp_path / "p4")

    assert artifact.candidate_count == 1
    row = json.loads(artifact.candidates_path.read_text(encoding="utf-8").strip())
    assert row["candidate_class"] == "TABLE_LIKE"
    assert row["numeric_line_count"] >= 3
    assert "NUMERIC_DENSITY" in row["signals"]
    assert "FINANCIAL_KEYWORDS" in row["signals"]
    assert len(row["candidate_id"]) == 64



def test_distributed_blocks_create_page_fallback_candidate(tmp_path: Path) -> None:
    p3 = _write_p3_artifact(
        tmp_path / "p3",
        [_distributed_table_page()],
    )
    artifact = detect_table_candidates(p3, tmp_path / "p4")

    rows = [
        json.loads(line)
        for line in artifact.candidates_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert rows
    distributed = [
        row for row in rows if "DISTRIBUTED_NUMERIC_BLOCKS" in row["signals"]
    ]
    assert len(distributed) == 1
    row = distributed[0]
    assert row["numeric_token_count"] == 12
    assert row["column_anchor_count"] >= 2
    assert "DISTRIBUTED_BLOCK_LAYOUT" in row["quality_signals"]
    assert "cells" not in row
    assert "rows" not in row
    assert "columns" not in row


def test_keyword_only_does_not_trigger(tmp_path: Path) -> None:
    p3 = _write_p3_artifact(
        tmp_path / "p3",
        [_plain_page("资产 负债 权益 收入 利润")],
    )
    artifact = detect_table_candidates(p3, tmp_path / "p4")
    assert artifact.candidate_count == 0


def test_drawing_only_does_not_trigger(tmp_path: Path) -> None:
    p3 = _write_p3_artifact(
        tmp_path / "p3",
        [_plain_page("", drawing_count=500)],
    )
    artifact = detect_table_candidates(p3, tmp_path / "p4")
    assert artifact.candidate_count == 0


def test_single_year_toc_line_does_not_trigger(tmp_path: Path) -> None:
    p3 = _write_p3_artifact(
        tmp_path / "p3",
        [_plain_page("第一章 公司概况 ........ 2024")],
    )
    artifact = detect_table_candidates(p3, tmp_path / "p4")
    assert artifact.candidate_count == 0


def test_dual_root_candidates_are_byte_identical(tmp_path: Path) -> None:
    p3 = _write_p3_artifact(tmp_path / "p3", [_table_page()])
    first = detect_table_candidates(p3, tmp_path / "a")
    second = detect_table_candidates(p3, tmp_path / "b")

    assert first.candidates_path.read_bytes() == second.candidates_path.read_bytes()


def test_existing_valid_artifact_is_reused(tmp_path: Path) -> None:
    p3 = _write_p3_artifact(tmp_path / "p3", [_table_page()])
    first = detect_table_candidates(p3, tmp_path / "p4")
    before = first.candidates_path.stat().st_mtime_ns
    second = detect_table_candidates(p3, tmp_path / "p4")

    assert second.artifact_dir == first.artifact_dir
    assert second.candidates_path.stat().st_mtime_ns == before


def test_corrupt_manifest_is_rejected(tmp_path: Path) -> None:
    p3 = _write_p3_artifact(tmp_path / "p3", [_table_page()])
    artifact = detect_table_candidates(p3, tmp_path / "p4")
    payload = json.loads(artifact.manifest_path.read_text(encoding="utf-8"))
    payload["schema_version"] = "wrong"
    artifact.manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(TableCandidateError) as exc_info:
        load_table_candidates(artifact.artifact_dir)

    assert exc_info.value.reason_code == "P4_ARTIFACT_INCOMPLETE_OR_CORRUPT"


def test_corrupt_jsonl_is_rejected(tmp_path: Path) -> None:
    p3 = _write_p3_artifact(tmp_path / "p3", [_table_page()])
    artifact = detect_table_candidates(p3, tmp_path / "p4")
    artifact.candidates_path.write_text("{broken\n", encoding="utf-8")

    with pytest.raises(TableCandidateError):
        load_table_candidates(artifact.artifact_dir)


def test_candidate_count_mismatch_is_rejected(tmp_path: Path) -> None:
    p3 = _write_p3_artifact(tmp_path / "p3", [_table_page()])
    artifact = detect_table_candidates(p3, tmp_path / "p4")
    payload = json.loads(artifact.manifest_path.read_text(encoding="utf-8"))
    payload["candidate_count"] = 99
    artifact.manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(TableCandidateError):
        load_table_candidates(artifact.artifact_dir)



@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("page_no", 999),
        ("bbox", [41.0, 81.0, 441.0, 153.0]),
        ("bbox", [10.0, 10.0, 5.0, 20.0]),
        ("block_nos", [1, 0]),
        ("block_nos", []),
        ("candidate_id", "0" * 64),
    ],
)
def test_tampered_candidate_identity_fields_are_rejected(
    field: str,
    value,
    tmp_path: Path,
) -> None:
    p3 = _write_p3_artifact(tmp_path / "p3", [_table_page()])
    artifact = detect_table_candidates(p3, tmp_path / "p4")
    rows = [
        json.loads(line)
        for line in artifact.candidates_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(rows) == 1
    rows[0][field] = value
    artifact.candidates_path.write_text(
        json.dumps(rows[0], ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(TableCandidateError) as exc_info:
        load_table_candidates(artifact.artifact_dir)

    assert exc_info.value.reason_code == "P4_ARTIFACT_INCOMPLETE_OR_CORRUPT"


def test_detection_does_not_open_pdf(monkeypatch, tmp_path: Path) -> None:
    p3 = _write_p3_artifact(tmp_path / "p3", [_table_page()])

    import financial_filing_data_foundation.native.parser as native_parser

    monkeypatch.setattr(
        native_parser.pymupdf,
        "open",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("P4 must not open PDF")
        ),
    )

    artifact = detect_table_candidates(p3, tmp_path / "p4")
    assert artifact.candidate_count == 1


def test_p3_artifact_files_are_unchanged(tmp_path: Path) -> None:
    p3 = _write_p3_artifact(tmp_path / "p3", [_table_page()])
    paths = [
        p3 / "document.json",
        p3 / "pages.jsonl",
        p3 / "sections.jsonl",
        p3 / "search.sqlite",
    ]
    before = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in paths}

    detect_table_candidates(p3, tmp_path / "p4")

    after = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in paths}
    assert before == after
