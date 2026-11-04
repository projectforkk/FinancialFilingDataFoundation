# 228 - P11-ISSUE-044 Outbound-Start Invariant Amendment Evidence

Status: **PASS - ISSUE-044 REMEDIATED / AMENDED DESIGN READY FOR EXACT-CANDIDATE REVIEW / P11-D IMPLEMENTATION STOPPED**

Prior accepted design baseline under re-review:
`104df1e5f4fe18c1c106029ea9026a8d66bf6e04`

STOP:
`development/227-p11-d-outbound-start-counter-review-stop.md`

Amended contract:
`design/31-p11-d-http-discovery-contract.md`

Amended contract SHA256:
`497407adb368f8abbbe12afa1096fb7d9674d2fdb1a5778c8468b8f4b52dfaf9`

## Exact remediation

The logical-fetch accounting contract is now coherent with connection-preparation failures and the independent retry/redirect budgets:

- `outbound_start_count` counts only actual Section 14.3 step-7 send transitions, including partial/failed header sends;
- connection-preparation failure may consume retry budget but does not increment `outbound_start_count`;
- exact invariant: `outbound_start_count <= 1 + retry_count + redirect_count <= 7`;
- equality on the left holds only when the initial attempt and every counted retry/redirect reach the send transition;
- the maximum reachable emitted-start count for one logical fetch is exactly 7;
- no valid state-machine path emits an eighth start;
- the Section 3 aggregate rate limit remains independently 8 starts/second across processes;
- a count-7 pre-send guard remains only as a defensive impossible-state invariant and fails closed as `P11_HTTP_FAILED`.

Normal exhausted-budget mappings are frozen before another send can be scheduled:

- HTTP 429 with `retry_count == 3` => `P11_RATE_LIMITED`;
- retryable 5xx/transport/read/header-send/connection-preparation failure with `retry_count == 3` => `P11_HTTP_FAILED`;
- otherwise valid redirect with `redirect_count == 3` => `P11_REDIRECT_NOT_ALLOWED`.

Redirect accounting was also made exact: `redirect_count` increments when a validated follow is scheduled; the resulting hop increments `outbound_start_count` only if connection preparation succeeds and the hop reaches step 7.

## Semantic/static evidence

Project-local probe:
`workspace/scratch/p11-issue044/counter_probe.py`

PASS results:

- `INTERLEAVINGS=20` for every ordering of three retries plus three redirects;
- `MAX_REACHABLE_EMITTED_STARTS=7`;
- `EIGHTH_EMITTED_START_REACHABLE=NO`;
- `PREPARATION_FAILURE_STRICT_INEQUALITY=PASS`;
- `TERMINAL_REASON_MAPPING=PASS`;
- stale scan found no eighth-start/ninth-send/absolute-cap-8 logical-fetch wording;
- `git diff --check` PASS;
- production/test/integration/runtime-lock diff = NONE.

Mandatory P11-D focused case numbering remains 1..68. Cases 37-38 now prove the corrected invariant, all 20 maximum interleavings, seventh-response exhaustion mappings, and that an eighth emitted start is unreachable.

## Preserved contracts

Unchanged:

- SEC User-Agent/privacy policy;
- endpoint/content-class allowlist;
- TLS/host/project-root containment;
- timeout/deadline/body-size/framing/header rules;
- cross-process 8 req/s and >=125 ms actual-start spacing;
- RESERVED/READY crash-safe shared rate gate;
- official SEC JSON validation/discovery/provenance semantics;
- ISSUE-040..043 remediations;
- P11-D/P11-E boundary;
- P11-A/B/C accepted production behavior.

## Verdict

# PASS

P11-ISSUE-044 is REMEDIATED at design level. P11-D implementation remains STOPPED until a new exact candidate passes fresh detached design review and receives a separate implementation authorization.
P11 provider production remains CLOSED.
