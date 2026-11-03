from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from financial_filing_data_foundation.candidates import detect_table_candidates
from financial_filing_data_foundation.native.models import (
    P3_PARSER_VERSION,
    SCHEMA_VERSION as P3_SCHEMA_VERSION,
)
from financial_filing_data_foundation.tables import (
    TableReconstructionError,
    load_reconstructed_tables,
    reconstruct_tables,
)
from financial_filing_data_foundation.tables import reconstruct


DOC_SHA = "b" * 64


def _word(
    text: str,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    block_no: int,
    line_no: int,
    word_no: int,
) -> dict:
    return {
        "text": text,
        "bbox": [x0, y0, x1, y1],
        "block_no": block_no,
        "line_no": line_no,
        "word_no": word_no,
    }


def _page(
    page_no: int,
    *,
    y_start: float = 100.0,
    rows: int = 5,
    drawing_count: int = 30,
) -> dict:
    words = []
    lines = []
    labels = ["项目", "营业收入", "利润", "资产", "负债", "现金流"]
    for row_no in range(rows):
        y0 = y_start + row_no * 24
        row_words = [
            _word(
                labels[row_no % len(labels)],
                50,
                y0,
                150,
                y0 + 12,
                0,
                row_no,
                0,
            ),
            _word(
                str(1000 + row_no * 10),
                300,
                y0,
                340,
                y0 + 12,
                0,
                row_no,
                1,
            ),
            _word(
                str(900 + row_no * 10),
                400,
                y0,
                440,
                y0 + 12,
                0,
                row_no,
                2,
            ),
        ]
        words.extend(row_words)
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
        "drawing_count": drawing_count,
        "text": text,
        "words": words,
        "blocks": [
            {
                "block_no": 0,
                "bbox": [
                    50,
                    y_start,
                    440,
                    y_start + (rows - 1) * 24 + 12,
                ],
                "type": "text",
                "text": text,
                "lines": lines,
                "reading_order_index": 0,
            }
        ],
        "warnings": [],
    }


