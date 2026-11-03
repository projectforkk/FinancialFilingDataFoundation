# 22 — P9 Codex Review Overlay 详细设计

状态：**DESIGN BASELINE — P9**

阶段：**P9 — Codex Review Overlay**

前置条件：
- P0–P8 = DONE / PASS
- accepted P8 merge = `415d2ad82e890be855198d4d4c57bca8d1beb406`
- P8 closeout = `development/47-p8-closeout.md`
- P7 validation schema = `p7-validation-v1`
- P6 raw fact schema = `p6-raw-facts-evidence-v1`
- project directory consolidation = PASS

---

## 1. P9 目标

P9 建立**可审计、append-only、evidence-grounded 的 Review Overlay 数据层**，将：

```text
P7 REVIEW_REQUIRED
      ↓
review queue
      ↓
explicit reviewer resolutions
      ↓
REVIEW_OVERLAY
      ↓
resolved fact view
      ↓
overlay-aware re-validation
      ↓
RESOLVED validation result
```

P9 的核心职责：

1. 从已验收 P7 REVIEW issues deterministic 生成 review queue；
2. 接收外部 reviewer（Codex 或 Human）提交的显式 resolution；
3. 验证 resolution target、evidence、base identity、before/after；
4. 以 immutable resolution records 保存 review history；
5. 不修改 P6 RawFact，而生成 `effective_*` resolved view；
6. 对 supported REVIEW issues 做 overlay-aware deterministic re-validation；
7. 生成 content-addressed resolved snapshot；
8. 可构造 resolved `ParsedDataRecord`，但**不隐式写 Registry**。

---

## 2. Codex / AI 边界

P9 production **不调用 Codex、OpenAI API 或任何远程 LLM API**。

原因：

- Review Overlay 是本地数据 contract / persistence / validation infrastructure；
- “Codex 阅读上下文、判断语义、选择 resolution”属于 P10 Skill orchestration；
- P9 只接受 reviewer 已明确提交的 resolution payload；
- 这样 P9 能 deterministic unit test / acceptance，不把模型行为混入 production truth。

允许 reviewer metadata：

- `reviewer_type = CODEX`
- `reviewer_type = HUMAN`

但只是审计字段，不触发模型调用。

P10 可在未来使用 P8 read-only tools + P9 local APIs/CLI 进行 Codex review。

---

## 3. 数据分层

严格保持：

```text
RAW
  ↓
LOCAL_EXTRACTED          ← P3/P5/P6/P7 immutable
  ↓
REVIEW_OVERLAY           ← P9 immutable resolution records
  ↓
RESOLVED                 ← P9 materialized effective view
  ↓
EXPORT                   ← later phase
```

P9 禁止覆盖：

- P3 page/section
- P5 table/cell
- P6 raw facts/evidence
- P7 report/issues
- source PDF
- Registry

---

## 4. 明确不做

P9 v1 禁止：

- 修改 `raw_value`
- 修改 `parsed_numeric_value`
- 修改 `raw_metric_name`
- canonical metric mapping
- fiscal period canonicalization
- YoY/QoQ/TTM
- accounting number correction
- OCR/Docling
- acquisition
- source PDF reopen
- remote AI/API
- MCP mutation tools
- P8 tool contract changes
- P10 Skill implementation
- P11 SEC provider
- automatic reviewer decision
- silent issue dismissal

若 reviewer 不能以 evidence 支撑 resolution：
保持 unresolved。

---

## 5. P9 输入

P9 使用同一 document 的：

- P3 NativeDocumentArtifact
- P5 ReconstructedTableArtifact
- P6 RawFactArtifact
- P7 ValidationArtifact

必须全部 loader PASS 且：

```text
P3 SHA == P5 SHA == P6 SHA == P7 SHA == document_sha256
```

P9 不打开 PDF。

### 5.1 Artifact discovery

P9 v1 复用已验收 P8 project-local catalog：

`financial_filing_data_foundation.mcp.catalog.McpCatalog`

注意：

- 只复用 internal catalog model/path guard；
- 不 import external MCP SDK；
- 不运行 MCP server；
- main FFDF runtime仍不需要外部 `mcp` package。

Public prepare API 输入：

- project_root
- catalog_path
- document_sha256
- review_root

artifact dirs 只能来自 catalog，不允许 reviewer resolution payload传任意路径。

---

## 6. Base status eligibility

### PASS

允许创建空 review queue。

用途：
- audit/no-op
- 保持 deterministic identity

不得无故创建 semantic resolution。

### REVIEW_REQUIRED

P9 正常目标。

