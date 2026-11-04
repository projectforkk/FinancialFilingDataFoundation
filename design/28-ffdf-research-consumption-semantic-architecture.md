# 28 — FFDF Research Consumption & Deterministic Semantic Reconstruction Architecture

状态：**ACTIVE CROSS-PHASE REFERENCE DESIGN — IMPLEMENTATION NOT AUTHORIZED**

适用范围：
- P6 Raw Facts / Evidence 之后的长期语义解释架构；
- P7 后续 semantic validation 演进；
- P9 durable review 的职责边界；
- P10 Codex Dynamic Research Integration；
- Research MCP Visual Fallback；
- 后续 canonical metric / derived financial metric 层。

本设计不修改 P0-P9 已验收历史。P9 v1 已完成 Independent Acceptance 并 merge main。

本文件在 P10 design baseline 中作为**未来 deterministic semantic architecture reference**。它不授权 Semantic Resolver production；任何实现必须在 P10/P9 accepted boundary 基础上再次明确 Design-First 授权。

---

## 1. 背景与问题

FFDF 已经能够稳定完成：

```text
PDF
→ P3 native page / section / FTS
→ P4 table candidate
→ P5 structural table reconstruction
→ P6 RawFact + Evidence
→ P7 validation
→ P8 read-only MCP
```

P6 的核心职责是保存**原始事实与原始证据**，而不是财务语义标准化。

因此大量真实财报会出现：

```text
raw_value 正确
evidence 完整
table structure 可定位

但：
raw_period_label = null
raw_unit = null
raw_scope = null
value role 未结构化
statement type 未结构化
```

这会使 P7 合理地产生：

```text
REVIEW_REQUIRED
reuse_eligible = false
```

这不是“PDF 没解析出来”，而是：

> Raw extraction 与财务语义理解之间缺少一层正式、可追溯、可校验的语义重建。

同时，产品目标并不要求 FFDF parser 在第一天就自动理解所有财报。即使 deterministic parser 暂时不足，Codex 仍应能够通过原始 PDF 视觉证据完成当前研究。

因此长期架构必须同时支持：

1. **现在能用**：Research MCP + Codex Visual Fallback；
2. **未来越来越自动**：Deterministic Financial Semantic Reconstruction。

二者不是替代关系。

---

## 2. 总体架构

长期目标：

```text
Original PDF
   ↓
P3 / P4 / P5
Raw structural artifacts
   ↓
P6 Immutable Raw Facts + Evidence
   ↓
S1 Deterministic Financial Semantic Reconstruction
   │
   ├─ Header Graph
   ├─ Statement Context
   ├─ Value Role
   ├─ Period
   ├─ Unit / Dimension
   ├─ Scope
   └─ Provenance / Candidates
   ↓
S2 Semantic Validation
   │
   ├─ critical fact readiness
   ├─ semantic correctness
   ├─ coverage
   └─ unresolved semantic issues
   ↓
P9 Durable Review Overlay
   │
   └─ only true unresolved ambiguity / reviewed decisions
   ↓
Resolved Semantic Facts
   ↓
Canonical Metric Mapping
   ↓
Canonical Facts
   ↓
Derived Financial Metrics
   │
   ├─ YoY
   ├─ QoQ
   ├─ TTM
   ├─ margins
   ├─ ROE
   └─ ROIC
   ↓
Research / Valuation / Investment Analysis
```

Research fallback 并行存在：

```text
P8 / Resolved Query
   ↓
Codex structured research
   ↓
still insufficient
   ↓
Research MCP Visual Evidence
   ↓
Codex reviewer decision
   ↓
current research result
```

---

## 3. 核心原则

### 3.1 Raw 永远 immutable

以下字段属于 P6 raw truth：

- `raw_metric_name`
- `raw_value`
- `parsed_numeric_value`
- `raw_period_label`
- `raw_unit`
- `raw_scope`
- `raw_fact_id`
- `evidence_id`

后续 semantic/review/canonical layer 不得覆盖或重写 P6 artifact。

---

### 3.2 Semantic interpretation 是派生层

所有后续解释必须：

```text
RawFact
+
context/evidence/rules
=
Semantic Interpretation
```

而不是修改 RawFact。

