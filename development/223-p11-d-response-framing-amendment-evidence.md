# 223 — P11-ISSUE-043 HTTP Response Framing Amendment Evidence

Status: **PASS — ISSUE-043 REMEDIATED / AMENDED DESIGN READY FOR CANDIDATE FREEZE / IMPLEMENTATION CLOSED**

Historical ineligible candidate: `97da9773b8d9858e639ac60d9f60c96e2cc0f36d`

STOP: `development/222-p11-d-response-framing-review-stop.md`

Amended design/31 SHA256: `9dfe33fdcc2249970e56d90c7ddbc99f295410157a0851bf40b0f1630006af08`

## Remediation

The contract now freezes exact response-framing/header cardinality:

- Transfer-Encoding absent or exactly one field; if present, normalized entire value exactly `chunked`;
- repeated/list/parameter/unsupported Transfer-Encoding fails `P11_HTTP_FAILED`;
- Content-Length absent or exactly one field; repeats fail even if equal;
- Transfer-Encoding + Content-Length always fails before body read;
- chunked size accounting uses dechunked entity bytes and never applies Content-Length parity;
- non-chunked Content-Length requires exact EOF parity;
- Content-Type exactly one entire normalized `application/json`, no parameters;
- Content-Encoding absent or exactly one `identity`; repeats/lists/other codings fail;
- partial/failed header-send transition counts one outbound start; connection-preparation failure does not;
- Location and Retry-After cardinality are explicit;
- retry_count/redirect_count are logical-fetch-global and do not reset;
- eighth-start success is allowed and pending ninth-action reason mapping is exact.

## Live compatibility

Formal current SEC observations used the configured `SEC_USER_AGENT` without exposing its value. Both ticker mapping and Apple Submissions endpoints returned HTTP 200 with exactly one `Content-Type: application/json`, exactly one `Transfer-Encoding: chunked`, no Content-Length and no Content-Encoding. This is compatible with the amended framing contract.

## Scratch probe

`workspace/scratch/p11-issue043/framing_probe.py` => `P11_ISSUE_043_FRAMING_PROBE=PASS`. It covers accepted chunked and fixed-length shapes plus TE+CL, duplicate TE/CL, unsupported/list TE, Content-Type parameter rejection, non-identity Content-Encoding and Content-Length parity failure.

## Contract retention

ISSUE-043 does not change accepted User-Agent, TLS, endpoint, timeout, cap values, retry limits, rate-gate RESERVED/READY algorithm, official SEC schema rules, descriptor normalization, provenance semantics, candidate ordering, or P11-D/P11-E boundary.

Mandatory focused implementation tests = **68**.

No `src/`, `tests/`, `integration/` or production `runtime-locks/` file is changed.

## Verdict

# PASS

P11-ISSUE-043 is REMEDIATED. A new exact design candidate and fresh detached review are required. P11-D implementation remains NOT AUTHORIZED. P11 provider production remains CLOSED.
