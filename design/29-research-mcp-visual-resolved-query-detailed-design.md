# 29 — FFDF Research Review MCP v3：Resolved Query、Visual Evidence 与 Controlled Review Write-Through 详细设计

> 状态：**ACTIVE DESIGN v3 — PRODUCTION IMPLEMENTATION AUTHORIZED FOR GATED EXECUTION**
>
> 当前真实基线：`main@8c6cd75`（`feat: add report-safe MCP interfaces`）
>
> 本文仅完成设计收敛，不授权 production implementation，不改变已验收 P0–P10，不修改 Raw/P3/P5/P6/P7/P9 既有语义。

---

## 0. 设计重置说明

本版 v3 是基于当前仓库真实状态重新设计，不继承任何未进入 Git 的会话性“设计完成”声明。

特别说明：

- 当前仓库不存在此前会话中提到的 `d7ec5aa3f74f3a30ab3f741546668497b008cbf7` 设计提交；
- 因此该 commit 不是任何实现或验收基线；
- 当前 design/29 仍属于旧版 future design；
- 当前实际 MCP server 已在 `main@8c6cd75` 增加 Report-Safe v1 三个工具；
- 本文将旧 design/29 与现有 14-tool MCP、P9 v1、P10 accepted contract 重新统一。

设计原则：**以当前 Git 代码为事实源，不以历史会话描述为事实源。**

---

## 1. 当前系统事实

### 1.1 P8 Raw Contract v1

P10 中冻结的 `P8_TOOL_NAMES_V1` 仍为以下 11 个工具：

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

该 11-tool 集合是 **P8 logical base contract**，必须保持冻结。

特别：

- `ffdf_get_fact` 永远返回 RawFact；
- P9 overlay 不得改变 P8 raw response；
- 不允许把 resolved/effective 值静默塞回 P8 raw contract；
- P10 当前 fingerprint 继续使用该 11-tool contract。

### 1.2 Report-Safe v1 已经进入 production

当前 `ffdf` MCP server 在原 11 个工具之外，已经增加并部署：

12. `ffdf_get_company_report_context`
13. `ffdf_search_company`
14. `ffdf_find_table_rows`

因此必须区分：

```text
P8_RAW_V1 logical contract = 11 tools
REPORT_SAFE_V1 extension    = 3 tools
current ffdf MCP surface    = 14 tools
```

这三个 Report-Safe 工具已经是当前真实 production baseline，不得在 design/29 中忽略或重新发明。

### 1.3 P9 v1

P9 当前 accepted public interface 提供：

- prepare
- tasks
- submit
- resolutions
- materialize
- report

P9 ResolutionAction 仅允许：

- `SET_PERIOD`
- `SET_UNIT`
- `SET_SCOPE`
- `CLASSIFY_TABLE_STATEMENT`
- `ATTEST_ISSUE_RESOLVED`

P9 不允许：

- SET_VALUE
- SET_METRIC
- PATCH_FACT
- 任意修改 raw numeric value
- 创建不存在的 RawFact

### 1.4 P10 accepted capability manifest

当前 P10 仍明确：

- P8 raw/query = AVAILABLE
- P9 review/resolved view = AVAILABLE
- PDF_VISUAL_EVIDENCE = UNAVAILABLE
- SEMANTIC_RESOLVER = UNAVAILABLE
- CANONICAL_METRIC_LAYER = UNAVAILABLE

因此 design/29 v3 在 Independent Acceptance 前不得声称 PDF visual 已经成为 accepted production capability。

---

## 2. 目标

v3 的目标不是重做解析器，而是在现有 P8/P9/Report-Safe 之上增加一个 **additive Research Review capability group**，解决两类需求。

### 2.1 QUALITY_REVIEW

用于入库后的数据库质量完善：

```text
已入库财报
→ 判断是否需要 review
→ 只处理未完善项
→ structured evidence first
→ 必要时视觉核验
→ 合法的 P9 resolution
→ materialize
→ 再验证 effective state
→ 后续研究复用
```

目标是：

**一次必要的人工/模型视觉复核，尽可能沉淀为可审计、可复用的 P9 reviewed state。**

### 2.2 RESEARCH_FALLBACK

用于正常公司研究过程中遇到的数据疑问：

```text
report-safe / P8 structured result
→ 数据是否足够可靠？
→ YES：直接研究
→ NO：读取 review state / context
→ structured context 不够
→ 必要才 render PDF
→ current-run judgment
```

默认原则：

**RESEARCH_FALLBACK 只读，不产生 durable mutation。**

研究生成流程不能因为“顺手发现问题”就自动写 P9。

---

## 3. 非目标

本项目明确不做：

- 重做 P3/P5/P6 parser；
- 修改 RawFact；
- 用 P9 修 raw numeric value；
- 自动 canonicalize metric；
- 引入新的 canonical metric layer；
- 自动抓取网络；
- arbitrary filesystem read；
- arbitrary SQL/SQLite query；
- arbitrary crop/bbox；
- shell/Python execution；
- 用视觉结果伪造 P5/P6 evidence；
- 把视觉判断自动提升为 parser truth；
- 建立新的 `is_complete=true/false` 持久化布尔字段；
- 解决临时公告未入库问题；
- 把 periodic filing catalog 当作完整 Corporate Event feed。

---

## 4. 总体架构：一个 FFDF MCP，实现三个 capability group

未来仍使用同一套 FFDF MCP 实现，不建立第二套互相竞争的数据接口。