只对 severity=`REVIEW` issue 生成 review task。

WARNING / INFO：
- 保留为 context
- 不要求 review
- 不阻止 resolved PASS

### FAIL / BLOCKED

P9 v1 不允许通过 overlay 修复 deterministic failure/blocker。

返回：

`P9_BASE_STATUS_NOT_REVIEWABLE`

理由：
P9 不允许通过人工 overlay 绕过 P7 FAILURE/BLOCKING correctness。

---

## 7. Artifact layout

Review root：

```text
<review_root>/<document_sha256>/
  review_manifest.json
  review_queue.jsonl
  resolutions/
    <resolution_id>.json
  snapshots/
    <overlay_set_hash>/
      resolved_facts.jsonl
      resolved_issues.jsonl
      resolution_report.json
      snapshot_manifest.json
```

关键原则：

- base manifest / queue immutable；
- resolution files immutable；
- snapshots content-addressed；
- 不维护可变 `current.json` 指针；
- 调用方以返回的 `overlay_set_hash` / snapshot path 明确引用具体 resolved state。

---

## 8. Schema / Policy versions

- Review manifest:
  `p9-review-overlay-v1`
- Review task:
  `p9-review-task-v1`
- Resolution:
  `p9-review-resolution-v1`
- Resolved fact:
  `p9-resolved-fact-v1`
- Resolution report:
  `p9-resolution-report-v1`
- Review policy:
  `p9-review-policy-v1`

---

## 9. Input fingerprints

`review_manifest.json` 必须固定：

- P3 document.json SHA256
- P3 pages.jsonl SHA256
- P5 manifest/tables/groups SHA256
- P6 manifest/facts/evidence SHA256
- P7 validation_report/issues SHA256
- P3 parser version
- P5 reconstruction version
- P6 extractor version
- P7 policy version
- P9 review policy version
- catalog SHA256
- document SHA256

每次：

- submit resolution
- materialize
- load snapshot

都重新验证 base fingerprints。

任一变化：

`P9_BASE_ARTIFACT_CHANGED`

旧 overlay不能 silent migrate。

---

## 10. Review queue

### 10.1 Queue source

只处理 P7 `severity=REVIEW` issues。

每个 P7 review issue → exactly one ReviewTask。

Warning 不单独生成 task。

### 10.2 ReviewTask contract

```json
{
  "schema_version": "p9-review-task-v1",
  "review_task_id": "...",
  "document_sha256": "...",
  "base_validation_report_sha256": "...",
  "issue_id": "...",
  "reason_code": "RAW_PERIOD_COVERAGE_LOW",
  "message": "...",
  "observed": {},
  "reviewability": "SUPPORTED",
  "supported_actions": ["SET_PERIOD"],
  "required_evidence_types": ["P5_CELL", "P6_EVIDENCE"]
}
```

### 10.3 Stable task ID

```text
SHA256(
 document_sha256
 + "\0" + base_validation_report_sha256
 + "\0" + issue_id
 + "\0" + P9_POLICY_VERSION
)
```

---

## 11. Supported P7 REVIEW reason codes

### 11.1 RAW_PERIOD_COVERAGE_LOW

SUPPORTED。

Actions：
- `SET_PERIOD`

Targets：
- FACT_FIELD
- TABLE_COLUMN_FIELD

Resolution state通过 effective period coverage重新计算。

### 11.2 RAW_PERIOD_AMBIGUOUS

SUPPORTED。

Actions：
- SET_PERIOD
- ATTEST_ISSUE_RESOLVED

Ambiguity issue只有在 evidence-grounded field resolutions + explicit issue attestation 完成后才可 resolved。

### 11.3 RAW_UNIT_COVERAGE_LOW

SUPPORTED。

Actions：
- SET_UNIT

Targets：
- FACT_FIELD
- TABLE_FIELD

### 11.4 RAW_UNIT_AMBIGUOUS

SUPPORTED。

Actions：
- SET_UNIT
- ATTEST_ISSUE_RESOLVED

当前 HK live observed count = 2。

不得仅通过“unit coverage ratio变高”自动消除 ambiguity issue。

### 11.5 RAW_SCOPE_AMBIGUOUS

SUPPORTED。

Actions：
- SET_SCOPE
- ATTEST_ISSUE_RESOLVED

### 11.6 CORE_STATEMENT_COVERAGE_LOW

SUPPORTED。

Action：
- `CLASSIFY_TABLE_STATEMENT`

Target：
- TABLE_STATEMENT_CLASS

Reviewed table classification只进入 overlay，不写回 raw metric / P5 table。

