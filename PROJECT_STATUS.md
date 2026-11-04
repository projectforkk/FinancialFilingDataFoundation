# Project Status

## Repository

`projectforkk/FinancialFilingDataFoundation`

## Current state

**P9_DONE / P10_DESIGN_AUTHORIZED**

## Accepted baseline

- phase: `P9_DONE`
- frozen acceptance candidate: `926c665f5dd667765781630638c62239b267ceb7`
- reviewed production candidate: `66308627d1dd1f0af2f02ff3f18d3e91f33dcc8d`
- reviewed/evidence candidate: `e7822438c80964f29960c3dafa278a5ede8cdc44`
- final formal review verdict: `PASS`
- final formal review evidence: `development/74-p9-jr3-formal-rereview-result.md`
- acceptance verdict: `PASS`
- acceptance evidence: `acceptance/37-p9-acceptance-result.md`
- accepted merge commit: `58a1d2236b68a56fc66ddf8b97603e7232c87265`
- accepted_baseline_sha: `58a1d2236b68a56fc66ddf8b97603e7232c87265`
- acceptance focused P9: `73 passed`
- acceptance synthetic golden: `2 passed, 71 deselected`
- acceptance full unit: `308 passed`
- post-merge full regression: `308 passed in 23.74s`
- live CN/HK: `PASS`
- accepted base immutability: `23 / 23 files unchanged`
- blocker: `NONE`

## Phase history

### P0 — Native PDF Parsing Feasibility Probe

- status: `DONE / PASS`
- acceptance evidence: `acceptance/05-p0-acceptance-result.md`
- closeout: `edff06b2b1138b50d742e92ce8b8df628c6d2c61`

### P1 — Identity / Registry / Incremental Planner

- status: `DONE / PASS`
- acceptance evidence: `acceptance/08-p1-acceptance-result.md`
- frozen candidate: `3b382f4091a96a2dff40144253da42bf8de1fcc2`
- accepted merge: `1cb6e88be318c0a1424d74ee601c336075361cd6`

### P2 — Acquisition Provider

- status: `DONE / PASS`
- acceptance evidence: `acceptance/11-p2-acceptance-result.md`
- frozen candidate: `803fe3d09bb69a6b378c4e619de00fde95aa9456`
- reviewed production candidate: `881c80be1938a128448ea3ed0b4e2cb962f46018`
- accepted merge: `4add9fff36b61e2521e9c8d749cee829adb4ab6f`
- deterministic suite: `87 passed`
- live CN / HK: `PASS`
- Dayu pin: `2115c86d5a9027bb51cbbc8a4d0175080732e4e6`

### P3 — Native Page / Section / FTS

- status: `DONE / PASS`
- acceptance evidence: `acceptance/14-p3-acceptance-result.md`
- frozen candidate: `7b81c97e73448389e38cf9936a8af7dfe074d1e1`
- reviewed production candidate: `3c3536db0bdfdfbc5300004731b04d992930904f`
- full suite: `104 passed in 2.65s`
- CN fresh dual-root: `PASS`
- HK fresh dual-root: `PASS`
- accepted merge: `24cb4571a9d9f97b4b963d6339970c931d979c4d`

### P4 — Table Candidate Detection

- status: `DONE / PASS`
- acceptance evidence: `acceptance/17-p4-acceptance-result.md`
- frozen candidate: `647d6179bdde9e370185fea1d389f0087370faae`
- reviewed production candidate: `ea78b2f9adbf0ad6564146ba166da85d1085bf81`
- full suite: `133 passed`
- live CN / HK: `PASS`
- accepted merge: `97f2de24861347c97bf875e7b72899eb11ab56c2`

### P5 — Table Reconstruction / Cross-page

- status: `DONE / PASS`
- acceptance evidence: `acceptance/20-p5-acceptance-result.md`
- frozen candidate: `44ddd73d736f1da64bab38641091a8c6d55c9990`
- reviewed production candidate: `2c4bafd36b59defd4ff47eeb16713cbee64e739e`
- full suite: `156 passed`
- live CN / HK: `PASS`
- accepted merge: `8ff01cd3feed41c4b81aff88bce6502d50e8f32e`

