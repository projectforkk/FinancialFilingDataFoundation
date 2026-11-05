---
name: FFDF公司财报下载
description: "根据公司代码和年度/年度区间，批量下载 CN/HK 正式财报并通过 FFDF 完成 P3-P7 解析、Validation、Registry 与 P8 live catalog 入库。"
---

# FFDF公司财报下载

## Purpose

根据用户提供的公司代码和单个年度或年度区间，调用 FFDF 已有用户 CLI 批量完成：

`正式财报获取 -> Raw Store -> Registry -> P3 -> P4 -> P5 -> P6 -> P7 -> Parsed Registry -> P8 live catalog`

本 Skill 只做财报下载、解析和入库，不做公司研究、不写研究报告、不调用任何 AI 模型。

## Invocation

两个参数为必填；另外允许一个可选控制词 `重新读入`：

`$FFDF公司财报下载 <company_code> <year_or_range> [重新读入]`

示例：

`$FFDF公司财报下载 605117 2021`

`$FFDF公司财报下载 605117 2021-2026`

`$FFDF公司财报下载 700 2024`

不得增加 market、period、model 等第三个必填参数。可选的 `重新读入` 只是控制词，不是第三个必填参数。

## Parameter 1 — company_code

必须是纯数字公司代码。

### Market inference

- 恰好 6 位数字 -> `market=CN`，ticker 原样保留；
- 1 到 5 位数字 -> `market=HK`，ticker 左侧补零到 5 位；
- 其他格式 -> 停止。

例如：

- `605117` -> CN / `605117`
- `688981` -> CN / `688981`
- `700` -> HK / `00700`
- `00700` -> HK / `00700`

禁止：

- 用公司名称猜代码；
- 根据历史聊天猜市场；
- 对非纯数字代码自动修正；
- 把 6 位代码改成 HK。

非法时输出：

`FFDF_DOWNLOAD_INPUT_INVALID: COMPANY_CODE_INVALID`

## Parameter 2 — year_or_range

允许两种格式：

### Single year

`YYYY`

例如：

`2021`

展开为：

`[2021]`

### Inclusive range

`YYYY-YYYY`

例如：

`2021-2026`

展开为：

`[2021, 2022, 2023, 2024, 2025, 2026]`

必须满足：

- 起始年 <= 结束年；
- 每个年度为四位整数；
- 不自动扩大范围；
- 不把 `2021-26` 猜成 `2021-2026`。

非法时输出：

`FFDF_DOWNLOAD_INPUT_INVALID: YEAR_OR_RANGE_INVALID`

## Supported filing periods

FFDF 当前用户 CLI 支持且本 Skill 固定尝试：

`Q1 -> H1 -> Q3 -> FY`

对每个 requested year 都按这个顺序执行。

不要使用 Q2。

## Important publication-window rule

FFDF CLI 对每个 period 有 deterministic default publication search window。

如果某个 requested slot 的默认 publication window 尚未开始，例如当前年度的 FY 尚未到下一年年报披露窗口，CLI 可能返回：

`default publication search window has not started yet`

必须分类为：

`FUTURE_WINDOW_NOT_STARTED`

这不是系统错误，不要人为扩大 window，也不要联网猜公告日期。

## Status-first skip rule

对每个 `year x period`，先执行：

`ffdf status --market <market> --ticker <ticker> --year <year> --period <period>`

如果 shell 中没有直接可用的 `ffdf` 命令，使用当前仓库已安装的等价入口：

`python -m financial_filing_data_foundation.user_cli status ...`

### Default: skip already-ingested filing

如果 status 正常返回：

`p8_catalog_registered == true`

则该当期财报视为已经入库。

默认：

`normalized_status = SKIPPED_ALREADY_INGESTED`

并**不再调用 `ffdf ingest`**。

这意味着默认不会：

- 重复下载；
- 重复进入 P3-P6；
- 再次计算 P7；
- 再次 upsert P8。

### Integrity exception

如果 status 同时显示：

- `local_document_status = CONFLICT`
- `local_document_status = DRIFTED`
- `local_document_status = AMBIGUOUS`

则不得仅因为 P8 catalog 有记录就静默跳过。

必须记录 blocker；不要把异常本地状态写成 SKIPPED_ALREADY_INGESTED。

### Optional directive: 重新读入

调用可以显式追加：

`重新读入`

例如：

`$FFDF公司财报下载 605117 2021-2026 重新读入`

指定后：

