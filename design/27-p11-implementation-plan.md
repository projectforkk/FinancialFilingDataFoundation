# 27 — P11 US SEC Provider Implementation Plan

Status: **DESIGN BASELINE CANDIDATE / PRODUCTION CLOSED**

Detailed design:
`design/26-p11-sec-provider-design.md`

Source-neutral contract:
`design/30-parsed-financial-document-v2-contract.md`

Acceptance baseline:
`acceptance/41-p11-acceptance-instruction.md`

Authorization:
`development/143-p11-design-authorization.md`

## P11-A — Design Baseline

Deliver:

- environment/interface audit;
- design/30 v2 contract;
- design/26 detailed design;
- design/27 implementation plan;
- acceptance/41 baseline;
- status/index/master/roadmap reconciliation;
- UTF-8 no BOM;
- git diff --check;
- design review;
- commit/push.

Gate:

`P11_READY_FOR_DEVELOPMENT`

No production code before PASS + explicit development authorization.

## P11-B — Environment / SEC Runtime Probe

Read-only / isolated probe only.

Confirm:

- main Python architecture/version;
- project-local Python 3.12 AMD64 viability;
- Arelle candidate exact version and package provenance;
- lxml wheel viability;
- runtime lock strategy;
- SEC TLS/network reachability;
- explicit User-Agent configuration path;
- no root/global Python mutation;
- all temp/runtime paths under project root.

No permanent runtime install until this gate is separately authorized.

Evidence:
`development/<next>-p11-environment-runtime-probe.md`

## P11-C — Identity / Period Contract

Implement only:

- US market support;
- Q2 support;
- CIK normalization/validation;
- periodic form normalization;
- amended form normalization;
- supplemental accession identity model;
- deterministic accession helpers.

Must retain CN/HK behavior byte/semantic compatible.

Focused tests:

1. CN/HK unchanged and still require non-empty ticker;
2. US CompanyRef with zero-padded CIK and ticker=null;
3. US CIK-only flow does not fabricate ticker;
4. one official ticker may populate normalized display ticker;
5. multiple official tickers with no caller selection => ticker=null;
6. ticker-only zero match => P11_COMPANY_IDENTITY_NOT_FOUND;
7. ticker-only multiple-CIK match => P11_COMPANY_IDENTITY_AMBIGUOUS;
8. caller ticker/CIK mismatch => P11_COMPANY_IDENTITY_AMBIGUOUS;
9. invalid CIK rejected;
10. Q2 valid for US;
11. Q2 rejected for CN;
12. Q2 rejected for HK;
13. H1 remains valid for existing markets;
14. 10-K/A normalization;
15. 10-Q/A normalization;
16. 20-F/A normalization;
17. 40-F/A normalization;
18. 8-K/6-K supplemental identity;
19. no forced 8-K/6-K periodic slot;
20. `PackageAwarePlannerRequired` exact class/base/reason_code/message;
21. generic IncrementalPlanner US guard executes before `build_required_slots` and before any registry method call;
22. CN/HK IncrementalPlanner return behavior remains unchanged.

STOP before acquisition changes if identity design assumption fails.

## P11-D — SEC HTTP / Discovery Client

**Preimplementation Design-First contract is frozen in `design/31-p11-d-http-discovery-contract.md`, but P11-D implementation remains NOT AUTHORIZED until that amended contract passes fresh detached design review.**

The normative design/31 contract freezes exact:

- User-Agent grammar/config source;
- timeout values;
- response-size limits by endpoint/content class;
- retry counts/backoff ceilings;
- redirect count;
- cross-process aggregate rate-gate lock/state format;
- failure recovery for stale/crashed lock holder.

The implementation must use one project-root-shared no-burst limiter with >=125 ms between outbound SEC request starts, giving <=8 requests/sec aggregate inside the supported single-installation boundary. If shared coordination is unavailable, block with `P11_RATE_LIMIT_SCOPE_UNSAFE`.

Implement dedicated SEC client contract:

- Submissions API;
- historical shard following;
- ticker lookup helper;
- strict HTTPS/host rules;
- explicit User-Agent;
- rate limiter;
- bounded timeout/retry;
- redirect revalidation;
- response-size caps;
- structured deterministic errors.

No package writes yet except isolated test fixtures if explicitly authorized.

Focused tests include:

- no User-Agent => block;
- >10 rps impossible;
- 429 Retry-After;
- 404 no retry storm;
- 5xx bounded retry;
- redirect to non-allowlisted host blocked;
- file:// rejected;
- malformed JSON rejected;
- current/historical submissions merged deterministically.

## P11-E — SEC Package Store

Implement:

- content-addressed assets;
- source package manifest;
- atomic staging/commit;
- exact SHA/size verification;
- package hash;
- receipt;
- source drift preservation;
- path traversal rejection;
- package/asset count/size caps.

Do not modify P2 RawDocumentStore behavior.

Focused tests:

- exact-byte identity;
- exact known `p11-sec-source-package-identity-v1` hash fixture;
- asset caller/order independence under canonical sort;
- canonical requested source_url participates in package identity;
- redirect-final URL/declared HTTP media/local-path/timestamp/request/ETag diagnostics do not change package identity;
- changed role/hash/file_name/source_url/size/dependency topology does change package identity;
- accession index.json required and byte-addressed;
- primaryDocument must be present in index.json;
- every index-listed .xsd/.xml captured under exact role rules;
- unrelated HTML/text exhibit not auto-downloaded;
- explicitly requested safe-basename exhibit captured only if listed in index.json;
- project-root-relative POSIX `local_content_path` round-trip;
- absolute/drive-relative/traversal local path reject;
- two distinct logical assets may share one asset_sha256 and remain two manifest/source-assets rows;
- content-addressed blob bytes stored once/reused;
- exact duplicate logical key (file_name, canonical source_url) rejected;
- role precedence FILING_INDEX > PRIMARY_DOCUMENT > structured suffix > REQUESTED_EXHIBIT;
- requested exhibit already included at higher precedence adds no duplicate row and keeps existing role;
- exact provider filename case preserved; lowercase used only for classification;
- asset_sha256 from exact captured bytes;
- byte_size from exact captured length;
- declared index size mismatch blocks;
- primary boolean true iff PRIMARY_DOCUMENT role;
- every direct accession-directory asset has dependency_depth=0 and referring_asset_sha256=null;
- package filingDate valid/missing/malformed cases;
- package discovery reportDate valid/null/malformed cases;
- same accession/new bytes => new package;
- existing package collision mismatch blocked;
- atomic failure leaves no partial accepted package;
- path escape blocked;
- timestamps excluded from package identity.

## P11-F — SEC Runtime / Parser

Create isolated P11 runtime only after P11-B PASS and after P11-E can assemble a complete deterministic accession package.

**Before any P11-F parser production code, perform a Design-First parser-contract freeze.**

It must record:

- exact runtime Python/version/architecture;
- exact Arelle/parser/HTML/XML library versions and dependency lock;
- exact `source_kind` classification rules;
- exact deterministic `media_type` classification rules for captured assets;
- HTML parser recovery/tree-normalization behavior;
- XML parser security/entity/network behavior;
- exact source-segment boundary and `normalized_text` rules;
- exact section detection/heading hierarchy rules;
- exact DOM table inclusion, cell text, rowspan/colspan and header-tree rules;
- exact Inline XBRL transformation registry behavior;
- `continuedAt` and `ix:exclude` behavior;
- canonical QName/DOM/XML locator golden fixtures;
- exact raw_value whitespace rule fixtures;
- exact parsed-decimal golden cases for format/scale/sign/nil;
- external taxonomy resolution/cache behavior;
- exact mapping of unresolved dependencies to REVIEW_REQUIRED vs BLOCKED;
- proof that deterministic parse performs no unrecorded network.

Candidate:

- Python 3.12 AMD64;
- arelle-release pinned;
- lxml pinned transitively/explicitly;
- lock file with hashes;
- source/runtime descriptor.

