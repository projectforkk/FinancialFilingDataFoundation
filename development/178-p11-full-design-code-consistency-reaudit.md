# 178 — P11 Full Design / Code Consistency Re-Audit

Status: **CHANGES_REQUIRED — PRIOR ACCEPTANCE SUSPENDED BEFORE MAIN INTEGRATION**

Audit owner: ChatGPT independent design/code review

Fresh-audit production candidate:

`9b7fcc9fc37a423eaafd1dde762e9c81d475df9e`

Previously recorded acceptance:

`development/177-p11-final-acceptance-review-2.md`

This audit deliberately reopens the design/code comparison before main integration. It does not dispute the command outputs recorded by formal acceptance; it finds important scenarios and semantics that the previous review/test plan did not cover.

## 1. Scope

Re-read and compared against the exact candidate:

- `design/26-p11-sec-provider-design.md`
- `design/27-p11-implementation-plan.md`
- `design/32-p11-us-scope-reopening.md`
- `development/147-p11-us-scope-reopening-authorization.md`

Reviewed exact candidate code across:

- identity/ticker resolution;
- SEC discovery/form/period policy;
- HTTP/Fair Access/security;
- acquisition and package store;
- Registry/planner/incremental behavior;
- HTML/iXBRL/XBRL parser;
- tables/raw facts/evidence;
- P7 validation;
- P8 catalog/service;
- CLI/runtime/feature gate.

No production code is changed by this audit.

## 2. What remains aligned

The following major design areas are materially implemented as designed:

- stable CIK-based US company identity for current ingest;
- explicit CIK bypasses ticker lookup;
- accession-based filing identity;
- official SEC submissions + Archives source chain;
- domestic FY/Q1/Q2/Q3 policy and FPI annual 20-F/40-F policy;
- no automatic quarterly 6-K mapping;
- SEC host/path allowlist;
- monitored User-Agent;
- internal default 8 req/s limiter;
- bounded retry/backoff, redirects and size controls;
- dedicated stdlib SEC subprocess runtime;
- immutable member-byte package store and canonical package SHA;
- additive/versioned SEC Registry with CN/HK v1 preserved;
- virtual HTML pagination;
- deterministic DOM/XML locators;
- raw QName preservation and no canonical metric mapping;
- context/unit/dimension/nil metadata preservation in the covered cases;
- source-aware evidence and member hash verification;
- current artifact compatibility/reuse gates;
- P8 exact tool family and no acquisition inside P8;
- CN/HK public support remains unchanged before integration.

These passed areas remain useful evidence and should not be unnecessarily redesigned.

## 3. P11-ISSUE-123 — BLOCKER — cached reuse can permanently miss a later amendment

### Design requirement

Design 26 §6.3 requires:

`original + /A amendment in one required slot → REVIEW_REQUIRED: AMENDED_VARIANT_PRESENT`.

Design 27 review scope also requires amendment handling to fail closed where ambiguous.

### Candidate behavior

Two cache shortcuts execute before any fresh SEC discovery:

1. `SecAcquirer.acquire()` calls `package_store.find_by_slot(...)` first and immediately returns a local package as `PARSE_LOCAL`.
2. `user_cli._us_plan_slot()` can return `REUSE_DATA` or `PARSE_LOCAL`; `_us_acquire_result()` then returns the local package without constructing an acquirer or fetching submissions metadata.

The formal REUSE_DATA tests deliberately enforce zero HTTP/acquisition calls.

### Defect

Scenario:

```text
T0: issuer files original 10-K
T1: FFDF acquires/parses/marks it research-ready
T2: SEC later files 10-K/A for the same FY slot
T3+: FFDF reruns the same slot
```

At T3, local REUSE_DATA/PARSE_LOCAL wins before discovery. The new amendment is never observed, so the original can remain research-ready indefinitely.

The clean-workspace Kellanova test covers only the case where original and amendment already coexist before first discovery. It does not cover amendment arrival after cache creation.

P7 does not independently recover this: `validate_sec_artifacts()` receives an external `amendment_conflict` boolean and does not discover/Registry-query the remote variant state itself.

### Root design gap

Design 26 §24 says REUSE_DATA/PARSE_LOCAL precedes discovery, while §6.3 requires fail-closed amendment detection. No freshness/revalidation contract resolves those requirements.

