from __future__ import annotations

import hashlib
import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from financial_filing_data_foundation.facts import load_raw_facts
from financial_filing_data_foundation.facts.models import EXTRACTOR_VERSION
from financial_filing_data_foundation.mcp.catalog import CatalogDocument, CatalogError, McpCatalog, normalize_sha256
from financial_filing_data_foundation.native import load_native_document
from financial_filing_data_foundation.native.models import P3_PARSER_VERSION
from financial_filing_data_foundation.registry import ValidationStatus
from financial_filing_data_foundation.tables import load_reconstructed_tables
from financial_filing_data_foundation.tables.models import RECONSTRUCTION_VERSION
from financial_filing_data_foundation.validation import load_validation_result
from financial_filing_data_foundation.validation.models import POLICY_VERSION as P7_POLICY_VERSION

from .models import (
    POLICY_VERSION,
    REVIEW_SCHEMA_VERSION,
    TASK_SCHEMA_VERSION,
    ReviewError,
    ReviewOverlayArtifact,
    ReviewTask,
)


_SUPPORTED_ACTIONS: dict[str, tuple[str, ...]] = {
    "RAW_PERIOD_COVERAGE_LOW": ("SET_PERIOD",),
    "RAW_PERIOD_AMBIGUOUS": ("SET_PERIOD", "ATTEST_ISSUE_RESOLVED"),
    "RAW_UNIT_COVERAGE_LOW": ("SET_UNIT",),
    "RAW_UNIT_AMBIGUOUS": ("SET_UNIT", "ATTEST_ISSUE_RESOLVED"),
    "RAW_SCOPE_AMBIGUOUS": ("SET_SCOPE", "ATTEST_ISSUE_RESOLVED"),
    "CORE_STATEMENT_COVERAGE_LOW": ("CLASSIFY_TABLE_STATEMENT",),
}


@dataclass(slots=True)
class _BaseContext:
    project_root: Path
    catalog_path: Path
    document: CatalogDocument
    review_dir: Path
    manifest: dict[str, Any]
    report: dict[str, Any]
    issues: list[dict[str, Any]]
    tasks: list[dict[str, Any]]
    tables: list[dict[str, Any]]
    facts: list[dict[str, Any]]
    evidence: list[dict[str, Any]]
    table_by_id: dict[str, dict[str, Any]]
    fact_by_id: dict[str, dict[str, Any]]
    evidence_by_id: dict[str, dict[str, Any]]
    cell_by_key: dict[tuple[str, str], dict[str, Any]]
    task_by_id: dict[str, dict[str, Any]]


