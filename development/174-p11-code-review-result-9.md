# 174 — P11 US SEC Provider Ninth Exact-Candidate Code Review

Status: **REVIEW_PASS**

Reviewed exact production candidate:
`9b7fcc9fc37a423eaafd1dde762e9c81d475df9e`

Failed predecessor candidate:
`2504614265b7a233ef9e4a772544ad63dd6eec37`

Failed formal acceptance evidence:
`development/171-p11-formal-test-evidence.md`

Failed evidence commit:
`09d9442ac846bf42e0094613c13665d731c5d031`

Acceptance failure review:
`development/172-p11-formal-acceptance-review-1.md`

Acceptance failure review commit:
`d28089f4e26749a7209afb2178564a4fbaea76c3`

Repair evidence:
`development/173-p11-ft08-acquisition-error-path-repair-evidence.md`

Repair evidence commit:
`bb56952f158e1139b3330546aa37102933251011`

Development branch:
`task/p11-sec-rebuild-development`

## 1. Exact-candidate lineage

PASS.

The reviewed production candidate is exactly `9b7fcc9fc37a423eaafd1dde762e9c81d475df9e`.

Candidate source/test changes are restricted to:
- `src/financial_filing_data_foundation/us_sec/acquisition.py`;
- `tests/unit/us_sec/test_provider_cli.py`.

After the candidate, only `development/173-p11-ft08-acquisition-error-path-repair-evidence.md` was added before this review. No production/test source changed after the exact candidate.

## 2. Formal FT-08 root cause

CONFIRMED.

The predecessor candidate imported `P11Reason` and `SecError` at module scope but repeated the same import inside three conditional JSON-decode exception branches in `SecAcquirer.acquire()`.

Under Python function scoping, those conditional imports made the names local to the entire function. Structural archive-index failures could reach later `raise SecError(...)` statements without executing a local import branch first, producing `UnboundLocalError` instead of the required controlled P11 error.

This exactly explains the formal acceptance failure recorded in evidence 171.

## 3. Production repair review

PASS.

The new candidate removes all three function-local duplicate imports and retains the existing module-level:

`from .errors import P11Reason, SecError`

No discovery, selection, history-range, package, path-policy, HTTP, parser, Registry, P8, or CLI behavior was otherwise changed.

The acquisition production diff is six deleted lines and no added production lines.

`SecAcquirer.acquire()` now has zero function-local `.errors` imports.

## 4. Error-contract regression coverage

PASS.

The new focused tests independently exercise:

1. invalid main submissions JSON;
2. invalid historical submissions JSON;
3. invalid archive index JSON;
4. invalid archive index directory shape;
5. invalid archive index item-list shape;
6. invalid archive index item-record shape.

All six require `SecError` with reason code `P11_SEC_DISCOVERY_FAILED`.

The three structural archive-index cases reproduce the predecessor `UnboundLocalError` before the production repair and pass after repair.

Positive acquisition tests remain present for valid submissions/index/package acquisition, local-package `PARSE_LOCAL`, amendment conflict, and scoped history-chunk fetching.

## 5. FT-08 targeted rerun

Repair evidence reports the original acceptance-only FT-08 security harness was rerun unchanged against the repaired code and returned PASS.

Reported decisive values include:
- malformed archive-index path: PASS;
- terminal 403 attempts: 2;
- terminal 429 attempts: 3;
- redirect host/cap: PASS;
- safe nested path: PASS;
- unsafe path cases: 8;
- source drift rejection: PASS;
- remote script not executed: PASS.

## 6. Regression evidence

Evidence 173 reports:
- focused provider/acquisition: 11 passed;
- reviewed FT-08 unit scope: 84 passed;
- P11 focused: 100 passed;
- full unit: 630 passed;
- CN/HK regression: 96 passed;
- compileall: PASS;
- git diff --check: PASS.

Governance constants remain unchanged:

```text
SUPPORTED_MARKETS = ("CN", "HK")
REGISTRY_SCHEMA_VERSION = 1
SEC_REGISTRY_SCHEMA_VERSION = 3
VIRTUAL_HTML_NORMALIZER_VERSION = VIRTUAL_HTML_V4
SEC_ARTIFACT_SCHEMA = p11-sec-artifacts-v1
```

## 7. New blocking findings

NONE.

## 8. Ninth review verdict

```text
P11 NINTH CODE REVIEW: REVIEW_PASS

EXACT PRODUCTION CANDIDATE:
9b7fcc9fc37a423eaafd1dde762e9c81d475df9e

FT-08 PRODUCTION DEFECT:
FIXED

NEW BLOCKING CODE FINDINGS:
NONE

FORMAL ACCEPTANCE:
REQUIRES NEW EXECUTION

MAIN MERGE:
NOT AUTHORIZED

P11 PRODUCTION AVAILABILITY:
NOT CHANGED
```

## 9. Next gate

The previous formal execution against `25046142...` remains failed and cannot be reclassified.

The repaired candidate must enter a new formal acceptance cycle under a newly issued plan tied to exact candidate `9b7fcc9fc37a423eaafd1dde762e9c81d475df9e`.

The new plan may reuse prior passed gates as design/reference context, but execution evidence for the new candidate must be produced under the new plan. At minimum it must rerun the complete deterministic regression, FT-08, live SEC fixture gates, idempotent reuse, Registry/incremental gates, and governance checks required by the accepted P11 design.

Next action:

`CHATGPT FORMAL TEST PLAN FOR EXACT CANDIDATE 9b7fcc9fc37a423eaafd1dde762e9c81d475df9e`

No main integration or production enablement is authorized before a new independent `ACCEPTANCE_PASS`.