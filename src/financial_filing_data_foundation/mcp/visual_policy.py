from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Mapping, Any

from financial_filing_data_foundation.mcp.research_review_contract import (
    ResearchQualityState,
)


VISUAL_POLICY_VERSION = "research-visual-trigger-v1"


class StructuredAssessment(StrEnum):
    SUFFICIENT = "SUFFICIENT"
    INSUFFICIENT = "INSUFFICIENT"
    CONFLICT = "CONFLICT"
    MISSING_LAYOUT_CONTEXT = "MISSING_LAYOUT_CONTEXT"
    MISSING_SOURCE = "MISSING_SOURCE"


class VisualRoute(StrEnum):
    NO_VISUAL = "NO_VISUAL"
    VISUAL_REQUIRED = "VISUAL_REQUIRED"
    UPSTREAM_FIX = "UPSTREAM_FIX"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class VisualTriggerDecision:
    policy_version: str
    visual_required: bool
    route: VisualRoute
    reason: str

    def to_dict(self) -> dict[str, object]:
        return {
            "policy_version": self.policy_version,
            "visual_required": self.visual_required,
            "route": self.route.value,
            "reason": self.reason,
        }


def evaluate_visual_trigger(
    *,
    quality_state: ResearchQualityState | str,
    structured_assessment: StructuredAssessment | str,
    target_related: bool,
    trusted_source_available: bool,
    upstream_fix_required: bool = False,
) -> VisualTriggerDecision:
    state = (
        quality_state
        if isinstance(quality_state, ResearchQualityState)
        else ResearchQualityState(str(quality_state))
    )
    assessment = (
        structured_assessment
        if isinstance(structured_assessment, StructuredAssessment)
        else StructuredAssessment(str(structured_assessment))
    )

    if upstream_fix_required or state is ResearchQualityState.NEEDS_UPSTREAM_FIX:
        return VisualTriggerDecision(
            VISUAL_POLICY_VERSION,
            False,
            VisualRoute.UPSTREAM_FIX,
            "Current issue requires upstream parser/extraction repair rather than visual-only review.",
        )

    if state in {
        ResearchQualityState.BLOCKED,
        ResearchQualityState.INVALID_REVIEW_STATE,
    }:
        return VisualTriggerDecision(
            VISUAL_POLICY_VERSION,
            False,
            VisualRoute.BLOCKED,
            "Document/review state is blocked or invalid; visual review must not bypass the blocker.",
        )

    if not target_related:
        return VisualTriggerDecision(
            VISUAL_POLICY_VERSION,
            False,
            VisualRoute.NO_VISUAL,
            "The unresolved condition is not related to the current research target.",
        )

    if assessment is StructuredAssessment.SUFFICIENT:
        return VisualTriggerDecision(
            VISUAL_POLICY_VERSION,
            False,
            VisualRoute.NO_VISUAL,
            "Structured P3/P5/P6/P9 evidence is sufficient.",
        )

    if assessment is StructuredAssessment.MISSING_SOURCE:
        return VisualTriggerDecision(
            VISUAL_POLICY_VERSION,
            False,
            VisualRoute.BLOCKED,
            "No trusted original PDF source is available for visual review.",
        )

    if not trusted_source_available:
        return VisualTriggerDecision(
            VISUAL_POLICY_VERSION,
            False,
            VisualRoute.BLOCKED,
            "Trusted original PDF source is unavailable.",
        )

    return VisualTriggerDecision(
        VISUAL_POLICY_VERSION,
        True,
        VisualRoute.VISUAL_REQUIRED,
        (
            "Target-related structured evidence is insufficient/conflicting "
            "or lacks required layout context; render only the recommended "
            "table/page scope."
        ),
    )
