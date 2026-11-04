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
| 24-p10-codex-dynamic-research-integration-design.md | P10 | ACCEPTED HISTORY |
| 25-p10-implementation-plan.md | P10 | ACCEPTED HISTORY |
| 26-p11-sec-provider-design.md | P11 | P11-A DESIGN BASELINE PASS / PRODUCTION CLOSED |
| 27-p11-implementation-plan.md | P11 | P11-A DESIGN BASELINE PASS / PRODUCTION CLOSED |
| 28-ffdf-research-consumption-semantic-architecture.md | future semantic architecture | ACTIVE REFERENCE / IMPLEMENTATION NOT AUTHORIZED |
| 29-research-mcp-visual-resolved-query-detailed-design.md | future Research MCP | ACTIVE REFERENCE / PRODUCTION NOT AUTHORIZED |
| 30-parsed-financial-document-v2-contract.md | cross-phase source-neutral parsed contract / P11 | P11-A DESIGN BASELINE PASS / PRODUCTION CLOSED |
| 31-p11-d-http-discovery-contract.md | P11-D exact HTTP / rate gate / discovery merge contract | P11-D DESIGN BASELINE PASS / IMPLEMENTATION CLOSED |

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
| P10 | 24 | 25 | acceptance/40 | DONE |
| P11 | 26 | 27 | acceptance/41 | DESIGN REVIEW STOPPED / ISSUE-032 OPEN |

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
`P10_DONE / P11_A_PASS / P11_B_PASS / P11_C_PASS / P11_D_ISSUE_044_OPEN_AMENDMENT_REQUIRED`

