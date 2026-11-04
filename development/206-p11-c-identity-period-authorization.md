# 206 — P11-C Identity / Period Contract Authorization

Status: **AUTHORIZED — P11-C PRODUCTION/TEST SCOPE ONLY / P11 PROVIDER PRODUCTION CLOSED**

Phase:
P11 — US SEC Provider

Prerequisites:
- P11-A Design Baseline = PASS (`development/203-p11-final-detached-design-review-result.md`);
- P11-B Environment / SEC Runtime Probe = PASS (`development/205-p11-environment-runtime-probe.md`).

## Authorized implementation scope

Allowed production files:
- `src/financial_filing_data_foundation/identity/models.py`;
- `src/financial_filing_data_foundation/identity/sec.py` (new, pure deterministic SEC identity helpers);
- `src/financial_filing_data_foundation/identity/__init__.py`;
- `src/financial_filing_data_foundation/planner/errors.py` (new);
- `src/financial_filing_data_foundation/planner/incremental.py`;
- `src/financial_filing_data_foundation/planner/__init__.py`.

Allowed focused tests:
- existing/new tests under `tests/unit/identity/`;
- `tests/unit/planner/test_incremental.py`.

Implement only the accepted P11-C contract:
- additive US `CompanyRef` / `FilingSlotKey` support;
- CN/HK semantics unchanged;
- Q2 valid only for US;
- exact CIK grammar/normalization;
- exact accession grammar and dash-removal helper;
- deterministic SEC form normalization for 10-K/10-Q/20-F/40-F/8-K/6-K plus `/A`;
- accession-bound supplemental identity model;
- pure ticker/CIK resolution logic using caller-supplied official mapping metadata, with no HTTP;
- exact `PackageAwarePlannerRequired(RuntimeError)` public API in `planner.errors`, re-exported from `planner`;
- US generic `IncrementalPlanner.build_plan` fail-fast guard before slot construction and before registry access.

## Exact planner exception

```python
class PackageAwarePlannerRequired(RuntimeError):
    reason_code = "P11_PACKAGE_AWARE_PLANNER_REQUIRED"
```

Exact message:
`market US requires P11 package-aware SEC planning`

Existing `ReasonCode` enum MUST NOT change.

## Focused acceptance

Must cover all 22 P11-C focused cases from `design/27-p11-implementation-plan.md`, including CN/HK compatibility, US Q2, form amendments, supplemental identity, ticker/CIK not-found/ambiguity, and planner guard ordering.

## Forbidden

- no SEC HTTP/client code;
- no acquisition changes;
- no registry schema/API changes;
- no parser/Arelle production code;
- no runtime-lock changes;
- no P11-D or later implementation;
- no P8/P9/P10 changes;
- no Research MCP / Semantic Resolver production.

Implementation branch/worktree:
- branch: `task/p11-c-identity-period`;
- worktree: `D:\Codex\FinancialFilingDataFoundation\worktrees\active\p11-c-identity-period`.

On focused + full unit PASS, freeze exact candidate, push GitHub, and run detached P11-C code review before closing the gate.

P11 provider production remains CLOSED.