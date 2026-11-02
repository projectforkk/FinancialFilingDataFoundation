# 10 — P1 Code Review

状态：**PASS — READY FOR ACCEPTANCE**

Repository:

\`projectforkk/FinancialFilingDataFoundation\`

Branch:

\`task/p1-identity-registry-planner\`

Reviewed production candidate:

\`03fe9adb691f5d43401fef9ac672bea39f35d26b\`

Production correction chain:

- \`444f3411a9c57b619be839e0088bddee13dd3d93\` — initial P1 implementation
- \`4072642b9cdf0085c418ce9679e886529f1483ff\` — independent source provenance
- \`3fe1b11523d9d38dc9e9d8e3fa0fc8b0f2c464c8\` — structured registry schema blocker
- \`dbc67bda0c00804622e87ce83cdba653d1a366f4\` — local content drift detection

Development amendment evidence:

\`20587f2dc209daf195e7f722de0f030c2f465898\`

---

## 1. Review Isolation

Valid Code Review execution used isolated detached worktree:

\`D:\\Codex\\FinancialFilingDataFoundation-P1FinalReview\`

Frozen reviewed SHA:

\`03fe9adb691f5d43401fef9ac672bea39f35d26b\`

HEAD was checked before and after both the full test group and the independent smoke matrix.

Result:

\`\`\`text
HEAD before = 03fe9adb691f5d43401fef9ac672bea39f35d26b
HEAD after  = 03fe9adb691f5d43401fef9ac672bea39f35d26b
\`\`\`

Earlier review attempts from a shared worktree and from an isolated worktree without a prepared \`workspace/\` parent were explicitly invalidated and are not used as PASS evidence.

---

## 2. Scope Review

PASS.

P1 implementation is limited to:

- identity value objects
- FilingSlotKey / FilingIdentity
- filing policy / required slot generation
- SQLite registry
- document registration
- independent document source provenance
- filing bindings
- parsed-data registry
- explicit PlannerReusePolicy
- deterministic incremental planning
- structured decision reasons

No P2 acquisition implementation was found.

No Dayu adapter or network provider was found.

No table extraction, MCP, Skill or investment-analysis implementation was found.

---

## 3. Identity Review

PASS.

Verified semantics:

- required business slot is \`FilingSlotKey\`;
- \`amended\` does not change required slot key;
- concrete bytes are identified by SHA256;
- filenames are not used as business identity;
- duplicate filing requirements are rejected;
- required filing ordering is deterministic.

No identity guessing path found.

---

## 4. Registry Review

PASS.

Schema:

- SQLite stdlib
- \`PRAGMA user_version = 1\`
- \`documents\`
- \`document_locations\`
- \`document_sources\`
- \`filing_bindings\`
- \`parsed_data\`

Verified invariants:

- content records are SHA-addressed;
- same SHA may have multiple locations;
- historical content records are not deleted to hide a path change;
- source provenance persists independently of filing identity;
- repeated same provenance is idempotent;
- unbound content is not treated as a local filing candidate;
- cross-slot binding conflict is explicit;
- unsupported newer registry schema is rejected rather than downgraded.

\`RegistrySchemaUnsupported.reason_code\`:

\`REGISTRY_SCHEMA_UNSUPPORTED\`

---

## 5. Local Content Drift Review

PASS.

Current local resolution re-hashes an existing bound path and compares current bytes with the registered SHA.

Required behavior verified:

- matching SHA → verified live location;
- changed-in-place SHA → drifted location;
- drifted bytes are not auto-rebound to the old filing identity;
- no verified live copy + drift → \`LocalDocumentStatus.DRIFTED\`;
- planner → \`BLOCKED / LOCAL_CONTENT_DRIFT\`;
- if another same-SHA duplicate remains verified, that verified copy remains usable.

This closes the stale-reuse defect identified in P1-ISSUE-006.

---

## 6. Reuse Policy Review

PASS.

Reuse requires compatible, validated, non-blocking parsed data under explicit \`PlannerReusePolicy\`.

Verified:

- parser version difference alone does not invalidate;
- explicit invalidated parser version blocks reuse;
- incompatible / unknown schema state blocks reuse;
- empty accepted-schema set means no schema is reusable;
- current unique local SHA different from parsed SHA prevents stale reuse;
- multiple distinct reusable parsed SHA without unique active-source evidence produces \`REVIEW_REQUIRED\`;
- same SHA multiple parse runs are selected deterministically.

No implicit "latest parser wins" or "latest file wins" behavior found.

---

## 7. Planner Matrix Review

Independent smoke matrix produced:

\`\`\`text
REUSE    REUSE_DATA         VALIDATED_COMPATIBLE_PARSED_DATA
LOCAL    PARSE_LOCAL        LOCAL_RAW_AVAILABLE
DOWNLOAD DOWNLOAD_AND_PARSE NO_REUSABLE_DATA_OR_LOCAL_RAW
REVIEW   REVIEW_REQUIRED    LOCAL_DOCUMENT_AMBIGUOUS
BLOCKED  BLOCKED            LOCAL_CONTENT_DRIFT
\`\`\`

Additional smoke checks:

\`\`\`text
PROVENANCE 1 cninfo s1
SCHEMA_BLOCKER REGISTRY_SCHEMA_UNSUPPORTED
\`\`\`

PASS.

---

## 8. Tests

Valid isolated review command executed against frozen production candidate.

Result:

\`\`\`text
51 passed in 1.87s
\`\`\`

This includes P1 tests and P0 regression tests.

No test failure remained.

---

## 9. Static / Dependency Review

PASS.

- compileall: PASS
- git diff --check: PASS
- no imports of Dayu
- no httpx / requests / urllib / socket network path
- no Docling
- no Torch
- no OpenAI / Anthropic / Google generative-AI SDK
- no P2 acquisition package
- candidate worktree clean after review

---

## 10. Source Immutability

PASS.

Document registration tests verify source bytes / size / mtime are unchanged.

Local resolver re-hashes for verification but does not rewrite the source file or silently update the registered identity.

---

## 11. Governance Findings

P1-ISSUE-004:

Some unaccepted P1 commits entered \`main\` early. No history rewrite is authorized. Until P1 Independent Acceptance PASS, accepted baseline remains P0 closeout:

\`edff06b2b1138b50d742e92ce8b8df628c6d2c61\`

P1-ISSUE-005 / P1-ISSUE-007:

Review evidence must use fixed-SHA isolated worktree and explicitly prepared ignored workspace. Final valid review complied with these rules.

These governance incidents do not weaken P1 acceptance criteria.

---

## 12. Findings

Blocking findings: **NONE**

Non-blocking observations:

- local resolution intentionally re-hashes bound local candidates for identity safety; performance calibration for large-scale registry scans belongs to a later operational phase, not P1 correctness.
- P1 does not decide acquisition-provider behavior; that remains P2.

---

## 13. Conclusion

**P1-H CODE REVIEW = PASS**

Transition authorized:

\`P1_IN_REVIEW → P1_READY_FOR_ACCEPTANCE\`

Next:

**P1-I — Acceptance Freeze**
