# 27 — P11 US SEC Provider Implementation Plan

Status: **DESIGN 40 FROZEN — DEVELOPMENT AWAITING CHATGPT AUTHORIZATION**

Detailed design:
`design/26-p11-sec-provider-design.md`

Scope contract:
`design/32-p11-us-scope-reopening.md`

Post-acceptance correction authority:
`design/33-p11-post-acceptance-design-correction.md`

Explicit 6-K scope correction:
`design/34-p11-explicit-6k-scope-correction.md`

Review 4 repair correction:
`design/35-p11-repair-140-143-design-correction.md`

Review 5 trust-boundary correction:
`design/36-p11-review5-trust-boundary-correction.md`

Review 5 freeze consistency and Raw Fact binding correction:
`design/37-p11-review5-freeze-consistency-and-raw-fact-binding.md`

Review 6 revalidation planner correction:
`design/38-p11-review6-revalidation-planner-correction.md`

Formal-Test-4 ticker snapshot observation identity correction:
`design/39-p11-ticker-snapshot-observation-identity.md`

Formal-Acceptance-5 SEC complete-submission source provenance correction:
`design/40-p11-sec-complete-submission-source-provenance.md`

Review 5 exact-candidate result:
`development/192-p11-fresh-full-exact-candidate-review-5.md = CHANGES_REQUIRED`

Re-audit:
`development/178-p11-full-design-code-consistency-reaudit.md`

## 1. Execution principle

The previous P11 acceptance cycle is historical evidence only. It does not authorize
main integration after the re-audit/design correction.

The current lifecycle is:

```text
DESIGN-ONLY COMMIT/FREEZE
→ CHATGPT DESIGN REVIEW
→ DEVELOPMENT INSTRUCTION
→ PC AGENT IMPLEMENTATION
→ DEVELOPMENT TESTS
→ EXACT PRODUCTION CANDIDATE FREEZE
→ DEVELOPMENT EVIDENCE
→ CHATGPT FRESH FULL EXACT-CANDIDATE REVIEW
→ only after REVIEW_PASS:
   FORMAL TEST PLAN
→ FORMAL ACCEPTANCE
→ MAIN MERGE / CLOSEOUT
```

The merge-ready candidate must already contain production US behavior. No production
logic is added after acceptance. Design and implementation must not first appear
together in one production candidate commit.

Development is currently blocked pending ChatGPT review and authorization of
Design 37.

## 2. Roles

### 2.1 PC Agent

PC Agent must:

1. read the corrected design baseline completely;
2. implement the explicitly authorized current-cycle issue scope as one coherent repair;
3. preserve accepted CN/HK behavior;
4. add deterministic regression tests for every repaired issue;
5. produce one exact merge-ready candidate SHA;
6. stop after candidate/evidence push;
7. execute formal tests only after ChatGPT reviews that exact candidate and issues a
   new formal plan.

PC Agent must not alter the corrected design contract without a STOP/design issue.

The current post-Formal-Acceptance-5 development cycle is limited to:

```text
ISSUE-148 implementation
```

ISSUE-148 is the complete-submission authoritative-source and provenance
correction frozen by Design 40.

`ISSUE-140` through `ISSUE-147` are fixed and require regression
preservation only. Historical ISSUE-123..139 remain historical and must not be
erased or silently reopened.

Design 40 keeps package manifest v1, parser V6, parsed artifact v2, discovery
v1, and existing P11 reason codes. It introduces source-container/provenance
schemas, upgrades SEC Registry to v5, and upgrades validation to v4.

### 2.2 ChatGPT

ChatGPT owns:

- corrected design decisions;
- exact-candidate code/design review;
- REVIEW_PASS / CHANGES_REQUIRED;
- formal test-plan authoring;
- independent evidence verification;
- ACCEPTANCE_PASS / ACCEPTANCE_FAILED.

### 2.3 GitHub

GitHub is the shared source of truth.

Local-only claims, screenshots or uncommitted artifacts are not acceptance evidence.

## 3. Gate S0 — Corrected Design Freeze

Before repair code changes, freeze the exact commit containing:

- `design/26-p11-sec-provider-design.md`;
- `design/27-p11-implementation-plan.md`;
- `design/32-p11-us-scope-reopening.md`;
- `design/33-p11-post-acceptance-design-correction.md`;
- `design/34-p11-explicit-6k-scope-correction.md`;
- `design/35-p11-repair-140-143-design-correction.md`;
- `design/36-p11-review5-trust-boundary-correction.md`;
- `design/37-p11-review5-freeze-consistency-and-raw-fact-binding.md`;
- `design/38-p11-review6-revalidation-planner-correction.md`;
- `design/39-p11-ticker-snapshot-observation-identity.md`;
- `design/40-p11-sec-complete-submission-source-provenance.md`.

Record:

```text
corrected_design_baseline_sha = exact final design-freeze commit returned by this task
previous_production_candidate_sha = f1cc76889718e06fdbdc46926e2b207b740a96e3
starting_branch
starting_head
```

The exact new `corrected_design_baseline_sha` is recorded in the PC Agent
result and later development evidence; it must not be guessed or inserted
before the final design-freeze commit exists.

No old ACCEPTANCE_PASS is carried forward.

## 4. Gate D1 — One-Pass Repair Development

The repair wave covers all open issues from the re-audit.

### 4.1 ISSUE-123 — discovery freshness / late amendment

Implement:

- current submissions/history discovery before online reuse planning;
- immutable discovery observation artifact + Registry persistence;
- delayed-amendment detection after original package/artifact already exists;
- fail closed when current discovery cannot be established;
- local-only status with explicit discovery-as-of metadata.

Repeat online ingest may skip archive downloads/parser work, but must not skip
discovery metadata.

### 4.2 ISSUE-124 — one logical fact source

Implement explicit:

- `INLINE_XBRL_PRIMARY`;
- `XBRL_INSTANCE_PRIMARY`.

Never concatenate both logical fact universes.

Expose `fact_source_mode` in artifacts/validation/P8.

### 4.3 ISSUE-125 — continuation/exclude semantics

Implement deterministic Inline XBRL continuation chains, exclusion handling,
multi-fragment evidence, missing/duplicate/cycle failures and regression fixtures.

### 4.4 ISSUE-126 — XBRL member allowlist / semantic isolation

Remove generic XML sweep behavior.

Only deterministic XBRL support members may enter XBRL semantic processing.
`OTHER` XML must never satisfy fact/context/unit resolution.

### 4.5 ISSUE-127 — ticker provenance

Current online ticker resolution must use current official source bytes.
Cached resolution must reparse verified bytes; serialized derivative mapping cannot
be trusted independently.

### 4.6 ISSUE-128 — package provenance

Keep the package SHA formula unchanged.

Add exact source URL ↔ CIK/accession/relative-name verification and package/member
Registry provenance comparison in P7/P8.

### 4.7 ISSUE-129 — DOM table grid/header correctness

Compute logical width from occupied span grid and build header metadata from real
header cells/span coverage.

### 4.8 ISSUE-130 — production enablement

The merge-ready candidate must:

- not require `FFDF_P11_US_DEV=1` for normal US CLI/P8;
- contain the intended public supported-market/capability declarations;
- still be isolated on the feature branch until acceptance.

Formal tests must run with the development flag absent.

### 4.9 ISSUE-139 — explicit Form 6-K scope

Explicit Form 6-K acquisition is deferred from P11 v1 by
`design/34-p11-explicit-6k-scope-correction.md`. The implementation must reject
`--filing-type 6-K`/`6-K/A` deterministically and must not coerce or silently ignore
that request. A future accession-level 6-K contract requires a new design review.

## 5. Required compatibility/version changes

Target constants:

```text
REGISTRY_SCHEMA_VERSION = 1
SEC_REGISTRY_SCHEMA_VERSION = 5

PACKAGE_MANIFEST_SCHEMA = p11-sec-package-v1
SEC_SOURCE_CONTAINER_SCHEMA = p11-sec-source-container-v1
SEC_PACKAGE_SOURCE_PROVENANCE_SCHEMA = p11-sec-package-source-v1

SEC_DISCOVERY_SCHEMA = p11-sec-discovery-v1
VIRTUAL_HTML_NORMALIZER_VERSION = VIRTUAL_HTML_V6
SEC_ARTIFACT_SCHEMA = p11-sec-artifacts-v2
SEC_VALIDATION_SCHEMA = p11-sec-validation-v4
```

Required behavior:

- SEC Registry v4 → v5 additive/idempotent migration;
- unknown future SEC schema fails closed before mutation;
- CN/HK `user_version=1` and accepted rows remain unchanged;
- package manifest v1 and package SHA formula remain unchanged;
- direct archive-member responses no longer supply package member bytes;
- complete-submission text is the current authoritative source container;
- new container/provenance artifacts are immutable and replayable;
- legacy packages remain audit-readable but are current-reuse-ineligible until
  fresh complete-submission provenance attestation succeeds;
- same-byte re-attestation may reuse V6/v2 parsed data as local input;
- validation-v3 cannot qualify for current reuse;
- validation-v4 binds package SHA plus package-source provenance SHA;
- no validation-v4 → v3 fallback;
- current validation-v4 artifacts use a deterministic schema-versioned path;
- no destructive raw-store/package migration.

## 4.10 Review 5 — Design 37 final design freeze

Design 36 is the Review 5 trust-boundary correction that established the
ISSUE-142/143 residual contract. Design 37 is the latest/current design
authority and supersedes Design 36 where Design 37 adds or corrects Review 5
freeze semantics. The current implementation must follow Design 37.

The exact-candidate Review 5 result is `CHANGES_REQUIRED`. The Design 37
final-freeze review is recorded in
`development/194-p11-design37-final-freeze-review-result.md`.

Current issue disposition:

```text
ISSUE-140 = FIXED
ISSUE-141 = FIXED
ISSUE-142 = DESIGN FROZEN / IMPLEMENTATION REQUIRED
ISSUE-143 = DESIGN FROZEN / IMPLEMENTATION REQUIRED
ISSUE-144 = GOVERNANCE CORRECTED
ISSUE-145 = DESIGN FROZEN / IMPLEMENTATION REQUIRED
```

The current Review 5 design freeze requires the next implementation to:

- fail closed for every malformed or unsafe `filings.files` descriptor;
- require strict `YYYY-MM-DD` history range syntax without coercion,
  truncation, or trailing-garbage acceptance;
- retain the shared complete-but-minimal history selector and conservative
  handling of missing ranges;
- replay every logical fact's context/unit references from immutable source
  nodes, including actual source-node reference equality and same-member
  context/unit resolution;
- independently replay the Raw Fact semantic payload and compare its raw value,
  QName, metric identity, source attributes, locator, fragment/continuation
  chain, and deterministic numeric candidate against the authoritative source;
- reject authentic XBRL instance bytes whose package role is inconsistent;
- preserve the `NO_STRUCTURED_FACTS` zero-fact/evidence invariant.

The Raw Fact semantic mismatch reason is frozen by Design 37 §4.6 as
`P11_RAW_FACT_SOURCE_MISMATCH` with `BLOCKING` severity. The implementation
must not invent or rename reason codes.

Historical Design 37 version contract (superseded for current execution by §5 and Design 40):

```text
SEC_DISCOVERY_SCHEMA = p11-sec-discovery-v1
VIRTUAL_HTML_NORMALIZER_VERSION = VIRTUAL_HTML_V6
SEC_ARTIFACT_SCHEMA = p11-sec-artifacts-v2
SEC_VALIDATION_SCHEMA = p11-sec-validation-v3
SEC_REGISTRY_SCHEMA_VERSION = 4
```

The validation schema changes because stronger source-node replay and Raw Fact
binding change validation acceptance semantics. V6 parsed artifacts remain
usable as local parse input, old validation-v2 results cannot qualify for
`REUSE_DATA`, and immutable raw SEC packages remain reusable. No development
implementation is authorized until ChatGPT reviews Design 37.

Formal Test Plan remains:

```text
NOT CREATED
NOT AUTHORIZED
```

## 4.11 Review 5 development verification matrix

These are development tests, not Formal Acceptance. They may be implemented only
after ChatGPT authorizes Design 37.

### ISSUE-142 residual history validation

The focused suite must cover:

```text
filings.files absent → valid empty inventory
filings.files non-list → BLOCK
descriptor non-object → BLOCK
name missing → BLOCK
name non-string → BLOCK
name empty → BLOCK
unsafe name → BLOCK
duplicate normalized name → BLOCK
filingFrom non-string → BLOCK
filingTo non-string → BLOCK
trailing date garbage → BLOCK
invalid calendar date → BLOCK
reversed range → BLOCK
missing ranges → conservatively selected
ancient provably irrelevant → excluded
late amendment range → selected
all descriptors validated before first history fetch
online source set == P7 reconstruction source set
```

