# 29 — Research MCP Visual Evidence, Resolved Query & Review Write-Through 详细设计

状态：**ACTIVE FUTURE REFERENCE DESIGN v2 — PRODUCTION NOT AUTHORIZED**

依赖：
- P8 Local MCP = DONE；
- P9 v1 Durable Review Overlay = DONE / PASS；
- accepted P9 merge = `58a1d2236b68a56fc66ddf8b97603e7232c87265`；
- design/28 = future semantic architecture reference；
- P10 = Codex Dynamic Research Integration v1 design。

授权状态：
- 本文件已被 P10 design reconciliation 接纳为 future additive capability reference；
- Research MCP production = **NOT AUTHORIZED**；
- P10 v1 不以本设计实现为前置条件。

本设计解决两个相互关联但职责不同的问题：

1. **QUALITY_REVIEW（数据库质量完善）**：指定公司与财报期间后，如何只处理尚未完善的 P7/P9 review 项，必要时让 Codex + Luna 查看原始 PDF 视觉证据，并把当前 P9 支持的语义修正持久化为 durable reviewed state；
2. **RESEARCH_FALLBACK（研究期视觉回退）**：当当前研究所需事实无法由既有 resolved state 或 P8 structured evidence 安全支持时，如何提供受控 visual evidence，并明确区分 durable resolution、run-local verified、raw extraction defect 与 unresolved。

**唯一数据访问边界：**

- 公司财报文档发现与 Raw/Structured/Evidence/Validation 读取，固定通过已验收 P8 MCP / accepted P8 service contract；
- durable review 写入，固定通过已验收 P9 public API semantics，由本设计新增的受控 Research MCP write-through tools 暴露；禁止直接编辑 P9 store 文件；
- 禁止 Codex/Luna 直接访问 SQLite、JSONL、artifact directory 或任意数据库；
- PDF visual 只能由 Research MCP 根据 `document_sha256` 从 trusted immutable source 渲染，caller 不得提交 filesystem path。

在该 production capability 尚未独立验收前，P10 v1 必须返回 `P10_VISUAL_CAPABILITY_REQUIRED`，不得假装本文件中的工具已经存在。

本设计不声称让 FFDF parser 自动完全正确，也不把模型视觉判断升级为 deterministic parser truth。

---

## 1. 目标

新增 additive Research MCP Extension，使 Codex 可以：

1. 对指定公司与财报期间，先通过 P8 确定已经 ingest 的正式财报；
2. 查询 P9 是否已有 durable reviewed overlay，并优先消费 Resolved View；
3. 用 deterministic `quality_state` 判断文档是已完善、待复核、需上游修复、阻断还是 review state 损坏；
4. 只枚举尚未完成的 P9 Review Task，不重复复核已经 PASS / durable resolved 的数据；
5. 优先使用 P8 RawFact / Evidence / Table / Page Text / Validation 完成语义判断；
6. structured evidence 不足且满足 Visual Trigger Matrix 时，定位并渲染最小充分的原始 PDF table/page visual evidence；
7. 由 Codex 负责 orchestration，Luna 作为推荐的高吞吐 visual reviewer profile 对必要图片进行判断；
8. 在真正满足当前 P9 evidence contract 时，通过受控 MCP write-through 提交 P9 resolution，并显式 materialize Resolved View；
9. 写入后重新读取 review state，只有 `resolved_validation_status=PASS` 且 `resolved_reuse_eligible=true` 才认定数据库层已完善；
10. 明确区分 durable resolved、run-local verified、raw extraction defect 与 unresolved；
11. 将 recurring visual-review patterns 反馈为后续 Semantic Resolver / parser rule candidate。

本设计优先优化“**一次视觉核实，后续重复复用**”，而不是让 Luna 重新阅读整份财报。

---

## 2. 非目标

本层不：

- 修改 P8 v1 现有 11 tools；
- 修改 RawFact；
- OCR；
- arbitrary file read；
- arbitrary bbox screenshot；
- direct database / SQLite / JSONL / artifact-store query；
- shell / SQL / Python execution；
- network；
- AI API；
- 自动生成 canonical metric；
- 自动注册 reusable parsed data；
- 自动把 Codex visual decision 当 deterministic parser truth；
- 自动把 visual pattern 变成 semantic rule；
- 掩盖 P5/P6 extraction defect。

---

## 3. 主路径

### 3.1 QUALITY_REVIEW — 指定公司/期间的数据完善主路径

这是第一层数据库完善的**唯一标准路径**：

```text
market + ticker + target fiscal years / report periods
        ↓
P8 MCP: ffdf_list_documents
        ↓
确定目标 document_sha256 集合
        ↓
Research MCP: ffdf_get_review_state
        ↓
quality_state
  ├─ COMPLETE_BASE / COMPLETE_REVIEWED
  │      → skip，不打开 PDF，不重复 review
  │
  ├─ BLOCKED / INVALID_REVIEW_STATE
  │      → STOP，返回明确 upstream / review-store error
  │
  └─ NEEDS_REVIEW
         ↓
Research MCP: ffdf_prepare_review_overlay（仅 overlay 不存在时）
         ↓
Research MCP: ffdf_list_review_tasks
         ↓
仅处理 unresolved + SUPPORTED tasks
         ↓
Research MCP: ffdf_get_review_context
         ↓
P8 structured evidence sufficient?
    ├─ YES
    │    → Codex reviewer decision
    │    → ffdf_submit_review_resolution
    │
    └─ NO
         ↓
      Visual Trigger Matrix
         ↓
      ffdf_render_table
         ↓
      context still insufficient?
         ├─ NO → Luna visual decision
         └─ YES
              → ffdf_render_table_group / ffdf_render_page
              → Luna visual decision
         ↓
Decision Class
  ├─ EXPLICIT_AND_ANCHORABLE
  │      → ffdf_submit_review_resolution
  ├─ EXPLICIT_VISUAL_ONLY
  │      → 不得 durable submit；记录 run-local / upstream candidate
  ├─ RAW_EXTRACTION_DEFECT
  │      → STOP P9；进入 parser Design-First repair
  └─ AMBIGUOUS
         → 保持 REVIEW_REQUIRED
         ↓
Research MCP: ffdf_materialize_resolved_view
         ↓
Research MCP: ffdf_get_review_state
         ↓
resolved_validation_status == PASS
AND resolved_reuse_eligible == true ?
  ├─ YES → COMPLETE_REVIEWED
  └─ NO  → 保持 NEEDS_REVIEW / NEEDS_UPSTREAM_FIX
```

