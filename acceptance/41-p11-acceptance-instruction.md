# 41 — P11 US SEC Provider Acceptance Instruction

Status: **ACCEPTANCE BASELINE CANDIDATE / NOT YET FROZEN**

Phase:
P11 — US SEC Provider

Detailed design:
`design/26-p11-sec-provider-design.md`

Implementation plan:
`design/27-p11-implementation-plan.md`

Parsed contract:
`design/30-parsed-financial-document-v2-contract.md`

## 1. Acceptance principle

P11 acceptance must prove that official SEC filing sources can be discovered, acquired, stored, parsed and validated without:

- weakening accepted CN/HK behavior;
- fabricating PDF-style evidence;
- silently substituting aggregate APIs;
- violating SEC fair access;
- modifying accepted P8/P9/P10 contracts.

Independent Acceptance uses a fresh exact-candidate worktree and project-local mutable workspace only.

## 2. Exact-candidate source binding

Every Python command must bind to the frozen candidate source.

No editable install may substitute for exact candidate source binding.

Dedicated P11 runtime must be separately pinned and verified by runtime lock.

## 3. Existing accepted baseline

Before P11 tests:

- accepted main baseline recorded exactly;
- P0-P10 production/tests/governance immutable manifest captured;
- P8/P9/P10 exact contracts/fingerprints recorded;
- CN/HK acquisition baseline recorded.

Any unexplained drift => STOP.

## 4. Identity acceptance

Mandatory:

1. market US accepted;
2. CIK input grammar exactly `^[0-9]{1,10}$` after surrounding ASCII whitespace trim;
3. normalized CIK exactly 10 digits / numeric value > 0;
4. signs, Unicode digits, separators and embedded whitespace rejected;
5. accession grammar exactly `^[0-9]{10}-[0-9]{2}-[0-9]{6}$`;
6. accession no-dash archive form exactly 18 digits;
7. primaryDocument must be a safe single basename with no slash/backslash/control/query/fragment;
8. ticker is not canonical identity;
9. exact caller CIK wins after validation and US ticker may be null;
10. CN/HK CompanyRef still require non-empty ticker;
11. US CIK-only flow never fabricates ticker;
12. exactly one official ticker may populate normalized display ticker;
13. zero/multiple official tickers for a known CIK may leave ticker=null without blocking CIK discovery;
14. ticker-only zero match => P11_COMPANY_IDENTITY_NOT_FOUND;
15. ticker lookup multiple-CIK ambiguity => P11_COMPANY_IDENTITY_AMBIGUOUS;
16. ticker/CIK mismatch => P11_COMPANY_IDENTITY_AMBIGUOUS;
17. Q2 supported for US;
18. US Q2 not mapped to H1;
19. CN Q2 rejected;
20. HK Q2 rejected;
21. existing CN/HK H1 behavior unchanged;
22. 10-K/A normalized to base 10-K + amended;
23. 10-Q/A normalized;
24. 20-F/A normalized;
25. 40-F/A normalized;
26. 8-K/6-K supplemental identity is accession-bound, not periodic-slot-forced.

## 5. Official SEC discovery acceptance

Use official SEC endpoints only.

Mandatory:

- Submissions current array;
- historical submissions shard;
- exact accession number;
- form;
- filing date;
- report date;
- primaryDocument;
- CIK;
- XBRL/iXBRL flags where available.

Malformed/missing fields produce deterministic reason codes.

No scraping of third-party filing mirrors.

## 6. Fair access / HTTP

Mandatory:

- explicit User-Agent required;
- no fake default contact identity;
- SEC policy is treated as aggregate, not per-process;
- supported single-installation aggregate implementation ceiling <=8 requests/sec;
- no-burst minimum 125 ms between outbound SEC request starts;
- concurrent two-process probe under the same canonical project root still observes aggregate <=8 requests/sec;
- all retries pass through the same cross-process rate gate;
- unavailable/unsafe shared coordination => `P11_RATE_LIMIT_SCOPE_UNSAFE`;
- HTTPS only;
- SEC allowlist only;
- redirect target revalidated;
- timeout bounded;
- retry count bounded;
- 429 respects Retry-After where present;
- 404 does not retry indefinitely;
- 403 surfaces blocked/access-denied;
- 5xx bounded retry;
- response-size cap enforced;
- content type validated;
- file:// rejected;
- arbitrary caller URL rejected.

