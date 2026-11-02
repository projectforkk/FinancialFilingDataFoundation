# 02 — Incremental Planner 与 Acquisition 详细设计

状态：DESIGN BASELINE

## 1. 核心顺序

每个目标 filing 必须严格按以下优先级决策：

```text
Parsed Data 可复用？
  ├─ YES → REUSE_DATA
  └─ NO
      ↓
Local Raw Document 可用？
  ├─ YES → PARSE_LOCAL
  └─ NO
      ↓
Official Acquisition
      ↓
DOWNLOAD_AND_PARSE
```

不得先下载再检查数据源；不得先解析再检查 reuse。

## 2. Required Filing Set

输入：
- market
- company identity
- start_year
- end_year
- filing policy

输出：
- required filing identities

CN/HK 首期至少支持：
- FY
- H1
- Q1
- Q3

是否要求某类 period 由 FilingPolicy 决定，不在 parser 内硬编码研究策略。

US 后续：
- 10-K
- 10-Q
- 20-F / 6-K 等由 provider policy 决定。

## 3. FilingSlotKey 与 FilingIdentity

Required filing / planner 的稳定业务槽位使用：

```text
FilingSlotKey =
market
company_id
filing_type
fiscal_year
raw_fiscal_period
```

具体 filing 文档身份为：

```text
FilingIdentity = FilingSlotKey + amended(bool | None)
```

`amended` 是 document variant 元数据，不改变 required slot；具体字节对象仍由 `document_sha256` 标识。

同一 slot 若存在多个不同 SHA 且无法依据 registry/source metadata 唯一确定 active document，planner 必须 `REVIEW_REQUIRED`，不得猜测。

业务主键不得依赖文件名。

## 4. REUSE_DATA 判定

只有同时满足才允许：

- ParsedData record 存在；
- validation_status == PASS；
- blocking_issue_count == 0；
- schema compatible；
- source document identity 未发生 material change；
- 未命中已知 parser defect invalidation rule。

parser_version 不同本身不是强制 reparse 理由。

## 5. Local raw file 判定

Local Registry 按 identity + content hash 管理。

候选文件必须：
- 可打开；
- hash 可计算；
- identity 与目标 filing 不冲突。

不允许仅凭文件名中的“2024 年报”直接确认 identity。

## 6. Acquisition Provider

```python
class AcquisitionProvider(Protocol):
    name: str

    def discover_documents(
        self,
        company: CompanyRef,
        window: FilingWindow,
    ) -> list[DocumentCandidate]: ...

    def download_document(
        self,
        candidate: DocumentCandidate,
    ) -> DownloadedDocument: ...

    def source_metadata(
        self,
        candidate: DocumentCandidate,
    ) -> SourceMetadata: ...
```

## 7. Dayu Adapter

已核对 Dayu baseline：
`2115c86d5a9027bb51cbbc8a4d0175080732e4e6`

CN/HK 高层 `fins download` 会把：
- PDF acquisition
- Docling conversion

串在同一 single-filing workflow。

FFDF 不应直接调用该高层 workflow 作为纯 acquisition。

Adapter 只允许复用窄能力：
- CninfoDiscoveryClient
- HkexnewsDiscoveryClient
- 对应 candidate / profile discovery
- PDF download
- source metadata

Adapter 输出 PDF 后必须停止；不得隐式调用：
`convert_pdf_to_docling_json`。

### 7.1 Dayu 源码获取与版本锁定

FFDF **不得假设目标 PC 已经预装 Dayu**。

P2 实施时必须从 Git 获取 Dayu 上游源码，并固定到已批准 commit：

- repository: `noho/dayu-agent`
- baseline commit: `2115c86d5a9027bb51cbbc8a4d0175080732e4e6`

推荐方式：

1. 将 Dayu checkout 放在 FFDF 仓库之外的 dependency/workspace 目录；
2. checkout 到固定 commit；
3. 上游 checkout 视为只读依赖，不直接手工修改；
4. FFDF 自己实现 Dayu Acquisition Adapter；
5. Adapter 只调用 downloader/discovery 窄能力；
6. 不把 Dayu 高层 processing workflow 作为 acquisition API；
7. 不因为需要 downloader 就把 Docling 默认 parser path 引入 FFDF native parser runtime。

若 Dayu downloader 存在缺陷：

- 优先在 FFDF Adapter 层做兼容；
- 若必须修改 Dayu，上游修改必须先形成设计变更，再通过受控 fork / 新 commit 管理；
- FFDF 随后显式更新 pin 到经过 review/acceptance 的新 commit；
- 禁止在本机 dependency checkout 中直接手改而不留下 Git 可追踪版本。

### 7.2 Dayu Runtime 隔离

已核对 pinned Dayu `pyproject.toml`：正式 package dependencies 包含 Docling / Docling Core 等重依赖。

同时已核对 Python package initializer：

- `dayu.fins.__init__` 会导入 `tools`；
- `dayu.fins.downloaders.__init__` 会同时导入 CN / HK / SEC downloader；
- `dayu.fins.pipelines.__init__` 会导入 CN / SEC pipeline。

因此不能把“只 import `cninfo_downloader.py` / `hkexnews_downloader.py`”等同于一个可靠的轻量依赖环境，也不得通过修改 upstream `__init__.py` 或自定义 source-loader 绕过正常 package 语义。

P2 正式采用：

```text
FFDF main runtime
  NO Dayu / NO Docling
      |
      | subprocess JSON protocol
      v
Dedicated Dayu acquisition runtime
  pinned upstream package
  CNINFO / HKEX narrow runner
      |
      v
raw PDF only
```

Dayu acquisition runtime 中 Docling package **可能因 upstream dependency 存在或被 import graph 加载**，但 P2 runner 禁止调用 Docling conversion / high-level workflow，且不得产生 Docling JSON artifact。

FFDF main runtime 必须继续保持 Dayu / Docling absent。

详细 contract 见：

- `design/08-p2-acquisition-provider-design.md`
- `design/09-p2-implementation-plan.md`

## 8. Download 去重

下载后必须：
- 计算 sha256；
- 写 source metadata；
- 检查同 hash 是否已存在；
- 相同文件不重复保存大对象。

## 9. Planner 输出

示例：

```json
{
  "company": "600519",
  "market": "CN",
  "items": [
    {"period": "2021_FY", "action": "REUSE_DATA"},
    {"period": "2022_FY", "action": "REUSE_DATA"},
    {"period": "2023_FY", "action": "PARSE_LOCAL"},
    {"period": "2024_FY", "action": "DOWNLOAD_AND_PARSE"}
  ]
}
```

Planner 不执行 action，只做确定性决策。

## 10. 验收重点

- DATA_READY 时不 parse；
- local raw 存在时不 download；
- 两者都无时才 download；
- Dayu CN/HK adapter 路径不得触发 Docling conversion；
- 同一 request 重复执行时 action 稳定、幂等。
