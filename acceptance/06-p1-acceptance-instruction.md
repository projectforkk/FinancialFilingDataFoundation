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

## 必验

1. P0 regression tests PASS。
2. P1 focused/integration tests PASS。
3. FilingSlotKey deterministic。
4. amended 不改变 slot key。
5. required filing ordering deterministic。
6. SQLite create/close/reopen 后 plan 不变。
7. same file registration idempotent。
8. same SHA multi-path 不重复 content record。
9. unbound document 不作为 local candidate。
10. reusable parsed → REUSE_DATA。
11. non-PASS/blocking/incompatible/defect invalidated → 不 reuse。
12. one local raw → PARSE_LOCAL。
13. no parsed/no local → DOWNLOAD_AND_PARSE。
14. parsed SHA 与 current local SHA 不同 → 阻止错误 reuse。
15. multiple distinct local SHA → REVIEW_REQUIRED，禁止猜测。
16. parser_version change alone 不触发 reparse。
17. source files unchanged。
18. no network。
19. no Dayu。
20. no Docling/Torch/OCR/external AI。
21. repeated build_plan deterministic。

## PASS

全部条件满足且无 blocker。

## FAIL

任一产品/设计验收条件失败。

## BLOCKED

仅用于外部执行环境阻断，不能用于普通测试失败。

P1 PASS 后才允许 P2。
