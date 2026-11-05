from __future__ import annotations

import ast
from pathlib import Path

from financial_filing_data_foundation.mcp.research_review_contract import (
    CURRENT_PRODUCTION_TOOL_NAMES,
    P8_RAW_V1_TOOL_NAMES,
    REPORT_SAFE_V1_TOOL_NAMES,
    RESEARCH_REVIEW_ERROR_CODES,
    RESEARCH_REVIEW_V1_READ_TOOL_NAMES,
    RESEARCH_REVIEW_V1_TOOL_NAMES,
    RESEARCH_REVIEW_V1_WRITE_TOOL_NAMES,
    RESEARCH_REVIEW_CONTRACT_VERSION,
    ResearchQualityState,
    ResearchReviewProfile,
    get_research_review_contract,
    write_tools_enabled,
)
from financial_filing_data_foundation.research.context import P8_TOOL_NAMES_V1


SERVER = Path("src/financial_filing_data_foundation/mcp/server.py")


def _server_tool_names() -> tuple[str, ...]:
    tree = ast.parse(SERVER.read_text(encoding="utf-8"))
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "TOOL_NAMES"
        ):
            value = ast.literal_eval(node.value)
            return tuple(value)
    raise AssertionError("TOOL_NAMES not found")


def test_contract_version_and_groups_are_frozen() -> None:
    assert RESEARCH_REVIEW_CONTRACT_VERSION == "research-review-mcp-v1"
    assert len(P8_RAW_V1_TOOL_NAMES) == 11
    assert len(REPORT_SAFE_V1_TOOL_NAMES) == 3
    assert len(RESEARCH_REVIEW_V1_READ_TOOL_NAMES) == 9
    assert len(RESEARCH_REVIEW_V1_WRITE_TOOL_NAMES) == 3
    assert len(RESEARCH_REVIEW_V1_TOOL_NAMES) == 12


def test_p8_logical_contract_matches_accepted_p10_contract() -> None:
    assert P8_RAW_V1_TOOL_NAMES == P8_TOOL_NAMES_V1


def test_current_production_surface_is_p8_plus_report_safe_only() -> None:
    assert CURRENT_PRODUCTION_TOOL_NAMES == _server_tool_names()
    assert len(CURRENT_PRODUCTION_TOOL_NAMES) == 14
    assert not set(RESEARCH_REVIEW_V1_TOOL_NAMES) & set(
        CURRENT_PRODUCTION_TOOL_NAMES
    )


def test_future_research_review_tool_names_are_unique_and_partitioned() -> None:
    assert set(RESEARCH_REVIEW_V1_READ_TOOL_NAMES).isdisjoint(
        RESEARCH_REVIEW_V1_WRITE_TOOL_NAMES
    )
    assert len(set(RESEARCH_REVIEW_V1_TOOL_NAMES)) == 12
    assert all(name.startswith("ffdf_") for name in RESEARCH_REVIEW_V1_TOOL_NAMES)


def test_write_permission_is_profile_gated() -> None:
    assert not write_tools_enabled(ResearchReviewProfile.RESEARCH_FALLBACK)
    assert write_tools_enabled(ResearchReviewProfile.QUALITY_REVIEW)
    assert not write_tools_enabled("UNKNOWN_PROFILE")


def test_quality_state_enum_is_exact() -> None:
    assert tuple(item.value for item in ResearchQualityState) == (
        "COMPLETE_BASE",
        "COMPLETE_REVIEWED",
        "NEEDS_REVIEW",
        "NEEDS_MATERIALIZATION",
        "NEEDS_UPSTREAM_FIX",
        "BLOCKED",
        "INVALID_REVIEW_STATE",
    )


def test_error_codes_are_unique_and_namespaced() -> None:
    assert len(RESEARCH_REVIEW_ERROR_CODES) == len(
        set(RESEARCH_REVIEW_ERROR_CODES)
    )
    assert all(
        code.startswith("RESEARCH_MCP_") for code in RESEARCH_REVIEW_ERROR_CODES
    )


def test_manifest_is_deterministic_and_contains_no_runtime_mutation() -> None:
    first = get_research_review_contract().to_dict()
    second = get_research_review_contract().to_dict()
    assert first == second
    assert first["version"] == "research-review-mcp-v1"
    groups = first["capability_groups"]
    assert groups["P8_RAW_V1"] == list(P8_RAW_V1_TOOL_NAMES)
    assert groups["REPORT_SAFE_V1"] == list(REPORT_SAFE_V1_TOOL_NAMES)
    assert groups["RESEARCH_REVIEW_V1"]["write"] == list(
        RESEARCH_REVIEW_V1_WRITE_TOOL_NAMES
    )