Parser operations:

- exact primary HTML/iXBRL parse;
- filing-local XML/XBRL parse;
- source segment extraction;
- section extraction;
- DOM table extraction;
- raw iXBRL/XBRL fact extraction;
- DEI fact extraction needed for later period binding;
- Arelle/local XBRL validation where frozen.

No network during deterministic parse.

P11-F MUST NOT mutate the already committed P11-E source package, add external taxonomy assets to it, or change `source_package_sha256`. External taxonomy/runtime-cache behavior is separate and frozen by the parser-contract amendment.

Focused tests use local frozen fixtures.

## P11-G — Final Period / Filing Identity Binding

Use P11-F parser outputs to confirm the final periodic identity in memory before any v2 document is written.

Extract/confirm:

- DocumentFiscalYearFocus;
- DocumentFiscalPeriodFocus;
- DocumentPeriodEndDate;
- immutable package discovery report_date from Submissions;
- form/report-date consistency.

Final periodic report_date follows design/26 Section 7 exactly: discovery vs DEI must agree when both exist, one may fill when the other is null, neither => P11_PERIOD_UNRESOLVED, disagreement => P11_PERIOD_CONFLICT. Package identity is never rewritten.

No registry write occurs in P11-G.

Rules tested:

- 10-K FY;
- 10-Q Q1/Q2/Q3;
- Q2 valid iff market=US;
- CN Q2 rejected;
- HK Q2 rejected;
- Q2 never aliases H1;
- 20-F/40-F FY;
- unresolved DEI => P11_PERIOD_UNRESOLVED;
- conflicting DEI/request => P11_PERIOD_CONFLICT;
- amendment remains distinct accession variant;
- multiple variants do not silently canonicalize.

Output of P11-G is the confirmed filing identity consumed by the v2 writer.

## P11-H — SEC Validation

Run deterministic validation over:

- immutable P11-E source package;
- P11-F parser outputs;
- P11-G confirmed filing identity.

Validation layers:

1. source/package integrity;
2. CIK/accession/form/report-date consistency;
3. DEI identity/period consistency;
4. fact/context/unit integrity;
5. duplicate/conflicting facts;
6. parser/Arelle validation mapping;
7. completeness signals;
8. compatibility/reuse status.

P11-H produces the final deterministic validation model consumed by P11-I, including:

- status = PASS | FAIL | REVIEW_REQUIRED | BLOCKED;
- compatibility_status;
- blocking_issues;
- warnings;
- structural/source/XBRL/financial/completeness check results;
- validator_version.

No `export-v2` directory, final `manifest.json`, or final `validation.json` is written in P11-H.

No registry write occurs in P11-H.

Companyfacts cross-check is optional/auxiliary and cannot turn invalid filing evidence into PASS.

## P11-I — Final ParsedFinancialDocument v2 Writer / Loader / Commit

Implement design/30 over:

- P11-F parser outputs;
- P11-G confirmed filing identity;
- P11-H final validation model.

For periodic filings, `document.json.fiscal_year` and `raw_fiscal_period` MUST come from the confirmed P11-G identity. No provisional/null periodic identity is permitted merely to allow writing.

Final required artifacts:

- manifest;
- document;
- source assets;
- segments;
- sections;
- tables;
- raw facts;
- evidence;
- validation.

Finalization order:

1. construct deterministic non-validation artifact bytes using the exact design/30 canonical JSON/JSONL serializer, row order, UTF-8/no-BOM/LF-only rules, and extensionless SHA-only raw blob path contract;
2. serialize P11-H final `validation.json`;
3. derive manifest `validation_status` and `blocking_issue_count` exactly from that validation model;
4. serialize final `manifest.json`;
5. write/verify all required files/counts/IDs/hashes/source references with the v2 loader in an exclusive attempt staging directory under `<parsed_root>/.staging/<parse_run_id>/<attempt_token>/export-v2`;
6. evaluate the deterministic final path `<parsed_root>/<parse_run_id>/export-v2`:
   - already present before commit => never overwrite; enter exact existing-final verification;
   - absent => perform exactly one atomic non-replacing same-filesystem directory commit;
