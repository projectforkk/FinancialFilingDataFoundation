# 209 — P11 Formal Test Execution Authorization 5

Status: **FORMAL_TEST_EXECUTION_AUTHORIZED**

Agent role: **Acceptance/Test Agent**

This is a Formal Test execution authorization only.

The agent is NOT a Development Agent for this task.

It must not modify production/test code, redesign P11, create a replacement
candidate, merge main, declare Formal Acceptance, or declare P11 DONE.

## 1. Exact authority

Repository:

`projectforkk/FinancialFilingDataFoundation`

Authoritative remote lineage:

`reconcile/p11-140-143-local-chain`

Design 39:

`fad6ee7512ec1f2f3da0c9a24c646959b2f45541`

Frozen production candidate:

`f1cc76889718e06fdbdc46926e2b207b740a96e3`

Development evidence:

`f859dc342060d8c534491639d85e7256c4e11a57`

Fresh Full Exact-Candidate Review PASS:

`development/207-p11-fresh-full-exact-candidate-review-8.md`

Review commit:

`56d884f5adfc4f5044f3970c3e43180b658c74a8`

Formal Test Plan 5:

`development/208-p11-formal-test-plan-5.md`

Exact Formal Test Plan SHA:

`4e20ca77889b9e2f35b470c99ee90c45c7853994`

Exact-plan review result:

```text
FORMAL_TEST_PLAN_PASS
FORMAL_TEST_EXECUTION_AUTHORIZED
```

Execute Plan 208 exactly.

## 2. Start / synchronization

Use:

`D:\Codex\FinancialFilingDataFoundation\worktrees\active\p11-sec-rebuild-development`

Start with:

```powershell
Set-Location 'D:\Codex\FinancialFilingDataFoundation\worktrees\active\p11-sec-rebuild-development'
git status --short
git branch --show-current
git fetch origin
git rev-parse HEAD
git rev-parse origin/reconcile/p11-140-143-local-chain
git log -12 --oneline --decorate
```

If a clean local branch is behind, synchronize only by safe fast-forward.

If local/remote history diverges:

```text
EXECUTION_BLOCKED
REASON: BRANCH_DIVERGENCE
STOP
```

No rebase/reset/force/clean.

## 3. Candidate freeze

Before testing:

```powershell
git cat-file -t f1cc76889718e06fdbdc46926e2b207b740a96e3
git cat-file -t 4e20ca77889b9e2f35b470c99ee90c45c7853994
git merge-base --is-ancestor f1cc76889718e06fdbdc46926e2b207b740a96e3 HEAD
git diff --name-status f1cc76889718e06fdbdc46926e2b207b740a96e3..HEAD
git status --short
git diff --check
```

Every post-candidate tracked change must be documentation/governance only.

Any unauthorized `src/`, `tests/`, dependency, runtime, packaging, or
production-config drift:

```text
EXECUTION_BLOCKED
REASON: PRODUCTION_TEST_DRIFT_AFTER_REVIEW_PASS
STOP
```

## 4. Formal environment

Use short paths as Plan 208 specifies.

Recommended:

```text
FFDF_ROOT = D:\ffdf-p11-ft5
TEMP/TMP = D:\t\p11f5
```

`FFDF_P11_US_DEV` must remain absent.

Record only whether SEC contact configuration is present. Never record its
value.

## 5. Execute FT-00 through FT-18 completely

Do not resume Formal Test 4 from FT-11.

Formal Test 5 is a fresh full cycle.

Execute every gate in Plan 208.

Critical ISSUE-147 gates:

- FT-02 observation identity;
- FT-03 actual historical-format legacy snapshot WITHOUT `snapshot_id`;
- FT-04 newest-only cached resolution / no stale fallback;
- FT-05 explicit-CIK / current ticker freshness;
- FT-10 fresh live Apple ticker-based acquire;
- FT-10A Apple package identity audit;
- FT-11 immediate ticker-based ingest;
- FT-12 repeat REUSE_DATA.

Do not replace those gates with development test counts.

## 6. Apple package identity audit is mandatory

Formal Test 4 recorded package SHA:

`1196a354461ac65afa4ce7f1c67b2d65b04c1e496f521f34a139c6d6e5872d3d`

Development smoke for candidate f1cc7688 recorded:

`d94d8c46e34ce25af8d42279dbb4a370b1e617d7daf421743f29468b77d19568`

The candidate did not change acquisition/package code.

For FT-10A record the complete current package member records:

```text
relative_name
role
byte_length
member_sha256
```

Compare against any available historical artifacts/receipts for both prior
package SHAs.

If package identity differs, identify the exact member-level difference.

Do not silently accept unexplained package SHA drift.

A verifiable official source/member change may be recorded as an explained live
identity change; an unexplained discrepancy is FAIL.

## 7. Exact ISSUE-147 live boundary

FT-10 followed immediately by FT-11 must prove:

```text
ticker-based acquire
then ticker-based ingest

ticker map fetched on both invocations

same official source bytes are allowed

source SHA may be equal

retrieved_at differs

snapshot IDs differ when retrieval times differ

both observation files remain valid

no P11_SOURCE_DRIFT

ingest succeeds
```

Record both snapshot IDs, timestamps and source SHAs.

## 8. Historical legacy compatibility

FT-03 must not generate the legacy fixture through a helper that automatically
adds a current-format `snapshot_id`.

Construct an actual historical payload shape with no `snapshot_id`.

Prove it is verified and read correctly, remains byte-immutable, and is not
used as the new online persistence destination.

## 9. Production/test repair is forbidden

If any required Formal Test assertion fails:

```text
EXECUTION_FAIL
STOP
```

Do not patch code.
Do not patch tracked tests.
Do not change Plan 208.
Do not create a new candidate.

Return to ChatGPT.

## 10. Formal evidence

If execution reaches evidence creation, create exactly:

`development/210-p11-formal-test-evidence-5.md`

It must satisfy all evidence requirements in Plan 208.

Before committing:

```powershell
git status --short
git diff --check
git diff --name-status f1cc76889718e06fdbdc46926e2b207b740a96e3..HEAD
```

No source/test changes are permitted.

Commit documentation only and push by normal fast-forward to:

`origin/reconcile/p11-140-143-local-chain`

## 11. Result classification

Each gate:

`PASS / FAIL / BLOCKED`

Overall:

- required assertion failure → `EXECUTION_FAIL`;
- required production repair → `EXECUTION_FAIL`;
- external/contact unavailability → `EXECUTION_BLOCKED`;
- all required gates pass → `EXECUTION_PASS`.

Do not declare Acceptance PASS.

## 12. Stop boundary

After evidence push, STOP.

Do not merge main.
Do not modify production/test code.
Do not declare Formal Acceptance.
Do not declare P11 DONE.

Next action:

`CHATGPT INDEPENDENT FORMAL ACCEPTANCE REVIEW 5`.
