# 19 — P5 Independent Acceptance Run Instruction

状态：**P5 ACCEPTANCE FREEZE**

Phase: `P5 — Table Reconstruction / Cross-page`

Accepted baseline before P5:
`97f2de24861347c97bf875e7b72899eb11ab56c2`

Reviewed production/development candidate:
`2c4bafd36b59defd4ff47eeb16713cbee64e739e`

Code Review:
- verdict: PASS
- evidence: `development/33-p5-code-review.md`
- review commit: `a529a792b1a7073d185a09aad1feedbe4115c5fa`

The acceptance candidate is the Git commit containing this file.

Independent Acceptance must:
- use a fresh detached worktree at the frozen SHA;
- keep HEAD stable;
- not modify production/tests/design/config/dependencies;
- run the full unit/regression suite;
- verify P0–P4 source/tests zero diff from accepted P4 baseline;
- rerun CN/HK live reconstruction from accepted P3/P4 artifacts;
- verify dual-root byte identity;
- verify input/raw immutability;
- verify semantic tamper rejection;
- verify no PDF open/OCR/Docling/network/AI;
- verify no P6 raw fact/account semantic implementation.

Expected current full suite:
`156 passed`

Live expectations:

CN 600519 FY2024:
- table_count 97
- group_count 4
- pages 60–67 reconstructed
- <=10s

HK 00700 FY2024:
- table_count 97
- group_count 18
- page 124 >=5 rows and >=2 value columns
- page 126 >=5 rows and >=2 value columns
- page 133 >=5 rows and >=2 value columns
- <=20s

Final verdict: PASS / FAIL / BLOCKED.

P6 implementation must not start during P5 acceptance.
