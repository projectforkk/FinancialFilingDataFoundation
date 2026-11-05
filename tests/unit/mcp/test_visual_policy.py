from __future__ import annotations

from financial_filing_data_foundation.mcp.research_review_contract import (
    ResearchQualityState,
)
from financial_filing_data_foundation.mcp.visual_policy import (
    StructuredAssessment,
    VisualRoute,
    evaluate_visual_trigger,
)


def test_complete_or_review_required_does_not_force_visual_when_structured_sufficient():
    decision = evaluate_visual_trigger(
        quality_state=ResearchQualityState.NEEDS_REVIEW,
        structured_assessment=StructuredAssessment.SUFFICIENT,
        target_related=True,
        trusted_source_available=True,
    )
    assert decision.visual_required is False
    assert decision.route is VisualRoute.NO_VISUAL


def test_unrelated_issue_does_not_trigger_visual():
    decision = evaluate_visual_trigger(
        quality_state=ResearchQualityState.NEEDS_REVIEW,
        structured_assessment=StructuredAssessment.CONFLICT,
        target_related=False,
        trusted_source_available=True,
    )
    assert decision.visual_required is False


def test_target_related_layout_gap_triggers_visual():
    decision = evaluate_visual_trigger(
        quality_state=ResearchQualityState.NEEDS_REVIEW,
        structured_assessment=StructuredAssessment.MISSING_LAYOUT_CONTEXT,
        target_related=True,
        trusted_source_available=True,
    )
    assert decision.visual_required is True
    assert decision.route is VisualRoute.VISUAL_REQUIRED


def test_upstream_fix_beats_visual():
    decision = evaluate_visual_trigger(
        quality_state=ResearchQualityState.NEEDS_UPSTREAM_FIX,
        structured_assessment=StructuredAssessment.CONFLICT,
        target_related=True,
        trusted_source_available=True,
    )
    assert decision.visual_required is False
    assert decision.route is VisualRoute.UPSTREAM_FIX


def test_invalid_review_state_is_blocked():
    decision = evaluate_visual_trigger(
        quality_state=ResearchQualityState.INVALID_REVIEW_STATE,
        structured_assessment=StructuredAssessment.INSUFFICIENT,
        target_related=True,
        trusted_source_available=True,
    )
    assert decision.route is VisualRoute.BLOCKED


def test_missing_trusted_source_is_blocked():
    decision = evaluate_visual_trigger(
        quality_state=ResearchQualityState.NEEDS_REVIEW,
        structured_assessment=StructuredAssessment.INSUFFICIENT,
        target_related=True,
        trusted_source_available=False,
    )
    assert decision.visual_required is False
    assert decision.route is VisualRoute.BLOCKED
