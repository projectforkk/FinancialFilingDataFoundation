# 07 — P1 Identity / Registry / Incremental Planner 实施计划

状态：**DESIGN BASELINE — P1 EXECUTION PLAN**

前置：P0_DONE

P1 设计：`design/06-p1-identity-registry-planner-design.md`

---

## 1. P1-A — Baseline / Branch

1. main 必须包含 P0 closeout。
2. main 必须包含 P1 design baseline。
3. 创建正式开发分支：
   `task/p1-identity-registry-planner`
4. 工作区干净。
5. 不使用 destructive reset/clean。

Gate A：**P1_READY_FOR_DEVELOPMENT**

---

## 2. P1-B — Domain Models

实现：

- CompanyRef
- FilingRequirement
- FilingPolicy
- FilingSlotKey
- FilingIdentity
- SourceMetadata
- planner action/reason enums

要求：

- immutable/frozen value objects；
- deterministic serialization；
- strict validation；
- amended 不改变 slot key。

Gate B：domain tests PASS。

---

## 3. P1-C — SQLite Registry Foundation

实现：

- DB initialization
- PRAGMA user_version=1
- documents
- document_locations
- filing_bindings
- parsed_data
- required indexes
- transaction boundaries

要求：

- stdlib sqlite3；
- no ORM dependency；
- version > 1 拒绝；
- no destructive migration。

Gate C：schema/persistence tests PASS。

---

## 4. P1-D — Document Registration

实现：

`register_document(path, source, expected_identity)`

要求：

- SHA256；
- file_size / mtime；
- PDF lightweight open/page_count；
- content-addressed documents；
- multi-location same SHA；
- source provenance independent of binding via `document_sources`；
- optional binding；
- provenance；
- source immutable；
- idempotent repeat registration；
- changed file content 更新 location，而不删除旧 content history。

Gate D：registration tests PASS。

---

## 5. P1-E — Parsed Data Registry / Reuse Evaluator

实现：

- register parsed record
- list slot parse records
- explicit `PlannerReusePolicy`
- compatibility checks
- validation/blocking checks
- accepted schema policy
- parser-version defect invalidation
- material-change check
- multiple reusable document SHA ambiguity handling

要求：

- parser_version change alone does not invalidate；
- invalidation rule must be explicit；
- no silent fallback。

Gate E：reuse-policy tests PASS。

---

## 6. P1-F — Incremental Planner

实现：

- required filing set
- local candidate resolution
- build_plan
- deterministic reason codes
- actions:
  - REUSE_DATA
  - PARSE_LOCAL
  - DOWNLOAD_AND_PARSE
  - REVIEW_REQUIRED
  - BLOCKED

Planner 不执行：

- parse
- download
- network
- Dayu

Gate F：planner decision matrix tests PASS。

---

## 7. P1-G — Focused / Integration Tests

完整覆盖 `design/06` 第 17 节要求。

重点场景：

```text
Reusable parsed → REUSE_DATA
No reusable + one local → PARSE_LOCAL
No reusable + no local → DOWNLOAD_AND_PARSE
Parsed SHA != current local SHA → PARSE_LOCAL
Multiple distinct local SHA → REVIEW_REQUIRED
Multiple reusable parsed SHA without unique local evidence → REVIEW_REQUIRED
Conflict binding → non-guessing result
```

另验证：

- SQLite reopen deterministic；
- source immutable；
- no network / no Dayu import；
- P0 tests regression PASS。

Gate G：all P0 + P1 tests PASS。

---

## 8. P1-H — Code Review

检查：

- scope limited to P1；
- no P2 implementation；
- identity conflict resolution implemented as design；
- SQLite invariants；
- deterministic planner；
- no filename identity guessing；
- no parser execution；
- no acquisition execution；
- no Dayu/Docling/Torch/AI；
- source immutable；
- tests satisfy matrix。

结论：

- PASS → P1_READY_FOR_ACCEPTANCE
- CHANGES_REQUIRED → 先修正；若发现设计问题，先更新设计再修代码。

