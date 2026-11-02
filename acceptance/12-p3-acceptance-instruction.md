# 12 — P3 Independent Acceptance Instruction

Final verdict: PASS / FAIL / BLOCKED.

Acceptance must use an exact frozen detached candidate and may not modify production/tests/design/dependencies.

Verify:
1. full P0-P3 unit suite PASS
2. P0-P2 source/tests unchanged
3. no OCR/Docling/Torch/Dayu dependency in P3
4. source PDF unchanged
5. all pages enumerated exactly once, 1-based
6. words/blocks/spans/bbox available；native DICT path 不保留 image binary payload；image-only page 仍明确 PAGE_TEXT_EMPTY
7. deterministic reading order
8. repeated headers/footers not section headings
9. section hierarchy/page ranges valid
10. section IDs deterministic
11. pages/sections JSONL UTF-8 no BOM；record separator 仅 ASCII LF；U+0085/U+2028/U+2029 必须在 string 内转义，不得形成伪记录边界
12. FTS5 page/section search PASS；`page_fts` 必须使用 `page_content` external-content contract，不能重复保存 canonical page text
13. repeated parse semantic artifacts deterministic excluding timings/paths as frozen
14. CN 600519 FY2024 live PASS <=30s
15. HK 00700 FY2024 live PASS <=30s
16. no table reconstruction/parser scope beyond P3

If FTS5/runtime/live source is externally unavailable, BLOCKED only when product correctness cannot be judged.
