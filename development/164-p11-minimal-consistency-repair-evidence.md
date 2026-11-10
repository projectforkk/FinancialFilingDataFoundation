# 164 — P11 Minimal Consistency Repair Evidence

Status: **DEVELOPMENT REPAIR COMPLETE — READY FOR SIXTH EXACT-CANDIDATE CODE REVIEW**

## Execution identity

- Previous review: `development/163-p11-code-review-result-5.md`
- Previous review commit: `78459034d525f59fc59effc48ee9c8dfd285531d`
- Previous candidate: `362877244aa553ca4d76eb71318b116cde04c6a5`
- New exact production candidate: `437b8ed3710a368dc128b0cf2c78b6d121d89f19`
- Development branch: `task/p11-sec-rebuild-development`
- Source candidate commit message: `fix: close P11 incremental compatibility and registry versioning`
- Repair evidence commit: this documentation commit; its exact SHA is recorded in the final handoff
- Isolated live root: `D:\t\p11designrepair-live6`
- Accepted CN/HK workspace mutation: **NONE OBSERVED**

The source candidate is based on the fifth review commit and contains only
`src/` and `tests/` changes. This document is a separate documentation-only
commit. No Formal Acceptance or main merge was run.

## Issue status

### P11-ISSUE-112: FIXED

The existing incremental planner path was tightened so Registry rows are not
enough by themselves: selected package SHA, current parser/schema, valid
artifact manifest, PASS validation, COMPATIBLE status, and zero blocking issues
are all required for `REUSE_DATA`. Local package acquisition is explicitly
`PARSE_LOCAL`, while CLI orchestration can select `REUSE_DATA` only after the
parsed artifact is independently verified.

### P11-ISSUE-116: FIXED

Registry parsed-data compatibility is explicit. `None` now persists as
`INCOMPATIBLE`; validation status and artifact-format compatibility are
independent; `reuse_eligible` is exactly PASS + COMPATIBLE + zero blocking.

### P11-ISSUE-120: FIXED

The normalizer is now `VIRTUAL_HTML_V4`, with deterministic cached hidden-state
evaluation and the HTML5 `<header>` correction. Ordinary `<header>` narrative
is visible; exact `ix:header` and `ix:hidden` content remains excluded from
ordinary narrative while hidden facts/evidence remain supported.

### P11-ISSUE-121: FIXED

SEC Registry extension versioning is persisted independently from Legacy
Registry v1. Fresh state creates SEC v3 metadata; old SEC v2 shape migrates
additively, defaults historical parsed compatibility to `INCOMPATIBLE`, and
reopen is idempotent. Newer unknown SEC extension versions fail closed.

P11-ISSUE-109/110/111/113/114/115/117/118/119: **UNCHANGED — prior accepted implementation preserved**.

## Exact version values

```text
VIRTUAL_HTML_NORMALIZER_VERSION: VIRTUAL_HTML_V4
SEC_ARTIFACT_SCHEMA: p11-sec-artifacts-v1
REGISTRY_SCHEMA_VERSION: 1
SEC_REGISTRY_SCHEMA_VERSION: 3
SUPPORTED_MARKETS: ("CN", "HK")
```

The SEC extension version is stored in `sec_schema_metadata` as
`key=schema_version, value=3`; SQLite `PRAGMA user_version` remains the Legacy
Registry value `1`.

## Registry migration evidence

```text
Old SEC Registry migration: PASS
Old SEC version: 2
New SEC version: 3
Legacy PRAGMA user_version before: 1
Legacy PRAGMA user_version after: 1
Old source package rows preserved: YES
Old binding rows preserved: YES
Old parsed rows preserved: YES, except additive compatibility resolution
Migrated old compatibility: INCOMPATIBLE
Second reopen idempotent: YES
Unknown/newer SEC version fail closed: PASS
```

Regression tests:

- `test_sec_registry_migrates_v2_to_v3_without_rewriting_legacy_rows`
- `test_sec_registry_v3_reopen_is_idempotent`
- `test_fresh_registry_uses_legacy_v1_and_sec_extension_v3`
- unknown/newer SEC extension version rejection
- `None` compatibility defaulting to `INCOMPATIBLE`

## Parser upgrade and incremental planner evidence

```text
Old artifact: <package_sha>.VIRTUAL_HTML_V3
Current parser: VIRTUAL_HTML_V4
Old V3 reused: NO
Planner before current reparse: PARSE_LOCAL
Network requests during local upgrade: 0
New artifact: <package_sha>.VIRTUAL_HTML_V4
Planner after current parse: REUSE_DATA
```

