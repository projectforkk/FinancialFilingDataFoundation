# 00 — Design Management Index

状态：**ACTIVE DESIGN GOVERNANCE INDEX**

本文件是 FFDF 设计书的管理索引，不替代各阶段详细设计；用于回答：

- 当前哪份设计是现行真源？
- 每份设计属于哪个 Phase？
- 哪些是历史已验收设计，哪些仍可修改？
- Issue 应写回哪里？
- Development / Review / Acceptance 如何与设计基线对应？
- 新设计文件如何编号、命名与冻结？

---

## 1. Design Source of Truth

设计真源位于 GitHub repository：

`projectforkk/FinancialFilingDataFoundation`

tracked `design/` 目录。

本机 working copy 不是独立真源；任何设计修改必须：
1. 修改 tracked design file；
2. UTF-8 without BOM；
3. `git diff --check`；
4. commit；
5. push；
6. 后续代码只以该 commit 为 baseline。

---

## 2. Design Lifecycle

每阶段必须：

```text
DESIGN_AUTHORIZED
→ detailed design
→ implementation plan
→ DESIGN_READY
→ DEVELOPMENT
→ CODE REVIEW
→ ACCEPTANCE FREEZE
→ INDEPENDENT ACCEPTANCE
→ DONE
```

若任一阶段发现问题且已有解决方案：

```text
STOP
→ facts/root cause
→ update detailed design + issue log
→ update implementation/acceptance rule if affected
→ commit design amendment
→ assess invalidated evidence
→ rerun affected gates
→ continue
```

禁止 code-first / design-later。

---

## 3. Design Document Classes

### A. Cross-phase architecture
长期有效：
- `01-project-detailed-design.md`
- `02-incremental-and-acquisition-design.md`
- `03-parsed-financial-document-contract.md`
- `04-pdf-quality-gate-design.md`
- `15-project-directory-management.md`

### B. Phase detailed design
定义一个 Phase 的 scope、contract、algorithm、error model、performance、acceptance semantics。

### C. Phase implementation plan
把 detailed design 拆成有序 Gate；不得改变 architecture semantics。

### D. Historical accepted design
Phase DONE 后保留，不重写当时的执行事实。
若后续 cross-phase rule 变化，用新设计明确 supersede 范围，不改历史 evidence。

---

## 4. Current Design Inventory

| File | Scope | Status |
|---|---|---|
| 01-project-detailed-design.md | 总体 architecture/governance | ACTIVE |
| 02-incremental-and-acquisition-design.md | incremental + acquisition | ACTIVE |
| 03-parsed-financial-document-contract.md | final parsed/export contract | ACTIVE |
| 04-pdf-quality-gate-design.md | quality/validation baseline | ACTIVE / P7 will refine |
| 05-p0-implementation-plan.md | P0 | ACCEPTED HISTORY |
| 06-p1-identity-registry-planner-design.md | P1 | ACCEPTED HISTORY |
| 07-p1-implementation-plan.md | P1 | ACCEPTED HISTORY |
| 08-p2-acquisition-provider-design.md | P2 | ACCEPTED + ACTIVE runtime reference |
| 09-p2-implementation-plan.md | P2 | ACCEPTED HISTORY |
| 10-p3-native-page-section-design.md | P3 | ACCEPTED HISTORY |
| 11-p3-implementation-plan.md | P3 | ACCEPTED HISTORY |
| 10-p4-table-candidate-design.md | P4 | ACCEPTED HISTORY |
| 11-p4-implementation-plan.md | P4 | ACCEPTED HISTORY |
| 12-p5-table-reconstruction-design.md | P5 | ACCEPTED HISTORY |
| 13-p5-implementation-plan.md | P5 | ACCEPTED HISTORY |
| 15-project-directory-management.md | project directory/workspace | ACTIVE |
| 16-p6-raw-facts-evidence-design.md | P6 | ACCEPTED HISTORY |
| 17-p6-implementation-plan.md | P6 | ACCEPTED HISTORY |
| 18-p7-quality-validation-design.md | P7 | ACTIVE DESIGN |
| 19-p7-implementation-plan.md | P7 | ACTIVE PLAN |

历史上 P3/P4 出现 10/11 重号。为保持 accepted references 不改名。

**P6 起不再重复编号。**

---

## 5. Future Numbering

从 P6 起固定唯一编号：

