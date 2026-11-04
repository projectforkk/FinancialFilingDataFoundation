from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from financial_filing_data_foundation.mcp import (
    McpCatalog,
    McpQueryService,
    McpServiceError,
)
from financial_filing_data_foundation.review import (
    ReviewError,
    load_resolved_snapshot,
)

from .context import (
    CAPABILITY_MANIFEST_V1,
    CONTEXT_SCHEMA_VERSION,
    INTEGRATION_POLICY_VERSION,
    ResearchContext,
    _accepted_p8_contract,
    _accepted_p9_contract,
    _canonical_review_root,
    _catalog_identity,
    _context_project_root,
    _fingerprint,
    _research_context_id,
)
from .models import P10Error, ResearchSpecBundle
from .spec import _canonical_json_bytes, verify_research_spec


LEDGER_SCHEMA_VERSION = "p10-research-evidence-ledger-v1"
PROVENANCE_VALIDATION_SCHEMA_VERSION = "p10-provenance-validation-v1"

P8_RAW_DIRECT = "P8_RAW_DIRECT"
RUN_LOCAL_STRUCTURED_VERIFIED = "RUN_LOCAL_STRUCTURED_VERIFIED"
P9_DURABLE_RESOLVED = "P9_DURABLE_RESOLVED"
UNRESOLVED = "UNRESOLVED"

USE_CLASSES_V1 = (
    P8_RAW_DIRECT,
    RUN_LOCAL_STRUCTURED_VERIFIED,
    P9_DURABLE_RESOLVED,
    UNRESOLVED,
)

_MAX_LEDGER_ENTRIES = 1000
_MAX_CLAIM_KEY_LENGTH = 256
_MAX_EXPLICIT_REFS_PER_ENTRY = 1000
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class EvidenceLedgerEntry:
    claim_key: str
    use_class: str
    document_sha256: str | None = None
    page_nos: tuple[int, ...] = ()
    table_ids: tuple[str, ...] = ()
    raw_fact_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    p9_resolution_ids: tuple[str, ...] = ()
    overlay_set_hash: str | None = None
    semantic_assertions: Mapping[str, Any] = field(default_factory=dict)
    derived_from_claim_keys: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_key": self.claim_key,
            "use_class": self.use_class,
            "document_sha256": self.document_sha256,
            "page_nos": sorted(self.page_nos),
            "table_ids": sorted(self.table_ids),
            "raw_fact_ids": sorted(self.raw_fact_ids),
            "evidence_ids": sorted(self.evidence_ids),
            "p9_resolution_ids": sorted(self.p9_resolution_ids),
            "overlay_set_hash": self.overlay_set_hash,
            "semantic_assertions": _copy_json_object(self.semantic_assertions),
            "derived_from_claim_keys": sorted(self.derived_from_claim_keys),
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "EvidenceLedgerEntry":
        if not isinstance(raw, Mapping):
            _raise_invalid("evidence ledger entry must be an object")
        expected = {
            "claim_key",
            "use_class",
            "document_sha256",
            "page_nos",
            "table_ids",
            "raw_fact_ids",
            "evidence_ids",
            "p9_resolution_ids",
            "overlay_set_hash",
            "semantic_assertions",
            "derived_from_claim_keys",
        }
        if set(raw) != expected:
            _raise_invalid("evidence ledger entry fields are invalid")
        return cls(
            claim_key=raw.get("claim_key"),
            use_class=raw.get("use_class"),
            document_sha256=raw.get("document_sha256"),
            page_nos=_tuple_from_list(raw.get("page_nos"), "page_nos"),
            table_ids=_tuple_from_list(raw.get("table_ids"), "table_ids"),
            raw_fact_ids=_tuple_from_list(raw.get("raw_fact_ids"), "raw_fact_ids"),
            evidence_ids=_tuple_from_list(raw.get("evidence_ids"), "evidence_ids"),
            p9_resolution_ids=_tuple_from_list(
                raw.get("p9_resolution_ids"), "p9_resolution_ids"
            ),
            overlay_set_hash=raw.get("overlay_set_hash"),
            semantic_assertions=_mapping_from_value(
                raw.get("semantic_assertions"), "semantic_assertions"
            ),
            derived_from_claim_keys=_tuple_from_list(
                raw.get("derived_from_claim_keys"), "derived_from_claim_keys"
            ),
        )


