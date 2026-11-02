# 23 — P3 Native Page / Section / FTS Development Evidence

状态：**P3-B / C / D / E / F / G PASS — READY FOR CODE REVIEW**

Branch:

`task/p3-native-page-section`

P3 design baseline:

- `design/10-p3-native-page-section-design.md`
- `design/11-p3-implementation-plan.md`

Accepted baseline before P3:

`4add9fff36b61e2521e9c8d749cee829adb4ab6f`

---

## 1. Implemented P3 Scope

Implemented:

- NativeDocumentArtifact / NativeParseError
- source SHA/size/mtime pre/post validation
- PyMuPDF native page geometry
- words
- text blocks
- lines
- spans / font / size / flags / color / origin
- bbox validation / clamping warnings
- deterministic block reading order
- image count
- compact drawing count
- repeated header/footer detection
- deterministic heading candidates
- deterministic section hierarchy
- deterministic section IDs
- deterministic page ranges
- UTF-8 no-BOM JSON / JSONL artifact persistence
- FTS5 page and section search
- complete-artifact reuse by source SHA/parser version
- staging-directory atomic publish

Not implemented:

- P4 table candidate detection
- table reconstruction
- OCR
- Docling
- facts/evidence
- MCP/Skill
- remote AI

---

## 2. P3-ISSUE-001 — JSONL Unicode line separators

First CN live artifact exposed that raw source text may contain Unicode line separators.

Problem:

- `ensure_ascii=False` preserved U+0085/U+2028/U+2029 literally;
- Python `str.splitlines()` interpreted them as record boundaries;
- one JSON object could appear as multiple logical lines.

Design-first correction:

- JSONL physical record separator fixed to ASCII LF;
- U+0085/U+2028/U+2029 escaped inside JSON strings;
- added line-safe JSONL test;
- first live evidence discarded.

Design commit:

`de259ed164b9805b6e19d860ddcd2e39c3c2e59a`

Main design baseline equivalent:

`5b6c8eda9fc834b93a5e5b7063bf0fa9d9552529`

Result: **CLOSED**

---

## 3. P3-ISSUE-002 — PyMuPDF DICT image payload performance

First HK live run exceeded the 30s Gate.

A/B evidence on representative HK pages:

```text
page 1  default DICT ~1231.69 ms  text-only DICT ~2.09 ms
page 20 default DICT ~466.96 ms   text-only DICT ~1.41 ms
page 32 default DICT ~392.13 ms   text-only DICT ~1.45 ms
page 34 default DICT ~425.28 ms   text-only DICT ~1.32 ms
```

Root cause:

PyMuPDF default DICT preserves image binary payload even though P3 uses only text layout.

Design-first correction:

- `TEXTFLAGS_DICT & ~TEXT_PRESERVE_IMAGES`
- one TextPage per page reused for words + dict
- image count remains separate via `get_images(full=True)`
- drawing count uses compact `get_cdrawings()`
- image-only pages remain explicit native-text-empty pages
- parser semantic version unchanged because prior code already ignored image blocks

Design commit:

`dc2e5a834732909202dc7eb6dbf6a2aed2c54dd2`

Main design baseline equivalent:

`a35304280d0863299d4b07ac893029a1310e9142`

Result: **CLOSED**

---

## 4. Focused Tests

P3 focused suite after both corrections:

```text
14 passed in 0.19s
```

Coverage includes:

- born-digital extraction
- blank page
- image-only page
- rotated page
- words/blocks/spans/bbox
- deterministic reading order
- Chinese/Arabic section hierarchy
- repeated header/footer suppression
- deterministic IDs/ranges
- page FTS
- section FTS
- UTF-8 no-BOM
- JSONL Unicode line-separator safety
- artifact reuse
- repeated fresh-root page/section byte determinism
- no heavy-path imports

---

## 5. Full Regression

Full current unit suite:

```text
101 passed in 2.68s
```

Includes P0 + P1 + P2 + P3.

Additional:

- compileall: PASS
- git diff --check: PASS
- P3 forbidden Dayu/Docling/Torch/AI/network import scan: no hits
- P4 table reconstruction scope scan: no hits

---

## 6. Live CN — 600519 FY2024

Source SHA:

`5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30`

Source size:

`3,626,217 bytes`

Observed:

- page_count: 143
- native_text_pages: 143
- empty_text_pages: 0
- word_count: 14,890
- block_count: 3,405
- span_count: 18,809
- section_count: 1,376
- warning_count: 0
- page FTS `2024`: 5 hits
- section FTS `2024`: 4 hits

Timings:

```text
open            9.114 ms
native_extract  825.190 ms
section         81.376 ms
persist         188.000 ms
total           1125.248 ms
```

Performance Gate:

`1125.248 ms <= 30000 ms`

Source before/after SHA/size/mtime:

unchanged.

Result: **PASS**

---

## 7. Live HK — 00700 FY2024

Source SHA:

`70f529984a87ef7f46d9e1db26bb9ef27eef9c01d29c59aabf69e557b479a6a0`

Source size:

`5,241,364 bytes`

Observed:

- page_count: 274
- native_text_pages: 272
- empty_text_pages: 2
- word_count: 15,839
- block_count: 7,042
- span_count: 19,793
- section_count: 1,079
- warning_count: 2
- page FTS `2024`: 5 hits
- section FTS `2024`: 0 hits

The section-query result is not a failure: the queried token is not guaranteed to appear in a heading title. Section FTS correctness is independently covered by focused tests.

Timings:

```text
open            11.594 ms
native_extract  887.043 ms
section         100.492 ms
persist         245.070 ms
total           1274.983 ms
```

Performance Gate:

`1274.983 ms <= 30000 ms`

Source before/after SHA/size/mtime:

unchanged.

Result: **PASS**

---

## 8. Live Machine Evidence

Fresh post-fix artifact root:

`workspace/p3-live-v3`

Evidence:

`workspace/p3-live-v3/p3-live-evidence.json`

Both live outputs were produced after P3-ISSUE-001 and P3-ISSUE-002 corrections.

---

## 9. Gate Result

- P3-B Models / Artifact IO: PASS
- P3-C Native Extraction: PASS
- P3-D Section Engine: PASS
- P3-E FTS5: PASS
- P3-F Unit / Integration: PASS
- P3-G Live CN/HK: PASS

Next:

**P3-H — Code Review**
