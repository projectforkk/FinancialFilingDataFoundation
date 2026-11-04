# 165 — P11 Package-Aware Reuse Amendment Evidence — ISSUE-027

Status: **PASS — AMENDED DESIGN READY FOR CANDIDATE FREEZE**

Phase:
P11 — US SEC Provider

Historical reviewed candidate:
`dff1e390f0a8825c75abb15cfb10c41543c676d5`

Review stop:
`development/164-p11-package-aware-reuse-review-stop.md`

Production remains CLOSED.

## P11-ISSUE-027 resolution

Generic reuse safety:

- accepted IncrementalPlanner remains CN/HK document-SHA reuse;
- market=US generic planner call fails closed with `P11_PACKAGE_AWARE_PLANNER_REQUIRED`;
- no US fallback to document-SHA-only reuse is allowed.

P11-K package-aware selector:

Inputs:

- confirmed periodic slot;
- current document_sha256;
- current source_package_sha256;
- accepted reuse/parser/schema policy;
- project root + P11 parsed-artifact root.

Candidate source:

- existing `SQLiteRegistry.list_parsed_data(slot)`;
- no registry schema migration required solely for package identity.

Exact reuse checks:

- artifact_path non-null;
- project-root-relative POSIX;
- resolved inside configured P11 parsed root;
- v2 loader passes;
- loaded parse_run_id == registry record;
- loaded/current/record document_sha256 agree;
- loaded source_package_sha256 == current package;
- loaded periodic identity == confirmed slot;
- parser/schema accepted;
- validation PASS;
- zero blockers;
- compatibility COMPATIBLE.

Fail-closed cases:

- same document SHA + different package SHA => `P11_SOURCE_PACKAGE_CHANGE`;
- missing artifact => `P11_REUSE_ARTIFACT_MISSING`;
- invalid/outside artifact path => `P11_REUSE_ARTIFACT_PATH_INVALID`;
- loader/hash/identity mismatch => `P11_REUSE_ARTIFACT_INVALID`.

Multiple exact-package reusable records select lexicographically smallest parse_run_id only after all exact-package checks.

## Existing behavior preserved

- CN/HK IncrementalPlanner behavior unchanged;
- supplemental 8-K/6-K remain outside periodic ParsedDataRecord reuse;
- P8/P9/P10 contracts unchanged;
- no registry migration solely for this reuse contract.

## Scope

Design/governance only.

No src/tests/integration/runtime-lock changes.

## Verdict

# PASS — READY FOR CANDIDATE FREEZE AND FRESH DETACHED DESIGN REVIEW

No production authorization is implied.


## Additional P11-ISSUE-028 resolution

Runtime reuse position is now explicit:

```text
requested target slot
→ discovery
→ P11-E current exact package
→ package-aware reuse selector
    ├─ exact reusable artifact => REUSE_DATA / skip P11-F..I
    └─ no reusable artifact => P11-F parse → P11-G identity → P11-H v2 → P11-I validation → P11-K persist
```

The selector uses the requested target slot and trusts prior confirmed identity only when the artifact is for the exact current package and passes all reuse gates. This preserves both correctness and the purpose of incremental reuse.
