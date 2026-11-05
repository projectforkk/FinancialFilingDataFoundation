# FFDF MCP Research Review Interface v1

## 1. 目标

Research Review v1 是 FFDF MCP 的 additive extension，用于研究前全期间质量监测、P9 resolved state 复用、结构化证据定位，以及在必要时读取原始 PDF 页面/表格图像。

它不改变 P8_RAW_V1 的 11-tool logical contract，也不修改 P9 v1 schema/action。

## 2. Runtime profile

### RESEARCH_FALLBACK

默认 profile，适用于普通公司研究：

- 可查询 P8 / Report-Safe / Review State / Resolved Fact；
- 可定位证据；
- 可 render trusted original PDF；
- 禁止 prepare / submit / materialize P9。

### QUALITY_REVIEW

显式数据库质量完善 profile：

- 包含全部 read/render；
- 可调用现有 P9 v1 prepare / submit / materialize；
- 仍不允许 SET_VALUE；
- Raw extraction defect 必须返回 Parser/Extraction 层。

启动参数：

    --research-review-profile RESEARCH_FALLBACK
    --review-root workspace/p9-live-review
    --registry workspace/ingest/registry.sqlite
    --trusted-raw-root workspace/ingest/raw-store

默认值与上面一致，因此现有只传 project-root/catalog 的配置仍可启动。

## 3. 研究前 Preflight

推荐研究流程：company report context → 全研究期间 filing coverage → 每份 document review state → ResearchRequirementSet coverage → minimal Repair Queue → 必要的 QUALITY_REVIEW / upstream fix → Preflight re-run → research_ready → 正式研究。

Preflight 不要求 database_fully_reviewed 才能研究。与本次研究无关的 REVIEW_REQUIRED 不自动阻断 research_ready。

## 4. Resolved query

- ffdf_get_review_state
- ffdf_get_resolved_fact
- ffdf_list_resolved_facts
- ffdf_list_review_tasks
- ffdf_get_review_context

RawFact 始终保留；effective value 不允许被 P9 改写。P9 v1 只影响其现有允许的 period/unit/scope/table classification/attestation 语义。

## 5. Evidence locator

ffdf_locate_evidence 使用 P3 FTS + literal scan，并返回相关页面、同页 P5 tables / P6 facts 及 recommended visual target；它不创建不存在的 RawFact。

PDF 中明确披露但 P6 没有事实时，路由为 P6_MISSING_FACT_CANDIDATE / upstream fix。

## 6. PDF Visual

- ffdf_render_table
- ffdf_render_table_group
- ffdf_render_page

安全边界：caller 不能传 filesystem path 或任意 bbox；PDF 来源必须通过 Registry + trusted raw-store + SHA256 + page_count 验证。返回真实 MCP ImageContent(image/png)。NORMAL=144 DPI，HIGH_DETAIL=216 DPI，超出像素预算时 deterministic tiling，截图默认不落盘。

VisualRef 不是 P9 v1 evidence type。

## 7. Visual Decision

只允许 EXPLICIT_AND_ANCHORABLE、EXPLICIT_VISUAL_ONLY、RAW_EXTRACTION_DEFECT、AMBIGUOUS 四类。只有第一类且存在合法 P5/P6 anchor、P9 action 支持时，才可能在 QUALITY_REVIEW 中 durable submit。RAW numeric mismatch 永远不能通过 P9 改值。

## 8. Write-through

- ffdf_prepare_review_overlay
- ffdf_submit_review_resolution
- ffdf_materialize_resolved_view

submit 需要 expected_base_validation_report_sha256 与 expected_overlay_set_hash_before；submit 后必须显式 materialize，再重新读取 review state。

## 9. Codex / reviewer runtime constraint

当前用户授权要求：若调用 Codex，只允许 Luna 5.6。

本接口本身不调用网络或模型；deterministic correctness 不依赖 Codex。若上层使用 Codex 做视觉 reviewer，只能使用 Luna 5.6，模型版本只记录 telemetry，不成为 P9 semantic truth。

## 10. 已验证 Golden

605117 2021–2026：23 份 periodic filings；2025FY 新能源行业 direct row；KAM pages 105/106；trusted PDF table ImageContent；default Research profile write blocked。

002371 2026Q3：10 pages / 10 tables / 315 facts / 315 evidence；quarterly table 四列结构需要 layout context，不能靠 raw cell role 猜语义。

P9 reuse：legal SET_PERIOD + SET_UNIT → materialize PASS → subsequent research returns COMPLETE_REVIEWED，无需重复 PDF。