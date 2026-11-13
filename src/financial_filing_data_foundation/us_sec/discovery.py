from __future__ import annotations

import base64
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping
from urllib.parse import urlsplit

from .errors import P11Reason, SecError
from .models import SecCompanyRef, SecFilingCandidate, SecIssuerKind
from .path_policy import archive_member_url, normalize_archive_relative_name
from .policy import SecFormPolicy


_ACCESSION_RE = re.compile(r"^\d{10}-\d{2}-\d{6}$")
SEC_DISCOVERY_SCHEMA = "p11-sec-discovery-v2"
SEC_MAX_HISTORY_CHUNKS = 256


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True, slots=True)
class SecHistoryChunk:
    name: str
    filing_from: str | None = None
    filing_to: str | None = None


@dataclass(frozen=True, slots=True)
class SecDiscoveryDecision:
    state: str
    selected_accession: str | None


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


def merge_filing_candidates(
    candidates: Iterable[SecFilingCandidate],
) -> tuple[SecFilingCandidate, ...]:
    """Merge official submissions rows without allowing accession drift."""

    by_accession: dict[str, SecFilingCandidate] = {}
    for candidate in candidates:
        accession = str(candidate.accession)
        previous = by_accession.get(accession)
        if previous is not None:
            if candidate_to_record(previous) != candidate_to_record(candidate):
                raise SecError(
                    P11Reason.P11_SEC_DISCOVERY_FAILED,
                    f"SEC accession has conflicting submissions metadata: {accession}",
                )
            continue
        by_accession[accession] = candidate
    return tuple(
        sorted(
            by_accession.values(),
            key=lambda item: (
                str(item.accession),
                str(item.form),
                str(item.filing_date),
                str(item.primary_document),
            ),
        )
    )


def derive_discovery_decision(
    candidates: Iterable[SecFilingCandidate],
) -> SecDiscoveryDecision:
    rows = merge_filing_candidates(candidates)
    originals = tuple(row for row in rows if not row.amended)
    amendments = tuple(row for row in rows if row.amended)
    if not rows:
        return SecDiscoveryDecision("NOT_FOUND", None)
    if amendments:
        return SecDiscoveryDecision(
            "AMENDED_VARIANT_PRESENT",
            originals[0].accession if len(originals) == 1 else None,
        )
    if len(originals) != 1:
        return SecDiscoveryDecision("SLOT_CANDIDATE_CONFLICT", None)
    return SecDiscoveryDecision("UNAMBIGUOUS", originals[0].accession)


def _canonical_candidate_records(
    candidates: Iterable[Mapping[str, Any]],
) -> tuple[dict[str, Any], ...]:
    rows = [dict(candidate) for candidate in candidates]
    rows.sort(
        key=lambda item: (
            str(item.get("accession") or ""),
            str(item.get("form") or ""),
            str(item.get("filing_date") or ""),
            str(item.get("primary_document") or ""),
        )
    )
    return tuple(rows)


