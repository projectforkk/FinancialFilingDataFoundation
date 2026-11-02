# 01 — Development Roadmap

状态：P1 DONE / P2 DESIGN AUTHORIZED

## 总原则

每个 Phase 独立：
DESIGN → IMPLEMENT → REVIEW → ACCEPTANCE。

不得一次性跨越多个未验收阶段。

## P0 — Native PDF Parsing Feasibility Probe

目标：
验证目标 PC 是否能以轻量 native path 快速读取代表性 CN/HK born-digital PDF。

实现范围：
- 环境审计；
- benchmark CLI / script；
- PDF open；
- SHA256；
- page count；
- text / words / blocks；
- bbox / drawings / images；
- cheap table-page candidate signals；
- per-stage timing；
- peak memory（若可可靠取得）；
- machine-readable result JSON。

明确不做：
- 完整 table reconstruction；
- OCR；
- Docling；
- MCP；
- Skill；
- CRDE；
- 投资分析。

首个样本：
600519 / 贵州茅台 FY2024，143 pages。

P0 性能 Gate：
- born-digital 代表样本 native probe > 120s → FAIL / investigate；
- 若明显低于 120s，继续根据实际结果收紧后续标准；
- 不允许用理论速度代替实测。

## P1 — Identity / Registry / Incremental Planner

建立：
- FilingIdentity
- DocumentRegistry
- ParsedDataRegistry
- build_plan
- REUSE_DATA / PARSE_LOCAL / DOWNLOAD_AND_PARSE

## P2 — Acquisition Provider

CN/HK Dayu narrow adapter。
必须证明不进入 Docling conversion。

## P3 — Native Page / Section

## P4 — Table Candidate Detection

## P5 — Table Reconstruction / Cross-page

## P6 — Raw Facts / Evidence

## P7 — Quality Gate / Validation

## P8 — Local MCP

## P9 — Codex Review Overlay

## P10 — Codex Skill

## P11 — US SEC Provider
