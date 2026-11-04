# 234 - P11-D SEC HTTP / Discovery Implementation Resume Authorization

Status: **AUTHORIZED - P11-D IMPLEMENTATION/UNIT TESTS ONLY / PROVIDER PRODUCTION CLOSED**

Accepted final P11-D design candidate:
`af6917b1cf5c653aee66d5bee08f73cb7edbdc47`

Final detached design review:
`development/233-p11-d-issue044-final-detached-design-review-result.md = PASS`

Supersedes the stopped implementation authorization path:
- `development/226-p11-d-http-discovery-implementation-authorization.md` authorized the pre-ISSUE-044 implementation attempt;
- `development/227-p11-d-outbound-start-counter-review-stop.md` stopped it before any production commit;
- this authorization resumes implementation only after ISSUE-044 design remediation and fresh detached review PASS.

Implementation branch:
`task/p11-d-sec-http-discovery`

Implementation worktree:
`D:\Codex\FinancialFilingDataFoundation\worktrees\active\p11-d-sec-http-discovery`

Authorized production scope only:
`src/financial_filing_data_foundation/sec/`

Authorized tests only:
`tests/unit/sec/`

No new third-party dependency is authorized. P11-D v1 remains standard-library networking only.

Implementation must conform exactly to the accepted `design/31-p11-d-http-discovery-contract.md`, including all 68 mandatory focused cases and the ISSUE-044 correction:

- `outbound_start_count <= 1 + retry_count + redirect_count <= 7`;
- connection-preparation failures may make the first inequality strict;
- one logical fetch can emit at most 7 request starts;
- no valid path may emit an eighth request start;
- all 20 maximum retry/redirect interleavings must be tested;
- exhausted 429 => `P11_RATE_LIMITED`;
- exhausted retryable 5xx/transport/preparation => `P11_HTTP_FAILED`;
- fourth otherwise-valid redirect => `P11_REDIRECT_NOT_ALLOWED`;
- cross-process aggregate rate gate remains 8 starts/second with >=125 ms actual-start spacing.

Before candidate freeze, required evidence:

- focused `tests/unit/sec/` PASS covering all mandatory cases 1..68;
- full `tests/unit` regression PASS using a short project-local pytest basetemp;
- compile/import PASS;
- `git diff --check` PASS;
- changed production/tests remain exactly inside authorized P11-D scope;
- no P11-A/B/C behavioral regression;
- no network call in tests unless explicitly isolated/faked by the accepted test contract;
- no provider-production authorization implied.

Explicitly prohibited:

- no acquisition/package-store/primary/index/taxonomy/exhibit production code;
- no registry changes;
- no identity/planner changes;
- no runtime-lock changes;
- no P11-E or later implementation;
- no Research MCP / Semantic Resolver production;
- no provider production authorization.

STOP if the accepted contract cannot be implemented inside this scope.
