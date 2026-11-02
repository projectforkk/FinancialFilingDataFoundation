# 08 — P1 Independent Acceptance Result

状态：**PASS**

Repository:

`projectforkk/FinancialFilingDataFoundation`

Phase:

`P1 — Identity / Registry / Incremental Planner`

Frozen acceptance candidate:

`3b382f4091a96a2dff40144253da42bf8de1fcc2`

Final reviewed production/development candidate contained by the frozen candidate:

`f5c5cd76b33199639a5266959fbf7dc0968a95c4`

Final Code Review:

`PASS`

Code Review evidence:

`development/13-p1-final-code-review.md`

Acceptance instruction:

`acceptance/07-p1-acceptance-run-instruction.md`

Accepted baseline before P1:

`edff06b2b1138b50d742e92ce8b8df628c6d2c61`

---

## 1. Verdict

# PASS

P1 satisfies the frozen Independent Acceptance criteria.

No P2 work was executed during P1 acceptance.

---

## 2. Acceptance Isolation

Independent Acceptance worktree:

`D:\Codex\FinancialFilingDataFoundation-P1Acceptance-3b382f4`

Mode:

detached HEAD

Frozen SHA:

`3b382f4091a96a2dff40144253da42bf8de1fcc2`

HEAD was checked before and after all critical command groups.

Observed:

```text
HEAD before = 3b382f4091a96a2dff40144253da42bf8de1fcc2
HEAD after  = 3b382f4091a96a2dff40144253da42bf8de1fcc2
```

Tracked worktree remained clean.

Result: **PASS**

---

## 3. Runtime

Verified:

- Python 3.14.9
- ARM64
- 64-bit
- SQLite 3.50.4
- PyMuPDF 1.28.2
- pytest 9.2.0

Absent:

- dayu
- docling
- torch
- pypdf

No dependency install/upgrade was performed during acceptance.

Result: **PASS**

---

## 4. Full Unit / Regression Suite

Command:

```powershell
Set-Location "D:\Codex\FinancialFilingDataFoundation-P1Acceptance-3b382f4"
New-Item -ItemType Directory -Force "workspace" | Out-Null
$env:PYTHONPATH="src"
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -m pytest tests\unit -q --basetemp "D:\Codex\FinancialFilingDataFoundation-P1Acceptance-3b382f4\workspace\pytest-acceptance"
```

Result:

```text
54 passed in 2.05s
```

This includes P1 tests and P0 regression tests.

Result: **PASS**

---

## 5. P0 Regression

Compared P0 probe production/tests against:

`edff06b2b1138b50d742e92ce8b8df628c6d2c61`

Result:

`git diff --exit-code = 0`

P0 source and P0 tests are unchanged by P1.

Result: **PASS**

---

## 6. Identity Acceptance

Independent matrix verified:

- normalized slot:
  `CN|CN:600519|ANNUAL_REPORT|2024|FY`
- original/amended/unknown variant share the same required slot;
- required filing order is deterministic by year then policy order;
- duplicate filing requirement is rejected.

Result: **PASS**

---

## 7. Registry / Provenance Acceptance

Verified:

- fresh empty DB initializes to schema v1;
- final-v1 required tables are present;
- `document_sources` required columns are present;
- same file registration is idempotent;
- same SHA across two paths creates one content record;
- canonical local path is deterministic;
- source bytes and mtime remain unchanged by registration;
- explicit re-registration after path content change preserves old content history;
- source provenance persists without expected filing identity;
- repeated same provenance is idempotent;
- unbound source content is not a local filing candidate.

Result: **PASS**

---

## 8. Planner Matrix

Independent acceptance observed:

```text
REUSE_DATA
  reason = VALIDATED_COMPATIBLE_PARSED_DATA

PARSE_LOCAL
  reason = LOCAL_RAW_AVAILABLE

DOWNLOAD_AND_PARSE
  reason = NO_REUSABLE_DATA_OR_LOCAL_RAW

REVIEW_REQUIRED
  reason = LOCAL_DOCUMENT_AMBIGUOUS

REVIEW_REQUIRED
  reason = MULTIPLE_REUSABLE_DOCUMENTS_AMBIGUOUS

BLOCKED
  reason = LOCAL_BINDING_CONFLICT

BLOCKED
  reason = LOCAL_CONTENT_DRIFT
```

Also verified:

