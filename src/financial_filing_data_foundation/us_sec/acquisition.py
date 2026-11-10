from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date
from html.parser import HTMLParser

from .discovery import SecHistoryChunk, SecSubmissions, discover_filings, parse_submissions, select_filing
from .errors import P11Reason, SecError
from .http import SecHttpClient
from .models import SecCompanyRef, SecFilingCandidate, SecIssuerKind
from .package import SecFilingPackage, SecMemberRole, SecPackageMember, SecPackageStore, build_package
from .path_policy import archive_member_url, archive_url_is_exact, normalize_archive_relative_name
from .policy import SecFormPolicy


@dataclass(frozen=True, slots=True)
class SecAcquisitionResult:
    package: SecFilingPackage
    candidate: SecFilingCandidate
    reused: bool
    plan_action: str = "DISCOVER_AND_ACQUIRE"


def _content_types(relative_name: str) -> tuple[str, ...]:
    lower = relative_name.casefold()
    if lower.endswith((".htm", ".html", ".xhtml")):
        return ("text/html", "application/xhtml+xml")
    if lower.endswith(".json"):
        return ("application/json", "text/json")
    if lower.endswith((".xml", ".xsd", ".xbrl")):
        return ("application/xml", "text/xml", "application/xhtml+xml")
    return ("application/octet-stream", "application/pdf", "text/plain")


def _member_role(name: str, primary: str, body: bytes | None = None) -> SecMemberRole:
    lower = name.casefold()
    if name == primary:
        return SecMemberRole.PRIMARY_DOCUMENT
    if lower == "filingsummary.xml":
        return SecMemberRole.FILING_SUMMARY
    if lower.endswith(".xsd"):
        return SecMemberRole.XBRL_SCHEMA
    if lower.endswith("_pre.xml"):
        return SecMemberRole.XBRL_PRESENTATION
    if lower.endswith("_cal.xml"):
        return SecMemberRole.XBRL_CALCULATION
    if lower.endswith("_lab.xml"):
        return SecMemberRole.XBRL_LABEL
    if lower.endswith("_def.xml"):
        return SecMemberRole.XBRL_DEFINITION
    if lower.endswith("_ref.xml"):
        return SecMemberRole.XBRL_REFERENCE
    if body:
        try:
            root = ET.fromstring(body)
            root_local = str(root.tag).rsplit("}", 1)[-1].casefold()
            if root_local == "linkbase":
                return SecMemberRole.OTHER
            if lower.endswith(".xml"):
                return SecMemberRole.XBRL_INSTANCE if root_local == "xbrl" else SecMemberRole.OTHER
        except ET.ParseError:
            pass
    if lower.endswith(".xml"):
        # Generic XML members (for example unrelated filing attachments) are
        # preserved as OTHER unless their root is the XBRL instance root.
        return SecMemberRole.OTHER
    if lower.endswith(".xbrl"):
        return SecMemberRole.XBRL_INSTANCE
    return SecMemberRole.OTHER


def _validate_source_bytes(name: str, body: bytes, content_type: str, *, primary: bool) -> None:
    if not body:
        raise SecError(P11Reason.P11_CONTENT_TYPE_INVALID, f"SEC member is empty: {name}")
    lower = name.casefold()
    if primary or lower.endswith((".htm", ".html", ".xhtml")):
        try:
            text = body.decode("utf-8-sig")
            parser = HTMLParser(convert_charrefs=True)
            parser.feed(text)
            parser.close()
        except (UnicodeDecodeError, AssertionError, ValueError) as exc:
            raise SecError(P11Reason.P11_CONTENT_TYPE_INVALID, f"SEC primary HTML bytes are invalid: {name}") from exc
        if "<html" not in text.casefold():
            raise SecError(P11Reason.P11_CONTENT_TYPE_INVALID, f"SEC primary member is not HTML: {name}")
        return
    if lower.endswith((".xml", ".xsd", ".xbrl")) or content_type in {"application/xml", "text/xml"}:
        try:
            ET.fromstring(body)
        except ET.ParseError as exc:
            raise SecError(P11Reason.P11_CONTENT_TYPE_INVALID, f"SEC XML member bytes are invalid: {name}") from exc


