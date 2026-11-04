from __future__ import annotations

from financial_filing_data_foundation.identity import (
    CompanyRef,
    FilingPolicy,
    FilingSlotKey,
    build_required_slots,
)
from financial_filing_data_foundation.planner.errors import PackageAwarePlannerRequired
from financial_filing_data_foundation.planner.models import (
    FilingPlan,
    PlannerAction,
    PlannerItem,
    ReasonCode,
    PlannerReusePolicy,
)
from financial_filing_data_foundation.registry import (
    CompatibilityStatus,
    LocalDocumentStatus,
    ParsedDataRecord,
    SQLiteRegistry,
    ValidationStatus,
)


def _record_rejection_reasons(
    record: ParsedDataRecord,
    policy: PlannerReusePolicy,
) -> tuple[ReasonCode, ...]:
    reasons: list[ReasonCode] = []
    if record.validation_status != ValidationStatus.PASS:
        reasons.append(ReasonCode.PARSED_VALIDATION_NOT_PASS)
    if record.blocking_issue_count > 0:
        reasons.append(ReasonCode.PARSED_BLOCKING_ISSUES)
    if record.compatibility_status == CompatibilityStatus.INCOMPATIBLE:
        reasons.append(ReasonCode.PARSED_SCHEMA_INCOMPATIBLE)
    elif record.compatibility_status == CompatibilityStatus.UNKNOWN:
        reasons.append(ReasonCode.PARSED_COMPATIBILITY_UNKNOWN)
    if record.schema_version not in policy.accepted_schema_versions:
        if ReasonCode.PARSED_SCHEMA_INCOMPATIBLE not in reasons:
            reasons.append(ReasonCode.PARSED_SCHEMA_INCOMPATIBLE)
    if record.parser_version in policy.invalidated_parser_versions:
        reasons.append(ReasonCode.PARSER_DEFECT_INVALIDATED)
    return tuple(reasons)


def _ordered_unique_reason_codes(
    reasons: list[ReasonCode],
) -> tuple[ReasonCode, ...]:
    seen: set[ReasonCode] = set()
    ordered: list[ReasonCode] = []
    for reason in reasons:
        if reason not in seen:
            seen.add(reason)
            ordered.append(reason)
    return tuple(ordered)


class IncrementalPlanner:
    def __init__(
        self, registry: SQLiteRegistry, reuse_policy: PlannerReusePolicy
    ) -> None:
        self.registry = registry
        self.reuse_policy = reuse_policy

    def build_plan(
        self,
        company: CompanyRef,
        start_year: int,
        end_year: int,
        policy: FilingPolicy,
    ) -> FilingPlan:
        if company.market == "US":
            raise PackageAwarePlannerRequired(
                "market US requires P11 package-aware SEC planning"
            )
        slots = build_required_slots(company, start_year, end_year, policy)
        items = tuple(self._plan_slot(company, slot) for slot in slots)
        return FilingPlan(
            company=company,
            start_year=start_year,
            end_year=end_year,
            items=items,
        )

    def _plan_slot(
        self,
        company: CompanyRef,
        slot: FilingSlotKey,
    ) -> PlannerItem:
        local = self.registry.resolve_local_document(slot)
        parsed = self.registry.list_parsed_data(slot)

        if local.status == LocalDocumentStatus.DRIFTED:
            return PlannerItem(
                slot=slot,
                ticker=company.ticker,
                action=PlannerAction.BLOCKED,
                reason_code=ReasonCode.LOCAL_CONTENT_DRIFT,
                blocking_reasons=(ReasonCode.LOCAL_CONTENT_DRIFT,),
            )

        if local.status == LocalDocumentStatus.CONFLICT:
            return PlannerItem(
                slot=slot,
                ticker=company.ticker,
                action=PlannerAction.BLOCKED,
                reason_code=ReasonCode.LOCAL_BINDING_CONFLICT,
                blocking_reasons=(ReasonCode.LOCAL_BINDING_CONFLICT,),
            )

        if local.status == LocalDocumentStatus.AMBIGUOUS:
            return PlannerItem(
                slot=slot,
                ticker=company.ticker,
                action=PlannerAction.REVIEW_REQUIRED,
                reason_code=ReasonCode.LOCAL_DOCUMENT_AMBIGUOUS,
                blocking_reasons=(ReasonCode.LOCAL_DOCUMENT_AMBIGUOUS,),
            )

        reusable: list[ParsedDataRecord] = []
        rejected_reasons: list[ReasonCode] = []
        valid_other_sha_exists = False

        for record in parsed:
            reasons = _record_rejection_reasons(record, self.reuse_policy)
            if reasons:
                rejected_reasons.extend(reasons)
                continue

            if (
                local.status == LocalDocumentStatus.RESOLVED
                and local.document_sha256 is not None
                and record.document_sha256 != local.document_sha256
            ):
                valid_other_sha_exists = True
                rejected_reasons.append(ReasonCode.SOURCE_MATERIAL_CHANGE)
                continue

            reusable.append(record)

        if reusable:
            reusable_shas = {record.document_sha256 for record in reusable}
            if (
                local.status != LocalDocumentStatus.RESOLVED
                and len(reusable_shas) > 1
            ):
                return PlannerItem(
                    slot=slot,
                    ticker=company.ticker,
                    action=PlannerAction.REVIEW_REQUIRED,
                    reason_code=ReasonCode.MULTIPLE_REUSABLE_DOCUMENTS_AMBIGUOUS,
                    blocking_reasons=(
                        ReasonCode.MULTIPLE_REUSABLE_DOCUMENTS_AMBIGUOUS,
                    ),
                )

            # list_parsed_data() is ordered by (document_sha256, parse_run_id),
            # so multiple reusable runs for one SHA choose deterministically.
            selected = reusable[0]
            return PlannerItem(
                slot=slot,
                ticker=company.ticker,
                action=PlannerAction.REUSE_DATA,
                reason_code=ReasonCode.VALIDATED_COMPATIBLE_PARSED_DATA,
                document_sha256=selected.document_sha256,
                local_path=(
                    local.canonical_path
                    if local.status == LocalDocumentStatus.RESOLVED
                    else None
                ),
                parse_run_id=selected.parse_run_id,
            )

        if local.status == LocalDocumentStatus.RESOLVED:
            reason = (
                ReasonCode.SOURCE_MATERIAL_CHANGE
                if valid_other_sha_exists
                else ReasonCode.LOCAL_RAW_AVAILABLE
            )
            return PlannerItem(
                slot=slot,
                ticker=company.ticker,
                action=PlannerAction.PARSE_LOCAL,
                reason_code=reason,
                document_sha256=local.document_sha256,
                local_path=local.canonical_path,
                blocking_reasons=_ordered_unique_reason_codes(rejected_reasons),
            )

        return PlannerItem(
            slot=slot,
            ticker=company.ticker,
            action=PlannerAction.DOWNLOAD_AND_PARSE,
            reason_code=ReasonCode.NO_REUSABLE_DATA_OR_LOCAL_RAW,
            blocking_reasons=_ordered_unique_reason_codes(rejected_reasons),
        )