- parser-version difference alone remains reusable;
- explicit invalidated parser version prevents reuse;
- empty accepted-schema set prevents reuse;
- current local SHA differing from parsed SHA produces `PARSE_LOCAL / SOURCE_MATERIAL_CHANGE`;
- same-SHA multiple parse runs select deterministic `run-a`;
- one drifted duplicate does not hide another verified same-SHA copy.

Result: **PASS**

---

## 9. Determinism / Persistence

Verified:

- repeated same-state plan is identical;
- close/reopen SQLite registry preserves the same plan;
- deterministic canonical path selection;
- deterministic parse-run selection.

Result: **PASS**

---

## 10. Schema Compatibility

### Future version

`user_version=2`

is rejected with:

`REGISTRY_SCHEMA_UNSUPPORTED`

Result: **PASS**

### Version 0 non-empty

A `user_version=0` DB containing a legacy user table is rejected with:

`REGISTRY_SCHEMA_UNSUPPORTED`

Post-failure inspection verified:

- `user_version` remains 0;
- no FFDF final-v1 tables were added;
- original legacy table remains the only user table.

No silent migration occurred.

Result: **PASS**

### Version 1 missing table

A v1 DB with missing `document_sources` is rejected during Registry initialization with:

`REGISTRY_SCHEMA_UNSUPPORTED`

Result: **PASS**

### Version 1 missing column

A v1 DB missing `document_sources.source_title` is rejected during Registry initialization with:

`REGISTRY_SCHEMA_UNSUPPORTED`

Result: **PASS**

P1-ISSUE-008 is therefore independently verified closed.

---

## 11. Source Immutability / Local Drift

Verified:

- normal registration does not change source bytes or mtime;
- local resolution re-hashes but does not rewrite files;
- registered file changed in place without re-registration is not treated as the old SHA;
- planner returns `BLOCKED / LOCAL_CONTENT_DRIFT`;
- if another verified same-SHA duplicate remains, that copy remains usable.

Result: **PASS**

---

## 12. Network / Heavy-path Prohibition

Static scan found no P1 imports of:

- dayu
- httpx
- requests
- urllib/socket network path
- docling
- torch
- external AI SDKs

Runtime:

```text
dayu=None
docling=None
torch=None
pypdf=None
```

No P2 acquisition directory was present in the frozen candidate.

No tables/MCP implementation was present.

Result: **PASS**

---

## 13. Machine-readable Acceptance Evidence

Generated ignored-workspace artifact:

`workspace\p1-acceptance\acceptance_matrix.json`

The matrix result contains:

`"verdict": "PASS"`

and records the accepted identity, planner, registry, drift, provenance, determinism and schema-blocker outcomes.

---

## 14. Invalidated Helper Attempt

The first independent matrix helper run stopped before the product matrix because the helper incorrectly compared:

`FilingIdentity.slot_key`

(a serialized string)

to a `FilingSlotKey` object.

This was an acceptance-helper assertion error, not a production/test/design failure.

Actions:

- that command group was discarded;
- frozen candidate HEAD was verified unchanged;
- only the ignored workspace helper was corrected;
- production/tests/config/design/dependencies were not modified;
- the full independent matrix was rerun from the beginning and passed.

No PASS evidence relies on the invalid helper attempt.

---

## 15. Governance

P1-ISSUE-004 remains a historical governance incident: some unaccepted P1 commits entered `main` before acceptance.

No reset, force push or history rewrite was used.

This Independent Acceptance used only the exact frozen candidate and did not infer acceptance from `main HEAD`.

P1-ISSUE-005 / 007 isolated-worktree rules were followed.

---

## 16. Final Evidence Summary

- frozen candidate: `3b382f4091a96a2dff40144253da42bf8de1fcc2`
- HEAD stability: PASS
- full tests: `54 passed in 2.05s`
- P0 regression: PASS
- identity: PASS
- registry persistence: PASS
- provenance: PASS
- planner matrix: PASS
- material change: PASS
- local content drift: PASS
- determinism: PASS
- fresh schema v1: PASS
- future schema blocker: PASS
- version=0 non-empty blocker: PASS
- incomplete-v1 table blocker: PASS
- incomplete-v1 column blocker: PASS
- source immutability: PASS
- network/heavy-path prohibition: PASS
- unresolved blocking finding: NONE

Final verdict:

# PASS

P1 is authorized to proceed to P1-K state closeout.

This result does not itself start P2.
