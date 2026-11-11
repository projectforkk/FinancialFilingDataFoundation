from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from financial_filing_data_foundation.mcp.catalog import McpCatalog
from financial_filing_data_foundation.mcp.service import McpQueryService
from financial_filing_data_foundation.registry import SQLiteRegistry

from .identity import sec_company
from .discovery import SecDiscoveryObservation
from .package import SecFilingPackage, SecPackageStore
from .parser import SEC_ARTIFACT_SCHEMA, SecParseResult, load_sec_artifacts, parse_sec_package
from .registry import register_sec_package, register_sec_parsed_run, register_sec_slot
from .validation import SecValidationResult, load_sec_validation, validate_sec_artifacts


@dataclass(frozen=True, slots=True)
class SecIngestResult:
    package: SecFilingPackage
    parsed: SecParseResult
    validation: SecValidationResult
    catalog_status: str
    research_ready: bool
    registry_path: Path
    catalog_path: Path


def _relative(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _upsert_catalog(
    root: Path,
    package: SecFilingPackage,
    ticker: str,
    parsed: SecParseResult,
    validation: SecValidationResult,
    *,
    catalog_path: Path,
    period: str,
    publish: bool,
    company_id: str | None = None,
    ticker_source_url: str | None = None,
    ticker_source_sha256: str | None = None,
    ticker_retrieved_at: str | None = None,
    discovery_observation: SecDiscoveryObservation | None = None,
) -> str:
    if not publish:
        return "NOT_REGISTERED_REVIEW_CONFLICT"
    if catalog_path.exists():
        payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    else:
        payload = {"schema_version": "p8-mcp-catalog-v1", "documents": []}
    if payload.get("schema_version") != "p8-mcp-catalog-v1" or not isinstance(payload.get("documents"), list):
        raise ValueError("P8 catalog schema is invalid")
    document = {
        "document_sha256": package.package_sha256,
        "package_sha256": package.package_sha256,
        "source_kind": "SEC",
        "market": "US",
        "ticker": ticker,
        "company_id": company_id or f"US:CIK{package.cik}",
        "provider_company_id": package.cik,
        "cik": package.cik,
        "ticker_source_url": ticker_source_url,
        "ticker_source_sha256": ticker_source_sha256,
        "ticker_retrieved_at": ticker_retrieved_at,
        "discovery_observation_sha256": (
            discovery_observation.observation_sha256
            if discovery_observation is not None
            else validation.discovery_observation_sha256 or parsed.discovery_observation_sha256
        ),
        "discovery_checked_at": (
            discovery_observation.retrieved_at
            if discovery_observation is not None
            else validation.discovery_checked_at or parsed.discovery_checked_at
        ),
        "selected_accession": (
            discovery_observation.selected_accession
            if discovery_observation is not None
            else validation.selected_accession or parsed.selected_accession
        ),
        "discovery_state": (
            discovery_observation.state
            if discovery_observation is not None
            else validation.discovery_state or parsed.discovery_state
        ),
        "fact_source_mode": parsed.fact_source_mode,
        "fiscal_year": package.fiscal_year,
        "filing_type": period.upper(),
        "raw_fiscal_period": period.upper(),
        "sec_artifact_dir": _relative(root, parsed.artifact_dir),
    }
    identity = ("US", str(document["company_id"]).upper(), package.fiscal_year, period.upper())
    documents = payload["documents"]
    replacement: int | None = None
    for index, row in enumerate(documents):
        row_company = str(row.get("company_id") or "").strip()
        if not row_company and str(row.get("cik") or "").strip().isdigit():
            row_company = f"US:CIK{str(row.get('cik')).zfill(10)}"
        if not row_company:
            row_company = str(row.get("ticker", "")).upper()
        row_identity = (
            str(row.get("market", "")).upper(),
            row_company.upper(),
            int(row.get("fiscal_year", 0)),
            str(row.get("raw_fiscal_period", row.get("filing_type", ""))).upper(),
        )
        if str(row.get("document_sha256", "")).lower() == package.package_sha256 and row_identity != identity:
            raise ValueError("P8 catalog package SHA is bound to a different filing identity")
        if row_identity == identity:
            if str(row.get("document_sha256", "")).lower() != package.package_sha256:
                raise ValueError("P8 SEC slot already points to another package")
            replacement = index
            break
    if replacement is None:
        documents.append(document)
        action = "ADDED"
    else:
        documents[replacement] = document
        action = "ALREADY_REGISTERED"
    documents.sort(key=lambda row: (str(row.get("market", "")), str(row.get("company_id") or row.get("ticker", "")), int(row.get("fiscal_year", 0)), str(row.get("raw_fiscal_period", "")), str(row.get("document_sha256", ""))))
    candidate = {"schema_version": "p8-mcp-catalog-v1", "documents": documents}
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", dir=catalog_path.parent, prefix=".p8-sec.", suffix=".tmp", delete=False) as handle:
        temp_path = Path(handle.name)
        handle.write(json.dumps(candidate, ensure_ascii=False, indent=2) + "\n")
    try:
        catalog = McpCatalog.load(root, temp_path)
        McpQueryService(catalog).get_document(package.package_sha256)
        os.replace(temp_path, catalog_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()
    return action


def ingest_sec_package(
    package: SecFilingPackage,
    *,
    root: str | Path,
    ticker: str,
    period: str,
    amendment_conflict: bool = False,
    company_id: str | None = None,
    ticker_source_url: str | None = None,
    ticker_source_sha256: str | None = None,
    ticker_retrieved_at: str | None = None,
    discovery_observation: SecDiscoveryObservation | None = None,
) -> SecIngestResult:
    project_root = Path(root).expanduser().resolve()
    base = project_root / "workspace" / "ingest" / "us"
    store = SecPackageStore(project_root / "workspace" / "ingest" / "raw-store")
    store.put(package)
    registry_path = project_root / "workspace" / "ingest" / "registry.sqlite"
    registry = SQLiteRegistry(registry_path)
    if discovery_observation is not None:
        registry.register_sec_discovery_observation(discovery_observation)
    register_sec_package(registry, package)
    parsed = parse_sec_package(package, base / "p11", discovery_observation=discovery_observation)
    validation = validate_sec_artifacts(
        parsed,
        base / "p7",
        amendment_conflict=amendment_conflict,
        package=package,
        discovery_observation=discovery_observation,
        registry=registry,
    )
    binding_status = "REVIEW_REQUIRED" if amendment_conflict else "SOURCE_CONFIRMED"
    register_sec_slot(registry, package, fiscal_year=package.fiscal_year, period=period, artifact_path=str(parsed.artifact_dir), binding_status=binding_status)
    parse_run_id = hashlib.sha256(f"{package.package_sha256}|{parsed.parser_version}".encode()).hexdigest()
    register_sec_parsed_run(
        registry,
        parse_run_id=parse_run_id,
        package_sha256=package.package_sha256,
        company_id=f"US:CIK{package.cik}",
        fiscal_year=package.fiscal_year,
        period=period,
        parser_version=parsed.parser_version,
        schema_version=SEC_ARTIFACT_SCHEMA,
        validation_status=validation.validation_status,
        compatibility_status=validation.compatibility_status,
        blocking_issue_count=validation.blocking_issue_count,
        artifact_path=str(parsed.artifact_dir),
    )
    ready = (
        validation.validation_status == "PASS"
        and not amendment_conflict
        and (discovery_observation is None or discovery_observation.state == "UNAMBIGUOUS")
    )
    catalog_path = project_root / "workspace" / "mcp" / "p8-live-catalog.json"
    catalog_status = _upsert_catalog(root=project_root, package=package, ticker=ticker, parsed=parsed, validation=validation, catalog_path=catalog_path, period=period, publish=ready, company_id=company_id, ticker_source_url=ticker_source_url, ticker_source_sha256=ticker_source_sha256, ticker_retrieved_at=ticker_retrieved_at, discovery_observation=discovery_observation)
    return SecIngestResult(package, parsed, validation, catalog_status, ready, registry_path, catalog_path)


def reuse_sec_package(
    package: SecFilingPackage,
    *,
    root: str | Path,
    ticker: str,
    period: str,
    parsed_artifact_dir: str | Path,
    amendment_conflict: bool = False,
    company_id: str | None = None,
    ticker_source_url: str | None = None,
    ticker_source_sha256: str | None = None,
    ticker_retrieved_at: str | None = None,
    discovery_observation: SecDiscoveryObservation | None = None,
) -> SecIngestResult:
    """Reuse a verified current SEC artifact without parsing or downloading."""

    project_root = Path(root).expanduser().resolve()
    parsed = load_sec_artifacts(parsed_artifact_dir)
    validation = load_sec_validation(
        project_root / "workspace" / "ingest" / "us" / "p7" / package.package_sha256
    )
    if parsed.package_sha256 != package.package_sha256 or validation.package_sha256 != package.package_sha256:
        raise ValueError("SEC reuse artifact identity differs from source package")
    registry_path = project_root / "workspace" / "ingest" / "registry.sqlite"
    registry = SQLiteRegistry(registry_path)
    if discovery_observation is not None:
        registry.register_sec_discovery_observation(discovery_observation)
    register_sec_package(registry, package)
    if discovery_observation is not None and (
        validation.discovery_observation_sha256 != discovery_observation.observation_sha256
        or validation.discovery_checked_at != discovery_observation.retrieved_at
        or validation.selected_accession != discovery_observation.selected_accession
        or validation.discovery_state != discovery_observation.state
    ):
        # A fresh online discovery is a new P7 binding even when the raw
        # package and parsed files are reusable.  Refresh only validation
        # metadata/evidence; never rerun the parser or mutate the raw package.
        validation = validate_sec_artifacts(
            parsed,
            project_root / "workspace" / "ingest" / "us" / "p7",
            package=package,
            discovery_observation=discovery_observation,
            registry=registry,
        )
    binding_status = "REVIEW_REQUIRED" if amendment_conflict else "SOURCE_CONFIRMED"
    register_sec_slot(
        registry,
        package,
        fiscal_year=package.fiscal_year,
        period=period,
        artifact_path=str(parsed.artifact_dir),
        binding_status=binding_status,
    )
    ready = (
        validation.validation_status == "PASS"
        and validation.compatibility_status == "COMPATIBLE"
        and validation.blocking_issue_count == 0
        and not amendment_conflict
        and (discovery_observation is None or discovery_observation.state == "UNAMBIGUOUS")
    )
    catalog_path = project_root / "workspace" / "mcp" / "p8-live-catalog.json"
    catalog_status = _upsert_catalog(
        root=project_root,
        package=package,
        ticker=ticker,
        parsed=parsed,
        validation=validation,
        catalog_path=catalog_path,
        period=period,
        publish=ready,
        company_id=company_id,
        ticker_source_url=ticker_source_url,
        ticker_source_sha256=ticker_source_sha256,
        ticker_retrieved_at=ticker_retrieved_at,
        discovery_observation=discovery_observation,
    )
    return SecIngestResult(package, parsed, validation, catalog_status, ready, registry_path, catalog_path)


__all__ = ["SecIngestResult", "ingest_sec_package", "reuse_sec_package"]
