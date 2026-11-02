# 18 — P2 Live Sample Freeze Evidence

状态：**P2-L LIVE_SAMPLES_FROZEN**

Branch:

`task/p2-acquisition-provider`

Discovery executed after deterministic P2-K PASS.

Full evidence is stored as UTF-8 no-BOM JSON under ignored workspace.

---

## 1. CN Frozen Sample

Market:

`CN`

Ticker:

`600519`

FFDF company id:

`CN:600519`

Slot:

`CN|CN:600519|ANNUAL_REPORT|2024|FY`

Discovery window:

`2025-01-01 .. 2025-06-30`

Provider:

`cninfo`

Provider company id:

`CNINFO:gssh0600519`

Provider company name:

`贵州茅台`

Exact candidate count:

`1`

Candidate:

- source_id: `1222993920`
- filing_date: `2025-04-02`
- fiscal_year: `2024`
- fiscal_period: `FY`
- amended: `false`
- language: `zh`
- source_title: `贵州茅台2024年年度报告`
- source_url: `http://static.cninfo.com.cn/finalpage/2025-04-03/1222993920.PDF`
- remote_content_length: `3,626,217`
- last_modified: `Wed, 02 Apr 2025 13:21:12 GMT`

Evidence:

`workspace/p2-live-discovery/cn-600519-fy2024-discovery.json`

This content length matches the existing known official FY2024 sample size used by P0, but P2 live acquisition will independently download and hash the source.

---

## 2. HK Frozen Sample

Market:

`HK`

Ticker:

`00700`

FFDF company id:

`HK:00700`

Slot:

`HK|HK:00700|ANNUAL_REPORT|2024|FY`

Discovery window:

`2025-03-01 .. 2025-06-30`

Provider:

`hkexnews`

Provider company id:

`HKEX:7609`

Provider company name:

`騰訊控股`

Exact candidate count:

`1`

Candidate:

- source_id: `11618398`
- filing_date: `2025-04-08`
- fiscal_year: `2024`
- fiscal_period: `FY`
- amended: `false`
- language: `zh`
- source_title: `2024 年報`
- source_url: `https://www1.hkexnews.hk/listedco/listconews/sehk/2025/0408/2025040800668_c.pdf`
- remote_content_length: `5,241,364`
- last_modified: `Tue, 08 Apr 2025 09:02:23 GMT`

Evidence:

`workspace/p2-live-discovery/hk-00700-fy2024-discovery.json`

---

## 3. Discovery Runtime

Discovery used:

- FFDF main adapter
- dedicated Dayu subprocess runtime
- pinned Dayu commit `2115c86d5a9027bb51cbbc8a4d0175080732e4e6`
- narrow provider discovery methods

No PDF download was performed during this Gate.

No Docling conversion was performed.

---

## 4. P2-ISSUE-005

The first discovery evidence attempt printed Unicode provider/company data directly to a CP932 Windows console and failed while rendering Chinese text.

That attempt is discarded.

The rerun used UTF-8 no-BOM JSON evidence and ASCII-only console summary:

```text
CN 600519 candidate_count=1
HK 00700 candidate_count=1
```

Both complete JSON evidence files were then read successfully.

---

## 5. Gate Result

**P2-L = PASS / LIVE_SAMPLES_FROZEN**

Next:

- P2-M live CN acquisition
- P2-N live HK acquisition
