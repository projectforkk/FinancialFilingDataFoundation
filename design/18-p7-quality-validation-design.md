# 18 — P7 Quality Gate / Validation 详细设计

状态：**DESIGN BASELINE — P7**

阶段：**P7 — Quality Gate / Validation**

前置条件：
- P0–P6 = DONE / PASS
- accepted P6 merge = `d13b62778d123ba109c5f8ab2329d121d81b186b`
- P6 artifact schema = `p6-raw-facts-evidence-v1`
- P1 Registry validation enum = `PASS / FAIL / REVIEW_REQUIRED / BLOCKED`

---

## 1. P7 目标

P7 将 P3/P5/P6 已验收 artifacts 转换为 deterministic validation result：

```text
validated document
+ validation issues
+ validation status
+ blocking_issue_count
+ compatibility status
+ reuse eligibility
```

P7 回答：

1. 当前结构化数据是否完整可验证？
2. 是否存在必须阻断的问题？
3. 是否存在需要 P9 Review Overlay 的歧义？
4. 是否满足 P1 ParsedDataRegistry 的复用条件？

P7 不修改任何上游 extraction。

---

## 2. 明确不做

P7 禁止：

- 修改 RawFact；
- 修正数字；
- canonical metric export；
- 生成 review overlay；
- 调用 Codex / remote AI；
- MCP；
- Skill；
- SEC acquisition；
- OCR / Docling；
- 投资分析；
- 财务预测。

P7 可以维护**仅用于验证规则匹配**的 raw-name alias set，但不得把 alias mapping 写回 RawFact 作为 canonical metric。

---

## 3. 输入

必须：

- P3 NativeDocumentArtifact
- P5 ReconstructedTableArtifact
- P6 RawFactArtifact

必须同一：
- `document_sha256`

所有 loader 必须 PASS。

P7 不重新打开 PDF。

---

## 4. 输出 Artifact

Schema：
`p7-validation-v1`

Policy version：
`p7-quality-policy-v1`

目录：

```text
<validation_root>/<document_sha256>/
  issues.jsonl
  validation_report.json
```

---

## 5. Validation Status

直接复用：

`financial_filing_data_foundation.registry.models.ValidationStatus`

### PASS

满足：
- 输入完整；
- blocking issue count = 0；
- review-required issue count = 0；
- deterministic checks无失败；
- compatibility = COMPATIBLE。

### REVIEW_REQUIRED

满足：
- 无 blocking issue；
- 但存在需要人工/Codex确认的 deterministic ambiguity；
- 例如 period/unit/scope coverage不足、ambiguous warning、核心 statement coverage 未充分确认。

### FAIL

系统已能完整执行 validation，但 deterministic correctness check 明确失败，例如：
- accounting reconciliation 明确不平；
- fact/evidence consistency错误（若未被 loader先阻断）；
- critical coverage低于 policy hard threshold。

FAIL 不自动修改事实。

### BLOCKED

无法可靠执行 validation：
- 上游 artifact缺失/损坏；
- document SHA mismatch；
- evidence链无法建立；
- required input unreadable。

---

## 6. CompatibilityStatus

复用：
- COMPATIBLE
- INCOMPATIBLE
- UNKNOWN

P7 v1：

### COMPATIBLE

- P3/P5/P6 schema/version在 policy allowlist；
- validation执行完整。

### INCOMPATIBLE

- schema/version明确不受当前 P7支持。

### UNKNOWN

- 无法判断兼容性但尚未达到明确 incompatible。

若 compatibility != COMPATIBLE：
`reuse_eligible=false`

---

## 7. ValidationIssue Contract

每条：

```json
{
  "issue_id": "...",
  "document_sha256": "...",
  "reason_code": "RAW_UNIT_COVERAGE_LOW",
  "severity": "REVIEW",
  "scope": "DOCUMENT",
  "page_no": null,
  "table_id": null,
  "raw_fact_ids": [],
  "evidence_ids": [],
  "message": "...",
  "observed": {},
  "policy_version": "p7-quality-policy-v1"
}
```

severity：
- INFO
- WARNING
- REVIEW
- BLOCKING
- FAILURE

其中：
- BLOCKING → status BLOCKED
- FAILURE → status FAIL
- REVIEW → status REVIEW_REQUIRED（若无更高严重度）
- WARNING/INFO 不改变 PASS。

---

## 8. Stable Issue ID

