# 156 — P11 US SEC Provider Formal Test / Acceptance Plan

Status: FORMAL_TEST_PLAN_ISSUED

Plan owner: ChatGPT independent review
Execution owner: PC Agent / local Windows environment
Final result reviewer: ChatGPT independent acceptance review

Production candidate under test:
05e06096bc8b788d0467a1ce3442829e87727b6b

Code review:
development/155-p11-code-review-result-4.md

Code-review verdict:
REVIEW_PASS

Development branch:
task/p11-sec-rebuild-development

## 1. Governance and freeze

This plan is the formal acceptance specification. PC Agent executes it; PC Agent does not redesign it, substitute easier fixtures, weaken expected outcomes, or declare final acceptance.

The tested production implementation is frozen at:
05e06096bc8b788d0467a1ce3442829e87727b6b

Before testing, verify that all commits after the production candidate contain only review/evidence/test-plan documentation. If any production source has changed after that SHA, stop with:

FORMAL_ACCEPTANCE_BLOCKED
REASON: PRODUCTION_CODE_DRIFT_AFTER_REVIEW_PASS

No production repair is allowed during formal acceptance. Any production defect requires a new production SHA, new exact-candidate code review, and re-entry into formal acceptance.

Do not merge main, change SUPPORTED_MARKETS, or change P11_SEC_PROVIDER availability during this execution.

## 2. Isolated acceptance workspace

All test artifacts must remain inside the project tree but must not mutate the accepted CN/HK workspace.

Use:
D:\Codex\FinancialFilingDataFoundation\work\p11-formal-acceptance-05e06096

as the isolated FFDF_ROOT for live P11 acceptance.

Recommended PowerShell bootstrap:

    $root = 'D:\Codex\FinancialFilingDataFoundation'
    $accept = Join-Path $root 'work\p11-formal-acceptance-05e06096'
    $tmp = Join-Path $accept 'tmp'
    $py = Join-Path $root '.venv\Scripts\python.exe'

    New-Item -ItemType Directory -Force -Path $accept,$tmp | Out-Null

    $env:FFDF_ROOT = $accept
    $env:FFDF_P11_US_DEV = '1'
    $env:PYTHONPATH = (Join-Path $root 'src')
    $env:TEMP = $tmp
    $env:TMP = $tmp

Do not copy or alter accepted CN/HK raw/source artifacts.

## 3. SEC contact precondition

Live SEC execution requires a monitored contact identity already supplied by the operator:
FFDF_SEC_CONTACT_EMAIL

Check only whether it is configured; do not record its actual value in tracked evidence.

If it is missing or invalid, execute all offline gates that do not require network, then stop live acceptance with:

LIVE_SEC = BLOCKED
REASON = FFDF_SEC_CONTACT_EMAIL_NOT_SET
FORMAL_ACCEPTANCE = BLOCKED

Do not invent an email and do not bypass the gate.

## 4. Frozen official SEC live fixtures

The following fixtures are frozen by this plan. PC Agent must not substitute other filings without a new ChatGPT test-plan revision.

### FIXTURE-A — Apple domestic annual / Inline XBRL

company: Apple Inc.
ticker: AAPL
CIK: 0000320193
fiscal year: 2025
FFDF period: FY
form: 10-K
accession: 0000320193-25-000079
filing date: 2025-10-31
report period: 2025-09-27
primary document: aapl-20250927.htm
SEC archive index:
https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/0000320193-25-000079-index.htm

Purpose: FT-01 domestic annual, live immutable package, parser/P7/P8, and FT-08 idempotency.

### FIXTURE-B — Apple domestic quarterly / Inline XBRL / custom taxonomy

company: Apple Inc.
ticker: AAPL
CIK: 0000320193
fiscal year: 2025
FFDF period: Q3
form: 10-Q
accession: 0000320193-25-000073
filing date: 2025-08-01
report period: 2025-06-28
primary document: aapl-20250628.htm
extension schema: aapl-20250628.xsd
SEC archive index:
https://www.sec.gov/Archives/edgar/data/320193/000032019325000073/0000320193-25-000073-index.htm

Purpose: FT-02 domestic Q3 chronology, FT-03 custom extension, live Evidence round-trip, hidden Inline XBRL check where present.

### FIXTURE-C — Kellanova original + amendment

company: Kellanova
ticker: K
CIK: 0000055067
fiscal year: 2024
FFDF period: FY
report period: 2024-12-28

Original:
form: 10-K
accession: 0001628280-25-007118
filing date: 2025-02-21
SEC archive index:
https://www.sec.gov/Archives/edgar/data/55067/000162828025007118/0001628280-25-007118-index.htm

