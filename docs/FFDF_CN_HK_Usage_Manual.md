# Financial Filing Data Foundation (FFDF) CN/HK 详细使用手册

**文档状态：FINAL / CN-HK PRODUCTION USE**
**适用仓库：`projectforkk/FinancialFilingDataFoundation`**
**项目根目录：`D:\Codex\FinancialFilingDataFoundation`**
**基线提交：`80b9a1a35af8877b9bab040554616c31dbc5055b`**
**适用市场：CN（中国大陆）、HK（香港）**
**编制日期：2026-11-05**

> 本手册面向日常使用、研究调用、数据准备、Review 处理和本地维护。FFDF 当前已经正式收口为 CN/HK 财报数据基盘；US SEC Provider、UK Provider 均不属于当前生产范围。

## 1. 手册目标与阅读方式

FFDF 不是“打开一个 GUI 就完成全部工作”的桌面软件，而是一个由本地数据资产、Python 生产代码、独立 Dayu acquisition runtime、独立 MCP runtime、P9 Review Overlay 和 P10 Research Integration 组成的数据基盘。

推荐按角色阅读：

- **只做财报研究**：重点阅读第 5、6、9、10、11、12、15 节。
- **负责准备新财报数据**：重点阅读第 7、8、13、16 节。
- **处理 `REVIEW_REQUIRED`**：重点阅读第 10 节。
- **维护项目**：重点阅读第 3、4、14、16、17、18 节。

日常研究的主路径是：

```text
已有 CN/HK 数据
  -> P8 MCP 读取原始结构化数据和 Evidence
  -> 必要时 P9 Review Overlay 做受控语义确认
  -> P10 冻结当前研究规范并校验证据账本
  -> Codex / reasoning host 完成研究输出
```

如果所需财报不在本地 catalog，则先进入 Data Preparation：

```text
缺少目标财报
  -> P1/P2 确认 identity / local raw
  -> 必要时 Dayu CNINFO / HKEX acquisition
  -> P3-P7 解析与验证
  -> 将通过验证的 artifact 加入 P8 catalog
  -> 再进入研究流程
```

## 2. 最终生产范围与明确边界

### 2.1 支持范围

生产代码公开的最终市场集合是：

```python
SUPPORTED_MARKETS = ("CN", "HK")
```

含义：

- `CN`：中国大陆正式财报，正式来源以 CNINFO 等已验收路径为准。
- `HK`：香港正式财报，正式来源以 HKEX News 等已验收路径为准。

### 2.2 不支持范围

以下能力不属于当前项目：

- US SEC HTML / Inline XBRL / XBRL Provider；
- UK filing provider；
- 任意其他未明确授权市场；
- MCP 内部调用 AI API；
- 生产解析代码调用远程 AI；
- 自动猜测期间、单位、scope、metric semantics；
- 通过 P9 修改原始数值或原始 metric text；
- 将 `REVIEW_REQUIRED` 静默当作 `PASS`；
- 将未验收能力伪装成已实现能力。

P10 capability manifest 中继续保留：

```text
P11_SEC_PROVIDER = UNAVAILABLE
```

这是兼容性契约，不代表 US 功能“待自动开启”。

## 3. 本机目录与 Runtime 架构

### 3.1 Canonical project root

所有 FFDF 自有代码、workspace、runtime、依赖和测试临时目录应位于：

```text
D:\Codex\FinancialFilingDataFoundation
```

不要在项目外部随意创建临时数据副本并作为生产输入。

### 3.2 三套运行环境

| Runtime | 路径 | 用途 |
|---|---|---|
| FFDF main | `D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe` | 生产代码、P1-P7、P9、P10、单元测试 |
| Dayu acquisition | `D:\Codex\FinancialFilingDataFoundation\runtimes\ffdf-dayu-2115c86\.venv\Scripts\python.exe` | CNINFO/HKEX discovery/download |
| MCP | `D:\Codex\FinancialFilingDataFoundation\runtimes\ffdf-mcp-2.3.0\.venv\Scripts\python.exe` | P8 MCP stdio server |

三套 runtime **不要混装依赖**。

### 3.3 Dayu source pin

Dayu source checkout：

```text
D:\Codex\FinancialFilingDataFoundation\dependencies\dayu-agent
```

验收 pin：

```text
commit: 2115c86d5a9027bb51cbbc8a4d0175080732e4e6
package: dayu-agent 0.1.4
```

Dayu source 必须保持 clean；若 commit 漂移或 worktree dirty，应视为 runtime boundary 问题，而不是自动继续。

### 3.4 Source-mode 运行原则

FFDF main runtime 不是 editable-install 模式。执行 FFDF Python 模块前，应绑定源码：

