# FFDF MCP 部署与使用说明

适用项目：FinancialFilingDataFoundation（FFDF）
适用市场：CN / HK
部署主机：WorkHome
部署日期：2026-11-05

## 1. 部署目标

FFDF MCP 用于让 Codex 直接读取本机已经下载、解析和验证过的财报数据。

当前 MCP 采用 stdio 方式，不是 Windows 常驻服务。Codex 需要使用时自动启动 MCP 进程，会话结束后进程可以退出。

中文注释：

- stdio 表示 Codex 通过标准输入/输出与 MCP Server 通信。
- 不需要开放 HTTP 端口。
- 不需要配置公网地址。
- 不需要把 FFDF 做成 Windows Service。
- MCP 本身只读，不负责下载新财报，也不修改解析结果。

## 2. 当前正式 MCP 配置

MCP 名称：ffdf

Server：ffdf-local

版本：p8-local-mcp-v1

项目根目录：

    D:\Codex\FinancialFilingDataFoundation

MCP 专用 Python：

    D:\Codex\FinancialFilingDataFoundation\runtimes\ffdf-mcp-2.3.0\.venv\Scripts\python.exe

正式 Catalog：

    D:\Codex\FinancialFilingDataFoundation\workspace\mcp\p8-live-catalog.json

源码路径：

    D:\Codex\FinancialFilingDataFoundation\src

## 3. Codex 全局注册方式

当前 WorkHome 已完成注册。等价命令如下：

    $root = "D:\Codex\FinancialFilingDataFoundation"
    $py = "$root\runtimes\ffdf-mcp-2.3.0\.venv\Scripts\python.exe"

    codex mcp add ffdf --env "PYTHONPATH=$root\src" -- "$py" -m financial_filing_data_foundation.mcp.server --project-root "$root" --catalog "$root\workspace\mcp\p8-live-catalog.json"

中文注释：

- codex mcp add ffdf：向 Codex 全局配置注册一个名为 ffdf 的 MCP Server。
- --env PYTHONPATH=...：让独立 MCP Python 能找到 FFDF 源码。
- -m financial_filing_data_foundation.mcp.server：启动 FFDF MCP Server 模块。
- --project-root：限定所有文件访问必须位于 FFDF 项目根目录。
- --catalog：指定 MCP 当前可见的正式财报目录。

## 4. 查看当前配置

    codex mcp get ffdf

正常状态应包含：

    enabled: true
    transport: stdio

查看所有 MCP：

    codex mcp list

应看到 ffdf 为 enabled。

中文注释：

enabled 只表示 Codex 已启用该 MCP 配置。真正可用还需要完成协议握手和工具调用验证。

## 5. 当前 FFDF MCP 工具

FFDF MCP 当前候选生产接口共 26 个。逻辑上分为三组：

- P8_RAW_V1：11 个冻结的 Raw/Read 工具；
- REPORT_SAFE_V1：3 个报告安全只读接口；
- RESEARCH_REVIEW_V1：12 个研究复核接口，其中 9 个 read/render，3 个 P9 write-through。

工具列表：

1. ffdf_list_documents
2. ffdf_get_document
3. ffdf_search_document
4. ffdf_read_pages
5. ffdf_list_sections
6. ffdf_list_tables
7. ffdf_get_table
8. ffdf_list_raw_facts
9. ffdf_get_fact
10. ffdf_get_evidence
11. ffdf_get_validation
12. ffdf_get_company_report_context
13. ffdf_search_company
14. ffdf_find_table_rows
15. ffdf_get_review_state
16. ffdf_get_resolved_fact
17. ffdf_list_resolved_facts
18. ffdf_list_review_tasks
19. ffdf_get_review_context
20. ffdf_locate_evidence
21. ffdf_render_table
22. ffdf_render_table_group
23. ffdf_render_page
24. ffdf_prepare_review_overlay
25. ffdf_submit_review_resolution
26. ffdf_materialize_resolved_view

默认 `--research-review-profile RESEARCH_FALLBACK`。该 profile 下 24–26 三个写工具虽然在 tool surface 中可见，但调用时会返回 `RESEARCH_MCP_WRITE_DISABLED`。只有显式启动 `QUALITY_REVIEW` profile 才允许通过现有 P9 v1 API 执行 prepare / submit / materialize。

中文注释：

