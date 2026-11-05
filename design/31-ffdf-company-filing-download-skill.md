# 31 — FFDF公司财报下载 Skill 设计

## 状态

**OPTIMIZATION V2 AUTHORIZED / STATUS-FIRST**

## 目标

新增项目级 Codex Skill：

`FFDF公司财报下载`

用途：用户只提供公司代码和单一年度/年度区间，Skill 自动识别 CN/HK 市场，逐年逐报告期调用现有 `ffdf ingest`，完成正式财报下载、Raw 注册、P3-P7 解析/验证、Parsed Registry 注册，并在 P7 非 blocking 时发布到 P8 live catalog。

## 参数

仅两个逻辑参数：

1. `company_code`
2. `year_or_range`

调用：

`$FFDF公司财报下载 <company_code> <year_or_range>`

例如：

`$FFDF公司财报下载 605117 2021`

`$FFDF公司财报下载 605117 2021-2026`

`$FFDF公司财报下载 700 2024`

## 市场识别

- 6 位纯数字：CN，保持原代码；
- 1-5 位纯数字：HK，左补零到 5 位；
- 其他：输入非法，fail closed。

不接受公司名称，不猜市场。

## 年度展开

- `YYYY` -> 单一年份；
- `YYYY-YYYY` -> 闭区间逐年；
- 起始年必须 <= 结束年；
- 不自动扩大区间。

## 报告期

FFDF 当前支持：`Q1/H1/Q3/FY`。

对每个年度按固定顺序：

`Q1 -> H1 -> Q3 -> FY`

CN：逐期调用 ingest。

HK：同样尝试 FFDF 支持的四个 period；NOT_FOUND 视为该期没有发现正式财报，不作为运行错误。这样既不会漏掉自愿季度披露，也不会把不存在的季度报告误判为系统故障。

## 执行链

每个 slot 调用：

`ffdf ingest --market <CN|HK> --ticker <ticker> --year <year> --period <period>`

现有 CLI 完整执行：

Acquire
-> Raw Store
-> Registry
-> P3
-> P4
-> P5
-> P6 Raw Fact / Evidence
-> P7 Validation
-> Parsed Registry
-> P8 live catalog（blocking_issue_count == 0 时）

不复制 parser 逻辑。

## 复用

如果本地已有相同正式财报，必须使用现有 incremental / Registry / Raw Store 逻辑，允许 `REUSED_LOCAL`，不得强制重复下载。

## 状态分类

每个 slot 记录：

- INGESTED
- REUSED_LOCAL
- NOT_FOUND
- FUTURE_WINDOW_NOT_STARTED
- REVIEW_REQUIRED
- BLOCKED
- INGEST_BLOCKED
- ERROR

`default publication search window has not started yet` -> FUTURE_WINDOW_NOT_STARTED，不视为系统失败。

P7 blocking > 0 -> INGEST_BLOCKED：保留 Registry/parsed 状态，但不得宣称已进入 P8 live catalog。

## 最终成功规则

PASS：
- 至少一个 requested slot 成功 ingest/reuse；
- 没有 BLOCKED / ERROR / INGEST_BLOCKED；
- NOT_FOUND / FUTURE_WINDOW_NOT_STARTED 只作为 gap。

PARTIAL：
- 至少一个 slot 成功；
- 同时存在 BLOCKED / ERROR / INGEST_BLOCKED。

FAIL：
- 没有任何 slot 成功；或
- 参数非法；或
- 运行环境/Dayu/CLI 不可用。

## 输出

至少输出：

- company_code_input
- market
- normalized_ticker
- requested_years
- attempted_slot_count
- ingested_count
- reused_count
- not_found_count
- future_not_started_count
- review_required_count
- blocked_count
- ingest_blocked_count
- error_count
- per-slot result
- P8 catalog publication status
- final status: PASS / PARTIAL / FAIL

## 安全与治理

- 不调用模型；
- 不调用外部 AI API；
- 只使用 FFDF 已有 CLI；
- 不改 Raw/P3/P4/P5/P6/P7 内容；
- 不执行 reset/clean/force push；
- 不提交 `00document/`、`01prompt/`。

## Optimization v2 — Status-First Complete-Slot Skip

在每个 `year x period` 调用 `ffdf ingest` 之前，必须先调用：

`ffdf status --market <market> --ticker <ticker> --year <year> --period <period>`

只有同时满足以下全部条件，才把该 slot 判定为：

`ALREADY_COMPLETE`

并完全跳过 `ffdf ingest`：

1. status 命令成功；
2. `local_document_status == RESOLVED`；
3. `document_sha256` 非空；
4. `raw_path` 非空；
5. `parsed_runs` 至少存在一个与当前 `document_sha256` 相同的记录；
6. 该匹配 parsed run 的 `blocking_issue_count == 0`；
7. `p8_catalog_registered == true`；
8. `p8_catalog_document.document_sha256 == document_sha256`。

Validation 可以是 PASS，也可以是 REVIEW_REQUIRED，只要 blocking=0 且已经进入 P8 live catalog，就属于完整入库。

只要上述任一条件不满足：

- 不得标记 ALREADY_COMPLETE；
- 继续执行现有 `ffdf ingest`；
- 由 ingest 的 acquire / parser / validation / catalog 逻辑决定后续状态。

这样可以避免已经完整入库的 filing 再次进入 P7 计算与 P8 upsert，同时仍然允许半成品、缺 catalog、缺 parsed run 或 blocking artifact 自动补齐。

### Summary changes

新增统计：

- `already_complete_count`
- per-slot `ALREADY_COMPLETE`

PASS / PARTIAL / FAIL 中，`ALREADY_COMPLETE` 与 `INGESTED` / `REUSED_LOCAL` 同样计为成功 slot。

### Safety

status-first 只做读取和完整性判断，不修改 Registry、Raw、P3-P8，不绕过既有 validation，也不把缺失状态伪装成成功。
