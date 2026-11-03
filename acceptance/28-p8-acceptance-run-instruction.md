# 28 — P8 Independent Acceptance Run Instruction

状态：**P8-J ACCEPTANCE INPUT FREEZE**

Phase:
`P8 — Local MCP`

Repository:
`projectforkk/FinancialFilingDataFoundation`

Formal branch:
`task/p8-local-mcp`

Accepted baseline before P8:
`5f314bab9d88fb16b4b46c662e0a9f1b8f1a9b13`

Reviewed P8 candidate:
`599db48a62622cb18de2c61d7100e8186a7ca936`

Final Code Review commit:
`544a4cc887a7bdcad029b77f043cbf270906c91f`

Final Code Review verdict:
`PASS`

Review evidence:
`development/45-p8-code-review.md`

---

## 1. Frozen Candidate

The Independent Acceptance candidate is the **Git commit containing this file**.

After this file is committed, its exact SHA must be recorded in `PROJECT_STATUS.md`.

Acceptance must create/use a fresh detached worktree at that exact SHA.

Do not use a moving branch HEAD as acceptance input.

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
- `development/45-p8-code-review.md`
- `acceptance/27-p8-acceptance-instruction.md`
- this file

---

## 3. Candidate Isolation

Acceptance worktree:

`D:\Codex\FinancialFilingDataFoundation\worktrees\acceptance\p8-<shortsha>`

Mode:

detached HEAD at frozen candidate.

Before/after every critical command group:

```powershell
git rev-parse HEAD
git status --short --branch
```

Required:
- exact frozen SHA
- no tracked modifications

---

## 4. Windows Pytest Temp Rule

Use only:

`D:\Codex\FinancialFilingDataFoundation\workspace\t\p8\accept-<shortsha>`

Do not place pytest basetemp beneath the acceptance worktree.

Do not create FFDF-owned sibling temp roots under `D:\Codex`.

This path is ignored disposable test execution state.

---

## 5. Runtime

### Main FFDF runtime

`D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe`

Expected:
- Python 3.14.9 ARM64
- PyMuPDF 1.28.2
- external `mcp` package absent

### Dedicated MCP runtime

`D:\Codex\FinancialFilingDataFoundation\runtimes\ffdf-mcp-2.3.0\.venv\Scripts\python.exe`

Expected:
- CPython 3.12.14 AMD64
- mcp 2.3.0
- PyMuPDF 1.28.2

Tracked lock:

`runtime-locks/mcp-2.3.0-py312-win-amd64.lock.txt`

Lock SHA256:

`8e958b8abcfd9b2de829451ffc253932fa26bb473f73837484b75b1019f092ec`

Independent acceptance must compare installed freeze to this tracked lock.

---

## 6. Canonical Live Catalog

Path:

`D:\Codex\FinancialFilingDataFoundation\workspace\mcp\p8-acceptance-catalog.json`

SHA256:

`e493f2f6a951007c1e5ac932268796d35d33386760f4503d48ff0a7f7a148cdc`

Exactly two documents:

### CN
- market: CN
- ticker: 600519
- fiscal_year: 2024
- filing_type: ANNUAL
- document SHA:
  `5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30`

### HK
- market: HK
- ticker: 00700
- fiscal_year: 2024
- filing_type: ANNUAL
- document SHA:
  `70f529984a87ef7f46d9e1db26bb9ef27eef9c01d29c59aabf69e557b479a6a0`

Catalog paths must remain project-root-relative.

---

## 7. Exact Tool Contract

Acceptance requires exactly these 11 names in this order:

1. `ffdf_list_documents`
2. `ffdf_get_document`
3. `ffdf_search_document`
4. `ffdf_read_pages`
5. `ffdf_list_sections`
6. `ffdf_list_tables`
7. `ffdf_get_table`
8. `ffdf_list_raw_facts`
9. `ffdf_get_fact`
10. `ffdf_get_evidence`
11. `ffdf_get_validation`

No arbitrary filesystem/SQL/Python/shell tool is allowed.

---

## 8. Full Unit / Regression Suite

From detached acceptance candidate:

```powershell
$env:PYTHONPATH="src"
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe \
  -m pytest tests\unit -q \
  --basetemp D:\Codex\FinancialFilingDataFoundation\workspace\t\p8\accept-<shortsha>
```

