# 32 — P8 Independent Acceptance Refreeze After P8-ISSUE-006

状态：**P8-J ACCEPTANCE REFREEZE**

Phase:
`P8 — Local MCP`

Repository:
`projectforkk/FinancialFilingDataFoundation`

Branch:
`task/p8-local-mcp`

Accepted baseline before P8:
`5f314bab9d88fb16b4b46c662e0a9f1b8f1a9b13`

Latest reviewed candidate:
`537ebbd17454f80c8838f58abbbd02d5994f8716`

Latest review evidence:
`development/48-p8-issue006-code-review.md`

Latest review commit:
`537b0fed9ae00d29f69f1ea6481a92793b4c22a7`

Historical acceptance:
- `acceptance/30-p8-final-acceptance-freeze.md`
- `acceptance/31-p8-acceptance-result.md`
- verdict: PASS
- status: historical / invalidated for final closeout by P8-ISSUE-006

## 1. Frozen Candidate

The exact Independent Acceptance candidate is the commit containing this file.

After commit, record that SHA in `PROJECT_STATUS.md`.

Acceptance must use a fresh detached worktree at exactly that SHA.

## 2. Mandatory Inputs

Read:
- AGENTS.md
- PROJECT_STATUS.md
- design/20-p8-local-mcp-design.md
- design/21-p8-implementation-plan.md
- development/41-p8-development-instruction.md
- development/42-p8-environment-audit.md
- development/47-p8-dual-runtime-test-amendment.md
- development/48-p8-issue006-code-review.md
- acceptance/27-p8-acceptance-instruction.md
- this file

## 3. Worktree

Path:

`D:\Codex\FinancialFilingDataFoundation\worktrees\acceptance\p8-<shortsha>`

Mode:
detached HEAD.

HEAD/status before and after each critical group must remain unchanged.

## 4. Main Runtime

`D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe`

Expected:
- Python 3.14.9 ARM64
- external mcp package absent
- no dedicated-SDK dependency added for P8-ISSUE-006

## 5. Dedicated MCP Runtime

`D:\Codex\FinancialFilingDataFoundation\runtimes\ffdf-mcp-2.3.0\.venv\Scripts\python.exe`

Expected:
- Python 3.12.14 AMD64
- mcp 2.3.0
- PyMuPDF 1.28.2
- pytest is not required/added merely for SDK-boundary testing

Runtime lock:

`runtime-locks/mcp-2.3.0-py312-win-amd64.lock.txt`

Expected SHA256:

`8e958b8abcfd9b2de829451ffc253932fa26bb473f73837484b75b1019f092ec`

Require:
- Git blob SHA == working-tree SHA == expected SHA
- bytes equal
- no BOM
- no CRLF
- git attribute text=set, eol=lf
- installed normalized package set == lock package set

## 6. Main Regression

Use project-root short basetemp:

`D:\Codex\FinancialFilingDataFoundation\workspace\t\p8\accept-<shortsha>`

Run:

`python -m pytest tests\unit -q`

Expected current count:

`235 passed`

This includes the four new static server-boundary tests and requires no external MCP SDK in the main runtime.

## 7. Dedicated Runtime Standalone SDK Harness

Run tracked:

`tests/integration/mcp_stdio_check.py`

using the dedicated MCP runtime.

Do not install pytest into the dedicated runtime.

Inputs:
- project root = canonical project root
- source root = detached acceptance worktree
- catalog = `workspace\mcp\p8-acceptance-catalog.json`
- output = project-root ignored workspace

Require:
- official SDK server spawn
- protocol negotiation
- exact 11 tools
- CN/HK live tool calls
- invalid document => tool error
- no protocol stdout pollution
- all frozen performance gates

## 8. Canonical Catalog

Path:

`D:\Codex\FinancialFilingDataFoundation\workspace\mcp\p8-acceptance-catalog.json`

Expected SHA256:

`e493f2f6a951007c1e5ac932268796d35d33386760f4503d48ff0a7f7a148cdc`

Exactly two documents:
- CN 600519 FY2024 SHA `5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30`
- HK 00700 FY2024 SHA `70f529984a87ef7f46d9e1db26bb9ef27eef9c01d29c59aabf69e557b479a6a0`

## 9. Performance Gates

- cold connect/list-tools <= 15000 ms
- first trusted bundle per document <= 20000 ms
- list_documents <= 2000 ms
- warm get_document <= 2000 ms
- warm search <= 2000 ms
- warm read_pages <= 2000 ms
- warm get_table <= 5000 ms
- warm fact/evidence <= 5000 ms
- warm validation <= 5000 ms

## 10. Security / Scope

Verify:
- P0–P7 source/tests unchanged outside P8 additions
- static exact 11 tool names
- stdio only
- no HTTP/SSE listener invocation
- no arbitrary filesystem/SQL/Python/shell/mutation tool
- no network/AI business path
- no P9/P10/P11 implementation

## 11. Immutability

Snapshot before/after standalone SDK harness:
- canonical catalog
- CN P3/P5/P6/P7 artifact files
- HK P3/P5/P6/P7 artifact files

Compare:
- SHA256
- size
- mtime_ns
- file count

Expected unchanged.

## 12. P8-ISSUE-006 Closure

Acceptance must explicitly verify:
- main pytest suite is SDK-free;
- dedicated MCP runtime lock did not gain pytest only for tests;
- tracked standalone harness executes successfully under dedicated runtime;
- no product behavior changed merely to satisfy test-runtime differences.

## 13. Verdict

Final verdict only:
`PASS / FAIL / BLOCKED`

P8 PASS allows P8-L closeout and P9 design authorization.

P9 implementation must not start during P8 acceptance.
