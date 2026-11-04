# Project Status

## Repository

`projectforkk/FinancialFilingDataFoundation`

## Current state

**P9_DONE / P10_DESIGN_READY**

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

### P10 — Codex Dynamic Research Integration

- status: `DESIGN READY / PRODUCTION NOT STARTED`
- branch: `design/p10-dynamic-research-integration`
- starting main: `e9b30626f2b88ac5527d42bd76d0b682efbeef0e`
- detailed design: `design/24-p10-codex-dynamic-research-integration-design.md`
- implementation plan: `design/25-p10-implementation-plan.md`
- acceptance baseline: `acceptance/38-p10-acceptance-instruction.md`
- reconciliation: `development/76-p10-design-reconciliation.md`
- design/28: future semantic reference / implementation not authorized
- design/29: future Research MCP reference / production not authorized
- production changes: `NONE`

## Approved next phase

**P10-N — Independent Acceptance**

Status:

`AUTHORIZED — P10-N INDEPENDENT ACCEPTANCE ONLY / EXACT CANDIDATE 183ca5dc...`

P10-C is closed:

- production candidate `35553df23f58a7f539b7390f98c7f154e42c817e`;
- detached review `development/86-p10-c-detached-code-review-result.md = PASS`.

P10-D is closed:

- amended design baseline `ba962aef818d7a31731637a5cfef1f57020a7d1d`;
- final production/test candidate `c8b4041c2d06e1d601707ca765ddd9e817f0dfc9`;
- development evidence `development/89-p10-d-context-evidence.md = PASS`;
- detached review result `development/91-p10-d-detached-code-review-result.md = PASS`;
- review result commit `109af3057942db62d80e8a39d0f18f68d0321fd8`.

P10-E is closed:

- amended design baseline `d6b34d84d1eeae6b0f2009895a14c5956217a18f`;
- production candidate `802a395247e490a83acaef744c1641188fbf704e`;
- development evidence `development/94-p10-e-provenance-evidence.md = PASS`;
- detached review instruction `development/95-p10-e-code-review-instruction.md`;
- detached review result `development/96-p10-e-detached-code-review-result.md = PASS`;
- review result commit `af7295d740ecadeb9c17705c1e1048f3f742a8e6`.

P10-F pre-implementation review found `P10-ISSUE-005` before any CLI production code existed.

Stop record:

`development/97-p10-f-preimplementation-design-stop.md`

Current P10-F design baseline:

`860e628ecf9f804734c9d343b3f2a9894928c9e9`

Development authorization:

`development/98-p10-f-cli-reauthorization.md`

P10-F production candidate:

`d8e7d81b4bb5a4f06cead9eba0e2d09884094676`

Development evidence:

`development/99-p10-f-cli-evidence.md = PASS`

Evidence commit:

`fad7f84`

Detached review instruction:

`development/100-p10-f-code-review-instruction.md`

Detached review result:

`development/101-p10-f-detached-code-review-result.md = PASS`

Review result commit:

`5b54748`

P10-F is closed.

P10-G authorization:

`development/102-p10-g-integration-instruction-authorization.md`

P10-G candidate:

`3a805a8f333ac20770d6aec1c8285d93993d18fc`

Integration artifact:

`integration/p10/FFDF_RESEARCH_INTEGRATION.md`

Artifact SHA256:

`ef10406c9957f7a68a9af001c913deef0a057e166100a2d852c0c8fcd2c46296`

Development evidence:

`development/103-p10-g-integration-instruction-evidence.md = PASS`

Evidence commit:

`241055f`

Detached documentation review instruction:

`development/104-p10-g-documentation-review-instruction.md`

Detached review stop:

`development/105-p10-g-detached-review-stop.md`

P10-ISSUE-006:

- same exact Git candidate produced LF active-worktree bytes and CRLF fresh-detached bytes under `core.autocrlf=true`;
- candidate Git blob itself is LF and has SHA256 `ef10406c9957f7a68a9af001c913deef0a057e166100a2d852c0c8fcd2c46296`;
- worktree-byte SHA is therefore not the cross-worktree identity;
- amended contract uses exact candidate Git blob bytes as P10-G artifact identity.

Current P10-G amended design baseline:

`d896173`

Review rerun authorization:

`development/106-p10-g-review-reauthorization.md`

The amended P10-F baseline freezes:

