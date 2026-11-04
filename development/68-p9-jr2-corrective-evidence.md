# 68 — P9-JR2 Corrective Development Evidence

Status: **DEVELOPMENT PASS — AWAITING DETACHED FORMAL RE-REVIEW**

Phase:
`P9 — Codex Review Overlay / P9-JR2`

## 1. Baselines

- accepted P8: `ee934ad05812c69b79f76db43e62cfd4050efb8e`
- prior failed re-review: `development/66-p9-jr-formal-rereview-result.md`
- P9-JR2 design baseline: `e7bb65cfdb046c83a467dc865b853658726a767a`
- exact corrective production candidate: `f02504a69d7bc454b674a4ad347aaeecad38f6be`

Corrective production delta from `e7bb65c...` is exactly:

- `src/financial_filing_data_foundation/review/cli.py`
- `src/financial_filing_data_foundation/review/evidence.py`
- `tests/unit/review/test_review_overlay.py`

No P0-P8 source/test path is changed.

## 2. P9-JR-F1 correction

File-path classification now rejects:

- `/tmp`
- `/secret.txt`
- `/etc/passwd`
- `C:\\secret.txt`
- `path=C:\\secret.txt`
- UNC paths
- explicit traversal

while preserving benign slash-bearing finance text such as:

- `2024/2025`
- `P5/P6 evidence`

SQL classification was changed from a lexical keyword-span rule to deterministic
statement grammar using SQL projection, object, assignment, and clause/end
signals.

Required blocked examples include:

- `SELECT * FROM secrets`
- `SELECT revenue FROM secrets`
- SQL function/schema SELECT forms
- `INSERT INTO`
- assignment-like `UPDATE ... SET ... =`
- `DELETE FROM`
- DDL table statements
- `UNION SELECT`
- `PRAGMA`

Required allowed natural language includes:

- `SQL review completed`
- `Select revenue from the annual report evidence.`
- `Update guidance set by management.`

All prior URL/shell/Python/credential checks remain active. Direct contract
probe also includes `bash -lc` and bare `PRAGMA`.

## 3. P9-JR-F2 correction

Argparse built-in help is disabled through the P9 parser class for root and
subparsers.

The following now all use the same deterministic parser error contract:

- no subcommand
- unknown subcommand
- missing required argument
- mutually-exclusive input conflict
- root `--help`
- root `-h`
- subcommand `--help`
- subcommand `-h`

Contract:

- exit 2
- stdout empty
- stderr exactly one JSON object
- `P9_CLI_ARGUMENT_ERROR`
- `invalid command line arguments`
- no argparse usage/help prose

## 4. Exact-candidate evidence

All work and temporary paths remained under:

`D:\Codex\FinancialFilingDataFoundation`

Exact HEAD:
`f02504a69d7bc454b674a4ad347aaeecad38f6be`

Results:

- focused P9: **64 passed**
- full unit: **299 passed**
- full direct Section 49 security probe: `security_failures=[]`
- raw CLI parser/help probe: `cli_failures=[]`
- compileall: PASS
- all seven review module imports: PASS / `IMPORT_OK`
- `git diff --check e7bb65c..f02504a`: PASS
- accepted-P8 source/test scope: PASS
- active tracked worktree clean after commit

Short ignored test roots under `worktrees/t/` were used to avoid Windows
deep-snapshot path-length errors.

## 5. Scope

No corrective change:

- modifies accepted P0-P8 production/tests/artifacts
- opens/modifies source PDF
- adds network/AI/Codex API
- adds external MCP SDK
- mutates Registry
- enters P9-K/L/M
- enters P10/P11/Research MCP/Semantic Resolver production

The pre-existing untracked
`docs/superpowers/plans/2026-11-03-p9-recovery-closeout.md`
remains preserved and excluded.

## 6. Gate

P9-JR2 development verification: **PASS**.

Next allowed action:
freeze an exact review candidate including this evidence and perform a fresh
detached formal re-review against all 55 acceptance items.

P9-K remains closed until that review is PASS.
