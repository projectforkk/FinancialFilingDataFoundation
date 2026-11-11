# 26 — P11 US SEC Provider Detailed Design

Status: **DESIGN CORRECTED — P11 REPAIR BASELINE / PRIOR ACCEPTANCE SUSPENDED**

Phase: **P11 — US SEC Provider**

Current authorization:
`development/147-p11-us-scope-reopening-authorization.md`

Current scope contract:
`design/32-p11-us-scope-reopening.md`

Post-acceptance correction authority:
`design/33-p11-post-acceptance-design-correction.md`

Re-audit trigger:
`development/178-p11-full-design-code-consistency-reaudit.md`

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

Ticker is an alias only. The authoritative identity remains CIK.

Rules:

- cache the exact official ticker-map source bytes, SHA256, source URL and retrieved_at;
- a serialized derivative mapping is never authoritative by itself;
- every cached lookup must first verify the cached source bytes against their SHA and
  then reparse ticker → CIK from those verified bytes;
- if a stored derivative mapping is retained for diagnostics, it must exactly equal
  the reparsed mapping or the snapshot is invalid;
- exact ticker matching is case-insensitive after ASCII upper-case normalization;
- if one query maps ambiguously, fail closed;
- user-provided CIK bypasses ticker lookup entirely;
- never infer CIK from company name.

Online freshness policy:

- every online `acquire --market US` and `ingest --market US` invocation using
  `--ticker` fetches the current SEC ticker map before resolving identity;
- a stale cached ticker map must not silently substitute for a failed current lookup;
- local-only `status` may use the newest verified cached snapshot for display/query
  convenience, but must report the snapshot `retrieved_at` and must not claim that
  the ticker alias is current;
- explicit `--cik` remains the stable offline identity path.

New fail-closed conditions include tampered snapshot bytes, derivative/source mismatch
and conflicting cached mappings.

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


### 6.3 Amendments and discovery freshness

Forms ending `/A` are variant filings.

An amendment:

- has its own accession;
- has its own package identity;
- does not create an extra required fiscal slot;
- does not automatically replace the original package.

P11 v1 must emit `REVIEW_REQUIRED: P11_AMENDED_VARIANT_PRESENT` when both
original and amended forms exist for a required slot.

This rule applies not only on first acquisition but also when an amendment appears
after an original package has already been cached and parsed.

Therefore immutable package reuse and remote filing-metadata freshness are separate
concepts.

For every online `acquire` or `ingest` invocation:

1. resolve the stable CIK;
2. fetch current SEC submissions metadata and only history chunks required for the
   requested fiscal slot;
3. build and persist a deterministic discovery observation;
4. evaluate the complete current candidate set for the slot;
5. only after that evaluation decide REUSE_DATA, PARSE_LOCAL or
   DISCOVER_AND_ACQUIRE.

There is no TTL shortcut for online `acquire` / `ingest`. A repeat run may avoid
all archive-member downloads and all parser work, but it may not skip the submissions
metadata freshness check.

`status` remains local-only and performs no SEC network acquisition. It reports
the latest persisted discovery observation and an explicit `discovery_checked_at`
timestamp. Its meaning is therefore "local state as of the last discovery check",
not a live SEC assertion.

If current discovery cannot be completed, online `acquire` / `ingest` must fail
closed with an explicit discovery-freshness error rather than silently claiming the
cached package is currently research-ready.

Candidate-set rules:

- original + amendment → `P11_AMENDED_VARIANT_PRESENT`;
- multiple non-amendment candidates for one required slot →
  `P11_SLOT_CANDIDATE_CONFLICT`;
- exactly one current candidate may proceed;
- no current candidate → `P11_FILING_NOT_FOUND`.

A persisted old discovery observation is evidence of what FFDF previously observed;
it is never a substitute for the mandatory online revalidation step.

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
- XBRL_DEFINITION
- FILING_SUMMARY
- COMPLETE_SUBMISSION_TEXT
- OTHER