- 对 requested slots 忽略默认的 already-ingested skip；
- 即使 `p8_catalog_registered == true` 也重新调用标准 `ffdf ingest`；
- 不删除 Raw；
- 不清空 Registry；
- 不删除 P3-P7；
- 不强制重新下载已有相同 SHA 的 PDF；
- FFDF 自身 `INCREMENTAL_FIRST` / immutable artifact 规则继续生效。

因此，`重新读入` 的含义是“重新执行标准 ingest”，不是 destructive rebuild。

如果没有明确出现 `重新读入` 四个字，默认永远跳过已经入库的当期财报。

## Execution command

对每个 `year x period`，从 FFDF repo root 执行：

`ffdf ingest --market <market> --ticker <ticker> --year <year> --period <period>`

优先使用当前项目已配置的 `ffdf` CLI / Python environment。

如果 shell 中没有直接可用的 `ffdf` 命令，应使用仓库已安装的等价入口，例如：

`python -m financial_filing_data_foundation.user_cli ingest ...`

但不得修改业务参数或切换到另一套 downloader/parser。

## What ingest already does

禁止在 Skill 中重复实现这些阶段。

现有 `ffdf ingest` 已负责：

1. 创建 canonical filing request；
2. 查询 Registry；
3. 已有文档时允许 `REUSED_LOCAL`；
4. 执行 Dayu doctor；
5. 使用 CNINFO / HKEX provider discovery；
6. 下载官方 PDF 或复用本地 Raw；
7. 校验 PDF / size / SHA256；
8. 写 content-addressed Raw Store；
9. Registry 注册；
10. P3 Native Page / Section / FTS；
11. P4 Table Candidate；
12. P5 Table Reconstruction；
13. P6 Raw Fact + Evidence；
14. P7 Validation；
15. Parsed Registry；
16. blocking_issue_count == 0 时 upsert 到 `workspace/mcp/p8-live-catalog.json`。

## Incremental / reuse rule

本 Skill 必须尊重 FFDF 的 `INCREMENTAL_FIRST`。

如果同一 filing 已经存在：

- 允许 `REUSED_LOCAL`；
- 不要求重新下载；
- 不删除旧 Raw；
- 不清空 Registry；
- 不强制重跑与当前 `ffdf ingest` 设计相冲突的 destructive operation。

## CN behavior

对于 CN 代码，逐年尝试：

- Q1
- H1
- Q3
- FY

`NOT_FOUND` 必须记录，不要伪造财报。

不要因为普通 A 股通常存在四个报告期，就把 provider 的 NOT_FOUND 静默改成成功。

## HK behavior

对于 HK 代码，同样按 FFDF 支持 period 尝试：

- Q1
- H1
- Q3
- FY

但香港发行人并非都披露 Q1/Q3。

因此：

`NOT_FOUND`

表示：

`该 slot 未找到正式报告`

它是 gap，不是 downloader/parser failure。

这种策略可以保留自愿 Q1/Q3 披露，同时不会把不存在的季度报告当系统错误。

## Per-slot status normalization

新增首要状态：

- `SKIPPED_ALREADY_INGESTED`

每个 slot 必须记录：

- year
- period
- market
- ticker
- exit_code
- acquisition_status
- document_sha256
- P3 status/page_count
- P4 status/candidate_count
- P5 status/table_count
- P6 status/fact_count/evidence_count
- P7 validation_status
- P7 blocking_issue_count
- P7 review_issue_count
- p8_catalog
- research_ready
- normalized_status
- message/reason_code

### SKIPPED_ALREADY_INGESTED

默认 status-first 快速路径。

条件：

- 未指定 `重新读入`；
- `p8_catalog_registered == true`；
- 没有明确 local CONFLICT / DRIFTED / AMBIGUOUS。

行为：

- 跳过 `ffdf ingest`；
- 直接复用当前入库结果。

### INGESTED

满足：

- CLI exit code 0；
- acquisition_status = DOWNLOADED；
- P3-P7 完成；
- blocking_issue_count = 0；
- P8 catalog 已新增或更新。

### REUSED_LOCAL

满足：

- CLI exit code 0；
- acquisition_status = REUSED_LOCAL；
- P3-P7 / Registry / P8 状态按当前 ingest 结果确认。

### NOT_FOUND

Acquisition 明确返回 NOT_FOUND。

不得凭空制造 PDF。

### FUTURE_WINDOW_NOT_STARTED

默认 publication window 尚未开始。

不得覆盖默认 window 强制向未来搜索。

### REVIEW_REQUIRED

Acquisition provider 本身返回 REVIEW_REQUIRED。

这与 P7 的 `validation_status=REVIEW_REQUIRED` 不同。

P7 REVIEW_REQUIRED 且 blocking=0 仍然可以发布到 P8；必须保留真实 validation status。

