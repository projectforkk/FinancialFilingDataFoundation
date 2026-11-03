# 10 — P4 Table Candidate Detection 详细设计

状态：**DESIGN BASELINE — P4**

阶段：**P4 — Table Candidate Detection**

前置：

- P0 / P1 / P2 / P3 = DONE / PASS
- accepted baseline: `b3b0b2eea983a26345453431fb08f6e5ba2c3d80`
- P3 artifact schema: `p3-native-document-v1`

---

## 1. P4 目标

P4 在**不重新打开 PDF、不执行 OCR、不执行 Docling、不调用网络/AI**的前提下，仅使用 P3 已验收 artifacts：

- `pages.jsonl`
- `sections.jsonl`
- `document.json`
- `search.sqlite`

检测“值得进入 P5 table reconstruction 的候选区域”。

P4 的输出是：

```text
page / region candidate
+ deterministic signals
+ score
+ source evidence pointers
```

P4 **不是** table parser。

---

## 2. P4 明确不做

P4 不允许：

- cell extraction；
- row/column reconstruction；
- header/body semantic table model；
- merged-cell inference；
- cross-page table stitching；
- accounting fact extraction；
- OCR；
- Docling；
- external AI；
- P5/P6 functionality。

---

## 3. 输入

P4 输入为一个完整、可加载的 P3 `NativeDocumentArtifact`。

必须先调用：

`load_native_document(artifact_dir)`

并验证 P3 artifact 完整性。

P4 不接受：

- 任意孤立 pages.jsonl path；
- 不完整 P3 artifact；
- source SHA 与 artifact identity 不一致的目录。

---

## 4. 输出 Artifact

P4 schema：

`p4-table-candidates-v1`

目录建议：

```text
<candidate_root>/
  <document_sha256>/
    candidates.jsonl
    candidate_manifest.json
```

content-addressed by source document SHA。

P4 parser/detector version：

`p4-table-candidate-v1`

---

## 5. Candidate Contract

每个 candidate 至少：

```json
{
  "candidate_id": "...",
  "document_sha256": "...",
  "page_no": 88,
  "bbox": [x0, y0, x1, y1],
  "block_nos": [3,4,5],
  "line_count": 18,
  "word_count": 126,
  "numeric_token_count": 49,
  "numeric_line_count": 15,
  "column_anchor_count": 5,
  "drawing_count_page": 322,
  "financial_keyword_hits": ["资产", "负债"],
  "signals": [
    "NUMERIC_DENSITY",
    "MULTI_COLUMN_ALIGNMENT",
    "FINANCIAL_KEYWORDS"
  ],
  "score": 8.25,
  "candidate_class": "TABLE_LIKE",
  "quality_signals": []
}
```

---

## 6. Stable Candidate Identity

`candidate_id`：

```text
SHA256(
  document_sha256
  + "\0" + page_no
  + "\0" + normalized_bbox
  + "\0" + sorted(block_nos)
)
```

不得依赖：

- wall clock；
- random UUID；
- filesystem order。

---

## 7. Candidate Region Unit

P4 优先以**连续 block group** 为候选区域。

同一页按 P3 `reading_order_index` 遍历 text blocks。

一个 block 若满足至少一个 table-like line signal，则进入 group candidate seed。

相邻 seed block 可以合并，当：

- vertical gap <= page_height * 0.04；
- horizontal overlap / common column anchors 足够；
- 中间没有明显长段 prose separator。

### 7.1 Distributed-block fallback

P3 实际 HK annual report 证明：复杂财务表可能把同一视觉表格的 row labels / numeric columns 拆成大量独立 text blocks；单个 block 内甚至只有 1 个 numeric token，因此 block-local seed 会漏掉整张表。

P4 允许一个 **page-level distributed-block fallback candidate**，但仍只做 candidate detection，不做 reconstruction。

触发至少满足：

- page numeric_token_count >= 12；
- numeric-bearing block count >= 4；
- page-level repeated numeric x anchor count >= 2；
- 且满足 financial keyword/context 或 numeric_token_count >= 20。

fallback candidate：

