# 01 — Development Roadmap

状态：**PROJECT CLOSED / CN-HK SCOPE COMPLETE / P0-P10 DONE / PASS**

## 总原则

每个已执行 Phase 均遵循：

`DESIGN → DEVELOPMENT → CODE REVIEW → INDEPENDENT ACCEPTANCE → DONE`

发现问题并确定解决方案时：

`STOP → update design → commit design baseline → rerun affected gates → continue`

不得 code-first / design-later。

## Final scope

本项目最终生产范围严格限定为：

- `CN`
- `HK`

US SEC Provider 不再属于 FFDF 当前项目目标。历史 P11 设计授权与设计分支保留为审计记录，但 P11 production 不执行。

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

状态：`OUT_OF_SCOPE / NOT_REQUIRED_NOT_EXECUTED`

说明：

- `development/143-p11-design-authorization.md` 是历史设计授权；
- P11 production 从未进入 accepted main baseline；
- 最终 CN/HK scope decision supersedes 后续 P11 开发；
- 已存在的 P11 design/task branches 仅作为历史审计资料保留；
- 如未来需要 US 市场，应作为新的 scope reopening / 新项目阶段重新设计、review 与 acceptance，不能直接继承未验收 P11 candidate。

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
PROJECT CLOSEOUT — CN/HK
```
