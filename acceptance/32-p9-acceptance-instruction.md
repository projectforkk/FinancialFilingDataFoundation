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
26. base_active_resolution_ids are store-computed and historical before state is recomputable
27. base_overlay_set_hash_before deterministic and tamper-checked
28. supersession graph valid
29. unknown/cycle/competing child errors
30. overlapping same value deterministic
31. overlapping different value conflict
32. zero-overlay snapshot deterministic
33. overlay_set_hash deterministic
34. resolved_facts preserve every raw field
35. effective period/unit/scope only from explicit overlay
36. statement classification remains overlay-only
37. period coverage uses P7 PERIOD_REVIEW
38. unit coverage uses P7 UNIT_REVIEW
39. ambiguity requires explicit attestation
40. core statement review augments, never rewrites, base signals
41. unsupported issue stays unresolved
42. resolved validation priority correct
43. resolved_reuse_eligible only when resolved PASS / compatible
44. resolved ParsedDataRecord helper deterministic
45. no implicit Registry write
46. snapshot semantic recomputation/tamper guard
47. base catalog/P3/P5/P6/P7 immutable
48. no source PDF open
49. no network/AI/Codex API
50. no external MCP SDK requirement
51. no P8 tool mutation
52. no P10/P11 implementation
53. local CLI deterministic JSON contract：success = exit 0 / stdout exactly one JSON / stderr empty；handled runtime failure = stdout empty / stderr exactly one JSON / exit 1；parser-level failure = stdout empty / stderr exactly one JSON / exit 2 / reason_code `P9_CLI_ARGUMENT_ERROR` / message `invalid command line arguments`；必须直接覆盖 no subcommand、unknown subcommand、missing required argument、`--input-json` + `--input-file` conflict
54. performance gates
55. resolution payload security invariant：完整 provisional persisted payload 在 resolution_id hash/persist 前执行 deterministic recursive string-leaf validation；URL/path/shell/SQL/Python/credential adversarial payload全部拒绝为 `P9_RESOLUTION_CONTENT_FORBIDDEN`；historical re-load/semantic validation同样执行；错误不得回显 offending secret/content；benign `2024/2025`、`P5/P6 evidence`、自然语言 keyword 不误拒

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

P9 PASS 后才允许 P10 Codex Dynamic Research Integration design。
