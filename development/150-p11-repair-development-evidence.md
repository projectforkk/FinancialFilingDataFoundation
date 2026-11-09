# P11 REPAIR DEVELOPMENT RESULT

reviewed_candidate:
529376cc084bd9990c144102fa723822b5229e1a

review_result:
development/149-p11-code-review-result.md

new_production_candidate_sha:
9bf84e1aeaca33f49830ada50b7876a2f36f04eb

development_branch:
task/p11-sec-rebuild-development

production_commit:
`fix: repair P11 SEC review findings`

## Issue repairs

### P11-ISSUE-101

root cause:
The discovery path mapped report-period calendar months to Q1/Q2/Q3/FY and required the report-period calendar year to equal the requested fiscal year.

fix:
Added official `fiscalYearEnd` metadata handling, deterministic fiscal-year interval classification, fiscal-quarter boundary calculation compatible with 52/53-week dates, and chronological/history metadata propagation. Calendar-month lookup and the unconditional report-period year-prefix rule were removed.

tests:
- `test_discovery_uses_fiscal_year_end_and_chronology_for_non_calendar_issuers`
- `test_discovery_supports_fpi_non_december_fiscal_year`
- `test_ticker_mapping_and_submission_discovery_are_fail_closed`
- SEC acquisition tests with official fiscal-year-end metadata

result:
PASS

### P11-ISSUE-102

root cause:
P7 did not require structured facts/evidence and ingest treated every zero-blocking result as research-ready.

fix:
Added `P11_STRUCTURED_FACTS_MISSING`; periodic SEC artifacts with zero facts become `REVIEW_REQUIRED`, facts without evidence remain blocking, and ingest publishes only a true `PASS` with complete source-aware fact/evidence validation.

tests:
- `test_periodic_zero_facts_is_review_required_and_not_research_ready`
- `test_facts_without_evidence_are_blocked`
- positive Inline-XBRL fixture with context, unit, Raw Fact, and Evidence

result:
PASS

### P11-ISSUE-103

root cause:
The client advertised gzip while the stdlib transport did not decode `Content-Encoding: gzip`.

fix:
Removed the unsupported gzip advertisement and fail closed on an unexpected response encoding.

tests:
- `test_http_client_declares_user_agent_and_enforces_size_and_content_type`
- `test_http_client_rejects_unhandled_content_encoding`

result:
PASS

### P11-ISSUE-104

root cause:
`SecHttpConfig.max_redirects` was not connected to the redirect handler, and HTTP error-body reads were unbounded.

fix:
Wired the configured limit through network and subprocess transports, retained per-hop HTTPS/SEC host/path validation, added an explicit redirect-limit reason, and bounded HTTP error-body reads.

tests:
- `test_redirect_handler_checks_each_hop_and_configures_redirect_limit`
- `test_network_transport_enforces_redirect_limit_and_bounded_error_body`
- `test_network_transport_bounds_non_redirect_http_error_body`

result:
PASS

### P11-ISSUE-105

root cause:
Evidence used a fact fragment hash as `block_id`, while P7 only checked that a DOM locator began with `/`.

fix:
Parser artifacts now use `VIRTUAL_HTML_V2`; HTML Evidence references a real normalized source block and keeps a separate fact locator/fragment hash. P7/P8 resolve HTML DOM paths and block locators against immutable member bytes. XML evidence uses a separate deterministic `XML_PATH` locator. Block, fact, member, and locator hashes are checked on round-trip.

tests:
- `test_html_parser_creates_stable_virtual_pages_dom_tables_and_evidence`
- `test_validation_blocks_corrupt_html_evidence_round_trip` (block, DOM locator, member SHA, fragment hash)
- `test_xml_instance_facts_preserve_source_qname_and_locator`

result:
PASS

### P11-ISSUE-106

root cause:
P8 loaded derived SEC artifacts without re-reading the immutable raw package and its members.

fix:
P8 deterministically resolves `workspace/ingest/raw-store`, verifies package manifest identity, package SHA, every member SHA/size, and every Evidence member/locator. The source chain is revalidated even for a cached P8 bundle.

tests:
- `test_p8_revalidates_raw_sec_package_before_serving[member]`
- `test_p8_revalidates_raw_sec_package_before_serving[delete]`
- `test_p8_revalidates_raw_sec_package_before_serving[manifest]`

result:
PASS

### P11-ISSUE-107

root cause:
The parser read XML contexts/units but did not extract XML instance facts.

fix:
Implemented stdlib-only XBRL instance fact extraction for `XBRL_INSTANCE` members, preserving raw QName, text, numeric candidate, context/unit references, period/entity/dimensions, decimals/precision, nil, member SHA, XML locator, and source Evidence. Inline and XML sources remain distinct raw facts.

tests:
- `test_xml_instance_facts_preserve_source_qname_and_locator`
- XML numeric and non-numeric facts with custom QName and XML Evidence round-trip

result:
PASS

## Verification

focused P11:
`$env:PYTHONPATH=(Resolve-Path 'src').Path; & 'D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe' -m pytest -q --basetemp=D:\t tests/unit/us_sec`

result:
`41 passed in 1.97s`

full suite:
`$env:PYTHONPATH=(Resolve-Path 'src').Path; & 'D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe' -m pytest -q --basetemp=D:\t`

result:
`571 passed in 63.48s`

CN/HK regression:
`$env:PYTHONPATH=(Resolve-Path 'src').Path; & 'D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe' -m pytest -q --basetemp=D:\t tests/unit/identity tests/unit/registry tests/unit/mcp tests/unit/user_cli`

result:
`96 passed in 8.08s`

compileall:
`& 'D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe' -m compileall -q src tests/unit/us_sec`

PASS

git diff --check:
`git diff --check`

PASS

## Safety declarations

accepted CN/HK raw/source artifacts mutated = NO

remote AI/API called by FFDF production code = NO

main merged = NO

formal acceptance performed = NO

formal test plan issued = NO
