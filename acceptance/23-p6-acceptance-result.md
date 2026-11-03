# 23 — P6 Independent Acceptance Result

状态：**PASS**

Phase:
`P6 — Raw Facts / Evidence`

Frozen acceptance candidate:
`07cb4258e1f2083b7c930686b637acdd89b03d0a`

Reviewed candidate:
`bb31515b4fc6ac09aea0aed0cf14262555a7398e`

Final production commit:
`11fce802f146b2d8ed064dbe63ec3c81d918be21`

Accepted baseline before P6:
`8ff01cd3feed41c4b81aff88bce6502d50e8f32e`

## Verdict

# PASS

## Isolation

Acceptance worktree:
`D:\Codex\FinancialFilingDataFoundation\worktrees\acceptance\p6-07cb425`

Frozen HEAD before/after:
`07cb4258e1f2083b7c930686b637acdd89b03d0a`

Tracked worktree remained clean.

## Full Regression

`189 passed in 3.93s`

P0–P5 source/tests versus accepted P5 baseline:
zero diff.

compileall / diff-check / static scope:
PASS.

## Scope Boundary

Confirmed no:
- source PDF open
- PyMuPDF use in P6 facts package
- OCR
- Dayu
- Docling
- Torch
- network
- external AI
- canonical metric mapping
- DATA_READY / P7 policy

PASS.

## Raw Fact Semantics

Verified:
- Decimal numeric truth
- source-preserving raw metric/value
- one fact per eligible VALUE cell
- period-header suppression
- explicit-only raw period/unit/scope
- no bare 公司/company scope guessing
- longest/non-overlapping unit matching
- longest/non-overlapping scope matching

PASS.

## Evidence

Verified:
- evidence_count == fact_count
- one evidence row per fact
- stable fact/evidence IDs
- label/value cell references
- P3 source-word refs
- bbox/source identity
- deterministic order
- invalid source ref blocking

PASS.

## Integrity / Reuse

Verified:
- input fingerprints
- valid reuse
- fact tamper blocking
- evidence tamper blocking
- semantic recomputation equality
- P3/P5 immutability

PASS.

## Live CN — 600519 FY2024

- fact_count: 2177
- evidence_count: 2177
- tables_with_facts: 80
- page 60: 51
- page 61: 34
- page 62: 42
- page 63: 41
- page 64: 8
- page 65: 28
- page 66: 6
- page 67: 31
- timings: 1822.062 / 2690.871 ms
- facts dual-root byte-identical: PASS
- evidence dual-root byte-identical: PASS
- inputs immutable: PASS
- facts SHA: `30b9845ecb8b0b9216a6f3fefdd640b9f63fe24fb71984cf1cb44ae0f39cb2c3`
- evidence SHA: `17d127ba1b37b7f39a1d9dae8336016261cb6b6ec7ac95ed70e97f3b519e39d2`
- performance <=10s: PASS

## Live HK — 00700 FY2024

- fact_count: 2989
- evidence_count: 2989
- tables_with_facts: 86
- page 124: 49
- page 126: 69
- page 133: 52
- timings: 3359.045 / 3119.764 ms
- facts dual-root byte-identical: PASS
- evidence dual-root byte-identical: PASS
- inputs immutable: PASS
- facts SHA: `a35142503ed53eeb57c441d6b69e4ce73e6990f2282d436b0cf20636c2222340`
- evidence SHA: `1bbf8bdd55a78663419ecffbe1471cb59862426bf70ba2831c6444246da79573`
- performance <=15s: PASS

## Design Issues

Independently verified closed:
- P6-ISSUE-001
- P6-ISSUE-002
- P6-ISSUE-003
- P6-ISSUE-004
- P6-ISSUE-005

## Final Summary

- frozen candidate: PASS
- HEAD stability: PASS
- full regression: PASS
- prior-phase integrity: PASS
- fact semantics: PASS
- evidence provenance: PASS
- determinism: PASS
- tamper guard: PASS
- live CN/HK: PASS
- source/input immutability: PASS
- performance: PASS
- blocker: NONE

Final verdict:

# PASS

P6 may proceed to closeout.

P7 implementation has not started during this acceptance.
