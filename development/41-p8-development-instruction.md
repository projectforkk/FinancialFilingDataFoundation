# 41 — P8 Development Instruction

任务：**Local MCP**

必须遵守：
- `design/00-design-management-index.md`
- `design/15-project-directory-management.md`
- `design/20-p8-local-mcp-design.md`
- `design/21-p8-implementation-plan.md`

## Scope

只实现：
- project-root-relative MCP catalog
- deterministic read-only query service
- official MCP SDK v2 stdio adapter
- 11 static tools
- MCP runtime pin/lock
- official SDK protocol integration tests

禁止：
- acquisition
- parsing
- artifact mutation
- Registry mutation
- review overlay mutation
- arbitrary path/file/shell/sql tool
- HTTP/SSE listener
- network
- remote AI / sampling
- P9/P10/P11 functionality

## Runtime

Main parse/test runtime:
`D:\Codex\FinancialFilingDataFoundation\.venv`

Dedicated MCP runtime:
`D:\Codex\FinancialFilingDataFoundation\runtimes\ffdf-mcp-2.3.0\.venv`

Approved base after P8-ISSUE-001:
`C:\Users\guoyg\AppData\Roaming\uv\python\cpython-3.12.14-windows-x86_64-none\python.exe`

- CPython 3.12.14 AMD64
- Windows ARM64 x64 emulation

All operational files remain under project root.

## Development Evidence Must Record

- design baseline/amendments
- exact mcp version
- runtime lock SHA
- production commit
- exact tool names
- focused/full tests
- SDK stdio integration
- negotiated protocol
- CN/HK live calls
- upstream immutability
- no-network/no-AI/no-mutation assertions

发现问题：
**先更新设计书，再改代码。**