```text
ffdf MCP
│
├── P8_RAW_V1                      [accepted / frozen]
│   └── 11 raw/read-only tools
│
├── REPORT_SAFE_V1                 [production]
│   └── 3 report-safe tools
│
└── RESEARCH_REVIEW_V1             [future additive]
    ├── Resolved Query
    ├── Review State
    ├── Review Context
    ├── Evidence Locator
    ├── Visual Renderer
    └── Controlled P9 Write-Through
```

关键点：

- P8 11-tool logical contract 不变；
- 当前 server 有 14 tools 不是对 P8 logical contract 的破坏；
- Future Research Review 工具继续 additive；
- 不允许为了新增 extension 修改旧工具的 raw semantics。

---

## 5. Runtime Profile 与权限隔离

同一实现支持两种运行 profile。

### 5.1 RESEARCH_FALLBACK

默认 profile，用于正常研究报告生成。

允许：

- 所有 P8 raw read
- Report-Safe read
- Review state/query
- Resolved read
- Review context
- Locator
- Visual render
- run-local reviewer decision

禁止：

- prepare overlay
- submit resolution
- materialize resolved view

写工具即使存在于 tool surface，也必须返回：

`RESEARCH_MCP_WRITE_DISABLED`

### 5.2 QUALITY_REVIEW

显式质量复核 profile。

允许：

- read/query/render
- prepare
- submit
- materialize

必须由显式 runtime 配置启用，例如：

`review_write_enabled=true`

正常研究用的 `ffdf` profile 默认保持 write-disabled。

如未来部署独立 `ffdf-review` MCP alias，也只能是**同一代码实现的 privileged runtime profile**，不能成为第二套数据架构。

---

## 5A. Research Preflight：正式研究前全期间质量监测

Research Preflight 位于 P8/P9 与正式公司研究之间，是 **Research Orchestration（研究编排）**，不是新的 Raw/Parser 层，也不直接成为 P9 durable truth。

标准位置：

```text
P8 / Report-Safe / P9
        ↓
Research Preflight
        ↓
必要的 QUALITY_REVIEW / upstream fix
        ↓
Preflight re-run
        ↓
正式公司研究
        ↓
报告生成
```

### 5A.1 目标

对用户指定的公司和研究期间执行一次“全量监测”，但这里的“全量”定义为：

- 全量扫描研究期间内的 in-scope filing/document 状态；
- 全量扫描这些 document 的 P7/P9 quality state；
- 全量检查本次研究明确要求的数据覆盖；
- 只对与当前研究相关且未完善的项目建立 repair queue。

明确不等于：

- 全量重新读取所有 PDF；
- 全量重新检查所有 RawFact；
- 所有 REVIEW_REQUIRED 都必须看图；
- 为了研究强制把整个数据库修成 PASS。

### 5A.2 三层 Preflight

#### A. Filing Coverage Scan

回答：

> 目标研究期间内，FFDF 当前 catalog / registry 覆盖了哪些正式财报？是否存在已知 filing coverage gap？

至少输出：

- market
- ticker
- requested research period
- observed filings
- latest observed filing
- per filing: fiscal_year / filing_type / document_sha256
- coverage warnings
- known missing expected slots（仅在 market-specific deterministic policy 能确认时）
- coverage_status

重要边界：

- 不得仅凭“catalog 没有”断言“公司没有发布”；
- 如果当前系统没有足够的 market filing policy 判断预期 filing，刁状态必须是 `NOT_EVALUATED` 或 `CATALOG_COVERAGE_UNCONFIRMED`；
- periodic filing coverage 不代表临时公告/event coverage。

#### B. Document Quality Scan

对研究期间每份 observed filing 调用/组合：

- base validation
- review state
- resolved state

输出每份文档的：

- COMPLETE_BASE
- COMPLETE_REVIEWED
- NEEDS_REVIEW
- NEEDS_MATERIALIZATION
- NEEDS_UPSTREAM_FIX
- BLOCKED
- INVALID_REVIEW_STATE

此步骤默认只读，不触发视觉、不写 P9。

#### C. Research Data Coverage Scan

回答：

> 即使 document 本身可用，本次研究真正需要的数据是否足够？

此步骤是 **consumer/orchestrator run-local contract**，FFDF 不从自然语言 Markdown 自动发明 canonical metric。

研究需求必须由调用方根据已冻结 ResearchSpec / 问题清单显式形成 `ResearchRequirement`，例如：

- requirement_id
- source_rule_ref
- description
- target_periods
- evidence/query strategy
- criticality

然后使用现有/未来接口检查：

- Report-Safe direct disclosure
- P8 raw fact/evidence
- resolved semantics
- company search
- table rows
- locator（必要时）

每个 requirement 输出：

- AVAILABLE
- PARTIAL
- NEEDS_REVIEW
- NEEDS_UPSTREAM_FIX
- NOT_DISCLOSED
- NOT_FOUND
- AMBIGUOUS
- NOT_APPLICABLE

Research Data Coverage 结果是 run-local research artifact，不写 Registry/P6/P9。

### 5A.3 Research Repair Queue

Preflight 必须生成最小 repair queue，不把所有非相关 Review Task 都升级为研究阻断。

每项至少包含：

- document_sha256
- requirement_id（如适用）
- review_task_id（如适用）
- reason
- disposition

disposition 允许：

- `QUALITY_REVIEW`
- `UPSTREAM_FIX`
- `RESEARCH_GAP`
- `NOT_DISCLOSED`
- `CATALOG_GAP`
- `NO_ACTION`

标准路由：

