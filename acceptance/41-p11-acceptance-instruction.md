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

Current + historical discovery merge MUST follow design/31: normalize through one candidate validator; filing semantic equality excludes `submission_source_urls`; same-accession semantic-equal duplicates dedupe while provenance becomes an ASCII-sorted unique union; differing semantic fields reject with `P11_SUBMISSIONS_INVALID`; candidate XBRL flags are non-null bool; output canonical-sorts by `(filing_date ASC, accession_number ASC)` independent of source/shard/provenance order.

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
- exact P11-D values/algorithms come from `design/31-p11-d-http-discovery-contract.md`;
- User-Agent source = `SEC_USER_AGENT`, grammar-valid visible ASCII identity + contact token, raw value never logged;
- headers = User-Agent + `Accept: application/json` + `Accept-Encoding: identity`;
- connect timeout 10s / read-idle timeout 30s / logical fetch deadline 120s;
- caps: ticker JSON 16 MiB / current Submissions 32 MiB / historical Submissions 16 MiB;
- redirect maximum = 3 and automatic redirects disabled;
- retry maximum = 3 with deterministic 1s/2s/4s fallback;
- Retry-After maximum accepted wait = 60s;
- total outbound-start cap per logical fetch = 8;
- shared lock path/state schema and 5s lock-acquisition ceiling exactly match design/31;
- invalid/corrupt rate state may recover only after a full 125ms wait while holding the safe kernel lock;
- rolling rate measurement uses half-open `[t,t+1s)` windows;

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
- P11 v1 raw blob path is extensionless SHA-only (`workspace/sec/raw/assets/sha256/<aa>/<sha>`), so identical bytes under different logical extensions cannot change `local_content_path`;
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

Finalization-order acceptance:

- P11-H computes validation in memory/model form and does not create a registry-eligible final export;
- before P11-H completes, no final `manifest.json` / `validation.json` pair exists;
- P11-I serializes the final validation.json from the P11-H validation model;
- P11-I derives manifest.validation_status and manifest.blocking_issue_count from that same final validation model;
- manifest.validation_status == validation.status;
- manifest.blocking_issue_count == len(validation.blocking_issues);
- no provisional/fabricated validation placeholder is accepted;
- complete staging export passes the final v2 loader before commit;
- staging root is `<parsed_root>/.staging`; two concurrent attempts for the same `parse_run_id` use distinct exclusive `attempt_token` directories and never share writable staging;
- final path absent => one atomic same-filesystem **non-replacing** directory commit attempt to exact `<parsed_root>/<parse_run_id>/export-v2`;
- commit outcome is distinguishable as `COMMITTED_NEW`, `DESTINATION_EXISTS`, or `COMMIT_ERROR`;
- two-process same-`parse_run_id` probe proves exactly one `COMMITTED_NEW`; a loser receiving `DESTINATION_EXISTS` transitions to existing-final verification and can succeed only after loader/identity/all-nine-byte equality;
- `COMMIT_ERROR` => `P11_FINAL_ARTIFACT_COMMIT_FAILED` / BLOCKED and cannot be reclassified from a later final-path existence observation;
- final path already exists and every required file is byte-identical plus loader/identity semantics match => idempotent success without replacing/mutating final bytes;
- final path already exists and any required byte/file/identity/validation semantic differs or is invalid => P11_FINAL_ARTIFACT_COLLISION / BLOCKED;
- existing final export is never overwritten, deleted or replaced;
- after new commit or idempotent existing-final success, final directory reload succeeds before P11-K;
- P11-K registry persistence occurs only after the final directory reloads successfully;
- simulated P11-K registry failure leaves the valid final export unchanged and unregistered;
- later retry may verify the existing final export idempotently and retry registry persistence;
- unregistered orphan final export is not selected for reuse;
- staging path is never registered or reusable;
- normal runtime cleanup removes only the current attempt's staging and never automatically deletes/recycles another attempt's staging;
- simulated loser with one-byte-different staging => `P11_FINAL_ARTIFACT_COLLISION`, with no final overwrite/delete/replace;
- simulated permission/I/O/invalid-path commit failure => `P11_FINAL_ARTIFACT_COMMIT_FAILED`, not idempotent success;
- P11-K does not mutate committed artifact bytes;
- after successful final reload, concurrent exact P11-K callers use `register_parsed_data_atomic` and both converge to registry success with exactly one exact row;
- a forced P11 registry row conflict blocks with `P11_REGISTRY_RECORD_CONFLICT` without final-artifact or existing-row mutation;
- a forced registry busy/locked/I/O failure blocks with `P11_REGISTRY_PERSISTENCE_FAILED` and remains safe for outer retry.

