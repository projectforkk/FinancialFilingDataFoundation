# 15 — P2 Dayu Source / Runtime Environment Audit

状态：**P2-B COMPLETE / RUNTIME DECISION APPROVED**

Branch:

`task/p2-acquisition-provider`

P2 design baseline:

`e53eca8c384f93382945cd2fc529e194a400d066`

Accepted P1 baseline:

`1cb6e88be318c0a1424d74ee601c336075361cd6`

---

## 1. Target PC

- OS: Windows 11 ARM64
- CPU: Snapdragon X Plus 8-core
- disk: D:
- free space observed: ~524 GB

---

## 2. FFDF Main Runtime

Path:

`D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe`

Observed:

- Python 3.14.9
- build: ARM64
- `platform.machine()`: ARM64
- dayu: absent
- docling: absent
- torch: absent

Decision:

**UNCHANGED**

P2 must not install Dayu or Docling into this runtime.

---

## 3. Available Python Interpreters

### 3.1 FFDF native interpreter

`C:\Users\guoyg\AppData\Local\Programs\Python\Python314-arm64\python.exe`

- Python 3.14.9 ARM64

Not selected for Dayu acquisition runtime because the pinned Dayu dependency tree includes heavy third-party packages for which Windows ARM64 / Python 3.14 compatibility is not the validated upstream path.

### 3.2 Existing uv-managed Python 3.12.14 x86_64

`C:\Users\guoyg\AppData\Roaming\uv\python\cpython-3.12.14-windows-x86_64-none\python.exe`

Observed:

- Python 3.12.14
- CPython build: `MSC v.1944 64 bit (AMD64)`
- 64-bit
- hosted on Windows ARM64 through Windows x64 emulation

This interpreter is already installed and does not require modifying system Python / PATH.

### 3.3 Historical Dayu runtime reference

Existing unrelated project venv:

`D:\Codex\FIReport\p1-06-dayu312-venv`

Observed base interpreter:

`C:\Users\guoyg\AppData\Roaming\uv\python\cpython-3.12.14-windows-x86_64-none\python.exe`

Historical venv:

- Python 3.12.14
- CPython build AMD64
- dayu-agent 0.1.4
- pinned upstream commit previously verified as `2115c86...`

Decision:

**REFERENCE ONLY — DO NOT USE AS FORMAL FFDF P2 RUNTIME**

---

## 4. Tooling

- uv: 0.13.5 aarch64-pc-windows-msvc
- Git: 2.55.0.windows.3

No system tool upgrade is required.

---

## 5. Canonical P2 Paths

Approved source checkout:

`D:\Codex\dependencies\dayu-agent`

Approved dedicated runtime root:

`D:\Codex\runtimes\ffdf-dayu-2115c86`

Observed before P2-C:

- dependency root does not exist
- Dayu checkout does not exist
- P2 runtime root does not exist

Therefore P2-C/D can create these paths without overwriting an existing user checkout/runtime.

---

## 6. Pinned Upstream Facts

Repository:

`https://github.com/noho/dayu-agent`

Commit:

`2115c86d5a9027bb51cbbc8a4d0175080732e4e6`

Package version at pin:

`0.1.4`

GitHub source review verified:

### CN

`dayu/fins/downloaders/cninfo_downloader.py`

narrow business methods:

- `resolve_company`
- `list_report_candidates`
- `download_report_pdf`

### HK

`dayu/fins/downloaders/hkexnews_downloader.py`

equivalent narrow discovery/download surface.

### Typed models

`dayu/fins/pipelines/cn_download_models.py`

contains typed query/profile/candidate/downloaded-asset models.

---

## 7. Dependency / Import-Graph Finding

Pinned `pyproject.toml` includes production dependencies such as:

- httpx
- requests
- aiohttp
- pandas
- lxml
- edgartools
- docling
- docling-core
- and additional application dependencies

Package initializer review also found:

- `dayu.fins.__init__` imports `tools`
- `dayu.fins.downloaders.__init__` imports CN, HK and SEC downloader modules
- `dayu.fins.pipelines.__init__` imports CN and SEC pipeline modules

Therefore:

```text
checkout + PYTHONPATH + only-httpx
```

is **not accepted** as a reproducible narrow runtime strategy.

Modifying upstream package initializers to make imports lighter is also rejected.

---

## 8. Runtime Decision

Approved P2 Dayu runtime:

```text
DEDICATED_X86_64_PYTHON312_DAYU_RUNTIME
```

Base interpreter:

`C:\Users\guoyg\AppData\Roaming\uv\python\cpython-3.12.14-windows-x86_64-none\python.exe`

Runtime location:

`D:\Codex\runtimes\ffdf-dayu-2115c86\.venv`

Install source:

the clean canonical checkout at the exact pinned commit.

FFDF communicates with it only through subprocess JSON protocol.

---

## 9. Docling Interpretation

Because Docling is an upstream declared dependency, it may be present in the dedicated Dayu acquisition runtime.

This does **not** authorize:

- Docling conversion
- high-level Dayu download workflow
- parser output
- Docling JSON artifact

The FFDF main runtime remains Dayu/Docling-free.

---

## 10. P2-B Gate

**PASS**

No production code was written during P2-B.

No Dayu source was cloned or installed during P2-B.

No network filing request was executed.

---

## 11. Next Step

Proceed to:

**P2-C — Pinned Dayu Checkout**

Only after exact commit + clean checkout verification may P2-D create the dedicated acquisition runtime.