Allowed：
- BALANCE
- INCOME
- CASHFLOW
- OTHER

### 11.7 Unsupported review reasons

例如未来：

- ROW_WITHOUT_LABEL_HIGH
- CONFLICTING_FACT_VALUES
- TABLE_FACT_COVERAGE_REVIEW
- unknown reason

ReviewTask：

`reviewability=UNSUPPORTED`

supported_actions=[]。

P9 v1不得人工强制关闭。

Resolved status保持 REVIEW_REQUIRED。

---

## 12. Warning issue handling

例如当前：

- ROW_WITHOUT_LABEL_PRESENT
- RAW_UNIT_COVERAGE_WARN
- RAW_SCOPE_COVERAGE_ZERO

P9 v1：

- 保留 base warning metadata；
- 不要求 resolution；
- resolved report中保留 warning counts；
- WARNING 不阻止 resolved PASS。

P9 不将 warning“升级”为 review，也不静默删除。

---

## 13. Resolution contract

每个 resolution JSON：

```json
{
  "schema_version": "p9-review-resolution-v1",
  "resolution_id": "...",
  "document_sha256": "...",
  "base_validation_report_sha256": "...",
  "review_task_id": "...",
  "issue_id": "...",
  "reason_code": "...",
  "action": "SET_PERIOD",
  "target": {},
  "value": "2024年度",
  "evidence_refs": [],
  "evidence_pages": [120],
  "before": {},
  "after": {},
  "reviewer": {
    "reviewer_type": "CODEX",
    "reviewer_id": "..."
  },
  "reviewed_at": "2026-11-03T21:00:00+09:00",
  "justification": "...",
  "base_active_resolution_ids": [],
  "base_overlay_set_hash_before": "...",
  "supersedes_resolution_id": null,
  "supporting_resolution_ids": []
}
```

---

## 14. Reviewer / timestamp

### reviewer_type

Allowed：
- CODEX
- HUMAN

### reviewer_id

- caller supplied
- trim
- 1..128 chars
- 不允许 secret/password/token

### reviewed_at

必须 caller supplied：
- RFC3339 / ISO8601
- timezone-aware
- 不允许 naive datetime
- core production不得自动使用 current time 生成审计时间

原因：
相同显式 submission必须有 deterministic ID。

---

## 15. Resolution ID

对规范化 resolution payload（不含 resolution_id）做 canonical JSON：

- UTF-8
- sort keys
- compact separators
- no NaN

```text
resolution_id =
SHA256(canonical_resolution_payload)
```

其中 persisted payload 还包含 P9 自动计算的 `base_active_resolution_ids` 与 `base_overlay_set_hash_before`。

因此：

- same caller submission + same explicit prior overlay state → same ID / idempotent；
- 若 prior active overlay state已变化，即使 caller字段相同，也会形成新的可审计 resolution identity；
- caller不得直接指定/覆盖这两个 base-state 字段。

---

## 16. Resolution actions

### 16.1 SET_PERIOD

Allowed target：

#### FACT_FIELD

```json
{"target_type":"FACT_FIELD","raw_fact_id":"...","field":"period"}
```

#### TABLE_COLUMN_FIELD

```json
{
  "target_type":"TABLE_COLUMN_FIELD",
  "table_id":"...",
  "column_index":2,
  "field":"period"
}
```

TABLE_COLUMN applies to matching P6 facts in same table/column whose raw_period_label is null。

### 16.2 SET_UNIT

Allowed：

FACT_FIELD / TABLE_FIELD。

TABLE_FIELD：

```json
{"target_type":"TABLE_FIELD","table_id":"...","field":"unit"}
```

只对 raw_unit=null facts产生 effective unit。

### 16.3 SET_SCOPE

Allowed：

FACT_FIELD / TABLE_FIELD。

只对 raw_scope=null facts产生 effective scope。

### 16.4 CLASSIFY_TABLE_STATEMENT

Target：

```json
{
  "target_type":"TABLE_STATEMENT_CLASS",
  "table_id":"..."
}
```

value：
- BALANCE
- INCOME
- CASHFLOW
- OTHER

### 16.5 ATTEST_ISSUE_RESOLVED

只允许：
- RAW_PERIOD_AMBIGUOUS
- RAW_UNIT_AMBIGUOUS
- RAW_SCOPE_AMBIGUOUS

Target：
ISSUE。

必须：
- `expected_observed_count` 与 base issue observed.count 一致；
- supporting_resolution_ids 非空；
- 每个 support resolution active；
- 每个 support resolution属于同一 issue；
- 每个 support resolution有 valid evidence。

