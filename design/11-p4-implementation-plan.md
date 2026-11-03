# 11 — P4 Table Candidate Detection 实施计划

状态：**DESIGN BASELINE — P4 EXECUTION PLAN**

设计：`design/10-p4-table-candidate-design.md`

## P4-A — Baseline / Branch
- main = P3 accepted baseline
- commit P4 design baseline
- create `task/p4-table-candidate-detection`
- clean worktree

## P4-B — Models / Token Signals
实现：
- TableCandidateArtifact
- TableCandidate
- deterministic candidate ID
- numeric token classifier
- keyword / TOC / spacing signals

Gate：focused unit tests PASS。

## P4-C — Region Detector
实现：
- load P3 pages/sections
- block seed detection
- adjacent seed grouping
- distributed-block page fallback
- bbox aggregation
- score/signals
- no cell/row/column reconstruction

### P4-ISSUE-002 — Candidate artifact identity integrity

P4-G Code Review 发现：初版 loader 仅检查 candidate_id 非空/唯一，没有根据 page/bbox/block_nos 重算 ID，也没有验证 page upper bound / bbox ordering。JSONL 若被修改但保留旧 ID，可能错误通过 reuse validation。

Approved fix:
- manifest 必须持有 page_count；
- validate page range；
- validate finite ordered bbox；
- validate non-empty integer block_nos；
- recompute candidate_id and require exact match；
- add tampered bbox/page/id regression tests；
- rerun P4-D/E/G。

### P4-ISSUE-001 — HK distributed-block table layout

P3 accepted HK artifact shows major statements split numeric values across many independent blocks. Initial block-local detector returned only 2 candidates and missed known financial statement pages 124/126/133.

Approved fix:
- add page-level numeric-bearing-block fallback;
- output only candidate bbox/block references/signals;
- no reconstruction semantics;
- add synthetic regression test;
- require HK pages 124/126/133 in live recall guard.

Gate：detector tests PASS。

## P4-D — Artifact Persistence
实现：
- candidates.jsonl
- candidate_manifest.json
- UTF-8 no BOM
- atomic temp-dir → final
- reuse validation
- corruption guard

Gate：artifact tests PASS。

## P4-E — Determinism / Regression
验证：
- byte-identical rerun
- P0–P3 full regression
- no PDF open
- no OCR/Docling/network/AI
- source/P3 artifact unchanged

## P4-F — Live CN/HK
使用已验收 P3 live artifacts：
- CN 600519 FY2024
- HK 00700 FY2024

记录：
- candidate count
- top candidate pages/scores/signals
- runtime
- deterministic dual-root equality

## P4-G — Code Review
isolated detached worktree。
发现问题先设计后代码。

## P4-H — Acceptance Freeze
固定 candidate SHA、live artifact roots、expected counts/ranges、commands。

## P4-I — Independent Acceptance
最终 verdict：PASS / FAIL / BLOCKED。

## P4-J — Closeout
PASS 后：
- acceptance evidence
- merge main
- main regression
- P4_DONE
- authorize P5 design

## Issue Rule
problem → STOP → design update → commit → rerun affected gates → continue。
