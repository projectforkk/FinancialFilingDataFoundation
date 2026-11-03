# 19 — P7 Quality Gate / Validation 实施计划

状态：**DESIGN BASELINE — P7 EXECUTION PLAN**

详细设计：
`design/18-p7-quality-validation-design.md`

## P7-A — Design Baseline / Branch
- commit design/plan/dev/acceptance
- create `task/p7-quality-validation`
- worktree under `worktrees/active/p7-quality-validation`

## P7-B — Models / Policy
实现：
- ValidationArtifact
- issue severity/scope
- policy thresholds
- stable issue ID
- parse_run_id

Gate: focused tests PASS.

## P7-C — Structural / Evidence Gates
- preflight loader/identity/version/tamper failure → P7_INPUT_ARTIFACT_INVALID (no artifact)
- trusted-input identity
- page sequence
- fact/evidence coverage
- evidence refs
- no-facts
- compatibility

Gate: blocking/failure tests PASS.

## P7-D — Coverage / Warning Policy
- P6 warning mapping
- period/unit/scope coverage
- tables_without_facts / reconstructed-table structural metrics
- no implicit P4 reopen or candidate_count inference
- core statement signal
- duplicate/conflict check uses exact P5 source lineage; repeated metric names across different rows are not conflicts

Gate: threshold boundary tests PASS.

## P7-E — Accounting Reconciliation
- validation-only alias matching
- context-safe balance equation
- context-safe cash equation
- Decimal tolerance
- skipped when ambiguous

Gate: pass/fail/skip tests PASS.

## P7-F — Persistence / Semantic Revalidation
- issues.jsonl
- report
- fingerprints
- atomicity/reuse
- full semantic recomputation tamper guard

## P7-G — Registry Integration
- build ParsedDataRecord
- PASS → reuse eligible
- REVIEW/FAIL/BLOCKED → not reusable
- P1 planner integration test

Validator does not implicitly mutate registry.

## P7-H — Full Regression
- P0–P7
- compile
- static forbidden imports
- no PDF open
- prior-phase zero diff

## P7-I — Live CN/HK
Use project-root P6 live inputs/results.
Record exact deterministic status/issues/metrics.
Do not force PASS.

## P7-J — Code Review
isolated project-root worktree.

## P7-K — Acceptance Freeze

## P7-L — Independent Acceptance

## P7-M — Closeout
PASS → merge main → full regression → P7_DONE → authorize P8.

## Issue Rule
先设计回写，再修代码。
