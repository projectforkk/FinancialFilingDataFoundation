# 157 — P11 Formal Acceptance Evidence

## Execution identity

- production_candidate: `05e06096bc8b788d0467a1ce3442829e87727b6`
- formal_test_plan: `development/156-p11-formal-test-plan.md`
- formal_test_plan_commit: `ccd506edc44b677457cd42347499f41cfe2b271a`
- development_branch: `task/p11-sec-rebuild-development`
- execution_branch_head: `ccd506edc44b677457cd42347499f41cfe2b271a`
- execution_worktree: `D:\Codex\FinancialFilingDataFoundation\worktrees\active\p11-sec-rebuild-development`
- isolated_ffdf_root: `D:\Codex\FinancialFilingDataFoundation\work\p11-formal-acceptance-05e06096`
- python: `Python 3.14.9`
- execution_date: `2026-11-10` (Asia/Tokyo)
- `FFDF_SEC_CONTACT_EMAIL` configured: `NO`
- actual SEC contact value: not recorded

Raw evidence files are under [`../work/p11-formal-acceptance-05e06096/evidence/`](../work/p11-formal-acceptance-05e06096/evidence/).

## Freeze and preflight

FT-00: **PASS**.

The preflight recorded:

- branch: `task/p11-sec-rebuild-development`
- `HEAD`: `ccd506edc44b677457cd42347499f41cfe2b271a`
- candidate revision resolved exactly to `05e06096bc8b788d0467a1ce3442829e87727b6`
- working tree status before evidence creation: clean
- post-candidate changed paths: `development/153-p11-code-review-result-3.md`, `development/154-p11-repair-development-evidence-3.md`, `development/155-p11-code-review-result-4.md`, `development/156-p11-formal-test-plan.md`
- post-candidate production/test source paths: none
- working-tree `git diff --check`: pass
- post-candidate documentation diff check: pass

Raw preflight: [`FT-00-preflight.txt`](../work/p11-formal-acceptance-05e06096/evidence/FT-00-preflight.txt).

Because `FFDF_SEC_CONTACT_EMAIL` was not configured, the plan's SEC precondition stopped all live SEC acquisition before any network request. All offline gates were still executed.

## Formal tests

### FT-01 — Apple 2025 10-K

**BLOCKED** — live SEC acquisition was not run because `FFDF_SEC_CONTACT_EMAIL` was not configured. The frozen accession `0000320193-25-000079` was not observed, and no live package SHA, member SHA, Raw Fact count, Evidence count, validation result, or P8 catalog result exists.

### FT-02 — Apple 2025 Q3 10-Q

**BLOCKED** — live SEC acquisition was not run because `FFDF_SEC_CONTACT_EMAIL` was not configured. The frozen accession `0000320193-25-000073` was not observed, and no live package or parsed-artifact result exists.

### FT-03 — Custom extension / Evidence / hidden iXBRL

**BLOCKED** — depends on the live-ingested FT-02 package, which was unavailable under the contact gate. No live `aapl:` fact or hidden-fact count was asserted. The deterministic custom/hidden Evidence checks required by the plan passed within FT-06; see [`FT-06-required-unit-tests-rerun-short-basetemp.stdout.txt`](../work/p11-formal-acceptance-05e06096/evidence/FT-06-required-unit-tests-rerun-short-basetemp.stdout.txt).

### FT-04 — Kellanova original + amendment

**BLOCKED** — live SEC discovery was not run because `FFDF_SEC_CONTACT_EMAIL` was not configured. The planned expected reason `P11_AMENDED_VARIANT_PRESENT` was not observed live; no original or amendment package was bound.

### FT-05 — Toyota 2025 20-F

**BLOCKED** — live SEC acquisition was not run because `FFDF_SEC_CONTACT_EMAIL` was not configured. The frozen accession `0001193125-25-142326` was not observed, and no live package/member, fact, Evidence, validation, or P8 result exists. The deterministic FPI 20-F/40-F annual-only policy test passed in FT-06.

### FT-06 — Negative / security / Evidence

**PASS** after an execution-environment retry. The required named tests were run together and passed: `29 passed in 1.32s`.

- Final selected-test output: [`FT-06-required-unit-tests-rerun-short-basetemp.stdout.txt`](../work/p11-formal-acceptance-05e06096/evidence/FT-06-required-unit-tests-rerun-short-basetemp.stdout.txt)
- Final selected-test metadata and exit code: [`FT-06-required-unit-tests-rerun-short-basetemp.meta.txt`](../work/p11-formal-acceptance-05e06096/evidence/FT-06-required-unit-tests-rerun-short-basetemp.meta.txt)
- The first supplementary run used a long basetemp name and stopped one test at Windows `WinError 206`; that raw failure is preserved in [`FT-06-required-unit-tests.stdout.txt`](../work/p11-formal-acceptance-05e06096/evidence/FT-06-required-unit-tests.stdout.txt). No production assertion failed in that run; the required tests passed when rerun with a shorter basetemp inside the same acceptance workspace.

