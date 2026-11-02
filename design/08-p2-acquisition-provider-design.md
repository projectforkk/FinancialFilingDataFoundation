# 08 — P2 Acquisition Provider 详细设计

状态：**DESIGN BASELINE — P2**

阶段：**P2 — Acquisition Provider**

前置条件：

- P0 = DONE
- P1 = DONE
- P1 Independent Acceptance = PASS
- accepted P1 merge commit = `1cb6e88be318c0a1424d74ee601c336075361cd6`

P2 只负责 **CN / HK 官方财报 acquisition**。

US SEC provider 保持在 **P11**，不得提前进入 P2。

---

## 1. P2 目标

P2 建立可复用、可审计、可隔离的官方原始财报获取能力。

对 P1 planner 已经判定为：

`DOWNLOAD_AND_PARSE`

的 CN / HK filing slot，P2 必须能够：

1. 调用官方来源 discovery；
2. 找到与目标 slot 精确匹配的候选；
3. 下载官方 PDF；
4. 独立校验 PDF / SHA256；
5. 将原始文件写入 FFDF 控制的 content-addressed raw store；
6. 保存完整 acquisition receipt；
7. 调用 P1 Registry 注册 raw document / source metadata / filing identity；
8. 下载结束后 **STOP**；
9. 不进入 Docling；
10. 不执行 PDF parsing；
11. 不实现 table / fact / evidence extraction。

---

## 2. P2 明确不做

P2 不实现：

- P3 page/section extraction；
- table candidate/reconstruction；
- OCR；
- Docling conversion；
- Raw Facts；
- Evidence extraction；
- MCP；
- Skill；
- Codex review；
- US SEC acquisition；
- investment analysis。

P2 的成功终点是：

```text
OFFICIAL RAW DOCUMENT
+ SHA256
+ SOURCE METADATA
+ ACQUISITION RECEIPT
+ P1 REGISTRY REGISTRATION
```

而不是 parsed document。

---

## 3. Dayu 上游固定基线

Dayu upstream：

- repository: `https://github.com/noho/dayu-agent`
- pinned commit: `2115c86d5a9027bb51cbbc8a4d0175080732e4e6`
- package version at baseline: `0.1.4`

P2 不允许使用浮动 branch / latest tag。

任何 Dayu pin 变更必须：

```text
problem / reason
→ design update
→ review new upstream commit
→ update pin
→ rerun affected P2 gates
```

---

## 4. Dayu import / dependency 事实

已核对 pinned upstream：

### 4.1 正式 package dependencies

Dayu `pyproject.toml` 正式依赖包含：

- requests
- httpx
- beautifulsoup4
- PyYAML
- aiohttp
- fastapi
- edgartools
- **docling**
- **docling-core**
- pandas
- lxml
- trafilatura
- 等

因此：

**禁止把 `pip install dayu-agent` 执行到 FFDF 主 `.venv`。**

否则会污染已经验收的 lightweight native parser runtime。

### 4.2 Package initializer 会扩大 import surface

即使业务代码直接写：

```python
from dayu.fins.downloaders.cninfo_downloader import CninfoDiscoveryClient
```

Python 仍会先执行 package initializer。

已核对：

- `dayu.fins.__init__` 导入 `tools`；
- `dayu.fins.downloaders.__init__` 同时导入 CN / HK / SEC downloader；
- `dayu.fins.pipelines.__init__` 导入完整 CN / SEC pipeline；
- 高层 pipeline 可继续到 Docling。

因此 P2 **不得假设**：

`checkout Dayu + 只装 httpx + PYTHONPATH import`

就是可靠的最小依赖方案。

### 4.3 设计结论

P2 使用：

**独立 Dayu acquisition runtime + subprocess process boundary**

而不是：

- 修改 Dayu `__init__.py`；
- 复制 Dayu downloader 到 FFDF；
- 自定义脆弱 source-loader 绕过 package init；
- 把 Dayu 装进 FFDF 主 runtime。

