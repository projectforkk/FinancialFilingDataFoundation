# 240 - P11-D ISSUE-045 Final Detached Design Review Result

Status: **PASS - ISSUE-045 CLOSED / AMENDED P11-D DESIGN ACCEPTED / CORRECTIVE IMPLEMENTATION NOT YET AUTHORIZED / PROVIDER PRODUCTION CLOSED**

Reviewed exact candidate:
`2e1f73aa92b259303aec0c5f195ce0ef63095256`

Authorization:
`development/239-p11-d-issue045-final-design-review-authorization.md`

Fresh detached worktree:
`D:\Codex\FinancialFilingDataFoundation\worktrees\review\p11-d-design-issue045-final`

Design amendment commit:
`b0db6f65dbe8b9b2e1baf084409a4d3b25c7aa65`

Canonical Git-blob SHA256 of `design/31-p11-d-http-discovery-contract.md`:
`270b2cf4c29ce8ba338f076821a0cc6bc08748a021b051dd3cdb0a3076d1d1db`

## Integrity and scope

PASS:

- detached HEAD exact candidate;
- branchless and clean;
- `git diff --check` PASS;
- no `src/`, `tests/`, `integration/` or production `runtime-locks/` changes since prior accepted design;
- canonical Git blob hash verified from raw `git show` bytes using a subprocess byte stream, matching development/238 exactly.

## ISSUE-045A shard request-target grammar

PASS:

- accepted bytes exactly `0x21..0x7e`;
- SP `0x20`, DEL, controls, non-ASCII rejected;
- `/`, `\`, `%`, `?`, `#` rejected;
- `.json` suffix exact case-sensitive;
- no percent-encoding/rewrite fallback;
- accepted spelling can be emitted as a raw stdlib request-target segment;
- invalid provider shard name => `P11_SUBMISSIONS_INVALID` before fetch;
- invalid direct history URL => `P11_SOURCE_HOST_NOT_ALLOWED` before network.

## ISSUE-045B redirect canonical loop identity

PASS:

- exact key = `("https", ascii_lowercase_host, 443, exact_path)`;
- absent port and explicit `:443` are identical;
- host case is normalized;
- path remains exact/case-sensitive;
- equivalent seen key is rejected before redirect count, next connection, rate gate or extra outbound start;
- existing external requested/final URL string semantics remain unchanged;
- distinct exact paths remain distinct.

## Preserved contracts

PASS:

- ISSUE-040..044 remain intact;
- ISSUE-044 seven-start invariant remains frozen;
- aggregate 8 starts/second and >=125 ms spacing unchanged;
- TLS/timeout/framing/body/retry/Retry-After unchanged;
- discovery descriptor/accession/provenance semantics unchanged;
- P11-A/B/C accepted behavior unchanged;
- P11-D/P11-E boundary unchanged.

Mandatory implementation matrix = exact **1..71**.

## Verdict

# PASS

P11-ISSUE-045 is CLOSED.
Candidate `2e1f73aa92b259303aec0c5f195ce0ef63095256` is the accepted amended P11-D design baseline.

Corrective implementation requires a separate authorization.
P11 provider production remains CLOSED.
