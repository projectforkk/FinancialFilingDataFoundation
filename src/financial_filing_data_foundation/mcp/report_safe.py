from __future__ import annotations

import copy
import re
from typing import Any

from .service import McpQueryService, McpServiceError, RESULT_SCHEMA_VERSION


REPORT_SAFE_VERSION = "p8-report-safe-v1"
_FILING_ORDER = {
    "Q1": 1,
    "H1": 2,
    "Q3": 3,
    "ANNUAL": 4,
    "ANNUAL_REPORT": 4,
}
_STATE_MARKER_WEIGHTS = {
    "实施公告": 8,
    "已经实施": 8,
    "已实施": 8,
    "审议通过": 6,
    "股东大会": 5,
    "尚需": 2,
    "拟": 1,
}


def _required_text(value: Any, name: str, max_length: int) -> str:
    if not isinstance(value, str):
        raise McpServiceError("P8_INVALID_ARGUMENT", f"{name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise McpServiceError("P8_INVALID_ARGUMENT", f"{name} must not be empty")
    if len(normalized) > max_length:
        raise McpServiceError(
            "P8_INVALID_ARGUMENT",
            f"{name} exceeds {max_length} characters",
        )
    return normalized


def _optional_year(value: Any, name: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise McpServiceError("P8_INVALID_ARGUMENT", f"{name} must be an integer")
    if value < 1900 or value > 2200:
        raise McpServiceError(
            "P8_INVALID_ARGUMENT",
            f"{name} is outside supported bounds",
        )
    return int(value)


def _bounded_int(
    value: Any,
    name: str,
    *,
    minimum: int,
    maximum: int,
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < minimum
        or value > maximum
    ):
        raise McpServiceError(
            "P8_INVALID_ARGUMENT",
            f"{name} must be an integer between {minimum} and {maximum}",
        )
    return int(value)


def _normalize_label(value: str) -> str:
    return re.sub(r"\s+", "", value).casefold()


def _filing_sort_key(metadata: dict[str, Any]) -> tuple[Any, ...]:
    filing_type = str(metadata.get("filing_type", "")).upper()
    return (
        int(metadata.get("fiscal_year", 0)),
        _FILING_ORDER.get(filing_type, 0),
        filing_type,
        str(metadata.get("document_sha256", "")),
    )


def _company_documents(
    service: McpQueryService,
    market: str,
    ticker: str,
    fiscal_year_from: int | None,
    fiscal_year_to: int | None,
) -> list[dict[str, Any]]:
    normalized_market = _required_text(market, "market", 32)
    normalized_ticker = _required_text(ticker, "ticker", 64)
    year_from = _optional_year(fiscal_year_from, "fiscal_year_from")
    year_to = _optional_year(fiscal_year_to, "fiscal_year_to")
    if year_from is not None and year_to is not None and year_from > year_to:
        raise McpServiceError(
            "P8_INVALID_ARGUMENT",
            "fiscal_year_from must be <= fiscal_year_to",
        )

    listed = service.list_documents(
        market=normalized_market,
        ticker=normalized_ticker,
    )["data"]["documents"]
    documents = [
        copy.deepcopy(row)
        for row in listed
        if (year_from is None or int(row["fiscal_year"]) >= year_from)
        and (year_to is None or int(row["fiscal_year"]) <= year_to)
    ]
    documents.sort(key=_filing_sort_key, reverse=True)
    return documents


def _result(tool: str, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "tool": tool,
        "document_sha256": None,
        "report_safe_version": REPORT_SAFE_VERSION,
        "data": data,
    }


def get_company_report_context(
    service: McpQueryService,
    market: str,
    ticker: str,
    fiscal_year_from: int | None = None,
    fiscal_year_to: int | None = None,
) -> dict[str, Any]:
    documents = _company_documents(
        service,
        market,
        ticker,
        fiscal_year_from,
        fiscal_year_to,
    )
    rows: list[dict[str, Any]] = []
    for metadata in documents:
        detail = service.get_document_summary_internal(metadata["document_sha256"])
        rows.append(
            {
                **metadata,
                "validation_status": detail["validation_status"],
                "compatibility_status": detail["compatibility_status"],
                "blocking_issue_count": detail["blocking_issue_count"],
                "review_issue_count": detail["review_issue_count"],
                "warning_issue_count": detail["warning_issue_count"],
                "reuse_eligible": detail["reuse_eligible"],
            }
        )

    latest = copy.deepcopy(rows[0]) if rows else None
    return _result(
        "ffdf_get_company_report_context",
        {
            "market": market.strip().upper(),
            "ticker": ticker.strip(),
            "filings": rows,
            "total": len(rows),
            "latest_filing": latest,
            "chronology_basis": (
                "fiscal_year plus filing_type order "
                "(Q1 < H1 < Q3 < ANNUAL); publication timestamps are not "
                "present in the P8 catalog"
            ),
            "report_guardrails": {
                "direct_disclosure_preferred": True,
                "preserve_source_labels": True,
                "newer_filing_state_overrides_older_filing_state": True,
                "section_search_requires_neighbor_context": True,
                "derived_values_must_declare_components": True,
            },
            "limitations": [
                "This catalog contains filing artifacts, not a complete temporary-announcement event feed.",
                "A latest periodic filing does not prove the latest real-world event state when later announcements are absent.",
                "REVIEW_REQUIRED does not mean unusable, but report claims should retain evidence and validation context.",
            ],
        },
    )


def search_company(
    service: McpQueryService,
    market: str,
    ticker: str,
    query: str,
    fiscal_year_from: int | None = None,
    fiscal_year_to: int | None = None,
    document_limit: int = 20,
    limit_per_document: int = 3,
    page_window: int = 1,
) -> dict[str, Any]:
    normalized_query = _required_text(query, "query", 512)
    checked_document_limit = _bounded_int(
        document_limit,
        "document_limit",
        minimum=1,
        maximum=50,
    )
    checked_per_document = _bounded_int(
        limit_per_document,
        "limit_per_document",
        minimum=1,
        maximum=10,
    )
    checked_window = _bounded_int(
        page_window,
        "page_window",
        minimum=0,
        maximum=2,
    )
    documents = _company_documents(
        service,
        market,
        ticker,
        fiscal_year_from,
        fiscal_year_to,
    )[:checked_document_limit]

    results: list[dict[str, Any]] = []
    documents_with_matches = 0
    for metadata in documents:
        sha = metadata["document_sha256"]
        detail = service.get_document(sha)["data"]
        bundle = service._bundle(sha)
        fts_limit = min(50, max(10, checked_per_document * 4))
        search = service.search_document(
            sha,
            normalized_query,
            fts_limit,
        )["data"]

        candidates: dict[int, dict[str, Any]] = {}
        query_folded = normalized_query.casefold()
        for page in bundle.pages:
            text = str(page.get("text", ""))
            if query_folded in text.casefold():
                page_no = int(page["page_no"])
                candidates[page_no] = {
                    "page_no": page_no,
                    "text": text,
                    "score": None,
                    "match_type": "literal",
                }

        for hit in search["results"]:
            page_no = int(hit["page_no"])
            existing = candidates.get(page_no)
            if existing is None:
                candidates[page_no] = {
                    "page_no": page_no,
                    "text": hit.get("text", ""),
                    "score": hit.get("score"),
                    "match_type": "fts",
                }
            else:
                existing["score"] = hit.get("score")
                existing["match_type"] = "literal+fts"

        ranked_hits: list[dict[str, Any]] = []
        for hit in candidates.values():
            text = str(hit.get("text", ""))
            markers = [
                marker
                for marker in _STATE_MARKER_WEIGHTS
                if marker in text
            ]
            hit["state_markers"] = markers
            hit["state_marker_score"] = sum(
                _STATE_MARKER_WEIGHTS[marker] for marker in markers
            )
            ranked_hits.append(hit)

        ranked_hits.sort(
            key=lambda hit: (
                -int(hit["state_marker_score"]),
                0 if str(hit["match_type"]).startswith("literal") else 1,
                float(hit["score"]) if hit.get("score") is not None else 0.0,
                int(hit["page_no"]),
            )
        )
        hits = ranked_hits[:checked_per_document]
        if not hits:
            continue
        documents_with_matches += 1
        for hit in hits:
            page_no = int(hit["page_no"])
            neighbor_nos = [
                candidate
                for candidate in range(
                    max(1, page_no - checked_window),
                    min(int(detail["page_count"]), page_no + checked_window) + 1,
                )
                if candidate != page_no
            ]
            neighbor_pages: list[dict[str, Any]] = []
            if neighbor_nos:
                neighbor_pages = service.read_pages(
                    sha,
                    neighbor_nos,
                )["data"]["pages"]
            results.append(
                {
                    "document": metadata,
                    "validation_status": detail["validation_status"],
                    "blocking_issue_count": detail["blocking_issue_count"],
                    "review_issue_count": detail["review_issue_count"],
                    "match_page": {
                        "page_no": page_no,
                        "score": hit.get("score"),
                        "match_type": hit.get("match_type"),
                        "state_markers": hit.get("state_markers", []),
                        "state_marker_score": hit.get("state_marker_score", 0),
                        "text": hit.get("text", ""),
                    },
                    "neighbor_pages": neighbor_pages,
                }
            )

    return _result(
        "ffdf_search_company",
        {
            "market": market.strip().upper(),
            "ticker": ticker.strip(),
            "query": normalized_query,
            "results": results,
            "documents_considered": len(documents),
            "documents_with_matches": documents_with_matches,
            "returned_hits": len(results),
            "ordering": (
                "newest filing first; within a filing, state-marker relevance "
                "then literal-substring match then P3 FTS score/page order"
            ),
            "page_window": checked_window,
            "report_usage": {
                "use_newer_disclosure_for_state": True,
                "read_neighbor_pages_before_declaring_section_complete": True,
                "do_not_infer_later_temporary_announcement_state": True,
            },
        },
    )


def find_table_rows(
    service: McpQueryService,
    market: str,
    ticker: str,
    label: str,
    match_mode: str = "exact",
    fiscal_year: int | None = None,
    filing_type: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    normalized_label = _required_text(label, "label", 256)
    normalized_target = _normalize_label(normalized_label)
    mode = _required_text(match_mode, "match_mode", 16).lower()
    if mode not in {"exact", "contains"}:
        raise McpServiceError(
            "P8_INVALID_ARGUMENT",
            "match_mode must be exact or contains",
        )
    checked_year = _optional_year(fiscal_year, "fiscal_year")
    normalized_filing_type = (
        _required_text(filing_type, "filing_type", 64).upper()
        if filing_type is not None
        else None
    )
    checked_limit = _bounded_int(limit, "limit", minimum=1, maximum=200)

    documents = _company_documents(
        service,
        market,
        ticker,
        checked_year,
        checked_year,
    )
    if normalized_filing_type is not None:
        documents = [
            row
            for row in documents
            if str(row.get("filing_type", "")).upper()
            == normalized_filing_type
        ]

    matches: list[dict[str, Any]] = []
    total_matches = 0
    for metadata in documents:
        bundle = service._bundle(metadata["document_sha256"])
        validation_status = str(
            getattr(
                bundle.validation_artifact.validation_status,
                "value",
                bundle.validation_artifact.validation_status,
            )
        )
        for table in sorted(bundle.tables, key=lambda row: (
            int(row.get("page_no", 0)),
            str(row.get("table_id", "")),
        )):
            for row in table.get("rows") or ():
                cells = list(row.get("cells") or ())
                label_cell = next(
                    (
                        cell
                        for cell in cells
                        if str(cell.get("role", "")).upper() == "LABEL"
                        and str(cell.get("text", "")).strip()
                    ),
                    cells[0] if cells else None,
                )
                if label_cell is None:
                    continue
                disclosure_label = str(label_cell.get("text", "")).strip()
                normalized_source = _normalize_label(disclosure_label)
                exact_match = normalized_source == normalized_target
                matched = exact_match or (
                    mode == "contains"
                    and normalized_target in normalized_source
                )
                if not matched:
                    continue
                total_matches += 1
                if len(matches) >= checked_limit:
                    continue
                matches.append(
                    {
                        "document": copy.deepcopy(metadata),
                        "validation_status": validation_status,
                        "page_no": int(table.get("page_no", 0)),
                        "table_id": str(table.get("table_id", "")),
                        "table_group_id": bundle.table_group_map.get(
                            str(table.get("table_id", ""))
                        ),
                        "row_index": row.get("row_index"),
                        "disclosure_label": disclosure_label,
                        "normalized_label": normalized_source,
                        "exact_match": exact_match,
                        "direct_disclosure": True,
                        "cells": copy.deepcopy(cells),
                    }
                )

    matches.sort(
        key=lambda row: (
            0 if row["exact_match"] else 1,
            -int(row["document"]["fiscal_year"]),
            -_FILING_ORDER.get(
                str(row["document"]["filing_type"]).upper(),
                0,
            ),
            int(row["page_no"]),
            int(row.get("row_index") or 0),
        )
    )
    matches = matches[:checked_limit]

    return _result(
        "ffdf_find_table_rows",
        {
            "market": market.strip().upper(),
            "ticker": ticker.strip(),
            "requested_label": normalized_label,
            "match_mode": mode,
            "matches": matches,
            "total_matches": total_matches,
            "returned": len(matches),
            "truncated": total_matches > len(matches),
            "report_usage": {
                "prefer_exact_direct_disclosure_over_manual_recomposition": True,
                "preserve_disclosure_label_in_report": True,
                "derived_aggregate_requires_explicit_component_fact_ids": True,
            },
        },
    )