```text
NEEDS_REVIEW + research-relevant + SUPPORTED
→ QUALITY_REVIEW

RAW_EXTRACTION_DEFECT / P6_MISSING_FACT_CANDIDATE / unsupported
→ UPSTREAM_FIX

财报明确未披露
→ NOT_DISCLOSED

catalog 未覆盖但无法证明公司未发布
→ CATALOG_GAP

与当前研究无关的 non-blocking review
→ NO_ACTION
```

### 5A.4 Research Ready 与 Database Complete 分离

严禁使用“所有 Review Task 必须解决”作为正式研究的唯一门槛。

定义：

#### `period_monitoring_complete`

表示目标研究期间内的 observed filings 已完成 Preflight 状态检查。

#### `research_ready`

只有当本次研究的 **critical requirements**：

- 已可可靠使用；或
- 已明确 NOT_DISCLOSED / NOT_APPLICABLE 且研究规则允许保留缺口；且
- 不存在会使核心研究结论失真的 unresolved blocker

时为 true。

因此允许：

```text
document = REVIEW_REQUIRED
但 remaining issue 与本次研究无关
且所有 critical requirements 可用
→ research_ready = true
```

#### `database_fully_reviewed`

可以作为 run summary 统计概念，但不得新增持久化 `is_complete` 字段，也不得与 `research_ready` 混淆。

### 5A.5 ResearchPreflightResult

建议 run-local schema：

```json
{
  "company": {"market": "CN", "ticker": "605117"},
  "research_period": {"from": 2021, "to": 2026},
  "filing_coverage": {
    "observed_document_count": 23,
    "latest_filing": "2026Q3",
    "coverage_status": "OBSERVED"
  },
  "quality_summary": {
    "complete_base": 17,
    "complete_reviewed": 4,
    "needs_review": 2,
    "needs_upstream_fix": 0,
    "blocked": 0
  },
  "research_coverage": {
    "critical_requirement_count": 40,
    "available": 37,
    "partial": 2,
    "not_disclosed": 1,
    "blocking": 0
  },
  "repair_queue": [],
  "period_monitoring_complete": true,
  "research_ready": true
}
```

该对象：

- 可被 Codex/Sol 用于决定是否开始正式分析；
- 不进入 Registry；
- 不改变 P7/P9；
- 不成为 canonical financial truth；
- 需要保留 ResearchSpec bundle hash / requirement-set fingerprint 以保证本次 preflight 可追溯。

### 5A.6 Preflight 执行策略

标准算法：

```text
1. 获取 company filing context
2. 枚举目标期间 observed filings
3. 对每份 filing 获取 quality state
4. 跳过 COMPLETE_BASE / COMPLETE_REVIEWED 的非必要复核
5. 根据本次 ResearchRequirementSet 检查数据覆盖
6. 建立最小 repair queue
7. 仅处理 research-relevant QUALITY_REVIEW 项
8. 如发现 upstream defect，路由 Parser/P6 修复
9. 完成必要修复后重新运行 Preflight
10. research_ready == true 后进入正式研究
```

### 5A.7 Token / Visual 原则

Research Preflight 本身不得触发“全量视觉审核”。

正确原则：

```text
全量状态扫描
→ 最小 repair queue
→ structured context first
→ target-related unresolved only
→ 必要时 visual
```

必须统计：

- observed_document_count
- reviewed_document_count
- skipped_complete_document_count
- repair_queue_count
- visual_required_count
- visual_call_count
- research_blocker_count

### 5A.8 与 P10 ResearchSpec 的关系

当前 P10 `ResearchSpecBundle` 只冻结研究规则文件的路径、大小、SHA256，不解析 Markdown 语义。

因此 v3 不引入自动“问题清单 → canonical metric”转换。

ResearchRequirementSet 由上层研究编排显式生成，并记录：

- `spec_bundle_hash`
- `requirement_set_hash`

未来如果要自动从规则文件生成 canonical requirements，属于单独的 Semantic Resolver / Research Planning 设计，不得夹带在本项目中。

### 5A.9 Preflight 不是新的 MCP truth layer

本阶段不新增 `ffdf_run_research_preflight` 这类万能 MCP 工具。

原因：

- Preflight 是对多个既有/未来 MCP 调用的研究编排；
- requirement semantics 来自上层研究任务，而不是 FFDF parser truth；
- 先保持各底层工具职责单一、可测试；
- 等 v3 各能力验收后，如确有必要，再单独设计一个只读 orchestration convenience tool。

---

## 6. Future RESEARCH_REVIEW_V1 Tool Surface

计划新增 12 个 additive tools。

### 6.1 Read / Query

1. `ffdf_get_review_state`
2. `ffdf_get_resolved_fact`
3. `ffdf_list_resolved_facts`
4. `ffdf_list_review_tasks`
5. `ffdf_get_review_context`
6. `ffdf_locate_evidence`
7. `ffdf_render_table`
8. `ffdf_render_table_group`
9. `ffdf_render_page`

### 6.2 Explicit Write-Through

10. `ffdf_prepare_review_overlay`
11. `ffdf_submit_review_resolution`
12. `ffdf_materialize_resolved_view`

所有 read/render tools 必须无 durable side effect。

三个 write tools 必须显式调用。

禁止：

```text
get_review_state
→ 自动 prepare
→ 自动 submit
→ 自动 materialize
```

---

## 7. Quality State：动态推导，不新增数据库布尔字段

状态必须由 P7 + P9 当前事实动态推导。

定义：