---

### 3.3 宁可 UNKNOWN，不允许错误赋值

Deterministic resolver 的正确性优先级：

```text
false semantic assignment = unacceptable
unknown / ambiguous = acceptable
```

覆盖率不能以错误赋值为代价提高。

---

### 3.4 Visual source 与 Codex interpretation 分层

PDF 页面图像是：

`authoritative source evidence`

Codex 对图片的解释是：

`reviewer decision`

两者不得混为同一层 truth。

---

### 3.5 P9 只负责 durable reviewed decision

P9 不做财务理解。

正式职责：

```text
validate
persist
supersede
materialize
audit
reuse
```

reviewer 可以是 Codex 或 human。

---

### 3.6 REVIEW_REQUIRED 不阻断当前研究

正式含义：

> deterministic pipeline 尚未证明整个 document 可以 canonical reuse。

它不等于：

`DATA_UNUSABLE`

Codex 可继续使用：

- RawFact；
- Evidence；
- Table；
- Page Text；
- PDF Visual Evidence；

完成当前研究。

---

## 4. 两条实施路线

### Route A — Research Runtime Fallback

目标：

> 在 FFDF 还不能自动解释所有财报时，让 Codex 现在就能可靠完成研究。

由 design/29 定义。

当前授权：**DESIGN REFERENCE ONLY / PRODUCTION CLOSED**。

P10 v1 不依赖该能力。当前 P8/P9 structured evidence 不足且确实需要 PDF visual 时，P10 必须返回 `P10_VISUAL_CAPABILITY_REQUIRED`。

未来只有在 Research MCP 被单独授权、实现、Code Review、Independent Acceptance 后，P10 capability manifest 才可把 PDF visual capability 从 UNAVAILABLE 改为 AVAILABLE。

---

### Route B — Deterministic Semantic Reconstruction

目标：

> 将高频、稳定、可证明的视觉/人工解释沉淀成 deterministic rules，使未来同类财报自动解析。

由本设计定义。

当前顺序：

```text
P10 core dynamic integration design/implementation/acceptance
→ separately authorize Research MCP when needed
→ collect reviewed/visual patterns
→ separately authorize Semantic Resolver
```

因此：

**design/28 可以作为长期 architecture baseline，但 Semantic Resolver production 不属于 P10 v1。**

---

## 5. Semantic Artifact

建议独立 artifact：

```text
semantic-root/
  <document_sha256>/
    semantic_manifest.json
    table_contexts.jsonl
    header_graphs.jsonl
    column_contexts.jsonl
    fact_semantics.jsonl
    semantic_issues.jsonl
```

Schema：

`p6-semantic-context-v1`

Engine version：

`financial-semantic-reconstruction-v1`

输入至少：

- trusted P3；
- trusted P5；
- trusted P6；
- FilingIdentity / filing context；
- rule set。

不得重新打开网络来源，不得修改 raw PDF。

---

## 6. Semantic Run Identity

必须区分三个 identity。

### 6.1 Semantic target key

单个 P6 fact 的稳定目标仍然是：

`raw_fact_id`

---

### 6.2 semantic_run_id

```text
SHA256(
  document_sha256
  + "\0" + p3_fingerprint
  + "\0" + p5_fingerprint
  + "\0" + p6_fingerprint
  + "\0" + filing_context_hash
  + "\0" + semantic_engine_version
  + "\0" + rule_set_hash
)
```

---

### 6.3 semantic_fact_revision_id

```text
SHA256(
  semantic_run_id
  + "\0" + raw_fact_id
  + "\0" + canonical_semantic_payload
)
```

这样：

- RawFact identity 稳定；
- 不同 semantic engine/rule run 不混淆；
- 同一 run 中 semantic payload 可验证。

---

## 7. Semantic Field State

每个 semantic field 不是简单 nullable 字符串。

统一状态：

```text
DETERMINISTIC
REVIEWED
AMBIGUOUS
UNKNOWN
NOT_REQUIRED
```

字段至少包括：

- statement_type；
- value_role；
- period；
- unit/dimension；
- scope。

---

## 8. Candidate Semantics

真实 ambiguity 必须保存候选，不允许只记一个 `AMBIGUOUS` flag。

