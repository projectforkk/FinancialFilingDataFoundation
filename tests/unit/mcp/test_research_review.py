from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import financial_filing_data_foundation.mcp.research_review as rr
from financial_filing_data_foundation.mcp.research_review import (
    ResearchReviewError,
    ResearchReviewService,
)


SHA = "a" * 64
BASE_HASH = "b" * 64


class FakeCatalog:
    catalog_path = Path("catalog.json")

    def get(self, value):
        if value == SHA:
            return SimpleNamespace(document_sha256=SHA)
        return None


class FakeP8:
    def __init__(self):
        self.fact = {
            "raw_fact_id": "fact-1",
            "raw_metric_name": "Revenue",
            "raw_value": "100",
            "parsed_numeric_value": "100",
            "raw_period_label": None,
            "raw_unit": None,
            "raw_scope": None,
            "page_no": 2,
            "table_id": "table-1",
            "evidence_id": "evidence-1",
        }

    def get_document(self, sha):
        return {
            "data": {
                "validation_status": "REVIEW_REQUIRED",
                "reuse_eligible": False,
                "review_issue_count": 1,
                "blocking_issue_count": 0,
                "page_count": 3,
            }
        }

    def get_fact(self, sha, fact_id):
        return {"data": dict(self.fact)}

    def get_evidence(self, sha, evidence_id):
        return {"data": {"evidence_id": evidence_id, "page_no": 2}}

    def get_table(self, sha, table_id, max_rows):
        return {
            "data": {
                "table_id": table_id,
                "page_no": 2,
                "table_group_id": None,
                "rows": [],
            }
        }

    def read_pages(self, sha, page_nos):
        return {
            "data": {
                "pages": [
                    {"page_no": page_no, "text": f"page {page_no}"}
                    for page_no in page_nos
                ]
            }
        }

    def list_raw_facts(self, *args):
        return {"data": {"facts": [dict(self.fact)], "total": 1}}

    def _bundle(self, sha):
        return SimpleNamespace(facts=(dict(self.fact),))


def _task():
    return SimpleNamespace(
        review_task_id="task-1",
        document_sha256=SHA,
        base_validation_report_sha256=BASE_HASH,
        issue_id="issue-1",
        reason_code="RAW_UNIT_AMBIGUOUS",
        message="unit",
        observed={},
        reviewability=rr.Reviewability.SUPPORTED,
        supported_actions=("SET_UNIT",),
        required_evidence_types=("P5_CELL",),
        scope="table",
        page_no=2,
        table_id="table-1",
        raw_fact_ids=("fact-1",),
        evidence_ids=("evidence-1",),
    )


def _service(tmp_path: Path, profile="RESEARCH_FALLBACK"):
    return ResearchReviewService(
        project_root=tmp_path,
        catalog=FakeCatalog(),
        p8_service=FakeP8(),
        review_root=tmp_path / "review",
        profile=profile,
    )


def _review_dir(tmp_path: Path) -> Path:
    path = tmp_path / "review" / SHA
    (path / "resolutions").mkdir(parents=True)
    (path / "snapshots").mkdir()
    (path / "review_manifest.json").write_text(
        json.dumps(
            {
                "document_sha256": SHA,
                "base_validation_report_sha256": BASE_HASH,
            }
        ),
        encoding="utf-8",
    )
    return path


def test_no_overlay_is_needs_review(tmp_path: Path) -> None:
    service = _service(tmp_path)
    state = service.get_review_state(SHA)["data"]
    assert state["quality_state"] == "NEEDS_REVIEW"
    assert state["write_enabled"] is False


