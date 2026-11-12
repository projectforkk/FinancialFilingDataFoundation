# 34 — P11 Explicit Form 6-K Scope Correction

Status: **AUTHORITATIVE DESIGN CORRECTION — P11 v1 EXPLICIT 6-K DEFERRED**

Date: 2026-11-13

Authority:

- `design/26-p11-sec-provider-design.md`
- `design/27-p11-implementation-plan.md`
- `design/32-p11-us-scope-reopening.md`
- `development/188-p11-full-design-code-consistency-review-3.md`

## Decision

Explicit Form 6-K acquisition is deferred from the accepted P11 v1 capability.

The current P11 identity model is a periodic `FilingSlotKey` whose raw period is
limited to `Q1`, `Q2`, `Q3`, and `FY`. The current CLI has no accession-level
explicit selector and its generic `--filing-type` option is not a safe 6-K identity
contract. Extending that option without a separate accession/request identity design
could silently map a 6-K filing into a standardized quarterly slot, which is
forbidden by the no-guessing rule.

Therefore:

- P11 v1 supports domestic `10-K`/`10-Q` periodic slots and FPI `20-F`/`40-F`
  FY slots only.
- P11 v1 does not auto-map `6-K` to `Q1`, `Q2`, or `Q3`.
- A caller that explicitly requests `--filing-type 6-K` or `6-K/A` must receive a
  deterministic `P11_UNSUPPORTED_EXPLICIT_6K` error; the request must not be
  ignored or coerced into a periodic slot.
- No 6-K package, Registry binding, P8 catalog entry, or research-ready artifact is
  created by this P11 v1 path.

## Deferred design requirements

Future explicit 6-K support requires a separately reviewed contract defining at least:

- accession-level request identity and deterministic selection;
- whether year/period are optional or informational;
- package/Registry/catalog identity without a standardized quarterly slot;
- amendment/conflict behavior for multiple explicitly requested accessions;
- CLI/API request and response fields;
- P8 listing/report ordering semantics.

This correction resolves the Design 32 wording/code mismatch without inventing
quarter semantics. It does not authorize a Formal Test Plan, Formal Acceptance, main
merge, or P11 DONE.