def _distributed_page(page_no: int = 1) -> dict:
    words = []
    blocks = []
    labels = ["收入", "利润", "资产", "负债", "现金流", "合计"]
    block_no = 0
    for row_no in range(6):
        y0 = 100 + row_no * 24
        # Label is intentionally outside P4 distributed numeric block_nos.
        label = {
            "block_no": block_no,
            "bbox": [50, y0, 140, y0 + 12],
            "type": "text",
            "text": labels[row_no],
            "lines": [
                {
                    "line_no": 0,
                    "bbox": [50, y0, 140, y0 + 12],
                    "text": labels[row_no],
                    "spans": [],
                    "repeated_header_footer": False,
                }
            ],
            "reading_order_index": block_no,
        }
        blocks.append(label)
        block_no += 1
        for col_no, x0 in enumerate((300.0, 400.0)):
            text = str(1000 + row_no * 10 + col_no)
            blocks.append(
                {
                    "block_no": block_no,
                    "bbox": [x0, y0, x0 + 40, y0 + 12],
                    "type": "text",
                    "text": text,
                    "lines": [
                        {
                            "line_no": 0,
                            "bbox": [x0, y0, x0 + 40, y0 + 12],
                            "text": text,
                            "spans": [],
                            "repeated_header_footer": False,
                        }
                    ],
                    "reading_order_index": block_no,
                }
            )
            words.append(
                _word(
                    text,
                    x0,
                    y0,
                    x0 + 40,
                    y0 + 12,
                    block_no,
                    0,
                    0,
                )
            )
            block_no += 1
    return {
        "page_no": page_no,
        "width": 595.0,
        "height": 842.0,
        "rotation": 0,
        "native_text_available": True,
        "native_char_count": 200,
        "word_count": len(words),
        "block_count": len(blocks),
        "line_count": len(blocks),
        "span_count": 0,
        "image_count": 0,
        "drawing_count": 0,
        "text": "綜合財務報表 收入 利润 资产 负债 现金流",
        "words": words,
        "blocks": blocks,
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


def _build_inputs(
    tmp_path: Path,
    pages: list[dict],
) -> tuple[Path, Path]:
    p3 = _write_p3(tmp_path / "p3", pages)
    p4 = detect_table_candidates(p3, tmp_path / "p4").artifact_dir
    return p3, p4


def _read_rows(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_visual_row_clustering_uses_y_centers() -> None:
    words = [
        {
            **_word("A", 10, 10, 20, 20, 0, 0, 0),
            "page_no": 1,
        },
        {
            **_word("1", 100, 11, 120, 21, 0, 0, 1),
            "page_no": 1,
        },
        {
            **_word("B", 10, 40, 20, 50, 0, 1, 0),
            "page_no": 1,
        },
    ]
    rows = reconstruct._cluster_visual_rows(words)
    assert len(rows) == 2
    assert [word["text"] for word in rows[0]] == ["A", "1"]
    assert [word["text"] for word in rows[1]] == ["B"]


def test_value_anchor_clustering_uses_numeric_right_edges() -> None:
    rows = [
        [
            {**_word("100", 300, 10, 340, 20, 0, 0, 0), "page_no": 1},
            {**_word("90", 400, 10, 440, 20, 0, 0, 1), "page_no": 1},
        ],
        [
            {**_word("110", 300, 30, 340, 40, 0, 1, 0), "page_no": 1},
            {**_word("95", 400, 30, 440, 40, 0, 1, 1), "page_no": 1},
        ],
    ]
    anchors = reconstruct._value_anchor_clusters(rows, 595.0, 4)
    assert anchors == [340.0, 440.0]


def test_reconstructs_label_and_value_cells_with_source_refs(
    tmp_path: Path,
) -> None:
    p3, p4 = _build_inputs(tmp_path, [_page(1)])
    artifact = reconstruct_tables(p3, p4, tmp_path / "p5")
    tables = _read_rows(artifact.tables_path)

    assert artifact.table_count == 1
    table = tables[0]
    assert table["value_column_count"] == 2
    assert table["value_column_anchors"] == [340.0, 440.0]
    assert table["row_count"] == 5
    first = table["rows"][0]
    roles = [cell["role"] for cell in first["cells"]]
    assert roles == ["LABEL", "VALUE", "VALUE"]
    assert first["cells"][0]["text"] == "项目"
    assert first["cells"][1]["numeric"] is True
    assert first["cells"][0]["source_words"][0]["page_no"] == 1


def test_ids_are_stable_across_dual_roots(tmp_path: Path) -> None:
    p3, p4 = _build_inputs(tmp_path, [_page(1)])
    first = reconstruct_tables(p3, p4, tmp_path / "a")
    second = reconstruct_tables(p3, p4, tmp_path / "b")

    assert first.tables_path.read_bytes() == second.tables_path.read_bytes()
    assert first.groups_path.read_bytes() == second.groups_path.read_bytes()


def test_distributed_candidate_reconstructs_value_columns(
    tmp_path: Path,
) -> None:
    p3, p4 = _build_inputs(tmp_path, [_distributed_page()])
    artifact = reconstruct_tables(p3, p4, tmp_path / "p5")
    tables = _read_rows(artifact.tables_path)

    assert tables
    table = tables[0]
    assert table["value_column_count"] == 2
    assert table["row_count"] >= 5
    assert "DISTRIBUTED_BLOCK_SOURCE" in table["quality_signals"]
    assert all(
        cell["role"] in {"VALUE", "UNASSIGNED", "LABEL"}
        for row in table["rows"]
        for cell in row["cells"]
    )


def test_adjacent_bottom_top_tables_form_group(tmp_path: Path) -> None:
    pages = [
        _page(1, y_start=600, rows=5),
        _page(2, y_start=100, rows=5),
    ]
    p3, p4 = _build_inputs(tmp_path, pages)
    artifact = reconstruct_tables(p3, p4, tmp_path / "p5")
    groups = _read_rows(artifact.groups_path)

    assert artifact.group_count == 1
    assert groups[0]["page_start"] == 1
    assert groups[0]["page_end"] == 2
    assert "ADJACENT_PAGES" in groups[0]["continuation_signals"]


def test_non_adjacent_tables_do_not_group(tmp_path: Path) -> None:
    pages = [
        _page(1, y_start=600, rows=5),
        _page(2, y_start=100, rows=1, drawing_count=0),
        _page(3, y_start=100, rows=5),
    ]
    # Page 2 will not generate a candidate.
    pages[1]["words"] = []
    pages[1]["blocks"] = []
    pages[1]["text"] = ""
    pages[1]["word_count"] = 0
    pages[1]["block_count"] = 0
    pages[1]["line_count"] = 0
    p3, p4 = _build_inputs(tmp_path, pages)
    artifact = reconstruct_tables(p3, p4, tmp_path / "p5")

    assert artifact.group_count == 0


def test_incompatible_value_columns_do_not_group(tmp_path: Path) -> None:
    first = _page(1, y_start=600, rows=5)
    second = _page(2, y_start=100, rows=5)
    # Move second numeric columns to incompatible normalized positions.
    for word in second["words"]:
        if word["word_no"] == 1:
            word["bbox"][0] = 180
            word["bbox"][2] = 220
        elif word["word_no"] == 2:
            word["bbox"][0] = 250
            word["bbox"][2] = 290
    for line in second["blocks"][0]["lines"]:
        line["bbox"] = [50, line["bbox"][1], 290, line["bbox"][3]]
    second["blocks"][0]["bbox"][2] = 290

    p3, p4 = _build_inputs(tmp_path, [first, second])
    artifact = reconstruct_tables(p3, p4, tmp_path / "p5")
    assert artifact.group_count == 0


def test_valid_artifact_is_reused(tmp_path: Path) -> None:
    p3, p4 = _build_inputs(tmp_path, [_page(1)])
    first = reconstruct_tables(p3, p4, tmp_path / "p5")
    before = first.tables_path.stat().st_mtime_ns
    second = reconstruct_tables(p3, p4, tmp_path / "p5")

    assert second.tables_path.stat().st_mtime_ns == before


def test_p4_fingerprint_change_is_blocked(tmp_path: Path) -> None:
    p3, p4 = _build_inputs(tmp_path, [_page(1)])
    artifact = reconstruct_tables(p3, p4, tmp_path / "p5")

    rows = _read_rows(p4 / "candidates.jsonl")
    rows[0]["score"] = float(rows[0]["score"]) + 0.001
    (p4 / "candidates.jsonl").write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )

    with pytest.raises(TableReconstructionError) as exc_info:
        load_reconstructed_tables(artifact.artifact_dir)

    assert exc_info.value.reason_code == "P5_INPUT_FINGERPRINT_MISMATCH"


@pytest.mark.parametrize("target", ["table_id", "row_id", "cell_id"])
def test_tampered_nested_identity_is_blocked(
    target: str,
    tmp_path: Path,
) -> None:
    p3, p4 = _build_inputs(tmp_path, [_page(1)])
    artifact = reconstruct_tables(p3, p4, tmp_path / "p5")
    tables = _read_rows(artifact.tables_path)

    if target == "table_id":
        tables[0]["table_id"] = "0" * 64
    elif target == "row_id":
        tables[0]["rows"][0]["row_id"] = "0" * 64
    else:
        tables[0]["rows"][0]["cells"][0]["cell_id"] = "0" * 64

    artifact.tables_path.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            for row in tables
        ),
        encoding="utf-8",
    )

    with pytest.raises(TableReconstructionError):
        load_reconstructed_tables(artifact.artifact_dir)


