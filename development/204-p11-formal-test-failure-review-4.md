# 204 — P11 Formal Test Execution 4 Failure Review

Status: **EXECUTION_FAIL / FORMAL_ACCEPTANCE_NOT_PASSED**

This record independently reviews the Formal Test Execution 4 failure against
the frozen production candidate. It is not an acceptance pass, merge
authorization, or P11 DONE record.

## 1. Exact authority

- Repository: `projectforkk/FinancialFilingDataFoundation`
- Formal candidate:
  `6eaace08c9ba5fb26809a7e02de5835123fb667a`
- Review PASS:
  `50baac22baf40b29fd08224b883c7b43f06f7736`
- Formal Test Plan 4:
  `4d2ca9abd9ed60d5b4bee8f2f76a2568baa67030`
- Formal execution authorization:
  `a63fe518dfa4ef1cfe1b8c27f607ed59668630cc`
- `FFDF_P11_US_DEV`: absent
- SEC contact: configured; value not recorded
- Production/test changes during Formal Test: none

No execution evidence commit was created because the executor stopped at the
first production defect, as authorized.

## 2. Formal gate disposition

```text
FT-00 .. FT-09: PASS
FT-10: FAIL
FT-11 .. FT-17: BLOCKED BY FORMAL STOP

OVERALL:
EXECUTION_FAIL
```

Deterministic regression evidence reported:

```text
ISSUE-146 = 9 passed
Review-5/6 focused aggregate = 79 passed
US SEC = 253 passed
MCP-focused = 93 passed
P0-P10 = 371 passed
full unit = 783 passed
compileall = PASS
git diff --check = PASS
legacy v2 immutability = PASS
corrupt v3 fail-closed = PASS
```

## 3. FT-10 live receipt

The initial Apple FY2025 live acquire succeeded:

```text
accession = 0000320193-25-000079
observation_sha256 =
ff12d767427f1a7667ce16e2cff69e55e26618fe447f18652a60f047b1173641

package_sha256 =
1196a354461ac65afa4ce7f1c67b2d65b04c1e496f521f34a139c6d6e5872d3d

current submissions fetches = 1
history fetches = 0
archive member fetches = 7
unrelated static-asset fetches = 0
```

The subsequent normal online ingest failed:

```text
exit code = 10
reason = P11_SOURCE_DRIFT
message = SEC ticker snapshot is immutable and differs
```

This is a production defect, not an external SEC outage and not fixture drift.

## 4. Independent code confirmation

Exact candidate code persists ticker-map snapshots at:

```text
workspace/ingest/us/ticker-map/<source_sha256>.json
```

The serialized snapshot includes:

```text
source_url
source_sha256
retrieved_at
source_bytes_b64
mapping
```

A fresh online ticker lookup creates a new `retrieved_at` even when the
official source bytes and `source_sha256` are identical.

Because the path is derived only from `source_sha256`, the second observation
targets the same file. The persistence code compares the entire serialized
payload byte-for-byte and raises `P11_SOURCE_DRIFT` because only
`retrieved_at` changed.

The reported read-only verification that the source-byte SHA is unchanged is
therefore consistent with the code-level root cause.

## 5. New blocking issue

```text
P11-ISSUE-147
TICKER-MAP SOURCE IDENTITY IS CONFLATED WITH RETRIEVAL-OBSERVATION IDENTITY
```

Design 26 requires caching exact official ticker-map bytes, source SHA, source
URL, and retrieved_at, and local status may use the newest verified cached
snapshot.

Therefore two online retrievals of identical source bytes at different
`retrieved_at` values are two legitimate retrieval observations, not source
drift.

The current `<source_sha256>.json` identity cannot represent that requirement
without either mutating the old observation or falsely rejecting the new one.

## 6. Lifecycle consequence

```text
FORMAL TEST EXECUTION 4:
EXECUTION_FAIL

FORMAL ACCEPTANCE:
NOT PASSED

CANDIDATE 6eaace08:
HISTORICAL REVIEW_PASS → FORMAL_EXECUTION_FAIL

MAIN MERGE:
NOT AUTHORIZED

P11 DONE:
NO

NEXT ACTION:
DESIGN CORRECTION FOR ISSUE-147
```

No FT-11..FT-17 result may be inferred from the blocked run.
