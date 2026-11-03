# P9-G Corrective Evidence — F1–F5

Status: READY FOR SECOND GITHUB REVIEW

Date: 2026-11-03 (Asia/Tokyo)

Branch: task/p9-review-overlay

This document records only the corrective P9-G work authorized by
development/55-p9-g-corrective-instruction.md. P9-I remains closed.
Historical development/52-p9-g-development-evidence.md was not modified.

## 1. Starting state and corrective commit

- Local HEAD before governance fast-forward:
  4207ae0c6eadf63b0c989b432e518f37c292836d
- Remote governance HEAD fetched:
  7a41d83f53c45ef1948440eb5b330aad5ebc54dc
- Fast-forward: 4207ae0 -> 7a41d83, clean and conflict-free.
- Incoming paths were governance/review documentation only:
  PROJECT_STATUS.md, development/54-p9-g-github-code-review.md, and
  development/55-p9-g-corrective-instruction.md.
- No uncommitted P9 production/test edits were present; the only untracked
  item was the excluded internal plan
  docs/superpowers/plans/2026-11-03-p9-recovery-closeout.md.
- Corrective implementation commit:
  f3b6dcd1b243c7a77734a1cdfa7459f38d91c842

Corrective source/test files changed in that commit:

- src/financial_filing_data_foundation/review/evidence.py
- src/financial_filing_data_foundation/review/queue.py
- src/financial_filing_data_foundation/review/resolve.py
- src/financial_filing_data_foundation/review/store.py
- tests/unit/review/test_review_overlay.py

No P0–P8 source/tests, raw/source artifacts, live P9-I output, or temporary
files were included.

## 2. F1 — complete immutable resolution-history semantic validation

Root cause: the prior implementation validated canonical bytes and graph
structure in store.py, while semantic target/evidence/before/after
recomputation was only used by selected materialization paths. A new submit or
the CLI resolutions path could therefore consume a re-signed historical record
before its semantic meaning had been checked.

Correction:

- Moved the authoritative semantic recomputation into
  evidence.validate_resolution_semantics().
- Added dependency-ordered evidence.validate_resolution_history() covering
  every persisted record, including superseded records.
- store.list_resolutions() now performs graph validation, reloads the
  immutable base bundle, and semantically validates the complete history.
- Submit, active-resolution APIs, materialization, snapshot loading, and CLI
  resolutions all pass through that validated loader path.
- Resolver materialization reuses the same semantic implementation instead of
  maintaining a second copy.

New regression coverage proves rejection of:

- re-signed historical before.affected_fact_ids before a later submit can
  write a new file;
- re-signed superseded-parent evidence when the terminal child remains
  structurally valid;
- tampered supporting evidence before attestation inheritance;
- semantically corrupt stores through both list_resolutions() and CLI
  resolutions.

## 3. F2 — submitted trimmed value preservation

For SET_PERIOD, SET_UNIT, and SET_SCOPE, target selection now keeps two
values:

- submitted_value: leading/trailing whitespace trimmed only, used for
  persisted resolution and effective output;
- normalized_value: whitespace-collapsed value used only for comparison.

Coverage proves that "  人民币   百万元  " persists and resolves as
"人民币   百万元", while whitespace-equivalent explicit raw values still
produce the designed no-op comparison result.

## 4. F3 — raw justification limit

Reviewer validation now requires non-whitespace justification and enforces the
raw persisted string length at <= 4000 characters. It does not collapse
whitespace for the length check and does not truncate.

Boundary coverage:

- 4000 characters: accepted;
- 4001 characters: rejected with P9_INVALID_RESOLUTION;
- whitespace-heavy raw input over 4000: rejected;
- whitespace-only input: rejected.

## 5. F4 — deterministic staging without random identity

prepare_review_overlay() no longer imports or calls uuid.uuid4().
Staging uses the deterministic document-bound path:

.<document_sha256>.tmp

If an unknown staging directory already exists, preparation fails with
P9_PERSIST_FAILED and leaves that directory untouched. Cleanup is performed
only after the current operation successfully creates the staging directory.
The source/scope test also asserts that the review production package contains
no UUID/random identity surface.

## 6. F5 — direct CLI matrix

Direct review_cli_main() coverage now exercises all required surfaces:

- prepare
- tasks
- submit --input-json
- submit --input-file
- resolutions
- materialize
- report
- malformed JSON
- non-object JSON

Successful calls assert return code 0, exactly one valid JSON document on
stdout, and empty stderr. Handled failures assert empty stdout, one
deterministic JSON diagnostic on stderr, and a non-zero return code.

## 7. Verification

Runtime:

D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe

Compile/import:

D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -m compileall src\financial_filing_data_foundation\review
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -c "import financial_filing_data_foundation.review; import financial_filing_data_foundation.review.cli"

Result: PASS; compileall exited 0 and imports succeeded.

Focused P9 suite:

D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -m pytest tests\unit\review\test_review_overlay.py -q --basetemp D:\Codex\FFDF-t\p9\corrective-focused-pre

Result: 40 passed in 8.41s.

Full unit regression:

D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -m pytest tests\unit -q --basetemp D:\Codex\FFDF-t\p9\corrective-full-pre

Result: 275 passed in 16.16s.

F1–F5 corrective subset:

D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -m pytest tests\unit\review\test_review_overlay.py -q -k "submit_revalidates_resigned_historical_before_before_new_write or materialize_revalidates_resigned_superseded_parent or attestation_rejects_resigned_support_evidence or cli_resolutions_rejects_semantically_corrupt_store or fill_preserves_trimmed_value_and_effective_value or raw_whitespace_equivalence_still_uses_collapsed_comparison or justification_uses_raw_4000_character_boundary or prepare_rejects_unknown_deterministic_staging_directory or cli_full_success_matrix_is_json_only or cli_submit_rejects_malformed_and_non_object_json" --basetemp D:\Codex\FFDF-t\p9\corrective-f1-f5

Result: 11 passed, 29 deselected in 1.94s.

Diff check: PASS before and after the corrective implementation commit;
staged corrective diff also passed git diff --check.

Scope scan: PASS.

- no OpenAI/Anthropic/Gemini/network API imports;
- no requests, httpx, urllib, socket, subprocess, or external MCP SDK;
- no PDF/OCR/source reopen;
- no Registry mutation;
- no random UUID/random identity generation;
- no P10/P11 production;
- corrective working-tree changes limited to the five listed P9 source/test
  files.

Immutability and synthetic:

D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -m pytest tests\unit\review\test_review_overlay.py -q -k "resolved_view_fills_nulls_without_mutating_raw_and_can_reach_pass or synthetic_golden_resolves_period_unit_and_core_to_pass" --basetemp D:\Codex\FFDF-t\p9\cor

Result: 2 passed, 38 deselected in 0.47s.

A before/after snapshot of 25 official catalog/P3/P5/P6/P7 files found no
SHA256, size, or mtime change. The synthetic path reached
REVIEW_REQUIRED -> PASS and built the resolved ParsedDataRecord.

## 8. Boundary and blocker status

- P9-I live execution: NOT RUN in this corrective task.
- P9-J/K/L/M: NOT RUN.
- No main merge, P10, or P11 work.
- Historical development/52 was not changed.
- Design ambiguity: none; F1–F5 were fully specified by the current design.
- Blocker: none.

The corrective implementation candidate is
f3b6dcd1b243c7a77734a1cdfa7459f38d91c842. This evidence file is the
separate corrective-evidence commit to be pushed after final verification.