7. classify the commit attempt:
   - `COMMITTED_NEW` => reload final path;
   - `DESTINATION_EXISTS` => concurrent winner/earlier attempt exists; enter exact existing-final verification;
   - `COMMIT_ERROR` => `P11_FINAL_ARTIFACT_COMMIT_FAILED` / BLOCKED; do not infer success from later path presence;
8. existing-final verification requires exact identity/validation semantics plus byte-for-byte equality of every required artifact against this attempt's validated staging export;
9. if existing final path differs/misses/fails => `P11_FINAL_ARTIFACT_COLLISION` / BLOCKED;
10. after new commit or idempotent existing-final success, reload the final path;
11. only after successful final reload may P11-K persist `ParsedDataRecord`.

Existing-final byte equality is checked over every required v2 file, not merely manifest identity.

A successful idempotent existing-final check discards/retires only this attempt's staging directory and keeps the original final directory unchanged.

Concurrent writers for one `parse_run_id` MUST use distinct staging directories. Exactly one no-replace commit can return `COMMITTED_NEW`; any losing writer that receives `DESTINATION_EXISTS` can succeed only after the same loader/identity/all-nine-byte existing-final verification. P11-B must prove the target runtime's exact no-replace atomic directory commit primitive before production authorization.

Final writer/loader must verify:

- schema;
- counts;
- hashes;
- IDs;
- locator integrity;
- `source_asset_id` recomputes from exact logical filename/source_url/content SHA;
- every artifact `source_asset_id + source_asset_sha256` pair resolves to exactly one logical source row;
- duplicate-content logical rows remain distinguishable;
- `primary_source_asset_id` resolves to the unique PRIMARY_DOCUMENT row;
- asset references;
- package/document identity;
- periodic document identity matches the confirmed binding;
- manifest validation_status/blocking_issue_count match validation.json;
- no provisional validation placeholder exists.

P11-I is the only gate that creates a registry-eligible final `export-v2` directory.

Byte-determinism requirements:

- all three JSON files use the exact canonical JSON bytes + one final LF from design/30;
- all six JSONL files use canonical row bytes, exact frozen top-level row ordering and LF-only line framing from design/30;
- empty JSONL = zero bytes;
- final artifact generation MUST NOT serialize wall-clock/performance/request/process/temp-path diagnostics;
- any performance/attempt diagnostics are written only to separate receipts outside `export-v2`;
- same exact source package + parser/config/identity/validation semantic model MUST reproduce identical SHA256 for all nine required final files;
- caller/input collection order, Python mapping/set iteration order and host newline mode MUST NOT affect final bytes;
- same-content logical assets with different source filename extensions still share the same extensionless SHA-only raw blob path.

No registry write occurs in P11-I.
No v1 masquerading.

Focused P11-I tests:

- two serializations with different wall-clock/performance receipt values produce identical hashes for all nine final files;
- CRLF/native-newline host settings do not change final bytes;
- JSON object insertion order does not change JSON bytes;
- shuffled caller/input row order does not change JSONL bytes;
- exact top-level JSONL row ordering matches design/30;
- semantically unordered issue/warning arrays are canonical-byte sorted;
- empty JSONL is zero bytes;
- same SHA under different logical filename extensions produces one extensionless physical blob path;
- no forbidden diagnostic field appears in any final export file;
- one semantic field change changes the relevant final bytes as expected.

## P11-J — Supplemental 8-K / 6-K

Implement accession-bound supplemental ingest.

No periodic slot forcing.

P11 v1 supplemental persistence is limited to source package + ParsedFinancialDocument v2 + supplemental export.

Do NOT write 8-K/6-K into the existing periodic SQLiteRegistry / ParsedDataRecord path.

Supplemental identity fields:

- fiscal_year null unless exact filing-native evidence supplies it;
- raw_fiscal_period always null;
- report_date official non-empty valid reportDate or null;
- no filing-date/calendar inference.

