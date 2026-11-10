# 162 — P11 Design-Consistency Repair Evidence

Status: **DEVELOPMENT REPAIR COMPLETE — READY FOR EXACT-CANDIDATE CODE REVIEW**

## Execution identity

- audit: `development/161-p11-full-design-code-consistency-audit.md`
- audit_commit: `be78d868524afb302091085856e70489bba2db24`
- previous_failed_candidate: `05e06096bc8b788d0467a1ce3442829e87727b6`
- new_production_candidate: `362877244aa553ca4d76eb71318b116cde04c6a5`
- development_branch: `task/p11-sec-rebuild-development`
- source repair predecessor: `84ce94954092a40a641fb8251b82945fa488f79`
- isolated_live_root: `D:\t\p11designrepair-live6`
- `FFDF_SEC_CONTACT_EMAIL` configured: `YES` (value not recorded)
- accepted CN/HK workspace mutation: `NONE OBSERVED`

The final production candidate contains the complete repair chain. The first
repair commit (`84ce949`) addressed P11-ISSUE-109 through P11-ISSUE-119 and
the associated orchestration, validation, table, identity, timeout, and
historical-discovery regressions. Candidate `3628772` completes the remaining
HTML source-block repair, parser determinism/performance work required for the
live Toyota document, and its unit regressions.

## Repair scope

### P11-ISSUE-109 — FIXED

Submissions discovery now tolerates safe nested `primaryDocument` paths on
unrelated rows while retaining fail-closed traversal/path rejection for the
requested filing. Regression coverage includes
`test_unrelated_nested_sec_primary_document_does_not_poison_periodic_discovery`
and `test_supported_filing_primary_document_path_traversal_is_rejected`.

### P11-ISSUE-110 — FIXED

SEC archive/member paths use one canonical, Windows-safe policy before URL
construction, download, package construction, and filesystem persistence.
Nested safe members remain supported; traversal, absolute, drive-qualified,
backslash, scheme, and host-injection forms fail closed. Regression coverage
includes `test_sec_url_allowlist_rejects_arbitrary_hosts_and_paths` and
`test_package_member_path_is_canonical_and_windows_safe`.

### P11-ISSUE-111 — FIXED

Explicit CIK is authoritative and bypasses current ticker-map lookup; ticker
resolution retains local source provenance, and stable CIK/company identity is
used by SEC orchestration/catalog paths. Market-specific CLI period validation
is enforced without changing CN/HK behavior. Regression coverage includes
`test_explicit_cik_bypasses_current_ticker_map`,
`test_cached_ticker_map_supports_local_identity_resolution_without_network`,
and `test_market_period_validation_is_scoped_before_provider_dispatch`.

### P11-ISSUE-112 — FIXED

The production US flow now integrates the incremental planner and Registry:
compatible parsed data is reused, an immutable local package is parsed locally,
and discovery/acquisition is used only when local state is absent. Successful
acquisition persists the SEC package/slot binding. Regression coverage includes
`test_us_cli_planner_uses_local_package_and_parsed_data_without_network` and
`test_incremental_planner_is_reuse_first_and_conflict_safe`.

### P11-ISSUE-113 — FIXED

Acquisition stores normalized declared content types, validates archive-index
shape and actual member bytes, and classifies filing-local XBRL members without
promoting generic/linkbase XML to the instance role. Regression coverage
includes `test_sec_acquirer_downloads_primary_and_xbrl_members_incrementally`
and `test_generic_xml_is_not_misclassified_as_xbrl_instance`.

### P11-ISSUE-114 — FIXED

SEC table artifacts now retain package/document identity separately from source
member identity and expose locator, heading/caption, row/column, nested-table,
Inline-XBRL, visibility/style, span, header-tree, source-text, cell-locator,
and fact-reference signals. Unit and P8 regressions cover `list_tables` and
`get_table`.

### P11-ISSUE-115 — FIXED

Explicit and typed dimensions remain distinct, typed-member source text is
preserved without inventing a QName, namespaced `xsi:nil` is recognized for
XML/Inline-XBRL facts, and raw QNames remain unchanged. Regression coverage is
in `test_namespaced_nil_and_explicit_typed_dimensions_are_preserved` and the
custom/raw-QName parser tests.

### P11-ISSUE-116 — FIXED

P7-US validates metadata/package/member/source/evidence/table and locator
integrity, and `reuse_eligible` requires PASS plus zero blocking issues and a
compatible artifact. The zero-fact case is explicitly `REVIEW_REQUIRED` and
not reusable via `test_periodic_zero_facts_is_review_required_and_not_research_ready`.

### P11-ISSUE-117 — FIXED

P8 SEC adapters support the existing tool family and map SEC virtual-page/raw
QName fields to the generic filters without changing CN/HK semantics. Unit
coverage exercises `list_documents`, `get_document`, `search_document`,
`read_pages`, `list_sections`, `list_tables`, `get_table`, `list_raw_facts`
with page/metric filters, `get_fact`, `get_evidence`, and `get_validation`.
The live full-tool smoke is recorded below.

### P11-ISSUE-118 — FIXED

The SEC HTTP configuration exposes bounded connect, read, and total timeout
contracts, including invalid-bound rejection and transport enforcement.
Regression coverage is in `test_http_config_exposes_connect_read_and_total_timeouts`
and the bounded transport tests.

### P11-ISSUE-119 — FIXED

Submissions history preserves `name`, `filingFrom`, and `filingTo`, and the
requested fiscal year selects only history chunks whose ranges can contain the
target. Regression coverage includes
`test_history_chunk_ranges_are_preserved_and_unrelated_chunks_are_not_selected`
and `test_sec_acquirer_fetches_only_history_chunks_covering_requested_year`.

