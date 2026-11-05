from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Callable, TypeVar

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
)

T = TypeVar("T")


def _tool_call(function: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    try:
        return function(*args, **kwargs)
    except McpServiceError as exc:
        raise ToolError(f"{exc.reason_code}: {exc}") from exc


def create_server(
    project_root: str | Path,
    catalog_path: str | Path,
) -> MCPServer:
    try:
        catalog = McpCatalog.load(project_root, catalog_path)
        service = McpQueryService(catalog)
    except CatalogError as exc:
        raise RuntimeError(f"{exc.reason_code}: {exc}") from exc
    except McpServiceError as exc:
        raise RuntimeError(f"{exc.reason_code}: {exc}") from exc

    server = MCPServer(
        name=SERVER_NAME,
        version=SERVER_VERSION,
        description=(
            "Read-only local access to validated Financial Filing Data "
            "Foundation artifacts."
        ),
        instructions=(
            "All tools are deterministic and local. No network, AI, "
            "arbitrary filesystem access, or mutation is available. "
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

    return server


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="FFDF P8 read-only local MCP stdio server"
    )
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--catalog", required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    server = create_server(args.project_root, args.catalog)
    server.run("stdio")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
