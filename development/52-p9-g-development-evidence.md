# P9-G Development Evidence — Local Candidate Integration

Status: COMPLETE FOR GITHUB REVIEW

Date: 2026-11-03 (Asia/Tokyo)

Branch: `task/p9-review-overlay`

This evidence records the authorized P9-G candidate integration only. It does
not claim Independent Acceptance and does not authorize P9-I through P9-M.

## 1. Starting state and safe integration

- Starting local branch HEAD: `c345cfc235ba3631ff6349826e75dbbf7e3c304a`
- Preserved P9-G candidate: `e6f83d560822214ab4ede0e317f853d100b6c9ea`
- Starting remote P9 HEAD after `git fetch origin`:
  `ebbf03aa6d75f74096c7672da007633b0f77b0a8`
- Common ancestor for this integration:
  `2c56e38a51f148b86ce6f4754bf9bae7a157fd7e`
- Remote delta from the common ancestor was governance/design-only:
  - `design/22-p9-review-overlay-design.md`
  - `development/53-p9-local-candidate-integration-instruction.md`
- Local candidate delta from the common ancestor was limited to the eight
  P9 review source/test files.
- Path-overlap check: no overlap between the remote delta and the local
  production/test candidate.
- Integration method: normal non-destructive `git merge --no-ff`.
- Merge result: clean; no conflicts.
- Integration merge commit: `efbe17ebd84208c26a5f8c497c39125afada6ca6`
- Merge parents:
  - local lineage: `c345cfc235ba3631ff6349826e75dbbf7e3c304a`
  - remote governance lineage: `ebbf03aa6d75f74096c7672da007633b0f77b0a8`
- No reset, clean, rebase, force push, history rewrite, checkout/restore, or
  candidate reconstruction was used.

The pre-existing untracked item was the internal plan
`docs/superpowers/plans/2026-11-03-p9-recovery-closeout.md`. It is not a P9
production/test file and is excluded from the candidate. There were no
uncommitted P9 production/test edits at integration start.

## 2. Files and candidate scope

The merge itself changed only:

- `design/22-p9-review-overlay-design.md`
- `development/53-p9-local-candidate-integration-instruction.md`

The P9-G candidate source/test files from `e6f83d...` were preserved unchanged
and revalidated. This task added this evidence file:

- `development/52-p9-g-development-evidence.md`

The change-range path scan found no P0-P8 source/tests, raw/source artifacts,
temporary outputs, or live-review artifacts. The candidate Git tree contains
no `workspace/p9-live-review`, `__pycache__`, `.pytest_cache`, or test-temp
paths.

## 3. P9-G CLI contract

Entrypoint:

```text
python -m financial_filing_data_foundation.review.cli
```

The implementation exposes the six required deterministic subcommands:
`prepare`, `tasks`, `submit`, `resolutions`, `materialize`, and `report`.
Submission input is limited to an explicit JSON string or explicit JSON file.
Successful CLI output is one JSON document on stdout; diagnostics are JSON on
stderr with a non-zero exit code. Focused coverage includes
`test_cli_success_writes_one_json_document_to_stdout` and
`test_cli_diagnostics_are_json_on_stderr_only`.

No live catalog CLI operation was run in this integration because P9-I live
execution remains closed. The P9 APIs and deterministic CLI contract were
verified through the focused unit suite and source/scope inspection.

## 4. Post-merge verification

All commands below used the main runtime:

`D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe`

### Compile/import

```powershell
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -m compileall src\financial_filing_data_foundation\review
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -c "import financial_filing_data_foundation.review; import financial_filing_data_foundation.review.cli"
```

Result: PASS. `compileall` exited 0 and both review imports succeeded.

### Focused P9 tests

```powershell
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -m pytest tests\unit\review\test_review_overlay.py -q --basetemp D:\Codex\FFDF-t\p9\focused-integrated
```

Result: `29 passed in 3.89s`.

### Full unit regression

```powershell
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -m pytest tests\unit -q --basetemp D:\Codex\FFDF-t\p9\full-integrated
```

Result: `264 passed in 9.01s`.

### Diff check

```powershell
git diff --check
```

Result after the clean integration merge: PASS.

## 5. Scope, immutability, and synthetic checks

Scope scan result: PASS.

- No external OpenAI/Anthropic/Gemini/network imports.
- No `requests`, `httpx`, `urllib`, `socket`, `subprocess`, or external MCP
  SDK import.
- No PDF/OCR/source-reopen surface and no P10/P11 production surface.
- No Registry mutation call. The only related imports are the internal
  `McpCatalog` path guard and read-only `ValidationStatus` types.
- No P0-P8 source/test path was introduced in the candidate change range.

Immutability result: PASS.

- The official acceptance catalog and the live catalog were byte-identical.
- A before/after snapshot covered 25 files: both catalogs plus all cataloged
  P3/P5/P6/P7 files for the CN and HK documents.
- SHA256, size, and `mtime` were unchanged after the synthetic checks.
- The targeted raw-preservation and synthetic tests passed:

```powershell
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -m pytest tests\unit\review\test_review_overlay.py -q -k "resolved_view_fills_nulls_without_mutating_raw_and_can_reach_pass or synthetic_golden_resolves_period_unit_and_core_to_pass" --basetemp D:\Codex\FFDF-t\p9\is
```

Result: `2 passed, 27 deselected in 0.43s`; synthetic
`REVIEW_REQUIRED -> PASS` and resolved `ParsedDataRecord` construction passed.

One earlier auxiliary run used an unnecessarily long basetemp and hit a
Windows path-length error while writing a temporary synthetic snapshot. The
same tests passed with the short basetemp above; no production change was
made for that environment-only issue.

Pre-existing temporary P9-I live directories were identified under
`D:\Codex\FinancialFilingDataFoundation\workspace\p9-live-review`. They were
not used or modified by this integration, are outside the candidate worktree
status, and are excluded from the Git tree and commit. They are not accepted
P9-G evidence.

## 6. Governance boundary and blocker

- P9-I, P9-J, P9-K, P9-L, and P9-M were not executed in this integration task
  and remain unauthorized.
- No merge to `main` was performed.
- No P10 or P11 work was performed.
- Design blocker: none.
- Integration blocker: none.

The candidate commit required by the integration instruction is preserved as
`e6f83d560822214ab4ede0e317f853d100b6c9ea`. The integration merge commit is
`efbe17ebd84208c26a5f8c497c39125afada6ca6`.
