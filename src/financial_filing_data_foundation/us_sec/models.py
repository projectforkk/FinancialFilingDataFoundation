from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class SecIssuerKind(StrEnum):
    UNKNOWN = "UNKNOWN"
    DOMESTIC = "DOMESTIC"
    FPI = "FPI"


@dataclass(frozen=True, slots=True)
class SecCompanyRef:
    cik: str
    ticker: str
    company_id: str
    company_name: str | None = None
    issuer_kind: SecIssuerKind = SecIssuerKind.UNKNOWN


@dataclass(frozen=True, slots=True)
class SecFilingSlot:
    company_id: str
    fiscal_year: int
    raw_fiscal_period: str
    issuer_kind: SecIssuerKind = SecIssuerKind.UNKNOWN

    def __post_init__(self) -> None:
        period = self.raw_fiscal_period.strip().upper()
        if period not in {"Q1", "Q2", "Q3", "FY"}:
            raise ValueError(f"unsupported US fiscal period: {period!r}")
        if self.fiscal_year < 1900 or self.fiscal_year > 2200:
            raise ValueError(f"fiscal_year out of supported range: {self.fiscal_year}")
        object.__setattr__(self, "company_id", self.company_id.strip())
        object.__setattr__(self, "raw_fiscal_period", period)

    def serialize(self) -> str:
        return "|".join(
            ("US", self.company_id, "SEC", str(self.fiscal_year), self.raw_fiscal_period)
        )


@dataclass(frozen=True, slots=True)
class SecFilingCandidate:
    cik: str
    ticker: str
    accession: str
    normalized_accession: str
    form: str
    filing_date: str
    report_period: str | None
    primary_document: str
    source_url: str
    amended: bool
    issuer_kind: SecIssuerKind = SecIssuerKind.UNKNOWN

    @property
    def base_form(self) -> str:
        return self.form[:-2] if self.form.endswith("/A") else self.form

