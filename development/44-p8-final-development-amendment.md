# 44 — P8 Final Development Amendment Evidence

状态：**P8 DEVELOPMENT COMPLETE / FINAL CANDIDATE READY FOR CODE REVIEW**

Branch:
`task/p8-local-mcp`

Accepted baseline before P8:
`5f314bab9d88fb16b4b46c662e0a9f1b8f1a9b13`

Core production commit:
`9e026677eff177737202c43a5702ce2ec880573d`

Official SDK integration/performance assertion test commit:
`45a01ad385d88e28ca178ff0d55ef7e79f0fa507`

Design amendments:
- P8-ISSUE-001 runtime base: `382a08369182c5be49a5e706ce62d8121a730dcb`
- P8-ISSUE-002 lazy artifact trust: `4cdac4c4dda5f65806bcf2d31513e508d2a21e57`
- P8-ISSUE-003 first trusted-bundle performance calibration: `fdd13e0d0a9960d73698460f08ef047126b3362c`
- P8-ISSUE-004 short Windows pytest basetemp: `52db63e9407d415c06ab15b0be6517c594316507`
- P8 issue numbering correction: `dd3fb8a934ba2b9e0df8d2ad545e764c7aac118a`

Runtime/lock evidence:
`development/42-p8-environment-audit.md`

Earlier development evidence:
`development/43-p8-development-evidence.md`

---

## 1. Final P8 Scope

Implemented:
- project-root-relative MCP catalog
- path containment / identity uniqueness
- lazy trusted artifact bundles
- immutable per-process bundle cache
- exact 11 read-only tools
- local FTS/page/section/table/fact/evidence/validation queries
- deterministic input guards / pagination / payload limits
- official MCP SDK 2.3.0 stdio adapter
- structured tool errors
- no arbitrary filesystem/sql/shell/python tools
- no mutation
- no network
- no AI/sampling
- no P9/P10/P11 behavior

---

## 2. Final Runtime

Dedicated MCP runtime:

`D:\Codex\FinancialFilingDataFoundation\runtimes\ffdf-mcp-2.3.0\.venv`

Base:
- CPython 3.12.14 AMD64
- Windows ARM64 x64 emulation

Exact roots:
- mcp 2.3.0
- PyMuPDF 1.28.2

Tracked lock:

`runtime-locks/mcp-2.3.0-py312-win-amd64.lock.txt`

Main FFDF runtime remains MCP-free.

---

## 3. P8-ISSUE-004 — Windows Deep Temp Path

An invalid full-regression attempt used:

`...\worktrees\active\p8-local-mcp\workspace\pytest-p8-final-dev`

P4/P5/P6 atomic output tests then exceeded the practical Windows path length and raised `FileNotFoundError` before product assertions.

Diagnostic:
- same representative P4 test
- basetemp `D:\Codex\_ffdf_p8_pytest\diag`
- result: PASS

Design-first amendment:
- Windows P8 pytest uses short external basetemp under `D:\Codex\_ffdf_p8_pytest`
- no accepted P4/P5/P6 production naming logic was changed

The long-basetemp failure run is invalidated as environment-path evidence and is not used for P8 correctness.

---

## 4. Final Full Regression

Command:

```powershell
$env:PYTHONPATH="src"
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe \
  -m pytest tests\unit -q \
  --basetemp D:\Codex\_ffdf_p8_pytest\full-52db63e
```

Result:

```text
231 passed in 5.54s
```

- FAIL: 0
- ERROR: 0

This includes P0–P8 unit/regression coverage.

---

## 5. Canonical Live Catalog

Operational acceptance catalog:

`workspace/mcp/p8-acceptance-catalog.json`

SHA256:

`e493f2f6a951007c1e5ac932268796d35d33386760f4503d48ff0a7f7a148cdc`

Documents:

### CN
- market: CN
- ticker: 600519
- fiscal year: 2024
- filing type: ANNUAL
- SHA: `5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30`

### HK
- market: HK
- ticker: 00700
- fiscal year: 2024
- filing type: ANNUAL
- SHA: `70f529984a87ef7f46d9e1db26bb9ef27eef9c01d29c59aabf69e557b479a6a0`

All artifact paths are project-root-relative.

---

## 6. Final Official SDK Integration

Client/runtime:
- official `mcp==2.3.0`
- stdio child server
- source from current P8 branch

Negotiated protocol:

`2026-07-28`

Exact tool list:

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

Result:
**11 / 11 PASS**

Representative live calls:
- list CN/HK documents: PASS
- CN/HK get_document: PASS
- CN local FTS search: PASS
- read pages: PASS
- sections: PASS
- list/get table: PASS
- list/get fact: PASS
- evidence relation: PASS
- validation: PASS
- invalid document -> tool error: PASS

---

## 7. Final Performance

Final canonical catalog SDK run:

- cold connect: **1123.615 ms**
- CN first full trusted bundle: **9701.485 ms**
- HK first full trusted bundle: **15047.519 ms**

Gates:
- cold connect <=15000 ms: PASS
- first trusted bundle per document <=20000 ms: PASS

Warm calls:
- list_documents: 3.218 ms
- get_document: 2.959 ms
- search: 4.172 ms
- read_pages: 2.945 ms
- get_table: 4.164 ms
- get_fact + get_evidence: 5.557 ms
- validation: 3.266 ms

All warm tool gates: **PASS**

---

## 8. Live Artifact Immutability

Before/after snapshot covered:
- canonical P8 catalog
- CN P3/P5/P6/P7 artifacts
- HK P3/P5/P6/P7 artifacts

Snapshot fields:
- SHA256
- file size
- mtime_ns

File count:

`25`

Comparison:

`snapshot_equal=True`

Changed files:

`[]`

Result:

**PASS**

---

## 9. Static / Security

Verified:
- compileall PASS
- git diff --check PASS
- server import stdout chars = 0
- business service no network import
- business service no subprocess import
- no AI SDK import
- no Dayu/Docling/Torch import
- server source only starts stdio transport
- exact static tool names = 11
- no arbitrary path/file/sql/shell/python tool surface
- no Registry mutation tool
- no artifact mutation tool
- P9/P10/P11 absent

---

## 10. Gate Result

- P8-A Design Baseline: PASS
- P8-B Environment / SDK: PASS
- P8-C Catalog: PASS
- P8-D Query Service: PASS
- P8-E MCP Adapter: PASS
- P8-F Deterministic / Security Regression: PASS
- P8-G Live Catalog: PASS
- P8-H Official SDK Protocol Integration: PASS

Final development blocker:

**NONE**

Next:

**P8-I — isolated Code Review**
