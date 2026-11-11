# P11 Corrected Design Repair Evidence

## Candidate identity

- Corrected design baseline: `09e3174b7e19a60cc5955862670fac8931af67db`
- Previous production candidate: `9b7fcc9fc37a423eaafd1dde762e9c81d475df9e`
- New P11 production candidate: `5a122478b34e5fce7a3a0e198dd40e5cdb14e07c`
- Branch: `task/p11-sec-rebuild-development`
- Candidate commit: `fix: implement corrected P11 SEC semantics and production gate`

The candidate was pushed to `origin/task/p11-sec-rebuild-development`. No main
merge, destructive reset/clean/force operation, or Formal Acceptance was run.
After the candidate commit, production and test files were frozen; this
documentation-only commit is the only subsequent change.

## Required version constants

| Constant | Value |
|---|---|
| `REGISTRY_SCHEMA_VERSION` | `1` |
| `SEC_REGISTRY_SCHEMA_VERSION` | `4` |
| `SEC_DISCOVERY_SCHEMA` | `p11-sec-discovery-v1` |
| `VIRTUAL_HTML_NORMALIZER_VERSION` | `VIRTUAL_HTML_V5` |
| `SEC_ARTIFACT_SCHEMA` | `p11-sec-artifacts-v2` |
| `SEC_VALIDATION_SCHEMA` | `p11-sec-validation-v2` |

The SEC package SHA formula remains the canonical sorted member-record formula
(`role`, `relative_name`, `member_sha256`, `byte_length`); descriptive
metadata was not added to the package hash.

## ISSUE-123 through ISSUE-130 closure

| Issue | Implemented behavior and evidence |
|---|---|
| P11-ISSUE-123 | Online US acquire/ingest performs current submissions/history discovery before local planning; immutable discovery observations retain official source bytes, hashes, candidates, state, selected accession and as-of time; amendment/conflict/not-found states fail closed; local status reports discovery-as-of data without network. |
| P11-ISSUE-124 | Parser selects exactly one logical fact source: `INLINE_XBRL_PRIMARY` or one verified `XBRL_INSTANCE_PRIMARY`; inline plus extracted instance does not duplicate facts; multiple instance members fail closed. |
| P11-ISSUE-125 | `continuedAt` chains, `ix:continuation`, chained fragments and `ix:exclude` are deterministic; missing, duplicate and cyclic targets are blocking; ordered fragment locators, hashes and source text are revalidated. |
| P11-ISSUE-126 | Archive acquisition uses SEC attachment metadata and exact filing-local references; generic XML is not swept; `OTHER` XML cannot supply facts, contexts or units; `.xbrl` extension alone does not authorize instance classification. |
| P11-ISSUE-127 | Online ticker resolution uses current SEC ticker-map bytes; cached snapshots verify source-byte SHA, reparse the bytes and compare the retained derivative; source/derivative tampering and conflicting cached mappings fail closed; explicit CIK bypass remains. |
| P11-ISSUE-128 | Package construction/reload binds every member URL to package CIK/accession/name; P7 and P8 compare package and member provenance with Registry `source_packages`/`package_members`; manifest, Registry and URL tampering fail closed. |
| P11-ISSUE-129 | SEC HTML table width uses occupied `colspan`/`rowspan` logical grid width; `value_column_count` follows that compatibility width; first-row `td` remains `BODY`; header tree uses actual `th` cells and span metadata. |
| P11-ISSUE-130 | Normal US identity, CLI and P8 paths no longer require `FFDF_P11_US_DEV`; feature-branch supported-market declarations include US while CN/HK behavior remains unchanged. |

## Registry migration

The SEC extension is additive from v3 to v4 and stores immutable discovery
observations. Legacy SQLite `PRAGMA user_version` remains `1`. Migration and
reopen are idempotent. Unknown future SEC extension versions are rejected
before DDL/data mutation. Existing package, binding and parsed rows are retained;
legacy parsed artifacts remain incompatible with the current V5/v2 parser gate.

## Exact changed source and test files

Source files in the production candidate:

- `src/financial_filing_data_foundation/identity/models.py`
- `src/financial_filing_data_foundation/mcp/catalog.py`
- `src/financial_filing_data_foundation/mcp/service.py`
- `src/financial_filing_data_foundation/registry/sqlite_registry.py`
- `src/financial_filing_data_foundation/us_sec/acquisition.py`
- `src/financial_filing_data_foundation/us_sec/discovery.py`
- `src/financial_filing_data_foundation/us_sec/errors.py`
- `src/financial_filing_data_foundation/us_sec/identity.py`
- `src/financial_filing_data_foundation/us_sec/ingest.py`
- `src/financial_filing_data_foundation/us_sec/package.py`
- `src/financial_filing_data_foundation/us_sec/parser.py`
- `src/financial_filing_data_foundation/us_sec/ticker_map.py`
- `src/financial_filing_data_foundation/us_sec/validation.py`
- `src/financial_filing_data_foundation/user_cli.py`

Test files in the production candidate:

- `tests/unit/identity/test_models.py`
- `tests/unit/us_sec/test_cli_runtime.py`
- `tests/unit/us_sec/test_corrected_repair.py`
- `tests/unit/us_sec/test_identity_policy.py`
- `tests/unit/us_sec/test_package_registry.py`
- `tests/unit/us_sec/test_parser.py`
- `tests/unit/us_sec/test_provider_cli.py`
- `tests/unit/us_sec/test_validation_p8.py`

No accepted CN/HK raw documents, P3-P10 artifacts, or their Registry rows were
mutated. The candidate commit contains only the listed source/test paths; the
CN/HK regression suite remained green.

## Developer verification

All commands below ran in
`D:\Codex\FinancialFilingDataFoundation\worktrees\active\p11-sec-rebuild-development`
with the existing project Python
`D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe`.

| Command | Exit | Result |
|---|---:|---|
| `& $py -m compileall src` | 0 | Compile succeeded. |
| `& $py -m pytest tests/unit/us_sec -q --basetemp D:\t\p11-final2-ussec` | 0 | `115 passed` |
| `& $py -m pytest tests/unit -q --basetemp D:\t\p11-final2-unit` | 0 | `645 passed` |
| `& $py -m pytest -q tests/unit/acquisition tests/unit/identity tests/unit/validation tests/unit/registry tests/unit/mcp tests/unit/research tests/unit/review --basetemp D:\t\p11-final2-cnhk-p8p9p10` | 0 | `371 passed` |
| `git diff --check` before candidate commit | 0 | No whitespace errors. |

Explicit production-mode coverage with `FFDF_P11_US_DEV` absent passed in the
US SEC suite, including:

- `test_us_cli_reuse_data_refreshes_discovery_without_reparsing_or_redownloading`;
- `test_sec_p8_reads_catalog_entry_without_network`;
- `test_sec_ingest_publishes_only_nonblocking_package`;
- `test_us_status_is_local_only_and_reports_discovery_as_of`.

The final full unit result (`645 passed`) is the CN/HK regression result; the
explicit focused CN/HK/P8/P9/P10 result was `371 passed`.

## Acceptance boundary

`FORMAL ACCEPTANCE NOT RUN`.

This commit is a merge-ready production candidate for exact-candidate review;
it is not a P11 acceptance or DONE declaration.
