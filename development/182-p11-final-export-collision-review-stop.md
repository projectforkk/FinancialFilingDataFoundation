# 182 — P11 Final Design Review Stop — Final Export Collision / Idempotent Commit

Status: **FAIL / STOP — P11-ISSUE-033 / PRODUCTION CLOSED**

Phase:
P11 — US SEC Provider

Reviewed exact candidate:
`992583b87af8f8c682dc434cc134317f4db35522`

Fresh detached review:
`D:\\Codex\\FinancialFilingDataFoundation\\worktrees\\review\\p11-design-992583b`

Review authorization:
`development/181-p11-validation-finalization-final-review-authorization.md`

Automated review:

- ISSUE-010..031 matrix = PASS;
- ISSUE-032 freeze guard = PASS;
- P0-P10 production/test/runtime diff = NONE;
- git diff --check = PASS.

## Finding

Manual finalization/persistence review found one remaining implementation ambiguity.

P11 v2 final persistence path is deterministic:

`<parsed_root>/<parse_run_id>/export-v2`

and `parse_run_id` is deterministic for the same document/package/parser/config.

Therefore a retry/re-run can encounter an already existing final export directory.

Current design freezes atomic commit but does not state whether P11-I must:

- overwrite the existing final directory;
- delete/replace it;
- fail;
- verify/reuse it.

It also does not state what happens when:

1. P11-I successfully commits the final export;
2. P11-K registry persistence then fails;
3. a later retry reaches the same deterministic final path.

Without an exact contract, implementations can violate immutable-artifact semantics or create non-idempotent retries.

## P11-ISSUE-033 — final export collision / idempotent commit / orphan recovery

Required correction:

### 1. Never overwrite final export

A registry-eligible final `export-v2` directory is immutable.

P11-I MUST NOT:

- overwrite it;
- delete it for replacement;
- mutate any child file in place.

### 2. Final path absent

If final path does not exist:

- write complete staging export;
- final loader PASS in staging;
- atomically move/rename staging directory to final path;
- reload final path;
- only then permit P11-K.

### 3. Final path already exists

If final path already exists:

- do not replace it;
- load/verify the existing final export;
- existing manifest.parse_run_id must equal requested parse_run_id;
- document/package/parser/schema/config/identity/validation semantics must equal the current deterministic output;
- every required final artifact byte must equal the newly generated staging artifact byte.

If all required files are byte-identical and both existing/staging exports validate:

- discard/retire staging;
- treat final commit as idempotent success;
- proceed to P11-K.

If any required file differs, is missing, invalid, or identity differs:

`P11_FINAL_ARTIFACT_COLLISION`

and BLOCK.

No replacement is allowed.

### 4. Registry failure after successful final commit

If P11-K registry persistence fails after the final export is committed:

- keep the valid final artifact unchanged;
- no ParsedDataRecord means it is not reusable through package-aware selector;
- a later retry may perform the exact-existing-final verification above;
- after idempotent verification succeeds, retry registry persistence;
- do not create a second final artifact;
- do not delete the orphan final export merely because registry write failed.

### 5. Staging semantics

Staging is never registry-eligible.

A stale staging directory may be safely removed only by an explicitly scoped cleanup path that proves it is under the P11 staging root and is not the final export path.

Normal retry logic must not infer success from staging content.

### 6. Acceptance

Acceptance must prove:

- first commit to absent final path succeeds;
- retry with byte-identical deterministic staging => idempotent success;
- existing final with one-byte child difference => P11_FINAL_ARTIFACT_COLLISION;
- existing final missing required file => P11_FINAL_ARTIFACT_COLLISION;
- existing final identity mismatch => P11_FINAL_ARTIFACT_COLLISION;
- no final overwrite/delete/mutation occurs;
- simulated registry failure leaves valid final artifact;
- later retry verifies existing final and can persist registry;
- unregistered orphan final is not selected for reuse;
- staging path is never registered/reused.

## Scope

No production/test/runtime changes.

P11-ISSUE-010..032 remediation remains valid.

## Verdict

# FAIL / STOP

Candidate `992583b...` is INELIGIBLE for DESIGN READY.

P11 production remains CLOSED.