The local integration constructed an immutable raw package, an old V3
artifact, and a stale PASS/COMPATIBLE Registry row. The current runtime chose
`PARSE_LOCAL`, rejected network/acquisition through a forbidden transport,
created V4, registered the current parsed run, and then selected
`REUSE_DATA`. The old V3 manifest bytes remained unchanged.

The compatibility/action matrix is covered as follows:

```text
PASS + COMPATIBLE + 0 blocking: YES, reuse = YES
PASS + INCOMPATIBLE + 0 blocking: YES, reuse = NO
REVIEW_REQUIRED + COMPATIBLE + 0 blocking: YES, reuse = NO
wrong package parsed row: YES, PARSE_LOCAL (not REUSE_DATA)
stale parser: YES, PARSE_LOCAL (not REUSE_DATA)
stale schema: YES, PARSE_LOCAL (not REUSE_DATA)
multiple local packages: YES, REVIEW_REQUIRED
current exact compatible parsed data: YES, REUSE_DATA
REUSE_DATA network calls: 0
REUSE_DATA parser reruns: 0
```

`SecAcquirer.acquire()` local-package behavior is separately verified as
`reused=True, plan_action=PARSE_LOCAL`.

## HTML hidden/evidence regression

```text
Visible HTML <header>: PRESERVED
ix:header hidden from ordinary narrative: PASS
ix:hidden facts/evidence: PRESERVED
P11-ISSUE-108 hidden evidence regression: PASS
```

The ISSUE-108 regression set remains green for hidden numeric facts, hidden
nonnumeric facts, corrupt hidden locator, corrupt member hash, corrupt
fragment hash, and visible block-anchor validation.

## Deterministic verification

```text
P11 focused:
90 passed in 3.93s

Full unit:
620 passed in 70.56s (0:01:10)

CN/HK regression:
96 passed in 7.23s

Additional non-US unit regression:
530 passed in 66.30s

Compileall:
PASS, `python -m compileall -q src tests`, exit 0

git diff --check:
PASS, exit 0
```

The exact CN/HK regression command was:

```text
tests/unit/identity tests/unit/registry tests/unit/mcp tests/unit/user_cli
```

## Developer live smoke

### Apple FY2025 10-K V4 developer live smoke: PASS

```text
Observed accession: 0000320193-25-000079
Observed parser version: VIRTUAL_HTML_V4
Raw Facts: 2262
Evidence: 2262
P7: PASS
P8: PASS
```

The local ingest command selected `PARSE_LOCAL`, used the existing raw package,
and returned `research_ready=true` with zero blocking issues.

### Apple FY2025 Q3 V4 developer live smoke: PASS

```text
Observed accession: 0000320193-25-000073
Observed parser version: VIRTUAL_HTML_V4
Raw Facts: 1538
Evidence: 1538
P7: PASS
P8: PASS
```

The local ingest command selected `PARSE_LOCAL`, used the existing raw package,
and returned `research_ready=true` with zero blocking issues.

### Toyota FY2025 20-F local developer smoke: PASS

The local acquisition/ingest action change was additionally exercised against
the existing Toyota package. The subsequent ingest selected `REUSE_DATA`,
returned PASS and `research_ready=true`, and the existing V4 artifact remained
the selected artifact.

### Kellanova amendment smoke

**NOT RE-RUN — unaffected by this repair.** Discovery, amendment selection,
and FPI policy were not changed in this pass. The prior developer smoke in
`development/162-p11-design-consistency-repair-evidence.md` remains PASS with
the expected `P11_AMENDED_VARIANT_PRESENT` controlled outcome.

## Governance handoff

```text
Production source changed after exact candidate: NO
Main merge: NOT RUN
P11 production availability: NOT CHANGED
Formal Acceptance: NOT RUN
Git push: PASS
```

The pushed branch contains the fifth review commit followed by exact source
candidate `437b8ed3710a368dc128b0cf2c78b6d121d89f19`; no source or test files
were changed after that candidate. Local targeted evidence is stored outside
the repository under `D:\Codex\FinancialFilingDataFoundation\work\p11-consistency-repair-evidence\`.

## Next action

`CHATGPT SIXTH EXACT-CANDIDATE CODE REVIEW OF 437b8ed3710a368dc128b0cf2c78b6d121d89f19`
