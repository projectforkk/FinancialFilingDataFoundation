# 22 — P3 Development Instruction

任务：Native Page / Section / FTS

Design:
- design/10-p3-native-page-section-design.md
- design/11-p3-implementation-plan.md
- design/03-parsed-financial-document-contract.md

Only implement P3 native page/section/FTS.

Forbidden:
- P4 table candidate logic
- table reconstruction
- OCR/Docling
- facts/evidence
- MCP/Skill
- remote AI

Runtime: existing FFDF ARM64 .venv / PyMuPDF / sqlite3.

Development order:
models/IO → extraction → sections → FTS → unit → full regression → live CN/HK → review.

Any discovered design issue must be committed to design before code fix.
