# 27 — P11 US SEC Provider Implementation Plan

Status: **CORRECTED REPAIR CYCLE ACTIVE — PRIOR ACCEPTANCE INVALIDATED FOR MERGE**

Detailed design:
`design/26-p11-sec-provider-design.md`

Scope contract:
`design/32-p11-us-scope-reopening.md`

Post-acceptance correction authority:
`design/33-p11-post-acceptance-design-correction.md`

Re-audit:
`development/178-p11-full-design-code-consistency-reaudit.md`

## 1. Execution principle

The previous P11 acceptance cycle is historical evidence only. It does not authorize
main integration after the re-audit/design correction.

The corrected lifecycle is:

```text
CORRECTED DESIGN FREEZE
→ PC AGENT ONE-PASS REPAIR DEVELOPMENT
→ MERGE-READY PRODUCTION CANDIDATE
→ CHATGPT EXACT-CANDIDATE CODE REVIEW
→ CHATGPT NEW FORMAL TEST PLAN
→ PC AGENT ONE-PASS FORMAL TEST EXECUTION
→ GIT TEST EVIDENCE
→ CHATGPT INDEPENDENT VERIFICATION
→ ACCEPT / FIX
→ MERGE EXACT ACCEPTED CANDIDATE
→ CLOSEOUT
```

The merge-ready candidate must already contain production US behavior. No production
logic is added after acceptance.

## 2. Roles

### 2.1 PC Agent

PC Agent must:

1. read the corrected design baseline completely;
2. implement P11-ISSUE-123 through P11-ISSUE-130 as one coherent repair;
3. preserve accepted CN/HK behavior;
4. add deterministic regression tests for every repaired issue;
5. produce one exact merge-ready candidate SHA;
6. stop after candidate/evidence push;
7. execute formal tests only after ChatGPT reviews that exact candidate and issues a
   new formal plan.

PC Agent must not alter the corrected design contract without a STOP/design issue.

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
- `design/33-p11-post-acceptance-design-correction.md`.

Record:

```text
corrected_design_baseline_sha
previous_production_candidate_sha = 9b7fcc9fc37a423eaafd1dde762e9c81d475df9e
starting_branch
starting_head
```

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
SEC_REGISTRY_SCHEMA_VERSION = 4
SEC_DISCOVERY_SCHEMA = p11-sec-discovery-v1
VIRTUAL_HTML_NORMALIZER_VERSION = VIRTUAL_HTML_V5
SEC_ARTIFACT_SCHEMA = p11-sec-artifacts-v2
SEC_VALIDATION_SCHEMA = p11-sec-validation-v2
```

Required behavior:

- SEC Registry v3 → v4 additive migration;
- v4 migration idempotent;
- unknown future SEC schema fails closed before mutation;
- CN/HK `user_version=1` and accepted rows unchanged;
- V4/v1 US parsed artifacts not reusable as corrected current artifacts;
- immutable old raw SEC packages may be reparsed to V5/v2 after current discovery;
- no destructive raw-store migration.

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

### T4 — acquisition/package/provenance

- primary + only required XBRL members;
- unrelated XML exhibit is not downloaded by default;
- member/package hashes;
- exact source URL path binding;
- Registry/manifest provenance tamper;
- source drift;
- host/path/content-type/size negatives.

### T5 — Registry v4

- true v3 fixture → v4;
- discovery observation rows preserved/reopened;
- idempotent reopen;
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
