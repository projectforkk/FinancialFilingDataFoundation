# 167 — P11 Package-Aware Reuse Review Stop — Public API / Error Surface

Status: **FAIL / STOP — P11-ISSUE-029 / PRODUCTION CLOSED**

Phase:
P11 — US SEC Provider

Reviewed exact candidate:
`dc1c59e1ec19e8cf3e75624643d045a9f954fd16`

Fresh detached review:
`D:\\Codex\\FinancialFilingDataFoundation\\worktrees\\review\\p11-design-dc1c59e`

Automated ISSUE-010..028 matrix:
`PASS`

## Finding

Manual review of the accepted P1 planner public contract found a remaining implementation ambiguity.

Accepted `IncrementalPlanner.build_plan(...)`:

- returns `FilingPlan`;
- uses `PlannerItem / PlannerAction / ReasonCode`;
- does not currently define a phase-capability exception contract.

The P11 design says market=US generic planner must “reject with P11_PACKAGE_AWARE_PLANNER_REQUIRED”, but does not freeze whether this means:

- raise an exception;
- return a synthetic BLOCKED FilingPlan;
- return a P11-specific decision object.

Those choices are materially different public APIs.

Likewise, the new package-aware SEC reuse selector has detailed eligibility rules but no exact return/result schema. An implementation would have to invent bool/tuple/record/action semantics.

## P11-ISSUE-029 — package-aware reuse public API / error surface

Required correction:

### Generic IncrementalPlanner US guard

Freeze exact fail-fast exception contract:

```python
class PackageAwarePlannerRequired(RuntimeError):
    reason_code = "P11_PACKAGE_AWARE_PLANNER_REQUIRED"
```

`IncrementalPlanner.build_plan(...)` MUST:

1. normalize/receive the already validated `CompanyRef`;
2. if `company.market == "US"`, raise `PackageAwarePlannerRequired` before:
   - `build_required_slots`;
   - any registry read;
   - any PlannerItem/FilingPlan construction;
3. exact message:
   `"market US requires P11 package-aware SEC planning"`.

CN/HK return behavior remains exactly unchanged.

### P11 package-aware selector result

Freeze exact P11 result object:

```text
SecReuseAction:
  REUSE_DATA
  PARSE_CURRENT_PACKAGE

SecReuseDecision:
  action
  reason_code
  document_sha256
  source_package_sha256
  parse_run_id nullable
  artifact_path nullable
```

Rules:

- REUSE_DATA requires non-null parse_run_id + artifact_path;
- PARSE_CURRENT_PACKAGE requires both null;
- reason_code is one exact P11 reuse reason;
- decision always echoes current document/package identity;
- selector never returns an arbitrary ParsedDataRecord directly;
- selector never mutates registry/artifacts.

Reason mapping must be frozen, including exact-package reuse success and no-reusable-current-package behavior.

Acceptance must prove exact exception class/message/reason_code and exact result object invariants.

## Scope

No production/test/runtime changes.

ISSUE-010..028 remediation remains valid.

## Verdict

# FAIL / STOP

Candidate `dc1c59e...` is INELIGIBLE for DESIGN READY.

P11 production remains CLOSED.
