# 17 — P6 Raw Facts / Evidence 实施计划

状态：**DESIGN BASELINE — P6 EXECUTION PLAN**

详细设计：
`design/16-p6-raw-facts-evidence-design.md`

## P6-A — Design Baseline / Branch
- commit P6 design/plan/instruction/acceptance
- main clean
- create `task/p6-raw-facts-evidence`
- worktree: `worktrees/active/p6-raw-facts-evidence`

Gate: `P6_READY_FOR_DEVELOPMENT`

## P6-B — Models / Numeric Parser
实现：
- RawFactArtifact
- error model
- Decimal numeric parser
- stable ID helpers

Gate:
focused tests PASS.

## P6-C — Evidence Index / Validation
实现：
- P3 word index
- P5 cell/source ref validation
- bbox union
- evidence refs

Gate:
invalid source ref blocked.

## P6-D — Fact Extraction
实现：
- row eligibility
- label assembly
- multi-value fact generation
- group mapping
- period/unit/scope explicit-only extraction
- warning aggregates

Gate:
focused extraction tests PASS.

## P6-E — Artifact Persistence / Reuse
实现：
- raw_facts.jsonl
- evidence.jsonl
- fact_manifest.json
- input fingerprints
- temp→final atomicity
- reuse
- semantic equality tamper guard

Gate:
artifact/tamper tests PASS.

## P6-F — Full Regression
- P0–P5 tests
- P6 tests
- compile
- diff check
- forbidden imports
- no PDF open

Gate:
full deterministic suite PASS.

## P6-G — Live CN/HK
使用 accepted P3/P5 artifacts。

CN:
- 600519 FY2024
- pages 60–67 fact coverage

HK:
- 00700 FY2024
- pages 124/126/133 fact coverage

要求 dual-root byte identity + immutability + performance.

## P6-H — Code Review
project-contained isolated worktree：
`worktrees/review/p6-<sha>`

检查：
- exact design
- prior phase zero diff
- fact/evidence semantics
- numeric Decimal
- no canonicalization
- tamper guard
- live results

## P6-I — Acceptance Freeze
固定：
- design baseline SHA
- production candidate SHA
- review commit
- accepted P5 baseline
- live artifact roots
- expected counts/ranges
- exact commands

## P6-J — Independent Acceptance
worktree：
`worktrees/acceptance/p6-<sha>`

verdict：
PASS / FAIL / BLOCKED

## P6-K — Closeout
PASS 后：
- evidence commit
- merge main
- main regression
- PROJECT_STATUS -> P6_DONE
- authorize P7 design

## Issue Rule
发现问题先更新 design/16 + 本计划，再继续代码。
