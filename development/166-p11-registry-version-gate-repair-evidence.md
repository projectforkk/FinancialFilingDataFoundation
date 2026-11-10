# 166 — P11 Registry Version-Gate Repair Evidence

Status: **DEVELOPMENT REPAIR COMPLETE — READY FOR SEVENTH EXACT-CANDIDATE CODE REVIEW**

## Execution identity

- Previous review: `development/165-p11-code-review-result-6.md`
- Previous review commit: `137e94d23a02c06b838e2cc5145b87aab91aa472`
- Previous candidate: `437b8ed3710a368dc128b0cf2c78b6d121d89f19`
- New production candidate: `d123c70689657d3102ae550adcd5b81d5dab4967`
- Development branch: `task/p11-sec-rebuild-development`
- Candidate commit message: `fix: harden P11 SEC registry migration version gate`
- Candidate changed files:
  - `src/financial_filing_data_foundation/registry/sqlite_registry.py`
  - `tests/unit/us_sec/test_package_registry.py`

The candidate was safely rebased onto the remote sixth-review documentation
commit so the branch could be pushed without force. That rebase changed no
source or test bytes. This evidence document is a separate documentation-only
commit. No Formal Acceptance or main merge was run.

## Issue status

```text
P11-ISSUE-121: FIXED
P11-ISSUE-122: FIXED
P11-ISSUE-109 through 120 except 121: UNCHANGED — prior reviewed FIXED status preserved
```

P11-ISSUE-121 now uses a genuine historical SEC v2 fixture built with raw
SQLite DDL. The fixture contains the accepted Legacy Registry v1 structure,
SEC v2 core tables without `sec_schema_metadata` and without
`compatibility_status`, deterministic package/member/binding/parsed rows, and
deterministic CN legacy rows. The test wraps `_migrate_sec_v2_to_v3()` and
observes exactly one migration call during `SQLiteRegistry(db)` initialization.

P11-ISSUE-122 now gates every existing versioned SEC extension by reading and
validating its metadata before current-version DDL. Unknown or unsupported
shapes are no longer treated as v2, and current-version DDL is confined to the
fresh-schema or explicitly validated migration paths.

## Real historical v2 migration

```text
REAL HISTORICAL V2 FIXTURE: YES
Fixture created through current SQLiteRegistry: NO
Historical SEC metadata present before migration: NO
compatibility_status column before migration: NO
PRAGMA user_version before: 1
SEC version inferred before: 2
Migration branch executed: YES
SEC version after: 3
PRAGMA user_version after: 1
compatibility_status after: INCOMPATIBLE
source package row preserved: YES
member rows preserved: YES
binding row preserved: YES
parsed row preserved: YES
legacy CN rows preserved: YES
second reopen idempotent: YES
```

The migration preserves source package SHA/accession/CIK/form, member SHA and
relative name/role, binding identity/company/year/period, and parsed run,
parser/schema/validation/blocking/artifact fields. The only SEC additions are
the compatibility column, forced to `INCOMPATIBLE` for historical rows, and
`sec_schema_metadata.schema_version = 3`.

The explicitly versioned v2 variant (`schema_version = 2`) is also covered and
migrates through the same validated path.

## Future-schema no-mutation gate

```text
Future SEC version fixture: 99
Current runtime result: RegistrySchemaUnsupported
Current v3 schema DDL executed before rejection: NO
Schema mutation: NO
Column mutation: NO
Index mutation: NO
Metadata mutation: NO
Row mutation: NO
```

The future fixture intentionally retains the historical no-
`compatibility_status` shape while declaring version 99. The before/after
snapshot compares `sqlite_master` table and index definitions, all table
columns, metadata/data rows, and `PRAGMA user_version`.

## ISSUE-122 RED → GREEN

```text
Before repair: FAIL
Failure reason: the old _ensure_sec_schema() called _create_sec_schema() before _read_sec_schema_version(); the future-version fixture gained compatibility_status and its table definition changed before RegistrySchemaUnsupported was raised.
After repair: PASS
```

The valid pre-repair run was:

```text
1 failed, 1 passed, 13 deselected
```

The failing assertion was the logical before/after database snapshot, not a
test harness or environment error.

## Deterministic verification

Commands were run with the project Python runtime and short project-local temp
paths.

```text
Registry focused:
16 passed in 0.84s

P11 focused:
92 passed in 3.54s

Full unit:
622 passed in 69.31s (0:01:09)

CN/HK regression:
96 passed in 6.50s

Compileall:
PASS, exit 0

git diff --check:
PASS, exit 0
```

The exact regression commands were:

```text
python -m pytest -q --basetemp D:\t\p11-registry-repair\candidate tests/unit/us_sec/test_package_registry.py
python -m pytest -q --basetemp D:\t\p11-registry-repair\p11-final tests/unit/us_sec
python -m pytest -q --basetemp D:\t\p11-registry-repair\unit-final tests/unit
python -m pytest -q --basetemp D:\t\p11-registry-repair\cnhk-final tests/unit/identity tests/unit/registry tests/unit/mcp tests/unit/user_cli
python -m compileall -q src tests
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
NOT RE-RUN — REGISTRY-ONLY REPAIR
```

The prior developer live evidence in
`development/164-p11-minimal-consistency-repair-evidence.md` remains the
reference for the unchanged SEC acquisition/parser/live paths. This pass did
not modify acquisition, parser, discovery, HTTP, P8, or live SEC logic.

```text
Production source changed after exact candidate: NO
Main merge: NOT RUN
P11 production availability: NOT CHANGED
Formal Acceptance: NOT RUN
Git push: PASS
```

The pushed candidate commit is `d123c70689657d3102ae550adcd5b81d5dab4967`.
Only this evidence document is added after that exact candidate.

## Next action

`CHATGPT SEVENTH EXACT-CANDIDATE CODE REVIEW OF d123c70689657d3102ae550adcd5b81d5dab4967`
