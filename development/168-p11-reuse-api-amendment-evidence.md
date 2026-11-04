# 168 — P11 Reuse Public API Amendment Evidence — ISSUE-029

Status: **PASS — AMENDED DESIGN READY FOR CANDIDATE FREEZE**

Phase:
P11 — US SEC Provider

Historical reviewed candidate:
`dc1c59e1ec19e8cf3e75624643d045a9f954fd16`

Review stop:
`development/167-p11-reuse-api-review-stop.md`

Production remains CLOSED.

## P11-ISSUE-029 resolution

### Generic planner US guard

Exact public exception:

```python
class PackageAwarePlannerRequired(RuntimeError):
    reason_code = "P11_PACKAGE_AWARE_PLANNER_REQUIRED"
```

Exact message:

`market US requires P11 package-aware SEC planning`

Guard runs before:
- build_required_slots;
- any registry method;
- any FilingPlan/PlannerItem construction.

CN/HK return behavior remains unchanged.

### SEC package-aware reuse public API

Public module:

`financial_filing_data_foundation.sec.reuse`

Exact public selector:

`select_sec_reuse(registry, slot, document_sha256, source_package_sha256, reuse_policy, project_root, parsed_root) -> SecReuseDecision`

Exact public enums:

- SecReuseAction;
- SecReuseReason.

Exact frozen/slots decision fields:

1. action;
2. reason_code;
3. rejection_reasons;
4. slot_key;
5. document_sha256;
6. source_package_sha256;
7. parse_run_id;
8. artifact_path.

The exact success/parse invariants, no-candidate decision, failure classification and rejection-reason priority are frozen in design/26 Section 17.1.

Selector is read-only and returns SecReuseDecision only.

### Input validation

Frozen exact validation includes:

- market must be US;
- document/package SHA lowercase 64-hex;
- parsed_root inside project_root;
- registry artifact_path stays inside parsed_root.

## Prior issue regression

ISSUE-010..028 remediation remains intact.

## Scope

Design/governance only.

No src/tests/integration/runtime-lock change.

## Verdict

# PASS — READY FOR CANDIDATE FREEZE AND FRESH DETACHED DESIGN REVIEW

No production authorization is implied.
