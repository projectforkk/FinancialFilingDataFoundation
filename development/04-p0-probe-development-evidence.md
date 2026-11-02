# 04 — P0 Probe Development Evidence

状态：**P0-D / P0-E / P0-F COMPLETE**

Branch:

`task/p0-native-pdf-feasibility`

Design baseline:

`10e5abd18d84a821891175e8e2b823809092d7ad`

Environment audit commit:

`52f127c9a04a4b3a53d582578fec261146ec9b36`

---

## 1. Implemented Scope

Implemented only P0 native PDF feasibility probe scope:

- PyMuPDF open
- SHA256
- file size
- page count
- page geometry
- rotation
- native text
- words
- blocks
- bbox integrity signals
- drawings
- images
- cheap table candidate signals
- per-stage timing
- per-page timing
- source immutability verification
- structured warnings
- machine-readable JSON output

Not implemented:

- OCR
- Torch
- Docling
- TableFormer
- full table reconstruction
- cross-page stitching
- MCP
- Skill
- CRDE
- financial analysis

---

## 2. Production Files

- `src/financial_filing_data_foundation/__init__.py`
- `src/financial_filing_data_foundation/probes/__init__.py`
- `src/financial_filing_data_foundation/probes/native_pdf_probe.py`

---

## 3. Focused Test File

- `tests/unit/probes/test_native_pdf_probe.py`

Coverage:

1. valid tiny born-digital PDF
2. image-only / empty native text page
3. rotated page
4. malformed-but-openable trailing bytes
5. deterministic JSON schema
6. source PDF immutability
7. output cannot overwrite source PDF
8. machine-readable JSON artifact creation
9. heavy-path import absence

---

## 4. Test Environment

Runtime:

`D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe`

- Python 3.14.9 ARM64
- PyMuPDF 1.28.2
- pytest 9.2.0

Absent:

- pypdf
- docling
- torch

---

## 5. Focused Test Command

```powershell
Set-Location "D:\Codex\FinancialFilingDataFoundation"
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe -m pytest tests\unit\probes -q --basetemp "D:\Codex\FinancialFilingDataFoundation\workspace\pytest-p0"
```

Final result:

```text
.........                                                                [100%]
9 passed in 0.14s
```

---

## 6. Test Infrastructure Findings

Initial test attempts exposed two environment/test issues:

1. the default Windows pytest temp directory was not accessible;
2. the heavy-path test initially matched the result field name `tableformer_used` rather than an actual import.

Corrections were limited to test execution / test assertion scope:

- pytest basetemp moved to ignored project `workspace/`;
- forbidden scan now checks real import statements.

Production probe code was not modified to force the tests to pass.

---

## 7. Static Verification

Command:

```powershell
.\.venv\Scripts\python.exe -m py_compile src\financial_filing_data_foundation\probes\native_pdf_probe.py
```

Result: PASS.

Forbidden import scan:

```text
docling
torch
tableformer
openai
anthropic
gemini
```

No matching import statements found.

`git diff --check`: PASS.

---

## 8. Gate Results

- P0-D Probe Implementation: **PASS**
- P0-E JSON Contract: **PASS**
- P0-F Focused Tests: **PASS**

---

## 9. Next Step

Proceed to:

**P0-G — Representative Sample Confirmation**

Only now may the 600519 / 贵州茅台 / FY2024 / 143-page representative PDF be identified and fixed for performance execution.
