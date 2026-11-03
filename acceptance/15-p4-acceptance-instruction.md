# 15 — P4 Independent Acceptance Instruction

状态：**DESIGN BASELINE — P4 ACCEPTANCE**

最终 verdict：PASS / FAIL / BLOCKED。

必须验证：
1. exact frozen candidate / stable HEAD；
2. P0–P3 regression PASS；
3. P3 source/tests semantics unchanged；
4. candidate detector does not open source PDF；
5. no OCR/Docling/Dayu/network/AI；
6. numeric/token/table-like signals deterministic；
7. financial keyword alone does not trigger；
8. drawing alone does not trigger；
9. TOC-like guard；
10. candidate IDs deterministic；
11. candidates JSONL UTF-8 no BOM / line-safe；
12. artifact reuse validation；
13. corrupt manifest / JSONL / count mismatch blocked；
14. CN 600519 FY2024 candidate_count > 0；
15. HK 00700 FY2024 candidate_count > 0；
16. dual-root byte-identical candidates；
17. CN <=5s；
18. HK <=10s；
19. P3 artifacts and raw PDFs unchanged；
20. no reconstructed cell/table objects。

验收不得修改 production/tests/design/config。

P4 PASS 后才允许 P5。