Final-export byte-determinism acceptance:

- `manifest.json`, `document.json`, `validation.json` use exact canonical JSON encoding from design/30, UTF-8/no-BOM/LF-only, exactly one final LF;
- every non-empty JSONL row uses the same canonical JSON encoding plus one LF;
- empty JSONL is exactly zero bytes;
- exact top-level row order:
  - source_assets by source_asset_id;
  - source_segments by (ordinal, segment_id);
  - sections by section_id;
  - tables by table_id;
  - raw_facts by raw_fact_id;
  - evidence by evidence_id;
- two complete serializations of the same semantic inputs under intentionally different wall-clock/performance diagnostics produce identical SHA256 for all nine required final files;
- Windows/CRLF/native-newline settings do not change final export bytes;
- JSON insertion order and shuffled caller/input collection order do not change final bytes;
- semantically unordered issue/warning/set-like arrays are canonical-byte sorted;
- no wall-clock timestamp, elapsed/duration, request/process/attempt ID, absolute/staging/temp path, random nonce, acquired_at or performance-only diagnostic appears in final export;
- performance diagnostics are stored only outside export-v2 and outside registry artifact_path;
- same-content logical assets with different filename extensions resolve to the same extensionless SHA-only physical blob path;
- semantic content change changes the relevant artifact bytes and is not normalized away;
- ISSUE-033 idempotent retry remains successful when only external diagnostic/performance receipt values differ.

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
- P11 periodic ParsedDataRecord artifact_path is the normalized project-root-relative POSIX path to the exact `<parsed_root>/<parse_run_id>/export-v2` directory;
- parse_run_id is lowercase 64-hex before path construction;
- stored artifact_path has no trailing slash and never points to manifest.json/child file/staging path;
- the complete export-v2 directory is atomically committed before registry persistence;
- no P11 registry schema migration is required solely for source-package identity.

P11-K concurrent registry persistence acceptance:

- accepted `SQLiteRegistry.register_parsed_data(record)` remains unchanged and is not the P11-K write API;
- additive exact API = `SQLiteRegistry.register_parsed_data_atomic(record: ParsedDataRecord) -> None`;
- additive public conflict exception = `ParsedDataRecordConflict(ValueError)`;
- canonical implementation path = `financial_filing_data_foundation.registry.sqlite_registry.ParsedDataRecordConflict`;
- canonical public import = `from financial_filing_data_foundation.registry import ParsedDataRecordConflict`;
- public import is the exact same class object as the implementation-path class; no alias/wrapper/duplicate class;
- `REGISTRY_SCHEMA_VERSION == 1`; no schema migration;
- `register_parsed_data_atomic` executes `BEGIN IMMEDIATE` before `SELECT * FROM parsed_data WHERE parse_run_id = ?`;
- two concurrent exact writers for one parse_run_id both return normally, exactly one physical row exists, and the row equals the requested record across every persisted semantic field except created_at;
- a third exact retry returns normally and does not add/change a row;
- same parse_run_id + any different persisted semantic field => exact `ParsedDataRecordConflict` message `parse_run_id already exists with different content: <parse_run_id>` and existing row unchanged;
- P11-K maps `ParsedDataRecordConflict` to `P11_REGISTRY_RECORD_CONFLICT` / BLOCKED;
- SQLite busy/locked/I/O/commit or other persistence failure => `P11_REGISTRY_PERSISTENCE_FAILED` / BLOCKED;
- busy/locked/I/O failure is never converted to success merely because a row is observed later;
- no hidden retry loop occurs inside the atomic registry API;
- registry failure never mutates/deletes/replaces final export-v2;
- later outer retry re-verifies existing final export before retrying atomic registry persistence;
- existing CN/HK callers continue using accepted `register_parsed_data()` and their planner/reuse behavior is unchanged.

Generic planner boundary:

- exact exception class = `PackageAwarePlannerRequired(RuntimeError)`;
- class attribute `reason_code == "P11_PACKAGE_AWARE_PLANNER_REQUIRED"`;
- exact `str(exc) == "market US requires P11 package-aware SEC planning"`;
- IncrementalPlanner.build_plan with market=US raises that exception before `build_required_slots`;
- no registry method is called before the exception;
- no FilingPlan/PlannerItem is returned for US;
- existing CN/HK IncrementalPlanner behavior remains unchanged.

