# 39 — P7 Development Evidence

状态：**P7 DEVELOPMENT COMPLETE / READY FOR CODE REVIEW**

Branch:
`task/p7-quality-validation`

Initial design baseline:
`4e048ddf4c15da443e7de3e70ac4bc216773eef4`

Design amendments:
- P7-ISSUE-001 remove implicit P4 dependency: branch `1c0bc22e1db34f2e5d82ef933157be4e73cb07be`
- P7-ISSUE-002 source-lineage duplicate/conflict identity: branch `a66fadfe6069f31674816a06e6da172dec98cc67`
- P7-ISSUE-003 preflight execution error vs BLOCKED status: branch `8bf04bf337bc1375475fab8eb3a80e145d145a7e`

Production commit:
`34d2a75d23731826dba2c48946a2f8056279fb33`

Accepted baseline before P7:
`d13b62778d123ba109c5f8ab2329d121d81b186b`

## 1. Implemented Scope

Added:
- `src/financial_filing_data_foundation/validation/models.py`
- `src/financial_filing_data_foundation/validation/policy.py`
- `src/financial_filing_data_foundation/validation/validate.py`
- `src/financial_filing_data_foundation/validation/__init__.py`
- `tests/unit/validation/test_validate.py`

Implemented:
- deterministic ValidationIssue
- PASS / FAIL / REVIEW_REQUIRED / BLOCKED
- CompatibilityStatus integration
- document/page/fact/evidence gates
- P6 warning mapping
- period/unit/scope coverage
- structural table/fact coverage
- core statement signals
- context-safe balance/cash reconciliation
- source-lineage defensive duplicate/conflict check
- stable issue IDs
- stable parse_run_id
- validation report/issues artifact
- input fingerprints
- atomic persistence/reuse
- full semantic recomputation tamper guard
- ParsedDataRecord builder
- P1 Registry/Planner reuse integration

Not implemented:
- fact correction
- canonical metric output
- review overlay
- MCP
- Skill
- SEC
- OCR/Docling/network/AI

## 2. P7-ISSUE-001

Original design listed candidate_count as a mandatory metric while P7 formally consumes only P3/P5/P6.

Resolved:
- no implicit P4 path reopen
- no candidate_count inference
- reconstructed-table structural metrics are authoritative.

## 3. P7-ISSUE-002

First live run produced false cross-row conflicts:
- CN: 110 review issues
- HK: 384 review issues

Sampling proved legitimate repeated labels across distinct rows.

Resolved:
duplicate/conflict key now uses exact P5 source lineage:

```text
table_id + row_id + value_cell_id + column_index
```

Different rows with the same raw metric do not conflict.

First live issue counts were invalidated and rerun.

## 4. Focused Tests

Final P7 focused:

`24 passed in 0.73s`

Coverage:
- status priority
- compatibility
- no-facts FAIL rather than BLOCKED
- invalid page sequence BLOCKED
- balance reconciliation pass/fail/skip
- cash reconciliation pass/fail
- same-lineage duplicate/conflict
- repeated metric across distinct rows not conflict
- preflight missing/corrupt input returns P7_INPUT_ARTIFACT_INVALID and no validation artifact
- semantic coverage thresholds
- row-without-label threshold
- stable issue ID
- full synthetic P3→P4→P5→P6→P7 PASS
- dual-root determinism
- reuse
- report/issue tamper
- ParsedDataRecord
- Planner REUSE_DATA only for PASS reusable record
- no PDF open
- upstream immutability

## 5. Full Regression

P0–P7:

`213 passed in 5.40s`

Additional:
- compileall PASS
- git diff --check PASS
- no Dayu/Docling/Torch/network/external-AI imports
- no PDF open
- no canonical metric implementation

## 6. Live Inputs

Project-root accepted-equivalent inputs:
- P3/P5: `workspace/live/p6-inputs`
- P6: `workspace/live/p6-facts`

Input immutability was checked for:
- P3 document/pages/sections/search DB
- P5 manifest/tables/groups
- P6 manifest/facts/evidence

PASS.

## 7. Final Live CN — 600519 FY2024

Validation status:
`REVIEW_REQUIRED`

Compatibility:
`COMPATIBLE`

Reuse eligible:
`false`

Issues:
- blocking: 0
- failure: 0
- review: 1
- warning: 2
- total: 3

Reason codes:
- `RAW_PERIOD_COVERAGE_LOW` — REVIEW
- `RAW_UNIT_COVERAGE_WARN` — WARNING
- `ROW_WITHOUT_LABEL_PRESENT` — WARNING

