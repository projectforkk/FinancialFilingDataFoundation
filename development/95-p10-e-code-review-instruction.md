# 95 — P10-E Detached Code Review Instruction

Status: **AUTHORIZED — REVIEW ONLY**

Phase:
`P10 — Codex Dynamic Research Integration`

Gate under review:
`P10-E — Evidence Ledger / Provenance Validator`

Design baseline:
`d6b34d84d1eeae6b0f2009895a14c5956217a18f`

Candidate:
`802a395247e490a83acaef744c1641188fbf704e`

Development evidence:
`development/94-p10-e-provenance-evidence.md`

Evidence commit:
`164f1aa8b97cdcdf5a8e43bffe4f604175d480ef`

## Review scope

Review only P10-E.

Verify:

- exact ledger/result schemas;
- four use-class profiles;
- spec-first/context/catalog identity;
- P8 refs through accepted `McpQueryService`;
- P9 exact snapshot/resolution validation through accepted loader;
- historical snapshot behavior;
- derived DAG/order/operand rules;
- deterministic error mapping;
- no external-source provenance in FFDF ledger v1;
- no P8/P9 semantic duplication;
- no P9 mutation API in production;
- no network/AI/external MCP SDK/subprocess/shell/SQL;
- no P10-F or later production.

## Isolation

Create detached worktree under:

`D:\\Codex\\FinancialFilingDataFoundation\\worktrees\\review\\p10-e-<authorization-sha>`

Every Python command must bind:

`PYTHONPATH=<detached-worktree>\\src`

Use only project-local **single-character** pytest basetemps because accepted P9 snapshot tests cross the Windows deep-path boundary with longer basetemps.

Do not delete prior basetemp evidence. Move a pre-existing single-character directory whole into project-local ignored workspace if a fresh slot is required.

## Required independent execution

- focused provenance suite;
- full `tests/unit`;
- compile/import;
- direct provenance probes;
- P8/P9 scope diff;
- dependency/runtime diff;
- forbidden-surface scan;
- detached status clean before/after.

## Verdict

`PASS / FAIL / BLOCKED`

If FAIL:

`STOP → facts/root cause → Design-First corrective loop`

Do not fix production in the review worktree.

A PASS only closes P10-E review. P10-F still requires separate authorization.
