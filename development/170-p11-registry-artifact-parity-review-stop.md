# 170 — P11 Reuse-API Final Design Review Stop — Registry / Artifact Metadata Parity

Status: **FAIL / STOP — P11-ISSUE-030 / PRODUCTION CLOSED**

Phase:
P11 — US SEC Provider

Reviewed exact candidate:
`d47a0b5de5c2b3e88a5df629476d05d26e7d83fb`

Fresh detached review:
`D:\\Codex\\FinancialFilingDataFoundation\\worktrees\\review\\p11-design-d47a0b5`

Automated ISSUE-010..029 contract matrix:
`PASS`

## Finding

Manual comparison against accepted P1 `ParsedDataRecord` found one remaining package-aware reuse ambiguity.

The accepted registry row stores:

- parse_run_id;
- document_sha256;
- parser_version;
- schema_version;
- validation_status;
- blocking_issue_count;
- compatibility_status;
- artifact_path.

The P11 selector design already verifies:

- loaded parse_run_id == registry parse_run_id;
- loaded/current/record document SHA agree;
- loaded package SHA == current package SHA;
- loaded slot == requested slot;
- loaded validation/reuse gates.

But it does not explicitly require the loaded v2 artifact metadata to equal the registry record for:

- parser_version;
- schema_version;
- validation_status;
- blocking_issue_count;
- compatibility_status.

Therefore an inconsistent/stale/corrupted registry row could disagree with the artifact while both individually appear policy-acceptable.

## P11-ISSUE-030 — registry/artifact metadata parity

Required correction:

Before a P11 periodic candidate can be reusable, the selector MUST verify exact parity:

```text
loaded manifest.parser_version == ParsedDataRecord.parser_version
loaded manifest.schema_version == ParsedDataRecord.schema_version
loaded validation.status == ParsedDataRecord.validation_status
loaded validation.blocking_issue_count == ParsedDataRecord.blocking_issue_count
loaded validation.compatibility_status == ParsedDataRecord.compatibility_status
```

Then and only then apply the reuse policy to the verified loaded/record values.

Any parity mismatch:

`P11_REUSE_ARTIFACT_INVALID`

No weaker validation-specific reason is used for metadata disagreement because the registry/artifact binding itself is invalid.

Acceptance must prove mismatch for each field independently returns PARSE_CURRENT_PACKAGE with P11_REUSE_ARTIFACT_INVALID.

Existing exact-package, package-change, path, validation, parser and schema rejection rules remain unchanged after parity succeeds.

## Scope

No production/test/runtime changes.

ISSUE-010..029 remediation remains valid.

## Verdict

# FAIL / STOP

Candidate `d47a0b5...` is INELIGIBLE for DESIGN READY.

P11 production remains CLOSED.
