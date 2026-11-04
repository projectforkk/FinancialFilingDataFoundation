# 127 — Corrected P10-N Independent Acceptance Reauthorization

Status: **AUTHORIZED — P10-N INDEPENDENT ACCEPTANCE ONLY / EXACT CORRECTED RE-FREEZE CANDIDATE**

Phase:
P10 — Codex Dynamic Research Integration

Gate:
P10-N — Independent Acceptance

Correct eligible P10-M re-freeze candidate:

4d1ab46f11d1d7b88934309ce32319e2200f0d8f

Historical invalid candidate reference:

56cbe185e97e6e07dd354e03b98942d87f8e5787

Historical invalid freeze attempt:

42e39c971a360ca4e0ee09761221cc8da7ddbaa9

Historical closeout stop:

development/126-p10-closeout-stop.md

Corrected re-freeze evidence:

development/123-p10-m-refreeze-evidence.md = PASS

Only the exact commit
4d1ab46f11d1d7b88934309ce32319e2200f0d8f
is eligible for this P10-N run.

## 1. Detached candidate

Create:

D:\Codex\FinancialFilingDataFoundation\worktrees\acceptance\p10-n-4d1ab46

with detached HEAD exactly:

4d1ab46f11d1d7b88934309ce32319e2200f0d8f

Do not use this authorization commit as the acceptance candidate.

Do not use source from main/active/review/integration/another worktree.

## 2. Exact source binding

Every P10 Python/test command:

PYTHONPATH=D:\Codex\FinancialFilingDataFoundation\worktrees\acceptance\p10-n-4d1ab46\src

PYTHONDONTWRITEBYTECODE=1

PYTHONIOENCODING=utf-8

No FFDF editable/install.

## 3. Frozen acceptance instruction

Read and obey from the detached candidate:

- acceptance/38-p10-acceptance-instruction.md
- acceptance/39-p10-final-acceptance-freeze.md
- acceptance/p10_independent_acceptance_harness.py
- acceptance/p10-base-immutability-manifest.json
- acceptance/p10-fixtures/**

The acceptance package is frozen.

No fix/change may be made in the detached acceptance worktree.

## 4. Fresh mutable acceptance root

Use only:

D:\Codex\FinancialFilingDataFoundation\workspace\p10-n\4d1ab46

The path must be absent before precheck.

Do not reuse P10-I/J/K development workspaces as acceptance outputs.

## 5. Required sequence

1. verify detached HEAD exactly;
2. verify detached worktree clean;
3. preserve existing basetemp a/b whole under project-local scratch if present;
4. run frozen harness precheck;
5. run fresh P10 research unit suite;
6. run fresh full P0-P10 unit suite;
7. read copied frozen Spec A completely;
8. dynamically execute Spec A and validate ledger;
9. read copied frozen Spec B completely;
10. dynamically execute Spec B and validate ledger;
11. verify A/B bundle hashes and selected tool sets differ;
12. read copied frozen live spec completely;
13. perform fresh live COMPLETE run;
14. build isolated P9 review state at final acceptance path through accepted P9 APIs;
15. validate raw/effective distinction and non-canonical reuse;
16. read each applicable negative spec completely;
17. execute K1-K5 fresh negative gates;
18. write frozen result summaries required by postcheck;
19. run harness postcheck;
20. recheck immutable 47-file base;
21. recheck detached status clean;
22. issue PASS / FAIL / BLOCKED.

## 6. Test basetemps

Use:

D:\Codex\FinancialFilingDataFoundation\worktrees\t\a

D:\Codex\FinancialFilingDataFoundation\worktrees\t\b

If present, move each whole to:

workspace/scratch/p10-n-preserved-<slot>-before-4d1ab46

Do not delete historical evidence.

## 7. Result artifact

On completion write on the active governance branch:

acceptance/40-p10-independent-acceptance-result.md

The result must record:

- exact detached candidate SHA;
- exact detached worktree path;
- precheck report + SHA;
- research/full test counts;
- dynamic Spec A/B raw SHA, bundle SHA, context IDs, selected tool sets;
- dynamic ledgers/validations;
- live generated isolated P9 resolution/overlay IDs;
- live COMPLETE output and ledger validation;
- K1-K5 reason codes;
- before/after immutable-base PASS;
- postcheck report + SHA;
- detached clean status;
- final verdict.

If any acceptance finding requires candidate/package/design change:

STOP -> FAIL/BLOCKED.

Do not patch the detached acceptance candidate.

A candidate change invalidates 4d1ab46f... and requires a new Design-First/freeze loop.

## 8. Scope

P10-N does not authorize:

- P11 production;
- Research MCP production;
- Semantic Resolver production;
- new P8/P9 mutations outside the isolated acceptance work root;
- any P10 production/design change;
- closeout/main integration.

PASS may permit a later separate P10 closeout authorization.

P10 remains not-DONE until the actual Independent Acceptance result is committed.
