# 35 — P11 ISSUE-140..143 Coherent Design Correction

Status: **AUTHORITATIVE P11 DESIGN CORRECTION — DEVELOPMENT AUTHORIZED AFTER FREEZE**

Date: 2026-11-13

This design is a forward correction to the active P11 design set:

- `design/26-p11-sec-provider-design.md`
- `design/27-p11-implementation-plan.md`
- `design/32-p11-us-scope-reopening.md`
- `design/33-p11-post-acceptance-design-correction.md`
- `design/34-p11-explicit-6k-scope-correction.md`

It resolves the four blockers identified by
`development/190-p11-fresh-full-exact-candidate-review-4.md`.

It does not alter accepted P0-P10 CN/HK behavior, does not authorize a Formal
Test Plan, does not authorize main integration, and does not declare P11 DONE.

---

## 1. Authority and problem statement

The reviewed production candidate
`55fc575cdaaeebd8b686ce76120978c714ca1a28` correctly repaired the core
correctness defects through ISSUE-139, but fresh full review found four
cross-boundary defects:

- P11-ISSUE-140 — namespace-authentic parser semantics still reuse the
  pre-repair V5/v2 compatibility identity;
- P11-ISSUE-141 — primary-document semantic XBRL references are authorized by
  literal prefix spelling rather than namespace identity;
- P11-ISSUE-142 — complete history discovery currently fetches every history
  chunk, contradicting the frozen incremental/minimal-history contract;
- P11-ISSUE-143 — P7 validates the fact-source-mode label but not the logical
  source invariant represented by that label.

These four defects must be repaired as one coherent compatibility/trust-boundary
cycle.

---

## 2. Version correction

The namespace-authentic parser semantics introduced for ISSUE-138 are a new
normalization contract and MUST NOT share compatibility identity with artifacts
produced before that correction.

The corrected current identities are:

```text
REGISTRY_SCHEMA_VERSION       = 1                     (unchanged)
SEC_REGISTRY_SCHEMA_VERSION   = 4                     (unchanged)
PACKAGE_MANIFEST_SCHEMA       = p11-sec-package-v1    (unchanged)

SEC_DISCOVERY_SCHEMA          = p11-sec-discovery-v2
VIRTUAL_HTML_NORMALIZER_VERSION = VIRTUAL_HTML_V6
SEC_ARTIFACT_SCHEMA           = p11-sec-artifacts-v3
SEC_VALIDATION_SCHEMA         = p11-sec-validation-v3
```

### 2.1 Compatibility consequence

A parsed artifact is current only when both are exact:

```text
parser_version = VIRTUAL_HTML_V6
schema_version = p11-sec-artifacts-v3
```

Every V5/v2 artifact, including an artifact produced by a candidate that already
used those literal version strings but had pre-ISSUE-138 namespace semantics, is
`INCOMPATIBLE`.

V5/v2 directories and bytes remain immutable. The raw SEC package remains
reusable after fresh current discovery. A current reparse writes to the distinct
V6 artifact directory; it must not overwrite or load the old V5 directory.

### 2.2 Validation consequence

P7 source-mode validation changes materially under ISSUE-143. Current P7
validation therefore uses `p11-sec-validation-v3`.

The validation artifact remains a current verification product bound to current
discovery; refreshing it does not authorize mutation of the immutable raw
package or historical parsed artifacts.

### 2.3 Discovery consequence

ISSUE-142 changes the canonical set of retained official submissions/history
source documents. New observations therefore use
`p11-sec-discovery-v2`.

A v1 observation is historical evidence but is not a current discovery
observation for P11 research-ready/reuse decisions. Online acquire/ingest must
create a fresh v2 observation before reuse planning.

---

## 3. ISSUE-141 — namespace-authentic semantic-reference acquisition

### 3.1 Namespaces

The reviewed namespaces are:

```text
XBRL linkbase:
http://www.xbrl.org/2003/linkbase

XLink:
http://www.w3.org/1999/xlink
```

