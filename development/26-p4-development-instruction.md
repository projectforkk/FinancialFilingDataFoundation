# 26 — P4 Development Instruction

任务：**Table Candidate Detection**

必须遵守：
- design/10-p4-table-candidate-design.md
- design/11-p4-implementation-plan.md

只实现：
- P3 artifact → candidate region detection
- deterministic signals/score
- candidate artifact persistence/reuse

禁止：
- PDF reopen
- cells/rows/columns reconstruction
- cross-page stitching
- OCR/Docling/network/AI
- P5/P6 functionality

Runtime：
FFDF main .venv，Python 3.14.9 ARM64 / PyMuPDF 1.28.2。

开发完成必须记录：
- design baseline
- production commit
- tests
- CN/HK live evidence
- source immutability
- no-scope-change assertion。
