# 48 — P9 Development Instruction

任务：**Codex Review Overlay Infrastructure**

必须遵守：
- `design/00-design-management-index.md`
- `design/15-project-directory-management.md`
- `design/22-p9-review-overlay-design.md`
- `design/23-p9-implementation-plan.md`
- accepted P8 baseline / catalog / read-only boundary

## Scope

只实现：

- P7 REVIEW issue → deterministic review queue；
- P5/P6 evidence-grounded resolution contract；
- append-only immutable resolution store；
- supersession/conflict graph；
- resolved facts with `effective_*` fields；
- overlay-aware re-validation；
- resolved ParsedDataRecord helper（no Registry write）；
- deterministic local CLI。

## Hard prohibitions

禁止：

- remote AI / Codex API / OpenAI API；
- external MCP SDK dependency；
- P8 MCP tool mutation；
- source PDF open；
- OCR / Docling；
- acquisition；
- changing raw_value / parsed_numeric_value；
- changing raw_metric_name；
- canonical metric mapping；
- overwriting P3/P5/P6/P7；
- Registry mutation；
- P10 Dynamic Research Integration implementation；
- P11 SEC provider。

## Recovery boundary — P9-ISSUE-004

当前 GitHub branch 只保存设计/治理 baseline；handoff 记录的 P9-B–F production/tests 仍位于 WorkHome active worktree 且尚未提交。

在 WorkHome 恢复前禁止：
- 从 GitHub 创建替代 `review/*.py` / `tests/unit/review/test_review_overlay.py`；
- 删除、覆盖或重建本地未提交 candidate；
- 将 handoff-reported test result 误写成 accepted baseline。

恢复后必须先核验本地 Git / untracked state，再安全同步 design-only commits。现场一致后从 P9-G CLI 继续。

## Reviewer boundary

P9 engine only validates/persists a reviewer submission.

`reviewer_type=CODEX` is metadata only.

Actual Codex reasoning/orchestration belongs to P10.

## Inputs

Canonical live artifact discovery uses accepted P8 catalog:

`workspace/mcp/p8-acceptance-catalog.json`

P9 code must reuse its project-root containment rules without importing external MCP SDK.

## Live expectations

CN 600519 FY2024:
- base P7 REVIEW tasks = 1
- reason = RAW_PERIOD_COVERAGE_LOW
- at least one evidence-grounded period overlay during development/live verification
- do not force global PASS unless evidence really covers threshold

HK 00700 FY2024:
- base P7 REVIEW tasks = 4
- reasons:
  - CORE_STATEMENT_COVERAGE_LOW
  - RAW_PERIOD_COVERAGE_LOW
  - RAW_UNIT_AMBIGUOUS
  - RAW_UNIT_COVERAGE_LOW
- no forced dismissal

Synthetic golden must prove complete REVIEW_REQUIRED → PASS flow.

## Development evidence

必须记录：

- design baseline/amendments；
- production commit；
- queue schema/hash；
- resolution schema/IDs；
- supersession/conflict tests；
- synthetic resolved PASS；
- CN/HK queue counts；
- live resolution evidence refs/pages；
- overlay_set_hash；
- resolved snapshot hashes；
- base artifact immutability；
- full regression；
- no-network/no-AI/no-PDF-open/no-Registry-write checks。

发现问题：

**先更新 design/22 / design/23，再改 production code。**
