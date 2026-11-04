# 220 — P11-ISSUE-041 / 042 Design Amendment Evidence

Status: **PASS — ISSUES-041-042 REMEDIATED / AMENDED DESIGN READY FOR CANDIDATE FREEZE / P11-D IMPLEMENTATION CLOSED**

Historical ineligible candidates:

- `54d132024065f02e92621a68aabd1da278da5c9a` — P11-ISSUE-040;
- `702ec64ab327929d65b624e387316bea813ef22f` — P11-ISSUE-041.

Stops:

- `development/218-p11-d-historical-shard-descriptor-review-stop.md`;
- `development/219-p11-d-discovery-candidate-ordering-preflight-stop.md`.

Amended contract:
`design/31-p11-d-http-discovery-contract.md`

Amended contract SHA256:
`06c360c378e9e8559f052a5916e5d69e3e41539c832cc73f308688344bb7c009`

## ISSUE-041 remediation — historical descriptor normalization

PASS.

Frozen sequence:

1. validate every `filings.files` descriptor before overlap filtering;
2. normalized required tuple = `(name, filingFrom, filingTo, filingCount)`;
3. group by exact case-sensitive `name`;
4. identical required tuples dedupe, including when ignored extra SEC metadata differs;
5. same name + any different required field => `P11_SUBMISSIONS_INVALID`;
6. first-wins / last-wins forbidden;
7. canonical descriptor order = `(filingFrom, filingTo, name)`;
8. only then apply inclusive filing-window overlap;
9. each selected shard name fetched exactly once in canonical order.

This makes descriptor input order, duplicate rows and overlap filtering deterministic.

## ISSUE-042 remediation — candidate ordering

PASS.

`SecDiscoveryCandidate` is now:

`@dataclass(frozen=True, slots=True)`

with no generated rich ordering.

Semantics:

- equality/hash use semantic `compare=True` fields;
- `submission_source_urls = field(compare=False)` stays outside equality/hash;
- optional `report_date` / `primary_doc_description` are never compared through generated `<` ordering;
- every discovery output sort uses the explicit canonical key `(filing_date, accession_number)`.

## Security preflight hardening retained in same amendment

PASS.

Before the next freeze, the design also made already-required security boundaries exact:

- rate directory is derived only from the explicit canonical project root;
- rate path must resolve inside that root;
- symlink/junction/reparse escape and non-regular lock/state/temp paths fail closed;
- TLS uses verified `ssl.create_default_context()` + hostname verification;
- no HTTP(S) proxy environment dispatch in P11-D stdlib transport;
- no unverified SSL-context escape hatch;
- prepared connection is closed if later rate-gate acquisition/validation fails.

No P11 capability was expanded.

## Scratch semantic probe

`workspace/scratch/p11-issues041042/semantic_probe.py`

Result:

- `P11_ISSUES_041_042_SEMANTIC_PROBE=PASS`;
- canonical descriptor count after exact-duplicate collapse = 2;
- all descriptor input permutations yielded the same canonical tuple;
- same-name conflicting required metadata raised `P11_SUBMISSIONS_INVALID` in the probe model;
- provenance-different candidates remained equal with equal hashes;
- auto rich ordering was absent.

## Static amendment guard

`workspace/scratch/p11-issues041042/amendment_guard.py`

Result:

- `P11_ISSUES_041_042_AMENDMENT_GUARD=PASS`;
- `MANDATORY_TESTS=56`;
- `HTTP_RATE_SECURITY_CONTRACT_RETAINED=PASS`;
- `PRODUCTION_TEST_RUNTIME_DIFF=NONE`;
- `git diff --check` PASS.

## Preserved accepted contracts

Unchanged:

- P11-A/B/C production behavior;
- `SEC_USER_AGENT` grammar/privacy;
- exact endpoint/content-class rules;
- 10s connect / 10s header-send / 30s read / 120s logical deadline;
- 16/32/16 MiB JSON caps;
- redirect/retry/Retry-After limits;
- 8 req/s / >=125 ms actual request-start spacing;
- RESERVED/READY crash-safe rate gate;
- official SEC JSON field/type validation;
- ISSUE-040 provenance semantic separation;
- P11-D/P11-E boundary.

## Verdict

# PASS

P11-ISSUE-041 and P11-ISSUE-042 are REMEDIATED.

The amended P11-D design is ready for a new exact candidate freeze and fresh detached review.

P11-D implementation remains NOT AUTHORIZED.
P11 provider production remains CLOSED.
