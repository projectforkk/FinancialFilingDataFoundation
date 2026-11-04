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
| 18-p7-quality-validation-design.md | P7 | ACCEPTED HISTORY |
| 19-p7-implementation-plan.md | P7 | ACCEPTED HISTORY |
| 20-p8-local-mcp-design.md | P8 | ACCEPTED HISTORY |
| 21-p8-implementation-plan.md | P8 | ACCEPTED HISTORY |
| 22-p9-review-overlay-design.md | P9 | ACCEPTED HISTORY |
| 23-p9-implementation-plan.md | P9 | ACCEPTED HISTORY |
| 24-p10-codex-dynamic-research-integration-design.md | P10 | DESIGN READY |
| 25-p10-implementation-plan.md | P10 | DESIGN READY |
| 28-ffdf-research-consumption-semantic-architecture.md | future semantic architecture | ACTIVE REFERENCE / IMPLEMENTATION NOT AUTHORIZED |
| 29-research-mcp-visual-resolved-query-detailed-design.md | future Research MCP | ACTIVE REFERENCE / PRODUCTION NOT AUTHORIZED |

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
- `24-p10-codex-dynamic-research-integration-design.md`
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
| P7 | 18 | 19 | acceptance/26 | DONE |
| P8 | 20 | 21 | acceptance/33 | DONE |
| P9 | 22 | 23 | acceptance/37 | DONE |
| P10 | 24 | 25 | acceptance/38 (baseline) | DESIGN READY |
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
`P9_DONE / P10_DESIGN_READY`

P10 design candidate：
- detailed design = `design/24-p10-codex-dynamic-research-integration-design.md`；
- implementation plan = `design/25-p10-implementation-plan.md`；
- acceptance baseline = `acceptance/38-p10-acceptance-instruction.md`；
- reconciliation = `development/76-p10-design-reconciliation.md`；
- design/28 semantic architecture = reference only / implementation not authorized；
- design/29 Research MCP = reference only / production not authorized。

Current P10-E amended design baseline：
`d6b34d84d1eeae6b0f2009895a14c5956217a18f`

P10-B first probe发现并关闭 `P10-ISSUE-001`：exact-candidate `PYTHONPATH=<worktree>\\src` source binding 已由 `ee5ddb9798f45b9abac081fb4f7c2c999c131b6c` 冻结。

