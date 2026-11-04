# 237 - P11-D URL Canonicalization / Shard Request-Target Review STOP

Status: **STOP - P11-ISSUE-045 OPEN / IMPLEMENTATION CANDIDATE INELIGIBLE / DESIGN AMENDMENT REQUIRED / PROVIDER PRODUCTION CLOSED**

Reviewed implementation candidate:
`be5f332cb4f6839fa85e1f82ebd91ca7cae52e33`

Review authorization:
`development/236-p11-d-final-code-review-authorization.md`

Fresh detached worktree:
`D:\Codex\FinancialFilingDataFoundation\worktrees\review\p11-d-be5f332-final`

Integrity checks before STOP:

- detached HEAD exact candidate = PASS;
- detached / branchless / clean = PASS;
- `git diff --check` = PASS;
- changed-file scope = exact authorized six SEC source files plus three SEC unit-test files;
- pre-freeze evidence remains historical: focused = 87 PASS, full unit = 564 PASS.

## P11-ISSUE-045A - historical shard request-target grammar is not implementably exact

The accepted design states:

- User-Agent "visible ASCII" explicitly means bytes `0x20..0x7e`;
- historical shard name is a non-empty "visible ASCII basename";
- historical URL is constructed as `https://data.sec.gov/submissions/<validated-shard-basename>`;
- percent-encoded path alternatives are not canonical and are rejected;
- P11-D must use standard-library HTTP transport.

Using the same visible-ASCII terminology, byte `0x20` (SP) is accepted by the current shard grammar. But Python standard-library `http.client.HTTPConnection.putrequest()` rejects a raw request-target containing SP with `InvalidURL` before any HTTP bytes are emitted. A project-local, no-network probe confirmed:

- `/submissions/normal.json` => accepted by `putrequest`;
- `/submissions/ leading.json` => `InvalidURL`;
- `/submissions/in terior.json` => `InvalidURL`.

The contract therefore does not currently freeze whether shard SP must be rejected at provider-data validation or encoded for transport; encoding would conflict with the separately frozen no-percent-alternative rule. Implementation must not choose ad hoc.

## P11-ISSUE-045B - redirect-loop identity is under-specified

The accepted URL rules allow:

- case-insensitive host comparison after ASCII lowercase normalization;
- explicit port `443` as equivalent allowed authority spelling.

The redirect contract rejects loops, but does not freeze the identity key used for loop detection. Raw-string loop tracking treats, for example:

- `https://data.sec.gov/submissions/CIK0000320193.json`
- `https://DATA.SEC.GOV:443/submissions/CIK0000320193.json`

as different strings even though they resolve to the same accepted logical endpoint under Section 7. That can permit an unnecessary additional outbound request before loop/redirect limits stop the flow.

## Required Design-First remediation

Before implementation correction resumes, freeze:

1. exact historical shard basename byte grammar, including whether SP `0x20` is permitted;
2. exact request-target construction rule consistent with stdlib transport and the no-percent-alternative rule;
3. exact canonical redirect-loop identity key after accepted scheme/host/port normalization;
4. whether loop detection occurs before `redirect_count` increment and before any next-hop connection/send;
5. exact reason mapping for invalid shard provider data vs invalid direct HTTP URL;
6. focused tests proving SP handling and canonical-equivalent self-loop rejection with no extra outbound start;
7. all ISSUE-040..044, framing, rate-gate, discovery/provenance and P11-D/P11-E boundaries remain unchanged.

## Verdict

# STOP

Candidate `be5f332cb4f6839fa85e1f82ebd91ca7cae52e33` is INELIGIBLE for P11-D acceptance.

P11-ISSUE-045 is OPEN.
P11-D implementation is STOPPED until a reviewed Design-First amendment closes ISSUE-045.
P11 provider production remains CLOSED.
