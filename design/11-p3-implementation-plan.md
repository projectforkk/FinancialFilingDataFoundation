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

## Issue rule
Problem found → STOP → update design first → commit → fix → rerun.
