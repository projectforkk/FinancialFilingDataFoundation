# 160 — P11 Final Acceptance Review — Live Discovery Failure

Status: **FINAL_ACCEPTANCE_FAIL**

Reviewed production candidate: 05e06096bc8b788d0467a1ce3442829e87727b6b
Live continuation evidence: development/159-p11-live-acceptance-continuation-evidence.md
Evidence commit: 31c0f94934d19675fd0948177a8d2f2d764d0af3

## 1. Lineage

PASS. Evidence commit 31c0f949... adds only development/159-p11-live-acceptance-continuation-evidence.md. From the reviewed candidate through the evidence commit/current branch there are no production or test source changes.

## 2. Frozen fixture verification

Official SEC filing pages confirm the frozen target filings are valid:
- Apple FY2025 10-K: accession 0000320193-25-000079, report period 2025-09-27, primary document aapl-20250927.htm.
- Apple FY2025 Q3 10-Q: accession 0000320193-25-000073, report period 2025-06-28, primary document aapl-20250628.htm.
- Toyota FY2025 20-F: accession 0001193125-25-142326, report period 2025-03-31, primary document d925022d20f.htm.

The target primary documents are simple safe archive member names. The repeated live error P11_SEC_DISCOVERY_FAILED / SEC primary document path is unsafe is therefore not caused by the frozen target filing primary documents.

## 3. P11-ISSUE-109 — unrelated valid nested SEC primaryDocument aborts whole submissions discovery

Severity: BLOCKING.

Affected gates:
- FT-01 Apple 10-K: FAIL
- FT-02 Apple 10-Q: FAIL
- FT-05 Toyota 20-F: FAIL
- FT-03: BLOCKED downstream of FT-02
- FT-08: BLOCKED downstream of FT-01

Root cause in candidate 05e06096:
- parse_submissions() iterates every SEC submissions-history row before requested filing-slot selection.
- For every row it constructs SecFilingCandidate.source_url through _candidate_url().
- _candidate_url() uses _SAFE_MEMBER_RE = ^[^/\\]+$ and rejects any primaryDocument containing '/'.
- This rejection occurs before discover_filings() filters to supported P11 forms / requested fiscal slot.
- SEC submissions history legitimately contains safe nested archive-relative primary-document paths, including Section 16 forms such as xslF345X06/form4.xml.
- Therefore one unrelated legitimate filing can poison the complete issuer submissions parse and block discovery of an otherwise valid 10-K, 10-Q, 20-F, or 40-F.

This behavior reproduced across Apple domestic annual, Apple domestic quarterly, and Toyota FPI annual live tests, so it is a production discovery defect rather than a single-fixture anomaly.

Security requirement: the repair must continue to reject absolute paths, '..' traversal, '.' path components, backslash/non-canonical traversal, URL/host injection, and other unsafe archive-relative paths.

Required behavior:
- valid canonical SEC archive-relative nested primaryDocument must not poison periodic discovery;
- unsafe traversal / absolute / injected path must remain fail-closed.

Equivalent implementation is acceptable if it either safely supports canonical nested paths or avoids constructing candidate source URLs for irrelevant unsupported filing rows before form filtering.

## 4. Required ISSUE-109 regressions

At minimum add:

1. test_unrelated_nested_sec_primary_document_does_not_poison_periodic_discovery
   - fixture contains an unrelated unsupported filing with primaryDocument xslF345X06/form4.xml;
   - fixture also contains a target 10-K or 10-Q with a normal primary document;
   - parse/discovery must succeed for the target;
   - unrelated filing must not become a required fiscal candidate.

2. test_supported_filing_primary_document_path_traversal_is_rejected
   - supported target filing uses ../evil.htm;
   - result must remain fail-closed with deterministic P11 path/discovery failure.

If the repair chooses direct nested-path support, add positive and negative canonical nested-path safety coverage as well.

## 5. FT-04 Kellanova classification

FT-04 returned P11_INVALID_US_IDENTITY / ticker not found: K before amendment discovery.

The frozen Kellanova filings themselves remain valid:
- original 10-K accession 0001628280-25-007118;
- 10-K/A accession 0000055067-25-000127;
- both report period 2024-12-28.

The acceptance command used both --ticker K and --cik 55067. The CLI therefore cross-checked K against the current SEC company_tickers.json association. Kellanova was acquired by Mars and delisted in December 2025; the current SEC ticker association no longer contains Kellanova/K. SEC also states ticker association files are periodically updated and accuracy/scope is not guaranteed.

Design 26 states that US stable identity is CIK-based, ticker is a display/query alias, and a user may provide CIK explicitly to bypass ticker lookup.

Therefore FT-04 is classified as ACCEPTANCE_PLAN_COMMAND_CORRECTION, not as proof of an amendment-policy production defect.

FT-04 must be retried after the production repair using CIK-only:

  python -m financial_filing_data_foundation.user_cli acquire --market US --cik 55067 --year 2024 --period FY

The frozen company, fiscal slot, original accession, amendment accession, and expected reason remain unchanged. Expected reason remains P11_AMENDED_VARIANT_PRESENT.

## 6. Other accepted results

- FT-00: PASS
- FT-06: PASS carried forward
- FT-07: PASS carried forward
- P11 focused: 53 passed
- Full unit: 583 passed
- CN/HK regression: 96 passed
- compileall: PASS
- git diff --check: PASS

These do not override the mandatory live-gate failures.

## 7. Final verdict

P11 FINAL ACCEPTANCE REVIEW: FAIL

Production candidate: 05e06096bc8b788d0467a1ce3442829e87727b6b
Previous code-review status: REVIEW_PASS, but live acceptance exposed a new blocking production defect.
P11-ISSUE-109: OPEN — BLOCKING
FT-01: FAIL — ISSUE-109
FT-02: FAIL — ISSUE-109
FT-03: BLOCKED — FT-02 dependency
FT-04: NOT VALIDLY EXERCISED — retry CIK-only
FT-05: FAIL — ISSUE-109
FT-06: PASS
FT-07: PASS
FT-08: BLOCKED — FT-01 dependency
Formal acceptance: FAIL
Main merge: NOT AUTHORIZED
P11 production availability: NOT AUTHORIZED

## 8. Required next action

Return from acceptance to one minimal development repair cycle for P11-ISSUE-109 only.

Do not change parser/evidence semantics, fiscal chronology, Registry/P8/P9/P10 behavior, amendment policy, accepted CN/HK behavior, SUPPORTED_MARKETS, or P11 capability availability.

Required development verification:
1. add ISSUE-109 focused regressions;
2. run P11 focused tests;
3. run full unit suite;
4. run CN/HK regression;
5. compileall;
6. git diff --check;
7. create a new exact production candidate commit;
8. create a separate development evidence commit;
9. stop for ChatGPT exact-candidate code review.

Do not continue formal live acceptance against 05e06096bc8b788d0467a1ce3442829e87727b6b.

After a new candidate receives REVIEW_PASS, formal acceptance must re-run the affected live gates against the same frozen accessions, retry FT-04 with CIK-only invocation, and re-run regression/security gates for the new candidate.