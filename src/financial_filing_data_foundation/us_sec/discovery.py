from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta
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
    history_files: tuple[str, ...] = ()
    fiscal_year_end: str | None = None
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


def _normalize_fiscal_year_end(value: Any) -> str | None:
    if value is None or not str(value).strip():
        return None
    text = str(value).strip()
    if not re.fullmatch(r"\d{4}", text):
        raise SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, "SEC fiscalYearEnd metadata is invalid")
    month = int(text[:2])
    day = int(text[2:])
    try:
        date(2000, month, day)
    except ValueError as exc:
        raise SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, "SEC fiscalYearEnd metadata is invalid") from exc
    return text


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
    if recent is None and "accessionNumber" in payload:
        # SEC historical submissions chunks use the array shape directly.
        recent = payload
    if not isinstance(recent, dict):
        raise SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, "SEC submissions recent history is missing")
    fiscal_year_end = _normalize_fiscal_year_end(
        payload.get("fiscalYearEnd", payload.get("fiscal_year_end"))
    )
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
    history_files: list[str] = []
    if isinstance(filings, dict) and isinstance(filings.get("files"), list):
        for item in filings["files"]:
            if isinstance(item, dict) and isinstance(item.get("name"), str):
                history_files.append(item["name"])
    return SecSubmissions(
        company=company,
        candidates=tuple(candidates),
        history_files=tuple(sorted(set(history_files))),
        fiscal_year_end=fiscal_year_end,
        raw_sha256=raw_sha256,
        source_url=source_url,
    )


def _report_date(report_period: str | None) -> date | None:
    if not report_period:
        return None
    try:
        return date.fromisoformat(report_period[:10])
    except ValueError:
        return None


def _fiscal_year_for_report_date(report_period: str | None, fiscal_year_end: str) -> int | None:
    report_date = _report_date(report_period)
    if report_date is None:
        return None
    end_month = int(fiscal_year_end[:2])
    end_day = int(fiscal_year_end[2:])
    return report_date.year + int((report_date.month, report_date.day) > (end_month, end_day))


def _quarter_for_report_date(
    report_period: str | None,
    *,
    fiscal_year: int,
    fiscal_year_end: str,
) -> str | None:
    report_date = _report_date(report_period)
    if report_date is None:
        return None
    end_month = int(fiscal_year_end[:2])
    end_day = int(fiscal_year_end[2:])
    try:
        fiscal_end = date(fiscal_year, end_month, end_day)
        fiscal_start = date(fiscal_year - 1, end_month, end_day) + timedelta(days=1)
    except ValueError:
        return None
    if not fiscal_start <= report_date <= fiscal_end:
        return None
    total_days = (fiscal_end - fiscal_start).days + 1
    elapsed_days = (report_date - fiscal_start).days + 1
    quarter_number = (elapsed_days * 4 + total_days - 1) // total_days
    return f"Q{quarter_number}" if 1 <= quarter_number <= 3 else None


def _fiscal_year_end_for_request(
    submissions: SecSubmissions,
    *,
    fiscal_year: int,
    issuer_kind: SecIssuerKind | None,
) -> str | None:
    if submissions.fiscal_year_end:
        return submissions.fiscal_year_end

    annuals: list[SecFilingCandidate] = []
    for candidate in submissions.candidates:
        if candidate.base_form not in {"10-K", "20-F", "40-F"}:
            continue
        if issuer_kind is not None and candidate.issuer_kind is not issuer_kind:
            continue
        report_date = _report_date(candidate.report_period)
        if report_date is not None and report_date.year == fiscal_year:
            annuals.append(candidate)
    end_dates: set[str] = set()
    for candidate in annuals:
        report_date = _report_date(candidate.report_period)
        if report_date is not None:
            end_dates.add(f"{report_date.month:02d}{report_date.day:02d}")
    return next(iter(end_dates)) if len(end_dates) == 1 else None


def _quarter_slots(
    submissions: SecSubmissions,
    *,
    fiscal_year: int,
    fiscal_year_end: str,
    issuer_kind: SecIssuerKind | None,
) -> dict[str, str]:
    report_periods: dict[str, str] = {}
    for candidate in submissions.candidates:
        if candidate.base_form != "10-Q":
            continue
        if issuer_kind is not None and candidate.issuer_kind is not issuer_kind:
            continue
        report_date = _report_date(candidate.report_period)
        if report_date is None or _fiscal_year_for_report_date(candidate.report_period, fiscal_year_end) != fiscal_year:
            continue
        quarter = _quarter_for_report_date(
            candidate.report_period,
            fiscal_year=fiscal_year,
            fiscal_year_end=fiscal_year_end,
        )
        if quarter is not None:
            report_periods[report_date.isoformat()] = quarter
    return report_periods


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
    fiscal_year_end = _fiscal_year_end_for_request(
        submissions,
        fiscal_year=fiscal_year,
        issuer_kind=issuer_kind,
    )
    if fiscal_year_end is None:
        return ()
    quarter_slots = _quarter_slots(
        submissions,
        fiscal_year=fiscal_year,
        fiscal_year_end=fiscal_year_end,
        issuer_kind=issuer_kind,
    )
    matches: list[SecFilingCandidate] = []
    for candidate in submissions.candidates:
        kind = issuer_kind or candidate.issuer_kind
        if kind is SecIssuerKind.UNKNOWN:
            continue
        try:
            allowed_forms = SecFormPolicy.forms_for(normalized_period, kind)
        except SecError:
            continue
        if candidate.base_form not in allowed_forms:
            continue
        if _fiscal_year_for_report_date(candidate.report_period, fiscal_year_end) != fiscal_year:
            continue
        report_date = _report_date(candidate.report_period)
        if normalized_period == "FY":
            is_target_slot = candidate.base_form in {"10-K", "20-F", "40-F"}
        else:
            is_target_slot = report_date is not None and quarter_slots.get(report_date.isoformat()) == normalized_period
        if not is_target_slot:
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
