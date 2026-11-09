# P11 SECOND REPAIR DEVELOPMENT RESULT

design_baseline_sha:
`c970d63c2699d016c1696451d2a66fc42850b4f1`

previous_candidate:
`9bf84e1aeaca33f49830ada50b7876a2f36f04eb`

review:
`development/151-p11-code-review-result-2.md`

review_commit:
`3499236fd55beeccfb4f1954170d65ca68a29ba0`

new_production_candidate_sha:
`1770a29205e1af03f64a541724c435ab710dc984`

development_branch:
`task/p11-sec-rebuild-development`

production_commit:
`fix: complete P11 fiscal chronology and hidden iXBRL evidence`

## Scope

This repair pass handled only `P11-ISSUE-101` and `P11-ISSUE-108`. The previous
repairs for `P11-ISSUE-102` through `P11-ISSUE-107` were preserved. No Registry,
P8 tool-name, CN/HK, P9, P10, XML extraction, HTTP, package-store, or runtime
architecture changes were made in this pass.

## P11-ISSUE-101

status:
`FIXED`

root cause:
The previous discovery implementation treated one submissions-level
`fiscalYearEnd=MMDD` as the exact boundary for every historical fiscal year. It
also assigned quarters by dividing one synthetic fiscal interval into four
parts. For a 52/53-week issuer, historical annual report periods move between
calendar dates, so a historical endpoint such as `2024-09-28` could be shifted
past the current `09/26` boundary.

implementation:

- completed FY discovery now anchors on the unique official annual filing
  `reportPeriod` for the requested fiscal year;
- completed-year quarter slots are assigned from ascending unique `10-Q`
  `reportPeriod` groups between the exact prior and target annual endpoints;
- an omitted prior annual is accepted only for a complete three-slot chronology
  before the exact target annual endpoint, otherwise discovery fails closed;
- in-progress years require the prior completed annual endpoint and official
  current `fiscalYearEnd` metadata, then assign available quarter slots by
  chronology within that bounded interval;
- original and `/A` filings with the same `reportPeriod` share one slot, while
  `select_filing` continues to emit `P11_AMENDED_VARIANT_PRESENT`;
- no ticker-specific or Apple-specific rule was added.

tests:

- `test_discovery_uses_exact_historical_annual_end_for_53_week_fiscal_year`
- `test_discovery_resolves_historical_quarters_by_chronology_not_duration_ratio`
- `test_discovery_handles_in_progress_non_calendar_fiscal_year_by_chronology`
- `test_discovery_groups_amendment_with_same_report_period`
- `test_discovery_uses_exact_fpi_annual_endpoint_for_history`
- calendar issuer Q1/Q2/Q3/FY assertions in the amendment-grouping fixture

result:
`PASS`

## P11-ISSUE-108

status:
`FIXED`

root cause:
Inline XBRL facts inside `ix:hidden` were extracted as Raw Facts but were forced
through visible normalized-block identity. Facts under `ix:header` therefore
had no visible block, received `P11_EVIDENCE_LOCATOR_INVALID`, and could make P7
blocking even though the hidden source node was valid and immutable.

implementation:

- hidden `ix:nonfraction` and `ix:nonnumeric` facts are identified by a hidden
  ancestor and emitted with `hidden=true`;
- hidden facts use `locator_kind=DOM_HIDDEN_FACT`, retain the exact DOM locator,
  member SHA, package SHA, raw text, and fragment hash, and legally carry
  `block_id=null` and `block_dom_locator=null`;
- `verify_sec_evidence()` round-trips hidden evidence against immutable HTML,
  requires the exact node to be a supported Inline XBRL fact under `ix:hidden`,
  and verifies raw text, fragment hash, member SHA, and package identity;
- visible `DOM_PATH` evidence still requires a real normalized block and a valid
  block DOM locator;
- the parser version is `VIRTUAL_HTML_V3`, and new artifacts use a
  parser-version-specific directory so old V2 cached artifacts are not silently
  reused.

tests:

- `test_hidden_inline_numeric_and_nonnumeric_facts_are_valid_source_evidence`
- `test_hidden_fact_corrupt_locator_or_hash_is_blocked` (locator/member/hash)
- `test_visible_inline_fact_still_requires_a_block_anchor`
- `test_parser_does_not_reuse_artifact_from_previous_normalizer_version`

result:
`PASS`

## TDD evidence

The new focused tests were run before the production repair and produced the
expected baseline failures: `43 passed, 9 failed`. After the minimal repair,
the focused suite passed with `52 passed`.

## Verification

P11 focused:

```text
$env:PYTHONPATH=(Resolve-Path 'src').Path; & 'D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe' -m pytest -q --basetemp=D:\t\p11thirdcandidate tests/unit/us_sec
```

result:
`52 passed in 1.86s`

Full unit suite:

```text
$env:PYTHONPATH=(Resolve-Path 'src').Path; & 'D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe' -m pytest -q --basetemp=D:\t\fullthirdcandidate
```

result:
`582 passed in 85.72s`

CN/HK regression:

```text
$env:PYTHONPATH=(Resolve-Path 'src').Path; & 'D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe' -m pytest -q --basetemp=D:\t\cnhkthirdcandidate tests/unit/identity tests/unit/registry tests/unit/mcp tests/unit/user_cli
```

result:
`96 passed in 7.99s`

compileall:

```text
& 'D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe' -m compileall -q src tests/unit/us_sec
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
`NO`

## Safety declarations

accepted CN/HK raw/source artifacts mutated = `NO`

remote AI/API called by FFDF production code = `NO`

main merged = `NO`

formal acceptance performed = `NO`

formal test plan issued = `NO`
