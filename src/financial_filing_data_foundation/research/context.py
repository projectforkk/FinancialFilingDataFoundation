from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from financial_filing_data_foundation.mcp import (
    CATALOG_SCHEMA_VERSION,
    RESULT_SCHEMA_VERSION,
    CatalogError,
    McpCatalog,
)
from financial_filing_data_foundation.review import (
    P9_VERSION,
    POLICY_VERSION,
    RESOLUTION_SCHEMA_VERSION,
    RESOLVED_VIEW_SCHEMA_VERSION,
)

from .models import P10Error, ResearchSpecBundle
from .spec import _canonical_json_bytes, verify_research_spec


CONTEXT_SCHEMA_VERSION = "p10-research-context-v1"
INTEGRATION_POLICY_VERSION = "p10-dynamic-research-v1"

P8_SERVER_VERSION_V1 = "p8-local-mcp-v1"
P8_CATALOG_SCHEMA_VERSION_V1 = "p8-mcp-catalog-v1"
P8_RESULT_SCHEMA_VERSION_V1 = "p8-mcp-result-v1"
P8_TOOL_NAMES_V1 = (
    "ffdf_list_documents",
    "ffdf_get_document",
    "ffdf_search_document",
    "ffdf_read_pages",
    "ffdf_list_sections",
    "ffdf_list_tables",
    "ffdf_get_table",
    "ffdf_list_raw_facts",
    "ffdf_get_fact",
    "ffdf_get_evidence",
    "ffdf_get_validation",
)

P9_VERSION_V1 = "p9-review-overlay-v1"
P9_POLICY_VERSION_V1 = "p9-review-policy-v1"
P9_RESOLUTION_SCHEMA_VERSION_V1 = "p9-review-resolution-v1"
P9_RESOLVED_VIEW_SCHEMA_VERSION_V1 = "p9-resolved-view-v1"

CAPABILITY_MANIFEST_V1 = (
    ("P8_RAW_QUERY", "AVAILABLE"),
    ("P8_PAGE_TEXT", "AVAILABLE"),
    ("P8_TABLE_STRUCTURED", "AVAILABLE"),
    ("P8_EVIDENCE", "AVAILABLE"),
    ("P8_VALIDATION", "AVAILABLE"),
    ("P9_REVIEW", "AVAILABLE"),
    ("P9_RESOLVED_VIEW", "AVAILABLE"),
    ("PDF_VISUAL_EVIDENCE", "UNAVAILABLE"),
    ("SEMANTIC_RESOLVER", "UNAVAILABLE"),
    ("CANONICAL_METRIC_LAYER", "UNAVAILABLE"),
    ("P11_SEC_PROVIDER", "UNAVAILABLE"),
)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


@dataclass(frozen=True, slots=True)
class P8ToolContract:
    server_version: str
    catalog_schema_version: str
    result_schema_version: str
    tool_names: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "server_version": self.server_version,
            "catalog_schema_version": self.catalog_schema_version,
            "result_schema_version": self.result_schema_version,
            "tool_names": list(self.tool_names),
        }


@dataclass(frozen=True, slots=True)
class P9PolicyContract:
    p9_version: str
    policy_version: str
    resolution_schema_version: str
    resolved_view_schema_version: str

    def to_dict(self) -> dict[str, str]:
        return {
            "p9_version": self.p9_version,
            "policy_version": self.policy_version,
            "resolution_schema_version": self.resolution_schema_version,
            "resolved_view_schema_version": self.resolved_view_schema_version,
        }


@dataclass(frozen=True, slots=True)
class ResearchContext:
    schema_version: str
    integration_policy_version: str
    spec_bundle_hash: str
    p8_catalog_sha256: str
    p8_tool_contract: P8ToolContract
    p8_tool_contract_fingerprint: str
    p9_policy_contract: P9PolicyContract
    p9_policy_fingerprint: str
    p9_review_root: str
    capabilities: tuple[tuple[str, str], ...]
    capability_manifest_hash: str
    research_context_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "integration_policy_version": self.integration_policy_version,
            "spec_bundle_hash": self.spec_bundle_hash,
            "p8_catalog_sha256": self.p8_catalog_sha256,
            "p8_tool_contract": self.p8_tool_contract.to_dict(),
            "p8_tool_contract_fingerprint": self.p8_tool_contract_fingerprint,
            "p9_policy_contract": self.p9_policy_contract.to_dict(),
            "p9_policy_fingerprint": self.p9_policy_fingerprint,
            "p9_review_root": self.p9_review_root,
            "capabilities": dict(self.capabilities),
            "capability_manifest_hash": self.capability_manifest_hash,
            "research_context_id": self.research_context_id,
        }


