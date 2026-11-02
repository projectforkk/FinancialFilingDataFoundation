# 21 — P2 Acquisition Provider Code Review

状态：**PASS — READY FOR ACCEPTANCE**

Repository:

`projectforkk/FinancialFilingDataFoundation`

Branch:

`task/p2-acquisition-provider`

Frozen reviewed candidate:

`881c80be1938a128448ea3ed0b4e2cb962f46018`

Accepted baseline before P2:

`1cb6e88be318c0a1424d74ee601c336075361cd6`

Dayu upstream pin:

`2115c86d5a9027bb51cbbc8a4d0175080732e4e6`

---

## 1. Review Isolation

Detached review worktree:

`D:\Codex\FinancialFilingDataFoundation-P2Review-881c80b`

HEAD before/after all critical command groups:

`881c80be1938a128448ea3ed0b4e2cb962f46018`

Tracked worktree remained clean.

Result: **PASS**

---

## 2. Full Regression

Review suite:

```text
87 passed in 2.65s
```

Includes P0, P1 and P2 tests.

Result: **PASS**

---

## 3. P0 / P1 Integrity

Compared with accepted P1 baseline:

`1cb6e88be318c0a1424d74ee601c336075361cd6`

No differences under:

- P0 probe source/tests
- P1 identity source/tests
- P1 registry source/tests
- P1 planner source/tests

Result: **PASS**

---

## 4. Runtime Isolation

FFDF main venv review:

- dayu=None
- docling=None
- torch=None

P2 main-runtime acquisition modules contain no direct Dayu/Docling/Torch import.

Dayu is used only through subprocess adapter and dedicated runtime.

Result: **PASS**

---

## 5. Dayu Source / Runtime

Canonical checkout:

`D:\Codex\dependencies\dayu-agent`

Review verified:

- HEAD exact pin
- clean worktree

Dedicated runtime Dayu origin:

`D:\Codex\runtimes\ffdf-dayu-2115c86\.venv\Lib\site-packages\dayu\__init__.py`

No upstream source patch.

Result: **PASS**

---

## 6. No-network Doctor

Review candidate real subprocess doctor:

```text
status=OK
runner_version=p2-dayu-runner-v1
commit=2115c86d5a9027bb51cbbc8a4d0175080732e4e6
network=False
docling_conversion=False
```

HEAD stable before/after.

Result: **PASS**

---

## 7. Subprocess Safety

Reviewed implementation and tests verify:

- args list
- `shell=False`
- explicit neutral cwd
- timeout handling
- UTF-8 no-BOM request/response
- request_id validation
- protocol version validation
- structured runner errors
- no log scraping as business contract

Result: **PASS**

---

## 8. Runner Call Surface

Runner actively imports/calls only narrow CN/HK discovery/downloader symbols.

Static review found no active import/call of:

- `cn_download_filing_workflow`
- `cn_download_workflow`
- `convert_pdf_to_docling_json`
- `docling_export`
- `SecDownloader`

Dayu package initializer transitively loads some broader modules; this is documented upstream behavior and not a conversion call.

Result: **PASS**

---

## 9. Candidate Safety

Verified:

- provider/market match
- ticker match
- exact fiscal year
- exact fiscal period
- source host allowlist
- HK requires https
- 0 candidate → NOT_FOUND
- >1 distinct exact source → REVIEW_REQUIRED
- identical same-source duplicates dedup
- same-source metadata conflict → REVIEW_REQUIRED / ACQUISITION_CANDIDATE_METADATA_CONFLICT
- no first/last-wins guessing

Result: **PASS**

---

## 10. Raw Store / Validation

Verified:

- staging containment
- PDF magic
- independent FFDF SHA
- runner SHA == FFDF SHA
- size check
- content-addressed raw path
- same-SHA dedup
- corrupt existing raw object blocks
- atomic staging commit
- raw source remains immutable after incremental rerun

Result: **PASS**

---

## 11. Receipt

Receipt includes:

- provider/source/slot metadata
- Dayu repo/pin/version/runtime
- actual download runner request_id
- runner_version
- Dayu SHA
- FFDF SHA
- final size/path
- downloaded_at
- registry result
- `docling_conversion_used=false`

Receipt id is deterministic from provider/source/content.

Semantic receipt collision is blocked.

Result: **PASS**

---

## 12. Registry Integration

Verified:

- `register_document()`
- SOURCE_CONFIRMED binding
- independent document source provenance
- exact raw SHA/path
- local resolution after acquisition

Result: **PASS**

---

## 13. Live CN

Sample:

`CN / 600519 / FY2024 / source 1222993920`

Result:

- DOWNLOADED
- size 3,626,217
- SHA:
  `5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30`
- matches independently known P0 official source
- receipt complete
- no Docling conversion

Result: **PASS**

---

## 14. Live HK

Sample:

`HK / 00700 / FY2024 / source 11618398`

Result:

- DOWNLOADED
- size 5,241,364
- SHA:
  `70f529984a87ef7f46d9e1db26bb9ef27eef9c01d29c59aabf69e557b479a6a0`
- receipt complete
- no Docling conversion

Result: **PASS**

---

## 15. Incremental Re-run

Both live slots:

second acquisition result:

`REUSED_LOCAL / LOCAL_RAW_ALREADY_AVAILABLE`

Protocol file count did not increase on second call.

Raw size/SHA/mtime remained unchanged.

Result: **PASS**

---

## 16. No P11 / No Parser

P2 contains:

- no SEC provider implementation
- no P3 parsing implementation
- no table/facts/evidence
- no MCP/Skill

Result: **PASS**

---

## 17. Findings

Blocking findings:

**NONE**

Resolved before final Review:

- P2-ISSUE-001 safe cwd
- P2-ISSUE-002 JSON BOM
- P2-ISSUE-003 transitive module loading semantics
- P2-ISSUE-004 byte-identical raw fixtures
- P2-ISSUE-005 live evidence console encoding
- P2-ISSUE-006 receipt request_id/runner_version
- P2-ISSUE-007 duplicate source metadata conflict

---

## 18. Conclusion

# PASS

P2-P Code Review authorizes:

`P2_READY_FOR_ACCEPTANCE`

Next:

**P2-Q — Acceptance Freeze**
