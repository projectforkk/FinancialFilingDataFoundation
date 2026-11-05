# 115 — FFDF财报数据完善 Skill v2 Skip-Complete Optimization Acceptance

## Candidate

Design commit:

`13b5da2 design: add skip-complete optimization to data improvement skill`

Implementation commit:

`9681fff feat: skip already-complete filings in data improvement skill`

## User-confirmed behavior

Final rule:

> 已经完善的财报不需要重新完善，除非明确指定“重新完善”。

## Invocation

Three required parameters remain:

`$FFDF财报数据完善 <company> <year_range> <model>`

Optional control word:

`重新完善`

Example:

`$FFDF财报数据完善 605117 2021-2026 luna5.6-max 重新完善`

The control word is not a fourth required parameter.

## Default skip behavior

For every observed filing in the research period:

1. call `ffdf_get_review_state`;
2. if state is `COMPLETE_BASE` or `COMPLETE_REVIEWED` and no explicit `重新完善` directive is present:
   - normalize to `SKIPPED_ALREADY_COMPLETE`;
   - keep the document available to Research Data Coverage;
   - do not enter duplicate Review Context / Luna / PDF Visual / P9 / materialization work.

Both COMPLETE_BASE and COMPLETE_REVIEWED are treated as already complete for improvement purposes.

## Explicit reimprove behavior

When `重新完善` is present:

- bypass the default complete-document skip;
- rerun Research Preflight / Research Data Coverage;
- reread current Review State;
- only currently existing, research-relevant unresolved Review Tasks may enter review;
- only use Luna 5.6 Max when model reasoning is genuinely required;
- only use PDF Visual when structured evidence remains insufficient;
- only write P9 when current P9 v1 legality conditions are satisfied.

Explicit reimprove does not authorize:

- Raw Fact mutation;
- creating missing RawFacts;
- fabricating Review Tasks;
- forcing COMPLETE_BASE into COMPLETE_REVIEWED;
- deleting existing P9 resolutions;
- clearing review overlays;
- repeated durable writes with no changed conclusion.

If no new legal action exists:

`REIMPROVE_NO_ACTION_REQUIRED`

and the existing complete state remains unchanged.

## States never skipped

The following remain routed through the existing Repair Queue:

- NEEDS_REVIEW
- NEEDS_MATERIALIZATION
- NEEDS_UPSTREAM_FIX
- BLOCKED
- INVALID_REVIEW_STATE

## Output additions

The Skill now reports:

- `reimprove_requested`
- `skipped_already_complete_count`
- per-document `SKIPPED_ALREADY_COMPLETE`
- `REIMPROVE_NO_ACTION_REQUIRED` when applicable

Skipped complete filings still count toward period monitoring and can support `research_ready=true`.

## Focused test

`tests/unit/skills/test_ffdf_research_preflight_skill.py`

Result:

**11 PASS / 0 FAIL**

Coverage includes:

- three required parameters plus optional reimprove directive;
- COMPLETE_BASE / COMPLETE_REVIEWED default skip;
- Research Data Coverage reuse;
- explicit reimprove bypass;
- no fabricated Review Task / forced P9;
- non-complete states never skipped;
- output counters and markers.

## Full FFDF unit regression

Result:

**530 PASS / 0 FAIL**

## Scope / safety

No production FFDF parser, Registry, P8, P9 or MCP implementation was changed.

Only:

- Skill orchestration;
- Agent default prompt;
- Skill README;
- static Skill contract tests;
- design / acceptance evidence.

Existing untracked directories remained untouched:

- `00document/`
- `01prompt/`

## Verdict

**OPTIMIZATION V2 ACCEPTANCE: PASS**
