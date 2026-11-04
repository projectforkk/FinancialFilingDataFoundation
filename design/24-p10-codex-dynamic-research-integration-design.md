# 24 — P10 Codex Dynamic Research Integration 详细设计

状态：**DESIGN BASELINE — P10**

阶段：**P10 — Codex Dynamic Research Integration**

前置 accepted baseline：
- P0–P9 = DONE / PASS；
- accepted P8 merge = `ee934ad05812c69b79f76db43e62cfd4050efb8e`；
- accepted P9 merge = `58a1d2236b68a56fc66ddf8b97603e7232c87265`；
- P9 Independent Acceptance = `acceptance/37-p9-acceptance-result.md` = PASS；
- P9 closeout = `development/75-p9-closeout.md`；
- current main at P10 design start = `e9b30626f2b88ac5527d42bd76d0b682efbeef0e`。

本设计只定义 P10。P11、Research MCP production、Semantic Resolver production 仍未获授权。

---

## 1. P10 目标

P10 建立并验收 **Codex 对 FFDF 的动态研究集成模式**。

核心目标不是提供固定研究 Skill，而是保证：

```text
runtime research specification
        ↓
Codex reads current specification completely
        ↓
Codex derives information needs dynamically
        ↓
P8 raw/evidence query
        ↓
P9 durable reviewed state where relevant
        ↓
run-local reasoning with explicit provenance
        ↓
research output required by the current specification
```

同一套 P10 production 在不修改代码的情况下，必须能够因为运行时研究规范内容不同而改变：

- 研究问题；
- 公司/期间范围；
- 查询顺序；
- 需要的事实/表格/证据；
- 是否需要 P9 review；
- 输出结构与要求。

---

## 2. 核心职责边界

长期职责保持：

```text
P8
= Raw Data & Evidence

Codex
= 财务理解 / 当前 research-run reasoning

P9
= Durable Reviewed Decision Store

P10
= Dynamic Research Integration Contract + deterministic run plumbing

Research MCP
= future additive Resolved Query + PDF Visual Evidence

Semantic Resolver
= future deterministic semantic automation
```

P10 不把任何上层职责下沉到 P8/P9。

---

## 3. P10 明确不做

P10 v1 禁止：

- 固定 Codex Skill；
- 固定问题数量；
- 固定问题编号 → tool sequence 映射；
- 固定报告章节映射；
- 把用户研究约束正文复制进 production；
- deterministic PDF parsing；
- P5/P6 raw correction；
- canonical metric mapping；
- Fiscal Period Engine；
- YoY/QoQ/TTM 的 canonical reusable calculation layer；
- valuation engine；
- investment recommendation engine；
- acquisition/download；
- 修改 P8 11-tool contract；
- 修改 P9 resolution semantics；
- MCP 内 AI / OpenAI / Codex API；
- P10 Python production 调用远程 LLM API；
- arbitrary filesystem browse；
- arbitrary SQL/shell/Python execution surface；
- silent fallback；
- guessing missing data；
- 把 run-local reasoning 注册成 reusable parsed data；
- Research MCP renderer/visual tools；
- Semantic Resolver；
- P11 SEC provider。

---

## 4. Accepted dependencies

P10 v1 只依赖已验收能力。

### 4.1 P8

P8 11 个 read-only tools 保持完全不变：

1. `ffdf_list_documents`
2. `ffdf_get_document`
3. `ffdf_search_document`
4. `ffdf_read_pages`
5. `ffdf_list_sections`
6. `ffdf_list_tables`
7. `ffdf_get_table`
8. `ffdf_list_raw_facts`
9. `ffdf_get_fact`
10. `ffdf_get_evidence`
11. `ffdf_get_validation`

`ffdf_get_fact` 永远是 RawFact，不得被 P10 改成 semantic/resolved fact。

### 4.2 P9

P10 可使用 accepted P9 local API / CLI：

- prepare
- tasks
- submit
- resolutions
- materialize
- report

以及 accepted public APIs。

P10 不重新实现：

- resolution identity；
- supersession；
- prior active state；
- evidence validation；
- overlay hash；
- resolved status；
- payload security。

---

## 5. P10 与 Codex 的边界

Codex 是 P10 的 reasoning host，不是 P10 production dependency。

P10 production：

- 不导入 Codex SDK；
- 不调用 Codex API；
- 不启动 remote AI request；
- 不保存或实现模型推理算法。

