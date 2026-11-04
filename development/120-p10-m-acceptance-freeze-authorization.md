# 120 — P10-M Acceptance Freeze Authorization

Status: **AUTHORIZED — P10-M ACCEPTANCE PACKAGE ONLY / NO DESIGN OR PRODUCTION CHANGES**

Phase:
`P10 — Codex Dynamic Research Integration`

Gate:
`P10-M — Acceptance Freeze`

Core design baseline:
`668269e87774730ade03afb4b7564256671eb31f`

Production source/test candidate:
`d8e7d81b4bb5a4f06cead9eba0e2d09884094676`

Integration instruction candidate:
`3a805a8f333ac20770d6aec1c8285d93993d18fc`

Integration Git-blob SHA256:
`ef10406c9957f7a68a9af001c913deef0a057e166100a2d852c0c8fcd2c46296`

Formal review:
`development/119-p10-l-formal-code-review-result.md = PASS`

Formal review result commit:
`157c9309a9e1c78baab08a0ab77bd3e7408facd8`

Only P10-M acceptance-package authoring/freeze is authorized.

## Allowed tracked paths

Allowed new/updated acceptance-only artifacts:

- `acceptance/39-p10-final-acceptance-freeze.md`
- `acceptance/p10_independent_acceptance_harness.py`
- `acceptance/p10-base-immutability-manifest.json`
- `acceptance/p10-fixtures/**`
- governance/status references needed to record the freeze

No `src/**`, `tests/**`, design/24, design/25, or acceptance/38 semantic change is authorized.

## Freeze content

Freeze at minimum:

- core design baseline;
- production source/test candidate;
- integration instruction candidate + exact Git-blob SHA;
- formal review PASS;
- accepted P8 server version + exact 11 tools;
- accepted P8 runtime lock SHA;
- accepted P9 public policy/schema versions;
- main/P10 runtime identity;
- exact tracked Spec A/B fixture bytes + SHA256;
- exact live/negative fixture bytes + SHA256;
- accepted live P8 catalog SHA;
- exact CN/HK live document identities;
- source PDF / P3 / P4 / P5 / P6 / P7 / catalog / Registry / runtime-lock immutability manifest;
- isolated P9 acceptance-root construction rule from P10-ISSUE-007;
- exact acceptance work-root layout;
- exact focused/full test commands;
- exact harness command;
- exact performance thresholds;
- evidence-ledger/live/negative expected behaviors;
- Windows short basetemp policy;
- exact-candidate PYTHONPATH rule.

## Acceptance harness boundary

The acceptance-only harness may orchestrate accepted P8/P9/P10 APIs and subprocess checks.

It must not:

- modify P10 production/design;
- modify accepted source/P8/P9/Registry/runtime artifacts;
- use network/remote AI;
- create Research MCP/Semantic Resolver/P11 production;
- bypass P9 review-store path binding;
- store hidden chain-of-thought.

All mutable state must stay under the supplied project-local acceptance work root.

## Freeze semantics

The P10-M commit containing the final freeze package is the acceptance package commit.

P10-N authorization must record that exact P10-M commit SHA and create the detached acceptance worktree from it.

Any later change to:

- design/24 or design/25;
- acceptance/38;
- P10 production/tests;
- integration instruction;
- frozen harness/fixtures/manifest;

invalidates the freeze and requires a new P10-M freeze.

## Evidence

After the freeze package passes local pre-freeze validation, commit/push it and record the exact commit in project status.

P10-N remains closed until a separate explicit authorization records the exact P10-M freeze commit.