Amendment:
form: 10-K/A
accession: 0000055067-25-000127
filing date: 2025-03-07
SEC archive index:
https://www.sec.gov/Archives/edgar/data/55067/000005506725000127/0000055067-25-000127-index.htm

Purpose: FT-04. Discovery/acquisition must not silently choose either package.
Expected reason: P11_AMENDED_VARIANT_PRESENT

### FIXTURE-D — Toyota foreign private issuer

company: Toyota Motor Corporation
ticker: TM
CIK: 0001094517
fiscal year: 2025
FFDF period: FY
form: 20-F
accession: 0001193125-25-142326
filing date: 2025-06-18
report period: 2025-03-31
primary document: d925022d20f.htm
extension schema: tm-20250331.xsd
SEC archive index:
https://www.sec.gov/Archives/edgar/data/1094517/000119312525142326/0001193125-25-142326-index.htm

Purpose: FT-05 FPI annual 20-F. Quarterly 6-K mapping remains unsupported/fail-closed.

## 5. FT-00 — Preflight gate

Run:

    Set-Location 'D:\Codex\FinancialFilingDataFoundation'
    git branch --show-current
    git status --short
    git rev-parse HEAD
    git rev-parse 05e06096bc8b788d0467a1ce3442829e87727b6b
    git diff --check

Also compare the reviewed candidate to current development branch and list every post-candidate changed path.

PASS criteria:
- branch = task/p11-sec-rebuild-development
- candidate exists exactly
- no post-candidate production source change
- no unknown dirty production changes
- git diff --check PASS
- documentation added after the candidate is permitted

## 6. FT-01 — live domestic 10-K end-to-end

Use FIXTURE-A.

Run live acquire:

    & $py -m financial_filing_data_foundation.user_cli acquire --market US --ticker AAPL --cik 320193 --year 2025 --period FY

The first isolated-workspace acquire must resolve exactly:
- accession 0000320193-25-000079
- form 10-K
- one 64-hex package_sha256
- package path inside $accept
- status DOWNLOADED on a genuinely clean acceptance workspace

Then ingest:

    & $py -m financial_filing_data_foundation.user_cli ingest --market US --ticker AAPL --cik 320193 --year 2025 --period FY

PASS requires:
- exact frozen accession
- identical package SHA to acquire
- validation_status = PASS
- blocking_issue_count = 0
- research_ready = true
- P8 catalog registration succeeds
- artifact directory is inside isolated acceptance root
- package manifest and all members load successfully through SecPackageStore.load
- no CN/HK workspace mutation

Record package SHA, primary member SHA, member count, Raw Fact count, Evidence count, hidden fact count, validation result, catalog result, artifact path.

## 7. FT-02 — live domestic 10-Q chronology end-to-end

Use FIXTURE-B.

Run:

    & $py -m financial_filing_data_foundation.user_cli acquire --market US --ticker AAPL --cik 320193 --year 2025 --period Q3
    & $py -m financial_filing_data_foundation.user_cli ingest  --market US --ticker AAPL --cik 320193 --year 2025 --period Q3

PASS requires exact:
- accession 0000320193-25-000073
- form 10-Q
- report period 2025-06-28
- validation PASS
- zero blocking issues
- research_ready true
- package/member hashes verify
- Raw Facts and Evidence are non-zero
- P8 read succeeds without network

This is also a live check that Apple FY2025 Q3 is mapped by source chronology, not by a calendar-quarter assumption.

## 8. FT-03 — custom extension + Evidence round-trip + hidden iXBRL

Use the already-ingested FIXTURE-B. Do not acquire a substitute filing.

### FT-03A custom extension

Inspect raw_facts.jsonl.

PASS requires at least one real filing fact with raw_qname beginning with:
aapl:

For at least one such custom fact:
- raw_qname is preserved
- evidence_id exists
- referenced Evidence exists
- Evidence member belongs to the immutable package
- source text/node resolves
- fragment hash verifies
- validation does not canonicalize the custom concept into a guessed standard metric

If no aapl: fact is found in this frozen filing, FT-03A FAILS. Do not replace the fixture.

### FT-03B live Evidence sample

Deterministically select:
1. first custom aapl: fact by raw_fact_id sort
2. first visible DOM_PATH fact by raw_fact_id sort
3. first XML_PATH fact by raw_fact_id sort, if XML Evidence exists

For every selected fact, call existing verification logic against the loaded immutable package and require successful round-trip.

### FT-03C hidden Inline XBRL

Count live facts where hidden == true.

If count > 0:
- sampled hidden facts must have Evidence
- locator kind must be DOM_HIDDEN_FACT
- DOM locator resolves to ix:nonfraction or ix:nonnumeric
- node is below ix:hidden
- raw text and fragment hash verify

