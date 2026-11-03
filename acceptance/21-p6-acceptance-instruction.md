# 21 — P6 Independent Acceptance Instruction

状态：**DESIGN BASELINE — P6 ACCEPTANCE**

最终 verdict：PASS / FAIL / BLOCKED。

## Mandatory

1. exact frozen candidate / stable HEAD
2. P0–P5 full regression PASS
3. prior accepted source/tests zero unintended diff
4. numeric parsing uses Decimal, no float value truth
5. raw_metric/raw_value preserve source text
6. multi-value row → one fact per value
7. no-label row not guessed
8. period/unit/scope only explicit deterministic evidence
9. one evidence per fact
10. evidence source refs resolve to current P3 words
11. evidence bbox/source refs valid
12. stable fact/evidence IDs
13. input fingerprints
14. artifact reuse
15. fact tamper blocked
16. evidence tamper blocked
17. complete semantic recomputation equality
18. raw PDF/P3/P4/P5 immutable
19. no PDF open
20. no OCR/Docling/Dayu/network/AI
21. no canonical metric / P7 logic
22. CN live PASS
23. HK live PASS
24. dual-root byte identity
25. CN <=10s
26. HK <=15s

Live minimum:

CN 600519 FY2024:
- fact_count > 0
- evidence_count == fact_count
- pages 60–67 total facts >=20

HK 00700 FY2024:
- fact_count > 0
- evidence_count == fact_count
- pages 124/126/133 each facts >=5

period/unit/scope may be null; if present must be source-grounded.

验收不得修改 production/tests/design/config/dependencies。

P6 PASS 后才允许 P7。
