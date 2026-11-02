# 05 — P0 Native PDF Parsing Feasibility Probe 实施计划

状态：**DESIGN BASELINE — EXECUTION PLAN**

适用阶段：**P0 — Native PDF Parsing Feasibility Probe**

仓库：`projectforkk/FinancialFilingDataFoundation`

正式开发分支：`task/p0-native-pdf-feasibility`

---

## 1. 目的

本文件把 P0 从“批准开发”落实为可执行、可复核、可验收的阶段实施计划。

P0 的唯一目标是：

> 在目标 Windows PC 上，验证代表性 CN/HK born-digital PDF 能否通过轻量 native path，以可接受性能稳定提取 text / words / blocks / bbox / drawings / images，并生成 cheap table candidate signals。

P0 不完成完整财报解析器，不完成 MCP，不完成 Skill，不完成 CRDE，不完成投资分析。

---

## 2. 执行原则

必须遵守：

`DESIGN → DEVELOPMENT → CODE REVIEW → ACCEPTANCE → DONE`

执行过程中：

- GitHub 是唯一真源；
- 原始 PDF 不可修改；
- 优先复用现有工具和环境；
- 不得仅因版本不是最新而升级系统 Python / Git / Node / PATH；
- 禁止 `git reset --hard` / `git clean -fd`，除非用户明确授权；
- P0 禁止 OCR / Torch / Docling / TableFormer / external AI API / Codex Vision；
- 不得提前实现 P1+；
- 不得用理论性能代替目标 PC 实测。

---

## 3. P0-A — 开发基线与工作区确认

### 输入

- Repository
- P0 branch
- GitHub 当前 HEAD
- 当前本地工作区

### 操作

1. 核对：
   - `main`
   - `task/p0-native-pdf-feasibility`
   - remote refs
   - local HEAD
2. 确认本地仓库目录。
3. 检查 `git status --short --branch --untracked-files=all`。
4. 清除仅由本会话误提前生成且未提交的文件。
5. 不使用破坏性 reset/clean。

### Gate A

- 工作区干净；
- P0 branch 与 GitHub 基线一致；
- 没有历史代码污染；
- 后续变更可从确定设计 baseline 追溯。

---

## 4. P0-B — PC Environment Audit

### 必须记录

- OS / Windows version
- CPU
- machine architecture
- Python executable
- Python version
- Python architecture
- pip
- uv
- PyMuPDF 是否已存在
- pypdf 是否已存在
- Git
- Codex
- Dayu 实际仓库位置
- Dayu Python / venv 位置
- 可复用依赖情况

### 规则

采用 existing-tools-first：

1. 已存在且兼容 → `REUSE_EXISTING`
2. 不存在 → `INSTALL_REQUIRED`
3. 存在但不兼容 → 先设计隔离环境
4. 不得擅自升级 system Python / PATH / Git / Node

### Gate B

形成明确、可复现的环境审计结果，并确定 P0 实际使用的 Python / architecture。

---

## 5. P0-C — P0 Python 环境与最小依赖决策

### 决策优先级

`现有兼容环境 → 项目内隔离 .venv → 新增最小依赖`

### 最小原则

P0 只安装实现 native probe 与 focused tests 必需的依赖。

不得因为方便顺手引入：

- OCR stack
- Torch
- Docling
- TableFormer
- neural layout model
- external AI SDK

### Gate C

记录：

- environment path
- Python version / architecture
- dependency names / versions
- reuse / install decision
- no-heavy-path assertion

---

## 6. P0-D — Native PDF Probe 实现

建议位置：

`src/financial_filing_data_foundation/probes/native_pdf_probe.py`

### 必须采集

文档级：

- file path
- SHA256
- file size
- page count
- parser/runtime environment
- warnings / errors

页面级：

- page_no
- width
- height
- rotation
- native_char_count
- word_count
- block_count
- drawing_count
- image_count
- bbox integrity signals
- cheap table candidate signals
- elapsed_ms

### 阶段计时

至少：

- open
- text
- layout
- drawings_images
- table_candidate_signals
- total

可以增加 hash / IO 等附加计时，但不得替代上述字段。

### 明确不做

- table reconstruction
- cross-page table stitching
- OCR
- semantic financial facts
- canonical metric
- fiscal period engine
- MCP
- Skill

### Gate D

单文件 probe 可稳定运行并生成完整 machine-readable result。

---

## 7. P0-E — Machine-readable JSON Contract

顶层至少：

```json
{
  "file": "...",
  "sha256": "...",
  "file_size": 0,
  "page_count": 0,
  "timings_ms": {
    "open": 0,
    "text": 0,
    "layout": 0,
    "drawings_images": 0,
    "table_candidate_signals": 0,
    "total": 0
  },
  "totals": {
    "native_chars": 0,
    "words": 0,
    "blocks": 0,
    "drawings": 0,
    "images": 0
  },
  "pages": []
}
```

每页至少：

- page_no
- width
- height
- rotation
- native_char_count
- word_count
- block_count
- drawing_count
- image_count
- cheap table candidate signals
- elapsed_ms

异常不得静默吞掉；必须以 warnings / errors 或结构化异常反映。

### Gate E

JSON 字段结构稳定、语义固定、重复执行可比较。

---

## 8. P0-F — Focused Unit Tests

至少覆盖：

