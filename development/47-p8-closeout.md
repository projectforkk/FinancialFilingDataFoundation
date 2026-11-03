# 47 — P8 Closeout

状态：**DONE / PASS**

Phase:
`P8 — Local MCP`

## 1. Accepted Inputs

Accepted baseline before P8:

`5f314bab9d88fb16b4b46c662e0a9f1b8f1a9b13`

Final reviewed production candidate:

`d31a5851767f102082e2078cd09df2b023e84227`

Final frozen Independent Acceptance candidate:

`fd8dccc7367ce682c972ab3aeff3c8d602044c41`

Independent Acceptance result:

`acceptance/31-p8-acceptance-result.md`

Verdict:

# PASS

## 2. Accepted Merge

Main merge commit:

`415d2ad82e890be855198d4d4c57bca8d1beb406`

Merge message:

`merge: accept P8 local MCP`

## 3. Accepted P8 Capabilities

P8 now provides:

- official MCP Python SDK 2.3.0 runtime；
- negotiated MCP protocol `2026-07-28`；
- local stdio transport only；
- exact 11 read-only deterministic domain tools；
- project-root-relative trusted artifact catalog；
- lazy per-document P3/P5/P6/P7 validation；
- cached trusted immutable document bundles；
- page / FTS / section query；
- reconstructed table list/detail；
- raw fact list/detail；
- evidence lookup；
- P7 validation report/issues lookup；
- deterministic tool error boundary；
- no arbitrary filesystem / SQL / Python / shell execution surface。

Exact tools:

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

## 4. Runtime / Lock

Dedicated MCP runtime:

`D:\Codex\FinancialFilingDataFoundation\runtimes\ffdf-mcp-2.3.0\.venv`

Accepted:
- CPython 3.12.14 AMD64
- mcp 2.3.0
- mcp-types 2.3.0
- PyMuPDF 1.28.2

Tracked lock:

`runtime-locks/mcp-2.3.0-py312-win-amd64.lock.txt`

Lock SHA256:

`8e958b8abcfD9b2de829451ffc253932fa26bb473f73837484b75b1019f092ec`

Runtime package set:
`30 / 30 MATCH`

Git blob / clean checkout bytes:
`MATCH`

EOL:
`LF`

## 5. Independent Acceptance

Full suite:

`231 passed`

Official SDK:
- protocol: `2026-07-28`
- exact tools: 11 / 11
- CN 600519 FY2024: PASS
- HK 00700 FY2024: PASS
- invalid document tool error: PASS
- read-only immutability: 25 / 25 files unchanged

Performance:
- cold connect: 1147.272 ms
- CN first trusted bundle: 10066.044 ms
- HK first trusted bundle: 14970.239 ms
- all warm gates: PASS

## 6. Post-merge Main Gate

Main HEAD under test:

`415d2ad82e890be855198d4d4c57bca8d1beb406`

Result:

`231 passed in 6.28s`

Also:
- compileall PASS
- git diff --check PASS
- main FFDF runtime external MCP package absent
- runtime lock SHA correct

## 7. P8 Issue Closure

Closed:

- P8-ISSUE-001 — CPython 3.14 ARM64 SDK dependency incompatibility
- P8-ISSUE-002 — eager artifact validation / cold startup
- P8-ISSUE-003 — empirical trusted-bundle performance calibration
- P8-ISSUE-004 — Windows deep pytest temp path
- P8-ISSUE-005 — runtime lock EOL portability

All design amendments preceded implementation changes.

## 8. Security Boundary

Accepted P8 does not provide:
- acquisition
- PDF parsing
- artifact mutation
- Registry mutation
- review overlay mutation
- arbitrary filesystem browsing
- arbitrary SQL
- arbitrary Python
- shell execution
- HTTP/SSE listener
- network calls from business service
- remote AI / sampling
- P9/P10/P11 functionality

`MCP_AI_API_CALLS = FORBIDDEN` remains active.

## 9. Next Authorized Phase

Authorized:

`P9 — Codex Review Overlay`

State:

`DESIGN AUTHORIZED`

Before production implementation, P9 must commit:
- `design/22-p9-review-overlay-design.md`
- `design/23-p9-implementation-plan.md`
- P9 development instruction
- P9 acceptance instruction

P9 must preserve:
`RAW -> LOCAL_EXTRACTED -> REVIEW_OVERLAY -> RESOLVED`

No P10 Skill or P11 SEC implementation is authorized during P9 design.
