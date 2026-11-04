from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re
from typing import Iterable


_ASCII_WHITESPACE = " \t\n\r\f\v"
_CIK_RE = re.compile(r"^[0-9]{1,10}$")
_ACCESSION_RE = re.compile(r"^[0-9]{10}-[0-9]{2}-[0-9]{6}$")
_DATE_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
_PERIODIC_FORMS = frozenset({"10-K", "10-Q", "20-F", "40-F"})
_SUPPLEMENTAL_FORMS = frozenset({"8-K", "6-K"})
_ALLOWED_FORMS = _PERIODIC_FORMS | _SUPPLEMENTAL_FORMS


class CikInvalid(ValueError):
    reason_code = "P11_CIK_INVALID"


class CompanyIdentityNotFound(ValueError):
    reason_code = "P11_COMPANY_IDENTITY_NOT_FOUND"


class CompanyIdentityAmbiguous(ValueError):
    reason_code = "P11_COMPANY_IDENTITY_AMBIGUOUS"


@dataclass(frozen=True, slots=True)
class SecFormIdentity:
    base_form: str
    amended: bool

    @property
    def supplemental(self) -> bool:
        return self.base_form in _SUPPLEMENTAL_FORMS

    @property
    def periodic(self) -> bool:
        return self.base_form in _PERIODIC_FORMS


@dataclass(frozen=True, slots=True)
class ResolvedUsCompanyIdentity:
    cik: str
    ticker: str | None


@dataclass(frozen=True, slots=True, order=True)
class SupplementalFilingIdentity:
    market: str
    cik: str
    accession_number: str
    base_form: str
    filing_date: str

    def __post_init__(self) -> None:
        market = self.market.strip().upper()
        if market != "US":
            raise ValueError("supplemental SEC identity market must be US")
        form = normalize_sec_form(self.base_form)
        if not form.supplemental:
            raise ValueError("supplemental SEC identity requires 8-K or 6-K")
        object.__setattr__(self, "market", market)
        object.__setattr__(self, "cik", normalize_cik(self.cik))
        object.__setattr__(
            self, "accession_number", normalize_accession_number(self.accession_number)
        )
        object.__setattr__(self, "base_form", form.base_form)
        object.__setattr__(self, "filing_date", normalize_filing_date(self.filing_date))

    @classmethod
    def from_form(
        cls,
        *,
        cik: str,
        accession_number: str,
        form: str,
        filing_date: str,
    ) -> "SupplementalFilingIdentity":
        normalized_form = normalize_sec_form(form)
        if not normalized_form.supplemental:
            raise ValueError("supplemental SEC identity requires 8-K or 6-K")
        return cls(
            market="US",
            cik=cik,
            accession_number=accession_number,
            base_form=normalized_form.base_form,
            filing_date=filing_date,
        )

    @property
    def accession_number_no_dashes(self) -> str:
        return accession_number_without_dashes(self.accession_number)

    def serialize(self) -> str:
        return "|".join(
            (
                self.market,
                self.cik,
                self.accession_number,
                self.base_form,
                self.filing_date,
            )
        )


def _trim_ascii_whitespace(value: str, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    return value.strip(_ASCII_WHITESPACE)


def normalize_cik(value: str) -> str:
    text = _trim_ascii_whitespace(value, "CIK")
    if _CIK_RE.fullmatch(text) is None or int(text) <= 0:
        raise CikInvalid(f"invalid SEC CIK: {value!r}")
    return text.zfill(10)


def cik_without_leading_zeros(value: str) -> str:
    return str(int(normalize_cik(value)))


def normalize_us_ticker(value: str | None) -> str | None:
    if value is None:
        return None
    text = _trim_ascii_whitespace(value, "ticker")
    if not text:
        return None
    if not text.isascii():
        raise ValueError("US ticker must contain only ASCII characters")
    return text.upper()


def normalize_accession_number(value: str) -> str:
    if not isinstance(value, str) or _ACCESSION_RE.fullmatch(value) is None:
        raise ValueError(f"invalid SEC accession_number: {value!r}")
    return value


def accession_number_without_dashes(value: str) -> str:
    return normalize_accession_number(value).replace("-", "")


def normalize_sec_form(value: str) -> SecFormIdentity:
    text = _trim_ascii_whitespace(value, "form")
    if not text.isascii():
        raise ValueError(f"unsupported SEC form: {value!r}")
    text = text.upper()
    amended = text.endswith("/A")
    base_form = text[:-2] if amended else text
    if base_form not in _ALLOWED_FORMS:
        raise ValueError(f"unsupported SEC form: {value!r}")
    return SecFormIdentity(base_form=base_form, amended=amended)


def normalize_filing_date(value: str) -> str:
    if not isinstance(value, str) or _DATE_RE.fullmatch(value) is None:
        raise ValueError(f"invalid SEC filing_date: {value!r}")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"invalid SEC filing_date: {value!r}") from exc
    if parsed.isoformat() != value:
        raise ValueError(f"invalid SEC filing_date: {value!r}")
    return value


