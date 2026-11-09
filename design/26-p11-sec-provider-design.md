# 26 — P11 US SEC Provider Detailed Design

Status: **DESIGN READY CANDIDATE — P11 REBUILD / PRODUCTION NOT IMPLEMENTED**

Phase: **P11 — US SEC Provider**

Current authorization:
`development/147-p11-us-scope-reopening-authorization.md`

Current scope contract:
`design/32-p11-us-scope-reopening.md`

## 1. Goal

Implement an official SEC/EDGAR acquisition and parsing path for US filings while
preserving the accepted P0-P10 CN/HK production behavior.

P11 must support a filing as an immutable **source package**, not pretend that every
SEC filing is one PDF.

Primary target:

```text
ticker / CIK
→ filing discovery
→ accession identity
→ primary HTML / Inline XBRL + required XBRL members
→ immutable package store
→ deterministic parsing
→ P3/P4/P5/P6/P7-compatible artifacts
→ P8 read-only research
```

## 2. Non-goals

P11 v1 does NOT:

- submit filings to EDGAR;
- use EDGAR Next filer-management/submission APIs;
- call remote AI/LLM APIs;
- use SEC companyfacts as filing source truth;
- implement investment analysis;
- implement canonical metric mapping;
- guess fiscal periods from filenames;
- auto-select every 6-K as a quarterly report;
- silently supersede an original filing with a /A amendment;
- mutate accepted CN/HK raw files or parsed artifacts;
- change P9 resolution semantics;
- turn P8 into an acquisition tool.

## 3. Official SEC interfaces

### 3.1 Public submissions metadata

Use:

`https://data.sec.gov/submissions/CIK##########.json`

CIK is 10-digit zero padded for the request URL.

The submissions response is the primary discovery source for recent filing history.
If the response lists older-history JSON files, P11 may fetch only the files needed
for the requested year range.

### 3.2 Filing archive

The exact filing bytes are acquired from SEC Archives using accession metadata.

Only allowlisted SEC hosts may be contacted by production acquisition code.

### 3.3 XBRL APIs

`companyfacts` and `companyconcept` are optional validation/cross-check inputs.

Rules:

- they are not replacements for exact filing bytes;
- they cannot supply a missing filing fact as if it came from the filing;
- custom taxonomy facts may not appear in the aggregate APIs and must remain
  available from filing-local Inline XBRL/XBRL parsing.

## 4. Fair Access / HTTP contract

Every automated request must:

- send an identifying User-Agent containing application/organization identity and a
  monitored contact email configured outside source code;
- respect the SEC maximum aggregate access rate of 10 requests/second;
- P11 internal default ceiling: **8 requests/second** for safety margin;
- share one limiter across all SEC hosts in the P11 process;
- respect HTTP 429 / 403 and `Retry-After` where provided;
- use bounded deterministic exponential backoff;
- use connect/read/total timeouts;
- reject unexpected redirect hosts.

No API key is required for public `data.sec.gov` APIs.

## 5. Company identity

### 5.1 Stable company identity

US company identity is CIK-based:

```text
market = US
company_id = US:CIK##########
ticker = display/query alias
provider_company_id = ##########
```

Ticker is not a stable primary key.

### 5.2 Ticker → CIK resolution

A resolver may use the SEC-published ticker/CIK association.

Rules:

- cache the source bytes and SHA;
- store retrieved_at/source URL;
- exact ticker matching is case-insensitive after ASCII upper-case normalization;
- if one query maps ambiguously, fail closed;
- user may provide CIK explicitly to bypass ticker lookup;
- never infer CIK from company name.

## 6. Filing identity

### 6.1 SEC accession identity

The authoritative provider filing identity is the SEC accession number.

Persist both:

- accession with dashes for display;
- normalized accession without dashes for archive paths / comparison.

### 6.2 FilingSlotKey

Add US period support without changing CN/HK semantics.

Domestic issuer policy:

```text
FY → 10-K
Q1 → 10-Q
Q2 → 10-Q
Q3 → 10-Q
```

US requires Q2; CN/HK continue to use their accepted Q1/H1/Q3/FY policy.

Slot identity remains:

```text
market
company_id
filing_type
fiscal_year
raw_fiscal_period
```

### 6.3 Amendments

Forms ending `/A` are variant filings.

An amendment:

- has its own accession;
- has its own package identity;
- does not create an extra required fiscal slot;
- does not automatically replace the original package.

P11 v1 must emit `REVIEW_REQUIRED: AMENDED_VARIANT_PRESENT` when both original and
amended forms exist for a required slot unless a later accepted deterministic policy
can prove which package is complete for research use.

## 7. Filing package model

### 7.1 Why a package is required

An SEC filing may contain:

- primary HTML, often Inline XBRL;
- XBRL instance;
- schema;
- presentation/calculation/label linkbases;
- FilingSummary or related metadata;
- complete submission text;
- exhibits.

The canonical acquired object is therefore `SecFilingPackage`.

### 7.2 Package member roles

Minimum roles:

- PRIMARY_DOCUMENT
- XBRL_INSTANCE
- XBRL_SCHEMA
- XBRL_PRESENTATION
- XBRL_CALCULATION
- XBRL_LABEL
- FILING_SUMMARY
- COMPLETE_SUBMISSION_TEXT
- OTHER

Not every filing has every role.

### 7.3 Minimal acquisition policy

Always acquire:

- primary document;
- all filing-local XBRL members necessary to resolve contexts, units and tagged facts.

Acquire complete-submission text only as fallback/evidence when required.

Do not download unrelated exhibits by default.

### 7.4 Member identity

Every member persists:

- source URL;
- SEC archive relative name;
- role;
- content type;
- byte length;
- SHA256.

### 7.5 Package identity

`package_sha256` is SHA256 of canonical JSON containing sorted immutable member
records:

```text
role
relative_name
member_sha256
byte_length
```

The package manifest itself is versioned.

## 8. Raw storage

Do not force SEC packages into the accepted PDF-only leaf layout.

Add a parallel package store:

```text
workspace/ingest/raw-store/
  sha256/                 # accepted CN/HK PDF objects unchanged
  packages/
    sha256/
      <aa>/
        <package_sha256>/
          manifest.json
          members/
            ...
```

Rules:

- member bytes immutable;
- atomic staging → verify → commit;
- same package SHA is reused;
- no archive path may escape package root;
- filenames are metadata only, never identity;
- source URL is never used as a local path.

## 9. Registry evolution

Registry migration must be additive and backward compatible.

Existing CN/HK tables remain valid.

New concepts:

### 9.1 source_packages

- package_sha256 PK
- provider = sec
- accession
- cik
- form
- filed_date
- accepted_at nullable
- report_period nullable
- primary_document
- manifest_schema_version
- first_seen_at

### 9.2 package_members

- package_sha256
- member_sha256
- relative_name
- role
- content_type
- byte_length
- source_url
- PRIMARY KEY(package_sha256, relative_name)

### 9.3 filing_bindings extension

A binding may reference either:

- legacy `document_sha256` (CN/HK PDF);
- SEC `package_sha256`.

The migration must not rewrite accepted CN/HK rows.

## 10. Parser architecture

P11 uses a dedicated source-aware parser path.

```text
SecFilingPackage
→ primary HTML/iXBRL DOM
→ source blocks + headings + DOM tables
→ Inline XBRL contexts/units/facts
→ deterministic logical-page normalization
→ P3-like page/section artifacts
→ P4 DOM table candidates
→ P5 deterministic HTML table reconstruction
→ P6 raw facts + evidence
→ P7 validation
```

PDF rendering is not the primary parser.

## 11. Logical pages for HTML

Existing P3/P6/P8 contracts use page numbers. HTML has no physical pages.

P11 therefore adds explicit pagination metadata:

```text
pagination_kind = VIRTUAL_HTML
```

A virtual page is a deterministic ordered group of source blocks.

Rules:

- stable for identical primary-document bytes + normalizer version;
- starts at 1;
- never presented as a physical SEC page;
- preserves block IDs and DOM locators;
- changes in normalizer version do not mutate old artifacts.

CN/HK continue to use:

`pagination_kind = PHYSICAL_PDF`.

## 12. Source blocks / DOM locators

Every normalized block receives:

- block_id;
- source_member_sha256;
- DOM path or deterministic node locator;
- raw text;
- source-order index;
- virtual_page_no;
- fragment hash.

Evidence can therefore return to the exact immutable HTML member even when no
physical PDF page exists.

## 13. Inline XBRL / XBRL raw facts

