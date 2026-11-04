# 38 — P10 Independent Acceptance Instruction

状态：**DESIGN BASELINE — P10 ACCEPTANCE**

Phase：
`P10 — Codex Dynamic Research Integration`

最终 verdict：
`PASS / FAIL / BLOCKED`

P10 acceptance 只验收 P10 v1。Research MCP、Semantic Resolver、P11 production 不在本次 scope。

---

## 1. Frozen identity

必须冻结并记录：

- design baseline SHA；
- production candidate SHA；
- formal Code Review PASS SHA；
- accepted P8 merge；
- accepted P9 merge；
- P8 tool fingerprint；
- P9 policy/schema versions；
- main/P10 runtime identity；
- exact Spec A/B bytes + SHA256；
- P8 catalog SHA；
- isolated P9 review-root fixture；
- exact acceptance commands。

candidate HEAD变化 → 本次 acceptance全部作废。

---

## 2. Mandatory items

1. frozen candidate HEAD stable；
2. design/24 exact baseline；
3. P0-P9 accepted source/tests zero unintended diff；
4. full P0-P10 suite PASS；
5. P8 exact 11 tools unchanged；
6. P8 raw `ffdf_get_fact` contract unchanged；
7. P9 source/tests/semantics unchanged；
8. no Research MCP production；
9. no Semantic Resolver production；
10. no P11 production；
11. no remote AI/OpenAI/Codex API in P10 production；
12. no network in deterministic P10 package；
13. no subprocess/shell/SQL execution surface；
14. project-root path guard；
15. spec file explicit-list only；
16. spec bundle raw-byte SHA correct；
17. spec bundle identity deterministic/order-independent；
18. duplicate logical names rejected；
19. external/traversal spec paths rejected；
20. spec mutation detected；
21. context manifest deterministic；
22. context includes exact P8/P9 fingerprints；
23. capability manifest exact；
24. PDF visual capability = UNAVAILABLE in P10 v1；
25. semantic resolver capability = UNAVAILABLE；
26. canonical layer capability = UNAVAILABLE；
27. missing capability never silent fallback；
28. evidence ledger schema valid；
29. document provenance resolves；
30. fact provenance resolves；
31. evidence provenance resolves；
32. table/page provenance resolves；
33. P9 resolution provenance resolves；
34. corrupt P9 state blocks；
35. raw/effective distinction preserved；
36. run-local/durable distinction preserved；
37. run-local data never Registry reusable；
38. derived claim references explicit operand claims；
39. invalid derived provenance rejected；
40. P10 CLI success JSON-only；
41. P10 CLI handled failure JSON-only；
42. P10 CLI parser failure deterministic JSON；
43. thin integration instruction contains no fixed question mapping；
44. thin integration instruction contains no fixed company/period/report schema；
45. runtime research spec is primary instruction source；
46. Spec A and Spec B produce different spec bundle hashes；
47. Spec A/B run without P10 production change；
48. Codex reads each frozen spec before FFDF research；
49. Codex tool selection changes according to information need；
50. live P8 document/validation query PASS；
51. live fact/table/evidence query PASS；
52. live relevant P9 interaction PASS；
53. isolated P9 review root only；
54. accepted base artifacts immutable；
55. missing filing returns DATA_PREPARATION_REQUIRED；
56. structured-insufficient case returns VISUAL_CAPABILITY_REQUIRED；
57. unresolved review never guessed；
58. REVIEW_REQUIRED not treated as DATA_UNUSABLE；
59. REVIEW_REQUIRED not treated as canonical reusable；
60. no raw numeric correction via P9；
61. external source provenance separated if used；
62. evidence ledger fresh validation PASS；
63. research output satisfies frozen runtime spec；
64. COMPLETE only when all required outputs supported；
65. partial/gap behavior follows runtime spec；
66. performance gates PASS；
67. all temp/basetemp/workspace remain under project root；
68. no hidden chain-of-thought stored as project artifact。

---

## 3. Dynamic Spec A/B

Acceptance 必须使用两份内容实质不同的 runtime research spec。

要求：

- files frozen before run；
- raw bytes SHA recorded；
- P10 production candidate完全相同；
- Codex完整读取当前 spec；
- resulting requested evidence/tool usage不同；
- output follows respective spec。

不得通过修改 P10 instruction/production 来适配 Spec B。

---

## 4. Live COMPLETE run

至少一个完整 live research run。

优先 fixture：

- CN 600519 FY2024；
- HK 00700 FY2024。

必须记录：

- document SHA；
- P8 calls summary；
- P9 calls/state summary；
- selected facts/tables/evidence；
- output artifact；
- evidence ledger；
- ledger validation；
- base before/after hashes。

