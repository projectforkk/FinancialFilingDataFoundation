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
16. spec descriptor size/SHA use exact raw bytes with no decode/BOM/newline normalization；
17. spec bundle identity uses exact Section 8.1 canonical JSON bytes, descriptors sorted by exact logical_name, and hash input = descriptor array only；caller input order cannot change identity；
18. spec input list is non-empty and blank/duplicate logical names are rejected；
19. input paths are project-root-relative only; resolved target must be a regular file inside resolved project root; persisted path is resolved project-relative POSIX form; absolute/outside/traversal escape rejected；
20. verify distinguishes malformed/tampered bundle (`P10_INVALID_SPEC_INPUT`), current-file drift/missing (`P10_RESEARCH_SPEC_CHANGED`), and root escape (`P10_SPEC_PATH_OUTSIDE_PROJECT`)；
21. context manifest deterministic and `research_context_id` uses exact design/24 Section 13.7 bytes, including context schema version and canonical P9 review-root identity；
22. context includes exact P8 accepted-tool descriptor/fingerprint and exact P9 public-policy descriptor/fingerprint; main runtime does not import dedicated `mcp/server.py`; Independent Acceptance cross-checks P8 server version/exact 11 names in dedicated MCP runtime；
23. capability manifest is exact Section 14 mapping, caller cannot override/omit/add keys, and `capability_manifest_hash` uses Section 13.1 canonical JSON；
24. PDF visual capability = UNAVAILABLE in P10 v1；
25. semantic resolver capability = UNAVAILABLE；
26. canonical layer capability = UNAVAILABLE；
27. missing capability never silent fallback；
28. evidence ledger top-level schema/context/spec identity valid and claim keys unique；
29. document provenance resolves through accepted P8 service；
30. fact provenance resolves to the claimed document and declared relations；
31. evidence provenance resolves to the claimed document and declared fact/table/page scope；
32. table/page provenance resolves and declared scope relations are consistent；
33. P9 durable provenance resolves through exact resolution IDs + overlay snapshot using accepted P9 loader；
34. corrupt P9/P8 upstream state blocks as UPSTREAM_INVALID; no silent raw fallback；
35. raw/effective distinction is enforced by the frozen use-class compatibility profiles；
36. run-local/durable/derived distinctions are enforced exactly；
37. run-local and derived data never become Registry/canonical reusable data；
38. derived graph uses existing claim keys, has no self/cycle, and only verified/durable operands；
39. invalid ledger/ref/use-class/graph/context provenance is rejected deterministically；
40. P10 CLI success = exit 0, stdout exactly one canonical JSON line, stderr empty；
41. P10 CLI handled/domain/input failure = exit 1, stdout empty, stderr exactly one canonical JSON error line；
42. P10 CLI parser failure = `P10_CLI_ARGUMENT_ERROR`, exit 2, stdout empty, stderr exactly one JSON line with no argparse usage/help prose；
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
68. no hidden chain-of-thought stored as project artifact；
69. every P10 Python command binds `PYTHONPATH` to the exact frozen candidate worktree `src`; detached review/acceptance must not execute source from shared main/another worktree, and FFDF must not be editable/installed into main `.venv` merely for P10；
70. P10-G integration instruction identity is verified from the exact frozen candidate Git blob bytes, not arbitrary checkout bytes; candidate commit and Git-blob SHA256 must match the acceptance freeze；
71. frozen acceptance fixture manifest and all frozen runtime-spec fixture identities are verified from exact candidate Git blob bytes; detached checkout EOL representation must not be used as fixture identity or copied into the acceptance workspace。

### 2.1 P10-F CLI acceptance matrix

Independent Acceptance must use raw subprocess execution against the exact frozen candidate and verify design/24 Section 31 byte/exit behavior.

Mandatory CLI matrix：

- exactly four subcommands；
- stdin JSON object only；
- no request-file option；
- stdin >16 MiB rejected as `P10_CLI_INPUT_INVALID`；
- empty/non-UTF8/invalid/non-object request rejected deterministically；
- extra/missing request envelope keys rejected；
- `freeze-spec` success exact envelope/data；
- `verify-spec` success exact envelope/data；
- `build-context` success exact envelope/data；
- `validate-ledger` success exact envelope/data；
- success = exit 0 / one stdout JSON line / empty stderr；
- handled failure = exit 1 / empty stdout / one stderr JSON line；
- parser failure = exit 2 / `P10_CLI_ARGUMENT_ERROR` / no usage/help prose；
- unknown/missing command gives `command=null`；
- recognized command parser failure retains exact command string；
- `--help` / `-h` is parser JSON error, not prose；
- catalog path must be project-root-relative；
- invalid catalog maps `P10_CATALOG_INVALID`；
- build-context spec drift precedes catalog semantic failure；
- validate-ledger spec drift precedes ledger semantic failure；
- validate-ledger deterministically rebuilds ResearchContext from spec/catalog/review-root；
- no `ResearchContext.from_dict` acceptance dependency；
- accepted P10-C/D/E reason codes propagate unchanged；
- unexpected internal failure = `P10_CLI_FAILED` with fixed message `unexpected CLI failure`；
- no traceback；
- canonical JSON is UTF-8, sorted-key, compact separator, `allow_nan=False`；
- no network/AI/external MCP SDK/subprocess/shell/SQL；
- no P8 business-call proxy；
- no P9 mutation；
- no implicit artifact write；
- exact-candidate source binding preserved。

