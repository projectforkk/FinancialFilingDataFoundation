# 23 — P9 Codex Review Overlay 实施计划

状态：**DESIGN BASELINE — P9 EXECUTION PLAN**

详细设计：
`design/22-p9-review-overlay-design.md`

## Current Recovery Baseline — P9-ISSUE-004

GitHub 当前 P9 branch 已包含未来 P10 路线 amendment；本地 active worktree 另有 handoff-reported、尚未提交的 P9-B–F candidate。该本地 candidate 在 WorkHome 失联前记录为 focused `7 passed`、full unit `242 passed / 0 fail`，但在重新连接并核验 worktree 前不得视为当前已验证事实或 accepted baseline。

安全恢复顺序固定为：
1. 恢复 WorkHome；
2. 在 `worktrees/active/p9-review-overlay` 执行只读 `git status/log/rev-parse` 核验；
3. 确认已知未提交 P9 production/tests 仍存在且无 tracked conflict；
4. 只允许安全 fast-forward/sync GitHub 的 design-only commits；
5. 禁止 reset / clean / checkout 覆盖 / 删除或从 GitHub 重建本地未提交 P9 文件；
6. 完成现场核验后继续 **P9-G — CLI**，再补 negative tests、P9-H–M。

本治理同步不授权提前实施 P10/P11。

---

## P9-A — Design Baseline

完成：
- detailed design
- implementation plan
- development instruction
- acceptance instruction
- design index/status/roadmap update
- latest accepted P8 baseline merged into P9 branch（P9-ISSUE-001）
- refreshed environment/internal-import audit after baseline merge
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
- P9-ISSUE-002 attestation evidence inheritance from active supporting resolutions
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

## P9-JR — Formal Review Corrective Gate

仅在 P9-J verdict = FAIL / CHANGES REQUIRED 且 design amendment 已 commit/push 后执行。

当前 authorized corrective scope 仅限：

- P9-J-F1：实现 payload-wide persisted resolution security validator，并在 submit 前与 historical semantic validation 时强制执行；
- P9-J-F2：把 argparse/parser-level failures 纳入 deterministic JSON diagnostic boundary；
- 为 F1/F2 增加 direct/adversarial unit tests；
- 重跑 focused P9 tests、full unit、compile/import、diff/scope checks；
- 创建新的 exact detached corrective candidate 做 P9-J re-review。

Gate：

- F1 adversarial probes（至少 URL in justification、SQL in value，并覆盖 path/shell/Python/credential classes）全部 deterministic reject；
- benign slash/keyword examples不误拒；
- 四个 parser-level cases均 stdout empty、stderr exactly one JSON object、reason_code/message stable、exit 2；
- focused/full unit PASS；
- no P0-P8 unintended diff；
- detached P9-J re-review PASS。

P9-JR PASS 前 P9-K 继续关闭。

---

## P9-JR2 — Second Formal Review Corrective Gate

Trigger：
`development/66-p9-jr-formal-rereview-result.md` = FAIL / CHANGES REQUIRED。

Authorized scope only：

- P9-JR-F1：修正 file-path false negatives 与 SQL natural-language false positive；
- P9-JR-F2：关闭 argparse help text surface，使 root/subcommand `-h/--help` 走 deterministic JSON parser error；
- 增加 direct/adversarial regression tests；
- focused/full/compile/scope verification；
- 新 exact candidate detached formal review。

Gate：

- `/tmp`、`/etc/passwd`、`C:\\secret.txt`、`path=C:\\secret.txt`、traversal 全部 deterministic reject；
- `2024/2025`、`P5/P6 evidence`、`SQL review completed`、`Select revenue from the annual report evidence.` 全部 allow；
- 原始 `SELECT * FROM secrets` 仍 reject；
- root/subcommand `-h/--help` 均 exit 2 / stdout empty / one JSON stderr；
- focused/full PASS；
- detached re-review PASS。

P9-JR2 PASS 前 P9-K 继续关闭。

---

## P9-JR3 — Shell-Token Corrective Gate

Trigger：
`development/70-p9-jr2-formal-rereview-result.md` = FAIL / CHANGES REQUIRED。

Authorized scope：

- reject bare command-segment executable tokens `powershell/pwsh/bash/curl/wget` plus existing argument forms；
- add direct regression tests；
- focused/full/contract probe；
- fresh detached formal review。

Gate：

- all five bare executable probes reject with `P9_RESOLUTION_CONTENT_FORBIDDEN`；
- argument forms continue rejecting；
- benign finance/natural-language probes remain allowed；
- focused/full PASS；
- detached re-review PASS。

P9-JR3 PASS 前 P9-K 关闭。

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
- authorize P10 Codex Dynamic Research Integration Design only

---

## Issue Rule

problem
→ STOP
→ design amendment
→ commit/push
→ rerun affected gates
→ continue。

禁止 code-first / design-later。
