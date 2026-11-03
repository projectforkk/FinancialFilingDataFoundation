# 32 — P5 Development Amendment — Semantic Reconstruction Integrity

状态：**P5-G / H / I REVALIDATED**

Issue:
`P5-ISSUE-001 — Derived reconstruction integrity`

Design correction:
`052e4a2d176025bfc0c047dd97cd1386ba8c1c56`

Production fix:
`434d57fc5d6bb88d2075000a069f14df1e161fcb`

## Review finding

The initial loader recomputed IDs and validated source refs, but a Code Review tamper probe proved that changing persisted `value_column_anchors` could still be accepted.

Root cause:
IDs did not cover every deterministic derived field.

## Final fix

On every load/reuse, P5 now:
1. validates current P3/P4 fingerprints;
2. loads current candidates/pages;
3. recomputes every expected table fragment;
4. recomputes continuation groups;
5. requires exact semantic equality with persisted tables/groups.

This covers:
- value anchors/count
- row count/bbox/signals
- cell role/text/bbox/numeric/source refs
- quality signals
- group membership/order/score/signals

## Tests after fix

Focused:
`23 passed in 0.49s`

Full P0–P5:
`156 passed in 3.83s`

Added derived tamper tests:
- value anchors
- cell text
- cell bbox
- cell numeric flag
- table quality signals
- group score
- group continuation signals

## Live after fix

CN:
- 97 fragments
- 4 groups
- 755.534 / 746.765 ms
- dual-root tables/groups byte-identical

HK:
- 97 fragments
- 18 groups
- 811.548 / 1299.753 ms
- dual-root tables/groups byte-identical
- page 124 = 24 rows / 3 value columns
- page 126 = 27 rows / 3 value columns
- page 133 = 27 rows / 2 value columns

All performance gates remain PASS.

## Gate impact

- P5-G Artifact Persistence / Reuse: PASS
- P5-H Determinism / Full Regression: PASS
- P5-I Live CN/HK: PASS
- prior P5-J review: INVALIDATED
- P5-J must rerun from a new frozen candidate
