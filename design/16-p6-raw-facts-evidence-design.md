# 16 — P6 Raw Facts / Evidence 详细设计

状态：**DESIGN BASELINE — P6**

阶段：**P6 — Raw Facts / Evidence**

前置条件：
- P0–P5 = DONE / PASS
- accepted P5 merge = `8ff01cd3feed41c4b81aff88bce6502d50e8f32e`
- project directory consolidation = PASS
- canonical project root = `D:\Codex\FinancialFilingDataFoundation`

---

## 1. P6 目标

P6 将 P5 已验收的 reconstructed structural tables 转换为：

1. **RawFact**：保留原始 metric/value/period/unit/scope；
2. **Evidence**：将每个 raw fact 精确回链到 P5 cell、P3 source words、page/bbox 与 document SHA。

正式追溯链：

```text
RawFact
→ Evidence
→ VALUE Cell + LABEL Cell(s)
→ Row
→ Reconstructed Table
→ P3 Source Words / BBox
→ Physical Page
→ Original Document SHA
→ P2 Source Metadata
```

P6 的职责是“可靠地保存原始事实及证据”，不是做财务语义标准化。

---

## 2. 明确不做

P6 禁止：

- canonical metric mapping；
- account taxonomy normalization；
- 将“营业收入”转换为 `revenue`；
- final fiscal-period standardization；
- YoY / QoQ / TTM；
- 资产=负债+权益等财务勾稽；
- completeness/quality final PASS；
- DATA_READY 判定；
- investment analysis；
- OCR；
- Docling；
- network；
- remote AI；
- Codex review overlay；
- P7 quality policy。

---

## 3. 输入

必须同时提供：

- valid P3 `NativeDocumentArtifact`
- valid P5 `ReconstructedTableArtifact`

要求：

- same `document_sha256`
- P3 artifact loader PASS
- P5 artifact loader PASS
- P5 input fingerprints仍与当前 P3/P4一致

P6 不重新打开 PDF。

---

## 4. Artifact

Schema：

`p6-raw-facts-evidence-v1`

Extractor version：

`p6-raw-fact-extractor-v1`

目录：

```text
<fact_root>/<document_sha256>/
  raw_facts.jsonl
  evidence.jsonl
  fact_manifest.json
```

---

## 5. RawFact Contract

每条：

```json
{
  "raw_fact_id": "...",
  "document_sha256": "...",
  "raw_metric_name": "营业收入",
  "raw_value": "174,144,662,063.32",
  "parsed_numeric_value": "174144662063.32",
  "raw_unit": null,
  "raw_period_label": null,
  "raw_scope": null,
  "table_id": "...",
  "table_group_id": null,
  "page_no": 88,
  "row_id": "...",
  "row_index": 4,
  "column_index": 2,
  "label_cell_ids": ["..."],
  "value_cell_id": "...",
  "evidence_id": "..."
}
```

原则：

- `raw_metric_name` / `raw_value` 保留原文；
- `parsed_numeric_value` 使用 decimal canonical string；
- period/unit/scope 只有存在 deterministic explicit evidence 才填写；
- 不允许凭 filing year、column order、币种习惯猜测。

---

## 6. Fact Eligibility

对每个 P5 table row：

必须同时满足：

1. 至少一个非空 `LABEL` cell；
2. 至少一个 `VALUE` cell；
3. VALUE cell `numeric == true`；
4. value raw text 可被 P6 numeric parser 完整解析；
5. metric raw text 非空。

每个 eligible VALUE cell 生成一条 RawFact。

不生成 fact 的情况：

- 无 LABEL；
- value 非 numeric；
- numeric parse失败；
- cell role = UNASSIGNED；
- empty value。

这些情况不猜测，记录 deterministic warning counter。

---

## 7. Raw Metric Name

同 row 所有非空 LABEL cells：

排序：
1. column_index
2. bbox x0
3. cell_id

