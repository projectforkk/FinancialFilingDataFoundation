# 161 — P11 Full Design / Code Consistency Audit

Status: **CHANGES_REQUIRED — FULL CONSISTENCY REPAIR BEFORE NEW ACCEPTANCE**

Audit target production candidate:
`05e06096bc8b788d0467a1ce3442829e87727b6b`

Current branch:
`task/p11-sec-rebuild-development`

Preceding live-failure review:
`development/160-p11-final-acceptance-review-failed-live-discovery.md`

## 1. Audit authority and method

This audit re-checks the complete tracked P11 implementation against the frozen/current design instead of reviewing only the live ISSUE-109 failure.

Normative/current design sources reviewed:
- `design/26-p11-sec-provider-design.md`
- `design/27-p11-implementation-plan.md`
- `design/32-p11-us-scope-reopening.md`
- `development/147-p11-us-scope-reopening-authorization.md`

Tracked implementation scope reviewed at exact candidate:
- all 18 modules under `src/financial_filing_data_foundation/us_sec/`;
- `src/financial_filing_data_foundation/identity/models.py`;
- `src/financial_filing_data_foundation/registry/__init__.py`;
- `src/financial_filing_data_foundation/registry/sqlite_registry.py`;
- `src/financial_filing_data_foundation/mcp/catalog.py`;
- `src/financial_filing_data_foundation/mcp/service.py`;
- `src/financial_filing_data_foundation/user_cli.py`;
- `runtime-locks/sec-stdlib-py314-win-arm64.lock.txt`;
- all seven `tests/unit/us_sec/test_*.py` files.

Local Desktop Commander device was offline during this audit, so GitHub tracked bytes at the exact candidate are the source of truth. No local-only state is claimed.

## 2. Areas substantially consistent with design

The following implementation areas are substantially aligned and are not reopened absent regression:
- US remains development-gated and accepted `SUPPORTED_MARKETS` remains exactly `(CN, HK)`;
- CIK-normalized company identity exists and accession is persisted as filing identity;
- domestic 10-K/10-Q and FPI 20-F/40-F form policy exists; 6-K quarterly auto-mapping remains fail-closed;
- amendments are not silently selected;
- chronology repairs P11-ISSUE-101 through P11-ISSUE-108 remain in place;
- SEC host allowlist, HTTPS, User-Agent/contact gate, 8 rps limiter, 403/429 handling, redirect validation, size bounds, and no-shell subprocess transport are implemented;
- package SHA is deterministic over sorted member role/name/hash/size records;
- package store is content-addressed, staged, hash-verified, and source-drift aware;
- additive SEC Registry tables preserve legacy CN/HK `PRAGMA user_version=1`; separate SEC schema version is intentionally documented;
- virtual HTML pagination is explicit and versioned;
- Inline XBRL/custom QName extraction, source evidence, hidden-fact evidence, XML evidence, and raw-package revalidation exist;
- P8 SEC loading is local/read-only and revalidates evidence against the immutable raw package;
- no remote AI/LLM dependency is present in the P11 production path;
- stdlib SEC runtime lock exists.

## 3. Confirmed design/code deviations

### P11-ISSUE-109 — unrelated valid nested SEC primaryDocument poisons issuer discovery
Severity: BLOCKING / LIVE CONFIRMED.

`parse_submissions()` constructs a source URL for every submissions row before requested form/slot filtering. `_candidate_url()` rejects every primaryDocument containing `/`. Legitimate unrelated SEC filings can use safe nested archive-relative names such as `xslF345X06/form4.xml`, causing the complete issuer submissions parse to fail before a valid 10-K/10-Q/20-F is selected.

Live evidence reproduced this on Apple 10-K, Apple 10-Q, and Toyota 20-F.

Required repair: allow canonical safe nested SEC relative paths or defer URL construction/path validation for irrelevant unsupported rows, while preserving strict traversal/host injection rejection.

### P11-ISSUE-110 — archive/member path safety is not canonical or Windows-safe end-to-end
Severity: BLOCKING SECURITY.

`package._safe_relative_name()` normalizes backslashes to `/` and checks a `PurePosixPath`, but does not reject Windows drive-qualified values such as `C:/evil`. On Windows a later filesystem join can treat a drive-qualified child as escaping the package root.

