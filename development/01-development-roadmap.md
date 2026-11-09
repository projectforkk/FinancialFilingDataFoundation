# 01 — Development Roadmap

状态：**P11 REOPENED / DESIGN READY / P0-P10 DONE PASS**

## 总原则

每个已执行 Phase 均遵循：

`DESIGN → DEVELOPMENT → CODE REVIEW → INDEPENDENT ACCEPTANCE → DONE`

发现问题并确定解决方案时：

`STOP → update design → commit design baseline → rerun affected gates → continue`

不得 code-first / design-later。

## Current scope

当前 accepted production 仍为：

- `CN`
- `HK`

2026-11-09 用户重新授权 P11 US SEC Provider。P11 进入全新的 design/development/review/acceptance lifecycle；2026-11-05 的 CN/HK closeout 保留为历史记录，不删除、不改写。

## P0 — Native PDF Parsing Feasibility Probe

状态：`DONE / PASS`

验证目标 PC 可使用轻量 native path 读取代表性 CN/HK born-digital PDF。

## P1 — Identity / Registry / Incremental Planner

状态：`DONE / PASS`

建立 FilingSlotKey / FilingIdentity、Registry、deterministic build_plan 与增量复用策略。

## P2 — Acquisition Provider

状态：`DONE / PASS`

建立 CN/HK Dayu narrow acquisition、独立 Dayu runtime、raw content-addressed store、receipt 与 Registry integration。

## P3 — Native Page / Section / FTS

状态：`DONE / PASS`

建立 deterministic physical page extraction、layout、sections 与 SQLite FTS5。

## P4 — Table Candidate Detection

状态：`DONE / PASS`

建立 table-like candidate detection。

## P5 — Table Reconstruction / Cross-page

状态：`DONE / PASS`

建立 rows/columns/cells reconstruction 与 cross-page continuity。

## P6 — Raw Facts / Evidence

状态：`DONE / PASS`

建立 raw facts 与 first-class evidence links。

## P7 — Quality Gate / Validation

状态：`DONE / PASS`

建立 deterministic validation、blocking issues、quality gates 与 reuse eligibility。

## P8 — Local MCP

状态：`DONE / PASS`

建立本地 deterministic read-only MCP tools；MCP AI API calls 禁止。

## P9 — Codex Review Overlay

状态：`DONE / PASS`

建立 evidence-grounded durable review overlay，不覆盖 RAW / LOCAL_EXTRACTED。

## P10 — Codex Dynamic Research Integration

状态：`DONE / PASS`

建立动态 research specification 消费模式，使用 accepted P8/P9 完成当前研究，不固化研究业务规则。

## P11 — US SEC Provider

状态：`REOPENED / DESIGN READY / DEVELOPMENT NEXT`

当前真源：

- `design/32-p11-us-scope-reopening.md`
- `design/26-p11-sec-provider-design.md`
- `design/27-p11-implementation-plan.md`
- `development/147-p11-us-scope-reopening-authorization.md`

原则：

- 从当前 accepted main 重新开发；
- 历史 P11 branch/probe 仅可作为参考证据，不能直接继承为 production candidate；
- 采用 SEC filing package + HTML/Inline XBRL first；
- P0-P10 CN/HK accepted behavior 必须保持回归兼容；
- US 只有在 independent acceptance PASS 后才进入 public supported markets。

## 最终执行顺序

```text
P0
↓
P1
↓
P2
↓
P3
↓
P4
↓
P5
↓
P6
↓
P7
↓
P8
↓
P9
↓
P10
↓
CN/HK accepted baseline
↓
P11 US SEC redesign/development/review/acceptance
```