### 3.2 RESEARCH_FALLBACK — 研究期视觉回退

```text
Locate document through P8
   ↓
Query P9 review/resolved state
   ↓
durable resolved data exists?
   ├─ YES → use Resolved Query
   └─ NO  → P8 Raw Structured
              ↓
         Visual Trigger Matrix
              ↓
       structured sufficient?
        ├─ YES → current-run research
        └─ NO
             ↓
       Review Context / Locate Evidence
             ↓
       render_table → optional group/page escalation
             ↓
       Codex/Luna reviewer decision
             ↓
       durable P9 submit only if current P9 contract is satisfied
       otherwise run-local / defect / unresolved
```

QUALITY_REVIEW 和 RESEARCH_FALLBACK 共用同一事实、视觉、P9 边界；区别只在触发来源和完成条件，不允许维护两套语义。

---

## 4. REVIEW_REQUIRED 的消费边界

`REVIEW_REQUIRED` 表示：

> deterministic FFDF pipeline 尚未证明整份 document 可以 canonical reuse。

它不表示：

`current research forbidden`

Codex 可以继续：

- raw facts；
- evidence；
- table；
- page text；
- visual evidence。

但必须遵守本设计的 visual trigger / derived-use gate。

---

## 5. P8 backward compatibility

P8 v1 原 11 tools contract 不变。

特别：

`ffdf_get_fact`

永远返回 RawFact，不因为后续 overlay 而改变 raw 字段。

Research MCP Extension 使用 additive tool surface。

---

## 6. 未来新增 tool surface

未来单独授权后新增 **12 个 additive Research MCP 工具**。P8 v1 原 11 tools 完全不变。

### 6.1 Read / query tools

1. `ffdf_get_review_state`
2. `ffdf_get_resolved_fact`
3. `ffdf_list_resolved_facts`
4. `ffdf_list_review_tasks`
5. `ffdf_get_review_context`
6. `ffdf_locate_evidence`
7. `ffdf_render_table`
8. `ffdf_render_table_group`
9. `ffdf_render_page`

### 6.2 Explicit write-through tools

10. `ffdf_prepare_review_overlay`
11. `ffdf_submit_review_resolution`
12. `ffdf_materialize_resolved_view`

Write-through tools 只能调用 accepted P9 public APIs：

- `prepare_review_overlay`
- `submit_resolution`
- `materialize_resolved_view`

不得：

- 重写 P9 resolution semantics；
- 直接修改 resolution JSONL / manifest / snapshot 文件；
- 提供 arbitrary P9 store path；
- 接受 SQL / shell / filesystem mutation；
- 支持 P9 当前 enum 之外的新 action；
- 通过 MCP 绕过 P9 evidence validation、supersession、active-set 或 conflict rules。

如果实现时 MCP SDK 对 image/list-image response 有协议限制，必须先更新设计，不得静默改成 arbitrary file path 返回。

### 6.3 Quality state — 不新增可漂移的“完善布尔字段”

数据库是否“完善”不得通过新的持久化 `is_complete` 字段表达。

Research MCP 必须从 P7 + P9 当前 validated state **确定性派生**：

```text
COMPLETE_BASE
  = P7 validation_status == PASS
    AND P7 reuse_eligible == true
    AND no invalid P9 state

COMPLETE_REVIEWED
  = P9 resolved_validation_status == PASS
    AND P9 resolved_reuse_eligible == true

NEEDS_REVIEW
  = document is REVIEW_REQUIRED
    AND at least one unresolved SUPPORTED review task exists

NEEDS_UPSTREAM_FIX
  = unsupported review condition exists
    OR visual decision = RAW_EXTRACTION_DEFECT
    OR P6_MISSING_FACT_CANDIDATE blocks durable correction

BLOCKED
  = P7 BLOCKING / FAILURE
    OR pipeline compatibility is not COMPATIBLE

INVALID_REVIEW_STATE
  = P9 store/snapshot exists but fails accepted validation
```

优先级：

`INVALID_REVIEW_STATE > BLOCKED > COMPLETE_REVIEWED > COMPLETE_BASE > NEEDS_UPSTREAM_FIX > NEEDS_REVIEW`

不得把 document-level `REVIEW_REQUIRED` 直接等同为“所有事实不可用”，也不得把某个 fact 已 resolved 误写为整份 document 已 COMPLETE。

### 6.4 Review Task selection

`ffdf_list_review_tasks` 必须返回 accepted P9 task identity，并至少支持：

- document_sha256；
- resolved/unresolved 状态；
- reviewability；
- supported_actions；
- reason_code；
- page_no；
- table_id；
- raw_fact_ids；
- evidence_ids。

QUALITY_REVIEW 默认只返回：

```text
resolved_state != RESOLVED
AND reviewability == SUPPORTED
```

UNSUPPORTED task 必须单独计数并映射到 `NEEDS_UPSTREAM_FIX`，不能交给 Luna 猜测解决。

### 6.5 Controlled P9 write-through

`ffdf_submit_review_resolution` 必须：

1. 只接受 P9 当前支持的 action：
   - `SET_PERIOD`
   - `SET_UNIT`
   - `SET_SCOPE`
   - `CLASSIFY_TABLE_STATEMENT`
   - `ATTEST_ISSUE_RESOLVED`
2. 要求 caller 提供 `review_task_id`；
3. 要求 `expected_base_validation_report_sha256`；
4. 若已有 overlay，要求 `expected_overlay_set_hash_before`；
5. 在 submit 前重新加载 accepted P9 current state；
6. current state 与 expected state 不同则拒绝：
   `RESEARCH_MCP_REVIEW_STATE_CHANGED`；