`acquisition.py` also uses `urljoin(base_url, name)` on archive-index names before a package-member path validator protects the filesystem. `../`, absolute, scheme/netloc, encoded traversal, or non-canonical member names must be rejected before any member request. If nested target primary documents are supported, deriving the accession directory by `candidate.source_url.rsplit('/', 1)` is also wrong because it may derive a nested subdirectory instead of the accession root.

Required repair: one canonical SEC archive-relative path policy shared by discovery/acquisition/package storage; validate before URL construction/fetch and before filesystem write; derive archive root from CIK + normalized accession; prove final URL remains below the exact accession directory; reject absolute, drive-qualified, `.`, `..`, backslash/non-canonical, scheme/netloc and traversal/injection forms.

### P11-ISSUE-111 — CIK-first identity contract is not honored consistently
Severity: BLOCKING IDENTITY / CLI / CATALOG.

Design says CIK is stable identity, ticker is an alias, and explicit `--cik` takes precedence / may bypass ticker lookup. Current `_us_company_and_client()` still fetches the current ticker map and requires the supplied ticker to resolve when both CIK and ticker are given. This caused historical/delisted Kellanova to fail before amendment discovery.

Additional identity drift exists in P8/catalog orchestration: SEC catalog filing identity and upsert/status matching are ticker-based, so the same CIK/package acquired through a ticker alias versus CIK-only alias can conflict or become invisible to status.

The ticker resolver defines snapshot metadata but the live CLI path does not persist/cache the source bytes, SHA, retrieved_at and source URL required by design.

Global CLI period parsing also accepts `H1` for US and `Q2` for CN/HK before later market-specific failure, rather than enforcing the designed market-specific period contract at the CLI boundary.

Required repair: explicit CIK is authoritative and must not depend on current ticker mapping; keep ticker as display alias only; use stable US company_id/CIK for SEC catalog/upsert/status identity; persist deterministic ticker-map provenance/cache when ticker resolution is actually used; enforce market-specific period validation without changing accepted CN/HK semantics.

### P11-ISSUE-112 — incremental planner is implemented but not integrated into production orchestration
Severity: BLOCKING ARCHITECTURE / INCREMENTAL.

`plan_sec_slot()` implements REUSE_DATA / PARSE_LOCAL / DISCOVER_AND_ACQUIRE / REVIEW_REQUIRED, but the US CLI/acquisition path does not call it. `_us_ingest()` always enters `_us_acquire()`, and `SecAcquirer.acquire()` fetches submissions before checking for a local package by accession.

`ffdf acquire --market US` also creates a Registry object but does not register the successful SEC package/slot; Registry persistence happens only during ingest. Therefore status/reuse cannot implement the design planner order after acquire.

Required repair: integrate Registry + package + compatible parsed-run state into US acquire/ingest/status orchestration so compatible parsed data performs REUSE_DATA without network, local immutable package performs PARSE_LOCAL without network, absent data performs DISCOVER_AND_ACQUIRE, and amendment conflicts remain review-required. Successful acquire must persist the source package/binding consistently with CLI contract.

### P11-ISSUE-113 — acquisition metadata and source-byte validation are incomplete
Severity: HIGH / SECURITY-CORRECTNESS.

`SecPackageMember.content_type` is populated from the HTTP header *key* rather than its value, so stored manifest/Registry content type can become `content-type` instead of `text/html` / `application/xml`.

Archive index shape is not robustly validated before iteration, and selected XBRL member handling is extension/role based in ways that can misclassify linkbases (for example definition XML as XBRL instance) and omit other legitimate filing-local XBRL extensions such as `.xbrl`.

Design requires content-type and actual-byte validation. Current HTTP checks declared MIME, while JSON is parsed later; primary HTML/XML member bytes are not consistently validated before package commit.

Required repair: persist actual normalized header values; validate archive-index structure deterministically; classify required XBRL members without treating every generic XML as an instance; support required filing-local XBRL members including safe `.xbrl` where applicable; add deterministic byte/content plausibility validation before accepting a source package, without loading remote subresources or executing filing code.

### P11-ISSUE-114 — HTML table artifact does not satisfy the P4/P5-US table contract
Severity: HIGH DESIGN MISMATCH.