def resolve_us_company_identity(
    *,
    cik: str | None,
    ticker: str | None,
    official_ticker_rows: Iterable[tuple[str, str]] = (),
    submission_tickers: Iterable[str] = (),
) -> ResolvedUsCompanyIdentity:
    normalized_ticker = normalize_us_ticker(ticker)

    rows: list[tuple[str, str]] = []
    for row_ticker, row_cik in official_ticker_rows:
        row_ticker_normalized = normalize_us_ticker(row_ticker)
        if row_ticker_normalized is None:
            continue
        rows.append((row_ticker_normalized, normalize_cik(row_cik)))

    submission_set = {
        normalized
        for raw in submission_tickers
        if (normalized := normalize_us_ticker(raw)) is not None
    }

    if cik is not None:
        normalized_cik = normalize_cik(cik)
        if normalized_ticker is not None:
            mapping_matches = {
                row_cik for row_ticker, row_cik in rows if row_ticker == normalized_ticker
            }
            if mapping_matches and mapping_matches != {normalized_cik}:
                raise CompanyIdentityAmbiguous(
                    "P11_COMPANY_IDENTITY_AMBIGUOUS: caller ticker/CIK mismatch"
                )
            if submission_set and normalized_ticker not in submission_set:
                raise CompanyIdentityAmbiguous(
                    "P11_COMPANY_IDENTITY_AMBIGUOUS: caller ticker/CIK mismatch"
                )
            persisted_ticker = normalized_ticker
        else:
            persisted_ticker = (
                next(iter(submission_set)) if len(submission_set) == 1 else None
            )
        return ResolvedUsCompanyIdentity(
            cik=normalized_cik,
            ticker=persisted_ticker,
        )

    if normalized_ticker is None:
        raise CompanyIdentityNotFound(
            "P11_COMPANY_IDENTITY_NOT_FOUND: CIK or ticker is required"
        )

    matches = {
        row_cik for row_ticker, row_cik in rows if row_ticker == normalized_ticker
    }
    if not matches:
        raise CompanyIdentityNotFound(
            f"P11_COMPANY_IDENTITY_NOT_FOUND: ticker {normalized_ticker!r} has no official CIK match"
        )
    if len(matches) != 1:
        raise CompanyIdentityAmbiguous(
            f"P11_COMPANY_IDENTITY_AMBIGUOUS: ticker {normalized_ticker!r} maps to multiple CIKs"
        )

    normalized_cik = next(iter(matches))
    if submission_set and normalized_ticker not in submission_set:
        raise CompanyIdentityAmbiguous(
            "P11_COMPANY_IDENTITY_AMBIGUOUS: resolved ticker/CIK mismatch"
        )
    return ResolvedUsCompanyIdentity(cik=normalized_cik, ticker=normalized_ticker)


__all__ = [
    "CompanyIdentityAmbiguous",
    "CompanyIdentityNotFound",
    "ResolvedUsCompanyIdentity",
    "SecFormIdentity",
    "SupplementalFilingIdentity",
    "accession_number_without_dashes",
    "cik_without_leading_zeros",
    "normalize_accession_number",
    "normalize_cik",
    "normalize_filing_date",
    "normalize_sec_form",
    "normalize_us_ticker",
    "resolve_us_company_identity",
]
