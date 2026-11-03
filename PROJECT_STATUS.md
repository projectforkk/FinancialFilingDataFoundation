# Project Status

## Repository

`projectforkk/FinancialFilingDataFoundation`

## Current state

**P6_DONE / P7_IN_REVIEW**

## Accepted baseline

- phase: `P6_DONE`
- frozen acceptance candidate: `07cb4258e1f2083b7c930686b637acdd89b03d0a`
- reviewed production candidate: `bb31515b4fc6ac09aea0aed0cf14262555a7398e`
- acceptance verdict: `PASS`
- acceptance evidence: `acceptance/23-p6-acceptance-result.md`
- accepted merge commit: `d13b62778d123ba109c5f8ab2329d121d81b186b`
- accepted_baseline_sha: `d13b62778d123ba109c5f8ab2329d121d81b186b`
- full regression: `189 passed`

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

## Approved next phase

**P7 — Quality Gate / Validation**

Status:

`DEVELOPMENT COMPLETE / CODE REVIEW PENDING`

Planned branch:

`task/p7-quality-validation`

P6 Independent Acceptance:

- verdict: `PASS`
- evidence: `acceptance/23-p6-acceptance-result.md`
- frozen candidate: `07cb4258e1f2083b7c930686b637acdd89b03d0a`
- full suite: `189 passed`
- live CN/HK: `PASS`
- blocker: `NONE`

P7 must not start production implementation until its detailed design and execution plan are committed.

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
9. P7 may implement only deterministic Quality Gate / Validation; P8 Local MCP remains separate.
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
- P7 — Quality Gate / Validation: `DESIGN AUTHORIZED`
- P8 — Local MCP: `NOT STARTED`
- P9 — Codex Review Overlay: `NOT STARTED`
- P10 — Codex Skill: `NOT STARTED`
- P11 — US SEC Provider: `NOT STARTED`
