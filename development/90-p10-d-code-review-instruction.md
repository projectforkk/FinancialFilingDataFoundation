# 90 — P10-D Detached Code Review Instruction

Status: **AUTHORIZED — P10-D REVIEW ONLY**

Phase:
`P10 — Codex Dynamic Research Integration`

Gate:
`P10-D — Research Context / Capability Manifest`

Design baseline:
`ba962aef818d7a31731637a5cfef1f57020a7d1d`

Reauthorization:
`development/88-p10-d-context-reauthorization.md`

Final production/test candidate:
`c8b4041c2d06e1d601707ca765ddd9e817f0dfc9`

Development evidence:
`development/89-p10-d-context-evidence.md`

Latest evidence commit:
`1033c5b779f1877172546d6e30d7ad204b28fd7e`

## 1. Review isolation

Create a fresh detached review worktree inside:

`D:\Codex\FinancialFilingDataFoundation\worktrees\review\p10-d-<shortsha>`

Review HEAD must be the exact governance candidate containing this instruction.

All Python/test commands must bind:

`PYTHONPATH=<detached-review-worktree>\src`

Do not execute shared active/main source.

No reset/clean/rebase/force push/history rewrite.

## 2. Mandatory review inputs

Read and compare:

- design/24 Sections 11–14, 35–36, P10-ISSUE-003；
- design/25 P10-D；
- acceptance/38 items 21–23 and item 69；
- development/87；
- development/88；
- development/89；
- exact production/test diff from `8fd2604..c8b4041`。

Confirm P10-E and later production is absent.

## 3. Contract review

Independently verify:

- exact P8 accepted integration descriptor；
- main runtime does not import dedicated `mcp/server.py`；
- exact P8 descriptor fingerprint；
- exact P9 public policy descriptor/fingerprint；
- P8/P9 public version drift fails closed；
- current catalog raw-byte SHA；
- current catalog semantic reload/equality through accepted `McpCatalog.load`；
- malformed/stale caller catalog maps to `P10_CATALOG_INVALID`；
- spec verification remains active；
- exact fixed capability mapping/hash；
- no caller capability override；
- canonical project-relative P9 review-root；
- absolute/drive-relative/traversal/symlink escape rejected；
- missing/not-directory review-root rejected；
- review-root identity included in context ID；
- exact Section 13.7 context ID bytes；
- no absolute path serialized；
- deterministic/reproducible context。

## 4. Independent execution

Run at minimum:

- focused `tests/unit/research/test_research_context.py`；
- full `tests/unit`；
- compile/import；
- `git diff --check`；
- P8/P9 source/test scope diff；
- dependency/runtime diff；
- forbidden production-surface scan。

Use fresh project-local short basetemps.

## 5. Direct probes

Independently prove at least:

1. known P8 fingerprint =
   `bbeb600e732d5ca567193602d2a2b067fcedeabf9cb5d7cfdf5598671c267bc8`；
2. known P9 fingerprint =
   `9b7a1078ab2365862dc5061c3b2a76a43f865553eb4df5938b96ffe9bbd4ff36`；
3. known capability hash =
   `30df28e273379e91c245222b751aaab1504b6c725ca4170a8fb6168082735935`；
4. known context fixture ID =
   `a06bbce2a58e6af4b84e5259c41439b4bae0567e3076e2320d26e3d08661d9eb`；
5. malformed manually-constructed `McpCatalog` -> `P10_CATALOG_INVALID`；
6. different review roots -> different context IDs；
7. serialized context contains no project absolute path；
8. P8 dedicated runtime server version/exact 11 tool names equal the frozen descriptor；
9. imported research/context modules resolve to detached candidate `src`。

## 6. Security / scope

Production must contain no:

- network/remote AI API；
- external MCP SDK；
- dedicated MCP server import in main-runtime context；
- subprocess/shell；
- SQL；
- environment dump；
- recursive prompt discovery。

No P8/P9 source/test changes.
No dependency/runtime changes.

## 7. Verdict

Allowed:

`PASS / FAIL / CHANGES REQUIRED`

PASS closes P10-D review and permits a later separate P10-E authorization.

This instruction does not authorize P10-E production.
