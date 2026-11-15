# 199 — P11 Review 6 Development Reauthorization

Status: **DESIGN_FREEZE_PASS / ISSUE-146 DEVELOPMENT_AUTHORIZED**

This record authorizes a narrow production/test correction for P11-ISSUE-146.
It is not a Formal Test Plan, Formal Acceptance, main-merge authorization, or
P11 DONE record.

## 1. Exact authority

Repository:

`projectforkk/FinancialFilingDataFoundation`

Remote lineage:

`reconcile/p11-140-143-local-chain`

Exact Design 38 freeze:

`92af6205eb8e090994dcece68850eddcd4232392`

Review-6 result:

`development/198-p11-fresh-full-exact-candidate-review-6.md`

Previous production candidate:

`35e2b70c78b6cff931c8484dc38f2eb7349735f5`

Previous evidence commit:

`93027f60be96f3998fb041ac6ad65bcf31c55834`

Verdict:

```text
DESIGN_FREEZE_PASS
ISSUE-146 DEVELOPMENT_AUTHORIZED
```

## 2. Current issue state

```text
ISSUE-140 = FIXED / regression preservation
ISSUE-141 = FIXED / regression preservation
ISSUE-142 = FIXED / regression preservation
ISSUE-143 = FIXED / regression preservation
ISSUE-144 = GOVERNANCE CORRECTED
ISSUE-145 = FIXED / regression preservation
ISSUE-146 = DEVELOPMENT AUTHORIZED
```

Do not redesign or reopen ISSUE-142/143/145 unless the correction proves a new
design defect.

## 3. Authorized production correction

Implement the Design 38 validation-only state:

```text
REVALIDATE_LOCAL
```

The planner must distinguish compatible parsed-artifact availability from
current validation-v3 reuse eligibility.

After fresh current discovery:

```text
compatible parsed + current reusable valid v3
→ REUSE_DATA

compatible parsed + v3 absent
→ REVALIDATE_LOCAL

compatible parsed + valid current v3 not reuse_eligible
→ REVALIDATE_LOCAL

no compatible parsed + immutable local package
→ PARSE_LOCAL

no local package
→ DISCOVER_AND_ACQUIRE
```

A present but corrupt current v3 must fail closed. It must not be treated as
absent, must not fall back to v2, and must not be silently overwritten through
migration.

## 4. Compatible parsed artifact

Create or refactor one helper that finds a compatible parsed artifact without
requiring current validation PASS/reuse eligibility.

Compatibility requires:

- selected package SHA match;
- parser version `VIRTUAL_HTML_V6`;
- artifact schema `p11-sec-artifacts-v2`;
- Registry artifact path present;
- `load_sec_artifacts()` succeeds;
- loaded parsed package SHA equals selected package SHA.

Validation status is evaluated separately.

## 5. REVALIDATE_LOCAL execution

For this action:

- use the immutable local package;
- load the compatible existing parsed artifact;
- do not invoke `parse_sec_package()`;
- register the fresh discovery observation;
- execute `validate_sec_artifacts()` directly;
- write current v3 to the existing Design-37 versioned path;
- preserve raw package bytes;
- preserve parsed artifact bytes;
- preserve legacy flat validation-v2 bytes;
- refresh current SEC parsed-run Registry validation fields;
- refresh slot binding and P8 catalog from the v3 result;
- compute research_ready from current v3 + current discovery.

A dedicated helper such as `revalidate_sec_package()` is allowed.

## 6. REUSE_DATA fresh-discovery refresh

The existing REUSE_DATA path must also refresh the current parsed-run Registry
validation fields after P7 reruns for the fresh discovery observation.

Do not fabricate a new parse identity solely because validation reran.

## 7. Required planner enum

Add:

```text
SecPlanAction.REVALIDATE_LOCAL = "REVALIDATE_LOCAL"
```

The CLI may expose this exact additive planner_action.

No schema or version bump results from this enum addition.

## 8. Frozen version contract

Unchanged:

```text
SEC_DISCOVERY_SCHEMA = p11-sec-discovery-v1
VIRTUAL_HTML_NORMALIZER_VERSION = VIRTUAL_HTML_V6
SEC_ARTIFACT_SCHEMA = p11-sec-artifacts-v2
SEC_VALIDATION_SCHEMA = p11-sec-validation-v3
SEC_REGISTRY_SCHEMA_VERSION = 4
```

No new reason code is authorized.

## 9. Required deterministic tests

At minimum:

```text
compatible parsed + reusable valid v3
→ REUSE_DATA

compatible parsed + v3 absent + optional legacy flat v2
→ REVALIDATE_LOCAL

compatible parsed + valid v3 not reuse_eligible
→ REVALIDATE_LOCAL

no compatible parsed + local raw package
→ PARSE_LOCAL

no local package
→ DISCOVER_AND_ACQUIRE
```

Migration execution:

```text
REVALIDATE_LOCAL
→ parser invocation count = 0
→ parsed artifact hashes unchanged
→ raw package hashes unchanged
→ legacy flat v2 hashes unchanged
→ validation-v3 executes
→ current v3 path remains schema-versioned
→ Registry validation fields equal v3
→ catalog/research_ready derive from v3
```

Corrupt current v3:

```text
compatible parsed + corrupt current v3 + valid legacy v2
→ fail closed
→ parser invocation count = 0
→ no v2 fallback
→ corrupt v3 is not silently overwritten
```

Fresh REUSE_DATA:

```text
parser invocation count = 0
P7 refresh executes for fresh discovery
Registry validation fields refresh from current v3
```

## 10. Regression

The next exact candidate must preserve all 35e2b70 fixes.

Rerun at minimum:

- Review-5/Review-6 focused tests;
- complete `tests/unit/us_sec`;
- US SEC + MCP;
- P0-P10 focused regression;
- full `tests/unit`;
- `python -m compileall src tests`;
- `git diff --check`.

Run Apple FY2025 developer smoke again only after deterministic tests pass.

## 11. Candidate/evidence discipline

Create one new production/test candidate after the implementation is complete.

Do not amend candidate 35e2b70.

After exact-candidate tests/smoke, create a separate documentation-only evidence
commit:

`development/200-p11-review6-issue146-evidence.md`

Then STOP for ChatGPT Fresh Full Exact-Candidate Review.

## 12. Formal boundary

```text
FORMAL TEST PLAN:
NOT CREATED / NOT AUTHORIZED

FORMAL TEST EXECUTION:
NOT AUTHORIZED

FORMAL ACCEPTANCE:
NOT RUN

MAIN MERGE:
NOT AUTHORIZED

P11 DONE:
NO
```
