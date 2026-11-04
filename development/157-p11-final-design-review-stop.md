# 157 — P11 Final Design Review Stop — Supplemental Identity Nullability

Status: **FAIL / STOP — P11-ISSUE-021 / PRODUCTION CLOSED**

Phase:
P11 — US SEC Provider

Reviewed exact candidate:
`a223d44d766609190806d1d349dab1d5d673423b`

Fresh detached review:
`D:\\Codex\\FinancialFilingDataFoundation\\worktrees\\review\\p11-design-a223d44`

Final contract matrix before semantic review:
`PASS`

## Finding

The final matrix passed ISSUE-010..020, but manual semantic review found an unresolved supplemental identity contradiction.

P11 design correctly defines 8-K/6-K as accession-bound supplemental filings that are not forced into periodic Q/FY slots.

However `design/30 document.json` still requires:

- `fiscal_year` for all filings;
- `report_date` for all filings;
- only `raw_fiscal_period` is explicitly nullable for supplemental filings.

For some 8-K/6-K filings, forcing a fiscal year or report date would require guessing, calendar-derived inference, or placeholder strings.

The existing SQLite `SourceMetadata.report_date` is also non-null string-oriented, so “may register supplemental filing” is not currently a safe source-neutral contract.

## P11-ISSUE-021 — supplemental identity nullability / registry boundary

Required design correction:

1. For `filing_role=PERIODIC`:
   - fiscal_year required integer;
   - raw_fiscal_period required;
   - report_date required when the official filing metadata/DEI contract requires it.

2. For `filing_role=SUPPLEMENTAL`:
   - fiscal_year = null unless explicit filing-native evidence establishes it;
   - raw_fiscal_period = null;
   - report_date = official report date when non-empty/valid, otherwise null;
   - no calendar-year inference solely from filing_date.

3. P11 v1 supplemental filings MUST NOT be persisted into periodic SQLite `ParsedDataRecord/FilingSlotKey`.

4. P11 v1 should keep supplemental identity authoritative in:
   - SEC source package;
   - ParsedFinancialDocument v2;
   - supplemental export.

5. Any future generic supplemental registry requires a separate additive registry contract.

Acceptance must prove:
- supplemental null fields round-trip;
- no guessed fiscal year;
- no periodic slot/ParsedDataRecord write;
- 8-K/6-K exact accession identity retained.

## Scope

No production/test/runtime changes.

ISSUE-010..020 remediation remains valid.

## Verdict

# FAIL / STOP

Candidate `a223d44...` is INELIGIBLE for DESIGN READY.

P11 production remains CLOSED.
