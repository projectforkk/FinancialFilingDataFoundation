# 219 — P11 Independent Formal Acceptance Review 6

Status: **FORMAL_ACCEPTANCE_NOT_PASSED / EVIDENCE_REMEDIATION_REQUIRED**

This is the independent ChatGPT review of Formal Test Execution 6 evidence.

The Acceptance/Test Agent reported `EXECUTION_PASS`.

The production candidate is not rejected by this review. No new production
defect has been established. However, the Formal evidence contains two exact
integrity conflicts that prevent Formal Acceptance PASS.

## 1. Exact authority

Repository:

`projectforkk/FinancialFilingDataFoundation`

Authoritative lineage:

`reconcile/p11-140-143-local-chain`

Design 40 exact freeze:

`db8edabb2630549e2d75a5becaccb15cb1c53749`

Production candidate:

`7aac34e763b4c9caac24489eb049aa3dc6efb026`

Fresh Full Review 9:

`5fe0bc139f9a2b0475a1912c65f40008e84572f4 = REVIEW_PASS`

Formal Test Plan 6:

`31cf1f04bb5ea56409e1e44230460d9b98060833`

Formal Test Execution Authorization 6:

`4aaa4b8076546f9daa258e1827cd1a61e3eeffbf`

Formal Test Evidence 6:

`development/218-p11-formal-test-evidence-6.md`

Evidence commit:

`01f60a3568c703a988962badbb1f3c74dd84f112`

Authorization → evidence is one documentation-only commit.

No source/test/dependency/runtime file changed during Formal Test 6.

## 2. Evidence accepted by this review

The following Formal Test 6 evidence is accepted:

- FT-00 candidate freeze/drift boundary;
- FT-01 deterministic regression;
- FT-02 complete ISSUE-147 nine-case acceptance-only matrix;
- FT-03 complete-submission source-container identity;
- FT-04 SGML inventory and exact byte slicing;
- FT-05 active-content rejection;
- FT-06 complete-submission-only package construction;
- FT-07 package-source provenance identity/replay;
- FT-08 20-case provenance/package/member tamper matrix;
- FT-09 legacy/current migration;
- FT-10 source conflict semantics;
- FT-11 Registry v5 migration;
- FT-12 validation-v4/no-v3-fallback;
- FT-13 planner/current-source eligibility;
- FT-14 P8/MCP provenance/no-network;
- FT-15/FT-16 Apple two-root complete-submission/package/provenance equality;
- FT-17 direct-member diagnostic isolation;
- FT-18 online repeat REUSE_DATA;
- FT-21 Kellanova amendment conflict;
- FT-22 ISSUE-142/143/145/146 acceptance regression;
- FT-23 P0-P10 and CN/HK preservation;
- FT-24 documentation-only drift boundary.

In particular, the previous Formal-Test-5 FT-02 gap is corrected: all nine
ISSUE-147 acceptance cases are now independently evidenced.

## 3. Blocker A — incorrect exact Design baseline SHA in Formal evidence

Evidence 218 records:

```text
Corrected Design Baseline:
09e3174b7e19a60cc5955862670fac8931af67db
```

That SHA is not the Design 40 freeze.

It is historical commit:

```text
09e3174b7e19a60cc5955862670fac8931af67db
design: remove superseded P11 exit contract
```

Git ancestry confirms it is an ancestor of the actual Design 40 freeze.

The exact frozen Design 40 baseline used by Review 9, Plan 6 and Authorization
6 is:

```text
db8edabb2630549e2d75a5becaccb15cb1c53749
```

Formal Test evidence is required to state the exact authority SHAs correctly.

Therefore the Evidence-218 authority header is not acceptable as an exact-SHA
acceptance receipt.

This is an evidence/governance defect, not a production-code defect.

## 4. Blocker B — FT-19 and FT-20 contradict the frozen no-member-fetch gate

Plan 216 requires current package construction for Apple Q3 and Toyota 20-F to
use complete-submission bytes and no individual archive-member fetch.

Evidence 218 records:

### FT-19 Apple Q3

```text
complete submission = 1
archive index = 0
archive member = 1
other/static = 0
```

### FT-20 Toyota FY2025

```text
complete submission = 1
archive index = 0
archive member = 1
other/static = 0
```

Those values contradict the frozen Plan-6 requirement.

They also conflict with:

- candidate code review;
- FT-06 acceptance transport;
- FT-15/FT-16 Apple FY request receipts;
- development smoke evidence.

The reviewed candidate acquisition implementation has network fetch sites for:

- current submissions;
- selected submissions history chunks;
- one complete-submission text source.

It constructs `archive_member_url(...)` only as a logical/public URL and does
not fetch those individual member URLs for package construction.

Therefore this independent review does **not** conclude that ISSUE-148 has
regressed.

The most likely remaining possibilities are:

1. FT-19/FT-20 harness URL classification is not mutually exclusive; or
2. an acceptance harness or diagnostic made an extra member request; or
3. an unexpected runtime path made a real member request.

Formal Acceptance cannot choose among those possibilities without URL-level
receipts.

## 5. Required remediation

Do not create a new production candidate.

Do not modify `src/` or `tests/`.

Use the same frozen candidate:

`7aac34e763b4c9caac24489eb049aa3dc6efb026`

A targeted Formal Test 6A must:

1. re-verify the exact authority chain and state Design 40 SHA correctly;
2. rerun Apple FY2025 Q3 from a fresh root;
3. rerun Toyota FY2025 20-F from a fresh root;
4. capture every actual SEC HTTP request URL in chronological order;
5. classify each request using mutually exclusive categories;
6. prove whether any individual archive-member URL was actually requested;
7. preserve complete-submission/package/provenance/validation identities;
8. make no production/test changes.

Required mutually exclusive categories:

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

The complete-submission `.txt` URL must never simultaneously count as an
individual archive member.

Expected current package construction:

```text
INDIVIDUAL_ARCHIVE_MEMBER = 0
ARCHIVE_INDEX = 0
STATIC_OR_BROWSER_ASSET = 0
```

If an actual individual member request occurs, Formal Test 6A is
`EXECUTION_FAIL` and the candidate must return to development review.

If the previous value was only a harness classification error and URL-level
receipts prove zero actual member fetches, corrected supplemental evidence may
resolve this acceptance blocker without a new candidate.

## 6. Candidate status

```text
PRODUCTION CANDIDATE 7aac34e7:
REVIEW_PASS REMAINS VALID

ISSUE-148:
NO NEW PRODUCTION DEFECT ESTABLISHED

DEVELOPMENT:
NOT REOPENED

FORMAL TEST EXECUTOR RESULT 6:
EXECUTION_PASS AS REPORTED

INDEPENDENT FORMAL ACCEPTANCE REVIEW 6:
NOT_PASSED

REASON:
EVIDENCE INTEGRITY / REQUEST-CLASSIFICATION REMEDIATION REQUIRED

MAIN MERGE:
NOT AUTHORIZED

P11 DONE:
NO
```