### 16.6 SUPERSEDE

不是独立 action。

通过新 resolution 的：

`supersedes_resolution_id`

表达 revision。

---

## 17. Fill-only rule

P9 v1 不覆盖 P6 explicit raw semantic field。

### FACT target

若目标 raw field 非 null：

- new value 与 raw 完全等价 → no-op，拒绝为 `P9_RESOLUTION_NO_EFFECT`
- new value 与 raw 不同 → `P9_PATCH_CONFLICTS_WITH_RAW`

### TABLE / TABLE_COLUMN target

对 target scope内：

- raw field null → affected
- raw field非 null且 normalized value等于 resolution → already explicit，忽略
- raw field非 null且不同 → reject entire resolution：
  `P9_PATCH_CONFLICTS_WITH_RAW`

必须至少影响 1 个 null fact，否则 NO_EFFECT。

---

## 18. Value normalization

P9 不 canonicalize fiscal semantics。

只做：

- trim
- whitespace collapse（用于比较）
- 原始 submitted value保留到 resolution `value`

Resolved fact的 effective value使用 submitted trimmed value。

Period/unit/scope不翻译、不转换标准 enum。

Statement class例外：固定 enum。

---

## 19. Effective field precedence / overlap

P9 v1 active resolutions若影响同一 fact / same field：

### same effective value

允许兼容重叠。

Resolved fact记录所有 resolution IDs（sorted）。

### different effective value

不得靠 specificity/time猜 winner。

materialization失败：

`P9_RESOLUTION_CONFLICT`

Resolution revision必须通过 supersedes chain消除旧 active assignment。

---

## 20. Supersession graph

每 resolution最多：

- 0 或 1 `supersedes_resolution_id`

要求：
- superseded ID存在；
- same document；
- same review task/issue；
- compatible target/action family；
- 不允许 cycle；
- 一个 resolution最多一个 active child。

若两个不同 children supersede同一 parent：

`P9_RESOLUTION_CONFLICT`

Active resolution：
没有被有效 child supersede的 terminal record。

所有历史文件保留。

---

## 21. Evidence refs

Resolution必须至少 1 个 evidence ref。

Allowed：

### P6_EVIDENCE

```json
{"type":"P6_EVIDENCE","evidence_id":"..."}
```

必须存在当前 P6 evidence。

### P5_CELL

```json
{
  "type":"P5_CELL",
  "table_id":"...",
  "cell_id":"..."
}
```

必须：
- table存在；
- cell存在；
- cell source_words非空；
- bbox有效。

P9 从 P5 cell自动取得 page/source words。

不允许：
- arbitrary page quote
- arbitrary filesystem path
- URL
- unsupported free-text evidence

---

## 22. Evidence-to-target constraints

### FACT_FIELD

至少一个 evidence ref必须：
- 是该 fact自己的 P6 evidence；
或
- 是该 fact所在 table 的 P5 cell。

### TABLE_COLUMN_FIELD

至少一个 P5_CELL必须属于：
- same table
- ideally matching column；若 cell role/header geometry不匹配 column，仍允许 reviewer引用同 table明确 header cell，但所有 evidence记录必须保留，不做猜测。

### TABLE_FIELD

evidence refs必须全部属于 same table（P5 cell或table内 fact evidence）。

### TABLE_STATEMENT_CLASS

至少一个 evidence ref来自 same table。

### ISSUE attestation

evidence来自 supporting resolutions，不单独自由引用。

---

## 23. Evidence pages

caller不直接填写 authoritative evidence_pages。

P9从 validated evidence refs自动派生：

- sorted unique page numbers

写入 resolution。

若 caller payload包含 evidence_pages：
必须与派生值完全一致，否则拒绝。

---

## 24. Before / after and explicit prior overlay state

caller不提供 authoritative `before`。

### 24.1 base_active_resolution_ids

提交时 P9 store必须先读取/验证当前 immutable resolution set，计算当前 active terminal resolution IDs：

- sorted
- unique
- caller不可传入 authoritative value

persist到：

`base_active_resolution_ids`

### 24.2 base_overlay_set_hash_before

```text
SHA256(
 document_sha256
 + "\0" + base_validation_report_sha256
 + "\0" + P9_POLICY_VERSION
 + "\0" + "\0".join(base_active_resolution_ids)
)
```

persist到：

`base_overlay_set_hash_before`

该 hash明确绑定“本 resolution 提交前 reviewer看到的 overlay state”。

### 24.3 before

P9自动从：

- immutable base raw facts；
- `base_active_resolution_ids` 指定的 prior overlay state；

