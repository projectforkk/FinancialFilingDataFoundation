from __future__ import annotations

import datetime as dt
import json
import re
from collections.abc import Iterable
from typing import Any

from financial_filing_data_foundation.identity import (
    normalize_accession_number,
    normalize_cik,
    normalize_sec_form,
    normalize_us_ticker,
)

from .errors import SecDiscoveryError, SecHttpError
from .http import SecHttpClient
from .models import SecContentClass, SecDiscoveryCandidate


_TICKER_URL = "https://www.sec.gov/files/company_tickers.json"
_DATE_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
_REQUIRED_ARRAYS = (
    "accessionNumber",
    "filingDate",
    "reportDate",
    "form",
    "primaryDocument",
    "primaryDocDescription",
    "isXBRL",
    "isInlineXBRL",
)


def _error(reason_code: str, message: str) -> SecDiscoveryError:
    return SecDiscoveryError(reason_code, message)


def _normalize_ticker_provider(value: str) -> str:
    normalized = normalize_us_ticker(value)
    if normalized is None:
        raise ValueError("ticker must not be empty")
    return normalized


def _validate_primary_document_basename(value: str) -> str:
    if not value or value in {".", ".."}:
        raise ValueError("primaryDocument must be a non-empty basename")
    if any(ch in value for ch in "/\\?#"):
        raise ValueError("primaryDocument must be a basename")
    if any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in value):
        raise ValueError("primaryDocument contains an ASCII control character")
    return value


def _json_object(body: bytes) -> dict[str, Any]:
    try:
        raw = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:  # Normally blocked by SecHttpClient.
        raise _error("P11_SUBMISSIONS_INVALID", "SEC discovery JSON is invalid") from exc
    if not isinstance(raw, dict):
        raise _error("P11_SUBMISSIONS_INVALID", "SEC discovery JSON must be an object")
    return raw


def _date(value: object, field: str, *, allow_empty: bool = False) -> str | None:
    if type(value) is not str:
        raise _error("P11_SUBMISSIONS_INVALID", f"{field} must be a JSON string")
    if allow_empty and value == "":
        return None
    if _DATE_RE.fullmatch(value) is None:
        raise _error("P11_SUBMISSIONS_INVALID", f"{field} must be YYYY-MM-DD")
    try:
        parsed = dt.date.fromisoformat(value)
    except ValueError as exc:
        raise _error("P11_SUBMISSIONS_INVALID", f"{field} is not a valid calendar date") from exc
    if parsed.isoformat() != value:
        raise _error("P11_SUBMISSIONS_INVALID", f"{field} is not canonical")
    return value


def _normalize_cik_provider(value: object) -> str:
    if type(value) is not str:
        raise _error("P11_SUBMISSIONS_INVALID", "Submissions cik must be a JSON string")
    try:
        return normalize_cik(value)
    except ValueError as exc:
        raise _error("P11_SUBMISSIONS_INVALID", "Submissions cik is invalid") from exc


def _normalize_accession_provider(value: object) -> str:
    if type(value) is not str:
        raise _error("P11_SUBMISSIONS_INVALID", "accessionNumber must be a JSON string")
    try:
        return normalize_accession_number(value)
    except ValueError as exc:
        raise _error("P11_SUBMISSIONS_INVALID", "accessionNumber is invalid") from exc


def _normalize_form_provider(value: object) -> tuple[str, str, bool]:
    if type(value) is not str:
        raise _error("P11_SUBMISSIONS_INVALID", "form must be a JSON string")
    try:
        info = normalize_sec_form(value)
    except ValueError as exc:
        raise _error("P11_SUBMISSIONS_INVALID", "SEC form is invalid or unsupported") from exc
    normalized_form = info.base_form + ("/A" if info.amended else "")
    return normalized_form, info.base_form, info.amended


def _normalize_primary(value: object) -> str:
    if type(value) is not str:
        raise _error("P11_SUBMISSIONS_INVALID", "primaryDocument must be a JSON string")
    try:
        return _validate_primary_document_basename(value)
    except ValueError as exc:
        raise _error("P11_SUBMISSIONS_INVALID", "primaryDocument is not a safe basename") from exc


def _normalize_description(value: object) -> str | None:
    if type(value) is not str:
        raise _error("P11_SUBMISSIONS_INVALID", "primaryDocDescription must be a JSON string")
    return None if value == "" else value


def _normalize_flag(value: object, field: str) -> bool:
    if type(value) is not int or value not in (0, 1):
        raise _error("P11_SUBMISSIONS_INVALID", f"{field} must be integer 0 or 1")
    return bool(value)


def _parallel_arrays(container: object, *, filing_count: int | None = None) -> dict[str, list[Any]]:
    if not isinstance(container, dict):
        raise _error("P11_SUBMISSIONS_INVALID", "SEC filing rows must be a JSON object")
    arrays: dict[str, list[Any]] = {}
    lengths: set[int] = set()
    for key in _REQUIRED_ARRAYS:
        value = container.get(key)
        if not isinstance(value, list):
            raise _error("P11_SUBMISSIONS_INVALID", f"missing or invalid filing array: {key}")
        arrays[key] = value
        lengths.add(len(value))
    if len(lengths) != 1:
        raise _error("P11_SUBMISSIONS_INVALID", "SEC filing parallel arrays have different lengths")
    count = next(iter(lengths))
    if filing_count is not None and count != filing_count:
        raise _error("P11_SUBMISSIONS_INVALID", "historical filingCount does not match shard rows")
    return arrays


