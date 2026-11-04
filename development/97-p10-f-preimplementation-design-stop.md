# 97 — P10-F Pre-Implementation Design Stop

Status: **STOPPED — P10-ISSUE-005 DESIGN AMENDMENT REQUIRED**

Phase:
`P10 — Codex Dynamic Research Integration`

Gate:
`P10-F — Deterministic CLI`

Prerequisite review:
`development/96-p10-e-detached-code-review-result.md = PASS`

Current branch baseline before P10-F:
`af7295d`

## 1. Stop timing

P10-F production had not started.

No `research/cli.py` existed.

No P10-F focused test existed.

The issue was found during the required pre-implementation contract review.

No P10-C/D/E production or tests were modified.

No P8/P9 source/test/runtime was modified.

## 2. Facts

The current design froze only:

- four command names;
- JSON stdout/stderr intent;
- deterministic parser failures;
- no argparse prose;
- no AI/network/subprocess.

It did **not** freeze:

- command-line arguments;
- stdin/request transport;
- request JSON envelope per command;
- catalog/review-root input representation;
- success JSON envelope;
- error JSON envelope;
- parser/transport/internal reason codes;
- exit codes;
- stdin size boundary;
- malformed request classification;
- catalog-load error mapping;
- whether `validate-ledger` consumes or deterministically rebuilds `ResearchContext`;
- exact error precedence for spec drift vs later ledger validation.

## 3. Risk

Without amendment, multiple incompatible implementations could all appear compliant.

Examples:

1. one implementation could use inline JSON while another reads arbitrary files;
2. one could deserialize a persisted context while another silently rebuilds it;
3. parser failures could emit different reason codes/exit codes;
4. malformed ledger could win over spec drift in one implementation and not another;
5. CLI file browsing could widen the P10 filesystem surface;
6. acceptance could not reproduce a single exact subprocess matrix.

## 4. Approved correction direction

Before P10-F code, freeze an exact machine contract:

- exact four subcommands;
- explicit exact-candidate `PYTHONPATH`;
- JSON request on stdin only;
- bounded stdin bytes;
- exact command args;
- project-root-relative catalog and P9 review-root semantics;
- exact request object schema for each command;
- exact success/error envelopes;
- exact canonical JSON serializer;
- exact exit codes;
- deterministic parser errors with no usage/help prose;
- no traceback to normal client;
- `validate-ledger` rebuilds context from frozen spec/catalog/review-root, then validates ledger;
- spec verification occurs before catalog/ledger semantic validation where the request envelope permits;
- no P8/P9 business-call proxy;
- no additional filesystem browse surface;
- no new dependency/runtime.

## 5. Gate boundary

Required sequence:

```text
STOP P10-F
→ amend design/24
→ amend design/25
→ amend acceptance/38
→ update governance/status
→ commit/push new design baseline
→ new explicit P10-F authorization
→ implementation
```

P10-G and later remain closed.

Research MCP production, Semantic Resolver production, and P11 production remain closed.
