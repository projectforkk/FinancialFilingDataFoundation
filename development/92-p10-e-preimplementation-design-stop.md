# 92 — P10-E Pre-Implementation Design Stop

Status: **STOPPED — P10-ISSUE-004 DESIGN AMENDMENT REQUIRED**

Phase:
`P10 — Codex Dynamic Research Integration`

Gate:
`P10-E — Evidence Ledger / Provenance Validator`

P10-D detached review:
`development/91-p10-d-detached-code-review-result.md = PASS`

P10-D review result commit:
`109af3057942db62d80e8a39d0f18f68d0321fd8`

## 1. Stop timing

P10-E had not been authorized.

No `research/provenance.py` exists.

No provenance-focused test exists.

No P10-D production/test, P8/P9 source/test/runtime, Research MCP, Semantic Resolver, or P11 production was modified.

The issue was found during the required pre-implementation contract review.

## 2. Facts

The current design names:

- schema `p10-research-evidence-ledger-v1`;
- a minimum claim-entry example;
- P8 document/page/table/fact/evidence validation;
- P9 resolution/snapshot validation;
- use-class compatibility;
- derived operand references;
- spec/context identity matching.

However it does not freeze enough information to produce one deterministic implementation.

### 2.1 Ledger envelope is underspecified

The design does not freeze the top-level ledger fields that bind a ledger to:

- `research_context_id`;
- `spec_bundle_hash`;
- claim entries.

It also does not define duplicate claim-key behavior or canonical entry/reference ordering.

### 2.2 Validation API is insufficient

The current design shows:

```python
validate_evidence_ledger(context, ledger)
```

but `ResearchContext` intentionally contains no absolute catalog path and no spec bytes.

Therefore that API cannot independently:

- re-verify current research-spec bytes;
- prove the supplied/current P8 catalog raw SHA still equals the frozen context;
- instantiate the accepted P8 service for document/table/fact/evidence validation.

### 2.3 Use-class compatibility is underspecified

The accepted research-use classes exist:

- `P8_RAW_DIRECT`;
- `RUN_LOCAL_STRUCTURED_VERIFIED`;
- `P9_DURABLE_RESOLVED`;
- `UNRESOLVED`.

But the design does not freeze:

- which direct/P9/derived references each class requires or forbids;
- whether `semantic_assertions` must be empty/non-empty;
- whether a derived claim can be durable;
- whether `UNRESOLVED` can be a derived operand;
- whether `document_sha256` may be null for derived-only or unresolved claims.

### 2.4 P8 relation rules are underspecified

Accepted P8 facts/evidence expose deterministic relations:

- fact -> `document_sha256`;
- fact -> `table_id`;
- fact -> `page_no`;
- fact -> `evidence_id`;
- evidence -> `document_sha256`;
- evidence -> `table_id`;
- evidence -> `page_no`;
- table -> `page_no`.

The design says these must resolve but does not freeze how cross-reference consistency is checked when multiple reference arrays are present.

### 2.5 P9 durable provenance is underspecified

Accepted P9 layout is deterministic:

```text
<context.p9_review_root>/<document_sha256>/
    resolutions/
    snapshots/<overlay_set_hash>/
```

Accepted `load_resolved_snapshot` validates snapshot/store/base identity and corruption.

But the ledger design does not freeze:

- whether `overlay_set_hash` is mandatory for durable claims;
- whether referenced resolution IDs must belong to the referenced snapshot active set;
- whether historical validated snapshots are allowed after later supersession;
- how missing snapshot/reference differs from corrupt P9 state.

### 2.6 Derived graph is underspecified

The design requires derived claims to reference operand claim keys, but does not freeze:

- duplicate references;
- self-reference;
- cycles;
- forward references / entry-order dependence;
- allowed operand use classes.

### 2.7 Validation result/error contract is underspecified

`ProvenanceValidation` has no frozen schema.

The design also does not distinguish:

- malformed/invalid provenance;
- catalog/context mismatch;
- current spec drift;
- corrupt accepted P8/P9 upstream state.

## 3. Accepted upstream facts

P8:

- `McpQueryService` can validate document, page bounds, table, raw fact, and evidence identity using accepted local artifacts.
- P6 fact/evidence artifacts already validate fact -> evidence identity internally.
- P10 must reuse P8 service/loaders rather than copy P8 truth semantics.

P9:

- `review_dir = review_root / document_sha256`;
- `load_resolved_snapshot(snapshot_dir, review_dir)` validates snapshot path, resolution store, base fingerprint, overlay hash, active IDs, and persisted snapshot bytes;
- P9 corruption raises accepted `ReviewError` reason codes;
- P10 must not silently fall back to raw data when claimed P9 provenance is corrupt.

## 4. Risk

Without a design amendment:

1. two valid-looking validators can accept different ledgers;
2. one implementation can treat run-local reasoning as durable;
3. derived claims can silently depend on unresolved/raw-semantic operands;
4. P9 resolution IDs can be detached from the claimed overlay snapshot;
5. spec/catalog drift can pass because the existing API has no inputs needed to re-check them;
6. corrupt P9 state can be misclassified as a missing ledger reference and silently bypassed;
7. ledger entry order can change validation behavior or identity.

## 5. Approved Design-First correction

Before P10-E code:

- freeze exact top-level ledger schema;
- freeze exact entry field/nullability rules;
- freeze four use-class compatibility profiles;
- freeze P8 direct-reference relation checks;
- freeze P9 review-dir/snapshot/resolution validation;
- allow historical validated P9 snapshots by exact overlay identity;
- freeze derived graph as order-independent, existing-key, acyclic, non-UNRESOLVED/non-raw operand provenance;
- freeze `semantic_assertions` as opaque JSON-compatible provenance metadata, not financial truth;
- explicitly exclude external-source provenance from the FFDF ledger v1;
- change validator API to also receive the frozen spec bundle and current accepted P8 catalog;
- freeze a deterministic PASS-only validation-result schema;
- freeze error mapping:
  - invalid ledger/reference/use-class/graph -> `P10_PROVENANCE_INVALID`;
  - current spec drift -> existing `P10_RESEARCH_SPEC_CHANGED`;
  - catalog/context incompatibility -> existing `P10_CONTEXT_INCOMPATIBLE`;
  - corrupt accepted P8/P9 state -> `P10_UPSTREAM_INVALID`;
- update P10-E plan/tests and acceptance provenance requirements before authorization.

## 6. Gate boundary

Required sequence:

```text
STOP P10-E
→ amend design/24
→ amend design/25
→ amend acceptance/38
→ update governance/status
→ commit/push new design baseline
→ new explicit P10-E authorization
→ implementation
```

No P10-E production may be written before that new baseline is GitHub truth.

P10-F and later remain closed.

Research MCP production, Semantic Resolver production, and P11 production remain closed.