Codex 负责：

- 完整读取当前 runtime research specification；
- 根据 specification 动态推导信息需求；
- 选择 P8/P9 查询；
- 解释结构化 table/header/page text；
- 判断是否已有足够 evidence；
- 在满足 P9 contract 时选择性提交 durable resolution；
- 形成当前 run 的研究结论。

---

## 6. Runtime Research Specification Bundle

每个 research run 必须先冻结用户当前提供的研究规范。

规范可以由多个文件组成，例如：

- task prompt；
- constraints；
- question list；
- output requirements；
- company-specific supplement；
- valuation/research policy；
- terminology rules。

P10 不规定这些文件内部 schema。

P10 只把它们当作 **opaque runtime instruction bytes** 进行冻结。

---

## 7. Spec 文件安全边界

P10 deterministic loader 只读取 caller 显式列出的 project-root-relative 文件。

要求：

- 路径必须位于 `D:\\Codex\\FinancialFilingDataFoundation` 内；
- 禁止 absolute external path；
- 禁止 traversal escape；
- 禁止目录自动递归扫描；
- 禁止“找到所有 prompt 文件”式隐式发现；
- symlink/junction resolve 后仍必须在 project root；
- caller 明确给出的文件顺序不作为 identity；identity 按 logical name 排序。

运行前若用户资料来自其他系统，应先由外部工作流显式提供为当前 run 的输入文件；P10 不自行访问 ChatGPT Library、Gmail、Google Drive 或网络。

---

## 8. Spec manifest

Schema：

`p10-research-spec-bundle-v1`

每个文件记录：

```json
{
  "logical_name": "company-analysis-constraints",
  "relative_path": "workspace/research-inputs/run-x/constraints.md",
  "size": 12345,
  "sha256": "..."
}
```

bundle：

```json
{
  "schema_version": "p10-research-spec-bundle-v1",
  "files": [],
  "spec_bundle_hash": "..."
}
```

`spec_bundle_hash`：

```text
SHA256(canonical JSON of sorted file descriptors)
```

文件内容本身不复制进 manifest。

---

## 9. Spec freeze rule

research run 一旦开始：

- Codex 必须读取 frozen bytes；
- P10 在关键阶段可重新验证文件 SHA；
- 任一文件变化 → `P10_RESEARCH_SPEC_CHANGED`；
- 不允许继续同一 run 并静默读取新版本。

用户要修改研究规则：

```text
end/current run
→ freeze new spec bundle
→ new research context
```

---

## 10. P10 deterministic support package

建议 package：

```text
src/financial_filing_data_foundation/
  research/
    __init__.py
    models.py
    spec.py
    context.py
    provenance.py
    cli.py
```

该 package 不做 financial reasoning。

---

## 11. Public deterministic APIs

### 11.1 freeze_research_spec

```python
freeze_research_spec(
    project_root: str | Path,
    files: Sequence[ResearchSpecInput],
) -> ResearchSpecBundle
```

职责：

- path guard；
- byte hash；
- deterministic ordering；
- manifest/hash。

### 11.2 verify_research_spec

```python
verify_research_spec(
    project_root,
    bundle,
) -> None
```

任何 drift 失败。

### 11.3 build_research_context

```python
build_research_context(
    spec_bundle,
    p8_catalog,
    p9_review_root,
    capability_policy,
) -> ResearchContext
```

只构造当前 accepted capability context，不替 Codex选研究问题。

### 11.4 validate_evidence_ledger

```python
validate_evidence_ledger(
    context,
    ledger,
) -> ProvenanceValidation
```

只验证 provenance identity / existence / compatibility，不判断投资结论正确性。

---

## 12. Research Context

Schema：

`p10-research-context-v1`

至少：

```json
{
  "schema_version": "p10-research-context-v1",
  "integration_policy_version": "p10-dynamic-research-v1",
  "spec_bundle_hash": "...",
  "p8_catalog_sha256": "...",
  "p8_tool_contract": "p8-mcp-result-v1/11-tools",
  "p9_review_policy": "p9-review-policy-v1",
  "p9_review_root": "project-relative configured root",
  "capabilities": {},
  "research_context_id": "..."
}
```

不得保存 absolute filesystem paths 到可共享 research provenance。

---

## 13. Research context identity

`research_context_id`：

