# 26 — P11 US SEC Provider Detailed Design

Status: **P11 DESIGN BASELINE CANDIDATE / PRODUCTION CLOSED**

Phase:
P11 — US SEC Provider

Predecessor:
P10 DONE / PASS.

Authorization:
`development/143-p11-design-authorization.md`

Environment/interface audit:
`development/144-p11-environment-interface-audit.md`

Source-neutral parsed contract:
`design/30-parsed-financial-document-v2-contract.md`

## 1. Goal

Build an evidence-grounded U.S. SEC/EDGAR ingestion and extraction path for operating-company filings, using exact filing source bytes and filing-native HTML / Inline XBRL / XBRL semantics.

P11 v1 must support:

Periodic filing families:
- 10-K / 10-K/A;
- 10-Q / 10-Q/A;
- 20-F / 20-F/A;
- 40-F / 40-F/A.

Supplemental filing families:
- 8-K / 8-K/A;
- 6-K / 6-K/A.

P11 v1 must NOT convert SEC HTML to PDF in order to reuse PDF-only schemas.

## 2. Non-goals

P11 v1 does not:

- change accepted P8 MCP tool/schema contract;
- change P9 review contract;
- change P10 capability fingerprint or dynamic-research contract;
- implement Research MCP production;
- implement Semantic Resolver production;
- canonicalize all US-GAAP concepts into one metric ontology;
- infer missing values;
- treat SEC companyfacts as filing-primary evidence;
- crawl arbitrary websites;
- submit filings to EDGAR;
- use filer API tokens.

## 3. Official source boundary

Primary official sources:

1. SEC Submissions API
   `https://data.sec.gov/submissions/CIK##########.json`

2. SEC EDGAR Archives filing directory
   `https://www.sec.gov/Archives/edgar/data/<CIK-no-leading-zero>/<accession-no-dashes>/`

3. Filing primary document from submission metadata / filing directory.

4. Filing-local XBRL/iXBRL dependencies and required taxonomy/linkbase assets.

5. SEC XBRL APIs only for auxiliary cross-checks:
   - companyfacts;
   - companyconcept;
   - frames.

SEC companyfacts is not filing truth because it aggregates standard taxonomy facts and does not preserve every custom filing concept.

## 4. Canonical company identity

For market `US`:

- canonical provider company identity = 10-digit zero-padded CIK;
- `CompanyRef.company_id` = normalized 10-digit CIK;
- `CompanyRef.ticker` becomes market-conditionally optional: CN/HK remain non-empty exactly as accepted P1 behavior, while US may use null;
- ticker is a lookup/display attribute and can change;
- ticker association is not sufficient for identity;
- CIK-only US operation is valid and MUST NOT fabricate a ticker;
- CIK never comes from filename inference.

Ticker resolution:

1. ticker lookup key = surrounding ASCII whitespace trim + ASCII uppercase; empty after trim is absent;
2. exact caller-supplied CIK wins after validation and does not require a ticker;
3. if no CIK is supplied, resolve the normalized ticker using the SEC-hosted ticker mapping;
4. zero official ticker matches => `P11_COMPANY_IDENTITY_NOT_FOUND`;
5. more than one distinct CIK match => `P11_COMPANY_IDENTITY_AMBIGUOUS`;
6. verify a caller/resolved ticker against Submissions API ticker metadata when available;
7. ticker/CIK mismatch => `P11_COMPANY_IDENTITY_AMBIGUOUS`.

Persisted/display ticker for v2:

- if caller supplied a ticker and it validates for the CIK, persist the normalized ASCII-uppercase ticker;
- if caller supplied no ticker and Submissions exposes exactly one distinct non-empty ticker after normalization, persist that ticker;
- if Submissions exposes zero or multiple distinct tickers for a valid caller CIK, persist `ticker=null` rather than choosing one arbitrarily;
- ticker null never blocks CIK-based filing discovery.

## 5. Identity model amendments

P11 requires additive identity support:

```text
market: CN | HK | US
raw_fiscal_period: Q1 | Q2 | Q3 | H1 | FY
```

Rules:

- CN/HK semantics remain unchanged;
- Q2 is valid iff market=US in P11 v1;
- CN Q2 and HK Q2 are rejected;
- US 10-Q uses Q1/Q2/Q3;
- US Q2 MUST NOT be mapped to H1;
- 10-K/20-F/40-F => FY;
- 8-K/6-K are supplemental and are not forced into periodic slots.

Periodic slot key remains:

`market + company_id + filing_type + fiscal_year + raw_fiscal_period`

For amended periodic forms, `filing_type` stores normalized base form and `amended=true`.

## 6. SEC filing identity

Canonical SEC submission identity:

`accession_number`

Canonical form normalization examples:

- 10-K/A -> base_form=10-K, amended=true;
- 10-Q/A -> base_form=10-Q, amended=true;
- 20-F/A -> base_form=20-F, amended=true;
- 40-F/A -> base_form=40-F, amended=true;
- 8-K/A -> base_form=8-K, amended=true;
- 6-K/A -> base_form=6-K, amended=true.

`source_id` for SEC SourceMetadata = exact accession number with dashes.

`provider` = `sec-edgar`.

`provider_company_id` = 10-digit CIK.

Exact input grammar:

### CIK

- caller/provider CIK is a string after surrounding ASCII whitespace trim;
- accepted lexical grammar = `^[0-9]{1,10}$`;
- numeric value must be > 0;
- normalized CIK = left-zero-padded to exactly 10 ASCII digits;
- signs, decimal points, separators, Unicode digits and embedded whitespace are rejected.

### accession_number

- exact accepted grammar = `^[0-9]{10}-[0-9]{2}-[0-9]{6}$`;
- normalized accession preserves this dashed form;
- archive directory form = remove the two dashes, yielding exactly 18 ASCII digits;
- no caller-supplied alternative separator or path form is accepted.

### primaryDocument

The value comes only from validated SEC submission/index metadata.

It MUST:

- be a non-empty basename, not a caller path;
- contain no `/`, `\\`, NUL or ASCII control characters;
- not equal `.` or `..`;
- not contain a query or fragment;
- be joined to the frozen Archives directory as a single URL path segment after validation.

