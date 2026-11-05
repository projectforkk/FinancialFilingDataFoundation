# 112 — FFDF Research Preflight Codex Skill Acceptance

## Candidate

Implementation commit:

`fdb4cfb feat: add FFDF research preflight Codex skill`

Design commit:

`1a074e6 design: define FFDF research preflight skill`

## Delivered Skill

Path:

`.agents/skills/FFDF财报数据完善/`

Files:

- `SKILL.md`
- `agents/openai.yaml`

Static contract test:

- `tests/unit/skills/test_ffdf_research_preflight_skill.py`

## Parameter Contract

Exactly three logical parameters:

1. `company`
2. `year_range` in `YYYY-YYYY`
3. `model`

Invocation:

`$FFDF财报数据完善 <company> <year_range> <model>`

Current only allowed canonical model:

`luna5.6-max`

Other models and automatic fallback are explicitly forbidden.

## Research-rule binding

The Skill keeps only three explicit parameters and reloads the current research rules from:

- `D:\Codex\公司概述\00_Prompt\公司分析的约束.md`
- `D:\Codex\公司概述\00_Prompt\问题清单.md`

If either rule file is unavailable, Research Data Coverage is not allowed to claim completion and `research_ready` cannot be declared true.

## Workflow Contract

Verified Skill includes:

- Filing Coverage Scan
- Document Quality Scan
- Research Data Coverage Scan
- minimal Research Repair Queue
- structured context first
- Luna 5.6 Max only for actual semantic/visual ambiguity
- PDF Visual only when structured evidence is insufficient
- P9 v1 legal write-through only in QUALITY_REVIEW
- RAW_EXTRACTION_DEFECT -> upstream fix
- P6_MISSING_FACT_CANDIDATE -> upstream fix
- re-run Preflight after repair
- `period_monitoring_complete`
- `research_ready`
- `database_fully_reviewed`
- final `RESEARCH PREFLIGHT: PASS/FAIL`

## Focused test

`tests/unit/skills/test_ffdf_research_preflight_skill.py`

Result:

**7 PASS / 0 FAIL**

Covers:

- Skill files exist
- frontmatter/name
- three-parameter invocation
- year-range contract
- Luna 5.6 Max fail-closed rule
- two research rule files
- Preflight/Review/Visual/P9 markers
- P9 prohibition markers
- explicit invocation UI configuration

## Full FFDF unit regression

First exploratory full run used:

`--basetemp .t\skill-acceptance`

Result:

- 499 PASS
- 15 FAIL

All failures were existing P9 snapshot tests failing with Windows `FileNotFoundError` because the longer basetemp made nested snapshot paths exceed the practical Windows path limit.

No Skill test failed and no production code was changed in response.

Authoritative rerun used the established short-path acceptance pattern:

`--basetemp .t\s`

Result:

**514 PASS / 0 FAIL**

Runtime approximately 52 seconds.

## Scope / safety

The Skill does not:

- add remote AI API calls to FFDF MCP;
- change P8/P9 production contracts;
- change Raw/P3/P5/P6/P7 artifacts;
- add network access;
- add arbitrary filesystem MCP tools;
- add SET_VALUE/PATCH_FACT;
- create canonical metrics;
- change the accepted Research Review implementation.

The Skill is host-Codex orchestration only.

## Git hygiene

Existing untracked directories remained untouched and uncommitted:

- `00document/`
- `01prompt/`

## Verdict

**ACCEPTANCE: PASS**

The FFDF Research Preflight Codex Skill is ready for merge to main and Git-managed use.