class SecAcquirer:
    def __init__(self, client: SecHttpClient, package_store: SecPackageStore) -> None:
        self.client = client
        self.package_store = package_store

    def acquire(
        self,
        company: SecCompanyRef,
        *,
        fiscal_year: int,
        period: str,
    ) -> SecAcquisitionResult:
        local = self.package_store.find_by_slot(
            cik=company.cik,
            fiscal_year=fiscal_year,
            period=period,
        )
        if local is not None:
            return SecAcquisitionResult(
                package=local,
                candidate=candidate_from_package(local, company),
                reused=True,
                plan_action="REUSE_DATA" if local.period.upper() == str(period).upper() else "PARSE_LOCAL",
            )
        submissions_url = f"https://data.sec.gov/submissions/CIK{company.cik}.json"
        response = self.client.fetch(
            submissions_url,
            expected_content_types=("application/json",),
            max_bytes=self.client.config.submissions_max_bytes,
        )
        try:
            payload = json.loads(response.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            from .errors import P11Reason, SecError

            raise SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, "SEC submissions response is invalid JSON") from exc
        submissions = parse_submissions(payload, company=company, source_url=submissions_url)
        candidates = discover_filings(submissions, fiscal_year=fiscal_year, period=period)
        if not candidates and submissions.history_files:
            historical_candidates = list(submissions.candidates)
            for chunk in _history_chunks_for_year(submissions, fiscal_year):
                history_name = chunk.name
                history_url = f"https://data.sec.gov/submissions/{history_name}"
                history_response = self.client.fetch(
                    history_url,
                    expected_content_types=("application/json",),
                    max_bytes=self.client.config.submissions_max_bytes,
                )
                try:
                    history_payload = json.loads(history_response.body.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    from .errors import P11Reason, SecError

                    raise SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, "SEC historical submissions response is invalid JSON") from exc
                historical = parse_submissions(history_payload, company=company, source_url=history_url)
                historical_candidates.extend(historical.candidates)
                candidates = discover_filings(
                    SecSubmissions(
                        company=company,
                        candidates=tuple(historical_candidates),
                        fiscal_year_end=submissions.fiscal_year_end or historical.fiscal_year_end,
                        history_files=submissions.history_files,
                        history_ranges=submissions.history_ranges,
                    ),
                    fiscal_year=fiscal_year,
                    period=period,
                )
                if candidates:
                    break
        candidate = select_filing(candidates)
        existing = self.package_store.find_by_accession(candidate.accession)
        if existing is not None:
            return SecAcquisitionResult(package=existing, candidate=candidate, reused=True)
        index_url = archive_member_url(company.cik, candidate.accession, "index.json")
        index_response = self.client.fetch(index_url, expected_content_types=("application/json",), max_bytes=self.client.config.submissions_max_bytes)
        try:
            index_payload = json.loads(index_response.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            from .errors import P11Reason, SecError

            raise SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, "SEC archive index is invalid JSON") from exc
        if not isinstance(index_payload, dict) or not isinstance(index_payload.get("directory"), dict):
            raise SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, "SEC archive index directory is invalid")
        raw_items = index_payload["directory"].get("item")
        if not isinstance(raw_items, list):
            raise SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, "SEC archive index item list is invalid")
        names: list[str] = []
        for item in raw_items:
            if not isinstance(item, dict) or not isinstance(item.get("name"), str):
                raise SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, "SEC archive index item is invalid")
            names.append(normalize_archive_relative_name(item["name"]))
        selected = [normalize_archive_relative_name(candidate.primary_document)]
        for name in sorted(set(names), key=str.casefold):
            lower = name.casefold()
            if name == candidate.primary_document:
                continue
            if lower.endswith((".xsd", ".xml", ".xbrl")):
                selected.append(name)
        members: list[SecPackageMember] = []
        for name in selected:
            member_url = archive_member_url(company.cik, candidate.accession, name)
            if not archive_url_is_exact(
                member_url,
                cik=company.cik,
                accession=candidate.accession,
                relative_name=name,
            ):
                raise SecError(P11Reason.P11_ARCHIVE_HOST_REJECTED, "SEC archive member escaped exact accession root")
            member_response = self.client.fetch(
                member_url,
                expected_content_types=_content_types(name),
                max_bytes=self.client.config.member_max_bytes,
            )
            content_type = next(
                (
                    str(value).split(";", 1)[0].strip().lower()
                    for key, value in member_response.headers.items()
                    if str(key).casefold() == "content-type"
                ),
                _content_types(name)[0],
            )
            _validate_source_bytes(name, member_response.body, content_type, primary=name == candidate.primary_document)
            members.append(
                SecPackageMember(
                    relative_name=name,
                    role=_member_role(name, candidate.primary_document, member_response.body),
                    content_type=content_type,
                    source_url=member_url,
                    body=member_response.body,
                )
            )
        package = build_package(
            cik=company.cik,
            accession=candidate.accession,
            form=candidate.form,
            fiscal_year=fiscal_year,
            period=period,
            members=members,
            filing_date=candidate.filing_date,
            report_period=candidate.report_period,
            primary_document=candidate.primary_document,
        )
        existed = self.package_store.package_dir(package.package_sha256).exists()
        self.package_store.put(package)
        return SecAcquisitionResult(package=package, candidate=candidate, reused=existed)


