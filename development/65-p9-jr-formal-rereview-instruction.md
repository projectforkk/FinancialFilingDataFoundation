# 65 — P9-JR Formal Detached Re-Review Instruction

Status: **ACTIVE — P9-JR FORMAL RE-REVIEW ONLY**

Phase:
`P9 — Codex Review Overlay`

Target branch:
`task/p9-review-overlay`

Exact corrective review candidate SHA:

`65d29cb7d41ab46fb898c1f0bc557537ab48421c`

Corrective production commit:

`2d42c02c4e5dc7026b50c6928a57b1781ba0d831`

Design corrective baseline:

`d668c6e21cba8ae274ebbb786ccb70e55c9e04c2`

Project-root governance commit:

`c40e13579830b485e115ad1ce1a99e803f85fd49`

Corrective evidence:

`development/64-p9-jr-corrective-evidence.md`

Failed prior review:

`development/62-p9-j-formal-code-review-result.md`

## 1. Hard boundary

This is review-only.

Use a fresh detached worktree inside:

`D:\Codex\FinancialFilingDataFoundation\worktrees\review`

All temporary review/test paths must also stay inside:

`D:\Codex\FinancialFilingDataFoundation`

Do not modify production, tests, design, accepted artifacts, catalog, runtime/dependencies, or source PDFs.

Do not enter P9-K/L/M, main merge, P10, P11, Research MCP production, or Semantic Resolver production.

## 2. Authoritative contracts

Review against:

- `design/22-p9-review-overlay-design.md` sections 41 and 49；
- P9-ISSUE-006 / P9-ISSUE-007；
- `design/23-p9-implementation-plan.md` P9-JR；
- `acceptance/32-p9-acceptance-instruction.md` all 55 mandatory items；
- `development/63-p9-j-corrective-development-instruction.md`；
- `development/64-p9-jr-corrective-evidence.md`。

## 3. Mandatory F1 re-review

Independently verify:

- payload-wide recursive string-leaf validator；
- validator runs before hash/persist；
- validator runs during historical semantic validation；
- original P9-J URL-in-justification probe is rejected；
- original P9-J SQL-in-value probe is rejected；
- path / shell / Python / credential classes are rejected；
- reason/message are exact and do not echo offending content；
- benign `2024/2025`, `P5/P6 evidence`, and natural-language keyword text remain allowed；
- no execution, network, AI, or arbitrary path behavior is introduced by the validator。

## 4. Mandatory F2 re-review

Independently verify raw subprocess behavior for:

- no subcommand；
- unknown subcommand；
- missing required argument；
- `--input-json` + `--input-file` conflict。

Each must be:

- exit 2；
- stdout empty；
- stderr exactly one JSON object；
- `status=ERROR`；
- `reason_code=P9_CLI_ARGUMENT_ERROR`；
- `message=invalid command line arguments`；
- no argparse `usage:` / `error:` prose。

Also confirm success exit 0 and handled runtime failure exit 1 remain unchanged.

## 5. Verification

Use exact detached candidate and main runtime:

`D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe`

Use short project-local ignored basetemp paths because Windows deep snapshot paths approach MAX_PATH.

Required:

- compileall/import review package；
- focused P9 tests；
- full unit tests；
- `git diff --check`；
- accepted-P8 scope review；
- source/security scan；
- exact raw CLI subprocess probe；
- acceptance 55-item mapping, with special attention to items 53 and 55；
- detached worktree remains clean。

## 6. Verdict

Allowed:
- PASS
- FAIL
- BLOCKED

PASS requires both P9-J-F1 and P9-J-F2 closed, all mandatory evidence paths credible, and no new substantive finding.

If PASS:
state that P9-K may be authorized after the re-review result is committed/pushed.

If FAIL/BLOCKED:
record exact finding and STOP.

## 7. Result artifact

After completing detached review, return to active worktree for documentation only.

Create:

`development/66-p9-jr-formal-rereview-result.md`

Commit/push only that review result document.

No production/test/design fixes are authorized in the review gate.
