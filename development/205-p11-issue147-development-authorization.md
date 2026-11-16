# 205 — P11 ISSUE-147 Development Authorization

Status: **DESIGN_FREEZE_PASS / DEVELOPMENT_AUTHORIZED**

This record authorizes a narrow production/test correction for P11-ISSUE-147.
It is not a Formal Test Plan, Formal Acceptance, main-merge authorization, or
P11 DONE record.

## 1. Exact authority

Repository:

`projectforkk/FinancialFilingDataFoundation`

Authoritative remote lineage:

`reconcile/p11-140-143-local-chain`

Formal Test 4 failure review:

`development/204-p11-formal-test-failure-review-4.md`

Exact Design 39 freeze:

`fad6ee7512ec1f2f3da0c9a24c646959b2f45541`

Previous production candidate:

`6eaace08c9ba5fb26809a7e02de5835123fb667a`

Verdict:

```text
DESIGN_FREEZE_PASS
ISSUE-147 DEVELOPMENT_AUTHORIZED
```

## 2. Authorized scope

Implement only:

```text
P11-ISSUE-147
ticker-map source identity vs retrieval-observation identity
```

ISSUE-140..146 are regression-preservation scope only.

Do not redesign or reopen them unless a new blocking conflict is discovered.

## 3. Required persistence behavior

New online ticker-map observations must use:

```text
workspace/ingest/us/ticker-map/
  observations/
    <ticker_snapshot_id>.json
```

where:

```text
ticker_snapshot_id =
SHA256(
  canonical_json({
    source_url,
    lowercase source_sha256,
    normalized retrieved_at
  })
)
```

The persisted observation includes:

```text
snapshot_id
source_url
source_sha256
retrieved_at
source_bytes_b64
mapping
```

Different retrieval timestamps produce different observation identities even
when source bytes are identical.

That condition must not raise `P11_SOURCE_DRIFT`.

## 4. Immutability

A completed observation file is immutable.

If the exact same `ticker_snapshot_id` path already exists, canonical payload
content must match exactly.

A same-observation identity conflict uses the existing:

```text
P11_SOURCE_DRIFT
```

No new reason code is authorized.

## 5. Legacy compatibility

Historical files may exist at:

```text
workspace/ingest/us/ticker-map/<source_sha256>.json
```

They remain read-only and must not be rewritten, renamed, deleted, or used as
the persistence destination for new online observations.

Their bytes, source SHA, derivative mapping and retrieval metadata must be
verified before local status use.

## 6. Cached local status

Local status must select the newest verified cached snapshot first, then resolve
the requested ticker only against that selected snapshot.

Do not combine ticker mappings across historical snapshots.

Do not fall back to an older snapshot if the newest verified snapshot does not
contain the requested ticker.

Within one selected snapshot, multiple CIKs for one ticker remain a controlled
ambiguity.

## 7. retrieved_at

New observations require deterministic, timezone-aware ISO-8601
`retrieved_at`.

Normalize before computing the snapshot identity.

Invalid current-format timestamps use the existing
`P11_TICKER_SNAPSHOT_INVALID`.

## 8. Required tests

Implement every Design 39 T147 test, including:

```text
T147-01 same bytes / T1 vs T2
T147-02 normal repeated online acquire → ingest
T147-03 true same-observation payload conflict
T147-04 legacy file immutability
T147-05 source-byte tamper
T147-06 derivative tamper
T147-07 newest snapshot wins
T147-08 no stale older-snapshot fallback
T147-09 explicit CIK zero ticker-map fetch
T147-10 Formal FT-10 failure reproduction
```

The critical reproduction must prove:

```text
same official ticker-map bytes
different retrieval times
first ticker-based acquire succeeds
second ticker-based ingest succeeds past ticker persistence
P11_SOURCE_DRIFT is absent
```

## 9. Regression

Run at minimum:

- focused ISSUE-147 tests;
- complete `tests/unit/us_sec`;
- Review-5/6 focused regressions;
- MCP-focused regression;
- P0-P10 focused compatibility;
- full `tests/unit`;
- `python -m compileall -q src tests`;
- `git diff --check`.

Preserve:

```text
REGISTRY_SCHEMA_VERSION = 1
SEC_REGISTRY_SCHEMA_VERSION = 4
SEC_DISCOVERY_SCHEMA = p11-sec-discovery-v1
VIRTUAL_HTML_NORMALIZER_VERSION = VIRTUAL_HTML_V6
SEC_ARTIFACT_SCHEMA = p11-sec-artifacts-v2
SEC_VALIDATION_SCHEMA = p11-sec-validation-v3
```

## 10. Developer live smoke

After deterministic regression passes, rerun the Apple FY2025 production path
with `FFDF_P11_US_DEV` absent.

This developer smoke must exercise the exact failed boundary:

```text
ticker-based acquire
then ticker-based ingest
```

Record:

- exact candidate SHA;
- first and second ticker snapshot IDs;
- source SHA on both calls;
- retrieved_at on both calls;
- confirmation source SHA may be equal while snapshot IDs differ;
- accession;
- observation SHA;
- package SHA;
- history fetch count;
- archive member fetch count;
- static-asset fetch count;
- planner action;
- validation-v3 path/status;
- research_ready.

The second call must not fail with `P11_SOURCE_DRIFT`.

## 11. Candidate/evidence discipline

Create a new production/test candidate descending from this authorization.

Do not amend candidate
`6eaace08c9ba5fb26809a7e02de5835123fb667a`.

After exact-candidate regression and developer smoke, create a separate
documentation-only evidence file:

`development/206-p11-issue147-development-evidence.md`

Then STOP for ChatGPT Fresh Full Exact-Candidate Review.

## 12. Formal lifecycle boundary

The failed Formal Test 4 cycle is closed.

This task does not authorize resuming FT-11..FT-17.

A completely new Formal Test cycle will be created only after the new candidate
passes Fresh Full Exact-Candidate Review.

```text
FORMAL TEST PLAN 5:
NOT CREATED

FORMAL TEST EXECUTION:
NOT AUTHORIZED

FORMAL ACCEPTANCE:
NOT PASSED

MAIN MERGE:
NOT AUTHORIZED

P11 DONE:
NO
```

## 13. Git safety

Forbidden:

- force push / force-with-lease;
- rebase/history rewrite;
- reset --hard;
- clean -fd / clean -fdx;
- merge main;
- cherry-pick/merge divergent historical repair lines.

If Design 39 cannot be implemented as written, STOP and return to ChatGPT.
