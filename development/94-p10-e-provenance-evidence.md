# 94 — P10-E Evidence Ledger / Provenance Validator Development Evidence

Status: **PASS — P10-E CANDIDATE READY FOR REVIEW**

Phase:
`P10 — Codex Dynamic Research Integration`

Gate:
`P10-E — Evidence Ledger / Provenance Validator`

Design baseline:
`d6b34d84d1eeae6b0f2009895a14c5956217a18f`

Reauthorization:
`development/93-p10-e-provenance-reauthorization.md`

Reauthorization commit:
`ff0173e0434e0b847cd77290aba5ee6238dbccbe`

Final production/test candidate:
`802a395247e490a83acaef744c1641188fbf704e`

Branch:
`design/p10-dynamic-research-integration`

Worktree:
`D:\\Codex\\FinancialFilingDataFoundation\\worktrees\\active\\p10-dynamic-research-design`

All work/test/temp paths remained inside:
`D:\\Codex\\FinancialFilingDataFoundation`

## 1. Exact candidate scope

Diff from P10-E reauthorization parent:

```text
M  src/financial_filing_data_foundation/research/__init__.py
A  src/financial_filing_data_foundation/research/provenance.py
A  tests/unit/research/test_research_provenance.py
```

No P8/P9 source or test path changed.

No dependency/runtime file changed.

No P10-F CLI, integration instruction, Research MCP, Semantic Resolver, or P11 production was added.

## 2. Implemented public contract

Implemented exactly:

```python
validate_evidence_ledger(
    context: ResearchContext,
    ledger: EvidenceLedger,
    spec_bundle: ResearchSpecBundle,
    p8_catalog: McpCatalog,
) -> ProvenanceValidation
```

Models:

- `EvidenceLedgerEntry`
- `EvidenceLedger`
- `ProvenanceValidation`

Schemas:

- `p10-research-evidence-ledger-v1`
- `p10-provenance-validation-v1`

Accepted use classes:

- `P8_RAW_DIRECT`
- `RUN_LOCAL_STRUCTURED_VERIFIED`
- `P9_DURABLE_RESOLVED`
- `UNRESOLVED`

`EXTERNAL_RUNTIME_SOURCE` is rejected from FFDF ledger v1.

## 3. Deterministic validation boundary

The validator:

1. derives project root only from accepted `McpCatalog`;
2. re-runs `verify_research_spec`;
3. verifies current raw catalog SHA and frozen P10-D context identity;
4. verifies ledger context/spec identity;
5. validates use-class profiles and derived DAG;
6. validates P8 direct refs through accepted `McpQueryService`;
7. validates P9 durable refs through accepted `load_resolved_snapshot`.

It does not:

- interpret financial truth in `semantic_assertions`;
- recalculate YoY/QoQ/TTM/margins;
- call network/AI;
- import external MCP SDK in main runtime;
- execute subprocess/shell/SQL;
- prepare/submit/materialize P9 state;
- mutate P8/P9/Registry/source artifacts.

## 4. Use-class enforcement

Focused tests prove:

### P8_RAW_DIRECT

- document required;
- direct P8 provenance required;
- page/table/fact/evidence direct refs accepted independently;
- P9 refs forbidden;
- derived refs forbidden;
- semantic assertions forbidden.

### RUN_LOCAL_STRUCTURED_VERIFIED

Source-backed:

- document + direct P8 provenance required;
- non-empty semantic assertions required;
- P9 refs forbidden.

Derived:

- document/direct/P9 refs absent;
- non-empty semantic assertions required;
- operand claim keys required.

### P9_DURABLE_RESOLVED

- document required;
- resolution IDs required;
- exact overlay-set SHA required;
- resolution IDs must belong to the claimed snapshot active set;
- historical validated snapshot remains valid by exact overlay identity;
- no silent fallback on corrupt P9 state.

### UNRESOLVED

- direct P8 refs may be absent or present;
- no P9/overlay/derived/assertion state;
- cannot be a derived operand.

## 5. P8 provenance behavior

Real synthetic P3→P7 artifacts and a real P8 catalog/service were used.

Validated:

- document provenance;
- page bounds;
- table provenance;
- raw fact provenance;
- evidence provenance;
- fact/evidence relation;
- page-scope relation;
- table-scope relation;
- canonical missing document/ref rejection;
- malformed/corrupt P8 artifact -> `P10_UPSTREAM_INVALID`.

Explicit missing/ref mismatch maps to:

`P10_PROVENANCE_INVALID`

No P6 fact/evidence hash/truth algorithm was copied into P10.

## 6. P9 durable provenance behavior

Tests use real P9 APIs:

- `prepare_review_overlay`
- `submit_resolution`
- `materialize_resolved_view`

only as **test fixture setup**.

P10-E production imports none of those mutation APIs.

Production validates existing durable state only via:

`load_resolved_snapshot(snapshot_dir, review_dir)`

Verified:

- exact document/overlay identity;
- exact active resolution membership;
- missing claimed snapshot -> `P10_PROVENANCE_INVALID`;
- corrupt snapshot -> `P10_UPSTREAM_INVALID`;
- historical snapshot remains valid after a later superseding resolution/snapshot;
- durable P9 claim is an allowed derived operand.

## 7. Derived graph

Verified:

- entry order does not change result;
- missing operand rejected;
- self-reference rejected;
- cycle rejected;
- duplicate operand refs rejected by structural validation;
- `P8_RAW_DIRECT` operand rejected;
- `UNRESOLVED` operand rejected;
- `RUN_LOCAL_STRUCTURED_VERIFIED` and `P9_DURABLE_RESOLVED` are allowed operands.