重新计算：

### before
- target identity
- affected fact IDs
- affected count
- base raw values
- current effective values（若已有 active overlays）

### after
- submitted semantic value
- expected affected fact count

resolution文件持久化 computed before/after。

这样 reviewer不能伪造 prior state，也不需要用 `reviewed_at` 推断执行顺序。

### 24.4 Historical state validation

loader必须验证：

- every `base_active_resolution_id` exists（除初始空集）；
- resolution自身不在 prior set；
- prior set内部不存在一个 resolution supersede另一个仍被同时声明 active；
-若当前 resolution声明 `supersedes_resolution_id`，该 parent必须存在于 prior active set；
- attestation每个 supporting_resolution_id必须存在于 prior active set；
- resolution dependency graph（base-state refs + supersedes refs）不得形成 cycle；
- `base_overlay_set_hash_before` 可重算一致；
- `before` 可用指定 prior set重算一致。

未来新增/后续 supersede不会改变历史 resolution的 prior-state contract。

---

## 25. Immutable resolution persistence

路径：

`resolutions/<resolution_id>.json`

write：
- canonical JSON
- UTF-8 no BOM
- LF
- exclusive create

若已存在：
- bytes完全相同 → idempotent reuse
- bytes不同 → `P9_RESOLUTION_STORE_CORRUPT`

不允许覆盖 existing resolution file。

---

## 26. Review base manifest

`review_manifest.json` 至少：

- schema_version
- policy_version
- document_sha256
- catalog_sha256
- base_validation_status
- base_validation_report_sha256
- review_task_count
- supported_task_count
- unsupported_task_count
- input_fingerprints
- queue_file
- queue_sha256

manifest / queue在创建后 immutable。

---

## 27. ResolvedFact contract

每个 P6 raw fact完整保留，并新增：

```json
{
  "...raw fields...": "...",
  "effective_period_label": "2024年度",
  "effective_unit": "人民币百万元",
  "effective_scope": null,
  "effective_statement_class": null,
  "overlay_resolution_ids": ["..."]
}
```

规则：

- raw_* 字段 byte/semantic unchanged
- effective period = raw period if non-null else overlay
- effective unit = raw unit if non-null else overlay
- effective scope = raw scope if non-null else overlay
- statement class only from table classification overlay
- overlay_resolution_ids sorted stable

---

## 28. overlay_set_hash

从 active terminal resolution IDs：

```text
SHA256(
 document_sha256
 + "\0" + base_validation_report_sha256
 + "\0" + P9_POLICY_VERSION
 + "\0" + "\0".join(sorted(active_resolution_ids))
)
```

如果无 resolutions：
仍有 stable zero-overlay hash。

---

## 29. Snapshot persistence

snapshot：

`snapshots/<overlay_set_hash>/`

写入：
- resolved_facts.jsonl
- resolved_issues.jsonl
- resolution_report.json
- snapshot_manifest.json

atomic temp dir → final。

final存在：
- full semantic/tamper validation
- valid → reuse
- invalid → block，不覆盖

---

## 30. Resolved issue states

每个 base REVIEW issue生成一条 resolved issue state：

```json
{
  "issue_id": "...",
  "reason_code": "...",
  "base_state": "REVIEW",
  "resolved_state": "RESOLVED",
  "reviewability": "SUPPORTED",
  "active_resolution_ids": [],
  "metrics_before": {},
  "metrics_after": {},
  "explanation": "..."
}
```

resolved_state：
- RESOLVED
- UNRESOLVED
- UNSUPPORTED
- CONFLICT

---

## 31. Overlay-aware re-validation

P9 不修改 P7 report。

P9 生成独立：

`resolution_report.json`

并复用 `validation.policy` 公共常量。

### 31.1 Period coverage

基于：

`effective_period_label`

计算 ratio。

`RAW_PERIOD_COVERAGE_LOW` resolved iff：

- fact_count < MIN_FACTS_FOR_SEMANTIC_COVERAGE；或
- effective period ratio >= `PERIOD_REVIEW = 0.10`

0.10–0.50 仍可保留 warning语义，但 REVIEW issue视为 resolved。

### 31.2 Unit coverage

`RAW_UNIT_COVERAGE_LOW` resolved iff：

- fact_count < minimum；或
- effective unit ratio >= `UNIT_REVIEW = 0.02`

### 31.3 Ambiguity

RAW_*_AMBIGUOUS：

只有 valid active `ATTEST_ISSUE_RESOLVED` 才 resolved。

Coverage提高不能自动消除 ambiguity。

### 31.4 Core statement coverage

