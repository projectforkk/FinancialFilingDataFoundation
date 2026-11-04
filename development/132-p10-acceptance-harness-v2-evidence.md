# 132 — P10 Acceptance Harness V2 Evidence

Status: **PASS — P10-ISSUE-009 HARNESS V2 CANDIDATE READY FOR TARGETED REVIEW**

Phase:
P10 — Codex Dynamic Research Integration

Authorization:
development/131-p10-acceptance-harness-v2-authorization.md

Design baseline:
ad78cbeaccfd444f1c5fcd31708b1300f6ad67a7

Harness v2 candidate:
db06b7a890e25908d224b6a63d8695be2f414b25

Prior partial candidate:
9621f20d33c1d1b650bcdf1a7686b5f0b9c7c817 = INELIGIBLE

## 1. Scope

Candidate diff from authorization commit:

M acceptance/p10_independent_acceptance_harness.py

No src/ change.
No tests/ change.
No fixture payload/manifest change.
No acceptance/39 freeze change.

## 2. Implemented contract

Harness v2:

- retains exact Git-blob loading for fixture manifest;
- retains exact Git-blob loading/copy for all 8 frozen fixtures;
- reads acceptance/p10-base-immutability-manifest.json from exact HEAD Git blob bytes;
- parses that blob as UTF-8 JSON;
- reports base manifest SHA from Git blob bytes;
- validates the 47 referenced project files from actual project filesystem bytes;
- reports manifest_identity_source=GIT_BLOB;
- updates CORE_DESIGN_BASELINE to ad78cbeaccfd444f1c5fcd31708b1300f6ad67a7.

## 3. Compile / static validation

py_compile:
PASS

git diff --check:
PASS

Out-of-scope diff:
NONE

## 4. Detached preview

Detached worktree:

D:\Codex\FinancialFilingDataFoundation\worktrees\review\p10-issue009-harness-db06b7a

Detached HEAD:

db06b7a890e25908d224b6a63d8695be2f414b25

Final detached status:

## HEAD (no branch)

Fresh preview workspace:

D:\Codex\FinancialFilingDataFoundation\workspace\p10-n-preview\db06b7a

Precheck:
PASS

Report:

D:\Codex\FinancialFilingDataFoundation\workspace\p10-n-preview\db06b7a-precheck.json

Report SHA256:

8f00b273215255d9e96000df7dcdb57d1b987b4f9afac44051315f7ddc78735d

## 5. Identity checks

Base immutability manifest:

- identity source = GIT_BLOB
- entry_count = 47
- SHA256 = ae176a49858caabb45e525fbeb9b99eec23e4b5f649dfa584ebe4656c2dba003

Fixture manifest:

- identity source = GIT_BLOB
- SHA256 = 345a00660a5e6150d2c1e547133cb9eb28aa39987d77010ce57f8f70f3d6cc3a

All 8 frozen fixture SHA/size checks:
PASS

## 6. Other precheck gates

P8:
- server = p8-local-mcp-v1
- exact tool count = 11
- runtime lock SHA unchanged

P9:
- p9-review-overlay-v1
- p9-review-policy-v1
- resolution schema unchanged
- resolved-view schema unchanged

CLI critical:
PASS

Security:
forbidden production surface = NONE

Future production paths:
ABSENT

Performance:
- freeze_spec_s = 0.0004064
- verify_spec_s = 0.0003075
- build_context_s = 0.0024989
- validate_ledger_s = 0.0025377

All below frozen limits.

## 7. Verdict

# PASS

P10-ISSUE-008 and P10-ISSUE-009 acceptance harness behavior is corrected in candidate db06b7a....

STOP after evidence.

A separate targeted formal review is required before P10-M re-freeze.

P10-N and closeout remain closed.
