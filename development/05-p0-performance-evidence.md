# 05 — P0 Representative Performance Evidence

状态：**P0-G / P0-H / P0-I COMPLETE**

Branch: `task/p0-native-pdf-feasibility`

Development commit: `f5fb270c2b46db390c7d774c741a96c0490f9ec9`

Design baseline: `10e5abd18d84a821891175e8e2b823809092d7ad`

---

## 1. P0-G Representative Sample

- company: `600519` 贵州茅台
- filing: FY2024 annual report
- source: `D:\Codex\FIReport\crde-dayu-workspaces\p1-08-fixture-capture\cn_600519_fy.pdf`
- file size: `3,626,217 bytes`
- page count: `143`
- SHA256: `5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30`
- LastWriteTime: `2026-11-02 22:08:28 +09:00`
- needs password: no
- document repaired flag: false
- metadata title: `贵州茅台酒股份有限公司2024年年度报告`

P0-G Gate: **PASS**

---

## 2. P0-H First Native Probe

Output: `workspace\p0\600519_fy_run1.json`

Summary:

- page_count: `143`
- total_ms: `1274.071`
- source_unchanged: `true`
- warning_count: `1`

Stage timings:

| Stage | ms |
|---|---:|
| open | 10.167 |
| text | 330.867 |
| layout | 424.149 |
| drawings_images | 430.503 |
| table_candidate_signals | 33.490 |
| hash_before | 13.147 |
| hash_after | 13.255 |
| total | 1274.071 |

Totals:

- native_chars: `176,089`
- words: `14,890`
- blocks: `3,405`
- drawings: `46,124`
- images: `2`
- native_text_pages: `143`
- empty_text_pages: `0`
- likely_table_pages: `106`

Constraints:

- OCR used: false
- Torch used: false
- Docling used: false
- TableFormer used: false
- external AI API used: false
- Codex Vision used: false

### Warning

Structured MuPDF warning:

`repaired broken tree structure in outline`

Interpretation for P0:

- outline/bookmark tree warning only;
- not a page-content loss warning;
- 143 / 143 pages contain native text;
- all pages were enumerated;
- warning is preserved in machine-readable output;
- no P0 blocker identified.

P0-H Gate: **PASS**

Performance requirement: `<= 120,000 ms`

Observed: `1,274.071 ms`

---

## 3. Slowest Pages — Run 1

| Page | elapsed_ms | chars | words | blocks | drawings | images |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 51.031 | 149 | 10 | 7 | 1 | 0 |
| 43 | 37.270 | 4216 | 471 | 64 | 1778 | 0 |
| 71 | 28.326 | 2293 | 138 | 41 | 1574 | 0 |
| 72 | 27.006 | 1929 | 104 | 19 | 1497 | 0 |
| 73 | 23.417 | 1830 | 101 | 18 | 1347 | 0 |

---

## 4. P0-I Repeatability Run

Second output: `workspace\p0\600519_fy_run2.json`

- page_count: `143`
- total_ms: `1271.943`
- warning_count: `1`
- source_unchanged: `true`

Comparison:

- SHA equal: true
- page_count equal: true
- totals equal: true
- summary equal: true
- warnings equal: true
- constraints equal: true
- all 143 page non-timing records equal: true
- run 1 total: `1274.071 ms`
- run 2 total: `1271.943 ms`
- absolute delta: `2.128 ms`

After both runs source remained unchanged:

- size: `3,626,217 bytes`
- LastWriteTime: `2026-11-02 22:08:28 +09:00`
- SHA256: `5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30`

P0-I Gate: **PASS**

---

## 5. Performance Finding

The broad P0 gate is `143-page native probe <= 120 seconds`.

Observed representative performance is approximately `1.27 seconds`.

This phase does not tighten the official performance gate; broader calibration belongs to a later design decision.

---

## 6. Next Step

Proceed to **P0-J — Code Review**.

No Independent Acceptance verdict is issued by this document.
