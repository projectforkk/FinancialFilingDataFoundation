# FFDF P11 — New Session Handoff Prompt

> Purpose: start a **new ChatGPT session** with enough repository-grounded context to continue the FinancialFilingDataFoundation project safely.
>
> This handoff deliberately requires a full repository/design/code read before continuing the current P11 repair. Do not jump directly to the latest issue list.

---

## 1. Repository

Repository:

`projectforkk/FinancialFilingDataFoundation`

Current working branch:

`task/p11-sec-rebuild-development`

Local project root used by the project:

`D:\Codex\FinancialFilingDataFoundation`

Active P11 worktree convention:

`D:\Codex\FinancialFilingDataFoundation\worktrees\active\p11-sec-rebuild-development`

Python:

`D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe`

Before doing anything:

1. fetch the current remote branch;
2. inspect branch HEAD, working-tree status and recent history;
3. never assume this handoff document is newer than Git;
4. treat Git as the source of truth.

Do not use destructive Git operations.

Forbidden unless the user explicitly changes project governance:

- `git reset --hard`
- `git clean -fd` / `git clean -fdx`
- rebase of published history
- commit amend of historical candidate/evidence
- force push
- history rewrite
- main merge without explicit authorization

---

# 2. Mandatory onboarding rule — read the whole project before continuing the current task

The new session must **first understand the whole project**, not only P11.

Do not propose a repair, write code, create a test plan, or authorize acceptance until the following repository reading is complete.

## 2.1 Read governance / status first

Read completely:

- `AGENTS.md`
- `PROJECT_STATUS.md`
- `README.md`
- `design/00-design-management-index.md`
- `design/README.md`
- `design/15-project-directory-management.md`

Use these to understand:

- repository governance;
- design source of truth;
- phase lifecycle;
- candidate/review/evidence/acceptance separation;
- issue management;
- directory/worktree rules;
- Git safety;
- current project status.

## 2.2 Read **all tracked design documents**

Read every Markdown file under:

`design/`

Do not read only P11 design.

Build a design inventory covering:

- cross-phase architecture;
- P0–P10 accepted historical designs;
- P11 active design;
- future/reference-only designs;
- superseding design corrections.

At minimum explicitly understand the relationship among:

- `01-project-detailed-design.md`
- `02-incremental-and-acquisition-design.md`
- `03-parsed-financial-document-contract.md`
- `04-pdf-quality-gate-design.md`
- P1 identity/Registry/planner design;
- P2 acquisition provider;
- P3 pages/sections;
- P4 table candidates;
- P5 table reconstruction;
- P6 raw facts/evidence;
- P7 validation;
- P8 local MCP;
- P9 review overlay;
- P10 dynamic research integration;
- `26-p11-sec-provider-design.md`;
- `27-p11-implementation-plan.md`;
- `32-p11-us-scope-reopening.md`;
- `33-p11-post-acceptance-design-correction.md`;
- `34-p11-explicit-6k-scope-correction.md`.

Current known P11 design lineage at the time this handoff was created:

Original corrected baseline:

`09e3174b7e19a60cc5955862670fac8931af67db`

Later authoritative P11 v1 6-K design correction / design freeze:

`4bf644374af3a0585453379fcc185d6464105776`

Do not call `09e3174...` alone the complete current design authority after Design 34.

If Git contains a later design correction, use the later frozen design.

## 2.3 Read **all production code**

Read the complete tracked production source tree:

`src/financial_filing_data_foundation/**`

Do not restrict reading to `us_sec/`.

Build a project-wide architecture map showing how these layers connect:

- identity / stable company identity;
- Registry;
- incremental planner;
- acquisition;
- native parser;
- pages / sections;
- table candidates;
- table reconstruction;
- raw facts / evidence;
- P7 validation;
- P8 MCP catalog/query service;
- P9 review overlay;
- P10 research integration;
- CLI;
- SEC/P11 provider;
- runtime/subprocess boundaries.

Then read the entire SEC implementation in detail, including at minimum:

