# 227 — P11-D Outbound-Start Counter Invariant Review STOP

Status: **STOP — P11-ISSUE-044 OPEN / IMPLEMENTATION STOPPED / DESIGN AMENDMENT REQUIRED / PROVIDER PRODUCTION CLOSED**

Implementation authorization:
`development/226-p11-d-http-discovery-implementation-authorization.md`

Accepted design candidate under re-review:
`104df1e5f4fe18c1c106029ea9026a8d66bf6e04`

Task branch/worktree:
`task/p11-d-sec-http-discovery`
`D:\Codex\FinancialFilingDataFoundation\worktrees\active\p11-d-sec-http-discovery`

No P11-D production commit was created before this STOP. The task worktree may retain uncommitted authorized-scope implementation scratch only; implementation must not proceed until Design-First remediation passes review.

## P11-ISSUE-044

The accepted P11-D contract simultaneously freezes:

- initial emitted HTTP request start = 1;
- `retry_count <= 3` and every retry-caused new request increments retry_count;
- `redirect_count <= 3` and every followed redirect-caused new request increments redirect_count;
- connection-preparation failures emit no HTTP request and therefore add no outbound start;
- no other transition can emit a new HTTP request.

Therefore for any logical fetch that emits requests:

`outbound_start_count = 1 + retry_count + redirect_count`

and the structural maximum is:

`1 + 3 + 3 = 7`.

However design/31 additionally states that an eighth emitted start may succeed and that a pending ninth action is blocked by an absolute start cap of 8. The mandatory implementation suite also requires an eighth-start HTTP 200 case.

That state is unreachable without violating the separately frozen retry or redirect limits. The implementation authorization therefore exposed a material contract inconsistency, not an implementation defect.

## Required remediation

Before implementation resumes, freeze one coherent invariant:

1. exact relationship among outbound_start_count, retry_count and redirect_count;
2. reachable structural maximum;
3. terminal behavior after the maximum reachable seventh emitted start;
4. whether any separate absolute start cap remains normative or only defensive;
5. exact reason mappings for terminal 429 / retryable 5xx / redirect when individual retry/redirect budgets are exhausted;
6. focused tests must prove all reachable interleavings and that an eighth emitted start never occurs;
7. all HTTP framing, rate-per-second, security, discovery, provenance and P11-D/P11-E contracts remain unchanged.

## Verdict

# STOP

P11-ISSUE-044 is OPEN.

P11-D implementation is STOPPED and NOT AUTHORIZED to continue until a reviewed Design-First amendment closes this issue.
P11 provider production remains CLOSED.