def _rows_from_arrays(
    arrays: dict[str, list[Any]],
    *,
    cik: str,
    source_url: str,
) -> list[SecDiscoveryCandidate]:
    count = len(arrays[_REQUIRED_ARRAYS[0]])
    result: list[SecDiscoveryCandidate] = []
    for index in range(count):
        accession = _normalize_accession_provider(arrays["accessionNumber"][index])
        filing_date = _date(arrays["filingDate"][index], "filingDate")
        report_date = _date(arrays["reportDate"][index], "reportDate", allow_empty=True)
        form, base_form, amended = _normalize_form_provider(arrays["form"][index])
        primary = _normalize_primary(arrays["primaryDocument"][index])
        description = _normalize_description(arrays["primaryDocDescription"][index])
        is_xbrl = _normalize_flag(arrays["isXBRL"][index], "isXBRL")
        is_inline = _normalize_flag(arrays["isInlineXBRL"][index], "isInlineXBRL")
        result.append(
            SecDiscoveryCandidate(
                cik=cik,
                accession_number=accession,
                form=form,
                base_form=base_form,
                amended=amended,
                filing_date=filing_date,  # type: ignore[arg-type]
                report_date=report_date,
                primary_document=primary,
                primary_doc_description=description,
                is_xbrl=is_xbrl,
                is_inline_xbrl=is_inline,
                submission_source_urls=(source_url,),
            )
        )
    return result


def load_sec_ticker_rows(client: SecHttpClient) -> tuple[tuple[str, str], ...]:
    response = client.get_json(_TICKER_URL, SecContentClass.TICKER_MAPPING_JSON)
    raw = _json_object(response.body)
    rows: set[tuple[str, str]] = set()
    for value in raw.values():
        if not isinstance(value, dict):
            raise _error("P11_SUBMISSIONS_INVALID", "ticker mapping row must be an object")
        for required in ("cik_str", "ticker", "title"):
            if required not in value:
                raise _error("P11_SUBMISSIONS_INVALID", f"ticker mapping row missing {required}")
        cik_raw = value["cik_str"]
        ticker_raw = value["ticker"]
        title_raw = value["title"]
        if type(cik_raw) is not int or not 1 <= cik_raw <= 9_999_999_999:
            raise _error("P11_SUBMISSIONS_INVALID", "ticker mapping cik_str must be an integer in range")
        if type(ticker_raw) is not str or type(title_raw) is not str:
            raise _error("P11_SUBMISSIONS_INVALID", "ticker mapping ticker/title must be strings")
        try:
            ticker = _normalize_ticker_provider(ticker_raw)
            cik = normalize_cik(str(cik_raw))
        except ValueError as exc:
            raise _error("P11_SUBMISSIONS_INVALID", "ticker mapping identity is invalid") from exc
        rows.add((ticker, cik))
    return tuple(sorted(rows, key=lambda row: (row[0], row[1])))


def _validate_shard_name(value: object) -> str:
    if type(value) is not str:
        raise _error("P11_SUBMISSIONS_INVALID", "historical shard name must be a string")
    if not value.endswith(".json"):
        raise _error("P11_SUBMISSIONS_INVALID", "historical shard name is invalid")
    if not value or value in {".", ".."} or any(ch in value for ch in "/\\?#"):
        raise _error("P11_SUBMISSIONS_INVALID", "historical shard name is invalid")
    if any(not 0x20 <= ord(ch) <= 0x7E for ch in value):
        raise _error("P11_SUBMISSIONS_INVALID", "historical shard name is invalid")
    return value


def _normalize_descriptors(files: object) -> tuple[tuple[str, str, str, int], ...]:
    if not isinstance(files, list):
        raise _error("P11_SUBMISSIONS_INVALID", "filings.files must be an array")
    by_name: dict[str, tuple[str, str, str, int]] = {}
    for raw in files:
        if not isinstance(raw, dict):
            raise _error("P11_SUBMISSIONS_INVALID", "historical shard descriptor must be an object")
        if not all(key in raw for key in ("name", "filingFrom", "filingTo", "filingCount")):
            raise _error("P11_SUBMISSIONS_INVALID", "historical shard descriptor is incomplete")
        name = _validate_shard_name(raw["name"])
        filing_from = _date(raw["filingFrom"], "filingFrom")
        filing_to = _date(raw["filingTo"], "filingTo")
        filing_count = raw["filingCount"]
        if type(filing_count) is not int or filing_count < 0:
            raise _error("P11_SUBMISSIONS_INVALID", "historical filingCount must be a non-negative integer")
        assert filing_from is not None and filing_to is not None
        if filing_from > filing_to:
            raise _error("P11_SUBMISSIONS_INVALID", "historical filingFrom must be <= filingTo")
        normalized = (name, filing_from, filing_to, filing_count)
        existing = by_name.get(name)
        if existing is not None and existing != normalized:
            raise _error("P11_SUBMISSIONS_INVALID", "same historical shard name has conflicting required metadata")
        by_name[name] = normalized
    return tuple(sorted(by_name.values(), key=lambda row: (row[1], row[2], row[0])))


