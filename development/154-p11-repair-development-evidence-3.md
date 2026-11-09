# P11 THIRD REPAIR DEVELOPMENT RESULT

previous_production_candidate:
`1770a29205e1af03f64a541724c435ab710dc984`

review:
`development/153-p11-code-review-result-3.md`

review_commit:
`9d9190d09758d9f20c7e0fed4fe289ced0ba0ae6`

new_production_candidate:
`05e06096bc8b788d0467a1ce3442829e87727b6b`

development_branch:
`task/p11-sec-rebuild-development`

production_commit:
`fix: close historical P11 fiscal-year fallback`

## Scope

This pass changed only the P11-ISSUE-101 discovery branch and its focused
regression test. P11-ISSUE-102 through P11-ISSUE-108 implementations were not
modified. No Registry, package, parser, evidence, P8/P9/P10, CN/HK, supported
market, or production-capability changes were made.

## P11-ISSUE-101

status:
`FIXED`

root cause:
When the requested fiscal year had no exact annual candidate, discovery entered
the in-progress branch after checking only the prior annual endpoint and current
`fiscalYearEnd` metadata. A historical target annual could therefore be missing
from the visible candidate set while a later completed annual was present, and
its quarters could be assigned against a synthetic current-year upper boundary.

implementation:

- added a deterministic latest-visible-annual endpoint helper over the official
  annual candidates (`10-K`, `20-F`, `40-F`);
- the in-progress branch now requires the prior FY exact annual endpoint to be
  equal to that latest visible annual endpoint, in addition to current official
  `fiscalYearEnd` metadata;
- if a later annual exists, or the prior annual/latest relationship cannot be
  established, discovery returns no matches and does not construct a synthetic
  historical endpoint;
- the existing exact-target-annual chronology and positive in-progress chronology
  remain unchanged.

regression_added:
`test_historical_year_missing_target_annual_does_not_use_in_progress_fallback`

fixture:

- current `fiscalYearEnd=0926`;
- FY2023 annual `2023-09-30`;
- FY2024 Q1/Q2/Q3 present;
- FY2024 annual absent;
- FY2025 annual `2025-09-27`.

expected_and_observed:
`FY2024 Q1/Q2/Q3/FY all return no match; PASS`

positive_regression_preserved:
`test_discovery_handles_in_progress_non_calendar_fiscal_year_by_chronology`
continues to resolve FY2027 Q1/Q2 when FY2026 is the latest visible annual and
FY2027 annual is absent.

## TDD evidence

The new regression was run before the production change and failed as expected:
`1 failed, 16 deselected`. After the minimal change, the discovery test file
passed with `17 passed`, and the complete P11 focused suite passed with `53
passed`.

## Verification

P11 focused:

```text
$env:PYTHONPATH=(Resolve-Path 'src').Path; & 'D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe' -m pytest -q --basetemp=D:\t\p11fourthcandidate2 tests/unit/us_sec
```

result:
`53 passed in 2.27s`

Full unit suite:

```text
$env:PYTHONPATH=(Resolve-Path 'src').Path; & 'D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe' -m pytest -q --basetemp=D:\t\unitfourthcandidate tests/unit
```

result:
`583 passed in 64.76s`

CN/HK regression:

```text
$env:PYTHONPATH=(Resolve-Path 'src').Path; & 'D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe' -m pytest -q --basetemp=D:\t\cnhkfourthcandidate tests/unit/identity tests/unit/registry tests/unit/mcp tests/unit/user_cli
```

result:
`96 passed in 7.09s`

compileall:

```text
& 'D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe' -m compileall -q src tests
```

result:
`PASS`

git diff --check:

```text
git diff --check
```

result:
`PASS`

developer live SEC smoke:
`NOT RUN — FFDF_SEC_CONTACT_EMAIL is not set; no live filing was downloaded.`

formal acceptance:
`NOT RUN`

## Safety declarations

accepted CN/HK raw/source artifacts mutated = `NO`

remote AI/API called by FFDF production code = `NO`

main merged = `NO`

formal acceptance performed = `NO`