---

## 5. 双 Runtime 架构

```text
FFDF Main Runtime
Python ARM64
PyMuPDF
SQLite
NO Dayu
NO Docling
       |
       | subprocess JSON protocol
       v
Dayu Acquisition Runtime
pinned dayu-agent @ 2115c86...
network access
CNINFO / HKEX downloader
       |
       | raw PDF + JSON response
       v
FFDF controlled staging
       |
       | independent SHA/PDF validation
       v
Content-addressed Raw Store
       |
       v
P1 Registry
```

### 5.1 FFDF Main Runtime

继续使用：

`D:\Codex\FinancialFilingDataFoundation\.venv`

必须保持：

- Dayu 不安装在该 venv；
- Docling 不安装在该 venv；
- Torch 不安装在该 venv；
- acquisition adapter 本身不得直接 import Dayu。

**Module-visibility 检查必须从 FFDF repo / neutral workspace cwd 执行。** Python 会把当前工作目录放入 `sys.path`；如果进程 cwd 恰好位于 Dayu source checkout，即使主 venv 没安装 Dayu，也可能通过源码目录发现 `dayu`。因此 `find_spec('dayu') != None` 只有在安全 cwd 下才可作为主 runtime 污染证据。

### 5.2 Dayu Acquisition Runtime

P2 单独创建。

要求：

- 不依赖其它项目的 venv 作为正式运行基础；
- 可以参考现有环境，但正式 runtime 必须可从 Git pin 重建；
- 使用 Dayu 官方支持的 Python 版本；
- 在目标 Windows ARM64 主机上若 native ARM64 dependency tree 不可用，可使用独立 AMD64 Python 3.12 runtime；
- 不修改 system Python / PATH；
- runtime 路径必须显式配置；
- Dayu upstream checkout 与 runtime 都不得位于 FFDF Git tracked tree。

### 5.3 Docling 在 acquisition runtime 中的语义

由于 upstream package dependency，独立 Dayu runtime **可能安装 / import Docling 相关包**。

P2 Gate 禁止的是：

- 调用 Docling conversion；
- 调用 Dayu high-level download workflow；
- 生成 Docling JSON；
- 将 Docling 结果传回 FFDF；
- 将 Dayu runtime 当 parser。

不能把“package 因 upstream import graph 被加载”误判为“执行了 Docling conversion”。

但 FFDF 主 runtime 中 Docling 必须继续 absent。

---

## 6. Dayu checkout 管理

推荐 canonical dependency root：

`D:\Codex\dependencies\dayu-agent`

具体路径可配置，不能作为业务 identity。

P2 environment setup 必须：

1. 若目录不存在：
   - clone `noho/dayu-agent`；
2. fetch required commit；
3. checkout detached：
   - `2115c86d5a9027bb51cbbc8a4d0175080732e4e6`；
4. 核对：
   - `git rev-parse HEAD`
   - `git status --porcelain`
5. 要求 checkout clean；
6. 不在此 checkout 内开发 FFDF patch。

禁止：

- 手工改 upstream 文件；
- commit 到原 upstream checkout；
- 用未记录的本地 patch；
- force checkout 覆盖未知用户改动。

若 checkout 已存在但 dirty：

`BLOCKED_DEPENDENCY_WORKTREE_DIRTY`

不得自动 reset / clean。

---

## 7. 如果 Dayu 上游发现问题

优先顺序：

### 7.1 FFDF Adapter 兼容

若可以在不改变 upstream 行为的情况下处理：

- contract translation；
- extra validation；
- retry wrapper；
- candidate filtering；
- path handling；

则在 FFDF adapter 层解决。

### 7.2 必须修改 Dayu

若 downloader 本身确实需要修复：

