# 144 — P11 Environment / Accepted Interface Audit

Status: **PASS — P11 DESIGN MAY PROCEED / PRODUCTION REMAINS CLOSED**

Phase:
P11 — US SEC Provider

Design authorization:
`development/143-p11-design-authorization.md`

Design worktree:
`D:\\Codex\\FinancialFilingDataFoundation\\worktrees\\active\\p11-sec-provider-design`

Design branch:
`design/p11-sec-provider`

Design start:
`5f64f7488c4b6558e4b90fb10142b23594785a6d`

## 1. Current environment

FFDF main runtime:

- Python 3.14.9
- Windows ARM64
- `lxml`: absent
- `bs4`: absent
- `html5lib`: absent
- `requests`: absent
- `httpx`: absent
- `arelle`: absent
- `pyxbrl`: absent
- `sec_edgar_downloader`: absent

No dependency manifest is currently used at repository root.

Existing isolated runtimes prove project-local Python 3.12 AMD64 isolation is available.

## 2. Official SEC source facts

Reviewed 2026-11-04 from official SEC documentation:

- `data.sec.gov` exposes public JSON APIs without API keys;
- Submissions API provides filer submission history;
- XBRL APIs cover 10-Q, 10-K, 8-K, 20-F, 40-F, 6-K and variants;
- APIs update throughout the day;
- current automated access maximum is 10 requests/second;
- SEC requires declared automated access / appropriate User-Agent behavior;
- accession number is the EDGAR submission identity;
- CIK is the SEC filer identity;
- ticker/CIK association files exist but SEC does not guarantee their accuracy/scope;
- post-acceptance corrections/deletions can change historical index state;
- Inline XBRL is the normal structured financial statement carrier for domestic operating companies and relevant foreign private issuer forms.

Official references:

- https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data
- https://www.sec.gov/about/webmaster-frequently-asked-questions
- https://www.sec.gov/data-research/structured-data/inline-xbrl
- https://www.sec.gov/file/company-tickers
- https://www.sec.gov/submit-filings/technical-specifications

## 3. XBRL runtime candidate

Current Arelle release observed on 2026-11-04:

- package: `arelle-release`
- version: `2.47.4`
- released: 2026-10-31
- requires Python >=3.11
- wheel: `py3-none-any`
- supports Inline XBRL 1.1 / XBRL 2.1
- supports SEC EDGAR validation tooling
- release wheel SHA256 published by PyPI:
  `366b9ced1a9e5058a31f4ffd347ec6fc6900c6931ade3d97a36d7836151fe3e1`

Arelle is a design candidate only. No runtime/dependency installation is authorized yet.

Recommended implementation boundary:
dedicated project-local P11 SEC runtime, preferably Python 3.12 AMD64, with a locked dependency set.

## 4. Accepted interface audit

### 4.1 Identity

Current P1 constraints:

- markets = `CN/HK` only;
- periods = `Q1/H1/Q3/FY`;
- no `US`;
- no `Q2`.

Therefore existing identity models cannot represent ordinary US 10-Q history without semantic corruption.

Do not map US Q2 to H1.

### 4.2 Acquisition

`AcquisitionProvider` abstraction is reusable in concept.

Current concrete acquisition models/service are not source-neutral:

- AcquisitionRequest rejects non-CN/HK;
- AcquisitionCandidate rejects periods outside Q1/H1/Q3/FY;
- expected providers are hard-coded to cninfo/hkexnews;
- source hosts are hard-coded to CNINFO/HKEX;
- receipt schema is Dayu/PDF-specific;
- candidate selection requires fiscal period before download.

SEC requires provisional discovery because reliable fiscal-period focus may need filing/iXBRL DEI facts after acquisition.

### 4.3 Raw store

Current `RawDocumentStore` is PDF-only:

- staging suffix = .pdf;
- PDF magic required;
- final object suffix = .pdf.