Record peak observed request rate in live acceptance.

## 7. Archive URL acceptance

Given CIK/accession/primaryDocument:

- CIK path is integer CIK without leading zero;
- accession path removes dashes;
- primary document filename is validated;
- computed URL matches official filing location;
- path traversal characters rejected.

## 8. Source package acceptance

Mandatory:

- accession-directory `index.json` is captured as exact `FILING_INDEX` bytes;
- primaryDocument comes from validated Submissions metadata, is a safe basename, and must be listed in the same index.json;
- every index-listed safe basename ending `.xsd` or `.xml` is automatically captured;
- exact suffix role classification matches design/26 Section 14;
- unrelated HTML/text exhibits are not auto-downloaded;
- explicitly requested exhibit uses exact safe basename and must be listed in index.json;
- same asset cannot appear twice with conflicting inventory metadata;
- exact primary source bytes preserved;
- primary document SHA256 independently recomputed;
- source package manifest canonical;
- exact `p11-sec-source-package-identity-v1` payload from design/26 Section 15 enforced;
- known package identity fixture produces an independently precomputed SHA256;
- package hash deterministic;
- caller/asset ordering does not change package hash after canonical sort;
- changing role/hash/file_name/canonical requested source_url/byte_size/primary/dependency topology changes package hash;
- changing redirect final URL/declared HTTP media type/local path/timestamp/request-id/ETag/Last-Modified does not change package hash;
- same package hash always maps to byte-identical immutable package manifest identity bytes; acquisition receipts may differ without rewriting that manifest;
- `local_content_path` persists as project-root-relative POSIX only;
- absolute/drive-relative/UNC/traversal local paths rejected;
- resolved local content must remain inside configured P11 SEC raw-assets root;
- two different logical source assets with identical bytes/SHA remain two manifest/source-assets rows;
- each row has a distinct deterministic `source_asset_id` derived from exact `(file_name, canonical source_url, asset_sha256)`;
- known `source_asset_id` fixture reproduces `41183564053cd4f7be5c66d4ed4e7c44d72ad137f9aaf60e7f5bf30c9ef41fa2`;
- content-addressed raw blob is physically reused once for those rows;
- exact duplicate logical key `(file_name, canonical requested source_url)` is rejected;
- package hash includes both logical rows even when their asset_sha256 matches;
- role precedence is exactly FILING_INDEX > PRIMARY_DOCUMENT > structured suffix > REQUESTED_EXHIBIT;
- an explicit request for an already included higher-precedence asset adds no duplicate row and does not change role;
- exact provider filename case/spelling is retained in logical identity; lowercasing is classification-only;
- every index-derived filename passes the frozen safe-basename rules;
- `asset_sha256` equals SHA256 of exact captured bytes;
- `byte_size` equals actual captured byte length, not substituted index metadata;
- numeric index size mismatch vs captured bytes => P11_PACKAGE_INVALID;
- `primary=true` iff role=PRIMARY_DOCUMENT, otherwise false;
- every P11 v1 package asset has `dependency_depth=0` and `referring_asset_sha256=null`;
- parser/runtime external taxonomy/cache assets are not appended to the immutable package and do not change `source_package_sha256`;
- package top-level filing_date is valid non-empty Submissions YYYY-MM-DD or P11_SUBMISSIONS_INVALID;
- package top-level report_date is immutable discovery reportDate/null and is never rewritten by DEI;
- package asset hash mismatch blocks;
- partial commit never becomes accepted package;
- same accession + changed bytes creates source drift/new package, not overwrite;
- all stored paths remain inside project root.

## 9. Period binding acceptance

Periodic forms:

- 10-K => FY;
- 10-Q => Q1/Q2/Q3;
- 20-F => FY;
- 40-F => FY.

Binding must use DEI period/fiscal-year focus and the immutable Submissions discovery reportDate contract from design/26.

Mandatory cases:

- Q1;
- Q2;
- Q3;
- FY;
- valid discovery reportDate + matching DEI DocumentPeriodEndDate => exact final report_date;
- null discovery reportDate + valid DEI DocumentPeriodEndDate => DEI fills final periodic report_date;
- valid discovery reportDate + missing DEI period-end => discovery value retained;
- both missing => P11_PERIOD_UNRESOLVED;
- discovery vs DEI date disagreement => P11_PERIOD_CONFLICT;
- malformed non-empty Submissions reportDate => P11_SUBMISSIONS_INVALID before package commit;
- later DEI confirmation never changes source_package_sha256;
- mismatched DEI vs requested slot => P11_PERIOD_CONFLICT;
- unresolved period => P11_PERIOD_UNRESOLVED;
- no calendar-month guessing.

