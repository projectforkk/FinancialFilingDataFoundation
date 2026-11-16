# 220 — P11 Targeted Formal Test Plan 6A — Evidence Remediation

Status: **FORMAL_TEST_PLAN_FROZEN / EXECUTION_NOT_YET_AUTHORIZED**

This is a targeted supplemental Formal Test plan.

It does not reopen development and does not replace Formal Test Plan 6.

Its only purpose is to resolve the two evidence-integrity blockers identified
by Independent Formal Acceptance Review 6.

## 1. Exact authority

Repository:

`projectforkk/FinancialFilingDataFoundation`

Authoritative lineage:

`reconcile/p11-140-143-local-chain`

Exact Design 40 freeze:

`db8edabb2630549e2d75a5becaccb15cb1c53749`

Frozen production candidate:

`7aac34e763b4c9caac24489eb049aa3dc6efb026`

Review 9:

`5fe0bc139f9a2b0475a1912c65f40008e84572f4 = REVIEW_PASS`

Formal Test Plan 6:

`31cf1f04bb5ea56409e1e44230460d9b98060833`

Formal Test Execution Authorization 6:

`4aaa4b8076546f9daa258e1827cd1a61e3eeffbf`

Formal Test Evidence 6:

`01f60a3568c703a988962badbb1f3c74dd84f112`

Independent Formal Acceptance Review 6:

`development/219-p11-formal-acceptance-review-6.md = NOT_PASSED / EVIDENCE_REMEDIATION_REQUIRED`

Review commit:

`6a021c04d423ce89f1d7c29d1612661906481321`

## 2. Candidate freeze

No production/test change is permitted.

Before execution prove:

```text
candidate = 7aac34e763b4c9caac24489eb049aa3dc6efb026
candidate is ancestor of HEAD
post-candidate tracked changes are documentation/governance only
worktree clean
git diff --check = PASS
FFDF_P11_US_DEV = ABSENT
```

If source/test/dependency/runtime drift exists:

```text
EXECUTION_BLOCKED
STOP
```

## 3. FT6A-00 — authority-SHA correction

The supplemental evidence must state the exact authority chain correctly.

Required:

```text
DESIGN 40 FREEZE:
db8edabb2630549e2d75a5becaccb15cb1c53749

PRODUCTION CANDIDATE:
7aac34e763b4c9caac24489eb049aa3dc6efb026

REVIEW 9:
5fe0bc139f9a2b0475a1912c65f40008e84572f4

FORMAL TEST PLAN 6:
31cf1f04bb5ea56409e1e44230460d9b98060833

FORMAL TEST 6 AUTHORIZATION:
4aaa4b8076546f9daa258e1827cd1a61e3eeffbf

FORMAL TEST 6 EVIDENCE:
01f60a3568c703a988962badbb1f3c74dd84f112

FORMAL ACCEPTANCE REVIEW 6:
6a021c04d423ce89f1d7c29d1612661906481321
```

The historical SHA:

`09e3174b7e19a60cc5955862670fac8931af67db`

must not be described as the corrected Design 40 baseline.

## 4. Mutually exclusive request classifier

Use an acceptance-only transport/harness whose request categories are mutually
exclusive.

Classification order must prevent a complete-submission `.txt` URL from also
counting as an individual archive member.

Required categories:

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

For every request, persist/record:

- chronological sequence number;
- HTTP method;
- exact URL;
- final category;
- response status or controlled failure;
- whether the request was made by acquire, ingest, status, P8/MCP, or harness
  diagnostic.

Every URL must have exactly one category.

## 5. FT6A-01 — Apple FY2025 Q3 fresh-root rerun

Use a brand-new empty root.

Target:

```text
ticker = AAPL
CIK = 0000320193
year = 2025
period = Q3
expected accession = 0000320193-25-000073
```

Run normal production acquire + ingest with `FFDF_P11_US_DEV` absent.

Record every SEC request URL.

Required package-construction classification:

```text
COMPLETE_SUBMISSION = 1
INDIVIDUAL_ARCHIVE_MEMBER = 0
ARCHIVE_INDEX = 0
STATIC_OR_BROWSER_ASSET = 0
```

Ticker/submissions counts must correspond exactly to the number of online
ticker/discovery invocations.

Also record and verify:

- complete-submission URL/SHA/length;
- provenance SHA;
- package SHA;
- selected member names/SHA/length;
- validation-v4 PASS/COMPATIBLE/blocking=0;
- research_ready=true;
- P8/MCP network calls=0.

If an actual individual archive-member request occurs:

```text
EXECUTION_FAIL
STOP
```

## 6. FT6A-02 — Toyota FY2025 20-F fresh-root rerun

Use another brand-new empty root.

Target:

```text
ticker = TM
CIK = 0001094517
year = 2025
period = FY
expected accession = 0001193125-25-142326
```

Run normal production acquire + ingest with `FFDF_P11_US_DEV` absent.

Record every SEC request URL.

Required package-construction classification:

```text
COMPLETE_SUBMISSION = 1
INDIVIDUAL_ARCHIVE_MEMBER = 0
ARCHIVE_INDEX = 0
STATIC_OR_BROWSER_ASSET = 0
```

Also record:

- complete-submission URL/SHA/length;
- provenance SHA;
- package SHA;
- selected member names/SHA/length;
- validation-v4 PASS/COMPATIBLE/blocking=0;
- research_ready=true;
- P8/MCP network calls=0.

If an actual individual archive-member request occurs:

```text
EXECUTION_FAIL
STOP
```

## 7. FT6A-03 — reconcile Evidence 218 counts

Explicitly explain the earlier Evidence-218 values:

```text
FT-19 archive member = 1
FT-20 archive member = 1
```

Allowed remediation result A:

```text
CLASSIFICATION_ERROR
```

Only if the rerun URL-level receipts prove zero actual individual-member
requests and the previous harness categorization rule is shown to have
double-counted or misclassified a request.

Allowed remediation result B:

```text
EARLIER_HARNESS_DIAGNOSTIC
```

Only if the exact extra URL is identified and proven to have been generated by
acceptance harness diagnostics rather than the normal product acquire/ingest
path.

Otherwise:

```text
REAL_PRODUCT_MEMBER_FETCH
→ EXECUTION_FAIL
→ RETURN TO DEVELOPMENT
```

Do not hand-wave this reconciliation.

## 8. No full-cycle rerun required

The accepted Formal Test 6 gates listed in Review 219 do not need to be rerun.

Do not substitute this targeted remediation for any future new production
candidate.

No source/test patch is allowed.

## 9. Evidence

If FT6A-00 through FT6A-03 pass, create exactly:

`development/222-p11-formal-test-evidence-6a.md`

Reserve 221 for execution authorization.

The evidence must include:

- exact authority SHAs;
- complete chronological URL list for Q3;
- complete chronological URL list for Toyota;
- mutually exclusive category for each URL;
- exact category totals;
- package/provenance/validation identities;
- explicit reconciliation of the old `archive member = 1` values;
- final source/test drift proof.

Raw harnesses/logs stay outside Git.

## 10. Result classification

```text
all targeted gates pass
→ EXECUTION_PASS

actual individual member fetch by product path
→ EXECUTION_FAIL

source/test change required
→ EXECUTION_FAIL

external SEC/contact prevents required live rerun
→ EXECUTION_BLOCKED
```

## 11. Stop boundary

After documentation-only evidence push:

```text
STOP FOR CHATGPT FORMAL ACCEPTANCE REVIEW 6 CONTINUATION
```

Do not modify production/test code.
Do not merge main.
Do not declare Formal Acceptance.
Do not declare P11 DONE.