Base P7 report已有：

`core_statement_signals`

P9增加 active TABLE_STATEMENT_CLASS overlays。

Resolved signal set：

- base true classes
- reviewed BALANCE/INCOME/CASHFLOW classes

`CORE_STATEMENT_COVERAGE_LOW` resolved iff signal_count >= 2。

OTHER 不增加。

### 31.5 Unsupported issue

永远 unresolved / unsupported。

---

## 32. Base FAIL / BLOCKED carry-through

虽然 P9 v1 prepare会拒绝 FAIL/BLOCKED base，resolved report仍定义：

- BLOCKED > FAIL > REVIEW_REQUIRED > PASS

不得通过 overlay把 base blocking/failure降级。

---

## 33. resolved validation status

若 base PASS且无 review tasks：
PASS。

若 base REVIEW_REQUIRED：

- any CONFLICT → REVIEW_REQUIRED
- any UNSUPPORTED → REVIEW_REQUIRED
- any UNRESOLVED → REVIEW_REQUIRED
- all base REVIEW issues RESOLVED → PASS

Base warnings不阻止 PASS。

### resolved_reuse_eligible

true iff：

- resolved_validation_status == PASS
- base compatibility == COMPATIBLE
- base blocking=0
- base failure=0
- fingerprints valid
- no resolution conflict

---

## 34. Resolution report contract

至少：

```json
{
  "schema_version": "p9-resolution-report-v1",
  "policy_version": "p9-review-policy-v1",
  "document_sha256": "...",
  "overlay_set_hash": "...",
  "base_validation_status": "REVIEW_REQUIRED",
  "resolved_validation_status": "PASS",
  "resolved_reuse_eligible": true,
  "base_review_issue_count": 1,
  "resolved_review_issue_count": 1,
  "unresolved_review_issue_count": 0,
  "unsupported_review_issue_count": 0,
  "conflict_issue_count": 0,
  "active_resolution_count": 4,
  "effective_metrics": {
    "period_nonnull_ratio": 0.12,
    "unit_nonnull_ratio": 0.04,
    "scope_nonnull_ratio": 0.07,
    "core_statement_signals": {}
  },
  "base_warning_issue_count": 2,
  "input_fingerprints": {}
}
```

---

## 35. Resolved ParsedDataRecord

P9提供纯 helper：

```python
build_resolved_parsed_data_record(
    snapshot,
    slot: FilingSlotKey,
    artifact_path: str,
) -> ParsedDataRecord
```

不写 Registry。

### parser_version

aggregate string包含：

- P3
- P5
- P6
- P7
- P9

### schema_version

`p9-resolved-view-v1`

### validation_status

resolved_validation_status。

### compatibility

继承 base P7 compatibility。

### parse_run_id

```text
SHA256(
 document_sha256
 + "\0" + base P7 policy/version identity
 + "\0" + overlay_set_hash
 + "\0" + P9_POLICY_VERSION
)
```

因此不同 overlay set是不同 parsed run。

---

## 36. Registry boundary

P9本身禁止：

`registry.register_parsed_data(...)`

只返回 record。

P10 Skill可在未来：
- review完成
- materialize
- 检查 resolved PASS
- 显式注册 resolved ParsedDataRecord

P9不提前编排。

---

## 37. No-op / idempotency

### prepare

相同 base：
- existing valid manifest/queue → reuse
- mismatch/tamper → block

### submit

同规范化 payload：
- same resolution_id
- same bytes
- idempotent

### materialize

相同 active resolution set：
- same overlay_set_hash
- same snapshot bytes
- reuse

---

## 38. Tamper validation

### base

所有 upstream loaders PASS + fingerprints match。

### manifest / queue

重新生成 queue并 semantic equality。

### resolution

- schema
- base_active_resolution_ids / base_overlay_set_hash_before recompute
- historical prior-state dependency DAG / cycle validation
- before state recompute from explicit prior set
- ID recompute
- task exists
- issue/reason match
- evidence re-resolve
- target re-resolve
- before/after recompute
- reviewed_at/reviewer validation
- supersession graph validation

### snapshot

重新从 base + active resolutions materialize：
- resolved_facts exact equality
- resolved_issues exact equality
- report exact semantic equality
- snapshot manifest hashes match

tamper：

`P9_ARTIFACT_INCOMPLETE_OR_CORRUPT`

---

## 39. Error codes

至少：

