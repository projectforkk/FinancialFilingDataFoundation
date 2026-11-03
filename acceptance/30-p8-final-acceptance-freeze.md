# 30 — P8 Final Independent Acceptance Freeze

状态：**P8-J FINAL ACCEPTANCE FREEZE**

Phase:
`P8 — Local MCP`

Repository:
`projectforkk/FinancialFilingDataFoundation`

Branch:
`task/p8-local-mcp`

Accepted baseline before P8:
`5f314bab9d88fb16b4b46c662e0a9f1b8f1a9b13`

Final reviewed candidate:
`d31a5851767f102082e2078cd09df2b023e84227`

Final review evidence:
- `development/45-p8-code-review.md`
- `development/46-p8-final-code-review.md`

Review/evidence branch state before freeze:
`75440093528e6a984d3c86362727d5615af25997`

Prior freezes:
- `acceptance/28-p8-acceptance-run-instruction.md`
- `acceptance/29-p8-acceptance-refreeze.md`

are historical and **not** the final acceptance input.

---

## 1. Frozen Candidate

The exact P8 Independent Acceptance candidate is the commit containing this file.

After committing this file, record that exact SHA in `PROJECT_STATUS.md`.

Acceptance must use a fresh detached worktree at that SHA.

No moving branch HEAD may be substituted.

---

## 2. Mandatory Inputs

Read:
- AGENTS.md
- PROJECT_STATUS.md
- design/15-project-directory-management.md
- design/20-p8-local-mcp-design.md
- design/21-p8-implementation-plan.md
- development/41-p8-development-instruction.md
- development/42-p8-environment-audit.md
- development/43-p8-development-evidence.md
- development/44-p8-final-development-amendment.md
- development/45-p8-code-review.md
- development/46-p8-final-code-review.md
- acceptance/27-p8-acceptance-instruction.md
- this file

---

## 3. Acceptance Worktree

Path:
`D:\Codex\FinancialFilingDataFoundation\worktrees\acceptance\p8-<shortsha>`

Mode:
detached HEAD.

Before/after every critical command group:
- `git rev-parse HEAD`
- `git status --short --branch`

HEAD must equal frozen SHA and tracked state must remain clean.

---

## 4. Pytest Temp Root

Windows acceptance basetemp:

`D:\Codex\FinancialFilingDataFoundation\workspace\t\p8\accept-<shortsha>`

Requirements:
- short path
- inside canonical project root
- outside detached acceptance worktree
- ignored/disposable only

---

## 5. Main Runtime

`D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe`

Expected:
- Python 3.14.9 ARM64
- PyMuPDF 1.28.2
- external mcp package absent

---

## 6. Dedicated MCP Runtime

`D:\Codex\FinancialFilingDataFoundation\runtimes\ffdf-mcp-2.3.0\.venv\Scripts\python.exe`

Expected:
- Python 3.12.14 AMD64
- mcp 2.3.0
- mcp-types 2.3.0
- PyMuPDF 1.28.2

Lock:
`runtime-locks/mcp-2.3.0-py312-win-amd64.lock.txt`

Expected SHA256:
`8e958b8abcfd9b2de829451ffc253932fa26bb473f73837484b75b1019f092ec`

Mandatory P8-ISSUE-005 checks:
- `.gitattributes` contains `runtime-locks/*.txt text eol=lf`
- `git check-attr`: text=set, eol=lf
- Git blob SHA == expected SHA
- acceptance working-tree SHA == expected SHA
- blob bytes == working-tree bytes
- no BOM
- no CRLF
- installed `uv pip freeze` normalized package set == tracked lock

---

## 7. Canonical Catalog

Path:
`D:\Codex\FinancialFilingDataFoundation\workspace\mcp\p8-acceptance-catalog.json`

Expected SHA256:
`e493f2f6a951007c1e5ac932268796d35d33386760f4503d48ff0a7f7a148cdc`

Exactly:
- CN / 600519 / FY2024 / ANNUAL / SHA `5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30`
- HK / 00700 / FY2024 / ANNUAL / SHA `70f529984a87ef7f46d9e1db26bb9ef27eef9c01d29c59aabf69e557b479a6a0`

All catalog artifact paths must remain project-root-relative.

---

## 8. Exact Tool Contract

Exactly:
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

No arbitrary filesystem, directory, SQL, Python, shell, command, acquisition, parse or mutation tool.

---

## 9. Full Regression

Run:
```powershell
$env:PYTHONPATH="src"
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -m pytest tests\unit -q --basetemp D:\Codex\FinancialFilingDataFoundation\workspace\t\p8\accept-<shortsha>
```

Expected current count:
`231 passed`

---

## 10. Static / Scope

Verify:
- compileall PASS
- git diff --check PASS
- no P0–P7 source change outside new mcp package
- business service no network/subprocess/remote-AI imports
- stdio only
- main runtime MCP-free
- no P9/P10/P11 implementation

---

## 11. Official SDK Integration

Run `tests/integration/mcp_stdio_check.py` with:
- dedicated MCP runtime
- detached acceptance source root
- canonical catalog
- output under project-root `workspace/current/p8/`

Require:
- negotiated protocol succeeds
- exact 11 tools
- CN/HK list/get
- search/read pages/sections
- table list/detail
- fact/evidence relation
- validation
- invalid document returns tool error
- protocol-clean stdout

---

## 12. Performance

Require:
- cold connect/list-tools <=15000 ms
- first trusted bundle per document <=20000 ms
- list_documents <=2000 ms
- warm get_document <=2000 ms
- warm search <=2000 ms
- warm read_pages <=2000 ms
- warm table <=5000 ms
- warm fact/evidence <=5000 ms
- warm validation <=5000 ms

---

## 13. Lazy Artifact Trust

Verify:
- constructor does not eager-load full catalog artifacts
- ffdf_list_documents is catalog-only identity metadata
- first content call runs full P3/P5/P6/P7 loaders/tamper checks
- trusted bundle cached by SHA
- upstream corruption maps to P8_UPSTREAM_ARTIFACT_INVALID
- cache does not change deterministic result semantics

---

## 14. Read-only Boundary

Verify no:
- acquisition
- parser execution
- artifact mutation
- Registry mutation
- review overlay mutation
- arbitrary filesystem/SQL/Python/shell
- HTTP/SSE listener
- network
- remote AI/sampling
- P9/P10/P11 behavior

---

## 15. Immutability

Before/after official SDK calls snapshot:
- canonical P8 catalog
- CN P3/P5/P6/P7 files
- HK P3/P5/P6/P7 files

Fields:
- SHA256
- size
- mtime_ns

Expected:
- 25 files
- identical before/after
- changed=[]

---

## 16. Issue Closure

Independently verify closed:
- P8-ISSUE-001 runtime compatibility
- P8-ISSUE-002 lazy startup
- P8-ISSUE-003 <=20s trusted bundle
- P8-ISSUE-004 project-root short pytest path
- P8-ISSUE-005 EOL-stable lock bytes

---

## 17. Verdict

Final verdict only:
`PASS / FAIL / BLOCKED`

PASS requires every frozen check above and no blocker.

Acceptance must not modify production, tests, design, config, runtime/dependencies or source artifacts.

P9 must not start before P8 PASS.
