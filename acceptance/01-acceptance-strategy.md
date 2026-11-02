# 01 — Acceptance Strategy

## 1. 独立验收原则

验收执行者只能给：
- PASS
- FAIL
- BLOCKED

不得在验收过程中修改 production code、tests、config 来使任务通过。

## 2. Evidence

每次验收至少保存：
- repository / branch / commit SHA
- design baseline SHA
- commands
- stdout/stderr 摘要
- machine-readable result
- test result
- timing
- environment

## 3. Functional Acceptance

针对最终系统：
- 数据存在 → REUSE
- 数据缺失、本地文件存在 → LOCAL
- 两者都无 → DOWNLOAD
- parse 结果 evidence 完整
- blocking issue 不得 DATA_READY
- repeated run 幂等

## 4. Performance Acceptance

所有 PDF 性能必须分阶段计时。
禁止只写“约 X 秒”而无原始结果。

## 5. Parser Accuracy Acceptance

Golden 样本核对：
- page count
- statement pages
- table title
- unit
- year columns
- scope
- selected values
- evidence location

最终 resolved golden key values 目标 100%。

## 6. Token / Codex Acceptance

MCP 本身必须 0 external AI API。
记录：
- local_accept_pages
- text_review_pages
- vision_review_pages
- model_exposure_ratio

不得以 token 节省为理由降低 golden accuracy。
