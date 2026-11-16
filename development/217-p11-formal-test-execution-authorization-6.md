# 217 — P11 Formal Test Execution Authorization 6

Status: **FORMAL_TEST_EXECUTION_AUTHORIZED**

Agent role: **Acceptance/Test Agent**

This authorization is for Formal Test execution only.

The agent is not a Development Agent for this task.

Do not modify production/test code, redesign P11, create a replacement
candidate, merge main, declare Formal Acceptance, or declare P11 DONE.

## 1. Exact authority

Repository:

`projectforkk/FinancialFilingDataFoundation`

Authoritative lineage:

`reconcile/p11-140-143-local-chain`

Design 40:

`db8edabb2630549e2d75a5becaccb15cb1c53749`

Frozen production candidate:

`7aac34e763b4c9caac24489eb049aa3dc6efb026`

Development evidence:

`2c68f85199e6e77dc30c37e5e6eb5515b5bd6fe2`

Fresh Full Exact-Candidate Review 9:

`development/215-p11-fresh-full-exact-candidate-review-9.md = REVIEW_PASS`

Review commit:

`5fe0bc139f9a2b0475a1912c65f40008e84572f4`

Formal Test Plan 6:

`development/216-p11-formal-test-plan-6.md`

Exact Plan 6 SHA:

`31cf1f04bb5ea56409e1e44230460d9b98060833`

Exact-plan review:

```text
FORMAL_TEST_PLAN_PASS
FORMAL_TEST_EXECUTION_AUTHORIZED
```

Execute Plan 216 exactly.

## 2. Start and Git synchronization

Use:

`D:\Codex\FinancialFilingDataFoundation\worktrees\active\p11-sec-rebuild-development`

Start with:

```powershell
Set-Location 'D:\Codex\FinancialFilingDataFoundation\worktrees\active\p11-sec-rebuild-development'
git status --short
git branch --show-current
git fetch origin
git rev-parse HEAD
git rev-parse origin/reconcile/p11-140-143-local-chain
git log -12 --oneline --decorate
```

Safe fast-forward only.

If local/remote history diverges:

```text
EXECUTION_BLOCKED
REASON: BRANCH_DIVERGENCE
STOP
```

Forbidden:

- rebase;
- reset --hard;
- clean -fd / clean -fdx;
- force / force-with-lease;
- history rewrite.

## 3. Candidate freeze

Before Formal Test:

```powershell
git cat-file -t 7aac34e763b4c9caac24489eb049aa3dc6efb026
git cat-file -t 31cf1f04bb5ea56409e1e44230460d9b98060833
git merge-base --is-ancestor 7aac34e763b4c9caac24489eb049aa3dc6efb026 HEAD
git diff --name-status 7aac34e763b4c9caac24489eb049aa3dc6efb026..HEAD
git status --short
git diff --check
```

All post-candidate tracked changes must be documentation/governance only.

Any source/test/dependency/runtime drift:

```text
EXECUTION_BLOCKED
REASON: PRODUCTION_TEST_DRIFT_AFTER_REVIEW_PASS
STOP
```

## 4. Environment

Recommended:

```text
formal root = D:\ffdf-p11-ft6
pytest temp = D:\t\p11f6
```

`FFDF_P11_US_DEV` must remain absent.

Record only whether SEC contact configuration exists; never record the value.

## 5. Execute FT-00 through FT-24

Execute all gates from Plan 216.

Do not substitute development unit tests for acceptance-only harness gates.

The following are mandatory and cannot be abbreviated.

### ISSUE-147 acceptance correction

FT-02 must independently execute all nine observation-identity cases.

The previous Formal-Test-5 history harness is not sufficient.

### ISSUE-148 source identity

FT-03 through FT-14 must independently prove:

- complete-submission source-container identity;
- exact SGML byte slicing;
- canonical active-content boundary;
- zero archive-index/member/static fetch package construction;
- package-source provenance identity and replay;
- complete tamper matrix;
- legacy/current migration;
- current source conflict semantics;
- Registry v5;
- validation-v4;
- planner current-source eligibility;
- P8/MCP provenance and no-network behavior.

### Apple two-root gate

FT-15 and FT-16 use two independent fresh Apple FY2025 roots.

Require exact equality of:

```text
accession
complete-submission URL
complete-submission SHA
complete-submission length
provenance SHA
selected member set
every member locator semantic field
every member SHA/length
package SHA
```

Any unexplained mismatch is FAIL.

### Network identity

Fresh package construction must record:

```text
complete submission = 1
archive index = 0
individual package member = 0
static/browser asset = 0
```

Direct member diagnostic bytes, if fetched for FT-17, are diagnostics only and
must not affect source/package/provenance identity.

## 6. Production/test repair forbidden

If any required Formal Test assertion fails:

```text
EXECUTION_FAIL
STOP
```

Do not patch `src/`.
Do not patch `tests/`.
Do not alter Design 40.
Do not create a new production candidate.

Return to ChatGPT.

## 7. Formal evidence

If all required gates complete, create exactly:

`development/218-p11-formal-test-evidence-6.md`

The evidence must satisfy every evidence requirement in Plan 216.

It must contain exact FT-00..FT-24 verdicts and enough receipts for independent
ChatGPT verification.

Raw harnesses/logs remain outside Git.

Before committing:

```powershell
git status --short
git diff --check
git diff --name-status 7aac34e763b4c9caac24489eb049aa3dc6efb026..HEAD
```

The evidence commit must be documentation only.

Push normally to:

`origin/reconcile/p11-140-143-local-chain`

## 8. Result classification

Each gate:

`PASS / FAIL / BLOCKED`

Overall:

- assertion failure → `EXECUTION_FAIL`;
- production/test repair required → `EXECUTION_FAIL`;
- external/contact failure → `EXECUTION_BLOCKED`;
- all gates pass → `EXECUTION_PASS`.

Do not declare Formal Acceptance PASS.

## 9. Stop boundary

After evidence push:

```text
STOP FOR CHATGPT INDEPENDENT FORMAL ACCEPTANCE REVIEW 6
```

Do not modify production/test code.
Do not merge main.
Do not declare Formal Acceptance.
Do not declare P11 DONE.