The validated-before-fetch fixture must include one apparently selectable valid
descriptor and one malformed descriptor, and must prove history fetch count is
zero before the blocking error.

### ISSUE-143 source-node replay

The focused suite must cover:

```text
valid Inline source chain → PASS
valid instance source chain → PASS
fact context_ref tamper → BLOCK
fact unit_ref tamper → BLOCK
persisted context semantic payload tamper → BLOCK
persisted unit semantic payload tamper → BLOCK
context/unit present only in another member → BLOCK
authentic XBRL instance bytes with OTHER/wrong role → BLOCK
two authentic instance roots across package members → BLOCK
DOM fact in instance mode → BLOCK
XML fact in Inline mode → BLOCK
```

### ISSUE-145 Raw Fact semantic binding

The focused suite must cover both source modes where applicable:

```text
fact raw_value tamper while evidence remains valid → BLOCK
fact raw_qname tamper while evidence remains valid → BLOCK
raw_metric_name tamper → BLOCK
parsed_numeric_candidate tamper → BLOCK
decimals/precision/scale/sign/nil source-attribute tamper → BLOCK as applicable
fact fragment_hash differs from evidence/source → BLOCK
fact source_fragments differ from evidence/source continuation chain → BLOCK
fact/evidence locator divergence → BLOCK
```

### Validation migration

The suite must prove:

```text
existing V6 / artifacts-v2 + validation-v2
→ REUSE_DATA denied

same raw package + same V6 parsed artifact
→ no parsed artifact mutation required
→ P7 validation-v3 executes
→ valid result becomes reusable only after v3 PASS
```

Old validation-v2 artifact bytes remain immutable.

### Historical validation-v3 persistence and migration regression

The development suite must also prove:

```text
legacy flat validation-v2 exists
→ hash validation.json and issues.jsonl before migration

current validation-v3 absent
→ REUSE_DATA denied

same V6/v2 parsed artifact reused as local input
→ parser does not rerun solely because validation is old

P7 v3 executes
→ current result path =
   p7/<package_sha256>/p11-sec-validation-v3/

after v3:
legacy validation-v2 validation.json hash unchanged
legacy validation-v2 issues.jsonl hash unchanged

v3 validation.json schema_version =
p11-sec-validation-v3

v3 PASS
→ historical Design-37 reuse eligibility restored

under Design 40 current runtime:
→ v3 alone is NOT current-reuse-eligible
→ current provenance + validation-v4 are required

v3 missing + valid v2 present
→ CLI/reuse/P8 must not accept v2 as current

v3 corrupt + valid v2 present
→ fail closed
→ no fallback to v2

v3 present + valid
→ CLI / ingest / P8 resolve the same current validation artifact

fresh discovery refresh
→ current v3 replacement is atomic
→ no partial current artifact is visible
```

The implementation must include a regression proving that current production
call sites do not independently hard-code the legacy flat validation path.

## 4.12 Review 6 — validation-only planner correction

Design 38 is the latest/current authority for validation-v3 migration planning.

After fresh current discovery:

```text
compatible parsed + current reusable v3
→ REUSE_DATA

compatible parsed + v3 absent
→ REVALIDATE_LOCAL

compatible parsed + valid current v3 not reuse_eligible
→ REVALIDATE_LOCAL

no compatible parsed + local package
→ PARSE_LOCAL

no local package
→ DISCOVER_AND_ACQUIRE
```

A present but corrupt current v3 fails closed and must not fall back to legacy
v2 or be silently overwritten as migration.

`REVALIDATE_LOCAL` must execute P7 v3 against the existing parsed artifact
without invoking the parser and must refresh current Registry validation fields.

Required development tests are frozen by Design 38.

## 4.13 Formal-Test-4 correction — ticker snapshot observation identity

Design 39 is the latest/current authority for ticker-map persistence.

The implementation must distinguish:

```text
source identity
!=
retrieval observation identity
```

New online snapshots use
`ticker-map/observations/<ticker_snapshot_id>.json`; legacy
`ticker-map/<source_sha>.json` files remain read-only compatibility evidence.

Repeated identical source bytes at different retrieval times are valid separate
observations and must not raise `P11_SOURCE_DRIFT`.

Local-only cached ticker resolution must use the newest verified snapshot only,
not combine mappings across historical snapshots.

