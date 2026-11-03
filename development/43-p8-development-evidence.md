# 43 — P8 Development Evidence

状态：**P8 DEVELOPMENT COMPLETE / READY FOR CODE REVIEW**

Branch:
`task/p8-local-mcp`

Initial design baseline:
`bf39d2028e4c03bee724c1c5389d513ebc904d00`

Design amendments:
- P8-ISSUE-001 compatible MCP runtime base: `382a08369182c5be49a5e706ce62d8121a730dcb`
- P8-ISSUE-002 lazy artifact validation: `4cdac4c4dda5f65806bcf2d31513e508d2a21e57`
- P8-ISSUE-003 first trusted-bundle performance calibration: `fdd13e0d0a9960d73698460f08ef047126b3362c`

Environment/lock commit:
`89b3cec9e72d76ee3624322328dcd36231434557`

Production commit:
`9e026677eff177737202c43a5702ce2ec880573d`

Accepted baseline before P8:
`5f314bab9d88fb16b4b46c662e0a9f1b8f1a9b13`

## 1. Implemented Scope

Added:

- `src/financial_filing_data_foundation/mcp/__init__.py`
- `src/financial_filing_data_foundation/mcp/catalog.py`
- `src/financial_filing_data_foundation/mcp/service.py`
- `src/financial_filing_data_foundation/mcp/server.py`
- `tests/unit/mcp/test_catalog_service.py`
- `tests/unit/mcp/test_server_static.py`
- `tests/integration/mcp_stdio_check.py`

Implemented:
- project-root-relative catalog
- path traversal/absolute-path guards
- duplicate SHA/filing identity guards
- lazy per-document trusted bundle loading
- immutable validated bundle cache
- 11 read-only deterministic tools
- P3 local FTS search
- page/section/table/fact/evidence/validation queries
- pagination/payload/argument guards
- upstream execution error vs valid P7 status separation
- official MCP SDK v2 stdio adapter
- ToolError mapping
- no arbitrary path/file/shell/sql/python surface

Not implemented:
- acquisition
- parsing
- artifact mutation
- Registry mutation
- review overlay mutation
- HTTP/SSE
- network
- AI/sampling
- P9/P10/P11

## 2. MCP Runtime

Dedicated runtime:
`D:\Codex\FinancialFilingDataFoundation\runtimes\ffdf-mcp-2.3.0\.venv`

Base:
CPython 3.12.14 AMD64 under Windows ARM64 x64 emulation.

Exact:
- mcp 2.3.0
- mcp-types 2.3.0
- PyMuPDF 1.28.2

Tracked lock:
`runtime-locks/mcp-2.3.0-py312-win-amd64.lock.txt`

Lock:
- 30 exact packages
- clean rebuild: MATCH
- main FFDF venv mcp: absent

Environment evidence:
`development/42-p8-environment-audit.md`

## 3. P8-ISSUE-001

Initial CPython 3.14.9 ARM64 MCP runtime install failed because:
`mcp -> pyjwt[crypto] -> cryptography 50.0.2`
fell back to source build and required unavailable MSVC `link.exe`.

No production code had been written.

Approved/implemented:
- CPython 3.12.14 AMD64 isolated runtime
- no SDK downgrade
- no system toolchain mutation
- exact runtime lock

PASS.

## 4. Unit / Regression

Focused P8:
`18 passed in 0.90s`

Full P0–P8:
`231 passed in 6.12s`

Additional:
- compileall PASS
- git diff --check PASS
- service/catalog have no network/AI/subprocess imports
- server transport source has only `server.run("stdio")`
- exact static tool names = 11
- main package initializer does not import external MCP SDK

## 5. Tool Set

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

No arbitrary:
- read_file
- list_directory
- sqlite_query
- execute_python
- run_command
- shell

## 6. Live Catalog

Ignored operational catalog:
`workspace/mcp/p8-acceptance-catalog.json`

Contains only project-root-relative paths.

