# 29 — P8 Independent Acceptance Re-freeze

状态：**P8-J ACCEPTANCE INPUT REFREEZE**

Phase:
`P8 — Local MCP`

Repository:
`projectforkk/FinancialFilingDataFoundation`

Formal branch:
`task/p8-local-mcp`

Accepted baseline before P8:
`5f314bab9d88fb16b4b46c662e0a9f1b8f1a9b13`

Final reviewed candidate:
`d31a5851767f102082e2078cd09df2b023e84227`

Final Code Review commit:
`992a329c2ad765c0f34aa1445d19c63f71c0f3b3`

Final review evidence:
`development/46-p8-final-code-review.md`

The prior freeze:
- `acceptance/28-p8-acceptance-run-instruction.md`
- commit `85ad92cfb7c95b7049495fe951eacd1c80521a71`

is **INVALIDATED_BY_P8_ISSUE_005**.

---

## 1. Frozen Candidate

The acceptance candidate is the exact Git commit containing this file.

After commit, record its SHA in `PROJECT_STATUS.md`.

Independent Acceptance must use a fresh detached worktree at that exact SHA.

Do not use the moving P8 branch HEAD.

---

## 2. Mandatory Inputs

Read before acceptance:

- `AGENTS.md`
- `PROJECT_STATUS.md`
- `design/15-project-directory-management.md`
- `design/20-p8-local-mcp-design.md`
- `design/21-p8-implementation-plan.md`
- `development/41-p8-development-instruction.md`
- `development/42-p8-environment-audit.md`
- `development/43-p8-development-evidence.md`
- `development/44-p8-final-development-amendment.md`
- `development/46-p8-final-code-review.md`
- `acceptance/27-p8-acceptance-instruction.md`
- this file

---

## 3. Candidate Isolation

Acceptance worktree:

`D:\Codex\FinancialFilingDataFoundation\worktrees\acceptance\p8-<shortsha>`

Mode:
detached HEAD.

Before and after every critical command group:

```powershell
git rev-parse HEAD
git status --short --branch
```

Required:
- exact frozen SHA
- no tracked modification

---

## 4. Windows Pytest Temp Root

Use:

`D:\Codex\FinancialFilingDataFoundation\workspace\t\p8\accept-<shortsha>`

Rules:
- short path
- inside canonical project root
- not under detached worktree
- ignored/disposable test state only

---

## 5. Main Runtime

`D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe`

Expected:
- Python 3.14.9 ARM64
- PyMuPDF 1.28.2
- external `mcp` package absent

---

## 6. Dedicated MCP Runtime

`D:\Codex\FinancialFilingDataFoundation\runtimes\ffdf-mcp-2.3.0\.venv\Scripts\python.exe`

Expected:
- CPython 3.12.14 AMD64
- mcp 2.3.0
- PyMuPDF 1.28.2

Tracked lock:

`runtime-locks/mcp-2.3.0-py312-win-amd64.lock.txt`

Expected lock SHA256:

`8e958b8abcfd9b2de829451ffc253932fa26bb473f73837484b75b1019f092ec`

Required P8-ISSUE-005 checks:

1. `.gitattributes` contains:
   `runtime-locks/*.txt text eol=lf`
2. `git check-attr text eol` returns:
   - text: set
   - eol: lf
3. Git blob SHA256 == expected SHA
4. clean acceptance working-tree lock SHA256 == expected SHA
5. blob bytes == working-tree bytes
6. lock is UTF-8 without BOM
7. CRLF absent
8. installed dedicated runtime `uv pip freeze` normalized package set == tracked lock

Any mismatch = FAIL.

---

## 7. Canonical Live Catalog

Path:

`D:\Codex\FinancialFilingDataFoundation\workspace\mcp\p8-acceptance-catalog.json`

Expected SHA256:

`e493f2f6a951007c1e5ac932268796d35d33386760f4503d48ff0a7f7a148cdc`

Exactly two identities:

### CN
- 600519
- FY2024
- ANNUAL
- document SHA:
  `5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30`

### HK
- 00700
- FY2024
- ANNUAL
- document SHA:
  `70f529984a87ef7f46d9e1db26bb9ef27eef9c01d29c59aabf69e557b479a6a0`