---

## 9. P1-I — Acceptance Freeze

固定：

- design baseline SHA
- production commit SHA
- review commit SHA
- Python/runtime
- exact test commands
- registry fixture commands
- expected action matrix

Freeze 后若设计改变，原 freeze 自动失效。

---

## 10. P1-J — Independent Acceptance

独立执行者不得修改 production/tests/config/design。

必须独立验证：

1. P0 regression；
2. P1 focused suite；
3. SQLite create/reopen；
4. registration idempotency；
5. exact planner matrix；
6. source material change；
7. ambiguous local non-guessing；
8. parser version non-invalidation；
9. explicit defect invalidation；
10. no network/Dayu/heavy path；
11. source immutability；
12. deterministic repeated plan。

Final verdict：

`PASS / FAIL / BLOCKED`

---

## 11. P1-K — State Closeout

仅 Independent Acceptance = PASS 后：

- acceptance evidence 入库；
- PROJECT_STATUS → P1_DONE；
- merge P1 branch → main；
- 才允许开始 P2 design。

---

## 12. 问题处置

### P1-ISSUE-001 — Registry public export omission

首次 P1-G test collection 发现：

- `ValidationStatus` 已在 `registry.models` 定义；
- `registry.__init__` 未公开导出；
- planner/tests 按稳定 package surface 导入时产生 `ImportError`；
- 测试尚未进入业务断言。

根因：P1 package public surface 未在原设计中明确列出全部跨模块稳定类型。

批准解决方案：

1. 在 `design/06` 明确 registry public exports；
2. 仅补充缺失的 public re-export，不改变 domain/schema/planner semantics；
3. 重新执行受影响的 P1-G full focused/regression suite；
4. 如果继续发现新问题，重复 design-first 流程。

受影响 Gate：P1-B / P1-G；P1-C SQLite schema 不受影响。

### P1-ISSUE-002 — Source provenance tied too tightly to identity binding

在开发后复核中发现：调用者可能已经知道官方 `SourceMetadata`，但暂时还没有足够证据提供 `expected_identity`。原实现只在创建 `filing_bindings` 时保存 source 字段，这会导致“有 provenance、无 identity”场景丢失来源信息。

根因：source provenance 与 filing identity binding 被建模在同一持久化路径。

批准解决方案：

1. 新增 `document_sources` 表，以 `(document_sha256, provider, source_id)` 为主键；
2. 只要 `source` 存在，无论是否有 `expected_identity`，都必须幂等保存 provenance；
3. source 不自动推断 filing slot；
4. `filing_bindings` 可保留 source snapshot，但不再承担唯一 provenance 存储职责；
5. 增加无 identity + 有 source 的 persistence/idempotency 测试；
6. 重新执行 P1-C / P1-D / P1-G，并重新 Code Review。

### P1-ISSUE-003 — Unsupported registry schema is plan-level blocker

设计复核确认：高于当前支持版本的 SQLite `user_version` 会导致 Registry 无法安全打开，因此不能生成某个 filing item 的伪 `BLOCKED` 结果。

批准解决方案：

- Registry 初始化直接抛结构化 `RegistrySchemaUnsupported`；
- 调用/验收层将其判定为 execution `BLOCKED`；
- 禁止 silent downgrade / destructive rewrite。

当前实现已采用该异常语义；需在验收中明确验证。

任何 Gate 发现问题且找到解决办法：

```text
STOP
→ root cause
→ update design
→ commit design baseline
→ assess affected gates
→ rerun affected gates
→ continue
```

禁止“先改代码、后补设计”。

---

## 13. 执行顺序

```text
P1-A Baseline / Branch
↓
P1-B Domain Models
↓
P1-C SQLite Registry
↓
P1-D Document Registration
↓
P1-E Parsed Registry / Reuse
↓
P1-F Planner
↓
P1-G Tests
↓
P1-H Code Review
↓
P1-I Acceptance Freeze
↓
P1-J Independent Acceptance
↓
P1-K Closeout
```

禁止跨 Gate。