当前：
1. P10-B rerun = `PASS — P10_ENVIRONMENT_READY`；
2. evidence = `development/79-p10-environment-interface-audit-rerun.md`；
3. design-owner review = `development/80-p10-b-github-review.md` = PASS；
4. P10-ISSUE-001 exact-candidate source binding = CLOSED / PASS；
5. historical P10-C authorization = `development/81-p10-c-spec-freeze-instruction.md`；
6. P10-C historical authorization 81 was stopped before code by `P10-ISSUE-002`；
7. amended design baseline = `f20e4fd46c8d56e85dce80a16daf91abafd6323f`；
8. stop record = `development/82-p10-c-preimplementation-design-stop.md`；
9. P10-C reauthorization = `development/83-p10-c-spec-freeze-reauthorization.md`；
10. P10-C production candidate = `35553df23f58a7f539b7390f98c7f154e42c817e`；
11. P10-C evidence = `development/84-p10-c-spec-freeze-evidence.md` = PASS；
12. P10-C detached review instruction = `development/85-p10-c-code-review-instruction.md`；
13. P10-C detached review result = `development/86-p10-c-detached-code-review-result.md` = PASS；
14. P10-C = CLOSED；
15. P10-D pre-implementation review found `P10-ISSUE-003`；
16. P10-D amended design baseline = `ba962aef818d7a31731637a5cfef1f57020a7d1d`；
17. stop record = `development/87-p10-d-preimplementation-design-stop.md`；
18. P10-D reauthorization = `development/88-p10-d-context-reauthorization.md`；
19. P10-D final production/test candidate = `c8b4041c2d06e1d601707ca765ddd9e817f0dfc9`；
20. P10-D evidence = `development/89-p10-d-context-evidence.md` = PASS；
21. P10-D detached review instruction = `development/90-p10-d-code-review-instruction.md`；
22. P10-D detached review result = `development/91-p10-d-detached-code-review-result.md` = PASS；
23. P10-D = CLOSED；
24. P10-E pre-implementation review found `P10-ISSUE-004` before production code；
25. P10-E stop record = `development/92-p10-e-preimplementation-design-stop.md`；
26. P10-E amended design baseline = `d6b34d84d1eeae6b0f2009895a14c5956217a18f`；
27. P10-E reauthorization = `development/93-p10-e-provenance-reauthorization.md`；
28. P10-E production candidate = `802a395247e490a83acaef744c1641188fbf704e`；
29. P10-E evidence = `development/94-p10-e-provenance-evidence.md` = PASS；
30. P10-E detached review instruction = `development/95-p10-e-code-review-instruction.md`；
31. P10-E detached review result = `development/96-p10-e-detached-code-review-result.md` = PASS；
32. P10-E review result commit = `af7295d740ecadeb9c17705c1e1048f3f742a8e6`；
33. P10-E = CLOSED；
34. P10-F pre-implementation review found `P10-ISSUE-005` before CLI code；
35. P10-F stop record = `development/97-p10-f-preimplementation-design-stop.md`；
36. P10-F amended design baseline = `860e628ecf9f804734c9d343b3f2a9894928c9e9`；
37. P10-F reauthorization = `development/98-p10-f-cli-reauthorization.md`；
38. P10-F production candidate = `d8e7d81b4bb5a4f06cead9eba0e2d09884094676`；
39. P10-F evidence = `development/99-p10-f-cli-evidence.md` = PASS；
40. P10-F detached review instruction = `development/100-p10-f-code-review-instruction.md`；
41. P10-F detached review result = `development/101-p10-f-detached-code-review-result.md` = PASS；
42. P10-F review result commit = `5b54748`；
43. P10-F = CLOSED；
44. P10-G authorization = `development/102-p10-g-integration-instruction-authorization.md`；
45. P10-G candidate = `3a805a8f333ac20770d6aec1c8285d93993d18fc`；
46. P10-G artifact SHA256 = `ef10406c9957f7a68a9af001c913deef0a057e166100a2d852c0c8fcd2c46296`；
47. P10-G evidence = `development/103-p10-g-integration-instruction-evidence.md` = PASS；
48. P10-G detached review instruction = `development/104-p10-g-documentation-review-instruction.md`；
49. P10-G detached review stop = `development/105-p10-g-detached-review-stop.md`；
50. P10-G pre-PASS review found `P10-ISSUE-006`: worktree SHA is EOL-sensitive；
51. P10-G amended design baseline = `d896173`；
52. P10-G review rerun authorization = `development/106-p10-g-review-reauthorization.md`；
53. P10-G detached review rerun result = `development/107-p10-g-detached-review-result.md` = PASS；
54. P10-G = CLOSED；
55. P10-H authorization = `development/108-p10-h-full-regression-authorization.md`；
56. P10-H evidence = `development/109-p10-h-full-regression-scope-evidence.md` = PASS；
57. P10-H = CLOSED；
58. P10-I authorization = `development/110-p10-i-dynamic-spec-authorization.md`；
59. P10-I evidence = `development/111-p10-i-dynamic-spec-evidence.md` = PASS；
60. P10-I = CLOSED；
61. P10-J authorization = `development/112-p10-j-live-run-authorization.md`；
62. P10-J live-run stop = `development/113-p10-j-live-run-stop.md`；
63. P10-J found `P10-ISSUE-007`: P9 review stores are path-bound / non-relocatable；
64. P10-J amended design baseline = `668269e`；
65. P10-J rerun authorization = `development/114-p10-j-live-run-reauthorization.md`；
66. P10-J evidence = `development/115-p10-j-live-research-evidence.md` = PASS / COMPLETE；
67. P10-J = CLOSED；
68. P10-K authorization = `development/116-p10-k-negative-gates-authorization.md`；
69. P10-K evidence = `development/117-p10-k-negative-gates-evidence.md` = PASS；
70. P10-K = CLOSED；
71. P10-L and later remain closed pending separate authorization；
72. P11 / Research MCP production / Semantic Resolver production remain closed。
