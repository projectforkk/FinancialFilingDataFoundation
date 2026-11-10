# 159 — P11 Live Acceptance Continuation Evidence

## Execution identity

- production_candidate: `05e06096bc8b788d0467a1ce3442829e87727b6`
- formal_test_plan: `development/156-p11-formal-test-plan.md`
- formal_test_plan_commit: `ccd506edc44b677457cd42347499f41cfe2b271a`
- previous_formal_evidence: `development/157-p11-formal-acceptance-evidence.md`
- previous_final_review: `development/158-p11-final-acceptance-review-blocked.md`
- previous_final_review_commit: `78ee9219b3b10b94ddda5c3f9e368e005e9d407c`
- development_branch: `task/p11-sec-rebuild-development`
- continuation_execution_head: `78ee9219b3b10b94ddda5c3f9e368e005e9d407c`
- isolated_ffdf_root: `D:\Codex\FinancialFilingDataFoundation\work\p11-formal-acceptance-05e06096`
- `FFDF_SEC_CONTACT_EMAIL` configured: `YES`
- actual SEC contact value: not recorded
- Python: `3.14.9`
- execution date: `2026-11-10` (Asia/Tokyo)

Raw continuation evidence is under [`../work/p11-formal-acceptance-05e06096/evidence/`](../work/p11-formal-acceptance-05e06096/evidence/).

## FT-00 — continuation preflight

**PASS**.

The continuation preflight recorded:

- branch: `task/p11-sec-rebuild-development`
- HEAD before this evidence document: `78ee9219b3b10b94ddda5c3f9e368e005e9d407c`
- candidate resolved exactly to `05e06096bc8b788d0467a1ce3442829e87727b6`
- working tree clean before this document
- post-candidate changes limited to development documents `153` through `158`
- post-candidate `src` and `tests` paths: none
- working-tree and post-candidate `git diff --check`: pass
- contact gate: configured, value not printed

Raw preflight: [`CONT-FT-00-preflight.txt`](../work/p11-formal-acceptance-05e06096/evidence/CONT-FT-00-preflight.txt).

## FT-01 — Apple FY2025 10-K

**FAIL**.

Frozen fixture: AAPL / CIK `0000320193` / FY2025 / 10-K / accession `0000320193-25-000079` / report period `2025-09-27`.

The live acquire command exited `10` with:

- reason code: `P11_SEC_DISCOVERY_FAILED`
- message: `SEC primary document path is unsafe`
- observed accession: `NOT_OBSERVED`
- observed form: `NOT_OBSERVED`
- package SHA: `NOT_OBSERVED`
- manifest/member SHA: `NOT_OBSERVED`
- facts/Evidence/hidden facts: `NOT_OBSERVED`
- validation/P8/research_ready: `NOT_REACHED`

Raw output: [`CONT-FT-01-acquire.stdout.txt`](../work/p11-formal-acceptance-05e06096/evidence/CONT-FT-01-acquire.stdout.txt), [`CONT-FT-01-acquire.meta.txt`](../work/p11-formal-acceptance-05e06096/evidence/CONT-FT-01-acquire.meta.txt). The planned ingest was not run because acquire failed: [`CONT-FT-01-ingest-not-run.txt`](../work/p11-formal-acceptance-05e06096/evidence/CONT-FT-01-ingest-not-run.txt).

This is an observed live defect in the frozen candidate. Production code was not changed.

## FT-02 — Apple FY2025 Q3 10-Q

**FAIL**.

Frozen fixture: AAPL / CIK `0000320193` / Q3 FY2025 / 10-Q / accession `0000320193-25-000073` / report period `2025-06-28`.

The live acquire command exited `10` with:

- reason code: `P11_SEC_DISCOVERY_FAILED`
- message: `SEC primary document path is unsafe`
- observed accession: `NOT_OBSERVED`
- observed form/report period: `NOT_OBSERVED`
- package/member SHA, Raw Facts, Evidence, validation, P8: `NOT_REACHED`

Raw output: [`CONT-FT-02-acquire.stdout.txt`](../work/p11-formal-acceptance-05e06096/evidence/CONT-FT-02-acquire.stdout.txt), [`CONT-FT-02-acquire.meta.txt`](../work/p11-formal-acceptance-05e06096/evidence/CONT-FT-02-acquire.meta.txt). The planned ingest was not run: [`CONT-FT-02-ingest-not-run.txt`](../work/p11-formal-acceptance-05e06096/evidence/CONT-FT-02-ingest-not-run.txt).

## FT-03 — custom extension / Evidence / hidden iXBRL

**BLOCKED**.

FT-03 requires the successfully ingested frozen FT-02 package. FT-02 did not produce a package, so no live `aapl:` fact, visible Evidence, XML Evidence, hidden-fact count, or live round-trip could be selected. Raw dependency record: [`CONT-FT-03-not-run.txt`](../work/p11-formal-acceptance-05e06096/evidence/CONT-FT-03-not-run.txt).

The deterministic custom/hidden Evidence tests remain carried forward as part of FT-06.

## FT-04 — Kellanova amendment conflict

**FAIL**.

Frozen fixture: K / CIK `0000055067` / FY2024 / report period `2024-12-28`.

The live acquire command exited `10` with:

- observed original accession: `NOT_OBSERVED`
- observed amendment accession: `NOT_OBSERVED`
- observed reason code: `P11_INVALID_US_IDENTITY`
- observed message: `ticker not found: K`
- expected reason code: `P11_AMENDED_VARIANT_PRESENT`
- active binding created: `NO_OBSERVED`

