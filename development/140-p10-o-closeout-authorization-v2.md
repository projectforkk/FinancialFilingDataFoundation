# 140 — P10-O Closeout / Main Integration Authorization v2

Status: **AUTHORIZED — P10-O CLOSEOUT INTEGRATION ONLY / FRESH V2 INTEGRATION**

Phase:
P10 — Codex Dynamic Research Integration

Gate:
P10-O — Closeout

Prerequisite Independent Acceptance result:

acceptance/40-p10-independent-acceptance-result.md = PASS

Acceptance result commit:

a05a3d20c6d2414750e069e44fd95aa81d80f74a

Accepted detached candidate:

183ca5dc89a606715a3e352bf92a235f7aa31fad

P10-N is CLOSED / PASS.

This authorization does not reopen P10 production/design/package and does not authorize P11, Research MCP production, or Semantic Resolver production.

## 1. Historical invalid closeout isolation

Historical authorization:

development/125-p10-closeout-authorization.md

Historical integration branch/worktree:

- branch: integration/p10-closeout
- merge commit: b560f49a78316fa59a4183de326d2dee0a80ebb6

These are INELIGIBLE because they preceded a real P10-N PASS.

Do not:

- reuse that branch/worktree;
- reset or rewrite it;
- delete it;
- fast-forward main from it.

Retain it as historical invalid evidence only.

## 2. Fresh integration source guard

Before creating the fresh integration branch:

1. fetch origin;
2. require active P10 branch clean;
3. require local P10 branch == origin/design/p10-dynamic-research-integration;
4. record exact P10 source HEAD after this authorization commit is pushed;
5. require origin/main exactly:
   e9b30626f2b88ac5527d42bd76d0b682efbeef0e
6. STOP on any main drift.

No reset, rebase, force push, destructive clean, or history rewrite.

## 3. Fresh v2 integration branch/worktree

Create only after this authorization is committed/pushed:

Branch:

integration/p10-closeout-v2

Worktree:

D:\Codex\FinancialFilingDataFoundation\worktrees\integration\p10-closeout-v2

Start exactly from recorded origin/main.

Merge the exact recorded P10 source HEAD with a normal non-history-rewriting merge.

A semantic merge conflict is a STOP condition; no manual conflict resolution is pre-authorized.

## 4. Post-merge integration gate

Bind every Python/test command to:

PYTHONPATH=D:\Codex\FinancialFilingDataFoundation\worktrees\integration\p10-closeout-v2\src

Run at minimum:

- P10 research unit suite;
- full P0-P10 unit suite;
- compile/import;
- git diff --check;
- P8 exact 11-tool contract;
- P8 runtime-lock SHA;
- P9 public policy/schema contract;
- P8/P9 accepted source/test zero unintended diff;
- dependency/runtime diff audit;
- forbidden P10 production surface scan;
- Research MCP / Semantic Resolver / P11 production absence;
- P10-G exact Git-blob identity;
- P10-N acceptance/40 presence and accepted-candidate identity;
- 47-file immutable-base manifest validation against current project files;
- integration worktree clean before closeout evidence.

Expected minimum regression:

- research >= 136 passed;
- full unit >= 444 passed.

Any failure blocks main integration.

## 5. Closeout evidence commit

Only after the integration gate PASS:

- create a new closeout evidence document;
- update PROJECT_STATUS to P10 DONE / ACCEPTED;
- update design/00-design-management-index.md;
- update development roadmap/master status references required by existing governance;
- record exact:
  - origin/main baseline;
  - merged P10 source HEAD;
  - integration merge commit;
  - acceptance result commit;
  - accepted detached candidate;
  - post-merge test counts;
  - P8/P9/runtime/security results;
  - immutable-base result.

The closeout evidence/status commit must be documentation/governance only.

Run git diff --check after the closeout evidence commit.

## 6. Main integration

Only after the fresh v2 integration branch including closeout evidence passes all checks:

1. push integration/p10-closeout-v2;
2. verify origin/main still equals the recorded P9 baseline;
3. verify main worktree clean;
4. fast-forward main only to the final v2 closeout commit;
5. push main;
6. verify local main == origin/main;
7. run final main:
   - P10 research unit suite;
   - full P0-P10 unit suite;
   - P8/P9/runtime/security boundary checks.

If final main verification fails:

STOP and do not declare P10 DONE.

## 7. Exit condition

P10 DONE requires all of:

- P10-N actual Independent Acceptance = PASS;
- fresh v2 closeout integration gate = PASS;
- main fast-forward/push = PASS;
- final main verification = PASS;
- no accepted P0-P9 regression;
- Research MCP production absent;
- Semantic Resolver production absent;
- P11 production absent/unauthorized.

P10 closeout does not automatically authorize P11 or any future optional production layer.
