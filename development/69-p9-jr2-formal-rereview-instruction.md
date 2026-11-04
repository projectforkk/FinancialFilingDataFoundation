# 69 — P9-JR2 Formal Detached Re-Review Instruction

Status: **ACTIVE — REVIEW ONLY**

Exact review candidate:
`e010d61c2227a3496b51cb8cc5f54df7e550cb6d`

Production correction:
`f02504a69d7bc454b674a4ad347aaeecad38f6be`

Design baseline:
`e7bb65cfdb046c83a467dc865b853658726a767a`

Prior FAIL:
`development/66-p9-jr-formal-rereview-result.md`

Evidence:
`development/68-p9-jr2-corrective-evidence.md`

## Boundary

Create a fresh detached worktree under
`D:\Codex\FinancialFilingDataFoundation\worktrees\review`.

All review/temp work remains inside
`D:\Codex\FinancialFilingDataFoundation`.

Do not edit production/tests/design in detached review.
Do not enter P9-K/L/M or later phases unless verdict is PASS.

## Mandatory re-review

Independently verify:

1. all prior P9-J original URL/SQL and parser-failure probes；
2. all `development/66` new probes:
   - `/tmp`
   - `path=C:\\secret.txt`
   - natural-language SELECT
   - root/subcommand help；
3. broader Section 49 examples including UNC/traversal, shell, SQL DML/DDL,
   Python and credentials；
4. benign finance/natural-language examples；
5. exact raw subprocess JSON behavior；
6. focused/full/compile/import/diff/scope；
7. all 55 acceptance items；
8. detached worktree clean after verification。

Required test roots must be short ignored paths under project `worktrees/t/`.

## Verdict

PASS / FAIL / BLOCKED.

PASS authorizes the design owner to enter P9-K only after the result artifact is
committed/pushed.

Create result:
`development/70-p9-jr2-formal-rereview-result.md`.

Review gate may only commit/push that result document.
