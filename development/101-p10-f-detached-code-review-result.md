# 101 — P10-F Detached Code Review Result

Status: **PASS — P10-F REVIEW CLOSED**

Phase:
`P10 — Codex Dynamic Research Integration`

Gate:
`P10-F — Deterministic CLI`

Design baseline:
`860e628ecf9f804734c9d343b3f2a9894928c9e9`

Production candidate:
`d8e7d81b4bb5a4f06cead9eba0e2d09884094676`

Development evidence:
`development/99-p10-f-cli-evidence.md`

Evidence commit:
`fad7f84332c7d2d3c4d9b3afd6f19c5801745c6d`

Review authorization:
`development/100-p10-f-code-review-instruction.md`

Review authorization commit:
`13e5a0954894f48108b68d28ece7593681dbbe0a`

Detached review worktree:
`D:\\Codex\\FinancialFilingDataFoundation\\worktrees\\review\\p10-f-13e5a09`

## 1. Isolation

Detached HEAD remained exactly:

`13e5a0954894f48108b68d28ece7593681dbbe0a`

Status before and after review:

```text
## HEAD (no branch)
```

All Python/subprocess commands bound:

`PYTHONPATH=D:\\Codex\\FinancialFilingDataFoundation\\worktrees\\review\\p10-f-13e5a09\\src`

Observed CLI import:

`D:\\Codex\\FinancialFilingDataFoundation\\worktrees\\review\\p10-f-13e5a09\\src\\financial_filing_data_foundation\\research\\cli.py`

No active/main source was executed.

## 2. Candidate scope

Exact production/test candidate diff:

```text
A  src/financial_filing_data_foundation/research/cli.py
A  tests/unit/research/test_research_cli.py
```

No P8/P9 source or test path changed.

No dependency/runtime file changed.

No P10-G integration instruction or later production existed in the reviewed candidate.

## 3. Design/code review

Reviewed against:

- design/24 Section 31;
- design/24 error model;
- P10-ISSUE-005;
- design/25 P10-F;
- acceptance/38 CLI matrix;
- development/97;
- development/98;
- development/99.

Verified:

- exact four commands only;
- exact argv contract;
- stdin-only JSON object transport;
- 16 MiB hard request limit;
- no request-file option;
- exact request object schemas;
- project-root-relative catalog boundary;
- accepted P9 review-root semantics reused;
- `build-context` spec-first validation;
- `validate-ledger` spec-first validation and deterministic context rebuild;
- no `ResearchContext.from_dict`;
- exact canonical JSON serializer;
- raw Windows machine output is LF-only UTF-8;
- success exit 0 / stdout one JSON / stderr empty;
- handled/domain/input failure exit 1 / stdout empty / stderr one JSON;
- parser failure exit 2 / `P10_CLI_ARGUMENT_ERROR`;
- `--help` and `-h` do not emit argparse prose;
- normal client receives no traceback;
- accepted P10-C/D/E reason codes propagate;
- unexpected failure uses fixed `P10_CLI_FAILED` envelope/message;
- no implicit artifact persistence;
- no P8 business-call proxy;
- no P9 mutation;
- no financial reasoning added.

No design/implementation mismatch was found.

## 4. Focused independent execution

Fresh detached-source command used a project-local basetemp.

Result:

```text
32 passed in 10.45s
FOCUSED_EXIT=0
```

## 5. Full P10 research regression

Prior single-character basetemp `u` was preserved whole under:

`workspace/scratch/p10-f-review-preserved-u-before-13e5a09`

Fresh basetemp:

`D:\\Codex\\FinancialFilingDataFoundation\\worktrees\\t\\u`

Result:

```text
136 passed in 24.13s
RESEARCH_EXIT=0
```

## 6. Full independent unit regression

Prior single-character basetemp `v` was preserved whole under:

`workspace/scratch/p10-f-review-preserved-v-before-13e5a09`

Fresh basetemp:

