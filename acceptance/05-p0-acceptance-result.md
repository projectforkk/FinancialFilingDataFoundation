# 05 — P0 Independent Acceptance Result

状态：**PASS**

Repository:

`projectforkk/FinancialFilingDataFoundation`

Branch:

`task/p0-native-pdf-feasibility`

Acceptance candidate:

`63547b5cfd3112a7c0598a32139b9b191c356c69`

Design baseline:

`8c5f6d3f203bfd15cfa452a976b23dc8a6f81461`

Production development commit:

`f5fb270c2b46db390c7d774c741a96c0490f9ec9`

Code Review commit:

`146ab7d4f92c3d28abc378b43ba578f1a82b1e1d`

Acceptance refreeze:

`acceptance/04-p0-acceptance-refreeze.md`

---

## 1. Verdict

**PASS**

P0 — Native PDF Parsing Feasibility Probe satisfies the frozen acceptance criteria.

---

## 2. Focused Tests

Command:

```powershell
Set-Location "D:\Codex\FinancialFilingDataFoundation"
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe -m pytest tests\unit\probes -q --basetemp "D:\Codex\FinancialFilingDataFoundation\workspace\pytest-acceptance"
```

Result:

```text
9 passed in 0.14s
```

---

## 3. Runtime / Heavy-path Verification

Verified runtime:

- Python 3.14.9
- ARM64
- 64-bit
- PyMuPDF 1.28.2
- pytest 9.2.0

Absent:

- pypdf
- docling
- torch

Forbidden import scan:

- no Torch import
- no Docling import
- no pypdf import
- no external AI SDK import
- no TableFormer import

Representative output constraints:

- OCR used: false
- Torch used: false
- Docling used: false
- TableFormer used: false
- external AI API used: false
- Codex Vision used: false

Heavy-path result: **PASS**

---

## 4. Representative PDF Identity

Source:

`D:\Codex\FIReport\crde-dayu-workspaces\p1-08-fixture-capture\cn_600519_fy.pdf`

Verified before run:

- file size: 3,626,217 bytes
- page count: 143
- password protected: false
- PyMuPDF repaired flag: false
- SHA256: `5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30`
- LastWriteTimeUtc: `2026-11-02 13:08:28`

Identity result: **PASS**

---

## 5. Independent Probe Run 1

Output:

`workspace\p0-acceptance\600519_fy_run1.json`

Result:

- page_count: 143
- pages length: 143
- page sequence: 1..143
- total: 1237.301 ms
- SHA before/after equal: true
- source_unchanged: true
- errors: []
- warnings: 1
- native text pages: 143
- empty text pages: 0
- likely table pages: 106

Totals:

- native_chars: 176,089
- words: 14,890
- blocks: 3,405
- drawings: 46,124
- images: 2

Stage timings:

- open: 9.924 ms
- text: 315.985 ms
- layout: 424.779 ms
- drawings_images: 412.288 ms
- table_candidate_signals: 33.323 ms
- hash_before: 13.012 ms
- hash_after: 13.582 ms
- total: 1237.301 ms

Performance gate:

`1237.301 ms <= 120000 ms`

Result: **PASS**

---

## 6. Independent Probe Run 2

Output:

`workspace\p0-acceptance\600519_fy_run2.json`

Result:

- page_count: 143
- total: 1222.031 ms
- SHA equal to Run 1: true
- page_count equal: true
- totals equal: true
- summary equal: true
- warnings equal: true
- constraints equal: true
- all 143 page non-timing records equal: true

Repeatability result: **PASS**

---

## 7. Warning Review

Observed structured warning:

`repaired broken tree structure in outline`

Assessment:

- outline/bookmark repair warning only;
- no missing page;
- 143 / 143 pages have native text;
- `errors == []`;
- no content-completeness blocker identified.

Warning result: **NON-BLOCKING**

---

## 8. Source Immutability

After Run 2:

- file size: 3,626,217 bytes
- LastWriteTimeUtc: `2026-11-02 13:08:28`
- SHA256: `5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30`

All match pre-run snapshot.

Source immutability result: **PASS**

---

## 9. Final Acceptance Summary

- candidate verification: PASS
- design baseline verification: PASS
- focused tests: PASS
- representative PDF identity: PASS
- 143 / 143 page enumeration: PASS
- native extraction statistics: PASS
- required JSON fields: PASS
- Run 1 performance: PASS
- Run 2 performance: PASS
- repeatability: PASS
- source immutability: PASS
- heavy-path prohibition: PASS
- warnings: reviewed, non-blocking
- blocker: NONE

Final verdict:

# PASS

P0 may proceed to state closeout.

This result does not start P1 automatically.