1. STOP 当前 P2 Gate；
2. 写设计 issue；
3. 明确 upstream defect；
4. 建立受控 fork / branch；
5. 修改 Dayu；
6. 独立测试；
7. 形成新的 Git commit；
8. 更新 FFDF pinned commit；
9. 重新执行 Dayu runtime + P2 affected gates。

禁止直接修改 canonical dependency checkout 后继续。

---

## 8. P2 Package 结构

建议：

```text
src/financial_filing_data_foundation/
  acquisition/
    __init__.py
    models.py
    provider.py
    service.py
    raw_store.py
    dayu_adapter.py
    dayu_runner.py
    dayu_protocol.py
```

职责：

- `models.py`：FFDF acquisition domain models；
- `provider.py`：AcquisitionProvider Protocol；
- `service.py`：slot acquisition orchestration；
- `raw_store.py`：content-addressed raw persistence / receipt；
- `dayu_adapter.py`：FFDF main runtime subprocess adapter；
- `dayu_runner.py`：使用 Dayu runtime 执行 narrow downloader；
- `dayu_protocol.py`：JSON protocol schema / validation。

---

## 9. AcquisitionProvider Contract

P2 正式 contract：

```python
class AcquisitionProvider(Protocol):
    name: str

    def discover_documents(
        self,
        request: AcquisitionRequest,
    ) -> tuple[AcquisitionCandidate, ...]: ...

    def download_document(
        self,
        candidate: AcquisitionCandidate,
        staging_path: Path,
    ) -> RunnerDownloadedAsset: ...

    def source_metadata(
        self,
        candidate: AcquisitionCandidate,
        profile: ProviderCompanyProfile,
    ) -> SourceMetadata: ...
```

Provider 本身不 parse。

---

## 10. AcquisitionRequest

P2 以单个 required slot 为 acquisition 单位：

```text
company: CompanyRef
slot: FilingSlotKey
window_start: YYYY-MM-DD
window_end: YYYY-MM-DD
```

规则：

- company.market == slot.market；
- company.company_id == slot.company_id；
- P2 market 只允许 CN / HK；
- date window 必须由调用方显式提供；
- P2 不凭 fiscal year 猜 filing date window；
- raw_fiscal_period 必须能映射到 Dayu target period。

P2 首期允许：

- FY
- H1
- Q1
- Q3

若 provider 返回 Q2/Q4，不代表 P2 planner policy 自动要求它们。

---

## 11. Candidate Contract

至少：

```text
provider
provider_company_id
provider_company_name
ticker
source_id
source_url
source_title
language
filing_date
fiscal_year
fiscal_period
amended
remote_content_length nullable
etag nullable
last_modified nullable
```

Candidate 不包含本地最终 path。

---

## 12. Exact Slot Candidate Selection

Dayu downloader 自己会做 category/title filtering 和同 period version selection。

FFDF 仍必须二次校验：

1. provider 与 market 匹配；
2. ticker 匹配；
3. candidate.fiscal_year == slot.fiscal_year；
4. candidate.fiscal_period == slot.raw_fiscal_period；
5. source_id 非空；
6. source_url provider host 合法。

过滤后：

- 0 个 → `NOT_FOUND`
- 1 个 → 可下载
- >1 个 distinct source → `REVIEW_REQUIRED / ACQUISITION_CANDIDATE_AMBIGUOUS`

不得按列表第一条猜。

---

## 13. Official Source Host Guard

CNINFO 允许 host：

- `www.cninfo.com.cn`
- `cninfo.com.cn`
- `static.cninfo.com.cn`

允许 upstream 当前使用的 http/https。

HKEX 允许 host：

- `www1.hkexnews.hk`
- `hkexnews.hk`
- 必须为 https，除非后续官方源事实证明需要设计变更。

任何非 allowlist source URL：

`SOURCE_HOST_NOT_ALLOWED`

不得下载。

---

## 14. Dayu Narrow Runner

Runner 只允许主动调用：

### CN

