# 55 — P9-G Corrective Implementation Instruction

Status: **ACTIVE CORRECTIVE INSTRUCTION**

Phase:
`P9 — Codex Review Overlay`

Target branch:
`task/p9-review-overlay`

Review basis:
`development/54-p9-g-github-code-review.md`

This instruction authorizes correction of **F1-F5 only**.

It does not authorize P9-I or any later gate.

---

## 1. Start from current GitHub truth

Before modifying production:

```powershell
cd D:\Codex\FinancialFilingDataFoundation\worktrees\active\p9-review-overlay
git status --short --branch --untracked-files=all
git fetch origin
git rev-parse HEAD
git rev-parse origin/task/p9-review-overlay
git log --oneline --decorate -12
```

The remote branch now contains the GitHub review evidence.

If the local branch is only behind by governance/review documentation and there are no conflicting uncommitted production/test edits, use a safe fast-forward:

```powershell
git merge --ff-only origin/task/p9-review-overlay
```

If fast-forward is not safe, STOP and report exact state.

Do not reset/rebase/clean/force/overwrite.

---

## 2. Read before changing

Read in full:
- `design/22-p9-review-overlay-design.md`
- `development/51-p9-codex-local-execution-instruction.md`
- `development/52-p9-g-development-evidence.md`
- `development/54-p9-g-github-code-review.md`
- current P9 source/test files

The current design already specifies the intended semantics for F1-F5.

Do not amend architecture or invent new behavior.

If a correction cannot be implemented without changing design semantics, STOP and report the exact ambiguity.

---

## 3. F1 — semantic validation of the complete immutable resolution history

Correct the current split where:
- `list_resolutions()` performs only canonical/file checks；
- `_validate_graph()` performs structural prior/supersession checks；
- semantic recomputation lives only in resolve/materialize paths；
- `submit_resolution()` can consume existing active records before every historical record has been semantically recomputed。

Required result:

Before existing resolution history is used for:
- a new submit；
- active resolution computation exposed through public APIs；
- materialization；
- snapshot load；
- CLI `resolutions`；

the complete immutable history must be validated against current immutable base artifacts.

Validation must include every persisted resolution, including superseded historical records:
1. canonical file/id validation；
2. prior-state/hash validation；
3. supersession/dependency graph validation；
4. reviewer/timestamp validation；
5. target semantics；
6. direct evidence or inherited attestation evidence；
7. evidence pages；
8. recomputed `before`；
9. recomputed `after`；
10. document/base-report/task/reason identity。

Do not trust persisted `before["affected_fact_ids"]` until the record has passed semantic recomputation.

### Implementation guidance

Use one authoritative semantic validation implementation.

Avoid duplicating the same semantics independently in `store.py` and `resolve.py`.

A valid approach is to move/refactor the current semantic recomputation helper into a layer usable by the store loader and resolver without introducing import cycles.

The exact internal function name is not prescribed.

### Mandatory F1 tests

Add tests proving:
- a re-signed historical resolution with tampered `before.affected_fact_ids` is rejected on a subsequent `submit_resolution()` before any new resolution file is written；
- a re-signed tampered superseded parent is rejected even when the terminal child itself is structurally valid；
- tampered support-resolution evidence cannot be inherited by a later attestation；
- validated `list_resolutions` / CLI `resolutions` rejects semantic store corruption；
- normal valid supersession/attestation history still passes。

No design weakening is allowed.

---

## 4. F2 — preserve submitted trimmed fill value

For `SET_PERIOD`, `SET_UNIT`, `SET_SCOPE`:

Required distinction:

### Persistence/effective value
Use:

`submitted value with leading/trailing whitespace trimmed only`

Do not collapse internal whitespace for the persisted resolution value or resolved effective value.

### Comparison value
Whitespace-collapsed normalization may be used for:
- raw explicit value equivalence；
- no-op/conflict comparison where the design requires normalized comparison。

Statement classification remains the fixed enum exception.

Do not translate/canonicalize period/unit/scope semantics.

### Mandatory F2 tests

Prove:
- input `"  人民币   百万元  "` persists as `"人民币   百万元"`；
- resolved effective value preserves the internal spacing；
- raw comparison still treats whitespace-equivalent explicit raw text as equivalent according to Section 18；
- ordinary existing fill-only tests remain green。

---

