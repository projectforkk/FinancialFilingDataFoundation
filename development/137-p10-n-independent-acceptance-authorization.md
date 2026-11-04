# 137 — P10-N Independent Acceptance Authorization — Exact ISSUE-008/009 Re-Freeze Candidate

Status: **AUTHORIZED — P10-N INDEPENDENT ACCEPTANCE ONLY**

Phase:
P10 — Codex Dynamic Research Integration

Gate:
P10-N — Independent Acceptance

Exact P10-M re-freeze candidate:

183ca5dc89a606715a3e352bf92a235f7aa31fad

P10-M re-freeze evidence:

development/136-p10-m-issue008009-refreeze-evidence.md = PASS

P10-M authorization:

development/135-p10-m-issue008009-refreeze-authorization.md

Targeted acceptance-package formal review:

development/134-p10-acceptance-package-formal-review-result.md = PASS

Only exact candidate
183ca5dc89a606715a3e352bf92a235f7aa31fad
is eligible for this P10-N run.

Do not use this authorization commit as the acceptance candidate.

## 1. Detached candidate

Create:

D:\Codex\FinancialFilingDataFoundation\worktrees\acceptance\p10-n-183ca5d

with detached HEAD exactly:

183ca5dc89a606715a3e352bf92a235f7aa31fad

Detached candidate must remain clean and immutable.

## 2. Exact source binding

Every P10 Python/test command must use:

PYTHONPATH=D:\Codex\FinancialFilingDataFoundation\worktrees\acceptance\p10-n-183ca5d\src

PYTHONDONTWRITEBYTECODE=1

PYTHONIOENCODING=utf-8

Do not use main/active/review/integration/another worktree source.

Do not editable/install FFDF.

## 3. Frozen package identities

Acceptance freeze:

- path: acceptance/39-p10-final-acceptance-freeze.md
- Git-blob SHA256:
  46156307c295c964f719baf3c979874ca9d714dce7b87c63c0a2aaca81d8e681
- Git-blob size: 15993

Harness v2:

- path: acceptance/p10_independent_acceptance_harness.py
- Git-blob SHA256:
  dba3e7b0cc2e85e9eb65f003421ecd0a19229632b93905d9669421e74d36b9e7
- size: 24625

Base immutability manifest:

- Git-blob SHA256:
  ae176a49858caabb45e525fbeb9b99eec23e4b5f649dfa584ebe4656c2dba003
- size: 12413
- entries: 47

Fixture manifest:

- Git-blob SHA256:
  345a00660a5e6150d2c1e547133cb9eb28aa39987d77010ce57f8f70f3d6cc3a
- size: 1227
- fixtures: 8

Integration instruction Git blob SHA:

ef10406c9957f7a68a9af001c913deef0a057e166100a2d852c0c8fcd2c46296

P10-N must verify exact Git blob bytes, not checkout-filtered bytes.

## 4. Fresh mutable acceptance root

Use only:

D:\Codex\FinancialFilingDataFoundation\workspace\p10-n\183ca5d

The path must be absent before precheck.

Do not reuse any P10-I/J/K or preview workspace as acceptance output.

## 5. Required sequence

1. verify detached HEAD exactly;
2. verify detached worktree clean;
3. preserve existing worktrees/t/a and b whole if present;
4. run frozen harness precheck;
5. require precheck PASS and both manifest identity sources = GIT_BLOB;
6. run fresh P10 research unit suite;
7. run fresh full P0-P10 unit suite;
8. read frozen Spec A completely;
9. dynamically execute Spec A and validate ledger;
10. read frozen Spec B completely;
11. dynamically execute Spec B and validate ledger;
12. verify Spec A/B bundle hashes and selected tool sets differ;
13. read frozen live-cn spec completely;
14. perform fresh live CN COMPLETE run;
15. construct isolated P9 review state at final acceptance path through accepted P9 APIs;
16. validate raw/effective distinction and non-canonical reuse;
17. read each applicable negative spec completely;
18. execute K1-K5 fresh negative gates;
19. write frozen result summaries required by postcheck;
20. run frozen harness postcheck;
21. require immutable 47-file base after-run PASS;
22. verify detached worktree still clean;
23. issue PASS / FAIL / BLOCKED.

## 6. Test basetemps

Use:

D:\Codex\FinancialFilingDataFoundation\worktrees\t\a
D:\Codex\FinancialFilingDataFoundation\worktrees\t\b

If either already exists, preserve whole under:

workspace/scratch/p10-n-preserved-<slot>-before-183ca5d

Do not delete historical evidence.

## 7. Expected minimum test counts

P10 research:
>= 136 passed

Full unit:
>= 444 passed

Any failure blocks acceptance.

## 8. Dynamic Spec A/B

Use the exact Git-blob fixture bytes copied by the frozen harness.

Required:

- different raw spec SHA where applicable;
- different spec_bundle_hash values;
- same P10 production candidate;
- frozen spec read completely before operation choice;
- materially different selected P8 tool sets;
- P10 ledger PASS for both;
- result summaries in acceptance workspace.

## 9. Live COMPLETE

Primary filing:

- CN 600519 FY2024
- document SHA:
  5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30

Target raw fact:

9b3e2e441e6730c0f3c979816dd764dcb4bf70e6cde16caae9e3897733b9a015

Required behavior:

- isolated P9 store created at final acceptance path with prepare_review_overlay;
- do not copy/move existing P9 store;
- supported/evidence-grounded SET_PERIOD=2024 only if generated task permits;
- materialize with accepted API;
- validate generated snapshot;
- raw_period=null;
- effective_period=2024;
- raw numeric unchanged;
- base status=REVIEW_REQUIRED;
- resolved status=REVIEW_REQUIRED;
- specific claim usable=true;
- resolved_reuse_eligible=false;
- canonical_reuse_eligible=false;
- evidence ledger PASS;
- run_status=COMPLETE.

## 10. Negative gates

Required exact outcomes:

- K1 = P10_DATA_PREPARATION_REQUIRED
- K2 = P10_VISUAL_CAPABILITY_REQUIRED
- K3 = P10_UPSTREAM_INVALID
- K4 = P10_RESEARCH_SPEC_CHANGED
- K5 = P10_REVIEW_UNRESOLVED

Required safety booleans all false for download/guess/fallback/refresh/semantic guess.

## 11. Result artifact

After all required checks complete, write on the active governance branch:

acceptance/40-p10-independent-acceptance-result.md

The result must record:

- exact candidate SHA;
- detached worktree path;
- frozen package Git-blob identities;
- precheck report and SHA;
- focused/full counts;
- Spec A/B hashes/context/tool sets/ledger results;
- live generated isolated P9 resolution ID and overlay hash;
- live COMPLETE output;
- K1-K5 outcomes;
- before/after base manifest PASS;
- postcheck report and SHA;
- detached clean status;
- final verdict.

If any finding requires design/package/production change:

STOP -> FAIL/BLOCKED.

Do not patch the detached candidate.

## 12. Scope

P10-N does not authorize:

- any P10 production/test/design/package change;
- main integration;
- P11 production;
- Research MCP production;
- Semantic Resolver production;
- P8/P9 mutation outside the isolated acceptance root.

PASS may permit a later separate P10 closeout authorization.

P10 remains not-DONE until actual Independent Acceptance PASS is committed.
