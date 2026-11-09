# 147 — P11 US SEC Provider Scope Reopening Authorization

Status: **AUTHORIZED — P11 REDESIGN + DEVELOPMENT PLANNING / PRODUCTION NOT YET STARTED**

Date: 2026-11-09

User instruction:

> 重新开发 P11；更新设计文档，更新好后，制定开发计划。

## 1. Authority

This instruction reopens the US SEC initiative that was previously closed by
`design/30-project-final-cn-hk-scope.md` and
`development/144-final-cn-hk-project-scope-closeout.md`.

Those files remain immutable historical records of the 2026-11-05 closeout decision.
They are not deleted or rewritten as if that decision never occurred.

For current execution, this authorization is newer and therefore supersedes the
CN/HK-only restriction **only for the newly reopened P11 lifecycle**.

## 2. Current baseline

- GitHub repository: `projectforkk/FinancialFilingDataFoundation`
- design branch base: `main @ 5190e866a4ee55dc8820e63ce3dae8fe3c69dfc8`
- P0-P10 accepted production behavior remains frozen.
- Post-closeout CN/HK user CLI remains accepted.
- P11 production is still absent on main.
- Existing historical P11 worktrees/branches/probes are audit history only and MUST
  NOT be treated as production candidates.

## 3. Authorized work in this gate

Authorized now:

1. reopen P11 scope;
2. audit accepted P1/P2/P3-P10 interfaces;
3. audit current SEC public-data interfaces;
4. create a fresh detailed P11 design at
   `design/26-p11-sec-provider-design.md`;
5. create a fresh implementation plan at
   `design/27-p11-implementation-plan.md`;
6. update current-state / design-index / roadmap documentation;
7. define acceptance, security, performance and compatibility gates.

Not authorized in this design gate:

- production SEC provider code;
- Registry migrations;
- runtime/dependency installation;
- changing `SUPPORTED_MARKETS` on main;
- changing P8/P9/P10 accepted contracts;
- downloading live filings into the accepted production workspace.

## 4. Historical P11 handling

Historical P11 candidates are not a development baseline.

Rules:

- do not merge an old P11 branch merely because code already exists;
- old probes may be read as evidence only;
- every production behavior must be justified by the new design;
- implementation starts from the accepted current main baseline;
- reusable historical code must be re-reviewed line-by-line against the new design.

## 5. Exit condition

This gate is complete when:

- scope reopening contract exists;
- detailed design exists and resolves the known PDF-vs-HTML/iXBRL incompatibilities;
- implementation plan is ordered and testable;
- current status/index/roadmap consistently say P11 is reopened;
- design changes are committed on a dedicated branch.

Production development starts only after this design baseline is frozen.
