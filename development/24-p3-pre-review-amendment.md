# 24 — P3 Pre-Code-Review Amendment Evidence

状态：**P3-ISSUE-003 / P3-ISSUE-004 CLOSED — P3-H READY**

Branch:

`task/p3-native-page-section`

Accepted baseline before P3:

`4add9fff36b61e2521e9c8d749cee829adb4ab6f`

---

## 1. P3-ISSUE-003 — Page FTS external-content contract

Finding:

Initial P3 implementation duplicated page text inside standalone `page_fts`, while approved design requires `page_content` to be canonical and `page_fts` to use external-content mode.

Correction:

```sql
CREATE TABLE page_content(
  page_no INTEGER PRIMARY KEY,
  text TEXT NOT NULL
)

CREATE VIRTUAL TABLE page_fts USING fts5(
  text,
  content='page_content',
  content_rowid='page_no'
)
```

Index rows use `rowid = page_no`.

Search joins:

`page_fts.rowid -> page_content.page_no`

Tests verify:

- schema SQL contains external-content contract;
- page_content count equals page_fts row count;
- DB close/reopen search remains correct;
- query remains parameterized and deterministic.

Result:

**CLOSED**

---

## 2. P3-ISSUE-004 — Existing artifact completeness/corruption validation

Finding:

Initial `load_native_document()` verified only `document.json`. An externally damaged final artifact could therefore be returned as reusable even if core files were missing or search metadata conflicted.

Correction:

Reuse/load now requires all:

- document.json
- pages.jsonl
- sections.jsonl
- search.sqlite

Manifest validation requires:

- schema = current P3 schema
- parser version = current P3 parser
- directory name = document SHA

Search metadata validation requires:

- document_sha256 matches manifest
- schema_version matches manifest

Any failure:

`ARTIFACT_INCOMPLETE_OR_CORRUPT`

No automatic deletion/overwrite of damaged final artifact is performed.

Tests verify:

- missing pages.jsonl is rejected;
- mismatched search metadata is rejected.

Result:

**CLOSED**

---

## 3. Final Focused / Regression

P3 focused:

```text
17 passed in 0.24s
```

Full P0-P3 suite:

```text
104 passed in 2.83s
```

Result:

**PASS**

---

## 4. Final Fresh Live Re-run

Fresh root:

`workspace/p3-live-v5`

### CN 600519 FY2024

- pages: 143
- sections: 1,376
- total: 1128.253 ms
- page FTS `2024`: 5 hits
- section FTS `2024`: 4 hits
- source unchanged: true

### HK 00700 FY2024

- pages: 274
- sections: 1,079
- total: 1284.799 ms
- page FTS `2024`: 5 hits
- section FTS `2024`: 0 hits
- source unchanged: true

Both:

`total <= 30000 ms`

Result:

**PASS**

---

## 5. Final Development Gate

- P3-B Models / Artifact IO: PASS
- P3-C Native Extraction: PASS
- P3-D Section Engine: PASS
- P3-E FTS5: PASS
- P3-F Unit / Integration: PASS
- P3-G Live CN/HK: PASS

Next:

**P3-H Code Review**