- `us_sec/identity.py`
- `us_sec/ticker_map.py`
- `us_sec/policy.py`
- `us_sec/discovery.py`
- `us_sec/http.py`
- `us_sec/acquisition.py`
- `us_sec/package.py`
- `us_sec/parser.py`
- `us_sec/validation.py`
- `us_sec/registry.py`
- `us_sec/planner.py`
- `us_sec/ingest.py`
- `us_sec/runtime.py`
- `us_sec/compatibility.py`
- SEC integration in `user_cli.py`;
- SEC integration in P8/MCP service and report-safe paths.

## 2.4 Read tests as executable contracts

Read the test tree sufficiently to understand accepted behavior and current P11 coverage.

At minimum read:

- all `tests/unit/us_sec/**`;
- Registry/planner/acquisition tests;
- P7 tests;
- P8/MCP catalog/service/report-safe tests;
- P9/P10 compatibility/regression tests;
- CLI tests;
- tests specifically associated with P11 issues 123 onward.

Do not assume green test counts prove a design requirement that has no test.

For every current P11 issue, identify:

- production implementation;
- positive tests;
- negative/tamper tests;
- compatibility/migration test;
- live developer evidence if any.

## 2.5 Read relevant development / review / acceptance history

The new session does not need to memorize every old development file, but it must understand the lifecycle history and read the documents required to explain the current state.

Read at minimum:

- P10 final acceptance / closeout records identified by `PROJECT_STATUS.md`;
- P11 reopening authorization;
- P11 corrected design/review records;
- latest P11 evidence and review sequence.

Important recent P11 chain:

- `development/178-p11-full-design-code-consistency-reaudit.md`
- `development/181-p11-corrected-design-repair-evidence.md`
- `development/182-p11-issue-131-repair-evidence.md`
- `development/183-p11-formal-test-plan-3.md`
- `development/184-p11-formal-test-execution-prompt-3.md`
- `development/185-p11-formal-test-evidence-3.md`
- `development/186-p11-live-ft10-acquisition-repair-evidence.md`
- `development/187-p11-issue-134-repair-evidence.md`
- `development/188-p11-full-design-code-consistency-review-3.md`
- `development/189-p11-full-design-repair-135-139-evidence.md`
- `development/190-p11-fresh-full-exact-candidate-review-4.md`

Historical Formal Plan 183 is tied to an older failed candidate and must never be resumed for a new candidate.

## 2.6 Produce an onboarding summary before continuing

After reading the repository, first report a concise but concrete onboarding summary containing:

1. overall project architecture;
2. P0–P10 accepted baseline;
3. P11 purpose and scope;
4. active design authority and exact design freeze;
5. current branch and exact HEAD;
6. parser/artifact/Registry compatibility versions;
7. current SEC trust-boundary model;
8. current P11 lifecycle state;
9. closed issues versus open issues;
10. exact next authorized task;
11. what is explicitly **not** authorized.

Only after this summary may the current task continue.

---

# 3. Project-wide state to verify against Git

At handoff creation time, the high-level project state is:

## Completed / accepted

### P0–P10

P0 through P10 are accepted production history.

P10 final accepted main baseline remains the accepted CN/HK production baseline.

Key accepted P10 records and exact SHAs are maintained in `PROJECT_STATUS.md`.

CN/HK behavior is frozen and must not be weakened by P11.

### Operational CN/HK CLI

CN/HK `acquire`, `ingest`, and `status` operational paths exist and are accepted.

### P11 design / reopening

P11 was historically closed as out-of-scope, then explicitly reopened.

Current active SEC design is built from Design 26/27/32/33 plus the later Design 34 correction.

### P11 issues already repaired in implementation

Recent fresh review currently considers these repaired or materially closed:

- P11-ISSUE-123
- P11-ISSUE-124
- P11-ISSUE-125
- P11-ISSUE-126
- P11-ISSUE-127
- P11-ISSUE-128
- P11-ISSUE-129
- P11-ISSUE-130
- P11-ISSUE-131
- P11-ISSUE-133
- P11-ISSUE-134
- P11-ISSUE-135
- P11-ISSUE-136 core correctness portion
- P11-ISSUE-137
- P11-ISSUE-138 parser namespace-authentic portion
- P11-ISSUE-139 design correction + deterministic 6-K rejection

Do not blindly trust this list; verify against current Git/review documents.

---

# 4. Latest reviewed P11 candidate and review result

Latest reviewed production candidate at handoff creation time:

`55fc575cdaaeebd8b686ce76120978c714ca1a28`

