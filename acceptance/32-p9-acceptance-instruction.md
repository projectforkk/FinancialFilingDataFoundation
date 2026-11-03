# 32 — P9 Independent Acceptance Instruction

状态：**DESIGN BASELINE — P9 ACCEPTANCE**

最终 verdict：
`PASS / FAIL / BLOCKED`

## Mandatory

1. frozen candidate HEAD stable
2. accepted P8 baseline = `ee934ad05812c69b79f76db43e62cfd4050efb8e` / `acceptance/33-p8-issue006-acceptance-result.md`
3. P0–P8 prior accepted source/tests zero unintended diff
4. full P0–P9 suite PASS
5. review manifest/input fingerprints valid
6. P7 PASS -> empty queue
7. P7 REVIEW_REQUIRED -> one task per REVIEW issue
8. WARNING/INFO do not become tasks
9. FAIL/BLOCKED cannot be dismissed by P9
10. task IDs deterministic
11. supported/unsupported reason mapping correct
12. reviewer metadata validated
13. reviewed_at timezone-aware and caller supplied
14. resolution ID deterministic
15. resolution JSON immutable / idempotent
16. P5 cell evidence resolves
17. P6 evidence resolves
18. evidence pages derived, not trusted blindly
19. attestation caller direct evidence is rejected/omitted; persisted attestation inherits union of active supporting-resolution evidence
20. target/evidence relationship validated
21. raw non-null fields never overwritten
22. raw_value / parsed_numeric_value unchanged
23. raw_metric_name unchanged
24. no-op resolution rejected
25. conflicting raw patch rejected
26. supersession graph valid
27. unknown/cycle/competing child errors
28. overlapping same value deterministic
29. overlapping different value conflict
30. zero-overlay snapshot deterministic
31. overlay_set_hash deterministic
32. resolved_facts preserve every raw field
33. effective period/unit/scope only from explicit overlay
34. statement classification remains overlay-only
35. period coverage uses P7 PERIOD_REVIEW
36. unit coverage uses P7 UNIT_REVIEW
37. ambiguity requires explicit attestation
38. core statement review augments, never rewrites, base signals
39. unsupported issue stays unresolved
40. resolved validation priority correct
41. resolved_reuse_eligible only when resolved PASS / compatible
42. resolved ParsedDataRecord helper deterministic
43. no implicit Registry write
44. snapshot semantic recomputation/tamper guard
45. base catalog/P3/P5/P6/P7 immutable
46. no source PDF open
47. no network/AI/Codex API
48. no external MCP SDK requirement
49. no P8 tool mutation
50. no P10/P11 implementation
51. local CLI JSON stdout only
52. performance gates

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
