# 141 — P10-O v2 Integration Evidence

Status: **PASS — FRESH V2 INTEGRATION GATE CLOSED / MAIN FAST-FORWARD READY**

Phase:
`P10 — Codex Dynamic Research Integration`

Gate:
`P10-O — Closeout`

Authorization:
`development/140-p10-o-closeout-authorization-v2.md`

## 1. Historical invalid closeout isolation

Historical invalid closeout branch/worktree remains untouched:

- branch: `integration/p10-closeout`
- merge commit: `b560f49a78316fa59a4183de326d2dee0a80ebb6`

It was not used for this closeout.

## 2. Fresh v2 integration identity

Recorded origin/main baseline:

`e9b30626f2b88ac5527d42bd76d0b682efbeef0e`

Exact P10 source HEAD merged:

`0b867235214ca46c574822490e55efbcf167247b`

Independent Acceptance result commit:

`a05a3d20c6d2414750e069e44fd95aa81d80f74a`

Accepted detached P10 candidate:

`183ca5dc89a606715a3e352bf92a235f7aa31fad`

Fresh integration branch:

`integration/p10-closeout-v2`

Fresh integration worktree:

`D:\\Codex\\FinancialFilingDataFoundation\\worktrees\\integration\\p10-closeout-v2`

Normal no-ff integration merge commit:

`a539500ef1fd0036eaa8d79a9bf7cfe78db57185`

Merge parents:

- main/P9 parent: `e9b30626f2b88ac5527d42bd76d0b682efbeef0e`
- exact P10 source parent: `0b867235214ca46c574822490e55efbcf167247b`

Merge completed without conflict.

## 3. Exact source binding

All post-merge Python/test commands bound:

`PYTHONPATH=D:\\Codex\\FinancialFilingDataFoundation\\worktrees\\integration\\p10-closeout-v2\\src`

No editable/install was used.

## 4. Post-merge P10 research regression

Result:

```text
136 passed in 24.85s
exit=0
```

Evidence:

`workspace/p10-closeout-v2/results/research-tests.txt`

SHA256:

`627e5f5e862e449fb09f8710fb5aea461b75771b44618bc9a2b0357327728d0d`

## 5. Post-merge full P0-P10 unit regression

Result:

```text
444 passed in 48.03s
exit=0
```

Evidence:

`workspace/p10-closeout-v2/results/full-tests.txt`

SHA256:

`3b2a83dfab4e3665fee75c1f474cec94cf1de381434538093b64461321fc7088`

No P0-P9 regression was observed.

## 6. Compile / import / runtime

```text
COMPILE_EXIT=0
IMPORT_OK
mcp_sdk=None
P9=p9-review-overlay-v1|p9-review-policy-v1|p9-review-resolution-v1|p9-resolved-view-v1
IMPORT_EXIT=0
DIFFCHECK_EXIT=0
```

P10 imports resolved to the fresh integration worktree source.

Runtime audit evidence:

`workspace/p10-closeout-v2/results/runtime-audit.txt`

SHA256:

`0f92d4c41e7246e627314b23aee4ed33639c5352cf11b9c4f526afbf07dc3723`

## 7. P8 accepted boundary

Observed:

```text
SERVER_VERSION=p8-local-mcp-v1
TOOL_COUNT=11
TOOLS=
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
```

P8 runtime lock SHA256:

`8e958b8abcfd9b2de829451ffc253932fa26bb473f73837484b75b1019f092ec`

P8 source/test diff from accepted P9 main baseline:

`NONE`

## 8. P9 accepted boundary

Public contract:

```text
p9-review-overlay-v1
p9-review-policy-v1
p9-review-resolution-v1
p9-resolved-view-v1
```

P9 source/test diff from accepted P9 main baseline:

`NONE`

P9 semantics remain unchanged.

## 9. Dependency / security / future-scope audit

Dependency/runtime diff from accepted P9 main baseline:

`NONE`

Forbidden P10 production surface:

`NONE`

Explicitly absent:

- external MCP SDK in main runtime;
- OpenAI/Anthropic/network clients;
- socket;
- subprocess/shell;
- SQL/sqlite production surface;
- P9 mutation API in P10 production.

Future production paths:

```text
src/financial_filing_data_foundation/semantic=ABSENT
src/financial_filing_data_foundation/sec=ABSENT
src/financial_filing_data_foundation/research_mcp=ABSENT
```

Therefore Research MCP production, Semantic Resolver production, and P11 SEC production remain absent.

## 10. Artifact / acceptance identity

P10-G exact integration Git blob SHA256:

`ef10406c9957f7a68a9af001c913deef0a057e166100a2d852c0c8fcd2c46296`

Independent Acceptance result:

`acceptance/40-p10-independent-acceptance-result.md = PASS`

Acceptance result exact candidate match:

`183ca5dc89a606715a3e352bf92a235f7aa31fad = MATCH`

## 11. Accepted base immutability

Acceptance base manifest Git-blob SHA256:

`ae176a49858caabb45e525fbeb9b99eec23e4b5f649dfa584ebe4656c2dba003`

Entry count:

`47`

Current project files against frozen manifest:

`47 / 47 PASS`

`BASE_IMMUTABLE=True`

Static audit evidence:

`workspace/p10-closeout-v2/results/static-audit.txt`

SHA256:

`4179a672d9e902860396f5cb907383c64b3dad86b30b2b91a6de4b43c5fe2ff7`

## 12. Integration worktree state

Before this evidence/status closeout change:

```text
## integration/p10-closeout-v2...origin/main [ahead 81]
```

No production/test mutation occurred after the merge.

## 13. Verdict

# PASS — MAIN FAST-FORWARD READY

The fresh v2 integration gate is closed.

Next permitted action under development/140:

1. commit this documentation/governance-only integration evidence;
2. push `integration/p10-closeout-v2`;
3. require `origin/main` still equals `e9b30626...`;
4. fast-forward main to the v2 integration evidence commit;
5. run final main research/full/boundary verification.

P10 is **not declared DONE until final main verification passes**.

P11 production, Research MCP production, and Semantic Resolver production remain closed.