def test_tampered_group_member_is_blocked(tmp_path: Path) -> None:
    p3, p4 = _build_inputs(
        tmp_path,
        [_page(1, y_start=600), _page(2, y_start=100)],
    )
    artifact = reconstruct_tables(p3, p4, tmp_path / "p5")
    groups = _read_rows(artifact.groups_path)
    assert groups
    groups[0]["member_table_ids"][0] = "0" * 64
    artifact.groups_path.write_text(
        json.dumps(groups[0], ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(TableReconstructionError):
        load_reconstructed_tables(artifact.artifact_dir)


def test_detection_does_not_open_pdf(monkeypatch, tmp_path: Path) -> None:
    p3, p4 = _build_inputs(tmp_path, [_page(1)])
    import financial_filing_data_foundation.native.parser as native_parser

    monkeypatch.setattr(
        native_parser.pymupdf,
        "open",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("P5 must not open source PDF")
        ),
    )
    artifact = reconstruct_tables(p3, p4, tmp_path / "p5")
    assert artifact.table_count == 1


def test_input_artifacts_are_unchanged(tmp_path: Path) -> None:
    p3, p4 = _build_inputs(tmp_path, [_page(1)])
    paths = [
        p3 / "document.json",
        p3 / "pages.jsonl",
        p3 / "sections.jsonl",
        p3 / "search.sqlite",
        p4 / "candidate_manifest.json",
        p4 / "candidates.jsonl",
    ]
    before = {
        path: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in paths
    }

    reconstruct_tables(p3, p4, tmp_path / "p5")

    after = {
        path: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in paths
    }
    assert before == after