### COMPLETE_BASE

满足：

- base validation_status == PASS
- base reuse_eligible == true
- 不依赖 unresolved P9 correction

含义：

基础 deterministic pipeline 已足够复用。

### COMPLETE_REVIEWED

满足：

- valid materialized resolved view
- resolved_validation_status == PASS
- resolved_reuse_eligible == true
- unresolved_review_issue_count == 0
- unsupported_review_issue_count == 0

含义：

经过 P9 review 后已达到可复用状态。

### NEEDS_REVIEW

例如：

- base == REVIEW_REQUIRED；
- 存在 unresolved + SUPPORTED task；
- 尚未完成必要 resolution。

### NEEDS_MATERIALIZATION

存在新的 active resolution，但当前 materialized snapshot 的 overlay hash 与 active set 不一致。

read tool 不得自动 materialize。

### NEEDS_UPSTREAM_FIX

例如：

- unsupported review issue；
- RAW_EXTRACTION_DEFECT；
- P6_MISSING_FACT_CANDIDATE；
- 当前 P9 schema 无合法 target。

### BLOCKED

例如：

- base validation == BLOCKED / FAIL；
- blocking issue 使当前文档不可安全复用；
- trusted source 无法验证且当前请求依赖视觉。

### INVALID_REVIEW_STATE

例如：

- P9 store corrupt；
- supersession graph invalid；
- snapshot/hash 不一致且无法解释；
- review base 与当前 P7 base hash 不兼容。

---

## 8. ffdf_get_review_state

输入：

- `document_sha256`

输出至少包括：

- document identity
- base_validation_status
- base_reuse_eligible
- base_review_issue_count
- base_blocking_issue_count
- has_review_overlay
- active_resolution_count
- active_resolution_ids
- active_overlay_set_hash
- snapshot_available
- snapshot_overlay_set_hash
- resolved_validation_status
- resolved_reuse_eligible
- resolved_review_issue_count
- unresolved_review_issue_count
- unsupported_review_issue_count
- quality_state
- write_profile
- visual_capability

不得：

- 自动 prepare；
- 自动 materialize；
- 静默回退损坏的 P9 store。

P9 corrupt 必须 fail closed。

---

## 9. Resolved Query 语义

### 9.1 Raw 与 Effective 分离

`ffdf_get_resolved_fact` 必须同时返回：

```json
{
  "raw": {
    "raw_fact_id": "...",
    "metric_name": "...",
    "value": "...",
    "period": null,
    "unit": null,
    "scope": null
  },
  "effective": {
    "value": "...",
    "period": "2026Q3",
    "unit": "CNY",
    "scope": "CONSOLIDATED"
  },
  "review": {
    "applied": true,
    "resolution_ids": ["..."],
    "overlay_set_hash": "..."
  }
}
```

强制规则：

- `effective.value` 不得由 P9 修改；
- raw numeric value 仍来自 P6；
- P9 只修改其 accepted semantic fields；
- metric_name 不 canonicalize；
- raw block 必须保持原样可追溯。

### 9.2 Research Resolved-First

研究层的语义选择规则：

```text
durable resolved field exists
→ use effective semantic field

no durable resolution
→ use base/raw field

raw field unresolved and required
→ review / fallback
```

但 “resolved-first” 只适用于**P9允许覆盖的语义字段**。

不得把 resolved-first 理解为：

“用模型结果覆盖 raw value”。

---

## 10. Report-Safe v1 与 Resolved Query 的关系

现有三个 Report-Safe v1 工具保持行为兼容，不在本阶段静默改变 response semantics。

### ffdf_get_company_report_context

继续负责：

- company filing coverage
- chronology
- base validation summary
- report guardrails

它不是 P9 resolved-state 的唯一权威入口。

### ffdf_search_company

继续负责：

- company-wide periodic filing search
- newest filing first
- neighboring page context
- stale-state risk reduction

不负责自动应用 P9 semantic overlay。

### ffdf_find_table_rows

继续返回 P5 direct disclosure rows。

关键：

- 数值仍来自 P5 direct disclosure；
- 不得因为 P9 出现而修改原始 row cells；
- 如 unit/period/scope/classification 存在 P9 resolution，研究调用方必须通过 Review/Resolved Query 取得 effective semantics。

未来如果需要 “Report-Safe v2 Effective Adapter”，必须单独设计版本，不得静默改变 v1。

---

## 11. Review Task 选择原则

QUALITY_REVIEW 不扫描整份财报。

标准路径：

```text
company + target periods
→ list documents
→ get review state
→ COMPLETE_* : skip
→ NEEDS_REVIEW : prepare if necessary
→ list unresolved tasks
→ only SUPPORTED tasks
```

默认只处理：

- unresolved
- SUPPORTED
- 与目标 document 绑定
- 当前 base hash 匹配

UNSUPPORTED task 不得强行 submit。

---

## 12. Review Context

`ffdf_get_review_context` 输入可按：

- review_task_id
- raw_fact_id
- issue_id
- table_id

返回最小充分上下文：

- review task
- reason_code
- supported_actions
- required_evidence_types
- base validation summary
- target raw fact
- same-table relevant P5 cells
- P6 evidence
- related issues
- current active resolutions
- effective semantic state
- relevant P3 page text
- recommended visual targets

不得返回：

- arbitrary filesystem path
- AI reasoning
- guessed semantic mapping
- invented evidence

---

## 13. Structured-First Visual Trigger Matrix

视觉不是默认动作。

### VISUAL_NOT_REQUIRED

