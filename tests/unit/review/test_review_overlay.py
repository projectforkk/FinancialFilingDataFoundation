from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from financial_filing_data_foundation.candidates import detect_table_candidates
from financial_filing_data_foundation.facts import extract_raw_facts, load_raw_facts
from financial_filing_data_foundation.facts.models import EXTRACTOR_VERSION
from financial_filing_data_foundation.identity import FilingSlotKey
from financial_filing_data_foundation.native.models import (
    P3_PARSER_VERSION,
    SCHEMA_VERSION as P3_SCHEMA_VERSION,
)
from financial_filing_data_foundation.native.search import build_search_db
from financial_filing_data_foundation.registry import ValidationStatus
from financial_filing_data_foundation.review import queue as review_queue_module
from financial_filing_data_foundation.review import store as review_store_module
from financial_filing_data_foundation.review.cli import main as review_cli_main
from financial_filing_data_foundation.review.evidence import validate_reviewer
from financial_filing_data_foundation.review.models import (
    ResolutionAction,
    ResolutionSubmission,
    ReviewResolution,
    ReviewError,
    ReviewerType,
    Reviewability,
)
from financial_filing_data_foundation.review.queue import (
    list_review_tasks,
    load_review_base,
    prepare_review_overlay,
)
from financial_filing_data_foundation.review.resolve import (
    build_resolved_parsed_data_record,
    load_resolved_snapshot,
    materialize_resolved_view,
)
from financial_filing_data_foundation.review.store import (
    _overlay_hash_before,
    _validate_graph,
    active_resolutions,
    list_resolutions,
    submit_resolution,
)
from financial_filing_data_foundation.tables import reconstruct_tables
from financial_filing_data_foundation.tables.models import RECONSTRUCTION_VERSION
from financial_filing_data_foundation.validation import validate_document_artifacts
from financial_filing_data_foundation.validation.models import (
    POLICY_VERSION as P7_POLICY_VERSION,
)


DOC_SHA = "e" * 64


def _word(
    text: str,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    line_no: int,
    word_no: int,
) -> dict:
    return {
        "text": text,
        "bbox": [x0, y0, x1, y1],
        "block_no": 0,
        "line_no": line_no,
        "word_no": word_no,
    }


def _page() -> dict:
    raw_rows = [("项目", "COL_A", "COL_B")] + [
        (f"指标{i:02d}", str(1000 + i), str(900 + i))
        for i in range(30)
    ]
    words: list[dict] = []
    lines: list[dict] = []
    for row_no, values in enumerate(raw_rows):
        y0 = 60 + row_no * 20
        row_words: list[dict] = []
        for word_no, (text, x0, x1) in enumerate(
            zip(values, (50.0, 300.0, 400.0), (220.0, 340.0, 440.0))
        ):
            word = _word(
                text,
                x0,
                y0,
                x1,
                y0 + 10,
                row_no,
                word_no,
            )
            words.append(word)
            row_words.append(word)
        lines.append(
            {
                "line_no": row_no,
                "bbox": [50, y0, 440, y0 + 10],
                "text": " ".join(word["text"] for word in row_words),
                "spans": [],
                "repeated_header_footer": False,
            }
        )
    text = "\n".join(line["text"] for line in lines)
    return {
        "page_no": 1,
        "width": 595.0,
        "height": 842.0,
        "rotation": 0,
        "native_text_available": True,
        "native_char_count": len(text),
        "word_count": len(words),
        "block_count": 1,
        "line_count": len(lines),
        "span_count": 0,
        "image_count": 0,
        "drawing_count": 80,
        "text": text,
        "words": words,
        "blocks": [
            {
                "block_no": 0,
                "bbox": [50, 60, 440, 60 + (len(lines) - 1) * 20 + 10],
                "type": "text",
                "text": text,
                "lines": lines,
                "reading_order_index": 0,
            }
        ],
        "warnings": [],
    }


