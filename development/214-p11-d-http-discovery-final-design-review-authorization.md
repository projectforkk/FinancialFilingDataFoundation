# 214 — P11-D HTTP / Discovery Final Design Review Authorization

Status: **AUTHORIZED — FRESH DETACHED DESIGN REVIEW ONLY / P11-D IMPLEMENTATION CLOSED / PROVIDER PRODUCTION CLOSED**

Exact design candidate:
`54d132024065f02e92621a68aabd1da278da5c9a`

Design-freeze authorization:
`development/212-p11-d-http-discovery-design-freeze-authorization.md`

Amendment evidence:
`development/213-p11-d-http-discovery-design-amendment-evidence.md = PASS`

Normative P11-D contract:
`design/31-p11-d-http-discovery-contract.md`

Fresh detached review worktree:
`D:\Codex\FinancialFilingDataFoundation\worktrees\review\p11-d-design-54d1320`

## Required review

Verdict only: PASS / FAIL / BLOCKED.

Review must verify:

1. exact candidate HEAD, detached, clean, `git diff --check`;
2. candidate diff since `65a6da25a0608f6de0b08278fcc094ca68b57829` is design/governance/acceptance only, with no `src/`, `tests/`, `integration/`, `runtime-locks/` change;
3. design/31 SHA256 matches development/213;
4. design/26, design/27 and acceptance/41 consistently delegate exact P11-D HTTP/discovery semantics to design/31;
5. official SEC policy evidence supports declared User-Agent and current 10 requests/sec public ceiling, while FFDF remains <=8/no-burst;
6. `SEC_USER_AGENT` configuration grammar is explicit, fail-closed and never fabricates/logs raw contact identity;
7. canonical project-root/rate-gate scope cannot silently derive from cwd/worktree;
8. content-class URL grammar cannot become an arbitrary allowlisted-host fetch primitive;
9. timeout, response-size, content-type/encoding, redirect, retry, Retry-After and outbound-start ceilings are exact and mutually consistent;
10. rate-gate protocol controls actual HTTP header-send starts, not merely reservation times; RESERVED/READY crash semantics and safe lock failure are coherent;
11. official ticker-map `cik_str` integer and Submissions current/history parallel-array schemas match the frozen validator contract;
12. current + historical merge is deterministic under source/shard reorder, duplicate accessions, current/history overlap and amendment variants;
13. provenance-only fields cannot accidentally turn semantically equal duplicate filings into false conflicts or unstable identity;
14. HTTP/discovery diagnostics remain outside source/package/parsed identity unless later gates explicitly include them;
15. P11-D does not authorize P11-E primary/index/taxonomy/exhibit/package fetch or writes;
16. P11-A/B/C accepted source behavior remains unchanged;
17. the 46 mandatory implementation tests cover the public/API/security/concurrency/discovery contract sufficiently;
18. manual semantic/cross-gate review finds no remaining material implementation-time ambiguity.

PASS authorizes only a later separate P11-D implementation authorization.

Any material ambiguity => STOP; open the next P11 issue; candidate becomes ineligible; Design-First amendment required.

P11-D implementation remains CLOSED during this review.
P11 provider production remains CLOSED.