# 12 — P1 Development Amendment — Final Schema v1 Compatibility

状态：**P1-C / P1-G REVALIDATED AFTER P1-ISSUE-008**

Branch:

`task/p1-identity-registry-planner`

Issue:

`P1-ISSUE-008 — Incomplete schema-v1 compatibility check`

Design baseline commit:

`3eb0f0f64b5cb4eaaa0b2247f0990cc2ae2604f2`

Primary production correction:

`443b96e441456dc28e419fa8162b07b1041be640`

Concurrent production correction merged:

`b63c88a837e281c570bf8041048e502f8910b9a0`

Resolved merge commit:

`4c5f1de60a7a11ac7efd487181c26b43cfe93335`

---

## 1. Review Finding

The earlier P1 Code Review identified that registry compatibility was determined primarily by:

`PRAGMA user_version`

During P1 development, the final v1 schema gained `document_sources` while still being pre-acceptance schema version 1.

A database created by an earlier P1 development revision could therefore be:

- `user_version = 1`
- structurally incomplete relative to final P1 v1

and still pass the old initialization check until later business SQL failed with an unstructured SQLite error such as `no such table`.

The earlier Code Review evidence in:

`development/10-p1-code-review.md`

was invalidated after this finding.

---

## 2. Final Design Rule

P1 final registry schema remains:

`REGISTRY_SCHEMA_VERSION = 1`

because P1 has not yet completed its first Independent Acceptance.

Compatibility now requires both:

1. supported `PRAGMA user_version`;
2. complete required table/column structure for final schema v1.

Additional rule:

- `user_version=0` is considered a new DB only when no non-`sqlite_%` user tables exist;
- version=0 with existing user tables is blocked rather than silently migrated.

Pre-acceptance P1 registry DBs are development artifacts and are not auto-migrated.

After P1 PASS, any structural schema change must use a new schema version and a separately designed migration policy.

---

## 3. Implementation

`SQLiteRegistry._initialize()` now:

- rejects newer unsupported versions;
- rejects version=0 non-empty DBs;
- creates final v1 schema only for a true empty version=0 DB;
- validates complete final-v1 schema for version=1;
- raises structured `RegistrySchemaUnsupported` for missing required tables/columns.

Required structure validation includes:

- `documents`
- `document_locations`
- `document_sources`
- `filing_bindings`
- `parsed_data`

and their required columns.

Reason code remains:

`REGISTRY_SCHEMA_UNSUPPORTED`

No automatic table repair, downgrade or destructive migration was introduced.

---

## 4. Concurrent Implementation Reconciliation

A concurrent branch commit:

`b63c88a837e281c570bf8041048e502f8910b9a0`

implemented required-table/column validation but did not cover the later design refinement:

`user_version=0 + existing user table → structured blocker`.

The branch merge produced conflicts only in:

- `src/financial_filing_data_foundation/registry/sqlite_registry.py`
- `tests/unit/registry/test_sqlite_registry.py`

Conflict resolution retained the more complete local implementation that includes:

- version=0 non-empty blocking;
- version=1 missing-table blocking;
- version=1 missing-column blocking.

No unrelated production file was changed during conflict resolution.

---

## 5. Regression Coverage

Added/retained tests verify:

1. newer registry schema is rejected;
2. version=0 non-empty registry is rejected;
3. version=1 missing required table is rejected;
4. version=1 missing required column is rejected;
5. all errors expose `REGISTRY_SCHEMA_UNSUPPORTED`;
6. existing identity/registry/planner/P0 tests continue to pass.

---

## 6. Final Development Rerun

Command:

```powershell
Set-Location "D:\Codex\FinancialFilingDataFoundation"
New-Item -ItemType Directory -Force "workspace" | Out-Null
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe -m pytest tests\unit -q --basetemp "D:\Codex\FinancialFilingDataFoundation\workspace\pytest-p1-schema-v1-merged"
```

Result:

```text
54 passed in 2.09s
```

Additional verification:

- `py_compile`: PASS
- `git diff --check`: PASS
- working tree after rerun: clean

---

## 7. Gate Impact

Affected gates:

- P1-C SQLite Registry
- P1-G Tests
- P1-H Code Review

Results:

- P1-C: **REVALIDATED PASS**
- P1-G: **REVALIDATED PASS**
- prior P1-H evidence: **INVALIDATED**
- P1-H must be rerun from the new frozen candidate in an isolated worktree

P1-I Acceptance Freeze has not been authorized yet.