Developer evidence commit:

`21962b8e4748cb8f800ad75be904624508d84ae8`

Latest fresh full exact-candidate review:

`development/190-p11-fresh-full-exact-candidate-review-4.md`

Review commit:

`adac1075a71881dc5aec41049ead3b03d1933d4c`

Review verdict:

```text
CHANGES_REQUIRED
REVIEW_PASS = NO
FORMAL TEST PLAN = NOT AUTHORIZED
FORMAL ACCEPTANCE = NOT RUN
MAIN MERGE = NOT AUTHORIZED
P11 DONE = NO
```

If Git contains a later candidate/review when the new session starts, use the later repository state.

---

# 5. Current task at handoff creation time

The current authorized task is a **single coherent repair cycle for P11-ISSUE-140 through P11-ISSUE-143**.

Do not create a Formal Test Plan yet.

## P11-ISSUE-140 — parser/artifact compatibility invalidation

Namespace-authentic parser behavior changed after V5/v2 was already in use.

The current reviewed candidate can still treat pre-ISSUE-138 V5/v2 parsed artifacts as compatible, allowing old semantics to bypass the repaired parser via REUSE_DATA / existing artifact reuse.

Required direction:

- freeze a new compatibility identity through design correction;
- pre-repair parsed artifacts become incompatible;
- immutable raw package remains reusable;
- parser actually re-runs;
- new artifact is written separately;
- old artifact remains immutable;
- current artifact becomes reusable afterward.

## P11-ISSUE-141 — namespace-authentic semantic-reference acquisition

Primary semantic reference parsing still recognizes literal `link:schemaRef` / `link:linkbaseRef` prefix spellings rather than XBRL linkbase namespace semantics.

Required:

- XBRL linkbase namespace URI based recognition;
- prefix-independent support;
- authentic XLink reference semantics;
- wrong/unbound lookalikes do not authorize acquisition;
- ISSUE-133/134 static-asset and semantic-reference behavior remains intact.

## P11-ISSUE-142 — complete but minimal history selection

Previous repair removed early history termination but now fetches every listed historical SEC submissions chunk.

This conflicts with the design requirement to fetch only the history required for the requested fiscal slot.

Required:

- complete candidate detection;
- late amendments remain discoverable;
- provably irrelevant history not fetched;
- conservative handling of incomplete metadata;
- deterministic bound/fail-closed behavior;
- online discovery and P7 reconstruction use the exact same source-selection rule.

If a safe rule cannot be designed from official metadata, stop and return to design rather than guessing.

## P11-ISSUE-143 — P7 fact-source semantic validation

P7 currently validates the fact-source-mode enum but not fully the mode-to-source invariant.

Required:

- INLINE_XBRL_PRIMARY facts/evidence only from authentic primary Inline XBRL;
- XBRL_INSTANCE_PRIMARY facts/evidence only from exactly one verified instance;
- NO_STRUCTURED_FACTS means zero logical facts;
- tampered yet internally consistent source-mode artifacts must fail closed.

---

# 6. Current repair instructions

The detailed repair prompt used immediately before this handoff should be reconstructed from:

- Review 190;
- current design;
- current source/tests;
- this handoff state.

The new session must not blindly reuse a stale chat prompt if Git has moved.

Required lifecycle:

```text
READ ENTIRE PROJECT / BUILD PROJECT MAP
→ CONFIRM CURRENT GIT STATE
→ DESIGN CORRECTION FOR ISSUE-140 IF REQUIRED
→ REPAIR ISSUE-140..143
→ DETERMINISTIC DEVELOPMENT TESTS
→ FULL US SEC REGRESSION
→ FULL UNIT REGRESSION
→ P0-P10 REGRESSION
→ LIVE APPLE DEVELOPER SMOKE
→ FREEZE NEW PRODUCTION CANDIDATE
→ DOCUMENTATION-ONLY DEVELOPMENT EVIDENCE
→ STOP
→ CHATGPT FRESH FULL EXACT-CANDIDATE DESIGN/CODE REVIEW
```

Do not skip the fresh full review.

---

# 7. Acceptance lifecycle rules

These are strict.

Developer evidence is not Formal Acceptance.

A local/live smoke PASS is not Formal Acceptance.