- `16-p6-raw-facts-evidence-design.md`
- `17-p6-implementation-plan.md`
- `18-p7-quality-validation-design.md`
- `19-p7-implementation-plan.md`
- `20-p8-local-mcp-design.md`
- `21-p8-implementation-plan.md`
- `22-p9-review-overlay-design.md`
- `23-p9-implementation-plan.md`
- `24-p10-codex-skill-design.md`
- `25-p10-implementation-plan.md`
- `26-p11-sec-provider-design.md`
- `27-p11-implementation-plan.md`

若新增 cross-phase design，使用 28+，不得插入并重命名已接受文件。

---

## 6. Phase Truth Matrix

| Phase | Detailed Design | Implementation Plan | Acceptance Result | State |
|---|---|---|---|---|
| P0 | 01/04 + 05 | 05 | acceptance/05 | DONE |
| P1 | 06 | 07 | acceptance/08 | DONE |
| P2 | 08 | 09 | acceptance/11 | DONE |
| P3 | 10-p3 | 11-p3 | acceptance/14 | DONE |
| P4 | 10-p4 | 11-p4 | acceptance/17 | DONE |
| P5 | 12 | 13 | acceptance/20 | DONE |
| P6 | 16 | 17 | acceptance/23 | DONE |
| P7 | 18 | 19 | acceptance/24 (baseline) | DESIGN READY |
| P8 | 20 | 21 | TBD | NOT STARTED |
| P9 | 22 | 23 | TBD | NOT STARTED |
| P10 | 24 | 25 | TBD | NOT STARTED |
| P11 | 26 | 27 | TBD | NOT STARTED |

---

## 7. Issue Management

每个 phase detailed design 或 implementation plan 必须包含 Issue Log。

Issue ID：

`P<phase>-ISSUE-<3-digit>`

例：
- P6-ISSUE-001
- P7-ISSUE-003

每条必须写：
- observed fact
- impact
- root cause
- approved solution
- affected gates
- invalidated evidence
- design amendment commit
- implementation fix commit
- rerun result

Issue 不允许只存在聊天记录或 commit message。

---

## 8. Design Freeze / Candidate Relation

Development evidence 必须记录：
- design baseline SHA
- latest design amendment SHA
- production candidate SHA

Code Review 必须审：
- exact production candidate
- current design baseline

Acceptance Freeze 必须固定：
- design baseline
- production candidate
- review result commit
- environment/runtime pins
- live fixtures
- commands/gates

Freeze 后任何 design amendment：
**原 freeze 自动失效。**

---

## 9. Encoding / Formatting

所有 tracked design/development/acceptance Markdown/JSON：
- UTF-8 without BOM
- LF preferred
- `git diff --check` clean

不得使用会按系统代码页重写 Unicode 的工具链。

发现 mojibake：
- 按 accepted Git evidence 重建；
- 不猜缺失字符；
- 单独记录修复 commit。

---

## 10. Directory Governance

目录治理以：
`design/15-project-directory-management.md`

为真源。

从 P6 起：
- dependencies/runtime/worktrees/workspace/data 均必须位于
  `D:\Codex\FinancialFilingDataFoundation\`
- 不再新增 FFDF-owned sibling directory。

---

## 11. Design Completeness Checklist

每份 phase detailed design 至少覆盖：

1. goal/non-goal
2. inputs
3. outputs/artifact schema
4. stable identity/IDs
5. deterministic algorithm
6. evidence/provenance
7. persistence/reuse
8. corruption/tamper validation
9. immutability
10. error/reason codes
11. performance gates
12. unit tests
13. live/golden tests
14. dependency boundary
15. forbidden functionality
16. public API
17. issue rule
18. exit condition

Implementation plan 至少覆盖：
- ordered gates
- exact completion criteria
- evidence required
- stop/go conditions
- review/acceptance freeze
- closeout

---

## 12. Design Change Authority

在当前项目治理中：
- user requirement > current design
- approved later cross-phase design > older active cross-phase design
- accepted phase history保留事实，不被后续设计 retroactively 改写
- code不得自行成为设计真源

---

## 13. Current Next Action

当前：
`P6_DONE / P7_DESIGN_READY`

下一步：
1. commit P7 design baseline；
2. create `task/p7-quality-validation`；
3. execute P7-A → P7-M；
4. Independent Acceptance PASS 后才进入 P8。
