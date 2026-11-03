# 22 — P6 Independent Acceptance Run Instruction

状态：**P6 ACCEPTANCE FREEZE**

Phase:
`P6 — Raw Facts / Evidence`

Accepted baseline before P6:
`8ff01cd3feed41c4b81aff88bce6502d50e8f32e`

Reviewed candidate:
`bb31515b4fc6ac09aea0aed0cf14262555a7398e`

Final hardened production commit:
`11fce802f146b2d8ed064dbe63ec3c81d918be21`

Code Review:
- verdict: PASS
- evidence: `development/37-p6-code-review.md`
- review commit: `714d774e2f65eed650b2a1ccb9bb387b3177545b`

The acceptance candidate is the Git commit containing this freeze file.

## Frozen Live Inputs

Project-root fresh P3/P4/P5 inputs:
`D:\Codex\FinancialFilingDataFoundation\workspace\live\p6-inputs`

CN raw identity:
- ticker: 600519
- period: FY2024
- document SHA: `5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30`

HK raw identity:
- ticker: 00700
- period: FY2024
- document SHA: `70f529984a87ef7f46d9e1db26bb9ef27eef9c01d29c59aabf69e557b479a6a0`

Fresh P3/P4/P5 deterministic artifacts were proven equivalent to accepted historical P5 evidence.

## Expected Deterministic Suite

`189 passed`

## Expected Live CN

- fact_count: 2177
- evidence_count: 2177
- tables_with_facts: 80
- pages 60–67 each have facts
- facts SHA: `30b9845ecb8b0b9216a6f3fefdd640b9f63fe24fb71984cf1cb44ae0f39cb2c3`
- evidence SHA: `17d127ba1b37b7f39a1d9dae8336016261cb6b6ec7ac95ed70e97f3b519e39d2`
- dual-root byte identity: PASS
- input immutability: PASS
- runtime <=10s

## Expected Live HK

- fact_count: 2989
- evidence_count: 2989
- tables_with_facts: 86
- page 124: 49 facts
- page 126: 69 facts
- page 133: 52 facts
- facts SHA: `a35142503ed53eeb57c441d6b69e4ce73e6990f2282d436b0cf20636c2222340`
- evidence SHA: `1bbf8bdd55a78663419ecffbe1471cb59862426bf70ba2831c6444246da79573`
- dual-root byte identity: PASS
- input immutability: PASS
- runtime <=15s

## Independent Acceptance Must Verify

1. fresh detached worktree under project root
2. frozen HEAD stable before/after every major group
3. full P0–P6 suite PASS
4. P0–P5 source/tests zero unintended diff
5. Decimal numeric truth
6. period-header suppression
7. no bare 公司/company scope guessing
8. longest/non-overlapping unit/scope rules
9. one evidence per fact
10. source refs resolve to current P3 words
11. stable fact/evidence IDs
12. fingerprints
13. semantic recomputation tamper guard
14. raw PDF/P3/P4/P5 immutable
15. no source PDF open
16. no OCR/Docling/Dayu/network/AI
17. no canonical metrics / P7 DATA_READY logic
18. live CN exact counts/SHA
19. live HK exact counts/SHA
20. dual-root byte identity
21. performance gates

Acceptance must not modify:
- production code
- tests
- design
- config
- dependencies

Final verdict:
`PASS / FAIL / BLOCKED`

P7 implementation must not begin during P6 acceptance.
