# 06 — P1 Identity / Registry / Incremental Planner 详细设计

状态：**DESIGN BASELINE — P1**

阶段：**P1 — Identity / Registry / Incremental Planner**

前置条件：

- P0 Independent Acceptance = PASS
- P0 state = DONE
- P0 closeout commit = `edff06b2b1138b50d742e92ce8b8df628c6d2c61`

---

## 1. P1 目标

P1 建立确定性的多年份 filing identity、Local Document Registry、Parsed Data Registry 与 Incremental Planner。

P1 必须能够在**不执行解析、不执行下载、不调用 Dayu、不调用网络**的前提下，为每个 required filing 生成稳定 action：

```text
REUSE_DATA
PARSE_LOCAL
DOWNLOAD_AND_PARSE
REVIEW_REQUIRED
BLOCKED
```

P1 的核心价值是把“是否需要重新解析/是否需要下载”变成可测试、可审计、可持久化的确定性决策。

---

## 2. P1 明确不做

P1 不实现：

- Dayu checkout / Dayu Adapter
- CNINFO / HKEX / SEC 网络访问
- PDF 内容解析
- section extraction
- table candidate / reconstruction
- OCR
- Docling
- Raw Facts / Evidence extraction
- MCP
- Skill
- Codex review
- investment analysis

`DOWNLOAD_AND_PARSE` 在 P1 只是 planner action，不执行下载或 parse。

---

## 3. Identity 设计冲突与解决

此前设计存在两个表述：

1. `design/02` 的 `FilingIdentity` 包含 `amended`；
2. `design/01` 的 `DocumentKey` 业务 identity 不包含 `amended`。

如果直接把 `amended` 放入 required filing 主键，修订版会被误当成额外 required filing。

P1 正式统一如下。

### 3.1 FilingSlotKey

Planner 的 required filing 单位：

```text
market
company_id
filing_type
fiscal_year
raw_fiscal_period
```

稳定串行化：

```text
{market}|{company_id}|{filing_type}|{fiscal_year}|{raw_fiscal_period}
```

`FilingSlotKey`：

- 不包含 filename；
- 不包含 local path；
- 不包含 SHA；
- 不包含 amended；
- 用于 required filing set、planner、registry 查询。

### 3.2 FilingIdentity

具体 filing 文档的业务身份候选：

```text
slot: FilingSlotKey
amended: bool | None
```

其中：

- `False`：明确非修订版；
- `True`：明确修订/更正版；
- `None`：P1 无足够证据确认。

`amended` 是 document variant 元数据，不改变 required slot。

### 3.3 Raw Document Identity

具体字节对象：

```text
document_sha256
```

同一 filing slot 可以存在多个不同 SHA 文档，例如原版与更正版。

P1 不允许仅凭“amended=True”猜测哪份是最终官方版本。

若同一 slot 存在多个不同 SHA 且 registry 无法确定唯一 active document，则 planner 输出 `REVIEW_REQUIRED`。

---

## 4. CompanyRef

最小字段：

```text
market
company_id
ticker
```

规则：

- `market` P1 首期允许 `CN` / `HK`；
- US identity/provider policy 留给 P11；
- `company_id` 是稳定业务 identity；
- `ticker` 是展示/查询字段，不作为唯一业务主键。

---

## 5. FilingPolicy / Required Filing Set

P1 不在 parser 内硬编码研究策略。

定义：

```python
FilingRequirement(
    filing_type: str,
    raw_fiscal_period: str,
)

FilingPolicy(
    requirements: tuple[FilingRequirement, ...],
)
```

CN/HK 可支持 period：

- Q1
- H1
- Q3
- FY

具体 request 要求哪些 period，由 `FilingPolicy` 明确给出。

Required filing set 生成规则：

1. `start_year <= end_year`；
2. year 从小到大；
3. 同年按 policy requirements 原始顺序；
4. 每个 requirement 生成一个 `FilingSlotKey`；
5. 重复 requirement 必须拒绝，不得静默去重。

---

## 6. Local Document Registry

P1 使用 SQLite，优先 stdlib `sqlite3`，不增加第三方 ORM。

Registry path 由调用者显式提供；生产默认建议放在 FFDF workspace/data 目录，测试使用临时 DB。

### 6.1 documents

内容对象表：

```text
document_sha256 PRIMARY KEY
file_size
page_count nullable
first_seen_at
```

同一 SHA 只保存一条 content record。

### 6.2 document_locations

文件位置表：

```text
path PRIMARY KEY
document_sha256
mtime_ns
last_seen_at
exists_flag
```

允许同一 SHA 对应多个路径。

不得因为 filename 相同判为同一文档。

### 6.3 filing_bindings

文档到 filing slot 的绑定：

