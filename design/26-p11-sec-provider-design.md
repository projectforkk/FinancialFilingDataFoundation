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
- ticker is a lookup/display attribute and can change;
- ticker association is not sufficient for identity;
- CIK never comes from filename inference.

Ticker resolution:

1. exact caller-supplied CIK wins after validation;
2. otherwise resolve ticker using SEC-hosted ticker mapping;
3. verify resolved CIK against Submissions API ticker/name metadata when available;
4. ambiguity or mismatch => `P11_COMPANY_IDENTITY_AMBIGUOUS`.

## 5. Identity model amendments

P11 requires additive identity support:

```text
market: CN | HK | US
raw_fiscal_period: Q1 | Q2 | Q3 | H1 | FY
```

Rules:

- CN/HK semantics remain unchanged;
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

## 7. Period binding

Discovery metadata is provisional.

Final periodic binding is confirmed after source acquisition.

Preferred evidence order:

1. Inline/XBRL DEI `DocumentFiscalYearFocus`;
2. Inline/XBRL DEI `DocumentFiscalPeriodFocus`;
3. filing form + report date consistency;
4. filer fiscal year end only as a consistency check.

Rules:

- 10-K must resolve to FY;
- 10-Q must resolve to Q1/Q2/Q3;
- 20-F/40-F must resolve to FY;
- conflicting DEI vs requested slot => REVIEW_REQUIRED/BLOCKED;
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
- obey a hard per-process ceiling <=10 requests/sec;
- default implementation target = <=8 requests/sec for headroom;
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
- max retry count is frozen before implementation.

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

Required assets:

- filing index metadata;
- primary document;
- exact XBRL instance if separate;
- filing-specific schema/linkbases required by the filing;
- explicitly requested exhibit(s), if permitted.

Do not download every exhibit by default.

Package manifest contains:

- schema_version;
- CIK;
- accession_number;
- base_form;
- amended;
- filing_date;
- report_date;
- primary_document;
- assets sorted by canonical role/name/url;
- each asset SHA256/size/media type;
- package hash.

## 15. Package identity

Primary `document_sha256`:
SHA256(exact primary document bytes).

`source_package_sha256`:
SHA256(canonical package manifest identity payload).

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

Supplemental accession-bound documents may be registered without a periodic FilingSlotKey binding in P11 v1; the supplemental manifest remains authoritative for their filing identity.

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
- P11_SOURCE_HOST_NOT_ALLOWED
- P11_REDIRECT_NOT_ALLOWED
- P11_HTTP_FAILED
- P11_RESPONSE_TOO_LARGE
- P11_CONTENT_TYPE_INVALID

Package:
- P11_PACKAGE_INVALID
- P11_PACKAGE_ASSET_MISSING
- P11_PACKAGE_HASH_MISMATCH
- P11_SOURCE_CONTENT_DRIFT
- P11_PATH_OUTSIDE_PROJECT

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

P11-ISSUE-001 through P11-ISSUE-009 are recorded in development/144.

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