## 10. ParsedFinancialDocument v2 acceptance

Exact schema:
`parsed-financial-document-v2`

Mandatory files:

- manifest.json;
- document.json;
- source_assets.jsonl;
- source_segments.jsonl;
- sections.jsonl;
- tables.jsonl;
- raw_facts.jsonl;
- evidence.jsonl;
- validation.json.

Loader independently verifies:

- counts;
- hashes;
- IDs;
- source asset references;
- locator integrity;
- document/package identity.

No P3/P6 v1 schema masquerading.

## 11. Source locator acceptance

At least one accepted evidence item each for applicable types:

- HTML_DOM;
- IXBRL_FACT;
- XBRL_FACT when fixture provides separate instance;
- SOURCE_ASSET metadata evidence.

Mandatory locator/identity fixtures:

- HTML path uses lowercase tag + 1-based same-tag sibling index exactly;
- XML/iXBRL path uses expanded Clark QName + 1-based same-QName sibling index exactly;
- namespace-prefix changes do not change XML locator identity;
- source locator object keys are exact and optional values appear as JSON null;
- locator resolves to exactly one node;
- every source-referencing artifact carries both `source_asset_id` and `source_asset_sha256`, and the pair resolves to exactly one source-assets row;
- same-content/different-logical-source fixtures produce distinct `evidence_id`, `raw_fact_id`, `segment_id`, `section_id` and `table_id` values;
- `document.primary_source_asset_id` resolves to the unique PRIMARY_DOCUMENT row and matches its SHA/name/media type/size;
- known `evidence_id`, `raw_fact_id`, `segment_id`, `section_id`, `table_id`, `cell_id`, `config_hash` and `parse_run_id` fixtures match independently precomputed hashes;
- caller order and local paths do not change those IDs;
- parser/config semantic change does change `parser_version` or `config_hash`.

Explicitly reject:

- synthetic physical page_no for HTML;
- fabricated bbox;
- evidence locator pointing outside captured package;
- ambiguous/zero-match locator;
- noncanonical namespace-prefix-based XML identity.

## 12. Inline XBRL raw facts

For selected live facts verify:

- exact concept QName;
- exact contextRef;
- unitRef where applicable;
- dimensions;
- decimals/precision where present;
- scale/sign/format where present;
- `continuedAt` chain and `ix:exclude` handling follows the frozen rule;
- raw_value is character content with Unicode whitespace-run -> one U+0020 and outer-space trim, before format/scale/sign;
- raw_value is unchanged by unit conversion/canonicalization because those are forbidden;
- deterministic parsed numeric applies only the frozen standards transform/format/sign/scale contract;
- nil => parsed numeric null;
- invalid/unsupported transform => parsed numeric null + explicit issue;
- period context;
- entity identifier;
- evidence locator to exact fact source node.

Raw metric name remains source truth.

## 13. Custom taxonomy

Mandatory live or frozen fixture case:

- custom concept retained;
- namespace retained;
- raw fact not dropped;
- unresolved label does not trigger canonical guess;
- evidence remains exact filing source.

## 14. HTML tables

For a deterministic HTML table fixture:

- DOM table identity deterministic;
- row/column reconstruction deterministic;
- rowspan/colspan deterministic;
- no bbox fabricated;
- source cell locator resolves to exact DOM node.

If visual CSS interpretation is necessary:

`P11_VISUAL_RENDERING_REQUIRED`.

## 15. Arelle/runtime

The mandatory P11-F pre-code parser-contract freeze must be present and accepted before parser implementation.

Acceptance verifies the frozen parser contract covers:

- exact parser/HTML/XML/Arelle library versions and lock;
- exact source_kind classification;
- deterministic media_type classification;
- HTML recovery/tree normalization;
- XML external entity/network behavior;
- source-segment boundaries and normalized_text;
- section detection/hierarchy;
- DOM table inclusion/cell text/rowspan/colspan/header-tree;
- Inline XBRL transformation registry;
- continuedAt / ix:exclude;
- locator goldens;
- raw-value and parsed-decimal goldens;
- external taxonomy/cache behavior;
- unresolved dependency status mapping;
- no unrecorded network during deterministic parse.

