# 03 — P0 Independent Acceptance Run Instruction

状态：**P0-K ACCEPTANCE INPUT FREEZE**

你是 **P0 Independent Acceptance 独立验收执行者**。

你不是开发者，也不是 Code Review 负责人。

最终 verdict 只能是：

- `PASS`
- `FAIL`
- `BLOCKED`

不得修改 production code、tests、config、设计文件或依赖版本来使验收通过。

不得创建 P1 代码，不得开始 P1，不得自行改变 P0 scope。

---

## 1. Repository / Branch

Repository:

`projectforkk/FinancialFilingDataFoundation`

Branch:

`task/p0-native-pdf-feasibility`

Design baseline:

`10e5abd18d84a821891175e8e2b823809092d7ad`

Environment audit commit:

`52f127c9a04a4b3a53d582578fec261146ec9b36`

Production development commit:

`f5fb270c2b46db390c7d774c741a96c0490f9ec9`

Performance evidence commit:

`f4c04b0d3475bde8b1749c9c14ada378d128341f`

Code Review commit:

`146ab7d4f92c3d28abc378b43ba578f1a82b1e1d`

Code Review result:

`PASS — READY FOR ACCEPTANCE`

---

## 2. Mandatory Files to Read First

Before executing any acceptance command, fully read:

- `AGENTS.md`
- `PROJECT_STATUS.md`
- `design/01-project-detailed-design.md`
- `design/04-pdf-quality-gate-design.md`
- `design/05-p0-implementation-plan.md`
- `development/02-p0-development-instruction.md`
- `development/03-p0-environment-audit.md`
- `development/04-p0-probe-development-evidence.md`
- `development/05-p0-performance-evidence.md`
- `development/06-p0-code-review.md`
- `acceptance/01-acceptance-strategy.md`
- `acceptance/02-p0-acceptance-instruction.md`
- this file

GitHub / branch content is the source of truth.

---

## 3. Acceptance Environment

Expected PC environment:

- Windows 11 ARM64
- Snapdragon X Plus 8-core
- project directory: `D:\Codex\FinancialFilingDataFoundation`
- project venv: `D:\Codex\FinancialFilingDataFoundation\.venv`
- Python: 3.14.9 ARM64
- PyMuPDF: 1.28.2
- pytest: 9.2.0

Expected absent modules in P0 runtime:

- pypdf
- docling
- torch

If the environment materially differs, report the difference before verdict.

Do not upgrade or replace system Python, Git, Node, PATH, PyMuPDF, or pytest during acceptance.

---

## 4. Representative PDF

Use exactly:

`D:\Codex\FIReport\crde-dayu-workspaces\p1-08-fixture-capture\cn_600519_fy.pdf`

Expected identity:

- company: `600519` 贵州茅台
- filing: FY2024 annual report
- page count: `143`
- file size: `3,626,217 bytes`
- SHA256: `5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30`

Before running the probe, independently verify size, SHA256 and page count.

If this exact file is unavailable, verdict may be `BLOCKED` under the generic acceptance rules.

---

## 5. Git / Candidate Verification

From:

`D:\Codex\FinancialFilingDataFoundation`

verify:

- current branch is `task/p0-native-pdf-feasibility`
- branch contains production commit `f5fb270c2b46db390c7d774c741a96c0490f9ec9`
- branch contains Code Review commit `146ab7d4f92c3d28abc378b43ba578f1a82b1e1d`
- working tree has no unexpected tracked modifications

Do not use `git reset --hard` or `git clean -fd`.

---

## 6. Focused Tests

Use project-local temporary directory because the host default pytest temp directory is not reliably accessible.

Command:

```powershell
Set-Location "D:\Codex\FinancialFilingDataFoundation"
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe -m pytest tests\unit\probes -q --basetemp "D:\Codex\FinancialFilingDataFoundation\workspace\pytest-acceptance"
```

Expected:

- all focused tests PASS
- current expected count: `9 passed`

Any failing focused test => `FAIL`, unless clearly caused by an external acceptance-environment blocker that meets the `BLOCKED` definition.

---

## 7. Heavy-path Verification

Verify source and runtime do not use:

- OCR
- Torch
- Docling
- TableFormer
- external AI API
- Codex Vision

At minimum inspect:

`src/financial_filing_data_foundation/probes/native_pdf_probe.py`

and verify runtime module availability for `docling` / `torch`.

If any forbidden heavy path is used by the P0 probe => `FAIL`.

---

## 8. Source Immutability Snapshot Before Run

Record before Run 1:

- file size
- LastWriteTime / mtime
- SHA256

These must be checked again after Run 2.

---

## 9. Probe Run 1

Command:

```powershell
Set-Location "D:\Codex\FinancialFilingDataFoundation"
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe -m financial_filing_data_foundation.probes.native_pdf_probe `
  "D:\Codex\FIReport\crde-dayu-workspaces\p1-08-fixture-capture\cn_600519_fy.pdf" `
  --output "workspace\p0-acceptance\600519_fy_run1.json" `
  --pretty
```

Inspect the generated JSON directly.

Required:

- `page_count == 143`
- `len(pages) == 143`
- page numbers exactly 1..143
- SHA matches expected SHA
- `sha256 == sha256_after`
- `source_unchanged == true`
- `errors == []`
- native text / word / block statistics available
- required per-stage timings present
- required per-page fields present
- total native probe `<= 120000 ms`
- constraints show no forbidden heavy path

Warnings must be reviewed; do not fail merely because a warning exists unless it is a blocking content/completeness warning.

Known prior observation, not an automatic acceptance result:

`repaired broken tree structure in outline`

Acceptance must independently inspect the current run.

---

## 10. Probe Run 2

Repeat with:

`workspace\p0-acceptance\600519_fy_run2.json`

Compare Run 1 and Run 2:

- SHA
- page count
- totals
- summary
- warnings
- constraints
- all page non-timing fields

Timing values may differ.

Output structure and non-timing data must be stable.

---

## 11. Source Immutability Snapshot After Run 2

Re-read:

- file size
- mtime
- SHA256

All must match the pre-run snapshot.

If the source PDF was modified => `FAIL`.

---

## 12. PASS Conditions

PASS requires all of the following:

- correct branch / candidate
- environment acceptable
- focused tests PASS
- exact representative PDF verified
- probe completes twice
- page_count correct
- all 143 pages enumerated
- SHA stable
- source immutable
- native statistics present
- JSON schema / required fields stable
- warnings inspected and no blocker
- no OCR
- no Torch
- no Docling
- no TableFormer
- no external AI API
- total native probe <= 120 seconds
- no acceptance blocker

---

## 13. FAIL Conditions

FAIL if any material acceptance condition fails, including:

- wrong page count
- missing pages
- unstable SHA
- source PDF modification
- focused test failure
- forbidden heavy parser path
- total > 120 seconds
- unstable required result schema
- silent content/error loss

---

## 14. BLOCKED Conditions

Use `BLOCKED` only when acceptance cannot be judged due to an external execution blocker such as:

- exact representative PDF inaccessible
- required approved runtime unavailable and cannot be used as designed
- external machine/tool access prevents execution

Do not use `BLOCKED` for an ordinary product/test failure.

---

## 15. Final Output

Final response must contain exactly one verdict:

`PASS` / `FAIL` / `BLOCKED`

plus a minimal evidence summary containing:

- branch / candidate SHA
- test result
- page count
- run 1 / run 2 total timings
- SHA/source immutability result
- heavy-path result
- warning/blocker summary

Do not modify code to obtain the verdict.

Do not start P1.

Do not declare the whole FFDF project complete.
