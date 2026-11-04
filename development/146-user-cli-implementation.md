# FFDF User CLI Implementation Record

Date: 2026-11-05
Scope: post-closeout operational usability; CN/HK only

## Implemented

- Added `src/financial_filing_data_foundation/user_cli.py`.
- Added repository-root `ffdf.cmd`.
- Added reversible `scripts/install-user-cli.ps1`.
- Added user commands: `acquire`, `ingest`, `status`.
- Added deterministic period/filing-type mappings.
- Added default publication search windows with optional explicit overrides.
- Added isolated operational workspace under `workspace/ingest`.
- Added safe P8 live-catalog upsert with conflict rejection.
- Added unit tests for mappings, command shape, and catalog safety.

## Behavior

`acquire`:
Registry check -> Dayu doctor -> official discovery/download when needed ->
PDF/SHA validation -> Raw Store -> Registry -> receipt.

`ingest`:
acquire -> P3 -> P4 -> P5 -> P6 -> P7 -> register_parsed_data ->
P8 catalog if validation has zero blocking issues.

`status`:
reports local Raw state, parsed runs, and P8 catalog registration.

## Production invariants preserved

- SUPPORTED_MARKETS remains exactly CN/HK.
- Existing P0-P10 parsing and validation modules are reused unchanged.
- No raw/source mutation.
- No AI/API integration.
- REVIEW_REQUIRED remains explicit.
- P8 identity conflicts are never silently overwritten.

## Acceptance result

- compileall: PASS
- installer PowerShell syntax: PASS
- CLI focused tests: 5 passed
- `ffdf.cmd --help`: PASS
- `ffdf status --market CN --ticker 600519 --year 2026 --period Q3`: PASS without network access
- full unit regression with required short Windows basetemp: 450 passed / 0 failed
- git diff --check: PASS

No live filing was downloaded during CLI acceptance.