Expected current count:

`231 passed`

Any actual unit/regression failure is `FAIL`, unless proven to be an external execution blocker.

---

## 9. Compile / Static Scope

Verify:

- compileall PASS
- `git diff --check` PASS
- no P0–P7 source changes outside `mcp/`
- business service has no network/subprocess/remote-AI imports
- server transport is stdio only
- package initializer does not import external MCP SDK
- main runtime remains MCP-free

---

## 10. Official SDK Stdio Integration

Use:

`tests/integration/mcp_stdio_check.py`

with:
- dedicated MCP runtime
- detached acceptance source root
- canonical live catalog
- output under project-root `workspace/current/p8/`

Mandatory:
- negotiated protocol works
- exact 11 tools
- CN/HK list
- CN/HK get_document
- search/read pages/sections
- table list/detail
- raw fact/evidence relation
- validation
- invalid document → tool error
- stdout protocol integrity

---

## 11. Performance Gates

Mandatory:

- cold connect/list-tools <= 15000 ms
- first trusted bundle per document <= 20000 ms
- list_documents <= 2000 ms
- warm get_document <= 2000 ms
- warm search <= 2000 ms
- warm read_pages <= 2000 ms
- warm table calls <= 5000 ms
- warm fact/evidence calls <= 5000 ms
- warm validation <= 5000 ms

The integration script contains these assertions.

---

## 12. Lazy Artifact Trust

Independently verify:

- service constructor does not eager-load document bundles
- `ffdf_list_documents` remains catalog-only and does not claim P7 status
- first artifact-dependent tool performs full P3/P5/P6/P7 trusted load
- successful bundle is cached
- corrupt upstream artifact returns `P8_UPSTREAM_ARTIFACT_INVALID`
- cache does not change business response semantics

---

## 13. Read-only / Security Boundary

Verify:
- no acquisition
- no parser execution
- no Registry mutation
- no artifact mutation
- no overlay mutation
- no arbitrary path tool
- no arbitrary SQL
- no execute-python
- no shell/command tool
- no HTTP/SSE listener
- no network use
- no remote AI / sampling
- no P9/P10/P11 behavior

---

## 14. Immutability Snapshot

Before official SDK live calls, snapshot:
- canonical P8 catalog
- CN P3/P5/P6/P7 files
- HK P3/P5/P6/P7 files

Fields:
- SHA256
- file size
- mtime_ns

After all live calls, repeat the snapshot.

Required:
- same file count
- identical SHA/size/mtime for every file

Expected current file count:
`25`

---

## 15. Issue-Specific Acceptance

### P8-ISSUE-001
Dedicated compatible runtime + exact lock: PASS required.

### P8-ISSUE-002
Cold startup must remain lazy and <=15s.

### P8-ISSUE-003
First trusted bundle <=20s without removing validation.

### P8-ISSUE-004
Full regression must use the project-root-local short basetemp and PASS.

---

## 16. PASS Conditions

PASS requires:
- exact frozen candidate
- HEAD stable
- full regression PASS
- runtime lock MATCH
- main runtime MCP absent
- exact catalog SHA
- exact 11 tools
- official SDK integration PASS
- CN/HK live PASS
- all performance gates PASS
- lazy artifact trust PASS
- read-only/security boundary PASS
- artifact/catalog immutability PASS
- no blocker

---

## 17. FAIL Conditions

FAIL includes:
- wrong tool list
- mutation
- network/AI path
- arbitrary tool surface
- P0–P7 regression
- runtime lock mismatch
- catalog mismatch
- protocol failure
- performance gate failure
- corrupt upstream accepted
- eager full-catalog preload reintroduced
- P9/P10/P11 implementation leaking into P8

---

## 18. BLOCKED

Use BLOCKED only for an external condition that prevents a valid judgment.

Do not use BLOCKED for an ordinary product/test failure.

---

## 19. Acceptance Output

Final verdict only:

`PASS / FAIL / BLOCKED`

Evidence summary must include:
- frozen SHA
- HEAD stability
- 231-test result
- lock result
- catalog SHA
- protocol/tool list
- CN/HK results
- performance
- immutability
- scope/security
- blocker summary

Do not start P9 until P8 Independent Acceptance = PASS.