- exact four CLI argv contracts;
- stdin-only JSON request transport;
- 16 MiB request limit;
- exact request schemas;
- project-relative catalog/review-root inputs;
- exact canonical success/error envelopes;
- exact CLI reason codes and exit codes;
- spec-first error precedence;
- deterministic context rebuild for validate-ledger;
- no request-file browse, implicit writes, network/AI/subprocess/SQL, P8 business proxy, or P9 mutation.

P10-G detached review rerun is PASS and the gate is closed.

Detached review result:

`development/107-p10-g-detached-review-result.md = PASS`

P10-H validation authorization:

`development/108-p10-h-full-regression-authorization.md`

P10-H evidence:

`development/109-p10-h-full-regression-scope-evidence.md = PASS`

P10-H is closed.

P10-I authorization:

`development/110-p10-i-dynamic-spec-authorization.md`

P10-I evidence:

`development/111-p10-i-dynamic-spec-evidence.md = PASS`

P10-I is closed.

P10-J live-run authorization:

`development/112-p10-j-live-run-authorization.md`

P10-J stopped after accepted P9 rejected a relocated/copy of existing review state:

`development/113-p10-j-live-run-stop.md`

P10-ISSUE-007:

- accepted P9 review manifest binds the project-relative `review_dir`；
- a byte-for-byte copied review store at another path is intentionally invalid；
- isolated P10 review roots must be constructed at their final path with accepted P9 `prepare`；
- only supported/evidence-grounded actions required by the frozen spec may be replayed；
- the isolated root must use its newly generated resolution/snapshot identity；
- source/live P9 state and P8 raw values remain immutable.

P10-J amended design baseline:

`668269e`

P10-J rerun authorization:

`development/114-p10-j-live-run-reauthorization.md`

P10-J live-run evidence:

`development/115-p10-j-live-research-evidence.md = PASS / COMPLETE`

P10-J is closed.

P10-K authorization:

`development/116-p10-k-negative-gates-authorization.md`

P10-K evidence:

`development/117-p10-k-negative-gates-evidence.md = PASS`

P10-K is closed.

P10-L formal review authorization:

`development/118-p10-l-formal-review-authorization.md`

P10-L formal review result:

`development/119-p10-l-formal-code-review-result.md = PASS`

P10-L is closed.

P10-M acceptance-freeze authorization:

`development/120-p10-m-acceptance-freeze-authorization.md`

P10-M freeze evidence:

`development/121-p10-m-acceptance-freeze-evidence.md = PASS`

Frozen package:

- `acceptance/39-p10-final-acceptance-freeze.md`
- `acceptance/p10_independent_acceptance_harness.py`
- `acceptance/p10-base-immutability-manifest.json`
- `acceptance/p10-fixtures/**`

Core design and production remain frozen.

Historical invalid freeze attempt:

`42e39c971a360ca4e0ee09761221cc8da7ddbaa9`

Stop record:

`development/122-p10-m-freeze-stop.md`

Reason: staged `git diff --cached --check` found trailing whitespace in `acceptance/39`, but PowerShell continued to commit/push. This commit is ineligible for P10-N and remains historical evidence.

Corrected re-freeze evidence:

`development/123-p10-m-refreeze-evidence.md = PASS`

Corrected `acceptance/39` SHA256:

`92889cc508c8d62e3fa8f36044fdde8dd81131970df54e615b1967b936603b94`

Corrected P10-M re-freeze evidence:

`development/123-p10-m-refreeze-evidence.md = PASS`

Actual eligible corrected P10-M re-freeze commit:

`4d1ab46f11d1d7b88934309ce32319e2200f0d8f`

The historical SHA recorded later as `56cbe185e97e6e07dd354e03b98942d87f8e5787` does not exist in Git and is invalid.

P10-M remains closed on the actual corrected candidate above.

Historical invalid P10-N authorization:

`development/124-p10-n-independent-acceptance-authorization.md`

Historical invalid closeout authorization:

`development/125-p10-closeout-authorization.md`

Closeout stop:

`development/126-p10-closeout-stop.md`

Facts:

- no `acceptance/40-p10-independent-acceptance-result.md` existed;
- no `workspace/p10-n` execution root existed;
- no P10-N detached acceptance worktree existed;
- therefore P10-N had not actually executed;
- historical integration merge `b560f49a78316fa59a4183de326d2dee0a80ebb6` is ineligible for main integration;
- `origin/main` remains the accepted P9 baseline `e9b30626f2b88ac5527d42bd76d0b682efbeef0e`.

