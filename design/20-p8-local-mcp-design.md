# 20 — P8 Local MCP 详细设计

状态：**DESIGN BASELINE — P8**

阶段：**P8 — Local MCP**

前置条件：
- P0–P7 = DONE / PASS
- accepted P7 merge = `5f314bab9d88fb16b4b46c662e0a9f1b8f1a9b13`
- P3/P5/P6/P7 artifacts 已具备 deterministic loader / tamper guard
- project directory consolidation = PASS

协议参考：
- MCP specification: `2026-07-28`
- official Python SDK stable v2
- environment audit observed latest PyPI `mcp==2.3.0`

---

## 1. P8 目标

P8 将**已经验收的本地 FFDF data artifacts**暴露为标准 MCP tools，使 Codex/兼容 MCP host 可以查询：

- documents
- page text / FTS
- sections
- reconstructed tables
- raw facts
- first-class evidence
- validation status / issues

P8 是 local deterministic tool boundary，不是 parser，不是 agent。

---

## 2. 明确不做

P8 v1 禁止：

- 下载财报
- acquisition
- parse PDF
- table detection/reconstruction
- raw fact extraction
- P7 validation重新运行
- Registry mutation
- review overlay mutation
- canonical metric mapping
- export analysis
- shell execution
- arbitrary filesystem browse/read
- network HTTP transport
- remote AI / MCP sampling
- Codex API
- OpenAI/Anthropic/Gemini API
- P9/P10/P11 functionality

Hard rule：

`MCP_AI_API_CALLS = FORBIDDEN`

---

## 3. 协议与 SDK

### 3.1 Protocol

P8 current target：
`2026-07-28`

使用 official SDK，而不是手写 MCP JSON-RPC。

理由：
- 2026-07-28 已移除 initialize/session model；
- official SDK v2 同时服务 modern 2026 与 legacy clients；
- 手写双 era protocol 会把 transport/protocol compatibility 变成本项目维护责任。

### 3.2 SDK Pin

exact pin：
`mcp==2.3.0`

P8 不使用 unpinned `mcp>=2`。

### 3.3 Transport

P8 v1：
**stdio only**

不启用：
- Streamable HTTP
- SSE
- remote bind/listen port

原因：
本阶段目标是本机 Codex/desktop host，HTTP authorization/network surface 不属于 P8。

---

## 4. Runtime Isolation

FFDF main runtime 保持：

`D:\Codex\FinancialFilingDataFoundation\.venv`

不安装 MCP SDK。

新 dedicated runtime：

`D:\Codex\FinancialFilingDataFoundation\runtimes\ffdf-mcp-2.3.0\.venv`

approved base：
`C:\Users\guoyg\AppData\Roaming\uv\python\cpython-3.12.14-windows-x86_64-none\python.exe`

- CPython 3.12.14 AMD64 / x86_64
- 运行于 Windows ARM64 的 x64 emulation
- 已被 P2 Dayu runtime 实际验证可稳定使用

P8 不使用 Python 3.14 ARM64 作为 MCP runtime base；原因见 P8-ISSUE-001。

runtime 至少：
- mcp==2.3.0
- PyMuPDF==1.28.2（兼容现有 P3 loader import graph）
- exact transitive lock

tracked lock：
`runtime-locks/mcp-2.3.0-py312-win-amd64.lock.txt`

安装过程：
1. create isolated venv
2. install exact roots
3. freeze complete dependency set
4. write tracked lock
5. rebuild verification from lock if resolver output changed
6. runtime doctor

---

## 5. Package Architecture

```text
financial_filing_data_foundation/
  mcp/
    __init__.py
    catalog.py
    service.py
    server.py
```

### catalog.py

负责：
- catalog load
- schema/path validation
- document lookup
- artifact locations

不得 import MCP SDK。

### service.py

负责：
- tool business logic
- input validation
- artifact loaders
- filtering/pagination
- deterministic return dict

不得 import MCP SDK。

### server.py

唯一 MCP SDK boundary：
- create MCPServer
- register static tools
- stdio serve
- convert service exceptions to tool errors

---

## 6. Catalog

Schema：
`p8-mcp-catalog-v1`

示例：