- P9_CATALOG_INVALID
- P9_DOCUMENT_NOT_FOUND
- P9_BASE_ARTIFACT_INVALID
- P9_BASE_ARTIFACT_CHANGED
- P9_BASE_STATUS_NOT_REVIEWABLE
- P9_TASK_NOT_FOUND
- P9_TASK_UNSUPPORTED
- P9_INVALID_RESOLUTION
- P9_TARGET_NOT_FOUND
- P9_EVIDENCE_INVALID
- P9_PATCH_CONFLICTS_WITH_RAW
- P9_RESOLUTION_NO_EFFECT
- P9_RESOLUTION_CONFLICT
- P9_SUPERSESSION_INVALID
- P9_RESOLUTION_STORE_CORRUPT
- P9_ARTIFACT_INCOMPLETE_OR_CORRUPT
- P9_PERSIST_FAILED

---

## 40. Public API

```python
prepare_review_overlay(
    project_root: str | Path,
    catalog_path: str | Path,
    document_sha256: str,
    review_root: str | Path,
) -> ReviewOverlayArtifact
```

```python
submit_resolution(
    review_dir: str | Path,
    submission: ResolutionSubmission,
) -> ReviewResolution
```

```python
list_review_tasks(review_dir) -> tuple[ReviewTask, ...]
```

```python
list_resolutions(review_dir) -> tuple[ReviewResolution, ...]
```

```python
materialize_resolved_view(
    review_dir: str | Path,
) -> ResolvedSnapshot
```

```python
load_resolved_snapshot(
    snapshot_dir,
    review_dir,
) -> ResolvedSnapshot
```

```python
build_resolved_parsed_data_record(
    snapshot,
    slot,
    artifact_path,
) -> ParsedDataRecord
```

---

## 41. Local CLI

P9提供 deterministic local CLI，供未来 P10 Skill调用。

入口：

`python -m financial_filing_data_foundation.review.cli`

subcommands：

- prepare
- tasks
- submit
- resolutions
- materialize
- report

CLI：

- 不调用 Codex
- 不调用 network
- JSON stdout only
- diagnostics stderr
- resolution input使用 explicit JSON file/string
- 不读取任意 secret

P10只负责编排 reviewer reasoning，不重实现 overlay persistence。

---

## 42. Package structure

```text
src/financial_filing_data_foundation/
  review/
    __init__.py
    models.py
    queue.py
    evidence.py
    store.py
    resolve.py
    cli.py
```

不修改 P8 MCP package。

---

## 43. Performance gates

代表 CN/HK accepted artifacts：

### prepare first load
- CN <=20s
- HK <=20s

与 P8 trusted bundle同量级，因为需要 P3/P5/P6/P7 semantic loaders。

### prepare reuse
<=2s

### submit one resolution
<=2s

### materialize
- CN <=10s
- HK <=10s

### load snapshot semantic validation
- CN <=10s
- HK <=10s

不包含 reviewer思考时间。

---

## 44. Determinism

相同：

- base artifacts
- resolution immutable set

必须：

- review_queue byte-identical
- resolution canonical bytes identical
- overlay_set_hash identical
- resolved_facts byte-identical
- resolved_issues byte-identical
- resolution_report semantic identical
- resolved parse_run_id identical

不得使用：
- random UUID
- implicit current time
- filesystem order

---

## 45. Immutability acceptance

P9 operation前后 snapshot：

- catalog
- P3
- P5
- P6
- P7

SHA/size/mtime必须全部 unchanged。

允许变更：
仅 `review_root`。

---

## 46. Unit tests

至少：

1. P7 PASS → empty queue
2. P7 REVIEW → task per REVIEW issue
3. warnings not tasks
4. FAIL rejected
5. BLOCKED rejected
6. stable review task ID
7. supported action mapping
8. unsupported reason remains unsupported
9. catalog path security inherited
10. fingerprint drift blocked
11. SET_PERIOD fact
12. SET_PERIOD table-column
13. SET_UNIT fact
14. SET_UNIT table
15. SET_SCOPE fact/table
16. raw non-null same → no-effect
17. raw non-null different → conflict with raw
18. no affected fact → no-effect
19. statement table classification
20. P6 evidence validation
21. P5 cell evidence validation
22. evidence wrong table blocked
23. evidence pages derived
24. reviewer validation
25. timezone-aware timestamp
26. stable resolution ID
27. idempotent resolution submit
28. immutable resolution tamper blocked
29. supersede valid
30. supersede unknown blocked
31. supersede cycle blocked
32. competing children conflict
33. overlapping same value okay
34. overlapping different values conflict
35. zero-overlay snapshot
36. effective raw value precedence
37. period coverage issue unresolved
38. period coverage issue resolved >=0.10
39. unit coverage resolved >=0.02
40. ambiguity cannot resolve without attestation
41. ambiguity attestation support validation
42. core signal base+reviewed >=2
43. unsupported issue remains review
44. resolved PASS
45. resolved reuse eligibility
46. build resolved ParsedDataRecord
47. resolved parse_run_id deterministic
48. snapshot dual-root determinism
49. snapshot tamper blocked
50. base artifact immutable
51. no PDF open
52. no network/AI/MCP SDK import
53. CLI stdout JSON only
54. CN live queue count
55. HK live queue count
56. evidence-grounded live CN resolution
57. live overlay does not modify raw
58. P8 accepted package/source unchanged

