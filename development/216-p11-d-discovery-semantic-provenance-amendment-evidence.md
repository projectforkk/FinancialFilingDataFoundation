# 216 — P11-ISSUE-040 Discovery Semantic / Provenance Amendment Evidence

Status: **PASS — ISSUE-040 REMEDIATED / AMENDED DESIGN READY FOR CANDIDATE FREEZE / P11-D IMPLEMENTATION CLOSED**

Historical ineligible candidate:
`54d132024065f02e92621a68aabd1da278da5c9a`

Review STOP:
`development/215-p11-d-discovery-semantic-provenance-review-stop.md`

Amended normative contract:
`design/31-p11-d-http-discovery-contract.md`

Amended contract SHA256:
`f4857f4e1837ae460059f1ab60bc5d61f4788ae034ef889590d519f8cb707e0f`

## Remediation A — semantic filing identity vs discovery provenance

PASS.

Public candidate now uses:

`submission_source_urls: tuple[str, ...] = field(compare=False)`

Frozen semantics:

- each source row starts with exactly one canonical requested current/history Submissions JSON URL;
- redirect final URL is diagnostic only and does not enter this tuple;
- provenance is excluded from dataclass equality/order and filing semantic identity;
- same-accession rows compare only semantic fields;
- semantic-equal duplicates dedupe;
- contributing provenance becomes ASCII-lexicographically sorted unique union;
- duplicate provenance URL collapses;
- different semantic field still fails with `P11_SUBMISSIONS_INVALID`;
- `dataclasses.asdict()` / full serialized equality cannot be used as semantic duplicate comparator without removing provenance.

This closes the false-conflict case where current Submissions and a historical shard contain the same filing under different source URLs.

## Remediation B — XBRL boolean nullability

PASS.

Public candidate fields are now exactly:

- `is_xbrl: bool`;
- `is_inline_xbrl: bool`.

They match the already frozen validator:

- both arrays required;
- JSON integer values exactly 0/1;
- normalized accepted candidate values non-null bool.

No accepted state can now contain `None` for these fields.

## Acceptance / test amendment

`acceptance/41-p11-acceptance-instruction.md` now mirrors:

- provenance-excluded filing semantic equality;
- sorted-unique provenance union;
- semantic conflicts still block;
- non-null candidate XBRL booleans.

Mandatory P11-D focused implementation cases increased from 46 to **49** with explicit coverage for:

- non-null public XBRL bool fields;
- current/history same-accession equal-semantic rows with different provenance URLs;
- provenance content/order excluded from equality/order and false-conflict behavior.

## Preserved P11-D contract

PASS.

ISSUE-040 does not change the previously frozen:

- SEC User-Agent grammar/privacy boundary;
- canonical project-root rate scope;
- content-class URL grammar;
- connect/header/read/logical timeouts;
- response-size caps;
- redirect/retry/Retry-After limits;
- 8 req/s no-burst / 125 ms actual-start spacing;
- RESERVED/READY kernel-lock protocol;
- response/content encoding rules;
- official ticker/Submissions schema rules;
- P11-D/P11-E capability boundary.

The existing rate-gate design probe remains valid:

- minimum actual simulated send gap >=125 ms;
- half-open one-second maximum <=8;
- corrupt/RESERVED/crash recovery >=125 ms;
- 5-second lock-acquisition fail-closed test PASS.

## Static amendment guard

`workspace/scratch/p11-issue040-amendment-guard.py`

Result:

- `P11_ISSUE_040_AMENDMENT_GUARD=PASS`;
- `MANDATORY_TESTS=49`;
- `HTTP_RATE_CONTRACT_RETAINED=PASS`;
- `PRODUCTION_TEST_RUNTIME_DIFF=NONE`;
- `git diff --check` PASS.

## Scope audit

PASS.

No `src/`, `tests/`, `integration/` or production `runtime-locks/` file is changed by the amendment.

P11-A/B/C accepted implementation remains unchanged.

## Verdict

# PASS

P11-ISSUE-040 is REMEDIATED.

The amended P11-D design is ready for a new exact candidate freeze and fresh detached design review.

P11-D implementation remains NOT AUTHORIZED.
P11 provider production remains CLOSED.
