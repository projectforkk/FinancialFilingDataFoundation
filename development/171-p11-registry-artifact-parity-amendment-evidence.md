# 171 — P11 Registry / Artifact Parity Amendment Evidence — ISSUE-030

Status: **PASS — AMENDED DESIGN READY FOR CANDIDATE FREEZE**

Phase:
P11 — US SEC Provider

Historical reviewed candidate:
`d47a0b5de5c2b3e88a5df629476d05d26e7d83fb`

Review stop:
`development/170-p11-registry-artifact-parity-review-stop.md`

Production remains CLOSED.

## P11-ISSUE-030 resolution

Before any periodic SEC artifact can be reused, the package-aware selector now requires exact parity between the loaded v2 artifact and the accepted P1 `ParsedDataRecord`.

Required equality:

```text
manifest.parser_version == record.parser_version
manifest.schema_version == record.schema_version
manifest.validation_status == validation.status == record.validation_status.value
manifest.blocking_issue_count == len(validation.blocking_issues) == record.blocking_issue_count
validation.compatibility_status == record.compatibility_status.value
```

Classification:

- any parity mismatch => `P11_REUSE_ARTIFACT_INVALID`;
- policy/validation-specific rejection is evaluated only after parity succeeds.

Acceptance now tests every parity field mismatch independently.

## Prior design regression

ISSUE-010..029 remediation remains intact.

Package-aware reuse still requires:

- exact current document SHA;
- exact current source package SHA;
- safe artifact path;
- v2 loader/hash/ID/source-reference integrity;
- exact requested slot identity;
- accepted parser/schema;
- PASS;
- zero blockers;
- COMPATIBLE.

CN/HK planner/reuse semantics remain unchanged.

## Scope

Design/governance only.

No src/tests/integration/runtime-lock change.

## Verdict

# PASS — READY FOR CANDIDATE FREEZE AND FRESH DETACHED DESIGN REVIEW

No production authorization is implied.