- list_documents：先确定本地有哪些财报。
- get_document：查看页数、表格数、Facts 数和 Validation 状态。
- search_document：搜索财报本地全文索引，不是互联网搜索。
- read_pages：读取指定原始页文本。
- list_tables / get_table：读取 P5 重建后的表格。
- list_raw_facts / get_fact：读取 P6 原始事实。
- get_evidence：追溯原始事实证据。
- get_validation：检查 P7 验证结果与问题。
- get_company_report_context：按最新优先列出同一公司的全部已入库报告，并附带 Validation 与报告生成防错规则。
- search_company：跨同一公司多期报告搜索，并自动附带相邻页；同时使用字面子串扫描补足中文 FTS 可能漏页的问题。
- find_table_rows：按 P5 原始披露行标签查询，保留“新能源行业”“外销”等源标签，优先使用直接披露值而不是人工重组。

## 6. 推荐研究调用顺序

    ffdf_get_company_report_context
      ↓
    ffdf_search_company
      ↓
    ffdf_find_table_rows
      ↓
    ffdf_get_document / ffdf_get_validation
      ↓
    ffdf_search_document / ffdf_read_pages
      ↓
    ffdf_list_tables / ffdf_get_table
      ↓
    ffdf_list_raw_facts / ffdf_get_fact
      ↓
    ffdf_get_evidence

中文注释：

生成正式研究报告时，优先先取 company_report_context，再做跨期搜索和源表行查询。直接披露的聚合行优先于 AI 自行重组；源标签不得随意扩大语义；涉及分红、回购等状态时必须先检查较新的报告；搜索章节性内容时必须读取相邻页。

随后再确认 Validation，并按需深入 P5/P6/Evidence。不要看到某个数值就直接当作已完成语义确认的数据。

REVIEW_REQUIRED 不等于失败。只要没有 blocking issue，数据仍可用于研究，但不能静默提升为 canonical PASS。当前 Catalog 仍以定期报告为主，不能用它证明未入库临时公告中的最新事件状态。


## 7. 新财报入库后如何让 MCP 看到

例如执行：

    ffdf ingest --market CN --ticker 605117 --year 2026 --period Q3

当 P7 没有 blocking issue 时，ingest 会自动把该财报加入：

    workspace/mcp/p8-live-catalog.json

MCP Server 在启动时读取 Catalog，因此新入库后推荐：

    完成 ffdf ingest
      ↓
    关闭当前 Codex 会话
      ↓
    新开 Codex 会话
      ↓
    ffdf MCP 自动重新启动
      ↓
    重新读取最新 Catalog

## 8. 当前部署验收结果

2026-11-05 已在 WorkHome 完成真实 stdio 握手：

    FFDF_MCP_HANDSHAKE=PASS
    PROTOCOL=2026-07-28
    TOOLS=26
    TICKER=605117
    DOCUMENTS=23
    YEARS=2021,2022,2023,2024,2025,2026

这说明：

- Codex MCP 配置可启动 FFDF；
- MCP protocol 握手成功；
- 26 个工具完整暴露：原11个 P8 + 3个 Report-Safe + 12个 Research Review；
- 605117 的 23 份本地财报可以被 MCP 查询；
- 当前 Catalog 与最新批量入库结果一致。

## 9. Codex 中的推荐提问方式

可以直接告诉 Codex：

> 使用 FFDF MCP，列出 605117 的全部本地财报。

或者：

> 使用 FFDF MCP，读取 605117 的 2026 Q3，先检查 validation，再分析利润表、资产负债表和现金流量表，所有结论保留 evidence。

或者：

> 使用 FFDF MCP 搜索 605117 2026 Q3 中与营业收入、归母净利润、经营现金流有关的页面和表格，并给出 evidence。

## 10. MCP 与下载命令的职责边界

    ffdf acquire
    = 下载 + Raw/Registry

    ffdf ingest
    = 下载 + P3-P7 + Parsed Registry + P8 Catalog

    FFDF MCP
    = 读取已经进入 P8 Catalog 的财报

中文注释：

MCP 不负责从 CNINFO/HKEX 下载文件。下载与解析应通过 ffdf ingest 完成；MCP 只负责向 Codex 暴露已验证的本地数据。

## 11. 故障排查

查看配置：

    codex mcp get ffdf

查看是否启用：

    codex mcp list

检查 Catalog：

    Get-Content D:\Codex\FinancialFilingDataFoundation\workspace\mcp\p8-live-catalog.json

如果刚完成新财报 ingest，但 Codex 看不到：

1. 确认 ingest 返回 p8_catalog=ADDED 或 ALREADY_REGISTERED；
2. 确认 research_ready=true；
3. 重启 Codex 会话；
4. 再调用 ffdf_list_documents。

## 12. 删除 MCP 配置

如需取消 Codex 中的 FFDF MCP：

    codex mcp remove ffdf

这只删除 Codex MCP 配置，不会删除：

- Raw PDF；
- Registry；
- P3-P7 artifacts；
- P8 Catalog；
- 任何财报数据。