It cannot safely store SEC HTML/XML/JSON source packages.

### 4.4 Registry

Registry document hashing/registration is mostly source-neutral.

Positive facts:

- arbitrary files can be registered;
- non-PDF files receive `page_count=None`;
- SourceMetadata is generic enough for provider/source URL/title/CIK metadata.

Constraints:

- FilingSlotKey still blocks US/Q2;
- ParsedDataRecord remains slot-bound;
- supplemental 8-K/6-K filings need a separate identity path or explicit planner extension.

### 4.5 PDF pipeline

P3 native parser is explicitly PDF-only.

P3/P5/P6 current artifact semantics require physical PDF constructs:

- physical `page_no`;
- bbox;
- word/block/line identities;
- table-cell geometry;
- P6 evidence IDs derived from page/word/bbox refs.

SEC HTML/iXBRL/XBRL must not fabricate virtual physical pages or synthetic bbox merely to satisfy these schemas.

### 4.6 P8/P9/P10

P8 catalog v1 requires P3/P5/P6/P7 directories.
P8 result/tool contract is accepted and frozen.

P10 v1 fingerprints the exact P8/P9 contract and currently reports:
`P11_SEC_PROVIDER = UNAVAILABLE`.

P11 v1 must not silently alter P8/P9/P10 accepted contracts.

Any future direct P10 consumption of SEC-native artifacts requires a separate explicit compatibility design/review/acceptance gate.

## 5. Design issues opened

### P11-ISSUE-001 — US identity gap

Need:

- market US;
- canonical CIK identity;
- Q2 support;
- exact form/amendment semantics;
- separate periodic vs supplemental filing role.

### P11-ISSUE-002 — acquisition core is CN/HK/PDF-specific

Need additive SEC acquisition contract without regressing P2.

### P11-ISSUE-003 — raw store is PDF-only

Need source-package storage for HTML/XML/JSON and exact raw bytes.

### P11-ISSUE-004 — ParsedFinancialDocument v1 is physical-PDF-specific

Need additive source-neutral v2 contract.
Do not rewrite accepted v1 history.

### P11-ISSUE-005 — SEC discovery period binding

Submissions metadata alone is insufficient for a trustworthy US fiscal-quarter slot in all cases.

Use filing facts such as DEI DocumentFiscalPeriodFocus / DocumentFiscalYearFocus for final binding when available.

### P11-ISSUE-006 — ticker is not canonical identity

SEC ticker files are lookup hints, not guaranteed authoritative identity.

CIK is provider canonical company identity.

### P11-ISSUE-007 — companyfacts is not filing truth

SEC companyfacts aggregates standard taxonomy facts and excludes custom-taxonomy facts.

Use exact filing/iXBRL/XBRL assets as primary evidence.
Companyfacts may be cross-check/acceleration only.

### P11-ISSUE-008 — post-acceptance corrections

Accession identity alone is not sufficient for byte identity.

Store exact source bytes + SHA256 + package manifest identity.

### P11-ISSUE-009 — fair access/security

Design must enforce:

- explicit User-Agent;
- <=10 requests/sec globally per process;
- HTTPS;
- strict SEC/FASB allowlist as needed;
- redirect revalidation;
- response-size limits;
- content-type checks;
- no arbitrary URL fetch;
- no archive path traversal.

## 6. Recommended architecture direction

P11 v1 should implement a parallel SEC-native path:

```text
SEC identity resolver
→ Submissions discovery
→ accession package acquisition
→ immutable SEC package store
→ HTML/iXBRL/XBRL parse
→ source-neutral ParsedFinancialDocument v2
→ deterministic SEC validation
→ parsed-data registry/export
```

Do not route SEC HTML through PDF conversion.

Do not create fake page/bbox evidence.

P11 v1 should preserve accepted P8/P9/P10 production unchanged.

## 7. Periodic vs supplemental filing scope

Periodic slot-bound v1 targets:

- 10-K / 10-K/A;
- 10-Q / 10-Q/A;
- 20-F / 20-F/A;
- 40-F / 40-F/A.

Supplemental accession-bound ingestion targets:

- 8-K / 8-K/A;
- 6-K / 6-K/A.

Supplemental filings are not silently forced into Q1/Q2/Q3/FY planner slots.

## 8. Production authorization status

No P11 production code is authorized.

Next design outputs:

- `design/30-parsed-financial-document-v2-contract.md`;
- `design/26-p11-sec-provider-design.md`;
- `design/27-p11-implementation-plan.md`;
- `acceptance/41-p11-acceptance-instruction.md`.

Only after design review + design baseline commit/push may a separate P11 development authorization be considered.


## 9. Detached review amendment findings (P11-ISSUE-010..016)

Detached review of candidate `3ccaedc14a4c0f3f222cd192c8b7e1479d787ccd` stopped before development authorization.

Stop record:
`development/147-p11-detached-design-review-stop.md`

Findings and amended resolution:

- **P11-ISSUE-010 — aggregate SEC rate scope**: CLOSED IN AMENDED DESIGN. Replace per-process interpretation with one project-root-shared cross-process no-burst gate, >=125 ms between outbound SEC request starts, <=8 req/s aggregate in the supported single-installation boundary. Unsafe/unavailable coordination => `P11_RATE_LIMIT_SCOPE_UNSAFE`.
- **P11-ISSUE-011 — package identity payload**: CLOSED IN AMENDED DESIGN. `p11-sec-source-package-identity-v1` exact object, exact asset identity fields/sort and exclusion list frozen in design/26 Section 15.
- **P11-ISSUE-012 — local content path semantics**: CLOSED IN AMENDED DESIGN. Persist project-root-relative POSIX only, resolve inside configured SEC raw-assets root, exclude from deterministic identities.
- **P11-ISSUE-013 — canonical source-node locator**: CLOSED IN AMENDED DESIGN. HTML same-tag sibling-index path and XML/iXBRL Clark-QName sibling-index path plus exact locator objects frozen in design/30 Section 11.1.
- **P11-ISSUE-014 — v2 deterministic ID formulas**: CLOSED IN AMENDED DESIGN. Exact objects for evidence/raw fact/config/parse run/segment/section/table/cell IDs frozen in design/30.
- **P11-ISSUE-015 — Inline XBRL raw/transformed value rule**: CLOSED AT BASE CONTRACT + PREIMPLEMENTATION FREEZE. Normative raw_value/transform boundary frozen now; exact parser/runtime transformation implementation must be Design-First frozen after P11-B and before any P11-G code.
- **P11-ISSUE-016 — CIK/accession/path grammar**: CLOSED IN AMENDED DESIGN. Exact CIK/accession grammar and primaryDocument basename rules frozen in design/26 Section 6.

P11-D also receives a mandatory preimplementation HTTP-contract freeze for exact timeout/size/retry/User-Agent and rate-lock recovery parameters.

No production/test/runtime change was made while resolving these design issues.


## 10. Second detached review findings (P11-ISSUE-017..019)

Fresh review of amended candidate `11648b22bfe97d88048c2dcf079034c37b3854af` stopped before development authorization.

Stop record:
`development/150-p11-amended-design-review-stop.md`

Resolution in the current amendment:

- **P11-ISSUE-017 — final package assembly**: CLOSED IN AMENDED DESIGN. Required accession-directory `index.json`, Submissions `primaryDocument`, automatic all-safe `.xsd/.xml` capture with exact suffix-role mapping, no automatic unrelated HTML/text exhibits, optional exhibit by exact safe basename present in index.json.
- **P11-ISSUE-018 — impossible gate order**: CLOSED IN AMENDED PLAN. Parser moves to P11-F, v2 writer/loader P11-G, final DEI period binding/registry P11-H.
- **P11-ISSUE-019 — Q2 market guard**: CLOSED IN AMENDED DESIGN. Q2 iff US; CN/HK Q2 rejected; existing H1 behavior preserved.