`D:\\Codex\\FinancialFilingDataFoundation\\worktrees\\t\\v`

Result:

```text
444 passed in 46.88s
FULL_EXIT=0
```

No prior-stage regression was found.

## 7. Independent raw/adversarial subprocess probes

Probe script:

`workspace/scratch/p10-f-review-direct-probe-13e5a09.py`

Probe state:

`workspace/g`

Both remained inside the canonical project root.

Results:

```text
RAW_SUCCESS=PASS
HELP_PARSER=PASS P10_CLI_ARGUMENT_ERROR
INVALID_JSON=PASS P10_CLI_INPUT_INVALID
NON_UTF8=PASS P10_CLI_INPUT_INVALID
OVERSIZE=PASS P10_CLI_INPUT_INVALID
EXTRA_KEY=PASS P10_CLI_INPUT_INVALID
BUILD_CONTEXT=PASS
CATALOG_ESCAPE=PASS P10_CATALOG_INVALID
REVIEW_ROOT=PASS P10_CONTEXT_INCOMPATIBLE
LEDGER_INVALID=PASS P10_PROVENANCE_INVALID
SPEC_FIRST_BUILD=PASS P10_RESEARCH_SPEC_CHANGED
SPEC_FIRST_LEDGER=PASS P10_RESEARCH_SPEC_CHANGED
RAW_LF_ONLY=PASS
CANONICAL_JSON=PASS
DIRECT_REVIEW_PROBES=PASS
PROBE_EXIT=0
```

Raw success bytes:

```text
b'{"command":"freeze-spec","data":{"files":[{"logical_name":"rules","relative_path":"inputs/rules.md","sha256":"a73e36ec19ff2a725608408e2b396eadd2ac6046cfa31e010f8d62daab565165","size":6}],"schema_version":"p10-research-spec-bundle-v1","spec_bundle_hash":"021830ab8ded8e8e5eeeef4aa190cf3ffa86ff73a97556f1ebc80f5245288371"},"status":"OK"}\n'
```

Raw parser/help bytes:

```text
b'{"command":"freeze-spec","message":"invalid command line arguments","reason_code":"P10_CLI_ARGUMENT_ERROR","status":"ERROR"}\n'
```

No CRLF, usage prose, or traceback was present.

## 8. Compile / import

Result:

```text
COMPILE_EXIT=0
IMPORT_OK
cli_file=D:\Codex\FinancialFilingDataFoundation\worktrees\review\p10-f-13e5a09\src\financial_filing_data_foundation\research\cli.py
commands=freeze-spec|verify-spec|build-context|validate-ledger
max_stdin=16777216
mcp_sdk=None
main_sig=(argv: Sequence[str] | None = None) -> int
IMPORT_EXIT=0
```

## 9. Scope / security

`git diff --check ad45e77..d8e7d81`:
**PASS**

P8/P9 source/test diff:
`NONE`

Dependency/runtime diff:
`NONE`

Forbidden production surface scan:
`NONE`

Additional prohibited-surface scan:
`NONE`

Verified absent:

- external MCP SDK;
- OpenAI/Codex/Anthropic network client;
- socket;
- subprocess/shell;
- SQL/sqlite;
- request-file option;
- `ResearchContext.from_dict`;
- P9 prepare/submit/materialize;
- arbitrary output persistence.

P10-G integration instruction:
`ABSENT`

## 10. Findings

No open correctness, determinism, security, scope, transport, path-boundary, or environment finding remains for P10-F.

`P10-ISSUE-005`:
**CLOSED / PASS**

The pre-candidate Windows CRLF implementation defect was correctly fixed before candidate freeze and did not recur in detached review.

## 11. Verdict

# PASS

P10-F review is closed.

A separate pre-implementation review and explicit instruction may authorize:

`P10-G — Thin Integration Instruction`

This review does not authorize P10-G production.

Research MCP production, Semantic Resolver production, and P11 production remain closed.
