# 153 — P11 US SEC Provider Third Exact-Candidate Code Review

Status: **CHANGES_REQUIRED**

Reviewed candidate:

`1770a29205e1af03f64a541724c435ab710dc984`

Design baseline:

`c970d63c2699d016c1696451d2a66fc42850b4f1`

Previous reviewed candidate:

`9bf84e1aeaca33f49830ada50b7876a2f36f04eb`

Repair evidence:

`development/152-p11-repair-development-evidence-2.md`

Prior review:

`development/151-p11-code-review-result-2.md`

Development branch:

`task/p11-sec-rebuild-development`

Branch HEAD inspected before this review document:

`48a076d02c7f8c11d60650b925317a261e6fdfb0`

## 1. Repository handoff / orientation gate

PASS.

Before reviewing the new candidate, the current Git repository was re-oriented as a
whole rather than treating P11 as an isolated module.

Reviewed/indexed:

- all current `design/*.md` files;
- the complete `src/financial_filing_data_foundation/` production source tree;
- the complete Python test tree and each test group's contract responsibility;
- all seven `tests/unit/us_sec/` files in full;
- the complete `development/` index;
- current P11 lifecycle documents `147` through `152` in full;
- P0-P10/P11 upstream/downstream relationships, persisted-artifact boundaries,
  Registry, P8, P9, P10 and CLI compatibility constraints.

The accepted P0-P10 / CN-HK baseline remains the compatibility baseline. P11 remains
an additive, gated extension and is not production-available.

## 2. Candidate / evidence lineage integrity

PASS.

Observed lineage:

- main baseline: `5190e866a4ee55dc8820e63ce3dae8fe3c69dfc8`;
- design baseline: `c970d63c2699d016c1696451d2a66fc42850b4f1`;
- previous candidate: `9bf84e1aeaca33f49830ada50b7876a2f36f04eb`;
- reviewed candidate: `1770a29205e1af03f64a541724c435ab710dc984`;
- evidence branch HEAD before this review: `48a076d02c7f8c11d60650b925317a261e6fdfb0`.

The reviewed candidate is 0 behind the design lineage. The development branch after
the reviewed candidate contains only review/evidence/plan documentation. No
production code changed after the reviewed SHA.

## 3. Prior review findings re-check

### P11-ISSUE-102 — Zero structured facts false PASS

**FIXED / PRESERVED**

Zero structured facts do not become research-ready PASS, and facts without Evidence
remain fail-closed.

### P11-ISSUE-103 — Unsupported gzip advertisement

**FIXED / PRESERVED**

The client does not advertise unsupported gzip decoding and unexpected content
encoding fails closed.

### P11-ISSUE-104 — Redirect limit / bounded error body

**FIXED / PRESERVED**

Configured redirect limits, per-hop allowlisting and bounded error-body behavior
remain present.

### P11-ISSUE-105 — Evidence round-trip

**FIXED**

Visible HTML Evidence still resolves a real normalized source block and fact DOM
locator against immutable source bytes. XML Evidence still uses an independently
resolvable `XML_PATH`.

### P11-ISSUE-106 — P8 raw package revalidation

**FIXED / PRESERVED**

P8 SEC reads still revalidate the immutable raw package/member chain before serving
derived facts/evidence.

### P11-ISSUE-107 — XML XBRL facts

**FIXED / PRESERVED**

Filing-local XBRL instance facts remain source-preserving Raw Facts with XML
Evidence.

### P11-ISSUE-108 — Valid Inline XBRL hidden facts

**FIXED**

The reviewed candidate now models legitimate hidden facts separately from visible
page blocks:

- parser version is `VIRTUAL_HTML_V3`;
- hidden `ix:nonfraction` and `ix:nonnumeric` facts use
  `locator_kind=DOM_HIDDEN_FACT`;
- hidden Evidence may have no visible `block_id` / `block_dom_locator`;
- `verify_sec_evidence()` resolves the exact DOM node against the immutable member;
- the resolved node must be a supported Inline XBRL fact under `ix:hidden`;
- member SHA, package identity, raw text and fragment hash are verified;
- visible `DOM_PATH` Evidence continues to require a real normalized block and
  block locator;
- corruption tests cover hidden locator/member/hash and visible-block regression.

This closes P11-ISSUE-108.

## 4. Remaining blocking finding

### P11-ISSUE-101 — Historical fiscal year with missing target annual is misclassified as in-progress

Severity: **BLOCKING / REPAIR INCOMPLETE**

The second repair correctly stopped using one current `fiscalYearEnd MMDD` as the
authoritative boundary when the exact target annual filing exists.

However, `discover_filings()` still uses this branch condition:

```text
target annual exists
→ completed-year chronology

target annual missing
→ treat as in-progress year
```

The implementation does not first prove that the requested fiscal year is actually
the current/in-progress fiscal year.

Current source behavior:

1. `target_annual_end = _unique_annual_end(... requested fiscal_year ...)`;
2. if `target_annual_end is None`, the code enters the in-progress branch;
3. it requires the prior year's annual endpoint and current
   `submissions.fiscal_year_end`;
4. it constructs a synthetic upper bound from
   `date(requested_fiscal_year, current MMDD)`;
5. it assigns any 10-Q report periods inside that interval to Q1/Q2/Q3;
6. it never checks whether a later annual filing already proves the requested FY is
   historical/completed.

Therefore a completed historical fiscal year whose target annual filing is absent
from the loaded candidate set can still resolve quarters using current fiscal-year
metadata instead of failing closed.

### Concrete regression that exposes the defect

Use an Apple-like 52/53-week chronology:

```text
current fiscalYearEnd metadata = 0926

FY2023 annual = 2023-09-30
FY2024 Q1     = 2023-12-30
FY2024 Q2     = 2024-03-30
FY2024 Q3     = 2024-06-29
FY2024 annual = MISSING
FY2025 annual = 2025-09-27
```

Request:

```text
fiscal_year = 2024
period = Q1 / Q2 / Q3
```

Required behavior:

```text
FAIL CLOSED
```

Reason:

- FY2025 annual exists, so FY2024 cannot be treated as the current in-progress FY;
- the exact FY2024 annual endpoint is unavailable;
- the accepted review rule requires a completed historical FY to anchor on its exact
  annual filing `reportPeriod`.

Current candidate behavior:

- no FY2024 annual → enters in-progress branch;
- prior FY2023 annual exists;
- current MMDD produces synthetic upper bound `2024-09-26`;
- the three FY2024 10-Q dates are before that synthetic bound;
- Q1/Q2/Q3 can therefore be returned instead of failing closed.

This is the same semantic defect class as P11-ISSUE-101, not a new unrelated issue.

## 5. Required repair

Keep the repair compact and limited to P11-ISSUE-101.

Before the in-progress fallback is allowed, prove that the requested fiscal year is
the immediate year after the latest completed annual filing available to discovery.

A safe implementation rule is:

```text
exact target annual exists
→ completed historical/current annual path

exact target annual missing
AND prior FY annual is the latest completed annual
AND current official fiscalYearEnd metadata exists
→ in-progress chronology path

otherwise
→ fail closed
```

Equivalent deterministic logic is acceptable, but it must not use ticker-specific
exceptions or wall-clock guessing.

At minimum add this regression:

`test_historical_year_missing_target_annual_does_not_use_in_progress_fallback`

The fixture must contain a later annual filing and assert that FY2024 Q1/Q2/Q3/FY
do not resolve when FY2024's exact annual endpoint is missing.

Also preserve the existing positive in-progress test where the prior annual really
is the latest completed annual.

## 6. Test evidence assessment

The developer evidence reports:

- P11 focused: `52 passed`;
- full unit suite: `582 passed`;
- CN/HK focused regression: `96 passed`;
- compileall: PASS;
- git diff --check: PASS.

Those results are useful development evidence, but they do not cover the historical
missing-target-annual branch above. They are not sufficient to advance to formal
testing while P11-ISSUE-101 remains open.

No live SEC run was claimed in `development/152`, and formal acceptance has not
started.

## 7. Third review verdict

```text
THIRD CODE REVIEW: CHANGES_REQUIRED

ISSUE-101: STILL OPEN — one historical/in-progress discrimination branch remains
ISSUE-102: FIXED
ISSUE-103: FIXED
ISSUE-104: FIXED
ISSUE-105: FIXED
ISSUE-106: FIXED
ISSUE-107: FIXED
ISSUE-108: FIXED

FORMAL TEST PLAN: NOT ISSUED
FORMAL ACCEPTANCE: NOT STARTED
```

Do not start formal acceptance on candidate:

`1770a29205e1af03f64a541724c435ab710dc984`

## 8. Required next action

PC Agent performs one minimal repair for the remaining P11-ISSUE-101 branch only.

After repair:

1. add the historical-missing-target-annual fail-closed regression;
2. preserve the existing in-progress positive regression;
3. run focused P11 tests;
4. run full unit regression;
5. run CN/HK regression;
6. compileall;
7. run `git diff --check`;
8. commit a new exact production candidate;
9. submit a separate development evidence commit;
10. stop for ChatGPT exact-candidate review.

No unrelated refactoring and no formal test plan until the new candidate receives
`REVIEW_PASS`.