```text
SHA256(
  integration_policy_version
  + "\0" + spec_bundle_hash
  + "\0" + p8_catalog_sha256
  + "\0" + p8_tool_contract_fingerprint
  + "\0" + p9_policy_fingerprint
  + "\0" + capability_manifest_hash
)
```

不包含：

- current time；
- random UUID；
- Codex response；
- tool call order。

它表示 deterministic input context，不表示“模型输出 deterministic”。

---

## 14. Capability Manifest

P10 v1 必须显式声明：

```text
P8_RAW_QUERY                 AVAILABLE
P8_PAGE_TEXT                 AVAILABLE
P8_TABLE_STRUCTURED          AVAILABLE
P8_EVIDENCE                  AVAILABLE
P8_VALIDATION                AVAILABLE
P9_REVIEW                    AVAILABLE
P9_RESOLVED_VIEW             AVAILABLE
PDF_VISUAL_EVIDENCE          UNAVAILABLE
SEMANTIC_RESOLVER            UNAVAILABLE
CANONICAL_METRIC_LAYER       UNAVAILABLE
P11_SEC_PROVIDER             UNAVAILABLE
```

任何不可用 capability 被当前 runtime specification 需要时，必须显式阻断。

---

## 15. Capability gap reason codes

至少：

- `P10_DATA_PREPARATION_REQUIRED`
- `P10_VISUAL_CAPABILITY_REQUIRED`
- `P10_SEMANTIC_CAPABILITY_REQUIRED`
- `P10_CANONICAL_CAPABILITY_REQUIRED`
- `P10_EXTERNAL_SOURCE_REQUIRED`
- `P10_UPSTREAM_INVALID`
- `P10_REVIEW_UNRESOLVED`
- `P10_INCOMPATIBLE_REQUIREMENT`

不能用“尽力猜测”替代。

---

## 16. Document availability

P10 不做 acquisition。

Codex 首先用 `ffdf_list_documents` 查当前 catalog。

若 runtime specification 需要的 filing 不存在：

`P10_DATA_PREPARATION_REQUIRED`

P10 不：

- 自动下载；
- 修改 catalog；
- 猜测最近 filing 可以替代缺失 filing；
- 把其他 fiscal period 当作目标 period。

数据准备属于独立 upstream workflow。

---

## 17. Query priority

每个信息需求遵循：

```text
durable resolved information already exists?
       ↓ yes
use P9 resolved state
       ↓ no
P8 exact/raw structured information
       ↓
structured context sufficient?
       ↓ yes
current-run research use
       ↓ no
P9 supported evidence-grounded review possible?
       ↓ yes
optional controlled P9 resolution
       ↓ no
capability gap / unresolved
```

P10 不要求 document 必须整体 PASS 才允许读取 raw evidence。

---

## 18. REVIEW_REQUIRED consumption

正式规则：

`REVIEW_REQUIRED != DATA_UNUSABLE`

Codex 可以使用：

- RawFact；
- Evidence；
- Table；
- Page Text；
- Validation issue context；
- P9 effective fields。

但不得把 document-level `REVIEW_REQUIRED` 静默说成 canonical reusable。

---

## 19. Research-use classes

P10 v1 对当前 run 的数据使用分为：

### P9_DURABLE_RESOLVED

已通过 validated P9 resolution/snapshot 得到。

可：

- 当前研究使用；
- 后续 run 在相同 base/overlay identity 下复用。

### P8_RAW_DIRECT

直接引用 P8 raw fact / evidence / page / table。

可：

- 原文/原始数字引用；
- 明确标注未知 semantic field。

不得：

- 在未知 period/unit/scope/value role 时假装语义完整。

### RUN_LOCAL_STRUCTURED_VERIFIED

Codex 只基于 P8 structured evidence（table/header/page text/evidence）明确解释当前 run 的 semantic meaning，但未形成 durable P9 resolution。

可用于当前 run。

必须：

- 保存 FFDF provenance；
- 标记 `durable=false`；
- 标记 `canonical_reuse_eligible=false`。

### UNRESOLVED

证据不足或冲突。

不得用于需要唯一 semantic interpretation 的结论或 derived calculation。

---

## 20. Structured sufficiency gate

P10 v1 没有 PDF visual tool。

如果 structured evidence 已明确提供：

- value；
- period/header relationship；
- unit/dimension；
- scope；
- value role；

Codex 可形成 `RUN_LOCAL_STRUCTURED_VERIFIED`。

如果以下任一情况无法通过 P8/P9 解决：