```powershell
$root = 'D:\Codex\FinancialFilingDataFoundation'
$env:PYTHONPATH = "$root\src"
$py = "$root\.venv\Scripts\python.exe"
```

如果忘记设置 `PYTHONPATH`，可能看到：

```text
ModuleNotFoundError: No module named 'financial_filing_data_foundation'
```

这通常不是“没有部署”，而是启动方式错误。

## 4. 部署自检与健康检查

### 4.1 Git 基线检查

```powershell
$root = 'D:\Codex\FinancialFilingDataFoundation'
Set-Location $root

git status --short --branch
git log -1 --oneline
```

正常应看到 `main...origin/main` 且没有未提交改动。

### 4.2 主 Runtime 自检

```powershell
$root = 'D:\Codex\FinancialFilingDataFoundation'
$env:PYTHONPATH = "$root\src"
& "$root\.venv\Scripts\python.exe" -c `
  "from financial_filing_data_foundation.identity import SUPPORTED_MARKETS; print(SUPPORTED_MARKETS)"
```

预期：

```text
('CN', 'HK')
```

### 4.3 Dayu Doctor

Dayu runner **必须使用脚本路径直接执行**，不要使用 `-m financial_filing_data_foundation.acquisition.dayu_runner`，因为 Dayu runtime 与 main runtime 是隔离的。

```powershell
$root = 'D:\Codex\FinancialFilingDataFoundation'
$dayuPy = "$root\runtimes\ffdf-dayu-2115c86\.venv\Scripts\python.exe"
$runner = "$root\src\financial_filing_data_foundation\acquisition\dayu_runner.py"
$dir = "$root\.t\dayu-doctor"
New-Item -ItemType Directory -Force -Path $dir | Out-Null

$req = "$dir\doctor.request.json"
$resp = "$dir\doctor.response.json"
$json = '{"protocol_version":"ffdf-dayu-acquisition-v1","operation":"doctor","request_id":"manual-doctor","dayu_source_dir":"D:\\Codex\\FinancialFilingDataFoundation\\dependencies\\dayu-agent"}'
[System.IO.File]::WriteAllText($req, $json, (New-Object System.Text.UTF8Encoding($false)))

if (Test-Path $resp) { Remove-Item $resp -Force }
& $dayuPy $runner --request $req --response $resp
Get-Content $resp -Raw
```

关键结果应包括：

```text
status = OK
protocol_version = ffdf-dayu-acquisition-v1
dayu_package_version = 0.1.4
dayu_source_clean = true
docling_conversion_used = false
network_used = false   # doctor 本身不访问网络
```

**注意：request JSON 必须为 UTF-8 无 BOM。** 带 BOM 的 JSON 会被严格拒绝。

### 4.4 MCP Smoke Test

```powershell
$root = 'D:\Codex\FinancialFilingDataFoundation'
$mcpPy = "$root\runtimes\ffdf-mcp-2.3.0\.venv\Scripts\python.exe"
$env:PYTHONPATH = "$root\src"

& $mcpPy "$root\tests\integration\mcp_stdio_check.py" `
  --project-root $root `
  --source-root $root `
  --catalog 'workspace/mcp/p8-live-catalog.json' `
  --output "$root\.t\mcp-smoke.json"
```

当前已验收结果：

- protocol：`2026-07-28`；
- 11 个 MCP tools；
- CN/HK 两份 live document 可读取；
- search/page/section/table/fact/evidence/validation 均可用。

## 5. 当前 Live Catalog

日常读取入口：

```text
workspace/mcp/p8-live-catalog.json
```

当前 catalog 中的示例数据：

| 市场 | Ticker | 财年 | 类型 | Document SHA256 |
|---|---|---:|---|---|
| CN | 600519 | 2024 | ANNUAL | `5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30` |
| HK | 00700 | 2024 | ANNUAL | `70f529984a87ef7f46d9e1db26bb9ef27eef9c01d29c59aabf69e557b479a6a0` |

Catalog schema：

```json
{
  "schema_version": "p8-mcp-catalog-v1",
  "documents": [
    {
      "document_sha256": "<64 lowercase/hex sha256>",
      "market": "CN",
      "ticker": "600519",
      "fiscal_year": 2024,
      "filing_type": "ANNUAL",
      "p3_artifact_dir": "workspace/.../p3/<sha>",
      "p5_artifact_dir": "workspace/.../p5/<sha>",
      "p6_artifact_dir": "workspace/.../p6/<sha>",
      "p7_artifact_dir": "workspace/.../p7/<sha>"
    }
  ]
}
```

规则：

- catalog 路径应位于 project root 内；
- artifact 路径使用 project-root-relative path；
- `document_sha256` 不可重复；
- `(market, ticker, fiscal_year, filing_type)` 不可重复；
- catalog 只引用已经存在、可验证的 P3/P5/P6/P7 artifact；
- 不要通过 catalog “伪造”缺失财报。

## 6. P8 MCP：日常读取财报数据

### 6.1 启动 MCP Server

```powershell
$root = 'D:\Codex\FinancialFilingDataFoundation'
$mcpPy = "$root\runtimes\ffdf-mcp-2.3.0\.venv\Scripts\python.exe"
$env:PYTHONPATH = "$root\src"

