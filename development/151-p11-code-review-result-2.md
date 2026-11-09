# 151 — P11 US SEC Provider Second Exact-Candidate Code Review

Status: **CHANGES_REQUIRED**

Reviewed candidate:

`9bf84e1aeaca33f49830ada50b7876a2f36f04eb`

Previous reviewed candidate:

`529376cc084bd9990c144102fa723822b5229e1a`

Repair evidence:

`development/150-p11-repair-development-evidence.md`

Prior review:

`development/149-p11-code-review-result.md`

## 1. Candidate / evidence integrity

PASS.

The repair candidate is exactly 2 commits ahead of the previous reviewed production
candidate and 0 behind.

The development branch after the repair candidate contains only review/evidence/plan
documents. No production code changed after the reviewed SHA.

## 2. Prior review issues re-check

### P11-ISSUE-102 — Zero structured facts false PASS

**FIXED**

Observed repair:

- added `P11_STRUCTURED_FACTS_MISSING`;
- zero structured facts no longer PASS;
- facts without Evidence block validation;
- ingest publishes only `validation_status == PASS`.

### P11-ISSUE-103 — Unsupported gzip advertisement

**FIXED**

Observed repair:

- client no longer advertises `Accept-Encoding: gzip`;
- unexpected non-identity Content-Encoding fails closed.

### P11-ISSUE-104 — Redirect limit / unbounded HTTPError body

**FIXED**

Observed repair:

- configured redirect limit is wired into the redirect handler and subprocess path;
- every redirect URL is revalidated through the SEC allowlist;
- redirect-limit reason code exists;
- HTTP error-body reads are bounded.

### P11-ISSUE-105 — Evidence round-trip

**FIXED FOR VISIBLE HTML + XML FACTS**

Observed repair:

- `VIRTUAL_HTML_V2`;
- visible Inline XBRL Evidence references an actual normalized source block;
- fact DOM locator is separate from block locator;
- XML facts use `XML_PATH`;
- validation resolves source locator and verifies source text/fragment hashes.

A separate hidden-fact defect remains and is recorded as P11-ISSUE-108 below.

### P11-ISSUE-106 — P8 raw package revalidation

**FIXED**

Observed repair:

- SEC bundle loading reopens the canonical raw package;
- package/member hashes are verified;
- Evidence member SHA must exist in the package;
- cached P8 bundles re-run raw source-chain validation before being served.

### P11-ISSUE-107 — XML XBRL facts

**FIXED**

Observed repair:

- filing-local XBRL instance members now produce Raw Facts;
- source QName, context/unit, period/entity/dimensions, numeric candidate, nil,
  member SHA and XML locator are preserved;
- XML Evidence is independently round-trip verified.

## 3. Remaining blocking finding

### P11-ISSUE-101 — Fiscal-year discovery is still unsafe for historical 52/53-week issuers

Severity: **BLOCKING / NOT FULLY FIXED**

The repair removed the original hard-coded 03/06/09/12 mapping, but discovery now
uses one submissions-level `fiscalYearEnd = MMDD` as the first-priority boundary
for all requested historical years.

Current function:

`_fiscal_year_end_for_request()`

returns `submissions.fiscal_year_end` immediately when present.

Then:

`_fiscal_year_for_report_date()`

assigns a report date to the next fiscal year whenever its month/day is later than
that single MMDD.

That is not safe for 52/53-week issuers because the exact year-end date moves between
years.

Concrete official SEC example: Apple fiscal year ends on the last Saturday of
September. SEC filings show:

- FY2023 report period: 2023-09-30;
- FY2024 report period: 2024-09-28;
- FY2025 report period: 2025-09-27;
- FY2026 report period: 2026-09-26.

If current submissions metadata contains the current 09/26 fiscal-year-end MMDD,
the current implementation evaluates historical 2024-09-28 as later than 09/26 and
therefore assigns it to FY2025. Historical FY2024 discovery can fail or shift.

Required fix:

1. do not use one current MMDD as the authoritative historical fiscal boundary;
2. for a requested completed fiscal year, prefer the exact annual filing
   `reportPeriod` for that requested FY as the fiscal-year-end anchor;
3. derive historical Q1/Q2/Q3 primarily from official filing chronology between the
   prior annual end and requested annual end, rather than proportional division of
   one synthetic MMDD interval;
