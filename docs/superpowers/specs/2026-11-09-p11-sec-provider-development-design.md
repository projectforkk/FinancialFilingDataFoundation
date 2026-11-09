# P11 US SEC Provider Development Design

## Intent

Build the production candidate for the reopened P11 phase: acquire official SEC
filings by CIK/accession, preserve an immutable filing package, parse primary
HTML/Inline XBRL and filing-local XBRL deterministically, expose source-aware
pages/tables/raw facts/evidence/validation through the existing P8 read path,
and add explicit US CLI support without changing accepted CN/HK behavior.

The current accepted baseline remains CN/HK. This document describes a
development candidate only; it does not enable US in the accepted public market
declaration and does not perform formal acceptance.

## Goals

- Stable US identity: `US:CIK##########`, with explicit-CIK and exact ticker
  resolution; ambiguous resolution fails closed.
- Official SEC submissions and archive discovery with accession, form, filing
  date, report period, primary document, amendment, and FPI policy handling.
- SEC fair-access controls: configured application/organization/contact
  User-Agent, one shared 8 req/s limiter, bounded retry/backoff, redirect host
  validation, TLS verification, and bounded responses.
- Immutable content-addressed SEC packages with deterministic package SHA,
  member metadata, atomic staging, source-drift detection, and additive Registry
  storage.
- HTML/iXBRL-first artifacts with deterministic virtual HTML pages, DOM locators,
  rowspan/colspan table reconstruction, raw QName/context/unit preservation, and
  fact-to-evidence round trips.
- P7 source-aware validation, P8 read-only access using the existing 11 tool
  names, and US CLI `acquire`, `ingest`, and `status` behind an explicit gate.
- US domestic Q1/Q2/Q3/FY policy and FPI annual 20-F/40-F support; unsupported
  automatic 6-K quarterly mapping fails closed.

## Non-goals

- No change to `SUPPORTED_MARKETS` or accepted production availability before
  independent P11 acceptance.
- No PDF parser, OCR, Docling, Arelle, Companyfacts-as-source, canonical metric
  mapping, fiscal-period inference from tag names, YoY/QoQ/TTM, valuation, or
  investment conclusions.
- No P8 acquisition/network/mutation behavior, P9 raw overlay mutation, P10
  responsibility changes, remote AI/API calls, arbitrary caller URLs, or source
  byte rewriting.
- No formal acceptance, merge to main, or acceptance PASS declaration.

## Approaches

1. **Extend the accepted PDF acquisition/parser path.** Rejected: SEC filings
   are package/HTML/iXBRL sources rather than one PDF, and this would violate the
   source-kind and evidence requirements.
2. **Put SEC network and parsing inside P8.** Rejected: P8 is an accepted
   read-only local boundary and must not acquire, parse, or use the network.
3. **Add an additive `us_sec` provider with a subprocess runtime boundary.**
   Chosen: the FFDF main runtime keeps Registry/orchestration and the current
   lightweight dependency set; a stdlib-only SEC runner owns controlled HTTP and
   HTML/XML parsing. The existing P8 service routes SEC artifact bundles without
   changing tool names or CN/HK loader semantics.

## Chosen design

### Identity and feature gate

Existing identity types gain an explicit, non-default development allowance for
US slots. `SUPPORTED_MARKETS` stays exactly `("CN", "HK")`. CLI and public
orchestration reject US unless `FFDF_P11_US_DEV=1` is explicitly present;
internal tests pass an explicit development flag. The gate is deterministic and
does not alter the accepted declaration.

### Provider and package boundary

`us_sec/http.py` enforces SEC host/path allowlists, configured User-Agent,
timeouts, bounded response reads, retry rules, and the process-wide limiter.
`us_sec/discovery.py` resolves submissions metadata into immutable filing
candidates and applies domestic/FPI/amendment policy. `us_sec/package.py`
selects only the primary document and filing-local XBRL members, validates safe
relative names and bytes, and commits `packages/sha256/<prefix>/<package_sha>`.
`us_sec/runtime.py` provides the JSON subprocess boundary; the runner uses only
stdlib HTTP/HTML/XML facilities and never executes filing content or remote
subresources.

### Registry, planner, and artifacts

Registry schema v2 is additive: v1 CN/HK tables remain readable, source package
and member tables are added idempotently, and SEC package bindings/parsed runs
are stored in separate additive tables where the v1 PDF foreign-key contract
cannot safely be made nullable. `SecIncrementalPlanner` implements
`REUSE_DATA → PARSE_LOCAL → DISCOVER_AND_ACQUIRE` for validated package runs.