def _write_native(root: Path) -> Path:
    page = _page()
    sections = [
        {
            "section_id": "section-1",
            "raw_title": "财务报表",
            "normalized_title": None,
            "level": 1,
            "page_start": 1,
            "page_end": 1,
            "parent_section_id": None,
            "bbox": [50, 40, 180, 52],
            "heading_score": 5.0,
            "heading_signals": ["TEST"],
            "quality_signals": [],
        }
    ]
    artifact = root / "p3" / DOC_SHA
    artifact.mkdir(parents=True)
    (artifact / "pages.jsonl").write_text(
        json.dumps(page, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (artifact / "sections.jsonl").write_text(
        json.dumps(sections[0], ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (artifact / "document.json").write_text(
        json.dumps(
            {
                "schema_version": P3_SCHEMA_VERSION,
                "document_sha256": DOC_SHA,
                "file_size": 123,
                "page_count": 1,
                "parser_version": P3_PARSER_VERSION,
                "timings_ms": {},
                "warnings": [],
            }
        ),
        encoding="utf-8",
    )
    build_search_db(
        artifact / "search.sqlite",
        DOC_SHA,
        [page],
        sections,
    )
    return artifact


def _relative(root: Path, value: Path) -> str:
    return value.resolve().relative_to(root.resolve()).as_posix()


def _build_fixture(root: Path) -> tuple[Path, dict[str, Path]]:
    p3 = _write_native(root)
    p4 = detect_table_candidates(p3, root / "p4").artifact_dir
    p5 = reconstruct_tables(p3, p4, root / "p5").artifact_dir
    p6 = extract_raw_facts(p3, p5, root / "p6").artifact_dir
    p7 = validate_document_artifacts(
        p3,
        p5,
        p6,
        root / "p7",
    ).artifact_dir

    catalog_path = root / "catalog.json"
    catalog_path.write_text(
        json.dumps(
            {
                "schema_version": "p8-mcp-catalog-v1",
                "documents": [
                    {
                        "document_sha256": DOC_SHA,
                        "market": "CN",
                        "ticker": "SYNTH",
                        "fiscal_year": 2024,
                        "filing_type": "ANNUAL",
                        "p3_artifact_dir": _relative(root, p3),
                        "p5_artifact_dir": _relative(root, p5),
                        "p6_artifact_dir": _relative(root, p6),
                        "p7_artifact_dir": _relative(root, p7),
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return catalog_path, {
        "p3": p3,
        "p4": p4,
        "p5": p5,
        "p6": p6,
        "p7": p7,
    }


def _build_extra_issue_fixture(
    root: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    reason_code: str,
    observed: dict,
    extra_tables: bool = False,
):
    catalog, artifacts = _build_fixture(root)
    if extra_tables:
        tables_path = artifacts["p5"] / "tables.jsonl"
        tables = [
            json.loads(line)
            for line in tables_path.read_text(encoding="utf-8").splitlines()
            if line
        ]
        extra = json.loads(json.dumps(tables[0]))
        extra["table_id"] = "synthetic-second-table"
        extra["rows"] = [json.loads(json.dumps(extra["rows"][0]))]
        extra["rows"][0]["row_id"] = "synthetic-second-row"
        extra["rows"][0]["cells"] = [
            json.loads(json.dumps(extra["rows"][0]["cells"][0]))
        ]
        extra["rows"][0]["cells"][0]["cell_id"] = "synthetic-second-cell"
        extra["rows"][0]["cells"][0]["text"] = "Income evidence"
        tables.append(extra)
        tables_path.write_text(
            "".join(
                json.dumps(table, ensure_ascii=False, sort_keys=True) + "\n"
                for table in tables
            ),
            encoding="utf-8",
            newline="\n",
        )
        monkeypatch.setattr(
            review_queue_module,
            "load_reconstructed_tables",
            lambda *args, **kwargs: SimpleNamespace(document_sha256=DOC_SHA),
        )
        monkeypatch.setattr(
            review_queue_module,
            "load_raw_facts",
            lambda *args, **kwargs: SimpleNamespace(document_sha256=DOC_SHA),
        )
    p7 = artifacts["p7"]
    issues_path = p7 / "issues.jsonl"
    issues = [
        json.loads(line)
        for line in issues_path.read_text(encoding="utf-8").splitlines()
        if line
    ]
    table_id = json.loads(
        (artifacts["p5"] / "tables.jsonl").read_text(encoding="utf-8").splitlines()[0]
    )["table_id"]
    issues.append(
        {
            "issue_id": f"synthetic-{reason_code.lower()}",
            "document_sha256": DOC_SHA,
            "severity": "REVIEW",
            "reason_code": reason_code,
            "message": f"synthetic {reason_code}",
            "observed": dict(observed),
            "scope": "synthetic",
            "page_no": 1,
            "table_id": table_id,
            "raw_fact_ids": [],
            "evidence_ids": [],
        }
    )
    issues_path.write_text(
        "".join(json.dumps(issue, ensure_ascii=False, sort_keys=True) + "\n" for issue in issues),
        encoding="utf-8",
    )
    report_path = p7 / "validation_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["validation_status"] = "REVIEW_REQUIRED"
    report["compatibility_status"] = "COMPATIBLE"
    report["reuse_eligible"] = False
    report["issue_count"] = len(issues)
    report["review_issue_count"] = sum(
        1 for issue in issues if issue.get("severity") == "REVIEW"
    )
    report["blocking_issue_count"] = 0
    report["failure_issue_count"] = 0
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        review_queue_module,
        "load_validation_result",
        lambda *args, **kwargs: SimpleNamespace(
            document_sha256=DOC_SHA,
            validation_status=ValidationStatus.REVIEW_REQUIRED,
        ),
    )
    overlay = prepare_review_overlay(root, catalog, DOC_SHA, root / "review")
    manifest, bundle, tasks = load_review_base(overlay.review_dir)
    return root, catalog, artifacts, overlay, manifest, bundle, tasks


def _tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(
        (item for item in root.rglob("*") if item.is_file()),
        key=lambda item: item.relative_to(root).as_posix(),
    ):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


@pytest.fixture()
def review_fixture(tmp_path: Path):
    catalog, artifacts = _build_fixture(tmp_path)
    before = {stage: _tree_hash(path) for stage, path in artifacts.items()}
    overlay = prepare_review_overlay(
        tmp_path,
        catalog,
        DOC_SHA,
        tmp_path / "review",
    )
    manifest, bundle, tasks = load_review_base(overlay.review_dir)
    return tmp_path, catalog, artifacts, before, overlay, manifest, bundle, tasks


def _task(tasks, reason: str):
    return next(task for task in tasks if task.reason_code == reason)


def _table_and_cell(bundle):
    table = bundle.context.tables[0]
    cell = next(
        cell
        for row in table["rows"]
        for cell in row["cells"]
        if int(cell["column_index"]) == 1
    )
    return table, cell


def _submission(
    task,
    *,
    action: str,
    target: dict,
    value: str | None,
    evidence_refs: list[dict],
    reviewed_at: str,
    supersedes: str | None = None,
    justification: str = "Deterministic P9 synthetic test resolution.",
) -> ResolutionSubmission:
    return ResolutionSubmission.from_dict(
        {
            "review_task_id": task.review_task_id,
            "action": action,
            "target": target,
            "value": value,
            "evidence_refs": evidence_refs,
            "reviewer_type": "HUMAN",
            "reviewer_id": "p9-unit-reviewer",
            "reviewed_at": reviewed_at,
            "justification": justification,
            "supersedes_resolution_id": supersedes,
        }
    )


def _submission_payload(submission: ResolutionSubmission) -> dict:
    return {
        "review_task_id": submission.review_task_id,
        "action": submission.action.value,
        "target": dict(submission.target),
        "value": submission.value,
        "evidence_refs": [dict(ref) for ref in submission.evidence_refs],
        "evidence_pages": (
            None
            if submission.evidence_pages is None
            else list(submission.evidence_pages)
        ),
        "reviewer_type": submission.reviewer_type.value,
        "reviewer_id": submission.reviewer_id,
        "reviewed_at": submission.reviewed_at,
        "justification": submission.justification,
        "supersedes_resolution_id": submission.supersedes_resolution_id,
        "supporting_resolution_ids": list(submission.supporting_resolution_ids),
        "expected_observed_count": submission.expected_observed_count,
    }


def _graph_resolution(
    resolution_id: str,
    *,
    parent: str | None,
    prior: tuple[str, ...],
) -> ReviewResolution:
    return ReviewResolution(
        resolution_id=resolution_id,
        document_sha256=DOC_SHA,
        base_validation_report_sha256="r" * 64,
        review_task_id="task",
        issue_id="issue",
        reason_code="RAW_PERIOD_AMBIGUOUS",
        action=ResolutionAction.SET_PERIOD,
        target={
            "target_type": "FACT_FIELD",
            "raw_fact_id": "fact",
            "field": "period",
        },
        value="PERIOD",
        evidence_refs=({"type": "P6_EVIDENCE", "evidence_id": "evidence"},),
        evidence_pages=(1,),
        before={
            "target": {
                "target_type": "FACT_FIELD",
                "raw_fact_id": "fact",
                "field": "period",
            },
            "selected_fact_ids": ["fact"],
            "affected_fact_ids": ["fact"],
            "affected_count": 1,
            "already_explicit_fact_ids": [],
            "base_raw_values": {"fact": None},
            "current_effective_values": {"fact": None},
        },
        after={"value": "PERIOD", "expected_affected_fact_count": 1},
        reviewer_type=ReviewerType.HUMAN,
        reviewer_id="graph-reviewer",
        reviewed_at="2026-11-03T22:00:00+09:00",
        justification="synthetic graph validation",
        base_active_resolution_ids=prior,
        base_overlay_set_hash_before=_overlay_hash_before(
            DOC_SHA, "r" * 64, prior
        ),
        supersedes_resolution_id=parent,
    )


def _resign_resolution_file(path: Path, mutate) -> Path:
    payload = json.loads(path.read_text(encoding="utf-8"))
    mutate(payload)
    payload.pop("resolution_id", None)
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    resolution_id = hashlib.sha256(canonical).hexdigest()
    payload["resolution_id"] = resolution_id
    replacement = path.with_name(f"{resolution_id}.json")
    path.unlink()
    replacement.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return replacement


def test_prepare_queue_contains_only_review_severity_and_is_deterministic(
    review_fixture,
) -> None:
    root, catalog, artifacts, before, overlay, _, _, tasks = review_fixture

    reasons = {task.reason_code for task in tasks}
    assert reasons == {"RAW_PERIOD_COVERAGE_LOW", "RAW_UNIT_COVERAGE_LOW"}
    assert all(task.reviewability is Reviewability.SUPPORTED for task in tasks)
    assert overlay.task_count == 2
    assert overlay.supported_task_count == 2
    assert overlay.unsupported_task_count == 0

    again = prepare_review_overlay(root, catalog, DOC_SHA, root / "review")
    assert again.to_dict() == overlay.to_dict()

    after = {stage: _tree_hash(path) for stage, path in artifacts.items()}
    assert after == before


def test_reviewer_timestamp_must_be_timezone_aware() -> None:
    submission = ResolutionSubmission.from_dict(
        {
            "review_task_id": "task",
            "action": "SET_PERIOD",
            "target": {
                "target_type": "FACT_FIELD",
                "raw_fact_id": "fact",
                "field": "period",
            },
            "value": "X",
            "evidence_refs": [{"type": "P6_EVIDENCE", "evidence_id": "e"}],
            "reviewer_type": "HUMAN",
            "reviewer_id": "reviewer",
            "reviewed_at": "2026-11-03T22:00:00",
            "justification": "test",
        }
    )
    with pytest.raises(ReviewError) as exc_info:
        validate_reviewer(submission)
    assert exc_info.value.reason_code == "P9_INVALID_RESOLUTION"


def test_resolution_binds_explicit_prior_state_and_supersession(review_fixture) -> None:
    _, _, _, _, overlay, _, bundle, tasks = review_fixture
    task = _task(tasks, "RAW_PERIOD_COVERAGE_LOW")
    table, cell = _table_and_cell(bundle)
    target = {
        "target_type": "TABLE_COLUMN_FIELD",
        "table_id": table["table_id"],
        "column_index": 1,
        "field": "period",
    }
    evidence = [
        {
            "type": "P5_CELL",
            "table_id": table["table_id"],
            "cell_id": cell["cell_id"],
        }
    ]

    first = submit_resolution(
        overlay.review_dir,
        _submission(
            task,
            action="SET_PERIOD",
            target=target,
            value="PERIOD_A",
            evidence_refs=evidence,
            reviewed_at="2026-11-03T22:00:00+09:00",
        ),
    )
    assert first.base_active_resolution_ids == ()
    assert len(first.base_overlay_set_hash_before) == 64

    second = submit_resolution(
        overlay.review_dir,
        _submission(
            task,
            action="SET_PERIOD",
            target=target,
            value="PERIOD_B",
            evidence_refs=evidence,
            reviewed_at="2026-11-03T22:01:00+09:00",
            supersedes=first.resolution_id,
        ),
    )
    assert second.base_active_resolution_ids == (first.resolution_id,)
    assert second.base_overlay_set_hash_before != first.base_overlay_set_hash_before
    assert second.resolution_id != first.resolution_id

    rows = list_resolutions(overlay.review_dir)
    active = active_resolutions(overlay.review_dir)
    assert len(rows) == 2
    assert tuple(item.resolution_id for item in active) == (second.resolution_id,)


def test_resolved_view_fills_nulls_without_mutating_raw_and_can_reach_pass(
    review_fixture,
) -> None:
    _, _, artifacts, before, overlay, _, bundle, tasks = review_fixture
    table, cell = _table_and_cell(bundle)
    evidence = [
        {
            "type": "P5_CELL",
            "table_id": table["table_id"],
            "cell_id": cell["cell_id"],
        }
    ]

    period_task = _task(tasks, "RAW_PERIOD_COVERAGE_LOW")
    period = submit_resolution(
        overlay.review_dir,
        _submission(
            period_task,
            action="SET_PERIOD",
            target={
                "target_type": "TABLE_COLUMN_FIELD",
                "table_id": table["table_id"],
                "column_index": 1,
                "field": "period",
            },
            value="PERIOD_TEST",
            evidence_refs=evidence,
            reviewed_at="2026-11-03T22:00:00+09:00",
        ),
    )
    unit_task = _task(tasks, "RAW_UNIT_COVERAGE_LOW")
    unit = submit_resolution(
        overlay.review_dir,
        _submission(
            unit_task,
            action="SET_UNIT",
            target={
                "target_type": "TABLE_FIELD",
                "table_id": table["table_id"],
                "field": "unit",
            },
            value="UNIT_TEST",
            evidence_refs=evidence,
            reviewed_at="2026-11-03T22:01:00+09:00",
        ),
    )
    assert unit.base_active_resolution_ids == (period.resolution_id,)

    snapshot = materialize_resolved_view(overlay.review_dir)
    loaded = load_resolved_snapshot(snapshot.snapshot_dir, overlay.review_dir)

    assert snapshot.overlay_set_hash == loaded.overlay_set_hash
    assert snapshot.fact_count == 60
    assert snapshot.active_resolution_count == 2
    assert snapshot.resolved_validation_status.value == "PASS"
    assert snapshot.resolved_reuse_eligible is True

    raw_facts = tuple(dict(row) for row in bundle.context.facts)
    resolved_rows = [
        json.loads(line)
        for line in snapshot.resolved_facts_path.read_text(encoding="utf-8").splitlines()
        if line
    ]
    assert len(raw_facts) == len(resolved_rows) == 60
    raw_by_id = {str(row["raw_fact_id"]): row for row in raw_facts}
    for row in resolved_rows:
        raw = raw_by_id[str(row["raw_fact_id"])]
        for key, value in raw.items():
            assert row[key] == value

    assert any(row["effective_period_label"] == "PERIOD_TEST" for row in resolved_rows)
    assert all(row["effective_unit"] == "UNIT_TEST" for row in resolved_rows)

    after = {stage: _tree_hash(path) for stage, path in artifacts.items()}
    assert after == before


def test_zero_overlay_snapshot_is_deterministic(review_fixture) -> None:
    _, _, _, _, overlay, _, _, _ = review_fixture
    first = materialize_resolved_view(overlay.review_dir)
    second = materialize_resolved_view(overlay.review_dir)

    assert first.overlay_set_hash == second.overlay_set_hash
    assert first.snapshot_dir == second.snapshot_dir
    assert first.active_resolution_count == 0
    assert first.fact_count == 60
    assert first.resolved_validation_status.value == "REVIEW_REQUIRED"


def test_resolution_payload_tamper_is_detected(review_fixture) -> None:
    _, _, _, _, overlay, _, bundle, tasks = review_fixture
    task = _task(tasks, "RAW_PERIOD_COVERAGE_LOW")
    table, cell = _table_and_cell(bundle)
    resolution = submit_resolution(
        overlay.review_dir,
        _submission(
            task,
            action="SET_PERIOD",
            target={
                "target_type": "TABLE_COLUMN_FIELD",
                "table_id": table["table_id"],
                "column_index": 1,
                "field": "period",
            },
            value="PERIOD_TEST",
            evidence_refs=[
                {
                    "type": "P5_CELL",
                    "table_id": table["table_id"],
                    "cell_id": cell["cell_id"],
                }
            ],
            reviewed_at="2026-11-03T22:00:00+09:00",
        ),
    )

    path = overlay.review_dir / "resolutions" / f"{resolution.resolution_id}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["base_overlay_set_hash_before"] = "0" * 64
    path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ReviewError) as exc_info:
        list_resolutions(overlay.review_dir)
    assert exc_info.value.reason_code == "P9_RESOLUTION_STORE_CORRUPT"


def test_tampered_prior_active_state_is_rejected(review_fixture) -> None:
    _, _, _, _, overlay, _, bundle, tasks = review_fixture
    task = _task(tasks, "RAW_PERIOD_COVERAGE_LOW")
    table, cell = _table_and_cell(bundle)
    resolution = submit_resolution(
        overlay.review_dir,
        _submission(
            task,
            action="SET_PERIOD",
            target={
                "target_type": "TABLE_COLUMN_FIELD",
                "table_id": table["table_id"],
                "column_index": 1,
                "field": "period",
            },
            value="PERIOD_TEST",
            evidence_refs=[
                {
                    "type": "P5_CELL",
                    "table_id": table["table_id"],
                    "cell_id": cell["cell_id"],
                }
            ],
            reviewed_at="2026-11-03T22:00:00+09:00",
        ),
    )
    _resign_resolution_file(
        overlay.review_dir / "resolutions" / f"{resolution.resolution_id}.json",
        lambda payload: payload.update(
            {
                "base_active_resolution_ids": ["missing-prior-resolution"],
            }
        ),
    )
    with pytest.raises(ReviewError) as exc_info:
        active_resolutions(overlay.review_dir)
    assert exc_info.value.reason_code == "P9_RESOLUTION_STORE_CORRUPT"


def test_tampered_before_state_is_rejected_after_id_recomputation(review_fixture) -> None:
    _, _, _, _, overlay, _, bundle, tasks = review_fixture
    task = _task(tasks, "RAW_PERIOD_COVERAGE_LOW")
    table, cell = _table_and_cell(bundle)
    resolution = submit_resolution(
        overlay.review_dir,
        _submission(
            task,
            action="SET_PERIOD",
            target={
                "target_type": "TABLE_COLUMN_FIELD",
                "table_id": table["table_id"],
                "column_index": 1,
                "field": "period",
            },
            value="PERIOD_TEST",
            evidence_refs=[
                {
                    "type": "P5_CELL",
                    "table_id": table["table_id"],
                    "cell_id": cell["cell_id"],
                }
            ],
            reviewed_at="2026-11-03T22:00:00+09:00",
        ),
    )
    _resign_resolution_file(
        overlay.review_dir / "resolutions" / f"{resolution.resolution_id}.json",
        lambda payload: payload["before"].update({"affected_count": 0}),
    )
    with pytest.raises(ReviewError) as exc_info:
        materialize_resolved_view(overlay.review_dir)
    assert exc_info.value.reason_code == "P9_ARTIFACT_INCOMPLETE_OR_CORRUPT"


def test_submit_revalidates_resigned_historical_before_before_new_write(review_fixture) -> None:
    _, _, _, _, overlay, _, bundle, tasks = review_fixture
    period_task = _task(tasks, "RAW_PERIOD_COVERAGE_LOW")
    unit_task = _task(tasks, "RAW_UNIT_COVERAGE_LOW")
    table, cell = _table_and_cell(bundle)
    evidence = [
        {
            "type": "P5_CELL",
            "table_id": table["table_id"],
            "cell_id": cell["cell_id"],
        }
    ]
    first = submit_resolution(
        overlay.review_dir,
        _submission(
            period_task,
            action="SET_PERIOD",
            target={
                "target_type": "TABLE_COLUMN_FIELD",
                "table_id": table["table_id"],
                "column_index": 1,
                "field": "period",
            },
            value="PERIOD_HISTORY",
            evidence_refs=evidence,
            reviewed_at="2026-11-03T22:00:00+09:00",
        ),
    )
    _resign_resolution_file(
        overlay.review_dir / "resolutions" / f"{first.resolution_id}.json",
        lambda payload: payload["before"].update({"affected_fact_ids": []}),
    )
    files_before = sorted(path.name for path in (overlay.review_dir / "resolutions").glob("*.json"))

    with pytest.raises(ReviewError) as exc_info:
        submit_resolution(
            overlay.review_dir,
            _submission(
                unit_task,
                action="SET_UNIT",
                target={
                    "target_type": "TABLE_FIELD",
                    "table_id": table["table_id"],
                    "field": "unit",
                },
                value="UNIT_HISTORY",
                evidence_refs=evidence,
                reviewed_at="2026-11-03T22:01:00+09:00",
            ),
        )

    assert exc_info.value.reason_code == "P9_ARTIFACT_INCOMPLETE_OR_CORRUPT"
    assert sorted(path.name for path in (overlay.review_dir / "resolutions").glob("*.json")) == files_before


def test_materialize_revalidates_resigned_superseded_parent(
    review_fixture,
) -> None:
    _, _, _, _, overlay, _, bundle, tasks = review_fixture
    task = _task(tasks, "RAW_PERIOD_COVERAGE_LOW")
    table, cell = _table_and_cell(bundle)
    target = {
        "target_type": "TABLE_COLUMN_FIELD",
        "table_id": table["table_id"],
        "column_index": 1,
        "field": "period",
    }
    evidence = [
        {
            "type": "P5_CELL",
            "table_id": table["table_id"],
            "cell_id": cell["cell_id"],
        }
    ]
    parent = submit_resolution(
        overlay.review_dir,
        _submission(
            task,
            action="SET_PERIOD",
            target=target,
            value="PERIOD_PARENT",
            evidence_refs=evidence,
            reviewed_at="2026-11-03T22:00:00+09:00",
        ),
    )
    child = submit_resolution(
        overlay.review_dir,
        _submission(
            task,
            action="SET_PERIOD",
            target=target,
            value="PERIOD_CHILD",
            evidence_refs=evidence,
            reviewed_at="2026-11-03T22:01:00+09:00",
            supersedes=parent.resolution_id,
        ),
    )
    replacement_parent = _resign_resolution_file(
        overlay.review_dir / "resolutions" / f"{parent.resolution_id}.json",
        lambda payload: payload.update(
            {
                "evidence_refs": [
                    {
                        "type": "P5_CELL",
                        "table_id": "tampered-table",
                        "cell_id": "tampered-cell",
                    }
                ]
            }
        ),
    )
    replacement_parent_id = replacement_parent.stem
    _resign_resolution_file(
        overlay.review_dir / "resolutions" / f"{child.resolution_id}.json",
        lambda payload: payload.update(
            {
                "base_active_resolution_ids": [replacement_parent_id],
                "base_overlay_set_hash_before": _overlay_hash_before(
                    payload["document_sha256"],
                    payload["base_validation_report_sha256"],
                    (replacement_parent_id,),
                ),
                "supersedes_resolution_id": replacement_parent_id,
            }
        ),
    )

    with pytest.raises(ReviewError) as exc_info:
        materialize_resolved_view(overlay.review_dir)

    assert exc_info.value.reason_code == "P9_EVIDENCE_INVALID"


def test_attestation_rejects_resigned_support_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, _, _, overlay, _, bundle, tasks = _build_extra_issue_fixture(
        tmp_path,
        monkeypatch,
        reason_code="RAW_UNIT_AMBIGUOUS",
        observed={"count": 1},
    )
    task = _task(tasks, "RAW_UNIT_AMBIGUOUS")
    table, cell = _table_and_cell(bundle)
    support = submit_resolution(
        overlay.review_dir,
        _submission(
            task,
            action="SET_UNIT",
            target={
                "target_type": "TABLE_FIELD",
                "table_id": table["table_id"],
                "field": "unit",
            },
            value="UNIT_SUPPORT",
            evidence_refs=[
                {
                    "type": "P5_CELL",
                    "table_id": table["table_id"],
                    "cell_id": cell["cell_id"],
                }
            ],
            reviewed_at="2026-11-03T22:00:00+09:00",
        ),
    )
    tampered = _resign_resolution_file(
        overlay.review_dir / "resolutions" / f"{support.resolution_id}.json",
        lambda payload: payload.update(
            {
                "evidence_refs": [
                    {
                        "type": "P5_CELL",
                        "table_id": "tampered-table",
                        "cell_id": "tampered-cell",
                    }
                ]
            }
        ),
    )
    with pytest.raises(ReviewError) as exc_info:
        submit_resolution(
            overlay.review_dir,
            ResolutionSubmission.from_dict(
                {
                    "review_task_id": task.review_task_id,
                    "action": "ATTEST_ISSUE_RESOLVED",
                    "target": {
                        "target_type": "ISSUE",
                        "issue_id": task.issue_id,
                        "expected_observed_count": 1,
                    },
                    "value": None,
                    "evidence_refs": [],
                    "supporting_resolution_ids": [tampered.stem],
                    "expected_observed_count": 1,
                    "reviewer_type": "HUMAN",
                    "reviewer_id": "p9-attestation-reviewer",
                    "reviewed_at": "2026-11-03T22:01:00+09:00",
                    "justification": "Tampered support evidence must be rejected.",
                }
            ),
        )
    assert exc_info.value.reason_code == "P9_EVIDENCE_INVALID"


def test_cli_resolutions_rejects_semantically_corrupt_store(
    review_fixture,
    capsys,
) -> None:
    _, _, _, _, overlay, _, bundle, tasks = review_fixture
    task = _task(tasks, "RAW_PERIOD_COVERAGE_LOW")
    table, cell = _table_and_cell(bundle)
    resolution = submit_resolution(
        overlay.review_dir,
        _submission(
            task,
            action="SET_PERIOD",
            target={
                "target_type": "TABLE_COLUMN_FIELD",
                "table_id": table["table_id"],
                "column_index": 1,
                "field": "period",
            },
            value="PERIOD_CLI_CORRUPT",
            evidence_refs=[
                {
                    "type": "P5_CELL",
                    "table_id": table["table_id"],
                    "cell_id": cell["cell_id"],
                }
            ],
            reviewed_at="2026-11-03T22:00:00+09:00",
        ),
    )
    _resign_resolution_file(
        overlay.review_dir / "resolutions" / f"{resolution.resolution_id}.json",
        lambda payload: payload["before"].update({"affected_fact_ids": []}),
    )
    with pytest.raises(ReviewError) as exc_info:
        list_resolutions(overlay.review_dir)
    assert exc_info.value.reason_code == "P9_ARTIFACT_INCOMPLETE_OR_CORRUPT"

    exit_code = review_cli_main(
        ["resolutions", "--review-dir", str(overlay.review_dir)]
    )
    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert json.loads(captured.err)["reason_code"] == "P9_ARTIFACT_INCOMPLETE_OR_CORRUPT"


def test_fill_preserves_trimmed_value_and_effective_value(review_fixture) -> None:
    _, _, _, _, overlay, _, bundle, tasks = review_fixture
    task = _task(tasks, "RAW_UNIT_COVERAGE_LOW")
    table, cell = _table_and_cell(bundle)
    saved = submit_resolution(
        overlay.review_dir,
        _submission(
            task,
            action="SET_UNIT",
            target={
                "target_type": "TABLE_FIELD",
                "table_id": table["table_id"],
                "field": "unit",
            },
            value="  人民币   百万元  ",
            evidence_refs=[
                {
                    "type": "P5_CELL",
                    "table_id": table["table_id"],
                    "cell_id": cell["cell_id"],
                }
            ],
            reviewed_at="2026-11-03T22:00:00+09:00",
        ),
    )
    assert saved.value == "人民币   百万元"

    snapshot = materialize_resolved_view(overlay.review_dir)
    rows = [
        json.loads(line)
        for line in snapshot.resolved_facts_path.read_text(encoding="utf-8").splitlines()
        if line
    ]
    affected = set(saved.before["affected_fact_ids"])
    assert affected
    assert {
        row["effective_unit"]
        for row in rows
        if row["raw_fact_id"] in affected
    } == {"人民币   百万元"}


def test_raw_whitespace_equivalence_still_uses_collapsed_comparison(
    review_fixture,
    monkeypatch,
) -> None:
    _, _, _, _, overlay, manifest, bundle, tasks = review_fixture
    fact = bundle.context.facts[0]
    fact["raw_unit"] = "人民币 百万元"
    monkeypatch.setattr(
        review_store_module,
        "load_review_base",
        lambda review_dir: (manifest, bundle, tasks),
    )
    task = _task(tasks, "RAW_UNIT_COVERAGE_LOW")
    with pytest.raises(ReviewError) as exc_info:
        submit_resolution(
            overlay.review_dir,
            _submission(
                task,
                action="SET_UNIT",
                target={
                    "target_type": "FACT_FIELD",
                    "raw_fact_id": fact["raw_fact_id"],
                    "field": "unit",
                },
                value="  人民币   百万元  ",
                evidence_refs=[
                    {"type": "P6_EVIDENCE", "evidence_id": fact["evidence_id"]}
                ],
                reviewed_at="2026-11-03T22:00:00+09:00",
            ),
        )
    assert exc_info.value.reason_code == "P9_RESOLUTION_NO_EFFECT"


def test_justification_uses_raw_4000_character_boundary(review_fixture) -> None:
    _, _, _, _, _, _, _, tasks = review_fixture
    task = _task(tasks, "RAW_PERIOD_COVERAGE_LOW")
    base = {
        "action": "SET_PERIOD",
        "target": {},
        "value": "PERIOD",
        "evidence_refs": [],
        "reviewed_at": "2026-11-03T22:00:00+09:00",
    }
    validate_reviewer(
        _submission(task, **base, justification="x" * 4000)
    )
    for justification in ("x" * 4001, "x" + (" " * 4000), " " * 20):
        with pytest.raises(ReviewError) as exc_info:
            validate_reviewer(
                _submission(task, **base, justification=justification)
            )
        assert exc_info.value.reason_code == "P9_INVALID_RESOLUTION"


def test_prepare_rejects_unknown_deterministic_staging_directory(tmp_path: Path) -> None:
    catalog, _ = _build_fixture(tmp_path)
    review_root = tmp_path / "review"
    review_root.mkdir()
    stale = review_root / f".{DOC_SHA}.tmp"
    stale.mkdir()

    with pytest.raises(ReviewError) as exc_info:
        prepare_review_overlay(tmp_path, catalog, DOC_SHA, review_root)

    assert exc_info.value.reason_code == "P9_PERSIST_FAILED"
    assert stale.is_dir()


def test_resolved_parsed_data_record_is_deterministic(review_fixture) -> None:
    _, _, _, _, overlay, _, _, _ = review_fixture
    snapshot = materialize_resolved_view(overlay.review_dir)
    slot = FilingSlotKey(
        market="CN",
        company_id="CN:SYNTH",
        filing_type="ANNUAL_REPORT",
        fiscal_year=2024,
        raw_fiscal_period="FY",
    )

    first = build_resolved_parsed_data_record(
        snapshot,
        slot,
        "review/snapshot",
    )
    second = build_resolved_parsed_data_record(
        snapshot,
        slot,
        "review/snapshot",
    )

    assert first == second
    assert first.document_sha256 == DOC_SHA
    assert first.artifact_path == "review/snapshot"
    assert P3_PARSER_VERSION in first.parser_version
    assert RECONSTRUCTION_VERSION in first.parser_version
    assert EXTRACTOR_VERSION in first.parser_version
    assert P7_POLICY_VERSION in first.parser_version


def test_cli_success_writes_one_json_document_to_stdout(review_fixture, capsys) -> None:
    _, _, _, _, overlay, _, _, _ = review_fixture

    exit_code = review_cli_main(
        ["tasks", "--review-dir", str(overlay.review_dir)]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""
    lines = captured.out.splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["status"] == "OK"
    assert isinstance(payload["data"], list)


def test_cli_diagnostics_are_json_on_stderr_only(tmp_path: Path, capsys) -> None:
    exit_code = review_cli_main(
        ["tasks", "--review-dir", str(tmp_path / "missing-review")]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    lines = captured.err.splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["status"] == "ERROR"
    assert payload["reason_code"] == "P9_ARTIFACT_INCOMPLETE_OR_CORRUPT"


def test_cli_full_success_matrix_is_json_only(
    review_fixture,
    tmp_path: Path,
    capsys,
) -> None:
    root, catalog, _, _, overlay, _, bundle, tasks = review_fixture

    def call(args: list[str]) -> str:
        exit_code = review_cli_main(args)
        captured = capsys.readouterr()
        assert exit_code == 0
        assert captured.err == ""
        lines = captured.out.splitlines()
        assert len(lines) == 1
        payload = json.loads(lines[0])
        assert payload["status"] == "OK"
        return lines[0]

    prepare_args = [
        "prepare",
        "--project-root",
        str(root),
        "--catalog",
        str(catalog),
        "--document-sha256",
        DOC_SHA,
        "--review-root",
        str(root / "review"),
    ]
    assert call(prepare_args) == call(prepare_args)

    tasks_args = ["tasks", "--review-dir", str(overlay.review_dir)]
    assert call(tasks_args) == call(tasks_args)

    table, cell = _table_and_cell(bundle)
    period_task = _task(tasks, "RAW_PERIOD_COVERAGE_LOW")
    unit_task = _task(tasks, "RAW_UNIT_COVERAGE_LOW")
    period_submission = _submission(
        period_task,
        action="SET_PERIOD",
        target={
            "target_type": "TABLE_COLUMN_FIELD",
            "table_id": table["table_id"],
            "column_index": 1,
            "field": "period",
        },
        value="CLI_PERIOD",
        evidence_refs=[
            {
                "type": "P5_CELL",
                "table_id": table["table_id"],
                "cell_id": cell["cell_id"],
            }
        ],
        reviewed_at="2026-11-03T22:00:00+09:00",
    )
    period_json = json.dumps(
        _submission_payload(period_submission),
        ensure_ascii=False,
        sort_keys=True,
    )
    submit_json_args = [
        "submit",
        "--review-dir",
        str(overlay.review_dir),
        "--input-json",
        period_json,
    ]
    assert call(submit_json_args)

    unit_submission = _submission(
        unit_task,
        action="SET_UNIT",
        target={
            "target_type": "TABLE_FIELD",
            "table_id": table["table_id"],
            "field": "unit",
        },
        value="CLI_UNIT",
        evidence_refs=[
            {
                "type": "P5_CELL",
                "table_id": table["table_id"],
                "cell_id": cell["cell_id"],
            }
        ],
        reviewed_at="2026-11-03T22:01:00+09:00",
    )
    input_file = tmp_path / "cli-submission.json"
    input_file.write_text(
        json.dumps(_submission_payload(unit_submission), ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
        newline="\n",
    )
    submit_file_args = [
        "submit",
        "--review-dir",
        str(overlay.review_dir),
        "--input-file",
        str(input_file),
    ]
    assert call(submit_file_args)

    resolutions_args = ["resolutions", "--review-dir", str(overlay.review_dir)]
    assert call(resolutions_args) == call(resolutions_args)

    materialize_args = ["materialize", "--review-dir", str(overlay.review_dir)]
    assert call(materialize_args) == call(materialize_args)

    report_args = ["report", "--review-dir", str(overlay.review_dir)]
    assert call(report_args) == call(report_args)


@pytest.mark.parametrize("payload", ["{", "[]"])
def test_cli_submit_rejects_malformed_and_non_object_json(
    review_fixture,
    capsys,
    payload: str,
) -> None:
    _, _, _, _, overlay, _, _, _ = review_fixture

    exit_code = review_cli_main(
        [
            "submit",
            "--review-dir",
            str(overlay.review_dir),
            "--input-json",
            payload,
        ]
    )
    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    lines = captured.err.splitlines()
    assert len(lines) == 1
    diagnostic = json.loads(lines[0])
    assert diagnostic["status"] == "ERROR"
    assert diagnostic["reason_code"] == "P9_INVALID_RESOLUTION"


def test_attestation_rejects_direct_evidence_and_inherits_supporting_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, _, _, overlay, _, bundle, tasks = _build_extra_issue_fixture(
        tmp_path,
        monkeypatch,
        reason_code="RAW_PERIOD_AMBIGUOUS",
        observed={"count": 1},
    )
    task = _task(tasks, "RAW_PERIOD_AMBIGUOUS")
    table, cell = _table_and_cell(bundle)
    target = {
        "target_type": "TABLE_COLUMN_FIELD",
        "table_id": table["table_id"],
        "column_index": 1,
        "field": "period",
    }
    evidence = [
        {
            "type": "P5_CELL",
            "table_id": table["table_id"],
            "cell_id": cell["cell_id"],
        }
    ]
    support = submit_resolution(
        overlay.review_dir,
        _submission(
            task,
            action="SET_PERIOD",
            target=target,
            value="PERIOD_AMBIGUOUS",
            evidence_refs=evidence,
            reviewed_at="2026-11-03T22:00:00+09:00",
        ),
    )
    second_fact = bundle.context.facts[1]
    support_two = submit_resolution(
        overlay.review_dir,
        _submission(
            task,
            action="SET_PERIOD",
            target={
                "target_type": "FACT_FIELD",
                "raw_fact_id": second_fact["raw_fact_id"],
                "field": "period",
            },
            value="PERIOD_AMBIGUOUS",
            evidence_refs=[
                {
                    "type": "P6_EVIDENCE",
                    "evidence_id": second_fact["evidence_id"],
                }
            ],
            reviewed_at="2026-11-03T22:00:30+09:00",
        ),
    )
    attestation_target = {
        "target_type": "ISSUE",
        "issue_id": task.issue_id,
        "expected_observed_count": 1,
    }
    direct_evidence = ResolutionSubmission.from_dict(
        {
            "review_task_id": task.review_task_id,
            "action": "ATTEST_ISSUE_RESOLVED",
            "target": attestation_target,
            "value": None,
            "evidence_refs": evidence,
            "supporting_resolution_ids": [
                support.resolution_id,
                support_two.resolution_id,
            ],
            "expected_observed_count": 1,
            "reviewer_type": "HUMAN",
            "reviewer_id": "p9-attestation-reviewer",
            "reviewed_at": "2026-11-03T22:01:00+09:00",
            "justification": "Attestation must inherit support evidence.",
        }
    )
    with pytest.raises(ReviewError) as exc_info:
        submit_resolution(overlay.review_dir, direct_evidence)
    assert exc_info.value.reason_code == "P9_EVIDENCE_INVALID"

    attestation = ResolutionSubmission.from_dict(
        {
            "review_task_id": task.review_task_id,
            "action": "ATTEST_ISSUE_RESOLVED",
            "target": attestation_target,
            "value": None,
            "evidence_refs": [],
            "supporting_resolution_ids": [
                support.resolution_id,
                support_two.resolution_id,
            ],
            "expected_observed_count": 1,
            "reviewer_type": "HUMAN",
            "reviewer_id": "p9-attestation-reviewer",
            "reviewed_at": "2026-11-03T22:02:00+09:00",
            "justification": "Attestation must inherit support evidence.",
        }
    )
    saved = submit_resolution(overlay.review_dir, attestation)
    expected_refs = tuple(
        sorted(
            {
                json.dumps(ref, ensure_ascii=False, sort_keys=True, separators=(",", ":")): ref
                for resolution in (support, support_two)
                for ref in resolution.evidence_refs
            }.values(),
            key=lambda ref: json.dumps(
                ref, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ),
        )
    )
    assert saved.evidence_refs == expected_refs
    assert saved.evidence_pages == tuple(
        sorted(set(support.evidence_pages) | set(support_two.evidence_pages))
    )


def test_attestation_expected_observed_count_must_match_base_issue(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, _, _, overlay, _, bundle, tasks = _build_extra_issue_fixture(
        tmp_path,
        monkeypatch,
        reason_code="RAW_UNIT_AMBIGUOUS",
        observed={"count": 3},
    )
    task = _task(tasks, "RAW_UNIT_AMBIGUOUS")
    table, cell = _table_and_cell(bundle)
    support = submit_resolution(
        overlay.review_dir,
        _submission(
            task,
            action="SET_UNIT",
            target={
                "target_type": "TABLE_FIELD",
                "table_id": table["table_id"],
                "field": "unit",
            },
            value="UNIT_AMBIGUOUS",
            evidence_refs=[
                {
                    "type": "P5_CELL",
                    "table_id": table["table_id"],
                    "cell_id": cell["cell_id"],
                }
            ],
            reviewed_at="2026-11-03T22:00:00+09:00",
        ),
    )
    with pytest.raises(ReviewError) as exc_info:
        submit_resolution(
            overlay.review_dir,
            ResolutionSubmission.from_dict(
                {
                    "review_task_id": task.review_task_id,
                    "action": "ATTEST_ISSUE_RESOLVED",
                    "target": {
                        "target_type": "ISSUE",
                        "issue_id": task.issue_id,
                        "expected_observed_count": 2,
                    },
                    "value": None,
                    "evidence_refs": [],
                    "supporting_resolution_ids": [support.resolution_id],
                    "expected_observed_count": 2,
                    "reviewer_type": "HUMAN",
                    "reviewer_id": "p9-attestation-reviewer",
                    "reviewed_at": "2026-11-03T22:01:00+09:00",
                    "justification": "Mismatched observed count must be rejected.",
                }
            ),
        )
    assert exc_info.value.reason_code == "P9_INVALID_RESOLUTION"


def test_unsupported_review_reason_remains_unresolved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, _, _, overlay, _, _, tasks = _build_extra_issue_fixture(
        tmp_path,
        monkeypatch,
        reason_code="FUTURE_REVIEW_REASON",
        observed={"count": 1},
    )
    task = _task(tasks, "FUTURE_REVIEW_REASON")
    assert task.reviewability is Reviewability.UNSUPPORTED
    assert task.supported_actions == ()

    snapshot = materialize_resolved_view(overlay.review_dir)
    issue = next(
        row
        for row in json.loads(
            "[" + ",".join(
                line
                for line in snapshot.resolved_issues_path.read_text(encoding="utf-8").splitlines()
                if line
            ) + "]"
        )
        if row["issue_id"] == task.issue_id
    )
    assert issue["resolved_state"] == "UNSUPPORTED"
    assert snapshot.resolved_validation_status.value == "REVIEW_REQUIRED"


def test_same_value_overlaps_are_deterministic(review_fixture) -> None:
    _, _, _, _, overlay, _, bundle, tasks = review_fixture
    task = _task(tasks, "RAW_PERIOD_COVERAGE_LOW")
    table, cell = _table_and_cell(bundle)
    target = {
        "target_type": "TABLE_COLUMN_FIELD",
        "table_id": table["table_id"],
        "column_index": 1,
        "field": "period",
    }
    evidence = [
        {
            "type": "P5_CELL",
            "table_id": table["table_id"],
            "cell_id": cell["cell_id"],
        }
    ]
    first = submit_resolution(
        overlay.review_dir,
        _submission(
            task,
            action="SET_PERIOD",
            target=target,
            value="SAME_PERIOD",
            evidence_refs=evidence,
            reviewed_at="2026-11-03T22:00:00+09:00",
        ),
    )
    second = submit_resolution(
        overlay.review_dir,
        _submission(
            task,
            action="SET_PERIOD",
            target=target,
            value="SAME_PERIOD",
            evidence_refs=evidence,
            reviewed_at="2026-11-03T22:01:00+09:00",
        ),
    )
    snapshot = materialize_resolved_view(overlay.review_dir)
    assert snapshot.active_resolution_count == 2
    row = next(
        json.loads(line)
        for line in snapshot.resolved_facts_path.read_text(encoding="utf-8").splitlines()
        if line and json.loads(line)["raw_fact_id"] in first.before["affected_fact_ids"]
    )
    assert row["overlay_resolution_ids"] == sorted(
        [first.resolution_id, second.resolution_id]
    )


def test_conflicting_active_overlay_values_fail_materialization(review_fixture) -> None:
    _, _, _, _, overlay, _, bundle, tasks = review_fixture
    task = _task(tasks, "RAW_PERIOD_COVERAGE_LOW")
    table, cell = _table_and_cell(bundle)
    target = {
        "target_type": "TABLE_COLUMN_FIELD",
        "table_id": table["table_id"],
        "column_index": 1,
        "field": "period",
    }
    evidence = [
        {
            "type": "P5_CELL",
            "table_id": table["table_id"],
            "cell_id": cell["cell_id"],
        }
    ]
    submit_resolution(
        overlay.review_dir,
        _submission(
            task,
            action="SET_PERIOD",
            target=target,
            value="PERIOD_A",
            evidence_refs=evidence,
            reviewed_at="2026-11-03T22:00:00+09:00",
        ),
    )
    submit_resolution(
        overlay.review_dir,
        _submission(
            task,
            action="SET_PERIOD",
            target=target,
            value="PERIOD_B",
            evidence_refs=evidence,
            reviewed_at="2026-11-03T22:01:00+09:00",
        ),
    )
    with pytest.raises(ReviewError) as exc_info:
        materialize_resolved_view(overlay.review_dir)
    assert exc_info.value.reason_code == "P9_RESOLUTION_CONFLICT"


def test_invalid_supersession_parent_is_rejected(review_fixture) -> None:
    _, _, _, _, overlay, _, bundle, tasks = review_fixture
    task = _task(tasks, "RAW_PERIOD_COVERAGE_LOW")
    table, cell = _table_and_cell(bundle)
    with pytest.raises(ReviewError) as exc_info:
        submit_resolution(
            overlay.review_dir,
            _submission(
                task,
                action="SET_PERIOD",
                target={
                    "target_type": "TABLE_COLUMN_FIELD",
                    "table_id": table["table_id"],
                    "column_index": 1,
                    "field": "period",
                },
                value="PERIOD_A",
                evidence_refs=[
                    {
                        "type": "P5_CELL",
                        "table_id": table["table_id"],
                        "cell_id": cell["cell_id"],
                    }
                ],
                reviewed_at="2026-11-03T22:00:00+09:00",
                supersedes="not-an-active-resolution",
            ),
        )
    assert exc_info.value.reason_code == "P9_SUPERSESSION_INVALID"


def test_competing_supersession_child_is_rejected(review_fixture) -> None:
    _, _, _, _, overlay, _, bundle, tasks = review_fixture
    task = _task(tasks, "RAW_PERIOD_COVERAGE_LOW")
    table, cell = _table_and_cell(bundle)
    target = {
        "target_type": "TABLE_COLUMN_FIELD",
        "table_id": table["table_id"],
        "column_index": 1,
        "field": "period",
    }
    evidence = [
        {
            "type": "P5_CELL",
            "table_id": table["table_id"],
            "cell_id": cell["cell_id"],
        }
    ]
    parent = submit_resolution(
        overlay.review_dir,
        _submission(
            task,
            action="SET_PERIOD",
            target=target,
            value="PERIOD_PARENT",
            evidence_refs=evidence,
            reviewed_at="2026-11-03T22:00:00+09:00",
        ),
    )
    submit_resolution(
        overlay.review_dir,
        _submission(
            task,
            action="SET_PERIOD",
            target=target,
            value="PERIOD_CHILD_A",
            evidence_refs=evidence,
            reviewed_at="2026-11-03T22:01:00+09:00",
            supersedes=parent.resolution_id,
        ),
    )
    with pytest.raises(ReviewError) as exc_info:
        submit_resolution(
            overlay.review_dir,
            _submission(
                task,
                action="SET_PERIOD",
                target=target,
                value="PERIOD_CHILD_B",
                evidence_refs=evidence,
                reviewed_at="2026-11-03T22:02:00+09:00",
                supersedes=parent.resolution_id,
            ),
        )
    assert exc_info.value.reason_code == "P9_SUPERSESSION_INVALID"


def test_supersession_cycle_is_rejected() -> None:
    first = _graph_resolution("a", parent="b", prior=("b",))
    second = _graph_resolution("b", parent="a", prior=("a",))
    with pytest.raises(ReviewError) as exc_info:
        _validate_graph((first, second))
    assert exc_info.value.reason_code == "P9_RESOLUTION_STORE_CORRUPT"


def test_competing_children_are_rejected_by_graph_validation() -> None:
    parent = _graph_resolution("parent", parent=None, prior=())
    child_a = _graph_resolution("child-a", parent="parent", prior=("parent",))
    child_b = _graph_resolution("child-b", parent="parent", prior=("parent",))
    with pytest.raises(ReviewError) as exc_info:
        _validate_graph((parent, child_a, child_b))
    assert exc_info.value.reason_code == "P9_RESOLUTION_CONFLICT"


def test_raw_nonnull_same_value_is_noop(review_fixture, monkeypatch) -> None:
    _, _, _, _, overlay, manifest, bundle, tasks = review_fixture
    fact = bundle.context.facts[0]
    fact["raw_period_label"] = "RAW_PERIOD"
    monkeypatch.setattr(
        review_store_module,
        "load_review_base",
        lambda review_dir: (manifest, bundle, tasks),
    )
    task = _task(tasks, "RAW_PERIOD_COVERAGE_LOW")
    with pytest.raises(ReviewError) as exc_info:
        submit_resolution(
            overlay.review_dir,
            _submission(
                task,
                action="SET_PERIOD",
                target={
                    "target_type": "FACT_FIELD",
                    "raw_fact_id": fact["raw_fact_id"],
                    "field": "period",
                },
                value="RAW_PERIOD",
                evidence_refs=[
                    {"type": "P6_EVIDENCE", "evidence_id": fact["evidence_id"]}
                ],
                reviewed_at="2026-11-03T22:00:00+09:00",
            ),
        )
    assert exc_info.value.reason_code == "P9_RESOLUTION_NO_EFFECT"


def test_raw_nonnull_conflict_is_rejected(review_fixture, monkeypatch) -> None:
    _, _, _, _, overlay, manifest, bundle, tasks = review_fixture
    fact = bundle.context.facts[0]
    fact["raw_period_label"] = "RAW_PERIOD"
    monkeypatch.setattr(
        review_store_module,
        "load_review_base",
        lambda review_dir: (manifest, bundle, tasks),
    )
    task = _task(tasks, "RAW_PERIOD_COVERAGE_LOW")
    with pytest.raises(ReviewError) as exc_info:
        submit_resolution(
            overlay.review_dir,
            _submission(
                task,
                action="SET_PERIOD",
                target={
                    "target_type": "FACT_FIELD",
                    "raw_fact_id": fact["raw_fact_id"],
                    "field": "period",
                },
                value="OTHER_PERIOD",
                evidence_refs=[
                    {"type": "P6_EVIDENCE", "evidence_id": fact["evidence_id"]}
                ],
                reviewed_at="2026-11-03T22:00:00+09:00",
            ),
        )
    assert exc_info.value.reason_code == "P9_PATCH_CONFLICTS_WITH_RAW"


def test_caller_cannot_override_prior_overlay_state(review_fixture) -> None:
    _, _, _, _, overlay, _, bundle, tasks = review_fixture
    task = _task(tasks, "RAW_PERIOD_COVERAGE_LOW")
    table, cell = _table_and_cell(bundle)
    submission = {
        "review_task_id": task.review_task_id,
        "action": "SET_PERIOD",
        "target": {
            "target_type": "TABLE_COLUMN_FIELD",
            "table_id": table["table_id"],
            "column_index": 1,
            "field": "period",
        },
        "value": "PERIOD_A",
        "evidence_refs": [
            {
                "type": "P5_CELL",
                "table_id": table["table_id"],
                "cell_id": cell["cell_id"],
            }
        ],
        "reviewer_type": "HUMAN",
        "reviewer_id": "p9-state-reviewer",
        "reviewed_at": "2026-11-03T22:00:00+09:00",
        "justification": "Store computes historical state.",
        "base_active_resolution_ids": ["forged"],
        "base_overlay_set_hash_before": "forged",
    }
    saved = submit_resolution(overlay.review_dir, submission)
    assert saved.base_active_resolution_ids == ()
    assert saved.base_overlay_set_hash_before != "forged"


def test_base_fingerprint_mutation_is_rejected(review_fixture) -> None:
    _, _, artifacts, _, overlay, _, _, _ = review_fixture
    report_path = artifacts["p7"] / "validation_report.json"
    original = report_path.read_bytes()
    try:
        report_path.write_bytes(original + b"\n")
        with pytest.raises(ReviewError) as exc_info:
            list_review_tasks(overlay.review_dir)
        assert exc_info.value.reason_code == "P9_BASE_ARTIFACT_CHANGED"
    finally:
        report_path.write_bytes(original)


@pytest.mark.parametrize("status", [ValidationStatus.FAIL, ValidationStatus.BLOCKED])
def test_fail_and_blocked_base_statuses_are_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    status: ValidationStatus,
) -> None:
    catalog, _ = _build_fixture(tmp_path)
    monkeypatch.setattr(
        review_queue_module,
        "load_validation_result",
        lambda *args, **kwargs: SimpleNamespace(
            document_sha256=DOC_SHA,
            validation_status=status,
        ),
    )
    with pytest.raises(ReviewError) as exc_info:
        prepare_review_overlay(tmp_path, catalog, DOC_SHA, tmp_path / "review")
    assert exc_info.value.reason_code == "P9_BASE_STATUS_NOT_REVIEWABLE"


def test_snapshot_semantic_tamper_is_rejected(review_fixture) -> None:
    _, _, _, _, overlay, _, _, _ = review_fixture
    snapshot = materialize_resolved_view(overlay.review_dir)
    path = snapshot.resolved_facts_path
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(ReviewError) as exc_info:
        load_resolved_snapshot(snapshot.snapshot_dir, overlay.review_dir)
    assert exc_info.value.reason_code == "P9_ARTIFACT_INCOMPLETE_OR_CORRUPT"


def test_review_source_has_no_forbidden_network_or_ai_surface() -> None:
    review_root = Path(__file__).parents[3] / "src" / "financial_filing_data_foundation" / "review"
    forbidden = (
        "openai",
        "anthropic",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "mcp.server",
        "mcpserver",
        "subprocess",
        "uuid",
        "random",
    )
    for path in review_root.glob("*.py"):
        source = path.read_text(encoding="utf-8").lower()
        for token in forbidden:
            assert token not in source, f"{token} found in {path.name}"
    assert "register_parsed_data" not in (
        review_root / "resolve.py"
    ).read_text(encoding="utf-8")


def test_synthetic_golden_resolves_period_unit_and_core_to_pass(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, _, artifacts, overlay, _, bundle, tasks = _build_extra_issue_fixture(
        tmp_path,
        monkeypatch,
        reason_code="CORE_STATEMENT_COVERAGE_LOW",
        observed={"signal_count": 1},
        extra_tables=True,
    )
    before = {stage: _tree_hash(path) for stage, path in artifacts.items()}
    table, cell = _table_and_cell(bundle)
    period_task = _task(tasks, "RAW_PERIOD_COVERAGE_LOW")
    unit_task = _task(tasks, "RAW_UNIT_COVERAGE_LOW")
    core_task = _task(tasks, "CORE_STATEMENT_COVERAGE_LOW")
    evidence = [
        {
            "type": "P5_CELL",
            "table_id": table["table_id"],
            "cell_id": cell["cell_id"],
        }
    ]
    submit_resolution(
        overlay.review_dir,
        _submission(
            period_task,
            action="SET_PERIOD",
            target={
                "target_type": "TABLE_COLUMN_FIELD",
                "table_id": table["table_id"],
                "column_index": 1,
                "field": "period",
            },
            value="PERIOD_GOLDEN",
            evidence_refs=evidence,
            reviewed_at="2026-11-03T22:00:00+09:00",
        ),
    )
    submit_resolution(
        overlay.review_dir,
        _submission(
            unit_task,
            action="SET_UNIT",
            target={
                "target_type": "TABLE_FIELD",
                "table_id": table["table_id"],
                "field": "unit",
            },
            value="UNIT_GOLDEN",
            evidence_refs=evidence,
            reviewed_at="2026-11-03T22:01:00+09:00",
        ),
    )
    submit_resolution(
        overlay.review_dir,
        _submission(
            core_task,
            action="CLASSIFY_TABLE_STATEMENT",
            target={
                "target_type": "TABLE_STATEMENT_CLASS",
                "table_id": table["table_id"],
            },
            value="BALANCE",
            evidence_refs=evidence,
            reviewed_at="2026-11-03T22:02:00+09:00",
        ),
    )
    second_table = bundle.context.tables[1]
    second_cell = second_table["rows"][0]["cells"][0]
    submit_resolution(
        overlay.review_dir,
        _submission(
            core_task,
            action="CLASSIFY_TABLE_STATEMENT",
            target={
                "target_type": "TABLE_STATEMENT_CLASS",
                "table_id": second_table["table_id"],
            },
            value="INCOME",
            evidence_refs=[
                {
                    "type": "P5_CELL",
                    "table_id": second_table["table_id"],
                    "cell_id": second_cell["cell_id"],
                }
            ],
            reviewed_at="2026-11-03T22:03:00+09:00",
        ),
    )
    snapshot = materialize_resolved_view(overlay.review_dir)
    slot = FilingSlotKey(
        market="CN",
        company_id="CN:GOLDEN",
        filing_type="ANNUAL_REPORT",
        fiscal_year=2024,
        raw_fiscal_period="FY",
    )
    record = build_resolved_parsed_data_record(
        snapshot,
        slot,
        "review/synthetic-golden",
    )
    assert snapshot.resolved_validation_status.value == "PASS"
    assert snapshot.resolved_reuse_eligible is True
    assert record.validation_status.value == "PASS"
    assert record.schema_version == "p9-resolved-view-v1"
    assert record.artifact_path == "review/synthetic-golden"
    assert {row["resolved_state"] for row in (
        json.loads(line)
        for line in snapshot.resolved_issues_path.read_text(encoding="utf-8").splitlines()
        if line
    )} == {"RESOLVED"}
    assert {stage: _tree_hash(path) for stage, path in artifacts.items()} == before
