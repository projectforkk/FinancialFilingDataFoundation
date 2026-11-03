# 58 — P9-I Live CN/HK Execution Instruction

Status: **ACTIVE — P9-I ONLY**

Phase:
`P9 — Codex Review Overlay`

Target branch:
`task/p9-review-overlay`

Authorization basis:
- `development/57-p9-g-corrective-github-rereview.md` — P9-G/P9-H PASS；
- `design/22-p9-review-overlay-design.md`；
- `design/23-p9-implementation-plan.md`；
- `acceptance/32-p9-acceptance-instruction.md`。

This instruction authorizes **P9-I live CN/HK validation only**.

It does not authorize P9-J/K/L/M, main merge, P10, or P11.

---

## 1. Hard governance boundary

P9-I is a validation/evidence gate, not a production-development gate.

Do NOT modify:
- P9 production source；
- P9 tests；
- P0–P8 source/tests；
- design semantics；
- accepted catalog；
- P3/P5/P6/P7 artifacts；
- runtime/dependencies；
- Registry；
- P8 MCP implementation。

Do NOT:
- reset / clean / rebase / force push；
- overwrite or delete unknown existing live-review directories；
- open source PDFs；
- invoke OCR；
- use network/AI/OpenAI/Codex API inside P9；
- use external MCP SDK；
- manufacture evidence；
- guess period/unit/scope values；
- force live documents to PASS；
- reuse earlier temporary P9-I output as accepted evidence。

If live execution exposes a product/design defect:
**STOP P9-I and report exact evidence.**
Do not patch production first.

---

## 2. Start from current GitHub truth

Before live work:

```powershell
cd D:\Codex\FinancialFilingDataFoundation\worktrees\active\p9-review-overlay

git status --short --branch --untracked-files=all
git fetch origin
git rev-parse HEAD
git rev-parse origin/task/p9-review-overlay
git log --oneline --decorate -12
```

If local HEAD is behind only by GitHub review/governance documentation and worktree has no conflicting production/test edits, safe fast-forward is allowed:

```powershell
git merge --ff-only origin/task/p9-review-overlay
```

Otherwise STOP and report.

---

## 3. Candidate / runtime

Use the exact current P9 branch candidate after safe sync.

Runtime:

`D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe`

Set:

```powershell
$env:PYTHONPATH="D:\Codex\FinancialFilingDataFoundation\worktrees\active\p9-review-overlay\src"
```

Do not install/upgrade dependencies.

---

## 4. Canonical P8 catalog

Use the **accepted canonical P8 local catalog** already used by P8/P9 validation.

Expected local catalog path from the established live environment is:

`D:\Codex\FinancialFilingDataFoundation\workspace\mcp\p8-live-catalog.json`

Before use:
1. confirm the file exists；
2. confirm it loads with the accepted internal `McpCatalog`；
3. confirm it contains the exact CN/HK documents below；
4. record catalog SHA256 / size / mtime_ns；
5. if the accepted/current P8 evidence identifies a different canonical catalog path or bytes, STOP and report instead of silently switching catalogs。

Do not create a replacement catalog for this Gate.

---

## 5. Exact live documents

### CN — 600519 FY2024

Expected document SHA256:

`5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30`

Required base queue:
- count = **1**
- exact reason = `RAW_PERIOD_COVERAGE_LOW`
- reviewability/action mapping must be correct。

### HK — 00700 FY2024

Expected document SHA256:

`70f529984a87ef7f46d9e1db26bb9ef27eef9c01d29c59aabf69e557b479a6a0`

Required base queue:
- count = **4**

Exact reason set:
- `CORE_STATEMENT_COVERAGE_LOW`
- `RAW_PERIOD_COVERAGE_LOW`
- `RAW_UNIT_AMBIGUOUS`
- `RAW_UNIT_COVERAGE_LOW`

The exact action/reviewability mapping must match current P9 design.

Any mismatch is a blocker.

---

## 6. Fresh live review roots

Do not reuse the earlier temporary P9-I directories.

Create fresh candidate-bound review roots under the allowed workspace, for example:

```text
D:\Codex\FinancialFilingDataFoundation\workspace\p9-live-review\8edece62-cn-a
D:\Codex\FinancialFilingDataFoundation\workspace\p9-live-review\8edece62-cn-b
D:\Codex\FinancialFilingDataFoundation\workspace\p9-live-review\8edece62-hk-a
D:\Codex\FinancialFilingDataFoundation\workspace\p9-live-review\8edece62-hk-b
```