P11 extracts filing-local raw facts without canonical mapping.

For each fact preserve at minimum:

- raw QName/concept;
- raw textual value;
- parsed numeric candidate nullable;
- contextRef;
- unitRef;
- decimals/precision when present;
- scale/sign when Inline XBRL uses them;
- startDate/endDate or instant from resolved context;
- entity identifier;
- explicit/typed dimensions;
- nil flag;
- source member;
- source block/DOM locator;
- evidence id.

Custom extension concepts are allowed and preserved as raw QNames.

Do not map them to US-GAAP/IFRS canonical metrics in P11.

## 14. Context and unit rules

A tagged fact is usable as structured raw fact only if referenced context/unit can
be deterministically resolved when required.

Unresolved references:

- retain raw source evidence;
- create validation issue;
- do not fabricate period/unit.

Period labels remain source-derived candidates. Fiscal quarter canonicalization is a
separate deterministic filing-policy step, not an XBRL concept-name guess.

## 15. Tables

HTML `<table>` elements are first-class table candidates.

P4-US candidate record includes:

- source table node locator;
- heading/caption context;
- row/column counts;
- nested-table signal;
- Inline XBRL fact presence;
- visibility/style signals.

P5-US reconstructs cells from DOM structure:

- rowspan/colspan;
- header tree;
- source text;
- fact references;
- DOM locator per cell.

No OCR/TableFormer is used for born-digital SEC HTML.

## 16. Evidence

P6 evidence becomes source-kind aware through additive fields.

US HTML evidence includes:

- package_sha256;
- member_sha256;
- virtual_page_no;
- block_id;
- dom_locator;
- fragment_hash;
- raw_text;
- table/cell coordinates where applicable.

Existing CN/HK PDF evidence fields remain unchanged.

Evidence loaders must verify source member hash before serving evidence.

## 17. Validation

P7-US must check at least:

1. accession/CIK/form metadata consistency;
2. package manifest/member hash integrity;
3. primary document exists and is parseable;
4. Inline XBRL contextRef resolution;
5. unitRef resolution where required;
6. duplicate/conflicting filing slot candidates;
7. period-end vs filing metadata plausibility;
8. DOM locator resolvability;
9. table/cell source traceability;
10. raw fact → evidence coverage;
11. no source member drift;
12. package/member path safety.

Status remains:

`PASS | REVIEW_REQUIRED | BLOCKED`.

## 18. companyfacts cross-check

Optional validation may query companyfacts for standard concepts.

Mismatch policy:

- exact filing artifact remains source truth;
- companyfacts mismatch produces warning/review evidence;
- companyfacts must never overwrite P6 raw facts;
- no cross-company frame data is used to fill filing-local gaps.

## 19. P8 integration

P8 keeps the same accepted tool names.

US integration is additive:

- list/get document can return market=US;
- read_pages returns virtual HTML pages and explicit `pagination_kind`;
- sections/tables/facts/evidence/validation use the same tool families;
- evidence responses may contain new source-locator fields.

No acquisition occurs inside P8.

A P8 catalog entry must identify the SEC package and compatible P3/P5/P6/P7 artifact
directories.

## 20. P9 / P10 compatibility

P9 may review US facts only after P8 artifact semantics are accepted.

P9 must not write to package members or base raw facts.

P10 sees US as another market only after P11 acceptance. No P10 research rule is
hard-coded for SEC tags.

## 21. CLI integration target

After parser acceptance, extend user CLI:

```text
ffdf acquire --market US --ticker AAPL --year 2026 --period Q3
ffdf ingest  --market US --ticker AAPL --year 2026 --period Q3
ffdf status  --market US --ticker AAPL --year 2026 --period Q3
```

Market-specific period validation:

- CN/HK: existing Q1/H1/Q3/FY unchanged;
- US domestic: Q1/Q2/Q3/FY.

An explicit `--cik` option is permitted and takes precedence over ticker lookup.

## 22. Runtime / dependency boundary

P11 does not use the Dayu runtime.

Preferred architecture:

```text
FFDF main runtime
  deterministic orchestration / Registry
        |
        | subprocess JSON
        v
Dedicated SEC runtime
  HTTP + HTML/XML parser only
        |
        v
staging package + parse artifacts
```

The development gate must audit the existing PC/runtime before selecting exact
packages.

Expected minimal dependencies:

- HTTP client;
- robust HTML/XML parser.

Do not add Arelle or another full XBRL processor unless a measured fixture proves the
minimal parser cannot safely resolve required filing-local facts.

Exact runtime pins are frozen only after environment audit.

## 23. Security

Production SEC code must:

- allowlist SEC hosts;
- reject arbitrary caller URLs;
- reject path traversal;
- cap response/member/package sizes;
- cap redirect count;
- validate content type and actual bytes;
- use TLS verification;
- never execute JavaScript from filings;
- never load remote resources referenced by filing HTML;
- never extract ZIP/archive entries outside controlled staging;
- never invoke shell from downloaded content.

Suggested initial size ceilings, subject to fixture measurement:

- submissions JSON: 32 MiB;
- single filing member: 128 MiB;
- complete package: 512 MiB.

Exceeding limits is fail-closed with explicit reason code.

## 24. Incremental reuse

Planner order remains:

```text
compatible parsed package available?
→ REUSE_DATA

else immutable local SEC package available?
→ PARSE_LOCAL

else
→ DISCOVER_AND_ACQUIRE
```

Same accession/package hash must not be redownloaded.

A source re-fetch that yields changed bytes for the same SEC archive member is
`SOURCE_DRIFT`, never silent overwrite.

## 25. Reason codes

Minimum new reason codes:

- P11_INVALID_US_IDENTITY
- P11_TICKER_CIK_AMBIGUOUS
- P11_SEC_RATE_LIMITED
- P11_SEC_ACCESS_DENIED
- P11_SEC_DISCOVERY_FAILED
- P11_FILING_NOT_FOUND
- P11_FORM_POLICY_MISMATCH
- P11_AMENDED_VARIANT_PRESENT
- P11_ARCHIVE_HOST_REJECTED
- P11_CONTENT_TYPE_INVALID
- P11_SIZE_LIMIT_EXCEEDED
- P11_PACKAGE_INVALID
- P11_MEMBER_HASH_MISMATCH
- P11_SOURCE_DRIFT
- P11_PRIMARY_DOCUMENT_MISSING
- P11_HTML_PARSE_FAILED
- P11_XBRL_CONTEXT_UNRESOLVED
- P11_XBRL_UNIT_UNRESOLVED
- P11_EVIDENCE_LOCATOR_INVALID
- P11_UNSUPPORTED_FPI_PERIODIC_MAPPING

## 26. Acceptance scope

P11 cannot be accepted by unit tests alone.

Required live/golden classes:

1. domestic 10-K with Inline XBRL;
2. domestic 10-Q with Inline XBRL;
3. filing with custom extension concepts;
4. filing with amended variant present;
5. foreign private issuer 20-F or 40-F annual filing;
6. negative malformed/path/content-type fixtures;
7. SEC throttling/access-denied simulation;
8. repeat acquire/parse proving idempotent reuse.

Exact accession fixtures are frozen during acceptance preparation, not guessed in
this design.

## 27. Performance gates

Initial targets:

- no unnecessary re-download for known accession/package;
- submissions discovery should fetch only required history chunks;
- HTML parser uses no OCR/neural layout;
- repeated parse of identical local package is skipped when accepted parsed data is
  reusable;
- P8 remains lazy-load and does not load every US package at startup.

Measured numeric timing thresholds are frozen after the environment probe.

## 28. Compatibility gates

Before adding `US` to public supported markets:

- all P11 focused tests PASS;
- full P0-P10 unit regression PASS;
- CN acquire/ingest/status behavior unchanged;
- HK acquire/ingest/status behavior unchanged;
- P8 CN/HK catalog queries unchanged;
- P9/P10 accepted tests unchanged;
- Registry migration opens old databases without rewriting source rows;
- `git diff --check` PASS.

## 29. Issue policy

All P11 implementation issues use:

`P11-ISSUE-###`

Each issue records facts, root cause, design amendment, invalidated evidence,
implementation fix and rerun result.

## 30. Exit condition

P11 is DONE only after:

DESIGN
→ DEVELOPMENT
→ DETACHED CODE REVIEW
→ ACCEPTANCE FREEZE
→ INDEPENDENT ACCEPTANCE
→ MAIN INTEGRATION
→ CLOSEOUT

Until then, current accepted production must continue to report the SEC provider as
unavailable.