- header relationship 缺失/冲突；
- P5 table crop/structure疑似错误；
- P6 目标 fact 缺失且 P3/P5 structured locator不足；
- raw value 与 visible/structured table context冲突；
- period/unit/scope/value role仍多义；
- cross-page context无法证明；

必须：

`P10_VISUAL_CAPABILITY_REQUIRED`

不得假装 design/29 已实现。

---

## 21. P9 usage policy

P9 resolution 不是遇到 REVIEW_REQUIRED 就强制执行。

只有当前 research need 需要 semantic clarification，且：

- task = SUPPORTED；
- target 合法；
- evidence 满足 P9 contract；
- Codex 能明确解释；
- 不涉及 raw numeric correction；

才允许 submit。

否则保持 unresolved。

---

## 22. P9 durable vs run-local

若 Codex 判断：

`EXPLICIT_AND_ANCHORABLE`

且当前 P9 action支持，可提交 P9。

如果解释只对当前 run 有意义或不满足 P9 evidence contract：

- 不 submit；
- 使用 run-local class；
- 不生成 reusable data。

---

## 23. Raw extraction defect

如果 structured evidence 本身证明 P5/P6 raw extraction 有 defect：

```text
STOP P9 correction
→ classify RAW_EXTRACTION_DEFECT
→ Design-First parser fix
→ rerun affected P5/P6/P7
```

P10 不允许通过 P9修改：

- raw numeric value；
- parsed numeric value；
- raw metric name。

---

## 24. Derived-use gate

任何当前 run derived calculation 的 operand 必须达到：

`DERIVED_USE_READY`

至少要求：

1. numeric value known/verified；
2. period verified；
3. value role verified；
4. required unit/dimension verified；
5. required scope verified；
6. no unresolved conflict；
7. provenance complete；
8. operation compatibility PASS。

---

## 25. Operation compatibility examples

### YoY

- compatible metric meaning；
- valid comparative periods；
- compatible scope；
- compatible dimension；
- compatible currency/scale where monetary。

### Margin

- numerator/denominator same period；
- compatible scope；
- compatible monetary basis。

### QoQ

YTD 不得当 standalone quarter。

### TTM

只有 runtime spec要求且 operands 可以证明 compatible 时才可当前 run 计算。

P10 不把这些 derived result 注册为 canonical reusable data。

---

## 26. Evidence Ledger

每个 research run 应产生 run-local evidence ledger。

Schema：

`p10-research-evidence-ledger-v1`

entry 至少：

```json
{
  "claim_key": "q1-revenue",
  "use_class": "P8_RAW_DIRECT",
  "document_sha256": "...",
  "page_nos": [1],
  "table_ids": [],
  "raw_fact_ids": [],
  "evidence_ids": [],
  "p9_resolution_ids": [],
  "overlay_set_hash": null,
  "semantic_assertions": {},
  "derived_from_claim_keys": []
}
```

ledger 是 provenance，不是 research rule。

---

## 27. Ledger validation

P10 deterministic validator 至少验证：

- document exists in current catalog；
- raw_fact belongs document；
- evidence belongs document/fact where claimed；
- table belongs document；
- page bounds；
- P9 resolution/snapshot identity valid；
- use_class compatible with refs；
- derived claim references existing operand claim keys；
- spec/context identity matches。

不验证：

- Codex自然语言结论是否“聪明”；
- 投资建议是否正确；
- 外部网页事实真伪。

---

## 28. External source boundary

runtime specification 可以要求 FFDF 之外的信息。

例如：

- market price；
- industry data；
- current policy；
- competitor information。

P10 不固化来源列表，也不发网络请求。

Codex 若按 runtime specification 使用外部来源：

- 必须与 FFDF provenance 分层；
- 标记 source class = `EXTERNAL_RUNTIME_SOURCE`；
- 不得把外部 source 当 P8/P9 evidence；
- 不得用外部 source 支持 P9 resolution，除非未来 P9 design明确扩展。

---

## 29. Thin Integration Instruction

P10 允许新增：

`integration/p10/FFDF_RESEARCH_INTEGRATION.md`

内容只能描述：

- P8/P9 能力；
- runtime spec freeze；
- provenance requirement；
- no guessing；
- capability gaps；
- durable vs run-local；
- prohibited behavior。

不得包含：

- 用户固定问题清单；
- 某一版研究报告章节；
- 固定年份范围；
- 固定公司；
- 固定估值方法；
- 固定投资规则正文。

