# Project Status

## Repository

`projectforkk/FinancialFilingDataFoundation`

## Current state

**P0_IN_DEVELOPMENT**

## Approved phase

**P0 — Native PDF Parsing Feasibility Probe**

正式开发分支：

`task/p0-native-pdf-feasibility`

## Design baseline

当前设计基线由以下文件共同组成：

- `AGENTS.md`
- `design/01-project-detailed-design.md`
- `design/02-incremental-and-acquisition-design.md`
- `design/03-parsed-financial-document-contract.md`
- `design/04-pdf-quality-gate-design.md`
- `design/05-p0-implementation-plan.md`
- `development/01-development-roadmap.md`
- `development/02-p0-development-instruction.md`
- `acceptance/01-acceptance-strategy.md`
- `acceptance/02-p0-acceptance-instruction.md`

设计准备完成时 main head：

`fe97cdd2abda5c956c2b508630ad05779f305901`

本文件更新后，以更新后的 main head 作为 P0 分支起点。

## Current scope

- 多年份财报数据源构建。
- 增量判定：已有数据 → 本地文件 → 下载 → 解析。
- CN/HK：PDF extraction。
- US：预留 SEC HTML / Inline XBRL / XBRL provider。
- Local MCP：0 AI API。
- Codex：只处理本机解析无法可靠完成的局部复核。
- CRDE / 财报分析：下游，不属于首期 Extraction 实现范围。

## Verified Dayu reference baseline

Dayu 参考基线：

`2115c86d5a9027bb51cbbc8a4d0175080732e4e6`

已核对：
- CN/HK 高层 `fins download` 会在 PDF acquisition 后继续 Docling conversion；
- FFDF 若复用 Dayu，应复用 acquisition/downloader 的窄能力，不以 Docling 为默认 parser。

## Representative performance evidence

贵州茅台 FY2024：
- 143 pages；
- 143/143 有 native text；
- PDF → Docling JSON 约 1802.6s；
- Docling JSON → snapshot 约 31.6s。

因此 P0 首先验证：目标 PC 上轻量 native PDF path 的真实性能与可读取性。

## P0 exit condition

只有 P0 独立验收 PASS 后，才允许进入 P1 Identity / Registry / Incremental Planner。

P0 不允许提前实现：
- 完整 table reconstruction；
- MCP；
- Skill；
- OCR；
- Docling parser path；
- external AI API。
