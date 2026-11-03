# 31 — P5 Development Evidence

状态：**P5 DEVELOPMENT COMPLETE / READY FOR CODE REVIEW**

Branch:
`task/p5-table-reconstruction`

Design baseline:
`aed9af6ac08df14b227fdb2bc39ab26595744fa0`

Production commit:
`619cfb1a6dfa4980350e354fdf26bd4ae2a862ff`

## Implemented

- candidate-scoped P3 word selection
- y-center visual row clustering
- numeric x1 value-anchor clustering
- structural LABEL / VALUE / UNASSIGNED cells
- cell bbox/text/source-word refs
- deterministic table/row/cell IDs
- table quality signals
- adjacent-page continuation groups
- deterministic group chains/IDs
- P3/P4 input fingerprints
- tables.jsonl / table_groups.jsonl / table_manifest.json
- artifact reuse and corruption validation

Not implemented:
- raw financial facts
- account normalization
- period/currency/unit semantics
- P6 evidence objects
- OCR/Docling/network/AI

## Focused Tests

`16 passed in 0.37s`

## Full Regression

`149 passed in 3.70s`

## CN Live

600519 FY2024:
- table_count: 97
- group_count: 4
- runtime A: 646.969 ms
- runtime B: 618.995 ms
- dual-root tables byte-identical
- dual-root groups byte-identical

Pages 60–67:
- all contain reconstructed fragments
- representative value-column counts: 2–4
- representative row counts: 3–49

Performance <=10s: PASS.

## HK Live

00700 FY2024:
- table_count: 97
- group_count: 18
- runtime A: 667.249 ms
- runtime B: 682.468 ms
- dual-root tables byte-identical
- dual-root groups byte-identical

Recall/structure:
- page 124: 24 rows / 3 value columns
- page 126: 27 rows / 3 value columns
- page 133: 27 rows / 2 value columns

Performance <=20s: PASS.

## Continuation

Real live groups exist in both documents.

CN examples:
- 63→64
- 65→66
- 67→68
- 110→111

HK includes multiple adjacent chains, including:
- 126→128 as a 3-page chain (126/127/128)
- 133→134
- other note/report chains

Strong continuation conditions therefore hold in real data; no design relaxation was required.

## Immutability

Independent development snapshot:
- CN P3/P4/raw input unchanged
- HK P3/P4/raw input unchanged

PASS.

## Determinism

- dual-root tables byte-identical
- dual-root groups byte-identical
- stable IDs
- deterministic ordering

PASS.

## Static Scope

P5 tables package contains no:
- source PDF open
- OCR
- Dayu
- Docling
- network
- Torch
- external AI
- raw/financial fact implementation

PASS.

## Development Gates

- P5-B Models/Fingerprints: PASS
- P5-C Rows: PASS
- P5-D Cells/Anchors: PASS
- P5-E Distributed: PASS
- P5-F Continuation: PASS
- P5-G Artifact: PASS
- P5-H Regression: PASS
- P5-I Live: PASS

Next:
**P5-J isolated Code Review**
