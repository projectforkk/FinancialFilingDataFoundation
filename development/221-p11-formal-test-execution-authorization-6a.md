# 221 — P11 Targeted Formal Test 6A Execution Authorization

Status: **FORMAL_TEST_EXECUTION_AUTHORIZED**

Agent role: **Acceptance/Test Agent**

This authorization is limited to the evidence-remediation plan in
`development/220-p11-formal-test-plan-6a-evidence-remediation.md`.

It does not reopen development.

## 1. Exact authority

Repository:

`projectforkk/FinancialFilingDataFoundation`

Authoritative lineage:

`reconcile/p11-140-143-local-chain`

Design 40 freeze:

`db8edabb2630549e2d75a5becaccb15cb1c53749`

Frozen production candidate:

`7aac34e763b4c9caac24489eb049aa3dc6efb026`

Review 9:

`5fe0bc139f9a2b0475a1912c65f40008e84572f4`

Formal Test Plan 6:

`31cf1f04bb5ea56409e1e44230460d9b98060833`

Formal Test 6 evidence:

`01f60a3568c703a988962badbb1f3c74dd84f112`

Formal Acceptance Review 6:

`6a021c04d423ce89f1d7c29d1612661906481321 = NOT_PASSED / EVIDENCE_REMEDIATION_REQUIRED`

Formal Test 6A plan:

`abccc6618614e7f18be93d56eba952c4f28e30ca`

Execute Plan 220 exactly.

## 2. Candidate freeze

Before execution:

```powershell
git status --short
git fetch origin
git rev-parse HEAD
git rev-parse origin/reconcile/p11-140-143-local-chain
git merge-base --is-ancestor 7aac34e763b4c9caac24489eb049aa3dc6efb026 HEAD
git diff --name-status 7aac34e763b4c9caac24489eb049aa3dc6efb026..HEAD
git diff --check
```

Every post-candidate tracked path must remain documentation/governance only.

Any source/test/dependency/runtime change:

```text
EXECUTION_BLOCKED
STOP
```

## 3. Required targeted execution

Execute only:

- FT6A-00 authority-SHA correction;
- FT6A-01 Apple FY2025 Q3 fresh-root URL-level rerun;
- FT6A-02 Toyota FY2025 20-F fresh-root URL-level rerun;
- FT6A-03 explicit reconciliation of Evidence-218 `archive member = 1`.

Do not rerun unrelated Formal Test gates unless needed to validate one of these
receipts.

## 4. Request capture

The acceptance harness must capture the exact chronological URL of every SEC
request.

Each request receives exactly one mutually exclusive category:

```text
TICKER_MAP
CURRENT_SUBMISSIONS
HISTORY_SUBMISSIONS
COMPLETE_SUBMISSION
INDIVIDUAL_ARCHIVE_MEMBER
ARCHIVE_INDEX
STATIC_OR_BROWSER_ASSET
OTHER_SEC
```

The complete-submission `.txt` URL must be classified only as
`COMPLETE_SUBMISSION`.

It must not also count as `INDIVIDUAL_ARCHIVE_MEMBER`.

## 5. Pass/fail boundary

For both Q3 and Toyota normal product acquire/ingest:

```text
INDIVIDUAL_ARCHIVE_MEMBER = 0
ARCHIVE_INDEX = 0
STATIC_OR_BROWSER_ASSET = 0
```

If an actual individual archive-member URL is requested by product execution:

```text
EXECUTION_FAIL
STOP
RETURN TO CHATGPT
```

Do not patch production/test code.

If zero actual member requests are proven, explicitly identify why Evidence
218 previously recorded `archive member = 1`.

## 6. Formal evidence

On PASS create exactly:

`development/222-p11-formal-test-evidence-6a.md`

Evidence must include:

- all exact authority SHAs;
- chronological URL receipts for Apple Q3;
- chronological URL receipts for Toyota;
- one final category for every request;
- category totals;
- package/source/provenance/validation identities;
- explicit old-count reconciliation;
- final documentation-only drift proof.

The evidence commit must be documentation only and pushed by normal
fast-forward.

## 7. Stop boundary

After evidence push:

```text
STOP FOR CHATGPT FORMAL ACCEPTANCE REVIEW 6 CONTINUATION
```

Do not modify production/test code.
Do not create a new candidate.
Do not merge main.
Do not declare Formal Acceptance.
Do not declare P11 DONE.
