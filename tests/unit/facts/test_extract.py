from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from financial_filing_data_foundation.candidates import detect_table_candidates
from financial_filing_data_foundation.facts import (
    RawFactError,
    extract_raw_facts,
    load_raw_facts,
    parse_numeric_value,
)
from financial_filing_data_foundation.facts import extract
from financial_filing_data_foundation.native.models import (
    P3_PARSER_VERSION,
    SCHEMA_VERSION as P3_SCHEMA_VERSION,
)
from financial_filing_data_foundation.tables import reconstruct_tables


DOC_SHA = "c" * 64


def _word(
    text: str,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    line_no: int,
    word_no: int,
) -> dict:
    return {
        "text": text,
        "bbox": [x0, y0, x1, y1],
        "block_no": 0,
        "line_no": line_no,
        "word_no": word_no,
    }


def _source_ref(page_no: int, word: dict) -> dict:
    return {
        "page_no": page_no,
        "block_no": word["block_no"],
        "line_no": word["line_no"],
        "word_no": word["word_no"],
        "bbox": word["bbox"],
    }


def _synthetic_records() -> tuple[list[dict], list[dict], list[dict]]:
    page_no = 1
    words = []
    rows = []

    raw_rows = [
        ("项目", "2024", "2023"),
        ("单位：人民币元", "", ""),
        ("营业收入", "1,234.00", "(900)"),
        ("员工人数", "2024", "2023"),
    ]
    for row_index, values in enumerate(raw_rows):
        y0 = 100 + row_index * 24
        row_words = []
        cells = []
        for column_index, (text, x0, x1) in enumerate(
            zip(values, (50.0, 300.0, 400.0), (180.0, 340.0, 440.0))
        ):
            if not text:
                continue
            word = _word(text, x0, y0, x1, y0 + 12, row_index, column_index)
            words.append(word)
            row_words.append(word)
            role = "LABEL" if column_index == 0 else "VALUE"
            numeric = column_index > 0
            cells.append(
                {
                    "cell_id": f"cell-{row_index}-{column_index}",
                    "column_index": column_index,
                    "role": role,
                    "text": text,
                    "bbox": word["bbox"],
                    "numeric": numeric,
                    "source_words": [_source_ref(page_no, word)],
                }
            )
        rows.append(
            {
                "row_id": f"row-{row_index}",
                "row_index": row_index,
                "bbox": [50, y0, 440, y0 + 12],
                "cells": cells,
                "structural_signals": [],
            }
        )

    pages = [
        {
            "page_no": page_no,
            "width": 595.0,
            "height": 842.0,
            "words": words,
        }
    ]
    tables = [
        {
            "table_id": "table-1",
            "document_sha256": DOC_SHA,
            "page_no": page_no,
            "page_width": 595.0,
            "page_height": 842.0,
            "bbox": [50, 100, 440, 184],
            "value_column_count": 2,
            "value_column_anchors": [340.0, 440.0],
            "row_count": len(rows),
            "rows": rows,
            "candidate_keywords": ["合并"],
        }
    ]
    return pages, tables, []


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("123", "123"),
        ("1,234", "1234"),
        ("1，234.50", "1234.50"),
        ("-123.45", "-123.45"),
        ("−123", "-123"),
        ("(1,234)", "-1234"),
        ("12.5%", "12.5"),
        ("￥1,234.00", "1234.00"),
        ("—", None),
        ("-", None),
        ("1 234", None),
        ("abc", None),
    ],
)
def test_parse_numeric_value(raw: str, expected: str | None) -> None:
    assert parse_numeric_value(raw) == expected


def test_period_header_is_suppressed_and_maps_periods() -> None:
    pages, tables, groups = _synthetic_records()
    facts, evidence, warnings = extract._extract_records(
        DOC_SHA, pages, tables, groups
    )

    assert len(facts) == 4
    assert not any(
        fact["raw_metric_name"] == "项目"
        for fact in facts
    )
    revenue = [
        fact for fact in facts if fact["raw_metric_name"] == "营业收入"
    ]
    assert [fact["raw_period_label"] for fact in revenue] == ["2024", "2023"]
    assert [fact["parsed_numeric_value"] for fact in revenue] == [
        "1234.00",
        "-900",
    ]
    assert all(fact["raw_unit"] == "人民币元" for fact in facts)
    assert all(fact["raw_scope"] == "合并" for fact in facts)
    assert len(evidence) == len(facts)
    assert warnings == []