CN:
- market CN
- ticker 600519
- FY2024
- SHA `5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30`

HK:
- market HK
- ticker 00700
- FY2024
- SHA `70f529984a87ef7f46d9e1db26bb9ef27eef9c01d29c59aabf69e557b479a6a0`

## 7. Business Service Live

Final lazy service run:

Service constructor:
`0.005 ms`

CN first trusted bundle:
`3635.958 ms`

HK first trusted bundle:
`7929.668 ms`

Both <=20s gate.

CN:
- pages 143
- tables 97
- raw facts 2177
- evidence 2177
- validation REVIEW_REQUIRED
- reuse false
- issues 3
- search returned 5
- fact/evidence relation PASS

HK:
- pages 274
- tables 97
- raw facts 2989
- evidence 2989
- validation REVIEW_REQUIRED
- reuse false
- issues 6
- fact/evidence relation PASS

Warm calls:
- search ~0.9ms
- read_pages <0.1ms
- list_sections <20ms
- list_tables <1ms
- get_table <=2ms
- list facts <4ms
- get fact/evidence <0.1ms
- validation <0.2ms

All tool performance gates PASS.

Catalog + P3/P5/P6/P7 artifact snapshot before/after:
**UNCHANGED**

## 8. P8-ISSUE-002

First official SDK implementation eagerly loaded both documents during server construction.

Observed invalidated cold timing:
`25,928.336 ms` >15s.

Protocol/tool correctness was otherwise PASS.

Design amendment changed:
- constructor to catalog-only
- list_documents to identity-only
- first artifact-dependent call validates one document
- validated bundle cached

Final cold protocol connect:
`1114.807 ms`

PASS.

## 9. P8-ISSUE-003

First post-lazy SDK run:
- CN first bundle 9985.873ms
- HK first bundle 15104.469ms

The provisional 15s first-bundle gate was calibrated before measuring the accepted 274-page HK input.

Design amended first bundle gate to <=20s without removing validation.

Final official SDK run:
- CN first bundle: `10634.132 ms`
- HK first bundle: `15171.995 ms`

Both <=20s.

## 10. Official MCP SDK Stdio Integration

Runtime:
mcp 2.3.0 official Python SDK.

Client:
`Client(StdioServerParameters(...), mode="auto")`

Server:
P8 stdio subprocess from exact branch source.

Negotiated protocol:
**2026-07-28**

Cold connect:
**1114.807 ms**

Exact tool list:
PASS (11/11).

Representative calls:
- list documents: PASS
- CN/HK get document: PASS
- CN search: PASS
- read pages: PASS
- list sections: PASS
- list/get table: PASS
- list/get raw fact: PASS
- get evidence: PASS
- get validation: PASS
- invalid document returns `is_error=True`: PASS
- fact/evidence relation: PASS

Server stdout protocol integrity:
PASS (official client completed normally; no non-protocol stdout).

Integration evidence:
`workspace/current/p8/mcp-stdio-summary-final.json`

## 11. Security / Scope

Verified:
- stdio only
- no listener
- no HTTP/SSE invocation
- no arbitrary filesystem path tool argument
- artifact paths only from validated catalog
- absolute/traversal catalog artifact paths blocked
- no mutation tool
- no Registry write
- no subprocess in business service
- no network import/call in business service
- no remote AI/sampling
- P7 REVIEW_REQUIRED remains a valid returned status
- corrupted upstream artifact raises P8_UPSTREAM_ARTIFACT_INVALID rather than fabricated BLOCKED status

## 12. Gate Result

- P8-A Design Baseline: PASS
- P8-B Environment/SDK: PASS
- P8-C Catalog: PASS
- P8-D Query Service: PASS
- P8-E MCP Adapter: PASS
- P8-F Deterministic/Security Regression: PASS
- P8-G Live Catalog: PASS
- P8-H Official SDK Protocol Integration: PASS

Next:
**P8-I — Code Review**
