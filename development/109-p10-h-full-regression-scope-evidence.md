# 109 — P10-H Full Regression / Scope Evidence

Status: **PASS — P10-H CLOSED**

Phase:
`P10 — Codex Dynamic Research Integration`

Gate:
`P10-H — Full Regression / Scope`

Authorization:
`development/108-p10-h-full-regression-authorization.md`

Authorization commit:
`5ee88e96e9f8d236e84bebaad7a0b85e34cd3c01`

Accepted P9 main baseline:
`e9b30626f2b88ac5527d42bd76d0b682efbeef0e`

Branch:
`design/p10-dynamic-research-integration`

## 1. Exact candidate identity

During validation:

```text
HEAD=5ee88e96e9f8d236e84bebaad7a0b85e34cd3c01
REMOTE=5ee88e96e9f8d236e84bebaad7a0b85e34cd3c01
```

Worktree was clean before and after validation.

Exact source binding:

`PYTHONPATH=D:\\Codex\\FinancialFilingDataFoundation\\worktrees\\active\\p10-dynamic-research-design\\src`

No editable/install was used.

## 2. P10 focused regression

Fresh project-local single-character basetemp:

`D:\\Codex\\FinancialFilingDataFoundation\\worktrees\\t\\w`

Prior `w` was preserved whole at:

`workspace/scratch/p10-h-preserved-w-before-5ee88e9`

Result:

```text
136 passed in 22.54s
RESEARCH_EXIT=0
```

## 3. Full P0-P10 unit regression

Fresh project-local single-character basetemp:

`D:\\Codex\\FinancialFilingDataFoundation\\worktrees\\t\\x`

Prior `x` was preserved whole at:

`workspace/scratch/p10-h-preserved-x-before-5ee88e9`

Result:

```text
444 passed in 37.49s
FULL_EXIT=0
```

No prior-stage regression was found.

## 4. Compile / import

Compile:

```text
COMPILE_EXIT=0
```

Exact imports:

```text
IMPORT_OK
research=...\worktrees\active\p10-dynamic-research-design\src\financial_filing_data_foundation\research\__init__.py
spec=...\research\spec.py
context=...\research\context.py
provenance=...\research\provenance.py
cli=...\research\cli.py
mcp_sdk=None
IMPORT_EXIT=0
```

All P10 imports resolve to exact active candidate source.

## 5. P0-P9 source/test scope

Exact `src/tests` diff from accepted P9 main baseline contains only P10 additions:

```text
A  src/financial_filing_data_foundation/research/__init__.py
A  src/financial_filing_data_foundation/research/cli.py
A  src/financial_filing_data_foundation/research/context.py
A  src/financial_filing_data_foundation/research/models.py
A  src/financial_filing_data_foundation/research/provenance.py
A  src/financial_filing_data_foundation/research/spec.py
A  tests/unit/research/test_research_cli.py
A  tests/unit/research/test_research_context.py
A  tests/unit/research/test_research_provenance.py
A  tests/unit/research/test_research_spec.py
```

P8 source/test diff:
`NONE`

P9 source/test diff:
`NONE`

Therefore no accepted P0-P9 production/test implementation was modified by P10.

## 6. P8 exact contract / runtime

Dedicated accepted P8 runtime was used with exact candidate source binding.

Observed:

```text
P8_SERVER_VERSION=p8-local-mcp-v1
P8_TOOL_COUNT=11
P8_TOOLS=
ffdf_list_documents
ffdf_get_document
ffdf_search_document
ffdf_read_pages
ffdf_list_sections
ffdf_list_tables
ffdf_get_table
ffdf_list_raw_facts
ffdf_get_fact
ffdf_get_evidence
ffdf_get_validation
P8_CONTRACT_EXIT=0
```

Runtime lock:

`runtime-locks/mcp-2.3.0-py312-win-amd64.lock.txt`

SHA256:

`8e958b8abcfd9b2de829451ffc253932fa26bb473f73837484b75b1019f092ec`

This matches the accepted P8 lock.

## 7. Dependency / runtime scope

Dependency/runtime diff from accepted P9 main:
`NONE`

No new runtime or dependency was added for P10.

## 8. Security / forbidden production surface

Static P10 production scan:

`FORBIDDEN_SURFACE=NONE`

Verified absent:

- external MCP SDK in main runtime;
- OpenAI/Codex/Anthropic API client;
- network client/socket;
- subprocess/shell;
- SQL/sqlite;
- P9 mutation APIs inside P10 production.

P10 production remains deterministic local integration plumbing.

## 9. Future production absence

Observed:

```text
src/financial_filing_data_foundation/semantic=ABSENT
src/financial_filing_data_foundation/sec=ABSENT
src/financial_filing_data_foundation/research_mcp=ABSENT
```

Therefore no Semantic Resolver, P11 SEC provider, or Research MCP production has been added.

## 10. P10-G integration artifact identity

Binary-safe exact Git blob check:

```text
INTEGRATION_BLOB_SHA256=ef10406c9957f7a68a9af001c913deef0a057e166100a2d852c0c8fcd2c46296
```

This matches the P10-ISSUE-006 amended frozen identity.

## 11. Diff / status

`git diff --check e9b3062..HEAD`:
**PASS**

Final status:

```text
## design/p10-dynamic-research-integration...origin/design/p10-dynamic-research-integration
```

No production/test/runtime mutation occurred during P10-H.

## 12. Verdict

# PASS

P10-H Full Regression / Scope is closed.

A separate explicit authorization may begin:

`P10-I — Dynamic Spec Integration`

P10-I and later remain closed until separately authorized.

Research MCP production, Semantic Resolver production, and P11 production remain closed.