def test_normal_metric_values_2024_and_2023_are_not_suppressed() -> None:
    pages, tables, groups = _synthetic_records()
    facts, _, _ = extract._extract_records(DOC_SHA, pages, tables, groups)
    employees = [
        fact for fact in facts if fact["raw_metric_name"] == "员工人数"
    ]
    assert [fact["raw_value"] for fact in employees] == ["2024", "2023"]


def test_evidence_ids_and_source_refs_are_deterministic() -> None:
    pages, tables, groups = _synthetic_records()
    first = extract._extract_records(DOC_SHA, pages, tables, groups)
    second = extract._extract_records(DOC_SHA, pages, tables, groups)
    assert first == second
    facts, evidence, _ = first
    assert len({fact["raw_fact_id"] for fact in facts}) == len(facts)
    assert len({row["evidence_id"] for row in evidence}) == len(evidence)
    assert [fact["evidence_id"] for fact in facts] == [
        row["evidence_id"] for row in evidence
    ]


def test_invalid_source_ref_is_blocked() -> None:
    pages, tables, groups = _synthetic_records()
    tables[0]["rows"][2]["cells"][0]["source_words"][0]["word_no"] = 999
    with pytest.raises(RawFactError) as exc_info:
        extract._extract_records(DOC_SHA, pages, tables, groups)
    assert exc_info.value.reason_code == "P6_INPUT_EVIDENCE_INVALID"


def test_conflicting_units_become_null_warning() -> None:
    pages, tables, groups = _synthetic_records()
    extra = tables[0]["rows"][1]["cells"][0]
    extra["text"] = "单位：人民币元 / 万元"
    facts, _, warnings = extract._extract_records(
        DOC_SHA, pages, tables, groups
    )
    assert all(fact["raw_unit"] is None for fact in facts)
    assert {
        row["reason_code"]: row["count"]
        for row in warnings
    }["AMBIGUOUS_RAW_UNIT"] == 1


def test_missing_label_numeric_row_is_skipped_with_warning() -> None:
    pages, tables, groups = _synthetic_records()
    row = tables[0]["rows"][2]
    row["cells"] = [
        cell for cell in row["cells"] if cell["role"] != "LABEL"
    ]
    facts, _, warnings = extract._extract_records(
        DOC_SHA, pages, tables, groups
    )
    assert not any(fact["row_index"] == 2 for fact in facts)
    assert {
        row["reason_code"]: row["count"]
        for row in warnings
    }["ROW_WITHOUT_LABEL"] == 1


def _page(page_no: int = 1) -> dict:
    raw_rows = [
        ("项目", "2024", "2023"),
        ("营业收入", "1000", "900"),
        ("利润", "200", "150"),
        ("资产", "5000", "4500"),
        ("负债", "2000", "1800"),
        ("现金流", "300", "250"),
    ]
    words = []
    lines = []
    for row_no, values in enumerate(raw_rows):
        y0 = 100 + row_no * 24
        row_words = []
        for word_no, (text, x0, x1) in enumerate(
            zip(values, (50.0, 300.0, 400.0), (150.0, 340.0, 440.0))
        ):
            word = _word(text, x0, y0, x1, y0 + 12, row_no, word_no)
            words.append(word)
            row_words.append(word)
        lines.append(
            {
                "line_no": row_no,
                "bbox": [50, y0, 440, y0 + 12],
                "text": " ".join(word["text"] for word in row_words),
                "spans": [],
                "repeated_header_footer": False,
            }
        )
    text = "\n".join(line["text"] for line in lines)
    return {
        "page_no": page_no,
        "width": 595.0,
        "height": 842.0,
        "rotation": 0,
        "native_text_available": True,
        "native_char_count": len(text),
        "word_count": len(words),
        "block_count": 1,
        "line_count": len(lines),
        "span_count": 0,
        "image_count": 0,
        "drawing_count": 30,
        "text": text,
        "words": words,
        "blocks": [
            {
                "block_no": 0,
                "bbox": [50, 100, 440, 232],
                "type": "text",
                "text": text,
                "lines": lines,
                "reading_order_index": 0,
            }
        ],
        "warnings": [],
    }