& $mcpPy -m financial_filing_data_foundation.mcp.server `
  --project-root $root `
  --catalog 'workspace/mcp/p8-live-catalog.json'
```

Server 使用 **stdio**。一般由 MCP client 启动，而不是手工打开后长期挂在窗口中。

MCP server 的生产边界：

- read-only；
- deterministic；
- 无任意文件系统浏览；
- 无网络访问；
- 无 AI API；
- 无 mutation。

### 6.2 11 个 MCP 工具速查

| 工具 | 主要用途 | 主要参数 |
|---|---|---|
| `ffdf_list_documents` | 列出本地财报 | `market?`, `ticker?`, `fiscal_year?` |
| `ffdf_get_document` | 获取单份文档汇总 | `document_sha256` |
| `ffdf_search_document` | 搜索 P3 FTS | `document_sha256`, `query`, `limit=10` |
| `ffdf_read_pages` | 读取物理页文本与基础几何 | `document_sha256`, `page_nos`，最多 10 页 |
| `ffdf_list_sections` | 列出 P3 sections | `document_sha256` |
| `ffdf_list_tables` | 列出 P5 tables | `document_sha256`, `page_no?`, `offset=0`, `limit=50` |
| `ffdf_get_table` | 获取表格 rows/cells | `document_sha256`, `table_id`, `max_rows=100` |
| `ffdf_list_raw_facts` | 列出 P6 RawFact | `document_sha256`, `page_no?`, `metric_contains?`, `offset`, `limit` |
| `ffdf_get_fact` | 获取单个 RawFact | `document_sha256`, `raw_fact_id` |
| `ffdf_get_evidence` | 获取 Evidence | `document_sha256`, `evidence_id` |
| `ffdf_get_validation` | 获取 P7 validation | `document_sha256`, `include_issues`, `severity?`, `offset`, `limit` |

### 6.3 推荐查询顺序

研究一家公司时，不要一开始遍历全部 pages/tables/facts。建议：

```text
1. ffdf_list_documents
2. ffdf_get_document
3. ffdf_get_validation
4. 根据研究问题：
   a. search -> pages/sections
   b. list_tables -> get_table
   c. list_raw_facts -> get_fact -> get_evidence
5. 如果语义仍不确定，再考虑 P9
```

### 6.4 典型研究查询

**查某公司本地有哪些财报**：

```text
ffdf_list_documents(market="CN", ticker="600519")
```

**搜索“营业收入”出现位置**：

```text
ffdf_search_document(
  document_sha256="5299...4a30",
  query="营业收入",
  limit=10
)
```

**查看某页**：

```text
ffdf_read_pages(
  document_sha256="5299...4a30",
  page_nos=[1, 2, 3]
)
```

**按 metric 过滤 RawFact**：

```text
ffdf_list_raw_facts(
  document_sha256="5299...4a30",
  metric_contains="营业收入",
  offset=0,
  limit=50
)
```

拿到 `raw_fact_id` 后：

```text
ffdf_get_fact(document_sha256="...", raw_fact_id="...")
ffdf_get_evidence(document_sha256="...", evidence_id="...")
```

## 7. 数据准备：什么时候需要 Acquisition

P10 研究流程遇到本地缺少目标财报时，应返回：

```text
P10_DATA_PREPARATION_REQUIRED
```

这时不要让 P10 自己联网下载，也不要用邻近期间替代。

上游 Data Preparation 顺序：

```text
目标 FilingSlot
  -> Registry 检查是否已有 raw document
     -> 已有：REUSED_LOCAL
     -> 没有：Dayu discovery
        -> 0 candidate：NOT_FOUND
        -> 多 candidate / metadata conflict：REVIEW_REQUIRED
        -> 唯一 candidate：download
  -> staging PDF validation
  -> content-addressed raw store
  -> Registry registration
  -> acquisition receipt
  -> P3-P7 parse / validation
  -> P8 catalog