4. for an in-progress fiscal year where the annual filing does not yet exist, use a
   deterministic current-year rule based on official current fiscal-year-end
   metadata plus prior annual chronology, and fail closed when the slot cannot be
   established safely;
5. preserve 52/53-week behavior without ticker-specific rules.

Required tests:

- current FYE MMDD differs from historical exact annual end;
- Apple-like sequence:
  - FY2023 = 09/30;
  - FY2024 = 09/28;
  - FY2025 = 09/27;
  - FY2026 = 09/26;
- historical FY2024 Q1/Q2/Q3/FY resolves while current FYE metadata is 09/26;
- in-progress non-calendar fiscal year before its 10-K exists;
- no hard-coded AAPL/ticker exception.

### P11-ISSUE-108 — Valid Inline XBRL hidden facts become blocking Evidence failures

Severity: **BLOCKING / NEW REVIEW FINDING**

Current parser behavior:

- `_facts()` extracts every `ix:nonfraction` / `ix:nonnumeric`, including facts
  inside `ix:hidden` / `ix:header`;
- `_blocks()` intentionally excludes nodes under `ix:header`;
- `_source_block_for_node()` therefore returns no normalized block for hidden facts;
- `_facts()` emits `P11_EVIDENCE_LOCATOR_INVALID` with severity `BLOCKING`
  whenever no source block exists;
- P7 therefore blocks a filing containing legitimate hidden facts.

Legitimate `ix:hidden` facts exist in SEC filings. SEC FilingSummary logs explicitly
report facts appearing in `ix:hidden`, including filings where hidden facts are
not referenced by visible `-sec-ix-hidden` style properties.

Required fix:

Model hidden Inline XBRL facts as valid source-aware facts rather than forcing them
through visible-page block identity.

Acceptable design:

- preserve the exact hidden fact DOM locator/member SHA/fragment hash;
- set `hidden = true`;
- use a dedicated locator/anchor kind such as `DOM_HIDDEN_FACT`, or define an
  explicit hidden source-block collection;
- do not require a visible `pages[].blocks[].block_id` for a legitimate hidden
  fact;
- P7 must still round-trip the fact locator to immutable HTML bytes and verify value
  and fragment hash;
- visible facts must continue to require valid normalized block/cell anchors.

Required tests:

1. `ix:hidden` numeric fact with context/unit → valid Raw Fact + Evidence;
2. `ix:hidden` nonnumeric fact → valid Raw Fact + Evidence;
3. hidden fact not referenced by visible CSS property must not cause a blocking
   parser failure merely because it is hidden;
4. corrupt hidden DOM locator/member SHA/fragment hash → BLOCKED;
5. visible-fact block validation remains unchanged.

## 4. External SEC verification used in review

Official SEC evidence confirms the fiscal-date issue and hidden-fact requirement:

- Apple FY2023 filing: period ended 2023-09-30;
- Apple FY2024 filing: period ended 2024-09-28;
- Apple FY2025 filing: period ended 2025-09-27;
- Apple FY2026 filing: period ended 2026-09-26;
- SEC XBRL Guide defines Current Fiscal Year End Date as the month/day marking the
  current fiscal year end and says it normally does not change from year to year,
  which is not a guarantee that exact 52/53-week report dates are identical;
- official SEC FilingSummary examples explicitly contain warnings about facts
  appearing in `ix:hidden`.

## 5. Review verdict

```text
SECOND CODE REVIEW: CHANGES_REQUIRED

ISSUE-102: FIXED
ISSUE-103: FIXED
ISSUE-104: FIXED
ISSUE-105: FIXED for visible HTML/XML
ISSUE-106: FIXED
ISSUE-107: FIXED

ISSUE-101: STILL OPEN
ISSUE-108: OPEN

FORMAL TEST PLAN: NOT ISSUED
FORMAL ACCEPTANCE: NOT STARTED
```

Do not start formal acceptance on candidate:

`9bf84e1aeaca33f49830ada50b7876a2f36f04eb`

## 6. Required next action

PC Agent performs one compact repair pass for only:

- P11-ISSUE-101;
- P11-ISSUE-108.

Avoid unrelated refactoring.

After repair:

1. add the focused regression fixtures described above;
2. run all P11 focused tests;
3. run full unit regression;
4. run CN/HK regression;
5. compileall;
6. git diff --check;
7. commit a new exact production candidate;
8. submit a separate repair evidence commit;
9. stop for ChatGPT review.

A formal test plan will be issued only after the new candidate receives
`REVIEW_PASS`.
