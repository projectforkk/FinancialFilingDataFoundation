# 102 — P10-G Authorization — Thin Integration Instruction

Status: **AUTHORIZED — P10-G ONLY**

Phase:
`P10 — Codex Dynamic Research Integration`

Gate:
`P10-G — Thin Integration Instruction`

Prerequisite:
`development/101-p10-f-detached-code-review-result.md = PASS`

P10-F review result commit:
`5b54748`

Current authoritative design:

- `design/24-p10-codex-dynamic-research-integration-design.md` Section 29;
- `design/25-p10-implementation-plan.md` P10-G;
- `acceptance/38-p10-acceptance-instruction.md`.

Pre-implementation contract review found no new ambiguity requiring a design amendment.

## 1. Allowed scope

Only this tracked artifact may be added:

`integration/p10/FFDF_RESEARCH_INTEGRATION.md`

No `src/` or `tests/` changes are authorized by P10-G.

No runtime/dependency change is authorized.

## 2. Required instruction content

The instruction may describe only stable FFDF/P10 integration behavior:

- read the current frozen runtime research specification completely before research;
- derive information needs dynamically from that specification;
- P8 read-only raw/evidence/table/page/validation capabilities;
- P9 durable reviewed-decision boundary;
- P10 spec/context/provenance/CLI support;
- query priority and `REVIEW_REQUIRED != DATA_UNUSABLE`;
- durable vs run-local vs unresolved use;
- no raw numeric correction through P9;
- derived-use readiness/provenance boundary;
- capability gaps and explicit BLOCKED/UNAVAILABLE behavior;
- missing filing = data preparation required, not silent substitution;
- external runtime sources separated from FFDF provenance;
- no guessing / no silent fallback;
- no hidden chain-of-thought artifact requirement;
- exact-candidate source binding and project-root boundary at execution time.

## 3. Forbidden instruction content

The instruction must not copy or freeze:

- any user's fixed research question list;
- any question-number to tool mapping;
- any fixed report chapter structure;
- any fixed company/ticker;
- any fixed fiscal-year range;
- any fixed valuation method;
- any fixed investment recommendation rule;
- any company-specific supplement;
- any current task prompt;
- any credentials/secrets;
- hidden reasoning / chain-of-thought.

It must not claim availability for:

- PDF visual evidence;
- Semantic Resolver;
- canonical metric layer;
- P11 SEC provider.

Those remain unavailable in P10 v1.

## 4. Boundary

The instruction must make clear:

- P10 does not replace P8 MCP;
- P10 does not proxy P9 mutation;
- Codex remains the reasoning host;
- P10 production does not call Codex/OpenAI/remote AI;
- P8/P9 business calls remain through their accepted interfaces;
- external sources are not P8/P9 evidence;
- P10-E FFDF ledger v1 excludes external-source entries.

## 5. Evidence

After authoring, create:

`development/103-p10-g-integration-instruction-evidence.md`

Evidence must include:

- exact artifact path;
- SHA256;
- scope review;
- required-topic coverage;
- forbidden-content review;
- static search results;
- no `src/tests` diff;
- no dependency/runtime diff;
- UTF-8/no-BOM;
- `git diff --check`;
- clean candidate state.

## 6. Stop

After evidence commit/push:

STOP P10-G.

A separate review must close P10-G before P10-H.

P10-H and later remain closed.

Research MCP production, Semantic Resolver production, and P11 production remain closed.
