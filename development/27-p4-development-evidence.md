# 27 — P4 Development Evidence

状态：**P4 DEVELOPMENT COMPLETE / READY FOR CODE REVIEW**

Branch:
`task/p4-table-candidate-detection`

Initial design baseline:
`029c0e165866e87cae67e96273740ad727eb8eeb`

P4-ISSUE-001 design correction:
`df123c3a39ef5e77765d40e6cab22f40f93a439f`

Production commit:
`14476f645253a673e3ffaf187f2885f38404b0aa`

## 1. Implemented

- deterministic numeric-token classifier
- block-local table-like seed detector
- adjacent block grouping
- page-level distributed-block fallback
- financial keyword / section / drawing / TOC signals
- deterministic candidate score / ID / bbox
- content-addressed P4 artifact
- candidates.jsonl
- candidate_manifest.json
- artifact reuse / corruption guard

Not implemented:
- cells
- rows / columns reconstruction
- cross-page stitching
- facts/evidence
- PDF reopen
- OCR/Docling/network/AI

## 2. P4-ISSUE-001

Initial live HK run returned only 2 candidates.

Root cause:
P3 HK layout splits visual table values across many independent blocks; main statement pages had 50–70+ numeric tokens but individual numeric blocks often contained only one value.

Design-first correction:
- distributed-block page fallback
- no reconstruction semantics
- HK pages 124 / 126 / 133 live recall guard

After correction:
HK candidate_count = 97
pages 124 / 126 / 133 = all present.

## 3. Focused Tests

Result:
`23 passed in 0.24s`

Coverage includes:
- numeric formats
- keyword-only false positive
- drawing-only false positive
- TOC/single-year guard
- deterministic candidate IDs
- distributed-block fallback
- artifact reuse
- corrupt manifest/JSONL/count
- no PDF open
- P3 artifact immutability

## 4. Full Regression

Result:
`127 passed in 2.88s`

Includes P0–P4 tests.

## 5. CN Live

Source:
- 600519 FY2024
- SHA `5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30`

Result:
- candidate_count: 97
- dual-root candidates byte-identical: true
- runtime A: ~273 ms
- runtime B: ~279 ms
- immutability rerun: ~271 ms
- source/P3 artifacts unchanged: true

Representative table-like pages include 60–67 and later financial-note pages.

## 6. HK Live

Source:
- 00700 FY2024
- SHA `70f529984a87ef7f46d9e1db26bb9ef27eef9c01d29c59aabf69e557b479a6a0`

Result:
- candidate_count: 97
- dual-root candidates byte-identical: true
- runtime A: ~292 ms
- runtime B: ~313 ms
- immutability rerun: ~311 ms
- source/P3 artifacts unchanged: true

Recall guard:
- page 124 綜合收益表: PASS
- page 126 綜合財務狀況表: PASS
- page 133 綜合現金流量表: PASS

## 7. Performance

Gate:
- CN <= 5s
- HK <= 10s

Observed:
- CN < 0.3s
- HK < 0.4s

PASS.

## 8. Static Scope

P4 candidate package:
- no pymupdf.open
- no Dayu
- no Docling
- no network SDK/path
- no Torch
- no external AI
- no reconstructed cells/rows/columns

PASS.

## 9. Development Gate

P4-B Models / signals: PASS
P4-C Region detector: PASS
P4-D Artifact persistence: PASS
P4-E Determinism/regression: PASS
P4-F Live CN/HK: PASS

Next:
**P4-G isolated Code Review**
