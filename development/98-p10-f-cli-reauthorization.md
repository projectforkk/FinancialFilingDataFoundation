# 98 — P10-F Reauthorization — Deterministic CLI

Status: **AUTHORIZED — P10-F ONLY / P10-ISSUE-005 AMENDED BASELINE**

Phase:
`P10 — Codex Dynamic Research Integration`

Gate:
`P10-F — Deterministic CLI`

Design baseline:
`860e628ecf9f804734c9d343b3f2a9894928c9e9`

Prerequisite review:
`development/96-p10-e-detached-code-review-result.md = PASS`

Pre-implementation stop:
`development/97-p10-f-preimplementation-design-stop.md`

Only P10-F is authorized.

## Allowed production/test scope

Allowed:

- `src/financial_filing_data_foundation/research/cli.py`
- minimal `src/financial_filing_data_foundation/research/__init__.py` export only if required
- `tests/unit/research/test_research_cli.py`

Do not modify P10-C/D/E semantics.

Do not modify P8/P9 source/tests/runtime/dependencies.

## Required machine contract

Implementation must follow design/24 Section 31 exactly:

- four commands only:
  - `freeze-spec`
  - `verify-spec`
  - `build-context`
  - `validate-ledger`
- exact argv contract
- stdin JSON object only
- 16 MiB request limit
- exact request object keys
- no request-file option
- project-root-relative catalog
- existing project-root-relative P9 review root
- canonical one-line JSON output
- exact success/error envelopes
- parser reason `P10_CLI_ARGUMENT_ERROR`, exit 2
- request transport reason `P10_CLI_INPUT_INVALID`, exit 1
- unexpected reason `P10_CLI_FAILED` with fixed message
- accepted domain P10 reason codes preserved
- build/validate spec-first precedence
- validate-ledger rebuilds ResearchContext from spec/catalog/review-root
- no `ResearchContext.from_dict`
- no usage/help prose
- no traceback
- no implicit write
- no P8 business proxy
- no P9 mutation
- no AI/network/external MCP SDK/subprocess/shell/SQL

## Required tests

Implement the design/25 P10-F focused subprocess matrix, including success/error byte behavior and error precedence.

All subprocess tests must bind exact candidate source through:

`PYTHONPATH=<exact-candidate-worktree>\\src`

All pytest basetemps remain inside:

`D:\\Codex\\FinancialFilingDataFoundation`

Use short project-local basetemps where P9 snapshot tests are involved.

## Evidence

After implementation and exact-candidate validation create:

`development/99-p10-f-cli-evidence.md`

Required evidence:

- candidate SHA
- exact commands
- focused CLI matrix result
- full unit result
- compile/import
- raw subprocess examples
- parser/help negative
- stdin size/encoding negatives
- spec-drift precedence
- catalog/review-root boundary
- scope/security scan
- P8/P9 zero diff
- dependency/runtime zero diff
- exact-candidate source binding
- clean status

## Stop

After evidence commit/push:

STOP P10-F.

A separate detached P10-F Code Review is required before P10-G.

P10-G and later remain closed.

Research MCP production, Semantic Resolver production, and P11 production remain closed.
