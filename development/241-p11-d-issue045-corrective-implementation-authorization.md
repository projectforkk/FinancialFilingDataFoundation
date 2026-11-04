# 241 - P11-D ISSUE-045 Corrective Implementation Authorization

Status: **AUTHORIZED - CORRECTIVE P11-D IMPLEMENTATION/UNIT TESTS ONLY / PROVIDER PRODUCTION CLOSED**

Accepted amended design candidate:
`2e1f73aa92b259303aec0c5f195ce0ef63095256`

Final design review:
`development/240-p11-d-issue045-final-detached-design-review-result.md = PASS`

Historical implementation candidate:
`be5f332cb4f6839fa85e1f82ebd91ca7cae52e33` = INELIGIBLE per development/237.

Implementation branch/worktree:
- `task/p11-d-sec-http-discovery`
- `D:\Codex\FinancialFilingDataFoundation\worktrees\active\p11-d-sec-http-discovery`

Authorized production scope remains only:
`src/financial_filing_data_foundation/sec/`

Authorized tests remain only:
`tests/unit/sec/`

Corrective implementation must:

1. enforce historical shard basename bytes exactly `0x21..0x7e`;
2. reject SP, control, non-ASCII, `/`, `\`, `%`, `?`, `#` and wrong-case `.json` suffix;
3. map invalid provider shard names to `P11_SUBMISSIONS_INVALID` before shard fetch;
4. map invalid direct history URL basename to `P11_SOURCE_HOST_NOT_ALLOWED` before network;
5. never percent-encode or rewrite an invalid shard basename into acceptability;
6. use redirect loop identity exactly `("https", ascii_lowercase_host, 443, exact_path)` after URL validation;
7. initialize visited identity from the initial request;
8. reject canonical-equivalent seen redirect before redirect-count increment, next connection, rate gate or extra outbound start;
9. preserve distinct valid path redirects and all prior ISSUE-040..044 behavior;
10. add mandatory focused cases 69..71 and retain 1..68 unchanged.

Before new candidate freeze:

- mandatory cases exactly 1..71 with no gaps;
- focused `tests/unit/sec` PASS;
- full `tests/unit` PASS with short project-local basetemp;
- compile/import PASS;
- `git diff --check` PASS;
- no files outside authorized SEC source/tests changed by corrective implementation;
- no real SEC network is required for unit acceptance.

No new third-party dependency is authorized.
No P11-E/acquisition/package/index/taxonomy/exhibit, registry, identity/planner, runtime-lock, Research MCP or provider-production change is authorized.

STOP if the amended contract cannot be implemented inside this scope.
