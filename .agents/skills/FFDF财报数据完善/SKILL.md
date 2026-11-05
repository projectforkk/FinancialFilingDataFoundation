---
name: FFDF财报数据完善
description: "在正式公司财报分析前，使用 FFDF MCP 对指定公司和年度区间执行 Research Preflight；只把真正需要模型判断的疑难项交给 Luna 5.6 Max，并按 P9 / upstream-fix 边界处理。"
---

# FFDF Research Preflight

## Purpose

在正式公司基本面、财务、估值或投资分析开始前，对目标公司的整个研究期间执行一次 Research Preflight。

本 Skill 只负责：

- 研究期间正式财报覆盖监测；
- P7 / P9 / Resolved quality state 监测；
- 本次研究数据覆盖检查；
- Research Repair Queue；
- 必要的 Luna 5.6 Max 语义 / PDF 视觉复核；
- 合法 P9 write-through 或 upstream-fix 路由；
- 输出 research readiness。

本 Skill 不负责：

- 下载新财报；
- 修改 Raw PDF；
- 修改 P3/P5/P6/P7 原始 artifact；
- Canonical Metric Layer；
- Semantic Resolver；
- CorporateEvent / DisclosureEvent 全量公告采集；
- 最终投资报告写作。

## Invocation and parameters

调用格式：

`$FFDF财报数据完善 <company> <year_range> <model>`

示例：

`$FFDF财报数据完善 605117 2021-2026 luna5.6-max`

`$FFDF财报数据完善 "德业股份" 2021-2026 luna5.6-max`

必须解析为且仅解析为三个逻辑参数：

### 1. company

必填。

允许：

- 股票代码 / ticker；
- 公司名称。

如果公司名称或代码不能唯一解析，停止并返回：

`PREFLIGHT_INPUT_INVALID: COMPANY_NOT_UNIQUE`

不得自动选择多个候选中的一个。

### 2. year_range

必填。

格式必须是：

`YYYY-YYYY`

首尾年度均包含。

必须满足：

- 起始年度 <= 结束年度；
- 不得自动扩大年度区间；
- 不得默认补成最近五年。

非法时返回：

`PREFLIGHT_INPUT_INVALID: YEAR_RANGE_INVALID`

### 3. model

必填。

当前唯一允许的 canonical value：

`luna5.6-max`

可以把大小写或展示形式规范化后比较，但最终 canonical value 必须严格为：

`luna5.6-max`

不允许：

- Luna 5.6 非 Max；
- 其他 Luna；
- Sol；
- Astra；
- 其他 Codex 模型；
- 外部 OpenAI API；
- 其他远程 AI API；
- 自动 fallback；
- 自动降级。

如果无法确认当前模型调用会使用 Luna 5.6 Max：

`MODEL_BLOCKED: LUNA_5_6_MAX_REQUIRED`

此时停止所有需要模型判断的步骤，但可以继续完成不依赖模型的确定性 Preflight，并明确列出未完成的 Repair Queue。

## Mandatory research rules

Research Data Coverage 不增加第四个参数。

每次运行必须从磁盘重新读取：

- `D:\Codex\公司概述\00_Prompt\公司分析的约束.md`
- `D:\Codex\公司概述\00_Prompt\问题清单.md`

这两个文件是本次 ResearchRequirementSet 的上层规则来源。

不得：

- 使用缓存版本替代；
- 从历史报告反推问题；
- 自行添加 canonical metric；
- 因某指标“常见”就自动加入必需项。

如果任一规则文件不可读：

- Filing Coverage Scan 和 Document Quality Scan 可以继续；
- Research Data Coverage 必须标记 `NOT_EVALUATED`；
- `research_ready` 不得宣称为 true；
- 输出明确 blocker。

## Architecture roles

固定职责：

`Codex = 总调度器`

`FFDF MCP = 数据与 deterministic tool layer`

`Luna 5.6 Max = 少量疑难语义 / PDF 视觉审查器`

`P9 = 合法语义修正持久化层`

禁止把所有 FFDF MCP 查询先交给 Luna。

正确路径：

`Codex -> FFDF MCP -> 筛选异常 -> Luna 5.6 Max（必要时）`

错误路径：

`Codex -> Luna -> Luna 全量读取全部财报 -> MCP`

## Required workflow

### Step 1 — Validate inputs

确认：

- company 非空且可唯一解析；
- year_range 合法；
- model == `luna5.6-max`。

记录规范化后的三个参数。

### Step 2 — Filing Coverage Scan

优先直接调用 FFDF MCP：

- `ffdf_get_company_report_context`
- `ffdf_list_documents`

枚举 year_range 内 observed formal filings。

至少记录：

- market；
- ticker；
- company；
- fiscal_year；
- filing_type；
- document_sha256；
- latest observed filing；
- observed document count。

重要边界：

`catalog missing != company did not publish`

如果 FFDF 当前没有足够 deterministic policy 证明某个理论 filing 缺失，使用：

`CATALOG_COVERAGE_UNCONFIRMED`

