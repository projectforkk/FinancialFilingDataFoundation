# 01 — Development Roadmap

状态：**P10 DONE / P11 DESIGN REVIEW STOPPED**

## 总原则

每个 Phase 独立执行：

`DESIGN → DEVELOPMENT → CODE REVIEW → INDEPENDENT ACCEPTANCE → DONE`

不得跨越未验收阶段。

发现问题并确定解决方案时：

`STOP → update design → commit design baseline → rerun affected gates → continue`

不得 code-first / design-later。

## P0 — Native PDF Parsing Feasibility Probe

状态：`DONE / PASS`

目标：
验证目标 PC 是否能以轻量 native path 快速读取代表性 CN/HK born-digital PDF。

## P1 — Identity / Registry / Incremental Planner

状态：`DONE / PASS`

建立：
- FilingSlotKey / FilingIdentity
- Document Registry
- Parsed Data Registry
- deterministic build_plan
- REUSE_DATA / PARSE_LOCAL / DOWNLOAD_AND_PARSE

## P2 — Acquisition Provider

状态：`DONE / PASS`

建立：
- CN/HK Dayu narrow acquisition
- dedicated Dayu runtime
- raw content-addressed store
- acquisition receipt
- P1 Registry integration
- no Docling conversion

US SEC 不在 P2，保留给 P11。

## P3 — Native Page / Section / FTS

状态：`DONE / PASS`

建立：
- deterministic physical page extraction
- words / blocks / spans / bbox
- section detection
- repeated header/footer marking
- pages.jsonl / sections.jsonl
- SQLite FTS5 page/section search
- artifact corruption guard

## P4 — Table Candidate Detection

状态：`DONE / PASS`

目标：
基于 P3 artifact 检测 table-like page/region candidate。

禁止：
- cell/row/column reconstruction
- cross-page table stitching
- OCR/Docling/AI

## P5 — Table Reconstruction / Cross-page

状态：`DONE / PASS`

目标：
从 P4 candidates 重建 rows/columns/cells，并处理跨页表格连续性。

## P6 — Raw Facts / Evidence

状态：`DONE / PASS`

目标：
从 reconstructed tables 生成 raw facts 与 first-class evidence links。

## P7 — Quality Gate / Validation

状态：`DONE / PASS`

目标：
deterministic validation、blocking issues、quality gates、reuse eligibility。

## P8 — Local MCP

状态：`DONE / PASS`

目标：
本地 deterministic MCP tools，只暴露已验证的数据能力；MCP AI API calls 继续禁止。

## P9 — Codex Review Overlay

状态：`DONE / PASS`

目标：
evidence-grounded durable review overlay，不覆盖 RAW/LOCAL_EXTRACTED。

## P10 — Codex Dynamic Research Integration

状态：`DONE / PASS`

目标：
让 Codex 每次读取当前 runtime research specification，动态使用 accepted P8/P9 完成当前研究；P10 不实现固定 Skill，不复制研究业务规则。

## P11 — US SEC Provider

状态：`P11-A PASS / P11-B PASS / P11-C AUTHORIZED IMPLEMENTATION / PRODUCTION NOT STARTED`

Latest reviewed design candidate：
- historical exact candidate = `cd2fa0b01d23c0e3f75945c5cce5120738f51077` = INELIGIBLE after P11-ISSUE-039；
- authoritative stop = `development/200-p11-phase-banner-review-stop.md`；
- ISSUE-038 amendment evidence = `development/198-p11-governance-status-amendment-evidence.md` = PASS and remains valid；
- ISSUE-039 amendment evidence = `development/201-p11-phase-banner-amendment-evidence.md` = PASS；
- accepted P11-A design baseline = `5877a238f5af6102ef48e56141cdb893590b6aab`；
- formal review result = `development/203-p11-final-detached-design-review-result.md` = PASS；
- `design/26-p11-sec-provider-design.md`；
- `design/27-p11-implementation-plan.md`；
- `design/30-parsed-financial-document-v2-contract.md`；
- `acceptance/41-p11-acceptance-instruction.md`；
- `development/144-p11-environment-interface-audit.md`；
- `development/145-p11-design-reconciliation.md`。

P11-B Environment / SEC Runtime Probe = CLOSED / PASS (`development/205-p11-environment-runtime-probe.md`). P11-C Identity / Period Contract is authorized by `development/206-p11-c-identity-period-authorization.md`. Next action: implement only the authorized P11-C scope. P11 provider production remains CLOSED.

目标：
SEC HTML / iXBRL / XBRL first acquisition and extraction path。

## 当前执行顺序

```text
P4 Table Candidate Detection
↓
P5 Table Reconstruction / Cross-page
↓
P6 Raw Facts / Evidence
↓
P7 Quality Gate / Validation
↓
P8 Local MCP
↓
P9 Codex Review Overlay
↓
P10 Codex Dynamic Research Integration
↓
P11 US SEC Provider
```