---

## 30. No fixed question mapping

严禁 production 出现类似：

```text
question_1 → ffdf_get_document
question_2 → ffdf_get_table
question_17 → P9 submit
```

Codex 必须根据当前 information need 选择工具。

Acceptance 必须用至少两个不同 runtime spec 证明这一点。

---

## 31. P10 local CLI

建议 machine CLI：

`python -m financial_filing_data_foundation.research.cli`

v1 commands：

- `freeze-spec`
- `verify-spec`
- `build-context`
- `validate-ledger`

CLI：

- JSON stdout only；
- diagnostic JSON stderr；
- no argparse text help；
- no network；
- no AI；
- no arbitrary command execution。

P10 CLI 不代理 P8/P9 business calls；Codex仍直接调用 P8 MCP / P9 CLI。

---

## 32. Operational run layout

ignored workspace：

```text
workspace/research-runs/
  <research_context_id>/
    spec_manifest.json
    context_manifest.json
    evidence_ledger.json
    provenance_validation.json
    output/
```

FFDF 不要求保存 Codex hidden reasoning。

不得把 chain-of-thought 当 project artifact。

---

## 33. Immutability

P10 run 前后必须保持：

- source PDFs unchanged；
- P3/P4/P5/P6/P7 unchanged；
- P8 catalog unchanged unless separately prepared by upstream；
- Registry unchanged；
- P8 runtime unchanged。

P9 只有 caller/Codex显式执行 authorized P9 operation时可改变指定 review_root。

---

## 34. Determinism boundary

P10 deterministic claims只覆盖：

- spec hashes；
- context manifest；
- capability manifest；
- provenance validator；
- same explicit inputs → same deterministic artifacts。

P10 不声称：

- Codex tool order deterministic；
- Codex natural language output byte-identical；
- reasoning deterministic。

---

## 35. Error model

至少：

- `P10_INVALID_SPEC_INPUT`
- `P10_SPEC_PATH_OUTSIDE_PROJECT`
- `P10_RESEARCH_SPEC_CHANGED`
- `P10_CATALOG_INVALID`
- `P10_CONTEXT_INCOMPATIBLE`
- `P10_PROVENANCE_INVALID`
- `P10_DATA_PREPARATION_REQUIRED`
- `P10_VISUAL_CAPABILITY_REQUIRED`
- `P10_UPSTREAM_INVALID`
- `P10_REVIEW_UNRESOLVED`
- `P10_CAPABILITY_UNAVAILABLE`

normal client 不输出 traceback。

---

## 36. Security

P10 deterministic package：

- no network；
- no AI API；
- no MCP SDK requirement in main runtime；
- no arbitrary filesystem traversal；
- no arbitrary SQL；
- no shell；
- no subprocess；
- no credentials read；
- no environment dump。

P8 MCP AI API rule保持：

`MCP_AI_API_CALLS = FORBIDDEN`

---

## 37. Research MCP / design/29 reconciliation

旧 draft design/29 定义未来 additive：

- Resolved Query；
- review context；
- missing-fact locator；
- PDF render/table/group；
- VisualRef；
- visual decision classes。

P10 v1 **不实现这些 Research MCP tools**。

P10 v1 对 design/29 的关系：

```text
P10 core accepted P8/P9 integration
      ↓
structured sufficient → research continues
      ↓
structured insufficient → P10_VISUAL_CAPABILITY_REQUIRED
      ↓
future separately authorized Research MCP
      ↓
visual capability becomes AVAILABLE
```

因此 P10 core 不被 Research MCP 阻塞。

---

## 38. Semantic Resolver / design/28 reconciliation

design/28 是 future deterministic semantic architecture。

P10 v1：

- 不构建 Header Graph；
- 不实现 Rule Registry；
- 不生成 semantic artifact；
- 不把 Codex decisions自动升级为 rules。

P10 可以记录 recurring structured/review gap telemetry，作为未来 rule candidate 输入，但 production rule promotion 必须另走 Design-First。

---

## 39. Capability evolution contract

未来 Research MCP / Semantic Resolver 验收后，只允许 additive capability。

不得改变：

- P8 raw contract；
- P9 durable history semantics；
- P10 runtime-spec-first原则。

P10 capability manifest 可从 UNAVAILABLE 变 AVAILABLE，但必须由新的 accepted baseline明确证明。

---

## 40. Unit tests

P10 deterministic unit至少：