Not every filing has every role.

### 7.3 Minimal acquisition policy

Always acquire:

- the exact primary document from submissions metadata;
- filing-local XBRL members that are deterministically identified as XBRL support
  members for the same accession.

A filename extension alone is not sufficient to authorize XBRL acquisition.

Preferred deterministic inclusion sources are:

1. SEC filing-directory metadata with recognized XBRL attachment types such as
   `EX-101.INS`, `EX-101.SCH`, `EX-101.PRE`, `EX-101.CAL`,
   `EX-101.LAB` and `EX-101.DEF`;
2. exact filing-local references discovered from already accepted primary/XBRL
   members, subject to the same archive-path and host restrictions.

Do not sweep every `.xml`, `.xbrl` or `.xsd` file merely because of its
extension.

Acquire complete-submission text only as fallback/evidence when required.

Do not download unrelated exhibits by default.

If a generic XML member is acquired for another accepted reason and is classified
`OTHER`, it must never supply XBRL facts, contexts or units.

### 7.4 Member identity and provenance

Every member persists:

- source URL;
- SEC archive relative name;
- role;
- content type;
- byte length;
- SHA256.

For SEC Archives members the source URL must exactly correspond to:

`package CIK + normalized accession + relative_name`.

A merely allowlisted `sec.gov` URL is insufficient provenance.

On package construction and package reload, FFDF must verify this exact relationship.

### 7.5 Package identity

`package_sha256` remains SHA256 of canonical JSON containing sorted immutable
member records:

```text
role
relative_name
member_sha256
byte_length
```

This package hash intentionally identifies the immutable member-byte set and does not
change to include mutable-looking descriptive metadata.

The package manifest remains versioned.

Because CIK/accession/form/source URL are outside the package hash, provenance
integrity is enforced separately:

- Registry `source_packages` identity must agree with the loaded package manifest;
- Registry `package_members` role/name/hash/length/source_url must agree with the
  loaded members;
- P7 and P8 must fail closed on any manifest/Registry/source-URL provenance mismatch.

The package SHA formula is not changed by this correction.

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

### 9.4 Discovery observations

Add an immutable discovery observation for each online US slot check.

A discovery observation records at minimum:

- observation_sha256;
- company_id / CIK;
- fiscal_year;
- raw_fiscal_period;
- retrieved_at;
- official source documents used, each with source URL + source SHA256;
- sorted relevant filing candidates with accession/form/filing_date/report_period;
- selected accession nullable;
- amendment/conflict state;
- canonical candidate fingerprint;
- artifact path for the persisted observation.

`observation_sha256` is computed from canonical JSON over the stable slot identity,
source hashes and sorted relevant candidate records.

Official discovery source bytes are retained in a content-addressed metadata cache so
the observation can be independently reconstructed.

The SEC Registry version is incremented additively to store discovery observations.
The legacy Registry `user_version` remains unchanged.


## 10. Parser architecture and logical fact source

P11 uses a dedicated source-aware parser path.

```text
SecFilingPackage
→ primary HTML/iXBRL DOM
→ source blocks + headings + DOM tables
→ choose exactly one logical fact-source mode
→ contexts/units/raw facts
→ deterministic logical-page normalization
→ P3-like page/section artifacts
→ P4 DOM table candidates
→ P5 deterministic HTML table reconstruction
→ P6 raw facts + evidence
→ P7 validation
```

PDF rendering is not the primary parser.

### 10.1 Fact-source modes

Every parsed SEC package declares exactly one `fact_source_mode`.

#### INLINE_XBRL_PRIMARY

Use when the primary document contains supported Inline XBRL facts.

Rules:

- P6 logical raw facts are emitted only from the primary Inline XBRL document;
- the extracted XBRL instance may be used for deterministic cross-checking and
  provenance diagnostics but does not emit a second logical P6 fact set;
