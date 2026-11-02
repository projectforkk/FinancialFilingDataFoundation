from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from financial_filing_data_foundation.identity import CompanyRef, FilingSlotKey


class PlannerAction(StrEnum):
    REUSE_DATA = "REUSE_DATA"
    PARSE_LOCAL = "PARSE_LOCAL"
    DOWNLOAD_AND_PARSE = "DOWNLOAD_AND_PARSE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    BLOCKED = "BLOCKED"


class ReasonCode(StrEnum):
    VALIDATED_COMPATIBLE_PARSED_DATA = "VALIDATED_COMPATIBLE_PARSED_DATA"
    MULTIPLE_REUSABLE_DOCUMENTS_AMBIGUOUS = "MULTIPLE_REUSABLE_DOCUMENTS_AMBIGUOUS"
    LOCAL_RAW_AVAILABLE = "LOCAL_RAW_AVAILABLE"
    NO_REUSABLE_DATA_OR_LOCAL_RAW = "NO_REUSABLE_DATA_OR_LOCAL_RAW"
    PARSED_VALIDATION_NOT_PASS = "PARSED_VALIDATION_NOT_PASS"
    PARSED_BLOCKING_ISSUES = "PARSED_BLOCKING_ISSUES"
    PARSED_SCHEMA_INCOMPATIBLE = "PARSED_SCHEMA_INCOMPATIBLE"
    PARSED_COMPATIBILITY_UNKNOWN = "PARSED_COMPATIBILITY_UNKNOWN"
    PARSER_DEFECT_INVALIDATED = "PARSER_DEFECT_INVALIDATED"
    SOURCE_MATERIAL_CHANGE = "SOURCE_MATERIAL_CHANGE"
    LOCAL_DOCUMENT_AMBIGUOUS = "LOCAL_DOCUMENT_AMBIGUOUS"
    LOCAL_BINDING_CONFLICT = "LOCAL_BINDING_CONFLICT"
    REGISTRY_SCHEMA_UNSUPPORTED = "REGISTRY_SCHEMA_UNSUPPORTED"


@dataclass(frozen=True, slots=True)
class PlannerReusePolicy:
    accepted_schema_versions: frozenset[str]
    invalidated_parser_versions: frozenset[str] = frozenset()


@dataclass(frozen=True, slots=True)
class PlannerItem:
    slot: FilingSlotKey
    ticker: str
    action: PlannerAction
    reason_code: ReasonCode
    document_sha256: str | None = None
    local_path: Path | None = None
    parse_run_id: str | None = None
    blocking_reasons: tuple[ReasonCode, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "slot_key": self.slot.serialize(),
            "market": self.slot.market,
            "company_id": self.slot.company_id,
            "ticker": self.ticker,
            "filing_type": self.slot.filing_type,
            "fiscal_year": self.slot.fiscal_year,
            "raw_fiscal_period": self.slot.raw_fiscal_period,
            "action": self.action.value,
            "reason_code": self.reason_code.value,
            "document_sha256": self.document_sha256,
            "local_path": str(self.local_path) if self.local_path else None,
            "parse_run_id": self.parse_run_id,
            "blocking_reasons": [reason.value for reason in self.blocking_reasons],
        }


@dataclass(frozen=True, slots=True)
class FilingPlan:
    company: CompanyRef
    start_year: int
    end_year: int
    items: tuple[PlannerItem, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "company": {
                "market": self.company.market,
                "company_id": self.company.company_id,
                "ticker": self.company.ticker,
            },
            "start_year": self.start_year,
            "end_year": self.end_year,
            "items": [item.to_dict() for item in self.items],
        }