```text
SHA256(
 document_sha256
 + "\0" + reason_code
 + "\0" + scope
 + "\0" + page_no-or-empty
 + "\0" + table_id-or-empty
 + "\0" + sorted(raw_fact_ids)
 + "\0" + POLICY_VERSION
)
```

不得 UUID/time。

---

## 9. Policy Metrics

validation report 至少：

### Document

- page_count
- table_count
- table_group_count
- raw_fact_count
- evidence_count
- unique_metric_count
- pages_with_facts
- tables_with_facts

### Evidence

- evidence_coverage_ratio
- source_word_coverage_ratio

P6 contract正常时：
`evidence_coverage_ratio = 1.0`

### Raw semantic coverage

- period_nonnull_ratio
- unit_nonnull_ratio
- scope_nonnull_ratio
- ambiguous warning counts
- row_without_label_count

### Structural

- reconstructed_table_count
- tables_without_facts
- tables_without_facts_ratio
- fact_density_per_table

`candidate_count` **不是 P7 v1 必选指标**，因为 P7 正式输入不包含 P4 artifact。不得沿 P5 manifest 中可能已失效的 `p4_artifact_dir` 去隐式打开 P4。若未来调用方显式提供 P4 artifact，可增加 optional observation，但不得改变当前 validation status 语义。

### Reconciliation

- evaluated_rule_count
- passed_rule_count
- failed_rule_count
- skipped_rule_count

---

## 10. Hard Structural Checks

### QG-001 Document identity

P3/P5/P6 SHA必须相同。

Mismatch：
`DOCUMENT_IDENTITY_MISMATCH / BLOCKING`

### QG-002 Page sequence

P3 physical pages必须连续 1..page_count。

Failure：
`PAGE_SEQUENCE_INVALID / BLOCKING`

### QG-003 Fact/evidence 1:1

P6 fact_count == evidence_count，每 fact evidence存在。

Failure：
`FACT_EVIDENCE_INCOMPLETE / BLOCKING`

### QG-004 Evidence references

每 evidence：
- page有效；
- fact/evidence document SHA一致；
- source_words非空；
- bbox合法。

Failure：
`EVIDENCE_REFERENCE_INVALID / BLOCKING`

### QG-005 Facts available

若 financial filing P6 fact_count == 0：
`NO_RAW_FACTS / FAILURE`

---

## 11. Coverage Policy

P7 v1 初始阈值必须是明确 policy，不把“confidence”作为真值。

### Evidence coverage

`1.0` required。

低于 1：
BLOCKING。

### Pages with facts

只作为 observation，不要求每页都有 facts。

### Tables without facts

```text
tables_without_facts_ratio =
tables_without_facts / max(1, reconstructed_table_count)
```

- <= 0.35 → no issue
- > 0.35 and <=0.60 → WARNING
- >0.60 → REVIEW

不是 FAILURE，因为 P5 table candidates可能包含非财务/说明表。

---

## 12. P6 Warning Mapping

P6 manifest warnings映射：

### ROW_WITHOUT_LABEL

计算：
`count / max(1, fact_count + count)`

- <= 0.20 → WARNING only
- >0.20 → REVIEW

不直接 FAIL。

### AMBIGUOUS_RAW_UNIT

count > 0：
`RAW_UNIT_AMBIGUOUS / REVIEW`

### AMBIGUOUS_RAW_SCOPE

count > 0：
`RAW_SCOPE_AMBIGUOUS / REVIEW`

### AMBIGUOUS_RAW_PERIOD

count > 0：
`RAW_PERIOD_AMBIGUOUS / REVIEW`

---

## 13. Explicit Semantic Coverage

coverage只衡量 P6 raw labels，不猜 missing semantics。

### period

- ratio >= 0.50 → no issue
- 0.10 <= ratio < 0.50 → WARNING
- ratio < 0.10 and fact_count >= 50 → REVIEW

### unit

- ratio >= 0.20 → no issue
- 0.02 <= ratio < 0.20 → WARNING
- ratio < 0.02 and fact_count >= 50 → REVIEW

### scope

scope在很多 notes facts中不重复出现，因此不设 FAIL阈值。

- ratio == 0 and fact_count >=50 → WARNING
- ambiguous scope → REVIEW

---

## 14. Core Statement Coverage

P7 v1 通过 raw metric alias与页面事实密度寻找“核心财务 statement evidence”。

仅用于 validation，不写回 canonical metric。

### Balance sheet alias signals

