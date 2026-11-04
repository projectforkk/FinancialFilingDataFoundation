# 164 — P11 Final Design Review Stop — Package-Aware Reuse

Status: **FAIL / STOP — P11-ISSUE-027 / PRODUCTION CLOSED**

Phase:
P11 — US SEC Provider

Reviewed exact candidate:
`dff1e390f0a8825c75abb15cfb10c41543c676d5`

Fresh detached review:
`D:\\Codex\\FinancialFilingDataFoundation\\worktrees\\review\\p11-design-dff1e39`

Automated ISSUE-010..026 contract matrix:
`PASS`

## Finding

Manual review of the accepted P1 registry/planner found that current reuse is document-SHA oriented, not SEC-package aware.

Current accepted behavior:

- `ParsedDataRecord` stores document_sha256, parser/schema/validation fields and artifact_path;
- it does not store source_package_sha256;
- `IncrementalPlanner` lists parsed records by slot;
- when local raw is resolved, it filters by document_sha256;
- multiple reusable runs for one document SHA are deterministically reduced to the first parse_run_id.

P11 source truth is stricter:

- `parse_run_id` includes source_package_sha256;
- a filing package can change while primary document bytes/document_sha256 remain unchanged;
- index.json or filing-local XBRL/schema/linkbase assets can drift independently of primary bytes.

Therefore generic document-SHA reuse can select a stale P11 parsed artifact for the wrong source package.

## P11-ISSUE-027 — package-aware periodic reuse

Required correction:

1. P11 v1 MUST NOT use generic `IncrementalPlanner.build_plan` for US parsed-data reuse.

2. Adding US to `CompanyRef` requires a safety guard:
   generic IncrementalPlanner rejects `market=US` with explicit `P11_PACKAGE_AWARE_PLANNER_REQUIRED` rather than silently applying document-SHA-only reuse.

3. P11-K introduces a package-aware SEC reuse selector/orchestrator.

Inputs:

- confirmed FilingSlotKey;
- current document_sha256;
- current source_package_sha256;
- accepted parser/schema/reuse policy.

4. The selector may use existing `registry.list_parsed_data(slot)`, but a record is reusable only after loading its v2 artifact from `artifact_path` and verifying:

- artifact_path exists and remains inside configured project/P11 parsed root;
- manifest/document load successfully under v2 loader;
- manifest.source_package_sha256 == current source_package_sha256;
- manifest/document document_sha256 == current document_sha256;
- parse_run_id == loaded manifest parse_run_id;
- parser/schema versions accepted;
- validation_status == PASS;
- blocking_issue_count == 0;
- compatibility_status == COMPATIBLE.

5. Missing/invalid artifact_path is never silently reusable.

6. Same primary document SHA + different package SHA => explicit source-package change / parse required, not REUSE_DATA.

7. Multiple reusable records for the exact same package are selected deterministically by parse_run_id only after all exact-package checks pass.

8. Existing CN/HK IncrementalPlanner behavior remains unchanged.

9. P11 v1 does not require a registry schema migration solely for package-aware reuse; package identity is verified from the registered v2 artifact manifest.

Acceptance must prove:

- same document SHA + package A parsed + current package B => no reuse;
- exact package A => reuse allowed when all validation/reuse gates pass;
- artifact_path missing/outside root/invalid => no reuse;
- manifest package/document/parse_run mismatch => no reuse;
- generic IncrementalPlanner US call is explicitly blocked;
- CN/HK planner regressions unchanged.

## Scope

No production/test/runtime changes were made during review.

ISSUE-010..026 remediation remains valid.

## Verdict

# FAIL / STOP

Candidate `dff1e390f0a8825c75abb15cfb10c41543c676d5` is INELIGIBLE for DESIGN READY.

P11 production remains CLOSED.