满足：

- target required semantics 已明确；
- existing structured evidence 一致；
- 无 target-related unresolved issue；
- 无相关 evidence conflict；
- 已存在 durable resolution 且 quality state 可复用。

### VISUAL_REQUIRED

仅在当前任务需要且 structured evidence 无法安全判断时触发，例如：

- period/unit/scope/header role 冲突；
- row/column relationship 不清；
- P5 crop/header relationship 有疑问；
- cross-page table context 必需；
- P6 fact 与 P5/P3 evidence 冲突；
- requested fact missing，需要定位 PDF 中是否实际披露；
- current task 明确依赖原始版式；
- parser defect suspicion。

重要：

**document == REVIEW_REQUIRED 本身不能自动触发视觉。**

必须是 target-related。

---

## 14. Missing-Fact Locator

`ffdf_locate_evidence` 只使用 trusted structured artifacts：

```text
P3 FTS / literal search
→ section
→ page
→ intersecting P5 tables
→ P6 facts where available
→ recommended visual target
```

它不是 canonical metric mapper。

禁止：

- arbitrary synonym explosion；
- 创建不存在的 RawFact；
- 把 locator hit 当作 fact truth；
- 自动写 P9。

若 PDF 中明确有值但 P6 没 RawFact：

标记：

`P6_MISSING_FACT_CANDIDATE`

进入 upstream extraction review。

---

## 15. Trusted PDF Source Resolver

调用者永远不能传 filesystem path。

唯一 caller identity：

- `document_sha256`

内部 resolver 必须：

1. 从 Registry 读取 document binding/location；
2. 选择 live registered source；
3. 优先并强制位于配置的 trusted raw-store root；
4. 校验文件存在；
5. 重新计算 SHA256；
6. 校验 file_size；
7. PDF 可打开；
8. page_count 与 Registry/P3 一致；
9. document identity 与当前 catalog document 一致。

当前 live ingest 已使用类似：

`workspace/ingest/raw-store/sha256/<prefix>/<sha>.pdf`

P3 `document.json.source_path` 只能作为交叉校验信息，不能成为 caller-controlled source。

如果只有未受信任或漂移路径：

`RESEARCH_MCP_VISUAL_SOURCE_UNTRUSTED`

fail closed。

---

## 16. Visual Renderer

视觉来源固定：

```text
immutable original PDF
→ PyMuPDF
→ deterministic render
→ MCP ImageContent
```

禁止：

```text
P3 text
→ re-layout
→ fake screenshot
```

### ffdf_render_page

参数：

- document_sha256
- page_no
- detail = NORMAL | HIGH_DETAIL

### ffdf_render_table

参数：

- document_sha256
- table_id
- mode
- detail

mode：

- TABLE_ONLY
- TABLE_WITH_HEADER
- TABLE_WITH_SURROUNDING_CONTEXT

默认：

- TABLE_WITH_HEADER

### ffdf_render_table_group

仅允许使用 P5 已存在的 table_group_id。

不得模型猜测 table group。

---

## 17. Crop / Detail / Tile Policy

调用者不能传任意 bbox。

clip 只能由 trusted P5 geometry + deterministic margin 计算。

升级顺序固定：

```text
structured
→ table NORMAL
→ table HIGH_DETAIL
→ table_group
→ page NORMAL
→ page HIGH_DETAIL
→ deterministic tile
```

不得：

- 默认整页高分辨率；
- 扫描整份 PDF；
- 无限前后翻页；
- 每个 fact 单独重复 render。

同一：

`document_sha256 + page_no/table_id + render_profile`

在同一 run 内必须 dedupe。

---

## 18. VisualRef

VisualRef 是 run evidence identity，不是 P9 v1 evidence type。

```text
visual_ref_id =
SHA256(
  document_sha256
  + page_no
  + normalized clip
  + render profile
  + tile identity
  + renderer version
)
```

另记录：

- render_sha256
- renderer_version
- page_no
- table_id/group_id
- clip
- detail
- tile identity

默认不把 PNG 落盘。

---

## 19. Visual Decision Classes

视觉后只能形成以下四类。

### EXPLICIT_AND_ANCHORABLE

PDF 视觉明确，并且存在合法 P5/P6 authoritative anchor。

允许：

- current-run use；
- 在 QUALITY_REVIEW profile 中，若现有 P9 contract 可表示该 semantic correction，则可 durable submit。

重要：

VisualRef 本身不是 P9 v1 evidence。

P9 durable submit 仍必须使用 P9 当前接受的：

- P5_CELL
- P6_EVIDENCE
- 以及 ATTEST 的合法 supporting resolutions

### EXPLICIT_VISUAL_ONLY

PDF 明确，但不存在合法 P5/P6 anchor。

允许：

- current-run verified use；
- 记录 run-local VisualRef。

禁止：

- durable P9 submit；
- canonical reuse。

### RAW_EXTRACTION_DEFECT

PDF 证明 P5/P6 raw extraction 错误，例如：

- 漏位；
- 小数点错误；
- OCR 数字错误；
- 错列；
- 数值绑定错误。

必须：

```text
STOP P9
→ parser defect
→ Design-First upstream fix
→ rerun affected stages
```

### AMBIGUOUS

视觉仍不能唯一判断。

保持：

- unresolved
- REVIEW_REQUIRED

禁止猜测。

---

## 20. P9 v1 Evidence Boundary

当前 P9 direct evidence 只接受既有 trusted evidence 类型，例如：

- `P6_EVIDENCE`
- `P5_CELL`