If any proposed root already exists from unknown/earlier work:
- do not delete it；
- choose another deterministic candidate-bound suffix and record it。

Only these review roots may change during P9-I.

Do not commit review-root contents to Git.

---

## 7. Mandatory before fingerprint snapshot

Before running any P9 live operation, record for:

- canonical P8 catalog；
- CN cataloged P3 files；
- CN cataloged P5 files；
- CN cataloged P6 files；
- CN cataloged P7 files；
- HK cataloged P3 files；
- HK cataloged P5 files；
- HK cataloged P6 files；
- HK cataloged P7 files。

For every file record:
- absolute or project-relative path；
- SHA256；
- size；
- `mtime_ns`。

Artifact paths must come from the catalog.

Do not infer alternate paths.

Save the fingerprint evidence outside raw/source artifact directories.

---

## 8. CN live procedure

### 8.1 Prepare

Prepare CN in root A.

Record:
- prepare first-load elapsed time；
- manifest SHA；
- queue SHA；
- queue count；
- exact reason/action mapping。

Run prepare again against the same root and record:
- reuse elapsed time；
- returned artifact equality；
- manifest/queue unchanged。

Performance design target:
- first prepare <= 20s；
- reuse <= 2s。

A performance miss must be recorded honestly. Do not optimize production during this Gate.

### 8.2 Select one evidence-grounded SET_PERIOD

Inspect the CN task and trusted P5/P6 evidence only.

Submit **at least one** `SET_PERIOD` resolution satisfying all of:
- targets a raw-null period fact or permitted table-column target；
- value is supported by existing trusted P5/P6 evidence；
- evidence refs are valid；
- no guessed mass fill；
- no value invented merely to cross the 0.10 coverage threshold。

If the artifacts do not contain sufficient evidence for a valid period value:
STOP and report P9-I blocked for CN.
Do not guess.

Record:
- review_task_id；
- target；
- submitted value；
- evidence refs/pages；
- resolution_id；
- base_active_resolution_ids；
- base_overlay_set_hash_before。

Submit timing target:
- <= 2s。

### 8.3 Materialize

Materialize CN.

Required:
- at least one raw-null `raw_period_label` remains null in raw fields；
- corresponding resolved fact has non-null `effective_period_label` from the explicit overlay；
- all original raw fields remain byte/semantic unchanged；
- overlay resolution IDs are visible；
- status is honest。

If effective period coverage remains below the P7 threshold:
- final resolved status **must remain `REVIEW_REQUIRED`**。

Do not force PASS.

Record:
- overlay_set_hash；
- active resolution IDs；
- resolved facts hash；
- resolved issues hash；
- resolution report hash；
- resolved status；
- resolved reuse eligibility；
- period coverage before/after；
- materialize elapsed time。

Performance design target:
- materialize <= 10s。

### 8.4 Snapshot load

Load the materialized snapshot through the P9 semantic loader.

Record:
- load elapsed time；
- same overlay hash；
- same report semantics。

Target:
- <= 10s。

---

## 9. HK live procedure

Prepare HK in root A.

Record:
- first/reuse timings；
- manifest/queue hashes；
- queue count = 4；
- exact four reason codes；
- exact supported/unsupported action mapping。

Do **not** manufacture resolutions merely to make HK pass.

P9-I acceptance for HK does not require forced dismissal.

Materialize the zero-overlay or only legitimately evidence-supported state.

Required:
- unsupported/unresolved conditions remain honest；
- no forced `ATTEST_ISSUE_RESOLVED`；
- no guessed unit/period；
- status reflects actual unresolved conditions。

Record:
- overlay_set_hash；
- active resolution count/IDs；
- resolved status；
- unresolved/unsupported issue states；
- materialize/load timings；
- snapshot hashes。

---

## 10. Dual-root determinism

For CN and HK, repeat the base preparation in root B from the same canonical artifacts.

Required deterministic checks:

### Base preparation
For root A vs B:
- `review_queue.jsonl` bytes identical；
- queue SHA identical；
- deterministic task IDs identical；
- review manifest semantics identical except allowed path/root-location fields explicitly designed to differ。

