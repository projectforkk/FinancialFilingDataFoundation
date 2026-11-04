# 100 — P10-F Detached Code Review Instruction

Status: **AUTHORIZED — P10-F REVIEW ONLY**

Phase:
`P10 — Codex Dynamic Research Integration`

Gate under review:
`P10-F — Deterministic CLI`

Design baseline:
`860e628ecf9f804734c9d343b3f2a9894928c9e9`

Reauthorization:
`development/98-p10-f-cli-reauthorization.md`

Production candidate:
`d8e7d81b4bb5a4f06cead9eba0e2d09884094676`

Development evidence:
`development/99-p10-f-cli-evidence.md`

Evidence commit:
`fad7f84`

## 1. Review isolation

Create a fresh detached worktree under:

`D:\\Codex\\FinancialFilingDataFoundation\\worktrees\\review\\p10-f-<authorization-sha>`

Review the authorization HEAD while keeping the exact production candidate identity above frozen.

Every Python/subprocess command must bind:

`PYTHONPATH=<detached-review-worktree>\\src`

Do not execute active/main source.

No reset/clean/rebase/force push.

All temp/probe state must remain under the canonical project root.

Use project-local single-character pytest basetemps for full regression because accepted P9 snapshot paths remain sensitive to Windows path length. Preserve pre-existing single-character directories whole under ignored `workspace/scratch` rather than deleting them.

## 2. Mandatory design/code review

Read and compare:

- design/24 Section 31 / error model / P10-ISSUE-005;
- design/25 P10-F;
- acceptance/38 CLI matrix;
- development/97;
- development/98;
- development/99;
- exact candidate diff `ad45e77..d8e7d81`.

Verify:

- exact four commands;
- exact argv;
- stdin-only JSON;
- 16 MiB limit;
- exact request schemas;
- project-relative catalog boundary;
- review-root contract reuse;
- spec-first precedence;
- deterministic context rebuild;
- exact canonical JSON envelopes;
- LF-only raw machine bytes on Windows;
- exit codes 0/1/2;
- parser/help behavior;
- domain reason propagation;
- fixed unexpected-error behavior;
- no traceback/usage prose;
- no implicit artifact write;
- no P8 business proxy;
- no P9 mutation;
- no P10-G or later production.

## 3. Required independent execution

Run at minimum:

- focused `tests/unit/research/test_research_cli.py`;
- entire `tests/unit/research`;
- full `tests/unit`;
- compile/import;
- raw subprocess byte probes;
- stdin size/encoding/request-schema negatives;
- spec-drift precedence probes;
- catalog/review-root boundary probes;
- `git diff --check`;
- P8/P9 source/test diff;
- dependency/runtime diff;
- forbidden-surface scan;
- detached status clean before/after.

## 4. Raw subprocess requirements

Independently capture raw `stdout/stderr` bytes for at least:

1. `freeze-spec` success;
2. `freeze-spec --help` parser error;
3. invalid JSON stdin;
4. >16 MiB stdin.

Verify:

- exact one line;
- `\n` terminator;
- no `\r\n`;
- correct stream;
- correct exit code;
- canonical/sorted/compact JSON;
- no traceback;
- no usage prose.

## 5. Security / scope

P10-F production must contain no:

- external MCP SDK;
- OpenAI/Codex/Anthropic client;
- network/socket;
- subprocess/shell;
- SQL/sqlite;
- arbitrary request-file browse;
- P8 MCP business proxy;
- P9 prepare/submit/materialize;
- implicit output persistence.

No P8/P9 source/test change.
No dependency/runtime change.
No P10-G integration instruction.

## 6. Verdict

Allowed:

`PASS / FAIL / BLOCKED`

FAIL/BLOCKED:

`STOP → facts/root cause → Design-First corrective loop`

Do not fix production in the detached review worktree.

PASS closes P10-F review only.

P10-G requires a separate pre-implementation review and explicit authorization.

Research MCP production, Semantic Resolver production, and P11 production remain closed.
