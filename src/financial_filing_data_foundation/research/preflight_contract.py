from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Final, Iterable, Mapping, Sequence

from financial_filing_data_foundation.mcp.research_review_contract import (
    ResearchQualityState,
)


RESEARCH_PREFLIGHT_SCHEMA_VERSION: Final = "research-preflight-v1"
RESEARCH_REQUIREMENT_SET_SCHEMA_VERSION: Final = "research-requirement-set-v1"

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ResearchPreflightContractError(ValueError):
    def __init__(self, reason_code: str, message: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


class RequirementCriticality(StrEnum):
    CRITICAL = "CRITICAL"
    NON_CRITICAL = "NON_CRITICAL"


class RequirementAvailability(StrEnum):
    AVAILABLE = "AVAILABLE"
    PARTIAL = "PARTIAL"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    NEEDS_UPSTREAM_FIX = "NEEDS_UPSTREAM_FIX"
    NOT_DISCLOSED = "NOT_DISCLOSED"
    NOT_FOUND = "NOT_FOUND"
    AMBIGUOUS = "AMBIGUOUS"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class FilingCoverageStatus(StrEnum):
    COMPLETE_BY_POLICY = "COMPLETE_BY_POLICY"
    OBSERVED_ONLY = "OBSERVED_ONLY"
    CATALOG_COVERAGE_UNCONFIRMED = "CATALOG_COVERAGE_UNCONFIRMED"
    NOT_EVALUATED = "NOT_EVALUATED"


class RepairDisposition(StrEnum):
    QUALITY_REVIEW = "QUALITY_REVIEW"
    UPSTREAM_FIX = "UPSTREAM_FIX"
    RESEARCH_GAP = "RESEARCH_GAP"
    NOT_DISCLOSED = "NOT_DISCLOSED"
    CATALOG_GAP = "CATALOG_GAP"
    NO_ACTION = "NO_ACTION"


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _required_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ResearchPreflightContractError(
            "RESEARCH_PREFLIGHT_INVALID_INPUT",
            f"{field_name} must be a non-blank string",
        )
    return value.strip()


def _required_sha256(value: object, field_name: str) -> str:
    text = _required_text(value, field_name)
    if not _SHA256_RE.fullmatch(text):
        raise ResearchPreflightContractError(
            "RESEARCH_PREFLIGHT_INVALID_INPUT",
            f"{field_name} must be lowercase SHA256",
        )
    return text


def _normalized_text_tuple(
    values: Iterable[str],
    field_name: str,
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    normalized = tuple(sorted({_required_text(item, field_name) for item in values}))
    if not normalized and not allow_empty:
        raise ResearchPreflightContractError(
            "RESEARCH_PREFLIGHT_INVALID_INPUT",
            f"{field_name} must not be empty",
        )
    return normalized


@dataclass(frozen=True, slots=True)
class ResearchRequirement:
    requirement_id: str
    source_rule_ref: str
    description: str
    target_periods: tuple[str, ...]
    evidence_strategies: tuple[str, ...]
    criticality: RequirementCriticality
    allow_partial: bool = False
    allow_not_disclosed: bool = False

    def normalized(self) -> "ResearchRequirement":
        return ResearchRequirement(
            requirement_id=_required_text(self.requirement_id, "requirement_id"),
            source_rule_ref=_required_text(self.source_rule_ref, "source_rule_ref"),
            description=_required_text(self.description, "description"),
            target_periods=_normalized_text_tuple(
                self.target_periods,
                "target_periods",
            ),
            evidence_strategies=_normalized_text_tuple(
                self.evidence_strategies,
                "evidence_strategies",
            ),
            criticality=RequirementCriticality(self.criticality),
            allow_partial=bool(self.allow_partial),
            allow_not_disclosed=bool(self.allow_not_disclosed),
        )

    def to_dict(self) -> dict[str, object]:
        item = self.normalized()
        return {
            "requirement_id": item.requirement_id,
            "source_rule_ref": item.source_rule_ref,
            "description": item.description,
            "target_periods": list(item.target_periods),
            "evidence_strategies": list(item.evidence_strategies),
            "criticality": item.criticality.value,
            "allow_partial": item.allow_partial,
            "allow_not_disclosed": item.allow_not_disclosed,
        }


@dataclass(frozen=True, slots=True)
class ResearchRequirementSet:
    schema_version: str
    spec_bundle_hash: str
    requirements: tuple[ResearchRequirement, ...]
    requirement_set_hash: str

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "spec_bundle_hash": self.spec_bundle_hash,
            "requirements": [item.to_dict() for item in self.requirements],
            "requirement_set_hash": self.requirement_set_hash,
        }


def build_research_requirement_set(
    spec_bundle_hash: str,
    requirements: Sequence[ResearchRequirement],
) -> ResearchRequirementSet:
    spec_hash = _required_sha256(spec_bundle_hash, "spec_bundle_hash")
    if not requirements:
        raise ResearchPreflightContractError(
            "RESEARCH_PREFLIGHT_INVALID_INPUT",
            "requirements must not be empty",
        )
    normalized = tuple(
        sorted(
            (item.normalized() for item in requirements),
            key=lambda item: item.requirement_id,
        )
    )
    ids = tuple(item.requirement_id for item in normalized)
    if len(ids) != len(set(ids)):
        raise ResearchPreflightContractError(
            "RESEARCH_PREFLIGHT_DUPLICATE_REQUIREMENT",
            "requirement_id values must be unique",
        )
    payload = {
        "schema_version": RESEARCH_REQUIREMENT_SET_SCHEMA_VERSION,
        "spec_bundle_hash": spec_hash,
        "requirements": [item.to_dict() for item in normalized],
    }
    return ResearchRequirementSet(
        schema_version=RESEARCH_REQUIREMENT_SET_SCHEMA_VERSION,
        spec_bundle_hash=spec_hash,
        requirements=normalized,
        requirement_set_hash=_sha256(payload),
    )


@dataclass(frozen=True, slots=True)
class ObservedFiling:
    document_sha256: str
    fiscal_year: int
    filing_type: str

    def normalized(self) -> "ObservedFiling":
        if isinstance(self.fiscal_year, bool) or not isinstance(self.fiscal_year, int):
            raise ResearchPreflightContractError(
                "RESEARCH_PREFLIGHT_INVALID_INPUT",
                "fiscal_year must be an integer",
            )
        return ObservedFiling(
            document_sha256=_required_sha256(
                self.document_sha256,
                "document_sha256",
            ),
            fiscal_year=int(self.fiscal_year),
            filing_type=_required_text(self.filing_type, "filing_type").upper(),
        )

    def to_dict(self) -> dict[str, object]:
        item = self.normalized()
        return {
            "document_sha256": item.document_sha256,
            "fiscal_year": item.fiscal_year,
            "filing_type": item.filing_type,
        }


@dataclass(frozen=True, slots=True)
class FilingCoverage:
    status: FilingCoverageStatus
    observed_filings: tuple[ObservedFiling, ...]
    latest_filing_label: str | None
    warnings: tuple[str, ...] = ()

    def normalized(self) -> "FilingCoverage":
        observed = tuple(
            sorted(
                (item.normalized() for item in self.observed_filings),
                key=lambda item: (
                    item.fiscal_year,
                    item.filing_type,
                    item.document_sha256,
                ),
            )
        )
        shas = tuple(item.document_sha256 for item in observed)
        if len(shas) != len(set(shas)):
            raise ResearchPreflightContractError(
                "RESEARCH_PREFLIGHT_DUPLICATE_DOCUMENT",
                "observed filing document_sha256 values must be unique",
            )
        label = (
            None
            if self.latest_filing_label is None
            else _required_text(self.latest_filing_label, "latest_filing_label")
        )
        return FilingCoverage(
            status=FilingCoverageStatus(self.status),
            observed_filings=observed,
            latest_filing_label=label,
            warnings=_normalized_text_tuple(
                self.warnings,
                "warnings",
                allow_empty=True,
            ),
        )

    def to_dict(self) -> dict[str, object]:
        item = self.normalized()
        return {
            "status": item.status.value,
            "observed_document_count": len(item.observed_filings),
            "observed_filings": [row.to_dict() for row in item.observed_filings],
            "latest_filing": item.latest_filing_label,
            "warnings": list(item.warnings),
        }


@dataclass(frozen=True, slots=True)
class DocumentQualityObservation:
    document_sha256: str
    quality_state: ResearchQualityState

    def normalized(self) -> "DocumentQualityObservation":
        return DocumentQualityObservation(
            document_sha256=_required_sha256(
                self.document_sha256,
                "document_sha256",
            ),
            quality_state=ResearchQualityState(self.quality_state),
        )

    def to_dict(self) -> dict[str, str]:
        item = self.normalized()
        return {
            "document_sha256": item.document_sha256,
            "quality_state": item.quality_state.value,
        }


@dataclass(frozen=True, slots=True)
class ResearchCoverageObservation:
    requirement_id: str
    availability: RequirementAvailability
    evidence_refs: tuple[str, ...] = ()
    note: str | None = None

    def normalized(self) -> "ResearchCoverageObservation":
        note = None if self.note is None else _required_text(self.note, "note")
        return ResearchCoverageObservation(
            requirement_id=_required_text(self.requirement_id, "requirement_id"),
            availability=RequirementAvailability(self.availability),
            evidence_refs=_normalized_text_tuple(
                self.evidence_refs,
                "evidence_refs",
                allow_empty=True,
            ),
            note=note,
        )

    def to_dict(self) -> dict[str, object]:
        item = self.normalized()
        return {
            "requirement_id": item.requirement_id,
            "availability": item.availability.value,
            "evidence_refs": list(item.evidence_refs),
            "note": item.note,
        }


@dataclass(frozen=True, slots=True)
class RepairQueueItem:
    disposition: RepairDisposition
    reason: str
    document_sha256: str | None = None
    requirement_id: str | None = None
    review_task_id: str | None = None

    def normalized(self) -> "RepairQueueItem":
        return RepairQueueItem(
            disposition=RepairDisposition(self.disposition),
            reason=_required_text(self.reason, "reason"),
            document_sha256=(
                None
                if self.document_sha256 is None
                else _required_sha256(self.document_sha256, "document_sha256")
            ),
            requirement_id=(
                None
                if self.requirement_id is None
                else _required_text(self.requirement_id, "requirement_id")
            ),
            review_task_id=(
                None
                if self.review_task_id is None
                else _required_text(self.review_task_id, "review_task_id")
            ),
        )

    def to_dict(self) -> dict[str, object]:
        item = self.normalized()
        return {
            "disposition": item.disposition.value,
            "reason": item.reason,
            "document_sha256": item.document_sha256,
            "requirement_id": item.requirement_id,
            "review_task_id": item.review_task_id,
        }


@dataclass(frozen=True, slots=True)
class ResearchPreflightResult:
    schema_version: str
    market: str
    ticker: str
    research_year_from: int
    research_year_to: int
    spec_bundle_hash: str
    requirement_set_hash: str
    filing_coverage: FilingCoverage
    document_quality: tuple[DocumentQualityObservation, ...]
    research_coverage: tuple[ResearchCoverageObservation, ...]
    repair_queue: tuple[RepairQueueItem, ...]
    period_monitoring_complete: bool
    research_ready: bool
    database_fully_reviewed: bool
    research_blocker_count: int
    preflight_hash: str

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "company": {
                "market": self.market,
                "ticker": self.ticker,
            },
            "research_period": {
                "from": self.research_year_from,
                "to": self.research_year_to,
            },
            "spec_bundle_hash": self.spec_bundle_hash,
            "requirement_set_hash": self.requirement_set_hash,
            "filing_coverage": self.filing_coverage.to_dict(),
            "document_quality": [
                item.to_dict() for item in self.document_quality
            ],
            "research_coverage": [
                item.to_dict() for item in self.research_coverage
            ],
            "repair_queue": [item.to_dict() for item in self.repair_queue],
            "period_monitoring_complete": self.period_monitoring_complete,
            "research_ready": self.research_ready,
            "database_fully_reviewed": self.database_fully_reviewed,
            "research_blocker_count": self.research_blocker_count,
            "preflight_hash": self.preflight_hash,
        }


