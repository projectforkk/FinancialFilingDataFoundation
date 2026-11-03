# 13 — P5 Table Reconstruction / Cross-page 实施计划

状态：**DESIGN BASELINE — P5 EXECUTION PLAN**

设计：
- `design/12-p5-table-reconstruction-design.md`

## P5-A — Baseline / Branch

1. main 必须为 P4 accepted closeout。
2. P5 design baseline 先提交 main。
3. 创建：
   `task/p5-table-reconstruction`
4. 使用独立 P5 development worktree。
5. clean worktree。
6. 不使用 destructive reset / clean。

Gate:
`P5_READY_FOR_DEVELOPMENT`

## P5-B — Models / Input Fingerprints

实现：
- ReconstructedTableArtifact
- reconstructed fragment contract
- row/cell structural roles
- table/group IDs
- P3/P4 input fingerprints
- corruption error reason codes

Gate:
focused model/fingerprint tests PASS。

## P5-C — Visual Row Reconstruction

实现：
- candidate-scoped word selection
- y-center row clustering
- deterministic word ordering
- row bbox
- source word refs
- stable row IDs

约束：
- 不能读取 candidate scope 之外的 words
- 不做 accounting semantics

Gate:
row clustering tests PASS。

## P5-D — Value Anchor / Cell Reconstruction

实现：
- numeric right-edge clustering
- value anchors
- LABEL / VALUE / UNASSIGNED structural cells
- deterministic cell text/bbox
- stable cell IDs
- quality signals

禁止：
- period semantic
- currency/unit semantic binding
- fact extraction

Gate:
cell reconstruction tests PASS。

## P5-E — Distributed-block Reconstruction

使用 P4 distributed candidates 验证：
- numeric blocks can form visual rows
- value anchors derived across blocks
- no dependence on P3 block grouping

Gate:
distributed synthetic tests PASS。

## P5-F — Cross-page Continuation Groups

实现：
- adjacent-page table matching
- normalized value-anchor compatibility
- bottom/top continuity
- deterministic chain grouping
- group IDs

只建立 fragment group，不 physically merge rows。

Gate:
continuation tests PASS。

## P5-G — Artifact Persistence / Reuse

实现：
- tables.jsonl
- table_groups.jsonl
- table_manifest.json
- UTF-8 no BOM
- atomic temp → final
- input fingerprint validation
- full identity/corruption guard

Gate:
artifact reuse/tamper tests PASS。

## P5-H — Determinism / Full Regression

验证：
- dual-root byte-identical table JSONL/group JSONL
- P0–P4 tests PASS
- no prior source/test changes
- no PDF open
- no OCR/Docling/Dayu/network/AI
- P3/P4 artifacts unchanged

## P5-I — Live CN/HK

使用 accepted P3/P4 live artifacts。

CN:
- fragments >0
- >=1 table with >=2 value columns
- pages 60–67 至少 2 页 reconstructed

HK:
- pages 124 / 126 / 133 each reconstructed
- each >=2 value columns
- each >=5 rows

Cross-page:
- combined CN/HK at least one continuation group
- 若事实不满足强 continuation 条件，STOP → design update；不得降低强条件制造 group

Performance:
- CN <=10s
- HK <=20s

## P5-J — Code Review

使用新的 detached worktree。

检查：
- P5 scope only
- IDs/fingerprints/corruption guard
- source word evidence
- candidate boundary containment
- no P6 semantics
- live structure guards
- deterministic artifacts
- performance
- prior phases unchanged

发现问题：
先更新设计。

Gate:
`P5_READY_FOR_ACCEPTANCE`

## P5-K — Acceptance Freeze

固定：
- exact candidate SHA
- P4 accepted baseline
- P3/P4 input roots
- CN/HK expected guards
- test commands/count
- performance thresholds
- reviewed candidate SHA

## P5-L — Independent Acceptance

新的 detached worktree。

必须独立验证：
- full suite
- prior-phase integrity
- deterministic dual-root
- row/cell IDs
- candidate containment
- tamper/fingerprint guards
- live CN/HK structure
- continuation group
- source/P3/P4 immutability
- no P6/heavy/network

Verdict:
PASS / FAIL / BLOCKED。

## P5-M — Closeout

仅 PASS：
- acceptance evidence
- merge accepted P5 → main
- verify main src/tests == frozen candidate
- full regression
- status P5_DONE
- authorize P6 design

## Issue Rule

任一 Gate：

```text
problem found
→ STOP
→ root cause
→ update design
→ commit design baseline
→ rerun affected gates
→ continue
```

禁止先改代码后补设计。
