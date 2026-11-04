# 108 — P10-H Full Regression / Scope Authorization

Status: **AUTHORIZED — P10-H VALIDATION ONLY / NO PRODUCTION CHANGES**

Phase:
`P10 — Codex Dynamic Research Integration`

Gate:
`P10-H — Full Regression / Scope`

Current design baseline:
`d8961731044d6c33c8a9e2cb96820819c3daa275`

P10-G review result:
`development/107-p10-g-detached-review-result.md = PASS`

P10-G review result commit:
`a60bcc5`

Only P10-H validation/evidence is authorized.

## Required execution

Using exact active candidate source binding:

`PYTHONPATH=D:\\Codex\\FinancialFilingDataFoundation\\worktrees\\active\\p10-dynamic-research-design\\src`

Run:

- P10 focused research suite;
- full P0-P10 unit suite;
- compile/import;
- `git diff --check`;
- exact branch/remote identity;
- P0-P9 production/test accepted-path scope audit;
- P8 exact 11-tool contract audit;
- P8 accepted runtime lock check;
- P9 source/test scope audit;
- dependency/runtime diff audit;
- forbidden P10 production surface audit;
- Research MCP / Semantic Resolver / P11 production absence audit;
- P10-G exact Git-blob identity audit;
- worktree clean before/after.

## Scope baseline

Accepted P9 main baseline:

`e9b30626f2b88ac5527d42bd76d0b682efbeef0e`

P10 is allowed to add/change only its authorized P10 paths.

No P0-P9 production/test implementation path may be modified by P10.

P8 must remain exactly 11 read-only tools.

P9 semantics/source/tests must remain unchanged.

No dependency/runtime addition is authorized.

## Forbidden

Do not:

- modify production/tests;
- modify P8/P9;
- install/editable-install FFDF;
- modify runtime locks;
- add Research MCP production;
- add Semantic Resolver production;
- add P11 production;
- add network/AI/subprocess/shell/SQL production surface.

## Evidence

Write:

`development/109-p10-h-full-regression-scope-evidence.md`

only after all required checks complete.

PASS closes P10-H and permits a separate P10-I authorization.

P10-I and later remain closed until then.