def _requirement_blocks(
    requirement: ResearchRequirement,
    observation: ResearchCoverageObservation,
) -> bool:
    if requirement.criticality is RequirementCriticality.NON_CRITICAL:
        return False
    status = observation.availability
    if status in {
        RequirementAvailability.AVAILABLE,
        RequirementAvailability.NOT_APPLICABLE,
    }:
        return False
    if status is RequirementAvailability.PARTIAL:
        return not requirement.allow_partial
    if status is RequirementAvailability.NOT_DISCLOSED:
        return not requirement.allow_not_disclosed
    return True


def build_research_preflight_result(
    *,
    market: str,
    ticker: str,
    research_year_from: int,
    research_year_to: int,
    requirement_set: ResearchRequirementSet,
    filing_coverage: FilingCoverage,
    document_quality: Sequence[DocumentQualityObservation],
    research_coverage: Sequence[ResearchCoverageObservation],
    repair_queue: Sequence[RepairQueueItem] = (),
) -> ResearchPreflightResult:
    market_value = _required_text(market, "market").upper()
    ticker_value = _required_text(ticker, "ticker")
    if (
        isinstance(research_year_from, bool)
        or not isinstance(research_year_from, int)
        or isinstance(research_year_to, bool)
        or not isinstance(research_year_to, int)
        or research_year_from > research_year_to
    ):
        raise ResearchPreflightContractError(
            "RESEARCH_PREFLIGHT_INVALID_INPUT",
            "research year range is invalid",
        )

    _required_sha256(requirement_set.spec_bundle_hash, "spec_bundle_hash")
    _required_sha256(
        requirement_set.requirement_set_hash,
        "requirement_set_hash",
    )

    filing = filing_coverage.normalized()
    quality = tuple(
        sorted(
            (item.normalized() for item in document_quality),
            key=lambda item: item.document_sha256,
        )
    )
    quality_shas = tuple(item.document_sha256 for item in quality)
    if len(quality_shas) != len(set(quality_shas)):
        raise ResearchPreflightContractError(
            "RESEARCH_PREFLIGHT_DUPLICATE_DOCUMENT",
            "document quality observations must be unique",
        )

    coverage = tuple(
        sorted(
            (item.normalized() for item in research_coverage),
            key=lambda item: item.requirement_id,
        )
    )
    coverage_ids = tuple(item.requirement_id for item in coverage)
    if len(coverage_ids) != len(set(coverage_ids)):
        raise ResearchPreflightContractError(
            "RESEARCH_PREFLIGHT_DUPLICATE_REQUIREMENT",
            "research coverage requirement_id values must be unique",
        )

    requirement_by_id = {
        item.requirement_id: item for item in requirement_set.requirements
    }
    if set(coverage_ids) != set(requirement_by_id):
        raise ResearchPreflightContractError(
            "RESEARCH_PREFLIGHT_REQUIREMENT_MISMATCH",
            "research coverage must contain exactly one item per requirement",
        )

    queue = tuple(
        sorted(
            (item.normalized() for item in repair_queue),
            key=lambda item: (
                item.disposition.value,
                item.document_sha256 or "",
                item.requirement_id or "",
                item.review_task_id or "",
                item.reason,
            ),
        )
    )

    observed_shas = {
        item.document_sha256 for item in filing.observed_filings
    }
    quality_sha_set = set(quality_shas)
    monitoring_complete = observed_shas == quality_sha_set

    blocker_count = sum(
        1
        for observation in coverage
        if _requirement_blocks(
            requirement_by_id[observation.requirement_id],
            observation,
        )
    )
    research_ready = monitoring_complete and blocker_count == 0

    reusable_states = {
        ResearchQualityState.COMPLETE_BASE,
        ResearchQualityState.COMPLETE_REVIEWED,
    }
    database_fully_reviewed = (
        monitoring_complete
        and all(item.quality_state in reusable_states for item in quality)
    )

    payload = {
        "schema_version": RESEARCH_PREFLIGHT_SCHEMA_VERSION,
        "company": {
            "market": market_value,
            "ticker": ticker_value,
        },
        "research_period": {
            "from": research_year_from,
            "to": research_year_to,
        },
        "spec_bundle_hash": requirement_set.spec_bundle_hash,
        "requirement_set_hash": requirement_set.requirement_set_hash,
        "filing_coverage": filing.to_dict(),
        "document_quality": [item.to_dict() for item in quality],
        "research_coverage": [item.to_dict() for item in coverage],
        "repair_queue": [item.to_dict() for item in queue],
        "period_monitoring_complete": monitoring_complete,
        "research_ready": research_ready,
        "database_fully_reviewed": database_fully_reviewed,
        "research_blocker_count": blocker_count,
    }

    return ResearchPreflightResult(
        schema_version=RESEARCH_PREFLIGHT_SCHEMA_VERSION,
        market=market_value,
        ticker=ticker_value,
        research_year_from=research_year_from,
        research_year_to=research_year_to,
        spec_bundle_hash=requirement_set.spec_bundle_hash,
        requirement_set_hash=requirement_set.requirement_set_hash,
        filing_coverage=filing,
        document_quality=quality,
        research_coverage=coverage,
        repair_queue=queue,
        period_monitoring_complete=monitoring_complete,
        research_ready=research_ready,
        database_fully_reviewed=database_fully_reviewed,
        research_blocker_count=blocker_count,
        preflight_hash=_sha256(payload),
    )