### CN resolution/materialization determinism

Reproduce the **same explicit CN resolution submission** in CN root B:
- same reviewer metadata including exact caller-supplied reviewed_at；
- same justification；
- same target/value/evidence。

Required:
- same resolution_id；
- same canonical resolution payload bytes；
- same overlay_set_hash；
- same resolved_facts bytes；
- same resolved_issues bytes；
- same resolution_report semantic content；
- same resolved parse identity where constructed。

If root-dependent path fields make manifest bytes differ, compare according to design semantics rather than falsely claiming byte identity for path-bearing manifest fields.

### HK
For equivalent zero-overlay state:
- same overlay_set_hash；
- same resolved snapshot bytes/semantics。

---

## 11. Mandatory after fingerprint snapshot

After **all** P9 live operations, repeat the exact fingerprint snapshot from section 7.

For every catalog/P3/P5/P6/P7 file:

- SHA256 before == after；
- size before == after；
- mtime_ns before == after。

Any difference:

**P9-I FAIL / STOP**

Do not repair or restore the changed base file during this Gate; report exact path and mismatch.

Only designated review roots may have changed.

---

## 12. No source mutation / scope check

After live execution verify:
- Git tracked production/tests/design unchanged；
- no catalog changes；
- no P3/P5/P6/P7 changes；
- no Registry change；
- no source PDF access；
- no network/AI/Codex API；
- no external MCP SDK；
- no P10/P11 work。

Run:

```powershell
git status --short --branch --untracked-files=all
git diff --check
```

Live review roots must remain outside the committed candidate.

---

## 13. P9-I evidence file

Create:

`development/59-p9-i-live-evidence.md`

It must record at least:

### Candidate identity
- starting/final branch HEAD；
- production corrective commit；
- P9-G re-review authorization commit。

### Catalog/base identity
- canonical catalog path；
- catalog SHA/size/mtime_ns；
- CN/HK document SHAs；
- base P7 status；
- base validation report SHAs。

### CN
- queue count/reason/actions；
- queue hash；
- selected evidence-grounded resolution；
- resolution ID；
- evidence refs/pages；
- before/after effective fact proof；
- raw period remains null；
- period coverage；
- resolved status；
- overlay hash；
- snapshot hashes；
- prepare/reuse/submit/materialize/load timings；
- dual-root determinism result。

### HK
- queue count = 4；
- exact reason set/actions；
- unresolved/unsupported outcome；
- no forced dismissal；
- overlay hash；
- snapshot hashes；
- prepare/reuse/materialize/load timings；
- dual-root determinism result。

### Immutability
- before/after fingerprint table or referenced machine-readable evidence；
- explicit result that every catalog/P3/P5/P6/P7 SHA/size/mtime_ns is unchanged。

### Scope
- Git status/diff；
- no network/AI/PDF/Registry/P10/P11；
- blockers。

Do not include huge raw artifacts in Git.

Small machine-readable fingerprint summaries may be committed under development evidence only if useful and contain no source content/secrets.

---

## 14. Commit/push

P9-I should not modify production/tests.

Expected Git change is evidence/documentation only.

Before commit:

```powershell
git status --short --branch --untracked-files=all
git diff --check
git diff
```

Ensure live review roots are not staged.

Commit evidence normally.

Suggested message:

`test: record P9 live CN HK validation`

Push normally to:

`origin/task/p9-review-overlay`

No force push.

If remote advanced, STOP and report; do not self-authorize merge.

---

## 15. PASS / STOP rule

P9-I can be reported PASS only if:
- CN queue = 1 exact reason；
- CN has >=1 genuinely evidence-grounded SET_PERIOD；
- raw period remains immutable while effective period is visible；
- CN resolved status is honest；
- HK queue = 4 exact reason set；
- HK has no forced dismissal；
- dual-root/repeated materialization deterministic；
- all base fingerprints unchanged；
- no scope violation。

If any item fails:
STOP and report the exact discrepancy.

---

## 16. Stop point

After successful evidence push:

STOP.

Do not execute:
- P9-J formal Code Review；
- P9-K Acceptance Freeze；
- P9-L Independent Acceptance；
- P9-M Closeout；
- main merge；
- P10；
- P11。

Wait for GitHub review of P9-I evidence.
