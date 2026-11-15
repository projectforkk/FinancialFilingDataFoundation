# 198 — P11 Fresh Full Exact-Candidate Review 6

Status: **CHANGES_REQUIRED — ISSUE-146 DESIGN CORRECTION REQUIRED**

This is the fresh full review of exact production candidate
`35e2b70c78b6cff931c8484dc38f2eb7349735f5` and its documentation-only
evidence child `93027f60be96f3998fb041ac6ad65bcf31c55834`.

It is not a Formal Test Plan, Formal Acceptance, main-merge authorization, or
P11 DONE record.

## 1. Exact identity

- Design baseline: `70353788d0b6188e757e24b10b0883b0a9a057dd`
- Development authorization: `0ae1596b7e5df5038c298d9a453171b40c81334b`
- Production candidate: `35e2b70c78b6cff931c8484dc38f2eb7349735f5`
- Evidence commit: `93027f60be96f3998fb041ac6ad65bcf31c55834`
- Candidate → evidence: documentation only, only
  `development/197-p11-review5-repair-evidence.md`

Remote authoritative lineage is
`reconcile/p11-140-143-local-chain`. The local worktree branch name reported
by the evidence is not the authoritative remote ref.

## 2. Reviewed development evidence

Evidence reports exact-candidate:

- focused Review-5: 79 passed;
- complete US SEC: 244 passed;
- MCP/US: 93 passed;
- P0-P10 focused: 371 passed;
- full unit: 774 passed;
- compileall: PASS;
- git diff --check: PASS;
- Apple FY2025 production smoke: PASS;
- accession `0000320193-25-000079`;
- observation SHA
  `b07b419aab758287675bd07e29ef4c91743c1226502d1fc1a83734dada427cbd`;
- package SHA
  `079185e72f20bd4fc1a2a19b2c57430390b2fb5482403b51752525a0264ff131`;
- fact source mode `INLINE_XBRL_PRIMARY`;
- 1131 facts;
- validation-v3 path and schema;
- blocking=0, review=0, research_ready=true.

These results are accepted as development evidence, not Formal Test evidence.

## 3. Issue disposition

```text
ISSUE-140: FIXED / preserved
ISSUE-141: FIXED / preserved
ISSUE-142: FIXED
ISSUE-143: FIXED
ISSUE-145: FIXED

VALIDATION-V3 VERSIONED STORAGE:
FIXED

P11-ISSUE-146:
OPEN / BLOCKING
```

### ISSUE-142

The candidate removes silent history-descriptor skipping, validates the complete
inventory before fetch, enforces exact dates and duplicate-name rejection, and
uses the shared selector for online/reconstructed source sets.

### ISSUE-143

The candidate independently scans package member bytes for authentic instance
roots, validates role consistency, replays Inline/XML source nodes, and checks
same-source context/unit semantics.

### ISSUE-145

The candidate independently compares persisted Raw Fact/Evidence semantics with
the immutable source projection and emits the frozen blocking
`P11_RAW_FACT_SOURCE_MISMATCH` for semantic mismatch.

## 4. Blocking finding — P11-ISSUE-146

The validation-v3 migration execution path does not satisfy Design 37.

Current `_current_reusable_sec_artifacts()` only reports a parsed artifact as
available when a current reusable v3 validation artifact can also be loaded.
With a compatible V6/v2 parsed artifact plus legacy validation-v2 and no
current v3, it returns no reusable artifact.

The planner therefore selects `PARSE_LOCAL`, and `_us_ingest()` calls
`ingest_sec_package()`, which reruns `parse_sec_package()`.

This violates the frozen migration contract requiring parser reuse and
validation-only v3 execution.

Additionally, `reuse_sec_package()` attempts to load current validation before
fresh revalidation, so it cannot serve as the missing-v3 migration path.

The candidate also lacks the required exact migration test proving parser
invocation count remains zero and legacy v2/parsed bytes remain unchanged.

## 5. Design-rooted ambiguity

Design 26 Layer B maps a compatible parsed package directly to `REUSE_DATA`,
while Design 37 correctly denies `REUSE_DATA` when current v3 is absent but
requires revalidation without parsing.

The repair therefore requires the explicit `REVALIDATE_LOCAL` planner state
frozen in Design 38 before code changes.

## 6. Verdict

```text
FRESH FULL EXACT-CANDIDATE REVIEW:
CHANGES_REQUIRED

REVIEW_PASS:
NO

FORMAL TEST PLAN:
NOT AUTHORIZED

FORMAL ACCEPTANCE:
NOT RUN

MAIN MERGE:
NOT AUTHORIZED

P11 DONE:
NO
```

The next production candidate must be a child of a new development authorization
that references the Design 38 freeze. Candidate 35e2b70 remains historical
Review-6 evidence and is not eligible for Formal Test.