CN：
- 资产总计 / 总资产
- 负债合计 / 总负债
- 所有者权益合计 / 股东权益合计 / 权益合计

EN：
- total assets
- total liabilities
- total equity / shareholders' equity

### Income alias signals

- 营业收入 / 营业总收入 / 收入
- 净利润 / 年度利润 / profit for the year
- revenue

### Cash flow alias signals

- 经营活动产生的现金流量净额
- 现金及现金等价物净增加额
- 期末现金及现金等价物余额
- net cash generated from operating activities
- net increase in cash and cash equivalents

Document存在以下三类中至少两类：
- balance signal
- income signal
- cashflow signal

→ `CORE_STATEMENT_SIGNAL_SUFFICIENT`

少于两类且 fact_count >=100：
`CORE_STATEMENT_COVERAGE_LOW / REVIEW`

不因为 alias缺失直接 FAIL。

---

## 15. Accounting Reconciliation

只在**同 page/table/period/unit/scope context 足够明确且唯一**时计算。

不得跨不兼容 context 猜测。

### 15.1 Assets = Liabilities + Equity

Alias仅供选择 facts。

要求：
- unique assets fact
- unique liabilities fact
- unique equity fact
- same raw_period_label（可全部 null但必须同 table/page）
- same raw_unit
- same raw_scope
- same table或同 continuation group

计算 Decimal：

```text
difference = abs(A - (L + E))
tolerance = max(1, abs(A) * 0.0005)
```

difference <= tolerance → PASS

否则：
`BALANCE_SHEET_RECONCILIATION_FAILED / FAILURE`

若无法形成唯一 compatible trio：
SKIPPED，不判失败。

### 15.2 Cash equation

只有能唯一识别：
- beginning cash
- net increase
- ending cash

同 compatible context才计算：

```text
abs(begin + increase - end) <= max(1, abs(end)*0.0005)
```

失败：
`CASH_RECONCILIATION_FAILED / FAILURE`

否则 SKIPPED。

---

## 16. Duplicate / Conflict Check

相同：

```text
normalized raw_metric_name
+ raw_period_label
+ raw_unit
+ raw_scope
+ table_id
+ column_index
```

若出现多个不同 `parsed_numeric_value`：

`CONFLICTING_FACT_VALUES / REVIEW`

不自动选一个。

完全相同 duplicate：
WARNING。

---

## 17. Reuse Eligibility

`reuse_eligible=true` iff：

- validation_status == PASS
- blocking_issue_count == 0
- compatibility_status == COMPATIBLE
- input fingerprints valid
- policy_version supported

REVIEW_REQUIRED / FAIL / BLOCKED：
false。

P7 不自行覆盖 P1 Registry已有记录。

---

## 18. ParsedDataRecord Integration

提供：

```python
build_parsed_data_record(
    validation_artifact,
    slot: FilingSlotKey,
    artifact_path: str,
) -> ParsedDataRecord
```

映射：

- parse_run_id = deterministic SHA over document SHA + P3/P5/P6 versions + P7 policy version
- document_sha256
- parser_version = aggregate pipeline version string
- schema_version = final P7 schema
- validation_status = report status
- blocking_issue_count
- compatibility_status
- artifact_path

调用方可再：
`registry.register_parsed_data(record)`

P7 validator本身不隐式写 registry。

---

## 19. Parse Run ID

```text
SHA256(
 document_sha256
 + "\0" + P3 parser version
 + "\0" + P5 reconstruction version
 + "\0" + P6 extractor version
 + "\0" + P7 policy version
)
```

stable。

---

## 20. Validation Report

至少：

```json
{
  "schema_version": "p7-validation-v1",
  "policy_version": "p7-quality-policy-v1",
  "document_sha256": "...",
  "validation_status": "REVIEW_REQUIRED",
  "compatibility_status": "COMPATIBLE",
  "reuse_eligible": false,
  "blocking_issue_count": 0,
  "failure_issue_count": 0,
  "review_issue_count": 2,
  "warning_issue_count": 3,
  "metrics": {},
  "input_fingerprints": {},
  "issues_file": "issues.jsonl",
  "timings_ms": {}
}
```

---

## 21. Input Fingerprints

记录 SHA：
- P3 document.json
- P3 pages.jsonl
- P5 manifest/tables/groups
- P6 manifest/raw_facts/evidence

及版本：
- P3 parser
- P5 reconstruction
- P6 extractor
- P7 policy

reuse必须全部一致。

---

## 22. Semantic Integrity

`load_validation_result` 必须：

