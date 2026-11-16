# 39 — P11 Formal-Test-4 Ticker Snapshot Observation Identity Correction

Status: **AUTHORITATIVE DESIGN CORRECTION — ISSUE-147**

Development: **NOT YET AUTHORIZED**

This design corrects the production defect discovered by Formal Test Execution 4
against candidate `6eaace08c9ba5fb26809a7e02de5835123fb667a`.

It does not reopen ISSUE-140..146 except for regression preservation.

## 1. Formal failure

Formal Test 4 FT-10 proved:

```text
first Apple FY2025 acquire:
PASS

second normal online ingest:
P11_SOURCE_DRIFT
SEC ticker snapshot is immutable and differs
```

The official ticker-map source bytes and source SHA were unchanged.

The defect is caused by storing ticker snapshots at:

```text
ticker-map/<source_sha256>.json
```

while the immutable serialized payload also contains a per-retrieval
`retrieved_at`.

A second legitimate retrieval of identical official bytes therefore targets the
same filename but has a different observation timestamp.

## 2. ISSUE-147

```text
P11-ISSUE-147
TICKER-MAP SOURCE IDENTITY IS CONFLATED WITH RETRIEVAL-OBSERVATION IDENTITY
```

Design 26 already requires:

- exact official source bytes;
- source SHA256;
- source URL;
- retrieved_at;
- derivative mapping verified from source bytes;
- online ticker-based acquire/ingest refreshes the current official ticker map;
- local status may use the newest verified cached snapshot.

Those rules require separate source identity and retrieval-observation identity.

## 3. Source identity

Ticker-map source identity is:

```text
source_url
+
exact source bytes
+
source_sha256 = SHA256(exact source bytes)
```

The derivative ticker→CIK mapping is not authoritative. It must be recomputed
from the verified source bytes and must equal any persisted diagnostic mapping.

Two observations with the same source SHA and identical bytes represent the
same source content, but not necessarily the same retrieval observation.

## 4. Retrieval-observation identity

Every successful online ticker-map fetch creates one immutable retrieval
observation.

Its identity is:

```text
ticker_snapshot_id =
SHA256(
  canonical_json({
    "source_url": source_url,
    "source_sha256": lowercase_source_sha256,
    "retrieved_at": normalized_retrieved_at
  })
)
```

Canonical JSON uses UTF-8, sorted keys, deterministic separators, and no
environment-dependent formatting.

`retrieved_at` is part of observation identity.

Therefore:

```text
same source bytes
same source SHA
different retrieved_at
→ different ticker_snapshot_id
→ both observations valid
→ NOT source drift
```

## 5. New persistence path

New online observations must be written under:

```text
workspace/ingest/us/ticker-map/
  observations/
    <ticker_snapshot_id>.json
```

The new observation payload retains:

```text
source_url
source_sha256
retrieved_at
source_bytes_b64
mapping
```

and must also persist:

```text
snapshot_id = ticker_snapshot_id
```

No source bytes are fetched again merely to validate a cached snapshot.

## 6. Observation immutability

A completed observation file is immutable.

If:

```text
observations/<ticker_snapshot_id>.json
```

already exists, the complete canonical payload must be identical.

If the same `ticker_snapshot_id` path contains different payload content:

```text
P11_SOURCE_DRIFT
BLOCK
```

This is a true same-observation identity conflict.

A different `retrieved_at` must never be compared as though it were the same
observation.

## 7. retrieved_at validation

For newly persisted observations, `retrieved_at` must be:

- a string;
- non-empty;
- valid ISO-8601;
- timezone-aware.

Normalize it deterministically before computing `ticker_snapshot_id`.

UTC `+00:00` is the preferred normal form for newly generated values.

Invalid current-format observation timestamps are:

```text
P11_TICKER_SNAPSHOT_INVALID
```

No new reason code is required.

## 8. Legacy snapshot compatibility

Historical snapshots may exist at:

```text
workspace/ingest/us/ticker-map/<source_sha256>.json
```

They are:

```text
LEGACY
READ-ONLY
IMMUTABLE
SUPPORTED FOR VERIFIED LOCAL STATUS COMPATIBILITY
NOT THE STORAGE IDENTITY FOR NEW ONLINE OBSERVATIONS
```

New online persistence must not overwrite, rename, delete, or rewrite these
legacy files.

A legacy snapshot remains valid only if:

- filename source SHA equals persisted source SHA;
- decoded source bytes hash to that SHA;
- source URL is valid for the official ticker-map source;
- persisted derivative mapping equals reparsed bytes;
- retrieved_at is usable as historical retrieval metadata.

Legacy compatibility does not permit a fresh online observation to reuse the
legacy source-SHA filename.

## 9. Cached local status selection

Local-only status must implement Design 26 literally:

```text
use the newest verified cached snapshot
```

Selection order:

1. discover all valid current observation snapshots plus valid legacy snapshots;
2. independently verify every candidate considered;
3. order by parsed retrieval time, newest first;
4. deterministic identity tiebreak;
5. select the newest verified snapshot;
6. resolve the requested ticker only against that one snapshot.