7. 证据仍由 P9 `validate_direct_evidence` / semantic validation 决定是否合法；
8. 不接受 raw numeric replacement、raw metric rename 或任意 field patch；
9. 成功只表示 resolution 已进入 immutable P9 store，不等于 document 已完善。

`ffdf_materialize_resolved_view` 必须在 submit 之后显式调用，并返回：

- overlay_set_hash；
- resolved_validation_status；
- resolved_reuse_eligible；
- resolved/unresolved/unsupported counts；
- active resolution IDs。

最终必须再次调用 `ffdf_get_review_state` 验证状态，不允许以“submit 成功”代替“数据库已完善”。

### 6.6 Codex + Luna reviewer profile

FFDF correctness contract 不绑定具体模型名称。

推荐运行配置：

```text
Codex = orchestration / tool selection / P9 submission host
Luna  = default high-throughput visual reviewer
```

P9 现有 `ReviewerType` 保持：

`CODEX`

不新增 `LUNA` enum，不修改 P9 schema。

建议 `reviewer_id` 使用稳定、无敏感信息的 profile，例如：

`codex/luna-review`

模型版本、token、运行统计属于 Research MCP telemetry / run log，不进入 P9 semantic truth。

视觉模型输出本身不能成为 P9 evidence type；当前 P9 durable submit 仍必须有合法 P5/P6 anchor。

---

## 7. Visual Trigger Matrix

Visual 不能由“Codex感觉不确定”单独触发。

必须存在至少一个 deterministic trigger，或由明确 research request 缺失 fact 触发。

### 7.1 VISUAL_REQUIRED

以下任一成立：

1. validation issue 直接涉及目标 fact/table；
2. required semantic field = UNKNOWN；
3. required semantic field = AMBIGUOUS；
4. structured evidence 对 period/unit/scope/value role 给出冲突；
5. value role 未确认；
6. column/header relationship 未确认；
7. requested metric 在 P6 facts 中缺失；
8. reconciliation / cross-fact consistency 明确异常；
9. RawFact 与 P5 table/header structured context 不一致；
10. P5 table context不足以解释目标值；
11. existing P9 overlay 与新的 current base/evidence state 不兼容；
12. research question要求区分 standalone quarter vs YTD，而 structured context无法证明。

---

### 7.2 VISUAL_RECOMMENDED

以下情况可视觉确认，但不强制：

- document = REVIEW_REQUIRED，但目标 fact 自身 required semantics 已完整；
- warning 与目标 fact无直接关系；
- non-critical descriptive fact；
- report text引用而非 derived calculation。

Codex可以直接使用 structured evidence，但必须保留 provenance。

---

### 7.3 VISUAL_NOT_REQUIRED

满足全部：

- target fact 存在；
- required semantics完整；
- no directly-related REVIEW/FAIL/BLOCKING issue；
- no evidence conflict；
- no requested derived-operation ambiguity；
- no missing-value request；
- no stale/incompatible P9 state。

此时不得为了“多确认一次”默认 render PDF。

目的：

控制视觉成本，并避免同一 durable decision被反复检查。

---

## 8. required semantic fields for research use

当前 Research MCP 不依赖未来完整 Semantic Resolver，但必须按 operation 计算最低 required fields。

至少：

### Raw fact quotation

需要：
- numeric/raw value；
- source evidence。

period/unit 可以未知，但输出必须显式标记未知。

### Period-specific fact assertion

需要：
- value；
- period；
- value role；
- required unit；
- required scope。

### YoY

两个 operand 必须：
- compatible metric meaning；
- subject periods matched as valid comparative periods；
- compatible scope；
- compatible unit/dimension；
- value role = VALUE；
- no conflict。

### Margin

numerator/denominator 必须：
- same period；
- compatible scope；
- compatible unit scale/currency where monetary；
- both reviewer-verified or structured-ready。

### Valuation input

必须至少达到：
- RUN_LOCAL_VERIFIED or durable resolved；
- period/unit/scope/value role complete；
- source provenance complete。

不得使用仅 visually guessed、无法定位 source 的值进入 valuation。

---

## 9. Missing-Fact Locator

仅有 `raw_fact_id` 不足以覆盖“P6根本没抽到目标数据”。

新增：

`ffdf_locate_evidence`

参数：

```json
{
  "document_sha256": "...",
  "query": "研发费用",
  "max_results": 10
}
```

query 是 research locator，不是 canonical metric mapper。

---

## 10. Locate algorithm

只使用现有 trusted artifacts：

```text
P3 FTS
→ sections
→ matching pages
→ P5 tables intersecting matching pages/regions
→ P6 facts where available
→ recommended visual targets
```

返回：

```json
{
  "query": "研发费用",
  "matches": [
    {
      "page_no": 6,
      "section_id": "...",
      "table_ids": ["..."],
      "fact_ids": [],
      "text_excerpt": "...",
      "recommended_visual_target": {
        "type": "TABLE_OR_PAGE",
        "table_id": "...",
        "page_no": 6
      }
    }
  ]
}
```

不得：

- 创建不存在的 RawFact；
- canonicalize query；
- 声称找到的是最终 metric truth。

---

## 11. Locator fallback

如果 P3 FTS 无结果：

返回：

`NO_STRUCTURED_MATCH`

而不是猜 page。

Codex可以在研究层判断：

- 是否扩大同义 query；
- 是否该数据确实未披露。

Research MCP 不自动做 arbitrary synonym search。

未来可由 P10根据运行时研究规范生成多个合法 search terms。

---

## 12. Review Context

`ffdf_get_review_context`

输入可以是：

- raw_fact_id；
- validation issue_id；
- table_id。

至少一个。

返回：

- document validation summary；
- target raw fact if present；
- evidence；
- table；
- related issues；
- semantic gaps；
- recommended visual targets；
- P9 current review state。

它不做 Codex reasoning。

---

## 13. Trusted PDF source mapping

Visual tool caller 不得传 filesystem path。

唯一 identity：

`document_sha256`

内部从 trusted Registry/Catalog 定位 immutable PDF。

render 前必须重新验证：