### Required repair

Design amendment first:

- separate **immutable package reuse** from **remote filing-metadata freshness**;
- persist discovery-check provenance/as-of timestamp/hash;
- define a bounded SEC submissions revalidation policy (TTL, explicit refresh, or equivalent);
- REUSE_DATA may skip member download and parser work, but must not claim current research readiness beyond the accepted discovery-freshness boundary;
- when a newly observed /A exists, slot becomes REVIEW_REQUIRED immediately;
- add deterministic test: original cached → remote submissions later adds amendment → reuse is denied/review required.

P11-ISSUE-123 is **OPEN / BLOCKING**.

## 4. P11-ISSUE-124 — BLOCKER — no logical fact merge rule between Inline XBRL and extracted XBRL instance

### Design requirement

Design 26 parser architecture is primary HTML/iXBRL first and describes P6 as filing-local raw facts, with source/evidence traceability.

### Candidate behavior

`parse_sec_package()` does:

```python
facts, evidence, issues = _facts(primary_html, ...)
xml_facts, xml_evidence, xml_issues = _xml_facts(package, ...)
facts.extend(xml_facts)
evidence.extend(xml_evidence)
```

There is no semantic dedupe, source precedence, cross-source identity, or alternate-evidence relation.

The accepted live packages contain extracted-instance-style `*_htm.xml` members, and the formal evidence reports:

- Apple FY: 2262 facts;
- Apple Q3: 1538 facts;
- Toyota FY: 6746 facts.

Those counts are consistent with dual-source enumeration, but this re-audit could not independently pair the local live artifacts because the connected PC was offline. The code-level absence of a merge rule is nevertheless confirmed.

### Defect

When the extracted XBRL instance represents the same filing facts already tagged in primary Inline XBRL, P8 exposes two distinct raw_fact_ids for one logical filing fact:

- DOM/hidden fact from primary HTML;
- XML_PATH fact from extracted instance.

P7 only checks raw_fact_id uniqueness, so semantic duplicates pass validation.

### Required repair

Freeze an explicit source rule before coding, for example:

- for Inline-XBRL filings, primary iXBRL is the logical raw-fact source;
- extracted instance may be fallback/cross-check/alternate evidence, not a second logical fact;
- for non-inline filings, XBRL instance is the primary fact source;
- define deterministic semantic fact identity using concept + resolved context + unit + value/nil + precision attributes/dimensions as appropriate;
- retain both source locators where useful without duplicating the logical P6 fact;
- add a fixture containing the same fact in primary iXBRL and XBRL instance and require one logical P8 fact.

Any change in emitted fact semantics requires parser/artifact compatibility invalidation (new normalizer/artifact version as appropriate).

P11-ISSUE-124 is **OPEN / BLOCKING**.

## 5. P11-ISSUE-125 — BLOCKER — Inline XBRL continuation/value semantics are incomplete

### Candidate behavior

Inline facts store:

`continued_at = continuedAt`

but there is no resolver for `ix:continuation` anywhere in the parser and no continuation regression test.

`raw_value` is produced by `_text(node)`, so it contains only text physically under the originating fact node.

The same generic text traversal also has no explicit `ix:exclude` fact-value handling.

### Defect

An `ix:nonNumeric` value split through `continuedAt` is emitted truncated. Text that Inline XBRL excludes from the fact value can also be included in the raw textual value.

This conflicts with design 26 §13's requirement to preserve each fact's raw textual value and source evidence.

### Required repair

- resolve continuation chains deterministically;
- detect missing continuation IDs and cycles;
- apply Inline-XBRL fact-value semantics including exclusion nodes;
- preserve all contributing source locators/evidence fragments;
- add continuation, chained continuation, broken continuation, cycle and exclude fixtures;
- bump parser/normalizer compatibility because fact values change.

P11-ISSUE-125 is **OPEN / BLOCKING**.

## 6. P11-ISSUE-126 — BLOCKER — acquisition over-collects arbitrary XML and parser can use OTHER XML as context/unit truth

### Design requirement

Design 26 §7.3:

- acquire primary document;
- acquire filing-local XBRL members necessary for facts/contexts/units;
- do not download unrelated exhibits by default.

### Candidate behavior

Acquisition selects every archive member ending:

`.xsd | .xml | .xbrl`.