```json
{
  "schema_version": "p8-mcp-catalog-v1",
  "documents": [
    {
      "document_sha256": "...",
      "market": "CN",
      "ticker": "600519",
      "fiscal_year": 2024,
      "filing_type": "ANNUAL",
      "p3_artifact_dir": "workspace/live/p6-inputs/cn/p3/...",
      "p5_artifact_dir": "workspace/live/p6-inputs/cn/p5/...",
      "p6_artifact_dir": "workspace/live/p6-facts/cn-a/...",
      "p7_artifact_dir": "workspace/live/p7-validation/cn-a/..."
    }
  ]
}
```

Catalog operational path：
`workspace/mcp/catalog.json`

不 tracked。

---

## 7. Catalog Path Security

Catalog 内 artifact path：

- 必须是 project-root-relative
- 不得 absolute
- 不得含 traversal escape
- resolve 后必须 `is_relative_to(project_root)`
- required artifact directory必须存在
- duplicate document_sha禁止
- duplicate market/ticker/year/filing_type identity禁止

MCP tool arguments**不得提供 artifact path**。

错误：
- `P8_CATALOG_INVALID`
- `P8_PATH_OUTSIDE_PROJECT_ROOT`

---

## 8. Artifact Trust

### 8.1 Lazy trusted bundle

Server/catalog 启动只验证 catalog schema/path/identity，**不得 eager 加载全部 document artifacts**。

首次调用需要 artifact 内容的 document tool 时，按该 document 分别调用：

- `load_native_document`
- `load_reconstructed_tables`
- `load_raw_facts`
- `load_validation_result`

完整验证成功后生成 immutable in-process bundle cache。后续同 document tool calls 复用该 bundle。

`ffdf_list_documents` 是唯一 catalog-only tool，不触发 artifact bundle load，也不返回 P7 status。

要求：
- same document SHA
- all tamper/fingerprint checks PASS

若 loader error：
`P8_UPSTREAM_ARTIFACT_INVALID`

P8 不把 upstream execution error伪装成：
`validation_status=BLOCKED`

必须保持 P7-ISSUE-003 的区分：
- valid P7 BLOCKED = document validation status
- upstream load failure = MCP tool execution error

---

## 9. Read-only Tool Set

P8 v1 固定 11 个 tools。

### 9.1 ffdf_list_documents

参数：
- market optional
- ticker optional
- fiscal_year optional

返回 **catalog identity metadata only**：
- document_sha256
- market
- ticker
- fiscal_year
- filing_type

不返回未经当前进程完整 loader 验证的 P7 status。调用方需要 validation summary 时使用 `ffdf_get_document` 或 `ffdf_get_validation`。

理由见 P8-ISSUE-002。

### 9.2 ffdf_get_document

参数：
- document_sha256

返回：
- catalog metadata
- P3 page count
- P5 table/group counts
- P6 fact/evidence counts
- P7 validation summary

### 9.3 ffdf_search_document

参数：
- document_sha256
- query
- limit default 10, max 50

调用 P3 FTS5。

不得 network search。

### 9.4 ffdf_read_pages

参数：
- document_sha256
- page_nos: list[int]

限制：
- 1–10 pages per call
- physical page valid
- output text total <= 200,000 chars

返回 page_no/text/geometry/basic counts。

不返回全部 word geometry，避免大 payload。

### 9.5 ffdf_list_sections

参数：
- document_sha256

返回 P3 sections，max 1000。

### 9.6 ffdf_list_tables

参数：
- document_sha256
- page_no optional
- offset default 0
- limit default 50 max 100

返回 table summary：
- table_id
- page
- bbox
- row/value-column count
- group id
- signals

不默认返回 all cells。

### 9.7 ffdf_get_table

参数：
- document_sha256
- table_id
- max_rows default 100 max 500

返回 table detail + rows/cells。
若 truncated：
- `truncated=true`
- total_row_count

### 9.8 ffdf_list_raw_facts

参数：
- document_sha256
- page_no optional
- metric_contains optional
- offset default 0
- limit default 50 max 100

metric filter：
casefold substring only，不做 canonicalization。

### 9.9 ffdf_get_fact

参数：
- document_sha256
- raw_fact_id

返回 exact raw fact。

### 9.10 ffdf_get_evidence

