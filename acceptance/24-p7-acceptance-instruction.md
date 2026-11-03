# 24 — P7 Independent Acceptance Instruction

状态：**DESIGN BASELINE — P7 ACCEPTANCE**

最终 verdict：
PASS / FAIL / BLOCKED

## Mandatory

1. exact frozen candidate / stable HEAD
2. P0–P6 regression PASS
3. prior accepted source/tests zero unintended diff
4. P3/P5/P6 identity validation
5. page sequence gate
6. fact/evidence 1:1 gate
7. evidence reference validation
8. no-facts deterministic failure
9. P6 warning mapping
10. period/unit/scope coverage policy
11. table-without-facts policy
12. core statement signal
13. balance reconciliation PASS case
14. balance reconciliation FAIL case
15. reconciliation SKIP when context ambiguous
16. cash reconciliation rules
17. duplicate/conflict rules
18. status priority correct
19. compatibility status correct
20. reuse_eligible only when PASS + compatible + zero blocking
21. deterministic issue IDs
22. deterministic parse_run_id
23. ParsedDataRecord mapping
24. planner REUSE_DATA only from reusable PASS record
25. review/fail/blocked not reusable
26. fingerprints
27. semantic recomputation
28. report tamper blocked
29. issue tamper blocked
30. raw PDF/P3/P4/P5/P6 immutable
31. no PDF open
32. no OCR/Docling/Dayu/network/AI
33. no canonical metric output
34. CN live deterministic
35. HK live deterministic
36. dual-root issues byte-identical
37. CN <=10s
38. HK <=15s

Live status does not have to be PASS.
Acceptance verifies deterministic correctness of the status/reasons.

验收不得修改：
- production code
- tests
- design
- config
- dependencies

P7 PASS 后才允许 P8 Local MCP。
