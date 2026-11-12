# 188 — P11 Full Design / Code Consistency Review 3

Status: **CHANGES_REQUIRED — NEW FORMAL TEST PLAN NOT AUTHORIZED**

Date: 2026-11-12

Review owner: ChatGPT independent design/code review

Corrected design baseline:

`09e3174b7e19a60cc5955862670fac8931af67db`

Exact reviewed production candidate:

`c7bcfa6bd3b01a769cc5e3063378c68c7a4dd67b`

Candidate development evidence:

`development/187-p11-issue-134-repair-evidence.md`

Evidence commit:

`d320583ce28841cf5daf975ce239dbffd64c5da6`

The focused P11-ISSUE-134 review previously found that repair correct. This document is a fresh, broader design/code consistency review performed before issuing any new Formal Test Plan. It deliberately does not carry forward a prior local REVIEW_PASS where a full-design check reveals additional defects.

## 1. Review authority and scope

The code was compared against:

- `design/26-p11-sec-provider-design.md`
- `design/27-p11-implementation-plan.md`
- `design/32-p11-us-scope-reopening.md`
- `design/33-p11-post-acceptance-design-correction.md`
- `development/178-p11-full-design-code-consistency-reaudit.md`

Reviewed production surfaces include:

- US identity and ticker mapping;
- form/period policy;
- current discovery/history discovery;
- discovery observations;
- Fair Access / HTTP / subprocess runtime;
- SEC acquisition and package selection;
- raw package storage and provenance;
- Registry v4 and compatibility;
- planner/reuse behavior;
- HTML/iXBRL/XBRL parsing;
- continuation/exclude semantics;
- tables and evidence;
- P7 validation;
- P8 catalog/service;
- report-safe composed MCP services;
- CLI/production enablement;
- P9/P10 compatibility boundary;
- CN/HK compatibility;
- current P11 unit-test contracts.

No production or test code is changed by this review.

## 2. Exact-candidate freeze

Candidate:

`c7bcfa6bd3b01a769cc5e3063378c68c7a4dd67b`

Evidence:

`d320583ce28841cf5daf975ce239dbffd64c5da6`

Candidate → evidence is documentation-only:

`development/187-p11-issue-134-repair-evidence.md`

No post-candidate production/test drift was found before this review.

## 3. Areas materially aligned with the corrected design

The following design areas are materially implemented as intended.

### 3.1 Stable identity / ticker provenance

- US stable identity is `US:CIK##########`.
- Explicit CIK bypasses ticker lookup.
- Online ticker-based acquire/ingest fetches the current official ticker map.
- Cached ticker lookup verifies retained source bytes/SHA, reparses the official bytes, and compares the derivative mapping.
- Local status can use verified cached ticker evidence without network.

Result: **ALIGNED**.

### 3.2 Production enablement

- The feature branch advertises US through `SUPPORTED_MARKETS`.
- US Q2 is accepted without changing CN/HK period semantics.
- Normal US CLI code paths do not require `FFDF_P11_US_DEV`.
- The old feature-gate helper remains present but is not the production authorization path.

Result: **ALIGNED for DC-08**.

### 3.3 Fair Access / HTTP / runtime

- identifying User-Agent/contact gate;
- process-compatible default 8 req/s limiter;
- bounded attempts/backoff;
- 403/429 reason codes;
- bounded Retry-After;
- redirect host validation/cap;
- connect/read/total timeout handling;
- size limits;
- HTTPS/SEC host/path allowlist;
- subprocess uses explicit argv and `shell=False`;
- dedicated SEC runtime remains stdlib-only.

Result: **ALIGNED**.

### 3.4 Acquisition/package after ISSUE-133/134

The current candidate correctly separates:

- recognized EX-101 metadata inclusion;
- deterministic `link:schemaRef` / `link:linkbaseRef` semantic-reference inclusion;
- ordinary browser/static references.

Live developer evidence restored Apple schema/linkbase members while keeping JPEG/static assets absent.

Package SHA remains the canonical member-byte-set identity, while exact source URL ↔ CIK/accession/name provenance is checked separately.

Result: **P11-ISSUE-133 and P11-ISSUE-134 remain fixed in this review**.