Any violation is `P11_SUBMISSIONS_INVALID` or `P11_PATH_OUTSIDE_PROJECT` according to whether the defect is provider metadata or a local path computation.

## 7. Period binding

Discovery metadata is provisional.

Final periodic binding is confirmed after source acquisition.

Preferred evidence order:

1. Inline/XBRL DEI `DocumentFiscalYearFocus`;
2. Inline/XBRL DEI `DocumentFiscalPeriodFocus`;
3. Inline/XBRL DEI `DocumentPeriodEndDate`;
4. normalized Submissions `reportDate`;
5. filing form consistency;
6. filer fiscal year end only as a consistency check.

Discovery report-date normalization:

- empty SEC Submissions `reportDate` => null;
- exact `YYYY-MM-DD` calendar-valid value => normalized discovery report date;
- non-empty malformed/invalid date => `P11_SUBMISSIONS_INVALID`;
- this discovery value is frozen in the source-package identity before parsing and is never rewritten from DEI.

Final periodic `document.json.report_date`:

- if discovery report date and DEI `DocumentPeriodEndDate` are both valid, they MUST match;
- if only one is valid/present, use that exact value;
- if neither is available, return `P11_PERIOD_UNRESOLVED`;
- disagreement => `P11_PERIOD_CONFLICT`;
- final v2 report-date confirmation never rewrites `source_package_sha256`.

Rules:

- 10-K must resolve to FY;
- 10-Q must resolve to Q1/Q2/Q3;
- 20-F/40-F must resolve to FY;
- conflicting DEI vs requested slot => REVIEW_REQUIRED/BLOCKED with `P11_PERIOD_CONFLICT` where applicable;
- no guessing based only on calendar month.

## 8. Supplemental filing identity

8-K/6-K ingestion uses an accession-bound supplemental identity:

```text
market
+ CIK
+ accession_number
+ base_form
+ filing_date
```

Supplemental filings do not enter `build_required_slots()` periodic planning in P11 v1.

They may be captured/exported for later research consumption.

## 9. Acquisition architecture

P11 adds a dedicated SEC adapter path.

```text
FFDF main runtime
  |
  | deterministic JSON request
  v
P11 SEC runtime
  |
  +-- SEC identity/discovery
  +-- rate-limited official HTTP
  +-- package acquisition
  +-- HTML/XML/XBRL parsing
  +-- deterministic response/artifacts
```

Recommended runtime:

- project-local;
- Python 3.12 AMD64;
- pinned lock;
- Arelle candidate: arelle-release 2.47.4;
- lxml supplied through locked dependency set;
- no remote AI APIs.

The exact runtime is frozen only after P11-B environment probe.

## 10. SEC HTTP policy

Every request MUST:

- use HTTPS;
- use explicit configured User-Agent;
- never use a fabricated/default contact identity;
- obey SEC's aggregate fair-access ceiling, not merely a per-process ceiling;
- all FFDF P11 processes under the same canonical project root share one cross-process SEC rate gate;
- the frozen standalone implementation ceiling is 8 requests/sec aggregate with no burst: minimum 125 ms between starts of outbound SEC requests;
- the gate state/lock lives under the canonical project-root `workspace/sec/rate/` and is shared by main/worktree executions that use that root;
- if aggregate coordination cannot be obtained safely, the request is blocked with `P11_RATE_LIMIT_SCOPE_UNSAFE`;
- independent installations/machines are not auto-coordinated; concurrent use of the same automation identity across installations is unsupported unless an explicitly designed shared limiter is supplied, and MUST NOT be assumed safe;
- revalidate redirect destination;
- use allowlisted hosts only;
- enforce response-size cap;
- enforce timeout;
- record status/content-type/final URL;
- preserve exact bytes before parse.

Missing required User-Agent configuration => BLOCKED.

Retry policy:

- 429: respect Retry-After when present, bounded retry;
- 5xx: bounded exponential retry;
- 404: no blind retry loop;
- 403/access denied: block and surface reason;
- retries also pass through the same aggregate rate gate;
- exact timeout, response-size caps, retry count/backoff and User-Agent grammar MUST be frozen by a Design-First P11-D HTTP-contract amendment before any P11-D production code is authorized; P11-D code may not choose these values ad hoc.

## 11. Host allowlist

Initial allowed hosts:

- data.sec.gov
- www.sec.gov
- sec.gov

Taxonomy dependency hosts are NOT implicitly allowed.

If Arelle/source dependency resolution requires a non-SEC taxonomy host such as FASB, that host must be explicitly frozen in a later design amendment or runtime descriptor before production.

No arbitrary URL fetch.

## 12. Discovery

Input:

- CIK;
- target form family;
- filing window;
- optional target accession.

Source:
Submissions API.

Discovery candidate fields:

- CIK;
- accession_number;
- form;
- base_form;
- amended;
- filing_date;
- report_date;
- primary_document;
- primary_doc_description if available;
- is_xbrl;
- is_inline_xbrl;
- provisional fiscal year/period;
- source URLs.

Historical submission shards referenced by Submissions `files` must be supported when the requested filing falls outside the current array.

## 13. Archive URL construction

For accession:

- CIK path component = integer CIK, no leading zero;
- accession directory = accession number without dashes;
- primary document path = metadata primaryDocument.

URL:

```text
https://www.sec.gov/Archives/edgar/data/<cik-int>/<accession-no-dashes>/<primaryDocument>
```

All components are validated, never string-concatenated from arbitrary caller path input.

## 14. Source package

P11 stores a filing as an immutable source package.

Required source-package assembly for P11 v1 is deterministic.

### Required accession index

Always capture the exact accession-directory machine-readable index:

`https://www.sec.gov/Archives/edgar/data/<cik-int>/<accession-no-dashes>/index.json`

Role:
`FILING_INDEX`

Its exact bytes are a package asset and its entries are the only automatic filing-directory inventory for P11 v1.

### Required primary document

Capture `primaryDocument` from validated Submissions metadata.

Requirements:

- safe basename under Section 6;
- must appear as an item in accession `index.json`;
- exact bytes are `PRIMARY_DOCUMENT`;
- absence/mismatch => `P11_PACKAGE_ASSET_MISSING`.

### Automatic structured-data assets

From accession `index.json`, automatically capture every regular-file item whose safe lowercase basename ends in:

- `.xsd`;
- `.xml`.

Role classification is deterministic by lowercase suffix:

- `*.xsd` => `TAXONOMY_SCHEMA`;
- `*_cal.xml` => `CALCULATION_LINKBASE`;
- `*_def.xml` => `DEFINITION_LINKBASE`;
- `*_lab.xml` => `LABEL_LINKBASE`;
- `*_pre.xml` => `PRESENTATION_LINKBASE`;
- `*_htm.xml` => `XBRL_INSTANCE`;
- any other `*.xml` => `OTHER_REQUIRED_DEPENDENCY`.

If one filename matches multiple suffix rules, the most-specific rule above wins in the listed order before generic `.xml`.

### Logical asset identity / blob dedup

The immutable package manifest represents logical accession-directory assets.

Logical asset key:

`(file_name, canonical requested source_url)`

Rules:

- `file_name` is the exact case-sensitive provider/index basename spelling; lowercase is used only transiently for suffix classification and never replaces the identity spelling;
- every index-derived filename must satisfy the same safe-basename/path rules as Section 6 before it can enter package assembly;
- the logical asset key MUST be unique inside one package;
- two different logical assets MAY have identical bytes and therefore the same `asset_sha256`;
- such rows MUST both remain in the package manifest/source-assets output;
- raw blob storage may physically reuse one content-addressed blob for those rows;
- exact duplicate logical keys are invalid, regardless of whether their metadata/bytes agree;
- `asset_sha256 = SHA256(exact captured asset bytes)`;
- `byte_size = len(exact captured asset bytes)`, never the provider-declared size substituted for actual bytes;
- if index.json provides a numeric declared size and it disagrees with captured byte_size, package construction blocks as `P11_PACKAGE_INVALID`;
- `primary=true` iff the final role is `PRIMARY_DOCUMENT`; all other roles use `primary=false`;
- package `asset_count` counts logical rows, not unique SHA blobs.

Every P11 v1 source-package row is selected directly from the accession directory in P11-E and therefore uses:

- `dependency_depth = 0`;
- `referring_asset_sha256 = null`.

P11-F MUST NOT append external taxonomy/runtime-cache assets to an already committed source package and MUST NOT mutate `source_package_sha256`.

External taxonomy dependencies in P11 v1 belong to the separately frozen parser runtime/cache contract. If a future design wants those external assets inside the immutable filing package, it requires a new versioned package-identity design amendment before package construction; it cannot reuse this v1 identity contract silently.

### Role precedence

One logical asset has exactly one manifest role.

Precedence:

1. accession `index.json` => `FILING_INDEX`;
2. exact filename equals validated `primaryDocument` => `PRIMARY_DOCUMENT`;
3. otherwise structured suffix classification above;
4. otherwise explicit requested exhibit => `REQUESTED_EXHIBIT`;
5. otherwise exclude from P11 v1 package.

If an explicitly requested exhibit is already included by rules 1-3, the request is satisfied by the existing logical row. No duplicate row is added and the higher-precedence role is retained.

### Optional exhibits

P11 v1 never auto-downloads unrelated HTML/text exhibits.

An optional exhibit may be captured only when the caller supplies its exact safe basename and that basename appears in the same accession `index.json`.

Role:
`REQUESTED_EXHIBIT`

No type/description guessing and no recursive arbitrary link following are allowed.

### External taxonomy dependencies

Standard/external taxonomy assets not present in the accession directory are NOT silently added by P11-E.

Their exact runtime/cache resolution behavior must be frozen by the mandatory P11-F parser-contract amendment before parser implementation.

Do not download every exhibit by default.

Package `manifest.json` is the immutable identity manifest, not an HTTP receipt.

It contains:

- schema_version;
- CIK;
- accession_number;
- base_form;
- amended;
- filing_date;
- report_date;
- primary_document;
- assets using the exact Section 15 identity rows/sort;
- package hash.

Acquisition-specific diagnostics are stored only in separate receipt records:

- final redirect URL;
- HTTP status;
- declared Content-Type;
- ETag / Last-Modified;
- request/retry timing;
- acquired_at.

A receipt never changes package identity or immutable package-manifest bytes.

## 15. Package identity

Primary `document_sha256`:
SHA256(exact primary document bytes).

Before constructing the package identity object, top-level fields are frozen as follows:

- `schema_version = "p11-sec-source-package-identity-v1"`;
- `cik` = normalized 10-digit target filer CIK from Section 6;
- `accession_number` = normalized dashed accession from Section 6;
- `base_form` = normalized base form from Section 6;
- `amended` = exact normalized amendment boolean;
- `filing_date` = non-empty calendar-valid Submissions `filingDate` in exact `YYYY-MM-DD`; missing/malformed => `P11_SUBMISSIONS_INVALID`;
- `report_date` = immutable normalized Submissions discovery reportDate from Section 7, valid date or null;
- `primary_document` = exact validated provider basename spelling;
- `assets` = complete logical asset rows after Section 14 selection, role precedence and canonical sort.

No parser output may alter these top-level package-identity values after package commit.

`source_package_sha256` is SHA256 of the exact canonical JSON bytes of this identity object:

```json
{
  "schema_version": "p11-sec-source-package-identity-v1",
  "cik": "##########",
  "accession_number": "##########-##-######",
  "base_form": "10-K",
  "amended": false,
  "filing_date": "YYYY-MM-DD",
  "report_date": null,
  "primary_document": "basename.ext",
  "assets": [
    {
      "role": "PRIMARY_DOCUMENT",
      "asset_sha256": "<lowercase sha256>",
      "file_name": "basename.ext",
      "source_url": "https://www.sec.gov/Archives/...",
      "byte_size": 0,
      "primary": true,
      "dependency_depth": 0,
      "referring_asset_sha256": null
    }
  ]
}
```