1. file exists；
2. SHA256 == document_sha256；
3. file size matches registry where available；
4. PDF opens；
5. page count == P3 page count；
6. source identity belongs to current document。

失败：

`RESEARCH_MCP_VISUAL_SOURCE_INVALID`

---

## 14. Catalog / Filing identity

未来 Research MCP catalog 必须支持：

- market；
- company_id；
- ticker；
- filing/report class；
- fiscal_year；
- raw_fiscal_period；
- document_sha256；
- artifact dirs；
- trusted source document reference。

不得继续只用：

`market + ticker + fiscal_year + filing_type`

区分季度/半年/年度 filing。

Document SHA 是具体文件 identity，不是业务 slot 本身。

---

## 15. PDF render source

必须：

```text
immutable original PDF
→ PyMuPDF render
→ MCP ImageContent
```

禁止：

```text
P3 text
→ re-layout
→ image
```

因为视觉 fallback 的价值就是恢复 parser 可能丢失的：

- multi-level headers；
- merged cells；
- unit/title location；
- x/y alignment；
- continuation layout。

---

## 16. render_page

参数：

```json
{
  "document_sha256": "...",
  "page_no": 1,
  "detail": "NORMAL"
}
```

detail：

- `NORMAL`
- `HIGH_DETAIL`

默认 NORMAL。

NORMAL 初始：

- target ~160 DPI；
- max dimension ~2200 px。

HIGH_DETAIL：

- higher DPI；
- 不允许无限扩大；
- 如果 full-page 超过 payload/detail policy，自动进入 deterministic tiling。

---

## 17. render_table

参数：

```json
{
  "document_sha256": "...",
  "table_id": "...",
  "mode": "TABLE_WITH_HEADER",
  "detail": "NORMAL"
}
```

mode：

- TABLE_ONLY；
- TABLE_WITH_HEADER；
- TABLE_WITH_SURROUNDING_CONTEXT。

默认：

`TABLE_WITH_HEADER`

---

## 18. Table crop policy

P5 bbox 只是定位 hint，不是最终真源。

### TABLE_ONLY

clip = table bbox + deterministic small margin。

### TABLE_WITH_HEADER

向上扩展 deterministic context window：

- enough to include likely table title/header/unit line；
- no arbitrary caller bbox。

### TABLE_WITH_SURROUNDING_CONTEXT

扩大到更多 section/table context，但仍限制在 current physical page。

---

## 19. P5 bbox failure fallback

若出现：

- header明显被 crop；
- table bbox不包含目标 value；
- target row不在 crop；
- visual与 structured table显著不一致；

Codex必须升级：

```text
render_table
→ render_page
```

不得继续基于错误 crop 下结论。

这类情况同时产生：

`P5_CONTEXT_DEFECT_CANDIDATE`

供后续 parser improvement review。

---

## 20. render_table_group

跨页核心表必须支持 P5 verified table group。

输入：

```json
{
  "document_sha256": "...",
  "table_group_id": "...",
  "detail": "NORMAL"
}
```

返回 group member pages/crops in page order。

每个 image metadata：

- table_id；
- page_no；
- clip_bbox；
- visual_ref_id；
- render_sha256。

如果 P5 没有 verified group：

不得自行猜跨页组。

fallback：

`render_page(page_no)`

必要时 Codex根据已有 section/table evidence显式请求相邻合法 page。

---

## 21. Adjacent page fallback

只有以下情况允许建议 adjacent page：

- current table位于 page bottom；
- P5 group存在；
- section continuation signal；
- target header/unit疑似在前一页/下一页；
- Codex当前研究明确需要 continuation context。

Research MCP 可以返回：

`recommended_adjacent_pages`

但不会自动扫描整份 PDF。

---

## 22. High-detail / tiling

固定 2200 px 不能成为绝对信息损失点。

对：

- landscape wide table；
- >N value columns；
- estimated glyph size too small；
- very dense annual report table；

允许 deterministic tile mode。

Tile contract：

- caller不能指定 arbitrary crop；
- system基于 trusted table/page geometry deterministic切片；
- overlap 固定；
- tile order 固定；
- 每 tile 独立 VisualRef；
- metadata包含 parent page/table identity。

例如：

```text
wide table
→ tile 1 left
→ tile 2 center overlap
→ tile 3 right overlap
```

---

## 23. VisualRef

```text
visual_ref_id =
SHA256(
  document_sha256
  + "\0" + page_no
  + "\0" + normalized clip bbox
  + "\0" + detail/render profile
  + "\0" + tile identity
  + "\0" + renderer version
)
```

另外：

`render_sha256 = SHA256(PNG bytes)`

Visual evidence 可重建和审计。

---

## 24. Image persistence

默认：

```text
PDF
→ in-memory pixmap
→ PNG bytes
→ MCP image response
```

不写 screenshot cache。

未来若需要 cache，必须 content-addressed 且单独设计。

---

## 25. Resolved Query

Codex/Luna 不应直接解释或读取 P9 resolution store 文件。

Research MCP 必须通过 accepted P9 public APIs / validated materialized snapshot 提供统一 resolved query。

新增：

- `ffdf_get_review_state`
- `ffdf_get_resolved_fact`
- `ffdf_list_resolved_facts`

内部只调用 validated P9 APIs / materialized snapshot。

不得重新实现 supersession/active-set semantics。

---

## 26. get_review_state

返回至少：

```json
{
  "document_sha256": "...",
  "has_review_overlay": true,
  "active_resolution_count": 2,
  "active_resolution_ids": ["..."],
  "overlay_set_hash": "...",
  "snapshot_available": true,
  "base_validation_status": "REVIEW_REQUIRED",
  "resolved_validation_status": "REVIEW_REQUIRED",
  "resolved_reuse_eligible": false
}
```

---

## 27. get_resolved_fact

返回 raw 与 effective 分离：

```json
{
  "raw_fact_id": "...",
  "raw": {
    "metric_name": "...",
    "value": "...",
    "period": null,
    "unit": null,
    "scope": null
  },
  "effective": {
    "period": "2026Q3",
    "unit": "CNY",
    "scope": null
  },
  "review": {
    "applied": true,
    "resolution_ids": ["..."],
    "overlay_set_hash": "..."
  }
}
```

