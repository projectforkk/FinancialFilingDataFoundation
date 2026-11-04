# 112 — P10-J Live P8/P9 Research Run Authorization

Status: **AUTHORIZED — P10-J LIVE RUN ONLY / NO PRODUCTION CHANGES**

Phase:
`P10 — Codex Dynamic Research Integration`

Gate:
`P10-J — Live P8/P9 Research Run`

Current design baseline:
`d8961731044d6c33c8a9e2cb96820819c3daa275`

P10-I evidence:
`development/111-p10-i-dynamic-spec-evidence.md = PASS`

P10-I evidence commit:
`4f6215f`

Only P10-J live research validation is authorized.

## Primary live fixture

Use accepted CN live filing:

- market: `CN`
- ticker: `600519`
- fiscal year: `2024`
- filing type: `ANNUAL`
- document SHA:
  `5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30`

Accepted live catalog:

`workspace/mcp/p8-live-catalog.json`

Do not download or rebuild the filing.

## Isolated P9 boundary

Existing P9 live state may be copied read-only into:

`workspace/research-runs/p10-j/review`

The source P9 live review root must remain byte-identical.

Do not write or mutate:

`workspace/p9-live-review`

No P9 mutation is required for this development run.

If mutation becomes necessary, STOP and authorize only an isolated P10-J review root.

## Required runtime specification

Create/freeze/read a project-local live runtime spec that requires a compact COMPLETE result for the durable-reviewed CN fact targeted by the existing active P9 resolution.

The output must include at least:

- document identity;
- base validation status;
- raw fact identity;
- raw metric name;
- raw value;
- raw period state;
- effective reviewed period;
- source table/page/evidence identity;
- P9 resolution ID;
- overlay-set hash;
- explicit `REVIEW_REQUIRED != DATA_UNUSABLE` behavior;
- explicit non-canonical-reuse status.

The run must not alter raw numeric value.

## Required live flow

1. freeze and verify runtime spec;
2. read frozen spec completely;
3. discover/list accepted P8 document;
4. query P8 validation;
5. dynamically query the targeted fact/table/evidence/page context;
6. validate relevant P9 durable snapshot/resolution;
7. produce the spec-required output;
8. create P10 evidence ledger;
9. validate ledger PASS;
10. record exact P8/P9 call summary;
11. hash accepted P8 base and source P9 state before/after;
12. final verdict = `COMPLETE`.

## Evidence classes

At minimum use:

- `P8_RAW_DIRECT` for raw fact/table/evidence provenance;
- `P9_DURABLE_RESOLVED` for the reviewed period resolution.

Do not claim P9 changes the raw numeric value.

Do not mark the document canonical reusable merely because the period resolution is valid.

## Scope

All P10-J runtime state must remain under:

`D:\\Codex\\FinancialFilingDataFoundation\\workspace\\research-runs\\p10-j`

No production/tests/design change is authorized.

## Evidence

Write:

`development/113-p10-j-live-research-evidence.md`

only after the COMPLETE run and immutability checks pass.

PASS closes P10-J and permits a separate P10-K authorization.

P10-K and later remain closed until separately authorized.