def _accepted_p8_contract() -> P8ToolContract:
    if (
        CATALOG_SCHEMA_VERSION != P8_CATALOG_SCHEMA_VERSION_V1
        or RESULT_SCHEMA_VERSION != P8_RESULT_SCHEMA_VERSION_V1
    ):
        raise P10Error(
            "P10_CONTEXT_INCOMPATIBLE",
            "accepted P8 public contract version changed",
        )
    return P8ToolContract(
        server_version=P8_SERVER_VERSION_V1,
        catalog_schema_version=CATALOG_SCHEMA_VERSION,
        result_schema_version=RESULT_SCHEMA_VERSION,
        tool_names=P8_TOOL_NAMES_V1,
    )


def _accepted_p9_contract() -> P9PolicyContract:
    if (
        P9_VERSION != P9_VERSION_V1
        or POLICY_VERSION != P9_POLICY_VERSION_V1
        or RESOLUTION_SCHEMA_VERSION != P9_RESOLUTION_SCHEMA_VERSION_V1
        or RESOLVED_VIEW_SCHEMA_VERSION != P9_RESOLVED_VIEW_SCHEMA_VERSION_V1
    ):
        raise P10Error(
            "P10_CONTEXT_INCOMPATIBLE",
            "accepted P9 public contract version changed",
        )
    return P9PolicyContract(
        p9_version=P9_VERSION,
        policy_version=POLICY_VERSION,
        resolution_schema_version=RESOLUTION_SCHEMA_VERSION,
        resolved_view_schema_version=RESOLVED_VIEW_SCHEMA_VERSION,
    )


def _fingerprint(value: Any) -> str:
    return _sha256_bytes(_canonical_json_bytes(value))


def _assert_inside(root: Path, candidate: Path) -> None:
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise P10Error(
            "P10_CONTEXT_PATH_OUTSIDE_PROJECT",
            "context path resolves outside project root",
        ) from exc


def _canonical_review_root(
    project_root: Path,
    p9_review_root: str | Path,
) -> str:
    try:
        candidate = Path(p9_review_root)
    except (TypeError, ValueError) as exc:
        raise P10Error(
            "P10_CONTEXT_INCOMPATIBLE",
            "p9_review_root is invalid",
        ) from exc
    if candidate.is_absolute() or candidate.drive or candidate.root:
        raise P10Error(
            "P10_CONTEXT_PATH_OUTSIDE_PROJECT",
            "p9_review_root must be project-root-relative",
        )
    try:
        pre_resolved = (project_root / candidate).resolve(strict=False)
    except (OSError, RuntimeError, ValueError) as exc:
        raise P10Error(
            "P10_CONTEXT_INCOMPATIBLE",
            "p9_review_root cannot be resolved",
        ) from exc
    _assert_inside(project_root, pre_resolved)
    try:
        resolved = (project_root / candidate).resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise P10Error(
            "P10_CONTEXT_INCOMPATIBLE",
            "p9_review_root does not exist",
        ) from exc
    _assert_inside(project_root, resolved)
    if not resolved.is_dir():
        raise P10Error(
            "P10_CONTEXT_INCOMPATIBLE",
            "p9_review_root must be a directory",
        )
    return resolved.relative_to(project_root).as_posix()


def _context_project_root(p8_catalog: McpCatalog) -> Path:
    if not isinstance(p8_catalog, McpCatalog):
        raise P10Error(
            "P10_CATALOG_INVALID",
            "p8_catalog must be an accepted McpCatalog",
        )
    try:
        root = p8_catalog.project_root.resolve(strict=True)
    except (OSError, RuntimeError, ValueError) as exc:
        raise P10Error(
            "P10_CATALOG_INVALID",
            "catalog project root is invalid",
        ) from exc
    if not root.is_dir():
        raise P10Error(
            "P10_CATALOG_INVALID",
            "catalog project root must be a directory",
        )
    return root


