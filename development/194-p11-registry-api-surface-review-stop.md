# 194 — P11 Final Design Review Stop — Registry API Canonical Surface

Status: **FAIL / STOP — P11-ISSUE-037 / PRODUCTION CLOSED**

Phase:
P11 — US SEC Provider

Reviewed exact candidate:
`cb35f537c75390d9b63b55af72c7278520ebd9be`

Review authorization:
`development/193-p11-registry-concurrency-final-review-authorization.md`

## Automated review

PASS:
- ISSUE-010..031 matrix;
- ISSUE-032..033 guard;
- ISSUE-034 byte-determinism guard;
- ISSUE-035 final-path concurrency guard;
- ISSUE-036 atomic registry guard;
- P0-P10 production/test/runtime diff = NONE;
- fixture and deterministic byte hashes stable.

## Manual finding 1 — contradictory P11-K write API

`design/26-p11-sec-provider-design.md` still contains the earlier normative sentence:

`P11-I MUST atomically commit the complete export directory at this final path and reload it successfully before P11-K may call register_parsed_data.`

Later ISSUE-036 text correctly says:

`P11-K MUST instead use SQLiteRegistry.register_parsed_data_atomic(...)`

These two authoritative statements conflict. P11 implementation must not be required to infer that the later sentence silently overrides the earlier API name.

## Manual finding 2 — public conflict exception path not frozen

ISSUE-036 names `ParsedDataRecordConflict(ValueError)` as public, but does not freeze its canonical module/export path.

Because P11-K and acceptance need a stable public exception surface, implementation must not choose freely between `registry.models`, `registry.sqlite_registry`, package-only export, or another location.

## P11-ISSUE-037 required correction

1. Replace every normative P11-K call-site reference to legacy `register_parsed_data` with `SQLiteRegistry.register_parsed_data_atomic(record)` while preserving references that explicitly describe the unchanged P0-P10/CN-HK legacy API.
2. Freeze canonical exception implementation path:
   `financial_filing_data_foundation.registry.sqlite_registry.ParsedDataRecordConflict`.
3. Freeze canonical public import:
   `from financial_filing_data_foundation.registry import ParsedDataRecordConflict`.
4. Require `financial_filing_data_foundation.registry.__init__` to export the exception during P11 production implementation.
5. Acceptance must prove the canonical import, subclass relation to `ValueError`, exact conflict message, and that P11-K catches/maps this exception only to `P11_REGISTRY_RECORD_CONFLICT`.
6. No production/test/runtime change during design review; no schema migration; existing `register_parsed_data()` callers unchanged.

## Verdict

# FAIL / STOP

Candidate `cb35f537c75390d9b63b55af72c7278520ebd9be` is INELIGIBLE for DESIGN READY.

P11-A remains OPEN/STOPPED.
P11-B remains NOT AUTHORIZED.
P11 production remains CLOSED.