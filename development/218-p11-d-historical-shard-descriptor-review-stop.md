# 218 — P11-D Historical Shard Descriptor Review STOP

Status: **STOP — P11-ISSUE-041 OPEN / CANDIDATE INELIGIBLE / P11-D IMPLEMENTATION CLOSED**

Reviewed exact candidate:
`702ec64ab327929d65b624e387316bea813ef22f`

Authorization:
`development/217-p11-d-issue040-final-design-review-authorization.md`

Fresh detached worktree:
`D:\Codex\FinancialFilingDataFoundation\worktrees\review\p11-d-design-702ec64`

## Checks passed before STOP

- exact candidate / detached / clean;
- `git diff --check` PASS;
- design-only scope PASS;
- canonical design/31 Git-blob SHA256 = `f4857f4e1837ae460059f1ab60bc5d61f4788ae034ef889590d519f8cb707e0f`, matching development/216;
- ISSUE-040 semantic/provenance separation PASS;
- XBRL non-null bool contract PASS;
- mandatory test numbering 1..49 PASS;
- prior HTTP/security/rate-gate values retained.

## P11-ISSUE-041

`filings.files` historical-shard descriptor validation is defined per row, but duplicate descriptor normalization is not frozen.

The contract does not specify what to do when the same historical shard `name` appears more than once, including cases where:

- every required descriptor field is identical;
- `name` is equal but `filingFrom` differs;
- `name` is equal but `filingTo` differs;
- `name` is equal but `filingCount` differs;
- descriptor input order changes.

Without an exact rule, implementations could choose incompatible behaviors such as:

- fetch every duplicate;
- first-wins;
- last-wins;
- name-only dedupe;
- dedupe only after overlap filtering.

Those choices can change:

- outbound request count / rate-gate behavior;
- which shard is fetched for a requested date window;
- whether conflicting provider metadata is detected;
- deterministic discovery behavior under provider array reordering.

This violates the review requirement that current/historical discovery and duplicate descriptor behavior be deterministic without implementation-time guessing.

## Required remediation

Freeze exact rules for:

1. descriptor validation before overlap filtering;
2. canonical descriptor identity fields;
3. exact duplicate descriptor dedupe;
4. same-name/different-required-field conflict handling;
5. canonical descriptor ordering;
6. fetch-at-most-once behavior for one shard name;
7. interaction with inclusive filing-window overlap;
8. focused tests for exact duplicate, conflicting duplicate and input-order invariance.

All ISSUE-040, HTTP, security and rate-gate semantics must remain unchanged.

## Verdict

# STOP

Candidate `702ec64ab327929d65b624e387316bea813ef22f` is INELIGIBLE.

P11-ISSUE-041 is OPEN.

P11-D implementation remains NOT AUTHORIZED.
P11 provider production remains CLOSED.