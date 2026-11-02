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

## 3. FilingIdentity

```text
market
company_id
filing_type
fiscal_year
raw_fiscal_period
amended
```

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
