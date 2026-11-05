from __future__ import annotations

from pathlib import Path

import pytest

from financial_filing_data_foundation.mcp.research_review_contract import (
    ResearchQualityState,
)
from financial_filing_data_foundation.research.preflight_contract import (
    FilingCoverage,
    FilingCoverageStatus,
    ObservedFiling,
    RepairDisposition,
    RepairQueueItem,
    RequirementAvailability,
    RequirementCriticality,
    ResearchCoverageObservation,
    ResearchPreflightContractError,
    ResearchRequirement,
    build_research_preflight_result,
    build_research_requirement_set,
)


SPEC_HASH = "1" * 64
DOC_A = "a" * 64
DOC_B = "b" * 64


def _requirement(
    requirement_id: str,
    *,
    criticality: RequirementCriticality = RequirementCriticality.CRITICAL,
    allow_partial: bool = False,
    allow_not_disclosed: bool = False,
) -> ResearchRequirement:
    return ResearchRequirement(
        requirement_id=requirement_id,
        source_rule_ref=f"Q-{requirement_id}",
        description=f"Requirement {requirement_id}",
        target_periods=("2025FY", "2026Q3"),
        evidence_strategies=("REPORT_SAFE", "RESOLVED_QUERY"),
        criticality=criticality,
        allow_partial=allow_partial,
        allow_not_disclosed=allow_not_disclosed,
    )


def _filing_coverage() -> FilingCoverage:
    return FilingCoverage(
        status=FilingCoverageStatus.OBSERVED_ONLY,
        observed_filings=(
            ObservedFiling(DOC_B, 2026, "Q3"),
            ObservedFiling(DOC_A, 2025, "ANNUAL"),
        ),
        latest_filing_label="2026Q3",
    )


def test_requirement_set_hash_is_order_independent_and_deterministic() -> None:
    first = build_research_requirement_set(
        SPEC_HASH,
        (_requirement("B"), _requirement("A")),
    )
    second = build_research_requirement_set(
        SPEC_HASH,
        (_requirement("A"), _requirement("B")),
    )

    assert first.requirement_set_hash == second.requirement_set_hash
    assert tuple(item.requirement_id for item in first.requirements) == (
        "A",
        "B",
    )
    assert first.to_dict() == second.to_dict()


def test_duplicate_requirement_id_is_rejected() -> None:
    with pytest.raises(
        ResearchPreflightContractError,
        match="requirement_id values must be unique",
    ) as exc_info:
        build_research_requirement_set(
            SPEC_HASH,
            (_requirement("A"), _requirement("A")),
        )

    assert exc_info.value.reason_code == "RESEARCH_PREFLIGHT_DUPLICATE_REQUIREMENT"


def test_research_ready_can_be_true_when_unrelated_document_needs_review() -> None:
    requirements = build_research_requirement_set(
        SPEC_HASH,
        (_requirement("REV"),),
    )
    result = build_research_preflight_result(
        market="cn",
        ticker="605117",
        research_year_from=2021,
        research_year_to=2026,
        requirement_set=requirements,
        filing_coverage=_filing_coverage(),
        document_quality=(
            # One document is still REVIEW_REQUIRED, but the current critical
            # research requirement is already usable.
            _quality(DOC_A, ResearchQualityState.COMPLETE_BASE),
            _quality(DOC_B, ResearchQualityState.NEEDS_REVIEW),
        ),
        research_coverage=(
            ResearchCoverageObservation(
                "REV",
                RequirementAvailability.AVAILABLE,
            ),
        ),
    )

    assert result.period_monitoring_complete is True
    assert result.research_ready is True
    assert result.database_fully_reviewed is False
    assert result.research_blocker_count == 0


def _quality(
    document_sha256: str,
    state: ResearchQualityState,
):
    from financial_filing_data_foundation.research.preflight_contract import (
        DocumentQualityObservation,
    )

    return DocumentQualityObservation(document_sha256, state)


def test_not_disclosed_can_be_allowed_by_research_rule() -> None:
    requirements = build_research_requirement_set(
        SPEC_HASH,
        (
            _requirement(
                "GUIDANCE",
                allow_not_disclosed=True,
            ),
        ),
    )
    result = build_research_preflight_result(
        market="CN",
        ticker="605117",
        research_year_from=2021,
        research_year_to=2026,
        requirement_set=requirements,
        filing_coverage=FilingCoverage(
            status=FilingCoverageStatus.OBSERVED_ONLY,
            observed_filings=(ObservedFiling(DOC_A, 2026, "Q3"),),
            latest_filing_label="2026Q3",
        ),
        document_quality=(
            _quality(DOC_A, ResearchQualityState.COMPLETE_BASE),
        ),
        research_coverage=(
            ResearchCoverageObservation(
                "GUIDANCE",
                RequirementAvailability.NOT_DISCLOSED,
                note="Latest filing contains no numeric guidance.",
            ),
        ),
    )

    assert result.research_ready is True
    assert result.research_blocker_count == 0


