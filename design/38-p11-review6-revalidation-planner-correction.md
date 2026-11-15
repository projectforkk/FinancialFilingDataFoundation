# 38 — P11 Review 6 Validation Revalidation Planner Correction

Status: **AUTHORITATIVE DESIGN CORRECTION — EXACT-CANDIDATE REVIEW 6**

Development: **NOT YET AUTHORIZED**

This correction is required by the fresh full review of production candidate
`35e2b70c78b6cff931c8484dc38f2eb7349735f5`.

It does not reopen the accepted ISSUE-142, ISSUE-143, or ISSUE-145 source
semantics. It corrects the incremental planner/execution state required by the
validation-v3 migration already frozen in Design 37.

## 1. Review finding — P11-ISSUE-146

Candidate 35e2b70 correctly implements strict history validation, immutable
source-node replay, Raw Fact/source semantic binding, and versioned validation-v3
storage.

However, the runtime still determines `parsed_available` through
`_current_reusable_sec_artifacts()`, which requires a current reusable
validation artifact. When a compatible V6 / artifacts-v2 parsed artifact exists
but only legacy validation-v2 exists, current v3 loading fails, the parsed
artifact is treated as unavailable, and the planner selects `PARSE_LOCAL`.
The normal ingest path then reruns `parse_sec_package()`.

That violates Design 37:

```text
compatible V6/v2 parsed artifact exists
+
current validation-v3 absent
+
legacy validation-v2 may exist

→ REUSE_DATA denied
→ parser must NOT rerun solely because validation is old
→ P7 validation-v3 must execute against the existing parsed artifact
```

The same gap exists in `reuse_sec_package()`: it attempts to load an existing
current validation artifact before executing fresh revalidation, so it cannot
serve as the migration path when v3 is absent.

This defect is:

```text
P11-ISSUE-146
VALIDATION-V3 REVALIDATION STATE IS MISSING FROM THE INCREMENTAL PLANNER
```

## 2. Corrected Layer-B planner state machine

Design 38 supersedes Design 26 §24 Layer B where validation-v3 migration
requires an additional state.

After the mandatory fresh current discovery gate establishes one unambiguous
selected accession, evaluate the selected immutable package, compatible parsed
artifact, and current validation-v3 separately.

The authoritative states are:

```text
current compatible parsed artifact
+
current valid v3 validation artifact
+
v3 reuse_eligible
→ REUSE_DATA

current compatible parsed artifact
+
current v3 absent
→ REVALIDATE_LOCAL

current compatible parsed artifact
+
current valid v3 exists
+
v3 is not reuse_eligible
→ REVALIDATE_LOCAL

no compatible parsed artifact
+
matching immutable local SEC package exists
→ PARSE_LOCAL

no matching local package
→ DISCOVER_AND_ACQUIRE
```

Add the exact planner action:

```text
REVALIDATE_LOCAL
```

to `SecPlanAction`.

This action is additive. It does not change persisted parser/artifact schemas,
Registry schema, or validation schema.

## 3. Corrupt current-v3 rule

A current versioned v3 directory is authoritative when present.

If the current v3 path exists but `load_sec_validation()` fails its current
schema/hash/path/integrity checks:

```text
FAIL CLOSED
DO NOT fall back to validation-v2
DO NOT silently treat the corrupt v3 as merely absent
DO NOT silently overwrite it through migration
```

Return the current validation integrity error for review/repair.

`REVALIDATE_LOCAL` is for a current v3 that is absent, or for a valid current
v3 that is intentionally not reuse-eligible and must be refreshed against the
fresh discovery observation. It is not a corruption-recovery bypass.

## 4. Compatible parsed artifact discovery

Planner code must distinguish:

```text
compatible parsed artifact available
```

from:

```text
research-ready current validation available
```

A compatible parsed artifact candidate is determined by:

- selected package SHA equality;
- `VIRTUAL_HTML_NORMALIZER_VERSION = VIRTUAL_HTML_V6`;
- `SEC_ARTIFACT_SCHEMA = p11-sec-artifacts-v2`;
- Registry artifact path resolves;
- `load_sec_artifacts()` succeeds;
- loaded parsed package SHA equals the selected immutable package SHA.

Current validation status is not part of parsed-artifact compatibility.

Do not require Registry `validation_status=PASS` merely to load a compatible
parsed artifact for P7 revalidation.

## 5. REUSE_DATA semantics

`REUSE_DATA` remains stronger than parsed-artifact compatibility.

It requires:

- compatible parsed artifact;
- current versioned validation-v3 artifact present;
- current v3 loads successfully;
- package/path identity matches;
- `validation_status=PASS`;
- `compatibility_status=COMPATIBLE`;
- `blocking_issue_count=0`;
- `reuse_eligible=true`.

The fresh online discovery observation still requires current P7 binding
refresh before final research-ready publication, as already frozen.

## 6. REVALIDATE_LOCAL execution

For `REVALIDATE_LOCAL`:

1. use the selected immutable local package;
2. load the compatible V6/v2 parsed artifact;
3. do not call `parse_sec_package()`;
4. register the fresh discovery observation;
5. verify package/parsed identity;
6. execute `validate_sec_artifacts()` directly using the fresh discovery
   observation and current Registry;
7. write only the schema-versioned validation-v3 artifact;
8. preserve legacy flat validation-v2 bytes;
9. update Registry current parsed-run validation fields from the new v3 result;
10. update the slot binding and P8 catalog using the new v3 result;
11. compute `research_ready` from the new v3 result and current discovery.

Implementation may introduce a dedicated helper such as
`revalidate_sec_package()`. The exact helper name is not a public contract.

## 7. Registry refresh requirement

After any current v3 validation execution against an existing parsed artifact,
including REVALIDATE_LOCAL and the fresh-discovery refresh used by REUSE_DATA,
the SEC parsed-run Registry row must be updated with the current validation
result:

```text
validation_status
compatibility_status
blocking_issue_count
artifact_path = parsed artifact path
```

The parse-run identity remains derived from the existing package/parser identity.
No new parse run is fabricated merely because P7 reran.

`SEC_REGISTRY_SCHEMA_VERSION = 4` remains unchanged.

## 8. CLI / planner output

The production CLI may expose:

```text
planner_action = REVALIDATE_LOCAL
```

for this migration/refresh state.

This is an additive planner value and accurately distinguishes validation-only
work from `PARSE_LOCAL`.

No caller may report `REUSE_DATA` before current v3 eligibility is established.

## 9. Required development tests

Add deterministic tests proving:

### Planner

```text
compatible V6/v2 parsed + current reusable v3
→ REUSE_DATA

compatible V6/v2 parsed + v3 absent + optional legacy flat v2
→ REVALIDATE_LOCAL

compatible V6/v2 parsed + valid v3 not reuse_eligible
→ REVALIDATE_LOCAL

no compatible parsed + local raw package
→ PARSE_LOCAL

no local package
→ DISCOVER_AND_ACQUIRE
```

### Migration execution

```text
REVALIDATE_LOCAL
→ parser invocation count = 0
→ parsed artifact bytes unchanged
→ raw package bytes unchanged
→ legacy v2 bytes unchanged
→ validation-v3 executes
→ v3 path is versioned
→ Registry validation fields reflect v3
→ catalog/research_ready derive from v3
```

### Corrupt v3

```text
compatible parsed + corrupt current v3 + valid legacy v2
→ fail closed
→ no v2 fallback
→ parser invocation count = 0
→ no automatic overwrite of corrupt v3
```

### Fresh REUSE_DATA refresh

For an existing current reusable v3 plus fresh discovery:

```text
parser invocation count = 0
P7 current v3 refresh executes as required
Registry validation fields are refreshed from the new v3 result
```

## 10. Version contract

Unchanged:

```text
SEC_DISCOVERY_SCHEMA = p11-sec-discovery-v1
VIRTUAL_HTML_NORMALIZER_VERSION = VIRTUAL_HTML_V6
SEC_ARTIFACT_SCHEMA = p11-sec-artifacts-v2
SEC_VALIDATION_SCHEMA = p11-sec-validation-v3
SEC_REGISTRY_SCHEMA_VERSION = 4
```

No new reason code is required.

## 11. Governance state

```text
ISSUE-140 = FIXED
ISSUE-141 = FIXED
ISSUE-142 = FIXED
ISSUE-143 = FIXED
ISSUE-144 = GOVERNANCE CORRECTED
ISSUE-145 = FIXED
ISSUE-146 = DESIGN FROZEN / IMPLEMENTATION REQUIRED

FRESH FULL EXACT-CANDIDATE REVIEW:
CHANGES_REQUIRED

FORMAL TEST PLAN:
NOT AUTHORIZED

FORMAL ACCEPTANCE:
NOT RUN

MAIN MERGE:
NOT AUTHORIZED

P11 DONE:
NO
```
