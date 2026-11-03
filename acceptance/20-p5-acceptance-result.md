# 20 — P5 Independent Acceptance Result

状态：**PASS**

Phase: `P5 — Table Reconstruction / Cross-page`

Frozen candidate:
`44ddd73d736f1da64bab38641091a8c6d55c9990`

Reviewed candidate:
`2c4bafd36b59defd4ff47eeb16713cbee64e739e`

Accepted baseline before P5:
`97f2de24861347c97bf875e7b72899eb11ab56c2`

## Verdict

# PASS

## Isolation

Acceptance worktree:
`D:\Codex\FinancialFilingDataFoundation-P5Acceptance-44ddd73`

Frozen HEAD remained:
`44ddd73d736f1da64bab38641091a8c6d55c9990`

Tracked worktree remained clean.

## Full Regression

`156 passed in 3.89s`

P0–P4 source/tests versus accepted P4 baseline:
zero diff.

## Live CN

600519 FY2024:
- table_count: 97
- group_count: 4
- runtime A/B: 847.303 / 827.070 ms
- dual-root tables byte-identical
- dual-root groups byte-identical
- pages 60–67 reconstructed
- performance <=10s PASS

## Live HK

00700 FY2024:
- table_count: 97
- group_count: 18
- runtime A/B: 923.005 / 1461.939 ms
- dual-root tables byte-identical
- dual-root groups byte-identical
- page 124: 24 rows / 3 value columns
- page 126: 27 rows / 3 value columns
- page 133: 27 rows / 2 value columns
- performance <=20s PASS

## Semantic Integrity

P5-ISSUE-001 independently verified closed.

Loader/reuse recomputes deterministic tables/groups from current P3/P4 input and requires exact semantic equality.

Tamper coverage includes:
- value anchors
- cell text/bbox/numeric
- table quality signals
- group score/signals
- nested IDs/group members

PASS.

## Immutability

Independent snapshots verified unchanged for both CN/HK:
- raw PDF
- P3 document.json/pages.jsonl/sections.jsonl/search.sqlite
- P4 candidate_manifest.json/candidates.jsonl

PASS.

## Scope

No:
- source PDF open
- OCR
- Dayu
- Docling
- network
- Torch
- external AI
- P6 raw facts/account semantic extraction

PASS.

## Final Summary

- exact frozen candidate: PASS
- HEAD stability: PASS
- full suite: 156 PASS
- prior-phase integrity: PASS
- live CN/HK: PASS
- continuation groups: PASS
- semantic integrity: PASS
- determinism: PASS
- source immutability: PASS
- performance: PASS
- scope boundary: PASS
- blocker: NONE

Final verdict:

# PASS

P5 may proceed to closeout.

P6 implementation has not started during this acceptance.
