# 32 — P9 Independent Acceptance Instruction

状态：**DESIGN BASELINE — P9 ACCEPTANCE**

最终 verdict：
`PASS / FAIL / BLOCKED`

## Mandatory

1. frozen candidate HEAD stable
2. P0–P8 prior accepted source/tests zero unintended diff
3. full P0–P9 suite PASS
4. review manifest/input fingerprints valid
5. P7 PASS -> empty queue
6. P7 REVIEW_REQUIRED -> one task per REVIEW issue
7. WARNING/INFO do not become tasks
8. FAIL/BLOCKED cannot be dismissed by P9
9. task IDs deterministic
10. supported/unsupported reason mapping correct
11. reviewer metadata validated
12. reviewed_at timezone-aware and caller supplied
13. resolution ID deterministic
14. resolution JSON immutable / idempotent
15. P5 cell evidence resolves
16. P6 evidence resolves
17. evidence pages derived, not trusted blindly
18. target/evidence relationship validated
19. raw non-null fields never overwritten
20. raw_value / parsed_numeric_value unchanged
21. raw_metric_name unchanged
22. no-op resolution rejected
23. conflicting raw patch rejected
24. supersession graph valid
25. unknown/cycle/competing child errors
26. overlapping same value deterministic
27. overlapping different value conflict
28. zero-overlay snapshot deterministic
29. overlay_set_hash deterministic
30. resolved_facts preserve every raw field
31. effective period/unit/scope only from explicit overlay
32. statement classification remains overlay-only
33. period coverage uses P7 PERIOD_REVIEW
34. unit coverage uses P7 UNIT_REVIEW
35. ambiguity requires explicit attestation
36. core statement review augments, never rewrites, base signals
37. unsupported issue stays unresolved
38. resolved validation priority correct
39. resolved_reuse_eligible only when resolved PASS / compatible
40. resolved ParsedDataRecord helper deterministic
41. no implicit Registry write
42. snapshot semantic recomputation/tamper guard
43. base catalog/P3/P5/P6/P7 immutable
44. no source PDF open
45. no network/AI/Codex API
46. no external MCP SDK requirement
47. no P8 tool mutation
48. no P10/P11 implementation
49. local CLI JSON stdout only
50. performance gates

## Synthetic golden

必须独立证明：

- base status REVIEW_REQUIRED；
- supported period/unit/core-statement review tasks；
- evidence-grounded resolutions；
- materialized resolved view；
- all base REVIEW issues resolved；
- resolved_validation_status=PASS；
- resolved_reuse_eligible=true；
- resolved ParsedDataRecord generated；
- raw source data unchanged。

## Live CN

600519 FY2024：

- base REVIEW queue count = 1
- exact reason = RAW_PERIOD_COVERAGE_LOW
- submit at least one verified P5/P6-evidence-grounded SET_PERIOD resolution
- at least one raw-null period fact gets effective_period_label
- raw_period_label remains null on that fact
- if effective coverage remains <0.10, final status must remain REVIEW_REQUIRED
- no guessed mass fill

## Live HK

00700 FY2024：

- base REVIEW queue count = 4
- exact reason set:
  - CORE_STATEMENT_COVERAGE_LOW
  - RAW_PERIOD_COVERAGE_LOW
  - RAW_UNIT_AMBIGUOUS
  - RAW_UNIT_COVERAGE_LOW
- no forced issue dismissal
- unsupported/unresolved logic remains honest

## Immutability

Before/after P9 live operations snapshot:

- P8 catalog
- P3
- P5
- P6
- P7

For all:
- SHA256
- size
- mtime_ns

Must be identical.

Only review_root may change.

## Acceptance prohibition

Acceptance executor不得修改：

- production
- tests
- design
- accepted catalog
- runtime/dependencies
- P3/P5/P6/P7/P8 artifacts

P9 PASS 后才允许 P10 Codex Skill design。
