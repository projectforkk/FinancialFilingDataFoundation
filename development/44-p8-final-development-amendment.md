# 44 — P8 Final Development Amendment Evidence

状态：**P8 DEVELOPMENT COMPLETE / FINAL CANDIDATE READY FOR CODE REVIEW**

Branch:
`task/p8-local-mcp`

Accepted baseline before P8:
`5f314bab9d88fb16b4b46c662e0a9f1b8f1a9b13`

Initial design baseline:
`bf39d2028e4c03bee724c1c5389d513ebc904d00`

Core production commit:
`9e026677eff177737202c43a5702ce2ec880573d`

Official SDK integration/performance assertion test commit:
`45a01ad385d88e28ca178ff0d55ef7e79f0fa507`

Runtime/lock commit:
`89b3cec9e72d76ee3624322328dcd36231434557`

Design amendments:

- P8-ISSUE-001 — compatible MCP runtime base:
  `382a08369182c5be49a5e706ce62d8121a730dcb`
- P8-ISSUE-002 — lazy artifact trust:
  `4cdac4c4dda5f65806bcf2d31513e508d2a21e57`
- P8-ISSUE-003 — trusted-bundle performance calibration:
  `fdd13e0d0a9960d73698460f08ef047126b3362c`
- P8-ISSUE-004 — Windows deep pytest temp path:
  initial amendment `52db63e9407d415c06ab15b0be6517c594316507`,
  issue-number correction `dd3fb8a934ba2b9e0df8d2ad545e764c7aac118a`,
  final project-root path correction `7708abb383fd8e8c6fafdf6cad09f8e20ca15993`
- P8-ISSUE-005 — runtime lock EOL portability:
  design amendment `261c664a8ec39e194bb87a50bc01a9176a1365c1`,
  `.gitattributes` implementation `e8ca4a9c670a7da6065b2fefa58c323ea5b30c86`

Earlier development evidence:
`development/43-p8-development-evidence.md`

Environment evidence:
`development/42-p8-environment-audit.md`

---

## 1. Final Implemented Scope

Implemented:

- project-root-relative MCP catalog；
- path containment / duplicate identity guards；
- lazy trusted P3/P5/P6/P7 bundle validation；
- immutable per-process validated bundle cache；
- exact 11 read-only domain tools；
- P3 local FTS/page/section queries；
- P5 table list/detail；
- P6 raw fact/evidence list/detail；
- P7 validation report/issues；
- deterministic argument/pagination/payload guards；
- official MCP Python SDK 2.3.0 stdio adapter；
- deterministic ToolError mapping；
- official SDK integration/performance gate script。

Not implemented:

- acquisition；
- PDF parsing；
- artifact mutation；
- Registry mutation；
- review overlay mutation；
- arbitrary filesystem tool；
- arbitrary SQL/Python/shell execution；
- HTTP/SSE listener；
- network use；
- remote AI / sampling；
- P9/P10/P11 behavior。

---

## 2. Runtime / Lock

Dedicated MCP runtime:

`D:\Codex\FinancialFilingDataFoundation\runtimes\ffdf-mcp-2.3.0\.venv`

Approved base:

`C:\Users\guoyg\AppData\Roaming\uv\python\cpython-3.12.14-windows-x86_64-none\python.exe`

Build:
CPython 3.12.14 AMD64 under Windows ARM64 x64 emulation.

Exact roots:

- mcp 2.3.0
- mcp-types 2.3.0
- PyMuPDF 1.28.2

Tracked lock:

`runtime-locks/mcp-2.3.0-py312-win-amd64.lock.txt`

Lock SHA256:

`8e958b8abcfD9b2de829451ffc253932fa26bb473f73837484b75b1019f092ec`

Normalized empty-venv rebuild:
**MATCH — 30 packages**

Main FFDF runtime:

`D:\Codex\FinancialFilingDataFoundation\.venv`

External MCP package:
**absent**

Runtime-lock checkout contract:
- `.gitattributes`: `runtime-locks/*.txt text eol=lf`
- Git blob SHA256: `8e958b8abcfD9b2de829451ffc253932fa26bb473f73837484b75b1019f092ec`
- fresh detached checkout working-tree SHA256: `8e958b8abcfD9b2de829451ffc253932fa26bb473f73837484b75b1019f092ec`
- blob/worktree bytes equal: `PASS`
- CRLF present: `false`