Raw 永远保留。

---

## 28. Corrupt P9 state

若已发现 review store，但 P9 validation失败：

`RESEARCH_MCP_RESOLVED_STORE_INVALID`

禁止：

```text
P9 corrupt
→ silent fallback raw
→ pretend no overlay
```

因为这会隐藏已存在但损坏的 reviewed state。

### 28.1 Prepare / submit / materialize 的 side-effect 边界

三个 write-through tool 都必须明确标记为 mutation tool，并且 caller 必须显式调用。

禁止：

```text
get_review_state
→ implicit prepare
→ implicit submit
→ implicit materialize
```

读操作不得产生 durable state。

允许且推荐：

```text
get_review_state
→ explicit prepare if needed
→ explicit submit one supported decision
→ explicit materialize
→ get_review_state verify
```

### 28.2 P9 evidence 与 visual evidence 的关系

当前 P9 v1 支持的 durable evidence 仍是 accepted P5/P6 evidence contract。

PDF visual 的作用是：

> 帮助 reviewer 判断 P5/P6 evidence 的正确语义。

PDF visual **不是**当前 P9 v1 的直接 durable evidence type。

因此：

- visual 清楚 + 存在合法 P5/P6 anchor → `EXPLICIT_AND_ANCHORABLE`，可按 P9 submit；
- visual 清楚 + 没有合法 P5/P6 anchor → `EXPLICIT_VISUAL_ONLY`，当前不得 durable submit；
- visual 证明 raw numeric extraction 错误 → `RAW_EXTRACTION_DEFECT`，不得用 P9 覆盖数值。

### 28.3 同一页面多 Task 的 token 优化

QUALITY_REVIEW 必须先按以下 identity 聚合：

`document_sha256 + table_id/page_no`

同一 table/page 上多个 Review Task：

- 先一次读取 structured context；
- 必要时一次 render；
- 同一 VisualRef 在当前 run 内复用；
- 每个 durable resolution 仍必须分别满足自己的 P9 target/evidence contract。

禁止为了每个 fact 重复渲染同一页面。

### 28.4 Visual escalation order

固定顺序：

```text
structured evidence
→ render_table NORMAL
→ render_table HIGH_DETAIL when needed
→ render_table_group when verified group exists
→ render_page NORMAL
→ render_page HIGH_DETAIL / deterministic tiles
```

只有明确需要上下文时才升级。

不得：

- 先全页后表格；
- 自动浏览整份 PDF；
- 自动前后翻页直到“找到答案”；
- 为 clean/resolved fact 重复截图。

### 28.5 QUALITY_REVIEW completion contract

指定公司/期间的质量完善任务完成时必须输出按 document 的结果：

- `document_sha256`
- report period identity
- initial quality_state
- final quality_state
- task_count
- resolved_count
- unresolved_count
- unsupported_count
- visual_call_count
- rendered_unique_page_count
- submitted_resolution_ids
- parser_defect_candidate_count
- missing_fact_candidate_count

只有所有目标 document 均为：

- `COMPLETE_BASE`，或
- `COMPLETE_REVIEWED`

才能把本次指定范围标记为：

`QUALITY_REVIEW_COMPLETE`

任何 `NEEDS_REVIEW / NEEDS_UPSTREAM_FIX / BLOCKED / INVALID_REVIEW_STATE` 都必须显式保留，不得以“Luna 已检查”代替完成状态。

---

## 29. Codex Visual Decision Classes

只允许四类：

### EXPLICIT_AND_ANCHORABLE

视觉结论明确，且可以回链到 P5/P6 authoritative evidence。

允许：

- current research use；
- 按当前 P9 contract提交 durable semantic resolution。

---

### EXPLICIT_VISUAL_ONLY

PDF视觉明确，但 structured P5/P6 evidence 无法形成当前 P9 anchor。

允许：

- current research use；
- RUN_LOCAL_VERIFIED。

当前 P9 v1：

- 不允许 durable submit；
- canonical reuse false。

---

### RAW_EXTRACTION_DEFECT

视觉证明 P5/P6 raw extraction错误。

处理：

```text
STOP overlay
→ parser defect
→ Design-First fix
→ rerun P5/P6/P7
```

禁止用 P9把错误 raw numeric value“修好”。

---

### AMBIGUOUS

视觉仍无法唯一解释。

保持：

- unresolved；
- REVIEW_REQUIRED。

不得猜。

---

## 30. Visual evidence != truth

正式定义：

```text
PDF Visual Source = authoritative source evidence
Codex interpretation = reviewer decision
```

即使视觉看起来清晰，也不能把“模型看到了”自动等同 deterministic parser truth。

---

## 31. Run-local Visual Fact

对于 `EXPLICIT_VISUAL_ONLY`：

```json
{
  "research_run_id": "...",
  "decision_class": "EXPLICIT_VISUAL_ONLY",
  "document_sha256": "...",
  "raw_fact_id": "...",
  "effective_period": "...",
  "effective_unit": "...",
  "effective_scope": "...",
  "effective_value_role": "...",
  "visual_ref_ids": ["..."],
  "usability": "RUN_LOCAL_VERIFIED",
  "durable": false,
  "canonical_reuse_eligible": false
}
```

---

## 32. RUN_LOCAL_VERIFIED 边界

允许：

- 当前报告中的事实陈述；
- 当前 research run 的必要计算；
- YoY / margin / other derived result，**仅当所有 operands 均满足 DERIVED_USE_READY**；
- 当前估值输入，若所有必要 semantic/provenance 条件满足并显式记录为 run-local。

不允许：

- 注册为 reusable parsed data；
- 下次研究无条件复用；
- 覆盖 P6 raw；
- 自动升级为 canonical metric；
- 省略 provenance。

---

## 33. DERIVED_USE_READY

一个 operand 只有在以下全部满足时才可进入 current-run derived calculation：

1. numeric value verified；
2. period verified；
3. value_role verified；
4. required unit/dimension verified；
5. required scope verified；
6. no unresolved conflict；
7. source provenance exists；
8. 若来源为 visual-only，至少一个 VisualRef + document SHA + page identity；
9. operation-specific compatibility checks PASS。