1. spec path under root；
2. absolute external path reject；
3. traversal reject；
4. duplicate logical name reject；
5. file missing reject；
6. raw byte hash；
7. order-independent bundle identity；
8. spec mutation detected；
9. deterministic context id；
10. catalog hash participates；
11. capability manifest exact；
12. visual unavailable；
13. no silent capability fallback；
14. valid P8 raw ledger ref；
15. invalid document reject；
16. invalid fact reject；
17. invalid evidence relation reject；
18. invalid table reject；
19. invalid page reject；
20. valid P9 resolution ref；
21. corrupt P9 state blocks；
22. durable/run-local ledger distinction；
23. derived operand reference validation；
24. spec/context mismatch reject；
25. JSON CLI success/failure contract；
26. no network/AI/subprocess/import surface；
27. P8 11 tools unchanged；
28. P9 source/tests unchanged。

---

## 41. Dynamic-spec integration tests

至少两份 runtime spec：

### Spec A

要求一组明确 FFDF structured questions / output。

### Spec B

内容与 A 实质不同：

- 不同问题；
- 或不同范围；
- 或不同输出要求。

验证：

- P10 production bytes不变；
- spec bundle hash不同；
- Codex读取不同规范；
- tool selection / requested evidence发生相应变化；
- 没有固定问题编号映射。

---

## 42. Live research acceptance

至少一个完整 live run。

首选 accepted live catalog：

- CN 600519 FY2024；
- HK 00700 FY2024。

必须证明：

1. freeze runtime spec；
2. Codex完整读取 frozen spec；
3. Codex发现 P8 tools；
4. Codex读取 document/validation；
5. Codex根据实际问题选择 fact/table/evidence/page tools；
6. 若 relevant review存在，Codex正确读取/使用 P9；
7. raw与effective不混淆；
8. 输出满足当次 runtime spec；
9. evidence ledger可验证；
10. base artifacts不变。

---

## 43. P9 live integration acceptance

至少一个 isolated review-root case 验证：

- base REVIEW_REQUIRED；
- Codex只在 research need需要时进入 P9；
- task supported；
- evidence-grounded；
- optional submit；
- materialize；
- raw unchanged；
- durable resolution以后可复用。

不得写 accepted P9 acceptance review_root。

---

## 44. Capability-gap acceptance

必须至少一个 case 证明：

structured P8/P9 无法安全支持当前问题时：

- 不猜；
- 不偷偷打开 arbitrary PDF path；
- 不调用未验收 Research MCP；
- 输出 `P10_VISUAL_CAPABILITY_REQUIRED` 或对应明确 gap；
- research output明确标记未完成部分。

这用于证明未来 design/29 的必要性，而不是在 P10 v1 越权实现它。

---

## 45. Data-preparation gap acceptance

若 runtime spec 请求 catalog 中不存在 filing：

必须：

`P10_DATA_PREPARATION_REQUIRED`

不得：

- 自动下载；
- 用错误期间替代；
- 假装“没有披露”。

---

## 46. External-source acceptance boundary

如果 acceptance spec允许外部来源，可做单独 test。

必须证明：

- FFDF source 与 external source provenance分开；
- external source不写进 P9；
- P10 production不实现网络来源策略。

P10 core acceptance 可以选择 FFDF-only spec，以隔离本阶段。

---

## 47. Performance

P10 deterministic plumbing：

- freeze spec bundle <= 2s for <= 10 MiB total input；
- verify spec <= 2s；
- build context <= 2s excluding P8 artifact first-load；
- validate ledger <= 5s for <= 1000 entries。

Codex inference/tool time单独记录，不作为 deterministic package Gate。

P8/P9调用继续使用各自 accepted performance gates。

---

## 48. Environment

P10 deterministic package运行于 FFDF main runtime：

`D:\\Codex\\FinancialFilingDataFoundation\\.venv`

### 48.1 Source-layout invocation contract

P10-B 实测确认 FFDF repository 是 source checkout / `src/` layout，main runtime 当前**没有**把 `financial_filing_data_foundation` 安装进 site-packages。

因此正式 Python invocation 必须绑定 exact candidate worktree：

```powershell
$env:PYTHONPATH="<exact-candidate-worktree>\src"
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -B -m ...
```

要求：

