# 30 — P5 Development Instruction

任务：**Table Reconstruction / Cross-page**

必须遵守：
- `design/12-p5-table-reconstruction-design.md`
- `design/13-p5-implementation-plan.md`

## Scope

只实现：
- P4 candidate-scoped word reconstruction
- visual rows
- structural LABEL / VALUE / UNASSIGNED cells
- numeric value anchors
- source word refs
- table fragment artifacts
- adjacent-page continuation groups
- deterministic artifact reuse / corruption guard

禁止：
- P6 raw facts
- account normalization
- period/currency/unit semantic binding
- OCR
- Docling
- Dayu
- network
- external AI

## Input

只允许读取已验证：
- P3 NativeDocumentArtifact
- P4 TableCandidateArtifact

P5 不重新打开 PDF。

## Runtime

FFDF main runtime：
`D:\Codex\FinancialFilingDataFoundation\.venv`

## Development evidence

必须记录：
- design baseline SHA
- production candidate SHA
- focused/full test result
- CN/HK live results
- continuation evidence
- determinism
- source/P3/P4 immutability
- no-P6/heavy-path assertion

发现问题且已有解决方案：
**先更新设计，再改代码。**