---

## 34. Operation-specific gates

### YoY

必须：
- same semantic metric；
- correct comparative period；
- same/compatible scope；
- same dimension；
- compatible currency/scale where monetary。

### Margin

必须：
- same period；
- compatible scope；
- compatible monetary basis。

### QoQ

不得把：
- YTD 与 standalone quarter；

直接相除或比较。

### TTM

必须来自：
- 四个 compatible quarter facts；
- 或明确可证明的 duration decomposition。

### Valuation

run-local visual verified 输入可以参与当前估值，但：
- 必须在 research provenance 中标记；
- 不得因此成为 canonical reusable data。

---

## 35. Missing fact + Visual-only

如果 `ffdf_locate_evidence` 找到 PDF 中目标数据，但 P6 没有 RawFact：

decision 可是：

`EXPLICIT_VISUAL_ONLY`

此时 raw_fact_id 可以为空，必须保存：

- document SHA；
- page；
- table/section if available；
- visual refs；
- literal observed text/value；
- current-run interpretation。

它不能提交当前 P9 v1 FACT_FIELD resolution，因为没有合法 raw target。

同时产生：

`P6_MISSING_FACT_CANDIDATE`

用于 parser improvement。

---

## 36. Future PDF_VISUAL_EVIDENCE in P9

长期可以新增 P9 evidence type：

`PDF_VISUAL_EVIDENCE`

要求：

- document_sha256；
- page_no；
- deterministic render profile；
- clip/tile identity；
- renderer version；
- render_sha256；
- visual_ref_id。

但当前 P9 v1 closeout 前不得实现。

必须后续 Design Amendment。

默认只允许支持 semantic overlay。

不得轻易允许改变 raw numeric value。

---

## 37. Long-term correction loop

每次 visual decision 可记录：

- trigger reason；
- structured gap type；
- visual result class；
- related table/header pattern；
- parser defect candidate；
- rule candidate fingerprint。

周期性治理：

```text
many repeated visual decisions
→ cluster recurring pattern
→ design review
→ Semantic Resolver rule candidate
→ Golden
→ implementation
→ acceptance
```

Codex decision 本身不自动训练/修改 production rule。

---

## 38. Visual trigger telemetry

为长期优化记录：

- visual_calls_per_document；
- trigger reason counts；
- render_table vs page vs group；
- repeated same-pattern count；
- decision classes；
- percentage resolved without visual；
- percentage visual-only；
- parser defect candidates；
- ambiguous rate。

这些是工程指标，不是 correctness proof。

---

## 39. 002371 Q3 Golden

Document：

- ticker: 002371；
- source: CNINFO；
- source_id: 1225641389；
- SHA256: `a0f8d84ab724f7c62b690d6504215602a623fc185c53c9e1079cd40653c600b9`。

第一页 KPI table：

Codex 必须能够通过：

```text
Raw facts
→ review context
→ render table/header
```

识别：

```text
本报告期
本报告期比上年同期增减
年初至报告期末
年初至报告期末比上年同期增减
```

并区分：

```text
11,305,675,488.89 → current-quarter VALUE
1.31%              → current-quarter YOY_PERCENT
31,467,092,379.45 → YTD VALUE
15.26%             → YTD YOY_PERCENT
```

不能把四列当成同一种金额。

---

## 40. Missing-Fact Golden

必须增加至少一个 fixture：

- 原 PDF 存在目标披露；
- P3 FTS 能定位；
- P6 没有对应 RawFact。

验证：

```text
research asks metric
→ list_raw_facts misses
→ locate_evidence
→ recommended table/page
→ render
→ run-local visual decision
→ P6 missing-fact candidate
```

---

## 41. Cross-page Golden

必须覆盖：

- table group 2+ pages；
- page 2 missing full header；
- render_table_group returns ordered evidence；
- Codex can inspect inherited visual context；
- no group → no guessed group；
- page fallback works。

---

## 42. Dense-table Golden

至少一个：

- landscape；
- small font；
- >8 value columns。

验证：

NORMAL不足时可以 deterministic HIGH_DETAIL/tile。

不能因为 max-dimension压缩导致 acceptance无法读。

---

## 43. Security

禁止工具：

- read_file(path)；
- render_file(path)；
- arbitrary crop/bbox；
- list_directory；
- sqlite_query；
- shell；
- execute_python。

Caller 只能使用 domain identity：

- market / ticker / fiscal year（仅用于 P8 document discovery）；
- document_sha256；
- raw_fact_id；
- issue_id / review_task_id；
- table_id；
- table_group_id；
- page_no；
- locator query。

特别禁止：

- direct SQLite/SQL；
- arbitrary project path；
- raw-store path；
- review_dir path；
- snapshot path；
- resolution-store file path。

Research MCP 内部通过 trusted catalog + accepted P9 root identity 完成映射。

---

## 44. Determinism

相同：

- PDF；
- artifact state；
- render args/profile；
- P9 state；

必须：

- same VisualRef；
- same render bytes/hash for same pinned renderer/runtime；
- same review state；
- same ResolvedFact response；
- same locator ordering。

Codex interpretation本身不是 deterministic artifact，因此不能纳入 FFDF deterministic equality claim。

---

## 45. Renderer/runtime pin

Visual acceptance 必须冻结：

- PyMuPDF exact version；
- Python runtime；
- render profile；
- output format；
- color/alpha policy；
- DPI/tiling algorithm。

Renderer升级会改变 render hash，必须形成新的 renderer version。

---

## 46. Performance gates

初始：

- get_review_state warm <= 2s；
- get_resolved_fact warm <= 3s；
- locate_evidence warm <= 3s；
- get_review_context warm <= 3s；
- render_table NORMAL <= 3s；
- render_page NORMAL <= 5s；
- render_table_group representative 2-page <= 6s；
- HIGH_DETAIL/tile单页 <= 8s。

不包含 Codex推理时间。

---

## 47. Error codes

至少：

