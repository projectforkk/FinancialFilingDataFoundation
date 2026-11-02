# 11 — P2 Independent Acceptance Result

状态：**PASS**

Repository:

`projectforkk/FinancialFilingDataFoundation`

Phase:

`P2 — Acquisition Provider`

Frozen acceptance candidate:

`803fe3d09bb69a6b378c4e619de00fde95aa9456`

Reviewed production candidate:

`881c80be1938a128448ea3ed0b4e2cb962f46018`

Code Review:

`PASS`

Evidence:

`development/21-p2-code-review.md`

Accepted baseline before P2:

`1cb6e88be318c0a1424d74ee601c336075361cd6`

---

## 1. Verdict

# PASS

P2 satisfies all frozen Independent Acceptance conditions.

No P3 implementation was started during acceptance.

---

## 2. Acceptance Isolation

Worktree:

`D:\Codex\FinancialFilingDataFoundation-P2Acceptance-803fe3d`

Mode:

detached HEAD

Frozen SHA before/after all critical command groups:

`803fe3d09bb69a6b378c4e619de00fde95aa9456`

Tracked worktree remained clean.

Result: **PASS**

---

## 3. Deterministic Suite

Full P0 + P1 + P2 unit/regression suite:

```text
87 passed in 2.70s
```

P0/P1 source and tests compared to accepted P1 baseline:

`git diff --exit-code = 0`

Result: **PASS**

---

## 4. FFDF Main Runtime Isolation

From neutral acceptance cwd:

- Python 3.14.9 ARM64
- dayu=None
- docling=None
- torch=None

Result: **PASS**

---

## 5. Dayu Pin / Immutability

Before fresh live acceptance:

- origin = `https://github.com/noho/dayu-agent.git`
- HEAD = `2115c86d5a9027bb51cbbc8a4d0175080732e4e6`
- worktree clean

After fresh CN/HK live acceptance:

- same HEAD
- worktree clean

No reset/clean/source patch was used.

Result: **PASS**

---

## 6. Real No-network Doctor

Acceptance-candidate runner through FFDF main adapter:

```text
status=OK
runner_version=p2-dayu-runner-v1
commit=2115c86d5a9027bb51cbbc8a4d0175080732e4e6
network=False
docling_conversion=False
```

Dayu module origin is under dedicated acquisition runtime site-packages.

Result: **PASS**

---

## 7. Static Safety

Verified no direct Dayu/Docling/Torch import in FFDF main acquisition modules.

Runner static scan found no active call/import of:

- cn_download_filing_workflow
- cn_download_workflow
- convert_pdf_to_docling_json
- docling_export
- SecDownloader

P2 contains no SEC provider implementation.

Result: **PASS**

---

## 8. Fresh Acceptance Root

Fresh root:

`workspace/p2-acceptance-live`

Created new:

- content-addressed raw store
- SQLite Registry
- adapter protocol workspace

Development live data was not reused for first acquisition.

Machine evidence:

`workspace/p2-acceptance-live/acceptance-live-evidence.json`

Encoding:

UTF-8 without BOM

Result: **PASS**

---

## 9. CN Fresh Live Acceptance

Sample:

`CN / 600519 / FY2024`

Expected source id:

`1222993920`

First acquisition:

`DOWNLOADED / ACQUISITION_COMPLETE`

Provider:

`cninfo`

Size:

`3,626,217`

SHA256:

`5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30`

Receipt:

- source id exact
- source URL exact
- provider company id exact
- filing date exact
- request_id begins `download-`
- runner_version = `p2-dayu-runner-v1`
- Dayu SHA == FFDF SHA
- docling_conversion_used = false

Registry:

- RESOLVED
- SOURCE_CONFIRMED
- source provenance count = 1

Second acquisition:

`REUSED_LOCAL / LOCAL_RAW_ALREADY_AVAILABLE`

Protocol JSON count:

- before: 0
- after first: 4
- after second: 4

Raw SHA/size/mtime unchanged.

Result: **PASS**

---

## 10. HK Fresh Live Acceptance

Sample:

`HK / 00700 / FY2024`

Expected source id:

`11618398`

First acquisition:

`DOWNLOADED / ACQUISITION_COMPLETE`

Provider:

`hkexnews`

Size:

`5,241,364`

SHA256:

`70f529984a87ef7f46d9e1db26bb9ef27eef9c01d29c59aabf69e557b479a6a0`

Receipt:

- source id exact
- source URL exact
- provider company id exact
- filing date exact
- request_id begins `download-`
- runner_version = `p2-dayu-runner-v1`
- Dayu SHA == FFDF SHA
- docling_conversion_used = false

Registry:

- RESOLVED
- SOURCE_CONFIRMED
- source provenance count = 1

Second acquisition:

`REUSED_LOCAL / LOCAL_RAW_ALREADY_AVAILABLE`

Protocol JSON count:

- before: 4
- after first: 8
- after second: 8

Raw SHA/size/mtime unchanged.

Result: **PASS**

---

## 11. No Conversion / Parser Artifacts

Fresh acceptance root scan:

`unexpected_conversion_artifacts = []`

No:

- Docling JSON
- parsed-document artifact
- table/fact/evidence artifact

P2 stopped after raw document + provenance + receipt + Registry.

Result: **PASS**

---

## 12. Final Summary

- exact frozen candidate: PASS
- HEAD stability: PASS
- deterministic suite: 87 PASS
- P0/P1 regression integrity: PASS
- main runtime isolation: PASS
- Dayu pin/clean: PASS
- doctor: PASS
- subprocess/static safety: PASS
- CN fresh live: PASS
- HK fresh live: PASS
- receipt contract: PASS
- Registry integration: PASS
- no-redownload second run: PASS
- raw immutability: PASS
- no Docling conversion: PASS
- no parser: PASS
- no SEC implementation: PASS
- blocker: NONE

Final verdict:

# PASS

P2 is authorized to proceed to P2-S closeout.
