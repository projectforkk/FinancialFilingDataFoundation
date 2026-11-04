# 239 - P11-D ISSUE-045 Final Detached Design Review Authorization

Status: **AUTHORIZED - EXACT ISSUE-045-REMEDIATED DESIGN CANDIDATE ONLY / IMPLEMENTATION STOPPED / PROVIDER PRODUCTION CLOSED**

Exact candidate:
`2e1f73aa92b259303aec0c5f195ce0ef63095256`

Design amendment commit:
`b0db6f65dbe8b9b2e1baf084409a4d3b25c7aa65`

Amendment evidence:
`development/238-p11-d-issue045-amendment-evidence.md = PASS`

Expected canonical Git-blob SHA256 of `design/31-p11-d-http-discovery-contract.md`:
`270b2cf4c29ce8ba338f076821a0cc6bc08748a021b051dd3cdb0a3076d1d1db`

Fresh detached review worktree:
`D:\Codex\FinancialFilingDataFoundation\worktrees\review\p11-d-design-issue045-final`

Required verdict: PASS / FAIL / BLOCKED.

Review must verify:
1. exact detached clean candidate and `git diff --check`;
2. design/governance-only changes since the prior accepted design baseline; no source/test/integration/runtime-lock changes;
3. canonical Git-blob SHA256 matches development/238;
4. shard basename exact byte grammar `0x21..0x7e`, exact `.json`, and exclusions `/ \ % ? #`;
5. provider invalid shard maps `P11_SUBMISSIONS_INVALID` before fetch and direct invalid history URL maps `P11_SOURCE_HOST_NOT_ALLOWED` before network;
6. raw accepted shard request-target is stdlib-sendable without percent rewriting;
7. redirect loop key exactly `("https", ascii_lowercase_host, 443, exact_path)`;
8. host case and absent-vs-explicit `:443` canonical-equivalent self-loop is rejected before redirect-count increment, next connection or extra outbound start;
9. distinct exact paths remain distinct and existing allowed redirects still work;
10. mandatory focused matrix is exactly 1..71 with new cases 69..71;
11. ISSUE-040..044 and all HTTP/rate/discovery/provenance/P11-D-P11-E boundaries remain unchanged;
12. no material implementation ambiguity remains.

PASS may authorize only a separate corrective P11-D implementation gate.
P11-D implementation remains STOPPED during review.
P11 provider production remains CLOSED.