不得自行写“未发布”。

周期财报 coverage 不等于临时公告 / event coverage。

### Step 3 — Document Quality Scan

对每份 observed filing 调用：

`ffdf_get_review_state`

按以下状态分类：

- `COMPLETE_BASE`
- `COMPLETE_REVIEWED`
- `NEEDS_REVIEW`
- `NEEDS_MATERIALIZATION`
- `NEEDS_UPSTREAM_FIX`
- `BLOCKED`
- `INVALID_REVIEW_STATE`

规则：

#### COMPLETE_BASE

直接可供研究使用。

不要调用 Luna。

不要看 PDF。

#### COMPLETE_REVIEWED

优先使用 resolved/effective 数据。

不要重复 Luna。

不要默认重复看 PDF。

#### NEEDS_REVIEW

只进入候选 Repair Queue。

不能仅因为 document 为 NEEDS_REVIEW 就自动看 PDF。

#### NEEDS_MATERIALIZATION

只允许在显式 QUALITY_REVIEW 流程中 materialize。

Read/query 不能产生隐藏写入。

#### NEEDS_UPSTREAM_FIX

不能用 P9 强行修。

路由 parser / extraction。

#### BLOCKED / INVALID_REVIEW_STATE

Fail closed。

不得 silent fallback 到 Raw 并宣称可用。

### Step 4 — Build ResearchRequirementSet

重新读取当前：

- 公司分析的约束.md；
- 问题清单.md。

把本次研究确实要求的数据形成 run-local ResearchRequirementSet。

每项至少包含：

- requirement_id；
- source_rule_ref；
- description；
- target_periods；
- evidence_strategies；
- criticality；
- allow_partial；
- allow_not_disclosed。

不得自动创建 Canonical Metric Layer。

### Step 5 — Research Data Coverage Scan

优先使用：

- `ffdf_get_company_report_context`
- `ffdf_search_company`
- `ffdf_find_table_rows`
- P8 Raw Fact / Evidence tools
- `ffdf_get_resolved_fact`
- `ffdf_list_resolved_facts`
- `ffdf_locate_evidence`（必要时）

每个 requirement 分类：

- `AVAILABLE`
- `PARTIAL`
- `NEEDS_REVIEW`
- `NEEDS_UPSTREAM_FIX`
- `NOT_DISCLOSED`
- `NOT_FOUND`
- `AMBIGUOUS`
- `NOT_APPLICABLE`

Locator hit 不是 RawFact。

如果 PDF 看起来存在披露但 P6 没有合法 RawFact：

`P6_MISSING_FACT_CANDIDATE -> UPSTREAM_FIX`

不得通过 P9 创建 Fact。

### Step 6 — Build minimal Research Repair Queue

每项至少包含：

- document_sha256；
- requirement_id（如适用）；
- review_task_id（如适用）；
- reason；
- disposition。

Disposition 只能是：

- `QUALITY_REVIEW`
- `UPSTREAM_FIX`
- `RESEARCH_GAP`
- `NOT_DISCLOSED`
- `CATALOG_GAP`
- `NO_ACTION`

标准路由：

`NEEDS_REVIEW + research-relevant + P9 SUPPORTED -> QUALITY_REVIEW`

`RAW_EXTRACTION_DEFECT -> UPSTREAM_FIX`

`P6_MISSING_FACT_CANDIDATE -> UPSTREAM_FIX`

明确未披露 -> `NOT_DISCLOSED`

catalog 无法证明覆盖 -> `CATALOG_GAP`

与当前研究无关的 non-blocking issue -> `NO_ACTION`

不要为了 database 全 PASS 而处理所有非研究相关 Review Task。

### Step 7 — Structured context first

对 `QUALITY_REVIEW` 项首先调用：

- `ffdf_list_review_tasks`
- `ffdf_get_review_context`

优先检查：

- P3 page text；
- P5 table/cell；
- P6 RawFact；
- P6 Evidence；
- P7 issue；
- 当前 P9 resolution；
- neighbor pages；
- recommended visual targets。

固定原则：

`STRUCTURED FIRST -> VISUAL SECOND`

### Step 8 — Luna 5.6 Max semantic review

只有结构化资料需要模型理解时才调用模型。

调用前再次验证：

`model == luna5.6-max`

只传当前 Review Task 的最小上下文。

要求 Luna 5.6 Max 判断：

- period 是否唯一；
- unit 是否唯一；
- scope 是否唯一；
- table classification 是否唯一；
- structured evidence 是否已经足够；
- 是否需要原始 PDF layout。

如果 structured evidence 足够：

不要 render PDF。

### Step 9 — PDF Visual only when required

只有 target-related structured evidence 仍不足时才调用：

1. `ffdf_render_table`
2. 必要时同表 `HIGH_DETAIL`
3. 必要时 `ffdf_render_table_group`
4. 必要时 `ffdf_render_page`
5. 最后才允许 HIGH_DETAIL / deterministic tiling

禁止：

- 全 PDF 顺序截图；
- 默认全页高分辨率；
- arbitrary filesystem path；
- arbitrary bbox；
- 同一目标无意义重复 render。

