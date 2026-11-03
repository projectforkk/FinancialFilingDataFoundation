# 63 — P9-J Corrective Development Instruction

Status: **AUTHORIZED — P9-JR ONLY**

Phase:
`P9 — Codex Review Overlay`

Trigger:
`development/62-p9-j-formal-code-review-result.md` = **FAIL / CHANGES REQUIRED**

Authoritative amended contracts:
- `design/22-p9-review-overlay-design.md` sections 41, 49, P9-ISSUE-006, P9-ISSUE-007
- `design/23-p9-implementation-plan.md` P9-JR
- `acceptance/32-p9-acceptance-instruction.md` items 53 and 55

## 1. Scope

Operational root constraint:

- all FFDF project work, including development, tests, temporary test directories, detached review worktrees, and generated review evidence, must remain inside `D:\\Codex\\FinancialFilingDataFoundation`；
- do not use external temporary roots such as `D:\\Codex\\FFDF-t`；
- ignored project-local locations such as `runtimes/` and `worktrees/` may be used for ephemeral execution state。

Only remediate:
- P9-J-F1 payload security invariant；
- P9-J-F2 parser-level CLI JSON diagnostic invariant；
- direct/adversarial tests needed to prove those fixes。

Do not enter P9-K/L/M, main merge, P10, P11, Research MCP production, or Semantic Resolver production.

Do not modify accepted P0-P8 production/tests/artifacts or raw/source PDFs.

## 2. F1 implementation contract

Implement a deterministic recursive string-leaf validator for the normalized persisted resolution payload.

Mandatory:
- validate `ReviewResolution.to_dict(include_id=False)` after canonical target/evidence/before/after construction and before resolution ID hashing/persistence；
- validate existing persisted resolutions again during historical semantic validation；
- cover URL, file path, shell command, SQL, Python code, credentials；
- reject with exactly:
  - reason_code `P9_RESOLUTION_CONTENT_FORBIDDEN`
  - message `resolution payload contains forbidden content`
- never echo offending content；
- benign examples including `2024/2025`, `P5/P6 evidence`, and natural-language keyword mentions must remain allowed。

## 3. F2 implementation contract

Parser-level CLI failures must be normalized before argparse can emit usage/error text.

Mandatory direct cases:
- no subcommand；
- unknown subcommand；
- missing required argument；
- `--input-json` together with `--input-file`。

For every parser-level case:
- exit 2；
- stdout empty；
- stderr exactly one JSON object；
- `status=ERROR`；
- `reason_code=P9_CLI_ARGUMENT_ERROR`；
- `message=invalid command line arguments`。

Success remains exit 0 / one stdout JSON / empty stderr.
Handled runtime failure remains exit 1 / empty stdout / one stderr JSON.

## 4. Verification

Use:
`D:\\Codex\\FinancialFilingDataFoundation\\.venv\\Scripts\\python.exe`

Run:
- focused P9 unit tests；
- full unit suite；
- compileall/import check；
- `git diff --check`；
- scope diff from accepted P8 baseline；
- confirm no network/AI/MCP SDK/Registry mutation/PDF reopen introduced。

Record the exact corrective candidate SHA and test counts.

## 5. Corrective formal review

Create a fresh detached review worktree at the exact corrective candidate.

The reviewer must:
- re-check F1/F2 against amended design；
- rerun the adversarial probes；
- verify all acceptance items, now 55 mandatory items；
- record a new formal review result artifact。

Only a detached P9-J corrective review verdict **PASS** authorizes P9-K.

## 6. Stop rule

Any new defect or design ambiguity:
`STOP → root cause → design amendment → commit/push → then implementation`.

No force push, reset --hard, clean, history rewrite, or destructive overwrite.