示例：

```json
{
  "field": "period",
  "status": "AMBIGUOUS",
  "candidates": [
    {
      "value": {"period_kind": "DURATION", "fiscal_period": "Q3"},
      "rule_ids": ["SEM-PERIOD-012"],
      "evidence_refs": ["..."]
    },
    {
      "value": {"period_kind": "YTD", "through_period": "Q3"},
      "rule_ids": ["SEM-PERIOD-014"],
      "evidence_refs": ["..."]
    }
  ],
  "conflict_reason": "SAME_PRIORITY_EXPLICIT_EVIDENCE_CONFLICT"
}
```

目的：

P9 reviewer 不需要重新扫描整个 PDF 才知道“在两个什么解释之间选择”。

---

## 9. Header Graph Contract

Header Graph 是 Semantic Resolver 的核心。

不得只靠散乱 regex。

每个 table/header 输出：

```json
{
  "table_id": "...",
  "header_nodes": [
    {
      "header_id": "...",
      "text": "本报告期",
      "row_span": [0, 0],
      "column_span": [1, 2],
      "source_cell_ids": ["..."]
    }
  ],
  "header_edges": [
    {
      "parent": "...",
      "child": "..."
    }
  ]
}
```

---

## 10. Header Graph Deterministic Algorithm

至少包含以下固定阶段：

```text
P5 cell geometry
→ identify candidate header rows
→ reconstruct horizontal spans
→ reconstruct vertical/parent-child relations
→ attach header path to each value column
→ classify header path
→ resolve conflict / ambiguity
```

### 10.1 Candidate header row

只能使用：

- table 前部连续 non-body rows；
- P5 cell role / numeric structure；
- explicit header markers；
- geometry alignment。

不得根据最终想得到的 period 反推 header。

### 10.2 Span reconstruction

Node span 必须由：

- bbox；
- covered value-column anchors；
- source cells；

deterministically 计算。

### 10.3 Column header path

每个 value column 得到 ordered path，例如：

```text
年初至报告期末
  → 比上年同期增减
```

### 10.4 Same-level conflict

同一级 explicit header 若给出两个互斥含义：

`AMBIGUOUS`

不得按 regex 顺序任选一个。

---

## 11. Cross-page Header Inheritance

只允许在 verified P5 `table_group_id` 内继承。

条件：

1. member pages adjacent；
2. continuation group 已通过 P5 contract；
3. continuation table value-column model compatible；
4. next fragment 无完整 conflicting header。

行为：

### repeated header

若后页重复 header 与前页语义一致：

`CONFIRMED_REPEATED_HEADER`

### partial header

允许继承缺失 parent context，但必须保留：

`INHERITED_TABLE_GROUP_CONTEXT`

### conflicting header

后页 explicit header 与 inherited header 冲突：

`AMBIGUOUS`

不得覆盖。

### no verified group

禁止跨页继承。

---

## 12. Statement Type

至少：

```text
BALANCE_SHEET
INCOME_STATEMENT
CASH_FLOW_STATEMENT
EQUITY_STATEMENT
KPI_TABLE
SEGMENT_TABLE
NOTE_TABLE
OTHER
UNKNOWN
```

证据来源优先：

1. explicit table title；
2. section title；
3. verified continuation inheritance。

不得仅根据几个 metric 名称就强制改变 table statement type。

---

## 13. Value Role

至少：

```text
VALUE
YOY_PERCENT
QOQ_PERCENT
CHANGE_PERCENT
CHANGE_AMOUNT
RATIO
PER_SHARE
COUNT
DATE
OTHER
UNKNOWN
```

例如季度 KPI：

```text
本报告期                 → VALUE / current period
本报告期同比             → YOY_PERCENT
年初至报告期末           → VALUE / YTD
年初至报告期末同比       → YOY_PERCENT / YTD comparison
```

Value Role 必须来自 header path + value syntax + row context。

---

## 14. Period Model

禁止把 `fiscal_year=2026, Q3` 默认等同自然年度 2026-07-01..09-30。

正式模型：