def _candidate_fingerprint(candidates: Iterable[Mapping[str, Any]]) -> str:
    payload = json.dumps(
        list(_canonical_candidate_records(candidates)),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return _sha256(payload)


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
        normalized_candidates = _canonical_candidate_records(
            candidate_to_record(candidate) for candidate in candidates
        )
        candidate_fingerprint = _candidate_fingerprint(normalized_candidates)
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
            "candidates": list(_canonical_candidate_records(self.candidates)),
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

    @classmethod
    def from_registry_row(cls, row: Mapping[str, Any]) -> "SecDiscoveryObservation":
        try:
            source_documents = json.loads(str(row["source_documents_json"]))
            candidates = json.loads(str(row["candidates_json"]))
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise SecError(
                P11Reason.P11_PROVENANCE_MISMATCH,
                "SEC Registry discovery observation JSON is invalid",
            ) from exc
        if not isinstance(source_documents, list) or not isinstance(candidates, list):
            raise SecError(
                P11Reason.P11_PROVENANCE_MISMATCH,
                "SEC Registry discovery observation payload is invalid",
            )
        return cls(
            observation_sha256=str(row["observation_sha256"]).lower(),
            company_id=str(row["company_id"]),
            cik=str(row["cik"]),
            fiscal_year=int(row["fiscal_year"]),
            period=str(row["raw_fiscal_period"]).upper(),
            retrieved_at=str(row["retrieved_at"]),
            source_documents=tuple(source_documents),
            candidates=tuple(candidates),
            candidate_fingerprint=str(row["candidate_fingerprint"]),
            selected_accession=(
                str(row["selected_accession"])
                if row["selected_accession"] is not None
                else None
            ),
            state=str(row["state"]).upper(),
            artifact_path=(
                str(row["artifact_path"])
                if row["artifact_path"] is not None
                else None
            ),
        )


def _decode_observation_source(source: Mapping[str, Any]) -> tuple[str, bytes]:
    url = str(source.get("url") or source.get("source_url") or "").strip()
    source_sha256 = str(source.get("sha256") or source.get("source_sha256") or "").strip().lower()
    body_b64 = source.get("body_b64")
    if not url or not source_sha256 or not isinstance(body_b64, str) or not body_b64:
        raise SecError(
            P11Reason.P11_PROVENANCE_MISMATCH,
            "SEC discovery source URL/hash/body is not persisted",
        )
    try:
        body = base64.b64decode(body_b64, validate=True)
    except (ValueError, TypeError) as exc:
        raise SecError(
            P11Reason.P11_PROVENANCE_MISMATCH,
            "SEC discovery source bytes are invalid base64",
        ) from exc
    if _sha256(body) != source_sha256:
        raise SecError(
            P11Reason.P11_PROVENANCE_MISMATCH,
            "SEC discovery source bytes do not match recorded SHA256",
        )
    return url, body


def _decode_submissions_json(body: bytes, *, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SecError(
            P11Reason.P11_PROVENANCE_MISMATCH,
            f"SEC discovery {label} is not valid JSON",
        ) from exc
    if not isinstance(payload, dict):
        raise SecError(
            P11Reason.P11_PROVENANCE_MISMATCH,
            f"SEC discovery {label} JSON root is not an object",
        )
    return payload


def _reject_incomplete_rows_near_slot(
    submissions: SecSubmissions,
    fiscal_year: int,
) -> None:
    for row in submissions.incomplete_periodic_rows:
        report_period = row.get("report_period")
        if not report_period:
            raise SecError(
                P11Reason.P11_SEC_DISCOVERY_FAILED,
                "SEC history contains an incomplete periodic row without report period",
            )
        try:
            report_year = date.fromisoformat(str(report_period)[:10]).year
        except ValueError as exc:
            raise SecError(
                P11Reason.P11_SEC_DISCOVERY_FAILED,
                "SEC history contains an incomplete periodic row with invalid report period",
            ) from exc
        if fiscal_year - 1 <= report_year <= fiscal_year + 1:
            raise SecError(
                P11Reason.P11_SEC_DISCOVERY_FAILED,
                "SEC history contains an incomplete periodic row near the requested fiscal slot",
            )


def _reconstruct_discovery_candidates(
    observation: SecDiscoveryObservation,
) -> tuple[SecFilingCandidate, ...]:
    expected_main_url = f"https://data.sec.gov/submissions/CIK{observation.cik}.json"
    source_rows: dict[str, bytes] = {}
    for raw_source in observation.source_documents:
        if not isinstance(raw_source, Mapping):
            raise SecError(P11Reason.P11_PROVENANCE_MISMATCH, "SEC discovery source document is invalid")
        url, body = _decode_observation_source(raw_source)
        if url in source_rows:
            raise SecError(P11Reason.P11_PROVENANCE_MISMATCH, "SEC discovery source URL is duplicated")
        source_rows[url] = body
    if expected_main_url not in source_rows:
        raise SecError(
            P11Reason.P11_PROVENANCE_MISMATCH,
            "SEC discovery official current submissions source is missing",
        )
    parsed_main = urlsplit(expected_main_url)
    if (
        parsed_main.scheme != "https"
        or parsed_main.netloc != "data.sec.gov"
        or parsed_main.path != f"/submissions/CIK{observation.cik}.json"
    ):
        raise SecError(P11Reason.P11_PROVENANCE_MISMATCH, "SEC discovery current submissions URL is invalid")
    company = SecCompanyRef(
        cik=observation.cik,
        ticker="",
        company_id=observation.company_id,
    )
    main_body = source_rows[expected_main_url]
    main_payload = _decode_submissions_json(main_body, label="current submissions")
    main_submissions = parse_submissions(
        main_payload,
        company=company,
        source_url=expected_main_url,
        raw_sha256=_sha256(main_body),
    )
    selected_history = select_history_chunks_for_slot(
        main_submissions,
        int(observation.fiscal_year),
    )
    expected_history_urls = [
        f"https://data.sec.gov/submissions/{chunk.name}"
        for chunk in selected_history
    ]
    expected_urls = {expected_main_url, *expected_history_urls}
    if set(source_rows) != expected_urls:
        raise SecError(
            P11Reason.P11_PROVENANCE_MISMATCH,
            "SEC discovery retained source set differs from official submissions files",
        )
    candidates: list[SecFilingCandidate] = list(main_submissions.candidates)
    incomplete_periodic_rows: list[dict[str, str | None]] = list(
        main_submissions.incomplete_periodic_rows
    )
    for history_url in expected_history_urls:
        parsed_url = urlsplit(history_url)
        if (
            parsed_url.scheme != "https"
            or parsed_url.netloc != "data.sec.gov"
            or parsed_url.path != f"/submissions/{parsed_url.path.rsplit('/', 1)[-1]}"
            or parsed_url.query
            or parsed_url.fragment
        ):
            raise SecError(P11Reason.P11_PROVENANCE_MISMATCH, "SEC discovery history submissions URL is invalid")
        body = source_rows[history_url]
        payload = _decode_submissions_json(body, label=f"history submissions {history_url}")
        history = parse_submissions(
            payload,
            company=company,
            source_url=history_url,
            raw_sha256=_sha256(body),
            allow_incomplete_periodic_rows=True,
        )
        candidates.extend(history.candidates)
        if history.incomplete_periodic_rows:
            incomplete_periodic_rows.extend(history.incomplete_periodic_rows)
    merged = merge_filing_candidates(candidates)
    aggregate = SecSubmissions(
        company=company,
        candidates=merged,
        fiscal_year_end=main_submissions.fiscal_year_end,
        incomplete_periodic_rows=tuple(incomplete_periodic_rows),
    )
    _reject_incomplete_rows_near_slot(aggregate, int(observation.fiscal_year))
    return merge_filing_candidates(
        discover_filings(
            aggregate,
            fiscal_year=int(observation.fiscal_year),
            period=str(observation.period),
        )
    )


def verify_sec_discovery_observation(
    observation: SecDiscoveryObservation,
    *,
    package: Any | None = None,
    registry_row: Mapping[str, Any] | None = None,
    expected_company_id: str | None = None,
    expected_cik: str | None = None,
    expected_fiscal_year: int | None = None,
    expected_period: str | None = None,
    expected_accession: str | None = None,
    expected_observation_sha256: str | None = None,
) -> None:
    """Verify the persisted SEC discovery observation trust boundary.

    This check intentionally re-hashes the observation and its persisted source
    bytes.  A recorded SHA or Registry row is not accepted as proof by itself.
    """

    if not isinstance(observation, SecDiscoveryObservation):
        raise SecError(
            P11Reason.P11_PROVENANCE_MISMATCH,
            "SEC discovery observation has an unsupported type",
        )

    if package is not None:
        expected_cik = expected_cik or str(package.cik)
        expected_company_id = expected_company_id or f"US:CIK{package.cik}"
        expected_fiscal_year = expected_fiscal_year or int(package.fiscal_year)
        expected_period = expected_period or str(package.period)
        expected_accession = expected_accession or str(package.accession)

    if not re.fullmatch(r"\d{10}", str(observation.cik)):
        raise SecError(P11Reason.P11_PROVENANCE_MISMATCH, "SEC discovery observation CIK is invalid")
    if not re.fullmatch(r"US:CIK\d{10}", str(observation.company_id)):
        raise SecError(P11Reason.P11_PROVENANCE_MISMATCH, "SEC discovery observation company_id is not stable CIK identity")
    if str(observation.company_id) != f"US:CIK{observation.cik}":
        raise SecError(P11Reason.P11_PROVENANCE_MISMATCH, "SEC discovery observation company_id/CIK mismatch")
    if expected_cik is not None and str(observation.cik) != str(expected_cik).zfill(10):
        raise SecError(P11Reason.P11_PROVENANCE_MISMATCH, "SEC discovery observation CIK differs from expected slot")
    if expected_company_id is not None and str(observation.company_id) != str(expected_company_id):
        raise SecError(P11Reason.P11_PROVENANCE_MISMATCH, "SEC discovery observation company_id differs from expected slot")
    if expected_fiscal_year is not None and int(observation.fiscal_year) != int(expected_fiscal_year):
        raise SecError(P11Reason.P11_PROVENANCE_MISMATCH, "SEC discovery observation fiscal_year differs from expected slot")
    if expected_period is not None and str(observation.period).upper() != str(expected_period).upper():
        raise SecError(P11Reason.P11_PROVENANCE_MISMATCH, "SEC discovery observation period differs from expected slot")

    reconstructed_candidates = _reconstruct_discovery_candidates(observation)
    reconstructed_records = _canonical_candidate_records(
        candidate_to_record(candidate) for candidate in reconstructed_candidates
    )
    observed_records = _canonical_candidate_records(observation.candidates)
    if reconstructed_records != observed_records:
        raise SecError(
            P11Reason.P11_PROVENANCE_MISMATCH,
            "SEC discovery candidates differ from independent submissions reconstruction",
        )
    decision = derive_discovery_decision(reconstructed_candidates)
    if str(observation.state).upper() != decision.state:
        raise SecError(
            P11Reason.P11_PROVENANCE_MISMATCH,
            "SEC discovery state differs from independent submissions reconstruction",
        )
    if observation.selected_accession != decision.selected_accession:
        raise SecError(
            P11Reason.P11_PROVENANCE_MISMATCH,
            "SEC discovery selected accession differs from independent submissions reconstruction",
        )
    if str(observation.state).upper() != "UNAMBIGUOUS":
        raise SecError(
            P11Reason.P11_DISCOVERY_FRESHNESS_UNKNOWN,
            "SEC discovery observation is not UNAMBIGUOUS",
        )
    if not observation.selected_accession:
        raise SecError(
            P11Reason.P11_DISCOVERY_FRESHNESS_UNKNOWN,
            "SEC discovery observation has no selected accession",
        )
    if expected_accession is not None and str(observation.selected_accession) != str(expected_accession):
        raise SecError(P11Reason.P11_PROVENANCE_MISMATCH, "SEC discovery selected accession differs from package")

    if package is not None:
        selected = next(
            (
                candidate
                for candidate in reconstructed_candidates
                if candidate.accession == observation.selected_accession
            ),
            None,
        )
        if selected is None:
            raise SecError(
                P11Reason.P11_PROVENANCE_MISMATCH,
                "SEC selected accession is not present in reconstructed candidates",
            )
        if str(package.form).upper() != str(selected.form).upper():
            raise SecError(P11Reason.P11_PROVENANCE_MISMATCH, "SEC package form differs from selected candidate")
        if package.primary_document and str(package.primary_document) != str(selected.primary_document):
            raise SecError(P11Reason.P11_PROVENANCE_MISMATCH, "SEC package primary document differs from selected candidate")
        if package.report_period and str(package.report_period) != str(selected.report_period):
            raise SecError(P11Reason.P11_PROVENANCE_MISMATCH, "SEC package report period differs from selected candidate")

    computed_fingerprint = _candidate_fingerprint(observation.candidates)
    if computed_fingerprint != str(observation.candidate_fingerprint).lower():
        raise SecError(
            P11Reason.P11_PROVENANCE_MISMATCH,
            "SEC discovery candidate fingerprint mismatch",
        )
    computed_observation_sha256 = _sha256(
        json.dumps(
            observation.canonical_payload(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )
    if computed_observation_sha256 != str(observation.observation_sha256).lower():
        raise SecError(
            P11Reason.P11_PROVENANCE_MISMATCH,
            "SEC discovery observation canonical SHA256 mismatch",
        )
    if expected_observation_sha256 is not None and str(observation.observation_sha256).lower() != str(expected_observation_sha256).lower():
        raise SecError(
            P11Reason.P11_PROVENANCE_MISMATCH,
            "SEC discovery observation SHA256 differs from expected binding",
        )

    if registry_row is not None:
        try:
            registry_sources = json.loads(str(registry_row["source_documents_json"]))
            registry_candidates = json.loads(str(registry_row["candidates_json"]))
            registry_values = (
                str(registry_row["observation_sha256"]).lower(),
                str(registry_row["company_id"]),
                str(registry_row["cik"]),
                int(registry_row["fiscal_year"]),
                str(registry_row["raw_fiscal_period"]).upper(),
                str(registry_row["retrieved_at"]),
                json.dumps(registry_sources, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
                json.dumps(registry_candidates, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
                str(registry_row["candidate_fingerprint"]),
                registry_row["selected_accession"],
                str(registry_row["state"]).upper(),
                registry_row["artifact_path"],
            )
            observation_values = (
                str(observation.observation_sha256).lower(),
                str(observation.company_id),
                str(observation.cik),
                int(observation.fiscal_year),
                str(observation.period).upper(),
                str(observation.retrieved_at),
                json.dumps(list(observation.source_documents), ensure_ascii=False, sort_keys=True, separators=(",", ":")),
                json.dumps(list(observation.candidates), ensure_ascii=False, sort_keys=True, separators=(",", ":")),
                str(observation.candidate_fingerprint),
                observation.selected_accession,
                str(observation.state).upper(),
                observation.artifact_path,
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise SecError(
                P11Reason.P11_PROVENANCE_MISMATCH,
                "SEC Registry discovery observation is invalid",
            ) from exc
        if registry_values != observation_values:
            raise SecError(
                P11Reason.P11_PROVENANCE_MISMATCH,
                "SEC Registry discovery observation differs from supplied observation",
            )


@dataclass(frozen=True, slots=True)
class SecSubmissions:
    company: SecCompanyRef
    candidates: tuple[SecFilingCandidate, ...]
    history_files: tuple[str, ...] = ()
    fiscal_year_end: str | None = None
    raw_sha256: str | None = None
    source_url: str | None = None
    history_ranges: tuple[SecHistoryChunk, ...] = ()
    incomplete_periodic_rows: tuple[dict[str, str | None], ...] = ()

    @property
    def history_chunks(self) -> tuple[SecHistoryChunk, ...]:
        if self.history_ranges:
            return self.history_ranges
        return tuple(SecHistoryChunk(name) for name in self.history_files)


def select_history_chunks_for_slot(
    submissions: SecSubmissions,
    fiscal_year: int,
) -> tuple[SecHistoryChunk, ...]:
    """Return the complete but minimal SEC history source set for one slot.

    A periodic filing for fiscal year Y may have a report period in Y-1, while
    amendments/conflicts can be filed arbitrarily later.  Therefore only
    chunks whose filingTo proves they ended before Jan 1 of Y-1 are excluded.
    Missing range metadata is conservatively included.
    """

    chunks = submissions.history_chunks
    if not chunks:
        return ()
    if len(chunks) > SEC_MAX_HISTORY_CHUNKS:
        raise SecError(
            P11Reason.P11_SEC_DISCOVERY_FAILED,
            f"SEC submissions history file count exceeds deterministic bound {SEC_MAX_HISTORY_CHUNKS}",
        )
    earliest_possible = date(int(fiscal_year) - 1, 1, 1)
    selected: list[SecHistoryChunk] = []
    seen_names: set[str] = set()
    for chunk in chunks:
        if chunk.name in seen_names:
            raise SecError(
                P11Reason.P11_SEC_DISCOVERY_FAILED,
                f"SEC history chunk is duplicated: {chunk.name}",
            )
        seen_names.add(chunk.name)
        parsed_from: date | None = None
        parsed_to: date | None = None
        if chunk.filing_from:
            try:
                parsed_from = date.fromisoformat(str(chunk.filing_from)[:10])
            except ValueError as exc:
                raise SecError(
                    P11Reason.P11_SEC_DISCOVERY_FAILED,
                    f"SEC history chunk range is invalid: {chunk.name}",
                ) from exc
        if chunk.filing_to:
            try:
                parsed_to = date.fromisoformat(str(chunk.filing_to)[:10])
            except ValueError as exc:
                raise SecError(
                    P11Reason.P11_SEC_DISCOVERY_FAILED,
                    f"SEC history chunk range is invalid: {chunk.name}",
                ) from exc
        if parsed_from is not None and parsed_to is not None and parsed_from > parsed_to:
            raise SecError(
                P11Reason.P11_SEC_DISCOVERY_FAILED,
                f"SEC history chunk range is reversed: {chunk.name}",
            )
        if parsed_to is not None and parsed_to < earliest_possible:
            continue
        selected.append(chunk)
    return tuple(sorted(selected, key=lambda item: item.name))


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
    allow_incomplete_periodic_rows: bool = False,
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
    incomplete_periodic_rows: list[dict[str, str | None]] = []
    for index, raw_accession in enumerate(accessions):
        if not isinstance(raw_accession, str) or not _ACCESSION_RE.fullmatch(raw_accession):
            raise SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, "SEC accession is invalid")
        form = _array(recent, "form", index)
        filing_date = _array(recent, "filingDate", index)
        primary_document = _array(
            recent,
            "primaryDocument",
            index,
            required=not allow_incomplete_periodic_rows,
        )
        report_period = _array(recent, "reportPeriod", index, required=False)
        if report_period is None:
            report_period = _array(recent, "reportDate", index, required=False)
        if not isinstance(form, str) or not isinstance(filing_date, str):
            raise SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, "SEC filing metadata is invalid")
        # Non-periodic submissions can legitimately carry unrelated nested
        # documents. They are not candidates for the P11 periodic provider, so
        # do not construct or validate an archive URL for them.
        if SecFormPolicy.base_form(form) not in {"10-K", "10-Q", "20-F", "40-F"}:
            continue
        if not isinstance(primary_document, str) or not primary_document.strip():
            if allow_incomplete_periodic_rows:
                incomplete_periodic_rows.append(
                    {
                        "accession": raw_accession,
                        "form": form.strip().upper(),
                        "filing_date": filing_date.strip(),
                        "report_period": (
                            report_period.strip()
                            if isinstance(report_period, str) and report_period.strip()
                            else None
                        ),
                        "primary_document": (
                            primary_document.strip()
                            if isinstance(primary_document, str)
                            else None
                        ),
                    }
                )
                continue
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
        incomplete_periodic_rows=tuple(incomplete_periodic_rows),
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
    "SEC_MAX_HISTORY_CHUNKS",
    "SecDiscoveryDecision",
    "SecDiscoveryObservation",
    "SecHistoryChunk",
    "SecSubmissions",
    "candidate_to_record",
    "derive_discovery_decision",
    "discover_filings",
    "merge_filing_candidates",
    "parse_submissions",
    "select_filing",
    "select_history_chunks_for_slot",
    "verify_sec_discovery_observation",
]