```text
RESEARCH_MCP_DOCUMENT_NOT_FOUND
RESEARCH_MCP_FACT_NOT_FOUND
RESEARCH_MCP_ISSUE_NOT_FOUND
RESEARCH_MCP_TABLE_NOT_FOUND
RESEARCH_MCP_TABLE_GROUP_NOT_FOUND
RESEARCH_MCP_PAGE_INVALID
RESEARCH_MCP_VISUAL_SOURCE_INVALID
RESEARCH_MCP_RENDER_FAILED
RESEARCH_MCP_PAYLOAD_LIMIT
RESEARCH_MCP_REVIEW_STATE_INVALID
RESEARCH_MCP_RESOLVED_STORE_INVALID
RESEARCH_MCP_RESOLVED_FACT_NOT_FOUND
RESEARCH_MCP_LOCATOR_NO_MATCH
```

不得输出普通 client Python traceback。

---

## 48. Immutability

Research MCP 调用前后必须证明：

- source PDF unchanged；
- P3 unchanged；
- P5 unchanged；
- P6 unchanged；
- P7 unchanged；
- Registry unchanged；
- P9 store unchanged unless caller explicitly执行 `ffdf_prepare_review_overlay` / `ffdf_submit_review_resolution` / `ffdf_materialize_resolved_view`。

所有 query/render tool 永远 read-only。

write-through tool 只能改变 P9 overlay/snapshot；不得改变 source/P3/P5/P6/P7/Registry。

---

## 49. Tests — Visual Trigger Matrix

至少：

1. null period → required；
2. null unit where required → required；
3. unrelated warning → not required；
4. target-related review issue → required；
5. conflicting period evidence → required；
6. complete clean resolved fact → not required；
7. requested missing metric → required locator path；
8. reconciliation inconsistency → required；
9. YTD/Q3 ambiguity → required；
10. existing durable reviewed resolution → no repeated visual by default。

---

## 50. Tests — Locator

至少：

1. FTS hit + table；
2. FTS hit no table；
3. multiple pages deterministic order；
4. no match；
5. query limits；
6. no arbitrary path；
7. no fabricated fact；
8. missing-fact golden。

---

## 51. Tests — Render

至少：

1. registered immutable PDF only；
2. SHA mismatch blocked；
3. page bounds；
4. table belongs document；
5. deterministic table crop；
6. header context；
7. P5 bbox-failure page fallback；
8. table-group ordering；
9. no guessed group；
10. HIGH_DETAIL；
11. deterministic tiling；
12. VisualRef stable；
13. PNG hash stable under frozen runtime；
14. no screenshot file persisted；
15. source/upstream immutable；
16. 002371 live visual golden。

---

## 52. Tests — Resolved Query / Quality State / Write-Through

至少：

1. no P9 overlay + P7 PASS → COMPLETE_BASE；
2. no P9 overlay + P7 REVIEW_REQUIRED + supported task → NEEDS_REVIEW；
3. period overlay；
4. unit overlay；
5. scope overlay；
6. multiple compatible overlays；
7. superseded excluded；
8. corrupt store → INVALID_REVIEW_STATE and blocks；
9. raw unchanged；
10. provenance returned；
11. resolved REVIEW_REQUIRED；
12. resolved PASS + reuse eligible → COMPLETE_REVIEWED；
13. Registry not mutated；
14. P8 raw tools unchanged；
15. existing durable overlay avoids repeat visual；
16. prepare is explicit and idempotent for same accepted base；
17. submit rejects stale expected overlay hash；
18. submit rejects unsupported action；
19. submit rejects raw numeric replacement；
20. submit uses accepted P9 evidence validation；
21. materialize after submit returns new overlay identity；
22. final get_review_state sees the materialized state；
23. read tools do not implicitly prepare/submit/materialize；
24. same-page multiple tasks reuse one rendered VisualRef in-run；
25. unsupported task maps to NEEDS_UPSTREAM_FIX rather than model guessing.

---

## 53. Tests — Run-local / Derived Use

至少：

1. visual-only fact quotation；
2. visual-only complete fact → RUN_LOCAL_VERIFIED；
3. missing period → not DERIVED_USE_READY；
4. YoY compatible operands；
5. YoY incompatible period blocked；
6. margin scope mismatch blocked；
7. valuation run-local allowed with provenance；
8. run-local never Registry reusable；
9. next run does not treat run-local as durable；
10. durable P9 state is reused next run。

---

## 54. Implementation gates

### R-A — Future Design Baseline

design/28 + design/29 v2 可以作为 reference design 冻结。

**本次 design 更新仍不授权 production implementation。R-B 及以后保持 CLOSED，直到 design-owner 以新 baseline 明确授权。**

### R-B — Trusted Source & Period-aware Identity

- raw PDF mapping；
- filing period identity；
- path security；
- SHA/page validation；
- no direct DB / SQL / arbitrary filesystem surface。

### R-C — Resolved Query + Quality State

先实现：

- `ffdf_get_review_state`；
- `ffdf_get_resolved_fact`；
- `ffdf_list_resolved_facts`；
- deterministic quality_state projection。

理由：已有 P9 durable result 必须最优先复用，避免任何重复 visual。

### R-D — Controlled P9 Write-Through

实现：

- `ffdf_prepare_review_overlay`；
- `ffdf_list_review_tasks`；
- `ffdf_submit_review_resolution`；
- `ffdf_materialize_resolved_view`；
- stale-state / optimistic-concurrency gate；
- accepted P9 semantics only。

先证明 structured-only review 可以完整闭环，再引入 visual。

### R-E — Visual Trigger Matrix

实现 deterministic trigger evaluator。

### R-F — Missing-Fact Locator

实现 P3/P5 locator。

### R-G — Visual Renderer

实现 page/table/group + NORMAL/HIGH_DETAIL/tiling + in-run dedupe。

### R-H — Visual Decision / Run-local Policy

验证四类 decision、derived-use gates、P9 anchor rule。

### R-I — 002371 Q3 Golden

验证 Q3 KPI visual fallback。

### R-J — QUALITY_REVIEW End-to-End Golden

至少覆盖：