@dataclass(frozen=True, slots=True)
class EvidenceLedger:
    schema_version: str
    research_context_id: str
    spec_bundle_hash: str
    entries: tuple[EvidenceLedgerEntry, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "research_context_id": self.research_context_id,
            "spec_bundle_hash": self.spec_bundle_hash,
            "entries": [
                item.to_dict()
                for item in sorted(self.entries, key=lambda entry: entry.claim_key)
            ],
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "EvidenceLedger":
        if not isinstance(raw, Mapping):
            _raise_invalid("evidence ledger must be an object")
        expected = {
            "schema_version",
            "research_context_id",
            "spec_bundle_hash",
            "entries",
        }
        if set(raw) != expected:
            _raise_invalid("evidence ledger fields are invalid")
        entries = raw.get("entries")
        if not isinstance(entries, list):
            _raise_invalid("evidence ledger entries must be a list")
        return cls(
            schema_version=raw.get("schema_version"),
            research_context_id=raw.get("research_context_id"),
            spec_bundle_hash=raw.get("spec_bundle_hash"),
            entries=tuple(EvidenceLedgerEntry.from_dict(item) for item in entries),
        )


@dataclass(frozen=True, slots=True)
class ProvenanceValidation:
    schema_version: str
    status: str
    research_context_id: str
    spec_bundle_hash: str
    entry_count: int
    validated_claim_keys: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "research_context_id": self.research_context_id,
            "spec_bundle_hash": self.spec_bundle_hash,
            "entry_count": self.entry_count,
            "validated_claim_keys": list(self.validated_claim_keys),
        }


def _raise_invalid(message: str) -> None:
    raise P10Error("P10_PROVENANCE_INVALID", message)


def _tuple_from_list(value: Any, name: str) -> tuple[Any, ...]:
    if not isinstance(value, list):
        _raise_invalid(f"{name} must be a list")
    return tuple(value)


