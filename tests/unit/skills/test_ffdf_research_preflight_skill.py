from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / ".agents" / "skills" / "ffdf-research-preflight" / "SKILL.md"
AGENT = (
    ROOT
    / ".agents"
    / "skills"
    / "ffdf-research-preflight"
    / "agents"
    / "openai.yaml"
)


def test_skill_files_exist() -> None:
    assert SKILL.is_file()
    assert AGENT.is_file()


def test_skill_frontmatter_and_parameter_contract() -> None:
    text = SKILL.read_text(encoding="utf-8")
    assert "name: ffdf-research-preflight" in text
    assert "$ffdf-research-preflight <company> <year_range> <model>" in text
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
    assert 'display_name: "FFDF研究前预检"' in text
    assert "$ffdf-research-preflight" in text
    assert "luna5.6-max" in text
    assert "allow_implicit_invocation: false" in text