- `CninfoDiscoveryClient`
- `CnReportQuery`
- `resolve_company`
- `list_report_candidates`
- `download_report_pdf`

### HK

- `HkexnewsDiscoveryClient`
- `CnReportQuery`
- 同样三个 method

Runner 禁止主动 import / call：

- `cn_download_filing_workflow`
- `cn_download_workflow`
- `CnPipeline`
- `convert_pdf_to_docling_json`
- `docling_export`
- 任何 process/rebuild/upload workflow。

由于 Python package initializer 可能 transitively import broader modules，Acceptance 的强制标准是：

**runner source/call graph 不进入 high-level workflow，且运行结果没有 Docling conversion / Docling artifact。**

---

## 15. Subprocess JSON Protocol

Protocol version：

`ffdf-dayu-acquisition-v1`

FFDF main runtime 通过：

`subprocess.run(..., shell=False, cwd=<explicit_safe_cwd>)`

调用 Dayu runtime。

`cwd` 必须显式设置为 FFDF-controlled neutral workspace，不得：

- 继承未知调用者 cwd；
- 使用 Dayu source checkout 作为 cwd；
- 依赖 cwd 把 Dayu source 注入 `sys.path`。

Dayu runner 必须从 dedicated runtime 已安装的 `site-packages` 解析 Dayu。

禁止：

- shell string 拼接；
- PowerShell eval；
- command injection；
- 解析人类日志作为业务结果。

### 15.1 Discover Request

```json
{
  "protocol_version": "ffdf-dayu-acquisition-v1",
  "operation": "discover",
  "request_id": "...",
  "market": "CN",
  "ticker": "600519",
  "window_start": "2025-01-01",
  "window_end": "2025-06-30",
  "target_periods": ["FY"]
}
```

### 15.2 Discover Response

```json
{
  "status": "OK",
  "profile": {},
  "candidates": []
}
```

### 15.3 Download Request

包含：

- exact candidate；
- FFDF-provided staging path。

### 15.4 Download Response

至少：

```text
status
candidate
dayu_temp_sha256
dayu_content_length
downloaded_at
staging_path
```

Runner 必须把 Dayu temp PDF copy 到 FFDF staging path 后删除自己的 Dayu temp file。

### 15.5 Response transport

业务 response 使用 JSON file / atomic write。

stdout / stderr 只作为 diagnostic log，不能作为唯一机器契约。

---

## 16. Runner Exit / Error Contract

至少 reason code：

```text
DAYU_RUNTIME_UNAVAILABLE
DAYU_SOURCE_COMMIT_MISMATCH
DAYU_WORKTREE_DIRTY
RUNNER_PROTOCOL_INVALID
RUNNER_TIMEOUT
DISCOVERY_FAILED
COMPANY_NOT_FOUND
NO_CANDIDATE
ACQUISITION_CANDIDATE_AMBIGUOUS
SOURCE_HOST_NOT_ALLOWED
DOWNLOAD_FAILED
STAGING_WRITE_FAILED
PDF_VALIDATION_FAILED
SHA_MISMATCH
RAW_STORE_FAILED
REGISTRY_FAILED
```

Error 必须标记：

- reason_code
- retryable bool
- provider
- request_id
- safe message

不得把 secrets / cookies / authorization headers 写入 receipt。

---

## 17. FFDF Independent Download Validation

Runner 返回后，FFDF main process 必须**重新**验证：

1. staging path 位于允许的 staging root；
2. 文件存在；
3. `%PDF-` magic bytes；
4. file_size > minimum safety threshold；
5. 独立计算 SHA256；
6. 独立 SHA == Dayu asset SHA；
7. candidate/source identity 未变；
8. source URL allowlist；
9. source bytes 在验证过程中未被修改。

Dayu 报告的 hash 不能作为 FFDF 唯一真值。

---

## 18. Raw Store

Raw storage root 必须显式配置。

不得把生产 raw files 写入 Git tracked source tree。

默认开发/测试可使用：

