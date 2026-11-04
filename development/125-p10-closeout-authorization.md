# 125 — P10 Closeout / Main Integration Authorization

Status: **AUTHORIZED — P10 CLOSEOUT INTEGRATION ONLY**

Phase:
P10 — Codex Dynamic Research Integration

Prerequisite:

acceptance/40-p10-independent-acceptance-result.md = PASS

Accepted Independent Acceptance candidate:

56cbe185e97e6e07dd354e03b98942d87f8e5787

P10-N is closed.

This authorization does not reopen P10 production/design and does not authorize P11, Research MCP production, or Semantic Resolver production.

## 1. Integration source

Before any merge:

1. fetch origin;
2. require active P10 branch clean;
3. require local P10 branch == origin/design/p10-dynamic-research-integration;
4. record the exact remote P10 HEAD;
5. require origin/main still equals the accepted P9 main baseline or explicitly STOP on drift.

No reset, rebase, force push, history rewrite, or destructive clean.

## 2. Integration worktree

Create fresh project-local integration worktree:

D:\Codex\FinancialFilingDataFoundation\worktrees\integration\p10-closeout

on branch:

integration/p10-closeout

starting exactly from current origin/main.

Merge the exact recorded P10 branch HEAD with a normal non-history-rewriting merge.

No manual conflict resolution is authorized if a semantic conflict exists; STOP and inspect first.

## 3. Post-merge gate in integration worktree

Bind:

PYTHONPATH=<integration-worktree>\src

Run at minimum:

- P10 research unit suite;
- full P0-P10 unit suite;
- compile/import;
- git diff --check;
- P8 exact 11-tool contract;
- P8 runtime-lock SHA;
- P9 public contract;
- P8/P9 accepted source/test scope review;
- dependency/runtime diff;
- forbidden production surface scan;
- future production absence;
- exact integration instruction Git-blob SHA;
- acceptance freeze/result presence and identity;
- 47-file immutable-base manifest verification;
- integration worktree clean.

Expected current minimum counts:

- research: 136 passed;
- full unit: 444 passed.

Any failure blocks main integration.

## 4. Closeout commit

After the integration tree passes:

- add a closeout evidence document on the integration branch;
- update project status/design index to P10 DONE / ACCEPTED;
- record exact:
  - origin/main baseline;
  - merged P10 source HEAD;
  - integration merge commit;
  - post-merge test counts;
  - P10-N result;
  - accepted candidate;
  - scope/security results.

The closeout evidence/status commit must change documentation/governance only.

Rerun git diff --check after the closeout evidence commit.

## 5. Main integration

Only after integration PASS:

1. push integration/p10-closeout;
2. verify main worktree clean and origin/main unchanged from recorded baseline;
3. fast-forward main to the final integration closeout commit;
4. push main;
5. verify local main == origin/main;
6. run final main post-integration P10 research suite and full unit suite with exact main PYTHONPATH;
7. verify P8/P9/runtime/security boundaries once more.

If the final main verification fails:

STOP and do not declare P10 DONE.

## 6. Exit condition

P10 DONE requires:

- P10-N Independent Acceptance = PASS;
- closeout integration gate = PASS;
- main push = PASS;
- final main verification = PASS;
- no accepted P0-P9 regression;
- P11 / Research MCP production / Semantic Resolver production remain absent/unauthorized.

Final closeout must not automatically authorize P11.
