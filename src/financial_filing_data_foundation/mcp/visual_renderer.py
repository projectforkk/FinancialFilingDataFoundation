from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Final

import pymupdf

from financial_filing_data_foundation.mcp.catalog import McpCatalog
from financial_filing_data_foundation.mcp.service import McpQueryService, McpServiceError
from financial_filing_data_foundation.mcp.trusted_source import (
    TrustedSourceError,
    resolve_trusted_pdf_source,
)


PDF_RENDERER_VERSION: Final = "ffdf-pdf-renderer-v1"
_NORMAL_DPI: Final = 144
_HIGH_DETAIL_DPI: Final = 216
_MAX_PNG_BYTES: Final = 10 * 1024 * 1024
_MAX_PIXEL_AREA: Final = 24_000_000


class RenderDetail(StrEnum):
    NORMAL = "NORMAL"
    HIGH_DETAIL = "HIGH_DETAIL"


class TableRenderMode(StrEnum):
    TABLE_ONLY = "TABLE_ONLY"
    TABLE_WITH_HEADER = "TABLE_WITH_HEADER"
    TABLE_WITH_SURROUNDING_CONTEXT = "TABLE_WITH_SURROUNDING_CONTEXT"


class VisualRenderError(RuntimeError):
    def __init__(self, reason_code: str, message: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


@dataclass(frozen=True, slots=True)
class RenderedVisual:
    visual_ref_id: str
    render_sha256: str
    mime_type: str
    png_bytes: bytes
    metadata: dict[str, Any]

    def public_metadata(self) -> dict[str, Any]:
        return {
            "visual_ref_id": self.visual_ref_id,
            "render_sha256": self.render_sha256,
            "mime_type": self.mime_type,
            **dict(self.metadata),
        }


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _dpi(detail: RenderDetail) -> int:
    return _HIGH_DETAIL_DPI if detail is RenderDetail.HIGH_DETAIL else _NORMAL_DPI


def _rounded_rect(rect: pymupdf.Rect) -> list[float]:
    return [
        round(float(rect.x0), 3),
        round(float(rect.y0), 3),
        round(float(rect.x1), 3),
        round(float(rect.y1), 3),
    ]


def _visual_ref(identity: dict[str, object]) -> str:
    return _sha256(_canonical_bytes(identity))


def _valid_bbox(value: object) -> tuple[float, float, float, float]:
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        raise VisualRenderError(
            "RESEARCH_MCP_RENDER_FAILED",
            "table bbox is invalid",
        )
    try:
        x0, y0, x1, y1 = (float(item) for item in value)
    except (TypeError, ValueError) as exc:
        raise VisualRenderError(
            "RESEARCH_MCP_RENDER_FAILED",
            "table bbox contains non-numeric coordinates",
        ) from exc
    if x1 <= x0 or y1 <= y0:
        raise VisualRenderError(
            "RESEARCH_MCP_RENDER_FAILED",
            "table bbox has non-positive size",
        )
    return x0, y0, x1, y1


class PdfVisualRenderer:
    def __init__(
        self,
        *,
        catalog: McpCatalog,
        p8_service: McpQueryService,
        registry_path: str | Path,
        trusted_raw_root: str | Path,
        max_pixel_area: int = _MAX_PIXEL_AREA,
        max_png_bytes: int = _MAX_PNG_BYTES,
    ) -> None:
        self.catalog = catalog
        self.p8 = p8_service
        self.registry_path = Path(registry_path).expanduser().resolve()
        self.trusted_raw_root = Path(trusted_raw_root).expanduser().resolve()
        if (
            isinstance(max_pixel_area, bool)
            or not isinstance(max_pixel_area, int)
            or max_pixel_area < 100_000
        ):
            raise ValueError("max_pixel_area must be an integer >= 100000")
        if (
            isinstance(max_png_bytes, bool)
            or not isinstance(max_png_bytes, int)
            or max_png_bytes < 100_000
        ):
            raise ValueError("max_png_bytes must be an integer >= 100000")
        self.max_pixel_area = max_pixel_area
        self.max_png_bytes = max_png_bytes
        self._cache: dict[str, RenderedVisual] = {}
        self.repeated_visual_avoided_count = 0
        self.visual_call_count = 0
        self._unique_page_targets: set[tuple[str, int]] = set()
        self._unique_table_targets: set[tuple[str, str]] = set()

    def _source(self, document_sha256: str):
        try:
            return resolve_trusted_pdf_source(
                catalog=self.catalog,
                registry_path=self.registry_path,
                trusted_raw_root=self.trusted_raw_root,
                document_sha256=document_sha256,
            )
        except TrustedSourceError as exc:
            raise VisualRenderError(exc.reason_code, str(exc)) from exc

    def _render_clip(
        self,
        *,
        document_sha256: str,
        page_no: int,
        clip: pymupdf.Rect | None,
        detail: RenderDetail,
        target_kind: str,
        target_id: str | None,
        tile_index: int = 0,
        tile_count: int = 1,
    ) -> RenderedVisual:
        source = self._source(document_sha256)
        if page_no < 1 or page_no > source.page_count:
            raise VisualRenderError(
                "RESEARCH_MCP_PAGE_INVALID",
                "page_no is outside the trusted PDF page range",
            )
        dpi = _dpi(detail)
        try:
            with pymupdf.open(source.path) as pdf:
                page = pdf[page_no - 1]
                page_rect = page.rect
                effective_clip = page_rect if clip is None else clip & page_rect
                if effective_clip.is_empty or effective_clip.width <= 0 or effective_clip.height <= 0:
                    raise VisualRenderError(
                        "RESEARCH_MCP_RENDER_FAILED",
                        "render clip is empty after page intersection",
                    )
                scale = dpi / 72.0
                pixel_area = int(effective_clip.width * scale) * int(
                    effective_clip.height * scale
                )
                if pixel_area > self.max_pixel_area:
                    raise VisualRenderError(
                        "RESEARCH_MCP_PAYLOAD_LIMIT",
                        "requested render exceeds deterministic pixel-area limit",
                    )

                identity = {
                    "renderer_version": PDF_RENDERER_VERSION,
                    "document_sha256": source.document_sha256,
                    "page_no": page_no,
                    "clip": _rounded_rect(effective_clip),
                    "detail": detail.value,
                    "dpi": dpi,
                    "target_kind": target_kind,
                    "target_id": target_id,
                    "tile_index": tile_index,
                    "tile_count": tile_count,
                    "alpha": False,
                    "colorspace": "RGB",
                    "format": "PNG",
                }
                visual_ref_id = _visual_ref(identity)
                cached = self._cache.get(visual_ref_id)
                if cached is not None:
                    self.repeated_visual_avoided_count += 1
                    return cached

                pix = page.get_pixmap(
                    matrix=pymupdf.Matrix(scale, scale),
                    clip=effective_clip,
                    alpha=False,
                    colorspace=pymupdf.csRGB,
                )
                png = pix.tobytes("png")
        except VisualRenderError:
            raise
        except Exception as exc:
            raise VisualRenderError(
                "RESEARCH_MCP_RENDER_FAILED",
                "PyMuPDF failed to render trusted PDF source",
            ) from exc

        if len(png) > self.max_png_bytes:
            raise VisualRenderError(
                "RESEARCH_MCP_PAYLOAD_LIMIT",
                "rendered PNG exceeds deterministic payload limit",
            )
        rendered = RenderedVisual(
            visual_ref_id=visual_ref_id,
            render_sha256=_sha256(png),
            mime_type="image/png",
            png_bytes=png,
            metadata={
                "renderer_version": PDF_RENDERER_VERSION,
                "document_sha256": source.document_sha256,
                "page_no": page_no,
                "clip": identity["clip"],
                "detail": detail.value,
                "dpi": dpi,
                "target_kind": target_kind,
                "target_id": target_id,
                "tile_index": tile_index,
                "tile_count": tile_count,
                "page_count": source.page_count,
            },
        )
        self._cache[visual_ref_id] = rendered
        return rendered

    def _tile_clips(
        self,
        clip: pymupdf.Rect,
        detail: RenderDetail,
    ) -> tuple[pymupdf.Rect, ...]:
        scale = _dpi(detail) / 72.0
        def area(rect: pymupdf.Rect) -> int:
            return max(1, int(rect.width * scale)) * max(
                1, int(rect.height * scale)
            )

        if area(clip) <= self.max_pixel_area:
            return (clip,)

        split_vertical = clip.height >= clip.width
        overlap = 18.0
        tile_count = 2
        while True:
            tiles: list[pymupdf.Rect] = []
            if split_vertical:
                step = clip.height / tile_count
                for index in range(tile_count):
                    y0 = clip.y0 + index * step
                    y1 = clip.y0 + (index + 1) * step
                    if index > 0:
                        y0 -= overlap
                    if index < tile_count - 1:
                        y1 += overlap
                    tiles.append(pymupdf.Rect(clip.x0, y0, clip.x1, y1))
            else:
                step = clip.width / tile_count
                for index in range(tile_count):
                    x0 = clip.x0 + index * step
                    x1 = clip.x0 + (index + 1) * step
                    if index > 0:
                        x0 -= overlap
                    if index < tile_count - 1:
                        x1 += overlap
                    tiles.append(pymupdf.Rect(x0, clip.y0, x1, clip.y1))
            if all(area(tile) <= self.max_pixel_area for tile in tiles):
                return tuple(tiles)
            tile_count += 1
            if tile_count > 32:
                raise VisualRenderError(
                    "RESEARCH_MCP_PAYLOAD_LIMIT",
                    "render target requires more than 32 deterministic tiles",
                )

    def _render_target(
        self,
        *,
        document_sha256: str,
        page_no: int,
        clip: pymupdf.Rect | None,
        detail: RenderDetail,
        target_kind: str,
        target_id: str | None,
    ) -> tuple[RenderedVisual, ...]:
        source = self._source(document_sha256)
        if page_no < 1 or page_no > source.page_count:
            raise VisualRenderError(
                "RESEARCH_MCP_PAGE_INVALID",
                "page_no is outside the trusted PDF page range",
            )
        with pymupdf.open(source.path) as pdf:
            page_rect = pdf[page_no - 1].rect
        effective = page_rect if clip is None else clip & page_rect
        if effective.is_empty or effective.width <= 0 or effective.height <= 0:
            raise VisualRenderError(
                "RESEARCH_MCP_RENDER_FAILED",
                "render target is empty after page intersection",
            )
        tiles = self._tile_clips(effective, detail)
        self.visual_call_count += 1
        if target_kind == "PAGE":
            self._unique_page_targets.add((document_sha256, page_no))
        elif target_kind == "TABLE" and target_id:
            self._unique_table_targets.add((document_sha256, target_id))
        return tuple(
            self._render_clip(
                document_sha256=document_sha256,
                page_no=page_no,
                clip=tile,
                detail=detail,
                target_kind=target_kind,
                target_id=target_id,
                tile_index=index,
                tile_count=len(tiles),
            )
            for index, tile in enumerate(tiles)
        )

    def telemetry(self) -> dict[str, int]:
        return {
            "visual_call_count": self.visual_call_count,
            "rendered_unique_page_count": len(self._unique_page_targets),
            "rendered_unique_table_count": len(self._unique_table_targets),
            "rendered_unique_image_count": len(self._cache),
            "repeated_visual_avoided_count": self.repeated_visual_avoided_count,
        }

    def render_page(
        self,
        document_sha256: str,
        page_no: int,
        *,
        detail: RenderDetail | str = RenderDetail.NORMAL,
    ) -> tuple[RenderedVisual, ...]:
        try:
            normalized_detail = (
                detail if isinstance(detail, RenderDetail) else RenderDetail(str(detail))
            )
        except ValueError as exc:
            raise VisualRenderError(
                "RESEARCH_MCP_RENDER_FAILED",
                "detail must be NORMAL or HIGH_DETAIL",
            ) from exc
        return self._render_target(
            document_sha256=document_sha256,
            page_no=int(page_no),
            clip=None,
            detail=normalized_detail,
            target_kind="PAGE",
            target_id=str(page_no),
        )

    def render_table(
        self,
        document_sha256: str,
        table_id: str,
        *,
        mode: TableRenderMode | str = TableRenderMode.TABLE_WITH_HEADER,
        detail: RenderDetail | str = RenderDetail.NORMAL,
    ) -> tuple[RenderedVisual, ...]:
        try:
            normalized_mode = (
                mode if isinstance(mode, TableRenderMode) else TableRenderMode(str(mode))
            )
            normalized_detail = (
                detail if isinstance(detail, RenderDetail) else RenderDetail(str(detail))
            )
        except ValueError as exc:
            raise VisualRenderError(
                "RESEARCH_MCP_RENDER_FAILED",
                "invalid table render mode/detail",
            ) from exc
        try:
            table = self.p8.get_table(document_sha256, table_id, 500)["data"]
        except McpServiceError as exc:
            raise VisualRenderError(
                "RESEARCH_MCP_TABLE_NOT_FOUND",
                str(exc),
            ) from exc
        x0, y0, x1, y1 = _valid_bbox(table.get("bbox"))
        if normalized_mode is TableRenderMode.TABLE_ONLY:
            left = right = top = bottom = 0.0
        elif normalized_mode is TableRenderMode.TABLE_WITH_HEADER:
            left = right = 12.0
            top = 72.0
            bottom = 12.0
        else:
            left = right = 24.0
            top = 120.0
            bottom = 72.0
        clip = pymupdf.Rect(
            x0 - left,
            y0 - top,
            x1 + right,
            y1 + bottom,
        )
        return self._render_target(
            document_sha256=document_sha256,
            page_no=int(table.get("page_no") or 0),
            clip=clip,
            detail=normalized_detail,
            target_kind="TABLE",
            target_id=str(table_id),
        )

    def render_table_group(
        self,
        document_sha256: str,
        table_group_id: str,
        *,
        detail: RenderDetail | str = RenderDetail.NORMAL,
    ) -> tuple[RenderedVisual, ...]:
        try:
            group = self.p8.get_table_group_internal(
                document_sha256,
                table_group_id,
            )
        except McpServiceError as exc:
            raise VisualRenderError(
                "RESEARCH_MCP_TABLE_GROUP_NOT_FOUND",
                str(exc),
            ) from exc
        members = list(group.get("member_table_ids") or [])
        if not members:
            raise VisualRenderError(
                "RESEARCH_MCP_TABLE_GROUP_NOT_FOUND",
                "table group has no member_table_ids",
            )
        visuals: list[RenderedVisual] = []
        for table_id in members:
            visuals.extend(
                self.render_table(
                    document_sha256,
                    str(table_id),
                    mode=TableRenderMode.TABLE_WITH_HEADER,
                    detail=detail,
                )
            )
        return tuple(visuals)
