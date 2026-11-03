# 38 — P7 Development Instruction

任务：**Quality Gate / Validation**

必须遵守：
- `design/00-design-management-index.md`
- `design/15-project-directory-management.md`
- `design/18-p7-quality-validation-design.md`
- `design/19-p7-implementation-plan.md`

## Scope

只实现：
- deterministic validation
- ValidationIssue
- structural/evidence coverage
- raw semantic coverage
- context-safe accounting reconciliation
- validation status
- compatibility status
- reuse eligibility
- ParsedDataRecord builder
- persistence/reuse/tamper guard

禁止：
- 修改 P6 facts/evidence
- canonical metric export
- review overlay
- Codex/remote AI
- MCP
- Skill
- SEC
- OCR/Docling
- PDF reopen

## Runtime

`D:\Codex\FinancialFilingDataFoundation\.venv`

## Worktree

`D:\Codex\FinancialFilingDataFoundation\worktrees\active\p7-quality-validation`

## Development Evidence

必须记录：
- design baseline SHA
- design amendments
- production SHA
- focused/full tests
- live CN/HK status/issues/metrics
- reconciliation outcomes
- planner reuse integration
- upstream immutability
- no-scope-change

发现问题：
**先更新设计书，再改代码。**
