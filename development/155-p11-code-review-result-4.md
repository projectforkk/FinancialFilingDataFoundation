# 155 — P11 US SEC Provider Fourth Exact-Candidate Code Review

Status: **REVIEW_PASS**

Reviewed candidate:

`05e06096bc8b788d0467a1ce3442829e87727b6b`

Design baseline:

`c970d63c2699d016c1696451d2a66fc42850b4f1`

Previous reviewed candidate:

`1770a29205e1af03f64a541724c435ab710dc984`

Repair evidence:

`development/154-p11-repair-development-evidence-3.md`

Prior review:

`development/153-p11-code-review-result-3.md`

Development branch:

`task/p11-sec-rebuild-development`

Branch HEAD inspected before this review document:

`7a4c3a94911563ef02adae66fbc9fa400ce2f20d`

## 1. Exact-candidate lineage gate

PASS.

The production candidate commit itself changes only:

- `src/financial_filing_data_foundation/us_sec/discovery.py`
- `tests/unit/us_sec/test_http_discovery.py`

The development branch after the reviewed production candidate contains only review/evidence documentation. No production implementation changed after the exact candidate SHA.

The review therefore applies specifically to:

`05e06096bc8b788d0467a1ce3442829e87727b6b`

and not to an unbounded branch state.

## 2. P11-ISSUE-101 re-check

**FIXED**

The prior blocking defect was:

> a requested historical fiscal year with a missing exact target annual could fall into the in-progress chronology branch even when a later completed annual filing proved that the requested year was already historical.

The reviewed candidate adds `_latest_annual_end()`, using visible official annual forms:

- `10-K`
- `20-F`
- `40-F`

with the existing issuer-kind filter and source-derived report periods.

The in-progress branch is now allowed only when all of the following are true:

1. the exact target annual is absent;
2. the prior fiscal year's exact annual endpoint exists;
3. that prior annual endpoint equals the latest visible completed annual endpoint for the matching issuer kind;
4. current official `fiscalYearEnd` metadata exists.

Otherwise discovery returns no matches before constructing the synthetic current-year upper boundary.

This implements the required deterministic rule from review 153:

```text
exact target annual exists
→ completed-year chronology

exact target annual missing
AND prior FY annual is the latest completed annual
AND current official fiscalYearEnd metadata exists
→ in-progress chronology

otherwise
→ fail closed
```

No ticker-specific exception and no wall-clock inference was introduced.

## 3. Required historical regression

PASS.

New regression:

`test_historical_year_missing_target_annual_does_not_use_in_progress_fallback`

Fixture contains:

- current `fiscalYearEnd=0926`;
- FY2023 annual `2023-09-30`;
- FY2024 Q1/Q2/Q3;
- missing FY2024 annual;
- later FY2025 annual `2025-09-27`.

The test asserts no match for FY2024:

- Q1;
- Q2;
- Q3;
- FY.

This directly covers the exact branch that remained open in review 153.

## 4. Positive in-progress regression

PASS / PRESERVED.

`test_discovery_handles_in_progress_non_calendar_fiscal_year_by_chronology`

continues to exercise the valid case where FY2026 is the latest completed annual and FY2027 is genuinely in progress.

The repaired gate therefore does not collapse all missing-target-annual cases into failure; it distinguishes the valid in-progress case from a completed historical year.

## 5. Prior P11 findings

Because the reviewed production commit changes only SEC discovery chronology and its focused test, the previously reviewed implementations for P11-ISSUE-102 through P11-ISSUE-108 are unchanged.

Fourth-review status:

- P11-ISSUE-101: **FIXED**
- P11-ISSUE-102: **FIXED**
- P11-ISSUE-103: **FIXED**
- P11-ISSUE-104: **FIXED**
- P11-ISSUE-105: **FIXED**
- P11-ISSUE-106: **FIXED**
- P11-ISSUE-107: **FIXED**
- P11-ISSUE-108: **FIXED**

No new blocking code-review finding was identified.

## 6. Development verification evidence

`development/154-p11-repair-development-evidence-3.md` reports:

- P11 focused: `53 passed in 2.27s`;
- full unit suite: `583 passed in 64.76s`;
- CN/HK regression: `96 passed in 7.09s`;
- compileall: PASS;
- `git diff --check`: PASS.

The evidence also records TDD behavior for the new regression:

- before repair: the new regression failed;
- after repair: the discovery test file passed and the complete P11 focused suite passed.

Developer live SEC smoke was not run because `FFDF_SEC_CONTACT_EMAIL` was not set.

These results are accepted as development evidence for code review. They do not constitute formal P11 acceptance.

## 7. Acceptance boundary

The design explicitly states that P11 cannot be accepted by unit tests alone.

Formal acceptance still requires the live/golden classes defined by `design/26-p11-sec-provider-design.md`, including at least:

1. domestic 10-K with Inline XBRL;
2. domestic 10-Q with Inline XBRL;
3. custom extension concepts;
4. amended variant present;
5. foreign private issuer 20-F or 40-F annual filing;
6. malformed/path/content-type negative fixtures;
7. throttling/access-denied simulation;
8. repeat acquire/parse proving idempotent reuse.

Therefore this review does **not** mark P11 production-available and does not authorize changing the accepted CN/HK compatibility baseline by itself.

## 8. Fourth review verdict

```text
FOURTH CODE REVIEW: REVIEW_PASS

ISSUE-101: FIXED
ISSUE-102: FIXED
ISSUE-103: FIXED
ISSUE-104: FIXED
ISSUE-105: FIXED
ISSUE-106: FIXED
ISSUE-107: FIXED
ISSUE-108: FIXED

NEW BLOCKING CODE FINDINGS: NONE

EXACT PRODUCTION CANDIDATE:
05e06096bc8b788d0467a1ce3442829e87727b6b

FORMAL ACCEPTANCE: NOT STARTED
PRODUCTION AVAILABILITY: NOT AUTHORIZED
```

## 9. Required next action

The exact candidate is now eligible to enter the formal P11 acceptance stage.

Next step:

1. issue a formal test/acceptance plan against exact candidate `05e06096bc8b788d0467a1ce3442829e87727b6b`;
2. freeze exact live/golden accession fixtures before execution;
3. configure an SEC-compliant contact identity for live requests;
4. execute the required live/golden, negative, idempotency and regression gates;
5. record exact evidence and stop for final acceptance review.

Do not merge P11 to main, change `SUPPORTED_MARKETS`, or mark `P11_SEC_PROVIDER` available until formal acceptance passes.