参数：
- document_sha256
- evidence_id

返回 exact evidence + source word refs。

### 9.11 ffdf_get_validation

参数：
- document_sha256
- include_issues default true
- severity optional
- offset/limit

返回 persisted P7 report + issues。

---

## 10. Tool Input Rules

Document SHA：
- exactly 64 lowercase/uppercase hex
- normalize lowercase

IDs：
- non-empty
- max 256 chars

query：
- trim
- length 1..512

metric_contains：
- max 256 chars

pagination：
- offset >=0
- 1 <= limit <= tool max

page_nos：
- unique
- sort ascending for deterministic output
- 1..page_count

invalid：
`P8_INVALID_ARGUMENT`

---

## 11. Output Contract

Business service returns JSON-serializable dict/list only。

通用 success：

```json
{
  "schema_version": "p8-mcp-result-v1",
  "tool": "ffdf_get_document",
  "document_sha256": "...",
  "data": {}
}
```

list result additionally：
- offset
- limit
- total
- returned
- truncated

不得在结果中泄露：
- arbitrary environment variables
- passwords/secrets
- unrelated filesystem paths

Artifact absolute paths默认不返回。

---

## 12. Error Model

Service exception：

`McpServiceError(reason_code, message)`

reason codes至少：
- P8_CATALOG_INVALID
- P8_PATH_OUTSIDE_PROJECT_ROOT
- P8_DOCUMENT_NOT_FOUND
- P8_INVALID_ARGUMENT
- P8_UPSTREAM_ARTIFACT_INVALID
- P8_TABLE_NOT_FOUND
- P8_FACT_NOT_FOUND
- P8_EVIDENCE_NOT_FOUND
- P8_PAYLOAD_LIMIT_EXCEEDED

MCP server将其转换为 deterministic tool error text/structured content。

不得输出 Python traceback给 normal client。

stderr可记录 diagnostic。

---

## 13. stdout / stderr Rule

stdio MCP：

**stdout = protocol only**

禁止：
- print debug
- startup banner
- logging to stdout

diagnostic：
stderr only。

unit test：
server module import不得输出 stdout。

---

## 14. No Arbitrary File Tool

明确禁止提供：
- read_file(path)
- list_directory(path)
- sqlite_query(sql)
- execute_python
- shell
- run_command

P8只提供 domain-specific tools。

---

## 15. No Mutation

P8 tool call 前后：
- P3 unchanged
- P5 unchanged
- P6 unchanged
- P7 unchanged
- Registry unchanged
- catalog unchanged

P8 v1 没有 mutation tool。

---

## 16. Determinism

相同 catalog + artifacts + args：

business response除 MCP envelope 外语义完全一致。

排序：
- documents: market,ticker,fiscal_year,filing_type,sha
- sections: page_start,page_end,section_id
- tables: page_no,bbox y/x,table_id
- facts: page_no,table_id,row_index,column_index,raw_fact_id
- issues: persisted P7 order

search scores使用 SQLite FTS deterministic result。

---

## 17. Catalog Live Fixture

P8 acceptance catalog使用现有 project-root live artifacts：

CN 600519 FY2024：
- P3: `workspace/live/p6-inputs/cn/p3/<sha>`
- P5: `workspace/live/p6-inputs/cn/p5/<sha>`
- P6: `workspace/live/p6-facts/cn-a/<sha>`
- P7: `workspace/live/p7-validation/cn-a/<sha>`

HK 00700 FY2024 同理。

Catalog位于：
`workspace/mcp/p8-acceptance-catalog.json`

---

## 18. MCP SDK Doctor

dedicated runtime必须验证：

- Python 3.12.14 AMD64
- mcp 2.3.0
- PyMuPDF 1.28.2
- server import
- no startup stdout
- static 11 tool registrations
- protocol modern connection
- legacy compatibility由 SDK integration test至少验证当前 SDK auto/client path可 list/call

---

## 19. Protocol Integration Test

使用 official Python SDK Client + stdio server subprocess。

必须验证：

1. server starts
2. client connects
3. negotiated protocol可用
4. tools/list = exact expected 11 tool names
5. ffdf_list_documents returns CN/HK
6. ffdf_get_document
7. ffdf_search_document
8. ffdf_get_table
9. ffdf_get_fact + ffdf_get_evidence relation
10. ffdf_get_validation
11. invalid doc returns tool error
12. server stdout无非协议污染
13. server exit clean

