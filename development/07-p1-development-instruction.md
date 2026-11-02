# 07 — P1 Development Instruction

任务：Identity / Registry / Incremental Planner

设计基线：
- `design/01-project-detailed-design.md`
- `design/02-incremental-and-acquisition-design.md`
- `design/06-p1-identity-registry-planner-design.md`
- `design/07-p1-implementation-plan.md`
- `development/01-development-roadmap.md`

执行必须严格遵守 P1-A → P1-K Gate。

## 开发边界

只实现：
- identity models
- SQLite registry
- document registration
- parsed-data registry/reuse policy
- deterministic incremental planner
- P1 tests

禁止：
- P2 acquisition
- Dayu import/call
- network
- Docling/Torch/OCR/AI
- parser execution
- table extraction
- MCP/Skill

## Runtime

复用项目 `.venv`：
- Python 3.14.9 ARM64
- PyMuPDF 1.28.2
- pytest 9.2.0
- stdlib sqlite3

P1 不新增第三方 runtime dependency，除非先更新设计。

## 开发提交要求

必须记录：
- design baseline SHA
- branch
- production commit
- changed files
- exact test commands/results
- known limitations
- no-scope-change statement

发现问题并找到方案时：先更新设计、提交新 baseline，再继续代码。
