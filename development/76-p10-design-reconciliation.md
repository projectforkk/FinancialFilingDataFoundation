# 76 — P10 Design Reconciliation Record

Status: **DESIGN REVIEW COMPLETE — NO PRODUCTION AUTHORIZATION IN THIS RECORD**

Phase:
`P10 — Codex Dynamic Research Integration`

## 1. Accepted starting point

P10 design worktree starts exactly from:

`main@e9b30626f2b88ac5527d42bd76d0b682efbeef0e`

P9 accepted merge:

`58a1d2236b68a56fc66ddf8b97603e7232c87265`

P9 acceptance:

`acceptance/37-p9-acceptance-result.md = PASS`

## 2. Prior design branch inspected

Prior branch:

`origin/design/research-consumption-visual-semantic`

Common ancestor with current main:

`3999422285950ec9f61b280454f57c695647f8c8`

Therefore its PROJECT_STATUS/design index/master edits predate the final P9 corrective reviews and acceptance and are not reusable as current governance truth.

No branch merge was performed.

Only the two design drafts were extracted as design inputs:

### design/28 draft

`design/28-ffdf-research-consumption-semantic-architecture.md`

Extracted draft SHA256:

`E4D36E3BB2DA0DAE7BFC3A56C04E446302D234816E7FA9D8FC6031CB7C4A26D9`

### design/29 draft

`design/29-research-mcp-visual-resolved-query-detailed-design.md`

Extracted draft SHA256:

`59584E76414E1157477886215467B450D8A849B3A33F57D91B8D9DADCCB765CD`

Extraction copies were kept only under project-root ignored workspace:

`workspace/scratch/p10-design-inputs/`

## 3. Reconciliation decisions

### R1 — P10 core does not depend on Research MCP

Old draft design/29 assumed Research MCP fallback would be implemented before P10 live research.

Final P9 closeout explicitly authorizes P10 DESIGN only and keeps Research MCP production closed.

Decision:

- P10 v1 uses accepted P8/P9 only；
- structured-sufficient research proceeds；
- structured-insufficient visual-required case returns `P10_VISUAL_CAPABILITY_REQUIRED`；
- no visual tool is implemented inside P10 v1。

### R2 — Research MCP remains future additive

design/29 is preserved as a future reference design.

Its production gates R-B onward remain closed until a later explicit design-owner authorization.

Future accepted Research MCP may change P10 capability manifest from:

`PDF_VISUAL_EVIDENCE = UNAVAILABLE`

to AVAILABLE without changing P8/P9 raw/history semantics。

### R3 — Semantic Resolver remains future deterministic layer

design/28 is preserved as long-term architecture.

P10 v1 does not implement:

- Header Graph；
- Semantic Artifact；
- Rule Registry；
- semantic readiness engine。

Codex run-local reasoning must never auto-promote itself into a deterministic parser rule。

### R4 — P9 v1 is accepted history

Draft wording that treated P9 as “acceptance in progress” is superseded.

Current accepted P9 identity remains:

`58a1d2236b68a56fc66ddf8b97603e7232c87265`

P10/design28/design29 cannot retroactively change P9 semantics。

### R5 — REVIEW_REQUIRED remains usable for current research

Retained rule:

`REVIEW_REQUIRED != DATA_UNUSABLE`

P10 may consume raw/evidence/table/page text and relevant durable P9 decisions while honestly preserving document reuse state。

### R6 — No fixed Skill

P10 does not revive the historical “P10 Codex Skill” route.

Runtime research specification remains the primary business-rule source.

## 4. New P10 design outputs

- `design/24-p10-codex-dynamic-research-integration-design.md`
- `design/25-p10-implementation-plan.md`
- `acceptance/38-p10-acceptance-instruction.md`
- reconciled `design/28`
- reconciled `design/29`

## 5. Production boundary

This record authorizes no production changes.

P10 production remains blocked until:

- design baseline is internally consistent；
- `git diff --check` PASS；
- UTF-8/no-BOM PASS；
- design baseline committed/pushed to GitHub；
- a subsequent P10 development instruction explicitly authorizes the first development gate。
