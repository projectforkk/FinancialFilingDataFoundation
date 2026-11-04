# 113 — P10-J Live Run Stop — P10-ISSUE-007

Status: **STOPPED — P10-ISSUE-007 DESIGN AMENDMENT REQUIRED**

Phase:
`P10 — Codex Dynamic Research Integration`

Gate:
`P10-J — Live P8/P9 Research Run`

Authorization:
`development/112-p10-j-live-run-authorization.md`

Authorization commit:
`17b6476`

## 1. Stop timing

The P10-J runtime spec had been frozen/read and P8 live queries had begun.

No P10 production/test/design code was changed.

No accepted P8/P9 source artifact was modified.

The run stopped before any P9 mutation and before any COMPLETE verdict.

## 2. Observed failure

A byte-for-byte copy of the existing CN live P9 review directory was placed under:

`workspace/research-runs/p10-j/review/<document_sha256>`

Accepted:

`load_resolved_snapshot(snapshot_dir, copied_review_dir)`

rejected the copied store with:

`review manifest differs from deterministic manifest`

## 3. Root cause

Accepted P9 review manifests are path-bound.

`review/queue.py::_expected_manifest(...)` persists:

`review_dir = review_dir.relative_to(project_root).as_posix()`

The source live review manifest contains:

`workspace/p9-live-review/<document_sha256>`

After copying the same bytes to:

`workspace/research-runs/p10-j/review/<document_sha256>`

the deterministic manifest expected for the new location differs from the copied manifest.

Therefore a P9 review directory is not a relocatable bundle.

This is an accepted P9 invariant, not a P9 defect.

## 4. Required correction

Do not weaken or bypass P9 validation.

For an isolated P10 live/acceptance review root:

1. call accepted `prepare_review_overlay` at the target isolated root;
2. inspect accepted tasks;
3. if the runtime research need requires review, submit only a supported, evidence-grounded resolution;
4. materialize via accepted P9 API;
5. use the newly generated isolated resolution/snapshot identity;
6. keep raw P8 facts unchanged;
7. do not force unrelated unresolved issues closed merely to make the run COMPLETE.

Existing P9 live state may be read as historical/reference evidence, but must not be copied/moved and treated as valid at another path.

## 5. Affected contract

Clarify:

- design/24 P9 live integration acceptance;
- design/25 P10-J;
- acceptance/38 controlled review fixture;
- P10-J authorization.

No P10 production change is required.

## 6. Gate boundary

Required sequence:

```text
STOP P10-J
→ amend design/24
→ amend design/25
→ amend acceptance/38
→ commit/push new design baseline
→ explicit P10-J reauthorization
→ rebuild isolated P9 review state through accepted P9 APIs
→ resume live run
```

P10-K and later remain closed.

Research MCP production, Semantic Resolver production, and P11 production remain closed.