```text
binding_id PRIMARY KEY
document_sha256
market
company_id
filing_type
fiscal_year
raw_fiscal_period
amended nullable
binding_status
source_provider nullable
source_id nullable
source_url nullable
source_title nullable
filing_date nullable
report_date nullable
acquired_at nullable
created_at
```

`binding_status`：

- `DECLARED`：调用者显式提供 expected identity；
- `SOURCE_CONFIRMED`：后续 provider/source metadata 可确认；
- `CONFLICT`：身份冲突，不得作为自动 local candidate。

P1 的 `register_document(... expected_identity=...)` 对显式 identity 建立 `DECLARED` binding。

没有 expected identity 时，只注册 content/location，不建立 filing binding。

---

## 7. register_document

接口：

```python
register_document(
    path: Path,
    source: SourceMetadata | None,
    expected_identity: FilingIdentity | None,
) -> RegisteredDocument
```

P1 行为：

1. resolve path；
2. 确认普通文件存在；
3. 计算 SHA256；
4. 获取 size / mtime；
5. PDF 时用轻量 open 检查 page count；不执行 P0 全量 probe；
6. 写/复用 `documents`；
7. upsert `document_locations`；
8. 若有 expected identity，写/复用 binding；
9. source metadata 存在时持久化 provenance；
10. 再次注册同一 path / same hash 必须幂等；
11. 源文件不得修改。

若 path 原来指向 SHA-A，之后内容变为 SHA-B：

- location 更新指向 SHA-B；
- SHA-A content record 保留用于历史追溯；
- planner 按当前 exists location + binding 计算；
- 不得覆盖历史 parsed record 的 source SHA。

---

## 8. Parsed Data Registry

记录至少：

```text
parse_run_id PRIMARY KEY
market
company_id
filing_type
fiscal_year
raw_fiscal_period
document_sha256
parser_version
schema_version
validation_status
blocking_issue_count
compatibility_status
artifact_path nullable
created_at
```

`validation_status`：

- PASS
- FAIL
- REVIEW_REQUIRED
- BLOCKED

`compatibility_status`：

- COMPATIBLE
- INCOMPATIBLE
- UNKNOWN

同一 slot 可保留多个历史 parse run。

Registry 不删除旧 run 来制造“当前唯一状态”。

---

## 9. Reuse Policy

`REUSE_DATA` 必须同时满足：

1. ParsedData record 存在；
2. `validation_status == PASS`；
3. `blocking_issue_count == 0`；
4. `compatibility_status == COMPATIBLE`；
5. schema version 被当前 policy 接受；
6. 未命中 parser defect invalidation rule；
7. 未发现 source document material change。

### 9.1 parser_version

parser_version 不同**本身不触发 reparse**。

只有 defect invalidation policy 明确命中时，旧 parse 才失效。

### 9.2 Material Change

P1 可确认的 material change：

- Parsed record 的 `document_sha256` 与当前 slot 唯一可用 local document SHA 不同。

此时不得 `REUSE_DATA`。

若当前 local slot 有多个不同 SHA 且无法唯一确定 active document：

`REVIEW_REQUIRED`

不得猜最新版本。

---

## 10. Local Candidate Resolution

对一个 slot：

### 10.1 无绑定文档

没有当前可用 binding/location：

`NO_LOCAL_DOCUMENT`

### 10.2 一个 distinct SHA

存在一个可用 distinct SHA：

`LOCAL_DOCUMENT_RESOLVED`

可用于 `PARSE_LOCAL`。

### 10.3 多路径，同 SHA

视为同一 raw document。

选择 canonical location 必须确定性：

1. `exists_flag=true`；
2. path 按 Unicode codepoint 升序；
3. 取第一条。

但 registry 输出同时保留全部 location 数量。

### 10.4 多个 distinct SHA

如果无法根据已持久化 source metadata 明确唯一 active document：

`REVIEW_REQUIRED`

P1 不实现“按标题猜修订版”或“按 mtime 猜最新”。

---

## 11. Incremental Planner

接口：

```python
build_plan(
    company: CompanyRef,
    start_year: int,
    end_year: int,
    policy: FilingPolicy,
) -> FilingPlan
```

Planner 只读 Registry，不执行 action。

### 11.1 决策顺序

对每个 `FilingSlotKey`：

```text
1. resolve current local document state
2. evaluate reusable parsed data
3. if reusable and no material change:
       REUSE_DATA
4. else if local state ambiguous/conflicting:
       REVIEW_REQUIRED
5. else if one local raw document resolved:
       PARSE_LOCAL
6. else:
       DOWNLOAD_AND_PARSE
```

这保持“reuse → local → download”的业务优先级，同时允许 local registry 提供 material-change 证据来阻止错误 reuse。

### 11.2 BLOCKED

P1 item 级 `BLOCKED` 仅用于确定性结构阻断，例如：

- registry 数据违反 invariant；
- slot binding 明确标记 `CONFLICT` 且无法归一；
- 数据库 schema/version 不受支持。

