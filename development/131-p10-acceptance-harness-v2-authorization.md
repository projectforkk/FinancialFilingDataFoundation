# 131 — P10 Acceptance Harness V2 Amendment Authorization

Status: **AUTHORIZED — P10-ISSUE-009 ACCEPTANCE HARNESS V2 ONLY**

Phase:
P10 — Codex Dynamic Research Integration

Design baseline:
ad78cbe

Prior partial harness candidate:
9621f20d33c1d1b650bcdf1a7686b5f0b9c7c817

Preview stop:
development/130-p10-acceptance-harness-preview-stop.md

Only the acceptance harness v2 amendment is authorized.

## Allowed path

- acceptance/p10_independent_acceptance_harness.py

No src/ change.
No tests/ change.
No fixture payload/manifest change.
No acceptance/39 freeze change yet.

## Required implementation

1. retain P10-ISSUE-008 fixture Git-blob loader;
2. update CORE_DESIGN_BASELINE to the exact ISSUE-009 design baseline;
3. read acceptance/p10-base-immutability-manifest.json from exact HEAD Git blob bytes;
4. parse that blob as UTF-8 JSON;
5. report manifest SHA from those Git blob bytes;
6. validate each of the 47 referenced project files from actual project filesystem bytes;
7. keep fixture_identity_source=GIT_BLOB;
8. expose base_manifest_identity_source=GIT_BLOB in pre/post reports.

## Required validation

- py_compile PASS;
- git diff --check PASS;
- src/tests diff NONE;
- detached fresh precheck PASS;
- precheck base manifest SHA equals ae176a49858caabb45e525fbeb9b99eec23e4b5f649dfa584ebe4656c2dba003;
- fixture manifest SHA equals 345a00660a5e6150d2c1e547133cb9eb28aa39987d77010ce57f8f70f3d6cc3a;
- all 8 fixture hashes PASS;
- detached status clean;
- production candidate unchanged.

After evidence, STOP.

A separate targeted formal review is required before P10-M re-freeze.

P10-N / closeout remain closed.