因此 v3 不新增 `PDF_VISUAL_EVIDENCE` 到 P9 schema。

理由：

- 不破坏 accepted P9 v1；
- 不需要为了视觉能力修改 durable semantic truth format；
- 视觉仅作为 reviewer 辅助证据；
- durable correction 必须仍有现有合法 anchor。

如果未来确实需要把 VisualRef 持久化为 P9 evidence：

必须单独进行 **P9 Design Amendment v2**，不能夹带在 Research Review MCP 实现中。

---

## 21. ATTEST_ISSUE_RESOLVED 限制

`ATTEST_ISSUE_RESOLVED` 不能成为万能逃生口。

只有同时满足以下条件才允许通过 Research MCP wrapper 提交：

- task.reviewability == SUPPORTED；
- task.supported_actions 包含 ATTEST；
- supporting_resolution_ids 非空；
- supporting resolutions 全部 active；
- 全部属于同一个 task / issue；
- supporting resolution 不是另一个 ATTEST；
- expected_observed_count 精确匹配；
- inherited evidence 非空；
- reason_code 不属于 upstream defect / unsupported class。

以下禁止 ATTEST：

- RAW_EXTRACTION_DEFECT
- P6_MISSING_FACT_CANDIDATE
- unsupported issue
- visual-only without anchor
- corrupt artifact
- missing trusted source
- unresolved ambiguity

---

## 22. Controlled P9 Write-Through

写工具只在 QUALITY_REVIEW profile 可用。

### ffdf_prepare_review_overlay

要求：

- explicit document_sha256；
- idempotent；
- 不覆盖已有有效 overlay；
- base P7 hash 必须匹配当前 document。

### ffdf_submit_review_resolution

wrapper 必须在调用现有 P9 public API 前重新检查：

- review_task_id
- expected_base_validation_report_sha256
- expected_overlay_set_hash_before
- current active resolution set
- task still unresolved
- task still SUPPORTED
- action in task.supported_actions
- evidence contract valid

如果状态已经变化：

`RESEARCH_MCP_REVIEW_STATE_CHANGED`

不得继续写。

### ffdf_materialize_resolved_view

必须显式调用。

submit 成功只代表：

“resolution immutable artifact 已写入”

不代表：

“document 已完善”。

最终必须：

```text
submit
→ materialize
→ get_review_state
```

只有 quality_state == COMPLETE_REVIEWED 才表示复核后可复用。

---

## 23. Research Fallback 不自动写库

正常报告生成中：

```text
structured result
→ resolved state if available
→ visual fallback if needed
→ run-local judgment
```

即使判断非常明确，也不得自动调用：

- prepare
- submit
- materialize

研究任务可输出：

- review candidate
- parser defect candidate
- missing fact candidate

然后由单独 QUALITY_REVIEW 任务处理。

这样保持：

**研究职责与数据治理职责分离。**

---

## 24. Run-Local Verified

对于 `EXPLICIT_VISUAL_ONLY`：

```json
{
  "decision_class": "EXPLICIT_VISUAL_ONLY",
  "document_sha256": "...",
  "page_no": 10,
  "visual_ref_ids": ["..."],
  "usability": "RUN_LOCAL_VERIFIED",
  "durable": false,
  "canonical_reuse_eligible": false
}
```

run-local decision：

- 可用于当前报告中的事实判断；
- 必须保留 provenance；
- 不进入 Registry；
- 不进入 P6；
- 不进入 P9 v1；
- 下一次研究不能自动视为已复核。

---

## 25. Derived-Use Gate

视觉确认不等于任何派生计算都可用。

如用于 YoY / margin / QoQ / TTM 等，必须逐项检查：

- numeric value
- period
- value role
- unit/dimension
- scope
- no unresolved conflict
- provenance

### YoY

必须：

- same semantic metric
- compatible comparative period
- compatible scope
- compatible dimension/currency/scale
- value role = VALUE

### Margin

必须：

- numerator/denominator same period
- compatible scope
- compatible monetary basis

### QoQ

禁止：

- YTD 与 standalone quarter 直接做 QoQ

### TTM

必须证明 duration decomposition 兼容。

---

## 26. 与最新报告生成流程的推荐关系

正常公司研究建议：

```text
ffdf_get_company_report_context
→ ffdf_search_company
→ ffdf_find_table_rows
→ per-document ffdf_get_review_state
→ durable resolved exists? use resolved semantics
→ structured ambiguity? ffdf_get_review_context
→ visual only if required
→ report generation
```

P8 raw tools继续用于：

- evidence tracing
- raw audit
- parser diagnosis

而不是让研究层静默把 raw 当 effective。

---

## 27. Event Coverage Boundary

design/29 v3 只解决：

**已入库正式文档的结构化数据/语义疑问与视觉复核。**

它不解决：

- 临时公告未入库；
- 权益分派实施公告缺失；
- 股东大会决议公告缺失；
- 回购进展公告缺失；
- 重大合同公告缺失；
- 其他 Corporate Event feed 缺失。

因此：

`latest periodic filing != latest real-world event state`

未来如需解决，另立：

**CorporateEvent / DisclosureEvent ingestion design**

不得把 event ingestion 偷渡进 Research Review MCP。

---

## 28. Security

禁止工具：

- read_file(path)
- render_file(path)
- list_directory
- sqlite_query
- shell
- execute_python
- arbitrary crop
- arbitrary raw-store path

caller 只能使用 domain identity：

