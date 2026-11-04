# 212 — P11-D Design-First HTTP / Discovery Contract Freeze Authorization

Status: **AUTHORIZED — DESIGN FREEZE ONLY / P11-D IMPLEMENTATION NOT AUTHORIZED / PROVIDER PRODUCTION CLOSED**

Prerequisites:

- P11-A Design Baseline = CLOSED / PASS;
- P11-B Environment / SEC Runtime Probe = CLOSED / PASS;
- P11-C Identity / Period Contract = CLOSED / PASS (`development/211-p11-c-final-detached-code-review-result.md`).

## Authorized design scope

Create and freeze a dedicated normative contract:

`design/31-p11-d-http-discovery-contract.md`

Amend only the minimum governance/design references required to make that contract authoritative:

- `design/26-p11-sec-provider-design.md`;
- `design/27-p11-implementation-plan.md`;
- `acceptance/41-p11-acceptance-instruction.md`;
- `design/00-design-management-index.md`;
- `design/01-project-detailed-design.md`;
- `development/01-development-roadmap.md`;
- `PROJECT_STATUS.md`;
- P11-D design-freeze evidence/review artifacts under `development/`.

## Mandatory frozen content

The amendment MUST freeze exact:

1. User-Agent configuration source and validation grammar without storing/fabricating contact identity;
2. request headers used for SEC discovery JSON;
3. HTTPS/host/port/userinfo/redirect validation;
4. connect/read/logical-fetch timeout values;
5. endpoint/content-class response-size caps;
6. content-type and UTF-8 JSON handling;
7. retryable/non-retryable status/transport classes;
8. retry count and deterministic backoff schedule;
9. Retry-After parsing/maximum wait behavior;
10. redirect count and total outbound-start cap;
11. project-root-shared cross-process 8 req/s no-burst gate;
12. exact rate-gate lock/state paths and state schema;
13. stale/crashed/corrupt rate-state recovery without deleting/breaking a live kernel lock;
14. exact mapping to existing P11 HTTP/security reason codes;
15. deterministic current + historical Submissions merge, duplicate-accession handling and stable ordering;
16. exact boundary between P11-D discovery and later P11-E package acquisition.

## External policy constraint

Current SEC official guidance states a maximum of 10 requests/second aggregate and requires a declared User-Agent for scripted EDGAR access. The accepted FFDF internal ceiling remains stricter: <=8 requests/second aggregate, no burst, >=125 ms between request starts.

Official source used for design verification:
`https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data`

## Explicitly prohibited

- no P11-D production code;
- no SEC HTTP client implementation;
- no source/test changes;
- no runtime-lock mutation;
- no acquisition/package-store implementation;
- no change to accepted P11-A/B/C production behavior;
- no Research MCP / Semantic Resolver production.

After the amendment is frozen, it requires a fresh detached design review before P11-D implementation can be separately authorized.

P11 provider production remains CLOSED.