def _normalize_target_forms(values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple or not values:
        raise ValueError("target_base_forms must be a non-empty tuple")
    normalized: set[str] = set()
    for value in values:
        try:
            normalized.add(normalize_sec_form(value).base_form)
        except (TypeError, ValueError) as exc:
            raise ValueError("target_base_forms contains an invalid SEC form") from exc
    return tuple(sorted(normalized))


def _input_date(value: str, field: str) -> str:
    if type(value) is not str or _DATE_RE.fullmatch(value) is None:
        raise ValueError(f"{field} must be YYYY-MM-DD")
    try:
        parsed = dt.date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be a valid calendar date") from exc
    if parsed.isoformat() != value:
        raise ValueError(f"{field} must be canonical YYYY-MM-DD")
    return value


def _merge_candidates(rows: Iterable[SecDiscoveryCandidate]) -> tuple[SecDiscoveryCandidate, ...]:
    by_accession: dict[str, SecDiscoveryCandidate] = {}
    for candidate in rows:
        existing = by_accession.get(candidate.accession_number)
        if existing is None:
            by_accession[candidate.accession_number] = candidate
            continue
        if existing != candidate:
            raise _error("P11_SUBMISSIONS_INVALID", "duplicate accession has conflicting semantic fields")
        urls = tuple(sorted(set(existing.submission_source_urls + candidate.submission_source_urls)))
        by_accession[candidate.accession_number] = SecDiscoveryCandidate(
            cik=existing.cik,
            accession_number=existing.accession_number,
            form=existing.form,
            base_form=existing.base_form,
            amended=existing.amended,
            filing_date=existing.filing_date,
            report_date=existing.report_date,
            primary_document=existing.primary_document,
            primary_doc_description=existing.primary_doc_description,
            is_xbrl=existing.is_xbrl,
            is_inline_xbrl=existing.is_inline_xbrl,
            submission_source_urls=urls,
        )
    return tuple(sorted(by_accession.values(), key=lambda row: (row.filing_date, row.accession_number)))


def discover_sec_filings(
    client: SecHttpClient,
    *,
    cik: str,
    target_base_forms: tuple[str, ...],
    filing_date_from: str,
    filing_date_to: str,
    target_accession: str | None = None,
) -> tuple[SecDiscoveryCandidate, ...]:
    try:
        normalized_cik = normalize_cik(cik)
    except (TypeError, ValueError) as exc:
        raise ValueError("cik is invalid") from exc
    forms = _normalize_target_forms(target_base_forms)
    date_from = _input_date(filing_date_from, "filing_date_from")
    date_to = _input_date(filing_date_to, "filing_date_to")
    if date_from > date_to:
        raise ValueError("filing_date_from must be <= filing_date_to")
    normalized_accession: str | None = None
    if target_accession is not None:
        try:
            normalized_accession = normalize_accession_number(target_accession)
        except (TypeError, ValueError) as exc:
            raise ValueError("target_accession is invalid") from exc

    current_url = f"https://data.sec.gov/submissions/CIK{normalized_cik}.json"
    current_response = client.get_json(current_url, SecContentClass.SUBMISSIONS_CURRENT_JSON)
    current = _json_object(current_response.body)
    if _normalize_cik_provider(current.get("cik")) != normalized_cik:
        raise _error("P11_SUBMISSIONS_INVALID", "Submissions cik does not match requested filer")
    filings = current.get("filings")
    if not isinstance(filings, dict):
        raise _error("P11_SUBMISSIONS_INVALID", "Submissions filings must be an object")
    recent = _parallel_arrays(filings.get("recent"))
    rows: list[SecDiscoveryCandidate] = _rows_from_arrays(recent, cik=normalized_cik, source_url=current_url)

    descriptors = _normalize_descriptors(filings.get("files"))
    for name, shard_from, shard_to, filing_count in descriptors:
        if shard_to < date_from or shard_from > date_to:
            continue
        shard_url = f"https://data.sec.gov/submissions/{name}"
        shard_response = client.get_json(shard_url, SecContentClass.SUBMISSIONS_HISTORY_JSON)
        shard = _json_object(shard_response.body)
        arrays = _parallel_arrays(shard, filing_count=filing_count)
        rows.extend(_rows_from_arrays(arrays, cik=normalized_cik, source_url=shard_url))

    merged = _merge_candidates(rows)
    filtered = tuple(
        row
        for row in merged
        if date_from <= row.filing_date <= date_to
        and row.base_form in forms
        and (normalized_accession is None or row.accession_number == normalized_accession)
    )
    if normalized_accession is not None:
        if len(filtered) != 1:
            raise _error("P11_FILING_NOT_FOUND", "requested SEC accession was not found")
    return filtered