```json
{
  "period_kind": "DURATION",
  "fiscal_year": 2026,
  "fiscal_period": "Q3",
  "calendar_start_date": "2026-07-01",
  "calendar_end_date": "2026-09-30",
  "duration_days": 92,
  "comparison_role": null,
  "derivation_basis": "HEADER_PLUS_FILING_CALENDAR"
}
```

Period kind 至少：

```text
INSTANT
DURATION
YTD
COMPARATIVE_DURATION
COMPARATIVE_INSTANT
UNKNOWN
```

---

## 15. Filing Context

Semantic engine 所需 filing context 至少包含：

- fiscal_year；
- raw_fiscal_period；
- report_date；
- filing_date；
- fiscal_year_end；
- period_class；
- amendment/restatement metadata。

如果 fiscal calendar 不足：

不得从 Q3 字样默认 calendar Q3。

状态：

`UNKNOWN_FISCAL_CALENDAR`

可进入 review。

---

## 16. Unit Model

不得用单一 `unit` enum 混合所有概念。

正式拆分：

```json
{
  "currency": "CNY",
  "scale": "1",
  "dimension": "MONETARY",
  "presentation_unit": "CNY",
  "source_level": "ROW_EXPLICIT"
}
```

维度至少：

```text
MONETARY
PERCENT
RATIO
PER_SHARE
COUNT
SHARES
VOLUME
AREA
DATE
OTHER
UNKNOWN
```

---

## 17. Unit Precedence

显式层级：

```text
FACT EXPLICIT
>
ROW EXPLICIT
>
COLUMN EXPLICIT
>
TABLE EXPLICIT
>
SECTION EXPLICIT
>
FILING CONTEXT DERIVATION
```

例如：

table：

`单位：人民币万元`

row：

`基本每股收益（元/股）`

结果：

`CNY_PER_SHARE`

不能得到万元/股。

同一级 explicit evidence 冲突：

`AMBIGUOUS`

而不是任选一个。

---

## 18. Scope Model

至少：

```text
CONSOLIDATED
PARENT
SUBSIDIARY
SEGMENT
OTHER
UNKNOWN
```

继承边界：

```text
section
→ table
→ table group
→ row/fact
```

只能在 explicit compatible context 内向下继承。

禁止跨 section/table group 静默继承。

同级冲突：

`AMBIGUOUS`

---

## 19. Rule Registry

所有 semantic rules 必须有稳定 ID。

示例：

```text
SEM-HEADER-001
SEM-PERIOD-001
SEM-PERIOD-012
SEM-UNIT-001
SEM-SCOPE-001
SEM-VALUE-ROLE-001
```

每条 rule 定义：

- rule_id；
- version；
- applicability；
- required inputs；
- priority；
- output；
- evidence requirement；
- conflict behavior；
- golden fixtures。

完整 rule set 生成：

`rule_set_hash`

任何 rule 变化：

产生新的 semantic_run_id。

不得 silent reuse 旧 semantic artifact。

---

## 20. Rule Promotion

Visual/Codex decisions 不得自动升级为 parser rule。

正式流程：

```text
recurring visual-review pattern
→ rule candidate
→ design review
→ explicit deterministic rule
→ golden tests
→ code review
→ acceptance
→ rule registry
```

---

## 21. Pre-canonical Metric Class

`required_semantics()` 不能依赖最终 canonical metric，否则形成循环依赖。

增加轻量 pre-canonical semantic class：

```text
MONETARY_FLOW
MONETARY_BALANCE
MONETARY_CHANGE
RATIO
PERCENT_CHANGE
PER_SHARE
COUNT
DATE
OTHER
UNKNOWN
```

这不是 canonical metric taxonomy。

只用于：

- required semantics；
- validation/readiness；
- unit expectations。

---

## 22. required_semantics()

正式函数：

```text
required_semantics(
  statement_type,
  value_role,
  semantic_metric_class
)
```

输出：

```json
{
  "period": true,
  "currency": true,
  "scale": true,
  "dimension": true,
  "scope": true,
  "comparison": false
}
```

例如：

### Revenue value

要求：

- period；
- currency；
- scale；
- scope；
- value_role。

### YoY percentage

要求：

- subject period；
- comparison relation；
- PERCENT dimension；
- scope compatibility。

不要求 currency。

### EPS

要求：

- period；
- CURRENCY_PER_SHARE / compatible dimension；
- scope。

