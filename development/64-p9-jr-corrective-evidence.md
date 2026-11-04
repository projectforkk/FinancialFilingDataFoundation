# 64 — P9-JR Corrective Development Evidence

Status: **DEVELOPMENT PASS — AWAITING DETACHED FORMAL RE-REVIEW**

Phase:
`P9 — Codex Review Overlay / P9-JR`

## 1. Baselines

- accepted P8 merge: `ee934ad05812c69b79f76db43e62cfd4050efb8e`
- failed formal review: `development/62-p9-j-formal-code-review-result.md`
- design corrective baseline: `d668c6e21cba8ae274ebbb786ccb70e55c9e04c2`
- project-root execution governance: `c40e13579830b485e115ad1ce1a99e803f85fd49`
- exact corrective production candidate: `2d42c02c4e5dc7026b50c6928a57b1781ba0d831`

Corrective candidate diff from `c40e135...` is exactly four files:

- `src/financial_filing_data_foundation/review/cli.py`
- `src/financial_filing_data_foundation/review/evidence.py`
- `src/financial_filing_data_foundation/review/store.py`
- `tests/unit/review/test_review_overlay.py`

Diff stat:
`251 insertions / 3 deletions`.

No P0-P8 production/test file is changed by the corrective candidate.

## 2. P9-J-F1 correction

Implemented the amended Section 49 payload-wide persisted-content invariant.

Implementation facts:

- deterministic recursive string-leaf validation；
- validation is applied to normalized `ReviewResolution.to_dict(include_id=False)` before resolution-ID hashing/persistence；
- the same validation is applied during historical resolution semantic validation；
- stable rejection:
  - `P9_RESOLUTION_CONTENT_FORBIDDEN`
  - `resolution payload contains forbidden content`
- rejection does not echo the offending content。

Direct adversarial unit coverage includes:

- URL in `justification`；
- SQL statement in `value`；
- Windows file path；
- shell command；
- Python executable syntax；
- credential assignment；
- a re-signed historical resolution containing forbidden content。

Benign false-positive guard includes:

- `2024/2025`；
- `P5/P6 evidence`；
- natural-language `SQL review completed`。

The two exact P9-J-F1 proof shapes are now rejected by the same persisted-payload validator rather than special-cased.

## 3. P9-J-F2 correction

Implemented a deterministic argparse boundary using a P9-specific parser error path.

Parser-level failures now produce:

- exit `2`；
- stdout empty；
- stderr exactly one JSON document；
- `status=ERROR`；
- `reason_code=P9_CLI_ARGUMENT_ERROR`；
- `message=invalid command line arguments`。

Direct unit coverage includes:

1. no subcommand；
2. unknown subcommand；
3. missing required argument；
4. `--input-json` + `--input-file` conflict。

Raw subprocess verification against exact candidate `2d42c02...` independently observed all four cases with the exact contract above.

Success remains exit 0 / one stdout JSON / empty stderr.
Handled post-parse/runtime errors remain exit 1 / empty stdout / one stderr JSON.

## 4. Exact-candidate test evidence

All accepted execution paths are inside:

`D:\Codex\FinancialFilingDataFoundation`

Short ignored Windows test roots were required because deep P9 snapshot paths include two 64-character hashes.

Accepted exact-candidate commands use:

- focused basetemp: `D:\Codex\FinancialFilingDataFoundation\worktrees\t\f`
- full basetemp: `D:\Codex\FinancialFilingDataFoundation\worktrees\t\u`

Results at exact HEAD `2d42c02c4e5dc7026b50c6928a57b1781ba0d831`:

- focused P9: **52 passed**；
- full unit: **287 passed**；
- compileall review package: PASS；
- import of all seven P9 review modules: PASS / `IMPORT_OK`；
- `git diff --check c40e135..2d42c02`: PASS；
- accepted-P8 source/test scope check: PASS；
- no unintended P0-P8 source/test path。

## 5. Environment/path evidence excluded from Gate

Two exploratory executions are explicitly **not** counted as acceptance evidence:

1. an early temp root outside the project directory was invalidated after the project-root-only constraint was stated；
2. project-local but longer basetemp names such as `runtimes/p9-jr-tests/focused` and `worktrees/t/f2` hit Windows path-length errors in deep content-addressed snapshot paths。

Those failures were execution-path-length failures, not semantic P9 test failures. The exact-candidate accepted evidence was rerun using the short project-local roots above.

## 6. Scope / immutability

The corrective work did not:

- modify P0-P8 accepted production/tests；
- modify catalog/P3/P5/P6/P7 artifacts；
- open or modify source PDFs；
- add network/AI/Codex API behavior；
- add external MCP SDK；
- add Registry mutation；
- enter P9-K/L/M；
- enter P10/P11/Research MCP/Semantic Resolver production。

The pre-existing untracked file:

`docs/superpowers/plans/2026-11-03-p9-recovery-closeout.md`

was preserved and excluded from all commits.

## 7. Gate result

P9-JR development verification: **PASS**.

Next allowed action:

- create a fresh detached worktree at the exact corrective review candidate；
- perform formal P9-J corrective re-review against the amended 55-item acceptance contract。

P9-K remains closed until that detached review returns **PASS**.