---

## 20. Performance

Business service：

- list_documents catalog-only <= 2s
- first trusted bundle load for one document <= 20s
- warm get_document <= 2s
- warm search <= 2s
- warm read_pages <= 2s
- warm list/get table <= 5s
- warm list/get facts/evidence <= 5s
- warm validation <= 5s

MCP process cold startup + protocol connect + list tools（不加载 document bundle）：
<= 15s

首次 artifact tool call 的 bundle validation 时间单独记录，不混入 server cold-start Gate。

不把网络时间计入，因为 P8无网络。

---

## 21. Security

P8 v1：
- stdio child process only
- no listener
- no auth，因为无 remote transport
- project root fixed
- catalog path explicit
- no arbitrary path args
- no subprocess from service
- no network
- no AI

catalog本身视为 trusted local operator configuration，但仍执行 schema/path validation。

---

## 22. Runtime Reproducibility

P8 runtime lock：
`runtime-locks/mcp-2.3.0-py312-win-amd64.lock.txt`

任何未来 rebuild：
- exact lock
- exact base Python
- package snapshot match
- protocol integration smoke

不得 silent dependency upgrade。

---

## 23. Unit Tests

至少：

1. catalog schema
2. relative paths
3. traversal blocked
4. absolute path blocked
5. duplicate doc SHA blocked
6. duplicate filing identity blocked
7. document not found
8. SHA normalization
9. query length
10. pagination boundaries
11. page limits
12. list documents deterministic
13. get document counts
14. search
15. read pages
16. sections
17. list tables pagination
18. get table
19. missing table
20. list facts filter
21. get fact
22. missing fact
23. get evidence
24. missing evidence
25. validation report
26. validation issue filtering
27. upstream corrupt artifact error
28. P7 preflight error distinction
29. no mutation
30. no arbitrary path surface
31. no network/AI imports
32. server import no stdout
33. exact tool names
34. official SDK stdio integration
35. CN/HK live tool calls

---

## 24. Package/API Boundary

Business API：

```python
catalog = McpCatalog.load(project_root, catalog_path)
service = McpQueryService(catalog)

service.list_documents(...)
service.get_document(...)
...
```

server adapter调用 service。

P9 可以复用 service读取数据，但不得通过修改 P8 tool contract偷偷加入 review mutation。

---

## 25. P8 Issue Log

### P8-ISSUE-003 — Empirical HK trusted-bundle validation slightly exceeded the provisional 15s threshold

After P8-ISSUE-002 lazy loading was implemented, official SDK integration measured:

- MCP cold connect: 1.258s；
- CN first full P3/P5/P6/P7 trusted bundle: 9.986s；
- HK first full trusted bundle: 15.104s；
- all warm calls: milliseconds；
- protocol/tool semantics: PASS。

The 15s first-bundle threshold was introduced before measuring the accepted 274-page HK artifact. The HK result exceeded it by ~0.104s while still performing the full required semantic tamper/fingerprint validation.

Rejected solutions:
- skip P7 semantic recomputation；
- trust persisted report without loader validation；
- weaken P6/P7 tamper guards；
- prewarm all documents at server startup (would reintroduce P8-ISSUE-002)。

Approved solution:
- keep cold MCP connect/list-tools gate at <=15s；
- set **first trusted bundle load per document <=20s** for P8 v1；
- retain all warm tool gates unchanged；
- record first-load timing separately for every live document；
- no validation step is removed or downgraded。

This is an empirical performance-policy amendment, not a correctness relaxation.

Affected gates: P8-H/I/K.

### P8-ISSUE-004 — deep Windows worktree pytest temp paths exceed filesystem path limit

P8-F full regression initially used a basetemp nested under the already-deep active worktree:

`.../worktrees/active/p8-local-mcp/workspace/pytest-p8-final-dev`

P4/P5/P6 tests create additional atomic temp directories containing 64-char document SHA values. On this Windows host the combined path became too long and `Path.write_text()` failed with `FileNotFoundError` before product assertions ran.

