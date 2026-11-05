# 100 — Research Review MCP v3 R-A1 Contract Freeze Evidence

## 目标

冻结 design/29 v3 的 Research Review MCP 基础契约，不注册未来工具、不改变当前 14-tool production server 行为。

## 设计基线

- branch: design/research-review-mcp-v3
- design baseline: d90df22
- current production baseline: main@8c6cd75
- P8 logical base contract: 11 tools
- Report-Safe v1 production extension: 3 tools
- current ffdf MCP production surface: 14 tools

## 本 Gate 修改

新增：

- src/financial_filing_data_foundation/mcp/research_review_contract.py
- tests/unit/mcp/test_research_review_contract.py

冻结：

- contract version: research-review-mcp-v1
- capability groups:
  - P8_RAW_V1
  - REPORT_SAFE_V1
  - RESEARCH_REVIEW_V1
- future Research Review tools: 9 read + 3 explicit write
- runtime profiles:
  - RESEARCH_FALLBACK
  - QUALITY_REVIEW
- quality states:
  - COMPLETE_BASE
  - COMPLETE_REVIEWED
  - NEEDS_REVIEW
  - NEEDS_MATERIALIZATION
  - NEEDS_UPSTREAM_FIX
  - BLOCKED
  - INVALID_REVIEW_STATE
- Research MCP error code namespace
- write permission rule: only QUALITY_REVIEW permits write-through tools

## Non-regression

本 Gate 没有：

- 修改 server.py
- 注册任何 future Research Review tool
- 修改 P8_TOOL_NAMES_V1
- 修改 Report-Safe v1
- 修改 P9 schema/action
- 修改 Raw/P3/P5/P6/P7/Registry
- 引入 PDF visual capability
- 引入 durable mutation

测试明确验证：

- P8_RAW_V1_TOOL_NAMES == accepted P10 P8_TOOL_NAMES_V1
- current server TOOL_NAMES == P8 raw 11 + Report-Safe 3
- future 12 tools 与 current production 14 tools 不重叠
- read/write tool sets 分离
- RESEARCH_FALLBACK write disabled
- QUALITY_REVIEW write enabled
- contract manifest deterministic

## 测试

首次 focused pytest 未进入业务逻辑：

- 原因：src-layout 未设置 PYTHONPATH
- 修正：PYTHONPATH=src

第二次测试遇到 Windows 用户临时目录 PermissionError：

- C:\Users\guoyg\AppData\Local\Temp\pytest-of-guoyg
- 与代码无关
- 按仓库既有实践改用短 basetemp

最终结果：

- compileall: PASS
- focused contract + static + research context: 45 PASS
- full tests/unit/mcp: 33 PASS
- git diff --check: PASS（仅工作树无 diff warning；新增文件）
- production server tool surface: unchanged

## Gate 结论

R-A1 Contract Freeze: PASS

下一 Gate：

R-A2 — Research Preflight Contract