只允许传领域标识：

- document_sha256；
- table_id；
- table_group_id；
- page_no。

### Step 10 — Visual decision class

Luna 5.6 Max 的视觉判断必须归入且仅归入：

- `EXPLICIT_AND_ANCHORABLE`
- `EXPLICIT_VISUAL_ONLY`
- `RAW_EXTRACTION_DEFECT`
- `AMBIGUOUS`

#### EXPLICIT_AND_ANCHORABLE

只有同时满足：

- PDF 视觉明确；
- 有合法 P5/P6 authoritative anchor；
- P9 v1 action 可以表达；

才可作为 durable P9 candidate。

#### EXPLICIT_VISUAL_ONLY

当前研究 run 可用，但：

- 不写 P9；
- 不成为 canonical reusable truth；
- 必须保留 VisualRef provenance。

#### RAW_EXTRACTION_DEFECT

必须：

`STOP P9 -> UPSTREAM_FIX -> parser/extraction repair`

禁止 SET_VALUE / PATCH_FACT。

#### AMBIGUOUS

保持 unresolved / REVIEW_REQUIRED。

禁止猜测。

### Step 11 — Controlled P9 write-through

普通研究默认：

`RESEARCH_FALLBACK`

不得写 P9。

只有显式 QUALITY_REVIEW 才允许调用：

- `ffdf_prepare_review_overlay`
- `ffdf_submit_review_resolution`
- `ffdf_materialize_resolved_view`

Submit 前必须核对：

- review_task_id；
- expected_base_validation_report_sha256；
- expected_overlay_set_hash_before；
- task still unresolved；
- task still SUPPORTED；
- action allowed；
- evidence legal。

状态变化时：

`RESEARCH_MCP_REVIEW_STATE_CHANGED`

必须停止写入并重新读取状态。

P9 v1 禁止：

- SET_VALUE；
- SET_METRIC；
- PATCH_FACT；
- 创建不存在的 RawFact；
- 把 VisualRef 当 P9 Evidence。

### Step 12 — Re-run Preflight

任何 QUALITY_REVIEW / upstream fix 完成后，必须重新运行 Preflight。

不得从修复步骤直接跳进正式分析。

### Step 13 — Readiness decision

区分：

#### period_monitoring_complete

所有 observed filings 已完成状态扫描。

#### research_ready

本次研究所有 critical requirements：

- 已可靠可用；或
- 明确 NOT_DISCLOSED / NOT_APPLICABLE 且研究规则允许；
- 不存在会影响核心研究结论的 unresolved blocker。

#### database_fully_reviewed

所有 observed documents 均为：

- COMPLETE_BASE；或
- COMPLETE_REVIEWED。

正式研究只要求：

`period_monitoring_complete = true`

且：

`research_ready = true`

不要求 database_fully_reviewed = true。

因此允许：

`document = NEEDS_REVIEW`

但该 issue 与当前研究无关、所有 critical requirements 可用：

`research_ready = true`

## Required output

结束时输出一份 concise Preflight summary，至少包括：

- company；
- normalized ticker/market（如已解析）；
- year_range；
- model；
- observed filing count；
- latest observed filing；
- COMPLETE_BASE count；
- COMPLETE_REVIEWED count；
- NEEDS_REVIEW count；
- NEEDS_UPSTREAM_FIX count；
- BLOCKED count；
- critical requirement count；
- AVAILABLE / PARTIAL / NOT_DISCLOSED / blocking count；
- Repair Queue；
- visual_required_count；
- visual_call_count；
- period_monitoring_complete；
- research_ready；
- database_fully_reviewed；
- blockers；
- warnings；
- known data gaps；
- catalog/event coverage limitations。

最终状态必须是二者之一：

`RESEARCH PREFLIGHT: PASS`

或：

`RESEARCH PREFLIGHT: FAIL`

只有 PASS 才允许调用方继续正式公司分析。

## Non-negotiable prohibitions

禁止：

1. 跳过 Preflight 直接宣称数据可研究；
2. 把全部财报交给 Luna 5.6 Max 重读；
3. 默认对全部 REVIEW_REQUIRED 看 PDF；
4. 使用 Luna 5.6 Max 以外模型；
5. 自动模型 fallback；
6. 通过 P9 修改 Raw 数值；
7. 通过 P9 创建缺失 RawFact；
8. arbitrary filesystem read；
9. arbitrary PDF bbox；
10. 任意 SQL surface；
11. 网络调用或外部 AI API；
12. silent fallback from corrupt P9 to Raw；
13. 猜测 period / unit / scope；
14. 把 catalog absence 写成 company not published；
15. 把 locator hit 当 RawFact；
16. 把 VisualRef 当 P9 v1 Evidence。

## Completion rule

只有同时满足：

`period_monitoring_complete == true`

和：

`research_ready == true`

才能输出：

`RESEARCH PREFLIGHT: PASS`

否则输出 FAIL，并列出精确 blocker 和下一步。