- contextRef/unitRef for an Inline XBRL fact must resolve from the primary Inline
  XBRL document's own XBRL resources;
- a missing primary context/unit is a validation issue and must not be silently
  repaired from an unrelated or extracted instance member.

#### XBRL_INSTANCE_PRIMARY

Use only when the primary document has no supported Inline XBRL facts and the package
contains exactly one verified XBRL instance suitable for the filing.

Rules:

- P6 logical raw facts come from that verified instance;
- the primary HTML still supplies narrative pages/sections/tables when present;
- multiple plausible XBRL instances fail closed with
  `P11_XBRL_INSTANCE_AMBIGUOUS`.

There is no mode that blindly concatenates primary Inline XBRL facts and instance
facts.

The artifact manifest records `fact_source_mode`.

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

P11 extracts filing-local raw facts without canonical metric mapping.

For each logical fact preserve at minimum:

- raw QName/concept;
- logical raw textual value;
- parsed numeric candidate nullable;
- contextRef;
- unitRef;
- decimals/precision when present;
- scale/sign/format when Inline XBRL uses them;
- startDate/endDate or instant from resolved context;
- entity identifier;
- explicit/typed dimensions;
- nil flag;
- fact_source_mode;
- primary source member;
- source block/DOM or XML locator;
- evidence id.

Custom extension concepts are allowed and preserved as raw QNames.

Do not map them to US-GAAP/IFRS canonical metrics in P11.

### 13.1 Inline XBRL continuation and exclusion

Inline XBRL logical text values must follow the Inline XBRL continuation model.

For any supported Inline fact carrying `continuedAt`:

- resolve the referenced `ix:continuation` by exact ID;
- append continuation content in deterministic chain order;
- allow chained continuations;
- reject missing IDs, duplicate target IDs and continuation cycles;
- content inside `ix:exclude` is not part of the logical fact value;
- excluded content remains available in source evidence but must not contaminate the
  fact value.

A continuation error creates `P11_INLINE_CONTINUATION_INVALID`, retains immutable
source evidence, and makes the affected structured fact unusable without guessing.

The fact/evidence contract supports an ordered `source_fragments` collection so one
logical fact may trace to the originating Inline fact node plus one or more
continuation nodes.

The evidence ID is deterministic over the logical fact identity and ordered source
fragment identities.

### 13.2 Cross-source duplicate policy

For `INLINE_XBRL_PRIMARY`, an extracted XBRL instance is not a second fact source.

If cross-checking is implemented, equivalent instance facts may be attached as
alternate/cross-check provenance, but they must not create another P8 raw-fact row.

For `XBRL_INSTANCE_PRIMARY`, instance facts are the sole logical fact rows.

Changing this source rule requires a new parser/artifact compatibility version.


## 14. Context and unit rules

A tagged fact is usable as a structured raw fact only if referenced context/unit can
be deterministically resolved when required.

For `INLINE_XBRL_PRIMARY`:

- contexts and units are resolved from the primary Inline XBRL document only;
- XBRL_INSTANCE, schema/linkbase and OTHER members must not silently repair a missing
  primary context/unit.

For `XBRL_INSTANCE_PRIMARY`:

- contexts and units are resolved from the selected verified XBRL instance only.

`OTHER` XML is never an XBRL semantic source.

Unresolved references:

- retain raw source evidence;
- create validation issue;
- do not fabricate period/unit;
- do not borrow a same-named context/unit from another source member.

Period labels remain source-derived candidates. Fiscal quarter canonicalization is a
separate deterministic filing-policy step, not an XBRL concept-name guess.


## 15. Tables

HTML `<table>` elements are first-class table candidates.

P4-US candidate record includes:

- source table node locator;
- heading/caption context;
- logical row/column counts;
- nested-table signal;
- Inline XBRL fact presence;
- visibility/style signals.

P5-US reconstructs an occupied logical grid from DOM structure.

Rules:

- `rowspan` and `colspan` populate the occupied grid;
- `column_count` is the maximum occupied logical grid width, not the number of
  origin cell nodes in a row;
- for SEC HTML, `value_column_count` remains a compatibility alias for the logical
  grid width unless a separately reviewed numeric-value-column contract is added;
- a cell is a header because it is a real `<th>`/header construct, not merely
  because it appears in row 0;
- `header_tree` is reconstructed from header cells and their span coverage over
  logical columns;
- each origin cell preserves source text, fact references and DOM locator.

No OCR/TableFormer is used for born-digital SEC HTML.


## 16. Evidence

P6 evidence is source-kind aware through additive fields.

US HTML evidence includes:

- package_sha256;
- member_sha256;
- virtual_page_no;
- block_id;
- dom_locator;
- fragment_hash;
- raw_text;
- table/cell coordinates where applicable.

For continued Inline XBRL facts, one logical evidence record may additionally contain
ordered `source_fragments`, where each fragment contains at minimum:

- source member SHA;
- DOM locator;
- fragment hash;
- source-order index;
- raw source text.

Existing CN/HK PDF evidence fields remain unchanged.

Evidence loaders must verify every referenced source member hash and every referenced
DOM/XML/source-fragment locator before serving evidence.

P8 must also verify the loaded package manifest/member provenance against the SEC
Registry before serving SEC evidence.


## 17. Validation

P7-US must check at least:

1. accession/CIK/form metadata consistency;
2. package manifest/member hash integrity;
3. package manifest/member provenance vs Registry identity;
4. exact member source URL vs package CIK/accession/relative_name;
5. primary document exists and is parseable;
6. discovery observation identity/source-hash integrity;
7. duplicate/conflicting current filing slot candidates;
8. amendment presence;
9. fact_source_mode validity;
10. Inline XBRL contextRef resolution;
11. unitRef resolution where required;
12. no context/unit resolution from OTHER XML;
13. continuation/exclude chain validity;
14. period-end vs filing metadata plausibility;
15. DOM/XML/source-fragment locator resolvability;
16. table/grid/header source traceability;
17. raw fact → evidence coverage;
18. no logical fact duplication caused by dual-source enumeration;
19. no source member drift;
20. package/member path safety.

P7 receives the exact discovery observation used by the online acquire/ingest
invocation. It does not accept a free-floating boolean as the sole proof of amendment
state.

Validation output records:

- discovery_observation_sha256;
- discovery_checked_at;
- selected accession;
- fact_source_mode.

Status remains:

`PASS | REVIEW_REQUIRED | BLOCKED`.

A P7 PASS is an as-of assertion tied to a specific discovery observation. It is not a
promise that SEC metadata can never change after that timestamp.

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
- evidence responses may contain new source-locator/source-fragment fields;
- document/validation responses expose `discovery_checked_at` and the discovery
  observation identity.

No acquisition occurs inside P8.

P8 therefore serves a validated snapshot **as of the last accepted discovery
observation**. It does not claim live SEC freshness.

A P8 catalog entry must identify:

- the SEC package;
- compatible P3/P5/P6/P7 artifact directories;
- stable CIK company identity;
- the discovery observation used for validation.

Before serving an SEC bundle, P8 must verify package/member provenance against the
Registry and verify the full evidence source chain.

## 20. P9 / P10 compatibility

P9 may review US facts only after P8 artifact semantics are accepted.

P9 must not write to package members or base raw facts.

P10 sees US as another market only after P11 acceptance. No P10 research rule is
hard-coded for SEC tags.


## 21. CLI integration target

Merge-ready P11 supports:

```text
ffdf acquire --market US --ticker AAPL --year 2026 --period Q3
ffdf ingest  --market US --ticker AAPL --year 2026 --period Q3
ffdf status  --market US --ticker AAPL --year 2026 --period Q3
```

Market-specific period validation:

- CN/HK: existing Q1/H1/Q3/FY unchanged;
- US domestic: Q1/Q2/Q3/FY.