以单空格 deterministic join。

只做 whitespace normalization：
- trim
- multiple spaces → single space

不：
- 翻译
- 去会计术语
- canonicalize
- synonym merge

---

## 8. Numeric Parser

使用 `decimal.Decimal`，禁止 float。

支持：

- `123`
- `1,234`
- `1，234`
- `-123.45`
- Unicode minus
- `(1,234.50)`
- `12.5%`
- `￥1,234`
- `¥1,234`
- `$1,234`
- `€1,234`
- `£1,234`

输出：
- raw_value：原字符串
- parsed_numeric_value：canonical Decimal string

示例：

```text
"1,234.00" -> "1234.00"
"(1,234)"  -> "-1234"
"12.5%"    -> "12.5"
```

百分比不自动除以 100。

currency symbol 只用于解析 numeric，不自动成为 `raw_unit`。

占位符：
- `-`
- `—`
- `–`

不视为 numeric fact。

---

## 9. Period Label

P6 只绑定明确 raw period label。

候选 pattern：

中文：
- `2024`
- `2024年`
- `2024年度`
- `本期`
- `上期`
- `本年`
- `上年`
- `期末`
- `期初`

英文：
- `2024`
- `current year`
- `prior year`
- `year ended ...`
- `as at ...`
- `current period`
- `prior period`

### 9.1 Mapping

P5 VALUE cell 已有 `column_index` 与 table `value_column_anchors`。

P6 在当前 fact row 之前的 rows 中搜索 header-like nonnumeric cells：

- text 命中 period pattern；
- cell bbox right/center 与目标 value anchor 最近；
- normalized x distance <= page width * 0.08；
- 选择最近的 preceding header row。

若唯一映射：
- raw_period_label = 原文

若：
- 无匹配
- 同距离冲突
- 多个不同 period 同时满足

则：
- null
- warning `AMBIGUOUS_RAW_PERIOD`（冲突时）

禁止默认“左列=本期、右列=上期”。

---

## 10. Raw Unit

在当前 reconstructed table 的所有 cell text 中寻找明确 unit phrase。

支持：

- `单位：元`
- `单位: 元`
- `人民币元`
- `人民币千元`
- `人民币万元`
- `千元`
- `万元`
- `百万元`
- `港元`
- `千港元`
- `HKD`
- `RMB`
- `CNY`
- `USD`
- `美元`

规则：
- unique normalized raw phrase → raw_unit 保留原 phrase；
- 多个等价形式可归为同一 normalized key，但输出使用稳定的首个原文 phrase；
- 冲突 unit → null + `AMBIGUOUS_RAW_UNIT`；
- 无 unit → null。

货币符号仅在 value cell 中出现时，不推导整表 unit。

---

## 11. Raw Scope

显式 scope pattern：

中文：
- 合并
- 合并报表
- 母公司
- 公司

英文：
- consolidated
- company
- parent company
- separate financial statements

仅扫描：
- table candidate keywords
- 前若干 header-like rows / label text

规则：
- unique scope → raw_scope 原文；
- conflicting scopes → null + `AMBIGUOUS_RAW_SCOPE`；
- none → null。

禁止根据 issuer/market 猜 scope。

---

## 12. Continuation Group Context

从 P5 `table_groups.jsonl` 构造：

`table_id -> group_id`

若一个 table 属于唯一 group：
- RawFact `table_group_id = group_id`

否则 null。

P6 不用 group 推断 period/unit/scope，也不跨页合并 facts。

---

## 13. Evidence Contract

每个 RawFact 必须且只能有一个 Evidence：

```json
{
  "evidence_id": "...",
  "document_sha256": "...",
  "extraction_version": "p6-raw-fact-extractor-v1",
  "page_no": 88,
  "bbox": [40.0, 120.0, 500.0, 136.0],
  "raw_text": "营业收入 | 174,144,662,063.32",
  "table_id": "...",
  "row_id": "...",
  "row_index": 4,
  "column_index": 2,
  "label_cell_ids": ["..."],
  "value_cell_id": "...",
  "source_words": []
}
```

