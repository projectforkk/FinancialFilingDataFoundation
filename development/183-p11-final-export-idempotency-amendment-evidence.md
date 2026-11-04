# 183 — P11 Final Export Idempotency Amendment Evidence — ISSUE-033

Status: **PASS — AMENDED DESIGN READY FOR CANDIDATE FREEZE / PRODUCTION CLOSED**

Phase:
P11 — US SEC Provider

Historical reviewed candidate:
`992583b87af8f8c682dc434cc134317f4db35522`

Authoritative stop:
`development/182-p11-final-export-collision-review-stop.md`

## P11-ISSUE-033 resolution

The deterministic final artifact path:

`<parsed_root>/<parse_run_id>/export-v2`

is now explicitly immutable and idempotent.

### Final path absent

P11-I:

1. writes complete staging export;
2. loads/verifies staging;
3. atomically moves/renames staging to final path;
4. reloads/verifies final path;
5. permits P11-K only after successful final reload.

### Final path already exists

P11-I never overwrites, deletes, replaces or mutates the existing final export.

It must:

- load/verify existing final export;
- verify exact requested parse_run_id;
- verify document/package/parser/schema/config/identity/validation semantics;
- compare every required artifact file byte-for-byte against newly generated staging.

Exact match:

- idempotent success;
- existing final directory remains unchanged;
- staging is discarded/retired;
- P11-K may proceed.

Any mismatch/missing/invalid state:

`P11_FINAL_ARTIFACT_COLLISION`

and BLOCKED.

### Registry failure recovery

If P11-K persistence fails after a valid final export exists:

- final artifact remains immutable;
- no registry row => artifact is not reusable by the package-aware selector;
- later retry may regenerate staging, idempotently verify the existing final export, and retry registry persistence;
- no second final path is created;
- final artifact is not deleted merely due to registry failure.

### Staging

- never registry-eligible;
- never reusable;
- normal runtime never infers success from staging presence;
- cleanup must prove target is under the configured staging root, is not the final path, and has no registry reference.

## Error / acceptance surface

Added exact reason:

`P11_FINAL_ARTIFACT_COLLISION`

Acceptance now requires:

- first absent-path atomic commit;
- byte-identical retry = idempotent success;
- one-byte difference = collision;
- missing required final file = collision;
- existing final identity mismatch = collision;
- no overwrite/delete/mutation of final export;
- simulated registry failure leaves valid orphan final export;
- later retry can verify existing final and persist registry;
- unregistered orphan is not a reuse candidate;
- staging is never registered/reused.

## Regression boundary

PASS:

- ISSUE-010..032 remediation remains intact;
- no `src/` change;
- no `tests/` change;
- no `integration/` change;
- no `runtime-locks/` change;
- P0-P10 accepted contracts unchanged.

## Verdict

# PASS — READY FOR CANDIDATE FREEZE AND FRESH DETACHED DESIGN REVIEW

This does not authorize P11 production.

P11-B remains NOT AUTHORIZED until the exact amended candidate passes fresh detached design review and P11-A is formally closed.
