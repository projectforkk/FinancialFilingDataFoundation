from __future__ import annotations

import base64
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date
from datetime import datetime, timezone
from typing import Any, Iterable

from .errors import P11Reason, SecError
from .models import SecCompanyRef, SecFilingCandidate, SecIssuerKind
from .path_policy import archive_member_url, normalize_archive_relative_name
from .policy import SecFormPolicy


_ACCESSION_RE = re.compile(r"^\d{10}-\d{2}-\d{6}$")
SEC_DISCOVERY_SCHEMA = "p11-sec-discovery-v1"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True, slots=True)
class SecHistoryChunk:
    name: str
    filing_from: str | None = None
    filing_to: str | None = None


def candidate_to_record(candidate: SecFilingCandidate) -> dict[str, Any]:
    return {
        "accession": candidate.accession,
        "normalized_accession": candidate.normalized_accession,
        "form": candidate.form,
        "filing_date": candidate.filing_date,
        "report_period": candidate.report_period,
        "primary_document": candidate.primary_document,
        "source_url": candidate.source_url,
        "amended": bool(candidate.amended),
        "issuer_kind": candidate.issuer_kind.value,
    }


@dataclass(frozen=True, slots=True)
class SecDiscoveryObservation:
    observation_sha256: str
    company_id: str
    cik: str
    fiscal_year: int
    period: str
    retrieved_at: str
    source_documents: tuple[dict[str, Any], ...]
    candidates: tuple[dict[str, Any], ...]
    candidate_fingerprint: str
    selected_accession: str | None
    state: str
    artifact_path: str | None = None

    @classmethod
    def create(
        cls,
        *,
        company: SecCompanyRef,
        fiscal_year: int,
        period: str,
        source_documents: Iterable[dict[str, Any]],
        candidates: Iterable[SecFilingCandidate],
        selected_accession: str | None,
        state: str,
        retrieved_at: str | None = None,
        artifact_path: str | None = None,
    ) -> "SecDiscoveryObservation":
        normalized_sources: list[dict[str, Any]] = []
        for source in source_documents:
            url = str(source.get("url") or source.get("source_url") or "").strip()
            body = source.get("body")
            body_b64 = source.get("body_b64")
            if isinstance(body, (bytes, bytearray)):
                body_bytes = bytes(body)
                body_b64 = base64.b64encode(body_bytes).decode("ascii")
            elif isinstance(body_b64, str):
                try:
                    body_bytes = base64.b64decode(body_b64, validate=True)
                except (ValueError, TypeError) as exc:
                    raise SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, "discovery source bytes are invalid") from exc
            else:
                body_bytes = b""
                body_b64 = None
            source_sha256 = str(source.get("sha256") or source.get("source_sha256") or "").strip().lower()
            if body_bytes:
                computed_sha256 = _sha256(body_bytes)
                if source_sha256 and source_sha256 != computed_sha256:
                    raise SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, "discovery source hash mismatch")
                source_sha256 = computed_sha256
            if not url or not source_sha256:
                raise SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, "discovery source URL/hash is missing")
            normalized_sources.append(
                {
                    "url": url,
                    "sha256": source_sha256,
                    "body_b64": body_b64,
                }
            )
        normalized_candidates = tuple(
            candidate_to_record(candidate)
            for candidate in sorted(
                tuple(candidates),
                key=lambda item: (item.accession, item.form, item.filing_date, item.primary_document),
            )
        )
        candidate_bytes = json.dumps(
            list(normalized_candidates), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        candidate_fingerprint = _sha256(candidate_bytes)
        observed_at = retrieved_at or datetime.now(timezone.utc).isoformat()
        canonical = {
            "schema_version": SEC_DISCOVERY_SCHEMA,
            "company_id": company.company_id,
            "cik": company.cik,
            "fiscal_year": int(fiscal_year),
            "period": str(period).strip().upper(),
            "sources": [
                {"url": item["url"], "sha256": item["sha256"]}
                for item in sorted(normalized_sources, key=lambda item: (item["url"], item["sha256"]))
            ],
            "candidates": list(normalized_candidates),
            "candidate_fingerprint": candidate_fingerprint,
            "selected_accession": selected_accession,
            "state": str(state).strip().upper(),
            "retrieved_at": observed_at,
        }
        observation_sha256 = _sha256(
            json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        )
        return cls(
            observation_sha256=observation_sha256,
            company_id=company.company_id,
            cik=company.cik,
            fiscal_year=int(fiscal_year),
            period=str(period).strip().upper(),
            retrieved_at=observed_at,
            source_documents=tuple(normalized_sources),
            candidates=normalized_candidates,
            candidate_fingerprint=candidate_fingerprint,
            selected_accession=selected_accession,
            state=str(state).strip().upper(),
            artifact_path=artifact_path,
        )

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "schema_version": SEC_DISCOVERY_SCHEMA,
            "company_id": self.company_id,
            "cik": self.cik,
            "fiscal_year": int(self.fiscal_year),
            "period": self.period,
            "sources": [
                {"url": item["url"], "sha256": item["sha256"]}
                for item in sorted(self.source_documents, key=lambda item: (item["url"], item["sha256"]))
            ],
            "candidates": list(self.candidates),
            "candidate_fingerprint": self.candidate_fingerprint,
            "selected_accession": self.selected_accession,
            "state": self.state,
            "retrieved_at": self.retrieved_at,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.canonical_payload(),
            "observation_sha256": self.observation_sha256,
            "retrieved_at": self.retrieved_at,
            "source_documents": [dict(item) for item in self.source_documents],
            "artifact_path": self.artifact_path,
        }


