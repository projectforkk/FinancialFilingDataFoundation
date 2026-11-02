# 19 — P2 Live CN / HK Acquisition and Incremental Re-run Evidence

状态：**P2-M / P2-N / P2-O PASS**

Branch:

`task/p2-acquisition-provider`

Frozen live samples:

`development/18-p2-live-sample-freeze.md`

Machine evidence:

`workspace/p2-live-acquisition/live-acquisition-evidence.json`

---

## 1. Runtime / Upstream

Dayu repository:

`https://github.com/noho/dayu-agent`

Pinned commit:

`2115c86d5a9027bb51cbbc8a4d0175080732e4e6`

Dedicated runtime:

`D:\Codex\runtimes\ffdf-dayu-2115c86\.venv\Scripts\python.exe`

Runtime:

- Python 3.12.14 AMD64
- dayu-agent 0.1.4

After both live runs:

- Dayu checkout HEAD unchanged
- Dayu checkout clean = true

---

## 2. CN Live — 600519 贵州茅台 FY2024

Slot:

`CN|CN:600519|ANNUAL_REPORT|2024|FY`

Provider:

`cninfo`

Source:

- source id: `1222993920`
- source URL: `http://static.cninfo.com.cn/finalpage/2025-04-03/1222993920.PDF`
- filing date: `2025-04-02`
- title: `贵州茅台2024年年度报告`

First acquisition:

`DOWNLOADED / ACQUISITION_COMPLETE`

File size:

`3,626,217 bytes`

Dayu SHA256:

`5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30`

FFDF recomputed SHA256:

`5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30`

This also exactly matches the independently known P0 official FY2024 sample SHA.

Registry:

- local status: RESOLVED
- binding: SOURCE_CONFIRMED
- source provenance count: 1
- source id: 1222993920

Receipt:

- deterministic receipt id:
  `2cc43e5419c1d295d32461a164bbd05fc3778dc165fb1349a485acb7ce9934d7`
- docling_conversion_used: false
- registry SHA == raw SHA
- Dayu SHA == FFDF SHA

### Incremental rerun

Second acquisition:

`REUSED_LOCAL / LOCAL_RAW_ALREADY_AVAILABLE`

Protocol JSON file count:

- before first: 0
- after first: 4
- after second: 4

Therefore second call created no new runner request/response files and did not invoke Dayu/network.

Raw file size/SHA/mtime were unchanged.

Result:

**P2-M PASS / P2-O PASS**

---

## 3. HK Live — 00700 腾讯控股 FY2024

Slot:

`HK|HK:00700|ANNUAL_REPORT|2024|FY`

Provider:

`hkexnews`

Source:

- source id: `11618398`
- source URL:
  `https://www1.hkexnews.hk/listedco/listconews/sehk/2025/0408/2025040800668_c.pdf`
- filing date: `2025-04-08`
- title: `2024 年報`

First acquisition:

`DOWNLOADED / ACQUISITION_COMPLETE`

File size:

`5,241,364 bytes`

Dayu SHA256:

`70f529984a87ef7f46d9e1db26bb9ef27eef9c01d29c59aabf69e557b479a6a0`

FFDF recomputed SHA256:

`70f529984a87ef7f46d9e1db26bb9ef27eef9c01d29c59aabf69e557b479a6a0`

Registry:

- local status: RESOLVED
- binding: SOURCE_CONFIRMED
- source provenance count: 1
- source id: 11618398

Receipt:

- deterministic receipt id:
  `6cb1fc4a1732825475e22bf00d1805ebeee16366c2f0c2fef3f67073708dd675`
- docling_conversion_used: false
- registry SHA == raw SHA
- Dayu SHA == FFDF SHA

### Incremental rerun

Second acquisition:

`REUSED_LOCAL / LOCAL_RAW_ALREADY_AVAILABLE`

Protocol JSON file count:

- before first: 4
- after first: 8
- after second: 8

Therefore second call created no new runner request/response files and did not invoke Dayu/network.

Raw file size/SHA/mtime were unchanged.

Result:

**P2-N PASS / P2-O PASS**

---

## 4. No Parser / No Docling Conversion

Neither live run produced:

- Docling JSON
- parsed document
- table output
- facts/evidence output

Acquisition receipt explicitly records:

`docling_conversion_used=false`

P2 stops after raw document + provenance + registry + receipt.

---

## 5. Source / Raw Immutability

After incremental rerun:

- CN raw SHA unchanged
- CN raw size unchanged
- CN raw mtime unchanged
- HK raw SHA unchanged
- HK raw size unchanged
- HK raw mtime unchanged

Dayu source checkout remained clean.

---

## 6. Gate Results

- P2-M Live CN: **PASS**
- P2-N Live HK: **PASS**
- P2-O Incremental Re-run: **PASS**

No blocking finding.

Next:

**P2-P — Code Review**
