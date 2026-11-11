# 169 — P11 US SEC Provider Eighth Exact-Candidate Code Review

Status: **REVIEW_PASS**

Reviewed exact production candidate:
`2504614265b7a233ef9e4a772544ad63dd6eec37`

Previous review:
`development/167-p11-code-review-result-7.md`

Previous review commit:
`aa204b8e7f62c10df6e3543a12de8c66dd8c8aec`

Repair evidence:
`development/168-p11-final-registry-compatibility-repair-evidence.md`

Repair evidence commit:
`4608dc00e4acc8cd2101b8543dcc0f80726988d7`

Development branch:
`task/p11-sec-rebuild-development`

## 1. Exact-candidate lineage

PASS.

The reviewed production candidate is exactly `2504614265b7a233ef9e4a772544ad63dd6eec37`.

After that candidate, the only branch change before this review is the documentation-only evidence file `development/168-p11-final-registry-compatibility-repair-evidence.md`. No production source or test file changed after the exact candidate.

Candidate production/test changes are restricted to:
- `src/financial_filing_data_foundation/registry/sqlite_registry.py`;
- `tests/unit/us_sec/test_package_registry.py`.

## 2. P11-ISSUE-121 — FIXED

The Registry now recognizes both real historical SEC schema-v2 shapes that existed in the P11 development lineage.

### v2-A — early historical v2

Historical reference: `05e06096bc8b788d0467a1ce3442829e87727b6b`.

Characteristics:
- no `sec_schema_metadata`;
- no `sec_parsed_data.compatibility_status`;
- legacy `PRAGMA user_version = 1`.

Current migration:
- recognizes the exact v2-A core column shape;
- adds `compatibility_status`;
- forces historical parsed rows to `INCOMPATIBLE`;
- creates `sec_schema_metadata`;
- persists SEC schema version 3;
- preserves legacy CN/HK rows and SEC package/member/binding/parsed identities.

### v2-B — late historical v2

Historical reference: `362877244aa553ca4d76eb71318b116cde04c6a5`.

Characteristics:
- `SEC_REGISTRY_SCHEMA_VERSION = 2` in that runtime;
- no persisted `sec_schema_metadata`;
- `sec_parsed_data.compatibility_status` already present with `TEXT NOT NULL DEFAULT 'INCOMPATIBLE'`;
- legacy `PRAGMA user_version = 1`.

The new raw-SQLite v2-B fixture matches the historical SEC DDL for the four core SEC tables, including the compatibility column position/default, and is not initialized through the current Registry.

Current migration:
- recognizes the exact v2-B core column shape;
- does not drop/recreate SEC tables;
- preserves package/member/binding/parsed identity/value fields;
- forces pre-versioned compatibility values to `INCOMPATIBLE`;
- creates SEC schema metadata version 3;
- remains idempotent on reopen.

The regression deliberately begins with a historical parsed row marked `COMPATIBLE` and proves migration resets it to `INCOMPATIBLE`.

### Unknown unversioned shape

The classifier compares the exact core-column sets against the two supported historical v2 variants. An unversioned SEC schema with an additional unknown column is rejected as `RegistrySchemaUnsupported`, migration is not executed, and the logical database snapshot remains unchanged.

P11-ISSUE-121: **FIXED**.

## 3. P11-ISSUE-122 — FIXED / preserved

The prior future-version protection remains intact.

For a versioned SEC extension, the stored SEC schema version is validated before any current-version DDL or migration is permitted.

The future-version regression still proves:
- version 99 is rejected;
- no table-definition mutation;
- no column mutation;
- no index mutation;
- no metadata mutation;
- no row mutation.

P11-ISSUE-122: **FIXED**.

## 4. Registry migration review

The reviewed state machine is now coherent:

```text
no SEC extension
→ create current v3 + persist SEC metadata

unversioned exact v2-A
→ migrate v2-A → v3

unversioned exact v2-B
→ migrate v2-B → v3

versioned supported v2
→ validate one of the supported historical v2 shapes
→ migrate → v3

versioned current v3
→ validate current schema
→ no migration

unknown unversioned shape
→ fail closed

future / unsupported version
→ fail closed before mutation
```

Legacy `REGISTRY_SCHEMA_VERSION` remains 1 and accepted CN/HK Registry semantics remain unchanged.

## 5. Regression/evidence assessment

Evidence 168 reports:
- Registry focused: 18 passed;
- P11 focused: 94 passed;
- full unit: 624 passed;
- CN/HK regression: 96 passed;
- compileall: PASS;
- git diff --check: PASS.

No live SEC rerun was required because this repair changes only Registry migration recognition/tests. Previously reviewed live acquisition/parser/P8 paths are unchanged.

Version/governance values remain:

```text
REGISTRY_SCHEMA_VERSION = 1
SEC_REGISTRY_SCHEMA_VERSION = 3
VIRTUAL_HTML_NORMALIZER_VERSION = VIRTUAL_HTML_V4
SEC_ARTIFACT_SCHEMA = p11-sec-artifacts-v1
SUPPORTED_MARKETS = ("CN", "HK")
```

## 6. Full issue status

```text
P11-ISSUE-101: FIXED
P11-ISSUE-102: FIXED
P11-ISSUE-103: FIXED
P11-ISSUE-104: FIXED
P11-ISSUE-105: FIXED
P11-ISSUE-106: FIXED
P11-ISSUE-107: FIXED
P11-ISSUE-108: FIXED
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
P11-ISSUE-121: FIXED
P11-ISSUE-122: FIXED
```

## 7. New blocking findings

NONE.

## 8. Eighth review verdict

```text
P11 EIGHTH CODE REVIEW: REVIEW_PASS

EXACT PRODUCTION CANDIDATE:
2504614265b7a233ef9e4a772544ad63dd6eec37

NEW BLOCKING CODE FINDINGS:
NONE

FORMAL TEST PLAN:
NOT YET ISSUED

FORMAL ACCEPTANCE:
NOT STARTED

MAIN MERGE:
NOT AUTHORIZED

P11 PRODUCTION AVAILABILITY:
NOT CHANGED
```

## 9. Next gate

The exact candidate is now eligible to enter Gate T0.

Next action:

`CHATGPT FORMAL TEST PLAN FOR EXACT CANDIDATE 2504614265b7a233ef9e4a772544ad63dd6eec37`

The formal plan must be newly issued for this accepted candidate and must not reuse the obsolete plan 156 unchanged. It must cover the live SEC fixture classes plus the newly accepted Registry migration/incremental compatibility gates discovered during reviews 161–169.

No main integration or production enablement is authorized until formal acceptance passes.