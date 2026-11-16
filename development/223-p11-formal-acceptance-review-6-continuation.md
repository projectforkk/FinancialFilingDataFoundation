# 223 — P11 Independent Formal Acceptance Review 6 — Continuation

Status: **ACCEPTANCE_PASS**

This continuation reviews the targeted Formal Test 6A evidence remediation
against the blockers recorded in
`development/219-p11-formal-acceptance-review-6.md`.

The production candidate remains:

`7aac34e763b4c9caac24489eb049aa3dc6efb026`

No new production candidate was created.

## 1. Exact authority

Repository:

`projectforkk/FinancialFilingDataFoundation`

Authoritative lineage:

`reconcile/p11-140-143-local-chain`

Exact Design 40 freeze:

`db8edabb2630549e2d75a5becaccb15cb1c53749`

Frozen production candidate:

`7aac34e763b4c9caac24489eb049aa3dc6efb026`

Fresh Full Review 9:

`5fe0bc139f9a2b0475a1912c65f40008e84572f4 = REVIEW_PASS`

Formal Test Plan 6:

`31cf1f04bb5ea56409e1e44230460d9b98060833`

Formal Test 6 Authorization:

`4aaa4b8076546f9daa258e1827cd1a61e3eeffbf`

Formal Test 6 Evidence:

`01f60a3568c703a988962badbb1f3c74dd84f112`

Formal Acceptance Review 6 initial result:

`6a021c04d423ce89f1d7c29d1612661906481321 = NOT_PASSED / EVIDENCE_REMEDIATION_REQUIRED`

Formal Test 6A Plan:

`abccc6618614e7f18be93d56eba952c4f28e30ca`

Formal Test 6A Authorization:

`36cc8eb37004b1d99584b5c62e585f934ebbbe5b`

Formal Test 6A Evidence:

`12700179754ffa9aa6d9c88d72d8bf3e56274ee6 = EXECUTION_PASS`

Authorization 6A → Evidence 6A is one documentation-only commit.

## 2. Blocker A remediation — exact Design authority

PASS.

Evidence 6A correctly records:

```text
Design 40 freeze:
db8edabb2630549e2d75a5becaccb15cb1c53749
```

The historical SHA:

`09e3174b7e19a60cc5955862670fac8931af67db`

is explicitly identified as not being the Design 40 baseline.

The exact-authority defect in Evidence 218 is therefore corrected.

## 3. Blocker B remediation — request classification

PASS.

The 6A acceptance harness uses mutually exclusive URL categories in an order
that classifies complete-submission `.txt` URLs before the generic archive
member category.

Every captured request receives exactly one category.

### Apple FY2025 Q3

Chronological product requests:

```text
1 TICKER_MAP
2 CURRENT_SUBMISSIONS
3 COMPLETE_SUBMISSION
4 TICKER_MAP
5 CURRENT_SUBMISSIONS
```

Totals:

```text
TICKER_MAP                = 2
CURRENT_SUBMISSIONS       = 2
HISTORY_SUBMISSIONS       = 0
COMPLETE_SUBMISSION       = 1
INDIVIDUAL_ARCHIVE_MEMBER = 0
ARCHIVE_INDEX             = 0
STATIC_OR_BROWSER_ASSET   = 0
OTHER_SEC                 = 0
```

No individual `.htm`, `.xml`, `.xsd` or linkbase URL was requested.

### Toyota FY2025 20-F

Chronological product requests:

```text
6  TICKER_MAP
7  CURRENT_SUBMISSIONS
8  COMPLETE_SUBMISSION
9  TICKER_MAP
10 CURRENT_SUBMISSIONS
```

Totals:

```text
TICKER_MAP                = 2
CURRENT_SUBMISSIONS       = 2
HISTORY_SUBMISSIONS       = 0
COMPLETE_SUBMISSION       = 1
INDIVIDUAL_ARCHIVE_MEMBER = 0
ARCHIVE_INDEX             = 0
STATIC_OR_BROWSER_ASSET   = 0
OTHER_SEC                 = 0
```

