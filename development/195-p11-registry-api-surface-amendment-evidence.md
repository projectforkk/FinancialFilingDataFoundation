# 195 — P11 Registry API Canonical-Surface Amendment Evidence — ISSUE-037

Status: **PASS — AMENDED DESIGN READY FOR CANDIDATE FREEZE / PRODUCTION CLOSED**

Phase:
P11 — US SEC Provider

Historical reviewed candidate:
`cb35f537c75390d9b63b55af72c7278520ebd9be`

Authoritative stop:
`development/194-p11-registry-api-surface-review-stop.md`

## Resolution

### Canonical P11-K write API

Every normative P11-K registry write reference now uses:

`SQLiteRegistry.register_parsed_data_atomic(record)`

The legacy accepted API:

`SQLiteRegistry.register_parsed_data(record)`

remains referenced only to state that P0-P10/CN-HK behavior is unchanged and that P11-K must not use it.

### Canonical conflict exception

Exact class:

`ParsedDataRecordConflict(ValueError)`

Canonical implementation path:

`financial_filing_data_foundation.registry.sqlite_registry.ParsedDataRecordConflict`

Canonical public import:

`from financial_filing_data_foundation.registry import ParsedDataRecordConflict`

`financial_filing_data_foundation.registry.__init__` must re-export the exact same class object; alias/wrapper/duplicate classes are forbidden.

### Acceptance

Acceptance now proves:

- canonical public import succeeds;
- public import identity equals implementation-path class identity;
- class is a `ValueError` subclass;
- exact conflict message is frozen;
- P11-K maps this exact exception to `P11_REGISTRY_RECORD_CONFLICT`;
- accepted legacy `register_parsed_data()` remains unchanged for existing callers.

## Scope

Unchanged from ISSUE-036:

- `BEGIN IMMEDIATE` concurrency algorithm;
- exact existing-row comparison;
- no hidden retry;
- busy/locked/I/O mapping;
- registry schema version 1;
- deterministic final artifact and ISSUE-035 commit protocol;
- package-aware reuse;
- CN/HK/P8/P9/P10 contracts.

No production/test/runtime change was made.

## Verdict

# PASS — READY FOR CANDIDATE FREEZE AND FRESH DETACHED DESIGN REVIEW

This does not authorize P11 production.

P11-B remains NOT AUTHORIZED until the exact amended candidate passes fresh detached P11-A design review.