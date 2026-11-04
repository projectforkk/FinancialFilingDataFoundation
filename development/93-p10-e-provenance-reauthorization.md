# 93 — P10-E Development Authorization — Evidence Ledger / Provenance Validator

Status: **AUTHORIZED — P10-E ONLY**

Phase:
`P10 — Codex Dynamic Research Integration`

Gate:
`P10-E — Evidence Ledger / Provenance Validator`

Design baseline:
`d6b34d84d1eeae6b0f2009895a14c5956217a18f`

Pre-implementation stop:
`development/92-p10-e-preimplementation-design-stop.md`

P10-D detached review:
`development/91-p10-d-detached-code-review-result.md = PASS`

## 1. Authorization

Only P10-E is authorized.

Implement the frozen Sections 26–27 contract and no later-stage production.

Authorized production path:

- `src/financial_filing_data_foundation/research/provenance.py`

Authorized supporting changes:

- `src/financial_filing_data_foundation/research/__init__.py`
- provenance-focused tests under `tests/unit/research/`

Do not implement P10-F CLI or later gates.

## 2. Required public contract

Implement exactly:

```python
validate_evidence_ledger(
    context: ResearchContext,
    ledger: EvidenceLedger,
    spec_bundle: ResearchSpecBundle,
    p8_catalog: McpCatalog,
) -> ProvenanceValidation
```

Required models:

- `EvidenceLedgerEntry`
- `EvidenceLedger`
- `ProvenanceValidation`

Required schemas:

- `p10-research-evidence-ledger-v1`
- `p10-provenance-validation-v1`

## 3. Existing-tools-first boundary

Must reuse:

- `verify_research_spec`
- frozen P10-D context identity logic
- `McpQueryService`
- accepted P9 `load_resolved_snapshot` / public review models

Do not copy:

- P8 fact/evidence hash algorithms
- P8 artifact truth semantics
- P9 resolution history/hash semantics

## 4. Frozen use classes

Only:

- `P8_RAW_DIRECT`
- `RUN_LOCAL_STRUCTURED_VERIFIED`
- `P9_DURABLE_RESOLVED`
- `UNRESOLVED`

`EXTERNAL_RUNTIME_SOURCE` must be rejected from FFDF ledger v1.

## 5. Frozen error mapping

- invalid ledger/ref/use class/derived graph/context binding:
  `P10_PROVENANCE_INVALID`
- current spec drift:
  `P10_RESEARCH_SPEC_CHANGED`
- catalog/context mismatch:
  `P10_CONTEXT_INCOMPATIBLE`
- corrupt accepted P8/P9 state:
  `P10_UPSTREAM_INVALID`

No traceback to normal client.

## 6. P9 read-only rule

Validator may read an existing snapshot only.

It must not:

- prepare review state
- submit a resolution
- materialize a snapshot
- mutate review root
- create P9 directories

Historical validated snapshots are allowed by exact overlay identity.

## 7. Focused test gate

Implement all design/25 P10-E focused cases.

At minimum prove:

- exact ledger/context/spec identity
- P8 direct refs + relations
- P9 exact resolution/snapshot overlay
- corrupt P9 fails closed
- four use-class profiles
- derived DAG/no-cycle/allowed operand classes
- spec drift precedence
- context/catalog mismatch
- exact validation result schema
- external-source rejection
- no absolute path/time/random/hidden reasoning

## 8. Security / environment

Every Python invocation:

```powershell
$env:PYTHONPATH="<exact candidate worktree>\src"
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -B ...
```

No new dependency/runtime.

No:

- network
- AI API
- external MCP SDK in main runtime
- subprocess/shell
- arbitrary SQL
- arbitrary filesystem browse
- environment dump
- Research MCP production
- Semantic Resolver production
- P11 production

## 9. Evidence

After implementation:

- focused provenance tests PASS
- full `tests/unit` PASS
- compile/import PASS
- `git diff --check` PASS
- P8/P9 source/tests zero diff
- dependency/runtime zero diff
- forbidden surface scan NONE
- exact candidate commit/push
- create `development/94-p10-e-provenance-evidence.md`

Then STOP.

P10-E requires a separate detached Code Review before P10-F can be authorized.

P10-F and later remain closed.