### P11-ISSUE-120 — FIXED

SEC HTML normalization now uses cached deterministic visible-text/hidden-state
evaluation, retains source-member and DOM locators, treats common `div`/`span`
and Inline-XBRL layouts as source blocks, and avoids duplicate nested narrative.
The normalizer remains versioned as `VIRTUAL_HTML_V3`. Regression coverage
includes `test_div_span_narrative_and_inline_fact_parent_are_preserved_without_duplicates`,
`test_visible_fact_in_empty_positioning_wrappers_gets_a_cell_source_block`,
and `test_visible_fact_with_inline_positioning_text_gets_the_outer_narrative_block`.
The latter two reproduce the previously failing Toyota 20-F positioning-wrapper
patterns.

## Offline verification

- P11 focused: `78 passed in 2.35s` (`tests/unit/us_sec`)
- Full unit: `608 passed in 66.49s (0:01:06)` (`tests/unit`)
- CN/HK regression: `96 passed in 6.95s`
- `compileall -q src tests`: **PASS**, exit code `0`
- `git diff --check`: **PASS**, exit code `0`
- `SUPPORTED_MARKETS`: `("CN", "HK")`
- default `FFDF_P11_US_DEV` gate: **disabled** when unset

The first full-unit run used a long Windows temporary path and encountered
path-length failures; the required short-basetemp rerun above completed with
all `608` tests passing.

## Developer live smoke

All live work used the isolated root `D:\t\p11designrepair-live6`; no accepted
CN/HK workspace was used.

### Apple FY2025 10-K

**PASS** — acquire and ingest reached P7/P8.

- CIK: `0000320193`
- accession: `0000320193-25-000079`
- form: `10-K`
- package SHA-256: `1ced30628971dfbdb18c4c8b40421c5cac404063be84faa37fd598f997d836bb`
- primary member SHA-256: `a3be29879d5bcf2dee80597dcfc1fe3c61f8a952b91591d63ca9f9d2b2075073`
- members: `8`
- pages/tables: `81 / 62`
- Raw Facts/Evidence: `2262 / 2262`
- hidden facts: `22`
- validation: `PASS`, blocking `0`, review `0`, reuse `true`
- P8 catalog: `ADDED`; `research_ready=true`

### Apple FY2025 Q3 10-Q

**PASS** — chronology resolved the expected Q3 filing and ingest reached P8.

- CIK: `0000320193`
- accession: `0000320193-25-000073`
- form: `10-Q`
- package SHA-256: `aae2f0471f4f7de00fff2ea6609cc83177f13ce2312420aa2ce98281bb70bfc8`
- primary member SHA-256: `7f01e707635f2d48edef83db92dccc80e371df9f4e01d996e2a3dc8aabf341c5`
- members: `8`
- pages/tables: `40 / 38`
- Raw Facts/Evidence: `1538 / 1538`
- hidden facts: `9`
- validation: `PASS`, blocking `0`, review `0`, reuse `true`
- P8 catalog: `ADDED`; `research_ready=true`

### Toyota FY2025 20-F

**PASS** — the second live run after the source-block repair completed through
P7/P8. The first post-repair run exposed 30 remaining positioning-wrapper
facts; that observation led to the inline-wrapper rule and the final rerun
below.

- CIK: `0001094517`
- accession: `0001193125-25-142326`
- form: `20-F`
- package SHA-256: `e1fdbff92d1204591c7544308526fed61e44147b33dd7a6ed21a81aab7b2478a`
- primary member SHA-256: `93941e42021dad006da22cd732132d6c56d3c339a73802712926ccf462e52f23`
- members: `4`
- pages/tables: `182 / 419`
- Raw Facts/Evidence: `6746 / 6746`
- hidden facts: `7`
- validation: `PASS`, blocking `0`, review `0`, reuse `true`
- P8 catalog: `ADDED`; `research_ready=true`

### Kellanova CIK-only amendment smoke

**PASS** — the command exited `1` with the expected controlled reason:
`P11_AMENDED_VARIANT_PRESENT` (`original and amended SEC filings require review
before active binding`). Read-only submissions inspection identified the frozen
original accession `0001628280-25-007118` and amendment accession
`0000055067-25-000127`; no active binding was created.

### P8 SEC full-tool smoke

**PASS** — run against the live Apple FY2025 10-K package with
`FFDF_P11_US_DEV=1`, without network access from the query service. The catalog
contained `3` US SEC documents (Apple FY, Apple Q3, Toyota FY). All existing
P8 tool methods completed:

- `list_documents`: total `3`
- `get_document`: `81` pages, `62` tables, `2262` Raw Facts, `2262` Evidence,
  `0` issues
- `search_document`: `5` matches returned
- `read_pages`: `1` page returned
- `list_sections`: tool succeeded; returned `0` sections for this artifact
- `list_tables` / `get_table`: total `62`; document identity matched package SHA
- `list_raw_facts(metric_contains="Revenues")`: total `2`
- `get_fact` / `get_evidence`: returned matching Raw Fact/Evidence identity
- `get_validation`: `PASS`

## Governance and handoff

- production source changed after exact candidate: **NO**
- development evidence commit: this document's separate documentation commit
- main merge: `NOT RUN`
- P11 production availability: `NOT CHANGED`
- formal acceptance: `NOT RUN`
- CN/HK accepted behavior: preserved by the `96 passed` regression and the
  unchanged `SUPPORTED_MARKETS` value

The next gate is **CHATGPT CODE REVIEW OF EXACT CANDIDATE
`362877244aa553ca4d76eb71318b116cde04c6a5`**. No formal acceptance plan was
resumed or edited.
