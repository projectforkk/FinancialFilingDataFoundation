from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / ".agents" / "skills" / "FFDF财报数据完善" / "SKILL.md"
AGENT = (
    ROOT
    / ".agents"
    / "skills"
    / "FFDF财报数据完善"
    / "agents"
    / "openai.yaml"
)


def test_skill_files_exist() -> None:
    assert SKILL.is_file()
    assert AGENT.is_file()


def test_skill_frontmatter_and_parameter_contract() -> None:
    text = SKILL.read_text(encoding="utf-8")
    assert "name: FFDF财报数据完善" in text
    assert "$FFDF财报数据完善 <company> <year_range> <model> [重新完善]" in text
    assert "company" in text
    assert "year_range" in text
    assert "model" in text
    assert "YYYY-YYYY" in text


def test_model_is_luna_5_6_max_fail_closed() -> None:
    text = SKILL.read_text(encoding="utf-8")
    assert "luna5.6-max" in text
    assert "MODEL_BLOCKED: LUNA_5_6_MAX_REQUIRED" in text
    assert "自动 fallback" in text
    assert "Luna 5.6 Max 以外模型" in text


def test_research_rules_are_bound_without_fourth_argument() -> None:
    text = SKILL.read_text(encoding="utf-8")
    assert r"D:\Codex\公司概述\00_Prompt\公司分析的约束.md" in text
    assert r"D:\Codex\公司概述\00_Prompt\问题清单.md" in text
    assert "Research Data Coverage 不增加第四个参数" in text


def test_preflight_and_review_flow_is_locked() -> None:
    text = SKILL.read_text(encoding="utf-8")
    required = (
        "Filing Coverage Scan",
        "Document Quality Scan",
        "Research Data Coverage Scan",
        "Research Repair Queue",
        "ffdf_get_review_state",
        "ffdf_get_review_context",
        "ffdf_render_table",
        "ffdf_submit_review_resolution",
        "RAW_EXTRACTION_DEFECT",
        "P6_MISSING_FACT_CANDIDATE",
        "period_monitoring_complete",
        "research_ready",
        "database_fully_reviewed",
        "RESEARCH PREFLIGHT: PASS",
        "RESEARCH PREFLIGHT: FAIL",
    )
    for marker in required:
        assert marker in text


def test_p9_boundaries_are_locked() -> None:
    text = SKILL.read_text(encoding="utf-8")
    assert "SET_VALUE" in text
    assert "PATCH_FACT" in text
    assert "VisualRef" in text
    assert "P9 v1 Evidence" in text
    assert "RESEARCH_FALLBACK" in text
    assert "QUALITY_REVIEW" in text


def test_agent_ui_is_explicit_invocation() -> None:
    text = AGENT.read_text(encoding="utf-8")
    assert 'display_name: "FFDF财报数据完善"' in text
    assert "$FFDF财报数据完善" in text
    assert "luna5.6-max" in text
    assert "allow_implicit_invocation: false" in text


def test_complete_documents_are_skipped_by_default() -> None:
    text = SKILL.read_text(encoding="utf-8")
    assert "SKIPPED_ALREADY_COMPLETE" in text
    assert "COMPLETE_BASE" in text
    assert "COMPLETE_REVIEWED" in text
    assert "不再进入重复完善流程" in text
    assert "仍然参与 Research Data Coverage" in text


def test_explicit_reimprove_bypasses_skip_safely() -> None:
    text = SKILL.read_text(encoding="utf-8")
    assert "$FFDF财报数据完善 605117 2021-2026 luna5.6-max 重新完善" in text
    assert "REIMPROVE_NO_ACTION_REQUIRED" in text
    assert "把 COMPLETE_BASE 强行改造成 COMPLETE_REVIEWED" in text
    assert "创建虚假的 Review Task" in text


def test_noncomplete_states_are_never_skipped() -> None:
    text = SKILL.read_text(encoding="utf-8")
    for marker in (
        "NEEDS_REVIEW",
        "NEEDS_MATERIALIZATION",
        "NEEDS_UPSTREAM_FIX",
        "BLOCKED",
        "INVALID_REVIEW_STATE",
    ):
        assert marker in text
    assert "不属于“已经完善”" in text


def test_output_tracks_skip_and_reimprove() -> None:
    text = SKILL.read_text(encoding="utf-8")
    assert "reimprove_requested" in text
    assert "skipped_already_complete_count" in text
    assert "SKIPPED_ALREADY_COMPLETE documents" in text