- `block_nos` = 参与 numeric evidence 的 blocks；
- bbox = 这些 evidence blocks 的 union bbox；
- signal = `DISTRIBUTED_NUMERIC_BLOCKS`；
- 可叠加 keyword / section / drawing signals；
- 不能输出/推断 cells、rows、columns；
- 若与 block-local candidate 高度重叠，不重复输出更弱 candidate。

P4 只输出 bbox + block references。

不输出 cells。

---

## 8. Numeric Token

P4 使用确定性 numeric-token classifier。

允许识别：

- integers；
- decimals；
- negative via `-` / Unicode minus；
- parenthetical negatives，如 `(1,234)`；
- thousands separators；
- percentages；
- currency-prefixed numbers；
- placeholders `—` / `-` 不单独算 numeric。

文本中年份 `2024` 可算 numeric token，但不能单独触发 table candidate。

---

## 9. Line-level Table Signals

对 P3 line / words 计算：

### 9.1 Numeric Density

```text
numeric_tokens / non_empty_tokens
```

强 signal：

- >= 0.30 且至少 2 个 numeric token

弱 signal：

- >= 0.20 且至少 2 个 numeric token

### 9.2 Multi-column Alignment

基于 word bbox x0 / x1 聚类。

候选 line 需要：

- 至少 3 个 token group；
- 或 text + 2 个分离 numeric group。

跨连续 lines 聚合 anchor。

`column_anchor_count >= 3` 为强 signal。

### 9.3 Spacing / Gap Signal

按 x 方向 token gap，存在至少 2 个显著 gap：

`gap >= max(12pt, median_word_height * 1.5)`

作为弱 table signal。

---

## 10. Financial Keyword Signal

P4 不是语义财务事实抽取，但可以使用轻量词典提高 candidate recall。

CN/HK 中文关键词至少：

- 资产
- 负债
- 权益
- 收入
- 营业
- 利润
- 现金流
- 本期
- 上期
- 期末
- 期初
- 人民币
- 港元
- 合计
- 项目

英文关键词至少：

- assets
- liabilities
- equity
- revenue
- profit
- cash flow
- total
- year ended
- amount

keyword signal 只能加分，不能单独成为 table candidate。

---

## 11. Page Structural Signal

P3 page record 提供：

- drawing_count
- image_count
- word_count
- block_count

P4 可使用：

### Drawing density

`drawing_count >= 20`

弱 signal。

`drawing_count >= 100`

强 signal。

但 drawing_count 只能作为 page-level score，不得虚构 region drawing bbox。

### Text density

极低 word_count + 高 drawing_count 可能是图表/非文本页。

P4 标记：

`NON_TEXT_HEAVY_PAGE`

但默认不输出 text table candidate，除非 text signals 仍满足阈值。

---

## 12. Section Context

若 candidate page 位于 P3 section title 命中：

- 财务报表
- 财务报告
- 合并资产负债表
- 利润表
- 现金流量表
- financial statements
- notes to financial statements

增加 context score。

P4 只能使用 section page range，不修改 section artifact。

---

## 13. Candidate Score

初始 deterministic score：

```text
+3.0  >= 3 numeric lines
+2.0  >= 6 numeric lines
+2.0  column_anchor_count >= 3
+1.0  column_anchor_count >= 5
+1.5  financial keyword hit
+0.5  drawing_count >= 20
+0.5  drawing_count >= 100
+1.0  section context
+0.5  repeated aligned numeric x positions
-2.0  prose-dominant block group
-1.0  TOC-like dotted leader dominance
```

Threshold：

- `score >= 4.0` → TABLE_LIKE
- `2.5 <= score < 4.0` → REVIEW_CANDIDATE
- below 2.5 → 不输出

P4 应偏 recall，不应为了 precision 过早丢弃财务表。

---

## 14. TOC / False-positive Guard

目录页常具有：

- dotted leaders；
- 单个页码 numeric；
- 多行标题 + 单个 numeric。

若多数 candidate lines：

- 每行仅 1 numeric token；
- 且存在大量 `....` / `……`；

标记：

`TOC_LIKE`

并降分。

---

## 15. Page / Region Determinism

