# 03 — P0 Environment Audit and Runtime Decision

状态：**P0-B COMPLETE / P0-C DECISION RECORDED**

执行分支：`task/p0-native-pdf-feasibility`

设计基线：`10e5abd18d84a821891175e8e2b823809092d7ad`

执行环境：WorkHome

---

## 1. P0-B Environment Audit

### 1.1 Operating System

- OS: Microsoft Windows 11 Home
- Version: 10.0.26200
- Build: 26200
- OS architecture: ARM64

### 1.2 CPU

- CPU: Snapdragon X Plus (8-core) @ 3.30 GHz
- Physical cores: 8
- Logical processors: 8
- Address width: 64-bit
- Native machine architecture: ARM64

### 1.3 System Python

Primary executable:

`C:\Users\guoyg\AppData\Local\Programs\Python\Python314-arm64\python.exe`

Observed:

- Python: CPython 3.14.9
- Build architecture: ARM64
- Pointer width: 64-bit
- `platform.machine()`: ARM64

System package state before P0 environment creation:

- PyMuPDF: NOT INSTALLED
- legacy `fitz`: NOT INSTALLED
- pypdf: NOT INSTALLED

### 1.4 pip / uv

- pip: 26.2.2
- pip Python: 3.14
- uv: 0.13.5
- uv build: aarch64-pc-windows-msvc

### 1.5 Git

- Git: 2.55.0.windows.3
- executable: `C:\Program Files\Git\cmd\git.exe`

### 1.6 Codex

- Codex CLI: 0.149.0
- executable: `C:\Users\guoyg\AppData\Local\Programs\OpenAI\Codex\bin\codex.exe`

---

## 2. Existing Dayu Environment

Existing runtime:

`D:\Codex\FIReport\p1-06-dayu312-venv`

Python executable:

`D:\Codex\FIReport\p1-06-dayu312-venv\Scripts\python.exe`

Observed:

- Python: 3.12.14
- Python build: 64-bit AMD64
- Host OS: Windows ARM64
- dayu-agent: 0.1.4
- installed package path:
  `D:\Codex\FIReport\p1-06-dayu312-venv\Lib\site-packages\dayu`

Installed package provenance from `direct_url.json`:

- repository: `https://github.com/noho/dayu-agent.git`
- commit: `2115c86d5a9027bb51cbbc8a4d0175080732e4e6`

This matches:

`D:\Codex\FIReport\company-research-data-engine\config\dayu-baseline.json`

Dayu runtime package dependencies include Docling and related heavy dependencies.

Within this Dayu venv at audit time:

- PyMuPDF: NOT INSTALLED
- pypdf: NOT INSTALLED

---

## 3. Reuse Assessment

### System Python

Decision: **DO NOT MODIFY SYSTEM ENVIRONMENT**

Reason:

- system Python is suitable as the interpreter source;
- P0 policy forbids unnecessary system environment mutation;
- PyMuPDF / pytest should be isolated to the FFDF repository.

### Existing Dayu venv

Decision: **DO NOT REUSE AS P0 PARSER RUNTIME**

Reasons:

1. It is an AMD64 Python runtime on an ARM64 host.
2. It intentionally carries Dayu / Docling heavy dependencies.
3. P0 explicitly forbids Docling / Torch / heavy parser paths.
4. Reusing this environment would weaken the P0 measurement because it would not test the target lightweight ARM64-native path.
5. Dayu is relevant later as an acquisition dependency boundary, not as the P0 parser runtime.

Dayu environment remains untouched.

### pypdf

Decision: **NOT REQUIRED FOR P0 CURRENT IMPLEMENTATION**

Reason:

The approved P0 probe requirements can be fulfilled with PyMuPDF native APIs. pypdf must not be added only for convenience.

---

## 4. P0-C Runtime Decision

Create a project-local isolated venv:

`D:\Codex\FinancialFilingDataFoundation\.venv`

Interpreter source:

`C:\Users\guoyg\AppData\Local\Programs\Python\Python314-arm64\python.exe`

Target runtime:

- CPython 3.14.9
- ARM64
- 64-bit

Approved minimum dependencies:

- `PyMuPDF==1.28.2`
- `pytest==9.2.0`

No pypdf dependency unless a later P0 design correction explicitly requires it.

---

## 5. Heavy-path Prohibition

P0 runtime must not install or invoke for the probe:

- OCR engines
- Torch
- Docling
- TableFormer
- neural layout frameworks
- external AI SDK/API
- Codex Vision

The P0 probe implementation must use only lightweight local native parsing capabilities.

---

## 6. Environment Creation Command

Approved command:

```powershell
uv venv .venv --python "C:\Users\guoyg\AppData\Local\Programs\Python\Python314-arm64\python.exe"
uv pip install --python ".venv\Scripts\python.exe" "PyMuPDF==1.28.2" "pytest==9.2.0"
```

After creation, verify:

```text
python version
python architecture
PyMuPDF version
pytest version
absence of pypdf
absence of docling
absence of torch
```

---

## 7. Gate Results

### P0-B Gate

**PASS**

Required environment facts have been recorded.

### P0-C Gate

**APPROVED TO EXECUTE**

Runtime decision:

`PROJECT_LOCAL_ARM64_VENV`

No system Python / PATH / Git / Node changes are authorized.

No Dayu environment changes are authorized.

---

## 8. P0-C Environment Verification

Created:

`D:\\Codex\\FinancialFilingDataFoundation\\.venv`

Verified runtime:

- executable: `D:\\Codex\\FinancialFilingDataFoundation\\.venv\\Scripts\\python.exe`
- Python: 3.14.9
- build: MSC 64-bit ARM64
- `platform.machine()`: ARM64
- pointer width: 64-bit
- PyMuPDF: 1.28.2
- pytest: 9.2.0
- pypdf: NOT INSTALLED
- docling: NOT INSTALLED
- torch: NOT INSTALLED

Environment creation completed without modifying system Python or Dayu venv.

### P0-C Gate

**PASS**

---

## 9. Next Step

Proceed to P0-D Native PDF Probe implementation.

Representative PDF discovery/execution remains deferred until P0-G.