def _catalog_identity(p8_catalog: McpCatalog) -> tuple[Path, str]:
    root = _context_project_root(p8_catalog)
    try:
        catalog_path = p8_catalog.catalog_path.resolve(strict=True)
    except (OSError, RuntimeError, ValueError) as exc:
        raise P10Error(
            "P10_CATALOG_INVALID",
            "catalog path is invalid",
        ) from exc
    try:
        catalog_path.relative_to(root)
    except ValueError as exc:
        raise P10Error(
            "P10_CATALOG_INVALID",
            "catalog path resolves outside project root",
        ) from exc
    if not catalog_path.is_file():
        raise P10Error(
            "P10_CATALOG_INVALID",
            "catalog path must be a file",
        )

    try:
        before = catalog_path.read_bytes()
        reloaded = McpCatalog.load(root, catalog_path)
        after = catalog_path.read_bytes()
    except (CatalogError, OSError) as exc:
        raise P10Error(
            "P10_CATALOG_INVALID",
            "catalog cannot be validated",
        ) from exc

    if before != after or reloaded != p8_catalog:
        raise P10Error(
            "P10_CATALOG_INVALID",
            "catalog changed or does not match caller state",
        )
    return root, _sha256_bytes(after)


def _research_context_id(
    *,
    schema_version: str,
    integration_policy_version: str,
    spec_bundle_hash: str,
    p8_catalog_sha256: str,
    p8_tool_contract_fingerprint: str,
    p9_policy_fingerprint: str,
    p9_review_root: str,
    capability_manifest_hash: str,
) -> str:
    identity = (
        schema_version
        + "\0"
        + integration_policy_version
        + "\0"
        + spec_bundle_hash
        + "\0"
        + p8_catalog_sha256
        + "\0"
        + p8_tool_contract_fingerprint
        + "\0"
        + p9_policy_fingerprint
        + "\0"
        + p9_review_root
        + "\0"
        + capability_manifest_hash
    )
    return _sha256_bytes(identity.encode("utf-8"))


def build_research_context(
    spec_bundle: ResearchSpecBundle,
    p8_catalog: McpCatalog,
    p9_review_root: str | Path,
) -> ResearchContext:
    project_root = _context_project_root(p8_catalog)
    verify_research_spec(project_root, spec_bundle)
    _, p8_catalog_sha256 = _catalog_identity(p8_catalog)

    p8_contract = _accepted_p8_contract()
    p8_fingerprint = _fingerprint(p8_contract.to_dict())

    p9_contract = _accepted_p9_contract()
    p9_fingerprint = _fingerprint(p9_contract.to_dict())

    canonical_review_root = _canonical_review_root(project_root, p9_review_root)

    capabilities = CAPABILITY_MANIFEST_V1
    capability_hash = _fingerprint(dict(capabilities))

    context_id = _research_context_id(
        schema_version=CONTEXT_SCHEMA_VERSION,
        integration_policy_version=INTEGRATION_POLICY_VERSION,
        spec_bundle_hash=spec_bundle.spec_bundle_hash,
        p8_catalog_sha256=p8_catalog_sha256,
        p8_tool_contract_fingerprint=p8_fingerprint,
        p9_policy_fingerprint=p9_fingerprint,
        p9_review_root=canonical_review_root,
        capability_manifest_hash=capability_hash,
    )

    return ResearchContext(
        schema_version=CONTEXT_SCHEMA_VERSION,
        integration_policy_version=INTEGRATION_POLICY_VERSION,
        spec_bundle_hash=spec_bundle.spec_bundle_hash,
        p8_catalog_sha256=p8_catalog_sha256,
        p8_tool_contract=p8_contract,
        p8_tool_contract_fingerprint=p8_fingerprint,
        p9_policy_contract=p9_contract,
        p9_policy_fingerprint=p9_fingerprint,
        p9_review_root=canonical_review_root,
        capabilities=capabilities,
        capability_manifest_hash=capability_hash,
        research_context_id=context_id,
    )
