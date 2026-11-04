# 192 — P11 Concurrent Registry Persistence Amendment Evidence — ISSUE-036

Status: **PASS — AMENDED DESIGN READY FOR CANDIDATE FREEZE / PRODUCTION CLOSED**

Phase:
P11 — US SEC Provider

Historical reviewed candidate:
`2ef1e8ced4b5c3d7103c73bdc8cc532882fa7d47`

Authoritative stop:
`development/191-p11-registry-concurrency-review-stop.md`

## P11-ISSUE-036 resolution

The accepted P0-P10/CN-HK registry path remains unchanged:

`SQLiteRegistry.register_parsed_data(record)`

P11-K uses an additive API:

`SQLiteRegistry.register_parsed_data_atomic(record: ParsedDataRecord) -> None`

with additive public conflict exception:

`ParsedDataRecordConflict(ValueError)`

`REGISTRY_SCHEMA_VERSION` remains `1`.

## Exact atomic algorithm

One SQLite connection performs:

1. `BEGIN IMMEDIATE`;
2. SELECT by exact `parse_run_id`;
3. existing row => compare every persisted semantic field except `created_at`;
4. exact existing row => normal idempotent success;
5. different existing row => rollback + `ParsedDataRecordConflict` with exact existing-message contract;
6. absent row => INSERT once + commit;
7. busy/locked/I/O/commit failure => fail closed;
8. no hidden retry loop.

`BEGIN IMMEDIATE` occurs before the existence check, eliminating the accepted method's SELECT-then-INSERT race for P11-K callers.

## P11 error mapping

- exact/new success => registry persistence success;
- `ParsedDataRecordConflict` => `P11_REGISTRY_RECORD_CONFLICT` / BLOCKED;
- SQLite busy/locked/I/O/commit or other persistence error => `P11_REGISTRY_PERSISTENCE_FAILED` / BLOCKED.

Registry failure never mutates/deletes/replaces the already verified final `export-v2`. A later outer retry must re-verify the existing final artifact before retrying atomic registry persistence.

## Project-local design probe

Probe:
`workspace/scratch/p11-registry-atomic-design-probe.py`

Observed:

```text
EXACT_RESULTS=[('T0', 'PASS', 'EXACT_EXISTING'), ('T1', 'PASS', 'INSERTED')]
ROW_COUNT=1
ROWS=[('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', 'same-payload')]
CONFLICT=parse_run_id already exists with different content: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
LOCK_FAILURE=database is locked
P11_REGISTRY_ATOMIC_DESIGN_PROBE=PASS
```

This probe is design evidence only. It does not modify production code.

## Contract updates

Updated authoritative design surfaces:

- `design/26-p11-sec-provider-design.md`: exact additive API, transaction algorithm, error mapping, no schema migration, old API unchanged;
- `design/27-p11-implementation-plan.md`: P11-K must use atomic API and no hidden retry;
- `design/30-parsed-financial-document-v2-contract.md`: final reload -> atomic registry boundary; registry cannot mutate final bytes;
- `acceptance/41-p11-acceptance-instruction.md`: two-writer exact success, one-row invariant, conflict/lock negative cases, CN/HK unchanged;
- `development/144-p11-environment-interface-audit.md`: ISSUE-036 environment/dependency boundary;
- `development/145-p11-design-reconciliation.md`: additive compatibility reconciliation.

## Regression boundary

PASS:

- ISSUE-010..035 remediation remains intact;
- no production source change;
- no test change;
- no integration/runtime-lock change;
- no registry schema migration;
- existing `register_parsed_data()` semantics and callers remain unchanged;
- CN/HK planner/reuse behavior remains unchanged;
- P8/P9/P10 contracts remain unchanged.

## Verdict

# PASS — READY FOR CANDIDATE FREEZE AND FRESH DETACHED DESIGN REVIEW

This does not authorize P11 production.

P11-B remains NOT AUTHORIZED until the exact amended candidate passes fresh detached P11-A design review.