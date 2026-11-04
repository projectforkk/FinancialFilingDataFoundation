# 158 — P11 Supplemental Identity Amendment Evidence — ISSUE-021

Status: **PASS — AMENDED DESIGN READY FOR FRESH DETACHED REVIEW**

Phase:
P11 — US SEC Provider

Historical reviewed candidate:
`a223d44d766609190806d1d349dab1d5d673423b`

Review stop:
`development/157-p11-final-design-review-stop.md`

Production remains CLOSED.

## P11-ISSUE-021 resolution

ParsedFinancialDocument v2 now freezes filing-role nullability:

### PERIODIC

- fiscal_year required;
- raw_fiscal_period required;
- report_date required;
- no provisional/null periodic identity.

### SUPPLEMENTAL

- fiscal_year null unless exact filing-native evidence establishes it;
- raw_fiscal_period always null;
- report_date official non-empty valid SEC reportDate or null;
- filing_date cannot be used to infer fiscal_year/report_date;
- no calendar-derived placeholder.

Registry boundary:

- P11 v1 supplemental filings are NOT written to existing periodic SQLiteRegistry / ParsedDataRecord;
- authority remains SEC source package + ParsedFinancialDocument v2 + supplemental export;
- generic supplemental registry is future separate additive design.

Acceptance now requires:

- null field round-trip;
- no guessed fiscal metadata;
- no periodic slot;
- no periodic registry/ParsedDataRecord write;
- accession identity retained.

## Regression of prior design resolutions

PASS:

- ISSUE-010 aggregate rate contract intact;
- ISSUE-011 package identity/hash/receipt intact;
- ISSUE-012 local path contract intact;
- ISSUE-013 locator contract intact;
- ISSUE-014 deterministic IDs intact;
- ISSUE-015 raw/transformed value intact;
- ISSUE-016 identity grammar intact;
- ISSUE-017 deterministic package assembly intact;
- ISSUE-018/020 implementation order intact;
- ISSUE-019 Q2 market guard intact.

## Scope

Design/governance only.

No src/tests/integration/runtime-lock change.

## Verdict

# PASS — READY FOR FRESH DETACHED DESIGN REVIEW

P11 production remains CLOSED.
