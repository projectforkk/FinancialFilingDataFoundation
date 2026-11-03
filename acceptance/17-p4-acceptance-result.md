# 17 — P4 Independent Acceptance Result

状态：**PASS**

Phase:
`P4 — Table Candidate Detection`

Frozen candidate:
`647d6179bdde9e370185fea1d389f0087370faae`

Reviewed candidate:
`ea78b2f9adbf0ad6564146ba166da85d1085bf81`

Accepted baseline before P4:
`24cb4571a9d9f97b4b963d6339970c931d979c4d`

## 1. Verdict

# PASS

## 2. Isolation

Acceptance worktree:
`D:\Codex\FinancialFilingDataFoundation-P4Acceptance-647d617`

Frozen HEAD before/after critical groups:
`647d6179bdde9e370185fea1d389f0087370faae`

Tracked worktree clean.

## 3. Full Regression

`133 passed in 3.18s`

P0–P3 source/tests versus accepted P3 baseline:
zero diff.

PASS.

## 4. Scope / Runtime

Static scope:
- no P4 PDF open
- no OCR
- no Dayu
- no Docling
- no network
- no Torch
- no external AI
- no cell/row/column reconstruction
- no cross-page table stitching

PASS.

## 5. CN Live Acceptance

Input:
600519 FY2024 P3 accepted artifact.

Results:
- candidate_count: 97
- run A: 276.327 ms
- run B: 285.949 ms
- dual-root candidates.jsonl byte-identical
- UTF-8 no BOM
- raw PDF unchanged
- P3 artifact files unchanged

Performance <=5s: PASS.

## 6. HK Live Acceptance

Input:
00700 FY2024 P3 accepted artifact.

Results:
- candidate_count: 97
- run A: 297.517 ms
- run B: 308.651 ms
- dual-root candidates.jsonl byte-identical
- UTF-8 no BOM
- raw PDF unchanged
- P3 artifact files unchanged

Recall guard:
- page 124: PASS
- page 126: PASS
- page 133: PASS

Performance <=10s: PASS.

## 7. P4-ISSUE Closure

P4-ISSUE-001 distributed-block layout:
PASS.

P4-ISSUE-002 candidate artifact identity integrity:
PASS.

Full test suite independently covers tampered:
- page
- bbox
- block_nos
- candidate_id
- manifest
- JSONL
- candidate count

## 8. Determinism

- stable candidate IDs
- stable candidate ordering
- dual-root candidates byte-identical
- valid artifact reuse
- corrupt artifact blocked

PASS.

## 9. Source Immutability

Acceptance snapshot compared:
- raw PDF SHA/size/mtime
- P3 document.json
- pages.jsonl
- sections.jsonl
- search.sqlite

Before == after for CN/HK.

PASS.

## 10. Final Summary

- exact frozen candidate: PASS
- HEAD stability: PASS
- full suite: 133 PASS
- P0–P3 regression: PASS
- candidate signals: PASS
- distributed-block fallback: PASS
- artifact identity guard: PASS
- live CN: PASS
- live HK: PASS
- recall guard: PASS
- determinism: PASS
- performance: PASS
- source immutability: PASS
- no reconstruction: PASS
- blocker: NONE

Final verdict:

# PASS

P4 may proceed to closeout.

P5 implementation has not started.