def _history_chunks_for_year(submissions: SecSubmissions, fiscal_year: int) -> tuple[SecHistoryChunk, ...]:
    chunks = submissions.history_chunks
    if not chunks:
        return ()
    selected: list[SecHistoryChunk] = []
    lower_bound = fiscal_year - 1
    upper_bound = fiscal_year + 1
    for chunk in chunks:
        if not chunk.filing_from or not chunk.filing_to:
            # Without both official range endpoints we cannot prove that a
            # chunk can contain the requested filing year.  Do not turn an
            # incomplete metadata row into an unbounded network fetch.
            continue
        try:
            from_date = date.fromisoformat(str(chunk.filing_from)[:10])
            to_date = date.fromisoformat(str(chunk.filing_to)[:10])
        except ValueError as exc:
            raise SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, f"SEC history chunk range is invalid: {chunk.name}") from exc
        if from_date > to_date:
            raise SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, f"SEC history chunk range is reversed: {chunk.name}")
        from_year = from_date.year
        to_year = to_date.year
        if from_year <= upper_bound and to_year >= lower_bound:
            selected.append(chunk)
    return tuple(sorted(selected, key=lambda item: item.name))


def candidate_from_package(package: SecFilingPackage, company: SecCompanyRef) -> SecFilingCandidate:
    primary = next(member for member in package.members if member.role is SecMemberRole.PRIMARY_DOCUMENT)
    base_form = SecFormPolicy.base_form(package.form)
    kind = (
        SecIssuerKind.FPI
        if base_form in {"20-F", "40-F"}
        else SecIssuerKind.DOMESTIC
        if base_form in {"10-K", "10-Q"}
        else SecIssuerKind.UNKNOWN
    )
    return SecFilingCandidate(
        cik=company.cik,
        ticker=company.ticker,
        accession=package.accession,
        normalized_accession=package.accession.replace("-", ""),
        form=package.form,
        filing_date=package.filing_date or "",
        report_period=package.report_period,
        primary_document=package.primary_document or primary.relative_name,
        source_url=primary.source_url,
        amended=package.form.endswith("/A"),
        issuer_kind=kind,
    )


__all__ = ["SecAcquirer", "SecAcquisitionResult", "candidate_from_package"]