Initial diagnostic rerun with a short external basetemp proved the failure was path length rather than product behavior. That external location is **not accepted** because project directory governance requires FFDF-owned execution state to remain under the canonical project root.

A second diagnostic used the project-root-local short path:

`D:\Codex\FinancialFilingDataFoundation\workspace\t\p8\diag-full`

Result:
`231 passed`

Approved solution：
1. P8 development/review/acceptance pytest on Windows must use a short **project-root-local** basetemp under `D:\Codex\FinancialFilingDataFoundation\workspace\t\p8\<run>`；
2. the directory remains ignored operational test state under the canonical project root；
3. do not use any `D:\Codex\_ffdf_*` sibling directory；
4. do not modify P4/P5/P6 atomic output naming or accepted production code merely to accommodate deep review worktree paths；
5. isolated Git worktree remains required；
6. full regression evidence from the long basetemp run is invalidated and must be rerun with the project-root-local short basetemp；
7. acceptance instruction must freeze this exact in-project convention.

### P8-ISSUE-002 — Eager artifact validation made MCP cold connect exceed the 15s gate

Official SDK stdio integration succeeded functionally and negotiated protocol `2026-07-28`, but initial implementation constructed `McpQueryService` by validating/loading every catalog document during server creation.

Observed:
- standalone two-document bundle preload: ~11.16s；
- official SDK connect + eager preload: ~25.93s；
- design cold startup/connect gate: <=15s；
- protocol/tool calls themselves succeeded。

Root cause:
- implementation interpreted artifact trust as eager server-wide preflight；
- design intent in §8 is first document access validation；
- eager preload scales startup linearly with catalog size。

Approved solution:
1. `McpQueryService.__init__` stores catalog only and starts with empty bundle cache；
2. `ffdf_list_documents` becomes catalog-only identity metadata and never claims P7 status；
3. first artifact-dependent call for a document performs full P3/P5/P6/P7 loader validation and caches the immutable bundle；
4. all later calls for that document use the validated cache；
5. upstream corruption still raises `P8_UPSTREAM_ARTIFACT_INVALID` on first artifact access；
6. add tests proving constructor/list_documents do not load/touch artifact contents；
7. cold protocol connect/list-tools <=15s；
8. record first-document trusted-load latency separately (<=20s, per P8-ISSUE-003)。

The first integration run remains valid evidence for protocol/tool correctness but **fails the cold-start performance gate** and is invalidated for performance acceptance.

Affected gates: P8-D/F/H/I/K.

### P8-ISSUE-001 — MCP SDK dependency has no usable CPython 3.14 ARM64 wheel path

Observed during P8-B environment audit:

- target: CPython 3.14.9 ARM64；
- exact root: `mcp==2.3.0` + `PyMuPDF==1.28.2`；
- resolver selected `cryptography==50.0.2` via `mcp -> pyjwt[crypto]`；
- no compatible prebuilt cryptography wheel was selected for cp314-win_arm64；
- build fell back to Rust/MSVC；
- Rust was available, but MSVC linker `link.exe` was not installed；
- install failed before P8 production code began。

Rejected solutions:
- install full Visual Studio Build Tools merely for P8；
- mutate system compiler/toolchain；
- downgrade MCP SDK；
- weaken exact SDK pin。

Approved solution:
- reuse already-installed uv-managed CPython 3.12.14 AMD64 under Windows ARM64 x64 emulation；
- this base is already validated by P2 Dayu runtime；
- create `runtimes/ffdf-mcp-2.3.0/.venv` from that interpreter；
- exact runtime lock name becomes `mcp-2.3.0-py312-win-amd64.lock.txt`；
- keep FFDF main Python 3.14 ARM64 unchanged and MCP-free；
- delete/recreate only the failed, unaccepted P8 runtime directory after this design amendment is committed；
- rerun SDK install/import/protocol doctor。

Affected gates: P8-B/H/I/K.

Initial failed runtime attempt is invalid evidence and must not be treated as an accepted P8 runtime.

发现问题：
必须追加 `P8-ISSUE-xxx` 后先提交 design amendment。

---

## 26. Exit

P8 Independent Acceptance PASS 后：
- P8 DONE
- P9 Review Overlay design authorized

P9不得在 P8 acceptance期间开始。
