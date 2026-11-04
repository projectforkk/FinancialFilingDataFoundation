# 78 — P10-B Initial Environment / Accepted Interface Audit Attempt

Status: **STOPPED — P10-ISSUE-001 DESIGN AMENDMENT REQUIRED**

Phase:
`P10 — Codex Dynamic Research Integration`

Authorized gate:
`P10-B — Environment / Accepted Interface Audit`

Starting design baseline:
`acb9009d4751bbe5f8f8acec32ea7ffe30ce4c2f`

Authorization:
`development/77-p10-environment-audit-instruction.md`

Starting branch/head:
- branch: `design/p10-dynamic-research-integration`
- HEAD / remote: `dfa5dd1cb1e00b0307a193a0a6b7d1b80e5dffb3`
- `origin/main`: `e9b30626f2b88ac5527d42bd76d0b682efbeef0e`
- worktree: `D:\\Codex\\FinancialFilingDataFoundation\\worktrees\\active\\p10-dynamic-research-design`

No production, tests, runtime, dependencies, P8/P9 artifacts, Registry, or source filing was modified.

## 1. Confirmed environment facts

Observed:

- Microsoft Windows 11 Home `10.0.26200`
- host architecture: ARM64
- FFDF main Python: `3.14.9`, 64-bit ARM64
- Node.js: `v24.22.1`, arm64/win32
- Codex: `codex-cli 0.149.0`
- P8 dedicated runtime: Python `3.12.14` AMD64, MCP `2.3.0`
- P8 server version: `p8-local-mcp-v1`
- P8 exact tool count: `11`
- P8 runtime lock SHA256:
  `8e958b8abcfD9b2de829451ffc253932fa26bb473f73837484b75b1019f092ec`
- P9 CLI exact command count: `6`
- P9 policy: `p9-review-policy-v1`
- P9 version: `p9-review-overlay-v1`

Exact P8 tools remained:

```text
ffdf_list_documents
ffdf_get_document
ffdf_search_document
ffdf_read_pages
ffdf_list_sections
ffdf_list_tables
ffdf_get_table
ffdf_list_raw_facts
ffdf_get_fact
ffdf_get_evidence
ffdf_get_validation
```

Exact P9 CLI commands remained:

```text
prepare
tasks
submit
resolutions
materialize
report
```

## 2. Stop finding — P10-ISSUE-001

The first probe found an invocation-contract gap.

With `PYTHONPATH` removed, the accepted main runtime executed:

```powershell
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -B -c "import financial_filing_data_foundation"
```

Observed:

```text
ModuleNotFoundError: No module named 'financial_filing_data_foundation'
BARE_EXIT=1
```

Package metadata probe returned:

```text
None
```

Therefore FFDF itself is not installed into main-runtime site-packages.

With the exact P10 candidate source bound:

```powershell
$env:PYTHONPATH="D:\Codex\FinancialFilingDataFoundation\worktrees\active\p10-dynamic-research-design\src"
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -B -c "import financial_filing_data_foundation; import financial_filing_data_foundation.mcp.catalog; import financial_filing_data_foundation.review as r; print('IMPORT_OK'); print(r.P9_VERSION)"
```

Observed:

```text
IMPORT_OK
p9-review-overlay-v1
BOUND_EXIT=0
```

Root cause:
the repository uses a source-checkout `src/` layout and does not install FFDF into the main virtual environment. The original P10 design named the runtime but did not freeze exact candidate source selection.

Risk:
review or acceptance could import from the wrong worktree, or an executor could incorrectly add an editable install to the accepted main runtime.

## 3. Other audit observations before stop

These observations did not introduce another blocker:

- P8 `catalog/service` import successfully from main runtime when exact candidate `src` is bound.
- main runtime intentionally has no top-level MCP SDK.
- P8 dedicated MCP runtime remains valid.
- P8 lock hash matches accepted P8.
- P9 public API import succeeds.
- P9 exact six-command CLI remains present.
- local Codex host is available.
- no `research`, `semantic`, `sec`, or `research_mcp` production package exists.
- no dependency/runtime file differs from `origin/main`.
- no new package install was required by the observed environment.

## 4. Required Design-First action

Per governance:

```text
STOP P10-B
→ record facts/root cause
→ amend design/24
→ amend design/25
→ amend acceptance/38
→ commit/push new design baseline
→ explicitly reauthorize P10-B
→ rerun/complete audit using exact-candidate source binding
```

The approved amendment must require:

- `PYTHONPATH=<exact-candidate-worktree>\\src` for P10 Python execution;
- detached review/acceptance to bind their own candidate `src`;
- no editable/install of FFDF into main `.venv` merely for P10;
- no new dependency/runtime.

## 5. Attempt verdict

# STOPPED

Category:
`P10-ISSUE-001 — SOURCE-LAYOUT INVOCATION CONTRACT GAP`

This is not a P8/P9 product failure and not a missing third-party dependency.

P10-C and later gates remain closed.
