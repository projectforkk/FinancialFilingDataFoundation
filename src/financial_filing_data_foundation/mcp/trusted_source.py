from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import pymupdf

from financial_filing_data_foundation.mcp.catalog import (
    McpCatalog,
    normalize_sha256,
)
from financial_filing_data_foundation.registry import SQLiteRegistry


TRUSTED_PDF_RESOLVER_VERSION: Final = "trusted-pdf-source-v1"


class TrustedSourceError(RuntimeError):
    def __init__(self, reason_code: str, message: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


@dataclass(frozen=True, slots=True)
class TrustedPdfSource:
    document_sha256: str
    path: Path
    file_size: int
    page_count: int
    market: str
    ticker: str
    fiscal_year: int
    filing_type: str
    resolver_version: str = TRUSTED_PDF_RESOLVER_VERSION

    def public_metadata(self) -> dict[str, object]:
        return {
            "document_sha256": self.document_sha256,
            "file_size": self.file_size,
            "page_count": self.page_count,
            "market": self.market,
            "ticker": self.ticker,
            "fiscal_year": self.fiscal_year,
            "filing_type": self.filing_type,
            "resolver_version": self.resolver_version,
        }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _assert_within(root: Path, candidate: Path) -> None:
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise TrustedSourceError(
            "RESEARCH_MCP_VISUAL_SOURCE_UNTRUSTED",
            "registered PDF lies outside trusted raw-store root",
        ) from exc


def _read_p3_manifest(document_dir: Path) -> dict[str, object]:
    path = document_dir / "document.json"
    if not path.is_file():
        raise TrustedSourceError(
            "RESEARCH_MCP_VISUAL_SOURCE_INVALID",
            "P3 document manifest is missing",
        )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TrustedSourceError(
            "RESEARCH_MCP_VISUAL_SOURCE_INVALID",
            "P3 document manifest cannot be read",
        ) from exc
    if not isinstance(payload, dict):
        raise TrustedSourceError(
            "RESEARCH_MCP_VISUAL_SOURCE_INVALID",
            "P3 document manifest root must be an object",
        )
    return payload


def resolve_trusted_pdf_source(
    *,
    catalog: McpCatalog,
    registry_path: str | Path,
    trusted_raw_root: str | Path,
    document_sha256: str,
) -> TrustedPdfSource:
    try:
        normalized = normalize_sha256(document_sha256)
    except Exception as exc:
        raise TrustedSourceError(
            "RESEARCH_MCP_DOCUMENT_NOT_FOUND",
            "document_sha256 is invalid",
        ) from exc

    document = catalog.get(normalized)
    if document is None:
        raise TrustedSourceError(
            "RESEARCH_MCP_DOCUMENT_NOT_FOUND",
            "document is not present in the configured MCP catalog",
        )

    root = Path(trusted_raw_root).expanduser().resolve()
    if not root.is_dir():
        raise TrustedSourceError(
            "RESEARCH_MCP_VISUAL_SOURCE_UNTRUSTED",
            "trusted raw-store root does not exist",
        )

    manifest = _read_p3_manifest(document.p3_artifact_dir)
    if str(manifest.get("document_sha256") or "").lower() != normalized:
        raise TrustedSourceError(
            "RESEARCH_MCP_VISUAL_SOURCE_INVALID",
            "P3 manifest document SHA does not match catalog",
        )

    source_path_raw = manifest.get("source_path")
    if not isinstance(source_path_raw, str) or not source_path_raw.strip():
        raise TrustedSourceError(
            "RESEARCH_MCP_VISUAL_SOURCE_INVALID",
            "P3 manifest source_path is missing",
        )
    source_path = Path(source_path_raw).expanduser().resolve()
    _assert_within(root, source_path)

    if source_path.suffix.lower() != ".pdf" or not source_path.is_file():
        raise TrustedSourceError(
            "RESEARCH_MCP_VISUAL_SOURCE_INVALID",
            "trusted source is not a live PDF file",
        )

    registry_file = Path(registry_path).expanduser().resolve()
    if not registry_file.is_file():
        raise TrustedSourceError(
            "RESEARCH_MCP_VISUAL_SOURCE_UNTRUSTED",
            "configured Registry does not exist",
        )
    registry = SQLiteRegistry(registry_file)
    if registry.location_sha(source_path) != normalized:
        raise TrustedSourceError(
            "RESEARCH_MCP_VISUAL_SOURCE_UNTRUSTED",
            "P3 source path is not registered to this document SHA",
        )

    try:
        expected_size = int(manifest["file_size"])
        expected_pages = int(manifest["page_count"])
    except (KeyError, TypeError, ValueError) as exc:
        raise TrustedSourceError(
            "RESEARCH_MCP_VISUAL_SOURCE_INVALID",
            "P3 manifest file_size/page_count is invalid",
        ) from exc

    stat_size = source_path.stat().st_size
    if stat_size != expected_size:
        raise TrustedSourceError(
            "RESEARCH_MCP_VISUAL_SOURCE_INVALID",
            "trusted PDF file size differs from P3 manifest",
        )

    actual_sha = _sha256_file(source_path)
    if actual_sha != normalized:
        raise TrustedSourceError(
            "RESEARCH_MCP_VISUAL_SOURCE_INVALID",
            "trusted PDF SHA256 differs from document identity",
        )

    try:
        with pymupdf.open(source_path) as pdf:
            if pdf.needs_pass:
                raise TrustedSourceError(
                    "RESEARCH_MCP_VISUAL_SOURCE_INVALID",
                    "trusted PDF is password protected",
                )
            actual_pages = int(pdf.page_count)
    except TrustedSourceError:
        raise
    except Exception as exc:
        raise TrustedSourceError(
            "RESEARCH_MCP_VISUAL_SOURCE_INVALID",
            "trusted PDF cannot be opened",
        ) from exc

    if actual_pages != expected_pages:
        raise TrustedSourceError(
            "RESEARCH_MCP_VISUAL_SOURCE_INVALID",
            "trusted PDF page_count differs from P3 manifest",
        )

    return TrustedPdfSource(
        document_sha256=normalized,
        path=source_path,
        file_size=stat_size,
        page_count=actual_pages,
        market=document.market,
        ticker=document.ticker,
        fiscal_year=document.fiscal_year,
        filing_type=document.filing_type,
    )