If the frozen runtime uses Arelle:

- exact package version pinned;
- dependency lock reproducible;
- runtime Python version/arch recorded;
- runtime package lock matches;
- parser operates on local package;
- validation messages mapped deterministically.

If final implementation does not use Arelle, acceptance must instead prove an equivalent frozen XBRL parser contract with the same required semantics.

## 16. Registry / package-aware reuse

Periodic filing:

- primary exact source asset registered;
- page_count null for HTML;
- source metadata accession/CIK correct;
- slot bound only after period confirmation;
- parsed record uses schema v2;
- P11 periodic ParsedDataRecord artifact_path is non-null project-root-relative POSIX under the configured P11 parsed-artifact root;
- no P11 registry schema migration is required solely for source-package identity.

Generic planner boundary:

- IncrementalPlanner.build_plan with market=US returns/raises explicit P11_PACKAGE_AWARE_PLANNER_REQUIRED and does not perform document-SHA-only reuse;
- existing CN/HK IncrementalPlanner behavior remains unchanged.

Package-aware SEC selector acceptance cases:

1. requested target slot + exact document SHA + exact package SHA + accepted parser/schema + PASS + 0 blockers + COMPATIBLE => reusable and P11-F/G/H/I parser/identity/v2/validation work is skipped;
2. same document SHA but different current source_package_sha256 => P11_SOURCE_PACKAGE_CHANGE / no reuse;
3. null or missing artifact_path => P11_REUSE_ARTIFACT_MISSING / no reuse;
4. absolute/drive-relative/UNC/traversal/outside-root artifact path => P11_REUSE_ARTIFACT_PATH_INVALID / no reuse;
5. v2 loader/hash/ID/source-reference failure => P11_REUSE_ARTIFACT_INVALID / no reuse;
6. loaded manifest parse_run_id != registry record parse_run_id => P11_REUSE_ARTIFACT_INVALID;
7. loaded manifest/document document_sha256 mismatch => P11_REUSE_ARTIFACT_INVALID;
8. loaded manifest source_package_sha256 mismatch => no reuse; exact source-package change reason retained;
9. loaded periodic document identity != requested target slot => P11_REUSE_ARTIFACT_INVALID;
10. exact-package REVIEW_REQUIRED/blocked/incompatible record => not reusable;
11. multiple fully reusable runs for one exact package select lexicographically smallest parse_run_id only after all exact-package checks;
12. document_sha256 equality alone is never sufficient for US reuse.

Changed package/content blocks silent reuse.

Supplemental filings remain outside existing periodic ParsedDataRecord reuse.

Existing CN/HK registry/reuse behavior unchanged.

## 17. Amendment behavior

Mandatory:

- original accession preserved;
- amendment accession preserved separately;
- amended=true correct;
- no blanket automatic supersession;
- ambiguous variant selection returns explicit review reason;
- prior source package not overwritten.

## 18. Supplemental 8-K / 6-K

At least one live or frozen official SEC case:

- accession-bound supplemental ingestion;
- primary document captured;
- `fiscal_year=null` when no exact filing-native fiscal-year evidence exists;
- `raw_fiscal_period=null` always for supplemental v1;
- `report_date=null` when SEC reportDate is empty/not valid;
- filing_date is not used to infer fiscal_year/report_date;
- no Q1/Q2/Q3/FY slot forced;
- no existing periodic SQLiteRegistry / ParsedDataRecord write;
- v2 writer/loader round-trips the null supplemental fields exactly;
- unrelated exhibits not downloaded by default;
- explicitly requested allowed exhibit can be captured;
- exact exhibit asset SHA/evidence retained.

## 19. Companyfacts boundary

Mandatory negative/consistency case:

- companyfacts may be queried only as auxiliary data;
- companyfacts mismatch cannot overwrite filing raw fact;
- companyfacts cannot create missing filing evidence;
- custom filing concept remains even if absent from companyfacts.

## 20. Post-acceptance correction/source drift

Simulated or live-safe deterministic case:

- same accession metadata + different source bytes detected;
- old package retained;
- new package identity created;
- reuse invalidated;
- P11_SOURCE_CONTENT_DRIFT surfaced.

## 21. Negative gates

Exact mandatory results:

- ticker-only company identity zero match -> P11_COMPANY_IDENTITY_NOT_FOUND
- ambiguous ticker/CIK -> P11_COMPANY_IDENTITY_AMBIGUOUS
- missing filing -> P11_FILING_NOT_FOUND
- missing User-Agent -> P11_USER_AGENT_REQUIRED
- unavailable cross-process aggregate rate coordination -> P11_RATE_LIMIT_SCOPE_UNSAFE
- bad host -> P11_SOURCE_HOST_NOT_ALLOWED
- hostile redirect -> P11_REDIRECT_NOT_ALLOWED
- oversized response -> P11_RESPONSE_TOO_LARGE
- bad content type -> P11_CONTENT_TYPE_INVALID
- package hash mismatch -> P11_PACKAGE_HASH_MISMATCH
- source drift -> P11_SOURCE_CONTENT_DRIFT
- generic US planner call -> P11_PACKAGE_AWARE_PLANNER_REQUIRED
- same document SHA but different source package -> P11_SOURCE_PACKAGE_CHANGE
- missing reuse artifact -> P11_REUSE_ARTIFACT_MISSING
- invalid/outside reuse artifact path -> P11_REUSE_ARTIFACT_PATH_INVALID
- reuse artifact loader/hash/identity mismatch -> P11_REUSE_ARTIFACT_INVALID
- unresolved dependency -> P11_DEPENDENCY_UNRESOLVED
- visual-only requirement -> P11_VISUAL_RENDERING_REQUIRED
- period conflict -> P11_PERIOD_CONFLICT

No silent fallback.

## 22. Security

Mandatory scan/probes:

- no remote AI API;
- no arbitrary shell command input;
- no arbitrary local path input;
- no arbitrary network host;
- no executable attachment execution;
- no HTML script execution;
- XML external entity behavior disabled/controlled;
- archive/path traversal blocked;
- redirects bounded;
- decompression/asset-count/size limits enforced.

## 23. P0-P10 regression

Must run:

- P11 focused suite;
- all P0-P11 unit tests;
- accepted CN/HK acquisition tests;
- accepted P8 MCP tests;
- accepted P9 tests;
- accepted P10 research tests;
- compile/import;
- git diff --check.

P8/P9/P10 accepted source/test paths must show zero unintended diff.

## 24. Live acceptance matrix

Minimum official SEC live matrix:

### L1 — domestic 10-K

Must be Inline XBRL when available.

Prove:
discovery → package → parse → facts/evidence → validation → registry.

### L2 — domestic 10-Q

Must include period binding and at least one numeric fact.

### L3 — Q2

Explicitly prove Q2 identity/period.

### L4 — foreign issuer

20-F or 40-F.

### L5 — supplemental

8-K or 6-K.

### L6 — amendment

One /A filing.

### L7 — custom taxonomy

At least one custom concept preserved.

Different cases may share a filing when all requirements are independently proven.

## 25. Performance

Record for each representative live run:

- request_count;
- peak_request_rate;
- bytes_downloaded;
- discovery_ms;
- download_ms;
- package_commit_ms;
- html_parse_ms;
- xbrl_parse_ms;
- validation_ms;
- total_ms.

No acceptance performance target may require violating SEC fair access.

## 26. Raw/source immutability

Before and after acceptance:

- P0-P10 accepted files unchanged;
- captured SEC assets unchanged;
- package manifest unchanged;
- source filing bytes unchanged;
- parsing never writes into raw asset file;
- evidence refers only to accepted raw assets.

## 27. P8/P9/P10 non-expansion

Mandatory:

- P8 server version unchanged;
- P8 exact 11 tool names unchanged;
- P8 catalog/result v1 unchanged;
- P9 schemas/policy unchanged;
- P10 capability fingerprint behavior unchanged;
- P10 still reports P11 provider unavailable to P10 v1 unless a later separately accepted compatibility phase changes that.

P11 acceptance does not silently create SEC research availability through P10.

## 28. Independent Acceptance isolation

Fresh detached exact candidate.

All mutable data under project root.

No production/tests/design changes during acceptance.

If a material defect is found:

STOP and return to Design-First flow.

## 29. Exit condition

P11 DONE requires:

- design baseline PASS;
- implementation gates PASS;
- formal Code Review PASS;
- acceptance freeze;
- Independent Acceptance PASS;
- fresh main integration;
- post-merge/final-main regression PASS;
- P0-P10 no regression;
- no unauthorized P8/P9/P10 compatibility expansion.

P11 closeout does not automatically authorize any next phase.