- document_sha256
- raw_fact_id
- review_task_id
- issue_id
- table_id
- table_group_id
- page_no
- locator query

所有 filesystem resolution 在 trusted internal resolver 内完成。

---

## 29. Determinism

在固定：

- PDF bytes
- P3/P5/P6/P7 artifacts
- P9 state
- renderer runtime
- render profile

条件下必须保证：

- same ReviewState
- same ResolvedFact
- same locator ordering
- same VisualRef
- same render SHA
- same recommended visual target ordering

模型 reviewer interpretation 不属于 deterministic artifact equality。

---

## 30. Renderer Freeze

Independent Acceptance 前必须冻结：

- Python exact runtime
- PyMuPDF exact version
- image format
- DPI
- alpha/color policy
- table margin policy
- HIGH_DETAIL profile
- tiling algorithm
- overlap
- tile ordering
- renderer_version

renderer 行为变化必须提升 renderer_version。

---

## 31. Telemetry

至少统计：

- review_state_call_count
- visual_call_count
- rendered_unique_page_count
- rendered_unique_table_count
- structured_sufficient_count
- visual_required_count
- EXPLICIT_AND_ANCHORABLE count
- EXPLICIT_VISUAL_ONLY count
- RAW_EXTRACTION_DEFECT count
- AMBIGUOUS count
- durable_resolution_submit_count
- repeated_visual_avoided_count

这些用于成本优化和设计反馈，不作为 correctness truth。

模型名称/token 只进入 run telemetry，不进入 P9 semantic truth。

---

## 32. Reviewer Identity

FFDF correctness contract 不绑定 Luna。

角色：

```text
orchestrator = Codex / caller
visual reviewer = runtime-selected model or human
```

当前可以默认使用 Luna 做高吞吐视觉复核，但：

- 不新增 `ReviewerType.LUNA`；
- durable P9 reviewer_type 继续使用已有 enum；
- 如由 Codex 承载模型复核流程，可使用明确 reviewer_id，例如 `codex/luna-review`；
- 模型版本单独记录 telemetry。

---

## 33. Internal Service Boundary

未来 extension 不应继续扩大对 private `McpQueryService._bundle` 的依赖。

当前 Report-Safe v1 已使用 `service._bundle`，这是已知技术债。

在 Research Review implementation 前应提供最小 public/internal service accessor，例如：

- trusted document bundle read
- P5 table iteration
- P6 fact/evidence indexes

要求：

- 不暴露 arbitrary paths；
- 不改变 public MCP contract；
- 不复制 artifact loading logic；
- Report-Safe 和 Research Review 共享同一受控 service layer。

---

## 34. Error Codes

至少定义：

- `RESEARCH_MCP_WRITE_DISABLED`
- `RESEARCH_MCP_DOCUMENT_NOT_FOUND`
- `RESEARCH_MCP_FACT_NOT_FOUND`
- `RESEARCH_MCP_REVIEW_TASK_NOT_FOUND`
- `RESEARCH_MCP_ISSUE_NOT_FOUND`
- `RESEARCH_MCP_TABLE_NOT_FOUND`
- `RESEARCH_MCP_TABLE_GROUP_NOT_FOUND`
- `RESEARCH_MCP_PAGE_INVALID`
- `RESEARCH_MCP_VISUAL_SOURCE_UNTRUSTED`
- `RESEARCH_MCP_VISUAL_SOURCE_INVALID`
- `RESEARCH_MCP_RENDER_FAILED`
- `RESEARCH_MCP_PAYLOAD_LIMIT`
- `RESEARCH_MCP_REVIEW_STATE_CHANGED`
- `RESEARCH_MCP_REVIEW_STATE_INVALID`
- `RESEARCH_MCP_RESOLVED_STORE_INVALID`
- `RESEARCH_MCP_LOCATOR_NO_MATCH`
- `RESEARCH_MCP_UPSTREAM_FIX_REQUIRED`

禁止直接向 client 暴露 Python traceback。

---

## 35. Golden Cases

### 35.1 002371 2026Q3

保留现有 live evidence 作为 period/value-role golden。

必须正确区分：

- current-quarter VALUE
- current-quarter YOY_PERCENT
- YTD VALUE
- YTD YOY_PERCENT

视觉只在 structured evidence 不能唯一判断时触发。

### 35.2 605117 Research Preflight + Report-Safe Integration

先对 2021–2026 in-scope filings 执行 Research Preflight，至少验证：

- observed filing list 稳定、可追溯；
- COMPLETE_BASE / COMPLETE_REVIEWED / NEEDS_REVIEW 分类正确；
- 非研究相关的 REVIEW_REQUIRED 不应自动阻断 research_ready；
- 只对 research-relevant unresolved task 建 repair queue；
- Preflight 本身不自动 render、不自动写 P9；
- 修复必要问题后 re-run Preflight，research_ready 能从 false/conditional 正确转为 true；
- ResearchPreflightResult 记录 spec_bundle_hash / requirement_set_hash。

随后继续验证 Report-Safe：

- 2025FY `新能源行业` direct row 可直接获取；
- `外销` disclosure label 不被扩写成“海外收入”；
- 2025FY KAM 跨 p105/p106 能读取完整上下文；
- newer periodic filing state 可覆盖 older filing state；
- 若临时公告未入库，系统不得声称已知最新现实事件状态；
- Report-Safe v1 行为不得因 Research Review extension 改变。

### 35.3 Existing P9 Reuse

证明：

```text
REVIEW_REQUIRED
→ supported resolution
→ materialize
→ COMPLETE_REVIEWED
→ next run uses durable resolved
→ no repeated visual by default
```

