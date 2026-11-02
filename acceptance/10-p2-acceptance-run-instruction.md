# 10 — P2 Independent Acceptance Run Instruction

状态：**P2-Q ACCEPTANCE INPUT FREEZE**

你是 **P2 Independent Acceptance 独立验收执行者**。

最终 verdict 只能是：

- `PASS`
- `FAIL`
- `BLOCKED`

验收不得修改：

- production code
- tests
- design
- config
- dependency versions
- Dayu upstream checkout

不得开始 P3。

---

## 1. Repository / Phase

Repository:

`projectforkk/FinancialFilingDataFoundation`

Phase:

`P2 — Acquisition Provider`

Formal branch:

`task/p2-acquisition-provider`

Accepted P1 baseline:

`1cb6e88be318c0a1424d74ee601c336075361cd6`

Reviewed P2 production candidate:

`881c80be1938a128448ea3ed0b4e2cb962f46018`

P2 Code Review commit:

`7c02e6f96bb6b1cb0bff9f1331e9db9d37b74ffe`

Code Review verdict:

`PASS`

Evidence:

`development/21-p2-code-review.md`

---

## 2. Frozen Acceptance Candidate

The frozen candidate is the commit containing this file.

After this file is committed, its exact SHA must be written into `PROJECT_STATUS.md`.

Independent Acceptance uses that exact commit in a fresh detached worktree.

Do not use moving branch HEAD as acceptance truth.

---

## 3. Mandatory Design / Evidence

Read before execution:

- AGENTS.md
- PROJECT_STATUS.md
- design/01-project-detailed-design.md
- design/02-incremental-and-acquisition-design.md
- design/08-p2-acquisition-provider-design.md
- design/09-p2-implementation-plan.md
- development/14-p2-development-instruction.md
- development/15-p2-environment-audit.md
- development/16-p2-dayu-runtime-doctor-evidence.md
- development/17-p2-deterministic-development-evidence.md
- development/18-p2-live-sample-freeze.md
- development/19-p2-live-acquisition-evidence.md
- development/20-p2-pre-review-amendment.md
- development/21-p2-code-review.md
- acceptance/09-p2-acceptance-instruction.md
- this file

---

## 4. Isolation

Create fresh detached worktree:

`D:\Codex\FinancialFilingDataFoundation-P2Acceptance-<shortsha>`

Before/after each critical group:

```powershell
git rev-parse HEAD
git status --short --branch
```

HEAD must equal exact frozen candidate.

Create ignored `workspace\` explicitly.

---

## 5. Runtime Freeze

FFDF main Python:

`D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe`

Expected:

- Python 3.14.9 ARM64
- dayu absent
- docling absent
- torch absent

Dayu source:

`D:\Codex\dependencies\dayu-agent`

Expected:

- repository: `https://github.com/noho/dayu-agent`
- HEAD: `2115c86d5a9027bb51cbbc8a4d0175080732e4e6`
- clean

Dedicated Dayu Python:

`D:\Codex\runtimes\ffdf-dayu-2115c86\.venv\Scripts\python.exe`

Expected:

- Python 3.12.14 AMD64
- dayu-agent 0.1.4

Do not install/upgrade anything during acceptance.

---

## 6. Deterministic Suite

From acceptance worktree:

```powershell
New-Item -ItemType Directory -Force "workspace" | Out-Null
$env:PYTHONPATH="src"
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -m pytest tests\unit -q --basetemp "<worktree>\workspace\pytest-acceptance"
```

Expected current count:

`87 passed`

Any product test failure = FAIL.

---

## 7. P0 / P1 Regression

Verify no source/test differences against accepted P1 baseline under:

- probes
- identity
- registry
- planner
- their unit tests

P2 must only add acquisition functionality.

---

## 8. Main Runtime Isolation

From acceptance worktree / neutral cwd verify:

- dayu not installed/visible
- docling not installed/visible
- torch not installed/visible

Do not perform this check from Dayu source checkout cwd.

---

## 9. Dayu Pin / Immutability

Before live:

- source HEAD exact pinned commit
- clean worktree

After live:

- same HEAD
- still clean

Mismatch before execution:

`BLOCKED` unless evidence shows candidate caused the mismatch.

Do not reset/clean source.

---

## 10. Real No-network Doctor

Use acceptance-candidate runner script through FFDF main adapter.

Required:

- status=OK
- runner_version=`p2-dayu-runner-v1`
- exact Dayu pin
- Dayu module origin under dedicated runtime site-packages
- network_used=false
- docling_conversion_used=false
- safe cwd
- no high-level workflow active call

---

## 11. Static Safety

Verify:

### FFDF main acquisition modules

No direct imports of:

- dayu
- docling
- torch

### Runner

No active import/call of:

- cn_download_filing_workflow
- cn_download_workflow
- convert_pdf_to_docling_json
- docling_export
- SecDownloader

### Adapter

Verify:

