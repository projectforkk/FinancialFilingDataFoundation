# 232 - P11-D ISSUE-044 Canonical-Hash Final Design Review Authorization

Status: **AUTHORIZED - FRESH DETACHED DESIGN REVIEW ONLY / IMPLEMENTATION STOPPED / PROVIDER PRODUCTION CLOSED**

Exact candidate:
`af6917b1cf5c653aee66d5bee08f73cb7edbdc47`

Historical ineligible review candidates:
- `760a4aa60a93c3d42570f7640798b80eaaad187e` - malformed evidence serialization per development/229;
- `63620f7360a91702016781e915ce71fac8fef848` - ambiguous hash basis per development/231.

Amendment evidence:
`development/228-p11-d-outbound-start-invariant-amendment-evidence.md = PASS`

Canonical design hash basis:
SHA256 MUST be computed over the exact Git blob bytes returned by `git show af6917b1cf5c653aee66d5bee08f73cb7edbdc47:design/31-p11-d-http-discovery-contract.md`, not checkout-transformed working-tree bytes.
Expected canonical Git-blob SHA256:
`497407adb368f8abbbe12afa1096fb7d9674d2fdb1a5778c8468b8f4b52dfaf9`

Fresh detached review worktree:
`D:\Codex\FinancialFilingDataFoundation\worktrees\review\p11-d-design-af6917b`

Required verdict: PASS / FAIL / BLOCKED.

Review must verify:
1. exact detached clean candidate and `git diff --check`;
2. design/governance-only scope; no source/test/integration/runtime-lock change;
3. canonical Git-blob SHA256 matches development/228 and the expected value above;
4. ISSUE-044 invariant `outbound_start_count <= 1 + retry_count + redirect_count <= 7` including strict inequality after connection-preparation failure;
5. maximum reachable emitted starts = 7 and eighth emitted start unreachable;
6. all 20 orderings of three retries and three redirects preserve the invariant and end at seven starts when every transition reaches send;
7. exact exhausted mappings: 429 => `P11_RATE_LIMITED`; retryable 5xx/transport/preparation => `P11_HTTP_FAILED`; fourth redirect => `P11_REDIRECT_NOT_ALLOWED`;
8. count-7 pre-send guard is defensive impossible-state handling only;
9. cross-process 8 starts/second and >=125 ms spacing remain unchanged;
10. ISSUE-040..043 and all HTTP framing/security/discovery/provenance contracts remain unchanged;
11. mandatory focused implementation cases are exactly 1..68, with 37-38 corrected and no stale eighth/ninth logical-fetch rule;
12. P11-A/B/C immutability and P11-D/P11-E boundary remain intact;
13. no material implementation ambiguity remains.

Any material ambiguity => STOP.
PASS may authorize only a separate implementation-resume gate.
P11-D implementation remains STOPPED during review.
P11 provider production remains CLOSED.
