# 103 — R-C / R-D / R-E Review State, Resolved Query, Context, Controlled Write Evidence

## R-C Review State + Resolved Query

实现：

- ffdf_get_review_state
- ffdf_get_resolved_fact
- ffdf_list_resolved_facts

规则：

- read 不自动 materialize
- active resolution 无匹配 snapshot → NEEDS_MATERIALIZATION
- corrupt review state → INVALID_REVIEW_STATE / fail closed
- RawFact value 保持原样
- P9 只提供 accepted effective semantic fields

## R-D Review Tasks + Context

实现：

- ffdf_list_review_tasks
- ffdf_get_review_context

Context 汇总：

- P7 task
- RawFact
- P6 Evidence
- P5 table
- neighbor P3 pages
- active P9 resolutions
- recommended visual targets

structured evidence first，不能直接从 REVIEW_REQUIRED 跳到截图。

## R-E Controlled Write-Through

实现：

- ffdf_prepare_review_overlay
- ffdf_submit_review_resolution
- ffdf_materialize_resolved_view

RESEARCH_FALLBACK 默认拒绝写入，返回：
`RESEARCH_MCP_WRITE_DISABLED`

QUALITY_REVIEW submit 强制校验：

- expected base validation hash
- expected active overlay hash
- task 仍存在
- task SUPPORTED
- action 在 task.supported_actions 中
- 继续调用现有 P9 v1 API

没有新增 SET_VALUE。

## 验证

早期 focused：19 PASS。
R-L synthetic P9 reuse Golden 所在 review+mcp suite：81 PASS。

live 605117：
- 2025FY quality_state = NEEDS_REVIEW
- write_enabled = false
- 调用 prepare 在默认 profile 被明确阻断

R-C / R-D / R-E：PASS。