1. schema/version；
2. fingerprints；
3. issues JSONL；
4. issue IDs；
5. report counts；
6. status recompute；
7. metrics recompute；
8. **完整重新执行 validation并与 persisted report/issues 做 semantic equality**。

tamper：
`P7_ARTIFACT_INCOMPLETE_OR_CORRUPT`

---

## 23. Determinism

相同 inputs：

- issues.jsonl byte-identical
- report除 timings 外语义相同
- stable issue IDs
- stable status
- stable metrics

issues排序：
1. severity rank
2. reason_code
3. page
4. table_id
5. issue_id

---

## 24. Persistence

atomic temp dir → final。

final存在：
- load/recompute/validate
- valid → reuse
- invalid → block，不覆盖

---

## 25. Immutability

P7不修改：
- raw PDF
- P3
- P4
- P5
- P6
- Registry（validator本体）

只写 P7 artifact。

---

## 26. Performance

代表样本：
- CN <=10s
- HK <=15s

通常 validation应远低于该门槛。

---

## 27. Live Expected Semantics

P7 acceptance**不预设 live 必须 PASS**。

正确状态由 policy deterministic决定。

尤其：
- HK P6 period coverage = 0，P7预期至少产生 period coverage REVIEW；
- CN可能因 unit/scope/row warning 或 reconciliation得到 PASS/REVIEW/FAIL中的 deterministic结果。

验收目标是：
- status可重现；
- issue evidence可解释；
- reuse_eligible与status一致。

---

## 28. Public API

```python
validate_document_artifacts(
    native_artifact_dir,
    reconstructed_table_dir,
    raw_fact_dir,
    validation_root,
) -> ValidationArtifact
```

```python
load_validation_result(...)
```

```python
build_parsed_data_record(
    validation_artifact,
    slot,
    artifact_path,
) -> ParsedDataRecord
```

---

## 29. Package

```text
src/financial_filing_data_foundation/
  validation/
    __init__.py
    models.py
    policy.py
    validate.py
```

---

## 30. Error Codes

至少：

- P7_INPUT_ARTIFACT_INVALID
- P7_ARTIFACT_INCOMPLETE_OR_CORRUPT
- P7_POLICY_INCOMPATIBLE
- P7_PERSIST_FAILED

validation issues使用业务 reason_code，不与异常 error code混用。

---

## 31. Tests

至少：

1. status priority BLOCKED > FAIL > REVIEW > PASS
2. compatible versions
3. incompatible version
4. evidence 100%
5. missing evidence block
6. no facts fail
7. row-without-label warning/review thresholds
8. ambiguous unit review
9. period coverage thresholds
10. unit coverage thresholds
11. core statement signal
12. balance reconciliation pass
13. balance reconciliation fail
14. reconciliation skipped on incompatible context
15. cash reconciliation pass/fail
16. duplicate same value warning
17. conflicting values review
18. stable issue ID
19. parse_run_id deterministic
20. reuse eligibility PASS only
21. build ParsedDataRecord
22. planner can REUSE after PASS record registered
23. planner cannot REUSE review/fail/blocked
24. dual-root determinism
25. artifact reuse
26. report tamper blocked
27. issue tamper blocked
28. fingerprint mismatch blocked
29. upstream immutable
30. no PDF open
31. no OCR/Docling/network/AI
32. CN live
33. HK live

---

## 32. Exit

Independent Acceptance PASS后：
- P7 DONE
- 才允许 P8 Local MCP。

---

## 33. P7 Issue Log

### P7-ISSUE-001 — P7 metrics originally required candidate_count without P4 as an input

Implementation preparation found a contract mismatch:

- formal P7 inputs are P3 / P5 / P6；
- P5 manifest contains a P4 fingerprint and historical path, but does not guarantee a portable/available P4 artifact path；
- requiring `candidate_count` would either fabricate it from reconstructed table count or implicitly follow a possibly stale absolute path。

Approved solution:
- P7 v1 mandatory structural metrics exclude `candidate_count`；
- use `reconstructed_table_count`, `tables_with_facts`, `tables_without_facts`, `tables_without_facts_ratio`, `fact_density_per_table`；
- never infer candidate_count from table_count；
- never reopen P4 through P5 manifest path；
- optional explicit P4 observation may be added only in a later design revision。

Affected gates: P7-B/C/D/H/J/L。

---

## 34. Issue Rule

problem → STOP → root cause → update design → commit → rerun affected gates → continue。