An explicit `--cik` option takes precedence over ticker lookup.

Network semantics:

- `acquire` and `ingest` perform current identity/discovery metadata checks before
  reuse planning;
- repeated runs may reuse package and parser artifacts after the metadata check;
- `status` is local-only and reports the discovery as-of timestamp.

### 21.1 Production feature gate

The final merge-ready candidate must be testable in actual production semantics.

Therefore:

- `FFDF_P11_US_DEV` must not be required for normal US CLI/P8 behavior in the
  merge-ready candidate;
- the feature branch may contain production-enable code and `SUPPORTED_MARKETS`
  declarations before acceptance because the branch is not accepted production;
- accepted `main` remains CN/HK-only until the exact merge-ready candidate passes
  independent acceptance and is merged;
- formal acceptance must run the production path with
  `FFDF_P11_US_DEV` absent;
- no production behavior may be changed after ACCEPTANCE_PASS merely as part of the
  merge step.

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

The corrected online planner has two layers.

### Layer A — current discovery gate

For every online `acquire` / `ingest`:

```text
current SEC ticker resolution when ticker is used
→ current submissions/history discovery
→ persist discovery observation
→ evaluate amendment/conflict/not-found
```

If this gate cannot establish one unambiguous current accession, no research-ready
reuse is returned.

### Layer B — byte/parser reuse

After Layer A selects one current accession:

```text
matching compatible parsed package available?
→ REUSE_DATA

else matching immutable local SEC package available?
→ PARSE_LOCAL

else
→ DISCOVER_AND_ACQUIRE archive members
```

Repeat-run expectations:

- submissions/ticker metadata requests are allowed/required as defined above;
- if the selected accession is unchanged, archive members are not redownloaded;
- if compatible parsed data exists, parser work is skipped;
- a new amendment or conflicting accession invalidates research-ready reuse;
- a source re-fetch that yields changed bytes for the same SEC archive member is
  `SOURCE_DRIFT`, never silent overwrite.

Thus `INCREMENTAL_FIRST` means "avoid redundant immutable-byte and parser work", not
"never revalidate mutable discovery metadata".


## 25. Reason codes

Minimum P11 reason codes include:

- P11_INVALID_US_IDENTITY
- P11_TICKER_CIK_AMBIGUOUS
- P11_TICKER_SNAPSHOT_INVALID
- P11_SEC_RATE_LIMITED
- P11_SEC_ACCESS_DENIED
- P11_SEC_DISCOVERY_FAILED
- P11_DISCOVERY_FRESHNESS_UNKNOWN
- P11_FILING_NOT_FOUND
- P11_FORM_POLICY_MISMATCH
- P11_AMENDED_VARIANT_PRESENT
- P11_SLOT_CANDIDATE_CONFLICT
- P11_ARCHIVE_HOST_REJECTED
- P11_CONTENT_TYPE_INVALID
- P11_SIZE_LIMIT_EXCEEDED
- P11_PACKAGE_INVALID
- P11_PROVENANCE_MISMATCH
- P11_MEMBER_HASH_MISMATCH
- P11_SOURCE_DRIFT
- P11_PRIMARY_DOCUMENT_MISSING
- P11_HTML_PARSE_FAILED
- P11_XBRL_INSTANCE_AMBIGUOUS
- P11_XBRL_CONTEXT_UNRESOLVED
- P11_XBRL_UNIT_UNRESOLVED
- P11_INLINE_CONTINUATION_INVALID
- P11_EVIDENCE_LOCATOR_INVALID
- P11_UNSUPPORTED_FPI_PERIODIC_MAPPING


## 26. Acceptance scope

P11 cannot be accepted by unit tests alone.

Required live/golden classes:

1. domestic 10-K with Inline XBRL;
2. domestic 10-Q with Inline XBRL;
3. filing with custom extension concepts;
4. original filing followed later by an amendment, proving a cached original cannot
   bypass fresh discovery;