Generic XML that is not an XBRL instance/linkbase is classified `OTHER`.

Then `_contexts_and_units()` explicitly scans both:

`XBRL_INSTANCE` **and** `OTHER` XML/XBRL members.

### Defect

This is both an acquisition-policy deviation and a correctness risk.

A primary iXBRL fact with an unresolved `contextRef=c1` can potentially be resolved from an unrelated OTHER XML attachment that happens to contain a `<context id="c1">`, suppressing the required unresolved-context review issue.

### Required repair

At minimum:

- OTHER XML must never supply XBRL context/unit truth;
- restrict context/unit fallback to verified XBRL instance members;
- define deterministic member inclusion from filing-local XBRL roles/references rather than every XML-family attachment;
- add a negative fixture where unrelated OTHER XML contains colliding context/unit IDs and prove it cannot satisfy a primary fact;
- add acquisition test proving unrelated XML exhibit is not downloaded by default.

P11-ISSUE-126 is **OPEN / BLOCKING**.

## 7. P11-ISSUE-127 — HIGH — cached ticker mapping is not cryptographically bound to official source bytes and has no freshness policy

### Candidate behavior

Ticker snapshot persists both:

- official `source_bytes_b64` + `source_sha256`;
- a separately serialized `mapping`.

`_cached_ticker_resolution()`:

1. reads the serialized `mapping` and selects the CIK from it;
2. separately verifies that `source_bytes_b64` hashes to `source_sha256`;
3. never reparses the verified source bytes and never proves the serialized mapping equals those bytes.

### Defect

The mapping can be modified independently while leaving verified official source bytes/SHA unchanged. FFDF can then report valid provenance SHA while resolving a ticker to a CIK not supported by those bytes.

Additionally, once any valid cache exists, ticker-only resolution can use it indefinitely; there is no refresh/freshness rule even though the design explicitly treats ticker as a non-stable alias.

### Required repair

- derive cached ticker resolution directly from the verified cached source bytes, or compare serialized mapping exactly with a reparsed mapping;
- fail closed on mismatch;
- define ticker-map freshness/revalidation semantics;
- add tampered-mapping and stale/remapped-ticker tests;
- explicit CIK behavior remains unchanged.

P11-ISSUE-127 is **OPEN / HIGH**.

## 8. P11-ISSUE-128 — HIGH — raw package provenance metadata is not fully bound/verified on reload

### Candidate behavior

The design intentionally defines `package_sha256` only over:

- role;
- relative_name;
- member_sha256;
- byte_length.

Therefore source URL, CIK, accession, form and other manifest metadata are outside the package identity hash.

`SecPackageStore.load()` verifies member bytes and reconstructs the manifest, but `SecPackageMember.__post_init__()` only verifies that a source URL is a generally allowlisted SEC Archives URL. It does not prove:

`source_url == archive_member_url(package.cik, package.accession, relative_name)`.

P8 verifies member hashes/evidence locators but does not compare package metadata/source URLs back to a Registry identity record.

### Defect

Local manifest provenance metadata can be altered without changing package SHA/member bytes and can still be self-consistent enough to load.

The bytes remain intact, but the claim about which SEC accession/CIK/URL they came from is weaker than design 26 §7.4/§17's metadata/source-integrity intent.

### Required repair

Without changing the design-defined package SHA formula:

- validate every member source URL against the package CIK + accession + relative_name on package construction/load;
- verify primary_document/form/period metadata policy;
- bind manifest metadata to a persisted manifest hash/provenance record or validate it against immutable Registry package identity before P8 serves it;
- add manifest CIK/accession/source-URL tamper tests.

P11-ISSUE-128 is **OPEN / HIGH**.

## 9. P11-ISSUE-129 — MEDIUM — DOM table structural counts/header classification are not fully span-correct

### Candidate behavior

The parser correctly records per-cell `row_span` and `col_span`, and internally builds an occupied grid.

But table metadata reports:

```python
column_count = max(len(row["cells"]) ...)
value_column_count = max(len(row["cells"]) ...)
```

This counts origin cells, not occupied grid width.

The current test's `colspan=2` is masked because another row happens to contain three separate cells.

Also, every cell in `row_index == 0` is classified as HEADER even if it is a `<td>`.

### Defect

