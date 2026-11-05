from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from financial_filing_data_foundation.mcp.catalog import McpCatalog, normalize_sha256
from financial_filing_data_foundation.mcp.research_review_contract import (
    ResearchQualityState,
    ResearchReviewProfile,
    write_tools_enabled,
)
from financial_filing_data_foundation.mcp.service import McpQueryService, McpServiceError
from financial_filing_data_foundation.review import (
    POLICY_VERSION,
    ResolutionAction,
    ResolutionSubmission,
    ReviewError,
    Reviewability,
    active_resolutions,
    list_review_tasks as p9_list_review_tasks,
    load_resolved_snapshot,
    materialize_resolved_view,
    prepare_review_overlay,
    submit_resolution,
)


RESEARCH_REVIEW_RESULT_SCHEMA_VERSION = "research-review-mcp-result-v1"


class ResearchReviewError(RuntimeError):
    def __init__(self, reason_code: str, message: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _overlay_set_hash(
    document_sha256: str,
    base_validation_report_sha256: str,
    active_ids: Sequence[str],
) -> str:
    ordered = tuple(sorted(str(item) for item in active_ids))
    material = (
        document_sha256
        + "\0"
        + base_validation_report_sha256
        + "\0"
        + POLICY_VERSION
        + "\0"
        + "\0".join(ordered)
    )
    return _sha256_bytes(material.encode("utf-8"))


def _read_json(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ResearchReviewError(
            "RESEARCH_MCP_REVIEW_STATE_INVALID",
            f"cannot read review JSON: {path.name}",
        ) from exc
    if not isinstance(raw, dict):
        raise ResearchReviewError(
            "RESEARCH_MCP_REVIEW_STATE_INVALID",
            f"review JSON root is invalid: {path.name}",
        )
    return raw


def _read_jsonl(path: Path) -> tuple[dict[str, Any], ...]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        raise ResearchReviewError(
            "RESEARCH_MCP_RESOLVED_STORE_INVALID",
            f"cannot read resolved JSONL: {path.name}",
        ) from exc
    rows: list[dict[str, Any]] = []
    for line in lines:
        if not line:
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ResearchReviewError(
                "RESEARCH_MCP_RESOLVED_STORE_INVALID",
                f"resolved JSONL is invalid: {path.name}",
            ) from exc
        if not isinstance(raw, dict):
            raise ResearchReviewError(
                "RESEARCH_MCP_RESOLVED_STORE_INVALID",
                f"resolved JSONL row is invalid: {path.name}",
            )
        rows.append(raw)
    return tuple(rows)


def _task_to_dict(task: Any) -> dict[str, Any]:
    return {
        "review_task_id": task.review_task_id,
        "document_sha256": task.document_sha256,
        "base_validation_report_sha256": task.base_validation_report_sha256,
        "issue_id": task.issue_id,
        "reason_code": task.reason_code,
        "message": task.message,
        "observed": dict(task.observed),
        "reviewability": task.reviewability.value,
        "supported_actions": list(task.supported_actions),
        "required_evidence_types": list(task.required_evidence_types),
        "scope": task.scope,
        "page_no": task.page_no,
        "table_id": task.table_id,
        "raw_fact_ids": list(task.raw_fact_ids),
        "evidence_ids": list(task.evidence_ids),
    }


def _resolution_to_summary(item: Any) -> dict[str, Any]:
    return {
        "resolution_id": item.resolution_id,
        "review_task_id": item.review_task_id,
        "issue_id": item.issue_id,
        "reason_code": item.reason_code,
        "action": item.action.value,
        "target": dict(item.target),
        "value": item.value,
        "evidence_refs": [dict(ref) for ref in item.evidence_refs],
        "evidence_pages": list(item.evidence_pages),
        "reviewer_type": item.reviewer_type.value,
        "reviewer_id": item.reviewer_id,
        "reviewed_at": item.reviewed_at,
    }


def _success(tool: str, document_sha256: str, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": RESEARCH_REVIEW_RESULT_SCHEMA_VERSION,
        "tool": tool,
        "document_sha256": document_sha256,
        "data": data,
    }


class ResearchReviewService:
    def __init__(
        self,
        *,
        project_root: str | Path,
        catalog: McpCatalog,
        p8_service: McpQueryService,
        review_root: str | Path,
        profile: ResearchReviewProfile | str = ResearchReviewProfile.RESEARCH_FALLBACK,
    ) -> None:
        self.project_root = Path(project_root).expanduser().resolve()
        self.catalog = catalog
        self.p8 = p8_service
        self.review_root = Path(review_root)
        if not self.review_root.is_absolute():
            self.review_root = self.project_root / self.review_root
        self.review_root = self.review_root.resolve()
        try:
            self.review_root.relative_to(self.project_root)
        except ValueError as exc:
            raise ResearchReviewError(
                "RESEARCH_MCP_REVIEW_STATE_INVALID",
                "review_root lies outside project root",
            ) from exc
        try:
            self.profile = (
                profile
                if isinstance(profile, ResearchReviewProfile)
                else ResearchReviewProfile(str(profile))
            )
        except ValueError as exc:
            raise ResearchReviewError(
                "RESEARCH_MCP_REVIEW_STATE_INVALID",
                "invalid Research Review runtime profile",
            ) from exc

    def _document_sha(self, document_sha256: str) -> str:
        try:
            normalized = normalize_sha256(document_sha256)
        except Exception as exc:
            raise ResearchReviewError(
                "RESEARCH_MCP_DOCUMENT_NOT_FOUND",
                "document_sha256 is invalid",
            ) from exc
        if self.catalog.get(normalized) is None:
            raise ResearchReviewError(
                "RESEARCH_MCP_DOCUMENT_NOT_FOUND",
                "document is not present in the configured catalog",
            )
        return normalized

    def _review_dir(self, document_sha256: str) -> Path:
        return self.review_root / self._document_sha(document_sha256)

    def _base_document(self, document_sha256: str) -> dict[str, Any]:
        try:
            return dict(self.p8.get_document(document_sha256)["data"])
        except McpServiceError as exc:
            raise ResearchReviewError(
                "RESEARCH_MCP_DOCUMENT_NOT_FOUND",
                str(exc),
            ) from exc

    def _review_runtime(
        self,
        document_sha256: str,
    ) -> dict[str, Any]:
        sha = self._document_sha(document_sha256)
        review_dir = self._review_dir(sha)
        if not review_dir.is_dir():
            return {
                "review_dir": review_dir,
                "exists": False,
                "tasks": (),
                "active": (),
                "base_validation_report_sha256": None,
                "overlay_set_hash": None,
                "snapshot": None,
            }

        manifest = _read_json(review_dir / "review_manifest.json")
        if str(manifest.get("document_sha256") or "") != sha:
            raise ResearchReviewError(
                "RESEARCH_MCP_REVIEW_STATE_INVALID",
                "review manifest document_sha256 mismatch",
            )
        base_hash = str(manifest.get("base_validation_report_sha256") or "")
        if len(base_hash) != 64:
            raise ResearchReviewError(
                "RESEARCH_MCP_REVIEW_STATE_INVALID",
                "review manifest base validation hash is invalid",
            )
        try:
            tasks = p9_list_review_tasks(review_dir)
            active = active_resolutions(review_dir)
        except ReviewError as exc:
            raise ResearchReviewError(
                "RESEARCH_MCP_REVIEW_STATE_INVALID",
                f"{exc.reason_code}: {exc}",
            ) from exc

        active_ids = tuple(sorted(item.resolution_id for item in active))
        overlay_hash = _overlay_set_hash(sha, base_hash, active_ids)
        snapshot_dir = review_dir / "snapshots" / overlay_hash
        snapshot = None
        if snapshot_dir.is_dir():
            try:
                snapshot = load_resolved_snapshot(snapshot_dir, review_dir)
            except ReviewError as exc:
                raise ResearchReviewError(
                    "RESEARCH_MCP_RESOLVED_STORE_INVALID",
                    f"{exc.reason_code}: {exc}",
                ) from exc

        return {
            "review_dir": review_dir,
            "exists": True,
            "tasks": tasks,
            "active": active,
            "base_validation_report_sha256": base_hash,
            "overlay_set_hash": overlay_hash,
            "snapshot": snapshot,
        }

    def get_review_state(self, document_sha256: str) -> dict[str, Any]:
        sha = self._document_sha(document_sha256)
        base = self._base_document(sha)
        try:
            runtime = self._review_runtime(sha)
        except ResearchReviewError as exc:
            return _success(
                "ffdf_get_review_state",
                sha,
                {
                    "quality_state": ResearchQualityState.INVALID_REVIEW_STATE.value,
                    "base_validation_status": base.get("validation_status"),
                    "base_reuse_eligible": bool(base.get("reuse_eligible")),
                    "error": {
                        "reason_code": exc.reason_code,
                        "message": str(exc),
                    },
                    "profile": self.profile.value,
                    "write_enabled": write_tools_enabled(self.profile),
                },
            )

        base_status = str(base.get("validation_status") or "")
        base_reuse = bool(base.get("reuse_eligible"))
        if (
            base_status in {"FAIL", "BLOCKED"}
            or int(base.get("blocking_issue_count") or 0) > 0
        ):
            quality = ResearchQualityState.BLOCKED
        elif not runtime["exists"]:
            quality = (
                ResearchQualityState.COMPLETE_BASE
                if base_status == "PASS" and base_reuse
                else ResearchQualityState.NEEDS_REVIEW
            )
        else:
            tasks = runtime["tasks"]
            active = runtime["active"]
            snapshot = runtime["snapshot"]
            unsupported = sum(
                1 for task in tasks if task.reviewability is Reviewability.UNSUPPORTED
            )
            if active and snapshot is None:
                quality = ResearchQualityState.NEEDS_MATERIALIZATION
            elif snapshot is None:
                if unsupported:
                    quality = ResearchQualityState.NEEDS_UPSTREAM_FIX
                elif base_status == "PASS" and base_reuse and not tasks:
                    quality = ResearchQualityState.COMPLETE_BASE
                else:
                    quality = ResearchQualityState.NEEDS_REVIEW
            else:
                report = snapshot.report
                resolved_status = str(report.get("resolved_validation_status") or "")
                resolved_reuse = bool(report.get("resolved_reuse_eligible"))
                unresolved = int(report.get("unresolved_review_issue_count") or 0)
                unsupported = int(report.get("unsupported_review_issue_count") or 0)
                if resolved_status in {"FAIL", "BLOCKED"}:
                    quality = ResearchQualityState.BLOCKED
                elif unsupported > 0:
                    quality = ResearchQualityState.NEEDS_UPSTREAM_FIX
                elif (
                    resolved_status == "PASS"
                    and resolved_reuse
                    and unresolved == 0
                ):
                    quality = ResearchQualityState.COMPLETE_REVIEWED
                else:
                    quality = ResearchQualityState.NEEDS_REVIEW

        snapshot = runtime["snapshot"]
        snapshot_report = {} if snapshot is None else dict(snapshot.report)
        tasks = runtime["tasks"]
        active = runtime["active"]
        data = {
            "quality_state": quality.value,
            "base_validation_status": base_status,
            "base_reuse_eligible": base_reuse,
            "base_review_issue_count": int(base.get("review_issue_count") or 0),
            "base_blocking_issue_count": int(base.get("blocking_issue_count") or 0),
            "has_review_overlay": bool(runtime["exists"]),
            "review_task_count": len(tasks),
            "supported_review_task_count": sum(
                1 for task in tasks if task.reviewability is Reviewability.SUPPORTED
            ),
            "unsupported_review_task_count": sum(
                1 for task in tasks if task.reviewability is Reviewability.UNSUPPORTED
            ),
            "active_resolution_count": len(active),
            "active_resolution_ids": sorted(item.resolution_id for item in active),
            "active_overlay_set_hash": runtime["overlay_set_hash"],
            "snapshot_available": snapshot is not None,
            "snapshot_overlay_set_hash": (
                None if snapshot is None else snapshot.overlay_set_hash
            ),
            "resolved_validation_status": snapshot_report.get(
                "resolved_validation_status"
            ),
            "resolved_reuse_eligible": snapshot_report.get(
                "resolved_reuse_eligible"
            ),
            "resolved_review_issue_count": snapshot_report.get(
                "resolved_review_issue_count"
            ),
            "unresolved_review_issue_count": snapshot_report.get(
                "unresolved_review_issue_count"
            ),
            "unsupported_review_issue_count": snapshot_report.get(
                "unsupported_review_issue_count"
            ),
            "base_validation_report_sha256": runtime[
                "base_validation_report_sha256"
            ],
            "profile": self.profile.value,
            "write_enabled": write_tools_enabled(self.profile),
        }
        return _success("ffdf_get_review_state", sha, data)

    def _resolved_rows(
        self,
        document_sha256: str,
    ) -> tuple[tuple[dict[str, Any], ...], str | None]:
        sha = self._document_sha(document_sha256)
        runtime = self._review_runtime(sha)
        snapshot = runtime["snapshot"]
        if runtime["active"] and snapshot is None:
            raise ResearchReviewError(
                "RESEARCH_MCP_REVIEW_STATE_CHANGED",
                "active resolutions exist without a matching materialized snapshot",
            )
        if snapshot is None:
            facts = self.p8.all_raw_facts_internal(sha)
            rows = []
            for fact in facts:
                row = dict(fact)
                row["effective_period_label"] = fact.get("raw_period_label")
                row["effective_unit"] = fact.get("raw_unit")
                row["effective_scope"] = fact.get("raw_scope")
                row["overlay_resolution_ids"] = []
                rows.append(row)
            return tuple(rows), None
        return _read_jsonl(snapshot.resolved_facts_path), snapshot.overlay_set_hash

    def get_resolved_fact(
        self,
        document_sha256: str,
        raw_fact_id: str,
    ) -> dict[str, Any]:
        sha = self._document_sha(document_sha256)
        try:
            raw = dict(self.p8.get_fact(sha, raw_fact_id)["data"])
        except McpServiceError as exc:
            raise ResearchReviewError(
                "RESEARCH_MCP_FACT_NOT_FOUND",
                str(exc),
            ) from exc
        rows, overlay_hash = self._resolved_rows(sha)
        resolved = next(
            (item for item in rows if str(item.get("raw_fact_id")) == raw_fact_id),
            None,
        )
        if resolved is None:
            raise ResearchReviewError(
                "RESEARCH_MCP_RESOLVED_STORE_INVALID",
                "raw fact is missing from effective fact set",
            )
        effective = {
            "raw_fact_id": raw_fact_id,
            "raw_metric_name": raw.get("raw_metric_name"),
            "raw_value": raw.get("raw_value"),
            "parsed_numeric_value": raw.get("parsed_numeric_value"),
            "period": resolved.get("effective_period_label"),
            "unit": resolved.get("effective_unit"),
            "scope": resolved.get("effective_scope"),
            "page_no": raw.get("page_no"),
            "table_id": raw.get("table_id"),
            "evidence_id": raw.get("evidence_id"),
        }
        return _success(
            "ffdf_get_resolved_fact",
            sha,
            {
                "raw": raw,
                "effective": effective,
                "review": {
                    "applied": bool(resolved.get("overlay_resolution_ids")),
                    "resolution_ids": list(
                        resolved.get("overlay_resolution_ids") or []
                    ),
                    "overlay_set_hash": overlay_hash,
                },
                "quality_state": self.get_review_state(sha)["data"][
                    "quality_state"
                ],
            },
        )

    def list_resolved_facts(
        self,
        document_sha256: str,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> dict[str, Any]:
        sha = self._document_sha(document_sha256)
        if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
            raise ResearchReviewError(
                "RESEARCH_MCP_REVIEW_STATE_INVALID",
                "offset must be a non-negative integer",
            )
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ResearchReviewError(
                "RESEARCH_MCP_REVIEW_STATE_INVALID",
                "limit must be an integer from 1 to 100",
            )
        rows, overlay_hash = self._resolved_rows(sha)
        ordered = tuple(
            sorted(rows, key=lambda item: str(item.get("raw_fact_id") or ""))
        )
        page = ordered[offset : offset + limit]
        return _success(
            "ffdf_list_resolved_facts",
            sha,
            {
                "facts": [dict(item) for item in page],
                "total": len(ordered),
                "offset": offset,
                "limit": limit,
                "truncated": offset + len(page) < len(ordered),
                "overlay_set_hash": overlay_hash,
            },
        )

    def list_review_tasks(
        self,
        document_sha256: str,
    ) -> dict[str, Any]:
        sha = self._document_sha(document_sha256)
        runtime = self._review_runtime(sha)
        tasks = runtime["tasks"]
        active = runtime["active"]
        active_task_ids = {item.review_task_id for item in active}
        return _success(
            "ffdf_list_review_tasks",
            sha,
            {
                "tasks": [
                    {
                        **_task_to_dict(task),
                        "has_active_resolution": (
                            task.review_task_id in active_task_ids
                        ),
                    }
                    for task in tasks
                ],
                "total": len(tasks),
                "quality_state": self.get_review_state(sha)["data"][
                    "quality_state"
                ],
            },
        )

    def get_review_context(
        self,
        document_sha256: str,
        review_task_id: str,
    ) -> dict[str, Any]:
        sha = self._document_sha(document_sha256)
        runtime = self._review_runtime(sha)
        task = next(
            (
                item
                for item in runtime["tasks"]
                if item.review_task_id == review_task_id
            ),
            None,
        )
        if task is None:
            raise ResearchReviewError(
                "RESEARCH_MCP_REVIEW_TASK_NOT_FOUND",
                "review task not found",
            )

        facts: list[dict[str, Any]] = []
        for fact_id in task.raw_fact_ids:
            try:
                facts.append(dict(self.p8.get_fact(sha, fact_id)["data"]))
            except McpServiceError as exc:
                raise ResearchReviewError(
                    "RESEARCH_MCP_REVIEW_STATE_INVALID",
                    f"review task references missing raw fact: {fact_id}",
                ) from exc

        evidence: list[dict[str, Any]] = []
        for evidence_id in task.evidence_ids:
            try:
                evidence.append(
                    dict(self.p8.get_evidence(sha, evidence_id)["data"])
                )
            except McpServiceError as exc:
                raise ResearchReviewError(
                    "RESEARCH_MCP_REVIEW_STATE_INVALID",
                    f"review task references missing evidence: {evidence_id}",
                ) from exc

        table = None
        if task.table_id:
            try:
                table = dict(self.p8.get_table(sha, task.table_id, 100)["data"])
            except McpServiceError as exc:
                raise ResearchReviewError(
                    "RESEARCH_MCP_TABLE_NOT_FOUND",
                    f"review task table is missing: {task.table_id}",
                ) from exc

        pages: list[dict[str, Any]] = []
        if task.page_no is not None:
            page_count = int(self._base_document(sha).get("page_count") or 0)
            page_nos = [
                page_no
                for page_no in range(
                    max(1, int(task.page_no) - 1),
                    min(page_count, int(task.page_no) + 1) + 1,
                )
            ]
            if page_nos:
                pages = list(self.p8.read_pages(sha, page_nos)["data"]["pages"])

        active_for_task = [
            _resolution_to_summary(item)
            for item in runtime["active"]
            if item.review_task_id == task.review_task_id
        ]
        targets: list[dict[str, Any]] = []
        if table is not None:
            targets.append(
                {
                    "kind": "TABLE",
                    "table_id": task.table_id,
                    "table_group_id": table.get("table_group_id"),
                    "page_no": table.get("page_no"),
                    "mode": "TABLE_WITH_HEADER",
                }
            )
        if task.page_no is not None:
            targets.append(
                {
                    "kind": "PAGE",
                    "page_no": int(task.page_no),
                    "detail": "NORMAL",
                }
            )

        return _success(
            "ffdf_get_review_context",
            sha,
            {
                "task": _task_to_dict(task),
                "raw_facts": facts,
                "evidence": evidence,
                "table": table,
                "neighbor_pages": pages,
                "active_resolutions": active_for_task,
                "review_state": self.get_review_state(sha)["data"],
                "recommended_visual_targets": targets,
            },
        )

    def locate_evidence(
        self,
        document_sha256: str,
        query: str,
        *,
        limit: int = 10,
    ) -> dict[str, Any]:
        sha = self._document_sha(document_sha256)
        if not isinstance(query, str) or not query.strip():
            raise ResearchReviewError(
                "RESEARCH_MCP_LOCATOR_NO_MATCH",
                "query must be a non-blank string",
            )
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 20:
            raise ResearchReviewError(
                "RESEARCH_MCP_REVIEW_STATE_INVALID",
                "limit must be an integer from 1 to 20",
            )
        normalized_query = query.strip()

        pages_by_no: dict[int, dict[str, Any]] = {}
        try:
            fts_rows = self.p8.search_document(
                sha,
                normalized_query,
                min(50, limit * 4),
            )["data"]["results"]
        except McpServiceError:
            fts_rows = []
        for row in fts_rows:
            page_no = int(row.get("page_no") or 0)
            if page_no < 1:
                continue
            pages_by_no.setdefault(
                page_no,
                {
                    "page_no": page_no,
                    "match_types": set(),
                    "fts": [],
                    "literal": None,
                },
            )
            pages_by_no[page_no]["match_types"].add("FTS")
            pages_by_no[page_no]["fts"].append(dict(row))

        literal_rows = self.p8.literal_page_search_internal(
            sha,
            normalized_query,
            max(limit * 4, 20),
        )
        for row in literal_rows:
            page_no = int(row.get("page_no") or 0)
            if page_no < 1:
                continue
            pages_by_no.setdefault(
                page_no,
                {
                    "page_no": page_no,
                    "match_types": set(),
                    "fts": [],
                    "literal": None,
                },
            )
            pages_by_no[page_no]["match_types"].add("LITERAL")
            pages_by_no[page_no]["literal"] = dict(row)

        selected = sorted(
            pages_by_no.values(),
            key=lambda row: (
                0 if "LITERAL" in row["match_types"] else 1,
                row["page_no"],
            ),
        )[:limit]

        matches: list[dict[str, Any]] = []
        visual_targets: list[dict[str, Any]] = []
        seen_target: set[tuple[str, str]] = set()

        for hit in selected:
            page_no = int(hit["page_no"])
            page_payload = self.p8.read_pages(sha, [page_no])["data"]["pages"][0]
            page_text = str(page_payload.get("text") or "")
            literal = hit.get("literal")
            if isinstance(literal, dict) and literal.get("snippet"):
                snippet = str(literal["snippet"])
            else:
                folded = page_text.casefold()
                pos = folded.find(normalized_query.casefold())
                if pos < 0:
                    snippet = page_text[:600]
                else:
                    snippet = page_text[
                        max(0, pos - 240) : min(
                            len(page_text),
                            pos + len(normalized_query) + 360,
                        )
                    ]

            table_payload = self.p8.list_tables(
                sha,
                page_no,
                0,
                100,
            )["data"]
            tables = list(table_payload.get("tables") or [])
            fact_payload = self.p8.list_raw_facts(
                sha,
                page_no,
                None,
                0,
                100,
            )["data"]
            facts = list(fact_payload.get("facts") or [])

            matches.append(
                {
                    "page_no": page_no,
                    "match_types": sorted(hit["match_types"]),
                    "snippet": snippet,
                    "tables": tables,
                    "raw_facts": facts,
                }
            )

            for table in tables:
                table_id = str(table.get("table_id") or "")
                if table_id and ("TABLE", table_id) not in seen_target:
                    seen_target.add(("TABLE", table_id))
                    visual_targets.append(
                        {
                            "kind": "TABLE",
                            "table_id": table_id,
                            "table_group_id": table.get("table_group_id"),
                            "page_no": page_no,
                            "mode": "TABLE_WITH_HEADER",
                        }
                    )
            page_key = ("PAGE", str(page_no))
            if page_key not in seen_target:
                seen_target.add(page_key)
                visual_targets.append(
                    {
                        "kind": "PAGE",
                        "page_no": page_no,
                        "detail": "NORMAL",
                    }
                )

        return _success(
            "ffdf_locate_evidence",
            sha,
            {
                "query": normalized_query,
                "matched": bool(matches),
                "matches": matches,
                "returned": len(matches),
                "recommended_visual_targets": visual_targets[:20],
                "interpretation": (
                    "Locator hits are evidence candidates, not new RawFacts. "
                    "If the PDF discloses a value that P6 did not extract, route "
                    "the case as P6_MISSING_FACT_CANDIDATE / upstream fix."
                ),
            },
        )

    def _require_write(self) -> None:
        if not write_tools_enabled(self.profile):
            raise ResearchReviewError(
                "RESEARCH_MCP_WRITE_DISABLED",
                "write-through tools are disabled in RESEARCH_FALLBACK profile",
            )

    def prepare_review_overlay(
        self,
        document_sha256: str,
    ) -> dict[str, Any]:
        self._require_write()
        sha = self._document_sha(document_sha256)
        self.review_root.mkdir(parents=True, exist_ok=True)
        try:
            artifact = prepare_review_overlay(
                self.project_root,
                self.catalog.catalog_path,
                sha,
                self.review_root,
            )
        except ReviewError as exc:
            raise ResearchReviewError(
                "RESEARCH_MCP_REVIEW_STATE_INVALID",
                f"{exc.reason_code}: {exc}",
            ) from exc
        return _success(
            "ffdf_prepare_review_overlay",
            sha,
            {
                "review": artifact.to_dict(),
                "review_state": self.get_review_state(sha)["data"],
            },
        )

    def submit_review_resolution(
        self,
        document_sha256: str,
        submission: Mapping[str, Any],
        *,
        expected_base_validation_report_sha256: str,
        expected_overlay_set_hash_before: str,
    ) -> dict[str, Any]:
        self._require_write()
        sha = self._document_sha(document_sha256)
        runtime = self._review_runtime(sha)
        if not runtime["exists"]:
            raise ResearchReviewError(
                "RESEARCH_MCP_REVIEW_STATE_CHANGED",
                "review overlay does not exist",
            )
        if (
            runtime["base_validation_report_sha256"]
            != expected_base_validation_report_sha256
            or runtime["overlay_set_hash"] != expected_overlay_set_hash_before
        ):
            raise ResearchReviewError(
                "RESEARCH_MCP_REVIEW_STATE_CHANGED",
                "review base or active overlay set changed",
            )
        try:
            parsed = ResolutionSubmission.from_dict(submission)
        except ReviewError as exc:
            raise ResearchReviewError(
                "RESEARCH_MCP_REVIEW_STATE_INVALID",
                f"{exc.reason_code}: {exc}",
            ) from exc

        task = next(
            (
                item
                for item in runtime["tasks"]
                if item.review_task_id == parsed.review_task_id
            ),
            None,
        )
        if task is None:
            raise ResearchReviewError(
                "RESEARCH_MCP_REVIEW_TASK_NOT_FOUND",
                "review task no longer exists",
            )
        if task.reviewability is not Reviewability.SUPPORTED:
            raise ResearchReviewError(
                "RESEARCH_MCP_UPSTREAM_FIX_REQUIRED",
                "review task is not supported by P9 v1",
            )
        if parsed.action.value not in set(task.supported_actions):
            raise ResearchReviewError(
                "RESEARCH_MCP_REVIEW_STATE_INVALID",
                "resolution action is not supported by this review task",
            )

        forbidden_attest_reasons = {
            "RAW_EXTRACTION_DEFECT",
            "P6_MISSING_FACT_CANDIDATE",
        }
        if (
            parsed.action is ResolutionAction.ATTEST_ISSUE_RESOLVED
            and task.reason_code in forbidden_attest_reasons
        ):
            raise ResearchReviewError(
                "RESEARCH_MCP_UPSTREAM_FIX_REQUIRED",
                "upstream defects cannot be resolved by attestation",
            )

        try:
            resolution = submit_resolution(runtime["review_dir"], parsed)
        except ReviewError as exc:
            raise ResearchReviewError(
                "RESEARCH_MCP_REVIEW_STATE_INVALID",
                f"{exc.reason_code}: {exc}",
            ) from exc
        return _success(
            "ffdf_submit_review_resolution",
            sha,
            {
                "resolution": resolution.to_dict(),
                "post_submit_review_state": self.get_review_state(sha)["data"],
                "materialization_required": True,
            },
        )

    def materialize_resolved_view(
        self,
        document_sha256: str,
    ) -> dict[str, Any]:
        self._require_write()
        sha = self._document_sha(document_sha256)
        review_dir = self._review_dir(sha)
        if not review_dir.is_dir():
            raise ResearchReviewError(
                "RESEARCH_MCP_REVIEW_STATE_CHANGED",
                "review overlay does not exist",
            )
        try:
            snapshot = materialize_resolved_view(review_dir)
        except ReviewError as exc:
            raise ResearchReviewError(
                "RESEARCH_MCP_RESOLVED_STORE_INVALID",
                f"{exc.reason_code}: {exc}",
            ) from exc
        return _success(
            "ffdf_materialize_resolved_view",
            sha,
            {
                "snapshot": snapshot.to_dict(),
                "review_state": self.get_review_state(sha)["data"],
            },
        )