Official SEC Accessing EDGAR Data documentation was rechecked: accession-number directories contain machine-readable index.json and all submitted filing component documents are stored in the accession directory.

No production/test/runtime change was made.


## 11. Third detached review finding — P11-ISSUE-020

Fresh review of `ae0f2a1c4c1ac3c1586dba4fabee807f002af987` stopped because v2 writer preceded final periodic identity binding.

Stop:
`development/154-p11-corrected-design-review-stop.md`

Resolution in current amendment:

- P11-F parser extracts DEI/raw facts;
- P11-G confirms final period/filing identity in memory, no registry write;
- P11-H writes/loads v2 using confirmed identity;
- P11-I validates;
- P11-K performs registry/ParsedData persistence only after validation/reuse gate.

P11-ISSUE-020 is closed in the amended design, pending fresh detached review.


## 12. Final manual review finding — P11-ISSUE-021

Review of `a223d44d766609190806d1d349dab1d5d673423b` passed the automated design matrix but manual semantic review found supplemental identity nullability was incomplete.

Stop:
`development/157-p11-final-design-review-stop.md`

Resolution in current amendment:

- periodic v2 retains required confirmed fiscal_year/raw_fiscal_period/report_date;
- supplemental fiscal_year is nullable unless filing-native evidence explicitly establishes it;
- supplemental raw_fiscal_period is always null;
- supplemental report_date is official non-empty valid SEC reportDate or null;
- filing_date/calendar year is never used to guess missing supplemental fiscal metadata;
- P11 v1 supplemental filings stay outside existing periodic SQLiteRegistry/ParsedDataRecord and remain authoritative in source package + v2 + supplemental export.

No production/test/runtime change was made.


## 13. Logical asset identity finding — P11-ISSUE-022

Fresh review of `5e1a1b7b39544af6c3ba464fc576174b480bd3ad` passed the automated contract matrix but manual package review found content-blob SHA and logical accession asset identity were conflated.

Stop:
`development/160-p11-logical-asset-review-stop.md`

Resolution in current amendment:

- raw content blobs deduplicate by asset_sha256;
- package/source-assets rows represent logical assets keyed by exact (file_name, canonical requested source_url);
- multiple logical rows may share one SHA/blob;
- duplicate logical keys are invalid;
- role precedence is FILING_INDEX > PRIMARY_DOCUMENT > structured suffix > REQUESTED_EXHIBIT;
- requested asset already captured at higher precedence is not duplicated or re-roled;
- all direct accession-directory assets use dependency_depth=0 / referring_asset_sha256=null.

No production/test/runtime change was made.


## 14. Additional amendment finding — P11-ISSUE-023

While P11-ISSUE-022 was stopped, cross-stage review found package identity is computed before DEI-based final period/report-date binding, but the package identity itself contains report_date.

Without an explicit distinction, a parser could be tempted to rewrite package identity after DEI confirmation.

Resolution in current amendment:

- source-package identity report_date = normalized SEC Submissions discovery reportDate (valid YYYY-MM-DD or null if empty; malformed non-empty blocks);
- this package field is immutable once package hash is computed;
- final periodic v2 document report_date is confirmed in P11-G using discovery reportDate and DEI DocumentPeriodEndDate;
- both valid must match;
- one may supply the final value when the other is null;
- both absent => P11_PERIOD_UNRESOLVED;
- disagreement => P11_PERIOD_CONFLICT;
- final DEI confirmation never rewrites source_package_sha256.

P11-ISSUE-023 is closed in the amended design pending fresh review.


## 15. Additional amendment finding — P11-ISSUE-024

While ISSUE-022/023 remained stopped, field-nullability review found P11 had already declared CIK canonical and ticker display-only, but accepted P1 CompanyRef and v2 document schema still implied ticker was always non-empty.