The validator does not claim to verify financial arithmetic or semantic compatibility.

## 8. Error precedence

Verified:

- current spec file drift returns
  `P10_RESEARCH_SPEC_CHANGED`
  before later malformed ledger checks;
- ledger context/spec mismatch returns
  `P10_PROVENANCE_INVALID`;
- current catalog/context mismatch returns
  `P10_CONTEXT_INCOMPATIBLE`;
- corrupt accepted P8/P9 state returns
  `P10_UPSTREAM_INVALID`.

## 9. Implementation correction before candidate freeze

The first focused implementation probe exposed a P10-E adapter bug:

P10 had assumed accepted P8 success envelopes included:

`status="OK"`

Actual accepted P8 service contract is:

```text
schema_version
tool
document_sha256
data
```

No P8 design/code change was needed.

P10-E was corrected to validate the existing P8 envelope:

- `schema_version == p8-mcp-result-v1`
- `tool` present
- `data` mapping

After that correction, the focused suite passed.

This correction happened before candidate commit `802a395...`.

## 10. Focused provenance suite — exact candidate

Exact candidate:

`802a395247e490a83acaef744c1641188fbf704e`

Command:

```powershell
$env:PYTHONPATH="D:\Codex\FinancialFilingDataFoundation\worktrees\active\p10-dynamic-research-design\src"
$env:PYTHONDONTWRITEBYTECODE="1"
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -B -m pytest tests\unit\research\test_research_provenance.py -q -p no:cacheprovider --basetemp D:\Codex\FinancialFilingDataFoundation\worktrees\t\y
```

Result:

```text
44 passed in 13.39s
FOCUSED_EXIT=0
```

This exceeds the design/25 minimum of 40 focused cases.

## 11. Full unit regression — exact candidate

Command:

```powershell
$env:PYTHONPATH="D:\Codex\FinancialFilingDataFoundation\worktrees\active\p10-dynamic-research-design\src"
$env:PYTHONDONTWRITEBYTECODE="1"
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -B -m pytest tests\unit -q -p no:cacheprovider --basetemp D:\Codex\FinancialFilingDataFoundation\worktrees\t\z
```

Result:

```text
412 passed in 42.92s
FULL_EXIT=0
```

P10-D final review had 368 passing unit tests.

P10-E adds 44 passing focused tests with no prior-stage regression.

## 12. Windows path-length environment evidence

An exact-candidate rerun initially used two-character basetemps:

- `...\worktrees\t\z0`
- `...\worktrees\t\z1`

Observed:

- focused: `5 failed, 39 passed`;
- full: `14 failed, 398 passed`.

Every failure was in P9 snapshot persistence and showed the already-known Windows deep-path form:

```text
P9_PERSIST_FAILED
FileNotFoundError
...\snapshots\.<overlay_hash>.tmp\resolution_report.json
```

The failures also affected accepted pre-existing P9 tests, proving the issue was not specific to P10-E product logic.

No code/design was changed in response.

Existing single-character basetemp directories `y` and `z` were preserved whole by moving them to project-local ignored workspace:

```text
workspace/scratch/p10-e-preserved-basetemp-y-before-802a395
workspace/scratch/p10-e-preserved-basetemp-z-before-802a395
```

Then fresh one-character `y` / `z` basetemps produced the PASS results in Sections 10–11.

This is an environment-path constraint, not a product failure.

## 13. Compile / import

Exact candidate:

```text
COMPILE_EXIT=0
IMPORT_OK
research/__init__.py -> exact active candidate src
research/provenance.py -> exact active candidate src
```

Public signature:

```text
(context: ResearchContext,
 ledger: EvidenceLedger,
 spec_bundle: ResearchSpecBundle,
 p8_catalog: McpCatalog) -> ProvenanceValidation
```

Exact constants:

```text
p10-research-evidence-ledger-v1
p10-provenance-validation-v1
('P8_RAW_DIRECT',
 'RUN_LOCAL_STRUCTURED_VERIFIED',
 'P9_DURABLE_RESOLVED',
 'UNRESOLVED')
```

## 14. Scope / security

`git diff --check ff0173e..802a395`:
**PASS**

Exact candidate paths:

```text
M  src/financial_filing_data_foundation/research/__init__.py
A  src/financial_filing_data_foundation/research/provenance.py
A  tests/unit/research/test_research_provenance.py
```

P8/P9 source/test diff:
`NONE`

Dependency/runtime diff:
`NONE`

Forbidden production surface scan:
`NONE`

The production scan explicitly checked for:

- external `mcp` SDK;
- OpenAI/Anthropic/network clients;
- socket;
- subprocess/shell;
- sqlite/SQL;
- P9 `prepare_review_overlay`;
- P9 `submit_resolution`;
- P9 `materialize_resolved_view`.

## 15. Encoding

UTF-8 decode PASS and BOM absent for:

- `research/provenance.py`
- `research/__init__.py`
- `test_research_provenance.py`

## 16. Final candidate state

Candidate:

`802a395247e490a83acaef744c1641188fbf704e`

During exact-candidate validation:

- local HEAD matched remote branch;
- worktree was clean;
- no production/test/runtime file changed after candidate commit.

## 17. Gate verdict

# PASS — P10-E CANDIDATE READY FOR REVIEW

P10-E implementation candidate is complete.

A separate detached P10-E Code Review is required before P10-F can be authorized.

P10-F and later remain closed.

Research MCP production, Semantic Resolver production, and P11 production remain closed.
