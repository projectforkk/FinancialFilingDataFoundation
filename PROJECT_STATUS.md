# Project Status

## Repository

`projectforkk/FinancialFilingDataFoundation`

## Current state

**P2_IN_DEVELOPMENT**

## Approved phase

**P2 — Acquisition Provider（IN DEVELOPMENT）**

P1 completed branch：

`task/p1-identity-registry-planner`

P2 development branch：

`task/p2-acquisition-provider`

Branch start design baseline：

`e53eca8c384f93382945cd2fc529e194a400d066`

当前 P1 独立验收执行指令：

`acceptance/07-p1-acceptance-run-instruction.md`

Frozen acceptance candidate：

`3b382f4091a96a2dff40144253da42bf8de1fcc2`

该 candidate 已冻结；后续 branch HEAD 的状态/验收证据提交不改变验收输入。

P1 Code Review：

- final verdict: `PASS`
- final evidence: `development/13-p1-final-code-review.md`
- reviewed candidate: `f5c5cd76b33199639a5266959fbf7dc0968a95c4`
- tests: `54 passed`
- previous evidence `development/10-p1-code-review.md` remains historical and was invalidated by `P1-ISSUE-008`.

P1 Independent Acceptance：

- verdict: `PASS`
- evidence: `acceptance/08-p1-acceptance-result.md`
- frozen candidate: `3b382f4091a96a2dff40144253da42bf8de1fcc2`
- full suite: `54 passed in 2.05s`
- blocker: `NONE`

当前 P1 design baseline：

以 P1 task branch 中最新已提交的 design baseline 为准；所有设计修正必须先提交并进入 GitHub。

当前已验收 baseline：

- phase: `P1_DONE`
- accepted candidate: `3b382f4091a96a2dff40144253da42bf8de1fcc2`
- acceptance verdict: `PASS`
- acceptance evidence: `acceptance/08-p1-acceptance-result.md`
- accepted merge commit: `1cb6e88be318c0a1424d74ee601c336075361cd6`
- accepted_baseline_sha: `1cb6e88be318c0a1424d74ee601c336075361cd6`
- closeout main verification: `54 passed`

治理异常 `P1-ISSUE-004` 已在 P1-K 以非破坏方式收口：未改写历史；最终 `main` 的 `src/tests` 与 frozen acceptance candidate 零差异，并通过 54 项 closeout 回归。P1 现已成为新的 accepted baseline。

P0 acceptance freeze/result 已保留为历史证据，不再作为当前 P1 验收入口。

P0 独立验收结果：

- verdict: `PASS`
- evidence: `acceptance/05-p0-acceptance-result.md`
- accepted candidate: `63547b5cfd3112a7c0598a32139b9b191c356c69`

## Design baseline

当前设计基线由以下文件共同组成：

- `AGENTS.md`
- `design/01-project-detailed-design.md`
- `design/02-incremental-and-acquisition-design.md`
- `design/03-parsed-financial-document-contract.md`
- `design/04-pdf-quality-gate-design.md`
- `design/05-p0-implementation-plan.md`
- `design/06-p1-identity-registry-planner-design.md`
- `design/07-p1-implementation-plan.md`
- `design/08-p2-acquisition-provider-design.md`
- `design/09-p2-implementation-plan.md`
- `development/01-development-roadmap.md`
- `development/02-p0-development-instruction.md`
- `development/07-p1-development-instruction.md`
- `development/14-p2-development-instruction.md`
- `acceptance/01-acceptance-strategy.md`
- `acceptance/02-p0-acceptance-instruction.md`
- `acceptance/06-p1-acceptance-instruction.md`
- `acceptance/09-p2-acceptance-instruction.md`

P0 closeout：

`edff06b2b1138b50d742e92ce8b8df628c6d2c61`

P1 accepted baseline：

`1cb6e88be318c0a1424d74ee601c336075361cd6`

P1 closeout/status main HEAD：

`6d7fda466fb83997da88d6d3586a8ed877f31810`

本次 P2 design baseline 提交完成后，以该 main HEAD 创建 `task/p2-acquisition-provider`。

## Current scope

- 多年份财报数据源构建。
- 增量判定：已有数据 → 本地文件 → 下载 → 解析。
- CN/HK：PDF extraction。
- US：预留 SEC HTML / Inline XBRL / XBRL provider。
- Local MCP：0 AI API。
- Codex：只处理本机解析无法可靠完成的局部复核。
- CRDE / 财报分析：下游，不属于首期 Extraction 实现范围。

## Verified Dayu reference baseline

Dayu 参考基线：

`2115c86d5a9027bb51cbbc8a4d0175080732e4e6`

已核对：
- CN/HK 高层 `fins download` 会在 PDF acquisition 后继续 Docling conversion；
- FFDF 若复用 Dayu，应复用 acquisition/downloader 的窄能力，不以 Docling 为默认 parser；
- Dayu 正式 package dependencies 包含 Docling / Docling Core；
- `dayu.fins` / `dayu.fins.downloaders` / `dayu.fins.pipelines` initializer 会扩大 import surface；
- P2 因此采用 pinned read-only checkout + dedicated Dayu acquisition runtime + subprocess JSON boundary；
- FFDF main runtime 继续保持 Dayu / Docling absent。

## Representative performance evidence

贵州茅台 FY2024：
- 143 pages；
- 143/143 有 native text；
- PDF → Docling JSON 约 1802.6s；
- Docling JSON → snapshot 约 31.6s。

因此 P0 首先验证：目标 PC 上轻量 native PDF path 的真实性能与可读取性。

## Phase status

- P0 Native PDF Parsing Feasibility Probe: `DONE / PASS`
- P1 Identity / Registry / Incremental Planner: `DONE / PASS`
- P2 Acquisition Provider: `DESIGN_READY / DEVELOPMENT_NOT_STARTED`
- P3+：未开始

P2 当前只批准 CN/HK official raw-document acquisition；US SEC 仍属于 P11。

P2 未通过 Independent Acceptance 前，不允许开始 P3 implementation。