`workspace/`

生产建议使用独立 data root。

Content-addressed layout：

```text
<raw_root>/
  sha256/
    ab/
      abcdef....pdf
  receipts/
    12/
      <receipt_id>.json
  staging/
```

`.gitignore` 已忽略：

- `workspace/`
- `data/`
- `*.pdf`

但 P2 不得依赖 gitignore 作为数据安全策略。

---

## 19. Raw Store Commit

下载流程：

```text
Dayu temp PDF
   ↓
runner copy
   ↓
FFDF staging file
   ↓
FFDF SHA/PDF validation
   ↓
content-addressed final path
   ↓
P1 register_document()
   ↓
acquisition receipt
```

若 final SHA path 已存在：

1. 重新校验 existing file SHA；
2. 相同 → reuse existing content；
3. 删除 staging；
4. 不重复保存大对象。

若 existing path bytes 与 path SHA 不匹配：

`RAW_STORE_CORRUPTION`

必须 BLOCK，不覆盖。

---

## 20. Acquisition Receipt

Receipt 是 P2 transport/provenance 证据，不要求修改 P1 registry schema。

`receipt_id`：

```text
SHA256(
  provider + "\0"
  + source_id + "\0"
  + document_sha256
)
```

至少保存：

- protocol_version
- request_id
- market
- ticker
- filing slot
- provider
- provider_company_id
- source_id
- source_url
- source_title
- language
- filing_date
- fiscal_year
- fiscal_period
- amended
- etag
- last_modified
- remote_content_length
- Dayu repo URL
- Dayu pinned commit
- Dayu package version
- Dayu runtime Python
- runner version
- Dayu-reported SHA
- FFDF-recomputed SHA
- final file size
- final raw path
- downloaded_at
- registry result
- `docling_conversion_used=false`

Receipt atomic write。

同一 provider/source/content 的 deterministic receipt_id 允许幂等 overwrite only if semantic content identical；否则 BLOCK。

---

## 21. P1 Registry Integration

Acquisition success 后调用：

```python
register_document(
    final_raw_path,
    source=SourceMetadata(...),
    expected_identity=FilingIdentity(
        slot=request.slot,
        amended=candidate.amended,
    ),
)
```

映射：

- provider → SourceMetadata.provider
- source_id → source_id
- source_url → source_url
- title → source_title
- filing_date → filing_date
- provider profile company_id → provider_company_id
- downloaded_at → acquired_at
- report_date → nullable，除非官方 source 明确给出

不得由文件名猜 report_date。

---

## 22. Acquisition Service

正式 orchestration：

```python
acquire_slot(
    request: AcquisitionRequest,
    provider: AcquisitionProvider,
    raw_store: RawDocumentStore,
    registry: SQLiteRegistry,
) -> AcquisitionResult
```

执行顺序：

1. defensive check 当前 slot local state；
2. 若 P1 Registry 已有 resolved local raw：
   - `REUSED_LOCAL`
   - 不 network；
3. provider discover；
4. exact slot selection；
5. download to staging；
6. independent validation；
7. raw-store commit/dedup；
8. registry registration；
9. receipt；
10. return。

P2 不调用 parser。

---

## 23. Incremental / Race Safety

P1 planner 是正常入口。

P2 仍做 defensive local recheck，处理 planner 与实际 acquisition 之间的 race。

如果 acquisition 前已有 local raw：

`REUSED_LOCAL`

不启动 Dayu runner。

如果两个 acquisition 同时下载同 SHA：

content-addressed final commit 必须幂等。

---

## 24. Upstream Checkout / Runtime Descriptor

P2 必须维护 runtime descriptor，至少记录：

```text
dayu_repository
dayu_commit
dayu_package_version
dayu_source_path
dayu_python_executable
dayu_python_version
dayu_python_arch
runtime_created_at
```

Adapter 调用前必须验证：

