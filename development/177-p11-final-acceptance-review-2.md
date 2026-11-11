# 177 — P11 US SEC Provider Independent Final Acceptance Review 2

Status: **ACCEPTANCE_PASS**

Accepted exact production candidate:
`9b7fcc9fc37a423eaafd1dde762e9c81d475df9e`

Code review:
`development/174-p11-code-review-result-9.md`

Code review commit:
`79f91e0dde8e71547e39229b1118ab553ab4dd38`

Formal test plan:
`development/175-p11-formal-test-plan-2.md`

Formal test plan commit:
`0c26d86ce648324ccda8d7c07574df30f1a2c0c3`

Formal evidence:
`development/176-p11-formal-test-evidence-2.md`

Evidence commit:
`cb113f7afd3f80eef6fb0624ee63ee45017e4ef6`

Development branch:
`task/p11-sec-rebuild-development`

## 1. Candidate / lineage verification

PASS.

The accepted production candidate is exactly `9b7fcc9fc37a423eaafd1dde762e9c81d475df9e`.

Current development-branch diff from the candidate contains only documentation files under `development/173` through `development/176`; no `src/`, `tests/`, runtime, packaging, or dependency bytes changed after the candidate.

The post-evidence branch synchronization and later clarification are documentation-only and do not alter the tested production candidate.

The execution explicitly used the active worktree source for the candidate and did not modify production/test code during formal acceptance.

## 2. Formal plan conformance

PASS.

Evidence 176 covers every required gate from plan 175:

- FT-00 candidate freeze;
- FT-01 deterministic regression;
- FT-02 Registry migration/version gate;
- FT-03 V3→V4 / planner reuse;
- FT-04 Apple FY2025 10-K live;
- FT-05 Apple FY2025 Q3 + full P8;
- FT-06 Toyota FY2025 20-F;
- FT-07 Kellanova CIK-only amendment;
- FT-08 security / HTTP / malformed source;
- FT-09 no-AI / runtime boundary;
- FT-10 idempotent REUSE_DATA;
- FT-11 CN/HK preservation.

No required gate is silently skipped.

## 3. Deterministic regression

PASS.

Accepted formal results:

```text
Provider/acquisition focused: 11 passed
Reviewed FT-08 scope: 84 passed
P11 focused: 100 passed
Full unit: 630 passed
CN/HK regression: 96 passed
compileall: PASS
git diff --check: PASS
```

The initial long-path Windows failures are environment/path-length failures and were rerun with the prescribed short basetemp. The authoritative reruns passed with zero test failures.

## 4. Registry / incremental compatibility

PASS.

Formal evidence proves:

### Registry

- early v2-A → v3;
- late v2-B → v3;
- migrated historical compatibility is fail-closed INCOMPATIBLE;
- legacy `PRAGMA user_version` remains 1;
- second reopen is idempotent;
- unknown unversioned shape fails closed without migration/mutation;
- future SEC metadata version 99 fails closed without mutation.

### Parser / planner

```text
VIRTUAL_HTML_V3 local artifact
→ PARSE_LOCAL
→ network = 0
→ VIRTUAL_HTML_V4 produced
→ PASS + COMPATIBLE + 0 blocking
→ REUSE_DATA
→ parser reruns = 0
→ network = 0
```

Stale parser, stale schema, wrong package and REVIEW_REQUIRED+COMPATIBLE states remain non-reusable.

## 5. Live SEC acceptance

PASS.

### Apple FY2025 10-K

Observed exact accession:
`0000320193-25-000079`

Observed:
- form 10-K;
- report period 2025-09-27;
- company `US:CIK0000320193`;
- parser `VIRTUAL_HTML_V4`;
- validation PASS;
- compatibility COMPATIBLE;
- blocking 0;
- research_ready true;
- 2262 raw facts;
- 2262 evidence;
- 62 tables.

### Apple FY2025 Q3 10-Q

Observed exact accession:
`0000320193-25-000073`

Observed:
- form 10-Q;
- report period 2025-06-28;
- parser VIRTUAL_HTML_V4;
- PASS / COMPATIBLE / zero blocking;
- 1538 raw facts;
- 1538 evidence;
- 38 tables.

