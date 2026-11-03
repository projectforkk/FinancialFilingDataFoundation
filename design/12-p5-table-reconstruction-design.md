# 12 — P5 Table Reconstruction / Cross-page 详细设计

状态：**DESIGN BASELINE — P5**

前置：
- P0–P4 DONE / PASS
- accepted P4 merge: `97f2de24861347c97bf875e7b72899eb11ab56c2`

## 1. 目标

P5 只从：
- P3 native page geometry
- P4 table candidates

重建 deterministic table fragments：

```text
candidate
→ visual rows
→ label/value columns
→ cells with source word refs
→ adjacent-page continuation groups
```

P5 不生成 accounting facts。

## 2. 明确不做

禁止：
- P6 raw facts/evidence semantics
- account normalization
- period/value semantic interpretation
- unit/currency fact binding
- OCR
- Docling
- network
- external AI

## 3. Inputs

必须同时提供：
- valid P3 NativeDocumentArtifact
- valid P4 TableCandidateArtifact

要求：
- same document_sha256
- P4 artifact valid
- P3 artifact valid

## 4. Artifact

Schema:
`p5-reconstructed-tables-v1`

Version:
`p5-table-reconstruction-v1`

目录：

```text
<table_root>/<document_sha256>/
  tables.jsonl
  table_groups.jsonl
  table_manifest.json
```

## 5. Table Fragment Contract

每个 P4 candidate 对应最多一个 reconstructed fragment。

至少：

```json
{
  "table_id": "...",
  "candidate_id": "...",
  "document_sha256": "...",
  "page_no": 126,
  "bbox": [...],
  "value_column_count": 2,
  "value_column_anchors": [365.2, 472.5],
  "row_count": 32,
  "rows": []
}
```

## 6. Row Contract

```json
{
  "row_id": "...",
  "row_index": 0,
  "bbox": [...],
  "cells": []
}
```

Row identity:

`SHA256(table_id + "\0" + row_index + "\0" + bbox)`

## 7. Cell Contract

P5 只使用结构角色：

- `LABEL`
- `VALUE`
- `UNASSIGNED`

不使用财务语义角色。

```json
{
  "cell_id": "...",
  "column_index": 0,
  "role": "LABEL",
  "text": "營業收入",
  "bbox": [...],
  "numeric": false,
  "source_words": [
    {
      "page_no": 124,
      "block_no": 1,
      "line_no": 2,
      "word_no": 0,
      "bbox": [...]
    }
  ]
}
```

Cell identity由 table/row/column/source words deterministic hash 生成。

## 8. Candidate Word Selection

只选：
- page_no == candidate.page_no
- word bbox 与 candidate bbox 相交
- word block_no ∈ candidate.block_nos

Distributed-block candidate 仍使用其 numeric evidence block_nos。

不得读取 candidate bbox 外的 words 来“补表”。

## 9. Visual Row Clustering

用 word y-center 聚类。

Tolerance：

`max(3.0pt, median_word_height * 0.60)`

排序：
- y center
- x0
- block_no / line_no / word_no

相邻 word y-center <= tolerance → 同 visual row。

cluster 完成后按 row top / left 排序。

不依赖 P3 block grouping。

## 10. Numeric Value Anchors

P5 使用 P4 numeric classifier 识别 numeric words。

对 numeric word **right edge x1** 做 1D clustering。

初始 tolerance：

`max(8pt, page_width * 0.025)`

Cluster 保留条件：
- 至少出现在 2 个 distinct visual rows；
- 或 candidate numeric_token_count < 4 时至少出现 1 次。

Anchor = median x1。

排序从左到右。

## 11. Column Model

P5 首期 structural columns：

- column 0 = LABEL
- column 1..N = VALUE anchors

不尝试把：
- note number
- currency
- period title

提前语义化。

Numeric word：
分配给最近 value anchor，若距离 <= anchor tolerance * 1.5。

其它 word：
默认 LABEL；若位于第一 value anchor右侧且无法匹配 numeric value，则 UNASSIGNED。

## 12. Cell Text Assembly

同 row/column words：

按：
- x0
- word_no

排序。

中文/无空格文本：
如果原 word bbox 间距很小，可直接连接；
默认 deterministic join 使用单空格，再执行轻量 punctuation spacing normalization。

不得修改 numeric raw text。

## 13. Cell BBox / Evidence

Cell bbox = source words union bbox。

必须保留 source word refs。

P5 evidence 仍是 geometry-level provenance，不是 P6 first-class financial evidence object。

## 14. Header / Body

P5 不强制语义 header detection。

可输出 structural row signal：

- `NO_NUMERIC_VALUE`
- `HAS_NUMERIC_VALUE`
- `MULTI_VALUE_ROW`

P6/P7 再决定 semantic interpretation。

## 15. Reconstruction Quality Signals

