# P11 second repair pass

## Scope

- Repair only P11-ISSUE-101 and P11-ISSUE-108.
- Preserve the previous fixes for P11-ISSUE-102 through P11-ISSUE-107.
- Do not alter Registry, P8 tool names, CN/HK behavior, XML extraction, HTTP,
  package storage, or runtime architecture except where directly required by the
  two review findings.

## Execution ledger

1. Add failing discovery tests for exact annual endpoints, chronology-based
   quarter slots, in-progress fiscal years, amendment grouping, calendar years,
   and FPI annuals.
2. Add failing hidden Inline XBRL tests for numeric/nonnumeric facts, round-trip
   corruption, and visible-block regression.
3. Implement the smallest discovery and hidden-evidence changes; bump the SEC
   parser version and prevent reuse of older cached artifacts.
4. Run focused tests, full unit tests, CN/HK regression, compileall, and
   `git diff --check`.
5. Commit production code/tests as the exact candidate, then commit this plan
   and the separate repair evidence.

## Stop conditions

If deterministic fiscal chronology or immutable hidden-fact evidence cannot be
implemented without breaking P8 or accepted CN/HK behavior, record the factual
blocker and stop without formal acceptance.