- args list
- shell=False
- explicit cwd
- timeout
- JSON request/response
- UTF-8 without BOM

---

## 12. Deterministic Acquisition Matrix

Independent checks must cover:

- CN mocked success
- HK mocked success
- 0 candidate → NOT_FOUND
- >1 distinct candidate → REVIEW_REQUIRED
- identical same-source duplicate → dedup
- same-source metadata conflict → REVIEW_REQUIRED / ACQUISITION_CANDIDATE_METADATA_CONFLICT
- bad host → blocked before download
- SHA mismatch → blocked before registry
- invalid PDF magic → blocked
- raw object corruption → blocked
- second run local short-circuit
- receipt includes request_id + runner_version
- receipt deterministic id
- source provenance registered

The full suite may provide this evidence, but acceptance should independently spot-check key machine behavior.

---

## 13. Fresh Live Acceptance Root

Use a fresh root inside acceptance worktree:

`workspace\p2-acceptance-live`

It must contain a new:

- raw store
- SQLite Registry
- adapter protocol workspace

Do not reuse development live Registry/raw root for first acquisition.

---

## 14. Frozen CN Live Sample

Market:

`CN`

Ticker:

`600519`

Company id:

`CN:600519`

Slot:

`CN|CN:600519|ANNUAL_REPORT|2024|FY`

Window:

`2025-01-01 .. 2025-06-30`

Provider:

`cninfo`

Provider company id:

`CNINFO:gssh0600519`

Expected exact source:

- source_id: `1222993920`
- source URL:
  `http://static.cninfo.com.cn/finalpage/2025-04-03/1222993920.PDF`
- filing date: `2025-04-02`
- remote length: `3,626,217`

Expected official SHA from development/P0 independent evidence:

`5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30`

Fresh acceptance must independently download/recompute.

---

## 15. Frozen HK Live Sample

Market:

`HK`

Ticker:

`00700`

Company id:

`HK:00700`

Slot:

`HK|HK:00700|ANNUAL_REPORT|2024|FY`

Window:

`2025-03-01 .. 2025-06-30`

Provider:

`hkexnews`

Provider company id:

`HKEX:7609`

Expected exact source:

- source_id: `11618398`
- source URL:
  `https://www1.hkexnews.hk/listedco/listconews/sehk/2025/0408/2025040800668_c.pdf`
- filing date: `2025-04-08`
- remote length: `5,241,364`

Expected SHA from development evidence:

`70f529984a87ef7f46d9e1db26bb9ef27eef9c01d29c59aabf69e557b479a6a0`

Fresh acceptance must independently download/recompute.

---

## 16. Live Acceptance Requirements

For both CN/HK:

First call:

- DOWNLOADED
- exact source_id
- exact provider
- exact source host
- exact expected size
- SHA matches expected
- receipt exists
- request_id begins `download-`
- runner_version = `p2-dayu-runner-v1`
- Dayu SHA == FFDF SHA
- registry SOURCE_CONFIRMED
- local state RESOLVED
- source provenance count >= 1
- docling_conversion_used=false
- no Docling JSON/parser output

Second call:

- REUSED_LOCAL
- no new runner protocol files
- raw SHA/size/mtime unchanged

---

## 17. UTF-8 Evidence

Complete live machine evidence must be UTF-8 without BOM JSON.

Console output may be ASCII-only.

Do not fail product because local code page cannot render Chinese source text.

---

## 18. PASS

PASS requires all frozen conditions:

- exact candidate HEAD
- 87 deterministic tests PASS
- P0/P1 integrity PASS
- FFDF runtime isolation PASS
- Dayu pin/clean PASS
- doctor PASS
- static safety PASS
- deterministic matrix PASS
- fresh CN live PASS
- fresh HK live PASS
- incremental no-redownload PASS
- raw/receipt/registry PASS
- no Docling conversion
- no parser
- no SEC implementation
- no unresolved blocker

---

## 19. FAIL

FAIL for product/design failure, including:

- wrong source selected
- SHA mismatch accepted
- candidate ambiguity guessed
- duplicate metadata conflict guessed
- corrupted raw object overwritten
- local second run invokes provider
- missing receipt request_id/runner_version
- Docling conversion invoked
- parser invoked
- deterministic regression failure

---

## 20. BLOCKED

BLOCKED only for external inability to judge, such as:

- official provider externally unavailable during fresh live acceptance
- pinned dependency/runtime unexpectedly inaccessible and not caused by candidate
- target machine cannot execute already-approved runtime

Do not use BLOCKED for ordinary product failure.

---

## 21. Final Evidence

Record:

- frozen candidate SHA
- HEAD stability
- deterministic suite
- runtime isolation
- Dayu pin/clean before/after
- doctor
- CN source/SHA/size
- HK source/SHA/size
- receipt request_id/runner_version
- registry status
- second-run protocol count
- raw immutability
- no Docling/parser/SEC
- warnings/blockers

Final verdict:

`PASS / FAIL / BLOCKED`
