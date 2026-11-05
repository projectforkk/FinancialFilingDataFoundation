# 30 — FFDF Research Preflight Codex Skill 设计

## 状态

**DONE / ACCEPTANCE PASS**

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
