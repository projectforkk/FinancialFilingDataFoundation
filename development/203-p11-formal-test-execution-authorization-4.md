# 203 — P11 Formal Test Execution Authorization 4

Status: **FORMAL_TEST_EXECUTION_AUTHORIZED**

This is an execution authorization only. It does not authorize production/test
changes, Formal Acceptance, main merge, or P11 DONE.

## 1. Exact authority

Repository:

`projectforkk/FinancialFilingDataFoundation`

Authoritative remote lineage:

`reconcile/p11-140-143-local-chain`

Design 38:

`92af6205eb8e090994dcece68850eddcd4232392`

Frozen production candidate:

`6eaace08c9ba5fb26809a7e02de5835123fb667a`

Development evidence commit:

`5ce97e18456c9e877c223df7abf01eec53e1f3ad`

Fresh Full Exact-Candidate Review PASS:

`development/201-p11-fresh-full-exact-candidate-review-7.md`

Review commit:

`50baac22baf40b29fd08224b883c7b43f06f7736`

Formal Test Plan:

`development/202-p11-formal-test-plan-4.md`

Exact Formal Test Plan SHA:

`4d2ca9abd9ed60d5b4bee8f2f76a2568baa67030`

Exact-plan review:

```text
FORMAL_TEST_PLAN_PASS
FORMAL_TEST_EXECUTION_AUTHORIZED
```

PC Agent must execute Plan 202 exactly from this authority.

## 2. Start / synchronization

Use the active P11 worktree:

`D:\Codex\FinancialFilingDataFoundation\worktrees\active\p11-sec-rebuild-development`

Start with:

```powershell
Set-Location 'D:\Codex\FinancialFilingDataFoundation\worktrees\active\p11-sec-rebuild-development'
git status --short
git branch --show-current
git fetch origin
git rev-parse HEAD
git rev-parse origin/reconcile/p11-140-143-local-chain
git log -10 --oneline --decorate
```

The authoritative remote must contain:

```text
6eaace08... production candidate
5ce97e18... development evidence
50baac22... REVIEW_PASS
4d2ca9ab... Formal Test Plan 4
<this authorization commit>
```

If the clean local branch is behind, synchronize only by a safe fast-forward to
the authoritative remote lineage.

Do not use reset, rebase, force, checkout-overwrite, or clean.

If local/remote history diverges:

```text
EXECUTION_BLOCKED
REASON: BRANCH_DIVERGENCE
```

Stop.

## 3. Candidate freeze

Before Formal Test:

```powershell
git cat-file -t 6eaace08c9ba5fb26809a7e02de5835123fb667a
git cat-file -t 4d2ca9abd9ed60d5b4bee8f2f76a2568baa67030
git merge-base --is-ancestor 6eaace08c9ba5fb26809a7e02de5835123fb667a HEAD
git diff --name-status 6eaace08c9ba5fb26809a7e02de5835123fb667a..HEAD
git status --short
git diff --check
```

All post-candidate tracked changes must be documentation/governance only.

Any `src/`, `tests/`, dependency, runtime, packaging, or production-config
drift:

```text
EXECUTION_BLOCKED
REASON: PRODUCTION_TEST_DRIFT_AFTER_REVIEW_PASS
```

## 4. Formal environment

Use short temporary paths exactly as required by Plan 202.

Recommended:

```text
FFDF_ROOT = D:\ffdf-p11-ft4
TEMP/TMP/pytest temp = D:\t\p11f4
```

Critically:

```text
FFDF_P11_US_DEV MUST BE ABSENT
```

Record only whether `FFDF_SEC_CONTACT_EMAIL` is configured. Never print,
persist, or commit its value.

## 5. Execute Plan 202 completely

Execute:

```text
FT-00 through FT-17
```

exactly as frozen in:

`development/202-p11-formal-test-plan-4.md`

Do not collapse gates merely because unit tests overlap them.

Critical gates include:

- FT-02 ISSUE-142 complete history inventory;
- FT-03 ISSUE-143/145 immutable source replay;
- FT-04 validation-v3/legacy-v2 migration;
- FT-05 ISSUE-146 REVALIDATE_LOCAL state;
- FT-08 static-asset/member-selection boundary;
- FT-10 live Apple FY2025 fresh run with request classification;
- FT-11 live repeat REUSE_DATA classification;
- FT-12 REVALIDATE_LOCAL transition using a disposable copy of live Apple
  artifacts;
- FT-13 Apple Q3;
- FT-14 Toyota 20-F;
- FT-15 Kellanova amendment conflict;
- FT-16 CN/HK/P0-P10 preservation.

## 6. Formal execution must not repair code

If any formal assertion shows a production/test defect:

```text
EXECUTION_FAIL
STOP
```

Do not patch the candidate.

Do not edit tracked tests to change expectations.

Do not change Design 38 or Plan 202 during execution.

A new production/test candidate requires returning to ChatGPT.

## 7. Live SEC policy

If SEC contact configuration is absent:

- run all offline gates;
- required live gates = BLOCKED;
- overall = EXECUTION_BLOCKED.

If SEC outage/rate/access conditions externally block correct production
behavior, record the controlled failure and mark the affected required gate
BLOCKED.

If current official metadata for a frozen slot has legitimately changed:

`EXTERNAL_FIXTURE_DRIFT`

Record observed current data. Do not silently change the expected fixture.

## 8. Required Apple transport evidence

For FT-10 record at minimum:

```text
current submissions fetch count
selected history descriptor names
history fetch count
archive-member fetch count
unrelated static-asset fetch count
ticker-map fetch count
package SHA
observation SHA
fact source mode
fact count
evidence count
table count
validation-v3 path
P7 status/blocking/review
P8 status
research_ready
```

Unrelated static-asset fetch count must be 0.

For FT-11 record:

```text
planner_action = REUSE_DATA
current discovery calls > 0
archive redownloads = 0
parser reruns = 0
status network calls = 0
```

For FT-12 record:

```text
planner_action = REVALIDATE_LOCAL
parser reruns = 0
archive redownloads = 0
raw hashes unchanged
parsed hashes unchanged
legacy-v2 hashes unchanged
new v3 PASS
corrupt-v3 rerun fails closed
no v2 fallback
```

## 9. Formal evidence

After all gates finish, create exactly:

`development/204-p11-formal-test-evidence-4.md`

The evidence must satisfy every requirement in Plan 202.

Raw logs and acceptance-only harness files remain outside Git.

Do not commit SEC contact information or other secrets.

Before evidence commit:

```powershell
git status --short
git diff --check
git diff --name-status 6eaace08c9ba5fb26809a7e02de5835123fb667a..HEAD
```

No source/test changes are allowed.

Commit only documentation/status evidence.

Suggested message:

`docs: record P11 formal test evidence 4`

Push normally to:

`origin/reconcile/p11-140-143-local-chain`

No force push.

## 10. Result classification

Each FT gate:

`PASS / FAIL / BLOCKED`

Overall:

- assertion failure or required production repair → `EXECUTION_FAIL`;
- externally unavailable required live gate → `EXECUTION_BLOCKED`;
- all required gates pass → `EXECUTION_PASS`.

Even if EXECUTION_PASS:

```text
FORMAL ACCEPTANCE:
NOT YET DECLARED
```

Only ChatGPT performs the independent Formal Acceptance review.

## 11. Stop boundary

After pushing `development/204-p11-formal-test-evidence-4.md`:

STOP.

Do not merge main.
Do not change production/test code.
Do not declare ACCEPTANCE_PASS.
Do not declare P11 DONE.

Next action:

`CHATGPT INDEPENDENT FORMAL ACCEPTANCE REVIEW 4`.

## 12. Final handoff

Use the exact final handoff format in Plan 202 §12 and include the exact evidence
commit SHA.

