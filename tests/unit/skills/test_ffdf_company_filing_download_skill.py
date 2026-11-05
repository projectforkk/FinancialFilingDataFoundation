from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / ".agents" / "skills" / "FFDF公司财报下载" / "SKILL.md"
AGENT = ROOT / ".agents" / "skills" / "FFDF公司财报下载" / "agents" / "openai.yaml"


def test_skill_files_exist() -> None:
    assert SKILL.is_file()
    assert AGENT.is_file()


def test_name_and_exact_two_parameter_contract() -> None:
    text = SKILL.read_text(encoding="utf-8")
    assert "name: FFDF公司财报下载" in text
    assert "$FFDF公司财报下载 <company_code> <year_or_range>" in text
    assert "只接受两个逻辑参数" in text
    assert "不得增加 market、period、model 等第三个必填参数" in text


def test_year_single_and_range_contract() -> None:
    text = SKILL.read_text(encoding="utf-8")
    assert "$FFDF公司财报下载 605117 2021" in text
    assert "$FFDF公司财报下载 605117 2021-2026" in text
    assert "[2021, 2022, 2023, 2024, 2025, 2026]" in text
    assert "YEAR_OR_RANGE_INVALID" in text


def test_market_inference_is_deterministic() -> None:
    text = SKILL.read_text(encoding="utf-8")
    assert "恰好 6 位数字" in text
    assert "1 到 5 位数字" in text
    assert "00700" in text
    assert "COMPANY_CODE_INVALID" in text


def test_ingest_pipeline_and_periods_are_locked() -> None:
    text = SKILL.read_text(encoding="utf-8")
    for marker in (
        "Q1 -> H1 -> Q3 -> FY",
        "ffdf ingest --market <market> --ticker <ticker> --year <year> --period <period>",
        "Raw Store",
        "P3",
        "P4",
        "P5",
        "P6 Raw Fact + Evidence",
        "P7 Validation",
        "Parsed Registry",
        "p8-live-catalog.json",
    ):
        assert marker in text


def test_reuse_and_nonblocking_publication_rules_are_locked() -> None:
    text = SKILL.read_text(encoding="utf-8")
    assert "REUSED_LOCAL" in text
    assert "INCREMENTAL_FIRST" in text
    assert "blocking_issue_count == 0" in text
    assert "INGEST_BLOCKED" in text
    assert "P7 REVIEW_REQUIRED" in text


def test_not_found_and_future_window_are_not_fabricated() -> None:
    text = SKILL.read_text(encoding="utf-8")
    assert "NOT_FOUND" in text
    assert "FUTURE_WINDOW_NOT_STARTED" in text
    assert "default publication search window has not started yet" in text
    assert "NOT_FOUND 时伪造财报" in text


def test_no_ai_and_no_destructive_bypass() -> None:
    text = SKILL.read_text(encoding="utf-8")
    assert "调用 AI 模型" in text
    assert "外部 OpenAI/Anthropic/Gemini API" in text
    assert "git reset --hard" in text
    assert "修改官方 Raw PDF" in text


def test_agent_ui_is_explicit_invocation() -> None:
    text = AGENT.read_text(encoding="utf-8")
    assert 'display_name: "FFDF公司财报下载"' in text
    assert "$FFDF公司财报下载" in text
    assert "605117 2021-2026" in text
    assert "allow_implicit_invocation: false" in text
