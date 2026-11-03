# 35 — P6 Development Instruction

任务：**Raw Facts / Evidence**

必须遵守：
- `design/00-design-management-index.md`
- `design/15-project-directory-management.md`
- `design/16-p6-raw-facts-evidence-design.md`
- `design/17-p6-implementation-plan.md`

## Scope

只实现：
- P5 structural table → raw facts
- Decimal numeric parsing
- raw period/unit/scope explicit-only extraction
- first-class evidence
- P3 source-word validation
- deterministic persistence/reuse/tamper guard

禁止：
- canonical metric
- accounting reconciliation
- P7 validation status / DATA_READY
- PDF reopen
- OCR / Docling / Dayu
- network / external AI
- MCP / Skill

## Runtime

`D:\Codex\FinancialFilingDataFoundation\.venv`

所有 workspace/worktree 必须位于 project root。

## Development Submission

必须记录：
- design baseline SHA
- branch
- production commit SHA
- changed files
- focused/full tests
- live CN/HK counts/timings
- dual-root hashes
- input immutability
- known limitations
- no-scope-change statement

发现问题：
**先更新设计书，再改代码。**