---

## 47. Live acceptance semantics

### CN 600519 FY2024

Base：
- P7 status = REVIEW_REQUIRED
- REVIEW tasks = **1**
- reason = RAW_PERIOD_COVERAGE_LOW
- warning context = 2

P9 acceptance必须：

1. deterministic queue task_count=1；
2. base raw facts=2177；
3. 提交至少一个**人工确认/evidence-grounded** period resolution；
4. resolution evidence必须来自 current P5/P6；
5. resolved facts保持 `raw_*` unchanged；
6. 至少一个 null period fact获得 effective_period_label；
7. 是否达到 global 0.10 threshold以实际 evidence覆盖为准，不得为了 PASS 批量猜；
8. 如果覆盖不足，resolved status诚实保持 REVIEW_REQUIRED。

### HK 00700 FY2024

Base REVIEW tasks = **4**：

- CORE_STATEMENT_COVERAGE_LOW
- RAW_PERIOD_COVERAGE_LOW
- RAW_UNIT_AMBIGUOUS
- RAW_UNIT_COVERAGE_LOW

P9 acceptance：
- queue count = 4
- reviewability/action mapping正确
- 不要求为了测试伪造足够 resolution使其 PASS
- 可以保持 unresolved
- 不得人工 dismissal。

### Synthetic golden

必须构造 deterministic synthetic document：
- base REVIEW_REQUIRED
- evidence-grounded period/unit/table classification resolutions
- all REVIEW issues resolved
- resolved status PASS
- resolved_reuse_eligible=true
- build resolved ParsedDataRecord成功

因此完整“REVIEW_REQUIRED → PASS”能力由 synthetic golden证明，live不靠猜测造假。

---

## 48. P9 acceptance outputs

Acceptance evidence至少记录：

- design baseline SHA
- production candidate SHA
- queue hashes
- base fingerprints
- CN/HK queue counts
- live resolution IDs
- overlay_set_hash
- resolved fact hashes
- raw/base immutability snapshot
- synthetic transition PASS
- full suite count
- no network/AI check

---

## 49. Security / scope

P9 resolution payload不得包含：

- file paths
- URLs
- shell commands
- SQL
- Python code
- credentials

justification仅审计文本，max 4000 chars。

P9 production不执行 justification内容。

---

## 50. P9 Issue Log

初始：无。

### P9-ISSUE-003 — Immutable resolution before-state was not reconstructible from timestamp/supersession alone

Resolution design requires persisted `before` state and later semantic recomputation. During store implementation preparation it became clear that wall-clock `reviewed_at` is audit metadata, not a safe execution-order primitive, and independent/concurrent resolutions may not have a total order in the supersession graph.

Without an explicit prior overlay set, a later loader cannot prove which active overlays existed when a resolution was submitted, so `before` could not be deterministically recomputed.

Approved solution:
1. store computes current active terminal set before validating/persisting a new resolution；
2. persist sorted `base_active_resolution_ids`；
3. persist deterministic `base_overlay_set_hash_before` over document/base-report/policy/prior IDs；
4. caller cannot override these fields；
5. compute `before` from base raw + explicit prior set, never from timestamp ordering；
6. superseded parent must be in the prior set；
7. attestation supporting resolutions must be in the prior set；
8. loader validates prior-set membership, supersession consistency, dependency DAG/cycles, hash and recomputed before；
9. same caller submission is idempotent only when submitted against the same prior overlay state。

No P9 resolution-store production code existed before this amendment.

Affected gates: P9-D / P9-E / P9-F / P9-J / P9-L.

发现问题必须：

```text
STOP
→ root cause
→ update design/22 + design/23 if affected
→ commit/push design amendment
→ invalidate affected evidence
→ fix
→ rerun
```

---

## 51. Exit

Independent Acceptance PASS：

- P9 → DONE
- P10 Codex Skill design authorized

P10 production不得在 P9 acceptance期间开始。

P11 SEC provider继续禁止提前进入。