@dataclass(frozen=True, slots=True)
class SecSubmissions:
    company: SecCompanyRef
    candidates: tuple[SecFilingCandidate, ...]
    history_files: tuple[str, ...] = ()
    fiscal_year_end: str | None = None
    raw_sha256: str | None = None
    source_url: str | None = None
    history_ranges: tuple[SecHistoryChunk, ...] = ()

    @property
    def history_chunks(self) -> tuple[SecHistoryChunk, ...]:
        if self.history_ranges:
            return self.history_ranges
        return tuple(SecHistoryChunk(name) for name in self.history_files)


def _array(recent: dict[str, Any], key: str, index: int, *, required: bool = True) -> Any:
    values = recent.get(key)
    if not isinstance(values, list) or index >= len(values):
        if required:
            raise SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, f"submissions field {key} is misaligned")
        return None
    return values[index]


def _candidate_url(cik: str, accession: str, primary_document: str) -> str:
    try:
        return archive_member_url(cik, accession, normalize_archive_relative_name(primary_document))
    except SecError as exc:
        raise SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, "SEC primary document path is unsafe") from exc


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
        # Non-periodic submissions can legitimately carry unrelated nested
        # documents. They are not candidates for the P11 periodic provider, so
        # do not construct or validate an archive URL for them.
        if SecFormPolicy.base_form(form) not in {"10-K", "10-Q", "20-F", "40-F"}:
            continue
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
    history_ranges: list[SecHistoryChunk] = []
    if isinstance(filings, dict) and isinstance(filings.get("files"), list):
        for item in filings["files"]:
            if not isinstance(item, dict) or not isinstance(item.get("name"), str):
                continue
            try:
                name = normalize_archive_relative_name(item["name"])
            except SecError as exc:
                raise SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, "SEC history file path is unsafe") from exc
            history_files.append(name)
            history_ranges.append(
                SecHistoryChunk(
                    name=name,
                    filing_from=str(item.get("filingFrom") or item.get("filing_from") or "").strip() or None,
                    filing_to=str(item.get("filingTo") or item.get("filing_to") or "").strip() or None,
                )
            )
    return SecSubmissions(
        company=company,
        candidates=tuple(candidates),
        history_files=tuple(sorted(set(history_files))),
        fiscal_year_end=fiscal_year_end,
        raw_sha256=raw_sha256,
        source_url=source_url,
        history_ranges=tuple(sorted(history_ranges, key=lambda item: item.name)),
    )


def _report_date(report_period: str | None) -> date | None:
    if not report_period:
        return None
    try:
        return date.fromisoformat(report_period[:10])
    except ValueError:
        return None


def _matches_issuer_kind(candidate: SecFilingCandidate, issuer_kind: SecIssuerKind | None) -> bool:
    return issuer_kind is None or issuer_kind is SecIssuerKind.UNKNOWN or candidate.issuer_kind is issuer_kind


def _annual_candidates(
    submissions: SecSubmissions,
    *,
    fiscal_year: int,
    issuer_kind: SecIssuerKind | None,
) -> tuple[SecFilingCandidate, ...]:
    annuals: list[SecFilingCandidate] = []
    for candidate in submissions.candidates:
        if candidate.base_form not in {"10-K", "20-F", "40-F"}:
            continue
        if not _matches_issuer_kind(candidate, issuer_kind):
            continue
        report_date = _report_date(candidate.report_period)
        if report_date is not None and report_date.year == fiscal_year:
            annuals.append(candidate)
    return tuple(annuals)


def _unique_annual_end(candidates: Iterable[SecFilingCandidate]) -> date | None:
    report_dates = sorted(
        {
            report_date
            for candidate in candidates
            if (report_date := _report_date(candidate.report_period)) is not None
        }
    )
    return report_dates[0] if len(report_dates) == 1 else None


