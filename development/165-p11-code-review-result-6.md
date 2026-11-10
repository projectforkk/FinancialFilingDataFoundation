# 165 — P11 US SEC Provider Sixth Exact-Candidate Code Review

Status: **CHANGES_REQUIRED**

Reviewed exact production candidate:
`437b8ed3710a368dc128b0cf2c78b6d121d89f19`

Previous review:
`development/163-p11-code-review-result-5.md`

Previous review commit:
`78459034d525f59fc59effc48ee9c8dfd285531d`

Repair evidence:
`development/164-p11-minimal-consistency-repair-evidence.md`

Repair evidence commit:
`ed9183790c79af87d737b6584c48c837f3a9ae17`

Development branch:
`task/p11-sec-rebuild-development`

## 1. Exact-candidate lineage

PASS.

The production candidate is `437b8ed3710a368dc128b0cf2c78b6d121d89f19`.

After that exact candidate, the evidence commit changes only `development/164-p11-minimal-consistency-repair-evidence.md`. No production source or test file changed after the candidate.

## 2. P11-ISSUE-112 — FIXED

The incremental planner now binds reusable parsed state to the selected local package and current artifact contract.

`_current_reusable_sec_artifacts()` requires the same package SHA, current parser version, current artifact schema, PASS validation, COMPATIBLE status, zero blocking issues, loadable artifacts, matching parsed/validation package identity, and reuse-eligible validation.

Reviewed regressions cover stale parser, stale schema, wrong package, exact compatible row, and multiple-local-package conflict. The REUSE_DATA branch calls `reuse_sec_package()` rather than `parse_sec_package()`, and its regression forbids SEC acquisition, HTTP fetch, and parser rerun.

`SecAcquirer.acquire()` correctly classifies package-only local state as `PARSE_LOCAL`, not `REUSE_DATA`.

P11-ISSUE-112: **FIXED**.

## 3. P11-ISSUE-116 — FIXED

Validation status and artifact compatibility are now separate concepts.

The new `sec_artifact_compatibility()` derives compatibility from current parser version and current SEC artifact schema.

`validate_sec_artifacts()` can therefore produce `REVIEW_REQUIRED + COMPATIBLE + reuse_eligible=false`, which is the required semantic separation.

Reuse eligibility is constrained by PASS + COMPATIBLE + zero blocking issues. `register_sec_parsed_data(... compatibility_status=None)` fails closed to INCOMPATIBLE rather than deriving compatibility from PASS.

P11-ISSUE-116: **FIXED**.

## 4. P11-ISSUE-120 — FIXED

The normalizer version is now `VIRTUAL_HTML_V4`, and `load_sec_artifacts()` requires both current artifact schema and current parser version.

Old V3 artifact directories are not reused as V4. The local-upgrade integration regression demonstrates old V3 parsed row/artifact → PARSE_LOCAL → zero network → new V4 artifact → REUSE_DATA, while leaving the old V3 manifest unchanged.

The HTML5 header defect is also fixed: ordinary visible `<header>` content is no longer classified as hidden; exact `ix:header` and `ix:hidden` remain excluded from ordinary visible narrative; hidden Inline-XBRL facts/evidence remain regression-protected.

P11-ISSUE-120: **FIXED**.

## 5. P11-ISSUE-121 — PARTIALLY OPEN

The production implementation now materially improves Registry versioning:
- legacy `REGISTRY_SCHEMA_VERSION` remains 1;
- `SEC_REGISTRY_SCHEMA_VERSION` is 3;
- `sec_schema_metadata` persists the SEC extension version independently;
- a v2→v3 migration path exists;
- migrated parsed rows are forced to INCOMPATIBLE;
- v3 reopen is intended to be idempotent.

However, the required v2→v3 regression does **not actually construct an old SEC v2 database**.

### 5.1 Invalid v2 fixture

`_make_v2_registry()` starts with `registry = SQLiteRegistry(db)`.

At candidate `437b8ed...`, that creates a fresh SEC v3 database and persists `sec_schema_metadata.schema_version = 3`.

The helper then drops only `sec_parsed_data.compatibility_status`. It does not remove SEC metadata, set the stored SEC version to 2, or create the historical v2 tables directly.

Therefore `test_sec_registry_migrates_v2_to_v3_without_rewriting_legacy_rows` does not exercise the historical no-metadata v2 path. On reopen the database still declares SEC schema v3; `_create_sec_schema()` merely re-adds the missing compatibility column using its default, and the true `_migrate_sec_v2_to_v3()` branch is not proven by this test.

The evidence statement `Old SEC version: 2 / New SEC version: 3` is therefore not supported by that regression fixture.

### 5.2 Required correction

Create an actual old v2 database using raw SQLite DDL or an exact historical v2 fixture. The fixture must not initialize through the current v3 `SQLiteRegistry`.

