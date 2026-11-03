# 28 — P4 Development Amendment — Candidate Artifact Identity

状态：**P4-D / E REVALIDATED**

Issue:
`P4-ISSUE-002 — Candidate artifact identity integrity`

Design correction:
`bdf6f5a06fdb7277edf94b4fa87f26fa3e240d2e`

Production fix:
`ec256e44517e5206555f35ac9b056711d6f968f9`

## Finding

Initial loader validated candidate_id presence/uniqueness but did not recompute it from candidate identity fields. A tampered JSONL row could retain the old ID.

## Fix

Loader now validates:
- manifest page_count
- 1 <= page_no <= page_count
- finite ordered normalized bbox
- non-empty sorted unique integer block_nos
- document SHA
- candidate ID uniqueness
- candidate ID recomputed from document/page/bbox/block_nos

## Tests after fix

Focused:
`29 passed in 0.29s`

Full P0–P4:
`133 passed in 3.04s`

Added tamper cases:
- out-of-range page
- changed bbox
- unordered bbox
- noncanonical block_nos
- empty block_nos
- forged candidate_id

## Live regression

CN:
- 97 candidates
- dual-root byte-identical

HK:
- 97 candidates
- dual-root byte-identical
- pages 124 / 126 / 133 present

Detector scoring/output semantics unchanged.

## Gate impact

- P4-D Artifact Persistence: PASS
- P4-E Determinism / Regression: PASS
- prior P4-G review evidence: invalidated
- P4-G must rerun from new frozen candidate