def test_active_without_snapshot_is_needs_materialization(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _review_dir(tmp_path)
    monkeypatch.setattr(rr, "p9_list_review_tasks", lambda _: (_task(),))
    resolution = SimpleNamespace(
        resolution_id="r1",
        review_task_id="task-1",
    )
    monkeypatch.setattr(rr, "active_resolutions", lambda _: (resolution,))

    service = _service(tmp_path)
    state = service.get_review_state(SHA)["data"]

    assert state["quality_state"] == "NEEDS_MATERIALIZATION"
    assert state["active_resolution_count"] == 1


def test_complete_reviewed_uses_matching_snapshot(
    tmp_path: Path,
    monkeypatch,
) -> None:
    review_dir = _review_dir(tmp_path)
    monkeypatch.setattr(rr, "p9_list_review_tasks", lambda _: (_task(),))
    resolution = SimpleNamespace(
        resolution_id="r1",
        review_task_id="task-1",
    )
    monkeypatch.setattr(rr, "active_resolutions", lambda _: (resolution,))
    overlay_hash = rr._overlay_set_hash(SHA, BASE_HASH, ("r1",))
    snapshot_dir = review_dir / "snapshots" / overlay_hash
    snapshot_dir.mkdir()
    fake_snapshot = SimpleNamespace(
        overlay_set_hash=overlay_hash,
        resolved_facts_path=snapshot_dir / "resolved_facts.jsonl",
        report={
            "resolved_validation_status": "PASS",
            "resolved_reuse_eligible": True,
            "resolved_review_issue_count": 1,
            "unresolved_review_issue_count": 0,
            "unsupported_review_issue_count": 0,
        },
    )
    monkeypatch.setattr(rr, "load_resolved_snapshot", lambda *args: fake_snapshot)

    service = _service(tmp_path)
    state = service.get_review_state(SHA)["data"]

    assert state["quality_state"] == "COMPLETE_REVIEWED"
    assert state["snapshot_available"] is True


def test_review_context_collects_structured_evidence(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _review_dir(tmp_path)
    monkeypatch.setattr(rr, "p9_list_review_tasks", lambda _: (_task(),))
    monkeypatch.setattr(rr, "active_resolutions", lambda _: ())

    context = _service(tmp_path).get_review_context(SHA, "task-1")["data"]

    assert context["task"]["reason_code"] == "RAW_UNIT_AMBIGUOUS"
    assert context["raw_facts"][0]["raw_fact_id"] == "fact-1"
    assert context["evidence"][0]["evidence_id"] == "evidence-1"
    assert [row["page_no"] for row in context["neighbor_pages"]] == [1, 2, 3]
    assert context["recommended_visual_targets"][0]["kind"] == "TABLE"


def test_research_profile_rejects_write(tmp_path: Path) -> None:
    service = _service(tmp_path)
    with pytest.raises(ResearchReviewError) as exc_info:
        service.prepare_review_overlay(SHA)
    assert exc_info.value.reason_code == "RESEARCH_MCP_WRITE_DISABLED"


def test_quality_review_requires_optimistic_state_match(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _review_dir(tmp_path)
    monkeypatch.setattr(rr, "p9_list_review_tasks", lambda _: (_task(),))
    monkeypatch.setattr(rr, "active_resolutions", lambda _: ())

    service = _service(tmp_path, "QUALITY_REVIEW")
    with pytest.raises(ResearchReviewError) as exc_info:
        service.submit_review_resolution(
            SHA,
            {
                "review_task_id": "task-1",
                "action": "SET_UNIT",
                "target": {
                    "target_type": "FACT_FIELD",
                    "raw_fact_id": "fact-1",
                    "field": "unit",
                },
                "value": "CNY",
                "evidence_refs": [],
                "reviewer_type": "HUMAN",
                "reviewer_id": "reviewer",
                "reviewed_at": "2026-11-05T00:00:00+00:00",
                "justification": "test",
            },
            expected_base_validation_report_sha256="c" * 64,
            expected_overlay_set_hash_before="d" * 64,
        )
    assert exc_info.value.reason_code == "RESEARCH_MCP_REVIEW_STATE_CHANGED"


def test_locator_returns_page_table_fact_candidates_without_creating_fact(
    tmp_path: Path,
    monkeypatch,
) -> None:
    service = _service(tmp_path)
    fake = service.p8
    fake.literal_page_search_internal = lambda sha, query, limit: (
        {
            "page_no": 2,
            "match_type": "LITERAL",
            "snippet": "关键审计事项 收入确认",
            "match_offset": 0,
        },
    )
    fake.search_document = lambda sha, query, limit: {
        "data": {"results": [{"page_no": 2, "score": 1.0}]}
    }
    fake.list_tables = lambda sha, page_no, offset, limit: {
        "data": {
            "tables": [
                {
                    "table_id": "table-1",
                    "page_no": 2,
                    "table_group_id": None,
                    "bbox": [1, 2, 3, 4],
                }
            ]
        }
    }
    fake.list_raw_facts = lambda sha, page_no, metric, offset, limit: {
        "data": {"facts": [dict(fake.fact)]}
    }

    result = service.locate_evidence(
        SHA,
        "关键审计事项",
        limit=5,
    )["data"]

    assert result["matched"] is True
    assert result["matches"][0]["page_no"] == 2
    assert result["matches"][0]["tables"][0]["table_id"] == "table-1"
    assert result["matches"][0]["raw_facts"][0]["raw_fact_id"] == "fact-1"
    assert result["recommended_visual_targets"][0]["kind"] == "TABLE"
    assert "do not create RawFacts" not in result["interpretation"]
    assert "does not" not in result["interpretation"].lower()
    assert "upstream fix" in result["interpretation"]