Metrics:
- page_count: 143
- reconstructed_table_count: 97
- table_group_count: 4
- raw_fact_count: 2177
- evidence_count: 2177
- unique_metric_count: 594
- pages_with_facts: 76
- tables_with_facts: 80
- tables_without_facts: 17
- tables_without_facts_ratio: 0.175258
- fact_density_per_table: 22.443299
- evidence_coverage_ratio: 1.0
- source_word_coverage_ratio: 1.0
- period_nonnull_ratio: 0.061093
- unit_nonnull_ratio: 0.041801
- scope_nonnull_ratio: 0.070740
- row_without_label_count: 353
- row_without_label_ratio: 0.139526
- core statement signals: balance/income/cashflow = true/true/true
- reconciliation evaluated: 0
- reconciliation skipped: 4

Dual-root:
- issues byte-identical: PASS
- report semantic-identical: PASS
- inputs immutable: PASS

Runtime:
- 3893.699 / 6036.540 ms

issues SHA:
`f8458ac09ff25cfcac9a9ab550f860c0a90de4493b36c111a179bcd10eadffd6`

Performance <=10s: PASS.

## 8. Final Live HK — 00700 FY2024

Validation status:
`REVIEW_REQUIRED`

Compatibility:
`COMPATIBLE`

Reuse eligible:
`false`

Issues:
- blocking: 0
- failure: 0
- review: 4
- warning: 2
- total: 6

Reason codes:
- `CORE_STATEMENT_COVERAGE_LOW` — REVIEW
- `RAW_PERIOD_COVERAGE_LOW` — REVIEW
- `RAW_UNIT_AMBIGUOUS` — REVIEW
- `RAW_UNIT_COVERAGE_LOW` — REVIEW
- `RAW_SCOPE_COVERAGE_ZERO` — WARNING
- `ROW_WITHOUT_LABEL_PRESENT` — WARNING

Metrics:
- page_count: 274
- reconstructed_table_count: 97
- table_group_count: 18
- raw_fact_count: 2989
- evidence_count: 2989
- unique_metric_count: 472
- pages_with_facts: 86
- tables_with_facts: 86
- tables_without_facts: 11
- tables_without_facts_ratio: 0.113402
- fact_density_per_table: 30.814433
- evidence_coverage_ratio: 1.0
- source_word_coverage_ratio: 1.0
- period_nonnull_ratio: 0.0
- unit_nonnull_ratio: 0.015055
- scope_nonnull_ratio: 0.0
- row_without_label_count: 388
- row_without_label_ratio: 0.114895
- core statement signals: balance/income/cashflow = false/true/false
- reconciliation evaluated: 0
- reconciliation skipped: 0

Dual-root:
- issues byte-identical: PASS
- report semantic-identical: PASS
- inputs immutable: PASS

Runtime:
- 7965.001 / 8399.415 ms

issues SHA:
`b39e2496c52d1a0dd5ea273258c29b57a02eadfa257b2bbf6ce97f1c70f4ec70`

Performance <=15s: PASS.

## 9. P7-ISSUE-003 Final Clarification

Code Review confirmed upstream P3/P5/P6 loaders can reject missing/corrupt/version-mismatched/tampered input before P7 has a trustworthy document identity.

Final design semantics:
- preflight input failure → `ValidationError(P7_INPUT_ARTIFACT_INVALID)`;
- no validation artifact is persisted;
- `ValidationStatus.BLOCKED` is reserved for blocking findings after trusted input loading/identity establishment;
- current production implementation already behaved this way, so no production-code change was required;
- dedicated regression now locks this boundary.

Final focused suite after clarification: `24 passed`.
Final full suite after clarification: `213 passed`.

## 10. Reuse Semantics

Synthetic complete validation:
- status PASS
- compatible
- blocking 0
- reuse_eligible true

After `build_parsed_data_record` + `SQLiteRegistry.register_parsed_data`:
- P1 planner returns `REUSE_DATA`.

Synthetic REVIEW_REQUIRED:
- reuse_eligible false
- planner does not return REUSE_DATA.

## 11. Gate Result

- P7-B Models/Policy: PASS
- P7-C Structural/Evidence: PASS
- P7-D Coverage: PASS
- P7-E Reconciliation: PASS
- P7-F Persistence/Tamper: PASS
- P7-G Registry Integration: PASS
- P7-H Full Regression: PASS
- P7-I Live CN/HK: PASS

Next:
**P7-J — Code Review**
