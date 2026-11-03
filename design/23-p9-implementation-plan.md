# 23 — P9 Codex Review Overlay 实施计划

状态：**DESIGN BASELINE — P9 EXECUTION PLAN**

详细设计：
`design/22-p9-review-overlay-design.md`

---

## P9-A — Design Baseline

完成：
- detailed design
- implementation plan
- development instruction
- acceptance instruction
- design index/status/roadmap update
- commit/push

Gate：
`P9_READY_FOR_DEVELOPMENT`

---

## P9-B — Models / Base Bundle / Queue

实现：
- versions/enums/errors
- P8 catalog reuse
- P3/P5/P6/P7 trusted bundle
- base fingerprints
- review manifest
- deterministic REVIEW-only queue
- task support mapping

Gate：
focused queue tests PASS。

---

## P9-C — Evidence / Target Resolution

实现：
- P6 evidence index
- P5 cell index
- target selection
- evidence-to-target validation
- derived evidence pages
- before/after calculation
- fill-only raw conflict guard

Gate：
target/evidence tests PASS。

---

## P9-D — Resolution Store

实现：
- canonical submission validation
- explicit reviewer/timestamp
- explicit `base_active_resolution_ids` / `base_overlay_set_hash_before` prior-state contract (P9-ISSUE-003)
- stable resolution ID
- immutable per-ID JSON
- idempotency
- supersession graph
- conflict detection

Gate：
resolution/store/supersession tests PASS。

---

## P9-E — Resolved Fact Materializer

实现：
- active terminal resolutions
- effective_period/unit/scope
- statement class overlay
- overlap rules
- overlay_set_hash
- content-addressed snapshot

Gate：
resolved-fact deterministic tests PASS。

---

## P9-F — Overlay-aware Re-validation

实现：
- P7 public policy constants reuse
- period/unit effective coverage
- ambiguity attestation
- base + reviewed core statement classes
- resolved issue states
- resolved validation status
- resolved reuse eligibility
- resolved ParsedDataRecord helper

Gate：
synthetic REVIEW_REQUIRED → PASS golden。

---

## P9-G — CLI

实现：
- prepare
- tasks
- submit
- resolutions
- materialize
- report

Gate：
JSON stdout / no AI / no network。

---

## P9-H — Full Regression / Scope

执行：
- P0–P9 unit suite
- compileall
- git diff --check
- P0–P8 zero unintended diff
- no PDF open
- no network/AI/MCP SDK
- no Registry mutation

Gate：
PASS。

---

## P9-I — Live CN/HK

使用 canonical P8 catalog。

CN：
- queue REVIEW task count = 1
- evidence-grounded period overlay >=1
- raw facts immutable
- effective field visible
- honest resolved status

HK：
- queue REVIEW task count = 4
- exact reason/action mapping
- no forced dismissal

双 root / repeated materialization：
byte/semantic deterministic。

---

## P9-J — Code Review

Detached：
`worktrees/review/p9-<sha>`

审：
- exact design
- append-only store
- raw immutability
- evidence
- supersession/conflict
- resolved status logic
- live/synthetic
- scope no P10/P11

---

## P9-K — Acceptance Freeze

固定：
- design baseline/amendments
- production candidate
- review commit
- P8 catalog SHA
- live base fingerprints
- queue counts/reasons
- synthetic golden expectations
- live resolution fixture IDs/evidence
- performance gates
- exact commands

---

## P9-L — Independent Acceptance

Detached project-root worktree。

不得修改：
- production
- tests
- design
- catalog
- runtime/dependencies
- P3/P5/P6/P7/P8 artifacts

verdict：
PASS / FAIL / BLOCKED。

---

## P9-M — Closeout

PASS 后：
- acceptance result
- merge main
- post-merge full regression
- PROJECT_STATUS P9_DONE
- design index/roadmap/master design
- authorize P10 Design only

---

## Issue Rule

problem
→ STOP
→ design amendment
→ commit/push
→ rerun affected gates
→ continue。

禁止 code-first / design-later。
