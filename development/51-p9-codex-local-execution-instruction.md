# 51 — P9 Codex Local Execution Instruction — Recovery + P9-G

状态：**ACTIVE DEVELOPMENT INSTRUCTION**

Phase:
`P9 — Codex Review Overlay`

Target branch:
`task/p9-review-overlay`

GitHub design/governance baseline at instruction creation:
`0f9f6a8ffc75b0d4d11eb96f21397c65a0720ca9`

This instruction is intentionally limited to one reviewable development gate.

---

## 1. Authority / truth sources

GitHub is the design/version truth source.

The WorkHome active worktree is the truth source for any existing uncommitted P9 production/tests.

Canonical worktree:

`D:\Codex\FinancialFilingDataFoundation\worktrees\active\p9-review-overlay`

Before coding, read in full:

- `design/00-design-management-index.md`
- `design/01-project-detailed-design.md`
- `design/22-p9-review-overlay-design.md`
- `design/23-p9-implementation-plan.md`
- `development/48-p9-development-instruction.md`
- `development/49-p9-environment-audit.md`
- `development/50-p9-baseline-refresh-audit.md`
- `acceptance/32-p9-acceptance-instruction.md`
- `PROJECT_STATUS.md`

Pay special attention to P9-ISSUE-002 / 003 / 004.

Do not infer behavior from this instruction when the current design files are more specific.

---

## 2. Hard governance rules

Design-First remains mandatory.

If implementation exposes a design ambiguity, contradiction, missing contract, or correctness problem:

`STOP current Gate → identify exact root cause → DO NOT patch production first → report the issue for design amendment`

For this task, Codex is **not authorized to invent or amend architecture/design semantics**.

Do not continue production changes across a design gap.

Forbidden:

- `git reset --hard`
- destructive reset
- `git clean`
- force push
- history rewrite
- checkout/restore that overwrites existing uncommitted P9 files
- deleting untracked P9 production/tests
- rebuilding local P9 files from GitHub merely because they are untracked
- changing P0-P8 accepted production/tests without explicit design authorization
- modifying raw/source artifacts
- source PDF reopen
- network/AI/OpenAI/Codex API inside P9 production
- external MCP SDK dependency
- Registry mutation
- P10/P11 implementation
- guessing missing data
- silent fallback/correction

---

## 3. Mandatory recovery inspection — no writes before completion

Run first:

```powershell
cd D:\Codex\FinancialFilingDataFoundation\worktrees\active\p9-review-overlay

git status --short --branch --untracked-files=all
git fetch origin
git rev-parse HEAD
git rev-parse origin/task/p9-review-overlay
git rev-parse origin/main
git log --oneline --decorate -15
git diff --stat
git diff --name-only
git ls-files --others --exclude-standard
git rev-list --left-right --count HEAD...origin/task/p9-review-overlay
```

Then inspect:

```powershell
Get-ChildItem src\financial_filing_data_foundation\review -Force
Get-ChildItem tests\unit\review -Force
```

Read every existing P9 file before modifying it, especially:

- `review/models.py`
- `review/evidence.py`
- `review/queue.py`
- `review/store.py`
- `review/resolve.py`
- `review/cli.py` if present
- `review/__init__.py` if present
- `tests/unit/review/test_review_overlay.py`

An earlier remote-tool history indicates that `review/cli.py` may already have been written. Do not overwrite it from an old handoff assumption.

---

## 4. Safe synchronization rule

If local HEAD is behind `origin/task/p9-review-overlay`, synchronize only after confirming the incoming changes are design/governance-only and do not collide with existing local work.

Preferred operation when safe:

```powershell
git merge --ff-only origin/task/p9-review-overlay
```

If fast-forward is not safe because of tracked conflicts or unexpected state:

**STOP. Do not reset, clean, checkout, restore, or reconstruct files.**

Report:
- local HEAD
- remote HEAD
- exact status
- conflicting paths
- why fast-forward is unsafe

No production change is authorized until the state is understood.

---

## 5. Re-establish current development truth

Historical handoff evidence reported:

- P9 core compile/import PASS
- focused tests: `7 passed`
- full unit regression: `242 passed / 0 fail`

These are historical only.

Re-run current truth using main runtime:

`D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe`

Set:

```powershell
$env:PYTHONPATH="D:\Codex\FinancialFilingDataFoundation\worktrees\active\p9-review-overlay\src"
New-Item -ItemType Directory -Force D:\Codex\FFDF-t\p9 | Out-Null
```

Compile/import current P9 modules before editing.

Use short pytest basetemp under:

`D:\Codex\FFDF-t\p9\...`

Do not use deep worktree pytest temp paths.

If a failure is only Windows path-length/environment setup, correct the command/environment rather than product semantics.

---

## 6. Authorized implementation scope — P9-G only

Complete/repair the existing local implementation for:

- `src/financial_filing_data_foundation/review/__init__.py`
- `src/financial_filing_data_foundation/review/cli.py`

The CLI entrypoint is:

`python -m financial_filing_data_foundation.review.cli`

Required subcommands:

- `prepare`
- `tasks`
- `submit`
- `resolutions`
- `materialize`
- `report`

The CLI must call the already-designed P9 APIs. Do not reimplement store/materialization semantics in the CLI.

Required API behavior remains defined by `design/22`.

---

## 7. CLI contract

Success:

- stdout contains JSON only
- exactly one valid JSON document per invocation
- no banner/debug/progress/log text on stdout

Diagnostics/errors:

- stderr only
- deterministic reason code/message
- non-zero exit code on failure

Requirements:

- deterministic
- no current-time-generated audit data
- no network
- no AI/OpenAI/Codex API
- no external MCP SDK
- no arbitrary path execution
- no arbitrary secret reading
- submission input only from explicit JSON string/file supplied by caller
- no Registry writes
- no source artifact mutation

Do not swallow `ReviewError` into a generic success response.

Preserve designed P9 reason codes where applicable.

---

## 8. Authorized test additions

Extend the existing P9 unit tests only as needed to cover this Gate and currently missing acceptance negatives.

At minimum cover, if not already present:

1. CLI success stdout is valid JSON only.
2. CLI diagnostics/errors go to stderr and return non-zero.
3. prepare/tasks/resolutions/materialize/report serialization is deterministic.
4. submit accepts explicit JSON string.
5. submit accepts explicit JSON file.
6. malformed/non-object submission rejected.
7. attestation inherits evidence from active supporting resolutions.
8. caller direct evidence for attestation rejected.
9. unsupported REVIEW reason remains unresolved.
10. conflicting active overlay values fail.
11. same-value overlap remains deterministic.
12. invalid supersession parent rejected.
13. cycle rejected.
14. competing child rejected.
15. raw non-null same-value no-op rejected.
16. raw non-null conflicting patch rejected.
17. tampered prior-state contract/hash rejected.
18. base artifact fingerprint mutation rejected.
19. snapshot semantic tamper rejected.
20. FAIL/BLOCKED base rejected.
21. no network/AI/external MCP SDK usage.
22. raw/source artifacts unchanged.

Do not manufacture tests that weaken the design merely to pass.

---

## 9. P9-ISSUE-002 invariant

For `ATTEST_ISSUE_RESOLVED`:

Caller direct authoritative evidence is not allowed.

Persisted attestation evidence must be derived from active same-issue `supporting_resolution_ids`:

`supporting resolutions → validate → union persisted evidence refs → deterministic dedupe/sort → derive evidence_pages → persist`

Empty inherited evidence must fail.

---

## 10. P9-ISSUE-003 invariant

Every persisted resolution must bind the explicit prior active overlay state:

- `base_active_resolution_ids`
- `base_overlay_set_hash_before`

Do not use `reviewed_at` to infer historical execution order.

Loader/store validation must preserve:

- caller cannot override prior set/hash
- superseded parent is in prior active set
- attestation supports are in prior active set
- prior set has no internally superseded member declared active
- dependency graph is acyclic
- hash recomputes
- `before` recomputes from raw base + explicit prior set
- later resolutions cannot change historical before-state

If the current implementation violates any of these and the fix is already fully specified by current design, fix it and test it.

If design is insufficient, STOP and report.

---

## 11. Required verification before push

Run at minimum:

```powershell
python -m compileall src\financial_filing_data_foundation\review
python -m pytest tests\unit\review\test_review_overlay.py -q --basetemp D:\Codex\FFDF-t\p9\focused
python -m pytest tests\unit -q --basetemp D:\Codex\FFDF-t\p9\full
git diff --check
```

Also perform a scope scan confirming P9 changes do not introduce:

- OpenAI/Anthropic/Codex API calls
- requests/httpx/socket-based network behavior
- external MCP SDK import
- PDF reopen
- Registry mutation
- P10/P11 production

Record exact current test counts; do not reuse historical counts.

---

## 12. Development evidence required

Create:

`development/52-p9-g-development-evidence.md`

It must record:

- starting local HEAD
- starting remote P9 branch HEAD
- safe-sync result
- list of pre-existing uncommitted/untracked P9 files found
- files modified by this task
- P9-G CLI command contract verified
- exact focused test command/result/count
- exact full unit command/result/count
- compileall result
- `git diff --check` result
- scope scan result
- network/AI/MCP SDK result
- raw/source mutation check
- blocker status
- candidate commit SHA after commit
- statement that P9-I/J/K/L/M were NOT executed in this task

Do not claim Independent Acceptance.

---

## 13. Commit/push boundary

Before committing:

```powershell
git status --short --branch --untracked-files=all
git diff --check
git diff
```

Ensure no:
- temp output
- pytest caches
- live review artifacts
- raw/source changes
- secrets
- unrelated P0-P8 edits

Then commit production/tests/evidence normally and push to:

`origin/task/p9-review-overlay`

No force push.

Suggested commit message:

`feat: complete P9 local review CLI and negative coverage`

If multiple normal commits are clearer, that is acceptable, but all must stay on the P9 branch.

---

## 14. STOP conditions

Stop without continuing to P9-H/I when any of these occurs:

- design ambiguity/contradiction
- unexpected tracked conflict during sync
- P0-P8 regression attributable to P9 changes
- raw/source mutation
- unresolved security/scope violation
- failing P9 tests
- inability to prove JSON-only CLI behavior
- inability to preserve P9-ISSUE-002/003 invariants

Report exact evidence instead of guessing.

---

## 15. Explicitly NOT authorized in this task

Do NOT execute:

- P9-I live CN/HK acceptance
- detached P9-J formal Code Review
- P9-K Acceptance Freeze
- P9-L Independent Acceptance
- P9-M Closeout
- merge to main
- P10 implementation/design beyond existing baseline
- P11

The next Gate will be authorized only after GitHub review of this pushed candidate.

---

## 16. Final response after push

Return exactly enough information for independent GitHub review:

- remote branch
- final commit SHA
- commits created
- files changed
- focused test result
- full unit result
- compileall result
- diff-check result
- scope scan result
- any design issue/blocker
- whether `development/52-p9-g-development-evidence.md` was pushed

Do not continue to the next Gate after push.