Table fragment至少：

- `NO_VALUE_COLUMNS`
- `SPARSE_ROWS`
- `MANY_UNASSIGNED_WORDS`
- `DISTRIBUTED_BLOCK_SOURCE`
- `LOW_ROW_COUNT`

这些 signals 不自动丢弃 fragment。

## 16. Stable Table Identity

`table_id = SHA256(document_sha256 + "\0" + candidate_id + "\0" + reconstruction_version)`

Candidate artifact变化会得到不同 candidate id / table id。

## 17. Cross-page Continuation

P5 不物理合并不同 page 的 rows。

输出 `table_groups.jsonl`：

```json
{
  "group_id": "...",
  "member_table_ids": ["...", "..."],
  "page_start": 126,
  "page_end": 127,
  "continuation_signals": [
    "ADJACENT_PAGES",
    "VALUE_COLUMNS_COMPATIBLE",
    "BOTTOM_TOP_CONTINUITY"
  ],
  "score": 4.0
}
```

## 18. Continuation Conditions

仅考虑相邻 page fragments。

必须：
1. page B = page A + 1
2. value_column_count 相同且 > 0
3. normalized anchor positions compatible：
   each abs(xA/page_widthA - xB/page_widthB) <= 0.04
4. A candidate bottom >= page_height * 0.65
5. B candidate top <= page_height * 0.40

加分：
- same/compatible financial keywords
- repeated numeric anchor pattern
- B first row resembles repeated header

P5 不要求所有 continuation 都识别。

不满足强条件 → 不 group，不猜。

## 19. Group Identity

`group_id = SHA256(document_sha256 + "\0" + "\0".join(member_table_ids))`

group member tables 保持 page order。

## 20. Multi-page Chains

若：
A→B continuation
B→C continuation

输出一个 A/B/C group。

只连接连续相邻链。

## 21. Artifact Input Fingerprints

P5 manifest 必须记录：
- P3 pages.jsonl SHA256
- P3 sections.jsonl SHA256
- P4 candidates.jsonl SHA256
- P4 candidate manifest SHA256
- P3 parser version
- P4 detector version

reuse 时重新计算并要求精确匹配。

防止 stale reconstruction。

## 22. Artifact Corruption Guard

load/reuse 验证：
- schema/version/document SHA
- input fingerprints
- table_count/group_count
- JSONL decode
- table_id recompute
- candidate_id exists in current P4 artifact
- page range
- row_id recompute
- cell_id recompute
- source word refs belong to page/candidate block set
- group member table IDs exist
- group pages monotonic/adjacent

任何失败：
`P5_ARTIFACT_INCOMPLETE_OR_CORRUPT`

## 23. Determinism

相同 P3/P4 input：
- tables.jsonl byte-identical
- table_groups.jsonl byte-identical
- IDs identical
- ordering identical

timings 不进入 deterministic JSONL。

## 24. Performance Gate

输入 P3/P4 JSON artifacts。

初始：
- CN <= 10s
- HK <= 20s

不含 P3/P4生成时间。

## 25. Live Recall / Structure Guard

CN 600519 FY2024：
- table fragments > 0
- 至少一个 fragment value_column_count >= 2
- pages 60–67 中至少 2 页有 reconstructed fragment

HK 00700 FY2024：
- pages 124 / 126 / 133 都有 reconstructed fragment
- 每页至少 2 value columns
- 至少 5 rows

Cross-page：
- 两个 live documents 合计至少生成 1 个 continuation group；
- 若强条件事实不成立，必须记录 evidence 并更新 acceptance expectation，不得降低算法强条件来制造 group。

## 26. Package

```text
src/financial_filing_data_foundation/
  tables/
    __init__.py
    models.py
    reconstruct.py
```

## 27. Public API

```python
reconstruct_tables(
    native_artifact_dir,
    candidate_artifact_dir,
    table_root,
) -> ReconstructedTableArtifact
```

```python
load_reconstructed_tables(artifact_dir) -> ReconstructedTableArtifact
```

## 28. Tests

至少：
1. y row clustering
2. numeric right-edge anchor clustering
3. label/value cell assignment
4. source word refs
5. stable IDs
6. no numeric column signal
7. distributed-block candidate
8. value anchor deterministic
9. adjacent continuation
10. incompatible columns not grouped
11. non-adjacent not grouped
12. input fingerprint mismatch blocked
13. table/cell/id tamper blocked
14. group member tamper blocked
15. dual-root deterministic
16. no PDF open
17. no OCR/Docling/network/AI
18. prior artifacts unchanged
19. CN live
20. HK live

## 29. Exit

Independent Acceptance PASS 后：
P5 DONE → authorize P6 Raw Facts / Evidence。

## 30. Issue Rule

problem → STOP → design update → commit → rerun affected gates → continue。