---

## 3. P8-ISSUE-001 — CPython 3.14 ARM64 SDK Dependency Path

Initial CPython 3.14.9 ARM64 installation of exact `mcp==2.3.0` selected `cryptography==50.0.2`, fell back to a source build, and failed because MSVC `link.exe` was unavailable.

Rejected:
- install Visual Studio Build Tools only for P8；
- mutate system compiler environment；
- SDK downgrade；
- unpinned MCP version。

Approved:
- isolated CPython 3.12.14 AMD64 runtime；
- exact dependency lock；
- main Python 3.14 ARM64 unchanged。

Result:
**CLOSED / PASS**

---

## 4. P8-ISSUE-002 — Eager Artifact Validation

Initial server construction eagerly validated both live documents.

Observed initial official SDK cold connect:

`25928.336 ms`

This exceeded the 15s gate.

Implemented:
- service constructor becomes catalog-only；
- `ffdf_list_documents` is identity-only；
- first artifact-dependent call validates one document；
- validated immutable bundle cached for warm calls。

Final lazy service constructor:

`0.005 ms`

Final official SDK cold connect:

`1124.791 ms`

Gate <=15000 ms:
**PASS**

Result:
**CLOSED / PASS**

---

## 5. P8-ISSUE-003 — First Trusted-Bundle Performance Calibration

Post-lazy first official run measured:

- CN: 9985.873 ms
- HK: 15104.469 ms

The provisional 15s first-bundle threshold was created before measuring the accepted 274-page HK input.

Design was amended to:
- retain full P3/P5/P6/P7 loader/tamper validation；
- keep cold connect <=15s；
- set first trusted bundle per document <=20s；
- leave warm tool gates unchanged。

Final gated official SDK run:

- CN first trusted bundle:
  `9589.440 ms`
- HK first trusted bundle:
  `12562.471 ms`

Both <=20000 ms:
**PASS**

Result:
**CLOSED / PASS**

---

## 6. P8-ISSUE-004 — Windows Deep Pytest Temp Path

A full-regression attempt using a basetemp nested beneath the already-deep active worktree caused P4/P5/P6 atomic test output paths to exceed the practical Windows path limit.

The original external diagnostic path under:

`D:\Codex\_ffdf_p8_pytest`

proved the failure was path-length-related, but that location is **not accepted** because project directory governance requires FFDF-owned execution state under the canonical project root.

Final accepted basetemp convention:

`D:\Codex\FinancialFilingDataFoundation\workspace\t\p8\<run>`

Final diagnostic/full regression command used:

`D:\Codex\FinancialFilingDataFoundation\workspace\t\p8\diag-full`

Result:

`231 passed in 6.10s`

- FAIL: 0
- ERROR: 0
- project-root containment: PASS
- no accepted P4/P5/P6 production naming changed

Result:
**CLOSED / PASS**

---

## 7. P8-ISSUE-005 — Runtime Lock EOL Portability

Code Review of the earlier candidate `599db48a62622cb18de2c61d7100e8186a7ca936` found that global `core.autocrlf=true` materialized the tracked lock as CRLF in a fresh detached worktree, while the active worktree still held LF bytes. Dependency content was unchanged, but the byte-level lock SHA differed across worktrees.

Design was amended before repository changes.

Implemented:
- tracked `.gitattributes`；
- `runtime-locks/*.txt text eol=lf`；
- current lock remains UTF-8 without BOM；
- no package version changed。

Fresh detached verification at `e8ca4a9c670a7da6065b2fefa58c323ea5b30c86`:
- Git blob SHA256: `8e958b8abcfD9b2de829451ffc253932fa26bb473f73837484b75b1019f092ec`；
- working-tree SHA256: `8e958b8abcfD9b2de829451ffc253932fa26bb473f73837484b75b1019f092ec`；
- blob CRLF: false；
- worktree CRLF: false；
- bytes equal: PASS。

The earlier `599db48...` Review candidate is invalidated as the final acceptance path. A new Review candidate must include this amendment.

Result:
**CLOSED / PASS**

---

## 8. Final Unit / Regression

P8 focused:

`18 passed in 0.90s`

P0–P8 full suite:

`231 passed in 6.10s`

Project-root-local basetemp:
`workspace\t\p8\diag-full`

Additional:

- compileall: PASS
- git diff --check: PASS
- service/catalog no network/AI/subprocess imports: PASS
- server source starts stdio only: PASS
- package initializer does not import external MCP SDK: PASS
- static exact tool names: 11/11

---

## 9. Canonical Live Catalog

Operational ignored catalog:

`workspace/mcp/p8-acceptance-catalog.json`

SHA256:

`e493f2f6a951007c1e5ac932268796d35d33386760f4503d48ff0a7f7a148cdc`

Documents:

### CN

- market: CN
- ticker: 600519
- fiscal year: 2024
- filing type: ANNUAL
- document SHA:
  `5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30`

### HK

- market: HK
- ticker: 00700
- fiscal year: 2024
- filing type: ANNUAL
- document SHA:
  `70f529984a87ef7f46d9e1db26bb9ef27eef9c01d29c59aabf69e557b479a6a0`

All catalog artifact paths:
**project-root-relative**

---

## 10. Business Service Live

Final main-runtime live service run:

Service constructor:
`0.005 ms`

### CN

- first trusted bundle: 3635.958 ms
- pages: 143
- tables: 97
- facts: 2177
- evidence: 2177
- validation: REVIEW_REQUIRED
- issues: 3
- search returned: 5
- fact/evidence relation: PASS

Warm:
- search 0.894 ms
- read page 0.014 ms
- list sections 12.516 ms
- list tables 0.721 ms
- get table 0.092 ms
- list raw facts 2.512 ms
- get fact 0.019 ms
- get evidence 0.035 ms
- validation 0.091 ms

### HK

- first trusted bundle: 7929.668 ms
- pages: 274
- tables: 97
- facts: 2989
- evidence: 2989
- validation: REVIEW_REQUIRED
- issues: 6
- fact/evidence relation: PASS

Warm:
- search 0.868 ms
- read page 0.024 ms
- list sections 16.851 ms
- list tables 0.612 ms
- get table 1.464 ms
- list raw facts 3.609 ms
- get fact 0.011 ms
- get evidence 0.014 ms
- validation 0.053 ms

Catalog + P3/P5/P6/P7 before/after snapshot:
**UNCHANGED**

---

## 11. Official MCP SDK Stdio Integration

Client:

`Client(StdioServerParameters(...), mode="auto")`

Runtime:
official `mcp==2.3.0`

Server:
exact current P8 branch source over stdio.

Negotiated protocol:

**2026-07-28**

Final gated run:

- cold connect:
  `1124.791 ms`
- CN first bundle:
  `9589.440 ms`
- HK first bundle:
  `12562.471 ms`

Warm protocol-level calls:

- list_documents: 1.839 ms
- get_document: 1.559 ms
- search: 3.899 ms
- read_pages: 2.722 ms
- get_table: 2.479 ms
- get_fact + get_evidence: 3.270 ms
- validation: 2.677 ms

All performance assertions:
**PASS**

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

Tool list:
**11 / 11 PASS**

Representative calls:
**PASS**

Invalid document:
`is_error=True`

Server stdout protocol integrity:
**PASS**

Integration output:

`workspace/current/p8/mcp-stdio-summary-gated.json`

---

## 12. Security / Read-only Boundary

Verified:

- stdio only；
- no listener；
- no HTTP/SSE invocation；
- no arbitrary file path tool argument；
- catalog artifact paths are relative and contained；
- absolute/traversal artifact catalog path rejected；
- no read_file/list_directory/sqlite_query/execute_python/run_command/shell tool；
- no Registry mutation；
- no artifact mutation；
- no subprocess in business service；
- no network/AI imports in business service；
- no remote sampling；
- valid P7 REVIEW_REQUIRED returned as status；
- corrupted upstream artifact becomes `P8_UPSTREAM_ARTIFACT_INVALID` tool execution error rather than fabricated validation BLOCKED。

---

## 13. Final Gate Result

- P8-A Design Baseline: PASS
- P8-B Environment / SDK: PASS
- P8-C Catalog: PASS
- P8-D Query Service: PASS
- P8-E MCP Adapter: PASS
- P8-F Deterministic / Security Regression: PASS
- P8-G Live Catalog: PASS
- P8-H Official SDK Protocol Integration: PASS

Blocking findings:
**NONE**

Final development status:

# READY FOR P8 CODE REVIEW