Required development tests are frozen by Design 39.

## 4.14 Formal-Acceptance-5 correction — authoritative complete-submission source

Design 40 is the latest/current authority for SEC package byte provenance.

Normal current package acquisition must:

```text
current discovery
→ exact complete-submission .txt fetch
→ strict byte-oriented SGML document inventory
→ deterministic document payload slices
→ package member bytes
→ immutable package
→ immutable package-source provenance
```

Direct individual member responses and index.json are not package byte sources.

New storage/provenance contract:

```text
PACKAGE_MANIFEST_SCHEMA = p11-sec-package-v1
SEC_SOURCE_CONTAINER_SCHEMA = p11-sec-source-container-v1
SEC_PACKAGE_SOURCE_PROVENANCE_SCHEMA = p11-sec-package-source-v1
SEC_REGISTRY_SCHEMA_VERSION = 5
SEC_VALIDATION_SCHEMA = p11-sec-validation-v4
```

Legacy unattested packages remain audit-only until fresh provenance attestation.

The old same-accession package conflict rule is migration-aware: an unattested
legacy package may coexist with exactly one current-source-attested package.

The next Formal Test must also restore the complete Plan-208 ISSUE-147
acceptance-only observation matrix.

Required development and live-smoke tests are frozen by Design 40.

## 6. Candidate commit rules

Production candidate commit contains only implementation + tests required by the
corrected design.

Do not mix formal test evidence into the candidate commit.

Required development evidence must record:

- corrected design baseline SHA;
- previous candidate SHA;
- exact new candidate SHA;
- changed production/test files;
- Registry migration;
- parser/artifact/validation versions;
- development test commands/results;
- explicit issue-by-issue closure matrix;
- explicit CN/HK non-mutation statement.

After the candidate commit, production/test source is frozen pending ChatGPT review.

## 7. Gate R1 — Exact-Candidate Review

ChatGPT re-reviews the exact candidate from Git.

Mandatory review points:

- online discovery occurs before reusable-local return;
- late amendment cannot bypass discovery;
- discovery snapshots are immutable/provenanced;
- ticker mapping is derived from verified bytes;
- only one logical fact-source mode emits P6 facts;
- extracted instance does not duplicate Inline XBRL facts;
- continuation/exclude semantics and source fragments are correct;
- OTHER XML cannot supply contexts/units/facts;
- member source URL is bound to CIK/accession/name;
- P7 consumes discovery observation rather than a free boolean;
- P8 verifies Registry/package/evidence chain and performs no network;
- DOM table width/header tree is span-correct;
- version bumps are complete and old artifacts fail compatibility safely;
- US works without `FFDF_P11_US_DEV`;
- CN/HK/P9/P10 behavior remains unchanged.

Verdict is exactly:

```text
REVIEW_PASS
CHANGES_REQUIRED
```

No formal acceptance begins before REVIEW_PASS.

## 8. Corrected Formal Test Groups

### T1 — static/version/contract

- compile;
- diff check;
- exact version constants;
- no AI/API boundary regressions.

### T2 — ticker/CIK identity

- explicit CIK bypass;
- current ticker-map lookup;
- cached snapshot byte/hash verification;
- derivative mapping tamper;
- ticker remap/conflicting cache fail closed.

### T3 — discovery freshness and amendment lifecycle

Deterministic two-stage fixture:

```text
run 1: original filing only → acquire/parse PASS
run 2: same local package/artifact, submissions now adds /A
expected: current metadata fetched → REVIEW_REQUIRED
```

Also test:

- multiple non-amendment candidates;
- not-found;
- discovery network failure with cached data;
- status performs no network and reports last discovery_checked_at.

### T4 — acquisition/package/source-container provenance

- exact complete-submission URL/path binding;
- complete-submission source-container atomic store;
- strict byte-oriented DOCUMENT/TYPE/SEQUENCE/FILENAME/TEXT inventory;
- deterministic TEXT/XML/XBRL payload offsets and replay;
- primary + only required XBRL members selected from the container;
- unrelated exhibits/browser/static assets are not fetched by default;
- archive index fetch count = 0 for current package construction;
- individual package-member fetch count = 0 for current package construction;
- member/package hashes remain the Design-26 byte-set identity;
- immutable package-source provenance hash/artifact;
- legacy unattested package remains audit-only;
- same-package re-attestation does not mutate package bytes/manifest;
- different legacy/current package SHAs may coexist during migration;
- current provenance conflict/source drift fails closed;
- host/path/content-type/size/container-structure negatives.

