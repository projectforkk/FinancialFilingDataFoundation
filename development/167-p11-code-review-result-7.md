# 167 — P11 US SEC Provider Seventh Exact-Candidate Code Review

Status: **CHANGES_REQUIRED**

Reviewed exact production candidate:
`d123c70689657d3102ae550adcd5b81d5dab4967`

Previous review:
`development/165-p11-code-review-result-6.md`

Previous review commit:
`137e94d23a02c06b838e2cc5145b87aab91aa472`

Repair evidence:
`development/166-p11-registry-version-gate-repair-evidence.md`

Repair evidence commit:
`2df59da87c372e9c401fbb9df24476d2d42cf991`

Development branch:
`task/p11-sec-rebuild-development`

## 1. Exact-candidate lineage

PASS.

The exact reviewed production candidate is `d123c70689657d3102ae550adcd5b81d5dab4967`.

After that candidate, the evidence commit adds only `development/166-p11-registry-version-gate-repair-evidence.md`. No production source or test file changed after the candidate.

## 2. P11-ISSUE-122 — FIXED

The future/unknown SEC schema gate is now ordered correctly.

For an existing versioned SEC extension, `_ensure_sec_schema()` validates the metadata table and reads the stored SEC version before applying current-version DDL.

Unsupported/newer versions therefore fail closed before `_create_sec_schema()`, `ALTER TABLE`, metadata rewrite, or current-v3 maintenance can run.

The new `test_future_sec_schema_fails_closed_without_mutation` uses a deliberately non-current future shape and snapshots tables, columns, indexes, metadata, rows, and `PRAGMA user_version` before and after the rejected open.

This directly covers the defect identified in review 165.

P11-ISSUE-122: **FIXED**.

## 3. P11-ISSUE-121 — STILL PARTIALLY OPEN

The new candidate correctly adds:

- persistent SEC schema metadata;
- SEC schema version 3;
- explicit version gating;
- real raw-SQLite historical migration tests;
- no-mutation rejection for future versions;
- idempotent v3 reopen;
- preservation of legacy CN/HK Registry v1.

The new raw-SQLite fixture correctly models the earliest historical SEC v2 shape used by candidate `05e06096...`: no `sec_schema_metadata` and no `sec_parsed_data.compatibility_status`.

That migration path is validly exercised and accepted.

However, review 163 opened ISSUE-121 because **two materially different schema shapes had both existed under SEC_REGISTRY_SCHEMA_VERSION=2**.

The later real P11 development candidate:

`362877244aa553ca4d76eb71318b116cde04c6a5`

had all of the following:

- `SEC_REGISTRY_SCHEMA_VERSION = 2`;
- no `sec_schema_metadata` table;
- `sec_parsed_data.compatibility_status` already present.

This is an actual prior P11 development schema, not a hypothetical shape.

Current candidate `d123c706...` treats every unversioned SEC extension as historical v2 only if `_validate_sec_v2_schema()` matches `_SEC_V2_REQUIRED_SCHEMA_COLUMNS` exactly.

That exact v2 definition excludes `compatibility_status`.

Therefore an existing database produced by candidate `362877...` is rejected as:

`SEC registry extension is not a supported historical v2 shape`

instead of being migrated deterministically to persisted SEC schema v3.

This violates the explicit ISSUE-121 repair requirement from review 163:

> migrate the prior P11 development schema deterministically and idempotently

and leaves one real prior P11 workspace state unsupported.

## 4. Required ISSUE-121 completion

Support both real historical version-2 shapes:

### v2-A — early v2

- no `sec_schema_metadata`;
- no `compatibility_status` column.

Migration behavior:

- add `compatibility_status`;
- force historical parsed rows to `INCOMPATIBLE`;
- create SEC schema metadata = 3.

### v2-B — later v2

- no `sec_schema_metadata`;
- `compatibility_status` column already present;
- schema otherwise matches the real `362877...` v2 implementation.

Migration behavior:

- preserve all rows/identities;
- force historical compatibility to `INCOMPATIBLE` because v2 did not carry an independently versioned compatibility contract;
- create SEC schema metadata = 3;
- do not drop/recreate SEC tables.

Do not accept arbitrary unversioned shapes. Recognition must remain restricted to the two exact supported historical v2 schemas.

## 5. Required regression

Add a raw-SQLite regression representing the exact `362877...` SEC v2-B schema.

Suggested test:

`test_sec_registry_migrates_late_v2_with_compatibility_column_to_v3`

The fixture must not be initialized through the current Registry.

It must have:

- `PRAGMA user_version = 1`;
- legacy Registry v1 schema;
- SEC v2 core tables;
- no `sec_schema_metadata`;
- `sec_parsed_data.compatibility_status` present;
- representative source/member/binding/parsed rows.

Opening current `SQLiteRegistry` must prove:

- recognized as supported historical v2-B;
- migrated to SEC schema v3;
- legacy PRAGMA remains 1;
- existing source/member/binding/parsed rows preserved;
- compatibility forced to INCOMPATIBLE;
- second reopen idempotent.

Also add a negative regression proving an unversioned SEC shape with any additional unknown column still fails closed rather than being guessed as v2.

## 6. Evidence assessment

Evidence 166 reports:

- Registry focused: 16 passed;
- P11 focused: 92 passed;
- full unit: 622 passed;
- CN/HK regression: 96 passed;
- compileall: PASS;
- git diff-check: PASS;
- real early-v2 migration: PASS;
- future-version no-mutation: PASS.

These results are accepted for the cases actually covered.

They do not cover the later real v2-B schema produced by candidate `362877...`.

## 7. Seventh review verdict

```text
P11 SEVENTH CODE REVIEW: CHANGES_REQUIRED

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
P11-ISSUE-122: FIXED

EXACT PRODUCTION CANDIDATE:
d123c70689657d3102ae550adcd5b81d5dab4967

FORMAL TEST PLAN:
NOT ISSUED

FORMAL ACCEPTANCE:
NOT RESUMED

MAIN MERGE:
NOT AUTHORIZED

P11 PRODUCTION AVAILABILITY:
NOT CHANGED
```

## 8. Required next action

Perform one final narrow Registry compatibility repair only.

Required scope:

1. recognize and migrate the exact late-v2 schema from candidate `362877...`;
2. keep the already-fixed early-v2 migration unchanged;
3. keep future/unknown schema no-mutation behavior unchanged;
4. add late-v2 positive migration regression;
5. add arbitrary-unversioned-shape negative regression;
6. rerun Registry-focused, complete P11, full unit, CN/HK, compileall, and diff-check;
7. produce a new exact production candidate;
8. produce a separate development evidence commit;
9. stop for ChatGPT eighth exact-candidate review.

No parser, discovery, acquisition, HTTP, P8, or live SEC changes are required or authorized by this review.

No formal acceptance plan is authorized before REVIEW_PASS.