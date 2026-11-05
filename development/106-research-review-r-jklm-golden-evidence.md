# 106 — R-J / R-K / R-L / R-M Golden & Security Evidence

## R-J — 002371 2026Q3

来源：
`workspace/ad-hoc/002371-2026q3-20261104`

SHA：
`a0f8d84ab724f7c62b690d6504215602a623fc185c53c9e1079cd40653c600b9`

已验收 artifact：
- page_count 10
- table_count 10
- RawFact 315
- Evidence 315
- blocking 0
- compatibility COMPATIBLE

第一页营业收入行实际结构化值：

- column 1: 11,305,675,488.89
- column 2: 1.31%
- column 3: 31,467,092,379.45
- column 4: 15.26%

当前 P5 四个 numeric cells 均只是 VALUE role，单靠结构化 role 不能唯一证明：
- 本报告期 VALUE
- 本报告期 YOY_PERCENT
- 年初至报告期末 VALUE
- 年初至报告期末 YOY_PERCENT

因此该案例正确路由为：
`MISSING_LAYOUT_CONTEXT → VISUAL_REQUIRED`
而不是猜测或改 raw value。

## R-K — 605117 Report-Safe + Preflight Integration

live catalog 2021–2026：
23 份正式 periodic filings。

2025FY `新能源行业` direct row：
- Revenue 10,180,522,048.26
- Cost 5,942,388,719.41
- GM 41.63
- disclosure label 保持“新能源行业”

KAM locator：
page 105 + 106。

Visual:
真实 MCP ImageContent 返回成功。

Report-Safe company context 已改用 manifest-level summary，避免 23 份财报逐份完整载入导致 60s timeout；语义不变。

## R-L — Existing P9 Reuse Golden

新增真实 P9 synthetic integration：

- SET_PERIOD
- SET_UNIT
- materialize
- resolved_validation_status PASS
- resolved_reuse_eligible true
- ResearchReviewService quality_state = COMPLETE_REVIEWED
- get_resolved_fact 使用 durable effective period/unit
- RawFact period/unit 原值仍为 null
- 无 Renderer 依赖

review + research-review Golden：81 PASS。

## R-M — CN/HK / Security / Corruption

26-tool stdio acceptance：
- protocol 2026-07-28
- CN legacy checks PASS
- HK legacy checks PASS
- invalid document error PASS
- 原 P8/Report-Safe 行为未破坏

Security：
- arbitrary path 不开放
- source SHA drift fail closed
- default research write disabled
- P9 corrupt state fail closed
- VisualRef/dedupe deterministic
- Windows long test path failure已确认是环境长度问题；使用项目既定短 basetemp `.t\r` 后通过

综合核心回归：
`tests/unit/mcp + tests/unit/research + tests/unit/review`
283 PASS / 0 FAIL。

R-J / R-K / R-L / R-M：PASS。
