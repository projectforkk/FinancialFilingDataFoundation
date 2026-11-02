# 07 — P1 Independent Acceptance Run Instruction

状态：**P1-I ACCEPTANCE INPUT FREEZE**

你是 **P1 Independent Acceptance 独立验收执行者**。

最终 verdict 只能是：

- `PASS`
- `FAIL`
- `BLOCKED`

不得修改 production code、tests、config、design 或 dependency version 来使验收通过。

不得开始 P2。

---

## 1. Repository / Phase

Repository:

`projectforkk/FinancialFilingDataFoundation`

Phase:

`P1 — Identity / Registry / Incremental Planner`

Formal branch:

`task/p1-identity-registry-planner`

Accepted baseline before P1:

`edff06b2b1138b50d742e92ce8b8df628c6d2c61`

P1 final design correction:

`3eb0f0f64b5cb4eaaa0b2247f0990cc2ae2604f2`

Final reviewed production/development candidate:

`f5c5cd76b33199639a5266959fbf7dc0968a95c4`

Final Code Review commit:

`e06681959a7d52237afa307620801a492d0f7307`

Final Code Review:

`PASS`

Evidence:

`development/13-p1-final-code-review.md`

The earlier `development/10-p1-code-review.md` is historical and invalidated by P1-ISSUE-008.

---

## 2. Frozen Acceptance Candidate

The acceptance candidate is the **Git commit containing this file**.

Its exact SHA must be read from `PROJECT_STATUS.md` after this freeze commit is created.

Independent Acceptance must use that exact SHA in a new detached worktree.

Do not use the moving branch HEAD as the acceptance candidate.

---

## 3. Mandatory Files to Read

Before executing acceptance checks, read:

- `AGENTS.md`
- `PROJECT_STATUS.md` from the project truth source for the exact frozen SHA
- `design/01-project-detailed-design.md`
- `design/02-incremental-and-acquisition-design.md`
- `design/06-p1-identity-registry-planner-design.md`
- `design/07-p1-implementation-plan.md`
- `development/07-p1-development-instruction.md`
- `development/09-p1-development-amendment.md`
- `development/12-p1-schema-v1-amendment.md`
- `development/13-p1-final-code-review.md`
- `acceptance/01-acceptance-strategy.md`
- `acceptance/06-p1-acceptance-instruction.md`
- this file

---

## 4. Candidate Isolation

Create a fresh independent Git worktree:

```text
D:\Codex\FinancialFilingDataFoundation-P1Acceptance-<shortsha>
```

Use detached HEAD at the frozen candidate SHA.

Before and after every critical acceptance command group:

```powershell
git rev-parse HEAD
git status --short --branch
```

Required:

`HEAD == frozen_candidate_sha`

If HEAD changes, that command group's evidence is invalid.

The acceptance worktree must explicitly create:

`workspace\`

before pytest or temporary DB/PDF generation.

---

## 5. Runtime

Use the already approved project runtime without changing it:

`D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe`

Expected:

- Python 3.14.9 ARM64
- PyMuPDF 1.28.2
- pytest 9.2.0
- sqlite3 stdlib
- dayu absent
- docling absent
- torch absent
- pypdf absent

Do not install or upgrade packages during acceptance.

---

## 6. Git / Scope Verification

Verify:

1. frozen candidate contains the reviewed production candidate;
2. P0 probe/tests are unchanged from accepted P0 baseline;
3. P1 production is limited to:
   - identity
   - registry
   - planner
4. no P2 acquisition implementation;
5. no Dayu adapter;
6. no network provider;
7. no table/MCP/Skill implementation.

---

## 7. Full Test Suite

From the isolated candidate worktree:

```powershell
New-Item -ItemType Directory -Force "workspace" | Out-Null
$env:PYTHONPATH="src"
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -m pytest tests\unit -q --basetemp "<acceptance-worktree>\workspace\pytest-acceptance"
```

Expected current count:

`54 passed`

Any actual unit/regression failure is `FAIL` unless it is demonstrably an external execution blocker.

---

## 8. Identity Acceptance

Independently verify:

- FilingSlotKey stable serialization;
- amended does not change slot key;
- duplicate FilingRequirement rejected;
- required filing ordering deterministic;
- filename is not business identity.

---

## 9. Registry Acceptance

Verify:

- new empty DB initializes to complete schema v1;
- content identity is SHA256;
- same SHA multi-path shares one content record;
- changed path content preserves historical document content record;
- source provenance persists without expected filing identity;
- repeated same provenance is idempotent;
- unbound content is not treated as local filing candidate;
- binding conflict is explicit;
- source file bytes/mtime are not modified by registration.

---

## 10. Schema Compatibility Acceptance

Independently verify all of the following.

### 10.1 Future version

`user_version > 1`

must raise:

`RegistrySchemaUnsupported`

with:

`reason_code == REGISTRY_SCHEMA_UNSUPPORTED`

No downgrade.

### 10.2 Version 0 non-empty

`user_version=0` plus an existing user table must be blocked.

It must not be auto-upgraded or have final-v1 tables silently added.

### 10.3 Incomplete version 1

A `user_version=1` DB missing any final-v1 required table or required column must be blocked during Registry initialization.

It must not reach a later unstructured:

`no such table`

or:

`no such column`

business SQL error.

---

## 11. Reuse / Planner Acceptance Matrix

Independently verify at least:

```text
valid reusable parsed data            -> REUSE_DATA
one local raw, no reusable data        -> PARSE_LOCAL
no parsed data, no local raw           -> DOWNLOAD_AND_PARSE
multiple distinct local SHA            -> REVIEW_REQUIRED
multiple reusable parsed SHA,
  no unique active-source evidence     -> REVIEW_REQUIRED