### 2.2 P10-G tracked artifact identity

Acceptance must freeze:

- exact P10 candidate commit；
- `integration/p10/FFDF_RESEARCH_INTEGRATION.md` exact Git blob object/content；
- SHA256 of the Git blob content bytes。

For candidate `3a805a8f333ac20770d6aec1c8285d93993d18fc`, known Git-blob SHA256 is:

`ef10406c9957f7a68a9af001c913deef0a057e166100a2d852c0c8fcd2c46296`

Independent Acceptance must calculate this from exact Git blob bytes, not from arbitrary checked-out worktree bytes. Blob extraction must be binary-safe; do not use a text/object pipeline that decodes/re-encodes `git cat-file` output before hashing.

If the detached worktree uses CRLF due Git checkout policy, record that representation separately; it is not an identity mismatch when LF-normalized content equals the frozen Git blob and the Git blob SHA matches.

The Git blob must decode as UTF-8 and contain no BOM.

### 2.3 Frozen acceptance fixture identity

The frozen acceptance fixture package uses exact candidate Git blob bytes as the cross-worktree identity source.

This applies to:

- `acceptance/p10-fixtures/manifest.json`;
- every fixture listed by that manifest.

Independent Acceptance must:

1. read the fixture manifest from `git cat-file blob HEAD:acceptance/p10-fixtures/manifest.json` using binary-safe subprocess bytes;
2. parse that exact blob as UTF-8 JSON;
3. read every listed fixture from `git cat-file blob HEAD:acceptance/p10-fixtures/<name>`;
4. validate the manifest size/SHA against those exact blob bytes;
5. copy those validated blob bytes into the mutable acceptance workspace;
6. record checkout representation separately if useful, but never treat checkout CRLF/LF bytes as frozen fixture identity.

Forbidden:

- using arbitrary checked-out Markdown bytes as the manifest identity source;
- copying CRLF-converted checkout bytes into the acceptance workspace when the frozen Git blob is LF;
- editing the fixture manifest to accommodate checkout EOL conversion;
- changing `.gitattributes` merely to make P10-N pass.

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

P10-ISSUE-007 fixture rule：

- isolated P9 store必须在最终目标 review root 通过 accepted `prepare_review_overlay` 创建；
- 不得复制/移动既有 P9 review directory 到新路径后当作有效 store；
- 不得编辑 manifest 绕过 `review_dir` path binding；
- 若需要重现既有 reviewed semantics，必须使用 isolated root新生成的 task/evidence contract重新提交 supported action；
- acceptance记录新生成的 isolated resolution ID 与 overlay-set hash；
- accepted/source P9 review root before/after bytes必须不变。

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

### 11.1 P10-E frozen FFDF ledger contract

Independent Acceptance 必须按 design/24 Sections 26–27 验证：

- top-level schema = `p10-research-evidence-ledger-v1`；
- `research_context_id` / `spec_bundle_hash` exact match；
- claim keys unique，entry order不改变 validation result；
- only four FFDF use classes are accepted；
- `EXTERNAL_RUNTIME_SOURCE` is rejected from FFDF ledger v1；
- `P8_RAW_DIRECT` 不能携带 P9 refs、derived refs 或 semantic assertions；
- source-backed `RUN_LOCAL_STRUCTURED_VERIFIED` 必须有 P8 refs + non-empty semantic assertions；
- derived `RUN_LOCAL_STRUCTURED_VERIFIED` 必须只通过 operand claim keys 建 provenance；
- `P9_DURABLE_RESOLVED` 必须绑定 exact document + resolution IDs + overlay snapshot hash；
- `UNRESOLVED` 不能作为 derived operand；
- derived graph 必须 existing-key / no-self / acyclic / order-independent；
- operands 只能来自 `RUN_LOCAL_STRUCTURED_VERIFIED` 或 `P9_DURABLE_RESOLVED`；
- P8 refs 通过 accepted `McpQueryService` 验证；
- P9 durable refs 通过 accepted `load_resolved_snapshot` 验证；
- historical P9 snapshot 可按 exact overlay identity 验证，不要求等于当前 latest overlay；
- missing explicit ref/path = `P10_PROVENANCE_INVALID`；
- corrupt accepted P8/P9 state = `P10_UPSTREAM_INVALID`；
- current spec drift = `P10_RESEARCH_SPEC_CHANGED`；
- current catalog/context mismatch = `P10_CONTEXT_INCOMPATIBLE`；
- no corrupt-P9 -> raw silent fallback；
- PASS output schema = `p10-provenance-validation-v1`；
- validation artifact contains no absolute path/time/random/hidden reasoning。

Acceptance 必须使用 exact API：

```python
validate_evidence_ledger(
    context,
    ledger,
    spec_bundle,
    p8_catalog,
)
```

不得在 acceptance 中通过额外 arbitrary path 参数绕过 frozen context/catalog contract。

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

每个 acceptance Python command 还必须先：

```powershell
$env:PYTHONPATH="<detached-p10-candidate-worktree>\src"
```

并记录实际值。禁止从 shared main / active development worktree 导入 candidate source。

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

- Mandatory 70 项全部有 credible evidence；
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
