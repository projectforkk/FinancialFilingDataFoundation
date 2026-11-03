# 47 — P8 Dual-Runtime Test Boundary Amendment Evidence

状态：**P8-E / P8-F / P8-H REVALIDATED**

Phase:
`P8 — Local MCP`

Issue:
`P8-ISSUE-006 — SDK boundary tests span two intentionally different runtimes`

Design amendment commit:
`bdab6a81bea6597ab2c12256497ed68d04363ea2`

Test amendment commit:
`f41e6a1eea1f2f60fc9b70ed5a5aa7b76f59562b`

P8 production code:
unchanged from the previously accepted/reviewed production implementation.

## 1. Finding

The first post-acceptance server-adapter pytest attempt showed that:

- FFDF main ARM64 runtime intentionally does not install external `mcp` / `anyio`;
- dedicated MCP runtime intentionally contains the frozen production MCP dependency set and does not install pytest;
- therefore one pytest module cannot be used to execute SDK-boundary tests in both runtimes without mutating a runtime contract.

This is a test execution boundary, not a product defect.

## 2. Approved Resolution

- main pytest suite stays SDK-free;
- main suite gains static AST/server-surface tests that do not import external MCP SDK;
- official SDK execution continues through tracked standalone:
  `tests/integration/mcp_stdio_check.py`
- dedicated MCP runtime lock is unchanged;
- no pytest is installed into the MCP runtime.

## 3. Main Runtime Regression

Candidate:

`f41e6a1eea1f2f60fc9b70ed5a5aa7b76f59562b`

Command used project-root short Windows basetemp.

Result:

`235 passed in 5.57s`

New static server tests:

`4 passed`

Verified:
- exact 11 static tool names;
- no arbitrary shell/sql/python/write/network tool name;
- stdio-only server invocation;
- no HTTP/SSE listener call in server source;
- no network/AI/process-execution imports in server adapter.

## 4. Dedicated Runtime SDK Harness

Runtime:

`runtimes/ffdf-mcp-2.3.0/.venv`

Tracked standalone harness:

`tests/integration/mcp_stdio_check.py`

Observed:

- protocol: `2026-07-28`
- cold connect/list-tools: `1062.027 ms`
- exact tools: `11 / 11 PASS`
- CN first trusted bundle: `9613.780 ms`
- HK first trusted bundle: `16021.619 ms`
- invalid document => MCP tool error: PASS
- CN/HK live calls: PASS

Warm:
- list_documents: 2.623 ms
- get_document: 2.250 ms
- search: 7.225 ms
- read_pages: 3.340 ms
- get_table: 1.722 ms
- fact/evidence: 2.833 ms
- validation: 3.650 ms

All frozen performance gates PASS.

## 5. Runtime Lock

Tracked lock:

`runtime-locks/mcp-2.3.0-py312-win-amd64.lock.txt`

Observed SHA256:

`8e958b8abcfd9b2de829451ffc253932fa26bb473f73837484b75b1019f092ec`

Git attributes:

- text = set
- eol = lf

No runtime package change was made.

## 6. Gate Impact

- P8-E MCP Adapter: REVALIDATED PASS
- P8-F Deterministic/Security Regression: REVALIDATED PASS
- P8-H Official SDK Protocol Integration: REVALIDATED PASS
- prior P8 Independent Acceptance is historical because the design changed afterward
- P8-I/J/K must be rerun for the amended test-execution contract

Next:

**new detached P8 Code Review**
