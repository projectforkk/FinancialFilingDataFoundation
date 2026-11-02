# 04 — CN/HK PDF Quality Gate 详细设计

状态：DESIGN BASELINE

## 1. 原则

“存在 native text”不等于“可可靠解析”。

Quality Gate 使用 deterministic signals + blocking flags。

不得使用“模型自己声称 95% confidence”作为自动通过依据。

## 2. Page Classification

候选状态：
- NORMAL
- TEXT_ORDER_SUSPECT
- ENCODING_SUSPECT
- TABLE_COMPLEX
- IMAGE_DOMINANT
- SCANNED
- CORRUPTED

## 3. Signals

### Text Integrity
- native chars
- replacement / invalid chars
- abnormal whitespace
- fragmented glyph ratio
- duplicated text ratio

### Reading Order
- block order consistency
- line baseline consistency
- x/y inversion
- multi-column ambiguity

### Layout
- page geometry
- rotation
- overlapping text
- drawing / image dominance

### Table
- candidate region confidence
- stable row baselines
- stable numeric x clusters
- header/body alignment
- cell count consistency
- multi-level header
- continuation likelihood

### Financial Consistency
仅做一致性检查，不自动修值：
- Assets ≈ Liabilities + Equity
- beginning cash + net increase ≈ ending cash
- period header consistency
- unit consistency

## 4. Blocking Flags

至少：
- YEAR_COLUMN_AMBIGUOUS
- UNIT_AMBIGUOUS
- SCOPE_AMBIGUOUS
- TABLE_GRID_AMBIGUOUS
- CROSS_PAGE_STITCH_AMBIGUOUS
- ENCODING_UNRECOVERABLE
- PAGE_CONTENT_INCOMPLETE
- FINANCIAL_RECONCILIATION_FAILED

存在 blocking flag 时，即使 aggregate quality score 较高，也不得 LOCAL_ACCEPT。

## 5. Routing

初始建议阈值仅作为 calibration 起点：

```text
score >= 0.90 且无 blocking flag
  → LOCAL_ACCEPT

0.75 <= score < 0.90
  → TEXT_REVIEW

score < 0.75 或存在 visual-only ambiguity
  → VISION_REVIEW

无法打开 / 页面缺失 / 关键证据不可得
  → BLOCKED
```

阈值必须通过 Golden calibration 调整。

## 6. Core Financial Statements

在 V0 / early calibration 阶段，以下页面即使本机得分很高，也应强制人工/Codex抽查：
- balance sheet；
- income statement；
- cash flow statement。

目的：测量 false-positive local accept。

## 7. Model Exposure

记录：

```text
MODEL_EXPOSURE_RATIO =
(text_review_pages + vision_review_pages) / total_pages
```

这是运行指标，不是先验承诺。

## 8. Performance Safety

born-digital 默认：
- OCR OFF
- heavy neural layout OFF
- TableFormer OFF

只有明确 reason code 才可进入 heavy fallback。

## 9. P0 特别要求

P0 不实现最终 quality score。
只采集可用于未来 gate 的原始 signals，并验证：
- 能否快速读取；
- 哪些页面明显异常；
- 哪些 signal 在代表样本上有区分度。