- source checkout HEAD == pinned commit；
- source checkout clean；
- configured Python exists；
- runner doctor PASS。

任何 mismatch：

STOP。

---

## 25. Runner Doctor

P2 runner 提供无网络：

`doctor`

用于验证：

- protocol version；
- Python；
- Dayu package version；
- source pin descriptor；
- CN downloader symbol import；
- HK downloader symbol import；
- 禁止 workflow symbol 未被 runner 主动引用；
- runner process cwd 不是 Dayu source checkout；
- imported Dayu module origin 位于 dedicated acquisition runtime `site-packages`。

实测 pinned Dayu 在 dedicated Python 3.12 AMD64 runtime 中首次导入 CN downloader 约 10.3 秒，因为 package initializer 会加载较大的 import graph。因此 doctor timeout 不能使用过短的 2–5 秒阈值；P2 初始 doctor timeout 设为 **60 秒**，后续可依据实测收紧。

Doctor 不下载文件，不访问官方站点。

---

## 26. P2 测试层级

### 26.1 Pure Unit

FFDF main runtime：

- models
- protocol schema
- candidate filtering
- URL allowlist
- subprocess command construction
- response validation
- SHA validation
- raw store
- receipt
- registry integration

全部 no-network。

### 26.2 Runner Contract Test

Dayu isolated runtime：

- doctor
- request parse
- response atomic write
- fake/injected downloader where feasible
- no high-level workflow call

### 26.3 Integration with pinned Dayu

验证：

- checkout pin；
- clean worktree；
- runner imports；
- CN/HK narrow downloader usable；
- main runtime remains Dayu-free。

### 26.4 Live Official Smoke

只有前面全部 PASS 后执行。

至少：

- 1 个 CN official filing；
- 1 个 HK official filing。

Live sample 在 P2 development environment audit 中确认并冻结到 acceptance instruction。

Live 不用于替代 deterministic tests。

---

## 27. Live Sample 原则

CN 首选已知代表：

- `600519`
- FY2024
- 官方 CNINFO PDF

HK 样本必须在 P2 environment/discovery audit 中通过 HKEX 官方来源确认后再冻结。

不得仅凭记忆写死 HK source_id / URL。

---

## 28. P2 Acceptance 必须验证

至少：

1. P0/P1 regression PASS；
2. FFDF main runtime 仍无 Dayu/Docling；
3. Dayu checkout exact pinned commit；
4. Dayu checkout clean；
5. dedicated runtime 可复建；
6. doctor PASS；
7. adapter 不直接 import Dayu；
8. subprocess uses `shell=False`；
9. no high-level Dayu workflow invocation；
10. no Docling conversion；
11. no Docling JSON artifact；
12. CN deterministic mocked integration PASS；
13. HK deterministic mocked integration PASS；
14. raw store SHA-addressed；
15. same SHA dedup；
16. source metadata mapping正确；
17. acquisition receipt完整；
18. P1 registry registration正确；
19. local exists → no network；
20. candidate 0 → NOT_FOUND；
21. candidate >1 → REVIEW_REQUIRED；
22. SHA mismatch → FAIL/BLOCK；
23. raw store corruption → BLOCK；
24. live CN official acquisition PASS；
25. live HK official acquisition PASS；
26. rerun local planner → PARSE_LOCAL / local reuse path，不重复 download；
27. source raw bytes immutable；
28. upstream checkout unchanged。

---

## 29. P2 Exit Condition

只有 P2 Independent Acceptance = PASS 后：

- P2 → DONE；
- accepted baseline 更新；
- 才允许进入 P3 Native Page / Section Extraction。

P2 未 PASS 前不得开始 P3 implementation。

---

## 30. Design-first Issue Rule

P2 任一步发现问题并找到方案：

```text
STOP
→ facts / root cause
→ update P2 design
→ commit design baseline
→ assess affected gates
→ rerun affected gates
→ continue
```

禁止 code-first / design-later。
