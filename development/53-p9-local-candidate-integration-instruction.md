# 53 — P9 Codex Local Candidate Integration Instruction

状态：**ACTIVE INTEGRATION INSTRUCTION**

Phase:
`P9 — Codex Review Overlay`

Target branch:
`task/p9-review-overlay`

Supersedes for current execution scope:
- the earlier broad request to continue P9-G through P9-M without intermediate GitHub review.

Still authoritative:
- `development/51-p9-codex-local-execution-instruction.md` for P9-G implementation/test requirements；
- `design/22-p9-review-overlay-design.md` including P9-ISSUE-005；
- `acceptance/32-p9-acceptance-instruction.md` for later acceptance criteria only.

---

## 1. Current known state

Remote governance branch advanced after local implementation work began.

Known remote governance history includes:
- `2c56e38a51f148b86ce6f4754bf9bae7a157fd7e` — P9 Codex local execution instruction；
- `642388a0eea7adef0506be2b236d2cf804db30ba` — P9-ISSUE-005 safe-integration design amendment。

Known local implementation candidate:

`e6f83d560822214ab4ede0e317f853d100b6c9ea`

Reported validation for that candidate:
- focused: `29 passed`
- full unit: `264 passed`
- compile/import: PASS
- scope: PASS
- immutability: PASS
- synthetic REVIEW_REQUIRED → PASS: PASS

These results remain development evidence, not accepted baseline.

P9-I temporary live verification may have been executed locally but was not committed. It is not authorized evidence for this integration task.

---

## 2. Hard prohibitions

Do NOT:
- force push
- reset --hard
- destructive reset
- git clean
- rebase
- history rewrite
- delete/rebuild the local candidate
- overwrite local production/tests from GitHub
- cherry-pick in a way that discards either lineage
- include temporary P9-I live output/artifacts
- continue to P9-I/J/K/L/M
- merge to main
- start P10/P11

---

## 3. Pre-integration inspection

Before any merge:

```powershell
cd D:\Codex\FinancialFilingDataFoundation\worktrees\active\p9-review-overlay

git status --short --branch --untracked-files=all
git fetch origin
git rev-parse HEAD
git rev-parse origin/task/p9-review-overlay
git log --oneline --decorate --graph --all -25
git show --stat --oneline e6f83d560822214ab4ede0e317f853d100b6c9ea
git diff --name-status origin/task/p9-review-overlay...e6f83d560822214ab4ede0e317f853d100b6c9ea
```

Verify:
1. local candidate commit exists；
2. local worktree has no unexpected uncommitted production/test edits beyond known temporary/non-candidate state；
3. remote delta since the candidate base is governance/design only；
4. any temporary P9-I outputs are identified and excluded from integration/push。

If any unexpected production/test delta exists outside `e6f83d...`, STOP and report it.

---

## 4. Authorized integration method

A normal non-destructive merge is authorized.

Preferred lineage:
- preserve local candidate `e6f83d...`；
- merge the current `origin/task/p9-review-overlay` governance head into the local branch；
- produce a merge commit with both histories as parents。

Example:

```powershell
git merge --no-ff origin/task/p9-review-overlay
```

This is authorized **only** after the pre-integration inspection above.

Do NOT use rebase.

---

## 5. Conflict policy

### No conflicts

Complete the merge normally.

### Governance/evidence-only conflicts

Allowed to resolve manually, using:
- latest GitHub design/governance semantics as authoritative；
- factual local development evidence retained where still true。

Typical governance paths may include:
- `design/*.md`
- `development/*.md`
- `PROJECT_STATUS.md`

Do not rewrite historical evidence to claim acceptance.

### Production/test conflicts

If any merge conflict touches:
- `src/financial_filing_data_foundation/review/*.py`
- `tests/unit/review/*.py`
- P0-P8 source/tests

STOP immediately.

Do not choose ours/theirs automatically.
Report exact file/hunks for design review.

---

## 6. Post-merge verification

After a clean governance integration, rerun the P9-G verification required by development/51 using the main runtime and short basetemp:

```powershell
$env:PYTHONPATH="D:\Codex\FinancialFilingDataFoundation\worktrees\active\p9-review-overlay\src"
New-Item -ItemType Directory -Force D:\Codex\FFDF-t\p9 | Out-Null

D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -m compileall src\financial_filing_data_foundation\review

D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -m pytest tests\unit\review\test_review_overlay.py -q --basetemp D:\Codex\FFDF-t\p9\focused-integrated

D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -m pytest tests\unit -q --basetemp D:\Codex\FFDF-t\p9\full-integrated

git diff --check
```

Also rerun:
- import check
- no-network/no-AI/no-external-MCP-SDK scope scan
- raw/source immutability check
- synthetic transition check if it is not already part of the focused suite

Record current exact counts. Do not assume 29/264.

---

## 7. Evidence update

Update or create the development evidence so it accurately records:
- local candidate SHA `e6f83d...`
- remote governance head integrated
- integration method = normal merge, not rebase/reset/force
- whether conflicts occurred
- exact conflict paths if any
- post-integration compile/import results
- focused test count/result
- full unit count/result
- diff check
- scope check
- immutability
- synthetic result
- confirmation that P9-I temporary verification is excluded and not accepted
- confirmation that P9-J/K/L/M were not executed

If `development/52-p9-g-development-evidence.md` already exists in the local candidate, update it only to reflect the integration/re-verification facts. Do not erase earlier factual history.

---

## 8. Push boundary

Before push:

```powershell
git status --short --branch --untracked-files=all
git log --oneline --decorate --graph -15
git diff --check
```

Confirm:
- candidate lineage preserved
- latest remote governance lineage included
- no temporary P9-I artifacts
- no unrelated files
- no secrets
- no P0-P8 unintended changes

Then push normally:

```powershell
git push origin task/p9-review-overlay
```

No force.

If push is rejected again because remote advanced, STOP and report the new remote HEAD. Do not self-authorize another merge.

---

## 9. Stop point

After successful normal push:

STOP.

Do not run:
- P9-I
- P9-J
- P9-K
- P9-L
- P9-M
- main merge
- P10
- P11

The pushed candidate must first be independently reviewed from GitHub.

---

## 10. Final report

Return:
- final remote branch HEAD
- merge commit SHA
- parent SHAs
- files changed by the merge
- whether any conflict occurred
- focused result
- full unit result
- compile/import result
- diff check
- scope check
- immutability result
- synthetic result
- evidence file updated/pushed
- blocker status

Do not continue further.