## 5. F3 — justification max 4000 persisted characters

Correct reviewer validation to enforce the design exactly:

- justification must contain non-whitespace text；
- persisted raw justification length must be **<= 4000 characters**；
- whitespace collapsing must not allow a raw payload longer than 4000 characters to pass；
- do not silently truncate。

Mandatory boundary tests:
- 4000 chars: accepted；
- 4001 chars: rejected with `P9_INVALID_RESOLUTION`；
- >4000 whitespace-heavy raw input with short normalized text: rejected；
- empty/whitespace-only input: rejected。

Do not change the audit-only/non-execution behavior of justification.

---

## 6. F4 — remove random UUID from P9 production

`queue.prepare_review_overlay()` must no longer use `uuid.uuid4()` or another random identity source.

Use a deterministic staging strategy consistent with:
- atomic finalization；
- no destructive cleanup of unknown state；
- append-only governance；
- deterministic P9 production。

A suitable approach is a deterministic document-bound staging path.

Important:
- if a staging path already exists and was not created by the current operation, do not blindly delete it；
- fail safely with an appropriate P9 persistence/corruption error；
- only clean up a temp directory that the current operation itself successfully created。

Do not use implicit current time as a replacement.

Mandatory test/scope assertion:
- P9 review production contains no random UUID/random identity generation.

---

## 7. F5 — complete the required CLI test matrix

Add direct CLI coverage for all required surfaces:

- `prepare`
- `tasks`
- `submit --input-json`
- `submit --input-file`
- `resolutions`
- `materialize`
- `report`
- malformed JSON
- non-object JSON

For successful invocations:
- return code 0；
- stdout contains exactly one valid JSON document；
- stderr empty。

For handled failures:
- stdout empty；
- stderr contains the deterministic diagnostic；
- non-zero return code。

Do not rely only on calling the underlying Python APIs.

The CLI itself must be exercised.

---

## 8. Regression requirements

After corrections, rerun with short basetemp:

```powershell
$env:PYTHONPATH="D:\Codex\FinancialFilingDataFoundation\worktrees\active\p9-review-overlay\src"
New-Item -ItemType Directory -Force D:\Codex\FFDF-t\p9 | Out-Null

D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -m compileall src\financial_filing_data_foundation\review

D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -m pytest tests\unit\review\test_review_overlay.py -q --basetemp D:\Codex\FFDF-t\p9\corrective-focused

D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -m pytest tests\unit -q --basetemp D:\Codex\FFDF-t\p9\corrective-full

git diff --check
```

Also rerun:
- import check；
- no network/AI/OpenAI/Codex API；
- no external MCP SDK；
- no PDF reopen；
- no Registry mutation；
- raw/source immutability check；
- synthetic REVIEW_REQUIRED → PASS；
- no P10/P11 production。

Use current actual test counts.

---

## 9. Evidence

Create:

`development/56-p9-g-corrective-evidence.md`

Record:
- starting remote HEAD；
- corrective files changed；
- F1 fix summary and tamper tests；
- F2 value-preservation tests；
- F3 4000-char boundary tests；
- F4 deterministic staging/no-random check；
- F5 full CLI matrix results；
- focused count/result；
- full unit count/result；
- compile/import；
- diff check；
- scope；
- immutability；
- synthetic；
- blocker status；
- final corrective candidate SHA。

Do not overwrite historical `development/52`; it remains evidence for the prior reviewed candidate.

---

## 10. Commit / push

Before commit:

```powershell
git status --short --branch --untracked-files=all
git diff --check
git diff
```

Ensure only corrective P9 source/tests/evidence are included.

No temporary P9-I artifacts.

Commit normally.

Suggested message:

`fix: harden P9 resolution validation and deterministic contracts`

Push normally to:

`origin/task/p9-review-overlay`

No force push.

If remote advanced again, STOP and report.

---

## 11. Stop point

After successful push:

STOP.

Do not execute:
- P9-I
- P9-J
- P9-K
- P9-L
- P9-M
- main merge
- P10
- P11

The corrective candidate must receive another GitHub code review first.

---

## 12. Final report

Return:
- remote branch HEAD；
- corrective commit SHA；
- files changed；
- focused result；
- full unit result；
- compile/import；
- diff check；
- scope；
- immutability；
- synthetic；
- evidence file pushed；
- blocker status。

Do not continue beyond this task.
