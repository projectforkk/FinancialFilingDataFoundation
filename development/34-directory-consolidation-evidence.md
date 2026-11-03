# 34 — Project Directory Consolidation Evidence

状态：**PASS**

Design baseline:
- `design/15-project-directory-management.md`
- directory design commits: `68a647c`, `50af94d`, `05b440a`
- runtime lock commit: `b5d2132`

## 1. Canonical Root

`D:\Codex\FinancialFilingDataFoundation`

Final:
- canonical Git checkout = root directory
- branch = `main`
- root tracked status = clean

## 2. Sibling Consolidation

Before migration, FFDF-owned sibling directories existed under `D:\Codex`:
- main-sync worktree
- P1–P5 development/review/acceptance worktrees
- `D:\Codex\dependencies\dayu-agent`
- `D:\Codex\runtimes\ffdf-dayu-2115c86`

After migration:
- no project-owned `FinancialFilingDataFoundation-*` sibling remains
- no FFDF-owned dependency/runtime remains outside project root

## 3. Worktrees

Final Git worktree count: `24`.

All worktree paths are within:

`D:\Codex\FinancialFilingDataFoundation\worktrees\...`

Historical clean worktrees:
`worktrees\archive\clean\`

Historical dirty worktrees:
`worktrees\archive\dirty\`

Dirty historical P1 worktrees were moved intact. Pre/post status equality was verified.

Local migration manifest:
`workspace\archive\directory-migration\dirty-worktrees-migration.json`

No reset/clean/force push was used.

## 4. Main Checkout Consolidation

Old linked main worktree:
`D:\Codex\FinancialFilingDataFoundation-main-sync-p1`

Its ignored workspace was preserved under:
`workspace\archive\main-sync-p1`

The linked main worktree was then removed through `git worktree remove`.

Canonical root was switched to current `main`.

## 5. Dayu Source

Old:
`D:\Codex\dependencies\dayu-agent`

New:
`D:\Codex\FinancialFilingDataFoundation\dependencies\dayu-agent`

Verified:
- commit: `2115c86d5a9027bb51cbbc8a4d0175080732e4e6`
- status: clean

## 6. Dayu Runtime Reproducibility Finding

Initial rebuild from the same Dayu source commit resolved newer transitive versions:
- docling 2.145.0 → 2.146.0
- docling-slim 2.145.0 → 2.146.0
- filelock 4.2.6 → 4.2.7

This first rebuild was rejected.

Design issue:
`DIR-ISSUE-002`

Tracked lock:
`runtime-locks/dayu-2115c86-py312-win-amd64.lock.txt`

Lock contains 146 exact third-party packages.
Dayu is installed separately from the pinned checkout with `--no-deps`.

## 7. Final Dayu Runtime

New:
`D:\Codex\FinancialFilingDataFoundation\runtimes\ffdf-dayu-2115c86\.venv`

Verified:
- Python: 3.12.14 AMD64
- dayu-agent: 0.1.4
- docling: 2.145.0
- docling-slim: 2.145.0
- filelock: 4.2.6
- torch: 2.15.0

Old/new normalized package snapshots:
**MATCH**

Old external runtime was retired only after all checks passed.

## 8. Dayu Doctor

Final doctor:
- status: OK
- source pin: PASS
- source clean: PASS
- module origin: new project-local runtime site-packages
- network_used: false
- docling_conversion_used: false

Doctor request/response:
`workspace\archive\directory-migration\doctor\`

## 9. FFDF Main Runtime Isolation

From canonical project root:
- dayu: absent
- docling: absent
- torch: absent

PASS.

## 10. Regression

Full unit/regression suite after migration:

`156 passed in 4.47s`

`git diff --check`: PASS.

## 11. Final Directory Gate

- canonical root: PASS
- root main/clean: PASS
- all worktrees inside root: PASS
- dependency inside root: PASS
- runtime inside root: PASS
- runtime lock: PASS
- Dayu doctor: PASS
- main runtime isolation: PASS
- historical dirty states preserved: PASS
- full regression: PASS
- source/history loss: NONE

Final verdict:

# PASS
