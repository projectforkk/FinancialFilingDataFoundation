from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from .discovery import (
    SecDiscoveryObservation,
    SecHistoryChunk,
    SecSubmissions,
    candidate_to_record,
    discover_filings,
    parse_submissions,
    select_filing,
)
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
    observation: SecDiscoveryObservation | None = None


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
            if lower.endswith((".xml", ".xbrl")):
                return SecMemberRole.XBRL_INSTANCE if root_local == "xbrl" else SecMemberRole.OTHER
        except ET.ParseError:
            pass
    if lower.endswith(".xml"):
        # Generic XML members (for example unrelated filing attachments) are
        # preserved as OTHER unless their root is the XBRL instance root.
        return SecMemberRole.OTHER
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
    def __init__(
        self,
        client: SecHttpClient,
        package_store: SecPackageStore,
        *,
        registry: Any | None = None,
        discovery_root: str | Path | None = None,
    ) -> None:
        self.client = client
        self.package_store = package_store
        self.registry = registry
        self.discovery_root = Path(discovery_root).expanduser().resolve() if discovery_root else None

    def _persist_observation(self, observation: SecDiscoveryObservation) -> SecDiscoveryObservation:
        if self.discovery_root is None:
            root = self.package_store.root.parent / "us" / "discovery"
        else:
            root = self.discovery_root
        root.mkdir(parents=True, exist_ok=True)
        target = root / f"{observation.observation_sha256}.json"
        payload = observation.to_dict()
        payload["artifact_path"] = str(target)
        if target.exists():
            try:
                existing = json.loads(target.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise SecError(P11Reason.P11_SOURCE_DRIFT, "SEC discovery observation artifact is invalid") from exc
            if existing != payload:
                raise SecError(P11Reason.P11_SOURCE_DRIFT, "SEC discovery observation artifact differs from immutable bytes")
        else:
            temp = target.with_suffix(f".{target.name}.tmp")
            temp.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            try:
                temp.replace(target)
            except FileExistsError:
                temp.unlink(missing_ok=True)
                existing = json.loads(target.read_text(encoding="utf-8"))
                if existing != payload:
                    raise SecError(P11Reason.P11_SOURCE_DRIFT, "SEC discovery observation artifact differs from immutable bytes")
        persisted = SecDiscoveryObservation(
            observation_sha256=observation.observation_sha256,
            company_id=observation.company_id,
            cik=observation.cik,
            fiscal_year=observation.fiscal_year,
            period=observation.period,
            retrieved_at=observation.retrieved_at,
            source_documents=observation.source_documents,
            candidates=observation.candidates,
            candidate_fingerprint=observation.candidate_fingerprint,
            selected_accession=observation.selected_accession,
            state=observation.state,
            artifact_path=str(target),
        )
        if self.registry is not None:
            self.registry.register_sec_discovery_observation(persisted)
        return persisted

    def _discover_with_candidates(
        self,
        company: SecCompanyRef,
        *,
        fiscal_year: int,
        period: str,
    ) -> tuple[SecDiscoveryObservation, tuple[SecFilingCandidate, ...]]:
        if not callable(getattr(self.client, "fetch", None)):
            raise SecError(P11Reason.P11_DISCOVERY_FRESHNESS_UNKNOWN, "SEC discovery client is unavailable")
        source_documents: list[dict[str, Any]] = []
        submissions_url = f"https://data.sec.gov/submissions/CIK{company.cik}.json"
        try:
            response = self.client.fetch(
                submissions_url,
                expected_content_types=("application/json",),
                max_bytes=self.client.config.submissions_max_bytes,
            )
        except Exception as exc:
            raise SecError(P11Reason.P11_DISCOVERY_FRESHNESS_UNKNOWN, "current SEC discovery could not be completed") from exc
        source_documents.append({"url": submissions_url, "body": response.body})
        try:
            payload = json.loads(response.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, "SEC submissions response is invalid JSON") from exc
        submissions = parse_submissions(
            payload,
            company=company,
            source_url=submissions_url,
            raw_sha256=source_documents[-1].get("sha256"),
        )
        candidates = discover_filings(submissions, fiscal_year=fiscal_year, period=period)
        if not candidates and submissions.history_files:
            historical_candidates = list(submissions.candidates)
            for chunk in _history_chunks_for_year(submissions, fiscal_year):
                history_url = f"https://data.sec.gov/submissions/{chunk.name}"
                try:
                    history_response = self.client.fetch(
                        history_url,
                        expected_content_types=("application/json",),
                        max_bytes=self.client.config.submissions_max_bytes,
                    )
                except Exception as exc:
                    raise SecError(P11Reason.P11_DISCOVERY_FRESHNESS_UNKNOWN, "SEC historical discovery could not be completed") from exc
                source_documents.append({"url": history_url, "body": history_response.body})
                try:
                    history_payload = json.loads(history_response.body.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
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
        rows = tuple(candidates)
        originals = tuple(row for row in rows if not row.amended)
        amendments = tuple(row for row in rows if row.amended)
        if not rows:
            state = "NOT_FOUND"
            selected_accession = None
        elif amendments:
            state = "AMENDED_VARIANT_PRESENT"
            selected_accession = originals[0].accession if len(originals) == 1 else None
        elif len(originals) != 1:
            state = "SLOT_CANDIDATE_CONFLICT"
            selected_accession = None
        else:
            state = "UNAMBIGUOUS"
            selected_accession = originals[0].accession
        observation = SecDiscoveryObservation.create(
            company=company,
            fiscal_year=fiscal_year,
            period=period,
            source_documents=source_documents,
            candidates=rows,
            selected_accession=selected_accession,
            state=state,
        )
        observation = self._persist_observation(observation)
        return observation, rows

    def discover(
        self,
        company: SecCompanyRef,
        *,
        fiscal_year: int,
        period: str,
    ) -> SecDiscoveryObservation:
        observation, _ = self._discover_with_candidates(
            company,
            fiscal_year=fiscal_year,
            period=period,
        )
        return observation

    def acquire(
        self,
        company: SecCompanyRef,
        *,
        fiscal_year: int,
        period: str,
        observation: SecDiscoveryObservation | None = None,
    ) -> SecAcquisitionResult:
        if observation is None:
            observation, candidates = self._discover_with_candidates(
                company,
                fiscal_year=fiscal_year,
                period=period,
            )
        else:
            candidates = tuple(_candidate_from_record(row, company) for row in observation.candidates)
        if observation.state != "UNAMBIGUOUS":
            reason = {
                "NOT_FOUND": P11Reason.P11_FILING_NOT_FOUND,
                "AMENDED_VARIANT_PRESENT": P11Reason.P11_AMENDED_VARIANT_PRESENT,
                "SLOT_CANDIDATE_CONFLICT": P11Reason.P11_SLOT_CANDIDATE_CONFLICT,
            }.get(observation.state, P11Reason.P11_DISCOVERY_FRESHNESS_UNKNOWN)
            raise SecError(reason, f"SEC discovery state is {observation.state}")
        candidate = select_filing(candidates)
        local_matches = self.package_store.find_all_by_slot(
            cik=company.cik,
            fiscal_year=fiscal_year,
            period=period,
        )
        local = next(
            (item for item in local_matches if item.accession == candidate.accession),
            None,
        )
        if local is not None:
            return SecAcquisitionResult(
                package=local,
                candidate=candidate,
                reused=True,
                plan_action="PARSE_LOCAL",
                observation=observation,
            )
        index_url = archive_member_url(company.cik, candidate.accession, "index.json")
        index_response = self.client.fetch(index_url, expected_content_types=("application/json",), max_bytes=self.client.config.submissions_max_bytes)
        try:
            index_payload = json.loads(index_response.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, "SEC archive index is invalid JSON") from exc
        if not isinstance(index_payload, dict) or not isinstance(index_payload.get("directory"), dict):
            raise SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, "SEC archive index directory is invalid")
        raw_items = index_payload["directory"].get("item")
        if not isinstance(raw_items, list):
            raise SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, "SEC archive index item list is invalid")
        items_by_name: dict[str, dict[str, Any]] = {}
        for item in raw_items:
            if not isinstance(item, dict) or not isinstance(item.get("name"), str):
                raise SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, "SEC archive index item is invalid")
            name = normalize_archive_relative_name(item["name"])
            items_by_name[name] = item
        primary_name = normalize_archive_relative_name(candidate.primary_document)
        selected = _select_archive_members(
            items_by_name,
            primary_name=primary_name,
            primary_body=None,
        )
        primary_url = archive_member_url(company.cik, candidate.accession, primary_name)
        primary_response = self.client.fetch(
            primary_url,
            expected_content_types=_content_types(primary_name),
            max_bytes=self.client.config.member_max_bytes,
        )
        _validate_source_bytes(primary_name, primary_response.body, "text/html", primary=True)
        selected = _select_archive_members(
            items_by_name,
            primary_name=primary_name,
            primary_body=primary_response.body,
        )
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
            member_response = primary_response if name == primary_name else self.client.fetch(
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
        return SecAcquisitionResult(
            package=package,
            candidate=candidate,
            reused=existed,
            observation=observation,
        )


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


_XBRL_INDEX_TYPES = frozenset(
    {
        "EX-101.INS",
        "EX-101.SCH",
        "EX-101.PRE",
        "EX-101.CAL",
        "EX-101.LAB",
        "EX-101.DEF",
        "EX-101.REF",
    }
)

_XBRL_REFERENCE_TYPES = frozenset(
    {
        "XBRL",
        "XBRL_INSTANCE",
        "XBRL_SCHEMA",
        "XBRL_PRESENTATION",
        "XBRL_CALCULATION",
        "XBRL_LABEL",
        "XBRL_DEFINITION",
        "XBRL_REFERENCE",
        "XBRL_LINKBASE",
        "XBRL_SUPPORT",
    }
)


def _is_semantic_xbrl_reference(item: dict[str, Any]) -> bool:
    item_type = str(item.get("type") or item.get("documentType") or "").strip().upper()
    return item_type in _XBRL_INDEX_TYPES or item_type in _XBRL_REFERENCE_TYPES


def _select_archive_members(
    items_by_name: dict[str, dict[str, Any]],
    *,
    primary_name: str,
    primary_body: bytes | None,
) -> list[str]:
    """Select only filing-local XBRL attachments proven by index/reference metadata."""

    selected: set[str] = {primary_name}
    for name, item in items_by_name.items():
        item_type = str(item.get("type") or item.get("documentType") or "").strip().upper()
        if item_type in _XBRL_INDEX_TYPES:
            selected.add(name)
        if name.casefold() == "filingsummary.xml":
            selected.add(name)
    if primary_body:
        text = primary_body.decode("utf-8-sig", errors="ignore")
        references = re.findall(
            r"(?:href|xlink:href|src)\s*=\s*['\"]([^'\"]+)['\"]",
            text,
            flags=re.IGNORECASE,
        )
        for reference in references:
            clean = reference.split("#", 1)[0].split("?", 1)[0].strip()
            if not clean:
                continue
            try:
                canonical_reference = normalize_archive_relative_name(clean)
            except SecError:
                continue
            item = items_by_name.get(canonical_reference)
            if item is not None and _is_semantic_xbrl_reference(item):
                selected.add(canonical_reference)
    return sorted(selected, key=str.casefold)


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


def _candidate_from_record(record: dict[str, Any], company: SecCompanyRef) -> SecFilingCandidate:
    try:
        issuer_kind = SecIssuerKind(str(record.get("issuer_kind") or SecIssuerKind.UNKNOWN.value))
    except ValueError:
        issuer_kind = SecIssuerKind.UNKNOWN
    return SecFilingCandidate(
        cik=company.cik,
        ticker=company.ticker,
        accession=str(record.get("accession") or ""),
        normalized_accession=str(record.get("normalized_accession") or ""),
        form=str(record.get("form") or ""),
        filing_date=str(record.get("filing_date") or ""),
        report_period=str(record.get("report_period")) if record.get("report_period") is not None else None,
        primary_document=str(record.get("primary_document") or ""),
        source_url=str(record.get("source_url") or ""),
        amended=bool(record.get("amended")),
        issuer_kind=issuer_kind,
    )


__all__ = ["SecAcquirer", "SecAcquisitionResult", "candidate_from_package"]