A table whose maximum width is represented only through colspan reports the wrong column count, and a body-only first row can be promoted to a header tree.

This deviates from design 26 §15's row/column count and deterministic header reconstruction requirements.

### Required repair

- compute structural width from the occupied grid/column indexes + spans;
- define `value_column_count` semantics separately;
- infer header role from `th`/scope/header relationships, not unconditional first-row promotion;
- add colspan-only and body-first-row fixtures.

P11-ISSUE-129 is **OPEN / MEDIUM**.

## 10. P11-ISSUE-130 — INTEGRATION BLOCKER — accepted candidate is still hard-coded development-only

This is not a defect in the pre-integration gate itself; design 32 correctly requires development-only behavior before acceptance.

However, the current accepted candidate still contains:

`feature_gate.py → require FFDF_P11_US_DEV=1`

and both CLI identity construction and P8 SEC catalog loading depend on that development gate.

Therefore Gate I1 cannot be completed by merely changing documentation/status/public `SUPPORTED_MARKETS`. Production source behavior must change to introduce the accepted production-enabled state.

The previous acceptance did not test that production-enabled code because it necessarily ran with `FFDF_P11_US_DEV=1`.

### Required process correction

Do not perform an unreviewed enablement edit during merge.

After issues 123–129 are repaired and reaccepted:

- implement production enablement as an explicit reviewed source diff;
- test US CLI and P8 with the development flag absent;
- verify the feature is available only under the intended production capability state;
- rerun CN/HK regression;
- then perform main integration.

P11-ISSUE-130 is **OPEN / INTEGRATION BLOCKER**.

## 11. Lower-priority observations

These do not independently block release but should be tracked:

1. The process-wide rate limiter is shared for clients using the same configured rate; constructing simultaneous clients with different custom rates can leave multiple live limiter instances. Production currently uses the same default rate, so this is not a present release blocker.
2. P8 re-verifies all SEC evidence on cached bundle access, which is safe but potentially expensive for filings with thousands of facts. This is a performance follow-up, not a correctness blocker.
3. SEC catalog legacy fallback can synthesize ticker-based `company_id` for old development fixtures. New ingest writes stable CIK identity; production integration should remove or tightly scope the fallback once migration compatibility no longer requires it.

## 12. Revised design/code verdict

The prior formal evidence remains valid for the scenarios it executed. The problem is incomplete coverage of important design semantics/lifecycle states, not falsified test output.

Current truth after this fresh audit:

```text
P11 FULL DESIGN/CODE RE-AUDIT:

CHANGES_REQUIRED

P11-ISSUE-123:
OPEN / BLOCKING
cached reuse misses later amendment

P11-ISSUE-124:
OPEN / BLOCKING
Inline-XBRL + XBRL-instance logical fact duplication/undefined merge semantics

P11-ISSUE-125:
OPEN / BLOCKING
continuedAt / continuation fact-value semantics incomplete

P11-ISSUE-126:
OPEN / BLOCKING
unrelated XML acquisition/context contamination

P11-ISSUE-127:
OPEN / HIGH
ticker-cache provenance/freshness defect

P11-ISSUE-128:
OPEN / HIGH
package manifest provenance not fully bound on reload

P11-ISSUE-129:
OPEN / MEDIUM
table span/header structural metadata defect

P11-ISSUE-130:
OPEN / INTEGRATION BLOCKER
production-enable path still requires unreviewed source logic

PRIOR ACCEPTANCE_PASS:
SUSPENDED / INSUFFICIENT FOR MAIN INTEGRATION

MAIN MERGE:
NOT AUTHORIZED

P11 PRODUCTION AVAILABILITY:
MUST NOT CHANGE
```

## 13. Required next step

Do not patch these independently without first repairing the design contracts for the ambiguous items.

Recommended next lifecycle:

```text
Design correction:
- amendment/discovery freshness contract
- HTML-vs-instance logical fact source/merge contract
- Inline-XBRL continuation/evidence contract
- production enablement gate contract

Then one implementation repair wave:
- issues 123–129
- focused new regressions
- exact new production candidate

Then:
ChatGPT exact-candidate review
→ new formal acceptance plan
→ live/formal acceptance
→ reviewed production-enable diff
→ main integration
→ closeout
```

No main merge or US availability change is authorized while this audit is open.
