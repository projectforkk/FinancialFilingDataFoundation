# 189 — P11 Final-Path Concurrency Amendment Evidence — ISSUE-035

Status: **PASS — AMENDED DESIGN READY FOR CANDIDATE FREEZE / PRODUCTION CLOSED**

Phase:
P11 — US SEC Provider

Historical reviewed candidate:
`00027be24be8e1c2ef3746600fa6e4f59ef641a5`

Authoritative stop:
`development/188-p11-final-path-concurrency-review-stop.md`

## P11-ISSUE-035 resolution

The deterministic final path remains:

`<parsed_root>/<parse_run_id>/export-v2`

but concurrent writers now have an exact no-overwrite commit protocol.

### Attempt-isolated staging

- staging root = `<parsed_root>/.staging`;
- each attempt uses `<parsed_root>/.staging/<parse_run_id>/<attempt_token>/export-v2`;
- `attempt_token` is diagnostic-only lowercase 32-hex from 128-bit OS CSPRNG entropy;
- attempt directory creation is exclusive;
- concurrent attempts never share writable staging;
- attempt token/staging/process identity never enter final export bytes or registry artifact_path;
- P11 v1 runtime cleanup removes only its own attempt staging and never auto-deletes another attempt's staging.

### Atomic no-replace final commit

One same-filesystem non-replacing atomic directory commit has exact outcomes:

- `COMMITTED_NEW`;
- `DESTINATION_EXISTS`;
- `COMMIT_ERROR`.

`DESTINATION_EXISTS` is not success and not collision by itself. It transitions to the existing ISSUE-033 verification path.

`COMMIT_ERROR` is `P11_FINAL_ARTIFACT_COMMIT_FAILED` / BLOCKED. Permission, invalid-path, cross-filesystem, I/O and unknown failures cannot be reclassified as destination-exists from a later existence observation.

### Concurrent loser

A losing writer that receives `DESTINATION_EXISTS` must:

- load/validate the immutable existing final export;
- verify requested parse_run_id and exact identity/package/parser/schema/config/validation semantics;
- compare all nine required final files byte-for-byte with its own validated staging export.

Exact equality:

- concurrent idempotent success;
- original final directory remains unchanged;
- only the loser's own staging may be retired;
- final reload succeeds before P11-K.

Mismatch/missing/invalid state:

`P11_FINAL_ARTIFACT_COLLISION` / BLOCKED.

### Runtime gate

P11-B must prove the target runtime provides an atomic same-filesystem no-replace directory commit primitive with distinguishable destination-exists semantics.

No copy/delete/replace fallback is allowed.

## Acceptance additions

Acceptance now requires:

- two concurrent same-parse_run_id attempts use different staging paths;
- both can produce byte-identical nine-file staging exports;
- exactly one commit returns COMMITTED_NEW;
- loser receives DESTINATION_EXISTS and succeeds only after exact existing-final verification;
- one-byte loser mismatch => P11_FINAL_ARTIFACT_COLLISION;
- permission/I/O/invalid-path commit failure => P11_FINAL_ARTIFACT_COMMIT_FAILED;
- no overwrite/delete/replace/mutation of final export;
- runtime cleanup never deletes another attempt's staging;
- P11-K is reached only after successful final reload.

## Regression boundary

PASS:

- ISSUE-010..034 remediation remains intact;
- no `src/` change;
- no `tests/` change;
- no `integration/` change;
- no `runtime-locks/` change;
- no registry schema migration;
- P0-P10 accepted contracts unchanged.

## Verdict

# PASS — READY FOR CANDIDATE FREEZE AND FRESH DETACHED DESIGN REVIEW

This does not authorize P11 production.

P11-B remains NOT AUTHORIZED until the exact amended candidate passes fresh detached P11-A design review.