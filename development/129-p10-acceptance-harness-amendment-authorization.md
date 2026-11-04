# 129 — P10 Acceptance Harness Amendment Authorization

Status: **AUTHORIZED — P10-ISSUE-008 ACCEPTANCE HARNESS ONLY**

Phase:
P10 — Codex Dynamic Research Integration

Issue:
P10-ISSUE-008

Design baseline:
f8bffca

Historical stopped P10-N:
development/128-p10-n-precheck-stop.md

Only the acceptance harness amendment required by P10-ISSUE-008 is authorized.

## Allowed path

- acceptance/p10_independent_acceptance_harness.py

No src/ change.
No tests/ change.
No fixture payload change.
No fixture manifest change.
No acceptance/39 re-freeze yet.

## Required implementation

validate_and_copy_fixtures must:

1. obtain acceptance/p10-fixtures/manifest.json from exact current candidate Git blob bytes;
2. parse that blob as UTF-8 JSON;
3. obtain every listed frozen fixture from exact current candidate Git blob bytes;
4. validate size/SHA against those blob bytes;
5. copy exact validated blob bytes into the mutable acceptance workspace;
6. report fixture_identity_source=GIT_BLOB;
7. never use detached checkout EOL representation as frozen fixture identity.

Use binary-safe git subprocess stdout bytes.

Do not edit .gitattributes.

## Required validation

Before committing the harness candidate:

- compile/import PASS;
- fixture manifest blob SHA/size check PASS;
- all 8 fixture blob size/SHA checks PASS;
- a fresh precheck preview from a detached worktree of the harness candidate must PASS;
- copied workspace fixture bytes must equal exact Git blobs;
- P10 production/tests diff = NONE;
- git diff --check PASS.

After evidence:

STOP.

A separate targeted formal review is required before any new P10-M freeze.

P10-N and closeout remain closed.