Primary document mandatory.

Requested exhibit acquisition is explicit and allowlisted by filing directory metadata.

Tests:

- 8-K primary only;
- 8-K/A;
- 6-K;
- requested exhibit;
- unrelated exhibit not downloaded by default;
- supplemental export retains accession identity.

## P11-K — Registry / Parsed Data / Package-Aware Incremental Reuse

Integrate **periodic SEC v2 results only** into existing registry with additive compatibility.

Supplemental 8-K/6-K remain outside the existing SQLiteRegistry / ParsedDataRecord path in P11 v1.

Registry/ParsedData persistence occurs only after P11-H validation has produced the final status, P11-G identity is confirmed, and P11-I has atomically committed/reloaded the complete final v2 export.

### Generic planner safety boundary

After P11-C adds US to CompanyRef:

- accepted generic IncrementalPlanner remains CN/HK document-SHA planner;
- IncrementalPlanner.build_plan for market=US MUST fail closed with `P11_PACKAGE_AWARE_PLANNER_REQUIRED`;
- P11 v1 US orchestration MUST use the dedicated package-aware SEC reuse selector;
- no generic planner fallback is allowed.

### Periodic persistence

For periodic filings:

- register the primary exact source asset with the confirmed filing identity;
- persist ParsedDataRecord only after the v2 artifact has been written/loaded and validation completed;
- artifact_path is mandatory for P11 periodic records and is the project-root-relative POSIX path to the exact `<parsed_root>/<parse_run_id>/export-v2` directory;
- parse_run_id is validated as lowercase 64-hex before path construction;
- the complete export-v2 directory is atomically committed or idempotently verified before registry persistence;
- an existing final export is never overwritten/deleted/replaced;
- any existing-final byte/identity mismatch => P11_FINAL_ARTIFACT_COLLISION;
- registry never points to manifest.json, another child file, or a staging/partial directory;
- no trailing slash is stored;
- P11-K MUST call additive `SQLiteRegistry.register_parsed_data_atomic(record)` rather than accepted `register_parsed_data(record)`;
- canonical exception implementation = `financial_filing_data_foundation.registry.sqlite_registry.ParsedDataRecordConflict`;
- canonical public exception import = `from financial_filing_data_foundation.registry import ParsedDataRecordConflict`; registry `__init__` re-exports the same class object, not an alias/wrapper/duplicate;
- `register_parsed_data_atomic` starts `BEGIN IMMEDIATE` before the parse_run_id lookup, so exact concurrent P11 writers serialize before the existence check;
- exact existing row across all persisted semantic fields except created_at => normal idempotent success;
- missing row => insert once and commit;
- same parse_run_id with any different persisted semantic field => `ParsedDataRecordConflict` => `P11_REGISTRY_RECORD_CONFLICT` / BLOCKED;
- SQLite busy/locked/I/O/commit or other persistence failure => `P11_REGISTRY_PERSISTENCE_FAILED` / BLOCKED;
- there is no hidden retry loop inside registry persistence;
- on registry failure after final export success, leave the final export unchanged; a later outer retry must re-verify the exact existing final export before retrying atomic registry persistence;
- an unregistered orphan final export is not reusable because the package-aware selector discovers candidates only from registry rows;
- `REGISTRY_SCHEMA_VERSION` remains 1 and no P11 schema migration is required;
- accepted `register_parsed_data()` and existing CN/HK callers remain unchanged.

### Package-aware reuse public API

Implement exact types from design/26 Section 17.1:

- `SecReuseAction`;
- `SecReuseReason`;
- frozen/slots `SecReuseDecision`.

Public module:
`financial_filing_data_foundation.sec.reuse`

Exact decision invariants, reason priority and candidate classification come from design/26 and are not implementation choices.

Focused API tests:

- exact `PackageAwarePlannerRequired` module/export/class/base/reason_code/message;
- generic US guard before build_required_slots/registry access;
- exact `select_sec_reuse(registry, slot, document_sha256, source_package_sha256, reuse_policy, project_root, parsed_root)` signature;
- non-US slot exact ValueError;
- invalid document/package SHA exact ValueError messages;
- parsed_root outside project_root exact ValueError;
- exact enum values;
- exact dataclass field order;
- REUSE_DATA invariant enforcement;
- PARSE_CURRENT_PACKAGE invariant enforcement;
- zero-candidate decision = P11_NO_REUSABLE_EXACT_PACKAGE;
- mixed candidate failure reasons use the exact priority order;
- selector is read-only;
- successful decision has empty rejection_reasons;
- selector returns SecReuseDecision, never ParsedDataRecord.

### Package-aware reuse selector

Runtime orchestration position:

```text
requested target slot
→ discovery
→ P11-E package
→ package-aware reuse check
    ├─ exact reusable artifact → REUSE_DATA and skip parser/identity/v2/validation
    └─ no reusable artifact → P11-F → P11-G → P11-H → P11-I → persist
```

Input:

- requested target FilingSlotKey (declared request target, not newly source-confirmed);
- current document_sha256;
- current source_package_sha256;
- reuse policy / accepted parser-schema policy;
- project root + configured P11 parsed-artifact root.

Algorithm:

1. call SQLiteRegistry.list_parsed_data(slot);
2. null artifact_path => P11_REUSE_ARTIFACT_MISSING;
3. resolve artifact_path as a project-root-relative POSIX directory path and require it to equal the expected `<parsed_root>/<record.parse_run_id>/export-v2` location;
4. absolute/drive-relative/UNC/traversal/outside-root or wrong-layout path => P11_REUSE_ARTIFACT_PATH_INVALID;
5. safe expected path absent => P11_REUSE_ARTIFACT_MISSING;
6. existing path not a directory or missing any required v2 file => P11_REUSE_ARTIFACT_INVALID;
7. load the directory with the P11 v2 loader;
8. require loaded manifest parse_run_id == record.parse_run_id;
9. require loaded manifest/document document_sha256 == current document_sha256 == record.document_sha256;
10. require loaded manifest source_package_sha256 == current source_package_sha256;
11. require loaded document periodic identity == requested target slot;
12. require exact registry/artifact metadata parity before policy classification:
   - manifest parser_version == record.parser_version;
   - manifest schema_version == record.schema_version;
   - manifest validation_status == validation.status == record.validation_status.value;
   - manifest blocking_issue_count == len(validation.blocking_issues) == record.blocking_issue_count;
   - validation compatibility_status == record.compatibility_status.value;
13. any parity mismatch => P11_REUSE_ARTIFACT_INVALID;
14. apply parser/schema reuse policy only to parity-verified values;
15. require PASS, zero blockers and COMPATIBLE;
16. only exact-package survivors are reusable;
17. if multiple exact-package survivors remain, choose lexicographically smallest parse_run_id.

Explicit results:

- same document SHA + different package SHA => `P11_SOURCE_PACKAGE_CHANGE`, parse current package;
- missing artifact => `P11_REUSE_ARTIFACT_MISSING`;
- invalid/outside path => `P11_REUSE_ARTIFACT_PATH_INVALID`;
- loader/hash/identity mismatch => `P11_REUSE_ARTIFACT_INVALID`;
- no exact-package reusable record => parse current package;
- document SHA equality alone is never sufficient.

Focused tests:

- exact package reuse PASS and parser/identity/v2/validation stages are skipped;
- same primary bytes + different index/XBRL package => no reuse;
- same package + two valid parse runs => deterministic smallest parse_run_id;
- null/missing artifact path => no reuse;
- absolute/UNC/traversal/outside-root artifact path => no reuse;
- manifest package mismatch => no reuse;
- manifest document mismatch => no reuse;
- manifest parse_run mismatch => no reuse;
- manifest/registry parser_version mismatch => P11_REUSE_ARTIFACT_INVALID;
- manifest/registry schema_version mismatch => P11_REUSE_ARTIFACT_INVALID;
- manifest/validation/registry validation_status mismatch => P11_REUSE_ARTIFACT_INVALID;
- manifest/validation/registry blocking_issue_count mismatch => P11_REUSE_ARTIFACT_INVALID;
- validation/registry compatibility_status mismatch => P11_REUSE_ARTIFACT_INVALID;
- validation/compatibility rejection is applied only after registry/artifact parity passes;
- generic IncrementalPlanner US call blocks;
- existing CN/HK planner/reuse suite unchanged.