Resolution in current amendment:

- CompanyRef ticker becomes market-conditionally optional: CN/HK still non-empty, US may be null;
- CIK-only US flow is valid and never fabricates ticker;
- ticker lookup key is ASCII-trim + ASCII uppercase;
- ticker-only zero official match => P11_COMPANY_IDENTITY_NOT_FOUND;
- multiple distinct CIK matches => P11_COMPANY_IDENTITY_AMBIGUOUS;
- caller ticker/CIK mismatch => P11_COMPANY_IDENTITY_AMBIGUOUS;
- when CIK is known and caller supplied no ticker, exactly one official ticker may populate display ticker; zero/multiple distinct tickers => ticker=null;
- v2 ticker is nullable for US;
- registry migration is unnecessary because current periodic SQLite slot/parsed-data identity does not persist ticker.

P11-ISSUE-024 is closed in the amended design pending fresh review.


## 16. Additional pre-candidate findings — P11-ISSUE-025..026

While ISSUE-022..024 remediation was still uncommitted and production remained closed, candidate-preflight review found two provenance/immutability gaps.

### P11-ISSUE-025 — logical source provenance collision

After allowing different logical accession assets to share identical bytes/SHA, v2 source-referencing artifacts still used only `source_asset_sha256`. That cannot distinguish two logical files that share one content blob.

Resolution:

- add deterministic `source_asset_id` derived from exact file_name + canonical requested source_url + asset_sha256;
- known fixture = `41183564053cd4f7be5c66d4ed4e7c44d72ad137f9aaf60e7f5bf30c9ef41fa2`;
- source-assets rows persist both logical ID and content SHA;
- document primary source references a `primary_source_asset_id`;
- segment/section/table/raw-fact/evidence rows carry both source_asset_id and source_asset_sha256;
- their deterministic IDs include source_asset_id, preventing same-content/different-source collisions;
- SOURCE_ASSET locator carries both logical ID and content SHA.

### P11-ISSUE-026 — parser-time package mutation ambiguity

The design reserved dependency_depth/referrer semantics for possible external dependencies after P11-E, but P11-E already commits the immutable package/hash before P11-F parser/runtime work.

Resolution:

- every P11 v1 package asset is an accession-directory direct asset;
- every package row uses dependency_depth=0 / referring_asset_sha256=null;
- P11-F cannot append external taxonomy/cache assets or rewrite source_package_sha256;
- external taxonomy/runtime-cache material is outside the filing package under the separately frozen parser contract;
- putting external dependencies into a future package requires a new versioned package identity design before package construction.

No production/test/runtime change was made.


## 17. Final detached review finding — P11-ISSUE-027

Fresh review of `dff1e390f0a8825c75abb15cfb10c41543c676d5` passed the ISSUE-010..026 automated matrix, but manual audit of accepted P1 planner/registry found generic reuse is document-SHA oriented and can select a stale SEC parse when source_package_sha256 changes without primary document bytes changing.

Stop:
`development/164-p11-package-aware-reuse-review-stop.md`

Accepted code facts:

- ParsedDataRecord has document_sha256/parse_run_id/artifact_path but no source_package_sha256 column;
- IncrementalPlanner lists parsed rows by slot and uses document_sha256 to filter current local raw;
- for multiple reusable runs sharing one document SHA it selects the first parse_run_id deterministically;
- SEC package identity can change through index/XBRL/schema/linkbase bytes while primary document SHA remains equal.

Resolution in current amendment:

- generic IncrementalPlanner remains CN/HK only for parsed-data reuse and explicitly blocks market=US with P11_PACKAGE_AWARE_PLANNER_REQUIRED;
- P11-K adds a package-aware SEC selector;
- selector loads the v2 artifact from safe project-relative artifact_path and verifies exact source_package_sha256, document_sha256, parse_run_id and confirmed slot before reuse;
- same document SHA + different package SHA => P11_SOURCE_PACKAGE_CHANGE / no reuse;
- no registry schema migration is required solely for package-aware reuse because package identity is revalidated from the immutable v2 artifact manifest;
- CN/HK planner behavior remains unchanged.

