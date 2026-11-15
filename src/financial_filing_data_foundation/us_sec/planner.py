from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .errors import P11Reason


class SecPlanAction(StrEnum):
    REUSE_DATA = "REUSE_DATA"
    REVALIDATE_LOCAL = "REVALIDATE_LOCAL"
    PARSE_LOCAL = "PARSE_LOCAL"
    DISCOVER_AND_ACQUIRE = "DISCOVER_AND_ACQUIRE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


@dataclass(frozen=True, slots=True)
class SecPlan:
    action: SecPlanAction
    reason_code: str | None = None


def plan_sec_slot(
    *,
    parsed_available: bool,
    package_available: bool,
    validation_reuse_eligible: bool,
    amendment_conflict: bool = False,
) -> SecPlan:
    if amendment_conflict:
        return SecPlan(SecPlanAction.REVIEW_REQUIRED, P11Reason.P11_AMENDED_VARIANT_PRESENT.value)
    if parsed_available:
        if validation_reuse_eligible:
            return SecPlan(SecPlanAction.REUSE_DATA)
        return SecPlan(SecPlanAction.REVALIDATE_LOCAL)
    if package_available:
        return SecPlan(SecPlanAction.PARSE_LOCAL)
    return SecPlan(SecPlanAction.DISCOVER_AND_ACQUIRE)


__all__ = ["SecPlan", "SecPlanAction", "plan_sec_slot"]
