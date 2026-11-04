# 99 — P10-F Deterministic CLI Development Evidence

Status: **PASS — P10-F CANDIDATE READY FOR REVIEW**

Phase:
`P10 — Codex Dynamic Research Integration`

Gate:
`P10-F — Deterministic CLI`

Design baseline:
`860e628ecf9f804734c9d343b3f2a9894928c9e9`

Reauthorization:
`development/98-p10-f-cli-reauthorization.md`

Reauthorization commit:
`ad45e7711f35d044b2be010ebbf14b5586c0ba0f`

Production/test candidate:
`d8e7d81b4bb5a4f06cead9eba0e2d09884094676`

Branch:
`design/p10-dynamic-research-integration`

Worktree:
`D:\\Codex\\FinancialFilingDataFoundation\\worktrees\\active\\p10-dynamic-research-design`

All development/test/probe paths remained under:
`D:\\Codex\\FinancialFilingDataFoundation`

## 1. Candidate scope

Exact candidate diff from P10-F reauthorization parent:

```text
A  src/financial_filing_data_foundation/research/cli.py
A  tests/unit/research/test_research_cli.py
```

No P8/P9 source or test path changed.

No dependency/runtime file changed.

No P10-G integration instruction, Research MCP, Semantic Resolver, or P11 production was added.

## 2. Implemented machine surface

P10-F exposes exactly:

```text
freeze-spec
verify-spec
build-context
validate-ledger
```

Invocation contract:

```powershell
$env:PYTHONPATH="<exact-candidate-worktree>\src"
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -B -m financial_filing_data_foundation.research.cli <command> ...
```

The main runtime still has no external MCP SDK.

Observed exact import:

```text
cli_file=D:\Codex\FinancialFilingDataFoundation\worktrees\active\p10-dynamic-research-design\src\financial_filing_data_foundation\research\cli.py
commands=freeze-spec|verify-spec|build-context|validate-ledger
max_stdin=16777216
mcp_sdk=None
```

## 3. P10-ISSUE-005 machine contract

Implementation follows design/24 Section 31:

- exactly four subcommands;
- stdin-only JSON object request;
- no request-file option;
- stdin raw-byte max = `16,777,216`;
- exact request object keys;
- project-root-relative catalog argument;
- accepted project-root-relative P9 review-root contract;
- `build-context` verifies spec before catalog/context semantic validation;
- `validate-ledger` verifies spec, loads catalog, rebuilds ResearchContext, then parses/validates ledger;
- no `ResearchContext.from_dict`;
- accepted P10-C/D/E reason codes propagate;
- parser errors use `P10_CLI_ARGUMENT_ERROR`, exit 2;
- input/envelope errors use `P10_CLI_INPUT_INVALID`, exit 1;
- unexpected internal failures use `P10_CLI_FAILED` and fixed message `unexpected CLI failure`;
- success emits exactly one canonical JSON line on stdout, stderr empty, exit 0;
- error emits exactly one canonical JSON line on stderr, stdout empty;
- no argparse usage/help prose;
- no normal-client traceback;
- no implicit artifact write;
- no P8 business-call proxy;
- no P9 mutation;
- no network/AI/external MCP SDK/subprocess/shell/SQL in production.

## 4. Pre-candidate implementation findings

### 4.1 Test collection harness correction

The first two focused attempts failed during pytest collection because a parameterized test used pytest's reserved fixture name `request`.

Observed category:

```text
'request' is a reserved name and cannot be used in @pytest.mark.parametrize
```

This was test-only harness code.

Correction:

- renamed parameterized variables to `raw_request` / `payload`;
- no design or production change was required.

### 4.2 Windows newline product defect

The first executable CLI matrix exposed a real P10-F implementation defect.

Initial implementation used Python `print()` for machine JSON.

On Windows, raw subprocess output ended with:

```text
\r\n
```

instead of the frozen deterministic byte contract:

```text
\n
```

This violated design/24 Section 31 canonical one-line machine output.

Correction before candidate freeze:

- added explicit `_write_json_line`;
- encode canonical JSON as UTF-8 bytes;
- append exact LF byte;
- write through stdout/stderr binary buffer;
- flush explicitly;
- retain a text-stream fallback only for in-process compatibility.

No design amendment was required because the frozen design already required deterministic canonical line bytes.

After correction, the focused CLI matrix passed.

## 5. Focused CLI subprocess matrix

Candidate:

`d8e7d81b4bb5a4f06cead9eba0e2d09884094676`

Command:

```powershell
$env:PYTHONPATH="D:\Codex\FinancialFilingDataFoundation\worktrees\active\p10-dynamic-research-design\src"
$env:PYTHONDONTWRITEBYTECODE="1"
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -B -m pytest tests\unit\research\test_research_cli.py -q -p no:cacheprovider --basetemp D:\Codex\FinancialFilingDataFoundation\worktrees\t\p10f2
```

Result:

```text
32 passed in 8.37s
CLI_EXIT=0
```

Matrix covers:

- exact command set;
- all four success envelopes;
- canonical stdout byte form;
- missing/unknown command;
- `--help`;
- missing/unknown argv;
- request-file option rejection;
- empty stdin;
- malformed JSON;
- non-UTF8 stdin;
- non-object root;
- extra/missing request keys;
- >16 MiB stdin;
- malformed freeze file entries;
- P10-C domain error propagation;
- spec drift;
- build spec-drift precedence over invalid catalog;
- validate spec-drift precedence over invalid ledger;
- catalog absolute/drive-relative/traversal forms;
- invalid catalog mapping;
- invalid review-root propagation;
- malformed ledger propagation;
- fixed unexpected-failure envelope;
- exact candidate source binding.