No production/test/runtime change was made during review/amendment.


## 18. Pre-freeze runtime-order finding — P11-ISSUE-028

While ISSUE-027 was being amended and before a new candidate was frozen, review found that requiring a newly confirmed slot before package-aware reuse would force P11-F parsing first, defeating incremental reuse.

Resolution:

- package-aware reuse runs after exact P11-E package assembly and before P11-F parsing;
- input slot is the requested target periodic FilingSlotKey, not a newly source-confirmed identity;
- an exact current package may reuse a previously PASS/compatible v2 artifact whose confirmed identity equals that requested target slot;
- exact reuse skips P11-F/G/H/I;
- no exact reusable package proceeds through parser → final identity → v2 → validation → persistence.

No production/test/runtime change was made.


## 19. Public API review finding — P11-ISSUE-029

Fresh review of `dc1c59e1ec19e8cf3e75624643d045a9f954fd16` passed the ISSUE-010..028 automated matrix, but manual review of the accepted planner API found the US fail-closed surface and the SEC reuse selector return contract were not exact enough for implementation.

Stop:
`development/167-p11-reuse-api-review-stop.md`

Resolution in the current amendment:

- generic IncrementalPlanner US guard uses exact public `PackageAwarePlannerRequired(RuntimeError)` with fixed reason_code and message, raised before slot construction or registry access;
- package-aware reuse public module is fixed to `financial_filing_data_foundation.sec.reuse`;
- exact `SecReuseAction`, `SecReuseReason`, frozen/slots `SecReuseDecision` field order and invariants are frozen;
- exact `select_sec_reuse(...)` signature and input validation are frozen;
- no-candidate behavior, failure reason priority, exact-package success behavior and read-only semantics are frozen.

No production/test/runtime change was made.


## 18. Reuse metadata parity finding — P11-ISSUE-030

Fresh detached review of `d47a0b5de5c2b3e88a5df629476d05d26e7d83fb` passed the ISSUE-010..029 automated contract matrix but manual comparison against accepted P1 `ParsedDataRecord` found registry/artifact metadata parity was not frozen.

Stop:
`development/170-p11-registry-artifact-parity-review-stop.md`

Resolution in the current amendment:

- loaded manifest parser_version must equal ParsedDataRecord.parser_version;
- loaded manifest schema_version must equal ParsedDataRecord.schema_version;
- manifest validation_status, validation.json status and ParsedDataRecord.validation_status must agree;
- manifest blocking_issue_count, len(validation.blocking_issues) and ParsedDataRecord.blocking_issue_count must agree;
- validation compatibility_status must equal ParsedDataRecord.compatibility_status;
- any mismatch is P11_REUSE_ARTIFACT_INVALID before reuse-policy classification.

No production/test/runtime change was made.


## 19. Parsed artifact path finding — P11-ISSUE-031

Fresh detached review of `85df002516d577531e68c303ad86c0903ca813c6` passed the ISSUE-010..030 matrix but manual review of accepted P1 `ParsedDataRecord.artifact_path` found the target type/layout was not frozen.

Stop:
`development/174-p11-artifact-path-contract-review-stop.md`

Resolution in current amendment:

- P11 periodic artifact_path always points to the v2 export directory, never manifest.json/child/staging;
- exact layout = <parsed_root>/<parse_run_id>/export-v2;
- parse_run_id must be lowercase 64-hex before path construction;
- registry stores normalized project-root-relative POSIX directory path, no trailing slash;
- directory is atomically committed before register_parsed_data;
- missing vs path-invalid vs existing-invalid reason mapping is frozen.

No production/test/runtime change was made.
