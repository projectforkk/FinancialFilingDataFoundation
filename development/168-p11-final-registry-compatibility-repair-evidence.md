# 168 — P11 Final Registry Compatibility Repair Evidence

Status: **DEVELOPMENT REPAIR COMPLETE — READY FOR EIGHTH EXACT-CANDIDATE CODE REVIEW**

## Execution identity

- Previous review: `development/167-p11-code-review-result-7.md`
- Previous review commit: `aa204b8e7f62c10df6e3543a12de8c66dd8c8aec`
- Previous candidate: `d123c70689657d3102ae550adcd5b81d5dab4967`
- New production candidate: `2504614265b7a233ef9e4a772544ad63dd6eec37`
- Development branch: `task/p11-sec-rebuild-development`
- Candidate commit message: `fix: support both historical P11 SEC v2 registry shapes`
- Candidate changed files:
  - `src/financial_filing_data_foundation/registry/sqlite_registry.py`
  - `tests/unit/us_sec/test_package_registry.py`

The source candidate was safely rebased onto the remote seventh-review
documentation commit so the branch could be pushed without force. The rebase
changed no source or test bytes. This evidence is a separate documentation-only
commit. No Formal Acceptance or main merge was run.

## Issue status

```text
P11-ISSUE-121: FIXED
P11-ISSUE-122: UNCHANGED — FIXED
P11-ISSUE-109 through 120 except 121: UNCHANGED — prior reviewed FIXED status preserved
```

The Registry now recognizes exactly two supported unversioned historical SEC v2
column shapes. Any other unversioned shape is rejected before migration.

## Historical shape matrix

### Early v2-A

```text
Historical source candidate: 05e06096bc8b788d0467a1ce3442829e87727b6
metadata before: NO
compatibility_status before: NO
migration: PASS
compatibility after: INCOMPATIBLE
second reopen: IDEMPOTENT
```

The existing raw-SQLite early-v2 fixture remains unchanged. Migration adds the
compatibility column, forces historical parsed rows to `INCOMPATIBLE`, creates
`sec_schema_metadata`, and records schema version 3.

### Late v2-B

```text
Historical source candidate: 362877244aa553ca4d76eb71318b116cde04c6a5
metadata before: NO
compatibility_status before: YES
historical compatibility: COMPATIBLE
migration: PASS
compatibility after: INCOMPATIBLE
second reopen: IDEMPOTENT
```

The late-v2 fixture is built entirely with raw SQLite DDL. Its SEC DDL was
compared directly with the exact historical candidate's
`src/financial_filing_data_foundation/registry/sqlite_registry.py`: it has the
four SEC core tables, `sec_parsed_data.compatibility_status` in the historical
column position/default, no `sec_schema_metadata`, and `PRAGMA user_version = 1`.
It is not initialized through the current `SQLiteRegistry`.

The parsed row deliberately starts as `COMPATIBLE`. The migration does not
drop/recreate tables or rewrite package/member/binding identity. It only forces
all historical compatibility values to `INCOMPATIBLE`, creates metadata, and
records `schema_version = 3`.

```text
Late v2-B fixture created through current SQLiteRegistry: NO
Late v2-B source rows preserved: YES
Late v2-B member rows preserved: YES
Late v2-B binding rows preserved: YES
Late v2-B parsed identity/value fields preserved: YES
Late v2-B second reopen idempotent: YES
Legacy CN/HK rows preserved: YES
Legacy PRAGMA user_version before: 1
Legacy PRAGMA user_version after: 1
SEC version after migration: 3
```

## Unsupported unversioned shape

```text
Unknown unversioned SEC shape: REJECTED
Schema guessed as v2: NO
Migration executed: NO
Database mutation: NO
```

The negative fixture is raw SQLite v2-A plus an unknown
`future_unknown_field` column. The before/after snapshot compares table SQL,
columns, indexes, metadata/data rows, and `PRAGMA user_version`; the migration
wrapper counter remains zero.

## Future-version protection

```text
Future SEC schema no-mutation: PASS
Future SEC version: 99
Database mutation before rejection: NO
Runtime result: RegistrySchemaUnsupported
```

The existing future-version regression remains green: metadata version is read
before any current-v3 DDL, ALTER, metadata rewrite, or row update.

## ISSUE-121 RED → GREEN

```text
Before repair: FAIL
Failure reason: the current d123c706 implementation rejected the exact late-v2-B shape because _SEC_V2_REQUIRED_SCHEMA_COLUMNS excluded compatibility_status.
After repair: PASS
```

The late-v2 positive regression failed against the previous candidate with
`RegistrySchemaUnsupported: SEC registry extension is not a supported
historical v2 shape`, then passed after the explicit V2_EARLY/V2_LATE classifier
was implemented.

## Deterministic verification

Commands used the project Python runtime and short project-local temp paths.
The complete P11, full unit, and CN/HK counts were run on the final source/test
tree before the candidate commit; the Registry-focused test was rerun on the
rebased exact candidate.

```text
Registry focused:
18 passed in 1.41s

P11 focused:
94 passed in 4.71s

Full unit:
624 passed in 73.53s (0:01:13)

CN/HK regression:
96 passed in 7.76s

Compileall:
PASS, exit 0

git diff --check:
PASS, exit 0
```

## Version and governance gates

```text
REGISTRY_SCHEMA_VERSION: 1
SEC_REGISTRY_SCHEMA_VERSION: 3
VIRTUAL_HTML_NORMALIZER_VERSION: VIRTUAL_HTML_V4
SEC_ARTIFACT_SCHEMA: p11-sec-artifacts-v1
SUPPORTED_MARKETS: ("CN", "HK")
```

```text
Live SEC:
NOT RE-RUN — FINAL REGISTRY COMPATIBILITY REPAIR ONLY
```

The prior live developer evidence remains applicable because this pass changed
only Registry migration recognition and Registry tests. No parser, discovery,
acquisition, HTTP, P8, or live SEC code was modified.

```text
Production source changed after exact candidate: NO
Main merge: NOT RUN
P11 production availability: NOT CHANGED
Formal Acceptance: NOT RUN
Git push: PASS
```

Only this evidence document is added after the exact production candidate.

## Next action

`CHATGPT EIGHTH EXACT-CANDIDATE CODE REVIEW OF 2504614265b7a233ef9e4a772544ad63dd6eec37`
