# 18 — P5 Independent Acceptance Instruction

状态：**DESIGN BASELINE — P5 ACCEPTANCE**

最终 verdict：
PASS / FAIL / BLOCKED。

验收不得修改 production/tests/design/config。

## 必验

1. exact frozen candidate / stable HEAD；
2. P0–P4 regression PASS；
3. prior source/tests zero semantic change；
4. P3 + P4 input fingerprint exact；
5. candidate-scoped words only；
6. visual row clustering deterministic；
7. numeric value anchors deterministic；
8. row/table/cell IDs stable；
9. source word refs valid；
10. no source word outside candidate page/block/bbox scope；
11. LABEL / VALUE / UNASSIGNED only；
12. no P6 accounting semantics；
13. continuation only adjacent pages；
14. anchor compatibility required；
15. bottom/top continuity required；
16. incompatible/non-adjacent fragments not grouped；
17. tables.jsonl dual-root byte-identical；
18. table_groups.jsonl dual-root byte-identical；
19. input fingerprint mismatch blocked；
20. tampered table/row/cell/group identity blocked；
21. tampered derived reconstruction fields（anchors、cell text/bbox/numeric、quality signals、group score/signals）必须通过 full recomputation semantic equality 被检出；
22. CN live structure guards PASS；
23. HK pages 124 / 126 / 133 structure guards PASS；
24. at least one valid continuation group across live CN/HK, unless a design-first evidence update formally changes this expectation；
25. CN <=10s；
26. HK <=20s；
27. raw PDF / P3 / P4 artifacts unchanged；
28. no PDF reopen；
29. no OCR/Docling/Dayu/network/AI；
30. no P6 raw fact/evidence implementation。

P5 PASS 后才允许 P6。