Evidence bbox：
- union(label cell bbox + value cell bbox)

source_words：
- union(label/value cells source_words)
- exact dedup by page/block/line/word/bbox
- sort by page/block/line/word

Evidence 不引用分析摘要，只引用原始财报 word geometry。

---

## 14. P3 Source Validation

P6 必须建立 P3 word index：

key：
`(page_no, block_no, line_no, word_no)`

每个 P5 source ref 必须验证：

- key exists
- bbox == P3 bbox（round 3 decimals）
- referenced page == fact page
- ref belongs to label/value cell

任何 mismatch：

`P6_INPUT_EVIDENCE_INVALID`

不生成部分可信 artifact。

---

## 15. Raw Text Validation

Evidence `raw_text`：

`raw_metric_name + " | " + raw_value`

P6 同时从 P3 source word index取得真实 word text，仅用于验证：

- referenced source words非空；
- label/value refs能解析到真实 P3 words；
- 不要求用 source words重新拼出完全相同 spacing，因为 P5已做 deterministic cell text assembly。

P6 不修改 P5 cell text。

---

## 16. Stable IDs

### RawFact

```text
SHA256(
 document_sha256
 + "\0" + table_id
 + "\0" + row_id
 + "\0" + value_cell_id
 + "\0" + EXTRACTOR_VERSION
)
```

### Evidence

```text
SHA256(
 raw_fact_id
 + "\0"
 + "\0".join(sorted(source_ref_keys))
)
```

不得使用 UUID/random/time。

---

## 17. Input Fingerprints

`fact_manifest.json` 必须记录：

- P3 pages.jsonl SHA256
- P3 sections.jsonl SHA256
- P5 tables.jsonl SHA256
- P5 table_groups.jsonl SHA256
- P5 table_manifest.json SHA256
- P3 parser version
- P5 reconstruction version
- P6 extractor version

reuse 时重新计算并全部匹配。

---

## 18. Manifest

至少：

```json
{
  "schema_version": "p6-raw-facts-evidence-v1",
  "extractor_version": "p6-raw-fact-extractor-v1",
  "document_sha256": "...",
  "fact_count": 1234,
  "evidence_count": 1234,
  "tables_with_facts": 80,
  "warnings": [],
  "input_fingerprints": {},
  "timings_ms": {}
}
```

---

## 19. Warning Model

warning 是 deterministic aggregate，不进入单 fact 猜测。

reason 至少：

- `ROW_WITHOUT_LABEL`
- `VALUE_PARSE_FAILED`
- `AMBIGUOUS_RAW_PERIOD`
- `AMBIGUOUS_RAW_UNIT`
- `AMBIGUOUS_RAW_SCOPE`

manifest warning：

```json
{
  "reason_code": "ROW_WITHOUT_LABEL",
  "count": 12
}
```

排序按 reason_code。

---

## 20. Artifact Integrity / Semantic Equality

`load_raw_facts` 必须验证：

1. schema/version/document SHA；
2. input fingerprints；
3. JSONL decode；
4. fact_count/evidence_count；
5. fact/evidence 1:1；
6. IDs recompute；
7. referenced table/row/cell存在；
8. source refs存在于当前 P3；
9. bbox valid；
10. parsed_numeric_value 可重算；
11. **完整 deterministic semantic equality**。

Semantic equality：
loader 从当前 P3/P5 input重新执行 extraction，要求：

- persisted raw_facts == recomputed raw_facts
- persisted evidence == recomputed evidence

逐记录完全相等。

任何 tamper：

`P6_ARTIFACT_INCOMPLETE_OR_CORRUPT`

---

## 21. Determinism

相同 input：

