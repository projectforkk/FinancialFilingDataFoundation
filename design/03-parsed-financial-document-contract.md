# 03 — ParsedFinancialDocument v1 Contract

状态：DESIGN BASELINE

## 1. 导出目录

```text
export/
  manifest.json
  document.json
  pages.jsonl
  sections.jsonl
  tables.jsonl
  raw_facts.jsonl
  evidence.jsonl
  validation.json
```

## 2. manifest.json

至少：

```json
{
  "schema_version": "1.0",
  "parser_version": "...",
  "quality_policy_version": "...",
  "document_sha256": "...",
  "parse_run_id": "...",
  "page_count": 143,
  "local_accept_pages": 0,
  "text_review_pages": 0,
  "vision_review_pages": 0,
  "blocking_issue_count": 0,
  "validation_status": "PASS"
}
```

## 3. document.json

至少：
- document_id
- document_key
- market
- company_id
- ticker
- filing_type
- fiscal_year candidate
- raw_fiscal_period
- filing_date
- report_date
- source_provider
- source_id
- source_url
- source_title
- original_file_name
- sha256
- file_size
- page_count

## 4. pages.jsonl

每行：
- page_no
- width
- height
- rotation
- native_text_available
- native_char_count
- word_count
- block_count
- image_count
- drawing_count
- raw_text nullable
- quality signals
- review status

页面编号一律使用物理 PDF page_no（1-based）。

## 5. sections.jsonl

字段：
- section_id
- parent_section_id nullable
- raw_title
- normalized_title candidate nullable
- level
- page_start
- page_end
- bbox nullable
- quality signals

## 6. tables.jsonl

字段：
- table_id
- raw_title
- page_start
- page_end
- page_fragments
- bbox fragments
- raw_unit
- raw_scope
- table_type_candidate
- header_tree
- rows
- raw_cells
- reconstruction signals
- blocking flags

每个 raw cell 至少：
- raw_text
- page_no
- bbox
- row_index
- column_index
- rowspan candidate
- colspan candidate

## 7. raw_facts.jsonl

字段：
- raw_fact_id
- raw_metric_name
- raw_value
- parsed_numeric_value candidate
- raw_unit
- raw_period_label
- raw_scope
- table_id
- page_no
- row_index
- column_index
- evidence_id

禁止只存 canonical metric。

## 8. evidence.jsonl

字段：
- evidence_id
- document_sha256
- extraction_run_id
- page_no
- bbox
- raw_text
- table_id nullable
- row_index nullable
- column_index nullable

Evidence 必须引用原始财报内容，而不是分析摘要。

## 9. validation.json

字段：
- status: PASS | FAIL | REVIEW_REQUIRED | BLOCKED
- structural_checks
- financial_consistency_checks
- completeness_checks
- blocking_issues
- warnings
- validated_at
- validator_version

## 10. Export Gate

只有：

```text
validation_status == PASS
AND blocking_issue_count == 0
```

才允许标记：
`DATA_READY`。

仍可导出调试 artifact，但不得让下游将其当 ready dataset。
