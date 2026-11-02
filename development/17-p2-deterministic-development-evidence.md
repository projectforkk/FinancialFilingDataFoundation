# 17 — P2 Deterministic Acquisition Development Evidence

状态：**P2-F / G / H / I / J / K PASS**

Branch:

`task/p2-acquisition-provider`

Latest design baselines include:

- P2-ISSUE-001 safe cwd
- P2-ISSUE-002 UTF-8 no-BOM JSON
- P2-ISSUE-003 transitive Dayu module loading
- P2-ISSUE-004 byte-identical raw fixtures

---

## 1. Implemented P2 Scope

Implemented:

- acquisition domain models
- AcquisitionProvider protocol
- strict JSON protocol
- content-addressed raw store
- acquisition receipt
- dedicated Dayu narrow runner:
  - doctor
  - discover
  - download
- FFDF main-runtime subprocess adapter
- source host allowlist
- exact slot filtering
- independent FFDF SHA/PDF validation
- P1 Registry integration
- acquisition service
- local short-circuit / no-redownload path
- deterministic CN/HK mocked integration

Not implemented in P2:

- Docling conversion
- PDF parser execution
- tables/facts/evidence
- SEC provider
- MCP/Skill

---

## 2. Runner Narrow Call Surface

Runner actively calls only:

- `CninfoDiscoveryClient.resolve_company`
- `CninfoDiscoveryClient.list_report_candidates`
- `CninfoDiscoveryClient.download_report_pdf`
- HKEX equivalents

Runner does not actively import/call:

- `cn_download_filing_workflow`
- `cn_download_workflow`
- `convert_pdf_to_docling_json`
- `docling_export`

Dayu package initializers may transitively load those modules; this is reported separately and does not authorize conversion.

---

## 3. Adapter Boundary

FFDF main adapter:

- does not import Dayu
- uses args-list subprocess
- `shell=False`
- explicit neutral cwd
- request/response JSON files
- UTF-8 without BOM
- timeout/error mapping
- exact request_id/protocol verification

Real cross-process doctor:

```text
status=OK
commit=2115c86d5a9027bb51cbbc8a4d0175080732e4e6
docling_conversion_used=False
network_used=False
```

Dayu origin:

`D:\Codex\runtimes\ffdf-dayu-2115c86\.venv\Lib\site-packages\dayu\__init__.py`

---

## 4. Raw Store

Implemented layout:

```text
raw_root/
  sha256/<first2>/<sha>.pdf
  receipts/<first2>/<receipt_id>.json
  staging/
```

Verified:

- PDF magic
- independent SHA256
- runner-size check
- staging containment
- SHA-addressed final path
- same-SHA dedup
- existing-object corruption blocker
- deterministic receipt id
- semantic receipt collision blocker
- atomic JSON write

---

## 5. Service Semantics

Verified deterministic actions:

- existing resolved local raw → REUSED_LOCAL / no provider call
- 0 exact candidate → NOT_FOUND
- >1 distinct exact candidate → REVIEW_REQUIRED
- bad source host → structured error before download
- runner SHA mismatch → blocked before registry
- successful acquisition → raw store + provenance + binding + receipt
- second run → no discovery/download

CN provider mapping:

`CN -> cninfo`

HK provider mapping:

`HK -> hkexnews`

---

## 6. Mocked Runner Contract

Fake narrow clients verified:

- CN discover mapping
- HK discover mapping
- download candidate round-trip
- raw PDF copy to FFDF staging
- Dayu temporary file cleanup
- no Docling conversion flag

---

## 7. Test Results

P2 acquisition focused suite:

```text
31 passed in 0.74s
```

Full deterministic unit/regression suite:

```text
85 passed in 2.64s
```

This includes P0 + P1 + P2 tests.

Additional:

- compileall: PASS
- git diff --check: PASS
- FFDF main acquisition direct Dayu/Docling/Torch import scan: no hits
- runner high-level workflow/Docling conversion call scan: no hits

---

## 8. Gate Results

- P2-F Domain / Protocol / Raw Store: PASS
- P2-G Narrow Runner: PASS
- P2-H FFDF Dayu Adapter: PASS
- P2-I Acquisition Service / Registry: PASS
- P2-J Deterministic CN/HK Mocked Integration: PASS
- P2-K Full Regression Before Live: PASS

Next:

**P2-L — Live Sample Confirmation**
