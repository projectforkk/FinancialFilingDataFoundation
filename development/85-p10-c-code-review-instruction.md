# 85 — P10-C Detached Code Review Instruction

Status: **AUTHORIZED — P10-C REVIEW ONLY**

Phase:
`P10 — Codex Dynamic Research Integration`

Gate:
`P10-C — Models / Spec Freeze`

Design baseline:
`f20e4fd46c8d56e85dce80a16daf91abafd6323f`

Reauthorization:
`development/83-p10-c-spec-freeze-reauthorization.md`

Production candidate:
`35553df23f58a7f539b7390f98c7f154e42c817e`

Development evidence:
`development/84-p10-c-spec-freeze-evidence.md`

Evidence commit:
`4da7240`

## 1. Review isolation

Create a fresh detached review worktree under:

`D:\Codex\FinancialFilingDataFoundation\worktrees\review\p10-c-<shortsha>`

The reviewed HEAD must remain exact and clean.

All Python/test commands must bind:

`PYTHONPATH=<detached-review-worktree>\src`

Do not use shared main or active P10 source.

No reset/clean/rebase/force push.

## 2. Mandatory review scope

Read and compare:

- design/24 Section 8 / 8.1 / 9 / 35 / 36 / P10-ISSUE-001/002；
- design/25 P10-C；
- acceptance/38 items 14–20 and item 69；
- development/83；
- development/84；
- exact P10-C production/tests。

Confirm no P10-D or later implementation.

## 3. Contract review

Independently verify:

- opaque raw-byte handling；
- exact descriptor schema；
- exact logical-name ordering；
- caller-order independence；
- exact raw-byte size/SHA；
- resolved project-relative POSIX path persistence；
- descriptor-array-only canonical hash；
- exact canonical JSON parameters；
- bundle self-consistency validation before descriptor use；
- path containment including traversal/symlink escape；
- drift detection；
- reason-code classification；
- no instruction content persisted；
- immutable dataclass models；
- no silent refresh。

## 4. Independent execution

Run at minimum:

- focused `tests/unit/research/test_research_spec.py`；
- full `tests/unit`；
- compile/import；
- `git diff --check`；
- P8/P9 source/test scope diff；
- dependency/runtime diff；
- forbidden production-surface scan。

Use project-local short basetemps that are absent before the run.

## 5. Direct adversarial probes

Independently verify at least:

1. known fixture hash =
   `b6a725f6545abd35747fc884d0d48b81c42c3746acfa89b985bcbc239a3db5e5`；
2. same files reversed input order -> same bundle/hash；
3. outside/traversal path -> `P10_SPEC_PATH_OUTSIDE_PROJECT`；
4. size-preserving file mutation -> `P10_RESEARCH_SPEC_CHANGED`；
5. bundle hash tamper -> `P10_INVALID_SPEC_INPUT`；
6. non-UTF8 bytes hash exactly；
7. imported research package resolves to detached candidate `src`。

## 6. Security / scope

Production must contain no:

- network/remote AI API；
- external MCP SDK；
- subprocess/shell；
- SQL；
- environment dump；
- recursive prompt discovery。

No P8/P9 source/test change.
No dependency/runtime change.

## 7. Verdict

Allowed:

`PASS / FAIL / CHANGES REQUIRED`

PASS closes P10-C review and permits a separate explicit P10-D authorization.

This instruction does not authorize P10-D production.
