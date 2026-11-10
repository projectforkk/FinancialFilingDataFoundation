# P11 full design/code consistency repair

## Scope

Repair P11-ISSUE-109 through P11-ISSUE-120 in one development candidate while
preserving P11-ISSUE-101 through P11-ISSUE-108, accepted CN/HK behavior, and the
development-only US gate. The production candidate contains only source and
tests; the repair evidence is a separate documentation commit.

## Work sequence

1. Add focused regressions for nested SEC archive paths, canonical Windows-safe
   member paths, CIK-first identity, market-specific periods, planner reuse,
   history range selection, archive metadata/bytes, and explicit timeout fields.
2. Repair SEC archive path construction and validation, submission history range
   metadata, archive-index handling, member role/content validation, and the
   three-part timeout contract.
3. Integrate the planner with the registry, package store, CLI acquire/ingest/
   status flow, stable CIK catalog identity, and ticker-map provenance.
4. Extend HTML normalization and XBRL contexts/facts with deterministic source
   blocks, table contract fields, dimension kinds, namespaced nil handling, and
   P8 SEC-compatible aliases/filters.
5. Complete P7-US metadata, period, table/evidence, and reuse eligibility gates.
6. Run focused P11, full unit, CN/HK regression, compileall, and diff checks;
   run developer live smoke only against the frozen SEC fixtures with the
   configured contact email. Commit/push the exact production candidate, then
   write and push the separate evidence document.

## Safety invariants

- `SUPPORTED_MARKETS` remains exactly `("CN", "HK")`.
- No original SEC bytes are modified and no remote AI/API is introduced.
- No main merge, force push, reset, or clean operation.
- REVIEW_REQUIRED remains non-reusable; only PASS + compatible + zero blocking
  data may take the REUSE_DATA path.
- A malformed or unsafe SEC path/index/member fails closed before fetch or
  package commit.
