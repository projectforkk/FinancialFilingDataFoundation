# 01 — Development Roadmap

状态：**P4 DONE / P5 DESIGN AUTHORIZED**

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

状态：`NOT STARTED`

目标：
从 P4 candidates 重建 rows/columns/cells，并处理跨页表格连续性。

## P6 — Raw Facts / Evidence

状态：`NOT STARTED`

目标：
从 reconstructed tables 生成 raw facts 与 first-class evidence links。

## P7 — Quality Gate / Validation

状态：`NOT STARTED`

目标：
deterministic validation、blocking issues、quality gates、reuse eligibility。

## P8 — Local MCP

状态：`NOT STARTED`

目标：
本地 deterministic MCP tools，只暴露已验证的数据能力；MCP AI API calls 继续禁止。

## P9 — Codex Review Overlay

状态：`NOT STARTED`

目标：
仅对 ambiguous local structured data 启用 Codex text review，输出 REVIEW_OVERLAY，不覆盖 RAW/LOCAL_EXTRACTED。

## P10 — Codex Skill

状态：`NOT STARTED`

目标：
把已验收 local data + review workflow 封装为 Codex Skill。

## P11 — US SEC Provider

状态：`NOT STARTED`

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
P10 Codex Skill
↓
P11 US SEC Provider
```