```

## 8. Dayu Acquisition 使用原则

### 8.1 Provider 映射

| 市场 | Provider |
|---|---|
| CN | `cninfo` |
| HK | `hkexnews` |

允许 host 已在生产代码中固定白名单。不要通过修改 URL 绕过 host 校验。

### 8.2 Production API

Acquisition 的公开生产 API 包括：

```python
from financial_filing_data_foundation.acquisition import (
    AcquisitionRequest,
    DayuRuntimeDescriptor,
    DayuSubprocessAdapter,
    RawDocumentStore,
    acquire_slot,
)
```

重要：当前最终基线没有“万能的一条 acquisition CLI”。上游 ingestion 由库 API/编排流程调用；不要直接把 Dayu runner 当作业务 CLI 使用。

### 8.3 Dayu runner 只负责窄协议

`dayu_runner.py` 支持的 runner protocol 包括 doctor/discovery/download 等窄操作。FFDF production adapter 会：

- 生成 request/response JSON；
- 调用独立 Dayu Python；
- 验证 protocol version 和 request_id；
- 验证 provider/ticker/期间；
- 验证源 host；
- 验证下载 SHA256/size；
- 提交 raw store；
- 写 acquisition receipt。

不要手工跳过这些验证只保留“下载 PDF”。

### 8.4 关键 Acquisition 状态

| 状态 | 含义 |
|---|---|
| `REUSED_LOCAL` | Registry 已有可信 raw document |
| `DOWNLOADED` | 已下载、校验并注册 |
| `NOT_FOUND` | 未发现精确候选 |
| `REVIEW_REQUIRED` | 候选歧义、metadata conflict 或 local ambiguity |
| `BLOCKED` | local conflict/drift 等阻塞状态 |

## 9. `REVIEW_REQUIRED` 的正确理解

`REVIEW_REQUIRED` **不等于整份财报不可用**。

仍可以根据具体研究问题使用：

- RawFact；
- Evidence；
- reconstructed table；
- page text；
- validation issue context；
- 已验证的 P9 effective fields。

但不能：

- 宣称整份文档已经 canonical reusable；
- 隐藏 unresolved semantic fields；
- 对依赖 unresolved semantics 的计算给出确定答案；
- 用 P9 改写错误的 raw numeric value。

如果发现 P5/P6 本身抽取错误，应回到 parser Design-First 修复，而不是用 P9 覆盖。

## 10. P9 Review Overlay：受控人工/Codex 复核

### 10.1 P9 能做什么

支持的 action：

```text
SET_PERIOD
SET_UNIT
SET_SCOPE
CLASSIFY_TABLE_STATEMENT
ATTEST_ISSUE_RESOLVED
```

支持 Reviewer：

```text
CODEX
HUMAN
```

P9 不负责：

- 修改 raw numeric value；
- 修改 parsed numeric value；
- 修改 raw metric name；
- 任意自由文本“拍脑袋修复”。

### 10.2 CLI 入口

```powershell
$root = 'D:\Codex\FinancialFilingDataFoundation'
$env:PYTHONPATH = "$root\src"
$py = "$root\.venv\Scripts\python.exe"
```

P9 CLI 不提供传统 argparse help 页面；错误输出是 machine-readable JSON。

### 10.3 Prepare Review Overlay

```powershell
& $py -m financial_filing_data_foundation.review.cli prepare `
  --project-root $root `
  --catalog 'workspace/mcp/p8-live-catalog.json' `
  --document-sha256 '<DOCUMENT_SHA256>' `
  --review-root 'workspace/review'
```

输出会给出 `review_dir`、task count 等。

### 10.4 查看 Review Tasks

```powershell
& $py -m financial_filing_data_foundation.review.cli tasks `
  --review-dir '<REVIEW_DIR>'
```

重点查看每个 task 的：

- `review_task_id`；
- `reason_code`；
- `reviewability`；
- `supported_actions`；
- `required_evidence_types`；
- `page_no` / `table_id` / `raw_fact_ids` / `evidence_ids`。

只有 `reviewability = SUPPORTED` 且证据满足时才提交 resolution。

### 10.5 提交 Resolution

建议先写 JSON 文件：

```json
{
  "review_task_id": "<TASK_ID>",
  "action": "SET_UNIT",
  "target": {
    "target_type": "TABLE_FIELD",
    "table_id": "<TABLE_ID>",
    "field": "unit"
  },
  "value": "CNY",
  "evidence_refs": [
    {
      "type": "P5_CELL",
      "table_id": "<TABLE_ID>",
      "cell_id": "<CELL_ID>"
    }
  ],
  "reviewer_type": "HUMAN",
  "reviewer_id": "operator",
  "reviewed_at": "2026-11-05T08:00:00+09:00",
  "justification": "Unit is explicitly stated in the table header.",
  "supersedes_resolution_id": null
}
```

**上例只是结构模板。** `action`、`target`、evidence 类型必须使用当前 task 真正允许的内容，不要照抄一个不匹配的模板。

