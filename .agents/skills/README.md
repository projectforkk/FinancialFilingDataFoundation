# Codex Skills

本目录预留后续 Codex Skill。

当前阶段不得先实现“全自动研究 Skill”；应先证明底层 PDF extraction 的性能、正确性、Evidence 与增量复用。

目标 Skill 后续只负责编排：
- build plan；
- acquisition；
- parse；
- review queue；
- Codex difficult-page review；
- resolution；
- validation / export。

Skill 不替代 deterministic parser。


## FFDF财报数据完善

正式公司研究前的 Research Preflight 编排 Skill。

调用：

`$FFDF财报数据完善 <company> <YYYY-YYYY> <model>`

当前唯一允许的 model：

`luna5.6-max`

Skill 直接编排 FFDF MCP 做全期间结构化监测，只在必要时调用 Luna 5.6 Max，并遵守 P9 / upstream-fix 边界。


## FFDF公司财报下载

按公司代码和年度/年度区间批量下载并解析正式财报。

调用：

`$FFDF公司财报下载 <company_code> <year_or_range>`

示例：

`$FFDF公司财报下载 605117 2021-2026`

Skill 自动识别 CN/HK，逐年逐期先用 `ffdf status` 跳过已入库财报；只有未入库 slot 才调用 `ffdf ingest`。如明确追加 `重新读入`，则对 requested slots 重新执行标准 ingest。