普通“没有数据/没有本地文件”不是 BLOCKED，应输出 `DOWNLOAD_AND_PARSE`。

---

## 12. Planner Item Contract

至少：

```json
{
  "slot_key": "...",
  "market": "CN",
  "company_id": "...",
  "ticker": "600519",
  "filing_type": "ANNUAL_REPORT",
  "fiscal_year": 2024,
  "raw_fiscal_period": "FY",
  "action": "REUSE_DATA",
  "reason_code": "VALIDATED_COMPATIBLE_PARSED_DATA",
  "document_sha256": "...",
  "local_path": null,
  "parse_run_id": "...",
  "blocking_reasons": []
}
```

所有 action 必须有稳定 `reason_code`。

---

## 13. Reason Codes

P1 至少：

```text
VALIDATED_COMPATIBLE_PARSED_DATA
LOCAL_RAW_AVAILABLE
NO_REUSABLE_DATA_OR_LOCAL_RAW
PARSED_VALIDATION_NOT_PASS
PARSED_BLOCKING_ISSUES
PARSED_SCHEMA_INCOMPATIBLE
PARSED_COMPATIBILITY_UNKNOWN
PARSER_DEFECT_INVALIDATED
SOURCE_MATERIAL_CHANGE
LOCAL_DOCUMENT_AMBIGUOUS
LOCAL_BINDING_CONFLICT
REGISTRY_SCHEMA_UNSUPPORTED
```

不得使用自由文本作为唯一决策原因。

---

## 14. SQLite Schema / Migration

P1 schema version：

`registry_schema_version = 1`

使用：

`PRAGMA user_version = 1`

要求：

- 新 DB 可自动初始化；
- version=1 可打开；
- version>1 必须拒绝并返回/抛出明确 `REGISTRY_SCHEMA_UNSUPPORTED`；
- 不得静默 downgrade；
- 不得 destructive migration。

---

## 15. Determinism / Idempotency

以下必须稳定：

- `FilingSlotKey` serialization；
- required filing ordering；
- same file registration；
- same registry state 的 `build_plan`；
- canonical local path selection；
- reuse evaluation；
- SQLite reopen 后 plan 不变。

不得依赖：

- dict/set 非稳定顺序；
- filesystem enumeration order；
- wall-clock time 做 planner decision；
- filename 文本猜 identity。

---

## 16. P1 Package 建议

```text
src/financial_filing_data_foundation/
  identity/
    models.py
  registry/
    sqlite_registry.py
    models.py
  planner/
    models.py
    incremental.py
```

P1 可以按实现简洁性调整文件拆分，但不得改变职责边界。

---

## 17. P1 测试要求

至少覆盖：

1. FilingSlotKey 稳定性；
2. amended 不改变 slot key；
3. required filing set 顺序；
4. duplicate policy rejection；
5. register same file idempotent；
6. same SHA multi-path；
7. changed path content updates location SHA without deleting history；
8. unbound document 不被 planner 当 local candidate；
9. reusable parsed data → REUSE_DATA；
10. validation non-PASS → 不 reuse；
11. blocking_issue_count > 0 → 不 reuse；
12. schema incompatible → 不 reuse；
13. parser defect invalidation → 不 reuse；
14. same SHA local + reusable parse → REUSE_DATA；
15. different local SHA vs parsed SHA → PARSE_LOCAL；
16. one local doc + no reusable data → PARSE_LOCAL；
17. no parsed + no local → DOWNLOAD_AND_PARSE；
18. multiple distinct local SHA → REVIEW_REQUIRED；
19. binding conflict → BLOCKED / REVIEW_REQUIRED according to invariant；
20. repeated build_plan deterministic；
21. DB close/reopen plan deterministic；
22. source file immutable；
23. no network / no Dayu invocation。

---

## 18. P1 Acceptance Gate

Independent Acceptance 必须验证：

- P0 production files 未被破坏；
- P1 tests 全部 PASS；
- SQLite registry persistence 正确；
- planner precedence 正确；
- DATA_READY/reusable scenario 不 parse/download；
- local raw scenario 不 download；
- absent scenario 输出 DOWNLOAD_AND_PARSE；
- ambiguous local scenario 不猜；
- parser_version change alone 不触发 reparse；
- defect invalidation 可触发 reparse；
- source material change 阻止错误 reuse；
- repeated plan byte-for-byte comparable（排除生成时间等非决策字段，最好 planner 不输出动态时间）；
- P1 无网络访问；
- P1 无 Dayu/Docling/Torch/AI；
- source raw files unchanged。

---

## 19. P1 退出条件

只有 Independent Acceptance = PASS 后：

- P1 → DONE；
- 才允许进入 P2 Acquisition Provider 详细设计/开发。

P1 未 PASS 前不得实现 Dayu acquisition adapter。