1. valid tiny born-digital PDF
2. empty-text / image-only page
3. rotated page
4. malformed-but-openable fixture（若能安全构造）
5. deterministic JSON schema
6. source document immutable
7. no heavy dependency / heavy path

测试 fixture 优先程序生成，避免把大型 PDF 纳入 Git。

### Gate F

Focused tests 全部 PASS。

---

## 9. P0-G — 代表样本确认

仅在 P0-D / E / F 已完成后进入。

首选样本：

- company: `600519`
- company name: 贵州茅台
- filing: FY2024
- expected page count: 143
- type: born-digital

### 样本查找顺序

1. 已有本地正式原始 PDF
2. 已有 Dayu workspace 中的原始 PDF
3. 若仍缺失，停止并按已批准 acquisition policy 处理，不在 P0 临时发明新下载流程

### 运行前固定

- source path
- SHA256
- file size
- mtime
- expected page count

### Gate G

代表样本身份确定，源文件保持 immutable。

---

## 10. P0-H — 第一次真实性能 Probe

在目标 Windows PC 上执行完整 native probe。

必须得到：

- 143 pages 是否全部枚举
- native chars
- words
- blocks
- drawings
- images
- cheap table candidate signals
- per-page elapsed
- per-stage elapsed
- total elapsed
- warnings / errors

### 当前性能 Gate

`143-page born-digital native probe <= 120 秒`

如果 > 120 秒：

P0 不得 PASS，必须分析真实瓶颈，包括但不限于：

- PyMuPDF
- Python architecture
- Windows ARM64 / AMD64
- file IO
- probe algorithm
- environment

不得提前假设目标为 10 / 20 / 30 秒。

### Gate H

得到第一组可复现真实性能证据。

---

## 11. P0-I — 重复执行与稳定性验证

同一 PDF 至少重跑一次。

核对：

- SHA 不变
- page_count 不变
- 143 页全部枚举
- JSON schema 稳定
- totals 合理稳定
- source size / mtime / SHA 不被 probe 修改
- timing 无异常失控

timing 不要求数值完全一致。

### Gate I

输出结构和 source immutability 可重复验证。

---

## 12. P0-J — Code Review

Code Review 必须检查：

- 是否严格限制在 P0 scope
- 是否存在 OCR / Docling / Torch / TableFormer
- 是否存在 external AI API
- 是否偷偷进入完整 table reconstruction
- 是否修改源 PDF
- 是否遗漏 per-stage timing
- JSON contract 是否满足设计
- tests 是否覆盖要求
- 是否存在 silent error
- 是否修改无关 production / environment

结论：

- `IN_REVIEW → READY_FOR_ACCEPTANCE`
- 或 `IN_REVIEW → CHANGES_REQUIRED`

---

## 13. P0-K — Independent Acceptance 输入固定

验收前固定：

- repository
- branch
- development commit SHA
- design baseline SHA
- environment
- Python path / version / architecture
- PyMuPDF version
- representative PDF path / SHA
- exact test command
- exact probe command
- result JSON path

验收执行者不得修改 production code / tests / config 使结果通过。

---

## 14. P0-L — Independent Acceptance

按 `acceptance/02-p0-acceptance-instruction.md` 执行。

PASS 至少要求：

- probe completes
- page_count 正确
- SHA stable
- 143 pages fully enumerated
- native text / words / blocks 等统计存在
- no OCR
- no Torch
- no Docling
- no TableFormer
- no external AI
- total <= 120s
- tests PASS
- source PDF unchanged
- no blocker

最终 verdict 只能是：

- `PASS`
- `FAIL`
- `BLOCKED`

---

## 15. P0-M — 状态收口

只有 Independent Acceptance = `PASS` 后：

1. 保存 acceptance evidence。
2. 更新 `PROJECT_STATUS.md`。
3. P0 → `DONE`。
4. 才允许进入 P1。

P0 未 PASS 前不得开始：

- P1 implementation
- P2 acquisition implementation
- P5 table reconstruction
- P8 Local MCP
- P10 Codex Skill

---

## 16. 执行顺序

严格按以下顺序：

```text
P0-A  Baseline / Workspace
↓
P0-B  Environment Audit
↓
P0-C  Environment Decision
↓
P0-D  Probe Implementation
↓
P0-E  JSON Contract
↓
P0-F  Focused Tests
↓
P0-G  Representative Sample
↓
P0-H  Performance Probe #1
↓
P0-I  Repeatability Probe
↓
P0-J  Code Review
↓
P0-K  Acceptance Input Freeze
↓
P0-L  Independent Acceptance
↓
P0-M  State Closeout
```

禁止跨 Gate 推进。

### 16.1 P0 问题处置规则

P0 任一步骤若发现问题并已经找到解决方案，必须先执行设计回写：

1. 停止当前 Gate；
2. 记录问题事实、根因、解决方案和影响范围；
3. 先更新对应设计文件并提交 Git；
4. 判断是否影响已经完成的 Gate；
5. 若影响，则重新执行受影响 Gate；
6. 若发生在 P0-K acceptance freeze 之后，则原 freeze 失效，必须重新生成验收冻结；
7. 只有新的设计 baseline 生效后，才能继续后续步骤。

不得先修改 production code 再补设计。

---

## 17. 当前执行入口

本实施计划写入并形成设计 commit 后，从：

**P0-A → P0-B**

开始执行。

当前不得先寻找或运行代表 PDF，也不得先写 production probe。