### P6 — Raw Facts / Evidence

- status: `DONE / PASS`
- acceptance evidence: `acceptance/23-p6-acceptance-result.md`
- frozen candidate: `07cb4258e1f2083b7c930686b637acdd89b03d0a`
- reviewed candidate: `bb31515b4fc6ac09aea0aed0cf14262555a7398e`
- full suite: `189 passed`
- live CN/HK: `PASS`
- accepted merge: `d13b62778d123ba109c5f8ab2329d121d81b186b`

### P7 — Quality Gate / Validation

- status: `DONE / PASS`
- acceptance evidence: `acceptance/26-p7-acceptance-result.md`
- frozen candidate: `8edb68a885ebcd80a0bdc31567e7adcd0aea19fd`
- reviewed candidate: `0b1ffcec4fa4416724a6c505a9706eb41999bead`
- full suite: `213 passed`
- live CN/HK deterministic validation: `PASS`
- accepted merge: `5f314bab9d88fb16b4b46c662e0a9f1b8f1a9b13`

### P8 — Local MCP

- status: `DONE / PASS`
- acceptance evidence: `acceptance/33-p8-issue006-acceptance-result.md`
- frozen candidate: `31525235a44c8576d22fba542438b491e15e653b`
- reviewed candidate: `537ebbd17454f80c8838f58abbbd02d5994f8716`
- full suite: `235 passed`
- official MCP protocol: `2026-07-28`
- exact tools: `11 / 11 PASS`
- live CN/HK MCP queries: `PASS`
- runtime package lock: `30 / 30 MATCH`
- runtime lock byte reproducibility: `PASS`
- P8-ISSUE-006 dual-runtime test boundary: `PASS`
- accepted merge: `ee934ad05812c69b79f76db43e62cfd4050efb8e`

### P9 — Codex Review Overlay

- status: `DONE / PASS`
- final production candidate: `66308627d1dd1f0af2f02ff3f18d3e91f33dcc8d`
- final reviewed/evidence candidate: `e7822438c80964f29960c3dafa278a5ede8cdc44`
- final formal review: `development/74-p9-jr3-formal-rereview-result.md` = `PASS`
- frozen acceptance candidate: `926c665f5dd667765781630638c62239b267ceb7`
- acceptance evidence: `acceptance/37-p9-acceptance-result.md`
- acceptance focused: `73 passed`
- acceptance synthetic: `2 passed, 71 deselected`
- acceptance full unit: `308 passed`
- CN 600519 FY2024 live acceptance: `PASS`
- HK 00700 FY2024 live acceptance: `PASS`
- base immutability: `23 / 23 files unchanged`
- post-merge full regression: `308 passed in 23.74s`
- accepted merge: `58a1d2236b68a56fc66ddf8b97603e7232c87265`

## Approved next phase

**P10 — Codex Dynamic Research Integration**

Status:

`DESIGN AUTHORIZED / PRODUCTION NOT STARTED`

Authorization basis:

- P9 Independent Acceptance: `PASS`
- acceptance evidence: `acceptance/37-p9-acceptance-result.md`
- accepted P9 merge: `58a1d2236b68a56fc66ddf8b97603e7232c87265`
- post-merge full regression: `308 passed in 23.74s`
- P9 blocker: `NONE`

Authorized now:

- read the latest accepted `main` design and P8/P9 contracts；
- prepare P10 detailed design / implementation plan / acceptance instruction；
- reconcile any prior cross-phase research-consumption / visual / semantic design drafts against the accepted P9 baseline before adopting them；
- commit/push a new P10 design baseline before any P10 production implementation。

Not authorized yet:

- P10 production code；
- P11 production；
- Research MCP production；
- Semantic Resolver production；
- any change that weakens P8 read-only or P9 durable-review boundaries。

## Project directory consolidation

