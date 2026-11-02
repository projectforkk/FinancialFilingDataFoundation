# 04 — P0 Independent Acceptance Refreeze

状态：**P0-K ACCEPTANCE INPUT REFREEZE**

本文件取代：

`acceptance/03-p0-acceptance-run-instruction.md`

原因：P0-K 初次 freeze 后，项目新增了 design-first issue resolution 治理规则，并补充了 P2 Dayu Git-pinned acquisition dependency 设计。根据最新设计，旧 freeze 自动失效，必须重新冻结。

---

## 1. Design Change

新 design baseline：

`8c5f6d3f203bfd15cfa452a976b23dc8a6f81461`

变更内容：

1. 全项目新增“发现问题 → 先更新设计 → 再继续”的强制治理规则；
2. P0 明确：freeze 后发生设计变更，必须 refreeze；
3. P2 明确：
   - 不得假设本机已安装 Dayu；
   - 从 Git 获取 `noho/dayu-agent`；
   - 固定 baseline commit `2115c86d5a9027bb51cbbc8a4d0175080732e4e6`；
   - upstream checkout 保持只读；
   - FFDF 通过 narrow Acquisition Adapter 使用 downloader；
   - 不把 Docling 高层处理链引入 native parser runtime；
   - 如必须修改 Dayu，先更新设计，再通过受控 fork / 新 commit 管理。

P0 branch 已合并新 design baseline：

`a45dd9295e9d55ee800550bf4c24cf36b16aac14`

---

## 2. Impact Assessment

Production development commit：

`f5fb270c2b46db390c7d774c741a96c0490f9ec9`

Performance evidence commit：

`f4c04b0d3475bde8b1749c9c14ada378d128341f`

Code Review commit：

`146ab7d4f92c3d28abc378b43ba578f1a82b1e1d`

Design change 后已核对：

- `git diff f5fb270..HEAD -- src tests`：无差异；
- production probe blob SHA 与 `f5fb270` 完全相同；
- focused test blob SHA 与 `f5fb270` 完全相同；
- 新设计变更不修改 P0 production code、tests、runtime、JSON contract、performance gate 或 acceptance criteria。

结论：

**P0-D 至 P0-J 无需因本次治理/P2设计变更重新开发或重新 Code Review。**

但原 P0-K freeze 已失效，因此本文件形成新的 P0-K freeze。

---

## 3. Candidate

Repository：

`projectforkk/FinancialFilingDataFoundation`

Branch：

`task/p0-native-pdf-feasibility`

Acceptance candidate 必须包含：

- design baseline `8c5f6d3f203bfd15cfa452a976b23dc8a6f81461`
- production commit `f5fb270c2b46db390c7d774c741a96c0490f9ec9`
- performance evidence `f4c04b0d3475bde8b1749c9c14ada378d128341f`
- Code Review `146ab7d4f92c3d28abc378b43ba578f1a82b1e1d`
- design merge `a45dd9295e9d55ee800550bf4c24cf36b16aac14`

Working tree must have no unexpected tracked modifications.

---

## 4. Acceptance Environment

Expected:

- Windows 11 ARM64
- Snapdragon X Plus 8-core
- project: `D:\Codex\FinancialFilingDataFoundation`
- venv: `D:\Codex\FinancialFilingDataFoundation\.venv`
- Python 3.14.9 ARM64
- PyMuPDF 1.28.2
- pytest 9.2.0
- pypdf absent
- docling absent
- torch absent

Do not change dependency versions during acceptance.

---

## 5. Representative PDF

Exact file:

`D:\Codex\FIReport\crde-dayu-workspaces\p1-08-fixture-capture\cn_600519_fy.pdf`

Expected:

- company: 600519 贵州茅台
- FY2024
- page count: 143
- size: 3,626,217 bytes
- SHA256: `5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30`

Acceptance must verify this independently before Run 1.

---

## 6. Focused Tests

Command:

```powershell
Set-Location "D:\Codex\FinancialFilingDataFoundation"
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe -m pytest tests\unit\probes -q --basetemp "D:\Codex\FinancialFilingDataFoundation\workspace\pytest-acceptance"
```

Required: all focused tests PASS.

---

## 7. Heavy-path Verification

P0 probe must not use:

- OCR
- Torch
- Docling
- TableFormer
- external AI API
- Codex Vision

At minimum inspect source imports and runtime availability of `docling` / `torch`.

---

## 8. Source Snapshot Before Run

Record:

- file size
- mtime
- SHA256

---

## 9. Probe Run 1

```powershell
Set-Location "D:\Codex\FinancialFilingDataFoundation"
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe -m financial_filing_data_foundation.probes.native_pdf_probe `
  "D:\Codex\FIReport\crde-dayu-workspaces\p1-08-fixture-capture\cn_600519_fy.pdf" `
  --output "workspace\p0-acceptance\600519_fy_run1.json" `
  --pretty
```

Required:

- page_count = 143
- len(pages) = 143
- page sequence = 1..143
- SHA matches expected
- source_unchanged = true
- errors = []
- native statistics available
- required stage timings available
- required per-page fields available
- total <= 120000 ms
- no forbidden heavy path

Warnings must be reviewed.

---

## 10. Probe Run 2

Repeat to:

`workspace\p0-acceptance\600519_fy_run2.json`

Compare non-timing fields:

- SHA
- page count
- totals
- summary
- warnings
- constraints
- all page non-timing fields

Timing values may differ.

---

## 11. Source Snapshot After Run 2

Recheck:

- size
- mtime
- SHA256

All must match pre-run snapshot.

---

## 12. Verdict

Final verdict only:

- `PASS`
- `FAIL`
- `BLOCKED`

PASS requires all P0 acceptance criteria in `acceptance/02-p0-acceptance-instruction.md` plus this refreeze to pass.

Independent acceptance must not modify production code, tests, config, design files, or dependency versions to obtain PASS.

Do not start P1 during P0 acceptance.