def test_critical_partial_blocks_when_not_allowed() -> None:
    requirements = build_research_requirement_set(
        SPEC_HASH,
        (_requirement("CFO"),),
    )
    result = build_research_preflight_result(
        market="CN",
        ticker="605117",
        research_year_from=2021,
        research_year_to=2026,
        requirement_set=requirements,
        filing_coverage=FilingCoverage(
            status=FilingCoverageStatus.OBSERVED_ONLY,
            observed_filings=(ObservedFiling(DOC_A, 2026, "Q3"),),
            latest_filing_label="2026Q3",
        ),
        document_quality=(
            _quality(DOC_A, ResearchQualityState.COMPLETE_BASE),
        ),
        research_coverage=(
            ResearchCoverageObservation(
                "CFO",
                RequirementAvailability.PARTIAL,
            ),
        ),
    )

    assert result.research_ready is False
    assert result.research_blocker_count == 1


def test_noncritical_gap_does_not_block_research_ready() -> None:
    requirements = build_research_requirement_set(
        SPEC_HASH,
        (
            _requirement(
                "OPTIONAL",
                criticality=RequirementCriticality.NON_CRITICAL,
            ),
        ),
    )
    result = build_research_preflight_result(
        market="CN",
        ticker="605117",
        research_year_from=2021,
        research_year_to=2026,
        requirement_set=requirements,
        filing_coverage=FilingCoverage(
            status=FilingCoverageStatus.OBSERVED_ONLY,
            observed_filings=(ObservedFiling(DOC_A, 2026, "Q3"),),
            latest_filing_label="2026Q3",
        ),
        document_quality=(
            _quality(DOC_A, ResearchQualityState.NEEDS_REVIEW),
        ),
        research_coverage=(
            ResearchCoverageObservation(
                "OPTIONAL",
                RequirementAvailability.AMBIGUOUS,
            ),
        ),
        repair_queue=(
            RepairQueueItem(
                disposition=RepairDisposition.NO_ACTION,
                reason="Unrelated non-critical research gap.",
                document_sha256=DOC_A,
                requirement_id="OPTIONAL",
            ),
        ),
    )

    assert result.research_ready is True
    assert result.database_fully_reviewed is False


def test_monitoring_is_incomplete_when_observed_filing_not_assessed() -> None:
    requirements = build_research_requirement_set(
        SPEC_HASH,
        (_requirement("REV"),),
    )
    result = build_research_preflight_result(
        market="CN",
        ticker="605117",
        research_year_from=2021,
        research_year_to=2026,
        requirement_set=requirements,
        filing_coverage=_filing_coverage(),
        document_quality=(
            _quality(DOC_A, ResearchQualityState.COMPLETE_BASE),
        ),
        research_coverage=(
            ResearchCoverageObservation(
                "REV",
                RequirementAvailability.AVAILABLE,
            ),
        ),
    )

    assert result.period_monitoring_complete is False
    assert result.research_ready is False


def test_preflight_hash_is_deterministic_across_input_order() -> None:
    requirements = build_research_requirement_set(
        SPEC_HASH,
        (_requirement("A"), _requirement("B")),
    )

    kwargs = dict(
        market="CN",
        ticker="605117",
        research_year_from=2021,
        research_year_to=2026,
        requirement_set=requirements,
        filing_coverage=_filing_coverage(),
    )
    first = build_research_preflight_result(
        **kwargs,
        document_quality=(
            _quality(DOC_B, ResearchQualityState.COMPLETE_REVIEWED),
            _quality(DOC_A, ResearchQualityState.COMPLETE_BASE),
        ),
        research_coverage=(
            ResearchCoverageObservation("B", RequirementAvailability.AVAILABLE),
            ResearchCoverageObservation("A", RequirementAvailability.AVAILABLE),
        ),
    )
    second = build_research_preflight_result(
        **kwargs,
        document_quality=(
            _quality(DOC_A, ResearchQualityState.COMPLETE_BASE),
            _quality(DOC_B, ResearchQualityState.COMPLETE_REVIEWED),
        ),
        research_coverage=(
            ResearchCoverageObservation("A", RequirementAvailability.AVAILABLE),
            ResearchCoverageObservation("B", RequirementAvailability.AVAILABLE),
        ),
    )

    assert first.preflight_hash == second.preflight_hash
    assert first.to_dict() == second.to_dict()


def test_coverage_must_match_requirement_set_exactly() -> None:
    requirements = build_research_requirement_set(
        SPEC_HASH,
        (_requirement("A"), _requirement("B")),
    )

    with pytest.raises(
        ResearchPreflightContractError,
        match="exactly one item per requirement",
    ):
        build_research_preflight_result(
            market="CN",
            ticker="605117",
            research_year_from=2021,
            research_year_to=2026,
            requirement_set=requirements,
            filing_coverage=FilingCoverage(
                status=FilingCoverageStatus.OBSERVED_ONLY,
                observed_filings=(ObservedFiling(DOC_A, 2026, "Q3"),),
                latest_filing_label="2026Q3",
            ),
            document_quality=(
                _quality(DOC_A, ResearchQualityState.COMPLETE_BASE),
            ),
            research_coverage=(
                ResearchCoverageObservation(
                    "A",
                    RequirementAvailability.AVAILABLE,
                ),
            ),
        )


def test_contract_module_has_no_mcp_calls_or_mutation_side_effects() -> None:
    source = Path(
        "src/financial_filing_data_foundation/research/preflight_contract.py"
    ).read_text(encoding="utf-8")

    forbidden = (
        "ffdf_render_",
        "submit_resolution(",
        "materialize_resolved_view(",
        "prepare_review_overlay(",
        "SQLiteRegistry(",
    )
    for marker in forbidden:
        assert marker not in source