```text
P7 REVIEW_REQUIRED
→ prepare
→ list unresolved supported task
→ structured/visual review
→ submit P9
→ materialize
→ get_review_state
→ COMPLETE_REVIEWED
→ next run no repeated visual
```

### R-K — Existing P9 Reuse Golden

已有 durable submit 的 document 必须直接 Resolved Query，不截图。

### R-L — Diverse CN/HK Golden

覆盖：

- cross-page；
- dense table；
- missing fact；
- raw extraction defect；
- ambiguous；
- unsupported task；
- same-page multi-task visual dedupe。

### R-M — Formal Code Review

review exact candidate。

### R-N — Acceptance Freeze

冻结 renderer/runtime/catalog/P9 wrapper contract/fixtures。

### R-O — Independent Acceptance

Research MCP Independent Acceptance PASS 后，才允许：

- additive 接入已验收 P10 integration contract；
- 把 capability manifest 中 `PDF_VISUAL_EVIDENCE` 从 UNAVAILABLE 升级为 AVAILABLE；
- 对外启用 P9 Review Write-Through MCP tools。

P10 core live research不以 R-O 为前置；在 R-O 之前 visual-required case 必须显式返回 capability gap。

---

## 55. design/28 / design/29 implementation order

明确顺序：

```text
P10 core accepted P8/P9 dynamic integration
       ↓
structured-sufficient research immediately usable
       ↓
explicit P10_VISUAL_CAPABILITY_REQUIRED where visual is truly needed
       ↓
separate Research MCP authorization / implementation / acceptance
       ↓
visual capability becomes additive to P10
       ↓
collect reviewed visual patterns
       ↓
separate Semantic Resolver authorization
```

因此：

- design/29 v2 = **未来 additive visual / resolved-query / controlled P9 write-through capability**；
- QUALITY_REVIEW = **数据库完善运行模式**；
- RESEARCH_FALLBACK = **研究期视觉回退模式**；
- design/28 = **未来 deterministic semantic automation architecture**；
- P10 v1 = **当前 accepted P8/P9 structured integration**。

---

## 56. Acceptance criteria

至少证明：

1. P8 v1 exact 11 tools unchanged；
2. P9 public semantics / action enum unchanged；
3. source/P3/P5/P6/P7/Registry immutable；
4. Codex/Luna 无 direct DB / SQL / artifact path access；
5. quality_state 由 P7/P9 validated state deterministic 派生；
6. COMPLETE_BASE 不创建 P9 overlay、不看图；
7. COMPLETE_REVIEWED 后续 run 不重复 visual；
8. NEEDS_REVIEW 只枚举 unresolved + SUPPORTED tasks；
9. UNSUPPORTED task 不交给模型猜测并映射 NEEDS_UPSTREAM_FIX；
10. prepare/submit/materialize 都是显式 mutation；
11. read/render tool 绝不产生 durable mutation；
12. stale expected overlay / base identity 阻断 submit；
13. submit 只能接受 P9 当前 5 类 action；
14. submit 不接受 raw numeric/raw metric correction；
15. materialize 后必须 re-query 才能宣布 COMPLETE_REVIEWED；
16. REVIEW_REQUIRED 仍可按规则继续 research；
17. Visual Trigger Matrix deterministic；
18. complete clean fact不会无理由看图；
19. same table/page 多 task 不重复 render；
20. missing fact可通过 locator找到候选 evidence；
21. table crop错误可以升级 page；
22. cross-page group可视觉检查；
23. dense table可 HIGH_DETAIL/tile；
24. PDF image来自 immutable source；
25. VisualRef可审计；
26. visual source 与 Codex/Luna decision明确分层；
27. EXPLICIT_AND_ANCHORABLE只有在合法 P5/P6 anchor 下可进入 P9；
28. EXPLICIT_VISUAL_ONLY只能 run-local；
29. RAW_EXTRACTION_DEFECT不能被 P9掩盖；
30. AMBIGUOUS保持 unresolved；
31. RUN_LOCAL_VERIFIED边界明确；
32. DERIVED_USE_READY operation gate生效；
33. run-local数据不进入 Registry reuse；
34. corrupt P9不能 silent fallback；
35. recurring pattern只形成 rule/parser candidate，不自动改 production；
36. 002371 Q3 golden PASS；
37. QUALITY_REVIEW end-to-end golden PASS；
38. missing-fact / cross-page / dense-table / defect / ambiguous golden PASS。

---

## 57. Issue rule

发现设计或实现问题：

```text
STOP
→ facts/root cause
→ update design/28 or design/29
→ commit/push design baseline
→ assess invalidated gates
→ implementation
→ rerun
```

禁止 code-first/design-later。

---

## 58. Exit

本 v2 reference design **仍不授权 implementation**。

下一步必须是 design-owner 对本 v2 baseline 的明确授权，之后才允许进入 R-B。

只有未来单独满足：

- Research MCP production authorization；
- exact implementation plan；
- R-B ～ R-N 全部 gate PASS；
- Formal Code Review PASS；
- Acceptance Freeze；
- Independent Acceptance PASS；

之后：

1. Research MCP Extension 才可把 P10 capability manifest 中 `PDF_VISUAL_EVIDENCE` 从 UNAVAILABLE 改为 AVAILABLE；
2. 才可对 Codex 暴露 `ffdf_prepare_review_overlay` / `ffdf_submit_review_resolution` / `ffdf_materialize_resolved_view`；
3. 才可把 QUALITY_REVIEW 作为正式“入库后 Luna 完善数据库”工作流；
4. 才根据最终 accepted tool schemas 编写 Codex + Luna production Prompt。

P10 始终负责：

- 当前研究规范读取；
- 信息需求规划；
- accepted capability选择；
- Codex reasoning；
- run-local decisions；
- final research output。

Research MCP 始终负责：

- accepted P8/P9 capability 的安全投影；
- resolved-first query；
- deterministic visual trigger / locator / renderer；
- controlled P9 write-through；
- quality-state verification。

Research MCP 不成为研究业务规则真源；Luna 也不成为数据库真源。数据库可复用状态仍由 accepted P7/P9 deterministic artifacts 决定。
