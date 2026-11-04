# 188 — P11 Final Design Review Stop — Deterministic Final-Path Commit Concurrency

Status: **FAIL / STOP — P11-ISSUE-035 / PRODUCTION CLOSED**

Phase:
P11 — US SEC Provider

Reviewed exact candidate:
`00027be24be8e1c2ef3746600fa6e4f59ef641a5`

Fresh detached review:
`D:\\Codex\\FinancialFilingDataFoundation\\worktrees\\review\\p11-design-00027be`

Review authorization:
`development/187-p11-final-export-byte-determinism-final-review-authorization.md`

## Automated review

PASS:

- exact HEAD = `00027be24be8e1c2ef3746600fa6e4f59ef641a5`;
- detached worktree clean;
- `git diff --check` = PASS;
- P0-P10 production/test/runtime-lock diff = NONE;
- ISSUE-010..031 matrix = PASS;
- ISSUE-032..033 guard = PASS;
- ISSUE-034 byte-determinism guard = PASS;
- known package/source-asset fixture hashes remain stable.

## Finding

Manual final-path/concurrency review found one remaining material implementation-time ambiguity.

The design freezes the deterministic final path:

`<parsed_root>/<parse_run_id>/export-v2`

and currently says:

1. if final path is absent, atomically move/rename staging to final;
2. if final path already exists, verify the existing final export and allow byte-identical idempotent success.

This does not define the race where two processes for the same `parse_run_id` both observe the final path as absent.

Possible execution:

1. process A and process B each build and validate their own staging export;
2. both observe final path absent;
3. process A atomically commits first;
4. process B then attempts its atomic move/rename and receives destination-exists / equivalent no-replace conflict.

The current design does not say whether process B must fail, retry, classify collision, or transition into exact existing-final verification.

Because final bytes are deterministic, a byte-identical losing process should be able to converge safely to the same immutable final export. But that behavior is not yet frozen.

The review authorization explicitly requires manual inspection of concurrency/race behavior around deterministic final-path commit and no remaining material implementation-time ambiguity. Therefore candidate `00027be...` cannot PASS P11-A.

## P11-ISSUE-035 — concurrent deterministic final-path commit

Required correction:

### 1. Commit must be non-replacing

The final commit primitive MUST have fail-if-destination-exists / no-replace semantics.

It MUST NOT overwrite, delete, replace, merge into, or mutate an existing final export directory.

If the selected runtime cannot provide an atomic same-filesystem no-replace directory commit primitive, P11 production remains BLOCKED until the runtime design is amended and accepted.

### 2. Staging must be process-attempt isolated

Concurrent writers for the same `parse_run_id` MUST NOT share a writable staging directory.

Each attempt uses a distinct project-local staging directory under the configured P11 staging root.

Attempt-specific staging identity is diagnostic only and MUST NOT enter final `export-v2` bytes or registry `artifact_path`.

### 3. Exact race outcome

After staging loader PASS, P11-I attempts one non-replacing atomic commit to the deterministic final path.

Outcomes are exactly:

- `COMMITTED_NEW`: final path did not exist and this process created it;
- `DESTINATION_EXISTS`: another process or earlier attempt already created the final path;
- `COMMIT_ERROR`: any other commit failure.

`DESTINATION_EXISTS` is not by itself a collision and is not success.

### 4. Losing writer recovery

On `DESTINATION_EXISTS`, the losing process MUST transition to the existing-final verification path already defined by ISSUE-033:

- verify exact final directory/layout;
- load/validate existing final export;
- require exact `parse_run_id` and identity/package/parser/schema/config/validation semantics;
- compare all nine required final files byte-for-byte with this process's validated staging export.

If exact:

- classify as concurrent idempotent success;
- keep the existing final directory unchanged;
- discard/retire only this process's staging directory;
- reload the final path;
- then P11-K may proceed.

If any mismatch/missing/invalid state:

`P11_FINAL_ARTIFACT_COLLISION`

and BLOCK.

### 5. Other commit errors

`COMMIT_ERROR` MUST NOT be reclassified as destination-exists without positive evidence from the commit primitive.

Permission errors, cross-filesystem moves, invalid paths, I/O failures and unknown errors fail closed and MUST NOT infer success from final-path presence observed later.

### 6. Registry race remains separate

Concurrent P11-K persistence is not allowed to mutate final bytes.

Registry handling must preserve existing accepted uniqueness/idempotency semantics. A registry failure leaves the verified final export immutable; a later retry must re-enter existing-final verification before retrying persistence.

No unregistered orphan becomes reusable without a valid registry row.

### 7. Acceptance

Acceptance must prove at least:

- two independent processes/attempts use distinct staging directories for the same `parse_run_id`;
- both produce byte-identical nine-file staging exports;
- exactly one no-replace commit wins;
- losing commit receives `DESTINATION_EXISTS` and transitions to existing-final verification;
- loser succeeds idempotently only after loader/identity/all-nine-byte equality;
- no overwrite/delete/replace/mutation occurs;
- loser with one-byte staging difference => `P11_FINAL_ARTIFACT_COLLISION`;
- generic commit I/O/permission error does not become idempotent success;
- cleanup can remove only the losing attempt's staging path and cannot remove the final path or another live staging attempt;
- P11-K is reached only after successful final reload.

## Scope

No production/test/runtime changes.

P11-ISSUE-010..034 remediation remains valid.

## Verdict

# FAIL / STOP

Candidate `00027be24be8e1c2ef3746600fa6e4f59ef641a5` is INELIGIBLE for DESIGN READY.

P11-A remains OPEN/STOPPED.

P11-B remains NOT AUTHORIZED.

P11 production remains CLOSED.