@dataclass(frozen=True, slots=True)
class ReviewBaseBundle:
    context: _BaseContext

    @property
    def document_sha256(self) -> str:
        return self.context.document.document_sha256

    @property
    def base_validation_report_sha256(self) -> str:
        return str(self.context.manifest["base_validation_report_sha256"])

    @property
    def p6_facts(self) -> tuple[dict[str, Any], ...]:
        return tuple(self.context.facts)

    @property
    def p7_report(self) -> dict[str, Any]:
        return self.context.report


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _jsonl_bytes(rows: Iterable[dict[str, Any]]) -> bytes:
    return b"".join(_canonical_json_bytes(row) + b"\n" for row in rows)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _read_json(path: Path, reason_code: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReviewError(reason_code, f"cannot read {path.name}: {exc}") from exc
    if not isinstance(value, dict):
        raise ReviewError(reason_code, f"{path.name} must contain a JSON object")
    return value


def _read_jsonl(path: Path, reason_code: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                row = json.loads(line)
                if not isinstance(row, dict):
                    raise ValueError(f"line {line_no} is not a JSON object")
                rows.append(row)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ReviewError(reason_code, f"cannot read {path.name}: {exc}") from exc
    return rows


def _assert_within(root: Path, path: Path, label: str) -> None:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise ReviewError(
            "P9_CATALOG_INVALID",
            f"{label} resolves outside project root",
        ) from exc


def _resolve_review_root(project_root: Path, review_root: str | Path) -> Path:
    candidate = Path(review_root).expanduser()
    if not candidate.is_absolute():
        candidate = project_root / candidate
    candidate = candidate.resolve()
    _assert_within(project_root, candidate, "review_root")
    return candidate


def _load_catalog(
    project_root: str | Path,
    catalog_path: str | Path,
) -> McpCatalog:
    try:
        return McpCatalog.load(project_root, catalog_path)
    except CatalogError as exc:
        reason = (
            "P9_DOCUMENT_NOT_FOUND"
            if exc.reason_code == "P8_DOCUMENT_NOT_FOUND"
            else "P9_CATALOG_INVALID"
        )
        raise ReviewError(reason, str(exc)) from exc


def _document_or_error(catalog: McpCatalog, document_sha256: str) -> CatalogDocument:
    try:
        normalized = normalize_sha256(document_sha256)
    except CatalogError as exc:
        raise ReviewError("P9_DOCUMENT_NOT_FOUND", str(exc)) from exc
    document = catalog.get(normalized)
    if document is None:
        raise ReviewError(
            "P9_DOCUMENT_NOT_FOUND",
            f"document not found in catalog: {normalized}",
        )
    return document


def _input_fingerprints(
    catalog: McpCatalog,
    document: CatalogDocument,
) -> dict[str, str]:
    return {
        "catalog_sha256": _sha256_file(catalog.catalog_path),
        "p3_document_sha256": _sha256_file(document.p3_artifact_dir / "document.json"),
        "p3_pages_sha256": _sha256_file(document.p3_artifact_dir / "pages.jsonl"),
        "p3_sections_sha256": _sha256_file(document.p3_artifact_dir / "sections.jsonl"),
        "p5_manifest_sha256": _sha256_file(document.p5_artifact_dir / "table_manifest.json"),
        "p5_tables_sha256": _sha256_file(document.p5_artifact_dir / "tables.jsonl"),
        "p5_groups_sha256": _sha256_file(document.p5_artifact_dir / "table_groups.jsonl"),
        "p6_manifest_sha256": _sha256_file(document.p6_artifact_dir / "fact_manifest.json"),
        "p6_facts_sha256": _sha256_file(document.p6_artifact_dir / "raw_facts.jsonl"),
        "p6_evidence_sha256": _sha256_file(document.p6_artifact_dir / "evidence.jsonl"),
        "p7_report_sha256": _sha256_file(document.p7_artifact_dir / "validation_report.json"),
        "p7_issues_sha256": _sha256_file(document.p7_artifact_dir / "issues.jsonl"),
        "p3_parser_version": P3_PARSER_VERSION,
        "p5_reconstruction_version": RECONSTRUCTION_VERSION,
        "p6_extractor_version": EXTRACTOR_VERSION,
        "p7_policy_version": P7_POLICY_VERSION,
        "p9_policy_version": POLICY_VERSION,
    }


def _task_id(
    document_sha256: str,
    report_sha256: str,
    issue_id: str,
) -> str:
    material = (
        document_sha256
        + "\0"
        + report_sha256
        + "\0"
        + issue_id
        + "\0"
        + POLICY_VERSION
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _build_tasks(
    document_sha256: str,
    report_sha256: str,
    issues: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for issue in issues:
        if str(issue.get("severity")) != "REVIEW":
            continue
        if str(issue.get("document_sha256")) != document_sha256:
            raise ReviewError(
                "P9_BASE_ARTIFACT_INVALID",
                "P7 issue document identity differs from catalog document",
            )
        reason = str(issue.get("reason_code") or "")
        actions = list(_SUPPORTED_ACTIONS.get(reason, ()))
        task = {
            "schema_version": TASK_SCHEMA_VERSION,
            "review_task_id": _task_id(
                document_sha256,
                report_sha256,
                str(issue.get("issue_id") or ""),
            ),
            "document_sha256": document_sha256,
            "base_validation_report_sha256": report_sha256,
            "issue_id": str(issue.get("issue_id") or ""),
            "reason_code": reason,
            "message": str(issue.get("message") or ""),
            "observed": dict(issue.get("observed") or {}),
            "scope": str(issue.get("scope") or ""),
            "page_no": issue.get("page_no"),
            "table_id": issue.get("table_id"),
            "raw_fact_ids": sorted(str(value) for value in issue.get("raw_fact_ids") or ()),
            "evidence_ids": sorted(str(value) for value in issue.get("evidence_ids") or ()),
            "reviewability": "SUPPORTED" if actions else "UNSUPPORTED",
            "supported_actions": actions,
            "required_evidence_types": (
                ["P5_CELL", "P6_EVIDENCE"] if actions else []
            ),
        }
        tasks.append(task)
    tasks.sort(key=lambda row: (str(row["reason_code"]), str(row["issue_id"])))
    return tasks


def _expected_manifest(
    *,
    project_root: Path,
    catalog: McpCatalog,
    document: CatalogDocument,
    review_dir: Path,
    report: dict[str, Any],
    fingerprints: dict[str, str],
    tasks: list[dict[str, Any]],
    queue_sha256: str,
) -> dict[str, Any]:
    try:
        catalog_relative = catalog.catalog_path.relative_to(project_root).as_posix()
        review_relative = review_dir.relative_to(project_root).as_posix()
    except ValueError as exc:
        raise ReviewError(
            "P9_CATALOG_INVALID",
            "catalog/review directory must remain inside project root",
        ) from exc
    report_sha = fingerprints["p7_report_sha256"]
    base_identity = {
        "document_sha256": document.document_sha256,
        "base_validation_report_sha256": report_sha,
        "input_fingerprints": fingerprints,
        "policy_version": POLICY_VERSION,
    }
    supported = sum(row["reviewability"] == "SUPPORTED" for row in tasks)
    return {
        "schema_version": REVIEW_SCHEMA_VERSION,
        "policy_version": POLICY_VERSION,
        "document_sha256": document.document_sha256,
        "project_root": str(project_root),
        "catalog_path": catalog_relative,
        "review_dir": review_relative,
        "market": document.market,
        "ticker": document.ticker,
        "fiscal_year": document.fiscal_year,
        "filing_type": document.filing_type,
        "base_validation_status": str(report.get("validation_status") or ""),
        "base_compatibility_status": str(report.get("compatibility_status") or ""),
        "base_validation_report_sha256": report_sha,
        "review_base_id": _sha256_bytes(_canonical_json_bytes(base_identity)),
        "input_fingerprints": fingerprints,
        "versions": {
            "p3_parser_version": P3_PARSER_VERSION,
            "p5_reconstruction_version": RECONSTRUCTION_VERSION,
            "p6_extractor_version": EXTRACTOR_VERSION,
            "p7_policy_version": P7_POLICY_VERSION,
        },
        "review_task_count": len(tasks),
        "supported_task_count": supported,
        "unsupported_task_count": len(tasks) - supported,
        "queue_file": "review_queue.jsonl",
        "queue_sha256": queue_sha256,
    }


def _validate_initial_base(
    document: CatalogDocument,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    try:
        native = load_native_document(document.p3_artifact_dir)
        tables = load_reconstructed_tables(document.p5_artifact_dir)
        facts = load_raw_facts(
            document.p6_artifact_dir,
            document.p3_artifact_dir,
            document.p5_artifact_dir,
        )
        validation = load_validation_result(
            document.p7_artifact_dir,
            document.p3_artifact_dir,
            document.p5_artifact_dir,
            document.p6_artifact_dir,
        )
    except Exception as exc:
        raise ReviewError(
            "P9_BASE_ARTIFACT_INVALID",
            f"upstream artifact validation failed: {exc}",
        ) from exc

    if not (
        native.document_sha256
        == tables.document_sha256
        == facts.document_sha256
        == validation.document_sha256
        == document.document_sha256
    ):
        raise ReviewError(
            "P9_BASE_ARTIFACT_INVALID",
            "P3/P5/P6/P7/catalog document SHA mismatch",
        )

    if validation.validation_status in (
        ValidationStatus.FAIL,
        ValidationStatus.BLOCKED,
    ):
        raise ReviewError(
            "P9_BASE_STATUS_NOT_REVIEWABLE",
            f"base validation status is {validation.validation_status.value}",
        )

    report = _read_json(
        document.p7_artifact_dir / "validation_report.json",
        "P9_BASE_ARTIFACT_INVALID",
    )
    issues = _read_jsonl(
        document.p7_artifact_dir / "issues.jsonl",
        "P9_BASE_ARTIFACT_INVALID",
    )
    return report, issues


def _build_indexes(
    tables: list[dict[str, Any]],
    facts: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
) -> tuple[
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
    dict[tuple[str, str], dict[str, Any]],
]:
    table_by_id: dict[str, dict[str, Any]] = {}
    cell_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for table in tables:
        table_id = str(table.get("table_id") or "")
        if not table_id or table_id in table_by_id:
            raise ReviewError(
                "P9_BASE_ARTIFACT_INVALID",
                "P5 table IDs are missing or duplicated",
            )
        table_by_id[table_id] = table
        page_no = int(table.get("page_no", 0) or 0)
        for row in table.get("rows") or ():
            row_id = str(row.get("row_id") or "")
            for cell in row.get("cells") or ():
                cell_id = str(cell.get("cell_id") or "")
                key = (table_id, cell_id)
                if not cell_id or key in cell_by_key:
                    raise ReviewError(
                        "P9_BASE_ARTIFACT_INVALID",
                        "P5 cell IDs are missing or duplicated within a table",
                    )
                enriched = dict(cell)
                enriched["_table_id"] = table_id
                enriched["_row_id"] = row_id
                enriched["_page_no"] = page_no
                cell_by_key[key] = enriched

    fact_by_id: dict[str, dict[str, Any]] = {}
    for fact in facts:
        fact_id = str(fact.get("raw_fact_id") or "")
        if not fact_id or fact_id in fact_by_id:
            raise ReviewError(
                "P9_BASE_ARTIFACT_INVALID",
                "P6 raw_fact_ids are missing or duplicated",
            )
        fact_by_id[fact_id] = fact

    evidence_by_id: dict[str, dict[str, Any]] = {}
    for row in evidence:
        evidence_id = str(row.get("evidence_id") or "")
        if not evidence_id or evidence_id in evidence_by_id:
            raise ReviewError(
                "P9_BASE_ARTIFACT_INVALID",
                "P6 evidence_ids are missing or duplicated",
            )
        evidence_by_id[evidence_id] = row
    return table_by_id, fact_by_id, evidence_by_id, cell_by_key


def _context_from_parts(
    *,
    project_root: Path,
    catalog: McpCatalog,
    document: CatalogDocument,
    review_dir: Path,
    manifest: dict[str, Any],
    report: dict[str, Any],
    issues: list[dict[str, Any]],
    tasks: list[dict[str, Any]],
) -> _BaseContext:
    tables = _read_jsonl(
        document.p5_artifact_dir / "tables.jsonl",
        "P9_BASE_ARTIFACT_INVALID",
    )
    facts = _read_jsonl(
        document.p6_artifact_dir / "raw_facts.jsonl",
        "P9_BASE_ARTIFACT_INVALID",
    )
    evidence = _read_jsonl(
        document.p6_artifact_dir / "evidence.jsonl",
        "P9_BASE_ARTIFACT_INVALID",
    )
    table_by_id, fact_by_id, evidence_by_id, cell_by_key = _build_indexes(
        tables, facts, evidence
    )
    task_by_id = {str(row["review_task_id"]): row for row in tasks}
    if len(task_by_id) != len(tasks):
        raise ReviewError(
            "P9_ARTIFACT_INCOMPLETE_OR_CORRUPT",
            "review task IDs are duplicated",
        )
    return _BaseContext(
        project_root=project_root,
        catalog_path=catalog.catalog_path,
        document=document,
        review_dir=review_dir,
        manifest=manifest,
        report=report,
        issues=issues,
        tasks=tasks,
        tables=tables,
        facts=facts,
        evidence=evidence,
        table_by_id=table_by_id,
        fact_by_id=fact_by_id,
        evidence_by_id=evidence_by_id,
        cell_by_key=cell_by_key,
        task_by_id=task_by_id,
    )


def prepare_review_overlay(
    project_root: str | Path,
    catalog_path: str | Path,
    document_sha256: str,
    review_root: str | Path,
) -> ReviewOverlayArtifact:
    catalog = _load_catalog(project_root, catalog_path)
    root = catalog.project_root
    document = _document_or_error(catalog, document_sha256)
    review_base = _resolve_review_root(root, review_root)
    final_dir = review_base / document.document_sha256

    if final_dir.exists():
        context = _load_context_from_review(final_dir)
        return _artifact_from_context(context)

    report, issues = _validate_initial_base(document)
    fingerprints = _input_fingerprints(catalog, document)
    report_sha = fingerprints["p7_report_sha256"]
    tasks = _build_tasks(document.document_sha256, report_sha, issues)
    queue_bytes = _jsonl_bytes(tasks)

    review_base.mkdir(parents=True, exist_ok=True)
    temp_dir = review_base / f".{document.document_sha256}.tmp"
    if temp_dir.exists():
        raise ReviewError(
            "P9_PERSIST_FAILED",
            f"deterministic staging directory already exists: {temp_dir}",
        )
    temp_created = False
    try:
        temp_dir.mkdir(parents=False, exist_ok=False)
        temp_created = True
        (temp_dir / "resolutions").mkdir()
        (temp_dir / "snapshots").mkdir()
        (temp_dir / "review_queue.jsonl").write_bytes(queue_bytes)
        manifest = _expected_manifest(
            project_root=root,
            catalog=catalog,
            document=document,
            review_dir=final_dir,
            report=report,
            fingerprints=fingerprints,
            tasks=tasks,
            queue_sha256=_sha256_bytes(queue_bytes),
        )
        _write_json(temp_dir / "review_manifest.json", manifest)
        try:
            os.replace(temp_dir, final_dir)
        except OSError:
            if not final_dir.exists():
                raise
            shutil.rmtree(temp_dir, ignore_errors=True)
        context = _load_context_from_review(final_dir)
        return _artifact_from_context(context)
    except Exception as exc:
        if temp_created and temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        if isinstance(exc, ReviewError):
            raise
        raise ReviewError("P9_PERSIST_FAILED", str(exc)) from exc


def _load_context_from_review(review_dir: str | Path) -> _BaseContext:
    directory = Path(review_dir).expanduser().resolve()
    manifest_path = directory / "review_manifest.json"
    queue_path = directory / "review_queue.jsonl"
    if not manifest_path.is_file() or not queue_path.is_file():
        raise ReviewError(
            "P9_ARTIFACT_INCOMPLETE_OR_CORRUPT",
            f"missing review manifest/queue under {directory}",
        )

    manifest = _read_json(
        manifest_path,
        "P9_ARTIFACT_INCOMPLETE_OR_CORRUPT",
    )
    if (
        manifest.get("schema_version") != REVIEW_SCHEMA_VERSION
        or manifest.get("policy_version") != POLICY_VERSION
    ):
        raise ReviewError(
            "P9_ARTIFACT_INCOMPLETE_OR_CORRUPT",
            "review manifest schema/policy mismatch",
        )
    try:
        project_root = Path(str(manifest["project_root"])).expanduser().resolve()
        directory.relative_to(project_root)
    except (KeyError, ValueError) as exc:
        raise ReviewError(
            "P9_ARTIFACT_INCOMPLETE_OR_CORRUPT",
            "review directory is not inside manifest project root",
        ) from exc

    catalog_text = str(manifest.get("catalog_path") or "")
    catalog_rel = Path(catalog_text)
    if not catalog_text or catalog_rel.is_absolute():
        raise ReviewError(
            "P9_ARTIFACT_INCOMPLETE_OR_CORRUPT",
            "manifest catalog path must be project-root-relative",
        )
    catalog = _load_catalog(project_root, catalog_rel)
    document = _document_or_error(
        catalog,
        str(manifest.get("document_sha256") or ""),
    )
    current_fingerprints = _input_fingerprints(catalog, document)
    if dict(manifest.get("input_fingerprints") or {}) != current_fingerprints:
        raise ReviewError(
            "P9_BASE_ARTIFACT_CHANGED",
            "base catalog/P3/P5/P6/P7 fingerprints changed",
        )

    report = _read_json(
        document.p7_artifact_dir / "validation_report.json",
        "P9_BASE_ARTIFACT_INVALID",
    )
    issues = _read_jsonl(
        document.p7_artifact_dir / "issues.jsonl",
        "P9_BASE_ARTIFACT_INVALID",
    )
    status = str(report.get("validation_status") or "")
    if status in {"FAIL", "BLOCKED"}:
        raise ReviewError(
            "P9_BASE_STATUS_NOT_REVIEWABLE",
            f"base validation status is {status}",
        )

    expected_tasks = _build_tasks(
        document.document_sha256,
        current_fingerprints["p7_report_sha256"],
        issues,
    )
    queue_bytes = queue_path.read_bytes()
    try:
        actual_tasks = _read_jsonl(
            queue_path,
            "P9_ARTIFACT_INCOMPLETE_OR_CORRUPT",
        )
    except ReviewError:
        raise
    if actual_tasks != expected_tasks or queue_bytes != _jsonl_bytes(expected_tasks):
        raise ReviewError(
            "P9_ARTIFACT_INCOMPLETE_OR_CORRUPT",
            "persisted review queue differs from deterministic queue",
        )

    expected_manifest = _expected_manifest(
        project_root=project_root,
        catalog=catalog,
        document=document,
        review_dir=directory,
        report=report,
        fingerprints=current_fingerprints,
        tasks=expected_tasks,
        queue_sha256=_sha256_bytes(queue_bytes),
    )
    if manifest != expected_manifest:
        raise ReviewError(
            "P9_ARTIFACT_INCOMPLETE_OR_CORRUPT",
            "review manifest differs from deterministic manifest",
        )
    return _context_from_parts(
        project_root=project_root,
        catalog=catalog,
        document=document,
        review_dir=directory,
        manifest=manifest,
        report=report,
        issues=issues,
        tasks=expected_tasks,
    )


def _artifact_from_context(context: _BaseContext) -> ReviewOverlayArtifact:
    return ReviewOverlayArtifact(
        review_dir=context.review_dir,
        document_sha256=context.document.document_sha256,
        task_count=len(context.tasks),
        supported_task_count=sum(
            row["reviewability"] == "SUPPORTED" for row in context.tasks
        ),
        unsupported_task_count=sum(
            row["reviewability"] == "UNSUPPORTED" for row in context.tasks
        ),
        manifest_path=context.review_dir / "review_manifest.json",
        queue_path=context.review_dir / "review_queue.jsonl",
    )


def load_review_base(
    review_dir: str | Path,
) -> tuple[dict[str, Any], ReviewBaseBundle, tuple[ReviewTask, ...]]:
    context = _load_context_from_review(review_dir)
    tasks = tuple(ReviewTask.from_dict(row) for row in context.tasks)
    return dict(context.manifest), ReviewBaseBundle(context), tasks


def list_review_tasks(review_dir: str | Path) -> tuple[ReviewTask, ...]:
    context = _load_context_from_review(review_dir)
    return tuple(ReviewTask.from_dict(row) for row in context.tasks)