A focused exact-candidate review is not automatically a full-design review.

A new Formal Test Plan may be created **only after** a fresh full exact-candidate design/code review returns:

`REVIEW_PASS`

Any source/test/design change after the reviewed exact candidate invalidates that REVIEW_PASS.

Formal Test Plan must be pinned to the exact production candidate SHA and the exact current design freeze.

Formal execution must be performed separately.

Then ChatGPT performs independent final acceptance verification.

Only after acceptance may main integration be considered, and only with explicit authorization.

---

# 8. Historical P11 Formal Test Plan warning

Do not reuse:

`development/183-p11-formal-test-plan-3.md`

It was pinned to an earlier candidate that later failed Formal Execution.

Do not resume FT-11 onward from that run.

Every new candidate after a code/design repair requires:

```text
fresh exact-candidate review
→ new Formal Test Plan
→ complete formal execution from the beginning
```

---

# 9. Current known live SEC baseline

Most recent successful Apple FY developer smoke before this handoff reported:

- Apple FY2025
- CIK `0000320193`
- accession `0000320193-25-000079`
- structured facts: `1,131`
- XSD: `1`
- linkbases: `4`
- static/browser requests: `0`
- P7: `PASS`
- `research_ready=true`
- `FFDF_P11_US_DEV` absent

This is development evidence only.

Do not assume live SEC state has not changed.

---

# 10. Required trust-boundary map for the new session

Before implementing anything, explicitly understand and summarize these boundaries:

## Identity

```text
explicit CIK
→ authoritative stable identity
→ ticker map bypassed
```

Ticker path:

```text
ticker
→ current official SEC ticker-map bytes
→ CIK
→ retained source bytes/SHA provenance
```

## Discovery

```text
current submissions/history metadata
→ complete candidate universe for requested slot
→ deterministic state
→ selected accession only if unambiguous
→ exact discovery observation
```

Mutable discovery metadata must be revalidated online before online reuse.

## Package

```text
accession
→ primary
→ deterministic XBRL support members
→ immutable SecFilingPackage
```

Package SHA identifies immutable member-byte set.

CIK/accession/form/source URL provenance is verified separately.

## Parsing

Exactly one logical source:

```text
INLINE_XBRL_PRIMARY
OR
XBRL_INSTANCE_PRIMARY
OR
NO_STRUCTURED_FACTS
```

Never concatenate both logical fact universes.

## P7

Must independently validate:

- package identity/provenance;
- discovery observation semantics;
- source evidence;
- fact-source semantics;
- tables/artifacts;
- research readiness.

## P8

Read-only.

No SEC acquisition.

Every public/composed SEC serving path must enforce the same Registry/package/discovery/evidence trust chain.

---

# 11. Do not infer project state from chat memory alone

If this prompt conflicts with current Git:

**Git wins.**

Specifically inspect:

- current branch HEAD;
- commits after `adac1075...`;
- latest design files;
- latest `development/` records;
- latest P11 candidate/evidence/review;
- whether ISSUE-140..143 have already been repaired.

Do not ask the user to repeat information already present in Git.

---

# 12. Expected first response in the new session

After repository reading, respond first with something equivalent to:

```text
FFDF REPOSITORY ONBOARDING COMPLETE

Repository:
...

Branch / HEAD:
...

Overall architecture:
...

P0-P10 accepted state:
...

P11 active design authority:
...

Current parser/artifact/Registry versions:
...

Latest production candidate:
...

Latest independent review:
...

Completed P11 work:
...

Current open blockers:
...

Current authorized task:
...

Formal Test Plan:
NOT AUTHORIZED / AUTHORIZED based on latest Git review

Formal Acceptance:
...

Main merge:
...

Next action:
...
```

Only then continue the task.

---

# 13. Desired behavior from the new session

The new session should behave as a design/code reviewer and lifecycle owner, not merely as a coding assistant.

When it finds a defect:

1. record exact facts;
2. locate violated design clause;
3. distinguish code defect vs design ambiguity;
4. assign/check P11 issue ID;
5. decide whether design correction is needed before code;
6. identify invalidated evidence;
7. define deterministic regressions;
8. preserve exact-candidate lifecycle boundaries.

Never lower a gate merely because many tests are green.

Never create a Formal Test Plan while a full-design blocker remains.