- verdict: `PASS`
- design: `design/15-project-directory-management.md`
- evidence: `development/34-directory-consolidation-evidence.md`
- canonical root: `D:\Codex\FinancialFilingDataFoundation`
- all linked worktrees inside project root: `PASS`
- Dayu source inside project root: `PASS`
- Dayu runtime inside project root: `PASS`
- runtime lock: `runtime-locks/dayu-2115c86-py312-win-amd64.lock.txt`
- old/new accepted package snapshot: `MATCH`
- full regression after migration: `156 passed`

## Current runtime boundaries

### FFDF main runtime

`D:\Codex\FinancialFilingDataFoundation\.venv`

- Python 3.14.9 ARM64
- PyMuPDF 1.28.2
- Dayu absent
- Docling absent
- Torch absent

### Dayu acquisition runtime

`D:\Codex\FinancialFilingDataFoundation\runtimes\ffdf-dayu-2115c86\.venv`

- Python 3.12.14 AMD64
- dayu-agent 0.1.4
- pinned source commit: `2115c86d5a9027bb51cbbc8a4d0175080732e4e6`

The P2 Dayu runtime is isolated from the FFDF main runtime.

### P8 MCP runtime

`D:\Codex\FinancialFilingDataFoundation\runtimes\ffdf-mcp-2.3.0\.venv`

- Python 3.12.14 AMD64
- mcp 2.3.0
- mcp-types 2.3.0
- PyMuPDF 1.28.2
- tracked lock: `runtime-locks/mcp-2.3.0-py312-win-amd64.lock.txt`
- lock SHA256: `8e958b8abcfD9b2de829451ffc253932fa26bb473f73837484b75b1019f092ec`
- `.gitattributes`: `runtime-locks/*.txt text eol=lf`
- official protocol acceptance: `2026-07-28`
- transport: `stdio only`

The P8 MCP runtime is isolated from the FFDF main runtime. MCP AI API calls remain forbidden.

## Accepted live source identities

### CN sample

- market: `CN`
- ticker: `600519`
- period: `FY2024`
- provider: `cninfo`
- source id: `1222993920`
- SHA256: `5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30`
- size: `3,626,217`

### HK sample

- market: `HK`
- ticker: `00700`
- period: `FY2024`
- provider: `hkexnews`
- source id: `11618398`
- SHA256: `70f529984a87ef7f46d9e1db26bb9ef27eef9c01d29c59aabf69e557b479a6a0`
- size: `5,241,364`

## Governance rules

1. GitHub is the truth source.
2. Every phase follows:
   `DESIGN → DEVELOPMENT → CODE REVIEW → INDEPENDENT ACCEPTANCE → DONE`.
3. If a problem is found and a solution is identified:
   `STOP → update design → commit design baseline → rerun affected gates → continue`.
4. Do not use destructive reset / clean / force push to hide state.
5. Original source documents are immutable.
6. MCP AI API calls are forbidden.
7. Tracked Markdown / JSON governance artifacts use `UTF-8 without BOM`.
8. Phase code enters the accepted baseline only after Independent Acceptance PASS.
9. P8 may expose only deterministic local MCP tools; MCP AI API calls remain FORBIDDEN and P9 Review Overlay remains separate.
10. Design index: `design/00-design-management-index.md`.
11. Directory governance: `design/15-project-directory-management.md`.
12. All FFDF-owned dependencies/runtimes/worktrees/workspace/data are managed under `D:\Codex\FinancialFilingDataFoundation`.

## Roadmap

- P0 — Native PDF Parsing Feasibility Probe: `DONE`
- P1 — Identity / Registry / Incremental Planner: `DONE`
- P2 — Acquisition Provider: `DONE`
- P3 — Native Page / Section / FTS: `DONE`
- P4 — Table Candidate Detection: `DONE`
- P5 — Table Reconstruction / Cross-page: `DONE`
- P6 — Raw Facts / Evidence: `DONE`
- P7 — Quality Gate / Validation: `DONE`
- P8 — Local MCP: `DONE`
- P9 — Codex Review Overlay: `DONE`
- P10 — Codex Dynamic Research Integration: `DESIGN AUTHORIZED / PRODUCTION NOT STARTED`
- P11 — US SEC Provider: `NOT STARTED`
