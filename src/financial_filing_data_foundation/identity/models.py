from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable


SUPPORTED_MARKETS = ("CN", "HK")
_ALLOWED_MARKETS = frozenset(SUPPORTED_MARKETS)
_ALLOWED_PERIODS = frozenset({"Q1", "H1", "Q3", "FY"})


def _clean_text(value: str, field: str) -> str:
    text = value.strip()
    if not text:
        raise ValueError(f"{field} must not be empty")
    return text


@dataclass(frozen=True, slots=True)
class CompanyRef:
    market: str
    company_id: str
    ticker: str

    def __post_init__(self) -> None:
        market = self.market.strip().upper()
        if market not in _ALLOWED_MARKETS:
            raise ValueError(f"unsupported P1 market: {self.market!r}")
        object.__setattr__(self, "market", market)
        object.__setattr__(self, "company_id", _clean_text(self.company_id, "company_id"))
        object.__setattr__(self, "ticker", _clean_text(self.ticker, "ticker"))


@dataclass(frozen=True, slots=True)
class FilingRequirement:
    filing_type: str
    raw_fiscal_period: str

    def __post_init__(self) -> None:
        filing_type = _clean_text(self.filing_type, "filing_type").upper()
        period = _clean_text(self.raw_fiscal_period, "raw_fiscal_period").upper()
        if period not in _ALLOWED_PERIODS:
            raise ValueError(f"unsupported P1 fiscal period: {period!r}")
        object.__setattr__(self, "filing_type", filing_type)
        object.__setattr__(self, "raw_fiscal_period", period)


@dataclass(frozen=True, slots=True)
class FilingPolicy:
    requirements: tuple[FilingRequirement, ...]

    def __post_init__(self) -> None:
        if not self.requirements:
            raise ValueError("FilingPolicy.requirements must not be empty")
        seen: set[tuple[str, str]] = set()
        for requirement in self.requirements:
            key = (requirement.filing_type, requirement.raw_fiscal_period)
            if key in seen:
                raise ValueError(f"duplicate filing requirement: {key!r}")
            seen.add(key)

    @classmethod
    def from_iterable(cls, requirements: Iterable[FilingRequirement]) -> "FilingPolicy":
        return cls(tuple(requirements))


@dataclass(frozen=True, slots=True, order=True)
class FilingSlotKey:
    market: str
    company_id: str
    filing_type: str
    fiscal_year: int
    raw_fiscal_period: str

    def __post_init__(self) -> None:
        market = self.market.strip().upper()
        if market not in _ALLOWED_MARKETS:
            raise ValueError(f"unsupported P1 market: {self.market!r}")
        if self.fiscal_year < 1900 or self.fiscal_year > 2200:
            raise ValueError(f"fiscal_year out of supported range: {self.fiscal_year}")
        period = self.raw_fiscal_period.strip().upper()
        if period not in _ALLOWED_PERIODS:
            raise ValueError(f"unsupported P1 fiscal period: {period!r}")
        object.__setattr__(self, "market", market)
        object.__setattr__(self, "company_id", _clean_text(self.company_id, "company_id"))
        object.__setattr__(self, "filing_type", _clean_text(self.filing_type, "filing_type").upper())
        object.__setattr__(self, "raw_fiscal_period", period)

    def serialize(self) -> str:
        return "|".join(
            (
                self.market,
                self.company_id,
                self.filing_type,
                str(self.fiscal_year),
                self.raw_fiscal_period,
            )
        )


@dataclass(frozen=True, slots=True)
class FilingIdentity:
    slot: FilingSlotKey
    amended: bool | None = None

    @property
    def slot_key(self) -> str:
        return self.slot.serialize()


@dataclass(frozen=True, slots=True)
class SourceMetadata:
    provider: str
    source_id: str
    source_url: str
    source_title: str
    filing_date: str | None = None
    report_date: str | None = None
    provider_company_id: str | None = None
    acquired_at: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "provider", _clean_text(self.provider, "provider"))
        object.__setattr__(self, "source_id", _clean_text(self.source_id, "source_id"))
        object.__setattr__(self, "source_url", _clean_text(self.source_url, "source_url"))
        object.__setattr__(self, "source_title", _clean_text(self.source_title, "source_title"))
        if self.acquired_at is not None:
            # Validate only; preserve the caller's exact ISO text.
            datetime.fromisoformat(self.acquired_at.replace("Z", "+00:00"))


def build_required_slots(
    company: CompanyRef,
    start_year: int,
    end_year: int,
    policy: FilingPolicy,
) -> tuple[FilingSlotKey, ...]:
    if start_year > end_year:
        raise ValueError("start_year must be <= end_year")
    slots: list[FilingSlotKey] = []
    for year in range(start_year, end_year + 1):
        for requirement in policy.requirements:
            slots.append(
                FilingSlotKey(
                    market=company.market,
                    company_id=company.company_id,
                    filing_type=requirement.filing_type,
                    fiscal_year=year,
                    raw_fiscal_period=requirement.raw_fiscal_period,
                )
            )
    return tuple(slots)
