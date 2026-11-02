# 11 — P3 Native Page / Section / FTS 实施计划

状态：**DESIGN BASELINE — P3 EXECUTION PLAN**

## P3-A Baseline
- main contains P2 closeout
- commit P3 design first
- create `task/p3-native-page-section`

## P3-B Models / Artifact IO
Implement page/block/span/section/artifact contracts, stable JSONL/JSON writers.

## P3-C Native Extraction
PyMuPDF only:
- preflight
- page geometry
- text / words / dict blocks/lines/spans
- images/drawings counts
- bbox validation
- deterministic block reading order

No OCR/Docling/table reconstruction.

## P3-D Section Engine
- global/body font statistics
- numbering rules
- repeated header/footer suppression
- heading score/signals
- deterministic hierarchy/page_end/section_id

## P3-E FTS5
- SQLite FTS5 page/section index
- parameterized query
- deterministic result ordering

## P3-F Unit / Integration
All tests from design/10.
P0-P2 regressions must PASS.

## P3-G Live CN/HK
Fresh artifact roots for accepted P2 raw files.
Record timings/page/section counts/FTS examples/SHA before-after.
Each <=30s.

## P3-H Code Review
Detached worktree; review contracts, determinism, no heavy path, live evidence.

## P3-I Acceptance Freeze
Freeze exact candidate, test commands, live raw paths/SHA, expected page counts observed in development.

## P3-J Independent Acceptance
Fresh detached worktree and fresh artifact roots.
Verdict PASS/FAIL/BLOCKED.

## P3-K Closeout
PASS only → merge main → verify src/tests equal frozen candidate → full regression → P3_DONE.

## P3 Issue Log

### P3-ISSUE-004 — 已发布 artifact reuse 缺少 completeness/corruption 校验

Pre-Code-Review 可恢复性审查发现：`load_native_document()` 初版只验证 `document.json`，如果外部删除 `pages.jsonl` / `sections.jsonl` / `search.sqlite`，同 SHA 下一次 parse 会直接返回一个不可用 artifact。

批准解决方案：
1. load/reuse 必须验证四个核心 artifact 文件都存在；
2. manifest schema/parser/source SHA 必须与目录/调用期望一致；
3. search.sqlite `metadata(document_sha256,schema_version)` 必须与 manifest 匹配；
4. 缺失/冲突统一抛 `ARTIFACT_INCOMPLETE_OR_CORRUPT`；
5. 不自动删除或覆盖损坏 final artifact，以保留审计现场；
6. 增加 missing-file / search-metadata mismatch tests；
7. 重新执行 P3-B/E/F/G/H。

### P3-ISSUE-003 — page FTS implementation 未使用设计规定的 external-content contract

Pre-Code-Review 对照 `design/10` 发现：设计要求 `page_content(page_no,text)` 作为 canonical page text table，并由 `page_fts` 使用 `content='page_content', content_rowid='page_no'`；初版实现却创建独立 `page_fts(page_no UNINDEXED,text)` 并重复保存正文。

虽然现有 page search tests 能通过，但这违反已批准 contract，并造成重复 page text storage。

批准解决方案：
1. `page_content` 保持 canonical page text；
2. `page_fts = fts5(text, content='page_content', content_rowid='page_no')`；
3. 索引写入使用 `rowid=page_no`；
4. 搜索通过 `page_fts.rowid -> page_content.page_no` join 返回正文；
5. 保持 query 参数化与 deterministic ordering；
6. 增加 DB reopen / external-content schema test；
7. 重新执行 P3-E/F/G/H。

### P3-ISSUE-002 — PyMuPDF DICT 默认 image payload 导致 HK native path 病理性变慢

P3-G 首次 HK live parse 超过 30s 且长期无 CPU-visible progress。逐页 A/B 确认：

- HK page 1 default DICT ≈ 1231.69 ms；text-only DICT ≈ 2.09 ms；
- page 20 default ≈ 466.96 ms；text-only ≈ 1.41 ms；
- page 32 default ≈ 392.13 ms；text-only ≈ 1.45 ms；
- page 34 default ≈ 425.28 ms；text-only ≈ 1.32 ms。

根因：`get_text("dict")` 默认包含 image payload，而 P3 仅需要 text span layout。另测 `get_cdrawings()` 代表页约 2.88–54.11 ms，可用于 drawing count。

批准解决方案：
1. P3 text layout 使用 `TEXTFLAGS_DICT & ~TEXT_PRESERVE_IMAGES`；
2. 同页构造一次 TextPage 并复用给 words/dict；
3. image count 独立 `get_images(full=True)`；
4. drawing count 使用 compact `get_cdrawings()`；
5. image-only page 继续明确 PAGE_TEXT_EMPTY；
6. 作废首轮 HK live performance 证据，修复后 fresh artifact root 重跑 P3-F/G；
7. 该修正不改变 parser version，因为原实现本来就丢弃 type!=0 image block，属于语义等价的性能修正。

### P3-ISSUE-001 — JSONL Unicode line separators break record boundaries

首次 CN live artifact 已成功抽取，但 evidence harness 用 `splitlines()` 读取 `pages.jsonl` 时遇到 `JSONDecodeError`。根因是原文含 Unicode line separator，`ensure_ascii=False` 原样保留，而 `splitlines()` 将其视为新行。

批准解决方案：
1. JSONL record separator 固定为 ASCII LF；
2. U+0085/U+2028/U+2029 在 JSON string 内强制 `\\uXXXX` escape；
3. 增加 line-safe JSONL unit test；
4. 作废首次 P3 live artifact，修复后 fresh root 重跑 P3-F/G；
5. 不改动源 PDF。

## Issue rule
Problem found → STOP → update design first → commit → fix → rerun.