If FIXTURE-B contains zero hidden facts, record LIVE_HIDDEN_FACT_NOT_PRESENT_IN_FROZEN_FIXTURE; deterministic hidden-fact unit tests in FT-06 remain mandatory. Zero hidden facts alone does not fail the entire acceptance.

## 9. FT-04 — amendment conflict live gate

Use FIXTURE-C.

Run:

    & $py -m financial_filing_data_foundation.user_cli acquire --market US --ticker K --cik 55067 --year 2024 --period FY

Expected outcome is non-zero with exact reason:
P11_AMENDED_VARIANT_PRESENT

PASS requires:
- discovery sees original and amendment for the same fiscal slot
- no silent original/amendment selection
- no active package binding is published for the conflicted slot
- original and amendment are not treated as two required fiscal slots

A successful normal acquire is FT-04 FAIL.

## 10. FT-05 — live FPI 20-F

Use FIXTURE-D.

Run:

    & $py -m financial_filing_data_foundation.user_cli acquire --market US --ticker TM --cik 1094517 --year 2025 --period FY
    & $py -m financial_filing_data_foundation.user_cli ingest  --market US --ticker TM --cik 1094517 --year 2025 --period FY

PASS requires:
- exact accession 0001193125-25-142326
- form 20-F
- report period 2025-03-31
- package/member SHA verification
- non-zero structured facts
- non-zero Evidence
- validation PASS
- zero blocking issues
- research_ready true
- P8 read succeeds without network

Also run existing deterministic FPI policy tests proving 6-K is not guessed as quarterly mapping.

## 11. FT-06 — deterministic negative/security/evidence gates

Run the complete P11 unit suite and separately report these required tests as present and passing.

test_http_discovery.py:
- test_sec_url_allowlist_rejects_arbitrary_hosts_and_paths
- test_http_client_declares_user_agent_and_enforces_size_and_content_type
- test_http_client_rejects_unhandled_content_encoding
- test_redirect_handler_checks_each_hop_and_configures_redirect_limit
- test_network_transport_enforces_redirect_limit_and_bounded_error_body
- test_network_transport_bounds_non_redirect_http_error_body
- test_historical_year_missing_target_annual_does_not_use_in_progress_fallback
- test_fpi_20f_and_40f_are_annual_candidates_only

test_package_registry.py:
- test_package_hash_is_canonical_and_store_is_immutable
- test_incremental_planner_is_reuse_first_and_conflict_safe

test_parser.py:
- test_hidden_inline_numeric_and_nonnumeric_facts_are_valid_source_evidence
- test_hidden_fact_corrupt_locator_or_hash_is_blocked
- test_visible_inline_fact_still_requires_a_block_anchor
- test_xml_instance_facts_preserve_source_qname_and_locator
- test_validation_blocks_corrupt_html_evidence_round_trip

test_validation_p8.py:
- test_periodic_zero_facts_is_review_required_and_not_research_ready
- test_facts_without_evidence_are_blocked
- test_p8_revalidates_raw_sec_package_before_serving
- test_sec_p8_reads_catalog_entry_without_network

test_provider_cli.py:
- test_sec_acquirer_does_not_silently_select_amendment
- test_sec_acquirer_downloads_primary_and_xbrl_members_incrementally

Any failure is a formal acceptance failure.

## 12. FT-07 — throttling/access-denied simulation

Do not intentionally provoke the live SEC service.

Use a local acceptance-only harness under the isolated work directory, importing the reviewed production implementation without changing tracked production source.

Required simulations:

429 terminal case:
- transport returns HTTP 429 on every attempt
- attempts stop exactly at configured max_attempts
- final reason = P11_SEC_RATE_LIMITED
- no silent success
- retry delay is bounded

403 terminal case:
- transport returns HTTP 403 on every attempt
- attempts stop exactly at configured max_attempts
- final reason = P11_SEC_ACCESS_DENIED
- no silent success
- retry delay is bounded

Retry-After recovery:
- test_rate_limiter_and_retry_after_are_deterministic must PASS

Redirect/error-body bounds:
- FT-06 redirect-limit and bounded-error-body tests must PASS

The harness file stays under work\p11-formal-acceptance-05e06096 and must not be added to production source.

## 13. FT-08 — live idempotency

Use FIXTURE-A only.

After FT-01, capture:
- package SHA
- SHA256 of package manifest bytes
- SHA256 of every raw package member
- artifact directory
- parser version
- Raw Fact count
- Evidence count
- P8 catalog identity

Then rerun:

    & $py -m financial_filing_data_foundation.user_cli acquire --market US --ticker AAPL --cik 320193 --year 2025 --period FY
    & $py -m financial_filing_data_foundation.user_cli ingest  --market US --ticker AAPL --cik 320193 --year 2025 --period FY