---

## 23. Semantic Readiness

Semantic layer 只输出：

```text
RAW_ONLY
SEMANTIC_PARTIAL
SEMANTIC_READY
```

不输出 `CANONICAL_READY`。

### RAW_ONLY

无足够 semantic interpretation。

### SEMANTIC_PARTIAL

至少一个关键 semantic field 已确认，但 required semantics 未齐全。

### SEMANTIC_READY

`required_semantics()` 要求全部满足，且：

- no unresolved field conflict；
- evidence/provenance valid；
- semantic artifact valid。

---

## 24. Canonical Readiness 属于后续层

Canonical layer 独立状态：

```text
UNMAPPED
MAPPED
AMBIGUOUS
CANONICAL_READY
```

关系：

```text
P6 Raw
→ Semantic
→ SEMANTIC_READY
→ Canonical Mapper
→ CANONICAL_READY
```

---

## 25. Semantic Validation

P7 后续版本应改为使用 semantic facts，而不是只统计 P6 raw nullable fields。

至少分：

- critical semantic gate；
- semantic coverage；
- unresolved ambiguity；
- evidence integrity。

---

## 26. Critical Fact Gate

不能只靠整体 coverage。

Golden / production gate 优先检查关键事实。

至少：

- total assets；
- total liabilities；
- equity；
- revenue；
- operating profit where applicable；
- net profit / attributable net profit；
- operating cash flow；
- EPS where disclosed。

原则：

```text
critical fact wrong assignment > any coverage percentage
```

对于 acceptance golden：

`critical semantic correctness = 100%`

---

## 27. Coverage

Coverage 只是 calibration / completeness metric。

分别计算：

```text
core_period_coverage
core_unit_coverage
core_scope_coverage

all_period_coverage
all_unit_coverage
all_scope_coverage
```

unit denominator 只包含 `unit-required facts`。

不能把百分比 fact 因“没有 CNY”算作 unit missing。

---

## 28. Golden Truth Governance

Golden 不允许由同一个 parser 自己生成 expected result。

每个 semantic golden 必须保存：

- document SHA；
- page/table/cell source；
- expected field/value；
- expected evidence；
- first reviewer；
- second reviewer；
- disagreement resolution；
- golden version。

至少双审或 reviewer + design-owner arbitration。

Golden 本身变更也必须版本化。

---

## 29. Golden Corpus

不仅按公司数量覆盖，还要按结构模式覆盖。

至少：

- CN Q1；
- CN H1；
- CN Q3；
- CN FY；
- HK interim；
- HK annual；
- merged multi-level header；
- continuation table；
- repeated/partial continuation header；
- mixed table units；
- row unit override；
- parent/consolidated same document；
- bilingual header；
- percentage columns；
- per-share；
- restated comparative；
- non-December fiscal year；
- blank header cells；
- multiple statements same page。

002371 2026Q3 作为第一个 KPI/header golden。

---

## 30. P9 v1 / Semantic Layer Migration

当前 P9 v1 已建立：

- immutable resolution store；
- target/evidence validation；
- prior active state；
- supersession；
- overlay hash；
- materialized resolved view。

P9 v1 已完成 Independent Acceptance，accepted merge 为：

`58a1d2236b68a56fc66ddf8b97603e7232c87265`

本设计不得 retroactively 修改 accepted P9 history / semantics。

未来 semantic layer 上线后：

```text
P9 v1 accepted history
→ design amendment / adapter
→ semantic-target review
```

可能新增：

```text
target_layer = SEMANTIC
semantic_fact_revision_id
semantic_field
```

但必须在 P9 closeout 后单独 Design-First。

---

## 31. PDF Visual Evidence 与 P9

当前 P9 v1 evidence 仍以 P5/P6 authoritative evidence 为主。

未来可能新增：

`PDF_VISUAL_EVIDENCE`

前提：

- document_sha256；
- page_no；
- deterministic clip；
- renderer version；
- render_sha256；
- source PDF fingerprint。

该扩展只能修：

- semantic field；
- reviewed interpretation。

不得默认允许通过视觉 overlay 修改：

- raw numeric value；
- raw metric name；
- parsed numeric value。

