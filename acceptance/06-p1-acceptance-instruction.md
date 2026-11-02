# 06 — P1 Independent Acceptance Instruction

状态：**DESIGN BASELINE — P1 ACCEPTANCE**

独立验收最终 verdict 只能是：
- PASS
- FAIL
- BLOCKED

验收不得修改 production code、tests、config、design 或 dependency version。

## 必读

- AGENTS.md
- PROJECT_STATUS.md
- design/01-project-detailed-design.md
- design/02-incremental-and-acquisition-design.md
- design/06-p1-identity-registry-planner-design.md
- design/07-p1-implementation-plan.md
- development/07-p1-development-instruction.md
- acceptance/01-acceptance-strategy.md
- 本文件

## Candidate Isolation

Independent Acceptance 必须在独立 Git worktree 中执行，并固定到 acceptance freeze 指定的 candidate SHA。

每组关键命令执行前后都必须验证：

`git rev-parse HEAD == frozen_candidate_sha`

若不一致，该组结果无效，必须停止并重新建立隔离 worktree；不得继续使用共享开发工作树的结果。

## 必验

1. P0 regression tests PASS。
2. P1 focused/integration tests PASS。
3. FilingSlotKey deterministic。
4. amended 不改变 slot key。
5. required filing ordering deterministic。
6. SQLite create/close/reopen 后 plan 不变。
7. same file registration idempotent。
8. same SHA multi-path 不重复 content record。
9. source metadata 在没有 expected identity 时仍持久化，不丢 provenance。
10. repeated same source provenance idempotent。
11. unbound document 不作为 local candidate。
12. reusable parsed → REUSE_DATA。
13. non-PASS/blocking/incompatible/defect invalidated → 不 reuse。
14. one local raw → PARSE_LOCAL。
15. no parsed/no local → DOWNLOAD_AND_PARSE。
16. parsed SHA 与 current local SHA 不同 → 阻止错误 reuse。
17. multiple distinct local SHA → REVIEW_REQUIRED，禁止猜测。
18. parser_version change alone 不触发 reparse。
19. accepted schema / invalidated parser versions 由显式 `PlannerReusePolicy` 决定；accepted set 为空表示无 schema 可复用。
20. 多个 distinct reusable parsed SHA 且无唯一 local active-source 证据 → REVIEW_REQUIRED。
21. registry schema version > supported → structured plan-level BLOCKED，不得 downgrade。
22. source files unchanged。
23. no network。
24. no Dayu。
25. no Docling/Torch/OCR/external AI。
26. repeated build_plan deterministic。

## PASS

全部条件满足且无 blocker。

## FAIL

任一产品/设计验收条件失败。

## BLOCKED

仅用于外部执行环境阻断，不能用于普通测试失败。

P1 PASS 后才允许 P2。