Do not combine ticker→CIK mappings across historical observations.

Therefore a ticker that changed CIK historically does not become ambiguous merely
because old and new verified snapshots disagree.

If the newest verified snapshot does not contain the requested ticker:

```text
do not silently fall back to an older snapshot
```

Local status must report that a verified current-enough cached alias resolution
is unavailable under the existing controlled status behavior.

Within the selected snapshot, one ticker mapping to multiple CIKs remains a
blocking ambiguity.

## 10. Online ticker behavior

Every online ticker-based acquire/ingest must:

1. fetch the current official SEC ticker-map endpoint;
2. parse the exact bytes;
3. compute source SHA;
4. assign a fresh retrieval timestamp;
5. compute `ticker_snapshot_id`;
6. persist the immutable observation;
7. resolve ticker→CIK from those exact current verified bytes.

Explicit CIK continues to bypass ticker-map lookup.

A repeated online call with unchanged ticker-map bytes must succeed and create
a second valid observation if its retrieval timestamp differs.

## 11. Provenance carried into CompanyRef

The resolved company may continue to carry:

```text
ticker_source_url
ticker_source_sha256
ticker_retrieved_at
```

These fields describe the observation used for that invocation.

No Registry schema change is required.

No package/parser/artifact/validation schema change is required.

## 12. Required development tests

### T147-01 identical bytes, two retrievals

```text
fetch #1 bytes = X, retrieved_at = T1
fetch #2 bytes = X, retrieved_at = T2

T1 != T2
source_sha1 == source_sha2
snapshot_id1 != snapshot_id2

both persist successfully
no P11_SOURCE_DRIFT
both files immutable
```

### T147-02 repeat online acquire→ingest

Use the normal ticker-based production path with the same official ticker-map
bytes on both calls.

Require:

```text
first acquire succeeds
second ingest succeeds past ticker persistence
no P11_SOURCE_DRIFT
current discovery continues normally
```

### T147-03 true same-observation conflict

Pre-create the exact current observation path for a known
`ticker_snapshot_id` with mismatched canonical payload.

Require:

```text
P11_SOURCE_DRIFT
```

### T147-04 legacy immutability

With a valid legacy:

```text
ticker-map/<source_sha>.json
```

record its hash, run a new online ticker fetch with identical source bytes, and
prove:

```text
legacy file hash unchanged
new observation created under observations/<snapshot_id>.json
```

### T147-05 source-byte integrity

Tamper source bytes without matching source SHA.

Require:

```text
P11_TICKER_SNAPSHOT_INVALID
```

### T147-06 derivative integrity

Tamper persisted derivative mapping while source bytes remain valid.

Require:

```text
P11_TICKER_SNAPSHOT_INVALID
```

### T147-07 newest snapshot wins

Create two verified snapshots where ticker A maps to different CIKs at T1<T2.

Local cached status must resolve from T2 only and must not report
cross-history ambiguity.

### T147-08 no stale fallback

Newest verified snapshot does not contain ticker A; an older snapshot does.

Require no fallback to the old alias.

### T147-09 explicit CIK

Explicit CIK online flow performs zero ticker-map fetches and is unchanged.

### T147-10 Formal FT-10 reproduction

Reproduce the Formal Test 4 Apple sequence with an acceptance transport:

```text
ticker-based acquire
then ticker-based ingest
same ticker-map bytes
different retrieval times
```

Require both ticker snapshots to persist and the second call to pass this
boundary.

## 13. Regression requirements

The development candidate must preserve:

- ISSUE-140..146 behavior;
- 253+ US SEC suite behavior or current collected equivalent;
- full unit suite;
- P0-P10 compatibility;
- validation-v3 migration;
- REVALIDATE_LOCAL;
- static-asset selection;
- CN/HK behavior.

Run compileall and git diff --check.

After deterministic regression, rerun Apple FY2025 developer smoke through both
ticker-based acquire and ticker-based ingest so this exact failure boundary is
exercised before a new formal cycle.

## 14. Frozen version contract

Unchanged:

```text
REGISTRY_SCHEMA_VERSION = 1
SEC_REGISTRY_SCHEMA_VERSION = 4
SEC_DISCOVERY_SCHEMA = p11-sec-discovery-v1
VIRTUAL_HTML_NORMALIZER_VERSION = VIRTUAL_HTML_V6
SEC_ARTIFACT_SCHEMA = p11-sec-artifacts-v2
SEC_VALIDATION_SCHEMA = p11-sec-validation-v3
```

No new P11 reason code.

## 15. Governance state

```text
FORMAL TEST EXECUTION 4:
EXECUTION_FAIL

FORMAL ACCEPTANCE:
NOT PASSED

ISSUE-140..146:
FIXED / REGRESSION PRESERVATION

ISSUE-147:
DESIGN FROZEN / IMPLEMENTATION REQUIRED

DEVELOPMENT:
NOT YET AUTHORIZED

MAIN MERGE:
NOT AUTHORIZED

P11 DONE:
NO
```
