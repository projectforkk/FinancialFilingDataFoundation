# 67 — P9-JR2 Corrective Development Instruction

Status: **AUTHORIZED — P9-JR2 ONLY**

Trigger:
`development/66-p9-jr-formal-rereview-result.md` = **FAIL / CHANGES REQUIRED**

Authoritative contracts:
- `design/22-p9-review-overlay-design.md` Section 41 / Section 49 / P9-ISSUE-008 / P9-ISSUE-009
- `design/23-p9-implementation-plan.md` P9-JR2
- `acceptance/32-p9-acceptance-instruction.md` items 53 and 55

Operational root:
all work remains inside `D:\\Codex\\FinancialFilingDataFoundation`.

## 1. Security classifier correction

Required implementation behavior:

- reject `/tmp`, `/secret.txt`, `/etc/passwd`；
- reject `C:\\secret.txt` and `path=C:\\secret.txt`；
- reject explicit traversal；
- continue rejecting URL/shell/Python/credential classes；
- continue rejecting `SELECT * FROM secrets`；
- allow `2024/2025`；
- allow `P5/P6 evidence`；
- allow `SQL review completed`；
- allow `Select revenue from the annual report evidence.`；
- SQL SELECT detection must use SQL-object termination/clause grammar rather than a raw keyword span；
- UPDATE SQL detection requires assignment-like SET syntax。

Keep the stable forbidden-content reason/message unchanged.

## 2. CLI help correction

Disable argparse built-in text help at:
- root parser；
- every subcommand parser。

Root/subcommand `-h/--help` must be handled exactly like other parser-level invalid arguments:

- exit 2；
- stdout empty；
- stderr exactly one JSON；
- `P9_CLI_ARGUMENT_ERROR`；
- `invalid command line arguments`。

Do not add an alternate text help surface.

## 3. Tests

Add direct regression tests for all new review probes.

Retain all prior F1/F2 tests.

Run:
- focused P9；
- full unit；
- compile/import；
- diff/scope；
- raw subprocess probe including root/subcommand help。

Use only short ignored paths under project `worktrees/t/` to avoid Windows path-length failures.

## 4. Review

After implementation/evidence commit:
- freeze exact corrective candidate；
- create fresh detached review worktree under project root；
- independently re-run security edge probes and CLI raw subprocess probes；
- map all 55 acceptance items；
- PASS required before P9-K。

Any new defect:
`STOP → root cause → design amendment → commit/push → then code`.

No P9-K/L/M, main merge, P10/P11, Research MCP production, or Semantic Resolver production before PASS.
