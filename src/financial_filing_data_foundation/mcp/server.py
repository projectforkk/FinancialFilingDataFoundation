from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path
from typing import Any, Callable, TypeVar

from mcp import types as mcp_types
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from financial_filing_data_foundation.mcp.catalog import CatalogError, McpCatalog
from financial_filing_data_foundation.mcp.service import (
    McpQueryService,
    McpServiceError,
)
from financial_filing_data_foundation.mcp.report_safe import (
    find_table_rows as _find_table_rows,
    get_company_report_context as _get_company_report_context,
    search_company as _search_company,
)
from financial_filing_data_foundation.mcp.research_review import (
    ResearchReviewError,
    ResearchReviewService,
)
from financial_filing_data_foundation.mcp.research_review_contract import (
    ResearchReviewProfile,
)
from financial_filing_data_foundation.mcp.visual_renderer import (
    PdfVisualRenderer,
    VisualRenderError,
)


SERVER_NAME = "ffdf-local"
SERVER_VERSION = "p8-local-mcp-v1"

TOOL_NAMES = (
    "ffdf_list_documents",
    "ffdf_get_document",
    "ffdf_search_document",
    "ffdf_read_pages",
    "ffdf_list_sections",
    "ffdf_list_tables",
    "ffdf_get_table",
    "ffdf_list_raw_facts",
    "ffdf_get_fact",
    "ffdf_get_evidence",
    "ffdf_get_validation",
    "ffdf_get_company_report_context",
    "ffdf_search_company",
    "ffdf_find_table_rows",
    "ffdf_get_review_state",
    "ffdf_get_resolved_fact",
    "ffdf_list_resolved_facts",
    "ffdf_list_review_tasks",
    "ffdf_get_review_context",
    "ffdf_locate_evidence",
    "ffdf_render_table",
    "ffdf_render_table_group",
    "ffdf_render_page",
    "ffdf_prepare_review_overlay",
    "ffdf_submit_review_resolution",
    "ffdf_materialize_resolved_view",
)

T = TypeVar("T")