The full P8 family was exercised with zero P8 HTTP/acquisition calls. Custom `aapl:` facts and hidden Inline-XBRL facts were present and evidence-resolved.

### Toyota FY2025 20-F

Observed exact accession:
`0001193125-25-142326`

Observed:
- form 20-F;
- report period 2025-03-31;
- PASS / COMPATIBLE / zero blocking;
- 6746 raw facts;
- 6746 evidence;
- P8 read without network.

Deterministic FPI policy still rejects guessed quarterly 6-K mapping.

### Kellanova FY2024

CIK-only discovery correctly observed:
- original `0001628280-25-007118`;
- amendment `0000055067-25-000127`.

Controlled result:
`P11_AMENDED_VARIANT_PRESENT`

No active binding/catalog/package was published for the conflicted slot.

## 6. FT-08 prior defect closure

PASS.

The prior formal failure is closed in this acceptance cycle.

All six required malformed discovery/source paths returned controlled `P11_SEC_DISCOVERY_FAILED`:

1. invalid main submissions JSON;
2. invalid historical submissions JSON;
3. invalid archive index JSON;
4. invalid archive directory;
5. invalid archive item list;
6. invalid archive item record.

No `UnboundLocalError`, `NameError`, or uncontrolled generic exception occurred.

The acceptance security harness also passed redirect limits, safe/unsafe archive paths, source drift, terminal 403/429 handling, bounded Retry-After, and no remote script execution.

## 7. Runtime / security boundary

PASS.

Formal audit reports:

```text
forbidden_ai_hits = 0
SEC runtime lock = stdlib-only
runtime argv allowlist = true
shell = false
filing-controlled arbitrary shell paths = 0
P8 HTTP/acquisition = 0
```

## 8. Idempotent reuse

PASS.

Formal repeated Apple FY execution produced:

```text
acquire = REUSED_LOCAL
planner = REUSE_DATA
HTTP calls = 0
acquisition calls = 0
parser reruns = 0
package/member/artifact identity unchanged = true
```

## 9. CN/HK preservation

PASS.

Formal acceptance confirms:

```text
SUPPORTED_MARKETS = ("CN", "HK")
REGISTRY_SCHEMA_VERSION = 1
PRAGMA user_version = 1
CN/HK regression = 96 passed
accepted CN/HK source/raw mutation = none
```

## 10. Independent acceptance verdict

All required formal gates passed against exact candidate `9b7fcc9fc37a423eaafd1dde762e9c81d475df9e`.

No production/test code changed during or after formal acceptance.

No unresolved blocking issue remains in the P11 acceptance scope.

```text
P11 INDEPENDENT FINAL ACCEPTANCE REVIEW 2:
ACCEPTANCE_PASS

ACCEPTED EXACT PRODUCTION CANDIDATE:
9b7fcc9fc37a423eaafd1dde762e9c81d475df9e

CODE REVIEW:
REVIEW_PASS

FORMAL EXECUTION:
EXECUTION_PASS

FT-00..FT-11:
PASS

NEW BLOCKING FINDINGS:
NONE

MAIN MERGE:
NOT YET RUN

P11 PRODUCTION AVAILABILITY:
NOT YET CHANGED
```

## 11. Next gate — main integration / closeout

The exact accepted candidate lineage is now authorized to proceed to main integration.

Next work must be a controlled integration/closeout task that:

1. merges the exact accepted candidate lineage without introducing unreviewed production changes;
2. updates public supported-market declarations to include US only as required by the accepted design;
3. changes P11 capability from unavailable to available;
4. updates project/user documentation and project status;
5. preserves explicit unsupported cases, including amendment conflict and unsupported FPI quarterly mapping;
6. runs a minimal post-merge regression/smoke on main;
7. records the merge SHA and final closeout evidence.

If integration requires any new production logic beyond reviewed enablement/status declarations, stop and return to review rather than silently extending scope.

Final state `P11 DONE / PASS` is permitted only after the controlled main integration and closeout evidence are complete.