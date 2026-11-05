from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

from mcp import Client
from mcp.client.stdio import StdioServerParameters


EXPECTED_TOOLS = (
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


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def _structured(result: Any) -> dict[str, Any]:
    if result.is_error:
        raise AssertionError(f"unexpected tool error: {result.content!r}")
    value = result.structured_content
    if not isinstance(value, dict):
        raise AssertionError(
            f"missing structured_content: {value!r}; content={result.content!r}"
        )
    return value


async def _run(args: argparse.Namespace) -> dict[str, Any]:
    project_root = args.project_root.resolve()
    source_root = args.source_root.resolve()
    env = dict(os.environ)
    env["PYTHONPATH"] = str(source_root / "src")
    params = StdioServerParameters(
        command=sys.executable,
        args=[
            "-m",
            "financial_filing_data_foundation.mcp.server",
            "--project-root",
            str(project_root),
            "--catalog",
            args.catalog,
        ],
        env=env,
        cwd=source_root,
    )

    connect_start = time.perf_counter()
    async with Client(
        params,
        mode="auto",
        read_timeout_seconds=45,
    ) as client:
        connected_ms = round(
            (time.perf_counter() - connect_start) * 1000.0,
            3,
        )
        protocol_version = str(client.protocol_version)

        tools_result = await client.list_tools()
        tool_names = tuple(tool.name for tool in tools_result.tools)
        if tool_names != EXPECTED_TOOLS:
            raise AssertionError(
                f"unexpected tools: expected={EXPECTED_TOOLS}, got={tool_names}"
            )

        listed = _structured(await client.call_tool("ffdf_list_documents"))
        docs = listed["data"]["documents"]
        if len(docs) != 2:
            raise AssertionError(f"expected two live docs, got {len(docs)}")
        by_market = {row["market"]: row for row in docs}
        cn = by_market["CN"]
        hk = by_market["HK"]

        cn_load_start = time.perf_counter()
        cn_detail = _structured(
            await client.call_tool(
                "ffdf_get_document",
                {"document_sha256": cn["document_sha256"]},
            )
        )
        cn_first_bundle_ms = round(
            (time.perf_counter() - cn_load_start) * 1000.0,
            3,
        )

        hk_load_start = time.perf_counter()
        hk_detail = _structured(
            await client.call_tool(
                "ffdf_get_document",
                {"document_sha256": hk["document_sha256"]},
            )
        )
        hk_first_bundle_ms = round(
            (time.perf_counter() - hk_load_start) * 1000.0,
            3,
        )

        cn_search = _structured(
            await client.call_tool(
                "ffdf_search_document",
                {
                    "document_sha256": cn["document_sha256"],
                    "query": "营业收入",
                    "limit": 5,
                },
            )
        )
        cn_pages = _structured(
            await client.call_tool(
                "ffdf_read_pages",
                {
                    "document_sha256": cn["document_sha256"],
                    "page_nos": [1],
                },
            )
        )
        cn_sections = _structured(
            await client.call_tool(
                "ffdf_list_sections",
                {"document_sha256": cn["document_sha256"]},
            )
        )

        cn_tables = _structured(
            await client.call_tool(
                "ffdf_list_tables",
                {
                    "document_sha256": cn["document_sha256"],
                    "offset": 0,
                    "limit": 5,
                },
            )
        )
        table_id = cn_tables["data"]["tables"][0]["table_id"]
        cn_table = _structured(
            await client.call_tool(
                "ffdf_get_table",
                {
                    "document_sha256": cn["document_sha256"],
                    "table_id": table_id,
                    "max_rows": 20,
                },
            )
        )

        cn_facts = _structured(
            await client.call_tool(
                "ffdf_list_raw_facts",
                {
                    "document_sha256": cn["document_sha256"],
                    "offset": 0,
                    "limit": 5,
                },
            )
        )
        first_fact = cn_facts["data"]["facts"][0]
        cn_fact = _structured(
            await client.call_tool(
                "ffdf_get_fact",
                {
                    "document_sha256": cn["document_sha256"],
                    "raw_fact_id": first_fact["raw_fact_id"],
                },
            )
        )
        cn_evidence = _structured(
            await client.call_tool(
                "ffdf_get_evidence",
                {
                    "document_sha256": cn["document_sha256"],
                    "evidence_id": first_fact["evidence_id"],
                },
            )
        )
        cn_validation = _structured(
            await client.call_tool(
                "ffdf_get_validation",
                {
                    "document_sha256": cn["document_sha256"],
                    "include_issues": True,
                    "offset": 0,
                    "limit": 100,
                },
            )
        )
        hk_validation = _structured(
            await client.call_tool(
                "ffdf_get_validation",
                {
                    "document_sha256": hk["document_sha256"],
                    "include_issues": True,
                    "offset": 0,
                    "limit": 100,
                },
            )
        )

        invalid = await client.call_tool(
            "ffdf_get_document",
            {"document_sha256": "f" * 64},
        )
        if not invalid.is_error:
            raise AssertionError("invalid document should return is_error=True")

        perf: dict[str, float] = {}

        started = time.perf_counter()
        _structured(await client.call_tool("ffdf_list_documents"))
        perf["list_documents_ms"] = round(
            (time.perf_counter() - started) * 1000.0, 3
        )

        started = time.perf_counter()
        _structured(
            await client.call_tool(
                "ffdf_get_document",
                {"document_sha256": cn["document_sha256"]},
            )
        )
        perf["warm_get_document_ms"] = round(
            (time.perf_counter() - started) * 1000.0, 3
        )

        started = time.perf_counter()
        _structured(
            await client.call_tool(
                "ffdf_search_document",
                {
                    "document_sha256": cn["document_sha256"],
                    "query": "营业收入",
                    "limit": 5,
                },
            )
        )
        perf["warm_search_ms"] = round(
            (time.perf_counter() - started) * 1000.0, 3
        )

        started = time.perf_counter()
        _structured(
            await client.call_tool(
                "ffdf_read_pages",
                {
                    "document_sha256": cn["document_sha256"],
                    "page_nos": [1],
                },
            )
        )
        perf["warm_read_pages_ms"] = round(
            (time.perf_counter() - started) * 1000.0, 3
        )

        started = time.perf_counter()
        _structured(
            await client.call_tool(
                "ffdf_get_table",
                {
                    "document_sha256": cn["document_sha256"],
                    "table_id": table_id,
                    "max_rows": 20,
                },
            )
        )
        perf["warm_get_table_ms"] = round(
            (time.perf_counter() - started) * 1000.0, 3
        )

        started = time.perf_counter()
        _structured(
            await client.call_tool(
                "ffdf_get_fact",
                {
                    "document_sha256": cn["document_sha256"],
                    "raw_fact_id": first_fact["raw_fact_id"],
                },
            )
        )
        _structured(
            await client.call_tool(
                "ffdf_get_evidence",
                {
                    "document_sha256": cn["document_sha256"],
                    "evidence_id": first_fact["evidence_id"],
                },
            )
        )
        perf["warm_fact_evidence_ms"] = round(
            (time.perf_counter() - started) * 1000.0, 3
        )

        started = time.perf_counter()
        _structured(
            await client.call_tool(
                "ffdf_get_validation",
                {
                    "document_sha256": cn["document_sha256"],
                    "include_issues": True,
                    "offset": 0,
                    "limit": 100,
                },
            )
        )
        perf["warm_validation_ms"] = round(
            (time.perf_counter() - started) * 1000.0, 3
        )

        limits = {
            "cold_connect_ms": (connected_ms, 15000.0),
            "cn_first_bundle_ms": (cn_first_bundle_ms, 20000.0),
            "hk_first_bundle_ms": (hk_first_bundle_ms, 20000.0),
            "list_documents_ms": (perf["list_documents_ms"], 2000.0),
            "warm_get_document_ms": (perf["warm_get_document_ms"], 2000.0),
            "warm_search_ms": (perf["warm_search_ms"], 2000.0),
            "warm_read_pages_ms": (perf["warm_read_pages_ms"], 2000.0),
            "warm_get_table_ms": (perf["warm_get_table_ms"], 5000.0),
            "warm_fact_evidence_ms": (perf["warm_fact_evidence_ms"], 5000.0),
            "warm_validation_ms": (perf["warm_validation_ms"], 5000.0),
        }
        for name, (observed, maximum) in limits.items():
            if observed > maximum:
                raise AssertionError(
                    f"performance gate failed: {name}={observed}ms > {maximum}ms"
                )

        return {
            "protocol_version": protocol_version,
            "cold_connect_ms": connected_ms,
            "tool_names": list(tool_names),
            "document_count": len(docs),
            "cn": {
                "first_bundle_load_ms": cn_first_bundle_ms,
                "page_count": cn_detail["data"]["page_count"],
                "table_count": cn_detail["data"]["table_count"],
                "fact_count": cn_detail["data"]["raw_fact_count"],
                "validation_status": cn_detail["data"]["validation_status"],
                "search_returned": cn_search["data"]["returned"],
                "read_pages_returned": cn_pages["data"]["returned"],
                "sections_returned": cn_sections["data"]["returned"],
                "tables_total": cn_tables["data"]["total"],
                "table_detail_id_matches": (
                    cn_table["data"]["table_id"] == table_id
                ),
                "fact_evidence_relation": (
                    cn_fact["data"]["evidence_id"]
                    == cn_evidence["data"]["evidence_id"]
                ),
                "validation_issue_count": (
                    cn_validation["data"]["issues_total"]
                ),
            },
            "hk": {
                "first_bundle_load_ms": hk_first_bundle_ms,
                "page_count": hk_detail["data"]["page_count"],
                "table_count": hk_detail["data"]["table_count"],
                "fact_count": hk_detail["data"]["raw_fact_count"],
                "validation_status": hk_detail["data"]["validation_status"],
                "validation_issue_count": (
                    hk_validation["data"]["issues_total"]
                ),
            },
            "invalid_document_is_error": bool(invalid.is_error),
            "performance_ms": perf,
        }


def main() -> int:
    args = _args()
    result = asyncio.run(_run(args))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
