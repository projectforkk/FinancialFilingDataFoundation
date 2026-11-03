# 25 — P7 Independent Acceptance Run Instruction

状态：**P7 ACCEPTANCE FREEZE**

Phase:
`P7 — Quality Gate / Validation`

Accepted baseline before P7:
`d13b62778d123ba109c5f8ab2329d121d81b186b`

Reviewed candidate:
`0b1ffcec4fa4416724a6c505a9706eb41999bead`

Production commit:
`34d2a75d23731826dba2c48946a2f8056279fb33`

Code Review:
- verdict: PASS
- evidence: `development/40-p7-code-review.md`
- review commit: `2b3163be8ccd230316450c00dcb327b8136b5ce2`

The acceptance candidate is the Git commit containing this freeze file.

## Expected Suite

`213 passed`

## Frozen Live Inputs

P3/P5:
`D:\Codex\FinancialFilingDataFoundation\workspace\live\p6-inputs`

P6:
`D:\Codex\FinancialFilingDataFoundation\workspace\live\p6-facts`

## Expected CN

600519 FY2024:
- validation_status: REVIEW_REQUIRED
- compatibility_status: COMPATIBLE
- reuse_eligible: false
- blocking: 0
- failure: 0
- review: 1
- warning: 2
- issue_count: 3
- reasons:
  - RAW_PERIOD_COVERAGE_LOW
  - RAW_UNIT_COVERAGE_WARN
  - ROW_WITHOUT_LABEL_PRESENT
- issues SHA: `f8458ac09ff25cfcac9a9ab550f860c0a90de4493b36c111a179bcd10eadffd6`
- dual-root issue bytes: identical
- report semantics: identical
- inputs immutable
- <=10s each run

## Expected HK

00700 FY2024:
- validation_status: REVIEW_REQUIRED
- compatibility_status: COMPATIBLE
- reuse_eligible: false
- blocking: 0
- failure: 0
- review: 4
- warning: 2
- issue_count: 6
- reasons:
  - CORE_STATEMENT_COVERAGE_LOW
  - RAW_PERIOD_COVERAGE_LOW
  - RAW_UNIT_AMBIGUOUS
  - RAW_UNIT_COVERAGE_LOW
  - RAW_SCOPE_COVERAGE_ZERO
  - ROW_WITHOUT_LABEL_PRESENT
- issues SHA: `b39e2496c52d1a0dd5ea273258c29b57a02eadfa257b2bbf6ce97f1c70f4ec70`
- dual-root issue bytes: identical
- report semantics: identical
- inputs immutable
- <=15s each run

## Mandatory Acceptance

1. fresh detached worktree under project root
2. frozen HEAD stable
3. P0–P7 full suite = 213 PASS
4. prior P0–P6 source/tests zero unintended diff
5. preflight missing/corrupt input → P7_INPUT_ARTIFACT_INVALID + no artifact
6. trusted-input BLOCKED semantics separate
7. no-facts FAIL
8. evidence/page/identity gates
9. coverage policy
10. P6 warning mapping
11. core statement signal
12. balance/cash reconciliation pass/fail/skip
13. source-lineage duplicate/conflict only
14. no cross-row false conflicts
15. stable issue IDs
16. stable parse_run_id
17. report/issues semantic recomputation
18. tamper rejection
19. reuse eligibility
20. ParsedDataRecord mapping
21. P1 Planner REUSE_DATA only for reusable PASS
22. CN exact live result/SHA
23. HK exact live result/SHA
24. dual-root determinism
25. upstream immutability
26. no PDF open
27. no OCR/Dayu/Docling/network/AI
28. no canonical metric output
29. performance gates

Acceptance must not modify production/tests/design/config/dependencies.

Final verdict:
PASS / FAIL / BLOCKED

P8 implementation must not begin during P7 acceptance.
