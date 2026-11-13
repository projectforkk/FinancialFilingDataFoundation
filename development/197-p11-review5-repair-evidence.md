# P11 Review 5 Repair Evidence

## Status

This is development evidence only. The exact production candidate is ready for a fresh, full, exact-candidate review by ChatGPT.

The repair is intentionally stopped at the development-candidate handoff. No design file was modified, no formal test plan was created, no formal acceptance was run, and no main-branch merge was performed.

## Authority and exact candidate

| Item | Value |
| --- | --- |
| Repository | `projectforkk/FinancialFilingDataFoundation` |
| Worktree | `D:\Codex\FinancialFilingDataFoundation\worktrees\active\p11-sec-rebuild-development` |
| Branch | `task/p11-sec-rebuild-development` |
| Authorized remote target | `origin/reconcile/p11-140-143-local-chain` |
| Starting authorization head | `0ae1596b7e5df5038c298d9a453171b40c81334b` |
| Design baseline | `70353788d0b6188e757e24b10b0883b0a9a057dd` |
| Previous production candidate | `a65723c3cf17bbccf10748e2c671671a2c7dfb1b` |
| New production candidate | `35e2b70c78b6cff931c8484dc38f2eb7349735f5` |

The production candidate was pushed normally from the authorized branch to the authorized remote target. The evidence commit is documentation-only and follows the candidate; it does not change the production candidate.

## Review 5 repair closure

### ISSUE-142: SEC discovery freshness and history safety

- `filings.files` is treated as a valid empty history inventory when absent.
- When present, it must be a list of descriptor objects with safe, non-empty names.
- Duplicate normalized names are rejected.
- Date fields require exact `YYYY-MM-DD` strings, valid calendar dates, and non-reversed ranges; no truncation or coercion is performed.
- Snake-case aliases are retained only when they are exact strings.
- `select_history_chunks` validates chunk types, safe names, exact dates, duplicate normalized names, and range ordering.
- Online and P7 selection use the same validated selector path.

### ISSUE-143: SEC XML source identity and replay

- Authentic XBRL instance roots are scanned across package member bytes and must resolve to exactly one instance source.
- XML and Inline XBRL source modes cannot be mixed.
- XML locators, facts, contexts, units, raw attributes, values, and evidence are reconstructed from the immutable source node and compared with the artifact.
- Context and unit canonical projections include the required period, entity, dimensions, and measures.
- A wrong authentic-instance role, foreign context/unit, source-member divergence, or source-node semantic divergence is blocking.

### ISSUE-145: raw fact and evidence source binding

- Inline facts are replayed from the primary source DOM, including continuation chains, hidden state, source fragments, fragment hashes, numeric candidates, and locator identity.
- XML facts are replayed from the unique authentic XBRL instance source.
- Raw fact fields and evidence fields are checked for semantic equality with the replayed source node.
- `P11_RAW_FACT_SOURCE_MISMATCH` is a blocking validation code.

### Validation artifact and MCP closure

- Validation schema is frozen as `p11-sec-validation-v3`.
- Validation artifacts are written atomically below `<p7>/<package_sha256>/p11-sec-validation-v3`.
- Current v3 loading validates the package SHA and versioned path identity.
- Flat v2 artifacts are not accepted as a fallback.
- MCP service loading uses the canonical P7/package validation path only; direct or legacy fallback loading was removed.

## Frozen identifiers

```text
SEC_DISCOVERY_SCHEMA = p11-sec-discovery-v1
VIRTUAL_HTML_NORMALIZER_VERSION = VIRTUAL_HTML_V6
SEC_ARTIFACT_SCHEMA = p11-sec-artifacts-v2
SEC_VALIDATION_SCHEMA = p11-sec-validation-v3
SEC_REGISTRY_SCHEMA_VERSION = 4
P11_RAW_FACT_SOURCE_MISMATCH = P11_RAW_FACT_SOURCE_MISMATCH / BLOCKING
```

## Changed production paths in the candidate

```text
src/financial_filing_data_foundation/mcp/service.py
src/financial_filing_data_foundation/us_sec/__init__.py
src/financial_filing_data_foundation/us_sec/discovery.py
src/financial_filing_data_foundation/us_sec/errors.py
src/financial_filing_data_foundation/us_sec/parser.py
src/financial_filing_data_foundation/us_sec/validation.py
```

## Changed test paths in the candidate

