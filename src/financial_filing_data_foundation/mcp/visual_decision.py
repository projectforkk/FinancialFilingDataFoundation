from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final


VISUAL_DECISION_POLICY_VERSION: Final = "research-visual-decision-v1"


class ReviewerFinding(StrEnum):
    EXPLICIT_SEMANTIC = "EXPLICIT_SEMANTIC"
    EXPLICIT_MISSING_FACT = "EXPLICIT_MISSING_FACT"
    RAW_VALUE_MISMATCH = "RAW_VALUE_MISMATCH"
    AMBIGUOUS = "AMBIGUOUS"


class VisualDecisionClass(StrEnum):
    EXPLICIT_AND_ANCHORABLE = "EXPLICIT_AND_ANCHORABLE"
    EXPLICIT_VISUAL_ONLY = "EXPLICIT_VISUAL_ONLY"
    RAW_EXTRACTION_DEFECT = "RAW_EXTRACTION_DEFECT"
    AMBIGUOUS = "AMBIGUOUS"


@dataclass(frozen=True, slots=True)
class VisualDecision:
    policy_version: str
    decision_class: VisualDecisionClass
    run_local_usable: bool
    durable_p9_candidate: bool
    upstream_fix_required: bool
    unresolved: bool
    upstream_reason: str | None
    explanation: str

    def to_dict(self) -> dict[str, object]:
        return {
            "policy_version": self.policy_version,
            "decision_class": self.decision_class.value,
            "run_local_usable": self.run_local_usable,
            "durable_p9_candidate": self.durable_p9_candidate,
            "upstream_fix_required": self.upstream_fix_required,
            "unresolved": self.unresolved,
            "upstream_reason": self.upstream_reason,
            "explanation": self.explanation,
        }


def classify_visual_decision(
    *,
    finding: ReviewerFinding | str,
    has_authoritative_p5_p6_anchor: bool,
    p9_action_supported: bool,
) -> VisualDecision:
    normalized = (
        finding if isinstance(finding, ReviewerFinding) else ReviewerFinding(str(finding))
    )

    if normalized is ReviewerFinding.RAW_VALUE_MISMATCH:
        return VisualDecision(
            VISUAL_DECISION_POLICY_VERSION,
            VisualDecisionClass.RAW_EXTRACTION_DEFECT,
            False,
            False,
            True,
            False,
            "RAW_EXTRACTION_DEFECT",
            (
                "Original PDF contradicts the extracted raw numeric value. "
                "P9 must not SET_VALUE; repair parser/extraction and re-run "
                "affected stages."
            ),
        )

    if normalized is ReviewerFinding.EXPLICIT_MISSING_FACT:
        return VisualDecision(
            VISUAL_DECISION_POLICY_VERSION,
            VisualDecisionClass.EXPLICIT_VISUAL_ONLY,
            True,
            False,
            True,
            False,
            "P6_MISSING_FACT_CANDIDATE",
            (
                "PDF disclosure is explicit but P6 has no authoritative RawFact "
                "target. It may be used for the current research run with VisualRef "
                "provenance, while durable repair belongs upstream."
            ),
        )

    if normalized is ReviewerFinding.AMBIGUOUS:
        return VisualDecision(
            VISUAL_DECISION_POLICY_VERSION,
            VisualDecisionClass.AMBIGUOUS,
            False,
            False,
            False,
            True,
            None,
            "Visual evidence still does not support one unique interpretation.",
        )

    if has_authoritative_p5_p6_anchor and p9_action_supported:
        return VisualDecision(
            VISUAL_DECISION_POLICY_VERSION,
            VisualDecisionClass.EXPLICIT_AND_ANCHORABLE,
            True,
            True,
            False,
            False,
            None,
            (
                "Visual review confirms an explicit semantic interpretation and "
                "an existing authoritative P5/P6 anchor plus P9 v1 action can "
                "represent the correction."
            ),
        )

    return VisualDecision(
        VISUAL_DECISION_POLICY_VERSION,
        VisualDecisionClass.EXPLICIT_VISUAL_ONLY,
        True,
        False,
        False,
        False,
        None,
        (
            "Visual evidence is explicit for the current run, but durable P9 "
            "write-through is not legal because an authoritative anchor or "
            "supported P9 action is absent."
        ),
    )