Asset identity rows are sorted lexicographically by:
`(role, file_name, source_url, asset_sha256, byte_size, primary, dependency_depth, referring_asset_sha256-or-empty)`.

`source_url` in the identity row is the canonical requested URL before redirects: absolute HTTPS, lowercase host, no fragment, no dot-segment traversal, and otherwise the validated resolved path/query. Redirect final URL belongs only to the acquisition receipt.

Canonical JSON uses the Section 28 canonical encoder exactly.

Excluded from package identity:

- redirect final URL;
- declared HTTP media/content type;
- ETag / Last-Modified;
- downloaded/acquired timestamps;
- request IDs;
- local paths;
- retry/HTTP diagnostics.

Those excluded fields remain provenance/diagnostic metadata but cannot change the package hash by themselves.

`source_package_sha256` itself is not included in its own identity payload.

The package-identity `report_date` field is the normalized **Submissions discovery reportDate** from Section 7, not the later DEI-confirmed/final v2 report date.

Therefore:

- valid discovery reportDate => exact `YYYY-MM-DD`;
- empty discovery reportDate => JSON null;
- malformed non-empty discovery reportDate blocks package construction as `P11_SUBMISSIONS_INVALID`;
- later DEI confirmation/conflict never mutates an already computed package identity/hash.

Known canonical fixture:

```json
{"accession_number":"0000320193-24-000123","amended":false,"assets":[{"asset_sha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","byte_size":123,"dependency_depth":0,"file_name":"example.htm","primary":true,"referring_asset_sha256":null,"role":"PRIMARY_DOCUMENT","source_url":"https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/example.htm"}],"base_form":"10-K","cik":"0000320193","filing_date":"2024-10-31","primary_document":"example.htm","report_date":"2024-09-28","schema_version":"p11-sec-source-package-identity-v1"}
```

Exact UTF-8 canonical bytes SHA256:

`16e76f846fcdccf44216816148ba346ae5c100f3fcdf6fa170a6f954267bae78`

Implementation tests must independently reproduce this hash.

Downloaded timestamps, local absolute paths and transient HTTP headers do not participate in package identity.

If the same accession later produces different exact bytes:

- do not overwrite old source bytes;
- capture a new package version;
- mark source-content drift;
- require re-validation;
- preserve prior provenance.

## 16. Raw storage

Do not modify P2 PDF RawDocumentStore semantics in-place.

P11 adds a dedicated source-package store, for example:

```text
workspace/sec/raw/
  assets/sha256/<aa>/<sha>.<safe-ext>
  packages/<package-sha>/manifest.json
  receipts/<receipt-id>.json
  staging/
```

Properties:

- content-addressed;
- atomic commit;
- exact-byte SHA validation;
- path traversal rejection;
- no executable interpretation;
- asset count/package size caps;
- duplicate SHA reuse allowed;
- semantic receipt collision rejected.

## 17. Registration

Primary document exact bytes are registered in SQLiteRegistry.

For non-PDF primary assets:

- page_count remains null;
- source metadata records accession/URL/CIK;
- expected identity is attached only after periodic binding is confirmed.

P11 v1 supplemental accession-bound filings MUST NOT be persisted into the existing periodic SQLiteRegistry / ParsedDataRecord path.

Reason:

- current registry parsed-data identity is periodic-slot oriented;
- current SourceMetadata/report-date contract is not a source-neutral supplemental identity contract;
- forcing supplemental filings into it would require placeholder/guessed period metadata.

For P11 v1, supplemental authority is limited to:

- immutable SEC source package;
- ParsedFinancialDocument v2;
- supplemental export identity keyed by CIK + accession + base form + filing date.

A future generic supplemental registry is a separate additive contract and requires separate design/review/acceptance.

### 17.1 Periodic SEC parsed-data reuse

Accepted generic `IncrementalPlanner` reuse is document-SHA oriented. That is insufficient for SEC because filing-package identity may change while the primary document bytes remain identical.

P11 v1 therefore freezes this boundary:

- `IncrementalPlanner.build_plan` remains the accepted CN/HK planner;
- P11 orchestration uses the shared identity/slot primitives but a dedicated package-aware SEC reuse selector;
- no US path may silently fall back to generic document-SHA-only reuse.

### Generic planner fail-fast API

P11-C adds this exact public exception in:
`financial_filing_data_foundation.planner.errors`

and re-exports it from:
`financial_filing_data_foundation.planner`.

```python
class PackageAwarePlannerRequired(RuntimeError):
    reason_code = "P11_PACKAGE_AWARE_PLANNER_REQUIRED"
```

After `CompanyRef` supports US, `IncrementalPlanner.build_plan(...)` MUST perform this guard before any slot construction or registry access:

```python
if company.market == "US":
    raise PackageAwarePlannerRequired(
        "market US requires P11 package-aware SEC planning"
    )
```

Exact contract:

- exception type = `PackageAwarePlannerRequired`;
- base class = `RuntimeError`;
- class attribute `reason_code` exactly `P11_PACKAGE_AWARE_PLANNER_REQUIRED`;
- exact `str(exc)` = `market US requires P11 package-aware SEC planning`;
- guard occurs before `build_required_slots`;
- guard occurs before any SQLiteRegistry method call;
- no `FilingPlan` or synthetic `PlannerItem` is returned for US;
- CN/HK behavior, result shape and existing `ReasonCode` enum remain unchanged.

### SEC reuse public result API

P11-K adds:
`financial_filing_data_foundation.sec.reuse`

with exact public types:

```python
class SecReuseAction(StrEnum):
    REUSE_DATA = "REUSE_DATA"
    PARSE_CURRENT_PACKAGE = "PARSE_CURRENT_PACKAGE"

class SecReuseReason(StrEnum):
    EXACT_PACKAGE_REUSE = "P11_EXACT_PACKAGE_REUSE"
    NO_REUSABLE_EXACT_PACKAGE = "P11_NO_REUSABLE_EXACT_PACKAGE"
    SOURCE_DOCUMENT_CHANGE = "P11_SOURCE_DOCUMENT_CHANGE"
    SOURCE_PACKAGE_CHANGE = "P11_SOURCE_PACKAGE_CHANGE"
    REUSE_ARTIFACT_MISSING = "P11_REUSE_ARTIFACT_MISSING"
    REUSE_ARTIFACT_PATH_INVALID = "P11_REUSE_ARTIFACT_PATH_INVALID"
    REUSE_ARTIFACT_INVALID = "P11_REUSE_ARTIFACT_INVALID"
    REUSE_VALIDATION_NOT_PASS = "P11_REUSE_VALIDATION_NOT_PASS"
    REUSE_BLOCKING_ISSUES = "P11_REUSE_BLOCKING_ISSUES"
    REUSE_SCHEMA_INCOMPATIBLE = "P11_REUSE_SCHEMA_INCOMPATIBLE"
    REUSE_COMPATIBILITY_UNKNOWN = "P11_REUSE_COMPATIBILITY_UNKNOWN"
    REUSE_PARSER_INVALIDATED = "P11_REUSE_PARSER_INVALIDATED"
```

`SecReuseDecision` is a frozen/slots dataclass with exact fields in this order:

```text
action: SecReuseAction
reason_code: SecReuseReason
rejection_reasons: tuple[SecReuseReason, ...]
slot_key: str
document_sha256: str
source_package_sha256: str
parse_run_id: str | None
artifact_path: str | None
```

The selector public function is exactly:

```python
def select_sec_reuse(
    registry: SQLiteRegistry,
    slot: FilingSlotKey,
    document_sha256: str,
    source_package_sha256: str,
    reuse_policy: PlannerReusePolicy,
    project_root: Path,
    parsed_root: Path,
) -> SecReuseDecision:
    ...
```

Parameter contract:

- `registry` is read-only during selection;
- `slot.market` MUST equal `US`; otherwise raise `ValueError("select_sec_reuse requires market US")`;
- `document_sha256` must match `^[0-9a-f]{64}$` or raise `ValueError("document_sha256 must be 64 lowercase hex")`;
- `source_package_sha256` must match `^[0-9a-f]{64}$` or raise `ValueError("source_package_sha256 must be 64 lowercase hex")`;
- `project_root` is resolved canonical project root;
- `parsed_root` must resolve inside `project_root`; otherwise raise `ValueError("parsed_root must be inside project_root")`;
- registry `artifact_path` values are interpreted relative to `project_root`, then must resolve inside `parsed_root`;
- the function performs no network access;
- the function performs no writes.

Invariants:

- `slot_key` equals the requested target `FilingSlotKey.serialize()`;
- `document_sha256` and `source_package_sha256` echo the current package inputs;
- `REUSE_DATA` requires:
  - reason_code = `EXACT_PACKAGE_REUSE`;
  - rejection_reasons = empty tuple;
  - parse_run_id non-null;
  - artifact_path non-null and normalized project-root-relative POSIX;
- `PARSE_CURRENT_PACKAGE` requires:
  - parse_run_id = null;
  - artifact_path = null;
  - reason_code != `EXACT_PACKAGE_REUSE`;
- selector returns `SecReuseDecision`, never an arbitrary `ParsedDataRecord`;
- selector is read-only: it never mutates registry, artifact files or package files.

If at least one exact-package candidate is reusable, rejected candidates do not leak into the successful decision; the selected decision has empty `rejection_reasons`.

If no candidate is reusable, `rejection_reasons` is the ordered unique set of observed reasons using this exact priority:

```text
P11_REUSE_ARTIFACT_PATH_INVALID
P11_REUSE_ARTIFACT_INVALID
P11_REUSE_ARTIFACT_MISSING
P11_SOURCE_PACKAGE_CHANGE
P11_SOURCE_DOCUMENT_CHANGE
P11_REUSE_VALIDATION_NOT_PASS
P11_REUSE_BLOCKING_ISSUES
P11_REUSE_SCHEMA_INCOMPATIBLE
P11_REUSE_COMPATIBILITY_UNKNOWN
P11_REUSE_PARSER_INVALIDATED
P11_NO_REUSABLE_EXACT_PACKAGE
```

The decision `reason_code` is the first item in that tuple.

If `list_parsed_data(slot)` returns zero rows, or rows exist but no more-specific rejection reason is observed, return:

```text
action = PARSE_CURRENT_PACKAGE
reason_code = P11_NO_REUSABLE_EXACT_PACKAGE
rejection_reasons = (P11_NO_REUSABLE_EXACT_PACKAGE,)
parse_run_id = null
artifact_path = null
```

Candidate classification:

- record.document_sha256 != current document SHA => `P11_SOURCE_DOCUMENT_CHANGE`; do not load that artifact;
- null artifact_path or safe expected export-v2 directory absent => `P11_REUSE_ARTIFACT_MISSING`;
- absolute/drive-relative/UNC/traversal/outside-root/wrong-layout/child-file artifact_path => `P11_REUSE_ARTIFACT_PATH_INVALID`;
- existing non-directory path, missing required v2 file, v2 load/hash/source-reference/parse-run/document/slot identity failure, or registry/artifact metadata parity mismatch => `P11_REUSE_ARTIFACT_INVALID`;
- exact document but loaded package != current package => `P11_SOURCE_PACKAGE_CHANGE`;
- validation != PASS => `P11_REUSE_VALIDATION_NOT_PASS`;
- blocking issue count > 0 => `P11_REUSE_BLOCKING_ISSUES`;
- schema not accepted / compatibility INCOMPATIBLE => `P11_REUSE_SCHEMA_INCOMPATIBLE`;
- compatibility UNKNOWN => `P11_REUSE_COMPATIBILITY_UNKNOWN`;
- parser version invalidated => `P11_REUSE_PARSER_INVALIDATED`.

Runtime position:

```text
requested periodic slot
→ SEC discovery
→ P11-E exact source-package assembly
→ package-aware reuse selector
    ├─ exact reusable package artifact found → REUSE_DATA / skip P11-F..I
    └─ no exact reusable artifact → P11-F parse → P11-G final identity → P11-H validation → P11-I final v2 export → P11-K persist
```