### 3.5 Registry/version compatibility

Observed target contracts remain:

- `REGISTRY_SCHEMA_VERSION = 1`;
- `SEC_REGISTRY_SCHEMA_VERSION = 4`;
- discovery observation storage exists;
- v3→v4 migration is additive;
- future/unknown SEC schema shapes fail closed before current-schema mutation;
- CN/HK legacy Registry version remains frozen.

Result: **ALIGNED**.

### 3.6 Fact-source/parser correction

The parser implements:

- `INLINE_XBRL_PRIMARY`;
- `XBRL_INSTANCE_PRIMARY`;
- no HTML+instance logical fact concatenation;
- V5/v2 artifact version;
- continuation chains;
- duplicate/missing/cyclic continuation failures;
- `ix:exclude` logical-value handling;
- ordered source fragments;
- OTHER XML exclusion from the normal fact-source path.

Result: **materially aligned**, subject to the source-authenticity blocker in §7.

### 3.7 DOM table correction

- logical width derives from occupied span positions;
- rowspan/colspan are preserved;
- first-row `td` is not automatically a header;
- header tree is based on actual header cells.

Result: **ALIGNED**.

### 3.8 Incremental online behavior

At the CLI layer, current discovery is invoked before local reuse planning.

Compatible parsed data may skip parser work; an unchanged local package may skip archive-member redownload.

Status remains local-only.

Result: **architecture aligned**, subject to the incomplete-history blocker in §5.

## 4. P11-ISSUE-135 — BLOCKER — P7 discovery-observation semantic trust is incomplete

### Design requirements

Design 26 §9.4 states that retained official discovery source bytes allow the observation to be independently reconstructed.

Design 26 §17 requires P7-US to check at least:

1. accession/CIK/form metadata consistency;
6. discovery observation identity/source-hash integrity;
7. duplicate/conflicting current slot candidates;
8. amendment presence;
9. fact_source_mode validity.

### Candidate behavior

`verify_sec_discovery_observation()` currently verifies:

- company/CIK/year/period identity;
- `state == UNAMBIGUOUS`;
- selected accession string presence/equality with an expected accession;
- source-body Base64/hash integrity;
- candidate fingerprint;
- canonical observation SHA;
- exact supplied-observation vs Registry-row equality.

However it does **not** independently derive the observation semantics.

It does not:

- reconstruct the candidate set by reparsing the retained official submissions/history source bytes;
- prove `observation.candidates` equals the candidates derivable from those source bytes;
- derive state from the candidate list;
- prove an UNAMBIGUOUS observation actually has exactly one non-amended original;
- detect an amendment in the stored candidate list when `state` was rewritten to UNAMBIGUOUS;
- detect multiple original candidates when `state` was rewritten to UNAMBIGUOUS;
- prove `selected_accession` is a member of the candidate list;
- compare the selected candidate form with `package.form`;
- validate the `fact_source_mode` value in P7.

A concrete impossible observation is currently representable and used by some test helpers:

```text
candidates = ()
state = UNAMBIGUOUS
selected_accession = <package accession>
```

The current trust checks can accept this shape when its hashes/Registry values are internally consistent.

Likewise, a candidate list containing an original plus amendment can be rewritten together with a new candidate fingerprint, state, selected accession and canonical observation SHA. The existing verifier proves internal hash consistency, but it does not independently prove the correct slot decision.

### Required repair

P7/discovery verification must fail closed unless it can independently establish the observation semantics.

At minimum:

1. validate every retained discovery source URL as the expected official SEC submissions/history source for the observation CIK;
2. decode and rehash retained source bytes;
3. parse those bytes with the production submissions parser;
4. reconstruct the complete candidate universe represented by those retained sources;
5. run the production slot-discovery rules for the observation FY/period;
6. compare reconstructed canonical candidates exactly with `observation.candidates`;
7. independently derive:
   - NOT_FOUND,
   - AMENDED_VARIANT_PRESENT,
   - SLOT_CANDIDATE_CONFLICT,
   - UNAMBIGUOUS;
