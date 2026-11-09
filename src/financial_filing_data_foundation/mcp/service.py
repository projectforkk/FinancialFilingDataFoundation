from __future__ import annotations

import copy
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Iterable

from financial_filing_data_foundation.facts import load_raw_facts
from financial_filing_data_foundation.native import load_native_document
from financial_filing_data_foundation.native.search import search_pages
from financial_filing_data_foundation.tables import load_reconstructed_tables
from financial_filing_data_foundation.validation import load_validation_result
from financial_filing_data_foundation.us_sec.parser import load_sec_artifacts
from financial_filing_data_foundation.us_sec.validation import load_sec_validation

from .catalog import CatalogDocument, CatalogError, McpCatalog, normalize_sha256


RESULT_SCHEMA_VERSION = "p8-mcp-result-v1"
_MAX_PAGE_TEXT_CHARS = 200_000
_MAX_SECTIONS = 1_000
_VALID_SEVERITIES = {"INFO", "WARNING", "REVIEW", "BLOCKING", "FAILURE"}


class McpServiceError(RuntimeError):
    def __init__(self, reason_code: str, message: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


@dataclass(frozen=True, slots=True)
class _DocumentBundle:
    catalog: CatalogDocument
    native: Any
    tables_artifact: Any
    facts_artifact: Any
    validation_artifact: Any
    pages: tuple[dict[str, Any], ...]
    sections: tuple[dict[str, Any], ...]
    tables: tuple[dict[str, Any], ...]
    groups: tuple[dict[str, Any], ...]
    facts: tuple[dict[str, Any], ...]
    evidence: tuple[dict[str, Any], ...]
    validation_report: dict[str, Any]
    validation_issues: tuple[dict[str, Any], ...]
    table_group_map: dict[str, str]
    page_index: dict[int, dict[str, Any]]
    table_index: dict[str, dict[str, Any]]
    fact_index: dict[str, dict[str, Any]]
    evidence_index: dict[str, dict[str, Any]]


class McpQueryService:
    def __init__(self, catalog: McpCatalog) -> None:
        self.catalog = catalog
        self._bundles: dict[str, _DocumentBundle] = {}

    def list_documents(
        self,
        market: str | None = None,
        ticker: str | None = None,
        fiscal_year: int | None = None,
    ) -> dict[str, Any]:
        market_filter = _optional_text_filter(market, "market", 32)
        ticker_filter = _optional_text_filter(ticker, "ticker", 64)
        if fiscal_year is not None:
            if isinstance(fiscal_year, bool) or not isinstance(fiscal_year, int):
                raise McpServiceError(
                    "P8_INVALID_ARGUMENT",
                    "fiscal_year must be an integer",
                )
            if fiscal_year < 1900 or fiscal_year > 2200:
                raise McpServiceError(
                    "P8_INVALID_ARGUMENT",
                    "fiscal_year is outside supported bounds",
                )

        rows: list[dict[str, Any]] = []
        for document in self.catalog.documents:
            if market_filter and document.market.casefold() != market_filter.casefold():
                continue
            if ticker_filter and document.ticker.casefold() != ticker_filter.casefold():
                continue
            if fiscal_year is not None and document.fiscal_year != fiscal_year:
                continue
            rows.append(document.metadata())
        return _success(
            "ffdf_list_documents",
            None,
            {
                "documents": rows,
                "total": len(rows),
            },
        )

    def get_document(self, document_sha256: str) -> dict[str, Any]:
        bundle = self._bundle(document_sha256)
        data = {
            **bundle.catalog.metadata(),
            "page_count": int(bundle.native.page_count),
            "table_count": int(bundle.tables_artifact.table_count),
            "table_group_count": int(bundle.tables_artifact.group_count),
            "raw_fact_count": int(bundle.facts_artifact.fact_count),
            "evidence_count": int(bundle.facts_artifact.evidence_count),
            "validation_status": _enum_value(
                bundle.validation_artifact.validation_status
            ),
            "compatibility_status": _enum_value(
                bundle.validation_artifact.compatibility_status
            ),
            "reuse_eligible": bool(bundle.validation_artifact.reuse_eligible),
            "blocking_issue_count": int(
                bundle.validation_artifact.blocking_issue_count
            ),
            "failure_issue_count": int(
                bundle.validation_artifact.failure_issue_count
            ),
            "review_issue_count": int(
                bundle.validation_artifact.review_issue_count
            ),
            "warning_issue_count": int(
                bundle.validation_artifact.warning_issue_count
            ),
            "issue_count": int(bundle.validation_artifact.issue_count),
        }
        return _success(
            "ffdf_get_document",
            bundle.catalog.document_sha256,
            data,
        )

    def search_document(
        self,
        document_sha256: str,
        query: str,
        limit: int = 10,
    ) -> dict[str, Any]:
        bundle = self._bundle(document_sha256)
        normalized_query = _required_text(query, "query", 512)
        checked_limit = _bounded_limit(limit, 10, 50)
        try:
            if bundle.catalog.source_kind.upper() == "SEC":
                needle = normalized_query.casefold()
                rows = []
                for page in bundle.pages:
                    text_value = str(page.get("text", ""))
                    position = text_value.casefold().find(needle)
                    if position >= 0:
                        rows.append(
                            {
                                "page_no": int(page.get("page_no", 0)),
                                "match_type": "LITERAL",
                                "snippet": text_value[max(0, position - 240): position + len(normalized_query) + 360],
                                "match_offset": position,
                            }
                        )
                        if len(rows) >= checked_limit:
                            break
            else:
                rows = list(
                    search_pages(
                        bundle.native.search_db_path,
                        normalized_query,
                        checked_limit,
                    )
                )
        except (sqlite3.Error, ValueError) as exc:
            raise McpServiceError(
                "P8_INVALID_ARGUMENT",
                f"invalid local FTS query: {exc}",
            ) from exc
        return _success(
            "ffdf_search_document",
            bundle.catalog.document_sha256,
            {
                "query": normalized_query,
                "results": rows,
                "returned": len(rows),
                "limit": checked_limit,
            },
        )

    def read_pages(
        self,
        document_sha256: str,
        page_nos: list[int],
    ) -> dict[str, Any]:
        bundle = self._bundle(document_sha256)
        pages = _page_numbers(page_nos, int(bundle.native.page_count))
        rows: list[dict[str, Any]] = []
        text_chars = 0
        for page_no in pages:
            page = bundle.page_index[page_no]
            text = str(page.get("text", ""))
            text_chars += len(text)
            if text_chars > _MAX_PAGE_TEXT_CHARS:
                raise McpServiceError(
                    "P8_PAYLOAD_LIMIT_EXCEEDED",
                    f"page text exceeds {_MAX_PAGE_TEXT_CHARS} characters",
                )
            rows.append(
                {
                    "page_no": page_no,
                    "width": page.get("width"),
                    "height": page.get("height"),
                    "rotation": page.get("rotation"),
                    "native_text_available": bool(
                        page.get("native_text_available")
                    ),
                    "pagination_kind": page.get("pagination_kind", "PHYSICAL_PDF"),
                    "normalizer_version": page.get("normalizer_version"),
                    "word_count": int(page.get("word_count", 0)),
                    "block_count": int(page.get("block_count", 0)),
                    "image_count": int(page.get("image_count", 0)),
                    "drawing_count": int(page.get("drawing_count", 0)),
                    "text": text,
                }
            )
        return _success(
            "ffdf_read_pages",
            bundle.catalog.document_sha256,
            {
                "pages": rows,
                "returned": len(rows),
                "text_chars": text_chars,
            },
        )

    def list_sections(self, document_sha256: str) -> dict[str, Any]:
        bundle = self._bundle(document_sha256)
        rows = [
            copy.deepcopy(row)
            for row in sorted(
                bundle.sections,
                key=lambda row: (
                    int(row.get("page_start", 0)),
                    int(row.get("page_end", 0)),
                    str(row.get("section_id", "")),
                ),
            )
        ]
        total = len(rows)
        truncated = total > _MAX_SECTIONS
        rows = rows[:_MAX_SECTIONS]
        return _success(
            "ffdf_list_sections",
            bundle.catalog.document_sha256,
            {
                "sections": rows,
                "total": total,
                "returned": len(rows),
                "truncated": truncated,
            },
        )

    def list_tables(
        self,
        document_sha256: str,
        page_no: int | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> dict[str, Any]:
        bundle = self._bundle(document_sha256)
        checked_offset = _offset(offset)
        checked_limit = _bounded_limit(limit, 50, 100)
        if page_no is not None:
            _validate_page_no(page_no, int(bundle.native.page_count))

        rows = [
            table
            for table in bundle.tables
            if page_no is None or int(table.get("page_no", 0)) == page_no
        ]
        rows = sorted(rows, key=_table_sort_key)
        summaries = [
            {
                "table_id": str(row["table_id"]),
                "candidate_id": row.get("candidate_id"),
                "page_no": int(row["page_no"]),
                "bbox": copy.deepcopy(row.get("bbox")),
                "row_count": int(row.get("row_count", 0)),
                "value_column_count": int(
                    row.get("value_column_count", 0)
                ),
                "table_group_id": bundle.table_group_map.get(
                    str(row["table_id"])
                ),
                "candidate_signals": list(
                    row.get("candidate_signals") or ()
                ),
                "quality_signals": list(
                    row.get("quality_signals") or ()
                ),
            }
            for row in rows
        ]
        return _paged_success(
            "ffdf_list_tables",
            bundle.catalog.document_sha256,
            "tables",
            summaries,
            checked_offset,
            checked_limit,
        )

    def get_table(
        self,
        document_sha256: str,
        table_id: str,
        max_rows: int = 100,
    ) -> dict[str, Any]:
        bundle = self._bundle(document_sha256)
        normalized_id = _required_text(table_id, "table_id", 256)
        checked_rows = _bounded_limit(max_rows, 100, 500)
        table = bundle.table_index.get(normalized_id)
        if table is None:
            raise McpServiceError(
                "P8_TABLE_NOT_FOUND",
                f"table not found: {normalized_id}",
            )

        result = copy.deepcopy(table)
        all_rows = list(result.get("rows") or ())
        result["rows"] = all_rows[:checked_rows]
        result["total_row_count"] = len(all_rows)
        result["returned_row_count"] = len(result["rows"])
        result["truncated"] = len(all_rows) > checked_rows
        result["table_group_id"] = bundle.table_group_map.get(normalized_id)
        return _success(
            "ffdf_get_table",
            bundle.catalog.document_sha256,
            result,
        )

    def list_raw_facts(
        self,
        document_sha256: str,
        page_no: int | None = None,
        metric_contains: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> dict[str, Any]:
        bundle = self._bundle(document_sha256)
        checked_offset = _offset(offset)
        checked_limit = _bounded_limit(limit, 50, 100)
        if page_no is not None:
            _validate_page_no(page_no, int(bundle.native.page_count))
        metric_filter = _optional_text_filter(
            metric_contains,
            "metric_contains",
            256,
        )

        rows: list[dict[str, Any]] = []
        for fact in bundle.facts:
            if page_no is not None and int(fact.get("page_no", 0)) != page_no:
                continue
            if metric_filter and metric_filter.casefold() not in str(
                fact.get("raw_metric_name", "")
            ).casefold():
                continue
            rows.append(fact)
        rows = sorted(rows, key=_fact_sort_key)
        return _paged_success(
            "ffdf_list_raw_facts",
            bundle.catalog.document_sha256,
            "facts",
            rows,
            checked_offset,
            checked_limit,
        )

    def get_fact(
        self,
        document_sha256: str,
        raw_fact_id: str,
    ) -> dict[str, Any]:
        bundle = self._bundle(document_sha256)
        normalized_id = _required_text(raw_fact_id, "raw_fact_id", 256)
        fact = bundle.fact_index.get(normalized_id)
        if fact is None:
            raise McpServiceError(
                "P8_FACT_NOT_FOUND",
                f"raw fact not found: {normalized_id}",
            )
        return _success(
            "ffdf_get_fact",
            bundle.catalog.document_sha256,
            copy.deepcopy(fact),
        )

    def get_evidence(
        self,
        document_sha256: str,
        evidence_id: str,
    ) -> dict[str, Any]:
        bundle = self._bundle(document_sha256)
        normalized_id = _required_text(evidence_id, "evidence_id", 256)
        evidence = bundle.evidence_index.get(normalized_id)
        if evidence is None:
            raise McpServiceError(
                "P8_EVIDENCE_NOT_FOUND",
                f"evidence not found: {normalized_id}",
            )
        return _success(
            "ffdf_get_evidence",
            bundle.catalog.document_sha256,
            copy.deepcopy(evidence),
        )

    def get_validation(
        self,
        document_sha256: str,
        include_issues: bool = True,
        severity: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> dict[str, Any]:
        bundle = self._bundle(document_sha256)
        checked_offset = _offset(offset)
        checked_limit = _bounded_limit(limit, 100, 100)
        normalized_severity = None
        if severity is not None:
            normalized_severity = _required_text(
                severity,
                "severity",
                32,
            ).upper()
            if normalized_severity not in _VALID_SEVERITIES:
                raise McpServiceError(
                    "P8_INVALID_ARGUMENT",
                    "severity must be one of "
                    + ", ".join(sorted(_VALID_SEVERITIES)),
                )

        report = copy.deepcopy(bundle.validation_report)
        if not include_issues:
            issues: list[dict[str, Any]] = []
            total = 0
        else:
            all_issues = [
                issue
                for issue in bundle.validation_issues
                if normalized_severity is None
                or str(issue.get("severity", "")).upper()
                == normalized_severity
            ]
            total = len(all_issues)
            issues = [
                copy.deepcopy(row)
                for row in all_issues[
                    checked_offset : checked_offset + checked_limit
                ]
            ]

        return _success(
            "ffdf_get_validation",
            bundle.catalog.document_sha256,
            {
                "report": report,
                "issues": issues,
                "issues_total": total,
                "issues_returned": len(issues),
                "issues_offset": checked_offset,
                "issues_limit": checked_limit,
                "issues_truncated": (
                    include_issues
                    and checked_offset + len(issues) < total
                ),
            },
        )

    def get_document_summary_internal(
        self,
        document_sha256: str,
    ) -> dict[str, Any]:
        """Read manifest-level document counts/status without loading JSONL bodies."""
        try:
            normalized = normalize_sha256(document_sha256)
        except CatalogError as exc:
            raise McpServiceError(exc.reason_code, str(exc)) from exc
        document = self.catalog.get(normalized)
        if document is None:
            raise McpServiceError(
                "P8_DOCUMENT_NOT_FOUND",
                f"document not found: {normalized}",
            )

        if document.source_kind.upper() == "SEC":
            if document.sec_artifact_dir is None:
                raise McpServiceError(
                    "P8_ARTIFACT_INVALID",
                    "SEC catalog entry has no artifact directory",
                )
            try:
                parsed = load_sec_artifacts(document.sec_artifact_dir)
                validation = load_sec_validation(
                    document.sec_artifact_dir.parent.parent
                    / "p7"
                    / parsed.package_sha256
                )
            except Exception as exc:
                raise McpServiceError(
                    "P8_ARTIFACT_INVALID",
                    "cannot read SEC artifact summary",
                ) from exc
            return {
                **document.metadata(),
                "page_count": len(parsed.pages),
                "table_count": len(parsed.tables),
                "table_group_count": 0,
                "raw_fact_count": len(parsed.facts),
                "evidence_count": len(parsed.evidence),
                "validation_status": validation.validation_status,
                "compatibility_status": validation.compatibility_status,
                "reuse_eligible": validation.reuse_eligible,
                "blocking_issue_count": validation.blocking_issue_count,
                "failure_issue_count": validation.failure_issue_count,
                "review_issue_count": validation.review_issue_count,
                "warning_issue_count": validation.warning_issue_count,
                "issue_count": validation.issue_count,
            }

        def load(path: Path, label: str) -> dict[str, Any]:
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise McpServiceError(
                    "P8_ARTIFACT_INVALID",
                    f"cannot read {label} manifest",
                ) from exc
            if not isinstance(raw, dict):
                raise McpServiceError(
                    "P8_ARTIFACT_INVALID",
                    f"{label} manifest root must be an object",
                )
            if str(raw.get("document_sha256") or "") != normalized:
                raise McpServiceError(
                    "P8_ARTIFACT_INVALID",
                    f"{label} document_sha256 mismatch",
                )
            return raw

        p3 = load(document.p3_artifact_dir / "document.json", "P3")
        p5 = load(document.p5_artifact_dir / "table_manifest.json", "P5")
        p6 = load(document.p6_artifact_dir / "fact_manifest.json", "P6")
        p7 = load(document.p7_artifact_dir / "validation_report.json", "P7")
        return {
            **document.metadata(),
            "page_count": int(p3.get("page_count") or 0),
            "table_count": int(p5.get("table_count") or 0),
            "table_group_count": int(p5.get("group_count") or 0),
            "raw_fact_count": int(p6.get("fact_count") or 0),
            "evidence_count": int(p6.get("evidence_count") or 0),
            "validation_status": str(p7.get("validation_status") or ""),
            "compatibility_status": str(p7.get("compatibility_status") or ""),
            "reuse_eligible": bool(p7.get("reuse_eligible")),
            "blocking_issue_count": int(p7.get("blocking_issue_count") or 0),
            "failure_issue_count": int(p7.get("failure_issue_count") or 0),
            "review_issue_count": int(p7.get("review_issue_count") or 0),
            "warning_issue_count": int(p7.get("warning_issue_count") or 0),
            "issue_count": int(p7.get("issue_count") or 0),
        }

    def all_pages_internal(
        self,
        document_sha256: str,
    ) -> tuple[dict[str, Any], ...]:
        """Return defensive P3 page copies for internal composed services."""
        bundle = self._bundle(document_sha256)
        return tuple(copy.deepcopy(item) for item in bundle.pages)

    def all_tables_internal(
        self,
        document_sha256: str,
    ) -> tuple[dict[str, Any], ...]:
        """Return defensive P5 table copies for internal composed services."""
        bundle = self._bundle(document_sha256)
        return tuple(copy.deepcopy(item) for item in bundle.tables)

    def table_group_map_internal(
        self,
        document_sha256: str,
    ) -> dict[str, str]:
        """Return a defensive table->group mapping for internal services."""
        bundle = self._bundle(document_sha256)
        return dict(bundle.table_group_map)

    def validation_status_internal(
        self,
        document_sha256: str,
    ) -> str:
        """Return the base P7 validation status for internal services."""
        bundle = self._bundle(document_sha256)
        return str(
            getattr(
                bundle.validation_artifact.validation_status,
                "value",
                bundle.validation_artifact.validation_status,
            )
        )

    def all_raw_facts_internal(
        self,
        document_sha256: str,
    ) -> tuple[dict[str, Any], ...]:
        """Return defensive copies for internal composed services only."""
        bundle = self._bundle(document_sha256)
        return tuple(copy.deepcopy(item) for item in bundle.facts)

    def get_table_group_internal(
        self,
        document_sha256: str,
        table_group_id: str,
    ) -> dict[str, Any]:
        """Resolve one deterministic P5 table group for internal services."""
        bundle = self._bundle(document_sha256)
        normalized = _required_text(
            table_group_id,
            "table_group_id",
            256,
        )
        for group in bundle.groups:
            group_id = str(group.get("group_id") or group.get("table_group_id") or "")
            if group_id == normalized:
                return copy.deepcopy(group)
        raise McpServiceError(
            "P8_TABLE_NOT_FOUND",
            f"table group not found: {normalized}",
        )

    def literal_page_search_internal(
        self,
        document_sha256: str,
        query: str,
        limit: int = 20,
    ) -> tuple[dict[str, Any], ...]:
        """Casefold literal P3 page scan for composed local services."""
        bundle = self._bundle(document_sha256)
        normalized_query = _required_text(query, "query", 512)
        checked_limit = _bounded_limit(limit, 20, 100)
        needle = normalized_query.casefold()
        rows: list[dict[str, Any]] = []
        for page in bundle.pages:
            page_text = str(page.get("text") or "")
            position = page_text.casefold().find(needle)
            if position < 0:
                continue
            start = max(0, position - 240)
            end = min(len(page_text), position + len(normalized_query) + 360)
            rows.append(
                {
                    "page_no": int(page.get("page_no") or 0),
                    "match_type": "LITERAL",
                    "snippet": page_text[start:end],
                    "match_offset": position,
                }
            )
            if len(rows) >= checked_limit:
                break
        return tuple(rows)

    def _bundle(self, document_sha256: str) -> _DocumentBundle:
        try:
            normalized = normalize_sha256(document_sha256)
        except CatalogError as exc:
            raise McpServiceError(
                exc.reason_code,
                str(exc),
            ) from exc
        bundle = self._bundles.get(normalized)
        if bundle is not None:
            return bundle

        document = self.catalog.get(normalized)
        if document is None:
            raise McpServiceError(
                "P8_DOCUMENT_NOT_FOUND",
                f"document not found: {normalized}",
            )

        bundle = _load_bundle(document)
        self._bundles[normalized] = bundle
        return bundle


def _load_bundle(document: CatalogDocument) -> _DocumentBundle:
    if document.source_kind.upper() == "SEC":
        return _load_sec_bundle(document)
    try:
        native = load_native_document(document.p3_artifact_dir)
        tables_artifact = load_reconstructed_tables(document.p5_artifact_dir)
        facts_artifact = load_raw_facts(
            document.p6_artifact_dir,
            document.p3_artifact_dir,
            document.p5_artifact_dir,
        )
        validation_artifact = load_validation_result(
            document.p7_artifact_dir,
            document.p3_artifact_dir,
            document.p5_artifact_dir,
            document.p6_artifact_dir,
        )
    except Exception as exc:
        raise McpServiceError(
            "P8_UPSTREAM_ARTIFACT_INVALID",
            "upstream artifact validation failed for "
            f"{document.document_sha256}: {exc}",
        ) from exc

    identities = {
        native.document_sha256,
        tables_artifact.document_sha256,
        facts_artifact.document_sha256,
        validation_artifact.document_sha256,
        document.document_sha256,
    }
    if len(identities) != 1:
        raise McpServiceError(
            "P8_UPSTREAM_ARTIFACT_INVALID",
            "catalog/P3/P5/P6/P7 document identity mismatch",
        )

    pages = tuple(_read_jsonl(native.pages_path))
    sections = tuple(_read_jsonl(native.sections_path))
    tables = tuple(_read_jsonl(tables_artifact.tables_path))
    groups = tuple(_read_jsonl(tables_artifact.groups_path))
    facts = tuple(_read_jsonl(facts_artifact.facts_path))
    evidence = tuple(_read_jsonl(facts_artifact.evidence_path))
    report = _read_json(validation_artifact.report_path)
    issues = tuple(_read_jsonl(validation_artifact.issues_path))

    group_map: dict[str, str] = {}
    for group in groups:
        group_id = str(group.get("group_id", ""))
        for table_id in group.get("member_table_ids") or ():
            table_key = str(table_id)
            existing = group_map.get(table_key)
            if existing is not None and existing != group_id:
                raise McpServiceError(
                    "P8_UPSTREAM_ARTIFACT_INVALID",
                    f"table belongs to multiple groups: {table_key}",
                )
            group_map[table_key] = group_id

    page_index = {int(row["page_no"]): row for row in pages}
    table_index = {str(row["table_id"]): row for row in tables}
    fact_index = {str(row["raw_fact_id"]): row for row in facts}
    evidence_index = {str(row["evidence_id"]): row for row in evidence}

    if len(page_index) != len(pages):
        raise McpServiceError(
            "P8_UPSTREAM_ARTIFACT_INVALID",
            "duplicate P3 page identity",
        )
    if len(table_index) != len(tables):
        raise McpServiceError(
            "P8_UPSTREAM_ARTIFACT_INVALID",
            "duplicate P5 table identity",
        )
    if len(fact_index) != len(facts):
        raise McpServiceError(
            "P8_UPSTREAM_ARTIFACT_INVALID",
            "duplicate P6 fact identity",
        )
    if len(evidence_index) != len(evidence):
        raise McpServiceError(
            "P8_UPSTREAM_ARTIFACT_INVALID",
            "duplicate P6 evidence identity",
        )

    return _DocumentBundle(
        catalog=document,
        native=native,
        tables_artifact=tables_artifact,
        facts_artifact=facts_artifact,
        validation_artifact=validation_artifact,
        pages=pages,
        sections=sections,
        tables=tables,
        groups=groups,
        facts=facts,
        evidence=evidence,
        validation_report=report,
        validation_issues=issues,
        table_group_map=group_map,
        page_index=page_index,
        table_index=table_index,
        fact_index=fact_index,
        evidence_index=evidence_index,
    )


def _load_sec_bundle(document: CatalogDocument) -> _DocumentBundle:
    if document.sec_artifact_dir is None:
        raise McpServiceError(
            "P8_UPSTREAM_ARTIFACT_INVALID",
            "SEC catalog entry has no artifact directory",
        )
    try:
        parsed = load_sec_artifacts(document.sec_artifact_dir)
        validation = load_sec_validation(document.sec_artifact_dir.parent.parent / "p7" / parsed.package_sha256)
    except Exception:
        # The catalog normally points at the P11 artifact directory and keeps P7
        # beside it.  A direct validation artifact is also accepted for small
        # local fixtures.
        try:
            parsed = load_sec_artifacts(document.sec_artifact_dir)
            validation = load_sec_validation(document.sec_artifact_dir)
        except Exception as exc:
            raise McpServiceError(
                "P8_UPSTREAM_ARTIFACT_INVALID",
                f"SEC upstream artifact validation failed for {document.document_sha256}: {exc}",
            ) from exc
    if parsed.package_sha256 != document.document_sha256:
        raise McpServiceError(
            "P8_UPSTREAM_ARTIFACT_INVALID",
            "catalog/SEC package identity mismatch",
        )
    tables = tuple(parsed.tables)
    facts = tuple(parsed.facts)
    evidence = tuple(parsed.evidence)
    pages = tuple(parsed.pages)
    sections = tuple(parsed.sections)
    issues = tuple(validation.issues)
    table_index = {str(row["table_id"]): row for row in tables}
    fact_index = {str(row["raw_fact_id"]): row for row in facts}
    evidence_index = {str(row["evidence_id"]): row for row in evidence}
    page_index = {int(row["page_no"]): row for row in pages}
    if len(page_index) != len(pages) or len(table_index) != len(tables) or len(fact_index) != len(facts) or len(evidence_index) != len(evidence):
        raise McpServiceError("P8_UPSTREAM_ARTIFACT_INVALID", "duplicate SEC artifact identity")
    native = SimpleNamespace(
        document_sha256=parsed.package_sha256,
        page_count=len(pages),
        search_db_path=None,
    )
    tables_artifact = SimpleNamespace(table_count=len(tables), group_count=0)
    facts_artifact = SimpleNamespace(fact_count=len(facts), evidence_count=len(evidence))
    return _DocumentBundle(
        catalog=document,
        native=native,
        tables_artifact=tables_artifact,
        facts_artifact=facts_artifact,
        validation_artifact=validation,
        pages=pages,
        sections=sections,
        tables=tables,
        groups=(),
        facts=facts,
        evidence=evidence,
        validation_report=validation.to_dict(),
        validation_issues=issues,
        table_group_map={},
        page_index=page_index,
        table_index=table_index,
        fact_index=fact_index,
        evidence_index=evidence_index,
    )


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise McpServiceError(
            "P8_UPSTREAM_ARTIFACT_INVALID",
            f"cannot read JSON {path.name}: {exc}",
        ) from exc
    if not isinstance(value, dict):
        raise McpServiceError(
            "P8_UPSTREAM_ARTIFACT_INVALID",
            f"{path.name} must contain a JSON object",
        )
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError(f"line {line_no} is not an object")
                rows.append(value)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise McpServiceError(
            "P8_UPSTREAM_ARTIFACT_INVALID",
            f"cannot read JSONL {path.name}: {exc}",
        ) from exc
    return rows


def _enum_value(value: Any) -> str:
    return str(getattr(value, "value", value))


def _success(
    tool: str,
    document_sha256: str | None,
    data: Any,
) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "tool": tool,
        "document_sha256": document_sha256,
        "data": data,
    }


def _paged_success(
    tool: str,
    document_sha256: str,
    key: str,
    rows: Iterable[dict[str, Any]],
    offset: int,
    limit: int,
) -> dict[str, Any]:
    values = list(rows)
    total = len(values)
    selected = [
        copy.deepcopy(row)
        for row in values[offset : offset + limit]
    ]
    return _success(
        tool,
        document_sha256,
        {
            key: selected,
            "offset": offset,
            "limit": limit,
            "total": total,
            "returned": len(selected),
            "truncated": offset + len(selected) < total,
        },
    )


def _required_text(value: Any, name: str, max_length: int) -> str:
    if not isinstance(value, str):
        raise McpServiceError(
            "P8_INVALID_ARGUMENT",
            f"{name} must be a string",
        )
    normalized = value.strip()
    if not normalized:
        raise McpServiceError(
            "P8_INVALID_ARGUMENT",
            f"{name} must not be empty",
        )
    if len(normalized) > max_length:
        raise McpServiceError(
            "P8_INVALID_ARGUMENT",
            f"{name} exceeds {max_length} characters",
        )
    return normalized


def _optional_text_filter(
    value: Any,
    name: str,
    max_length: int,
) -> str | None:
    if value is None:
        return None
    return _required_text(value, name, max_length)


def _offset(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise McpServiceError(
            "P8_INVALID_ARGUMENT",
            "offset must be an integer >= 0",
        )
    return int(value)


def _bounded_limit(value: Any, default: int, maximum: int) -> int:
    if value is None:
        value = default
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 1
        or value > maximum
    ):
        raise McpServiceError(
            "P8_INVALID_ARGUMENT",
            f"limit must be an integer between 1 and {maximum}",
        )
    return int(value)


def _validate_page_no(value: Any, page_count: int) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 1
        or value > page_count
    ):
        raise McpServiceError(
            "P8_INVALID_ARGUMENT",
            f"page_no must be between 1 and {page_count}",
        )
    return int(value)


def _page_numbers(values: Any, page_count: int) -> list[int]:
    if not isinstance(values, list):
        raise McpServiceError(
            "P8_INVALID_ARGUMENT",
            "page_nos must be a list of integers",
        )
    if not 1 <= len(values) <= 10:
        raise McpServiceError(
            "P8_INVALID_ARGUMENT",
            "page_nos must contain between 1 and 10 pages",
        )
    result = sorted({_validate_page_no(value, page_count) for value in values})
    if len(result) != len(values):
        raise McpServiceError(
            "P8_INVALID_ARGUMENT",
            "page_nos must be unique",
        )
    return result


def _table_sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
    bbox = row.get("bbox") or [0, 0, 0, 0]
    return (
        int(row.get("page_no", 0)),
        float(bbox[1]),
        float(bbox[0]),
        str(row.get("table_id", "")),
    )


def _fact_sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        int(row.get("page_no", 0)),
        str(row.get("table_id", "")),
        int(row.get("row_index", 0)),
        int(row.get("column_index", 0)),
        str(row.get("raw_fact_id", "")),
    )
