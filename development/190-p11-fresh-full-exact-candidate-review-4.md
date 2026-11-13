# 190 — P11 Fresh Full Exact-Candidate Design / Code Review 4

Status: **CHANGES_REQUIRED — FORMAL TEST PLAN NOT AUTHORIZED**

Date: 2026-11-13

Review owner: ChatGPT independent design/code review

## 1. Exact authority

Original corrected design baseline:

`09e3174b7e19a60cc5955862670fac8931af67db`

Subsequent authoritative P11 v1 6-K design correction / current design freeze:

`4bf644374af3a0585453379fcc185d6464105776`

That commit modifies:

- `design/27-p11-implementation-plan.md`
- `design/32-p11-us-scope-reopening.md`
- adds `design/34-p11-explicit-6k-scope-correction.md`

Exact reviewed production candidate:

`55fc575cdaaeebd8b686ce76120978c714ca1a28`

Developer evidence:

`development/189-p11-full-design-repair-135-139-evidence.md`

Evidence commit:

`21962b8e4748cb8f800ad75be904624508d84ae8`

Prior full review:

`development/188-p11-full-design-code-consistency-review-3.md`

Prior review commit:

`882b76cb082875b6867e3b409674038192675142`

This is a fresh full-design review. Developer PASS claims are evidence only and are not carried forward as review conclusions.

## 2. Candidate freeze / lineage

The candidate is in the expected forward lineage after the prior review and the Design 34 correction.

Candidate → evidence:

`55fc575cdaaeebd8b686ce76120978c714ca1a28`
→
`21962b8e4748cb8f800ad75be904624508d84ae8`

contains only:

`development/189-p11-full-design-repair-135-139-evidence.md`

Therefore:

```text
CANDIDATE → EVIDENCE:
DOCUMENTATION ONLY — PASS

POST-CANDIDATE SOURCE/TEST DRIFT:
NONE FOUND
```

## 3. ISSUE-135 fresh review

Verdict:

`FIXED in the reviewed implementation`

The candidate now independently reconstructs the discovery decision from retained official SEC source bytes.

The verifier:

- requires the exact current submissions URL for the CIK;
- decodes and re-hashes retained source bytes;
- reparses the current submissions document;
- derives the history file inventory from those official bytes;
- requires the retained source set to match the expected source set;
- reparses retained history documents;
- merges official filing candidates with accession metadata-drift detection;
- re-runs production fiscal-slot discovery;
- compares reconstructed canonical candidates to persisted candidates;
- independently derives state;
- independently derives selected accession;
- binds selected accession to package accession;
- binds selected candidate form, primary document and report period to the package;
- recomputes candidate fingerprint;
- recomputes canonical observation SHA;
- compares the observation to the Registry row.

This closes the prior “self-consistent forged observation” weakness.

P7 now also rejects unknown fact-source-mode strings and invalid zero/nonzero fact combinations.

The remaining source-mode semantic consistency defect found in this review is separately recorded as P11-ISSUE-143 below.

## 4. ISSUE-136 fresh review

Correctness verdict:

`CORE LATE-AMENDMENT / COMPLETE-CANDIDATE BUG FIXED`

The previous early-success history break is gone.

Online discovery now aggregates candidates from every selected history chunk before the slot decision is derived.

This fixes the concrete split-history cases:

- original in one chunk + amendment in another;
- multiple originals split across chunks;
- an already-known current candidate no longer suppresses later chunk processing.

The retained observation also includes every source document used by this implementation, allowing P7/P8 reconstruction.

However the repair changes the history-selection policy to “fetch every listed history chunk”, which conflicts with the frozen minimal-history/performance contract. That is recorded separately as P11-ISSUE-142.

## 5. ISSUE-137 fresh review

Verdict:

`FIXED`

For SEC documents, `get_document_summary_internal()` now obtains the summary from:

`self._bundle(normalized)`

rather than directly trusting the parsed/P7 manifests.

The SEC `_bundle()` cache path re-runs `_verify_sec_source_chain()`, so report-safe/company-context reads cannot use a one-time verification as a permanent trust bypass.

The new regressions cover:

- valid summary path;
- Registry discovery source tamper;
- cached re-read after tamper;
- missing Registry observation;
- raw package manifest tamper;
- summary/detail identity agreement.

This aligns the public report-safe composed path with Design 26 §19.

## 6. ISSUE-138 fresh review

Parser/source-authenticity verdict:

`PARSER REPAIR IMPLEMENTED`

The parser now tracks namespace URIs through the HTML DOM and recognizes Inline XBRL constructs by namespace URI rather than only by local name/prefix.

Reviewed behavior now includes:

- supported 2011/2013 Inline XBRL namespaces;
- prefix-independent Inline fact recognition;
- namespace-aware continuation and exclude;
- XBRL contexts/units only from the XBRL instance namespace;
- XBRLDI dimensions only from the XBRLDI namespace;
- XBRL instance root requires the reviewed XBRL instance namespace;
- wrong-namespace local-name lookalikes do not become structured truth;
- custom taxonomy business facts remain allowed under a valid XBRL instance.

The acquisition member-role classifier also now requires the authentic XBRL instance namespace before assigning `XBRL_INSTANCE`.

However the namespace-authentic parser semantics changed the meaning of V5/v2 artifacts without invalidating the old compatibility identity. That is P11-ISSUE-140.

In addition, the primary-document semantic-reference acquisition parser remains prefix-string based rather than namespace-authentic. That is P11-ISSUE-141.

## 7. ISSUE-139 fresh review

Verdict:

`DESIGN-CORRECTED / IMPLEMENTED`

Design 34 is a valid forward design correction in the candidate ancestry.

It explicitly defers accession-level Form 6-K acquisition from P11 v1 and requires deterministic rejection rather than silent quarterly coercion.

The CLI now rejects US:

- `--filing-type 6-K`;
- `--filing-type 6-K/A`;

with:

`P11_UNSUPPORTED_EXPLICIT_6K`

before SEC provider acquisition can proceed.

This resolves the previous Design 32/code contradiction.

For future governance, the current P11 design freeze must be recorded as `4bf644...` (which contains and descends from the earlier corrected design lineage), not as `09e3174...` alone.

## 8. P11-ISSUE-140 — BLOCKER — namespace-authentic parser semantics reuse the pre-repair V5/v2 compatibility identity

### Facts

The candidate still declares:

```text
VIRTUAL_HTML_NORMALIZER_VERSION = VIRTUAL_HTML_V5
SEC_ARTIFACT_SCHEMA = p11-sec-artifacts-v2
```

`sec_artifact_compatibility()` treats that pair as current/compatible.

`_current_reusable_sec_artifacts()` also accepts a stored parsed row when:

- parser version = current `VIRTUAL_HTML_NORMALIZER_VERSION`;
- schema = current `SEC_ARTIFACT_SCHEMA`;
- validation = PASS;
- compatibility = COMPATIBLE;
- blocking count = 0.

`parse_sec_package()` itself returns an existing artifact directory immediately when:

`<package_sha>.VIRTUAL_HTML_V5`

already exists.

### Why this is a real compatibility defect

P11-ISSUE-138 changes parser semantics.

Before this repair, local-name lookalikes could affect:

- whether Inline facts exist;
- which fact-source mode is selected;
- emitted Raw Facts;
- contexts;
- units;
- dimensions;
- continuation/exclude interpretation;
- whether an XML member is a usable XBRL instance.

After the repair, those semantics are namespace-authentic.

Therefore an artifact produced by a prior candidate using the same:

`VIRTUAL_HTML_V5 + p11-sec-artifacts-v2`

identity is not guaranteed to have current semantics.

Yet the new candidate can:

1. classify that previous artifact as compatible;
2. return `REUSE_DATA`; or
3. take a `PARSE_LOCAL` path but have `parse_sec_package()` load the existing V5 directory instead of reparsing.

The namespace-authentic parser may never run.

An isolated fresh Apple smoke does not test this path because it starts from a fresh artifact root.

### Design basis

Design 26 explicitly ties deterministic normalized artifacts to the normalizer version and requires compatibility invalidation when logical fact-source semantics change.

Design 33 established V5/v2 specifically to invalidate prior changed fact semantics.