相同 P3 artifact 重跑 P4：

- candidate count 相同；
- candidate_id 相同；
- candidates.jsonl byte-for-byte 相同；
- manifest 除 timings 外语义相同。

不得使用 nondeterministic float formatting。

bbox round to 3 decimals。

score round to 3 decimals。

---

## 16. Artifact Reuse / Corruption Guard

若 final candidate artifact 已存在：

必须验证：

- schema_version；
- detector_version；
- document_sha256；
- P3 parser_version；
- P3 artifact identity；
- candidates.jsonl 存在且可完整 JSONL decode；
- candidate `document_sha256` 与 manifest 一致；
- `1 <= page_no <= manifest.page_count`；
- bbox 必须为 4 个 finite number，且 `x1 >= x0 / y1 >= y0`；
- block_nos 必须为 non-empty deterministic integer list；
- loader 必须按 `document_sha256 + page_no + normalized_bbox + sorted(block_nos)` **重新计算 candidate_id 并与存储值精确比较**；
- candidate_id 唯一；
- manifest candidate_count 与 JSONL count 一致。

全部 PASS → reuse。

任一失败：

`P4_ARTIFACT_INCOMPLETE_OR_CORRUPT`

不得 silent overwrite。

---

## 17. Source Immutability

P4 不打开 source PDF。

只读 P3 artifact。

因此必须验证：

- P3 artifact files 不改；
- raw PDF 不改；
- P1/P2 Registry 不改。

---

## 18. Performance Gate

P4 输入是 JSONL，不重新 parse PDF。

代表性 live P3 artifacts：

- CN 600519 FY2024 — 143 pages
- HK 00700 FY2024 — 274 pages

初始 performance gate：

- CN P4 detection <= 5s
- HK P4 detection <= 10s

不包含 P3 parse time。

如果实际远低于 gate，可后续收紧。

---

## 19. Package 结构

建议：

```text
src/financial_filing_data_foundation/
  candidates/
    __init__.py
    models.py
    detector.py
```

P4 不创建 `tables/` reconstruction package。

---

## 20. Public API

```python
detect_table_candidates(
    native_artifact_dir: str | Path,
    candidate_root: str | Path,
) -> TableCandidateArtifact
```

以及：

```python
load_table_candidates(
    artifact_dir: str | Path,
) -> TableCandidateArtifact
```

---

## 21. Tests

至少：

1. numeric token parser；
2. percentage / parenthetical negative；
3. single-year line 不触发；
4. multiple numeric columns触发；
5. multi-column alignment；
6. financial keyword only 不触发；
7. drawing only 不触发；
8. TOC dotted leader降分；
9. candidate id deterministic；
10. bbox deterministic；
11. same input byte-identical candidates；
12. artifact reuse；
13. corrupt manifest rejection；
14. corrupt JSONL rejection；
15. candidate_count mismatch；
16. source P3 artifact unchanged；
17. CN live candidate detection；
18. HK live candidate detection；
19. no PDF open；
20. no OCR/Docling/network/AI。

---

## 22. Live Acceptance Expectations

P4 不要求人工标注所有表，但必须设置代表性 recall guard。

必须至少证明：

CN 600519 FY2024：
- 财务报表相关 pages 有 candidate；
- candidate count > 0；
- repeated run deterministic。

HK 00700 FY2024：
- financial statements / notes 中有 candidate；
- candidate count > 0；
- repeated run deterministic；
- 基于已验收 P3 artifact 的事实页：page 124 `綜合收益表`、page 126 `綜合財務狀況表`、page 133 `綜合現金流量表` 必须命中 candidate，防止 distributed-block layout 回归漏检。

并记录 top candidates 的 page / score / signals 供 P5 review。

---

## 23. Exit Condition

只有 Independent Acceptance PASS：

- P4 → DONE；
- 才允许 P5 Table Reconstruction / Cross-page。

P4 不得提前生成 reconstructed cell/table objects。

---

## 24. Issue Rule

发现问题：

```text
STOP
→ root cause
→ update design
→ commit design baseline
→ rerun affected gates
→ continue
```

禁止 code-first / design-later。