提交：

```powershell
& $py -m financial_filing_data_foundation.review.cli submit `
  --review-dir '<REVIEW_DIR>' `
  --input-file 'D:\Codex\FinancialFilingDataFoundation\workspace\review-input.json'
```

### 10.6 查看 Resolutions

```powershell
& $py -m financial_filing_data_foundation.review.cli resolutions `
  --review-dir '<REVIEW_DIR>'
```

### 10.7 Materialize / Report

```powershell
& $py -m financial_filing_data_foundation.review.cli materialize `
  --review-dir '<REVIEW_DIR>'

& $py -m financial_filing_data_foundation.review.cli report `
  --review-dir '<REVIEW_DIR>'
```

P9 snapshot 是 durable reviewed state；原始 P5/P6 数据仍保持不变。

## 11. P10 Research Integration：研究规范绑定

P10 的职责不是替你做财务判断，而是：

- 冻结当前 runtime research specification；
- 验证规范没有 drift；
- 建立 ResearchContext；
- 暴露 capability manifest；
- 校验 Evidence Ledger。

### 11.1 研究开始前的原则

每次研究都应先读取当前研究规范，而不是把旧的固定问题清单固化到 FFDF 代码里。

顺序：

```text
当前研究规范文件
  -> freeze-spec
  -> verify-spec
  -> build-context
  -> reasoning host 动态决定查哪些 P8/P9 数据
  -> 建立 evidence ledger
  -> validate-ledger
  -> 输出研究结果
```

### 11.2 P10 CLI 环境

```powershell
$root = 'D:\Codex\FinancialFilingDataFoundation'
$env:PYTHONPATH = "$root\src"
$py = "$root\.venv\Scripts\python.exe"
```

P10 CLI 的命令只有：

```text
freeze-spec
verify-spec
build-context
validate-ledger
```

`--help` 不作为普通帮助页面使用；非法参数按 machine-readable JSON error 返回。

### 11.3 Freeze Spec

假设研究规范位于 project root 内：

```text
workspace/research-inputs/company-analysis-rules.md
workspace/research-inputs/question-list.md
```

请求文件 `freeze-request.json`：

```json
{
  "files": [
    {
      "logical_name": "rules",
      "relative_path": "workspace/research-inputs/company-analysis-rules.md"
    },
    {
      "logical_name": "questions",
      "relative_path": "workspace/research-inputs/question-list.md"
    }
  ]
}
```

运行：

```powershell
Get-Content '.\workspace\research-inputs\freeze-request.json' -Raw | `
  & $py -m financial_filing_data_foundation.research.cli freeze-spec `
  --project-root $root
```

保存输出中的 `data`，其中包含：

- 文件 SHA256；
- 文件 size；
- `spec_bundle_hash`。

### 11.4 Verify Spec

输入结构：

```json
{
  "spec_bundle": {
    "schema_version": "p10-research-spec-bundle-v1",
    "files": [],
    "spec_bundle_hash": "..."
  }
}
```

运行：

```powershell
Get-Content '.\workspace\research-inputs\verify-request.json' -Raw | `
  & $py -m financial_filing_data_foundation.research.cli verify-spec `
  --project-root $root
```

如果研究规范已被修改，会显式失败，不允许静默刷新。

### 11.5 Build Context

```powershell
Get-Content '.\workspace\research-inputs\build-context-request.json' -Raw | `
  & $py -m financial_filing_data_foundation.research.cli build-context `
  --project-root $root `
  --catalog 'workspace/mcp/p8-live-catalog.json' `
  --p9-review-root 'workspace/review'
```

输入 JSON 仅包含：

```json
{
  "spec_bundle": { "...": "freeze-spec 输出的 data" }
}
```

### 11.6 Validate Evidence Ledger

请求结构：

```json
{
  "spec_bundle": { "...": "已冻结 spec bundle" },
  "ledger": {
    "schema_version": "<以当前 P10 schema 为准>",
    "research_context_id": "<BUILD_CONTEXT 返回值>",
    "spec_bundle_hash": "<SPEC_BUNDLE_HASH>",
    "entries": []
  }
}
```

运行：

```powershell
Get-Content '.\workspace\research-inputs\ledger-request.json' -Raw | `
  & $py -m financial_filing_data_foundation.research.cli validate-ledger `
  --project-root $root `
  --catalog 'workspace/mcp/p8-live-catalog.json' `
  --p9-review-root 'workspace/review'
