from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final


RESEARCH_REVIEW_CONTRACT_VERSION: Final = "research-review-mcp-v1"


class CapabilityGroup(StrEnum):
    P8_RAW_V1 = "P8_RAW_V1"
    REPORT_SAFE_V1 = "REPORT_SAFE_V1"
    RESEARCH_REVIEW_V1 = "RESEARCH_REVIEW_V1"


P8_RAW_V1_TOOL_NAMES: Final = (
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

REPORT_SAFE_V1_TOOL_NAMES: Final = (
    "ffdf_get_company_report_context",
    "ffdf_search_company",
    "ffdf_find_table_rows",
)

RESEARCH_REVIEW_V1_READ_TOOL_NAMES: Final = (
    "ffdf_get_review_state",
    "ffdf_get_resolved_fact",
    "ffdf_list_resolved_facts",
    "ffdf_list_review_tasks",
    "ffdf_get_review_context",
    "ffdf_locate_evidence",
    "ffdf_render_table",
    "ffdf_render_table_group",
    "ffdf_render_page",
)

RESEARCH_REVIEW_V1_WRITE_TOOL_NAMES: Final = (
    "ffdf_prepare_review_overlay",
    "ffdf_submit_review_resolution",
    "ffdf_materialize_resolved_view",
)

RESEARCH_REVIEW_V1_TOOL_NAMES: Final = (
    RESEARCH_REVIEW_V1_READ_TOOL_NAMES
    + RESEARCH_REVIEW_V1_WRITE_TOOL_NAMES
)

CURRENT_PRODUCTION_TOOL_NAMES: Final = (
    P8_RAW_V1_TOOL_NAMES + REPORT_SAFE_V1_TOOL_NAMES
)


class ResearchReviewProfile(StrEnum):
    RESEARCH_FALLBACK = "RESEARCH_FALLBACK"
    QUALITY_REVIEW = "QUALITY_REVIEW"


class ResearchQualityState(StrEnum):
    COMPLETE_BASE = "COMPLETE_BASE"
    COMPLETE_REVIEWED = "COMPLETE_REVIEWED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    NEEDS_MATERIALIZATION = "NEEDS_MATERIALIZATION"
    NEEDS_UPSTREAM_FIX = "NEEDS_UPSTREAM_FIX"
    BLOCKED = "BLOCKED"
    INVALID_REVIEW_STATE = "INVALID_REVIEW_STATE"


RESEARCH_REVIEW_ERROR_CODES: Final = (
    "RESEARCH_MCP_WRITE_DISABLED",
    "RESEARCH_MCP_DOCUMENT_NOT_FOUND",
    "RESEARCH_MCP_FACT_NOT_FOUND",
    "RESEARCH_MCP_REVIEW_TASK_NOT_FOUND",
    "RESEARCH_MCP_ISSUE_NOT_FOUND",
    "RESEARCH_MCP_TABLE_NOT_FOUND",
    "RESEARCH_MCP_TABLE_GROUP_NOT_FOUND",
    "RESEARCH_MCP_PAGE_INVALID",
    "RESEARCH_MCP_VISUAL_SOURCE_UNTRUSTED",
    "RESEARCH_MCP_VISUAL_SOURCE_INVALID",
    "RESEARCH_MCP_RENDER_FAILED",
    "RESEARCH_MCP_PAYLOAD_LIMIT",
    "RESEARCH_MCP_REVIEW_STATE_CHANGED",
    "RESEARCH_MCP_REVIEW_STATE_INVALID",
    "RESEARCH_MCP_RESOLVED_STORE_INVALID",
    "RESEARCH_MCP_LOCATOR_NO_MATCH",
    "RESEARCH_MCP_UPSTREAM_FIX_REQUIRED",
)


@dataclass(frozen=True, slots=True)
class ResearchReviewContract:
    version: str
    p8_raw_tools: tuple[str, ...]
    report_safe_tools: tuple[str, ...]
    research_review_read_tools: tuple[str, ...]
    research_review_write_tools: tuple[str, ...]
    profiles: tuple[str, ...]
    quality_states: tuple[str, ...]
    error_codes: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "capability_groups": {
                CapabilityGroup.P8_RAW_V1.value: list(self.p8_raw_tools),
                CapabilityGroup.REPORT_SAFE_V1.value: list(self.report_safe_tools),
                CapabilityGroup.RESEARCH_REVIEW_V1.value: {
                    "read": list(self.research_review_read_tools),
                    "write": list(self.research_review_write_tools),
                },
            },
            "profiles": list(self.profiles),
            "quality_states": list(self.quality_states),
            "error_codes": list(self.error_codes),
        }


def get_research_review_contract() -> ResearchReviewContract:
    return ResearchReviewContract(
        version=RESEARCH_REVIEW_CONTRACT_VERSION,
        p8_raw_tools=P8_RAW_V1_TOOL_NAMES,
        report_safe_tools=REPORT_SAFE_V1_TOOL_NAMES,
        research_review_read_tools=RESEARCH_REVIEW_V1_READ_TOOL_NAMES,
        research_review_write_tools=RESEARCH_REVIEW_V1_WRITE_TOOL_NAMES,
        profiles=tuple(item.value for item in ResearchReviewProfile),
        quality_states=tuple(item.value for item in ResearchQualityState),
        error_codes=RESEARCH_REVIEW_ERROR_CODES,
    )


def write_tools_enabled(profile: ResearchReviewProfile | str) -> bool:
    try:
        normalized = (
            profile
            if isinstance(profile, ResearchReviewProfile)
            else ResearchReviewProfile(str(profile))
        )
    except ValueError:
        return False
    return normalized is ResearchReviewProfile.QUALITY_REVIEW