5. foreign private issuer 20-F or 40-F annual filing;
6. primary iXBRL + extracted instance fixture proving one logical P6 fact set;
7. non-inline HTML + XBRL-instance fixture;
8. continuation/exclude conformance-style fixtures;
9. unrelated XML context/unit collision negative fixture;
10. ticker snapshot tamper/remap negative fixtures;
11. manifest/source-URL provenance tamper negative fixtures;
12. colspan/rowspan/header-table fixtures;
13. path/content-type/size/security negatives;
14. SEC throttling/access-denied simulation;
15. repeat online acquire/ingest proving:
    - discovery metadata is revalidated;
    - archive member downloads are skipped when accession is unchanged;
    - parser is skipped when compatible parsed data is reusable;
16. production-mode CLI/P8 with `FFDF_P11_US_DEV` absent;
17. full CN/HK/P8/P9/P10 non-regression.

Exact live accessions are frozen during acceptance preparation, not guessed in this
design.

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

Before adding US to accepted production main:

- all corrected P11 focused tests PASS;
- full P0-P10 unit regression PASS;
- CN acquire/ingest/status behavior unchanged;
- HK acquire/ingest/status behavior unchanged;
- P8 CN/HK catalog queries unchanged;
- P9/P10 accepted tests unchanged;
- Registry v3 → v4 migration is additive/idempotent and legacy `user_version`
  remains unchanged;
- future/unknown Registry schema still fails closed without mutation;
- old V4 / p11-sec-artifacts-v1 parsed artifacts are not silently reused under the
  new fact semantics;
- compatible local raw SEC packages may be reparsed after fresh discovery;
- production US CLI/P8 passes with `FFDF_P11_US_DEV` absent;
- `git diff --check` PASS.

The merge-ready candidate itself contains all production behavior required after
merge. Gate I1 must not introduce unreviewed production-code changes.

## 29. Issue policy

All P11 implementation issues use:

`P11-ISSUE-###`

Each issue records facts, root cause, design amendment, invalidated evidence,
implementation fix and rerun result.


## 30. Exit condition

P11 is DONE only after:

```text
CORRECTED DESIGN
→ REPAIR DEVELOPMENT
→ DETACHED EXACT-CANDIDATE CODE REVIEW
→ NEW ACCEPTANCE FREEZE
→ INDEPENDENT ACCEPTANCE IN PRODUCTION SEMANTICS
→ EXACT-CANDIDATE MAIN INTEGRATION
→ CLOSEOUT
```

Until then, accepted production main continues to report the SEC provider as
unavailable.

The prior acceptance recorded before `development/178-p11-full-design-code-consistency-reaudit.md`
does not authorize main integration.

## 31. Corrected compatibility/version baseline

The repair intentionally changes parser semantics, artifact shape and SEC Registry
state.

Required target versions:

```text
REGISTRY_SCHEMA_VERSION = 1              # legacy CN/HK stays frozen
SEC_REGISTRY_SCHEMA_VERSION = 4          # additive discovery observation support
SEC_DISCOVERY_SCHEMA = p11-sec-discovery-v1
VIRTUAL_HTML_NORMALIZER_VERSION = VIRTUAL_HTML_V5
SEC_ARTIFACT_SCHEMA = p11-sec-artifacts-v2
SEC_VALIDATION_SCHEMA = p11-sec-validation-v2
```

The package SHA formula remains unchanged.

Compatibility rules:

- V4 / p11-sec-artifacts-v1 parsed artifacts are INCOMPATIBLE with corrected fact
  semantics;
- immutable raw packages remain reusable after current discovery revalidation;
- local old artifacts are never mutated in place;
- reparsing creates V5/v2 artifacts;
- SEC Registry v3 migrates additively to v4;
- accepted CN/HK Registry/data/artifacts remain unchanged.

Any implementation that cannot preserve these compatibility rules must stop and
return to design review.

