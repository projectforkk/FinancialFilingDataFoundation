# 144 — Final CN/HK Project Scope Closeout Decision

Status: **DONE / PASS**

## Decision

FFDF is being closed as a CN/HK financial-filing data foundation. US SEC work is no longer required by the project.

This decision supersedes `development/143-p11-design-authorization.md` as the current project direction without rewriting or deleting that historical record.

## Main-baseline facts at closeout start

- main HEAD before closeout edits: `5f64f74`;
- main and origin/main were aligned;
- P0-P10 accepted;
- P11 production was not merged into main;
- `CompanyRef("US", ...)` was already rejected by accepted P1 behavior;
- acquisition production paths were already CN/HK-only;
- P10 exposed `P11_SEC_PROVIDER = UNAVAILABLE`.

## Baseline regression observation

An initial unit run using the longer basetemp `.t/closeout-pre/b` produced 14 P9/P10 snapshot failures caused by Windows path-length exhaustion.

The required short project-local basetemp rerun `.t/u/b` produced:

`444 passed`

Therefore the initial 14 failures are test-environment MAX_PATH false failures, not production regressions.

## Required closeout changes

- freeze final CN/HK scope in design and current-status documents;
- mark P11 as `OUT_OF_SCOPE / NOT_REQUIRED_NOT_EXECUTED`;
- keep historical P11 artifacts for audit only;
- expose the final supported market tuple in production identity code without changing accepted validation behavior;
- run full consistency review and final regressions;
- commit/push only after review is PASS.
