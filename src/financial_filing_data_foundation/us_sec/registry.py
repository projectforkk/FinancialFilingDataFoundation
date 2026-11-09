from __future__ import annotations

from pathlib import Path
from typing import Any

from financial_filing_data_foundation.registry import SQLiteRegistry
from financial_filing_data_foundation.registry.sqlite_registry import SEC_REGISTRY_SCHEMA_VERSION

from .package import SecFilingPackage, SecPackageStore


def register_sec_package(registry: SQLiteRegistry, package: SecFilingPackage) -> None:
    registry.register_sec_package(package)


def register_sec_slot(
    registry: SQLiteRegistry,
    package: SecFilingPackage,
    *,
    fiscal_year: int,
    period: str,
    artifact_path: str | Path | None = None,
    binding_status: str = "SOURCE_CONFIRMED",
) -> str:
    return registry.register_sec_binding(
        package,
        company_id=f"US:CIK{package.cik}",
        fiscal_year=fiscal_year,
        period=period,
        artifact_path=None if artifact_path is None else str(artifact_path),
        binding_status=binding_status,
    )


def register_sec_parsed_run(
    registry: SQLiteRegistry,
    *,
    parse_run_id: str,
    package_sha256: str,
    company_id: str,
    fiscal_year: int,
    period: str,
    parser_version: str,
    schema_version: str,
    validation_status: str,
    blocking_issue_count: int,
    artifact_path: str | Path | None,
) -> None:
    registry.register_sec_parsed_data(
        parse_run_id=parse_run_id,
        package_sha256=package_sha256,
        company_id=company_id,
        fiscal_year=fiscal_year,
        period=period,
        parser_version=parser_version,
        schema_version=schema_version,
        validation_status=validation_status,
        blocking_issue_count=blocking_issue_count,
        artifact_path=None if artifact_path is None else str(artifact_path),
    )


__all__ = [
    "SEC_REGISTRY_SCHEMA_VERSION",
    "register_sec_package",
    "register_sec_parsed_run",
    "register_sec_slot",
]
