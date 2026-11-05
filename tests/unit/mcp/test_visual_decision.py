from __future__ import annotations

from financial_filing_data_foundation.mcp.visual_decision import (
    ReviewerFinding,
    VisualDecisionClass,
    classify_visual_decision,
)


def test_anchorable_semantic_decision_can_be_durable_candidate():
    decision = classify_visual_decision(
        finding=ReviewerFinding.EXPLICIT_SEMANTIC,
        has_authoritative_p5_p6_anchor=True,
        p9_action_supported=True,
    )
    assert decision.decision_class is VisualDecisionClass.EXPLICIT_AND_ANCHORABLE
    assert decision.durable_p9_candidate is True


def test_explicit_without_anchor_is_run_local_only():
    decision = classify_visual_decision(
        finding=ReviewerFinding.EXPLICIT_SEMANTIC,
        has_authoritative_p5_p6_anchor=False,
        p9_action_supported=True,
    )
    assert decision.decision_class is VisualDecisionClass.EXPLICIT_VISUAL_ONLY
    assert decision.run_local_usable is True
    assert decision.durable_p9_candidate is False


def test_raw_value_mismatch_routes_parser_fix_not_p9():
    decision = classify_visual_decision(
        finding=ReviewerFinding.RAW_VALUE_MISMATCH,
        has_authoritative_p5_p6_anchor=True,
        p9_action_supported=True,
    )
    assert decision.decision_class is VisualDecisionClass.RAW_EXTRACTION_DEFECT
    assert decision.upstream_fix_required is True
    assert decision.durable_p9_candidate is False


def test_missing_fact_is_run_local_and_upstream_candidate():
    decision = classify_visual_decision(
        finding=ReviewerFinding.EXPLICIT_MISSING_FACT,
        has_authoritative_p5_p6_anchor=False,
        p9_action_supported=False,
    )
    assert decision.decision_class is VisualDecisionClass.EXPLICIT_VISUAL_ONLY
    assert decision.upstream_reason == "P6_MISSING_FACT_CANDIDATE"
    assert decision.durable_p9_candidate is False


def test_ambiguous_stays_unresolved():
    decision = classify_visual_decision(
        finding=ReviewerFinding.AMBIGUOUS,
        has_authoritative_p5_p6_anchor=False,
        p9_action_supported=False,
    )
    assert decision.decision_class is VisualDecisionClass.AMBIGUOUS
    assert decision.unresolved is True