Raw output: [`CONT-FT-04-acquire-kellanova.stdout.txt`](../work/p11-formal-acceptance-05e06096/evidence/CONT-FT-04-acquire-kellanova.stdout.txt), [`CONT-FT-04-acquire-kellanova.meta.txt`](../work/p11-formal-acceptance-05e06096/evidence/CONT-FT-04-acquire-kellanova.meta.txt).

The frozen amendment-conflict result was not reached. Production code was not changed.

## FT-05 — Toyota FY2025 20-F

**FAIL**.

Frozen fixture: TM / CIK `0001094517` / FY2025 / 20-F / accession `0001193125-25-142326` / report period `2025-03-31`.

The live acquire command exited `10` with:

- reason code: `P11_SEC_DISCOVERY_FAILED`
- message: `SEC primary document path is unsafe`
- observed accession/form/report period: `NOT_OBSERVED`
- package/member SHA, Raw Facts, Evidence, validation, P8, research_ready: `NOT_REACHED`

Raw output: [`CONT-FT-05-acquire-toyota.stdout.txt`](../work/p11-formal-acceptance-05e06096/evidence/CONT-FT-05-acquire-toyota.stdout.txt), [`CONT-FT-05-acquire-toyota.meta.txt`](../work/p11-formal-acceptance-05e06096/evidence/CONT-FT-05-acquire-toyota.meta.txt). The planned ingest was not run: [`CONT-FT-05-ingest-not-run.txt`](../work/p11-formal-acceptance-05e06096/evidence/CONT-FT-05-ingest-not-run.txt).

The deterministic FPI annual-only policy result remains carried forward from FT-06; the live Toyota package was not obtained.

## FT-06 / FT-07 carried results

The frozen production candidate, relevant production implementation, and FT-07 acceptance harness were unchanged during this continuation.

- FT-06: **PASS — CARRIED FORWARD** from `development/157-p11-formal-acceptance-evidence.md`; previous selected tests passed `29`.
- FT-07: **PASS — CARRIED FORWARD** from `development/157-p11-formal-acceptance-evidence.md`.
- FT-07 harness SHA-256 observed unchanged in this continuation: `11D2F9FBF547347AE46FE6B16B38A50ED441FAB2C89F8F039080861FB201CEB4`.

## FT-08 — Apple live idempotency

**BLOCKED**.

FT-08 requires the completed FT-01 baseline package. FT-01 failed before producing an accession/package/artifact baseline, so the second acquire/ingest was not run. No before/after identity comparison is available:

| Field | First run | Second run |
| --- | --- | --- |
| accession | NOT_OBSERVED | NOT_RUN |
| package SHA | NOT_OBSERVED | NOT_RUN |
| manifest/member hashes | NOT_OBSERVED | NOT_RUN |
| parser version | NOT_OBSERVED | NOT_RUN |
| Raw Fact/Evidence counts | NOT_OBSERVED | NOT_RUN |
| catalog/registry state | NOT_OBSERVED | NOT_RUN |
| known-member network fetches | NOT_OBSERVED | NOT_RUN |

Raw dependency record: [`CONT-FT-08-not-run.txt`](../work/p11-formal-acceptance-05e06096/evidence/CONT-FT-08-not-run.txt).

## Final regression rerun

Final regression results after the live attempts:

- P11 focused: `53 passed in 1.60s` — [`CONT-regression-p11-focused.stdout.txt`](../work/p11-formal-acceptance-05e06096/evidence/CONT-regression-p11-focused.stdout.txt)
- Full unit: `583 passed in 45.77s` — [`CONT-regression-full-unit-short-temp.stdout.txt`](../work/p11-formal-acceptance-05e06096/evidence/CONT-regression-full-unit-short-temp.stdout.txt)
- CN/HK regression: `96 passed in 7.17s` — [`CONT-regression-cnhk.stdout.txt`](../work/p11-formal-acceptance-05e06096/evidence/CONT-regression-cnhk.stdout.txt)
- compileall: exit `0` — [`CONT-regression-compileall.meta.txt`](../work/p11-formal-acceptance-05e06096/evidence/CONT-regression-compileall.meta.txt)
- `git diff --check`: exit `0` — [`CONT-regression-git-diff-check.meta.txt`](../work/p11-formal-acceptance-05e06096/evidence/CONT-regression-git-diff-check.meta.txt)

The first continuation full-unit command used the plan's `.t\p11-live-final` path and recorded `568 passed, 15` Windows path-creation failures. It was preserved in [`CONT-regression-full-unit.stdout.txt`](../work/p11-formal-acceptance-05e06096/evidence/CONT-regression-full-unit.stdout.txt). The final `583 passed` run changed only the temporary basetemp path; no source or test code changed.

## Production freeze and result

- production source changed during continuation: `NO`
- test source changed during continuation: `NO`
- main merge: `NOT RUN`
- P11 production availability: `NOT CHANGED`
- live continuation execution result: `LIVE_CONTINUATION_EXECUTION_FAIL`
- failure reasons: FT-01/FT-02/FT-05 `P11_SEC_DISCOVERY_FAILED / SEC primary document path is unsafe`; FT-04 `P11_INVALID_US_IDENTITY / ticker not found: K`
- final acceptance verdict: not made by the execution agent

Next action: `CHATGPT FINAL ACCEPTANCE REVIEW`.