PASS requires:
- second acquire status = REUSED_LOCAL
- same accession
- same package SHA
- all package member hashes unchanged
- manifest bytes/hash unchanged
- same parser version
- deterministic parsed artifact identity/content
- same Raw Fact count and Evidence count
- second P8 catalog action = ALREADY_REGISTERED
- Registry does not create a conflicting active slot
- no network re-download of known package members after local package reuse

If the final network condition needs request instrumentation, use an acceptance-only harness around the existing transport; do not patch production code.

## 14. Full regression gates

P11 focused:

    & $py -m pytest -q --basetemp (Join-Path $tmp 'p11') tests/unit/us_sec

Development baseline: 53 passed.
Formal result: no failures.

Full unit suite:

    & $py -m pytest -q --basetemp (Join-Path $tmp 'unit') tests/unit

Development baseline: 583 passed.
Formal result: no failures.

CN/HK regression:

    & $py -m pytest -q --basetemp (Join-Path $tmp 'cnhk') tests/unit/identity tests/unit/registry tests/unit/mcp tests/unit/user_cli

Development baseline: 96 passed.
Formal result: no failures.

Compile:

    & $py -m compileall -q src tests

Expected: PASS.

Diff:

    git diff --check

Expected: PASS.

## 15. Evidence requirements

PC Agent must create:
development/157-p11-formal-acceptance-evidence.md

Do not create or alter the test plan; this file 156 is the test plan.

Evidence must include:
- exact production candidate
- exact plan path and plan commit
- branch and HEAD at execution
- post-candidate changed path list
- Python version
- FFDF_SEC_CONTACT_EMAIL configured = YES/NO only; never record address
- isolated FFDF_ROOT path
- execution timestamp
- FT-00 through FT-08 separately
- exact frozen accession observed for every live fixture
- package SHA/member hashes for live successful fixtures
- Raw Fact/Evidence/hidden-fact counts
- validation/P8 result
- amendment exact reason code
- 403/429 simulation attempt counts and reason codes
- idempotency before/after hashes
- focused/full/CN-HK regression output
- compileall and diff-check result
- explicit declaration whether production source changed during acceptance

Preserve raw command output under:
work\p11-formal-acceptance-05e06096\evidence\

The Markdown evidence must reference those local evidence files by relative path and include decisive values, not merely say see log.

## 16. Formal decision rule

PC Agent must not make the final project acceptance decision. It may report only one execution result:

EXECUTION_PASS — every required FT-00..FT-08 and regression gate passed
EXECUTION_FAIL — at least one executed required gate failed
EXECUTION_BLOCKED — a required gate could not execute, including missing SEC contact identity

Even if EXECUTION_PASS:
- do not merge main
- do not change SUPPORTED_MARKETS
- do not change P11 capability availability
- do not edit README/PROJECT_STATUS to production-ready
- do not announce P11 DONE

Stop and submit the exact evidence commit to ChatGPT for independent final acceptance review.

## 17. Required final PC Agent handoff

Return:

P11 FORMAL TEST EXECUTION: COMPLETE

Production candidate:
05e06096bc8b788d0467a1ce3442829e87727b6b

Formal test plan:
development/156-p11-formal-test-plan.md

Formal acceptance evidence:
development/157-p11-formal-acceptance-evidence.md

Evidence commit:
<exact SHA>

FT-00 Preflight:
<PASS/FAIL/BLOCKED>

FT-01 Apple 2025 10-K:
<PASS/FAIL/BLOCKED>

FT-02 Apple 2025 Q3 10-Q:
<PASS/FAIL/BLOCKED>

FT-03 Custom extension / Evidence:
<PASS/FAIL/BLOCKED>

FT-04 Kellanova amendment:
<PASS/FAIL/BLOCKED>

FT-05 Toyota 2025 20-F:
<PASS/FAIL/BLOCKED>

FT-06 Negative/security:
<PASS/FAIL/BLOCKED>

FT-07 Throttling/access denied:
<PASS/FAIL/BLOCKED>

FT-08 Idempotency:
<PASS/FAIL/BLOCKED>

P11 focused:
<result>

Full unit suite:
<result>

CN/HK regression:
<result>

Compileall:
<result>

git diff --check:
<result>

Live SEC:
<RUN/BLOCKED>

Production code changed during acceptance:
NO

Execution result:
<EXECUTION_PASS/EXECUTION_FAIL/EXECUTION_BLOCKED>

Main merge:
NOT RUN

P11 production availability:
NOT CHANGED

Next action:
CHATGPT FINAL ACCEPTANCE REVIEW
