# Project Status

## Repository

`projectforkk/FinancialFilingDataFoundation`

## Current state

**DESIGN_BASELINE_IN_PREPARATION**

## Current scope

- 多年份财报数据源构建。
- 增量判定：已有数据 → 本地文件 → 下载 → 解析。
- CN/HK：PDF extraction。
- US：预留 SEC HTML / Inline XBRL / XBRL provider。
- Local MCP：0 AI API。
- Codex：只处理本机解析无法可靠完成的局部复核。
- CRDE / 财报分析：下游，不属于首期 Extraction 实现范围。

## Current design baseline facts

已确认的 Dayu 参考基线：`2115c86d5a9027bb51cbbc8a4d0175080732e4e6`。

CN/HK Dayu 当前公开 `fins download` 工作流会在 PDF 下载后继续执行 Docling conversion；本项目若复用 Dayu，应复用 acquisition/downloader 能力，而不是强制沿用 Docling parsing。

贵州茅台 FY2024 代表样本：
- 143 pages；
- 143/143 有 native text；
- Dayu PDF → Docling JSON 约 1802.6s；
- Docling JSON → snapshot 约 31.6s；
- 因此本项目首要风险是 native PDF parser 的性能与准确性，而非 MCP transport。

## Next development gate

**P0 — Native PDF Parsing Feasibility Probe**

在任何完整 MCP / Skill 实现前，先验证目标 PC 对代表性 CN/HK born-digital PDF 的：
- PDF open；
- text / words / blocks；
- bbox / drawings / images；
- cheap table candidate detection；
- 耗时、内存、异常页比例。
