# 116 — P10-K Negative Capability Gates Authorization

Status: **AUTHORIZED — P10-K NEGATIVE VALIDATION ONLY / NO PRODUCTION CHANGES**

Phase:
`P10 — Codex Dynamic Research Integration`

Gate:
`P10-K — Negative Capability Gates`

Current design baseline:
`668269e87774730ade03afb4b7564256671eb31f`

P10-J evidence:
`development/115-p10-j-live-research-evidence.md = PASS / COMPLETE`

P10-J evidence commit:
`d6f1e32`

Only P10-K negative validation/workspace evidence is authorized.

## Required cases

### K1 — Missing filing

Use the accepted live catalog with a frozen runtime spec requesting a filing absent from the catalog.

Required result:

`P10_DATA_PREPARATION_REQUIRED`

Must prove:

- no download;
- no substitute company;
- no substitute fiscal period;
- no unsupported statement that the filing was never disclosed.

### K2 — Visual-only requirement

Use a frozen runtime spec whose required claim genuinely depends on visual-only PDF evidence not exposed by P10 v1 structured capabilities.

Required result:

`P10_VISUAL_CAPABILITY_REQUIRED`

Must prove:

- no guess;
- no arbitrary PDF open through P10;
- no fake RUN_LOCAL_STRUCTURED_VERIFIED;
- no Research MCP implementation/use.

### K3 — Corrupt P9 state

Construct a fresh isolated P9 store under the P10-K workspace through accepted P9 APIs.

First prove valid P9 provenance.

Then tamper only the isolated negative fixture.

Required result:

- validator blocks with `P10_UPSTREAM_INVALID`;
- no silent raw fallback;
- accepted/source P8/P9 state unchanged.

### K4 — Mid-run spec mutation

Freeze a project-local runtime spec, then mutate one byte.

Required result:

`P10_RESEARCH_SPEC_CHANGED`

No silent refresh.

### K5 — Unresolved semantic requirement

Use a frozen runtime spec that requires a semantic field which is absent in raw P8 and has no supported/durable P9 resolution for the case.

Preferred live fixture:
CN 600519 target fact
`9b3e2e441e6730c0f3c979816dd764dcb4bf70e6cde16caae9e3897733b9a015`

Its raw unit is null and the live review queue has no supported unit-resolution task.

Required result:

`P10_REVIEW_UNRESOLVED`

No guessed unit and no fake durable/run-local verified value.

## Workspace

All runtime/test state must remain under:

`D:\\Codex\\FinancialFilingDataFoundation\\workspace\\research-runs\\p10-k`

No tracked production/tests/design mutation is authorized.

## Evidence

On PASS write:

`development/117-p10-k-negative-gates-evidence.md`

PASS closes P10-K and permits a separate P10-L authorization.

P10-L and later remain closed until separately authorized.