### 35.4 其他必须 Golden

- cross-page table
- dense table
- missing fact
- raw extraction defect
- visual-only no anchor
- ambiguous
- unsupported task
- same-page multi-task visual dedupe
- corrupt P9
- stale snapshot / active overlay mismatch
- source SHA drift
- write disabled in RESEARCH_FALLBACK

---

## 36. Implementation Gates

### R-A0 — Current Main Reconciliation

本 v3 已完成的设计输入：

- main@8c6cd75
- P8 11-tool frozen logical contract
- current 14-tool server
- Report-Safe v1 production
- P9 v1 accepted API/schema
- P10 PDF visual unavailable

R-A0 的正式产物就是本 design/29 v3。

### R-A1 — Contract Freeze

冻结：

- 三 capability group
- 12 future tool names
- runtime profile
- quality-state enum
- error codes
- P8/P9 non-regression rules

### R-A2 — Research Preflight Contract

冻结：

- Filing Coverage / Document Quality / Research Data Coverage 三层模型
- ResearchRequirementSet run-local 输入边界
- ResearchPreflightResult schema
- Research Repair Queue disposition
- research_ready 判定
- period_monitoring_complete 判定
- Preflight 不自动写 P9 / 不自动看图
- Preflight 与 P10 ResearchSpecBundle 的 fingerprint 关系

R-A2 不实现 Semantic Resolver，不创建 canonical metric layer。

### R-B — Trusted Source Resolver

实现：

- Registry → trusted raw-store path
- SHA/file_size/page_count verification
- caller path prohibition

### R-C — Review State + Resolved Query

实现：

- get_review_state
- get_resolved_fact
- list_resolved_facts
- quality state machine

不实现 visual。

### R-D — Review Tasks + Context

实现：

- list_review_tasks
- get_review_context
- shared service accessor

### R-E — Controlled P9 Write-Through

实现：

- prepare
- submit
- materialize
- mode gate
- optimistic state verification
- ATTEST restrictions

此阶段仍不需要 visual。

### R-F — Locator

实现：

- locate_evidence
- no fabricated fact

### R-G — Visual Trigger Policy

实现 deterministic target-related trigger evaluator。

### R-H — Renderer

实现：

- page
- table
- group
- high detail
- tiling
- VisualRef

### R-I — Run-Local Decision Policy

实现：

- four visual decision classes
- derived-use gate
- no durable write in research mode

### R-J — 002371 Golden

### R-K — 605117 Report-Safe Integration Golden

### R-L — Existing P9 Reuse Golden

### R-M — Diverse CN/HK + Security + Corruption Golden

### R-N — Formal Code Review

### R-O — Acceptance Freeze

冻结 runtime / renderer / fixtures / candidate commit。

### R-P — Independent Acceptance

只有 R-P PASS 后，才允许讨论 production enablement。

### R-Q — P10 Capability Reconciliation

Independent Acceptance PASS 后另行更新 P10 capability manifest：

`PDF_VISUAL_EVIDENCE: UNAVAILABLE → AVAILABLE`

该更新不得提前进入 R-B–R-P。

---

## 37. Non-Regression Requirements

实现全过程必须保证：

1. P8 11-tool logical contract fingerprint 不变；
2. `ffdf_get_fact` raw contract 不变；
3. Report-Safe v1 三工具原有字段和行为不被静默改变；
4. P9 v1 schema/version 不变；
5. P9 ResolutionAction 不扩展；
6. Raw/P3/P5/P6/P7/Registry source artifacts 不被 render/read 工具修改；
7. 默认 research profile 无 durable write；
8. run-local visual decision 不进入 canonical reuse；
9. corrupt P9 不 silent fallback raw；
10. source SHA drift fail closed；
11. temporary-announcement coverage limitation继续明确存在。

---

## 38. Testing Requirements

每个 gate 至少执行：

- focused unit tests
- compile/import
- contract tests
- security/path tests
- immutability tests
- deterministic repeat tests

涉及 write-through：

- stale-state tests
- supersession tests
- P9 store integrity tests
- concurrent/optimistic state tests

涉及 render：

- trusted source only
- SHA mismatch
- page bounds
- deterministic crop
- header context
- cross-page group
- high detail
- tiling
- VisualRef stable
- render SHA stable under frozen runtime
- no screenshot persistence

最终：

- full unit suite
- integration
- golden
- independent acceptance

所有结果记录 PASS / FAIL / SKIP。

---

## 39. Design Issue Rule

实现过程中发现设计与真实代码冲突：

```text
STOP
→ establish facts
→ root cause
→ update design/29
→ design-only commit
→ assess invalidated gates
→ resume implementation
```

禁止 code-first / design-later。

---

## 40. Production Authorization Boundary

本文完成后状态仍是：

**DESIGN COMPLETE / PRODUCTION IMPLEMENTATION NOT AUTHORIZED**

本设计已于 2026-11-05 获得用户明确授权，允许按 gate 顺序推进 production implementation；任何 gate 仍必须独立通过其设计、测试和证据要求。

不得使用：

- 旧 design/29；
- 不存在的 d7ec5aa 会话性 commit；
- 旧“P8 永远只有11个 server tools”的错误假设；
- “P9 MCP”这一不准确表述；
- “视觉结果可直接写入 P9 evidence”的错误假设。

Production implementation 从 R-A1 开始，并严格按 R-A1 → R-A2 → R-B ... 的 gate 顺序推进。