Package-aware SEC result API:

- public module = `financial_filing_data_foundation.sec.reuse`;
- exact public function signature = `select_sec_reuse(registry, slot, document_sha256, source_package_sha256, reuse_policy, project_root, parsed_root) -> SecReuseDecision`;
- non-US slot => exact `ValueError("select_sec_reuse requires market US")`;
- invalid document SHA => exact `ValueError("document_sha256 must be 64 lowercase hex")`;
- invalid package SHA => exact `ValueError("source_package_sha256 must be 64 lowercase hex")`;
- parsed_root outside project_root => exact `ValueError("parsed_root must be inside project_root")`;
- exact `SecReuseAction` values:
  - REUSE_DATA;
  - PARSE_CURRENT_PACKAGE;
- exact `SecReuseReason` values/strings follow design/26 Section 17.1;
- exact frozen/slots `SecReuseDecision` field order:
  1. action;
  2. reason_code;
  3. rejection_reasons;
  4. slot_key;
  5. document_sha256;
  6. source_package_sha256;
  7. parse_run_id;
  8. artifact_path;
- REUSE_DATA decision requires exact success reason, empty rejection_reasons, non-null parse_run_id/artifact_path;
- PARSE_CURRENT_PACKAGE requires null parse_run_id/artifact_path and non-success reason;
- zero parsed candidates => exact P11_NO_REUSABLE_EXACT_PACKAGE decision;
- mixed failure candidates produce ordered unique rejection_reasons using the exact design/26 priority;
- reason_code equals first rejection_reasons item on parse decisions;
- successful exact-package decision does not retain rejected-candidate reasons;
- selector returns SecReuseDecision, not ParsedDataRecord;
- selector performs no registry/artifact/package mutation.

Package-aware SEC selector acceptance cases:

1. requested target slot + exact document SHA + exact package SHA + exact registry/artifact metadata parity + accepted parser/schema + PASS + 0 blockers + COMPATIBLE => reusable and P11-F/G/H/I parser/identity/validation/final-v2 work is skipped;
2. same document SHA but different current source_package_sha256 => P11_SOURCE_PACKAGE_CHANGE / no reuse;
3. null artifact_path or safe expected export-v2 directory absent => P11_REUSE_ARTIFACT_MISSING / no reuse;
4. absolute/drive-relative/UNC/traversal/outside-root path, path to manifest.json/child file, or safe but wrong `<parsed_root>/<parse_run_id>/export-v2` layout => P11_REUSE_ARTIFACT_PATH_INVALID / no reuse;
5. expected path exists but is not a directory, required v2 file is missing, or v2 loader/hash/ID/source-reference fails => P11_REUSE_ARTIFACT_INVALID / no reuse;
6. loaded manifest parse_run_id != registry record parse_run_id => P11_REUSE_ARTIFACT_INVALID;
7. loaded manifest/document document_sha256 mismatch => P11_REUSE_ARTIFACT_INVALID;
8. loaded manifest source_package_sha256 mismatch => no reuse; exact source-package change reason retained;
9. loaded periodic document identity != requested target slot => P11_REUSE_ARTIFACT_INVALID;
10. loaded manifest parser_version != registry record parser_version => P11_REUSE_ARTIFACT_INVALID;
11. loaded manifest schema_version != registry record schema_version => P11_REUSE_ARTIFACT_INVALID;
12. loaded manifest validation_status != validation.status or either != registry record validation_status => P11_REUSE_ARTIFACT_INVALID;
13. loaded manifest blocking_issue_count != len(validation.blocking_issues) or either != registry record blocking_issue_count => P11_REUSE_ARTIFACT_INVALID;
14. loaded validation compatibility_status != registry record compatibility_status => P11_REUSE_ARTIFACT_INVALID;
15. parity-passing exact-package REVIEW_REQUIRED/blocked/incompatible record => not reusable under the corresponding validation/reuse reason;
16. multiple fully reusable runs for one exact package select lexicographically smallest parse_run_id only after all exact-package checks;
17. document_sha256 equality alone is never sufficient for US reuse.

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
- existing deterministic final export differs from current staging/identity -> P11_FINAL_ARTIFACT_COLLISION
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

Record for each representative live run in a separate project-local performance receipt outside final `export-v2` and outside registry `artifact_path`:

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
