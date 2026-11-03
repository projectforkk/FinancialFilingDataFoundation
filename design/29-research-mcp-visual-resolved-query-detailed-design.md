# 29 — Research MCP Visual Evidence & Resolved Query 详细设计

状态：**ACTIVE PROPOSED DETAILED DESIGN**

依赖：
- P8 Local MCP = DONE；
- P9 v1 Durable Review Overlay = acceptance in progress；
- design/28 = architecture baseline；
- P10 = future Codex Dynamic Research Integration。

本设计解决：

> 当结构化数据不完整、不准确或根本缺失时，Codex 如何继续完成当前研究，并在安全边界内复用已有 reviewed result。

本设计不声称让 FFDF parser 自动完全正确。

---

## 1. 目标

新增 additive Research MCP Extension，使 Codex 可以：

1. 查询 P8 RawFact / Evidence / Table / Validation；
2. 查询 P9 是否已有 durable reviewed overlay；
3. 优先消费 Resolved View，避免重复 visual review；
4. 在 structured evidence 不足时定位原始 PDF 位置；
5. 获取原始 PDF table/page visual evidence；
6. 对当前研究做 reviewer decision；
7. 明确区分 run-local verified 与 durable/canonical reusable；
8. 在真正满足 P9 evidence contract 时选择性提交 P9；
9. 将 recurring visual-review patterns 反馈为后续 Semantic Resolver rule candidate。

---

## 2. 非目标

本层不：

- 修改 P8 v1 现有 11 tools；
- 修改 RawFact；
- OCR；
- arbitrary file read；
- arbitrary bbox screenshot；
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

```text
Locate document
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
        ├─ YES → research
        └─ NO
             ↓
       Review Context / Locate Evidence
             ↓
       render_table
             ↓
       context complete?
        ├─ YES → Codex reviewer decision
        └─ NO
             ↓
       render_table_group / render_page
             ↓
       still ambiguous?
        ├─ YES → remain REVIEW_REQUIRED
        └─ NO  → run-local verified or P9 durable submit
```

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

## 6. 新增 tool surface

建议新增 8 个工具：

1. `ffdf_get_review_state`
2. `ffdf_get_resolved_fact`
3. `ffdf_list_resolved_facts`
4. `ffdf_get_review_context`
5. `ffdf_locate_evidence`
6. `ffdf_render_table`
7. `ffdf_render_table_group`
8. `ffdf_render_page`

如果实现时 MCP SDK 对 image/list-image response 有协议限制，必须先更新设计，不得静默改成 arbitrary file path 返回。

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

Codex 不应直接解释 P9 resolution store。

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

- document_sha256；
- raw_fact_id；
- issue_id；
- table_id；
- table_group_id；
- page_no；
- locator query。

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
- P9 store unchanged unless caller explicitly执行 authorized P9 submit。

render tool 永远 read-only。

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

## 52. Tests — Resolved Query

至少：

1. no P9 overlay → raw/effective equivalent；
2. period overlay；
3. unit overlay；
4. scope overlay；
5. multiple compatible overlays；
6. superseded excluded；
7. corrupt store blocks；
8. raw unchanged；
9. provenance returned；
10. deterministic response；
11. resolved REVIEW_REQUIRED；
12. resolved PASS；
13. Registry not mutated；
14. P8 raw tools unchanged；
15. existing overlay avoids repeat visual.

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

### R-A — Design Baseline

Freeze design/28 + design/29。

### R-B — Trusted Source & Period-aware Catalog

- raw PDF mapping；
- filing period identity；
- path security；
- SHA/page validation。

### R-C — Resolved Query

先实现：
- review state；
- resolved fact/list。

理由：已有 P9 result 应最优先避免重复 visual。

### R-D — Visual Trigger Matrix

实现 deterministic trigger evaluator。

### R-E — Missing-Fact Locator

实现 P3/P5 locator。

### R-F — Visual Renderer

实现 page/table/group + NORMAL/HIGH_DETAIL/tiling。

### R-G — 002371 Golden

验证 Q3 KPI visual fallback。

### R-H — Run-local Decision Policy

验证 derived-use gates。

### R-I — Existing P9 Reuse Golden

第一次 durable submit后，下一 run直接 Resolved Query，不再截图。

### R-J — Diverse CN/HK Golden

覆盖 cross-page/dense/missing fact。

### R-K — Code Review

review exact candidate。

### R-L — Acceptance Freeze

冻结 renderer/runtime/catalog/fixtures。

### R-M — Independent Acceptance

PASS后才授权接入 P10 live research。

---

## 55. design/28 / design/29 implementation order

明确顺序：

```text
design/28 architecture approved
+
design/29 detailed fallback approved
       ↓
implement design/29 first
       ↓
Codex research immediately usable
       ↓
collect visual-review patterns
       ↓
implement design/28 semantic resolver
       ↓
reduce recurring visual fallback
```

因此两条路线并存：

- design/29 = **现在能用**；
- design/28 = **未来越来越自动**。

---

## 56. Acceptance criteria

至少证明：

1. P8 v1 11 tools unchanged；
2. source/P3/P5/P6/P7 immutable；
3. REVIEW_REQUIRED 可继续 research；
4. Visual Trigger Matrix deterministic；
5. complete clean fact不会无理由看图；
6. missing fact可通过 locator找到候选 evidence；
7. table crop错误可以升级 page；
8. cross-page group可视觉检查；
9. dense table可 HIGH_DETAIL/tile；
10. PDF image来自 immutable source；
11. VisualRef可审计；
12. visual source 与 Codex decision明确分层；
13. EXPLICIT_AND_ANCHORABLE可进入 P9；
14. EXPLICIT_VISUAL_ONLY只能 run-local；
15. RAW_EXTRACTION_DEFECT不能被 P9掩盖；
16. AMBIGUOUS保持 unresolved；
17. RUN_LOCAL_VERIFIED边界明确；
18. DERIVED_USE_READY operation gate生效；
19. run-local数据不进入 Registry reuse；
20. durable P9 result下次自动通过 Resolved Query获取；
21. corrupt P9不能 silent fallback；
22. recurring pattern只形成 rule candidate，不自动改 parser；
23. 002371 Q3 golden PASS；
24. missing-fact / cross-page / dense-table golden PASS。

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

Independent Acceptance PASS 后，Research MCP Extension 可供 P10 使用。

P10 负责：

- 当前研究规范读取；
- 信息需求规划；
- P8/Resolved Query/Visual tool选择；
- Codex reasoning；
- run-local decisions；
- optional P9 durable submit；
- 最终研究报告。

Research MCP 不成为研究业务规则真源。
