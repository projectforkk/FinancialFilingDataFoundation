from __future__ import annotations

import ast
from pathlib import Path

import financial_filing_data_foundation.mcp as mcp_package


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
)


def _source_path() -> Path:
    return Path(mcp_package.__file__).resolve().parent / "server.py"


def _tree() -> ast.Module:
    return ast.parse(_source_path().read_text(encoding="utf-8"))


def _literal_tuple_assignment(name: str) -> tuple[str, ...]:
    for node in _tree().body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            continue
        value = ast.literal_eval(node.value)
        return tuple(value)
    raise AssertionError(f"missing assignment: {name}")


def test_tool_name_constant_is_exact_and_read_only() -> None:
    names = _literal_tuple_assignment("TOOL_NAMES")
    assert names == EXPECTED_TOOLS
    forbidden_fragments = (
        "shell",
        "exec",
        "python",
        "sql",
        "write",
        "delete",
        "upload",
        "http",
        "network",
    )
    assert not any(
        fragment in tool_name.lower()
        for tool_name in names
        for fragment in forbidden_fragments
    )


def test_server_source_registers_exact_static_tool_names() -> None:
    names: list[str] = []
    for node in ast.walk(_tree()):
        if not isinstance(node, ast.FunctionDef):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            func = decorator.func
            if not (
                isinstance(func, ast.Attribute)
                and func.attr == "tool"
                and isinstance(func.value, ast.Name)
                and func.value.id == "server"
            ):
                continue
            for keyword in decorator.keywords:
                if (
                    keyword.arg == "name"
                    and isinstance(keyword.value, ast.Constant)
                    and isinstance(keyword.value.value, str)
                ):
                    names.append(keyword.value.value)
    assert tuple(names) == EXPECTED_TOOLS


def test_server_transport_is_stdio_only_and_no_http_listener_call() -> None:
    source = _source_path().read_text(encoding="utf-8")
    assert 'server.run("stdio")' in source
    assert ".run_sse_async(" not in source
    assert ".run_streamable_http_async(" not in source


def test_server_has_no_network_ai_or_process_execution_imports() -> None:
    imported: list[str] = []
    for node in ast.walk(_tree()):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")
    forbidden_prefixes = (
        "httpx",
        "requests",
        "urllib",
        "socket",
        "subprocess",
        "openai",
        "anthropic",
        "google.generativeai",
    )
    assert not any(
        imported_name == prefix or imported_name.startswith(prefix + ".")
        for imported_name in imported
        for prefix in forbidden_prefixes
    )
