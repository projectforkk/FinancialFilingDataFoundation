from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from .discovery import (
    SEC_MAX_HISTORY_CHUNKS,
    SecDiscoveryObservation,
    SecHistoryChunk,
    SecSubmissions,
    candidate_to_record,
    derive_discovery_decision,
    discover_filings,
    merge_filing_candidates,
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
                root_namespace = _xml_namespace(str(root.tag))
                return (
                    SecMemberRole.XBRL_INSTANCE
                    if root_local == "xbrl" and root_namespace == _XBRL_INSTANCE_NAMESPACE
                    else SecMemberRole.OTHER
                )
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


_XBRL_LINK_NAMESPACE = "http://www.xbrl.org/2003/linkbase"
_XBRL_INSTANCE_NAMESPACE = "http://www.xbrl.org/2003/instance"
_SEMANTIC_REFERENCE_TAGS = frozenset({"link:schemaref", "link:linkbaseref"})
_XBRL_MEMBER_ROLES = frozenset(
    {
        SecMemberRole.XBRL_INSTANCE,
        SecMemberRole.XBRL_SCHEMA,
        SecMemberRole.XBRL_PRESENTATION,
        SecMemberRole.XBRL_CALCULATION,
        SecMemberRole.XBRL_LABEL,
        SecMemberRole.XBRL_DEFINITION,
        SecMemberRole.XBRL_REFERENCE,
    }
)


class _SemanticReferenceHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.references: list[str] = []

    def _record(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if str(tag).casefold() not in _SEMANTIC_REFERENCE_TAGS:
            return
        normalized = {
            str(key).casefold(): "" if value is None else str(value)
            for key, value in attrs
        }
        reference = normalized.get("xlink:href") or normalized.get("href")
        if reference:
            self.references.append(reference)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._record(tag, attrs)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._record(tag, attrs)


def _xml_local_name(tag: str) -> str:
    text = str(tag)
    if text.startswith("{") and "}" in text:
        return text.split("}", 1)[1].casefold()
    return text.rsplit(":", 1)[-1].casefold()


def _xml_namespace(tag: str) -> str | None:
    text = str(tag)
    if text.startswith("{") and "}" in text:
        return text[1:].split("}", 1)[0]
    return None


def _xml_attribute_local(element: ET.Element, name: str) -> str | None:
    wanted = name.casefold()
    for key, value in element.attrib.items():
        text = str(key)
        if text.casefold() == wanted or text.rsplit("}", 1)[-1].rsplit(":", 1)[-1].casefold() == wanted:
            return str(value)
    return None


def _extract_semantic_xbrl_references(body: bytes, *, primary_html: bool) -> tuple[str, ...]:
    if primary_html:
        try:
            parser = _SemanticReferenceHTMLParser()
            parser.feed(body.decode("utf-8-sig"))
            parser.close()
        except (UnicodeDecodeError, AssertionError, ValueError):
            return ()
        return tuple(parser.references)

    try:
        root = ET.fromstring(body)
    except ET.ParseError:
        return ()
    references: list[str] = []
    for element in root.iter():
        if (
            _xml_namespace(str(element.tag)) != _XBRL_LINK_NAMESPACE
            or _xml_local_name(str(element.tag)) not in {"schemaref", "linkbaseref"}
        ):
            continue
        reference = _xml_attribute_local(element, "href")
        if reference:
            references.append(reference)
    return tuple(references)


def _canonical_semantic_reference(reference: str) -> str | None:
    clean = str(reference).split("#", 1)[0].split("?", 1)[0].strip()
    if not clean:
        return None
    try:
        return normalize_archive_relative_name(clean)
    except SecError:
        return None


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
        all_candidates = list(submissions.candidates)
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
            historical = parse_submissions(
                history_payload,
                company=company,
                source_url=history_url,
            )
            all_candidates.extend(historical.candidates)
        aggregate = SecSubmissions(
            company=company,
            candidates=merge_filing_candidates(all_candidates),
            fiscal_year_end=submissions.fiscal_year_end,
            history_files=submissions.history_files,
            history_ranges=submissions.history_ranges,
        )
        candidates = discover_filings(aggregate, fiscal_year=fiscal_year, period=period)
        rows = merge_filing_candidates(candidates)
        decision = derive_discovery_decision(rows)
        state = decision.state
        selected_accession = decision.selected_accession
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
        primary_url = archive_member_url(company.cik, candidate.accession, primary_name)
        primary_response = self.client.fetch(
            primary_url,
            expected_content_types=_content_types(primary_name),
            max_bytes=self.client.config.member_max_bytes,
        )
        _validate_source_bytes(primary_name, primary_response.body, "text/html", primary=True)
        primary_content_type = next(
            (
                str(value).split(";", 1)[0].strip().lower()
                for key, value in primary_response.headers.items()
                if str(key).casefold() == "content-type"
            ),
            _content_types(primary_name)[0],
        )
        members_by_name: dict[str, SecPackageMember] = {
            primary_name: SecPackageMember(
                relative_name=primary_name,
                role=SecMemberRole.PRIMARY_DOCUMENT,
                content_type=primary_content_type,
                source_url=primary_url,
                body=primary_response.body,
            )
        }
        accepted_xbrl_bodies: dict[str, tuple[SecMemberRole, bytes]] = {}
        while True:
            selected = _select_archive_members(
                items_by_name,
                primary_name=primary_name,
                primary_body=primary_response.body,
                accepted_member_bodies=accepted_xbrl_bodies,
            )
            pending = [name for name in selected if name not in members_by_name]
            if not pending:
                break
            for name in pending:
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
                _validate_source_bytes(name, member_response.body, content_type, primary=False)
                member = SecPackageMember(
                    relative_name=name,
                    role=_member_role(name, primary_name, member_response.body),
                    content_type=content_type,
                    source_url=member_url,
                    body=member_response.body,
                )
                members_by_name[name] = member
                if member.role in _XBRL_MEMBER_ROLES:
                    accepted_xbrl_bodies[name] = (member.role, member.body)
        members = [members_by_name[name] for name in selected]
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
    if len(chunks) > SEC_MAX_HISTORY_CHUNKS:
        raise SecError(
            P11Reason.P11_SEC_DISCOVERY_FAILED,
            f"SEC submissions history file count exceeds deterministic bound {SEC_MAX_HISTORY_CHUNKS}",
        )
    selected: list[SecHistoryChunk] = []
    seen_names: set[str] = set()
    for chunk in chunks:
        if chunk.name in seen_names:
            raise SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, f"SEC history chunk is duplicated: {chunk.name}")
        seen_names.add(chunk.name)
        parsed_from = None
        parsed_to = None
        if chunk.filing_from:
            try:
                parsed_from = date.fromisoformat(str(chunk.filing_from)[:10])
            except ValueError as exc:
                raise SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, f"SEC history chunk range is invalid: {chunk.name}") from exc
        if chunk.filing_to:
            try:
                parsed_to = date.fromisoformat(str(chunk.filing_to)[:10])
            except ValueError as exc:
                raise SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, f"SEC history chunk range is invalid: {chunk.name}") from exc
        if parsed_from is not None and parsed_to is not None and parsed_from > parsed_to:
            raise SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, f"SEC history chunk range is reversed: {chunk.name}")
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

def _select_archive_members(
    items_by_name: dict[str, dict[str, Any]],
    *,
    primary_name: str,
    primary_body: bytes | None,
    accepted_member_bodies: dict[str, tuple[SecMemberRole, bytes]] | None = None,
) -> list[str]:
    """Select filing members from independent metadata or semantic references."""

    selected: set[str] = {primary_name}
    for name, item in items_by_name.items():
        item_type = str(item.get("type") or item.get("documentType") or "").strip().upper()
        if item_type in _XBRL_INDEX_TYPES:
            selected.add(name)
        if name.casefold() == "filingsummary.xml":
            selected.add(name)
    semantic_sources: list[tuple[bytes, bool]] = []
    if primary_body is not None:
        semantic_sources.append((primary_body, True))
    for name, (role, body) in sorted(
        (accepted_member_bodies or {}).items(),
        key=lambda row: row[0].casefold(),
    ):
        if role in _XBRL_MEMBER_ROLES:
            semantic_sources.append((body, False))
    for body, primary_html in semantic_sources:
        for reference in _extract_semantic_xbrl_references(body, primary_html=primary_html):
            canonical_reference = _canonical_semantic_reference(reference)
            if canonical_reference is not None and canonical_reference in items_by_name:
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