Existing CN/HK reuse semantics remain unchanged.

## P11-L — Full Regression / Security

Run:

- P11 focused;
- full P0-P11 unit;
- compile/import;
- git diff --check;
- CN/HK acquisition regression;
- P8/P9/P10 zero unintended diff;
- dependency/runtime audit;
- runtime lock verification;
- arbitrary network/path negative scan;
- no remote AI.

Gate: PASS.

## P11-M — Live SEC Runs

At minimum:

1. domestic 10-K Inline XBRL;
2. domestic 10-Q Inline XBRL;
3. Q2 period case;
4. foreign issuer 20-F or 40-F;
5. supplemental 8-K or 6-K;
6. amendment;
7. custom taxonomy fact.

For each live run:

- official SEC discovery;
- exact source package;
- exact hashes;
- v2 parse;
- evidence link;
- validation result;
- registry/reuse behavior where periodic;
- request count/rate;
- source bytes immutable.

No live test may exceed SEC fair-access ceiling.

## P11-N — Negative Capability Gates

Must prove:

- ticker/CIK ambiguity => explicit block/review;
- missing filing => P11_FILING_NOT_FOUND;
- missing User-Agent => P11_USER_AGENT_REQUIRED;
- hostile redirect => P11_REDIRECT_NOT_ALLOWED;
- oversized response => P11_RESPONSE_TOO_LARGE;
- source-content drift => P11_SOURCE_CONTENT_DRIFT;
- missing dependency => P11_DEPENDENCY_UNRESOLVED;
- visual-only interpretation => P11_VISUAL_RENDERING_REQUIRED;
- period conflict => P11_PERIOD_CONFLICT;
- custom taxonomy not silently dropped;
- companyfacts mismatch cannot override filing source.

## P11-O — Formal Code Review

Fresh detached exact-candidate worktree.

Review:

- design baseline;
- identity/period semantics;
- official-source boundary;
- security/fair access;
- package identity;
- parser evidence integrity;
- v2 contract;
- no synthetic PDF evidence;
- CN/HK regression;
- P8/P9/P10 unchanged;
- runtime lock;
- live/negative evidence.

Verdict:
PASS / FAIL / BLOCKED.

## P11-P — Acceptance Freeze

Freeze:

- exact design baseline;
- exact production candidate;
- formal review PASS;
- runtime lock;
- official source fixtures;
- live accession targets;
- expected source/package hashes where stable;
- test commands;
- security limits;
- basetemp paths;
- accepted P0-P10 immutability manifest.

Any production/design/acceptance-package change invalidates freeze.

## P11-Q — Independent Acceptance

Fresh detached worktree.

Must independently repeat:

- focused/full regression;
- identity/period cases;
- SEC package acquisition from official endpoints;
- v2 parse/evidence;
- periodic live cases;
- supplemental case;
- amendment case;
- custom taxonomy preservation;
- negative security/capability gates;
- immutable P0-P10 base.

No production/test/design edits during acceptance.

## P11-R — Closeout

Only after Independent Acceptance PASS:

- acceptance result;
- fresh integration branch from current accepted main;
- post-merge regression;
- final main verification;
- P11_DONE governance sync.

P11 closeout does not automatically authorize:

- P8/P10 SEC query compatibility extension;
- Research MCP;
- Semantic Resolver;
- later phase production.

## Issue Rule

Any material issue:

```text
STOP
→ facts/root cause
→ amend design/26 + design/27 + acceptance/41 (+ design/30 if contract affected)
→ commit/push new baseline
→ invalidate affected evidence
→ reauthorize
```

No code-first/design-later.