### FT-07 — Throttling / access denied simulation

**PASS** using the acceptance-only harness [`ft07_throttling_harness.py`](../work/p11-formal-acceptance-05e06096/tmp/ft07_throttling_harness.py).

- HTTP 429: 3/3 attempts, final reason `P11_SEC_RATE_LIMITED`, retry delays `[1.0, 1.0]`, no success
- HTTP 403: 3/3 attempts, final reason `P11_SEC_ACCESS_DENIED`, retry delays `[1.0, 2.0]`, no success
- Final harness output: [`FT-07-throttling-access-denied-harness-rerun.stdout.txt`](../work/p11-formal-acceptance-05e06096/evidence/FT-07-throttling-access-denied-harness-rerun.stdout.txt)
- Final harness exit metadata: [`FT-07-throttling-access-denied-harness-rerun.meta.txt`](../work/p11-formal-acceptance-05e06096/evidence/FT-07-throttling-access-denied-harness-rerun.meta.txt)
- An initial harness-only assertion bug was preserved in [`FT-07-throttling-access-denied-harness.stderr.txt`](../work/p11-formal-acceptance-05e06096/evidence/FT-07-throttling-access-denied-harness.stderr.txt); the reviewed production implementation was not changed.

### FT-08 — Live idempotency

**BLOCKED** — depends on FT-01's live Apple package, which could not be acquired because `FFDF_SEC_CONTACT_EMAIL` was not configured. No live before/after package, member, manifest, parser, fact, Evidence, or P8 comparison exists.

## Regression gates

The final runs used a short temporary directory under the project root solely for Windows test fixtures whose planned acceptance-root paths exceeded the Windows path limit. The directory was removed after the runs. Raw stdout/stderr, commands, and exit codes remain in the acceptance workspace.

| Gate | Final result | Evidence |
| --- | --- | --- |
| P11 focused `tests/unit/us_sec` | `53 passed in 1.94s` | [`regression-p11-focused.stdout.txt`](../work/p11-formal-acceptance-05e06096/evidence/regression-p11-focused.stdout.txt), [`regression-p11-focused.meta.txt`](../work/p11-formal-acceptance-05e06096/evidence/regression-p11-focused.meta.txt) |
| Full unit `tests/unit` | `583 passed in 57.77s` | [`regression-full-unit-short-project-temp.stdout.txt`](../work/p11-formal-acceptance-05e06096/evidence/regression-full-unit-short-project-temp.stdout.txt), [`regression-full-unit-short-project-temp.meta.txt`](../work/p11-formal-acceptance-05e06096/evidence/regression-full-unit-short-project-temp.meta.txt) |
| CN/HK regression | `96 passed in 5.08s` | [`regression-cnhk-short-project-temp.stdout.txt`](../work/p11-formal-acceptance-05e06096/evidence/regression-cnhk-short-project-temp.stdout.txt), [`regression-cnhk-short-project-temp.meta.txt`](../work/p11-formal-acceptance-05e06096/evidence/regression-cnhk-short-project-temp.meta.txt) |
| `compileall -q src tests` | `PASS`, exit 0 | [`regression-compileall-short-project-cache.meta.txt`](../work/p11-formal-acceptance-05e06096/evidence/regression-compileall-short-project-cache.meta.txt) |
| `git diff --check` | `PASS`, exit 0 | [`regression-git-diff-check-final.meta.txt`](../work/p11-formal-acceptance-05e06096/evidence/regression-git-diff-check-final.meta.txt) |

The first runs with the literal long acceptance basetemp are also preserved: full unit `31` path-creation failures after `552` passes, CN/HK `1` path-creation failure after `95` passes, and compileall failure caused by the long cache path. The final short-project-temp runs passed without changing production code. Raw records: [`regression-full-unit.meta.txt`](../work/p11-formal-acceptance-05e06096/evidence/regression-full-unit.meta.txt), [`regression-cnhk.meta.txt`](../work/p11-formal-acceptance-05e06096/evidence/regression-cnhk.meta.txt), and [`regression-compileall.meta.txt`](../work/p11-formal-acceptance-05e06096/evidence/regression-compileall.meta.txt).

## Acceptance workspace contents

No live SEC package was created because the contact precondition blocked live execution. The acceptance workspace contains the raw evidence, temporary runner, and acceptance-only FT-07 harness; accepted CN/HK raw/source artifacts were not copied or modified.

## Execution result

- Live SEC: `BLOCKED`
- Live SEC reason: `FFDF_SEC_CONTACT_EMAIL_NOT_SET`
- production source changed during acceptance: `NO`
- P11 focused: `PASS`
- Full unit suite: `PASS`
- CN/HK regression: `PASS`
- compileall: `PASS`
- git diff --check: `PASS`
- execution result: `EXECUTION_BLOCKED`
- final P11 acceptance verdict: not made by the test executor
- main merge: `NOT RUN`
- P11 production availability: `NOT CHANGED`

Next action: `CHATGPT FINAL ACCEPTANCE REVIEW`.
