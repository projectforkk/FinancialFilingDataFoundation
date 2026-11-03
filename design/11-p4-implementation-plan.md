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
- bbox aggregation
- score/signals
- no cell/row/column reconstruction

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