```

研究输出中每个 FFDF 支持的关键 claim 应能追溯到 document/page/table/raw_fact/evidence/P9 resolution 等 identity。

## 12. Codex / Reasoning Host 的推荐工作流

### 12.1 第一步：确认数据是否存在

先调用：

```text
ffdf_list_documents
```

如果目标财报不存在：

```text
P10_DATA_PREPARATION_REQUIRED
```

不要让模型自己猜一个替代财报。

### 12.2 第二步：看 Validation

调用：

```text
ffdf_get_document
ffdf_get_validation
```

如果状态是 `REVIEW_REQUIRED`，继续看具体 issue，不要直接判定整份文档不可用。

### 12.3 第三步：按信息需求选工具

- 找文字披露：`ffdf_search_document` -> `ffdf_read_pages`
- 看财务表：`ffdf_list_tables` -> `ffdf_get_table`
- 找具体数字：`ffdf_list_raw_facts` -> `ffdf_get_fact`
- 证明数字来源：`ffdf_get_evidence`
- 语义字段不确定：进入 P9 Review

### 12.4 第四步：Derived Calculation

只有所有 operand 都具备以下条件才计算：

- numeric value 已知；
- period 已知；
- value role 已知；
- 必要 unit/dimension 已知；
- scope 已知；
- 没有 unresolved conflict；
- provenance 完整；
- operation 语义兼容。

不要从不兼容的累计值随意推 standalone quarter。

### 12.5 第五步：外部信息单独处理

行业、政策、估值、市场价格、竞争对手等可能来自 FFDF 外部。

这类来源属于：

```text
EXTERNAL_RUNTIME_SOURCE
```

不要冒充 P8/P9 Evidence，也不要写入 FFDF P10 ledger v1 作为内部 Evidence。

## 13. Native PDF Probe

P0 probe 可用于快速检查一份 PDF 是否适合轻量 native path：

```powershell
$root = 'D:\Codex\FinancialFilingDataFoundation'
$env:PYTHONPATH = "$root\src"
$py = "$root\.venv\Scripts\python.exe"

& $py -m financial_filing_data_foundation.probes.native_pdf_probe `
  'D:\path\to\filing.pdf' `
  --pretty `
  --output "$root\workspace\probe-result.json"
```

用途：

- page count；
- text/layout extraction feasibility；
- 基础 PDF 质量信号；
- 判断是否需要进一步处理。

不要把 probe 输出当作正式 P3-P7 artifact。

## 14. 测试与回归

### 14.1 Windows 必须使用短 basetemp

FFDF 的 P9 snapshot path 很长。Windows 下如果 pytest basetemp 太长，可能产生假失败：

```text
FileNotFoundError
P9_PERSIST_FAILED
```

标准执行方式：

```powershell
$root = 'D:\Codex\FinancialFilingDataFoundation'
$tmp = "$root\.t\u"

if (Test-Path $tmp) { Remove-Item -Recurse -Force $tmp }
New-Item -ItemType Directory -Force -Path $tmp | Out-Null

$env:TEMP = $tmp
$env:TMP = $tmp
$env:PYTHONPATH = "$root\src"

& "$root\.venv\Scripts\python.exe" -m pytest -q `
  --basetemp "$tmp\b" `
  tests/unit
```

项目收口时最终结果：

```text
445 passed
```

### 14.2 Compile Check

```powershell
$env:PYTHONPATH = "$root\src"
& "$root\.venv\Scripts\python.exe" -m compileall -q "$root\src"
```

### 14.3 Git Diff Check

```powershell
git diff --check
git status --short --branch
```

## 15. 日常使用：最简操作清单

### 15.1 只查已有财报

1. 确认 `workspace/mcp/p8-live-catalog.json` 存在。
2. MCP client 使用 dedicated MCP runtime 启动 server。
3. `ffdf_list_documents` 查目标 filing。
4. `ffdf_get_validation` 查看质量状态。
5. 根据问题调用 search/table/fact/evidence。
6. 需要受控语义确认时使用 P9。
7. 研究规范变化时重新执行 P10 freeze/verify/context。

### 15.2 新增一份财报

1. 确认目标 filing identity。
2. Registry 检查是否已有 local raw。
3. 缺失时通过 P2 acquisition / Dayu adapter 获取正式财报。
4. 完成 raw store + receipt + registry。
5. 执行 P3-P7 解析与验证。
6. 检查 artifact 完整性。
7. 将文档加入 `p8-live-catalog.json`。
8. 跑 P8 MCP smoke。
9. 再交给研究流程使用。

## 16. 数据、备份与 Git 的边界

非常重要：**Git 仓库不是完整数据备份。**

以下目录通常是运行数据/本地依赖并被 `.gitignore` 排除：

```text
workspace/
data/
cache/
dependencies/
runtimes/
worktrees/
.t/
t/
```

因此：