- raw_facts.jsonl byte-identical
- evidence.jsonl byte-identical
- IDs/order identical

排序：

1. page_no
2. table_id
3. row_index
4. column_index
5. raw_fact_id

JSON：
- UTF-8 without BOM
- LF
- sorted keys
- compact JSONL

timings 不进入 deterministic JSONL。

---

## 22. Persistence / Atomicity

生成：

```text
<root>/.<sha>.<uuid>.tmp/
→ write JSONL + manifest
→ validate self
→ os.replace temp -> final
```

若 final 已存在：
- load/semantic validate
- valid → REUSE
- invalid → `P6_ARTIFACT_INCOMPLETE_OR_CORRUPT`
- 不 silent overwrite

---

## 23. Immutability

P6 不修改：

- raw PDF
- P1 Registry
- P3 artifact
- P4 artifact
- P5 artifact

只写：
- P6 artifact root

---

## 24. Performance Gate

基于已验收 P3/P5 artifacts：

- CN 600519 FY2024 <= 10s
- HK 00700 FY2024 <= 15s

不包含 P3/P4/P5时间。

---

## 25. Live Acceptance Expectations

CN 600519 FY2024：
- raw_fact_count > 0
- evidence_count == raw_fact_count
- 至少 20 facts 来自 pages 60–67
- 每个 fact 有 valid evidence/source refs
- dual-root raw_facts/evidence byte-identical

HK 00700 FY2024：
- raw_fact_count > 0
- evidence_count == raw_fact_count
- pages 124/126/133 均至少有 5 facts
- valid evidence/source refs
- dual-root byte-identical

period/unit/scope：
- 不要求必须非空；
- 若非空必须有 deterministic explicit source。

---

## 26. Package Structure

```text
src/financial_filing_data_foundation/
  facts/
    __init__.py
    models.py
    extract.py
```

P6 evidence 与 fact 同 package，避免在 P6 提前引入复杂 evidence service。

---

## 27. Public API

```python
extract_raw_facts(
    native_artifact_dir: str | Path,
    reconstructed_table_dir: str | Path,
    fact_root: str | Path,
) -> RawFactArtifact
```

```python
load_raw_facts(
    artifact_dir: str | Path,
    native_artifact_dir: str | Path,
    reconstructed_table_dir: str | Path,
) -> RawFactArtifact
```

---

## 28. Error Codes

至少：

- `P6_INPUT_ARTIFACT_INVALID`
- `P6_INPUT_EVIDENCE_INVALID`
- `P6_ARTIFACT_INCOMPLETE_OR_CORRUPT`
- `P6_PERSIST_FAILED`

不 silent fallback。

---

## 29. Tests

至少覆盖：

1. numeric integer
2. decimal
3. thousands separator
4. parenthetical negative
5. percent
6. currency prefix
7. placeholder reject
8. label + one value -> one fact
9. label + multi value -> multi facts
10. no label -> skip/warning
11. nonnumeric value -> no fact
12. raw metric preserves text
13. period header unique mapping
14. period ambiguity -> null/warning
15. unique unit
16. unit conflict
17. unique scope
18. scope conflict
19. group_id mapping
20. evidence bbox union
21. source refs dedup/sort
22. invalid P3 source ref blocked
23. stable fact/evidence IDs
24. dual-root byte identity
25. artifact reuse
26. fingerprint mismatch blocked
27. fact tamper blocked
28. evidence tamper blocked
29. no PDF open
30. no OCR/Docling/network/AI
31. prior artifact immutability
32. CN live
33. HK live

---

## 30. P6 Exit

只有 Independent Acceptance = PASS：

- P6 → DONE
- accepted baseline 更新
- 才允许 P7 Quality Gate / Validation

---

## 31. Issue Rule

```text
problem
→ STOP
→ root cause
→ update design
→ commit design amendment
→ rerun affected gates
→ continue
```

禁止 code-first / design-later。
