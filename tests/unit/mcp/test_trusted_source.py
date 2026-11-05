from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pymupdf
import pytest

from financial_filing_data_foundation.identity import FilingIdentity, FilingSlotKey
from financial_filing_data_foundation.mcp.catalog import McpCatalog
from financial_filing_data_foundation.mcp.trusted_source import (
    TrustedSourceError,
    resolve_trusted_pdf_source,
)
from financial_filing_data_foundation.registry import SQLiteRegistry


def _pdf(path: Path, text: str = "sample") -> None:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fixture(tmp_path: Path):
    root = tmp_path / "project"
    raw_root = root / "workspace" / "ingest" / "raw-store"
    raw_root.mkdir(parents=True)
    staging = raw_root / "staging.pdf"
    _pdf(staging)
    sha = _sha(staging)
    final = raw_root / "sha256" / sha[:2] / f"{sha}.pdf"
    final.parent.mkdir(parents=True)
    staging.replace(final)

    registry_path = root / "workspace" / "ingest" / "registry.sqlite"
    registry = SQLiteRegistry(registry_path)
    slot = FilingSlotKey(
        market="CN",
        company_id="605117",
        filing_type="ANNUAL",
        fiscal_year=2025,
        raw_fiscal_period="FY",
    )
    identity = FilingIdentity(slot=slot, amended=False)
    registry.register_document(final, expected_identity=identity)

    p3 = root / "p3" / sha
    p5 = root / "p5" / sha
    p6 = root / "p6" / sha
    p7 = root / "p7" / sha
    for path in (p3, p5, p6, p7):
        path.mkdir(parents=True)
    (p3 / "document.json").write_text(
        json.dumps(
            {
                "document_sha256": sha,
                "file_size": final.stat().st_size,
                "page_count": 1,
                "source_path": str(final),
            }
        ),
        encoding="utf-8",
    )
    catalog_path = root / "catalog.json"
    catalog_path.write_text(
        json.dumps(
            {
                "schema_version": "p8-mcp-catalog-v1",
                "documents": [
                    {
                        "document_sha256": sha,
                        "market": "CN",
                        "ticker": "605117",
                        "fiscal_year": 2025,
                        "filing_type": "ANNUAL",
                        "p3_artifact_dir": p3.relative_to(root).as_posix(),
                        "p5_artifact_dir": p5.relative_to(root).as_posix(),
                        "p6_artifact_dir": p6.relative_to(root).as_posix(),
                        "p7_artifact_dir": p7.relative_to(root).as_posix(),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return (
        McpCatalog.load(root, catalog_path),
        registry_path,
        raw_root,
        final,
        sha,
    )


def test_resolves_registered_immutable_pdf(tmp_path: Path) -> None:
    catalog, registry_path, raw_root, final, sha = _fixture(tmp_path)

    source = resolve_trusted_pdf_source(
        catalog=catalog,
        registry_path=registry_path,
        trusted_raw_root=raw_root,
        document_sha256=sha,
    )

    assert source.path == final.resolve()
    assert source.document_sha256 == sha
    assert source.page_count == 1
    assert "path" not in source.public_metadata()


def test_rejects_source_outside_trusted_root(tmp_path: Path) -> None:
    catalog, registry_path, raw_root, final, sha = _fixture(tmp_path)
    outside = tmp_path / "outside.pdf"
    outside.write_bytes(final.read_bytes())
    manifest = catalog.documents[0].p3_artifact_dir / "document.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["source_path"] = str(outside)
    manifest.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(TrustedSourceError) as exc_info:
        resolve_trusted_pdf_source(
            catalog=catalog,
            registry_path=registry_path,
            trusted_raw_root=raw_root,
            document_sha256=sha,
        )

    assert exc_info.value.reason_code == "RESEARCH_MCP_VISUAL_SOURCE_UNTRUSTED"


def test_rejects_sha_drift(tmp_path: Path) -> None:
    catalog, registry_path, raw_root, final, sha = _fixture(tmp_path)
    replacement = raw_root / "replacement.pdf"
    _pdf(replacement, "changed")
    final.write_bytes(replacement.read_bytes())

    with pytest.raises(TrustedSourceError) as exc_info:
        resolve_trusted_pdf_source(
            catalog=catalog,
            registry_path=registry_path,
            trusted_raw_root=raw_root,
            document_sha256=sha,
        )

    assert exc_info.value.reason_code == "RESEARCH_MCP_VISUAL_SOURCE_INVALID"


def test_rejects_unregistered_source_path(tmp_path: Path) -> None:
    catalog, registry_path, raw_root, final, sha = _fixture(tmp_path)
    duplicate = raw_root / "duplicate.pdf"
    duplicate.write_bytes(final.read_bytes())
    manifest = catalog.documents[0].p3_artifact_dir / "document.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["source_path"] = str(duplicate)
    manifest.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(TrustedSourceError) as exc_info:
        resolve_trusted_pdf_source(
            catalog=catalog,
            registry_path=registry_path,
            trusted_raw_root=raw_root,
            document_sha256=sha,
        )

    assert exc_info.value.reason_code == "RESEARCH_MCP_VISUAL_SOURCE_UNTRUSTED"


def test_rejects_unknown_document(tmp_path: Path) -> None:
    catalog, registry_path, raw_root, _, _ = _fixture(tmp_path)

    with pytest.raises(TrustedSourceError) as exc_info:
        resolve_trusted_pdf_source(
            catalog=catalog,
            registry_path=registry_path,
            trusted_raw_root=raw_root,
            document_sha256="f" * 64,
        )

    assert exc_info.value.reason_code == "RESEARCH_MCP_DOCUMENT_NOT_FOUND"