Corrected P10-N authorization:

`development/127-p10-n-corrected-reauthorization.md`

Exact acceptance candidate:

`4d1ab46f11d1d7b88934309ce32319e2200f0d8f`

Corrected P10-N execution reached frozen harness precheck and STOPPED before any research acceptance run.

Stop record:

`development/128-p10-n-precheck-stop.md`

P10-ISSUE-008 facts:

- fixture manifest size/SHA matches exact candidate Git blob bytes;
- all 8 frozen Markdown fixture Git blobs are LF;
- detached Windows checkout under `core.autocrlf=true` materializes CRLF;
- frozen harness incorrectly used checkout `Path.read_bytes()` as fixture identity;
- no P10 production/test change or fixture semantic drift occurred.

The prior P10-M freeze and corrected P10-N authorization are invalidated by the acceptance-package identity defect.

Current ISSUE-008 design baseline:

`f8bffca`

Acceptance harness amendment authorization:

`development/129-p10-acceptance-harness-amendment-authorization.md`

Partial harness candidate:

`9621f20d33c1d1b650bcdf1a7686b5f0b9c7c817`

Detached precheck preview:

- fixture identity source = `GIT_BLOB`;
- all 8 frozen fixture hashes = PASS;
- precheck status = PASS;
- preview then exposed P10-ISSUE-009: base immutability manifest still used checkout bytes.

Preview stop:

`development/130-p10-acceptance-harness-preview-stop.md`

The partial harness candidate is not eligible for formal review/freeze.

P10-ISSUE-009 design baseline:

`ad78cbe`

Harness v2 authorization:

`development/131-p10-acceptance-harness-v2-authorization.md`

Harness v2 candidate:

`db06b7a890e25908d224b6a63d8695be2f414b25`

Harness v2 evidence:

`development/132-p10-acceptance-harness-v2-evidence.md = PASS`

Detached precheck preview = PASS with both base manifest and fixture manifest identity source `GIT_BLOB`.

Targeted formal review authorization:

`development/133-p10-acceptance-package-formal-review-authorization.md`

Targeted formal review result:

`development/134-p10-acceptance-package-formal-review-result.md = PASS`

P10-M re-freeze authorization:

`development/135-p10-m-issue008009-refreeze-authorization.md`

Re-freeze evidence:

`development/136-p10-m-issue008009-refreeze-evidence.md = PASS / PACKAGE READY`

Fresh precheck preview = PASS; base and fixture manifest identities are both `GIT_BLOB`.

Actual P10-M re-freeze commit:

`183ca5dc89a606715a3e352bf92a235f7aa31fad`

P10-M is closed on this exact candidate.

P10-N authorization:

`development/137-p10-n-independent-acceptance-authorization.md`

Only exact candidate `183ca5dc89a606715a3e352bf92a235f7aa31fad` was eligible. The first execution attempt stopped because the mutable live P9 submission metadata did not match the frozen acceptance/39 metadata. Stop record: `development/138-p10-n-execution-stop.md`. Fresh rerun authorization: `development/139-p10-n-rerun-authorization.md`. Candidate/package/design remained unchanged.

Fresh Independent Acceptance result:

`acceptance/40-p10-independent-acceptance-result.md = PASS`

Verified in the fresh rerun:

- precheck PASS with Git-blob fixture/base identity;
- research unit `136 passed`;
- full unit `444 passed`;
- dynamic Spec A/B hashes/toolsets differ and both ledgers PASS;
- live CN 600519 run = COMPLETE;
- fresh isolated P9 resolution/overlay validated;
- K1–K5 exact negative capability gates PASS;
- immutable 47-file base postcheck PASS;
- detached candidate remained clean at `183ca5dc89a606715a3e352bf92a235f7aa31fad`.

P10-N is CLOSED / PASS.

P10-O closeout/main integration remains CLOSED until a separate explicit authorization.

P10 production remains frozen; P11 / Research MCP production / Semantic Resolver production remain unauthorized.

Still not authorized:

- P10-J and later production;
- Research MCP production;
- Semantic Resolver production;
- P11 production;
- any weakening of P8 read-only or P9 durable-review boundaries.

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
- P10 — Codex Dynamic Research Integration: `DESIGN READY / PRODUCTION NOT STARTED`
- P11 — US SEC Provider: `NOT STARTED`