8. independently derive selected accession;
9. require the selected accession to exist in the candidate set;
10. bind selected candidate accession/form/primary metadata to the package as required by Design 26 §17;
11. explicitly validate `fact_source_mode` against the reviewed modes and its basic package/source invariant.

Required regressions include a self-consistently rehashed observation containing:

- original + amendment but forged UNAMBIGUOUS state;
- two originals but forged UNAMBIGUOUS state;
- selected accession absent from candidates;
- candidate form differing from package form;
- candidates changed together with recomputed fingerprint/observation SHA;
- source bytes whose reparsed candidates differ from the persisted candidate list;
- invalid fact_source_mode.

Status:

`P11-ISSUE-135 — OPEN / BLOCKING`

## 5. P11-ISSUE-136 — BLOCKER — historical discovery can stop before the complete current candidate set is known

### Design requirement

Design 26 §6.3 requires every online acquire/ingest to:

```text
fetch current submissions/history discovery
→ build the complete current candidate set for the requested slot
→ evaluate amendment/conflict/not-found/unambiguous
→ only then perform reuse planning
```

The design explicitly requires late amendments to invalidate a previously cached original.

### Candidate behavior

In `SecAcquirer._discover_with_candidates()`:

1. current submissions are parsed;
2. if no candidate is found, selected history chunks are iterated;
3. after each history chunk, `discover_filings(...)` is called;
4. the loop executes:

```python
if candidates:
    break
```

This means the first relevant history chunk that yields one candidate ends history discovery.

A deterministic failing scenario is:

```text
history chunk A → original 10-K
history chunk B → same-slot 10-K/A
```

Both chunks are selected as relevant.

After A, `candidates` becomes non-empty and the loop stops.

B is never fetched.

The resulting observation can incorrectly become UNAMBIGUOUS and research-ready.

The same defect applies to two non-amendment candidates split across multiple relevant chunks.

### Additional late-amendment boundary

`_history_chunks_for_year()` currently selects history chunks using filing-date ranges constrained roughly to `fiscal_year ± 1`.

A later amendment belongs to the old report/fiscal slot but may have a much later filing date. A filing-date-only upper bound can therefore exclude the chunk that contains a delayed /A.

The corrected discovery policy must define the minimal history range that is sufficient to prove the **current complete slot candidate set**, not merely the range likely to contain the original filing.

### Required repair

- remove early success termination across relevant history chunks;
- aggregate all required source candidates before slot evaluation;
- define and implement history-chunk selection that cannot miss a later amendment for the requested slot merely because the amendment filing date is later than FY+1;
- retain every source body used in the resulting discovery observation;
- maintain bounded/fail-closed network behavior.

Required regressions:

1. original in first relevant history chunk, amendment in second;
2. first original in one chunk, conflicting second original in another;
3. delayed amendment in a later filing-date chunk outside the current FY±1 upper bound;
4. repeat cached original → current history now contains delayed amendment → no research-ready reuse.

Status:

`P11-ISSUE-136 — OPEN / BLOCKING`

## 6. P11-ISSUE-137 — BLOCKER — public report-safe SEC summary path bypasses the P8 source/discovery trust chain

### Design requirement

Design 26 §19 requires that before serving an SEC bundle, P8 verify package/member provenance against the Registry and verify the full evidence source chain.

Design 32 also requires P8/P9/P10 compatibility: US may become another research market only through the accepted read-only trust boundary.

### Candidate behavior

Normal P8 document/data paths use:

`McpQueryService._bundle()`

For SEC bundles this runs:

`_verify_sec_source_chain(...)`

including Registry package/member provenance, evidence/member verification and exact discovery-observation verification.

Cached SEC bundles are reverified on each access.

However:

`McpQueryService.get_document_summary_internal()`

has a separate SEC branch that directly loads:

- the SEC parsed artifact;
- the P7 validation artifact;

and returns:

- validation status;
- compatibility status;
- reuse eligibility;
- blocking/review/warning counts;
- artifact counts.

It does **not** call `_bundle()` or `_verify_sec_source_chain()`.

This is not a dead private helper. Public MCP tool:

`ffdf_get_company_report_context`

calls report-safe `get_company_report_context()`, which calls `get_document_summary_internal()` and serves these SEC trust/status values.