def _annual_end_for_year(
    submissions: SecSubmissions,
    *,
    fiscal_year: int,
    issuer_kind: SecIssuerKind | None,
) -> date | None:
    return _unique_annual_end(
        _annual_candidates(submissions, fiscal_year=fiscal_year, issuer_kind=issuer_kind)
    )


def _latest_annual_end(
    submissions: SecSubmissions,
    *,
    issuer_kind: SecIssuerKind | None,
) -> date | None:
    annual_ends = [
        report_date
        for candidate in submissions.candidates
        if candidate.base_form in {"10-K", "20-F", "40-F"}
        and _matches_issuer_kind(candidate, issuer_kind)
        and (report_date := _report_date(candidate.report_period)) is not None
    ]
    return max(annual_ends, default=None)


def _quarter_slots_between(
    submissions: SecSubmissions,
    *,
    prior_annual_end: date | None,
    next_annual_end: date,
    issuer_kind: SecIssuerKind | None,
    require_complete: bool,
) -> dict[str, str]:
    grouped: set[date] = set()
    for candidate in submissions.candidates:
        if candidate.base_form != "10-Q":
            continue
        if not _matches_issuer_kind(candidate, issuer_kind):
            continue
        report_date = _report_date(candidate.report_period)
        if report_date is None or report_date >= next_annual_end:
            continue
        if prior_annual_end is not None and report_date <= prior_annual_end:
            continue
        grouped.add(report_date)
    ordered_dates = sorted(grouped)
    if len(ordered_dates) == 0 or len(ordered_dates) > 3 or (require_complete and len(ordered_dates) != 3):
        return {}
    return {report_date.isoformat(): f"Q{index}" for index, report_date in enumerate(ordered_dates, start=1)}


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
    annual_candidates = _annual_candidates(
        submissions,
        fiscal_year=fiscal_year,
        issuer_kind=issuer_kind,
    )
    target_annual_end = _unique_annual_end(annual_candidates)
    if normalized_period == "FY":
        if target_annual_end is None:
            return ()
        quarter_slots: dict[str, str] = {}
    elif target_annual_end is not None:
        prior_annual_end = _annual_end_for_year(
            submissions,
            fiscal_year=fiscal_year - 1,
            issuer_kind=issuer_kind,
        )
        # A short recent-history fixture may omit the prior annual.  Accept it
        # only when exactly three unique 10-Q report periods precede the exact
        # target annual endpoint; this is chronology, not a date estimate.
        quarter_slots = _quarter_slots_between(
            submissions,
            prior_annual_end=prior_annual_end,
            next_annual_end=target_annual_end,
            issuer_kind=issuer_kind,
            require_complete=True,
        )
    else:
        # For an in-progress year the prior completed annual and the official
        # current fiscalYearEnd metadata are both required.  The metadata is
        # only the current-year upper boundary; quarter slots are chronological.
        prior_annual_end = _annual_end_for_year(
            submissions,
            fiscal_year=fiscal_year - 1,
            issuer_kind=issuer_kind,
        )
        if (
            prior_annual_end is None
            or _latest_annual_end(submissions, issuer_kind=issuer_kind) != prior_annual_end
            or not submissions.fiscal_year_end
        ):
            return ()
        try:
            next_annual_end = date(
                fiscal_year,
                int(submissions.fiscal_year_end[:2]),
                int(submissions.fiscal_year_end[2:]),
            )
        except ValueError:
            return ()
        if next_annual_end <= prior_annual_end:
            return ()
        quarter_slots = _quarter_slots_between(
            submissions,
            prior_annual_end=prior_annual_end,
            next_annual_end=next_annual_end,
            issuer_kind=issuer_kind,
            require_complete=False,
        )
    matches: list[SecFilingCandidate] = []
    for candidate in submissions.candidates:
        kind = candidate.issuer_kind if issuer_kind in {None, SecIssuerKind.UNKNOWN} else issuer_kind
        if kind is SecIssuerKind.UNKNOWN:
            continue
        try:
            allowed_forms = SecFormPolicy.forms_for(normalized_period, kind)
        except SecError:
            continue
        if candidate.base_form not in allowed_forms:
            continue
        report_date = _report_date(candidate.report_period)
        if normalized_period == "FY":
            is_target_slot = report_date == target_annual_end
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


__all__ = [
    "SEC_DISCOVERY_SCHEMA",
    "SecDiscoveryObservation",
    "SecHistoryChunk",
    "SecSubmissions",
    "candidate_to_record",
    "discover_filings",
    "parse_submissions",
    "select_filing",
]
