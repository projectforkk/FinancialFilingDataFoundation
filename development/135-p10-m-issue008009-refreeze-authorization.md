# 135 — P10-M Acceptance Re-Freeze Authorization After ISSUE-008/009

Status: **AUTHORIZED — P10-M RE-FREEZE ONLY**

Phase:
P10 — Codex Dynamic Research Integration

Prerequisites:

- targeted formal review result:
  development/134-p10-acceptance-package-formal-review-result.md = PASS
- targeted formal review result commit:
  5a411b0
- design baseline:
  ad78cbeaccfd444f1c5fcd31708b1300f6ad67a7
- production candidate:
  d8e7d81b4bb5a4f06cead9eba0e2d09884094676
- integration instruction candidate:
  3a805a8f333ac20770d6aec1c8285d93993d18fc
- harness v2 candidate:
  db06b7a890e25908d224b6a63d8695be2f414b25

Only P10-M re-freeze work is authorized.

## Allowed paths

- acceptance/39-p10-final-acceptance-freeze.md
- development/136-p10-m-issue008009-refreeze-evidence.md
- PROJECT_STATUS.md
- design/00-design-management-index.md

No src/ change.
No tests/ change.
No harness change.
No fixture payload/manifest change.
No design/24/25/acceptance38 change.

## Frozen Git-blob identities

Harness v2:

- path: acceptance/p10_independent_acceptance_harness.py
- size: 24625
- SHA256: dba3e7b0cc2e85e9eb65f003421ecd0a19229632b93905d9669421e74d36b9e7

Base immutability manifest:

- path: acceptance/p10-base-immutability-manifest.json
- size: 12413
- SHA256: ae176a49858caabb45e525fbeb9b99eec23e4b5f649dfa584ebe4656c2dba003

Fixture manifest:

- path: acceptance/p10-fixtures/manifest.json
- size: 1227
- SHA256: 345a00660a5e6150d2c1e547133cb9eb28aa39987d77010ce57f8f70f3d6cc3a

Integration instruction Git blob SHA remains:

ef10406c9957f7a68a9af001c913deef0a057e166100a2d852c0c8fcd2c46296

## Freeze requirements

Update acceptance/39 to record:

- new design baseline;
- unchanged production candidate;
- unchanged integration instruction candidate/blob SHA;
- original production formal review PASS;
- targeted acceptance-package formal review PASS;
- new harness v2 Git-blob SHA/size;
- base/fixture manifests as Git-blob identities;
- exact Git-blob identity rule for frozen tracked package files;
- P10-ISSUE-008/009 closure conditions;
- fresh P10-N must use a later exact re-freeze commit SHA.

Before the re-freeze commit:

1. UTF-8/no-BOM checks PASS;
2. git diff --check PASS;
3. git diff --cached --check PASS;
4. src/tests diff NONE;
5. harness/fixture/design contract diff NONE;
6. all frozen blob identities independently rechecked;
7. acceptance harness fresh precheck preview PASS;
8. native exit codes checked explicitly.

Do not write a guessed future re-freeze SHA into any document.

The exact re-freeze SHA is whatever commit is actually produced after all checks pass.

After the re-freeze commit/push:

STOP.

A separate P10-N authorization must reference the actual exact re-freeze commit.

P10-N and closeout remain closed until then.