At minimum the real v2 fixture must have PRAGMA user_version=1, the required legacy CN/HK schema, SEC core tables in historical v2 shape, no v3 SEC metadata for the real historical no-metadata path, `sec_parsed_data` without `compatibility_status` for the oldest v2 shape, and real source/member/binding/parsed rows.

Then opening current `SQLiteRegistry` must prove v2→v3, legacy PRAGMA stays 1, source/member/binding identity is unchanged, old parsed row is retained, migrated compatibility is INCOMPATIBLE, and second reopen is idempotent.

P11-ISSUE-121 remains **PARTIALLY OPEN** until the real migration path is regression tested.

## 6. New blocking finding — P11-ISSUE-122

### Future/unknown SEC schema can be mutated before its version is rejected

Current `_ensure_sec_schema()` performs this order:

inspect table names → `_create_sec_schema(conn)` → `_read_sec_schema_version(conn)` → reject unsupported/newer version.

For an existing versioned SEC registry, `_create_sec_schema()` may execute current-v3 DDL before the stored version is checked. In particular it may create current-version objects or add the current `compatibility_status` column before discovering that `sec_schema_metadata.schema_version` is newer than the runtime supports.

A forward-version fail-closed gate must not modify an unknown future schema before rejecting it.

The existing `test_unknown_sec_extension_version_fails_closed` does not catch this because it starts from a fully current v3 database and changes only metadata to 99. In that shape `_create_sec_schema()` happens to be effectively a no-op.

### Required repair

Reorder Registry initialization so an existing versioned SEC extension is gated by its stored version **before** applying current-version schema DDL.

Required state machine:

- no SEC core + no SEC metadata → create fresh current SEC schema;
- SEC core present + no metadata → infer historical v2 only under the explicitly supported historical shape, then migrate v2→v3;
- SEC metadata present → read version first;
- stored version == current → validate current schema; apply only explicitly safe idempotent current maintenance;
- stored version == supported old version → run explicit migration;
- stored version > current or otherwise unsupported → fail closed with NO schema/data mutation.

Retain the existing incomplete-core fail-closed behavior.

### Required regression

Add `test_future_sec_schema_fails_closed_without_mutation`.

Construct a database that declares a future SEC version (for example 99) and is intentionally not identical to the current v3 shape. Snapshot table definitions, columns, metadata, and row contents. Opening current `SQLiteRegistry` must raise `RegistrySchemaUnsupported` and leave schema and rows unchanged.

P11-ISSUE-122: **OPEN / BLOCKING**.

## 7. Development evidence assessment

Evidence 164 reports P11 focused 90 passed, full unit 620 passed, CN/HK regression 96 passed, compileall PASS, git diff-check PASS, Apple FY2025 10-K V4 developer smoke PASS, Apple FY2025 Q3 V4 smoke PASS, P8 PASS, zero network during V3→V4 local upgrade, and zero parser reruns during REUSE_DATA.

These results are accepted for the paths they actually exercise. They do not establish the claimed old SEC v2 migration because the migration fixture was built from the current v3 Registry.

## 8. Sixth review verdict

```text
P11 SIXTH CODE REVIEW: CHANGES_REQUIRED

P11-ISSUE-109: FIXED
P11-ISSUE-110: FIXED
P11-ISSUE-111: FIXED
P11-ISSUE-112: FIXED
P11-ISSUE-113: FIXED
P11-ISSUE-114: FIXED
P11-ISSUE-115: FIXED
P11-ISSUE-116: FIXED
P11-ISSUE-117: FIXED
P11-ISSUE-118: FIXED
P11-ISSUE-119: FIXED
P11-ISSUE-120: FIXED
P11-ISSUE-121: PARTIALLY OPEN
P11-ISSUE-122: NEW BLOCKER

EXACT PRODUCTION CANDIDATE:
437b8ed3710a368dc128b0cf2c78b6d121d89f19

FORMAL TEST PLAN:
NOT ISSUED

FORMAL ACCEPTANCE:
NOT RESUMED

MAIN MERGE:
NOT AUTHORIZED

P11 PRODUCTION AVAILABILITY:
NOT CHANGED
```

## 9. Required next action

Perform one narrow Registry-only repair pass.

Required scope:
1. correct the v2 migration fixture so it is a genuine historical v2 database and actually executes `_migrate_sec_v2_to_v3()`;
2. reorder SEC Registry version gating so a declared unknown/newer version is read and rejected before any current-version schema mutation;
3. add the future-version no-mutation regression;
4. retain all 90 current P11 tests plus the new regressions;
5. rerun full unit, CN/HK regression, compileall and diff-check;
6. produce a new exact production candidate;
7. produce a separate development evidence commit;
8. stop for ChatGPT seventh exact-candidate review.

Do not reopen parser, discovery, P8, acquisition or live SEC code unless a regression proves it necessary.

No new formal acceptance plan is authorized before REVIEW_PASS.