# 31 — P8 Independent Acceptance Result

状态：**PASS**

Phase:
`P8 — Local MCP`

Frozen acceptance candidate:
`fd8dccc7367ce682c972ab3aeff3c8d602044c41`

Final reviewed candidate:
`d31a5851767f102082e2078cd09df2b023e84227`

Final Code Review commit:
`992a329c2ad765c0f34aa1445d19c63f71c0f3b3`

Accepted baseline before P8:
`5f314bab9d88fb16b4b46c662e0a9f1b8f1a9b13`

## Verdict

# PASS

## 1. Acceptance Isolation

Detached worktree:

`D:\Codex\FinancialFilingDataFoundation\worktrees\acceptance\p8-fd8dccc`

Frozen HEAD before/after all critical groups:

`fd8dccc7367ce682c972ab3aeff3c8d602044c41`

Tracked status remained clean.

Result:
**PASS**

## 2. Full Regression

P0–P8 unit suite:

`231 passed in 6.07s`

P0–P7 source/tests vs accepted P7 baseline:

**zero diff**

compileall:
PASS

`git diff --check`:
PASS

Result:
**PASS**

## 3. Runtime Isolation

FFDF main runtime:

`D:\Codex\FinancialFilingDataFoundation\.venv`

Observed:
- Python 3.14.9 ARM64
- external `mcp`: absent

Dedicated MCP runtime:

`D:\Codex\FinancialFilingDataFoundation\runtimes\ffdf-mcp-2.3.0\.venv`

Observed:
- CPython 3.12.14 AMD64
- 64-bit
- mcp 2.3.0
- mcp-types 2.3.0
- PyMuPDF 1.28.2

Result:
**PASS**

## 4. Runtime Lock / P8-ISSUE-005

Tracked lock:

`runtime-locks/mcp-2.3.0-py312-win-amd64.lock.txt`

Expected SHA256:

`8e958b8abcfD9b2de829451ffc253932fa26bb473f73837484b75b1019f092ec`

Independent acceptance observed:

- Git blob SHA256:
  `8e958b8abcfD9b2de829451ffc253932fa26bb473f73837484b75b1019f092ec`
- acceptance worktree SHA256:
  `8e958b8abcfD9b2de829451ffc253932fa26bb473f73837484b75b1019f092ec`
- blob/worktree bytes equal: true
- BOM: false
- CRLF: false
- git attribute text: set
- git attribute eol: lf

Installed runtime package set:
- tracked lock package count: 30
- installed normalized freeze count: 30
- exact normalized set match: true
- missing: []
- extra: []

Result:
**PASS**

## 5. Canonical Catalog

Path:

`D:\Codex\FinancialFilingDataFoundation\workspace\mcp\p8-acceptance-catalog.json`

SHA256:

`e493f2f6a951007c1e5ac932268796d35d33386760f4503d48ff0a7f7a148cdc`

Documents: exactly 2.

CN:
- market: CN
- ticker: 600519
- fiscal_year: 2024
- filing_type: ANNUAL
- document SHA:
  `5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30`

HK:
- market: HK
- ticker: 00700
- fiscal_year: 2024
- filing_type: ANNUAL
- document SHA:
  `70f529984a87ef7f46d9e1db26bb9ef27eef9c01d29c59aabf69e557b479a6a0`

All P3/P5/P6/P7 paths:
project-root-relative.

Result:
**PASS**

## 6. Static / Security Boundary

Business service/catalog acceptance scan found no:
- arbitrary network client imports
- socket access
- subprocess execution
- remote AI imports
- arbitrary filesystem tool surface
- sqlite_query
- execute_python
- run_command

Server transport:
- `server.run("stdio")` only

No HTTP/SSE listener invocation.

No P9/P10/P11 implementation in P8.

Result:
**PASS**

## 7. Official MCP SDK Integration

Runtime:
official `mcp==2.3.0`

Client:
`Client(StdioServerParameters(...), mode="auto")`

Negotiated protocol:

**2026-07-28**

Cold connect:

`1147.272 ms`

Gate <=15000 ms:
PASS.

Exact tools, in order:

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

Tool contract:
**11 / 11 PASS**

## 8. Live CN — 600519 FY2024

First trusted bundle:

`10066.044 ms`

Gate <=20000 ms:
PASS.

Returned:
- page_count: 143
- table_count: 97
- raw_fact_count: 2177
- validation_status: REVIEW_REQUIRED
- validation_issue_count: 3
- search_returned: 5
- read_pages_returned: 1
- sections_returned: 1000
- tables_total: 97
- table detail identity: true
- fact/evidence relation: true

Result:
**PASS**

## 9. Live HK — 00700 FY2024

First trusted bundle:

`14970.239 ms`

Gate <=20000 ms:
PASS.

Returned:
- page_count: 274
- table_count: 97
- raw_fact_count: 2989
- validation_status: REVIEW_REQUIRED
- validation_issue_count: 6

Result:
**PASS**

## 10. Warm Protocol Performance

- list_documents: 3.764 ms
- get_document: 3.261 ms
- search: 7.517 ms
- read_pages: 2.948 ms
- get_table: 3.282 ms
- fact + evidence: 6.794 ms
- validation: 3.980 ms

All frozen warm gates:
**PASS**

## 11. Error Boundary

Invalid document:
- MCP result `is_error=True`

Valid P7 `REVIEW_REQUIRED`:
- returned as document validation state
- not fabricated as MCP execution error

Upstream corruption behavior is covered by the accepted deterministic suite:
- `P8_UPSTREAM_ARTIFACT_INVALID`

Result:
**PASS**

## 12. Read-only Immutability

Snapshot scope:
- canonical P8 catalog
- CN P3/P5/P6/P7 files
- HK P3/P5/P6/P7 files

Files:
`25`

Before/after:
- SHA256: identical
- size: identical
- mtime_ns: identical
- file count: 25 / 25
- changed files: []

Result:
**PASS**

## 13. Issue Closure

Independently verified:

- P8-ISSUE-001 — compatible isolated MCP runtime: PASS
- P8-ISSUE-002 — lazy startup / no eager bundle load: PASS
- P8-ISSUE-003 — first trusted bundle <=20s: PASS
- P8-ISSUE-004 — short project-root pytest root: PASS
- P8-ISSUE-005 — EOL-stable runtime lock bytes: PASS

## 14. Final Summary

- frozen SHA stability: PASS
- full regression: PASS
- prior-phase integrity: PASS
- runtime isolation: PASS
- package lock reproducibility: PASS
- lock byte reproducibility: PASS
- catalog integrity: PASS
- static security/scope: PASS
- official SDK protocol: PASS
- exact tool contract: PASS
- CN live: PASS
- HK live: PASS
- performance: PASS
- immutability: PASS
- blockers: NONE

Final verdict:

# PASS

P8 may proceed to closeout.

P9 implementation was not started during P8 Independent Acceptance.
