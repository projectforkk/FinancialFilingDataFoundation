# 172 — P11 Revised Formal Acceptance Review 1

Status: **ACCEPTANCE_FAILED**

Reviewed production candidate:
`2504614265b7a233ef9e4a772544ad63dd6eec37`

Code review:
`development/169-p11-code-review-result-8.md`

Formal plan:
`development/170-p11-revised-formal-test-plan.md`

Formal plan commit:
`062c419a40c1b49d83efeca3eaa320a3634b6eda`

Formal execution evidence:
`development/171-p11-formal-test-evidence.md`

Evidence commit:
`09d9442ac846bf42e0094613c13665d731c5d031`

## 1. Evidence / lineage

PASS.

The evidence commit contains documentation only after the reviewed candidate. No production or test source changed during formal execution.

FT-00 through FT-07 and FT-09 through FT-11 passed. FT-08 failed.

## 2. FT-08 production defect

The acceptance-only malformed SEC archive-index harness expected a controlled `SecError` with reason `P11_SEC_DISCOVERY_FAILED`.

Candidate `25046142...` instead raises:

`UnboundLocalError: cannot access local variable 'SecError' where it is not associated with a value`.

Root cause verified in `src/financial_filing_data_foundation/us_sec/acquisition.py`:

- the module already imports `P11Reason, SecError` at top level;
- `SecAcquirer.acquire()` repeats `from .errors import P11Reason, SecError` inside several JSON-decode `except` branches;
- those import statements make both names local to the entire function under Python scoping rules;
- on a path where JSON decoding succeeds, those local imports do not execute;
- later malformed archive-index shape checks execute `raise SecError(P11Reason...)` while the local names are unbound;
- Python therefore raises `UnboundLocalError` instead of the required controlled P11 reason.

This is a production-code defect, not a harness/environment failure.

## 3. Required repair

Perform a narrow acquisition error-path repair:

1. remove the redundant function-local imports of `P11Reason, SecError` from `SecAcquirer.acquire()` and use the existing module-level imports;
2. preserve all intended reason codes/messages;
3. add deterministic unit regressions for malformed archive-index shapes, including at least invalid directory, invalid item list, and invalid item record;
4. ensure malformed archive-index JSON itself still maps to `P11_SEC_DISCOVERY_FAILED`;
5. ensure invalid submissions and historical-submissions JSON still map to `P11_SEC_DISCOVERY_FAILED`;
6. do not change discovery policy, package selection, parser, Registry, P8, supported markets, or production availability.

## 4. Formal acceptance verdict

```text
P11 REVISED FORMAL ACCEPTANCE: ACCEPTANCE_FAILED

FAILED GATE:
FT-08 SECURITY / HTTP / SOURCE INTEGRITY

ROOT CAUSE:
PRODUCTION ACQUISITION ERROR-PATH NAME SHADOWING

PRODUCTION CANDIDATE:
2504614265b7a233ef9e4a772544ad63dd6eec37

MAIN MERGE:
NOT AUTHORIZED

P11 PRODUCTION AVAILABILITY:
NOT CHANGED
```

## 5. Lifecycle

Because production code must change, the current formal acceptance cycle is closed as failed.

Required next lifecycle:

`code fix → new exact production candidate → ChatGPT exact-candidate code review → new/revised formal test plan → new formal execution`.

Do not resume the old plan against modified production bytes.