Again, no individual package-member URL was requested.

## 4. Evidence-218 reconciliation

PASS.

The earlier Formal Test 6 harness used:

```text
if path starts with /Archives/ and ends with /index.json:
    archive_index
else if path starts with /Archives/:
    archive_member
```

It had no earlier complete-submission category.

Therefore the exact complete-submission `.txt` request was counted as
`archive member = 1`.

Evidence 6A proves this was:

```text
CLASSIFICATION_ERROR
```

and not:

```text
REAL_PRODUCT_MEMBER_FETCH
```

No production repair is required.

## 5. Identity preservation across remediation

PASS.

Apple Q3 6A reproduces the exact Formal Test 6 identities:

```text
accession:
0000320193-25-000073

source-container SHA:
83a65bbe8d3ab67e4f35769cbb56c46eb0b557c2b0890b940b2d76e59548ad87

package SHA:
194e409b107b8a9014d8d796396f66d602cbdee90ae1bd7681830a960f55cb9a

provenance SHA:
1136c59e7b4495f3fae68c73fe1d9ca624c2f5efeb8c468deb1212671aabd285
```

Toyota 6A also reproduces the exact Formal Test 6 identities:

```text
accession:
0001193125-25-142326

source-container SHA:
b1564b0cd42563fec3fe0fa838b57f3c1c01bb01a48ee445104f211f098ea7e0

package SHA:
8195c504b7aa9c1ce981dfafd39c73bd799029b6ad14da32855ba7ea3b762e4b

provenance SHA:
f02b070a4e59e621db58e388a31c8209c8c6ccf59f5389be4ee6888c6a4ef9f1
```

Both remain:

```text
validation-v4 = PASS
compatibility = COMPATIBLE
blocking = 0
reuse_eligible = true
research_ready = true
P8/MCP SEC network calls = 0
```

The targeted rerun therefore changes no source/package/provenance semantics.

## 6. Post-candidate drift

PASS.

Independent Git review confirms candidate
`7aac34e763b4c9caac24489eb049aa3dc6efb026`
through Evidence 6A contains only documentation/governance changes after the
candidate.

No post-candidate path under:

- `src/`;
- `tests/`;
- dependency lock/configuration;
- runtime production configuration

is changed.

## 7. Formal Test 6 final acceptance aggregation

The independent review now accepts:

- the Formal Test 6 gates previously accepted in Review 219;
- the complete ISSUE-147 nine-case acceptance-only matrix;
- Design-40 complete-submission source identity;
- SGML deterministic byte slicing;
- package-source provenance and replay;
- Registry v5;
- validation-v4;
- legacy/current migration;
- planner current-source eligibility;
- P8/MCP no-network;
- Apple FY2025 root A/root B exact identity equality;
- direct-member diagnostic isolation;
- Apple Q3;
- Toyota 20-F and 6-K guard;
- Kellanova amendment conflict;
- ISSUE-142/143/145/146 regression;
- CN/HK and P0-P10 preservation;
- corrected Q3/Toyota URL-level request classification.

There are no remaining Formal Test 6 evidence blockers.

## 8. Final verdict

```text
FORMAL TEST 6:
EXECUTION_PASS

FORMAL TEST 6A:
EXECUTION_PASS

INDEPENDENT FORMAL ACCEPTANCE REVIEW 6:
ACCEPTANCE_PASS

PRODUCTION CANDIDATE:
7aac34e763b4c9caac24489eb049aa3dc6efb026

ISSUE-140..148:
FIXED / REGRESSION PRESERVATION

P0-P10:
ACCEPTED BASELINE PRESERVED

P11 US SEC PROVIDER:
FORMALLY ACCEPTED

MAIN MERGE:
NOT YET AUTHORIZED IN THIS COMMIT

P11 DONE:
NO
```

The next lifecycle action is a separate exact main-merge readiness review and
main-merge authorization.

P11 becomes DONE only after the authorized merge to main and closeout record
are independently verified.