```text
tests/unit/us_sec/test_repair_140_143.py
tests/unit/us_sec/test_validation_p8.py
```

The test changes cover the strict history matrix, Inline and XML source-node tampering, continuation chains, context/unit semantics, evidence locator divergence, and validation-v3 path and no-fallback behavior.

## Exact-candidate developer verification

All checks below were rerun at exact candidate `35e2b70c78b6cff931c8484dc38f2eb7349735f5`, in the worktree above, with Python `3.14.9` and pytest `9.2.0`. Temporary pytest roots were outside the repository under `D:\ffdf-p11-test`; no test skips were reported.

```text
python -m compileall src tests
exit 0

git diff --check
exit 0
```

```text
python -m pytest -q tests/unit/us_sec/test_repair_140_143.py tests/unit/us_sec/test_validation_p8.py --basetemp D:\ffdf-p11-test\candidate35-focused
79 passed in 1.66s

python -m pytest -q tests/unit/us_sec --basetemp D:\ffdf-p11-test\candidate35-ussec
244 passed in 17.20s

python -m pytest -q tests/unit/mcp tests/unit/us_sec/test_validation_p8.py tests/unit/us_sec/test_package_registry.py --basetemp D:\ffdf-p11-test\candidate35-mcp
93 passed in 8.83s

python -m pytest -q tests/unit/acquisition tests/unit/identity tests/unit/validation tests/unit/registry tests/unit/mcp tests/unit/research tests/unit/review --basetemp D:\ffdf-p11-test\candidate35-p0p10
371 passed in 59.10s

python -m pytest -q tests/unit --basetemp D:\ffdf-p11-test\candidate35-full
774 passed in 80.82s
```

## Apple production-path smoke

The normal production CLI path was run against isolated root `D:\ffdf-p11-c35-live-20261113` with `FFDF_P11_US_DEV` absent:

```text
FFDF_ROOT=D:\ffdf-p11-c35-live-20261113
python -m financial_filing_data_foundation.user_cli ingest --market US --cik 320193 --ticker AAPL --year 2025 --period FY
exit 0
```

Observed result:

```text
accession: 0000320193-25-000079
package_sha256: 079185e72f20bd4fc1a2a19b2c57430390b2fb5482403b51752525a0264ff131
validation: PASS
blocking_issue_count: 0
review_issue_count: 0
P8: ADDED
research_ready: true
```

The traced production-path run used isolated root `D:\ffdf-p11-c35-live-traced-20261113` and recorded the URLs requested by the production transport without changing the production code. It observed:

```text
current submissions fetches: 1
selected history chunks: 0
history fetches: 0
archive fetches: 8
static-asset fetches: 0
```

The discovery observation was written to:

```text
D:\ffdf-p11-c35-live-traced-20261113\workspace\ingest\us\discovery\b07b419aab758287675bd07e29ef4c91743c1226502d1fc1a83734dada427cbd.json
```

Its observation SHA is `b07b419aab758287675bd07e29ef4c91743c1226502d1fc1a83734dada427cbd`; it records one discovery source, the selected accession above, and state `UNAMBIGUOUS`.

The traced run also recorded:

```text
V6 manifest fact_source_mode: INLINE_XBRL_PRIMARY
V6 manifest fact_count: 1131
V6 manifest issue_count: 0
V6 manifest table_count: 62
validation path: D:\ffdf-p11-c35-live-traced-20261113\workspace\ingest\us\p7\079185e72f20bd4fc1a2a19b2c57430390b2fb5482403b51752525a0264ff131\p11-sec-validation-v3
validation schema: p11-sec-validation-v3
P7 validation: PASS
P7 blocking issues: 0
P7 review issues: 0
catalog: ADDED
research_ready: true
```

## Governance stop

```text
Formal Test Plan: NOT CREATED
Formal Test execution: NOT PERFORMED
Formal Acceptance: NOT RUN
Main merge: NOT RUN
P11 DONE: NO
REVIEW_PASS: NOT DECLARED
STOP FOR CHATGPT FRESH FULL EXACT-CANDIDATE REVIEW.
```

Candidate-to-evidence scope is documentation-only:

```text
candidate: 35e2b70c78b6cff931c8484dc38f2eb7349735f5
candidate -> evidence changed paths: development/197-p11-review5-repair-evidence.md only
CANDIDATE -> EVIDENCE: DOCUMENTATION ONLY — YES
```