All artifact paths must be project-root-relative.

---

## 8. Exact Tool Set

Exactly, in order:

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

No arbitrary file/directory/SQL/Python/shell tools.

---

## 9. Full Unit / Regression

Run from detached candidate:

```powershell
$env:PYTHONPATH="src"
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe \
  -m pytest tests\unit -q \
  --basetemp D:\Codex\FinancialFilingDataFoundation\workspace\t\p8\accept-<shortsha>
```

Expected current count:

`231 passed`

---

## 10. Static / Scope

Verify:

- compileall PASS
- `git diff --check` PASS
- P0–P7 source unchanged outside P8 `mcp/`
- service/catalog no network/subprocess/remote-AI imports
- server stdio only
- package initializer does not import external MCP SDK
- main runtime external MCP package absent
- no P9/P10/P11 implementation

---

## 11. Official MCP SDK Live Integration

Use:

`tests/integration/mcp_stdio_check.py`

Inputs:
- dedicated MCP runtime
- detached acceptance source root
- canonical acceptance catalog
- output under `workspace/current/p8/`

Mandatory:
- protocol negotiation succeeds
- exact 11 tools
- CN/HK list/get
- search/read pages/sections
- list/get table
- list/get raw fact
- evidence relation
- validation
- invalid document returns tool error
- stdout remains protocol-clean

---

## 12. Performance

Required:

- cold connect/list-tools <=15000 ms
- first trusted bundle per document <=20000 ms
- list_documents <=2000 ms
- warm get_document <=2000 ms
- warm search <=2000 ms
- warm read_pages <=2000 ms
- warm table <=5000 ms
- warm fact/evidence <=5000 ms
- warm validation <=5000 ms

Integration script asserts these limits.

---

## 13. Lazy Artifact Trust

Verify:

- service constructor does not eager-load bundles
- ffdf_list_documents is catalog-only identity metadata
- ffdf_list_documents does not claim P7 validation status
- first artifact-dependent call runs full P3/P5/P6/P7 loader validation
- validated bundle is cached
- corrupt upstream data produces `P8_UPSTREAM_ARTIFACT_INVALID`
- cache does not change deterministic business semantics

---

## 14. Read-only / Security

Verify:
- no acquisition
- no parser execution
- no artifact mutation
- no Registry mutation
- no overlay mutation
- no arbitrary path/file/SQL/Python/shell execution
- no HTTP/SSE listener
- no network
- no AI/sampling
- no P9/P10/P11 functionality

---

## 15. Immutability Snapshot

Before live SDK run, snapshot:
- canonical P8 catalog
- CN P3/P5/P6/P7 files
- HK P3/P5/P6/P7 files

For every file:
- SHA256
- size
- mtime_ns

After live calls, repeat.

Expected:
- file count: 25
- all fields identical
- changed files: []

---

## 16. Issue Closure

Acceptance must independently verify:

- P8-ISSUE-001: compatible isolated MCP runtime + lock
- P8-ISSUE-002: lazy cold startup
- P8-ISSUE-003: <=20s first trusted bundle
- P8-ISSUE-004: short project-root-local pytest temp root
- P8-ISSUE-005: EOL-stable lock bytes across clean worktree

---

## 17. PASS

PASS requires all frozen checks above to pass and no blocker.

---

## 18. FAIL

FAIL includes any:
- regression failure
- lock byte/package mismatch
- catalog mismatch
- tool contract mismatch
- protocol failure
- performance failure
- mutation
- security/scope leak
- eager preload regression
- P9/P10/P11 implementation in P8

---

## 19. BLOCKED

Only for an external condition that prevents judgment.

Do not use BLOCKED for an ordinary product/test failure.

---

## 20. Final Output

Verdict only:

`PASS / FAIL / BLOCKED`

Evidence summary must include:
- exact frozen SHA
- HEAD stability
- 231-test result
- lock package + byte result
- catalog hash
- protocol/tool result
- CN/HK result
- performance
- immutability
- security/scope
- blocker summary

Do not start P9 until P8 Independent Acceptance PASS.
