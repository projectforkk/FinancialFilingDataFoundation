from __future__ import annotations

import ast
from pathlib import Path

SERVER = Path(
    "src/financial_filing_data_foundation/mcp/server.py"
)


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


def test_server_declares_exact_read_only_tool_names() -> None:
    source = SERVER.read_text(encoding="utf-8")
    tree = ast.parse(source)

    values = {}
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "TOOL_NAMES"
        ):
            values = ast.literal_eval(node.value)
            break

    assert tuple(values) == EXPECTED_TOOLS
    assert len(set(values)) == 26


def test_server_exposes_stdio_only_and_no_arbitrary_tools() -> None:
    source = SERVER.read_text(encoding="utf-8")

    assert 'server.run("stdio")' in source
    assert "streamable-http" not in source
    assert 'server.run("sse")' not in source
    assert 'server.run("streamable-http")' not in source

    forbidden_tool_names = (
        "read_file",
        "list_directory",
        "sqlite_query",
        "execute_python",
        "run_command",
        "shell",
        "download_document",
        "parse_document",
        "submit_resolution",
    )
    for name in forbidden_tool_names:
        assert f'name="{name}"' not in source


def test_service_has_no_network_ai_or_subprocess_imports() -> None:
    source = Path(
        "src/financial_filing_data_foundation/mcp/service.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)

    forbidden_prefixes = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "openai",
        "anthropic",
        "dayu",
        "docling",
        "torch",
    )
    assert not any(
        name == prefix or name.startswith(prefix + ".")
        for name in imported
        for prefix in forbidden_prefixes
    )


def test_package_initializer_does_not_import_external_mcp_sdk() -> None:
    source = Path(
        "src/financial_filing_data_foundation/mcp/__init__.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")

    assert "mcp" not in imports
    assert not any(name.startswith("mcp.") for name in imports)
