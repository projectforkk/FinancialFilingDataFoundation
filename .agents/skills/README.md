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


## ffdf-research-preflight

正式公司研究前的 Research Preflight 编排 Skill。

调用：

`$ffdf-research-preflight <company> <YYYY-YYYY> <model>`

当前唯一允许的 model：

`luna5.6-max`

Skill 直接编排 FFDF MCP 做全期间结构化监测，只在必要时调用 Luna 5.6 Max，并遵守 P9 / upstream-fix 边界。