def _mapping_from_value(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        _raise_invalid(f"{name} must be an object")
    return dict(value)


def _copy_json_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            _raise_invalid("semantic_assertions contains non-finite number")
        return value
    if isinstance(value, list):
        return [_copy_json_value(item) for item in value]
    if isinstance(value, Mapping):
        copied: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                _raise_invalid("semantic_assertions object keys must be strings")
            copied[key] = _copy_json_value(item)
        return copied
    _raise_invalid("semantic_assertions must be JSON-compatible")
    raise AssertionError("unreachable")


def _copy_json_object(value: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        _raise_invalid("semantic_assertions must be an object")
    copied = _copy_json_value(value)
    assert isinstance(copied, dict)
    try:
        _canonical_json_bytes(copied)
    except (TypeError, ValueError) as exc:
        raise P10Error(
            "P10_PROVENANCE_INVALID",
            "semantic_assertions is not canonical JSON-compatible",
        ) from exc
    return copied


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and _SHA256_RE.fullmatch(value) is not None


def _validate_unique_strings(values: object, name: str) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        _raise_invalid(f"{name} must be a tuple")
    result: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value:
            _raise_invalid(f"{name} must contain non-empty strings")
        result.append(value)
    if len(result) != len(set(result)):
        _raise_invalid(f"{name} must be unique")
    return tuple(result)


def _validate_pages(values: object) -> tuple[int, ...]:
    if not isinstance(values, tuple):
        _raise_invalid("page_nos must be a tuple")
    result: list[int] = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            _raise_invalid("page_nos must contain positive integers")
        result.append(value)
    if len(result) != len(set(result)):
        _raise_invalid("page_nos must be unique")
    return tuple(result)


def _validate_entry(entry: EvidenceLedgerEntry) -> None:
    if not isinstance(entry, EvidenceLedgerEntry):
        _raise_invalid("ledger contains an invalid entry")
    if (
        not isinstance(entry.claim_key, str)
        or not entry.claim_key.strip()
        or len(entry.claim_key) > _MAX_CLAIM_KEY_LENGTH
    ):
        _raise_invalid("claim_key must be a non-blank string of at most 256 characters")
    if entry.use_class not in USE_CLASSES_V1:
        _raise_invalid("unsupported evidence-ledger use_class")

    if entry.document_sha256 is not None and not _is_sha256(entry.document_sha256):
        _raise_invalid("document_sha256 must be lowercase SHA256 or null")
    if entry.overlay_set_hash is not None and not _is_sha256(entry.overlay_set_hash):
        _raise_invalid("overlay_set_hash must be lowercase SHA256 or null")

    pages = _validate_pages(entry.page_nos)
    tables = _validate_unique_strings(entry.table_ids, "table_ids")
    facts = _validate_unique_strings(entry.raw_fact_ids, "raw_fact_ids")
    evidence = _validate_unique_strings(entry.evidence_ids, "evidence_ids")
    resolutions = _validate_unique_strings(
        entry.p9_resolution_ids, "p9_resolution_ids"
    )
    derived = _validate_unique_strings(
        entry.derived_from_claim_keys, "derived_from_claim_keys"
    )
    assertions = _copy_json_object(entry.semantic_assertions)

    explicit_ref_count = (
        len(pages)
        + len(tables)
        + len(facts)
        + len(evidence)
        + len(resolutions)
        + len(derived)
    )
    if explicit_ref_count > _MAX_EXPLICIT_REFS_PER_ENTRY:
        _raise_invalid("ledger entry has too many explicit references")

    direct_count = len(pages) + len(tables) + len(facts) + len(evidence)
    has_assertions = bool(assertions)

    if entry.use_class == P8_RAW_DIRECT:
        if entry.document_sha256 is None or direct_count == 0:
            _raise_invalid("P8_RAW_DIRECT requires a document and direct P8 provenance")
        if resolutions or entry.overlay_set_hash is not None or derived or has_assertions:
            _raise_invalid("P8_RAW_DIRECT contains incompatible provenance fields")
        return

    if entry.use_class == RUN_LOCAL_STRUCTURED_VERIFIED:
        if resolutions or entry.overlay_set_hash is not None or not has_assertions:
            _raise_invalid(
                "RUN_LOCAL_STRUCTURED_VERIFIED requires semantic assertions and no P9 refs"
            )
        if derived:
            if entry.document_sha256 is not None or direct_count != 0:
                _raise_invalid(
                    "derived RUN_LOCAL_STRUCTURED_VERIFIED must use operand claims only"
                )
        else:
            if entry.document_sha256 is None or direct_count == 0:
                _raise_invalid(
                    "source-backed RUN_LOCAL_STRUCTURED_VERIFIED requires P8 provenance"
                )
        return

    if entry.use_class == P9_DURABLE_RESOLVED:
        if (
            entry.document_sha256 is None
            or not resolutions
            or entry.overlay_set_hash is None
            or derived
            or has_assertions
        ):
            _raise_invalid(
                "P9_DURABLE_RESOLVED requires document/resolutions/overlay only"
            )
        return

    if entry.use_class == UNRESOLVED:
        if resolutions or entry.overlay_set_hash is not None or derived or has_assertions:
            _raise_invalid("UNRESOLVED contains incompatible provenance fields")
        if direct_count and entry.document_sha256 is None:
            _raise_invalid("UNRESOLVED with P8 refs requires document_sha256")
        return

    raise AssertionError("unhandled use class")


def _validate_ledger_structure(ledger: EvidenceLedger) -> dict[str, EvidenceLedgerEntry]:
    if not isinstance(ledger, EvidenceLedger):
        _raise_invalid("ledger type is invalid")
    if ledger.schema_version != LEDGER_SCHEMA_VERSION:
        _raise_invalid("evidence ledger schema_version mismatch")
    if not _is_sha256(ledger.research_context_id):
        _raise_invalid("ledger research_context_id must be lowercase SHA256")
    if not _is_sha256(ledger.spec_bundle_hash):
        _raise_invalid("ledger spec_bundle_hash must be lowercase SHA256")
    if not isinstance(ledger.entries, tuple):
        _raise_invalid("ledger entries must be a tuple")
    if len(ledger.entries) > _MAX_LEDGER_ENTRIES:
        _raise_invalid("evidence ledger has more than 1000 entries")

    by_key: dict[str, EvidenceLedgerEntry] = {}
    for entry in ledger.entries:
        _validate_entry(entry)
        if entry.claim_key in by_key:
            _raise_invalid("duplicate claim_key in evidence ledger")
        by_key[entry.claim_key] = entry
    return by_key


def _validate_derived_graph(by_key: Mapping[str, EvidenceLedgerEntry]) -> None:
    allowed_operands = {
        RUN_LOCAL_STRUCTURED_VERIFIED,
        P9_DURABLE_RESOLVED,
    }
    dependencies: dict[str, tuple[str, ...]] = {}
    for claim_key, entry in by_key.items():
        dependencies[claim_key] = entry.derived_from_claim_keys
        for operand in entry.derived_from_claim_keys:
            if operand == claim_key:
                _raise_invalid("derived claim cannot reference itself")
            target = by_key.get(operand)
            if target is None:
                _raise_invalid("derived claim references missing operand")
            if target.use_class not in allowed_operands:
                _raise_invalid("derived claim references a non-ready operand use class")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(key: str) -> None:
        if key in visiting:
            _raise_invalid("derived claim graph contains a cycle")
        if key in visited:
            return
        visiting.add(key)
        for dependency in dependencies.get(key, ()):
            visit(dependency)
        visiting.remove(key)
        visited.add(key)

    for key in sorted(dependencies):
        visit(key)


def _context_incompatible(message: str) -> None:
    raise P10Error("P10_CONTEXT_INCOMPATIBLE", message)


def _validate_context(
    context: ResearchContext,
    spec_bundle: ResearchSpecBundle,
    p8_catalog: McpCatalog,
) -> Path:
    if not isinstance(context, ResearchContext):
        _raise_invalid("research context type is invalid")

    try:
        project_root = _context_project_root(p8_catalog)
    except P10Error as exc:
        if exc.reason_code == "P10_CATALOG_INVALID":
            raise P10Error("P10_CONTEXT_INCOMPATIBLE", str(exc)) from exc
        raise

    verify_research_spec(project_root, spec_bundle)
    if spec_bundle.spec_bundle_hash != context.spec_bundle_hash:
        _raise_invalid("spec bundle does not match research context")

    try:
        validated_root, catalog_sha = _catalog_identity(p8_catalog)
    except P10Error as exc:
        if exc.reason_code == "P10_CATALOG_INVALID":
            raise P10Error("P10_CONTEXT_INCOMPATIBLE", str(exc)) from exc
        raise
    if validated_root != project_root or catalog_sha != context.p8_catalog_sha256:
        _context_incompatible("current catalog does not match frozen research context")

    if (
        context.schema_version != CONTEXT_SCHEMA_VERSION
        or context.integration_policy_version != INTEGRATION_POLICY_VERSION
    ):
        _context_incompatible("research context schema/policy is incompatible")

    p8_contract = _accepted_p8_contract()
    p8_fingerprint = _fingerprint(p8_contract.to_dict())
    if (
        context.p8_tool_contract != p8_contract
        or context.p8_tool_contract_fingerprint != p8_fingerprint
    ):
        _context_incompatible("P8 contract does not match frozen research context")

    p9_contract = _accepted_p9_contract()
    p9_fingerprint = _fingerprint(p9_contract.to_dict())
    if (
        context.p9_policy_contract != p9_contract
        or context.p9_policy_fingerprint != p9_fingerprint
    ):
        _context_incompatible("P9 contract does not match frozen research context")

    canonical_review_root = _canonical_review_root(
        project_root,
        context.p9_review_root,
    )
    if canonical_review_root != context.p9_review_root:
        _context_incompatible("P9 review root is not canonical")

    capabilities = CAPABILITY_MANIFEST_V1
    capability_hash = _fingerprint(dict(capabilities))
    if (
        context.capabilities != capabilities
        or context.capability_manifest_hash != capability_hash
    ):
        _context_incompatible("capability manifest does not match P10 v1")

    expected_context_id = _research_context_id(
        schema_version=context.schema_version,
        integration_policy_version=context.integration_policy_version,
        spec_bundle_hash=context.spec_bundle_hash,
        p8_catalog_sha256=context.p8_catalog_sha256,
        p8_tool_contract_fingerprint=context.p8_tool_contract_fingerprint,
        p9_policy_fingerprint=context.p9_policy_fingerprint,
        p9_review_root=context.p9_review_root,
        capability_manifest_hash=context.capability_manifest_hash,
    )
    if expected_context_id != context.research_context_id:
        _context_incompatible("research_context_id is inconsistent")

    return project_root


_REFERENCE_ERRORS = {
    "P8_DOCUMENT_NOT_FOUND",
    "P8_TABLE_NOT_FOUND",
    "P8_FACT_NOT_FOUND",
    "P8_EVIDENCE_NOT_FOUND",
    "P8_INVALID_ARGUMENT",
}


def _p8_call(function, *args):
    try:
        return function(*args)
    except McpServiceError as exc:
        if exc.reason_code in _REFERENCE_ERRORS:
            raise P10Error("P10_PROVENANCE_INVALID", str(exc)) from exc
        raise P10Error("P10_UPSTREAM_INVALID", str(exc)) from exc


def _response_data(response: Mapping[str, Any]) -> dict[str, Any]:
    if (
        not isinstance(response, Mapping)
        or response.get("schema_version") != "p8-mcp-result-v1"
        or not isinstance(response.get("tool"), str)
    ):
        raise P10Error(
            "P10_UPSTREAM_INVALID",
            "accepted P8 service returned an invalid response envelope",
        )
    data = response.get("data")
    if not isinstance(data, Mapping):
        raise P10Error(
            "P10_UPSTREAM_INVALID",
            "accepted P8 service returned invalid response data",
        )
    return dict(data)


def _validate_p8_refs(
    service: McpQueryService,
    entries: tuple[EvidenceLedgerEntry, ...],
) -> None:
    document_cache: dict[str, dict[str, Any]] = {}
    table_cache: dict[tuple[str, str], dict[str, Any]] = {}
    fact_cache: dict[tuple[str, str], dict[str, Any]] = {}
    evidence_cache: dict[tuple[str, str], dict[str, Any]] = {}

    def document(sha: str) -> dict[str, Any]:
        if sha not in document_cache:
            document_cache[sha] = _response_data(_p8_call(service.get_document, sha))
        return document_cache[sha]

    def table(sha: str, table_id: str) -> dict[str, Any]:
        key = (sha, table_id)
        if key not in table_cache:
            table_cache[key] = _response_data(
                _p8_call(service.get_table, sha, table_id)
            )
        return table_cache[key]

    def fact(sha: str, fact_id: str) -> dict[str, Any]:
        key = (sha, fact_id)
        if key not in fact_cache:
            fact_cache[key] = _response_data(
                _p8_call(service.get_fact, sha, fact_id)
            )
        return fact_cache[key]

    def evidence(sha: str, evidence_id: str) -> dict[str, Any]:
        key = (sha, evidence_id)
        if key not in evidence_cache:
            evidence_cache[key] = _response_data(
                _p8_call(service.get_evidence, sha, evidence_id)
            )
        return evidence_cache[key]

    for entry in entries:
        sha = entry.document_sha256
        if sha is None:
            continue

        doc = document(sha)
        if str(doc.get("document_sha256")) != sha:
            raise P10Error(
                "P10_UPSTREAM_INVALID",
                "P8 document identity mismatch",
            )
        page_count = doc.get("page_count")
        if isinstance(page_count, bool) or not isinstance(page_count, int):
            raise P10Error(
                "P10_UPSTREAM_INVALID",
                "P8 document page_count is invalid",
            )

        declared_pages = set(entry.page_nos)
        declared_tables = set(entry.table_ids)
        declared_evidence = set(entry.evidence_ids)

        for page_no in entry.page_nos:
            if page_no < 1 or page_no > page_count:
                _raise_invalid("ledger page reference is outside document bounds")

        for table_id in entry.table_ids:
            row = table(sha, table_id)
            if str(row.get("document_sha256")) != sha:
                raise P10Error("P10_UPSTREAM_INVALID", "P8 table document mismatch")
            page_no = row.get("page_no")
            if declared_pages and page_no not in declared_pages:
                _raise_invalid("table page is outside declared page_nos")

        for raw_fact_id in entry.raw_fact_ids:
            row = fact(sha, raw_fact_id)
            if str(row.get("document_sha256")) != sha:
                raise P10Error("P10_UPSTREAM_INVALID", "P8 fact document mismatch")
            page_no = row.get("page_no")
            table_id = str(row.get("table_id") or "")
            evidence_id = str(row.get("evidence_id") or "")
            if declared_pages and page_no not in declared_pages:
                _raise_invalid("raw fact page is outside declared page_nos")
            if declared_tables and table_id not in declared_tables:
                _raise_invalid("raw fact table is outside declared table_ids")
            if declared_evidence and evidence_id not in declared_evidence:
                _raise_invalid(
                    "raw fact evidence is outside declared evidence_ids"
                )

        for evidence_id in entry.evidence_ids:
            row = evidence(sha, evidence_id)
            if str(row.get("document_sha256")) != sha:
                raise P10Error(
                    "P10_UPSTREAM_INVALID",
                    "P8 evidence document mismatch",
                )
            page_no = row.get("page_no")
            table_id = str(row.get("table_id") or "")
            if declared_pages and page_no not in declared_pages:
                _raise_invalid("evidence page is outside declared page_nos")
            if declared_tables and table_id not in declared_tables:
                _raise_invalid("evidence table is outside declared table_ids")


def _assert_inside_project(project_root: Path, candidate: Path) -> None:
    try:
        candidate.relative_to(project_root)
    except ValueError as exc:
        raise P10Error(
            "P10_PROVENANCE_INVALID",
            "claimed P9 provenance resolves outside project root",
        ) from exc


def _validate_p9_refs(
    project_root: Path,
    context: ResearchContext,
    entries: tuple[EvidenceLedgerEntry, ...],
) -> None:
    review_root = (project_root / context.p9_review_root).resolve(strict=True)
    _assert_inside_project(project_root, review_root)

    snapshot_cache: dict[tuple[str, str], Any] = {}

    for entry in entries:
        if entry.use_class != P9_DURABLE_RESOLVED:
            continue
        assert entry.document_sha256 is not None
        assert entry.overlay_set_hash is not None

        review_dir_candidate = review_root / entry.document_sha256
        snapshot_candidate = (
            review_dir_candidate / "snapshots" / entry.overlay_set_hash
        )
        try:
            review_dir = review_dir_candidate.resolve(strict=True)
            snapshot_dir = snapshot_candidate.resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            raise P10Error(
                "P10_PROVENANCE_INVALID",
                "claimed P9 review/snapshot path does not exist",
            ) from exc
        _assert_inside_project(project_root, review_dir)
        _assert_inside_project(project_root, snapshot_dir)
        if not review_dir.is_dir() or not snapshot_dir.is_dir():
            _raise_invalid("claimed P9 review/snapshot path is not a directory")

        cache_key = (entry.document_sha256, entry.overlay_set_hash)
        if cache_key not in snapshot_cache:
            try:
                snapshot_cache[cache_key] = load_resolved_snapshot(
                    snapshot_dir,
                    review_dir,
                )
            except ReviewError as exc:
                raise P10Error("P10_UPSTREAM_INVALID", str(exc)) from exc
            except (OSError, RuntimeError, ValueError) as exc:
                raise P10Error(
                    "P10_UPSTREAM_INVALID",
                    "accepted P9 snapshot loader failed",
                ) from exc

        snapshot = snapshot_cache[cache_key]
        if (
            snapshot.document_sha256 != entry.document_sha256
            or snapshot.overlay_set_hash != entry.overlay_set_hash
        ):
            raise P10Error(
                "P10_UPSTREAM_INVALID",
                "P9 snapshot identity mismatch",
            )
        active_ids = snapshot.report.get("active_resolution_ids")
        if not isinstance(active_ids, list) or any(
            not isinstance(item, str) for item in active_ids
        ):
            raise P10Error(
                "P10_UPSTREAM_INVALID",
                "P9 snapshot active_resolution_ids is invalid",
            )
        active_set = set(active_ids)
        missing = [
            resolution_id
            for resolution_id in entry.p9_resolution_ids
            if resolution_id not in active_set
        ]
        if missing:
            _raise_invalid(
                "P9 resolution is not active in the claimed overlay snapshot"
            )


def validate_evidence_ledger(
    context: ResearchContext,
    ledger: EvidenceLedger,
    spec_bundle: ResearchSpecBundle,
    p8_catalog: McpCatalog,
) -> ProvenanceValidation:
    project_root = _validate_context(context, spec_bundle, p8_catalog)
    by_key = _validate_ledger_structure(ledger)

    if ledger.research_context_id != context.research_context_id:
        _raise_invalid("ledger research_context_id does not match context")
    if ledger.spec_bundle_hash != context.spec_bundle_hash:
        _raise_invalid("ledger spec_bundle_hash does not match context")

    _validate_derived_graph(by_key)

    service = McpQueryService(p8_catalog)
    entries = tuple(by_key[key] for key in sorted(by_key))
    _validate_p8_refs(service, entries)
    _validate_p9_refs(project_root, context, entries)

    return ProvenanceValidation(
        schema_version=PROVENANCE_VALIDATION_SCHEMA_VERSION,
        status="PASS",
        research_context_id=context.research_context_id,
        spec_bundle_hash=context.spec_bundle_hash,
        entry_count=len(entries),
        validated_claim_keys=tuple(sorted(by_key)),
    )