Therefore after a valid ingest/catalog entry is created, tampering or deleting the Registry discovery observation/package/member provenance can be detected by ordinary P8 bundle access while the report-safe company-context path can still return the previously recorded PASS/reuse state.

### Required repair

Every public/composed SEC-serving path that exposes validation/research status must enforce the same SEC trust boundary.

A straightforward safe option is:

- for SEC, make `get_document_summary_internal()` obtain/verify the SEC bundle through the same source-chain verification path before returning the summary.

If a lighter manifest-only implementation is retained, it must still independently perform every required SEC package/discovery trust check; optimization cannot bypass correctness.

Required regressions:

1. valid SEC company context succeeds;
2. delete exact Registry discovery observation → `ffdf_get_company_report_context` fails closed;
3. tamper discovery source bytes after one successful context read → next context read fails;
4. tamper Registry package/member provenance → context fails;
5. cached report-safe path still revalidates the SEC chain.

Status:

`P11-ISSUE-137 — OPEN / BLOCKING`

## 7. P11-ISSUE-138 — BLOCKER — XBRL / Inline-XBRL source authenticity is based on local tag names rather than reviewed namespaces

### Design requirement

Design 26 §10.1 defines:

- `INLINE_XBRL_PRIMARY` only when the primary contains supported Inline XBRL facts;
- `XBRL_INSTANCE_PRIMARY` only when there is exactly one **verified XBRL instance** suitable for the filing.

DC-05 also requires that generic XML is not XBRL truth.

### Candidate behavior

`_member_role()` classifies an XML member as `XBRL_INSTANCE` when its root local name is merely:

`xbrl`

It does not require the XBRL instance namespace.

The parser then resolves contexts, units and facts using local-name matching.

Similarly, primary Inline fact detection tests local names:

- `nonfraction`;
- `nonnumeric`;

without proving that the element belongs to the supported Inline XBRL namespace.

Consequently a wrong-namespace XML document shaped like:

```xml
<xbrl xmlns="urn:not-xbrl">
  ...
</xbrl>
```

can be classified as the sole XBRL instance candidate, and local-name/contextRef-shaped descendants can enter `XBRL_INSTANCE_PRIMARY`.

Likewise an HTML element with a lookalike local fact name can influence Inline fact-source selection without a reviewed Inline XBRL namespace binding.

### Required repair

Introduce namespace-aware source qualification.

At minimum:

- classify an XBRL instance only when its root is the reviewed XBRL instance QName/namespace;
- reject or classify as OTHER a local-name-only lookalike;
- ensure context/unit extraction for the instance source uses reviewed XBRL/XBRLDI namespaces as appropriate;
- ensure supported Inline XBRL fact/continuation/exclude constructs are recognized only through the supported Inline XBRL namespace binding rather than arbitrary local-name lookalikes;
- preserve evidence locator behavior and existing valid SEC fixtures.

Required regressions:

- wrong-namespace `<xbrl>` cannot become XBRL_INSTANCE_PRIMARY;
- correct XBRL instance namespace still succeeds;
- arbitrary `foo:nonfraction` / lookalike elements do not trigger INLINE_XBRL_PRIMARY;
- supported SEC Inline XBRL namespace still succeeds;
- OTHER XML with local `context/unit` names remains semantically inert.

Status:

`P11-ISSUE-138 — OPEN / BLOCKING`

## 8. P11-ISSUE-139 — SCOPE CONTRACT MISMATCH — explicit Form 6-K acquisition path is absent

### Design scope

Design 32 §4 states for foreign private issuers:

- FY → 20-F or 40-F;
- Form 6-K may be acquired explicitly;
- 6-K must not be auto-mapped to a standardized quarterly slot.

### Candidate behavior

Current `parse_submissions()` drops periodic candidates whose base form is not one of:

`10-K, 10-Q, 20-F, 40-F`

`SecFormPolicy` has no explicit 6-K path.

The US CLI ignores `--filing-type` for SEC discovery and exposes only period-based FY/Q1/Q2/Q3 selection.

Therefore the current provider correctly avoids auto-mapping 6-K to a quarter, but it also has no explicit 6-K acquisition route.

