from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pymupdf

from financial_filing_data_foundation.identity import FilingIdentity, FilingSlotKey
from financial_filing_data_foundation.mcp.catalog import McpCatalog
from financial_filing_data_foundation.mcp.visual_renderer import (
    PdfVisualRenderer,
    RenderDetail,
    TableRenderMode,
)
from financial_filing_data_foundation.registry import SQLiteRegistry


class FakeP8:
    def __init__(self, table):
        self.table = table

    def get_table(self, sha, table_id, max_rows):
        return {"data": dict(self.table)}

    def get_table_group_internal(self, sha, group_id):
        return {
            "group_id": group_id,
            "member_table_ids": [self.table["table_id"]],
        }


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fixture(tmp_path: Path):
    root = tmp_path / "project"
    raw_root = root / "workspace" / "ingest" / "raw-store"
    raw_root.mkdir(parents=True)
    tmp_pdf = raw_root / "temp.pdf"
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((80, 80), "Revenue table header")
    page.draw_rect(pymupdf.Rect(80, 120, 500, 300))
    page.insert_text((100, 160), "Revenue 100")
    doc.save(tmp_pdf)
    doc.close()
    sha = _sha(tmp_pdf)
    final = raw_root / "sha256" / sha[:2] / f"{sha}.pdf"
    final.parent.mkdir(parents=True)
    tmp_pdf.replace(final)

    registry_path = root / "workspace" / "ingest" / "registry.sqlite"
    slot = FilingSlotKey(
        market="CN",
        company_id="605117",
        filing_type="ANNUAL",
        fiscal_year=2025,
        raw_fiscal_period="FY",
    )
    SQLiteRegistry(registry_path).register_document(
        final,
        expected_identity=FilingIdentity(slot=slot, amended=False),
    )

    dirs = {}
    for name in ("p3", "p5", "p6", "p7"):
        dirs[name] = root / name / sha
        dirs[name].mkdir(parents=True)
    (dirs["p3"] / "document.json").write_text(
        json.dumps(
            {
                "document_sha256": sha,
                "file_size": final.stat().st_size,
                "page_count": 1,
                "source_path": str(final),
            }
        ),
        encoding="utf-8",
    )
    catalog_path = root / "catalog.json"
    catalog_path.write_text(
        json.dumps(
            {
                "schema_version": "p8-mcp-catalog-v1",
                "documents": [
                    {
                        "document_sha256": sha,
                        "market": "CN",
                        "ticker": "605117",
                        "fiscal_year": 2025,
                        "filing_type": "ANNUAL",
                        "p3_artifact_dir": dirs["p3"].relative_to(root).as_posix(),
                        "p5_artifact_dir": dirs["p5"].relative_to(root).as_posix(),
                        "p6_artifact_dir": dirs["p6"].relative_to(root).as_posix(),
                        "p7_artifact_dir": dirs["p7"].relative_to(root).as_posix(),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    catalog = McpCatalog.load(root, catalog_path)
    table = {
        "table_id": "table-1",
        "page_no": 1,
        "bbox": [80.0, 120.0, 500.0, 300.0],
    }
    renderer = PdfVisualRenderer(
        catalog=catalog,
        p8_service=FakeP8(table),
        registry_path=registry_path,
        trusted_raw_root=raw_root,
    )
    return renderer, sha


def test_page_render_is_png_and_deterministic(tmp_path: Path):
    renderer, sha = _fixture(tmp_path)
    first = renderer.render_page(sha, 1)[0]
    second = renderer.render_page(sha, 1)[0]

    assert first.mime_type == "image/png"
    assert first.png_bytes.startswith(b"\x89PNG")
    assert first.visual_ref_id == second.visual_ref_id
    assert first.render_sha256 == second.render_sha256
    assert renderer.repeated_visual_avoided_count == 1


def test_table_render_uses_deterministic_clip(tmp_path: Path):
    renderer, sha = _fixture(tmp_path)
    visual = renderer.render_table(
        sha,
        "table-1",
        mode=TableRenderMode.TABLE_WITH_HEADER,
    )[0]

    assert visual.metadata["target_kind"] == "TABLE"
    assert visual.metadata["target_id"] == "table-1"
    assert visual.metadata["clip"] == [68.0, 48.0, 512.0, 312.0]


def test_high_detail_has_distinct_visual_ref(tmp_path: Path):
    renderer, sha = _fixture(tmp_path)
    normal = renderer.render_page(sha, 1, detail=RenderDetail.NORMAL)[0]
    high = renderer.render_page(sha, 1, detail=RenderDetail.HIGH_DETAIL)[0]

    assert normal.visual_ref_id != high.visual_ref_id
    assert normal.metadata["dpi"] == 144
    assert high.metadata["dpi"] == 216


def test_group_render_uses_existing_group_members(tmp_path: Path):
    renderer, sha = _fixture(tmp_path)
    visuals = renderer.render_table_group(sha, "group-1")
    assert len(visuals) == 1
    assert visuals[0].metadata["target_id"] == "table-1"


def test_public_metadata_never_exposes_pdf_path(tmp_path: Path):
    renderer, sha = _fixture(tmp_path)
    metadata = renderer.render_page(sha, 1)[0].public_metadata()
    assert "path" not in metadata
    assert "source_path" not in metadata


def test_deterministic_tiling_when_pixel_budget_is_small(tmp_path: Path):
    renderer, sha = _fixture(tmp_path)
    renderer.max_pixel_area = 600_000

    first = renderer.render_page(sha, 1, detail=RenderDetail.NORMAL)
    second = renderer.render_page(sha, 1, detail=RenderDetail.NORMAL)

    assert len(first) > 1
    assert len(first) == len(second)
    assert [item.visual_ref_id for item in first] == [
        item.visual_ref_id for item in second
    ]
    assert [item.metadata["tile_index"] for item in first] == list(
        range(len(first))
    )
    assert all(
        item.metadata["tile_count"] == len(first) for item in first
    )
    assert renderer.repeated_visual_avoided_count == len(first)
    telemetry = renderer.telemetry()
    assert telemetry["visual_call_count"] == 2
    assert telemetry["rendered_unique_page_count"] == 1
    assert telemetry["rendered_unique_image_count"] == len(first)