### T5 — Registry v5 / validation-v4

- true v4 SEC Registry fixture → v5;
- v5 migration idempotent;
- source-container/provenance/member-locator rows round-trip;
- discovery observation rows preserved;
- legacy package/binding/parsed rows preserved for audit;
- current reuse requires source provenance;
- validation-v4 binds package SHA + provenance SHA;
- no validation-v4 → v3 fallback;
- same-byte re-attestation may revalidate V6/v2 without parser rerun;
- legacy user_version=1 unchanged;
- future schema no-mutation failure;
- CN/HK rows untouched.

### T6 — parser/raw facts/evidence

- INLINE_XBRL_PRIMARY;
- XBRL_INSTANCE_PRIMARY;
- primary + extracted instance yields one logical P6 fact set;
- multiple XBRL instance ambiguity;
- continuation;
- chained continuation;
- ix:exclude;
- missing continuation;
- duplicate target;
- cycle;
- custom QName;
- dimensions/nil/context/unit;
- unrelated OTHER XML context collision cannot resolve a fact;
- every source fragment round-trips to immutable bytes.

### T7 — DOM tables

- colspan-only width;
- rowspan occupancy;
- first-row td is not automatically HEADER;
- multi-row th span header tree;
- fact references/cell locators.

### T8 — P7/P8

- discovery observation bound to validation;
- PASS only for unambiguous current slot;
- P8 list/get/search/pages/sections/tables/facts/evidence/validation;
- discovery-as-of exposed;
- P8 no network;
- source chain/provenance tamper blocked.

### T9 — production CLI/capability

With `FFDF_P11_US_DEV` absent:

```text
ffdf acquire --market US ...
ffdf ingest  --market US ...
ffdf status  --market US ...
```

P8 US catalog/query must also work.

### T10 — live SEC fixtures

Retain at least:

- Apple FY2025 10-K;
- Apple FY2025 Q3 10-Q;
- Kellanova FY2024 original + 10-K/A;
- Toyota FY2025 20-F.

For repeat live ingest:

- current discovery metadata is re-fetched;
- unchanged accession causes zero archive member redownload;
- reusable parsed artifact causes zero parser rerun.

For Inline XBRL live fixtures, record logical fact counts by source mode and prove no
HTML/instance double enumeration.

### T11 — full regression

- full unit suite;
- CN CLI;
- HK CLI;
- P8 CN/HK;
- P9/P10 accepted tests;
- no accepted CN/HK raw/artifact mutation.

## 9. Formal evidence

Formal evidence must include:

- exact candidate SHA;
- exact formal-plan SHA;
- corrected design baseline SHA;
- every command and exit code;
- focused/full pass counts;
- live accessions/source URLs;
- discovery source hashes and observation hashes;
- package/member hashes;
- fact_source_mode and logical fact counts;
- repeat-run network classification;
- validation/P8 results;
- production-mode no-dev-flag proof;
- CN/HK regression;
- all skips/failures explicitly recorded.

If production code changes during formal testing, stop and return to a new candidate
review.

## 10. Gate V1 — Independent Verification

ChatGPT verifies:

- exact candidate identity;
- no post-review source drift;
- all corrected test groups executed;
- no hidden failures/skips;
- delayed amendment scenario proved;
- dual-source duplication is absent;
- continuation evidence is coherent;
- production path works without dev flag;
- CN/HK regression passed.

Verdict:

```text
ACCEPTANCE_PASS
ACCEPTANCE_FAILED
```

## 11. Gate I1 — Exact Main Integration

After ACCEPTANCE_PASS:

- merge the exact accepted candidate lineage;
- do not modify production/test behavior during the merge step;
- if merge requires source/test changes, acceptance is invalidated and review restarts;
- update status/user docs after merge;
- run a minimal post-merge smoke that does not substitute for formal acceptance;
- record merge SHA.

## 12. Closeout

Closeout records:

- corrected design baseline SHA;
- repaired production candidate SHA;
- code-review result;
- formal plan/evidence;
- acceptance verdict;
- merge SHA;
- supported forms/periods;
- explicit unsupported cases;
- migration/version summary.

Only then:

`P11 DONE / PASS`.