Design 26 §15 requires source locator, heading/caption context, row/column counts, nested-table signal, Inline-XBRL-fact presence, visibility/style signals, rowspan/colspan, header tree, source text, fact references, and DOM locator per cell.

Current `_tables()` lacks heading/caption context, nested-table signal, Inline XBRL presence, and visibility/style/candidate signals. It also writes table `document_sha256` as the primary member SHA rather than package/document identity; source-member identity should be separate.

Required repair: emit the full designed deterministic table metadata and preserve package/document versus source-member identities distinctly; add P8 list/get-table regressions.

### P11-ISSUE-115 — XBRL fact/context fidelity is incomplete
Severity: HIGH DATA-FIDELITY.

Design requires explicit/typed dimensions and nil semantics to be preserved. Current context extraction collapses explicitMember and typedMember into the same shape and sets `member_qname` to flattened text even for typed dimensions. Inline/XML nil detection looks for an unqualified `nil` attribute and can miss namespaced `xsi:nil`.

Required repair: preserve dimension kind and deterministic typed-member value/source representation; preserve explicit-member QName separately; detect namespaced nil correctly in HTML/iXBRL and XML; retain raw QName/attributes and do not introduce canonical metric guessing.

### P11-ISSUE-116 — P7-US required validation gates and reuse semantics are incomplete
Severity: BLOCKING VALIDATION.

Design 26 §17 requires at least metadata consistency, package/member integrity, primary parseability, context/unit resolution, slot conflict, period-end plausibility, DOM resolvability, table/cell traceability, fact→evidence coverage, no source drift and path safety.

Current validation covers several source/evidence checks but does not fully enforce period-end versus filing metadata plausibility or table/cell source traceability, and metadata checks are weak.

`SecValidationResult.reuse_eligible` is currently `blocking == 0`. Accepted P7 semantics require PASS + zero blocking + compatible. A REVIEW_REQUIRED P11 artifact can therefore be marked reusable even though ingest correctly refuses to publish it. This becomes unsafe once the planner is integrated.

Required repair: implement the missing deterministic P7-US gates and align reuse_eligible with accepted P7 PASS/compatibility semantics.

### P11-ISSUE-117 — P8 SEC raw-fact/tool compatibility is incomplete
Severity: BLOCKING P8 INTEGRATION.

`McpQueryService.list_raw_facts()` filters and sorts using legacy fields such as `page_no` and `raw_metric_name`, but P11 SEC facts expose `virtual_page_no` and `raw_qname`. Therefore SEC page filtering and `metric_contains` can silently return no matching facts.

Existing P11 tests do not exercise the full P8 SEC tool family or these filters. The P11 raw-fact/evidence records also need an explicit compatibility strategy so generic P8/P10 consumers can use existing tool contracts while receiving additive SEC-specific QName/context/source fields.

Required repair: source-kind-aware P8 adaptation or compatible additive aliases without changing CN/HK output semantics; prove list/get/search/pages/sections/tables/facts/evidence/validation behavior, including fact page/metric filters, on SEC fixtures.

### P11-ISSUE-118 — HTTP timeout contract is only partially represented
Severity: DESIGN RECONCILIATION REQUIRED.

Design requires bounded connect/read/total timeouts. Current config exposes one `timeout_seconds`; urllib uses it for socket operations and the subprocess adds a coarse outer timeout. There is no explicit connect/read/total contract.

Required repair: implement explicit deterministic bounded timeout semantics compatible with the stdlib/runtime boundary, or STOP and submit a design amendment if the frozen requirement cannot be implemented safely without changing the approved dependency boundary. Do not silently drop the requirement.

### P11-ISSUE-119 — historical submissions chunks are not selected by requested year range
Severity: PERFORMANCE / DISCOVERY CONTRACT.

`parse_submissions()` stores only history file names and drops SEC `filingFrom` / `filingTo` metadata. `SecAcquirer` then fetches history files sequentially until a match appears. Design performance gate requires discovery to fetch only required history chunks.

Required repair: preserve history chunk range metadata and select only chunks capable of containing the requested filing year/period, with fail-closed deterministic behavior and request-count tests.

### P11-ISSUE-120 — HTML block/page normalization is too narrow for general SEC born-digital HTML
Severity: HIGH PARSER / LIVE-RISK.