P11 latest reviewed candidate：
- historical exact candidate = `c3a2f84c7ebd5f8533adfaaa596b97f672dfb31d` = INELIGIBLE after P11-ISSUE-038；
- authoritative stop = `development/197-p11-governance-status-review-stop.md`；
- ISSUE-037 amendment evidence = `development/195-p11-registry-api-surface-amendment-evidence.md` = PASS and remains valid；
- ISSUE-038 amendment evidence = `development/198-p11-governance-status-amendment-evidence.md` = PASS and remains valid；
- historical exact candidate = `cd2fa0b01d23c0e3f75945c5cce5120738f51077` = INELIGIBLE after P11-ISSUE-039；
- authoritative stop = `development/200-p11-phase-banner-review-stop.md`；
- ISSUE-039 amendment evidence = `development/201-p11-phase-banner-amendment-evidence.md` = PASS；
- exact amended candidate = `5877a238f5af6102ef48e56141cdb893590b6aab`；
- formal review authorization = `development/202-p11-phase-banner-final-review-authorization.md`；
- detailed design = `design/26-p11-sec-provider-design.md`；
- implementation plan = `design/27-p11-implementation-plan.md`；
- source-neutral parsed contract = `design/30-parsed-financial-document-v2-contract.md`；
- acceptance baseline = `acceptance/41-p11-acceptance-instruction.md`；
- P11 production = CLOSED；
- P11-A formal review result = `development/203-p11-final-detached-design-review-result.md` = PASS；
- accepted P11-A design baseline = `5877a238f5af6102ef48e56141cdb893590b6aab`；
- P11-B authorization = `development/204-p11-b-environment-runtime-probe-authorization.md`；
- P11-B result = `development/205-p11-environment-runtime-probe.md` = PASS；
- P11-C authorization = `development/206-p11-c-identity-period-authorization.md`；
- P11-C candidate = `027288f6d5bb064f82764b3dc19961996de1dab8`；
- P11-C final review = `development/211-p11-c-final-detached-code-review-result.md` = PASS；
- P11-C integration merge = `1a5b04f22e1821558337821c758f70a7458da9ae`；
- P11-D design contract = `design/31-p11-d-http-discovery-contract.md`；
- P11-D amendment evidence = `development/213-p11-d-http-discovery-design-amendment-evidence.md` = PASS；
- P11-D ISSUE-040 stop = `development/215-p11-d-discovery-semantic-provenance-review-stop.md`；
- P11-D ISSUE-040 amendment evidence = `development/216-p11-d-discovery-semantic-provenance-amendment-evidence.md` = PASS；
- P11-D ISSUE-041 stop = `development/218-p11-d-historical-shard-descriptor-review-stop.md`；
- P11-D ISSUE-042 preflight stop = `development/219-p11-d-discovery-candidate-ordering-preflight-stop.md`；
- P11-D ISSUE-041/042 amendment evidence = `development/220-p11-d-issues041042-amendment-evidence.md` = PASS；
- P11-D ISSUE-043 stop = `development/222-p11-d-response-framing-review-stop.md`；
- P11-D ISSUE-043 amendment evidence = `development/223-p11-d-response-framing-amendment-evidence.md` = PASS；
- next action = freeze P11-D amended design candidate and run fresh detached design review；
- P11-B = CLOSED / PASS；
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
71. P10-L authorization = `development/118-p10-l-formal-review-authorization.md`；
72. P10-L formal review result = `development/119-p10-l-formal-code-review-result.md` = PASS；
73. P10-L = CLOSED；
74. P10-M authorization = `development/120-p10-m-acceptance-freeze-authorization.md`；
75. P10-M freeze evidence = `development/121-p10-m-acceptance-freeze-evidence.md` = PASS；
76. P10-M historical freeze attempt = `42e39c971a360ca4e0ee09761221cc8da7ddbaa9` = INVALID；
77. P10-M stop record = `development/122-p10-m-freeze-stop.md`；
78. P10-M corrected re-freeze evidence = `development/123-p10-m-refreeze-evidence.md` = PASS；
79. P10-M actual corrected re-freeze commit = `4d1ab46f11d1d7b88934309ce32319e2200f0d8f`；
80. historical later-recorded candidate `56cbe185e97e6e07dd354e03b98942d87f8e5787` = INVALID / NON-EXISTENT；
81. P10-M = CLOSED on actual candidate `4d1ab46f...`；
82. historical P10-N authorization = `development/124-p10-n-independent-acceptance-authorization.md` = INVALID；
83. historical closeout authorization = `development/125-p10-closeout-authorization.md` = INVALID；
84. closeout stop = `development/126-p10-closeout-stop.md`；
85. historical integration merge `b560f49a78316fa59a4183de326d2dee0a80ebb6` = INELIGIBLE；
86. corrected P10-N authorization = `development/127-p10-n-corrected-reauthorization.md`；
87. corrected P10-N candidate = `4d1ab46f11d1d7b88934309ce32319e2200f0d8f`；
88. P10-N precheck stop = `development/128-p10-n-precheck-stop.md`；
89. P10-N found `P10-ISSUE-008`: frozen fixture identity was checkout-EOL-sensitive；
90. prior P10-M freeze + corrected P10-N authorization are INVALIDATED；
91. P10-ISSUE-008 design baseline = `f8bffca`；
92. acceptance harness amendment authorization = `development/129-p10-acceptance-harness-amendment-authorization.md`；
93. partial harness candidate = `9621f20d33c1d1b650bcdf1a7686b5f0b9c7c817`；
94. detached precheck preview = PASS for fixture Git-blob identity；
95. preview stop = `development/130-p10-acceptance-harness-preview-stop.md`；
96. preview found `P10-ISSUE-009`: base manifest identity still checkout-filter-sensitive；
97. partial harness candidate is INELIGIBLE；
98. P10-ISSUE-009 design baseline = `ad78cbe`；
99. harness v2 authorization = `development/131-p10-acceptance-harness-v2-authorization.md`；
100. harness v2 candidate = `db06b7a890e25908d224b6a63d8695be2f414b25`；
101. harness v2 evidence = `development/132-p10-acceptance-harness-v2-evidence.md` = PASS；
102. targeted formal review authorization = `development/133-p10-acceptance-package-formal-review-authorization.md`；
103. targeted formal review result = `development/134-p10-acceptance-package-formal-review-result.md` = PASS；
104. P10-M re-freeze authorization = `development/135-p10-m-issue008009-refreeze-authorization.md`；
105. P10-M re-freeze evidence = `development/136-p10-m-issue008009-refreeze-evidence.md` = PASS / PACKAGE READY；
106. P10-M exact re-freeze commit = `183ca5dc89a606715a3e352bf92a235f7aa31fad`；
107. P10-M = CLOSED；
108. P10-N authorization = `development/137-p10-n-independent-acceptance-authorization.md`；
109. P10-N first execution stop = `development/138-p10-n-execution-stop.md`；
110. P10-N fresh rerun authorization = `development/139-p10-n-rerun-authorization.md`；
111. P10-N result = `acceptance/40-p10-independent-acceptance-result.md` = PASS；
112. P10-N accepted detached candidate = `183ca5dc89a606715a3e352bf92a235f7aa31fad`；
113. P10-N = CLOSED / PASS；
114. P10-O v2 closeout authorization = `development/140-p10-o-closeout-authorization-v2.md`；
115. P10-O v2 integration evidence = `development/141-p10-o-v2-integration-evidence.md` = PASS；
116. P10-O v2 merge commit = `a539500ef1fd0036eaa8d79a9bf7cfe78db57185`；
117. main integration evidence commit = `230968937a8ebdcbde56982a22b37125e4aefff4`；
118. final closeout = `development/142-p10-closeout.md` = DONE / PASS；
119. P10 = DONE / PASS；
120. historical `integration/p10-closeout @ b560f49a78316fa59a4183de326d2dee0a80ebb6` remains INELIGIBLE；
121. P11 design authorization = `development/143-p11-design-authorization.md`；
122. P11 environment/interface audit = `development/144-p11-environment-interface-audit.md` = PASS / design may proceed；
123. P11 design reconciliation = `development/145-p11-design-reconciliation.md` = PASS；
124. P11 design candidate = `design/26` + `design/27` + `design/30` + `acceptance/41`；
125. P11 candidate `3ccaedc14a4c0f3f222cd192c8b7e1479d787ccd` = INELIGIBLE after detached design review；
126. review stop = `development/147-p11-detached-design-review-stop.md`；
127. P11-ISSUE-010..016 = REMEDIATED IN AMENDED DESIGN / FRESH REVIEW REQUIRED；
128. amendment evidence = `development/148-p11-design-amendment-evidence.md` = PASS；
129. P11 amended candidate `11648b22bfe97d88048c2dcf079034c37b3854af` = INELIGIBLE after fresh review；
130. second review stop = `development/150-p11-amended-design-review-stop.md`；
131. P11-ISSUE-017..019 = REMEDIATED / FRESH REVIEW REQUIRED；
132. second amendment evidence = `development/151-p11-second-design-amendment-evidence.md` = PASS；
133. partial candidate `9ccf430db68fba8dec877550be855fbeed83648a` = INELIGIBLE / design30 omitted from staging；
134. assembly stop = `development/152-p11-third-candidate-assembly-stop.md`；
135. corrected candidate `ae0f2a1c4c1ac3c1586dba4fabee807f002af987` = INELIGIBLE after fresh review；
136. review stop = `development/154-p11-corrected-design-review-stop.md`；
137. P11-ISSUE-020 = REMEDIATED / FRESH REVIEW REQUIRED；
138. amendment evidence = `development/155-p11-period-binding-order-amendment-evidence.md` = PASS；
139. P11 candidate `a223d44d766609190806d1d349dab1d5d673423b` = INELIGIBLE after final design review；
140. review stop = `development/157-p11-final-design-review-stop.md`；
141. P11-ISSUE-021 = REMEDIATED / FRESH REVIEW REQUIRED；
142. amendment evidence = `development/158-p11-supplemental-identity-amendment-evidence.md` = PASS；
143. P11 candidate `5e1a1b7b39544af6c3ba464fc576174b480bd3ad` = INELIGIBLE after fresh review；
144. review stop = `development/160-p11-logical-asset-review-stop.md`；
145. P11-ISSUE-022..024 = REMEDIATED / FRESH REVIEW REQUIRED；
146. amendment evidence = `development/161-p11-logical-asset-amendment-evidence.md` = PASS；
147. P11-ISSUE-025..026 = REMEDIATED / CANDIDATE FREEZE REQUIRED；
148. amendment evidence = `development/162-p11-source-asset-provenance-amendment-evidence.md` = PASS；
149. P11 candidate `dff1e390f0a8825c75abb15cfb10c41543c676d5` = INELIGIBLE after detached review；
150. review authorization = `development/163-p11-source-provenance-final-review-authorization.md`；
151. review stop = `development/164-p11-package-aware-reuse-review-stop.md`；
152. P11 candidate `dc1c59e1ec19e8cf3e75624643d045a9f954fd16` = INELIGIBLE after detached review；
153. review authorization = `development/166-p11-package-aware-reuse-final-review-authorization.md`；
154. review stop = `development/167-p11-reuse-api-review-stop.md`；
155. P11-ISSUE-029 = REMEDIATED；
156. amendment evidence = `development/168-p11-reuse-api-amendment-evidence.md` = PASS；
157. candidate `d47a0b5de5c2b3e88a5df629476d05d26e7d83fb` = INELIGIBLE after fresh review；
158. review authorization = `development/169-p11-reuse-api-final-review-authorization.md`；
159. review stop = `development/170-p11-registry-artifact-parity-review-stop.md`；
160. P11-ISSUE-030 = REMEDIATED / FRESH REVIEW REQUIRED；
161. amendment evidence = `development/171-p11-registry-artifact-parity-amendment-evidence.md` = PASS；
162. premature d47a0b5 PASS artifact = `development/172-p11-d47a0b5-stale-pass-result-invalid.md` = INVALID / retained for audit；
163. candidate `85df002516d577531e68c303ad86c0903ca813c6` = INELIGIBLE after fresh review；
164. review authorization = `development/173-p11-registry-artifact-parity-final-review-authorization.md`；
165. review stop = `development/174-p11-artifact-path-contract-review-stop.md`；
166. P11-ISSUE-031 = REMEDIATED；
167. amendment evidence = `development/175-p11-artifact-path-amendment-evidence.md` = PASS；
168. candidate `b0424620f4b7e6fc0b898c657166b171fc35e7a7` = INELIGIBLE after manual cross-gate review；
169. review authorization = `development/176-p11-artifact-path-final-review-authorization.md`；
170. review stop = `development/178-p11-validation-finalization-review-stop.md`；
171. premature PASS artifact `development/177-p11-final-detached-design-review-result.md` = INVALID / NOT AUTHORITATIVE；
172. invalidation record = `development/179-p11-b042462-stale-pass-result-invalid.md`；
173. P11-ISSUE-032 = REMEDIATED；
174. amendment evidence = `development/180-p11-validation-finalization-amendment-evidence.md` = PASS；
175. candidate `992583b87af8f8c682dc434cc134317f4db35522` = INELIGIBLE after fresh review；
176. review authorization = `development/181-p11-validation-finalization-final-review-authorization.md`；
177. review stop = `development/182-p11-final-export-collision-review-stop.md`；
178. P11-ISSUE-033 = REMEDIATED；
179. amendment evidence = `development/183-p11-final-export-idempotency-amendment-evidence.md` = PASS；
180. candidate `866e07025e53b2da852700d2e688b3a3af0bc39a` = INELIGIBLE after fresh review；
181. review authorization = `development/184-p11-final-artifact-idempotency-final-review-authorization.md`；
182. review stop = `development/185-p11-final-export-byte-determinism-review-stop.md`；
183. P11-ISSUE-034 = REMEDIATED / FRESH REVIEW REQUIRED；
184. amendment evidence = `development/186-p11-final-export-byte-determinism-amendment-evidence.md` = PASS；
185. amended exact candidate = `00027be24be8e1c2ef3746600fa6e4f59ef641a5`；
186. review authorization = `development/187-p11-final-export-byte-determinism-final-review-authorization.md`；
187. candidate `00027be24be8e1c2ef3746600fa6e4f59ef641a5` = INELIGIBLE after manual final-path concurrency review；
188. review stop = `development/188-p11-final-path-concurrency-review-stop.md`；
189. P11-ISSUE-035 = REMEDIATED / FRESH REVIEW REQUIRED；
190. amendment evidence = `development/189-p11-final-path-concurrency-amendment-evidence.md` = PASS；
191. amended exact candidate = `2ef1e8ced4b5c3d7103c73bdc8cc532882fa7d47`；
192. review authorization = `development/190-p11-final-path-concurrency-final-review-authorization.md`；
193. candidate `2ef1e8ced4b5c3d7103c73bdc8cc532882fa7d47` = INELIGIBLE after concurrent registry persistence review；
194. review stop = `development/191-p11-registry-concurrency-review-stop.md`；
195. P11-ISSUE-036 = REMEDIATED / FRESH REVIEW REQUIRED；
196. amendment evidence = `development/192-p11-registry-concurrency-amendment-evidence.md` = PASS；
197. amended exact candidate = `cb35f537c75390d9b63b55af72c7278520ebd9be`；
198. review authorization = `development/193-p11-registry-concurrency-final-review-authorization.md`；
199. candidate `cb35f537c75390d9b63b55af72c7278520ebd9be` = INELIGIBLE after registry API surface review；
200. review stop = `development/194-p11-registry-api-surface-review-stop.md`；
201. P11-ISSUE-037 = REMEDIATED / FRESH REVIEW REQUIRED；
202. amendment evidence = `development/195-p11-registry-api-surface-amendment-evidence.md` = PASS；
203. amended exact candidate = `c3a2f84c7ebd5f8533adfaaa596b97f672dfb31d`；
204. review authorization = `development/196-p11-registry-api-surface-final-review-authorization.md`；
205. candidate `c3a2f84c7ebd5f8533adfaaa596b97f672dfb31d` = INELIGIBLE after governance-state review；
206. review stop = `development/197-p11-governance-status-review-stop.md`；
207. P11-ISSUE-038 = REMEDIATED / FRESH REVIEW REQUIRED；
208. amendment evidence = `development/198-p11-governance-status-amendment-evidence.md` = PASS；
209. amended exact candidate = `cd2fa0b01d23c0e3f75945c5cce5120738f51077`；
210. review authorization = `development/199-p11-governance-status-final-review-authorization.md`；
211. candidate `cd2fa0b01d23c0e3f75945c5cce5120738f51077` = INELIGIBLE after phase-banner/current-state review；
212. review stop = `development/200-p11-phase-banner-review-stop.md`；
213. P11-ISSUE-039 = REMEDIATED / FRESH REVIEW REQUIRED；
214. amendment evidence = `development/201-p11-phase-banner-amendment-evidence.md` = PASS；
215. amended exact candidate = `5877a238f5af6102ef48e56141cdb893590b6aab`；
216. formal review authorization = `development/202-p11-phase-banner-final-review-authorization.md`；
217. P11-A formal review result = `development/203-p11-final-detached-design-review-result.md` = PASS；
218. P11-A = CLOSED / PASS；
219. P11-B authorization = `development/204-p11-b-environment-runtime-probe-authorization.md`；
220. P11-B result = `development/205-p11-environment-runtime-probe.md` = PASS；
221. P11-B = CLOSED / PASS；
222. P11-C authorization = `development/206-p11-c-identity-period-authorization.md`；
223. P11-C implementation candidate = `027288f6d5bb064f82764b3dc19961996de1dab8`；
224. P11-C authoritative review authorization = `development/210-p11-c-final-review-authorization.md`；
225. P11-C review result = `development/211-p11-c-final-detached-code-review-result.md` = PASS；
226. P11-C integration merge = `1a5b04f22e1821558337821c758f70a7458da9ae`；
227. P11-C = CLOSED / PASS；
228. P11-D implementation = NOT AUTHORIZED / Design-First freeze required first；
229. P11 production = CLOSED；
230. Research MCP production / Semantic Resolver production remain closed / not authorized。