- `git push` 只保证代码、设计和受版本控制文档被保存；
- live artifact、raw document、runtime、Dayu source checkout 需要单独备份；
- 如果重装电脑，只 clone Git 仓库并不能恢复全部本地数据基盘。

建议至少单独备份：

```text
workspace/
data/
runtime-locks/
```

并记录 runtime rebuild 方法和 Dayu pin。

原始 source document 禁止被修改；如需重新解析，应生成新的下游 artifact，而不是覆盖 source。

## 17. 常见错误与处理

| 症状 / Reason | 常见原因 | 处理 |
|---|---|---|
| `ModuleNotFoundError: financial_filing_data_foundation` | 未设置 `PYTHONPATH` | `$env:PYTHONPATH="$root\src"` |
| MCP runtime 中缺主项目依赖 | runtime 隔离是设计要求 | 不要把 main 依赖装进 MCP runtime |
| Dayu runtime 里 `pymupdf` 缺失 | 错误使用 `-m` 加载 FFDF package init | 用 `dayu_runner.py` 脚本路径直接执行 |
| Dayu request 报 UTF-8 BOM | PowerShell 写 JSON 带 BOM | 使用 `UTF8Encoding($false)` |
| `DAYU_SOURCE_COMMIT_MISMATCH` | Dayu checkout 不在 pin | 恢复/重建指定 commit，不要猜测继续 |
| `DAYU_WORKTREE_DIRTY` | Dayu source 有改动 | 审查改动，保持 production pin clean |
| `SOURCE_HOST_NOT_ALLOWED` | URL 不在 CNINFO/HKEX 白名单 | 检查 discovery/provider，不要绕过校验 |
| `NO_CANDIDATE` | 指定 filing 未找到 | 核对公司、年份、期间和正式发布时间 |
| `ACQUISITION_CANDIDATE_AMBIGUOUS` | 多个精确候选 | 人工检查 source_id / filing metadata |
| `P8_CATALOG_INVALID` | catalog schema/path/duplicate 有问题 | 检查 relative paths、SHA 和 filing identity |
| `P8_INVALID_ARGUMENT` | SHA 或工具参数非法 | 按工具 schema 传参 |
| `REVIEW_REQUIRED` | 存在质量/语义问题 | 看具体 issue；可用证据仍可按边界使用 |
| `P10_DATA_PREPARATION_REQUIRED` | 本地没有目标财报 | 先走上游 ingestion |
| `P10_RESEARCH_SPEC_CHANGED` | freeze 后规范被修改 | 重新 freeze，建立新 research context |
| `P10_VISUAL_CAPABILITY_REQUIRED` | 仅结构化数据无法证明视觉关系 | 显式报告 gap，不猜测 |
| `P10_SEMANTIC_CAPABILITY_REQUIRED` | 需要未实现的 semantic resolver | 使用受控 P9 或报告 gap |
| `P10_UPSTREAM_INVALID` | 上游 artifact 不可信 | 回到上游修复，不静默 fallback |
| pytest 多个 P9 snapshot `FileNotFoundError` | Windows MAX_PATH | 使用 `$root\.t\u\b` 短 basetemp |

## 18. 安全与治理规则

任何维护都继续遵守：

```text
Design-First
no destructive reset
no force push
no source/raw mutation
no guessed fields
no MCP AI API
no remote AI in production parsing/acquisition
```

如果发现生产缺陷：

```text
发现问题
  -> STOP 当前 gate / workflow
  -> 确认事实和根因
  -> 更新对应设计
  -> 提交设计基线
  -> 修改代码/测试
  -> Code Review
  -> Regression / Acceptance
  -> 再继续
```

不要为了“快速跑通”而：

- 删除 validation；
- 修改 raw value；
- 放宽 host 白名单；
- 把 unsupported market 映射成 CN/HK；
- 把 `REVIEW_REQUIRED` 当 `PASS`；
- 让 P10 自动下载缺失数据；
- 让模型在缺证据时猜测。

## 19. Git 日常维护

### 19.1 更新代码

```powershell
Set-Location 'D:\Codex\FinancialFilingDataFoundation'
git fetch origin
git status --short --branch
git pull --ff-only
```

如果本地有未提交修改，不要直接覆盖。

### 19.2 提交文档/代码

```powershell
git diff --check
git status --short

git add <明确文件列表>
git diff --cached --check
git diff --cached --stat

git commit -m "docs: update FFDF usage manual"
git push origin main
```

不使用：

```text
git reset --hard
git push --force
```

除非未来治理明确重新授权，且不违反既有 accepted baseline。

## 20. 推荐的研究操作模板

### 20.1 财报研究前