def _write_p3(root: Path, pages: list[dict]) -> Path:
    artifact = root / DOC_SHA
    artifact.mkdir(parents=True)
    (artifact / "pages.jsonl").write_text(
        "".join(
            json.dumps(page, ensure_ascii=False) + "\n"
            for page in pages
        ),
        encoding="utf-8",
    )
    (artifact / "sections.jsonl").write_text("", encoding="utf-8")
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
    conn.execute(
        "CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL)"
    )
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


def _build_p3_p5(tmp_path: Path) -> tuple[Path, Path]:
    p3 = _write_p3(tmp_path / "p3", [_page()])
    p4 = detect_table_candidates(p3, tmp_path / "p4").artifact_dir
    p5 = reconstruct_tables(p3, p4, tmp_path / "p5").artifact_dir
    return p3, p5


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_full_artifact_extract_reuse_and_dual_root(tmp_path: Path) -> None:
    p3, p5 = _build_p3_p5(tmp_path)
    first = extract_raw_facts(p3, p5, tmp_path / "p6-a")
    second = extract_raw_facts(p3, p5, tmp_path / "p6-b")

    assert first.fact_count > 0
    assert first.fact_count == first.evidence_count
    assert first.facts_path.read_bytes() == second.facts_path.read_bytes()
    assert first.evidence_path.read_bytes() == second.evidence_path.read_bytes()

    before = first.facts_path.stat().st_mtime_ns
    reused = extract_raw_facts(p3, p5, tmp_path / "p6-a")
    assert reused.facts_path.stat().st_mtime_ns == before

    facts = _read_jsonl(first.facts_path)
    assert not any(fact["raw_metric_name"] == "项目" for fact in facts)
    assert {
        fact["raw_period_label"]
        for fact in facts
    } == {"2024", "2023"}


def test_fact_tamper_is_blocked(tmp_path: Path) -> None:
    p3, p5 = _build_p3_p5(tmp_path)
    artifact = extract_raw_facts(p3, p5, tmp_path / "p6")
    facts = _read_jsonl(artifact.facts_path)
    facts[0]["raw_metric_name"] = "tampered"
    artifact.facts_path.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            + "\n"
            for row in facts
        ),
        encoding="utf-8",
    )

    with pytest.raises(RawFactError) as exc_info:
        load_raw_facts(artifact.artifact_dir, p3, p5)
    assert exc_info.value.reason_code == "P6_ARTIFACT_INCOMPLETE_OR_CORRUPT"


def test_evidence_tamper_is_blocked(tmp_path: Path) -> None:
    p3, p5 = _build_p3_p5(tmp_path)
    artifact = extract_raw_facts(p3, p5, tmp_path / "p6")
    evidence = _read_jsonl(artifact.evidence_path)
    evidence[0]["raw_text"] = "tampered"
    artifact.evidence_path.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            + "\n"
            for row in evidence
        ),
        encoding="utf-8",
    )

    with pytest.raises(RawFactError):
        load_raw_facts(artifact.artifact_dir, p3, p5)


def test_input_fingerprint_change_is_blocked(tmp_path: Path) -> None:
    p3, p5 = _build_p3_p5(tmp_path)
    artifact = extract_raw_facts(p3, p5, tmp_path / "p6")
    tables_path = p5 / "tables.jsonl"
    tables_path.write_bytes(tables_path.read_bytes() + b"\n")

    with pytest.raises(Exception):
        load_raw_facts(artifact.artifact_dir, p3, p5)


def test_extraction_does_not_open_pdf(monkeypatch, tmp_path: Path) -> None:
    p3, p5 = _build_p3_p5(tmp_path)

    import financial_filing_data_foundation.native.parser as native_parser

    monkeypatch.setattr(
        native_parser.pymupdf,
        "open",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("P6 must not open PDF")
        ),
    )

    artifact = extract_raw_facts(p3, p5, tmp_path / "p6")
    assert artifact.fact_count > 0


def test_p3_p5_inputs_unchanged(tmp_path: Path) -> None:
    p3, p5 = _build_p3_p5(tmp_path)
    paths = [
        p3 / "document.json",
        p3 / "pages.jsonl",
        p3 / "sections.jsonl",
        p3 / "search.sqlite",
        p5 / "table_manifest.json",
        p5 / "tables.jsonl",
        p5 / "table_groups.jsonl",
    ]
    before = {
        path: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in paths
    }

    extract_raw_facts(p3, p5, tmp_path / "p6")

    after = {
        path: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in paths
    }
    assert before == after
