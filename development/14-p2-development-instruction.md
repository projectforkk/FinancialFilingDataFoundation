# 14 — P2 Development Instruction

任务：**CN/HK Acquisition Provider**

设计基线：

- `design/01-project-detailed-design.md`
- `design/02-incremental-and-acquisition-design.md`
- `design/08-p2-acquisition-provider-design.md`
- `design/09-p2-implementation-plan.md`
- `development/01-development-roadmap.md`

执行必须严格遵守 P2-A → P2-S Gate。

---

## 1. Scope

只实现：

- CN/HK acquisition domain models；
- AcquisitionProvider contract；
- pinned Dayu dependency/runtime descriptor；
- subprocess JSON protocol（`shell=False` + explicit safe cwd）；
- Dayu narrow runner；
- FFDF Dayu adapter；
- raw document store；
- acquisition receipt；
- acquisition service；
- P1 Registry integration；
- deterministic tests；
- controlled CN/HK live smoke。

禁止：

- US SEC provider；
- Docling conversion；
- Dayu high-level workflow；
- PDF parsing；
- tables/facts/evidence；
- MCP/Skill；
- external AI API。

---

## 2. Runtime Boundary

### FFDF main runtime

`D:\Codex\FinancialFilingDataFoundation\.venv`

必须保持：

- no Dayu
- no Docling
- no Torch

### Dayu acquisition runtime

单独创建。

不得把 Dayu 安装到 FFDF main venv。

不得把其它项目 venv 作为正式 FFDF runtime。

---

## 3. Upstream Pin

Dayu：

- repository: `noho/dayu-agent`
- commit: `2115c86d5a9027bb51cbbc8a4d0175080732e4e6`

任何 pin 变化先更新设计。

---

## 4. Development Order

必须：

1. environment/source audit；
2. checkout；
3. dedicated runtime；
4. doctor；
5. models/protocol/raw store；
6. runner；
7. adapter；
8. service/registry；
9. mocked integration；
10. deterministic regression；
11. live sample freeze；
12. live CN/HK；
13. incremental rerun；
14. isolated Code Review；
15. acceptance freeze。

禁止跳过 doctor 直接写 live integration。

---

## 5. Dependency Checkout Safety

若 Dayu checkout 已存在：

- 先 read-only inspect；
- HEAD mismatch / dirty → STOP；
- 不 reset；
- 不 clean；
- 不 overwrite。

如需修改 upstream：

先更新设计并建立受控 fork/new commit。

---

## 6. Development Submission

必须记录：

- design baseline SHA；
- branch；
- production commit SHA；
- Dayu source commit；
- Dayu runtime descriptor；
- changed files；
- deterministic tests；
- live evidence；
- exact commands/results；
- known limitations；
- no-scope-change statement；
- no-Docling-conversion assertion。

发现问题并确定方案：

**先更新设计，再继续。**
