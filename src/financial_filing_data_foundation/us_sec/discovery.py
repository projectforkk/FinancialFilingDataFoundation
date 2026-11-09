from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Any, Iterable

from .errors import P11Reason, SecError
from .models import SecCompanyRef, SecFilingCandidate, SecIssuerKind
from .policy import SecFormPolicy


_ACCESSION_RE = re.compile(r"^\d{10}-\d{2}-\d{6}$")
_SAFE_MEMBER_RE = re.compile(r"^[^/\\]+$")


@dataclass(frozen=True, slots=True)
class SecSubmissions:
    company: SecCompanyRef
    candidates: tuple[SecFilingCandidate, ...]
    raw_sha256: str | None = None
    source_url: str | None = None


def _array(recent: dict[str, Any], key: str, index: int, *, required: bool = True) -> Any:
    values = recent.get(key)
    if not isinstance(values, list) or index >= len(values):
        if required:
            raise SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, f"submissions field {key} is misaligned")
        return None
    return values[index]


def _candidate_url(cik: str, accession: str, primary_document: str) -> str:
    if not _SAFE_MEMBER_RE.fullmatch(primary_document) or primary_document in {".", ".."}:
        raise SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, "SEC primary document path is unsafe")
    normalized = accession.replace("-", "")
    return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{normalized}/{primary_document}"


def _issuer_kind(form: str) -> SecIssuerKind:
    base = SecFormPolicy.base_form(form)
    if base in {"20-F", "40-F"}:
        return SecIssuerKind.FPI
    if base in {"10-K", "10-Q"}:
        return SecIssuerKind.DOMESTIC
    return SecIssuerKind.UNKNOWN


def parse_submissions(
    payload: dict[str, Any],
    *,
    company: SecCompanyRef,
    source_url: str | None = None,
    raw_sha256: str | None = None,
) -> SecSubmissions:
    if not isinstance(payload, dict):
        raise SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, "SEC submissions must be an object")
    raw_cik = payload.get("cik")
    if raw_cik is not None and str(raw_cik).zfill(10) != company.cik:
        raise SecError(P11Reason.P11_INVALID_US_IDENTITY, "SEC submissions CIK does not match requested CIK")
    filings = payload.get("filings")
    recent = filings.get("recent") if isinstance(filings, dict) else None
    if not isinstance(recent, dict):
        raise SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, "SEC submissions recent history is missing")
    accessions = recent.get("accessionNumber")
    forms = recent.get("form")
    dates = recent.get("filingDate")
    primary_documents = recent.get("primaryDocument")
    if not all(isinstance(value, list) for value in (accessions, forms, dates, primary_documents)):
        raise SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, "SEC submissions arrays are missing")
    candidates: list[SecFilingCandidate] = []
    for index, raw_accession in enumerate(accessions):
        if not isinstance(raw_accession, str) or not _ACCESSION_RE.fullmatch(raw_accession):
            raise SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, "SEC accession is invalid")
        form = _array(recent, "form", index)
        filing_date = _array(recent, "filingDate", index)
        primary_document = _array(recent, "primaryDocument", index)
        report_period = _array(recent, "reportPeriod", index, required=False)
        if report_period is None:
            report_period = _array(recent, "reportDate", index, required=False)
        if not isinstance(form, str) or not isinstance(filing_date, str) or not isinstance(primary_document, str):
            raise SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, "SEC filing metadata is invalid")
        if report_period is not None and not isinstance(report_period, str):
            report_period = None
        kind = _issuer_kind(form)
        candidates.append(
            SecFilingCandidate(
                cik=company.cik,
                ticker=company.ticker,
                accession=raw_accession,
                normalized_accession=raw_accession.replace("-", ""),
                form=form.strip().upper(),
                filing_date=filing_date.strip(),
                report_period=report_period.strip() if report_period else None,
                primary_document=primary_document.strip(),
                source_url=_candidate_url(company.cik, raw_accession, primary_document.strip()),
                amended=SecFormPolicy.is_amendment(form),
                issuer_kind=kind,
            )
        )
    return SecSubmissions(company=company, candidates=tuple(candidates), raw_sha256=raw_sha256, source_url=source_url)


def _period_for_report_date(report_period: str | None) -> str | None:
    if not report_period:
        return None
    try:
        month = date.fromisoformat(report_period[:10]).month
    except ValueError:
        return None
    return {3: "Q1", 6: "Q2", 9: "Q3", 12: "FY"}.get(month)


def discover_filings(
    submissions: SecSubmissions,
    *,
    fiscal_year: int,
    period: str,
    issuer_kind: SecIssuerKind | None = None,
) -> tuple[SecFilingCandidate, ...]:
    normalized_period = period.strip().upper()
    if normalized_period not in {"Q1", "Q2", "Q3", "FY"}:
        raise SecError(P11Reason.P11_FORM_POLICY_MISMATCH, f"unsupported US period: {period}")
    matches: list[SecFilingCandidate] = []
    for candidate in submissions.candidates:
        if not candidate.report_period or candidate.report_period[:4] != str(fiscal_year):
            continue
        kind = issuer_kind or candidate.issuer_kind
        if kind is SecIssuerKind.UNKNOWN:
            continue
        try:
            allowed_forms = SecFormPolicy.forms_for(normalized_period, kind)
        except SecError:
            continue
        if candidate.base_form not in allowed_forms:
            continue
        if _period_for_report_date(candidate.report_period) != normalized_period:
            continue
        matches.append(candidate)
    matches.sort(key=lambda item: (item.amended, item.filing_date, item.accession))
    return tuple(matches)


def select_filing(candidates: Iterable[SecFilingCandidate]) -> SecFilingCandidate:
    rows = tuple(candidates)
    originals = tuple(row for row in rows if not row.amended)
    amendments = tuple(row for row in rows if row.amended)
    if not rows:
        raise SecError(P11Reason.P11_FILING_NOT_FOUND, "no SEC filing matched requested slot")
    if len(originals) != 1:
        raise SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, "multiple or missing original SEC filings")
    if amendments:
        raise SecError(
            P11Reason.P11_AMENDED_VARIANT_PRESENT,
            "original and amended SEC filings require review before active binding",
        )
    return originals[0]


__all__ = ["SecSubmissions", "discover_filings", "parse_submissions", "select_filing"]