## 6. Full P10 research regression

Prior single-character basetemp `s` was preserved whole at:

`workspace/scratch/p10-f-preserved-s-before-d8e7d81`

Fresh project-local basetemp:

`D:\\Codex\\FinancialFilingDataFoundation\\worktrees\\t\\s`

Result:

```text
136 passed in 23.11s
RESEARCH_EXIT=0
```

This includes P10-C/D/E plus P10-F tests.

## 7. Full unit regression

Prior single-character basetemp `t` was preserved whole at:

`workspace/scratch/p10-f-preserved-t-before-d8e7d81`

Fresh project-local basetemp:

`D:\\Codex\\FinancialFilingDataFoundation\\worktrees\\t\\t`

Result:

```text
444 passed in 44.84s
FULL_EXIT=0
```

P10-E final review had 412 passing unit tests.

P10-F adds 32 passing focused tests with no prior-stage regression.

## 8. Raw subprocess byte probe

Probe script:

`workspace/scratch/p10-f-raw-cli-probe-d8e7d81.py`

Probe fixture:

`workspace/f`

Both remained project-local.

### freeze-spec success

Observed:

```text
SUCCESS_EXIT=0
SUCCESS_STDOUT_REPR=b'{"command":"freeze-spec","data":{"files":[{"logical_name":"rules","relative_path":"inputs/rules.md","sha256":"a73e36ec19ff2a725608408e2b396eadd2ac6046cfa31e010f8d62daab565165","size":6}],"schema_version":"p10-research-spec-bundle-v1","spec_bundle_hash":"021830ab8ded8e8e5eeeef4aa190cf3ffa86ff73a97556f1ebc80f5245288371"},"status":"OK"}\n'
SUCCESS_STDERR_REPR=b''
```

### parser/help error

Observed:

```text
HELP_EXIT=2
HELP_STDOUT_REPR=b''
HELP_STDERR_REPR=b'{"command":"freeze-spec","message":"invalid command line arguments","reason_code":"P10_CLI_ARGUMENT_ERROR","status":"ERROR"}\n'
```

No usage/help prose and no traceback was emitted.

### invalid JSON input error

Observed:

```text
INPUT_EXIT=1
INPUT_STDOUT_REPR=b''
INPUT_STDERR_REPR=b'{"command":"freeze-spec","message":"stdin request is invalid JSON","reason_code":"P10_CLI_INPUT_INVALID","status":"ERROR"}\n'
```

Probe assertions:

```text
RAW_LF_ONLY=PASS
RAW_SUBPROCESS_PROBE=PASS
PROBE_EXIT=0
```

Therefore machine output is verified on Windows at the raw byte level as LF-only, not merely text-normalized by pytest.

## 9. Compile / import

Candidate:

`d8e7d81b4bb5a4f06cead9eba0e2d09884094676`

Observed:

```text
COMPILE_EXIT=0
IMPORT_OK
cli_file=D:\Codex\FinancialFilingDataFoundation\worktrees\active\p10-dynamic-research-design\src\financial_filing_data_foundation\research\cli.py
commands=freeze-spec|verify-spec|build-context|validate-ledger
max_stdin=16777216
mcp_sdk=None
main_sig=(argv: Sequence[str] | None = None) -> int
IMPORT_EXIT=0
```

## 10. Scope / security

`git diff --check ad45e77..d8e7d81`:
**PASS**

P8/P9 source/test diff:

`NONE`

Dependency/runtime diff:

`NONE`

Forbidden production surface scan:

`NONE`

Explicit scan covered:

- P9 mutation APIs;
- OpenAI/Anthropic/network clients;
- socket;
- subprocess;
- sqlite/SQL;
- external MCP SDK.

Request-file production surface:

`NONE`

P10-G integration instruction:

`ABSENT`

No P10-G or later production is present.

## 11. Encoding

UTF-8 decode PASS and BOM absent for:

- `research/cli.py`;
- `test_research_cli.py`.

Repository CRLF checkout warnings are Git/Windows working-tree canonicalization behavior. The candidate Git diff passed `git diff --check`, and raw subprocess output itself is LF-only.

## 12. Final candidate identity/state

Candidate:

`d8e7d81b4bb5a4f06cead9eba0e2d09884094676`

During exact-candidate validation:

```text
HEAD=d8e7d81b4bb5a4f06cead9eba0e2d09884094676
REMOTE=d8e7d81b4bb5a4f06cead9eba0e2d09884094676
```

Tracked worktree status before/after exact validation:

```text
## design/p10-dynamic-research-integration...origin/design/p10-dynamic-research-integration
```

No production/test/runtime file was modified after the candidate commit.

## 13. Gate verdict

# PASS — P10-F CANDIDATE READY FOR REVIEW

P10-F implementation candidate is complete.

After this evidence is committed/pushed:

**STOP P10-F development.**

A separate detached P10-F Code Review is required before P10-G can be authorized.

P10-G and later remain closed.

Research MCP production, Semantic Resolver production, and P11 production remain closed.
