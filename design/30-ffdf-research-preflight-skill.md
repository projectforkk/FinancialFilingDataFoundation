# 30 — FFDF Research Preflight Codex Skill 设计

## 状态

**OPTIMIZATION V2 DONE / ACCEPTANCE PASS**

用户已明确授权：
- 将 Research Preflight 编排制作成 Codex Skill；
- Skill 参数固定为：公司、年度区间、使用模型；
- Skill 生成后纳入 Git 管理；
- 当前唯一允许的模型为 Luna 5.6 Max。

## 目标

新增一个项目级 Codex Skill：

`FFDF财报数据完善`

用于在正式公司财报研究前，编排 FFDF MCP 完成研究期间全量状态监测，并只把真正需要模型判断的疑难项交给 Luna 5.6 Max。

本 Skill 不替代 FFDF parser、P8、P9 或正式研究报告 Skill。

## 输入参数

### company

必填。

接受：
- 股票代码 / ticker；
- 公司名称。

Skill 不自行猜测多个候选；无法唯一解析时停止。

### year_range

必填。

格式：

`YYYY-YYYY`

含首尾年度，例如：

`2021-2026`

必须满足：
- 起始年 <= 结束年；
- 不得自动扩大研究期间。

### model

必填。

当前唯一合法 canonical value：

`luna5.6-max`

不允许：
- 自动 fallback；
- 改用其他 Luna；
- Sol / Astra / 其他 Codex 模型；
- 外部 OpenAI API / 其他 AI API。

模型不可用时，只停止需要模型判断的步骤；确定性 MCP 查询仍可完成并输出阻断原因。

## 调用形式

推荐：

`$FFDF财报数据完善 <company> <year_range> <model>`

例如：

`$FFDF财报数据完善 605117 2021-2026 luna5.6-max`

`$FFDF财报数据完善 德业股份 2021-2026 luna5.6-max`

## 执行流程

1. 参数校验；
2. Filing Coverage Scan；
3. Document Quality Scan；
4. Research Data Coverage Scan；
5. Build Research Repair Queue；
6. 对 research-relevant QUALITY_REVIEW 项获取 Review Context；
7. 结构化证据不足时才调用 Luna 5.6 Max；
8. Luna 判断仍需版式证据时才调用 PDF Visual；
9. 合法语义问题进入 P9；Raw extraction / missing fact 路由 upstream fix；
10. 修复后重跑 Preflight；
11. 输出 `RESEARCH PREFLIGHT: PASS/FAIL` 与 readiness 摘要。

## 职责边界

Codex：
- 总调度；
- 直接调用 FFDF MCP；
- 管理 Repair Queue；
- 调用 Luna 5.6 Max；
- 检查 P9 合法性。

FFDF MCP：
- 数据 / deterministic tools；
- 不调用远端模型；
- 不接受 arbitrary filesystem path / arbitrary bbox。

Luna 5.6 Max：
- 只处理语义或视觉疑难点；
- 不承担全量财报扫描。

P9：
- 只持久化 P9 v1 合法语义修正；
- 不允许 SET_VALUE / PATCH_FACT / 创建不存在 RawFact。

## 输出合同

至少输出：
- company；
- year_range；
- model；
- observed filing count；
- latest filing；
- COMPLETE_BASE / COMPLETE_REVIEWED / NEEDS_REVIEW / NEEDS_UPSTREAM_FIX / BLOCKED 统计；
- critical requirement coverage；
- Repair Queue；
- visual call count；
- period_monitoring_complete；
- research_ready；
- database_fully_reviewed；
- blockers / warnings / data gaps；
- 最终 PASS / FAIL。

## Git / 版本边界

Skill 文件位于：

`.agents/skills/FFDF财报数据完善/`

至少包含：
- `SKILL.md`
- `agents/openai.yaml`

并新增静态测试锁定：
- Skill 名称；
- 三参数合同；
- model 唯一允许值；
- Luna 5.6 Max fail-closed；
- Preflight / Review Context / Visual / P9 路由关键规则。

所有变更通过独立 Git 分支提交，不提交现有未跟踪 `00document/`、`01prompt/`。


## Optimization v2 — 已完善财报默认跳过 / 显式重新完善

用户确认最终语义：

> 已经完善的财报不需要重新完善，除非指定“重新完善”。

### 必填参数保持不变

仍然只有三个必填参数：

1. company
2. year_range
3. model

调用：

`$FFDF财报数据完善 <company> <year_range> <model>`

允许追加一个可选控制词：

`重新完善`

例如：

`$FFDF财报数据完善 605117 2021-2026 luna5.6-max 重新完善`

`重新完善` 不是第四个必填参数，只是显式 bypass-skip 控制词。

### 默认 skip-first 规则

对 research period 内每份 observed filing，先调用：

`ffdf_get_review_state`

如果状态为：

- `COMPLETE_BASE`
- `COMPLETE_REVIEWED`

则默认标记：

`SKIPPED_ALREADY_COMPLETE`

并跳过该财报后续的：

- Review Context 获取；
- Luna 5.6 Max 语义判断；
- PDF Visual；
- P9 write-through；
- materialize。

这两种状态都视为“已经完善，不需要重复完善”。

### 重新完善

只有用户明确指定 `重新完善` 时，才绕过 `SKIPPED_ALREADY_COMPLETE`。

重新完善的含义是：

- 重新执行本次 Research Preflight / Research Data Coverage；
- 对目标财报重新读取当前 Review State；
- 对当前仍存在且 research-relevant 的 Review Task 重新判断；
- 必要时才调用 Luna 5.6 Max；
- 必要时才调用 PDF Visual；
- 只有满足现有 P9 v1 合法条件时才允许新 resolution/materialization。

重新完善不表示：

- 修改 Raw Fact；
- 创建不存在的 Review Task；
- 创建不存在的 RawFact；
- 把 COMPLETE_BASE 强行改成 P9 reviewed；
- 删除已有 P9 resolution；
- 破坏性重建 review overlay；
- 为了“重新完善”而重复截图或重复写入没有变化的结论。

如果重新完善后没有新的合法 Review Task，保持原状态并报告：

`REIMPROVE_NO_ACTION_REQUIRED`

### 异常状态

以下状态永远不能因为“以前完善过”而静默跳过：

- `NEEDS_REVIEW`
- `NEEDS_MATERIALIZATION`
- `NEEDS_UPSTREAM_FIX`
- `BLOCKED`
- `INVALID_REVIEW_STATE`

必须按照既有 Research Repair Queue 路由处理。

### 输出变化

新增：

- `reimprove_requested: true|false`
- `skipped_already_complete_count`
- per-document `SKIPPED_ALREADY_COMPLETE`
- 必要时 `REIMPROVE_NO_ACTION_REQUIRED`

`SKIPPED_ALREADY_COMPLETE` 计入可直接研究的成功文档，不影响 `research_ready=true`。

### 安全边界

skip-first 只减少重复完善工作，不改变：

- P8 Raw Contract；
- P9 v1；
- Research Review MCP；
- Luna 5.6 Max-only 模型约束；
- parser/extraction upstream-fix 路由；
- Raw/P3/P5/P6/P7 immutability。