任何 numeric extraction defect 应回到 parser defect flow。

---

## 32. Registry Lineage

长期建议支持：

```text
RAW parse run
→ semantic run
→ review resolution set
→ resolved semantic run
→ canonical mapping run
```

每层至少：

- run_id；
- parent_run_id(s)；
- document_sha256；
- input_fingerprints；
- engine/schema version；
- rule_set_hash where applicable；
- artifact hashes；
- validation status。

这样研究结论能够完整追到原始 PDF。

---

## 33. MCP Compatibility

P8 v1 已验收的 11 tools 永远保持 raw contract。

例如：

`ffdf_get_fact`

不得未来静默变成 semantic fact。

未来 additive tools：

- `ffdf_get_semantic_fact`
- `ffdf_list_semantic_facts`
- `ffdf_get_document_readiness`

Canonical layer 再单独增加 canonical query tools。

---

## 34. Performance

Semantic engine 初始目标：

- first semantic build representative CN <= 10s；
- representative HK <= 20s；
- validated reuse <= 2s；
- loader semantic replay/tamper validation <= 10s。

不包含 Codex inference。

---

## 35. Determinism

相同：

- P3/P5/P6；
- filing context；
- engine version；
- rule set；

必须得到：

- same semantic_run_id；
- same header graph bytes；
- same fact semantics bytes；
- same issue IDs；
- same semantic readiness。

禁止：

- random UUID；
- implicit current time；
- filesystem order；
- network；
- remote AI。

---

## 36. Error / Issue Model

执行错误至少：

```text
SEM_INPUT_INVALID
SEM_FILING_CONTEXT_INCOMPLETE
SEM_ARTIFACT_CORRUPT
SEM_RULESET_INCOMPATIBLE
SEM_PERSIST_FAILED
```

semantic issue 至少：

```text
SEM_HEADER_AMBIGUOUS
SEM_PERIOD_AMBIGUOUS
SEM_UNIT_AMBIGUOUS
SEM_SCOPE_AMBIGUOUS
SEM_VALUE_ROLE_AMBIGUOUS
SEM_FISCAL_CALENDAR_UNKNOWN
SEM_CONTEXT_CONFLICT
```

---

## 37. Immutability

Semantic engine 只写 semantic artifact。

必须证明以下前后不变：

- raw PDF；
- P3；
- P4；
- P5；
- P6；
- P7 historical artifact；
- Registry unless explicit later registration step。

---

## 38. Unit / Golden Tests

至少覆盖：

1. header node/span；
2. multi-level parent-child；
3. merged header；
4. current quarter vs YTD；
5. YoY value role；
6. table unit；
7. row unit override；
8. same-level unit conflict；
9. consolidated/parent scope；
10. table-group header inheritance；
11. repeated continuation header；
12. conflicting continuation header；
13. non-calendar fiscal year；
14. restated comparative；
15. candidate ambiguity preservation；
16. required_semantics；
17. semantic readiness；
18. stable IDs；
19. rule_set invalidation；
20. dual-root determinism；
21. raw immutability；
22. 002371 Q3 golden；
23. CN/HK diverse golden corpus。

---

## 39. Relationship with design/29

design/29 是**未来 additive research visual/resolved-query capability reference**。

本设计是**长期 parser intelligence improvement**。

正式顺序：

```text
P10 core uses accepted P8/P9
→ structured sufficient: research continues
→ structured insufficient: explicit visual capability gap
→ separately authorized Research MCP may later provide visual evidence
→ collect real reviewed/visual patterns
→ separately authorized Semantic Resolver may promote proven deterministic rules
```

不得因 Semantic Resolver 或 Research MCP 尚未实现而让 P10 猜测；也不得因二者尚未完成而阻塞 structured-sufficient 的当前 Codex research。

---

## 40. Exit

本设计只有在：

- Semantic artifact contract frozen；
- Header Graph algorithm frozen；
- rule registry frozen；
- golden governance established；
- implementation phase explicitly authorized；

之后才能进入 production implementation。

未达到上述条件前，不得 code-first。

即使上述设计条件完整，也仍需要 design owner 在当时 accepted baseline 上单独授权 Semantic Resolver production；本 P10 design baseline 不提供该授权。
