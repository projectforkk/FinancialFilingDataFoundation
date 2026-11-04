# FFDF CN/HK User CLI Design

Status: FINAL / post-closeout operational surface
Scope: CN/HK only
Production baseline preserved: P0-P10

## 1. Goal

Provide a user-facing Windows command surface over already accepted FFDF acquisition,
P3-P7 parsing, Registry, and P8 catalog capabilities.

The CLI is orchestration only. It must not alter parser semantics, validation policy,
raw/source immutability, supported markets, or P9/P10 contracts.

Required commands:

- `ffdf acquire`: download or reuse one official filing, validate PDF/SHA, commit Raw Store, register source/identity in Registry.
- `ffdf ingest`: run acquire, P3-P7, register parsed data, and publish a non-blocking result to the P8 live catalog.
- `ffdf status`: inspect local Raw/parsed/P8 registration state.

## 2. Supported identity

Markets are exactly `CN` and `HK`.

User period values are exactly:

- Q1
- H1
- Q3
- FY

Canonical company_id defaults to `{MARKET}:{ticker}`, matching the accepted P1/P2 convention.

Identity/Registry filing_type mapping:

| period | filing_type |
|---|---|
| Q1 | QUARTERLY_REPORT |
| H1 | INTERIM_REPORT |
| Q3 | QUARTERLY_REPORT |
| FY | ANNUAL_REPORT |

P8 catalog does not contain raw_fiscal_period, so its filing_type must preserve period uniqueness:

| period | P8 filing_type |
|---|---|
| Q1 | Q1 |
| H1 | H1 |
| Q3 | Q3 |
| FY | ANNUAL |

This prevents same-year Q1/Q3 collisions while preserving the accepted ANNUAL label.

## 3. Publication search window

The fiscal period and publication search window are separate concepts.

When the user does not provide an explicit window, the CLI uses a conservative
official-publication search window and caps the end at the current local date:

- Q1: fiscal year 03-01 through 05-31
- H1: fiscal year 06-01 through 09-30
- Q3: fiscal year 09-01 through 11-30
- FY: next year 01-01 through 06-30

The user may override the window with both `--window-start` and `--window-end`.
One-sided windows are rejected.

## 4. Runtime boundary

The user command runs with the FFDF main venv and source-mode PYTHONPATH.
It does not pip-install FFDF.

Acquisition continues to execute Dayu through the isolated accepted runtime:

`runtimes/ffdf-dayu-2115c86/.venv/Scripts/python.exe`

Dayu doctor is executed before acquisition.

## 5. Persistent operational data

User-initiated operations are isolated under:

`workspace/ingest/`

Layout:

- raw-store/
- registry.sqlite
- acquisition-workspace/
- cn/p3..p7
- hk/p3..p7

The accepted P8 entry remains:

`workspace/mcp/p8-live-catalog.json`

## 6. Ingest gate

`ffdf ingest` always registers the P7 parsed-data record in Registry.

P8 publication occurs only when `blocking_issue_count == 0`.

Therefore:

- PASS with no blocking issues -> Research Ready
- REVIEW_REQUIRED with no blocking issues -> Research Ready, but not silently canonical reusable
- blocking validation -> parsed result retained in Registry, not published into P8 live catalog

No CLI path converts REVIEW_REQUIRED into PASS.

## 7. Catalog safety

Catalog updates are:

- project-relative only;
- schema checked;
- artifact paths validated by `McpCatalog.load`;
- written through a same-directory temporary file then atomically replaced;
- idempotent for the same filing identity + SHA;
- fail-closed when an existing filing identity points to a different SHA;
- fail-closed when a SHA is already bound to a different P8 identity.

Amended/replacement filing conflicts therefore require explicit review rather than silent overwrite.

## 8. User command exposure

Repository root contains `ffdf.cmd`.

It binds:

- `FFDF_ROOT`
- `PYTHONPATH=<root>\src`
- `<root>\.venv\Scripts\python.exe -m financial_filing_data_foundation.user_cli`

From the repository root it can be run as:

`.\ffdf.cmd ...`

For the exact global form `ffdf ...`, the reversible installer
`scripts/install-user-cli.ps1` adds the project root to the Windows User PATH.

## 9. Non-goals

This CLI does not:

- add US or UK providers;
- call remote AI;
- mutate source/raw documents;
- guess filing identity or semantic fields;
- auto-resolve P9 review issues;
- replace P8/P9/P10 research contracts;
- create a Windows background service.

## 10. Acceptance

Required gates:

1. compileall PASS;
2. dedicated CLI unit tests PASS;
3. `python -m ...user_cli --help` PASS;
4. `ffdf.cmd --help` PASS;
5. existing full unit suite PASS;
6. `git diff --check` PASS.