### Review classification

The wording “may be acquired explicitly” is less prescriptive than the required periodic-slot mappings, so this issue is not the primary reason this candidate fails review.

However, it is a frozen scope-contract/code mismatch and must be resolved before the next full-design REVIEW_PASS:

either:

1. implement a deterministic explicit 6-K acquisition path that does not invent a standardized quarterly slot; or
2. issue and freeze an explicit design correction stating that explicit 6-K acquisition is not part of the accepted P11 v1 capability.

Do not silently leave design and implementation contradictory.

Status:

`P11-ISSUE-139 — OPEN / DESIGN-SCOPE RESOLUTION REQUIRED`

## 9. Previously repaired issues

Fresh inspection did not reopen the implementation defects represented by:

- P11-ISSUE-123 — online current discovery occurs before reuse planning at the CLI layer;
- P11-ISSUE-124 — one logical fact-source mode;
- P11-ISSUE-125 — continuation/exclude;
- P11-ISSUE-126 — generic XML is not deliberately swept as XBRL truth;
- P11-ISSUE-127 — ticker provenance/current online resolution;
- P11-ISSUE-128 — package/member provenance;
- P11-ISSUE-129 — logical DOM grid/header semantics;
- P11-ISSUE-130 — production branch enablement without dev flag;
- P11-ISSUE-131 — exact observation/Registry binding exists;
- P11-ISSUE-133 — static/browser assets are not automatically fetched;
- P11-ISSUE-134 — semantic XBRL references no longer depend on semantic SEC index type.

This does not negate the new full-audit defects in §§4–8.

## 10. Test-contract gaps corresponding to the new blockers

Existing green unit counts do not cover the newly identified invariants.

Notably:

- ISSUE-131 tests alter candidates without recomputing all dependent hashes, but do not test a fully self-consistent forged observation decision;
- some valid-observation test helpers use an empty candidate set together with UNAMBIGUOUS/selected accession;
- history tests intentionally enforce fetching only a year-window chunk and do not cover original/amendment split across multiple relevant history chunks;
- no SEC report-safe company-context tamper regression forces the same P8 trust chain;
- no wrong-namespace XBRL-instance/Inline-XBRL authenticity regression exists;
- explicit 6-K acquisition is not tested because no such code path exists.

The recorded developer results remain valid evidence for what those commands tested, but they do not prove the missing design invariants.

## 11. Full-audit verdict

```text
CORRECTED DESIGN BASELINE:
09e3174b7e19a60cc5955862670fac8931af67db

REVIEWED EXACT CANDIDATE:
c7bcfa6bd3b01a769cc5e3063378c68c7a4dd67b

CANDIDATE EVIDENCE COMMIT:
d320583ce28841cf5daf975ce239dbffd64c5da6

ISSUE-133:
CLOSED

ISSUE-134:
CLOSED

NEW P11-ISSUE-135:
OPEN / BLOCKING

NEW P11-ISSUE-136:
OPEN / BLOCKING

NEW P11-ISSUE-137:
OPEN / BLOCKING

NEW P11-ISSUE-138:
OPEN / BLOCKING

NEW P11-ISSUE-139:
OPEN / DESIGN-SCOPE RESOLUTION REQUIRED

FULL DESIGN/CODE CONSISTENCY REVIEW:
CHANGES_REQUIRED

REVIEW_PASS:
NO

NEW FORMAL TEST PLAN:
NOT AUTHORIZED

FORMAL ACCEPTANCE:
NOT RUN FOR THIS CANDIDATE

MAIN MERGE:
NOT AUTHORIZED

P11 DONE:
NO
```

## 12. Required next lifecycle

Do **not** create a Formal Test Plan for `c7bcfa6...`.

The next lifecycle is:

```text
P11-ISSUE-135..139 repair / scope resolution
→ developer regression tests
→ freeze NEW production candidate SHA
→ documentation-only development evidence
→ ChatGPT fresh FULL exact-candidate design/code review
→ only if REVIEW_PASS, create a NEW Formal Test Plan
```

The next repair should be performed as one coherent cycle so that discovery, P7 and P8 trust semantics are re-reviewed together rather than repaired piecemeal.