SEC artifacts are stored under package-keyed project-relative directories and
contain manifest, virtual pages, sections, reconstructed HTML tables, raw facts,
evidence, and validation. Every source locator includes package/member identity;
raw facts retain the filing QName and unresolved references are review/blocking
issues rather than guessed values.

### P8 and CLI

The catalog gets an additive SEC source-kind entry. Existing PDF entries continue
through the current loaders. The P8 service loads SEC artifacts lazily and maps
the same list/get/search/pages/sections/tables/facts/evidence/validation tools to
virtual HTML pages with `pagination_kind=VIRTUAL_HTML`. It never calls the SEC
provider or network.

The CLI accepts US Q1/Q2/Q3/FY and `--cik` only when the gate is enabled; CN/HK
period parsing and runtime behavior remain unchanged. US ingest uses the SEC
package parser, validation, Registry, and catalog publication only when there
are no blocking validation issues.

## Verification boundary

Focused tests cover identity/period/amendment/FPI rules, HTTP guards and retry
limits, deterministic package hashes and drift, registry migration, planner
reuse, HTML/iXBRL/table/evidence round-trips, P7/P8 SEC reads, CLI gate/Q2
parsing, and no-AI/no-arbitrary-URL boundaries. The existing CN/HK suite is run
with the project-root-local short basetemp convention. Live SEC smoke is only
attempted when a monitored contact email is explicitly configured.

## Resolved implementation decisions

- Filing year/period selection uses SEC `reportPeriod` as the source-of-truth
  candidate field. The requested fiscal year must match the report-period year;
  filing date is metadata and a deterministic tie-break only after exact form,
  period, and amendment class matching. Multiple same-slot originals or an
  original plus `/A` are review conflicts, never guessed by recency or filename.
- Original and amended filings remain separately acquirable packages, but an
  unresolved required-slot conflict returns `REVIEW_REQUIRED` and does not bind
  an active package or publish a P8 catalog entry.
- `package_sha256` is the US source identity. The P8-compatible
  `document_sha256` field is populated with that same value for SEC entries and
  is accompanied by an explicit `package_sha256`; no second mutable document
  identity is invented. Parsed runs include parser/normalizer versions so later
  versions can coexist.
- The default package includes the primary document, every filing-local XBRL
  member selected by role/suffix, and members explicitly referenced by the
  primary document. An absent required referenced member is a blocking package
  issue; unrelated exhibits are not downloaded by default.
- P7 classifies missing/invalid primary HTML, malformed package/member hashes,
  unsafe paths, source drift, and unresolvable required table/evidence locators
  as blocking. Unresolved context/unit references and amendment conflicts are
  review issues with raw evidence retained. A review result is never relabeled
  PASS; unresolved active conflicts still suppress P8 publication.
- 20-F and 40-F are both valid FPI annual forms. If both are present for the
  same annual slot, selection is review-required. The candidate does not expose
  automatic 6-K quarterly mapping; an explicit 6-K acquisition API may preserve
  the form as an event document without assigning it Q1/Q2/Q3 semantics.
- Virtual pages use `VIRTUAL_HTML_V1`: normalized source blocks are grouped in
  source order with at most 48 blocks and 6000 UTF-8 characters per page. The
  normalizer version is persisted in the artifact and parsed-run identity;
  existing compatible data remains reusable unless a defect rule invalidates it.
- Inline XBRL visible/hidden facts, nonnumeric facts, nil facts, continuations,
  duplicates, and non-numeric parse failures are retained as raw records. Facts
  are never silently deduplicated or numerically guessed; validation reports
  duplicate/parse/reference issues explicitly.
- The development gate applies to SEC acquisition, CLI, catalog loading, and
  P8 SEC reads. CN/HK P8 reads remain unchanged. A SEC catalog cannot make US
  visible in a default accepted process.
- `--cik` may be used without `--ticker` and uses a CIK display alias. When both
  are supplied, ticker resolution must agree with the explicit CIK; disagreement
  fails closed instead of silently ignoring the ticker.

## Builder handoff

The remaining work is implementation and focused verification against
`design/26-p11-sec-provider-design.md`, `design/27-p11-implementation-plan.md`,
and `development/147-p11-us-scope-reopening-authorization.md`. Any conflict
that would require destructive Registry migration, arbitrary network/filesystem
access, accepted CN/HK mutation, or remote AI is a design issue and stops the
candidate rather than being guessed around.