def _tool_call(function: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    try:
        return function(*args, **kwargs)
    except (McpServiceError, ResearchReviewError, VisualRenderError) as exc:
        raise ToolError(f"{exc.reason_code}: {exc}") from exc


def _visual_content(visuals: tuple[Any, ...]) -> list[Any]:
    metadata = [item.public_metadata() for item in visuals]
    content: list[Any] = [
        mcp_types.TextContent(
            text=json.dumps(
                {
                    "schema_version": "research-visual-content-v1",
                    "images": metadata,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
    ]
    for item in visuals:
        high_detail = str(item.metadata.get("detail") or "") == "HIGH_DETAIL"
        content.append(
            mcp_types.ImageContent(
                data=base64.b64encode(item.png_bytes).decode("ascii"),
                mimeType=item.mime_type,
                _meta=(
                    {"codex/imageDetail": "original"}
                    if high_detail
                    else None
                ),
            )
        )
    return content


def create_server(
    project_root: str | Path,
    catalog_path: str | Path,
    review_root: str | Path = "workspace/p9-live-review",
    registry_path: str | Path = "workspace/ingest/registry.sqlite",
    trusted_raw_root: str | Path = "workspace/ingest/raw-store",
    research_review_profile: str = "RESEARCH_FALLBACK",
) -> MCPServer:
    try:
        catalog = McpCatalog.load(project_root, catalog_path)
        service = McpQueryService(catalog)
        root = Path(project_root).expanduser().resolve()
        review_service = ResearchReviewService(
            project_root=root,
            catalog=catalog,
            p8_service=service,
            review_root=review_root,
            profile=research_review_profile,
        )
        registry = Path(registry_path)
        if not registry.is_absolute():
            registry = root / registry
        trusted_raw = Path(trusted_raw_root)
        if not trusted_raw.is_absolute():
            trusted_raw = root / trusted_raw
        renderer = PdfVisualRenderer(
            catalog=catalog,
            p8_service=service,
            registry_path=registry,
            trusted_raw_root=trusted_raw,
        )
    except CatalogError as exc:
        raise RuntimeError(f"{exc.reason_code}: {exc}") from exc
    except McpServiceError as exc:
        raise RuntimeError(f"{exc.reason_code}: {exc}") from exc

    server = MCPServer(
        name=SERVER_NAME,
        version=SERVER_VERSION,
        description=(
            "Local access to validated FFDF artifacts with additive report-safe, "
            "resolved review, and PDF visual capabilities."
        ),
        instructions=(
            "All tools are deterministic and local. No network, AI, or arbitrary "
            "filesystem access is available. Research fallback is read-only; "
            "P9 write-through requires explicit QUALITY_REVIEW profile. "
            "For research reports, prefer exact direct disclosure rows over "
            "manual recomposition, preserve source labels, search newer "
            "filings before carrying forward an older event state, and read "
            "neighbor pages before treating a multi-page section as complete. "
            "Derived values must declare their components. The filing catalog "
            "is not a complete temporary-announcement event feed."
        ),
        log_level="WARNING",
    )

    @server.tool(
        name="ffdf_list_documents",
        description="List validated local filing documents in the configured catalog.",
        structured_output=True,
    )
    def ffdf_list_documents(
        market: str | None = None,
        ticker: str | None = None,
        fiscal_year: int | None = None,
    ) -> dict[str, Any]:
        return _tool_call(
            service.list_documents,
            market,
            ticker,
            fiscal_year,
        )

    @server.tool(
        name="ffdf_get_document",
        description="Get counts and validation summary for one local filing document.",
        structured_output=True,
    )
    def ffdf_get_document(document_sha256: str) -> dict[str, Any]:
        return _tool_call(service.get_document, document_sha256)

    @server.tool(
        name="ffdf_search_document",
        description="Search one filing's local P3 FTS index. This is not web search.",
        structured_output=True,
    )
    def ffdf_search_document(
        document_sha256: str,
        query: str,
        limit: int = 10,
    ) -> dict[str, Any]:
        return _tool_call(
            service.search_document,
            document_sha256,
            query,
            limit,
        )

    @server.tool(
        name="ffdf_read_pages",
        description="Read text and basic geometry for up to ten physical pages.",
        structured_output=True,
    )
    def ffdf_read_pages(
        document_sha256: str,
        page_nos: list[int],
    ) -> dict[str, Any]:
        return _tool_call(
            service.read_pages,
            document_sha256,
            page_nos,
        )

    @server.tool(
        name="ffdf_list_sections",
        description="List deterministic P3 sections for a document.",
        structured_output=True,
    )
    def ffdf_list_sections(document_sha256: str) -> dict[str, Any]:
        return _tool_call(service.list_sections, document_sha256)

    @server.tool(
        name="ffdf_list_tables",
        description="List reconstructed P5 table summaries with pagination.",
        structured_output=True,
    )
    def ffdf_list_tables(
        document_sha256: str,
        page_no: int | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> dict[str, Any]:
        return _tool_call(
            service.list_tables,
            document_sha256,
            page_no,
            offset,
            limit,
        )

    @server.tool(
        name="ffdf_get_table",
        description="Get reconstructed P5 table rows/cells with a bounded row count.",
        structured_output=True,
    )
    def ffdf_get_table(
        document_sha256: str,
        table_id: str,
        max_rows: int = 100,
    ) -> dict[str, Any]:
        return _tool_call(
            service.get_table,
            document_sha256,
            table_id,
            max_rows,
        )

    @server.tool(
        name="ffdf_list_raw_facts",
        description="List source-preserving P6 raw facts with optional local filters.",
        structured_output=True,
    )
    def ffdf_list_raw_facts(
        document_sha256: str,
        page_no: int | None = None,
        metric_contains: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> dict[str, Any]:
        return _tool_call(
            service.list_raw_facts,
            document_sha256,
            page_no,
            metric_contains,
            offset,
            limit,
        )

    @server.tool(
        name="ffdf_get_fact",
        description="Get one exact P6 raw fact by stable raw_fact_id.",
        structured_output=True,
    )
    def ffdf_get_fact(
        document_sha256: str,
        raw_fact_id: str,
    ) -> dict[str, Any]:
        return _tool_call(
            service.get_fact,
            document_sha256,
            raw_fact_id,
        )

    @server.tool(
        name="ffdf_get_evidence",
        description="Get first-class P6 evidence and source-word references.",
        structured_output=True,
    )
    def ffdf_get_evidence(
        document_sha256: str,
        evidence_id: str,
    ) -> dict[str, Any]:
        return _tool_call(
            service.get_evidence,
            document_sha256,
            evidence_id,
        )

    @server.tool(
        name="ffdf_get_validation",
        description=(
            "Get persisted P7 validation report/issues. Upstream execution "
            "errors remain tool errors rather than validation BLOCKED."
        ),
        structured_output=True,
    )
    def ffdf_get_validation(
        document_sha256: str,
        include_issues: bool = True,
        severity: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> dict[str, Any]:
        return _tool_call(
            service.get_validation,
            document_sha256,
            include_issues,
            severity,
            offset,
            limit,
        )

    @server.tool(
        name="ffdf_get_company_report_context",
        description=(
            "Get report-safe company filing context, validation summaries, "
            "chronology limits, and research guardrails."
        ),
        structured_output=True,
    )
    def ffdf_get_company_report_context(
        market: str,
        ticker: str,
        fiscal_year_from: int | None = None,
        fiscal_year_to: int | None = None,
    ) -> dict[str, Any]:
        return _tool_call(
            _get_company_report_context,
            service,
            market,
            ticker,
            fiscal_year_from,
            fiscal_year_to,
        )

    @server.tool(
        name="ffdf_search_company",
        description=(
            "Search the same company across local filings, newest first, "
            "and include neighboring P3 pages to reduce stale-state and "
            "multi-page omission errors."
        ),
        structured_output=True,
    )
    def ffdf_search_company(
        market: str,
        ticker: str,
        query: str,
        fiscal_year_from: int | None = None,
        fiscal_year_to: int | None = None,
        document_limit: int = 20,
        limit_per_document: int = 3,
        page_window: int = 1,
    ) -> dict[str, Any]:
        return _tool_call(
            _search_company,
            service,
            market,
            ticker,
            query,
            fiscal_year_from,
            fiscal_year_to,
            document_limit,
            limit_per_document,
            page_window,
        )

    @server.tool(
        name="ffdf_find_table_rows",
        description=(
            "Find exact or containing P5 source row labels across a company. "
            "Returns original disclosure labels and full row cells so reports "
            "can prefer direct disclosure over manual recomposition."
        ),
        structured_output=True,
    )
    def ffdf_find_table_rows(
        market: str,
        ticker: str,
        label: str,
        match_mode: str = "exact",
        fiscal_year: int | None = None,
        filing_type: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        return _tool_call(
            _find_table_rows,
            service,
            market,
            ticker,
            label,
            match_mode,
            fiscal_year,
            filing_type,
            limit,
        )

    @server.tool(
        name="ffdf_get_review_state",
        description="Get derived P7/P9 quality state without materializing or mutating review data.",
        structured_output=True,
    )
    def ffdf_get_review_state(document_sha256: str) -> dict[str, Any]:
        return _tool_call(review_service.get_review_state, document_sha256)

    @server.tool(
        name="ffdf_get_resolved_fact",
        description="Get one RawFact together with effective P9 semantic fields and provenance.",
        structured_output=True,
    )
    def ffdf_get_resolved_fact(
        document_sha256: str,
        raw_fact_id: str,
    ) -> dict[str, Any]:
        return _tool_call(review_service.get_resolved_fact, document_sha256, raw_fact_id)

    @server.tool(
        name="ffdf_list_resolved_facts",
        description="List effective facts while preserving underlying RawFact identity.",
        structured_output=True,
    )
    def ffdf_list_resolved_facts(
        document_sha256: str,
        offset: int = 0,
        limit: int = 50,
    ) -> dict[str, Any]:
        return _tool_call(
            review_service.list_resolved_facts,
            document_sha256,
            offset=offset,
            limit=limit,
        )

    @server.tool(
        name="ffdf_list_review_tasks",
        description="List deterministic P9 review tasks and active-resolution flags.",
        structured_output=True,
    )
    def ffdf_list_review_tasks(document_sha256: str) -> dict[str, Any]:
        return _tool_call(review_service.list_review_tasks, document_sha256)

    @server.tool(
        name="ffdf_get_review_context",
        description="Get minimal structured P3/P5/P6/P7/P9 context for one review task.",
        structured_output=True,
    )
    def ffdf_get_review_context(
        document_sha256: str,
        review_task_id: str,
    ) -> dict[str, Any]:
        return _tool_call(
            review_service.get_review_context,
            document_sha256,
            review_task_id,
        )

    @server.tool(
        name="ffdf_locate_evidence",
        description="Locate P3 pages, P5 tables and P6 facts without creating new RawFacts.",
        structured_output=True,
    )
    def ffdf_locate_evidence(
        document_sha256: str,
        query: str,
        limit: int = 10,
    ) -> dict[str, Any]:
        return _tool_call(
            review_service.locate_evidence,
            document_sha256,
            query,
            limit=limit,
        )

    @server.tool(
        name="ffdf_render_table",
        description="Render a trusted-original-PDF table crop; no path or arbitrary bbox input.",
        structured_output=False,
    )
    def ffdf_render_table(
        document_sha256: str,
        table_id: str,
        mode: str = "TABLE_WITH_HEADER",
        detail: str = "NORMAL",
    ) -> list[Any]:
        return _visual_content(
            _tool_call(
                renderer.render_table,
                document_sha256,
                table_id,
                mode=mode,
                detail=detail,
            )
        )

    @server.tool(
        name="ffdf_render_table_group",
        description="Render P5-declared members of one deterministic cross-page table group.",
        structured_output=False,
    )
    def ffdf_render_table_group(
        document_sha256: str,
        table_group_id: str,
        detail: str = "NORMAL",
    ) -> list[Any]:
        return _visual_content(
            _tool_call(
                renderer.render_table_group,
                document_sha256,
                table_group_id,
                detail=detail,
            )
        )

    @server.tool(
        name="ffdf_render_page",
        description="Render one trusted original PDF physical page by SHA and 1-based page number.",
        structured_output=False,
    )
    def ffdf_render_page(
        document_sha256: str,
        page_no: int,
        detail: str = "NORMAL",
    ) -> list[Any]:
        return _visual_content(
            _tool_call(
                renderer.render_page,
                document_sha256,
                page_no,
                detail=detail,
            )
        )

    @server.tool(
        name="ffdf_prepare_review_overlay",
        description="QUALITY_REVIEW-only explicit P9 overlay preparation.",
        structured_output=True,
    )
    def ffdf_prepare_review_overlay(document_sha256: str) -> dict[str, Any]:
        return _tool_call(review_service.prepare_review_overlay, document_sha256)

    @server.tool(
        name="ffdf_submit_review_resolution",
        description="QUALITY_REVIEW-only P9 v1 resolution with optimistic state checks.",
        structured_output=True,
    )
    def ffdf_submit_review_resolution(
        document_sha256: str,
        submission: dict[str, Any],
        expected_base_validation_report_sha256: str,
        expected_overlay_set_hash_before: str,
    ) -> dict[str, Any]:
        return _tool_call(
            review_service.submit_review_resolution,
            document_sha256,
            submission,
            expected_base_validation_report_sha256=expected_base_validation_report_sha256,
            expected_overlay_set_hash_before=expected_overlay_set_hash_before,
        )

    @server.tool(
        name="ffdf_materialize_resolved_view",
        description="QUALITY_REVIEW-only explicit materialization of the active P9 overlay set.",
        structured_output=True,
    )
    def ffdf_materialize_resolved_view(document_sha256: str) -> dict[str, Any]:
        return _tool_call(review_service.materialize_resolved_view, document_sha256)

    return server


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="FFDF P8 read-only local MCP stdio server"
    )
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--review-root", default="workspace/p9-live-review")
    parser.add_argument("--registry", default="workspace/ingest/registry.sqlite")
    parser.add_argument("--trusted-raw-root", default="workspace/ingest/raw-store")
    parser.add_argument(
        "--research-review-profile",
        choices=tuple(item.value for item in ResearchReviewProfile),
        default=ResearchReviewProfile.RESEARCH_FALLBACK.value,
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    server = create_server(
        args.project_root,
        args.catalog,
        args.review_root,
        args.registry,
        args.trusted_raw_root,
        args.research_review_profile,
    )
    server.run("stdio")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