ISSUE-138 is another semantic change after that V5/v2 baseline.

### Required repair

Freeze a new parser compatibility identity for the namespace-authentic semantics.

The exact version numbers must be recorded in a design correction before or with implementation.

A typical shape would be a new normalizer version and, if the persisted artifact contract requires it, a new artifact schema version.

The minimum requirement is:

- pre-ISSUE-138 V5/v2 parsed artifacts MUST NOT qualify for `REUSE_DATA`;
- `PARSE_LOCAL` must actually run the namespace-authentic parser rather than load the old directory;
- immutable raw SEC packages remain reusable after fresh current discovery;
- old artifacts remain immutable;
- new artifacts are written separately.

Required regression:

```text
create/stage a pre-ISSUE-138 V5/v2 artifact
whose old semantics include a wrong-namespace fact/source

run the current planner/ingest path

expected:
old artifact = INCOMPATIBLE
REUSE_DATA = denied
raw package = reusable
new parser actually executes
new artifact contains namespace-authentic result
old artifact bytes unchanged
```

Status:

`P11-ISSUE-140 — OPEN / BLOCKING`

## 9. P11-ISSUE-141 — BLOCKER — primary semantic-reference acquisition authenticates the “link:” prefix string, not the XBRL linkbase namespace

### Candidate behavior

For XML/XBRL support members, semantic reference discovery checks the XBRL linkbase namespace.

For the primary HTML path, however, `_SemanticReferenceHTMLParser` authorizes a reference when the literal tag string is one of:

- `link:schemaref`;
- `link:linkbaseref`.

It does not track or verify the URI bound to the `link` prefix.

It also treats the literal `xlink:href` attribute name as sufficient without verifying the XLink namespace binding.

Existing semantic-reference positive tests encode this prefix-only behavior: their primary fixtures use `<link:schemaRef>` / `<link:linkbaseRef>` without declaring an authentic `xmlns:link` binding.

### Consequences

A lookalike primary construct such as:

```xml
<link:schemaRef
  xmlns:link="urn:not-xbrl"
  xlink:href="local.xml">
```

can authorize a filing-local download.

If the target bytes themselves happen to be a valid XBRL instance, the later member classifier can promote them to `XBRL_INSTANCE`.

When the primary has no authentic Inline facts, that package can then select `XBRL_INSTANCE_PRIMARY`, even though the acquisition authorization came from a non-XBRL semantic construct.

Conversely, a valid linkbase-namespace `schemaRef` using another prefix is not recognized by the primary semantic-reference parser.

This is inconsistent with the namespace-authentic source rule introduced for ISSUE-138 and with Design 26 §7.3’s requirement that reference-based members be deterministically identified as XBRL support members.

### Required repair

Make primary semantic-reference discovery namespace-aware.

At minimum:

- resolve namespace declarations in the primary HTML;
- identify `schemaRef` / `linkbaseRef` by the reviewed XBRL linkbase namespace URI, independent of prefix;
- validate XLink reference semantics as appropriate rather than trusting an arbitrary `xlink:` prefix spelling;
- preserve same-accession path/host restrictions;
- wrong-namespace lookalikes must not authorize acquisition;
- valid alternate prefixes must work.

Update the ISSUE-134 positive fixtures so that they declare authentic namespaces rather than relying on an unbound `link:` prefix.

Required regressions:

1. valid linkbase namespace + standard prefix → target acquired;
2. valid linkbase namespace + alternate prefix → target acquired;
3. wrong namespace bound to `link` → target not acquired;
4. unbound `link:` lookalike → target not acquired;
5. wrong XLink binding → target not authorized;
6. static/browser references remain zero-fetch;
7. generic XML hyperlink remains rejected.

Status:

`P11-ISSUE-141 — OPEN / BLOCKING`

## 10. P11-ISSUE-142 — DESIGN-CONTRACT BLOCKER — current discovery fetches every historical submissions chunk rather than only the chunks required for the requested slot

### Candidate behavior

`_history_chunks_for_year()` currently:

- receives `fiscal_year`;
- validates all listed history entries;
- selects every history chunk;
- sorts every selected chunk by name.

The fiscal year no longer affects selection.

The observation verifier likewise requires the retained source set to be:

`current submissions + every history file listed by current submissions`.

### Design conflict

Design 26 §6.3 states that online discovery fetches current submissions metadata and:

“only history chunks required for the requested fiscal slot”.

Design 26 §27 separately states:

“submissions discovery should fetch only required history chunks”.

The previous early-break behavior was incorrect because a later relevant chunk could contain an amendment/conflicting candidate.

Fetching the issuer’s entire historical submissions corpus on every online slot request fixes completeness by over-fetching, but it does not satisfy the frozen incremental/minimal-history contract.

For a long-lived issuer this can also make unrelated ancient history or incomplete legacy rows affect every current-slot request.

### Required repair

Define a bounded deterministic history selection that preserves late-amendment correctness without downloading provably irrelevant older history.

The rule must:

- include every chunk that can contain the requested slot’s original/amendment/conflicting accession;
- include later filing-date chunks that can contain delayed amendments;
- conservatively include chunks with insufficient range metadata when necessary;
- exclude chunks that are provably earlier than any filing that can belong to the requested slot;
- never stop merely because one candidate is found;
- keep the online and observation-reconstruction source-selection algorithms identical.

If the project intentionally chooses “fetch all history forever” as the new contract, update/freeze the design first rather than silently contradicting Design 26.

Required regressions include:

- ancient provably irrelevant chunk is not fetched;
- original in an eligible older chunk is fetched;
- amendment in a later chunk is fetched;
- missing-range chunk is handled conservatively;
- online selected source set exactly matches P7 reconstruction expectations;
- repeat current-slot discovery does not regress archive/parser reuse.

Status:

`P11-ISSUE-142 — OPEN / BLOCKING`

## 11. P11-ISSUE-143 — BLOCKER — P7 validates the fact_source_mode label but not its semantic source invariant

### Candidate behavior

P7 now validates that `fact_source_mode` is one of:

- `INLINE_XBRL_PRIMARY`;
- `XBRL_INSTANCE_PRIMARY`;
- `NO_STRUCTURED_FACTS`.

It also rejects:

- `NO_STRUCTURED_FACTS` with facts;
- structured modes with zero facts.

However it does not verify that the persisted facts/evidence actually come from the source required by that mode.

For example, a parsed artifact can claim:

`XBRL_INSTANCE_PRIMARY`

while its facts/evidence are DOM-path facts from the primary HTML and the package contains no selected XBRL instance.

Likewise `INLINE_XBRL_PRIMARY` is not explicitly required by P7 to use only the primary HTML/DOM fact source.

The evidence locators may individually resolve, so locator validation alone does not prove the declared source mode.

### Design basis

Design 26 §10.1 defines source mode as a semantic invariant, not a display label:

- INLINE_XBRL_PRIMARY → P6 logical facts only from primary iXBRL;
- XBRL_INSTANCE_PRIMARY → P6 logical facts only from exactly one verified instance.

Design 26 §17 explicitly requires P7 to check `fact_source_mode validity`.

### Required repair

P7 must verify source-mode semantics.

At minimum:

For `INLINE_XBRL_PRIMARY`:

- every logical Raw Fact is primary-document Inline XBRL;
- evidence/source member is the primary member;
- locator kind matches the Inline/DOM evidence model;
- no logical XML-instance fact rows exist.

For `XBRL_INSTANCE_PRIMARY`:

- exactly one verified authentic XBRL instance is the logical source;
- every logical fact/evidence row points to that instance member;
- locator kind is the XML path model;
- no primary Inline fact rows are emitted as logical facts.

For `NO_STRUCTURED_FACTS`:

- zero logical Raw Facts.

Required negative tests must modify the mode and dependent manifest fields consistently enough that simple enum/hash checks are insufficient, then prove P7 blocks the semantic mismatch.

Status:

`P11-ISSUE-143 — OPEN / BLOCKING`

## 12. Previously repaired issue status

Fresh inspection supports the following current status:

```text
P11-ISSUE-123  CLOSED
P11-ISSUE-124  CLOSED
P11-ISSUE-125  CLOSED
P11-ISSUE-126  CLOSED
P11-ISSUE-127  CLOSED
P11-ISSUE-128  CLOSED
P11-ISSUE-129  CLOSED
P11-ISSUE-130  CLOSED
P11-ISSUE-131  CLOSED
P11-ISSUE-133  CLOSED
P11-ISSUE-134  CLOSED
P11-ISSUE-135  FIXED
P11-ISSUE-136  CORE CORRECTNESS FIXED; superseded by ISSUE-142 contract gap
P11-ISSUE-137  FIXED
P11-ISSUE-138  PARSER AUTHENTICITY FIXED; compatibility gap tracked as ISSUE-140 and acquisition gap as ISSUE-141
P11-ISSUE-139  DESIGN-CORRECTED / IMPLEMENTED
```

No reason was found to reopen the prior fixes outside the newly identified cross-boundary issues.

## 13. Developer evidence interpretation

Recorded developer results:

- focused 135–139: 33 passed;
- US SEC + MCP catalog: 193 passed;
- full unit: 703 passed;
- compileall: PASS;
- git diff --check: PASS;
- Apple FY live smoke:
  - accession `0000320193-25-000079`;
  - 1,131 structured facts;
  - XSD = 1;
  - linkbases = 4;
  - browser/static fetches = 0;
  - P7 PASS;
  - research_ready=true.

These are useful development evidence and remain valid for the scenarios executed.

They do not exercise:

- reuse of a pre-ISSUE-138 V5/v2 artifact;
- wrong/unbound XBRL linkbase prefix in primary semantic-reference acquisition;
- minimal required-history selection;
- semantically mismatched but syntactically valid fact_source_mode.

Therefore they cannot close P11-ISSUE-140..143.

## 14. Fresh full exact-candidate verdict

```text
ORIGINAL CORRECTED BASELINE:
09e3174b7e19a60cc5955862670fac8931af67db

CURRENT DESIGN FREEZE INCLUDING DESIGN 34:
4bf644374af3a0585453379fcc185d6464105776

REVIEWED EXACT PRODUCTION CANDIDATE:
55fc575cdaaeebd8b686ce76120978c714ca1a28

DEVELOPER EVIDENCE COMMIT:
21962b8e4748cb8f800ad75be904624508d84ae8

CANDIDATE → EVIDENCE:
DOCUMENTATION ONLY — PASS

P11-ISSUE-135:
FIXED

P11-ISSUE-136:
CORE CORRECTNESS FIXED

P11-ISSUE-137:
FIXED

P11-ISSUE-138:
PARSER NAMESPACE AUTHENTICITY FIXED

P11-ISSUE-139:
DESIGN-CORRECTED / IMPLEMENTED

NEW P11-ISSUE-140:
OPEN / BLOCKING

NEW P11-ISSUE-141:
OPEN / BLOCKING

NEW P11-ISSUE-142:
OPEN / BLOCKING

NEW P11-ISSUE-143:
OPEN / BLOCKING

FRESH FULL DESIGN/CODE REVIEW:
CHANGES_REQUIRED

REVIEW_PASS:
NO

FORMAL TEST PLAN:
NOT AUTHORIZED

FORMAL ACCEPTANCE:
NOT RUN FOR THIS CANDIDATE

MAIN MERGE:
NOT AUTHORIZED

P11 DONE:
NO
```

## 15. Required next lifecycle

Do not create a Formal Test Plan for `55fc575...`.

The next repair cycle should address P11-ISSUE-140..143 coherently.

Recommended order:

1. freeze compatibility/version correction for namespace-authentic parser semantics;
2. make primary semantic-reference acquisition namespace-authentic;
3. replace fetch-all-history with a design-compliant complete-but-minimal history-source policy, or explicitly correct/freeze the design if fetch-all is intentional;
4. strengthen P7 source-mode semantic validation;
5. run focused + US SEC + full unit + P0-P10 regression;
6. test migration/reparse from pre-ISSUE-138 V5/v2 artifacts;
7. freeze a new production candidate;
8. create documentation-only developer evidence;
9. perform another fresh full exact-candidate review;
10. only after REVIEW_PASS create a new Formal Test Plan.

Any new parser/artifact version must preserve immutable old artifacts and must not modify accepted CN/HK data.