```text
[ ] 当前研究规则已确定
[ ] 所需公司/年份/期间已明确
[ ] P8 catalog 中存在目标财报
[ ] document validation 已查看
[ ] 需要的 P9 durable state 已验证
[ ] 研究规范已 freeze / verify
```

### 20.2 研究过程中

```text
[ ] 先 structured evidence，后扩大读取范围
[ ] 每个关键数字保留 RawFact / Evidence 链
[ ] REVIEW_REQUIRED 按 issue 粒度判断
[ ] 不隐藏 unresolved semantic field
[ ] Derived calculation 的 operand 全部具备语义
[ ] 外部来源与 FFDF provenance 分离
```

### 20.3 研究结束

```text
[ ] 关键 FFDF claim 有 evidence ledger
[ ] validate-ledger = PASS
[ ] 没有把 run-local interpretation 写成 canonical data
[ ] 没有把 external source 写成 P8/P9 evidence
[ ] 没有把 unsupported capability 当作已实现
```

## 21. 管理员快速自检清单

```powershell
$root = 'D:\Codex\FinancialFilingDataFoundation'
Set-Location $root

# 1. Git
git status --short --branch

# 2. Main runtime
$env:PYTHONPATH = "$root\src"
& "$root\.venv\Scripts\python.exe" -c `
 "from financial_filing_data_foundation.identity import SUPPORTED_MARKETS; print(SUPPORTED_MARKETS)"

# 3. Compile
& "$root\.venv\Scripts\python.exe" -m compileall -q "$root\src"

# 4. Unit regression (short path)
$tmp = "$root\.t\u"
New-Item -ItemType Directory -Force -Path $tmp | Out-Null
$env:TEMP = $tmp
$env:TMP = $tmp
& "$root\.venv\Scripts\python.exe" -m pytest -q `
  --basetemp "$tmp\b" tests/unit

# 5. MCP smoke
$mcpPy = "$root\runtimes\ffdf-mcp-2.3.0\.venv\Scripts\python.exe"
& $mcpPy "$root\tests\integration\mcp_stdio_check.py" `
  --project-root $root `
  --source-root $root `
  --catalog 'workspace/mcp/p8-live-catalog.json' `
  --output "$root\.t\mcp-smoke.json"
```

全部通过后，可以认为当前本地 CN/HK 数据基盘处于可用状态。

## 22. 最终能力矩阵

| 能力 | 状态 |
|---|---|
| CN filing identity / acquisition / parsing | AVAILABLE |
| HK filing identity / acquisition / parsing | AVAILABLE |
| Local raw store / registry / incremental reuse | AVAILABLE |
| Native page / section / FTS | AVAILABLE |
| Table reconstruction | AVAILABLE |
| Raw facts + Evidence | AVAILABLE |
| Quality validation | AVAILABLE |
| P8 local read-only MCP | AVAILABLE |
| P9 durable review overlay | AVAILABLE |
| P10 dynamic research integration | AVAILABLE |
| PDF visual evidence service | UNAVAILABLE |
| Semantic Resolver production | UNAVAILABLE |
| Canonical Metric Layer | UNAVAILABLE |
| US SEC Provider | OUT_OF_SCOPE / UNAVAILABLE |
| UK Provider | OUT_OF_SCOPE / UNAVAILABLE |

## 23. 关键文件索引

| 文件 | 用途 |
|---|---|
| `README.md` | 项目入口与最终范围 |
| `PROJECT_STATUS.md` | 当前项目状态 |
| `design/30-project-final-cn-hk-scope.md` | CN/HK 最终范围契约 |
| `development/145-final-full-repository-consistency-review.md` | 全库设计/代码一致性 Review |
| `integration/p10/FFDF_RESEARCH_INTEGRATION.md` | P10 研究集成规则 |
| `workspace/mcp/p8-live-catalog.json` | 日常 P8 live catalog |
| `src/financial_filing_data_foundation/mcp/server.py` | P8 MCP server 和工具定义 |
| `src/financial_filing_data_foundation/review/cli.py` | P9 CLI |
| `src/financial_filing_data_foundation/research/cli.py` | P10 CLI |
| `src/financial_filing_data_foundation/acquisition/dayu_runner.py` | Dayu 窄协议 runner |

## 24. 结论

FFDF 当前已经完成本地部署并完成项目收口。日常使用应把它理解成：

> **CN/HK 正式财报的本地、确定性、可追溯数据基盘。**

研究者主要通过 P8 MCP 读取数据，通过 P9 处理受支持的 Review，通过 P10 将当前研究规范和证据链绑定起来；数据缺失时回到上游 Data Preparation，而不是在研究层静默联网或猜测。

保持这条边界，才能保证 FFDF 的核心价值：**财报解析一次、长期复用、证据可追溯、增量更新、异常显式暴露。**
