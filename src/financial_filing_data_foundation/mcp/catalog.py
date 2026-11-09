from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from financial_filing_data_foundation.us_sec.feature_gate import is_us_development_enabled


CATALOG_SCHEMA_VERSION = "p8-mcp-catalog-v1"
_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


class CatalogError(RuntimeError):
    def __init__(self, reason_code: str, message: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


@dataclass(frozen=True, slots=True)
class CatalogDocument:
    document_sha256: str
    market: str
    ticker: str
    fiscal_year: int
    filing_type: str
    p3_artifact_dir: Path | None = None
    p5_artifact_dir: Path | None = None
    p6_artifact_dir: Path | None = None
    p7_artifact_dir: Path | None = None
    source_kind: str = "PDF"
    package_sha256: str | None = None
    sec_artifact_dir: Path | None = None
    raw_fiscal_period: str | None = None

    @property
    def filing_identity(self) -> tuple[str, str, int, str]:
        return (
            self.market.upper(),
            self.ticker.upper(),
            int(self.fiscal_year),
            self.filing_type.upper(),
        )

    def metadata(self) -> dict[str, Any]:
        result = {
            "document_sha256": self.document_sha256,
            "market": self.market,
            "ticker": self.ticker,
            "fiscal_year": self.fiscal_year,
            "filing_type": self.filing_type,
        }
        if self.source_kind.upper() != "PDF":
            result.update(
                {
                    "source_kind": self.source_kind,
                    "package_sha256": self.package_sha256,
                    "raw_fiscal_period": self.raw_fiscal_period,
                }
            )
        return result


@dataclass(frozen=True, slots=True)
class McpCatalog:
    project_root: Path
    catalog_path: Path
    documents: tuple[CatalogDocument, ...]

    @classmethod
    def load(
        cls,
        project_root: str | Path,
        catalog_path: str | Path,
    ) -> "McpCatalog":
        root = Path(project_root).expanduser().resolve()
        if not root.is_dir():
            raise CatalogError(
                "P8_CATALOG_INVALID",
                f"project root does not exist: {root}",
            )

        catalog = Path(catalog_path).expanduser()
        if not catalog.is_absolute():
            catalog = root / catalog
        catalog = catalog.resolve()
        _assert_within(root, catalog, "catalog")
        if not catalog.is_file():
            raise CatalogError(
                "P8_CATALOG_INVALID",
                f"catalog file does not exist: {catalog}",
            )

        try:
            payload = json.loads(catalog.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CatalogError(
                "P8_CATALOG_INVALID",
                f"cannot read catalog JSON: {exc}",
            ) from exc

        if not isinstance(payload, dict):
            raise CatalogError(
                "P8_CATALOG_INVALID",
                "catalog root must be a JSON object",
            )
        if payload.get("schema_version") != CATALOG_SCHEMA_VERSION:
            raise CatalogError(
                "P8_CATALOG_INVALID",
                "unsupported catalog schema_version",
            )
        raw_documents = payload.get("documents")
        if not isinstance(raw_documents, list):
            raise CatalogError(
                "P8_CATALOG_INVALID",
                "catalog documents must be a list",
            )

        documents: list[CatalogDocument] = []
        seen_sha: set[str] = set()
        seen_identity: set[tuple[str, str, int, str]] = set()
        for index, raw in enumerate(raw_documents):
            if not isinstance(raw, dict):
                raise CatalogError(
                    "P8_CATALOG_INVALID",
                    f"documents[{index}] must be an object",
                )
            document = _parse_document(root, raw, index)
            if document.document_sha256 in seen_sha:
                raise CatalogError(
                    "P8_CATALOG_INVALID",
                    f"duplicate document_sha256: {document.document_sha256}",
                )
            if document.filing_identity in seen_identity:
                raise CatalogError(
                    "P8_CATALOG_INVALID",
                    "duplicate filing identity: "
                    + repr(document.filing_identity),
                )
            seen_sha.add(document.document_sha256)
            seen_identity.add(document.filing_identity)
            documents.append(document)

        documents.sort(
            key=lambda item: (
                item.market.upper(),
                item.ticker.upper(),
                item.fiscal_year,
                item.filing_type.upper(),
                item.document_sha256,
            )
        )
        return cls(
            project_root=root,
            catalog_path=catalog,
            documents=tuple(documents),
        )

    def get(self, document_sha256: str) -> CatalogDocument | None:
        normalized = normalize_sha256(document_sha256)
        for document in self.documents:
            if document.document_sha256 == normalized:
                return document
        return None


def normalize_sha256(value: str) -> str:
    if not isinstance(value, str):
        raise CatalogError(
            "P8_INVALID_ARGUMENT",
            "document_sha256 must be a string",
        )
    normalized = value.strip().lower()
    if not _SHA256_RE.fullmatch(normalized):
        raise CatalogError(
            "P8_INVALID_ARGUMENT",
            "document_sha256 must be exactly 64 hexadecimal characters",
        )
    return normalized


def _required_text(raw: dict[str, Any], key: str, index: int) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise CatalogError(
            "P8_CATALOG_INVALID",
            f"documents[{index}].{key} must be a non-empty string",
        )
    return value.strip()


def _required_year(raw: dict[str, Any], index: int) -> int:
    value = raw.get("fiscal_year")
    if isinstance(value, bool) or not isinstance(value, int):
        raise CatalogError(
            "P8_CATALOG_INVALID",
            f"documents[{index}].fiscal_year must be an integer",
        )
    if value < 1900 or value > 2200:
        raise CatalogError(
            "P8_CATALOG_INVALID",
            f"documents[{index}].fiscal_year is outside supported bounds",
        )
    return int(value)


def _artifact_path(
    root: Path,
    raw: dict[str, Any],
    key: str,
    index: int,
) -> Path:
    text = _required_text(raw, key, index)
    candidate = Path(text)
    if candidate.is_absolute():
        raise CatalogError(
            "P8_PATH_OUTSIDE_PROJECT_ROOT",
            f"documents[{index}].{key} must be project-root-relative",
        )
    resolved = (root / candidate).resolve()
    _assert_within(root, resolved, f"documents[{index}].{key}")
    if not resolved.is_dir():
        raise CatalogError(
            "P8_CATALOG_INVALID",
            f"documents[{index}].{key} directory does not exist: {resolved}",
        )
    return resolved


def _assert_within(root: Path, path: Path, label: str) -> None:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise CatalogError(
            "P8_PATH_OUTSIDE_PROJECT_ROOT",
            f"{label} resolves outside project root",
        ) from exc


def _parse_document(
    root: Path,
    raw: dict[str, Any],
    index: int,
) -> CatalogDocument:
    document_sha256 = normalize_sha256(
        _required_text(raw, "document_sha256", index)
    )
    market = _required_text(raw, "market", index).upper()
    ticker = _required_text(raw, "ticker", index)
    filing_type = _required_text(raw, "filing_type", index).upper()
    fiscal_year = _required_year(raw, index)

    source_kind = str(raw.get("source_kind", "PDF")).strip().upper()
    if source_kind not in {"PDF", "SEC", "US_SEC"}:
        raise CatalogError(
            "P8_CATALOG_INVALID",
            f"documents[{index}].source_kind is unsupported",
        )
    if source_kind in {"SEC", "US_SEC"}:
        if market != "US":
            raise CatalogError(
                "P8_CATALOG_INVALID",
                f"documents[{index}] SEC source must use market US",
            )
        if not is_us_development_enabled():
            raise CatalogError(
                "P11_INVALID_US_IDENTITY",
                "US SEC catalog entries require FFDF_P11_US_DEV=1",
            )
        package_sha256 = normalize_sha256(
            _required_text(raw, "package_sha256", index)
        )
        if package_sha256 != document_sha256:
            raise CatalogError(
                "P8_CATALOG_INVALID",
                f"documents[{index}] document_sha256 must equal package_sha256 for SEC",
            )
        raw_period = _required_text(raw, "raw_fiscal_period", index).upper()
        if raw_period not in {"Q1", "Q2", "Q3", "FY"}:
            raise CatalogError(
                "P8_CATALOG_INVALID",
                f"documents[{index}].raw_fiscal_period is invalid",
            )
        return CatalogDocument(
            document_sha256=document_sha256,
            market=market,
            ticker=ticker,
            fiscal_year=fiscal_year,
            filing_type=filing_type,
            source_kind="SEC",
            package_sha256=package_sha256,
            sec_artifact_dir=_artifact_path(root, raw, "sec_artifact_dir", index),
            raw_fiscal_period=raw_period,
        )

    return CatalogDocument(
        document_sha256=document_sha256,
        market=market,
        ticker=ticker,
        fiscal_year=fiscal_year,
        filing_type=filing_type,
        p3_artifact_dir=_artifact_path(root, raw, "p3_artifact_dir", index),
        p5_artifact_dir=_artifact_path(root, raw, "p5_artifact_dir", index),
        p6_artifact_dir=_artifact_path(root, raw, "p6_artifact_dir", index),
        p7_artifact_dir=_artifact_path(root, raw, "p7_artifact_dir", index),
    )