最终 run verdict必须为 `COMPLETE`。

---

## 5. P9 controlled review case

使用 isolated P10 acceptance review root，不写 accepted P9 review roots。

若 live spec需要 review：

- prepare；
- tasks；
- only supported/evidence-grounded submit；
- materialize；
- raw unchanged；
- resolution identity可验证。

不得 mass fill。

不得为了让 run COMPLETE 强制关闭 unresolved issue。

---

## 6. REVIEW_REQUIRED boundary

必须独立证明：

- document-level REVIEW_REQUIRED 仍可读取/引用 raw evidence；
- specific claim可在足够 evidence 下完成；
- document-level canonical reuse仍为 false时不得说 true；
- unrelated unresolved issue不自动使所有 raw evidence unusable。

---

## 7. Visual capability gap

P10 v1 没有 Research MCP visual renderer。

构造一个确实需要 visual evidence 的 case。

必须：

```text
structured P8/P9 insufficient
→ P10_VISUAL_CAPABILITY_REQUIRED
→ no guess
→ no arbitrary PDF open through P10
→ no fake RUN_LOCAL_VERIFIED
```

不得临时实现 screenshot/render tool绕过 acceptance scope。

---

## 8. Missing filing gap

runtime spec要求一个 catalog不存在 filing：

必须：

- explicit `P10_DATA_PREPARATION_REQUIRED`；
- 不下载；
- 不换期间；
- 不用另一家公司/年度替代；
- 不声称“未披露”。

---

## 9. Spec mutation negative

freeze后修改任一 input byte。

必须：

`P10_RESEARCH_SPEC_CHANGED`

同一 research_context不得继续。

---

## 10. Corrupt P9 negative

若 P9 review state存在但 tamper/validation失败：

必须 BLOCK。

禁止：

```text
corrupt overlay
→ ignore overlay
→ silently use raw as if overlay absent
```

---

## 11. Provenance

每个 acceptance required claim至少有一个可验证 provenance entry。

FFDF provenance可引用：

- document_sha256；
- page；
- table；
- raw_fact；
- evidence；
- P9 resolution；
- overlay_set_hash。

external source若存在必须单独 source class。

不得把自然语言“模型看到了”当 provenance。

---

## 12. Immutability

before/after 至少覆盖：

- source PDF；
- P3；
- P4 where applicable；
- P5；
- P6；
- P7；
- P8 catalog；
- Registry；
- P8 runtime lock。

P9只允许 isolated acceptance review root变化。

---

## 13. Performance

deterministic P10 plumbing：

- freeze spec <= 2s / <=10MiB；
- verify spec <= 2s；
- build context <= 2s（不含 P8 first artifact load）；
- validate ledger <= 5s / <=1000 entries。

Codex inference/tool duration单独记录，不作为 deterministic performance fail，除非发生 hang/timeout导致无法完成 acceptance。

---

## 14. Security / scope scan

必须证明 P10 production无：

- openai；
- anthropic；
- remote LLM client；
- requests/httpx/socket/network client；
- subprocess；
- shell；
- arbitrary SQL；
- arbitrary file browser；
- Research MCP renderer；
- Semantic Resolver；
- P11 provider。

P10 host-side Codex运行不等于 P10 production调用 AI API；二者必须在 evidence 中分层。

---

## 15. Acceptance worktree

必须使用独立 detached worktree：

`D:\\Codex\\FinancialFilingDataFoundation\\worktrees\\acceptance\\p10-<sha>`

所有 basetemp/temporary state必须在项目根内。

Windows path length在 freeze 时按当前 accepted path policy选择足够短的 project-local basetemp。

禁止使用 project root之外 sibling temp。

---

## 16. Acceptance executor prohibition

Independent Acceptance executor不得修改：

- production；
- tests；
- design；
- accepted P8/P9 artifacts；
- runtime/dependencies；
- tracked catalog/config。

发现问题：

- verdict FAIL/BLOCKED；
- 记录事实；
- 回 Design-First；
- 不在 acceptance现场修 code。

---

## 17. PASS condition

PASS 要求：

- Mandatory 68 项全部有 credible evidence；
- fresh focused/full PASS；
- dynamic Spec A/B PASS；
- live COMPLETE run PASS；
- P9 controlled review boundary PASS；
- visual gap negative PASS；
- missing filing negative PASS；
- spec mutation negative PASS；
- corrupt P9 negative PASS；
- base immutability PASS；
- no open design/correctness/security finding。

PASS 后只授权 P10 closeout。

不会自动授权 Research MCP / Semantic Resolver / P11 production。