- `PYTHONPATH` 必须指向当前 exact candidate 的 `src`，不得指向共享 main 或另一 worktree；
- Code Review / Acceptance detached worktree 必须使用各自 detached candidate 的 `src`；
- 不得为了让 `python -m` 可用而把 FFDF editable/install 到 main `.venv`；
- 不得依赖当前 PowerShell working directory 隐式发现 package；
- main runtime 继续保持无 MCP SDK；
- P8 dedicated runtime在调用 P8 server source时同样显式绑定对应 accepted/candidate `src`。

裸 main-runtime import 在未设置 `PYTHONPATH` 时失败是当前 repository layout 的预期环境事实，不代表缺少第三方 dependency。

不得为了 P10 安装 AI SDK。

若 Codex host/MCP connection需要独立 runtime，复用已验收 P8 MCP runtime，不改 lock，除非 Design-First amendment。

---

## 49. P10 provenance output

P10 acceptance evidence至少记录：

- design baseline SHA；
- production candidate SHA；
- spec file hashes；
- spec bundle hash；
- research context id；
- P8 catalog SHA；
- P8 tool names/fingerprint；
- P9 policy/review-root identity；
- exact document SHA；
- tool/action transcript summary；
- evidence ledger validation result；
- capability gaps；
- base immutability snapshot；
- final research-run verdict。

不保存 hidden chain-of-thought。

---

## 50. Run verdict

P10 integration run至少支持：

- `COMPLETE`
- `PARTIAL_WITH_EXPLICIT_GAPS`
- `BLOCKED`

`COMPLETE` 只有当前 runtime specification 的 required outputs全部有可接受 provenance时成立。

`PARTIAL_WITH_EXPLICIT_GAPS` 只有 runtime specification允许 partial output时可用。

否则 gap → `BLOCKED`。

---

## 51. No silent downgrade

以下都禁止：

- P9 corrupt → pretend no overlay；
- visual needed → ignore ambiguity；
- filing missing → substitute another period；
- spec changed → continue old context；
- external source unavailable → invent result；
- unknown unit/scope/period → silently assume；
- run-local → mark durable；
- REVIEW_REQUIRED → pretend canonical reusable。

---

## 52. P10 Issue Log

### P10-ISSUE-001 — Main runtime does not install the FFDF src-layout package

P10-B read-only audit at design baseline `acb9009d4751bbe5f8f8acec32ea7ffe30ce4c2f` observed：

- `D:\\Codex\\FinancialFilingDataFoundation\\.venv\\Scripts\\python.exe` = Python 3.14.9 ARM64；
- direct `import financial_filing_data_foundation` without source-path binding fails with `ModuleNotFoundError`；
- with `PYTHONPATH=<exact-worktree>\\src`, accepted P8 `McpCatalog/McpQueryService` and P9 public API import successfully；
- main runtime intentionally has no `mcp` SDK；
- P8 dedicated MCP runtime remains separate and valid。

Root cause：

Repository uses a source-checkout `src/` layout and does not install FFDF itself into the main virtual environment. Earlier P10 design named the runtime but did not freeze how candidate source is selected.

Risk：

Without an explicit source-path contract, Code Review / Acceptance could accidentally execute source from another worktree or tempt an unnecessary editable install into the accepted runtime.

Approved solution：

1. every P10 Python command explicitly sets `PYTHONPATH=<exact candidate worktree>\\src`；
2. review/acceptance use the detached candidate's own `src`；
3. no FFDF editable/install is added to main `.venv` merely for P10；
4. no new dependency/runtime is required；
5. P10-B must be rerun/completed after this amendment is pushed。

Affected gates：P10-B / P10-F / P10-H / P10-L / P10-N.

任何问题必须：

```text
STOP
→ facts/root cause
→ update design/24 (+ design/25/acceptance if affected)
→ commit/push amendment
→ assess invalidated evidence
→ implementation
→ rerun
```

---

## 53. Exit condition

P10 DESIGN_READY 需要：

- design/24 frozen；
- design/25 frozen；
- acceptance instruction frozen；
- design/28/29 relationship reconciled；
- design index/master/status/roadmap synchronized；
- design baseline committed/pushed。

P10 production 在该 design baseline 成为 GitHub 真源之前不得开始。

P10 DONE 需要后续：

```text
DEVELOPMENT
→ CODE REVIEW
→ ACCEPTANCE FREEZE
→ INDEPENDENT ACCEPTANCE
→ CLOSEOUT
```

P11、Research MCP production、Semantic Resolver production仍需各自后续明确授权。
