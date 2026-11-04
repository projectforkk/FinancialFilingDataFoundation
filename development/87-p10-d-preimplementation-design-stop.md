# 87 — P10-D Pre-Implementation Design Stop

Status: **STOPPED — P10-ISSUE-003 DESIGN AMENDMENT REQUIRED**

Phase:
`P10 — Codex Dynamic Research Integration`

Gate:
`P10-D — Research Context / Capability Manifest`

P10-C review:
`development/86-p10-c-detached-code-review-result.md = PASS`

Current production baseline before P10-D:
`35553df23f58a7f539b7390f98c7f154e42c817e`

## 1. Stop timing

P10-D had not been authorized and no `research/context.py` or context-focused test existed.

The issue was found during the required pre-implementation contract review.

No P10-C production/test was modified.

No P8/P9 source/test/runtime was modified.

## 2. Facts

The original design named:

- `p8_tool_contract_fingerprint`；
- `p9_policy_fingerprint`；
- `capability_manifest_hash`；

but did not freeze their exact input bytes.

The original `research_context_id` formula also omitted `p9_review_root`, despite that root being an input and persisted field.

Accepted runtime boundary facts:

- P8 catalog/result schema constants are available from main-runtime public P8 API；
- P8 server version and exact 11 tool names live in dedicated `mcp/server.py`；
- main runtime intentionally has no external MCP SDK；
- P9 policy/schema constants are available from public P9 API。

## 3. Risk

Without amendment:

1. context fingerprints could vary by implementation；
2. different P9 review roots could collide on one context ID；
3. P10 could accidentally import dedicated MCP server and add an MCP SDK requirement to main runtime；
4. caller capability overrides could silently claim unsupported capability；
5. provenance could bind to an incompletely identified context。

## 4. Approved Design-First correction

Before P10-D code:

- remove caller `capability_policy` from P10 v1 build API；
- freeze exact P8 accepted integration descriptor；
- use public P8 catalog/result constants in main runtime；
- cross-check P8 server/tool names only during dedicated-runtime acceptance；
- freeze exact P9 public policy descriptor；
- freeze canonical JSON fingerprint bytes；
- hash current catalog raw bytes and semantically reload through accepted `McpCatalog.load`；
- canonicalize/guard existing project-relative P9 review root；
- include canonical review-root identity in context ID；
- freeze exact capability mapping/hash with no caller override；
- include context schema version in context ID；
- add `P10_CONTEXT_PATH_OUTSIDE_PROJECT`；
- update P10-D focused tests and acceptance items 21–23。

## 5. Gate boundary

Required sequence:

```text
STOP P10-D
→ amend design/24
→ amend design/25
→ amend acceptance/38
→ update governance/status
→ commit/push new design baseline
→ new explicit P10-D authorization
→ implementation
```

No P10-D production may be written before that new baseline is GitHub truth.

P10-E and later remain closed.

Research MCP production, Semantic Resolver production, and P11 production remain closed.