binding conflict                       -> BLOCKED
registered path content drift          -> BLOCKED / LOCAL_CONTENT_DRIFT
```

Also verify:

- parser_version difference alone does not force reparse;
- explicit invalidated parser version prevents reuse;
- empty accepted schema set means no reuse;
- current unique local SHA != parsed SHA prevents stale reuse;
- same-SHA duplicate locations remain usable when one copy drifts but another remains verified.

---

## 12. Determinism / Persistence

Verify:

- repeated same-state `build_plan` returns identical decision data;
- SQLite close/reopen does not change plan;
- canonical local path choice is deterministic;
- same-SHA multiple reusable parse runs choose deterministic parse_run_id.

---

## 13. Heavy-path / Network Prohibition

Static and runtime verification must show P1 does not use:

- Dayu
- httpx / requests
- urllib/socket network path
- Docling
- Torch
- external AI SDK/API

P1 acceptance must not make network calls.

---

## 14. P0 Regression

Verify P0 production/tests are unchanged from:

`edff06b2b1138b50d742e92ce8b8df628c6d2c61`

and the P0 tests included in the full suite still pass.

---

## 15. Governance Checks

P1-ISSUE-004 remains a recorded Git governance incident:

some unaccepted P1 commits entered `main` early.

This does not change the acceptance candidate.

Until this P1 Independent Acceptance returns PASS:

`accepted_baseline_sha = edff06b2b1138b50d742e92ce8b8df628c6d2c61`

Do not infer acceptance from `main HEAD`.

---

## 16. PASS Conditions

PASS requires all of the following:

- exact frozen candidate used;
- candidate HEAD stable;
- full suite PASS;
- P0 regression intact;
- identity semantics PASS;
- registry persistence PASS;
- provenance PASS;
- final schema-v1 completeness checks PASS;
- version=0 non-empty blocker PASS;
- future schema blocker PASS;
- planner matrix PASS;
- local content drift blocker PASS;
- determinism PASS;
- no network / Dayu / heavy path;
- source immutability PASS;
- no unresolved blocking finding.

---

## 17. FAIL Conditions

FAIL for any product/design acceptance failure, including:

- wrong planner action;
- stale parsed data reused after current local source change;
- drifted file treated as old registered SHA;
- ambiguous source guessed;
- incomplete v1 DB accepted;
- version=0 non-empty DB silently migrated;
- schema downgrade;
- source file modified;
- forbidden P2/network/heavy path;
- nondeterministic plan;
- unit/regression failure.

---

## 18. BLOCKED Conditions

BLOCKED only when acceptance cannot be judged because of an external execution blocker.

Do not use BLOCKED for an ordinary product/test failure.

---

## 19. Final Acceptance Output

Final verdict:

`PASS / FAIL / BLOCKED`

Evidence summary must include:

- frozen candidate SHA;
- HEAD stability;
- full test result;
- P0 regression result;
- identity/registry/planner matrix result;
- schema-v1 structural checks;
- source immutability;
- heavy-path/network result;
- blocker/warning summary.

Do not start P2 during P1 acceptance.