`_blocks()` only promotes h1-h6, p, li, caption, td/th, title, pre and Inline-XBRL fact nodes. Common meaningful SEC narrative represented by div/span structures can be omitted from virtual-page text. Additionally, a paragraph/cell containing an inline ix fact is skipped when its child is itself treated as a block, which can discard surrounding narrative text.

Design requires deterministic source blocks/headings and P3-like virtual page/section artifacts for filing HTML, not only tagged facts/tables.

Required repair: deterministic visible-text block normalization that preserves narrative in common SEC DOM structures without duplicate nested text, excludes script/style/hidden content appropriately, retains exact DOM/source-member anchors, and keeps virtual pages repeatable. Add realistic div/span + inline-fact fixtures. Section extraction should be reviewed against the same source-block model rather than assuming all SEC headings are literal h1-h6.

## 4. Test coverage gaps that allowed the deviations

Current P11 unit tests contain no regression for:
- unrelated nested `primaryDocument` such as `xslF345X06/form4.xml`;
- Windows drive-qualified or pre-fetch archive path escape;
- explicit CIK taking precedence when ticker is stale/missing;
- persisted ticker-map provenance/cache;
- production planner orchestration with zero network on REUSE_DATA/PARSE_LOCAL;
- Registry visibility immediately after US acquire;
- actual stored live member content-type value;
- archive-index malformed shape / `.xbrl` / linkbase role handling;
- required P4-US table signals;
- explicit versus typed dimensions / namespaced nil;
- period plausibility and table/cell source-trace P7 gates;
- REVIEW_REQUIRED implying `reuse_eligible=False`;
- P8 SEC raw-fact page/metric filters and full P8 tool family;
- explicit connect/read/total timeout semantics;
- history chunk range selection/request count;
- div/span narrative preservation in virtual HTML pages.

## 5. Accepted implementation variances / non-findings

These are not required repair items in this audit:
- SEC Registry uses separate additive SEC tables rather than physically adding package_sha256 to legacy filing_bindings; this preserves legacy v1 rows and is an accepted additive implementation variance.
- companyfacts/companyconcept are not used; design marks them optional.
- the dedicated subprocess currently handles SEC HTTP while HTML/XML parsing runs in the main FFDF process. Design calls the separate parser runtime a preferred architecture rather than an absolute requirement; no defect is opened solely for that placement.
- complete submission text is not acquired by default; design only requires it as fallback/evidence when needed.

## 6. Formal-test-plan implications

The prior formal plan 156 cannot simply be resumed after repair. Design 27 also requires explicit acceptance coverage for:
- Registry migration/reopen/idempotence and planner REUSE/PARSE_LOCAL/DOWNLOAD behavior;
- the complete P8 SEC tool family, not merely a generic P8 read;
- US CLI acquire/ingest/status;
- no-AI/security boundary;
- the corrected CIK-first identity behavior.

After a repaired exact candidate receives REVIEW_PASS, ChatGPT must issue a revised formal acceptance plan. PC Agent must not edit 156 to retrofit these gates.

## 7. Audit verdict

`05e06096bc8b788d0467a1ce3442829e87727b6b` is NOT design-conformant and is ineligible for further acceptance.

Required status:
`CHANGES_REQUIRED`

Open repair scope:
`P11-ISSUE-109` through `P11-ISSUE-120` as defined in this audit.

Previously fixed P11-ISSUE-101 through P11-ISSUE-108 must remain regression-protected.

## 8. Next action

Perform one design-consistency repair pass on the development branch. Fix all confirmed deviations above in one candidate rather than submitting another single-defect patch. If any requirement genuinely conflicts with the frozen design/runtime boundary, STOP and document the conflict before changing design; do not guess.

After implementation:
1. run focused P11 tests;
2. run full unit suite;
3. run CN/HK regression;
4. run compileall;
5. run git diff --check;
6. run controlled developer live smoke with the configured SEC contact against the frozen Apple/Toyota fixtures and Kellanova CIK-only amendment check;
7. create one new exact production candidate commit;
8. create a separate development evidence document/commit;
9. push and stop for ChatGPT exact-candidate review;
10. do not resume formal acceptance until that review passes.
