# 146 — P11 Detached Design Review Instruction

Status: **REVIEW AUTHORIZED — DESIGN ONLY**

Phase:
P11 — US SEC Provider

Exact design candidate to review:

`3ccaedc`

Full candidate resolution must be recorded before verdict.

Candidate branch:
`design/p11-sec-provider`

Review must use a fresh detached project-local worktree.

Production remains closed.

## Review scope

Review exact candidate:

- `development/144-p11-environment-interface-audit.md`;
- `development/145-p11-design-reconciliation.md`;
- `design/26-p11-sec-provider-design.md`;
- `design/27-p11-implementation-plan.md`;
- `design/30-parsed-financial-document-v2-contract.md`;
- `acceptance/41-p11-acceptance-instruction.md`;
- synchronized project status/index/master/roadmap.

## Required review questions

1. Does the design preserve P0-P10 accepted history?
2. Is US/Q2 identity explicit and non-corrupting to CN/HK?
3. Is CIK canonical and ticker only lookup/display?
4. Are periodic vs supplemental filing semantics explicit?
5. Are amendment semantics non-destructive/non-silent?
6. Does acquisition avoid assuming PDF?
7. Are exact source bytes/package identity deterministic?
8. Are post-acceptance corrections handled without overwrite?
9. Is SEC fair-access behavior explicit?
10. Are redirect/host/path/content-size security boundaries implementable?
11. Is companyfacts clearly auxiliary only?
12. Are custom taxonomy facts preserved?
13. Does v2 evidence avoid fake page/bbox?
14. Is raw/transformed numeric provenance auditable?
15. Does v2 serialization avoid absolute-path identity leaks?
16. Is runtime/network separation implementable?
17. Is Arelle merely a candidate until runtime probe?
18. Are P8/P9/P10 v1 explicitly unchanged?
19. Does acceptance test every material design promise?
20. Does any production implementation still require guessing a material contract that should be designed first?

## Review method

At minimum:

- exact HEAD check;
- `git diff --check`;
- UTF-8/no-BOM/replacement-character scan;
- diff scope vs accepted main `5f64f7488c4b6558e4b90fb10142b23594785a6d`;
- production/tests/runtime diff must be NONE;
- cross-document consistency scan;
- security/boundary scan;
- official-source fact spot-check against current SEC docs;
- issue list with severity.

## Verdict

Only:

- PASS
- FAIL
- BLOCKED

Any material ambiguity that would force production code to invent behavior => FAIL/BLOCKED and return to Design-First amendment.

No development authorization may be created before PASS.