A primary-document semantic reference is authorizing only when:

1. the element local name is `schemaRef` or `linkbaseRef`;
2. the element namespace URI resolves exactly to the XBRL linkbase namespace;
3. the reference attribute local name is `href`;
4. the reference attribute namespace URI resolves exactly to the XLink namespace;
5. the target passes the existing same-accession archive path/host safety rules.

Prefix spelling is irrelevant.

Therefore:

- `link:schemaRef` with authentic namespace is valid;
- `l:schemaRef` with another prefix bound to the same namespace is valid;
- a literal `link:` prefix bound to another URI is invalid;
- an unbound `link:` prefix is invalid;
- a literal `xlink:href` with a wrong/unbound XLink binding is invalid;
- ordinary `href`, `src`, anchors, browser assets, and generic XML hyperlinks
  do not authorize acquisition.

Namespace scope must follow XML namespace declarations on the primary document,
including declarations inherited from ancestors.

### 3.2 XML/XBRL support-member references

The same QName rule applies when scanning accepted XML/XBRL support members:
the element must be in the XBRL linkbase namespace and the `href` attribute
must be in the XLink namespace.

This strengthens the existing XML semantic-reference path without changing
same-accession/path/provenance controls.

---

## 4. ISSUE-142 — complete but minimal history selection

### 4.1 Required invariant

Online discovery and P7 observation reconstruction MUST call the same
deterministic history-selection function.

The selector operates only on the history-file inventory from the authenticated
current submissions document. It must validate duplicate names, maximum count,
date syntax, and non-reversed ranges before selection.

### 4.2 Conservative lower bound

For requested fiscal year `Y`, define:

```text
earliest_possible_slot_filing_date = January 1 of (Y - 1)
```

Rationale:

- an FY candidate used by the current P11 slot rules has a report period in
  fiscal year Y;
- a domestic quarterly candidate for fiscal year Y can have its report period in
  the preceding calendar year;
- a filing cannot legitimately precede the report period it reports;
- delayed amendments/conflicts can occur arbitrarily later and therefore there
  is no safe upper filing-date bound.

The selector therefore has **no upper date cutoff**.

### 4.3 Selection rule

For each validated history chunk:

- if `filingTo` is present and parses to a date strictly earlier than
  `January 1 (Y - 1)`, the chunk is provably too early and MUST be excluded;
- otherwise the chunk MUST be included;
- a missing `filingTo` is insufficient to prove irrelevance and therefore MUST
  be included conservatively;
- missing range metadata is not by itself an error;
- malformed supplied dates, reversed supplied ranges, duplicate names, unsafe
  names, or history count above the deterministic bound fail closed.

All selected chunks are processed; discovery MUST NOT stop after the first
candidate.

This rule intentionally includes later chunks so a delayed amendment or
conflicting filing cannot be hidden by an earlier cached/original filing, while
excluding ancient chunks that are provably earlier than any slot candidate
recognized by the P11 rules.

### 4.4 Observation reconstruction

A v2 observation source set must equal exactly:

```text
current submissions document
+ history chunks selected by the shared selector
```

No extra unselected history body and no missing selected history body is
accepted by P7 reconstruction.

This exact-source-set equality is part of the discovery trust boundary.

---

## 5. ISSUE-143 — P7 fact-source semantic validation

The `fact_source_mode` is a semantic invariant, not descriptive metadata.

P7 must validate the persisted logical facts and their evidence against the
actual package members.

### 5.1 INLINE_XBRL_PRIMARY

P7 requires:

- exactly one package primary document;
- every logical Raw Fact resolves to evidence from that primary member;
- every fact locator/evidence locator is the Inline/DOM locator model, not an
  XML-path logical-fact locator;
- no logical Raw Fact is sourced from an XBRL instance member.

A package may contain XBRL support/linkbase members, but they are not a second
logical fact source.

### 5.2 XBRL_INSTANCE_PRIMARY

P7 requires:

- no primary Inline-XBRL logical facts;
- exactly one package member classified as an authentic XBRL instance;
- every logical Raw Fact and its evidence point to that same instance member;
- logical fact/evidence locators use the XML-path model;
- no DOM/primary-document logical fact is present.

### 5.3 NO_STRUCTURED_FACTS

P7 requires exactly zero logical Raw Facts.

Evidence unrelated to logical Raw Facts may exist only if allowed by the
persisted artifact contract; it cannot be used to manufacture a structured fact.

### 5.4 Fail-closed behavior

A syntactically valid manifest whose mode is changed together with internally
consistent counts/hashes still fails if the facts/evidence/member/locator
semantics do not satisfy the selected mode.

The reason is a blocking `P11_FACT_SOURCE_MODE_INVALID` (or the exact existing
reviewed reason code mapped to that invariant).

---

## 6. Shared trust and compatibility boundaries

The repair MUST preserve all previously accepted/repaired P11 boundaries:

- stable CIK identity and authenticated ticker mapping;
- fresh online discovery before reuse planning;
- amendment/conflict fail-closed behavior;
- immutable raw package and exact source URL provenance;
- no browser/static subresource sweep;
- EX-101 and authentic semantic XBRL support acquisition;
- namespace-authentic Inline XBRL and XBRL instance parsing;
- continuation/exclude semantics;
- DOM span/header semantics;
- SEC report-safe/P8 source-chain revalidation;
- explicit 6-K/6-K/A deterministic defer;
- no acquisition/network in P8;
- no remote AI/LLM call in deterministic production;
- no CN/HK/P0-P10 behavior change.

---

## 7. Required executable contracts

The repair is incomplete unless tests map design → implementation → positive
case → negative/tamper case → compatibility/migration case.

### ISSUE-140

Required:

- historical pre-ISSUE-138 V5/v2 row/artifact is incompatible;
- it cannot trigger `REUSE_DATA`;
- `PARSE_LOCAL` actually executes V6;
- raw package is reused without member redownload;
- V6/v3 artifact is separate;
- old V5/v2 bytes remain unchanged;
- subsequent V6/v3 run can reuse current parsed data.

### ISSUE-141

Required:

- authentic standard prefix succeeds;
- authentic alternate prefixes succeed;
- wrong linkbase namespace fails to authorize;
- unbound lookalike fails;
- wrong/unbound XLink namespace fails;
- ordinary HTML/static references remain zero-fetch;
- generic XML hyperlinks remain non-authorizing.

### ISSUE-142

Required:

- ancient chunk ending before Y-1 is not fetched;
- eligible older chunk is fetched;
- later amendment chunk is fetched;
- missing-range chunk is included conservatively;
- malformed/reversed ranges fail closed;
- all selected chunks are aggregated before slot decision;
- online selected source set equals P7 reconstructed expected source set;
- repeat discovery still permits immutable package/parser reuse when accession is
  unchanged.

### ISSUE-143

Required:

- valid Inline mode passes;
- valid one-instance mode passes;
- valid no-structured-facts mode passes;
- Inline mode with XML-instance facts/evidence blocks;
- instance mode with DOM/primary facts/evidence blocks;
- instance mode without exactly one authentic instance blocks;
- instance mode whose facts point to a different member blocks;
- no-structured mode with a logical fact blocks;
- tampered mode/count/hash combinations cannot bypass semantic validation.

---

## 8. Development and lifecycle gates

After this design correction is committed, the authorized sequence is:

```text
IMPLEMENT 140–143
→ focused development tests
→ complete tests/unit/us_sec
→ full tests/unit regression
→ focused P0–P10 compatibility regression
→ compile/static checks
→ live developer smoke
→ freeze exact production candidate
→ documentation-only developer evidence
→ STOP
→ fresh full exact-candidate review
```

A Formal Test Plan remains forbidden until the new fresh full review returns
`REVIEW_PASS`.

No main merge, acceptance declaration, history rewrite, force push, destructive
reset/clean, or amendment of historical candidate/evidence commits is authorized.
