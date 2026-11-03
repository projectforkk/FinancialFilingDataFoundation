# 42 — P8 MCP Runtime Environment Audit

状态：**P8-B COMPLETE / PASS**

Branch:
`task/p8-local-mcp`

Initial P8 design baseline:
`bf39d2028e4c03bee724c1c5389d513ebc904d00`

P8-ISSUE-001 design amendment:
`382a08369182c5be49a5e706ce62d8121a730dcb`

## 1. Main Runtime

`D:\Codex\FinancialFilingDataFoundation\.venv`

Observed:
- Python 3.14.9 ARM64
- PyMuPDF 1.28.2
- `mcp`: absent

Decision:
**UNCHANGED / MCP-FREE**

## 2. First MCP Runtime Attempt

Attempted:
- CPython 3.14.9 ARM64
- mcp==2.3.0
- PyMuPDF==1.28.2

Resolver:
- 30 packages
- `mcp -> pyjwt[crypto] -> cryptography==50.0.2`

Failure:
- no selected cp314-win_arm64 cryptography wheel
- source build invoked Rust/MSVC
- Rust available
- MSVC `link.exe` absent
- build failed

This attempt is invalid evidence and was removed.

No production code existed at this point.

## 3. Approved Runtime Base

`C:\Users\guoyg\AppData\Roaming\uv\python\cpython-3.12.14-windows-x86_64-none\python.exe`

Observed build:
`CPython 3.12.14 [MSC v.1944 64 bit (AMD64)]`

Host:
Windows ARM64, x64 emulation.

This base is already used successfully by the accepted P2 Dayu runtime.

## 4. Accepted Dedicated MCP Runtime

`D:\Codex\FinancialFilingDataFoundation\runtimes\ffdf-mcp-2.3.0\.venv`

Installed exact roots:
- `mcp==2.3.0`
- `PyMuPDF==1.28.2`

Resolved/installed:
**30 packages**

Core:
- mcp 2.3.0
- mcp-types 2.3.0
- PyMuPDF 1.28.2
- cryptography 50.0.2
- pywin32 312
- pydantic 2.14.2
- anyio 4.16.0

MCP server import:
`from mcp.server import MCPServer`
PASS.

## 5. Runtime Lock

Tracked:
`runtime-locks/mcp-2.3.0-py312-win-amd64.lock.txt`

Contains exact 30 package versions.

No local editable/file dependency.

## 6. Rebuild Verification

A fresh temporary venv was created from the same CPython 3.12.14 AMD64 base and installed only from the tracked lock.

Result:
- package count: 30
- normalized freeze: **MATCH**
- mcp: 2.3.0
- PyMuPDF: 1.28.2
- build: AMD64
- temporary verification runtime removed after PASS

## 7. Architecture Note

On Windows ARM64, `platform.machine()` may report host architecture even from the x64-emulated interpreter.

Architecture truth for this runtime is recorded using:
- base executable path
- `sys.version` build string = AMD64
- pointer size = 64-bit

## 8. Isolation

From FFDF main runtime:
`importlib.util.find_spec("mcp") == None`

PASS.

## 9. P8-B Gate

- exact SDK version: PASS
- isolated runtime: PASS
- no system Python/PATH mutation: PASS
- lock generated: PASS
- lock rebuild: PASS
- main runtime isolation: PASS
- P8-ISSUE-001 closed at environment layer: PASS

Final:
# PASS

Authorized next:
**P8-C Catalog / P8-D Query Service**
