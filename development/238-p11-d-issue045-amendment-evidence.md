# 238 - P11-ISSUE-045 URL Canonicalization / Shard Request-Target Amendment Evidence

Status: **PASS - ISSUE-045 REMEDIATED AT DESIGN LEVEL / FRESH DETACHED DESIGN REVIEW REQUIRED / IMPLEMENTATION STOPPED**

STOP:
`development/237-p11-d-url-canonicalization-review-stop.md`

Design amendment commit:
`b0db6f65dbe8b9b2e1baf084409a4d3b25c7aa65`

Canonical Git-blob SHA256 of amended `design/31-p11-d-http-discovery-contract.md`:
`270b2cf4c29ce8ba338f076821a0cc6bc08748a021b051dd3cdb0a3076d1d1db`

## Remediation A - exact historical shard request-target grammar

Frozen grammar:

- source only from current Submissions `filings.files[].name`;
- non-empty raw ASCII bytes in exact range `0x21..0x7e`;
- SP `0x20`, DEL, controls and non-ASCII rejected;
- `/`, `\`, `%`, `?`, `#` rejected;
- suffix `.json` exact case-sensitive;
- accepted spelling appended as one unescaped request-target segment;
- no percent-encoding or rewriting fallback.

Reason mapping:

- invalid provider descriptor name => `P11_SUBMISSIONS_INVALID` before shard fetch;
- direct invalid `SUBMISSIONS_HISTORY_JSON` URL => `P11_SOURCE_HOST_NOT_ALLOWED` before network.

This removes the old ambiguity between User-Agent visible-ASCII terminology, stdlib request-target legality and the frozen no-percent-alternative rule.

## Remediation B - exact redirect-loop identity

Frozen internal key after URL validation:

`("https", ascii_lowercase_host, 443, exact_path)`

Semantics:

- absent port and explicit `:443` are identical;
- host case is normalized to ASCII lowercase;
- path remains exact/case-sensitive;
- query/fragment are absent by existing URL contract;
- initial request key is inserted before redirects;
- a seen key fails `P11_REDIRECT_NOT_ALLOWED` before redirect-count increment, next-hop connection preparation, rate-gate acquisition or extra outbound start;
- `requested_url` / `final_url` external string semantics remain unchanged.

## Project-local probe

`workspace/scratch/p11-issue045/issue045_probe.py`

PASS:

- valid safe shard basenames can be passed to stdlib `http.client.putrequest()` as raw request-targets;
- SP / percent / path-unsafe shard examples are rejected by the frozen model;
- host-case + explicit-443 equivalent URLs produce the same canonical loop key;
- distinct exact paths remain distinct.

Probe result markers:

- `VALID_SHARD_RAW_REQUEST_TARGETS=PASS`;
- `SP_PERCENT_UNSAFE_SHARDS_REJECTED=PASS`;
- `CANONICAL_EQUIVALENT_LOOP_KEY=PASS`;
- `DISTINCT_PATH_KEY_REMAINS_DISTINCT=PASS`;
- `P11_ISSUE045_PROBE=PASS`.

## Mandatory matrix

Implementation focused cases are now exactly **1..71** with no gaps.

New cases:

- 69 = provider shard basename grammar and exact preservation;
- 70 = direct history URL invalid basename rejection with no percent fallback;
- 71 = canonical-equivalent redirect loop blocked before redirect count / second connection / outbound start.

## Preserved contracts

Unchanged:

- ISSUE-040..044 remediations;
- SEC User-Agent/privacy;
- verified direct TLS / no proxy dispatch;
- timeout/deadline/framing/body caps/retry/Retry-After;
- shared RESERVED/READY rate gate and 8 starts/second / >=125 ms spacing;
- discovery schema, descriptor ordering, accession/provenance semantics;
- P11-A/B/C accepted behavior;
- P11-D/P11-E boundary.

No `src/`, `tests/`, `integration/` or production `runtime-locks/` file changed in this design amendment.

## Verdict

# PASS

P11-ISSUE-045 is REMEDIATED at design level.
Implementation remains STOPPED until a new exact design candidate passes fresh detached review and a separate corrective implementation authorization is issued.
P11 provider production remains CLOSED.