### BLOCKED

Acquisition/provider 返回 BLOCKED 或其他明确 acquisition blocker。

### INGEST_BLOCKED

财报已经获取和解析，但：

`P7 blocking_issue_count > 0`

因此：

- Registry / artifacts 可以存在；
- 不得宣称已成功发布到 P8 live catalog；
- final summary 必须显式显示。

### ERROR

其他无法归类的执行错误。

必须保留：

- exit code；
- reason_code；
- 最小错误信息。

## Exit-code awareness

不要只看进程是否输出 JSON。

至少按现有 CLI 语义识别：

- `0`: ingest/reuse 成功；
- `2`: acquisition NOT_FOUND；
- `3`: acquisition REVIEW_REQUIRED；
- `4`: acquisition BLOCKED；
- `6`: ingest 已执行但 research_ready false，重点检查 P7 blocking；
- `10`: CLI exception/error。

同时以返回 JSON 字段为最终细分依据。

## Continue-on-slot policy

批量年度任务中，一个 slot 的 NOT_FOUND 或 FUTURE_WINDOW_NOT_STARTED 不应阻止后续 slot。

默认继续处理剩余年度和 period。

对于 BLOCKED / INGEST_BLOCKED / ERROR：

- 记录精确错误；
- 默认继续其他独立 slot，以得到完整批量结果；
- 最终状态降级为 PARTIAL 或 FAIL；
- 不要隐藏失败。

## Final status

### PASS

满足：

- 至少一个 slot 为 SKIPPED_ALREADY_INGESTED、INGESTED 或 REUSED_LOCAL；
- 不存在 BLOCKED；
- 不存在 INGEST_BLOCKED；
- 不存在 ERROR。

允许同时存在：

- NOT_FOUND；
- FUTURE_WINDOW_NOT_STARTED；
- P7 REVIEW_REQUIRED 但 blocking=0。

### PARTIAL

满足：

- 至少一个 slot 为 SKIPPED_ALREADY_INGESTED、INGESTED 或 REUSED_LOCAL；
- 但同时存在 BLOCKED / INGEST_BLOCKED / ERROR。

### FAIL

满足任一：

- 参数非法；
- FFDF CLI/Dayu 环境不可用；
- requested slots 中没有任何 SKIPPED_ALREADY_INGESTED / INGESTED / REUSED_LOCAL；
- 全部 slot 都无法执行成功。

## Required summary

结束时必须输出：

- `skill = FFDF公司财报下载`
- `company_code_input`
- `market`
- `normalized_ticker`
- `year_input`
- `requested_years`
- `attempted_slot_count`
- `ingested_count`
- `reused_count`
- `not_found_count`
- `future_not_started_count`
- `review_required_count`
- `blocked_count`
- `ingest_blocked_count`
- `error_count`
- 每个 year/period 的 normalized status；
- 每个成功 document 的 SHA256；
- P8 catalog publication 结果；
- `FINAL STATUS: PASS | PARTIAL | FAIL`。

## Example summary

```text
FFDF公司财报下载

company_code_input: 605117
market: CN
normalized_ticker: 605117
requested_years: 2021-2022

2021 Q1  SKIPPED_ALREADY_INGESTED
2021 H1  INGESTED
2021 Q3  INGESTED
2021 FY  INGESTED
2022 Q1  INGESTED
2022 H1  INGESTED
2022 Q3  INGESTED
2022 FY  INGESTED

attempted_slot_count: 8
ingested_count: 7
skipped_already_ingested_count: 1
reused_count: 0
not_found_count: 0
future_not_started_count: 0
blocked_count: 0
ingest_blocked_count: 0
error_count: 0

FINAL STATUS: PASS
```

## Non-negotiable prohibitions

禁止：

1. 调用 AI 模型；
2. 调用外部 OpenAI/Anthropic/Gemini API；
3. 通过网页手工下载来替代 FFDF provider；
4. 修改官方 Raw PDF；
5. 修改现有 P3/P4/P5/P6/P7 artifact 内容来伪造 PASS；
6. 删除 Registry；
7. 删除 Raw Store；
8. 使用 git reset --hard / git clean -fd；
9. NOT_FOUND 时伪造财报；
10. FUTURE_WINDOW_NOT_STARTED 时强行扩大 publication window；
11. P7 blocking>0 时写成 P8 已成功入库；
12. 把 P7 REVIEW_REQUIRED 自动改成 PASS。
13. 未指定 `重新读入` 时，对已入库 slot 再次执行 ingest。

## Completion rule

必须处理完所有可执行 requested slots，并输出完整 summary 后才算本 Skill 完成。