The selector runs after the current exact source package is known but before parsing. Otherwise reuse would not save parser work.

P11 package-aware reuse selector input:

- requested target periodic `FilingSlotKey` from the P11 slot/request planner; it is a declared target, not yet newly source-confirmed;
- current `document_sha256`;
- current `source_package_sha256`;
- accepted reuse policy / parser compatibility policy;
- configured project root and P11 parsed-artifact root.

Candidate discovery:

- call existing `SQLiteRegistry.list_parsed_data(slot)`;
- no registry schema migration is required solely for P11 v1 package-aware reuse;
- every P11 periodic reusable `ParsedDataRecord` MUST have non-null `artifact_path`.

### P11 periodic artifact_path contract

For P11 periodic v2 records, `artifact_path` always identifies the **ParsedFinancialDocument v2 export directory**, never `manifest.json` or another child file.

Exact persistence layout:

```text
<parsed_root>/<parse_run_id>/export-v2/
  manifest.json
  document.json
  source_assets.jsonl
  source_segments.jsonl
  sections.jsonl
  tables.jsonl
  raw_facts.jsonl
  evidence.jsonl
  validation.json
```

Rules:

- `parse_run_id` MUST match `^[0-9a-f]{64}$` before use as a path component;
- `parsed_root` resolves inside `project_root`;
- registry stores `artifact_path` as the normalized project-root-relative POSIX path to the exact `export-v2` directory;
- stored `artifact_path` has no trailing slash;
- registry never stores the path to `manifest.json`;
- registry never stores a staging/partial directory.

Reuse path classification:

- null `artifact_path` => `P11_REUSE_ARTIFACT_MISSING`;
- safe resolved `artifact_path` does not exist => `P11_REUSE_ARTIFACT_MISSING`;
- absolute/drive-relative/UNC/traversal/outside-`parsed_root` path => `P11_REUSE_ARTIFACT_PATH_INVALID`;
- path exists but is not a directory => `P11_REUSE_ARTIFACT_INVALID`;
- directory exists but any required v2 file above is missing => `P11_REUSE_ARTIFACT_INVALID`;
- otherwise the accepted v2 loader validates schema/hash/identity/source-reference integrity.

P11-I MUST atomically commit the complete export directory at this final path and reload it successfully before P11-K may call `register_parsed_data`.

### Final export idempotency / collision contract

The final path is deterministic:

`<parsed_root>/<parse_run_id>/export-v2`

and final artifact bytes are immutable once accepted.

P11-I MUST follow this exact commit contract:

#### Final path absent

If the final path does not exist:

1. build the complete export under a project-local staging directory;
2. run the complete v2 loader against staging;
3. atomically move/rename the staging directory to the final path;
4. reload the final path;
5. only after successful final reload may P11-K persist the registry row.

#### Final path already exists

If the final path already exists, P11-I MUST NOT overwrite, delete, replace or mutate it.

Instead:

1. verify the existing final path is a directory at the exact expected layout;
2. load/validate the existing final export;
3. require existing `manifest.parse_run_id == requested parse_run_id`;
4. require existing document/package/parser/schema/config/identity/validation semantics to equal the current deterministic output;
5. compare every required final artifact file as exact bytes against the newly generated staging export.

If every required file is present, both exports load successfully, and every required file byte is identical:

- discard/retire staging;
- classify the commit as idempotent success;
- reuse the existing immutable final directory;
- P11-K may proceed.

If any required file differs, is missing, fails loading, or carries a different identity:

`P11_FINAL_ARTIFACT_COLLISION`

and the run is BLOCKED.

No replacement of the existing final path is permitted.

#### Registry failure after final commit

If P11-I commits/reuses a valid final export and P11-K registry persistence fails:

- leave the final export unchanged;
- absence of a ParsedDataRecord means the orphan final export is not discoverable/reusable through the package-aware selector;
- a later retry may regenerate staging, perform the exact-existing-final byte/identity verification above, and retry registry persistence;
- do not create a second final path;
- do not delete the orphan final export merely because registry persistence failed.

#### Staging

Staging is never registry-eligible and never reusable.

A stale staging directory may be removed only by an explicitly scoped cleanup path that proves:

- the path is below the configured P11 staging root;
- it is not the deterministic final export path;
- no registry row points to it.

Normal runtime logic never treats staging presence as success.

For each candidate record, the selector MUST load the v2 artifact through the accepted v2 loader and verify all of:

1. loader/schema/hash/ID/source-reference integrity passes;
2. loaded manifest `schema_version == parsed-financial-document-v2`;
3. loaded manifest `parse_run_id == ParsedDataRecord.parse_run_id`;
4. loaded manifest/document `document_sha256 == current document_sha256 == ParsedDataRecord.document_sha256`;
5. loaded manifest `source_package_sha256 == current source_package_sha256`;
6. loaded document periodic identity equals the requested target slot; because the artifact is for the exact current package and previously passed validation, its confirmed identity may safely satisfy the current request without re-parsing;
7. exact registry/artifact metadata parity:
   - loaded manifest `parser_version == ParsedDataRecord.parser_version`;
   - loaded manifest `schema_version == ParsedDataRecord.schema_version`;
   - loaded manifest `validation_status == validation.json.status == ParsedDataRecord.validation_status.value`;
   - loaded manifest `blocking_issue_count == len(validation.json.blocking_issues) == ParsedDataRecord.blocking_issue_count`;
   - loaded validation `compatibility_status == ParsedDataRecord.compatibility_status.value`;
8. parser/schema versions satisfy the accepted reuse policy only after parity passes;
9. loaded/registry validation status = PASS;
10. loaded/registry blocking issue count = 0;
11. loaded/registry compatibility status = COMPATIBLE.

A candidate failing any condition is not reusable.

Specific rules:

- same primary `document_sha256` but different `source_package_sha256` => no reuse and explicit `P11_SOURCE_PACKAGE_CHANGE`;
- null artifact_path or safe resolved artifact directory absent => `P11_REUSE_ARTIFACT_MISSING`;
- absolute/drive-relative/UNC/traversal/outside configured parsed root => `P11_REUSE_ARTIFACT_PATH_INVALID`;
- existing artifact_path that is not a directory, missing required v2 files, or loader/hash/identity mismatch => `P11_REUSE_ARTIFACT_INVALID`;
- any parser_version/schema_version/validation_status/blocking_issue_count/compatibility_status mismatch between the loaded v2 artifact and ParsedDataRecord => `P11_REUSE_ARTIFACT_INVALID` before policy/validation classification;
- exact-package candidates whose registry/artifact parity passes but whose verified values fail validation/compatibility reuse the existing validation/reuse rejection semantics;
- if more than one candidate is fully reusable for the exact same package/document/slot, select the lexicographically smallest `parse_run_id` after all exact-package checks;
- no candidate may be chosen merely because its `document_sha256` matches.

Registry persistence in P11-K may continue using existing `ParsedDataRecord` because `parse_run_id` and `artifact_path` bind to the package-aware v2 artifact; package equivalence is re-verified from that artifact before reuse.

Existing CN/HK planner/reuse semantics remain unchanged.

## 18. Parser architecture

Never route SEC HTML through PyMuPDF.

P11 parser has three cooperating layers:

### 18.1 Source text layer

Parse HTML/Inline XBRL as source text/DOM.

Output:

- source segments;
- sections;
- HTML tables;
- DOM locators.

### 18.2 XBRL fact layer

Parse iXBRL/XBRL facts.

Preserve:

- concept QName/namespace;
- contextRef;
- unitRef;
- dimensions;
- decimals/precision;
- scale/sign/format;
- nil;
- exact lexical text;
- transformed numeric value when deterministically available;
- period/entity context.

### 18.3 Validation layer

Use deterministic source/package checks and, when runtime is frozen, local Arelle validation.

No network is allowed during the deterministic parse phase unless a future explicit design amendment says otherwise.

## 19. Dependency capture

Any parser dependency needed after acquisition must be captured into the source package or deterministic local runtime/cache before parse.

If a required remote taxonomy/schema cannot be safely captured under the frozen allowlist:

- parsing may still preserve raw source text;
- structured semantic validation becomes REVIEW_REQUIRED/BLOCKED according to exact failure;
- do not silently fetch arbitrary dependencies.

## 20. ParsedFinancialDocument v2

P11 writes `parsed-financial-document-v2` as frozen in design/30.

Key principle:

- source-native locators;
- no fake PDF page/bbox;
- exact source asset SHA in evidence;
- raw filing concept names preserved.

## 21. HTML tables

HTML table reconstruction is DOM-based, not geometric.

Table/cell identity uses:

- document SHA;
- asset SHA;
- DOM path / HTML id;
- row/column indices;
- parser version.

rowspan/colspan are resolved structurally.

CSS rendering is not required for v1 table truth.

If visual layout is necessary to interpret a table:

`P11_VISUAL_RENDERING_REQUIRED`

and remain unresolved.

## 22. XBRL raw fact extraction

Primary source truth is the filing iXBRL/XBRL.

For each fact:

- preserve raw source node;
- preserve exact concept QName;
- preserve context/unit/dimensions;
- preserve lexical text;
- compute parsed numeric only with explicit transform rules;
- link to exact source asset/DOM/XML node.

Normative `raw_value` rule for Inline XBRL/XBRL v2:

- resolve the fact element plus its valid `continuedAt` chain in source order;
- ignore descendants covered by `ix:exclude`;
- concatenate descendant character data in document order after standards-required entity decoding;
- normalize each Unicode whitespace run to one U+0020 SPACE and trim leading/trailing U+0020;
- do NOT apply Inline XBRL `format`, `scale`, `sign`, unit conversion or canonical metric semantics to `raw_value`;
- `nil=true` preserves the lexical text (normally empty) and forces `parsed_numeric_value=null`;
- source asset SHA + canonical source locators remain the proof of the original lexical source.

Numeric transformation boundary:

- `parsed_numeric_value` may apply only standards-defined iXBRL/XBRL lexical transformation, format, sign and base-10 scale;
- transformed output is a canonical decimal string or null;
- no currency/unit conversion, period inference, concept canonicalization or rounding beyond the filing's transform semantics;
- unsupported/invalid transform => parsed value null + explicit validation issue, never guess.

Because the exact standards transformation implementation may depend on the runtime/parser selected by P11-B, **P11-F parser production is CLOSED until a Design-First parser-contract freeze records the exact runtime version, transformation registry behavior, continuation/exclude handling golden fixtures and canonical decimal cases.** P11-F implementation may not choose these semantics ad hoc.

Companyfacts may confirm a standard fact but cannot replace filing evidence.

## 23. Custom taxonomy

Custom concepts are preserved as raw concepts.

Do not drop facts merely because taxonomy is custom.

If concept labels/definitions cannot be resolved:

- raw QName remains valid source truth;
- semantic label remains unresolved;
- validation may warn/review;
- no canonical guess.

## 24. Amendment policy

Original and amended filings are separate accession packages.

No automatic rule states that an amendment fully supersedes all facts in the original filing.

Periodic planner/reuse must not silently select an amendment as a complete replacement.

If caller requests a slot with multiple relevant variants and no explicit variant policy:

`P11_FILING_VARIANT_REVIEW_REQUIRED`

## 25. Post-acceptance corrections/deletions

SEC historical index/file state can change after acceptance.

P11 therefore uses both:

- stable provider identity: accession;
- immutable content identity: SHA/package hash.

Refresh policy checks current metadata/content identity without deleting prior accepted source packages.

A changed/missing source after prior acquisition becomes explicit source drift, not silent overwrite.

## 26. Source metadata

SEC SourceMetadata:

- provider = sec-edgar;
- source_id = accession number;
- source_url = primary document URL;
- source_title = form + filer/source description;
- filing_date = official filing date;
- report_date = report date;
- provider_company_id = 10-digit CIK;
- acquired_at = diagnostic exact ISO timestamp.

## 27. Error / reason codes

Minimum P11 codes:

Identity/discovery:
- P11_COMPANY_IDENTITY_NOT_FOUND
- P11_COMPANY_IDENTITY_AMBIGUOUS
- P11_CIK_INVALID
- P11_SUBMISSIONS_INVALID
- P11_FILING_NOT_FOUND
- P11_FILING_VARIANT_REVIEW_REQUIRED
- P11_PERIOD_UNRESOLVED
- P11_PERIOD_CONFLICT

HTTP/security:
- P11_USER_AGENT_REQUIRED
- P11_RATE_LIMITED
- P11_RATE_LIMIT_SCOPE_UNSAFE
- P11_SOURCE_HOST_NOT_ALLOWED
- P11_REDIRECT_NOT_ALLOWED
- P11_HTTP_FAILED
- P11_RESPONSE_TOO_LARGE
- P11_CONTENT_TYPE_INVALID

Package/storage:
- P11_PACKAGE_INVALID
- P11_PACKAGE_ASSET_MISSING
- P11_PACKAGE_HASH_MISMATCH
- P11_SOURCE_CONTENT_DRIFT
- P11_PATH_OUTSIDE_PROJECT
- P11_FINAL_ARTIFACT_COLLISION

Planner/reuse:
- P11_PACKAGE_AWARE_PLANNER_REQUIRED
- P11_EXACT_PACKAGE_REUSE
- P11_NO_REUSABLE_EXACT_PACKAGE
- P11_SOURCE_DOCUMENT_CHANGE
- P11_SOURCE_PACKAGE_CHANGE
- P11_REUSE_ARTIFACT_MISSING
- P11_REUSE_ARTIFACT_PATH_INVALID
- P11_REUSE_ARTIFACT_INVALID
- P11_REUSE_VALIDATION_NOT_PASS
- P11_REUSE_BLOCKING_ISSUES
- P11_REUSE_SCHEMA_INCOMPATIBLE
- P11_REUSE_COMPATIBILITY_UNKNOWN
- P11_REUSE_PARSER_INVALIDATED

Parse:
- P11_HTML_PARSE_FAILED
- P11_IXBRL_PARSE_FAILED
- P11_XBRL_PARSE_FAILED
- P11_DEPENDENCY_UNRESOLVED
- P11_VISUAL_RENDERING_REQUIRED

Validation:
- P11_DEI_IDENTITY_CONFLICT
- P11_XBRL_VALIDATION_REVIEW_REQUIRED
- P11_FACT_CONTEXT_INVALID
- P11_VALIDATION_BLOCKED

Runtime:
- P11_RUNTIME_UNAVAILABLE
- P11_RUNTIME_LOCK_MISMATCH
- P11_RUNTIME_PROTOCOL_INVALID
- P11_RUNTIME_TIMEOUT

## 28. Deterministic IDs

All IDs use canonical JSON + SHA256.

Canonical JSON:

```python
json.dumps(
    value,
    ensure_ascii=False,
    sort_keys=True,
    separators=(",", ":"),
    allow_nan=False,
).encode("utf-8")
```

No absolute path/time/random value participates in:

- source_package_sha256;
- parse_run_id;
- raw_fact_id;
- evidence_id;
- table_id;
- section_id.

## 29. Runtime protocol

If a dedicated P11 runtime is used, main/runtime communication is local JSON only.

No pickle.

No arbitrary Python expression.

No caller-supplied command.

Requests contain bounded structured fields only.

Runtime may write only inside the project-local P11 workspace/raw roots provided by frozen configuration.

## 30. P8/P9/P10 compatibility

P11 v1 MUST leave accepted:

- P8 tool names/server/result/catalog v1;
- P9 review policy/schema;
- P10 capability/context fingerprints;

unchanged.

P11 v1 artifacts are not automatically queryable through P8.

A future compatibility phase may expose SEC-native artifacts, but it must be separately designed/reviewed/accepted.

Until then P10 v1 `P11_SEC_PROVIDER=UNAVAILABLE` means unavailable to P10 v1, not that P11 provider does not exist globally.

## 31. Security

Forbidden:

- arbitrary network host;
- arbitrary redirect;
- file:// URL;
- caller-controlled local path escape;
- archive traversal;
- executable attachment execution;
- remote AI API;
- browser automation;
- hidden companyfacts substitution;
- HTML-to-PDF evidence fabrication.

## 32. Live acceptance targets

At least:

1. one domestic 10-K Inline XBRL;
2. one domestic 10-Q Inline XBRL with Q2 included somewhere in test coverage;
3. one foreign issuer 20-F or 40-F;
4. one supplemental 8-K or 6-K ingestion case;
5. one amendment case;
6. one custom taxonomy fact case.

Live sources must be official SEC only.

## 33. Performance

Acceptance records separately:

- submissions discovery time;
- asset download time;
- package commit time;
- HTML parse time;
- XBRL parse time;
- validation time;
- total time;
- bytes downloaded;
- request count;
- peak request rate.

No performance gate may encourage violating SEC fair access.

## 34. Regression boundary

Every P11 gate must prove:

- existing CN/HK acquisition still passes;
- P0-P10 unit regression passes;
- P8/P9/P10 accepted source/tests unchanged unless a later separately authorized compatibility phase explicitly says otherwise;
- no main-runtime remote AI/network dependency introduced.

## 35. Issue log

P11-ISSUE-001 through P11-ISSUE-009 are recorded in `development/144-p11-environment-interface-audit.md`. P11-ISSUE-010 through P11-ISSUE-033 were found during successive detached/manual design reviews and candidate-preflight checks; stop/amendment evidence is retained in `development/147` through `development/183`. The current amended design contains explicit resolutions for ISSUE-010..033; none is accepted as DESIGN READY until the next exact candidate passes a fresh detached design review.

Any new material issue:

```text
STOP
→ facts/root cause
→ amend design/26 + design/27 + acceptance/41
→ commit/push new design baseline
→ reauthorize affected implementation gate
```

## 36. Exit condition

P11 production is authorized only after:

- design/26 complete;
- design/27 complete;
- design/30 complete;
- acceptance/41 complete;
- design review PASS;
- design baseline commit/push;
- explicit P11 development authorization.

No implicit production authorization.
