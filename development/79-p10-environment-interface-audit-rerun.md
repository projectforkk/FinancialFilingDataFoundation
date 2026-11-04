# 79 — P10-B Environment / Accepted Interface Audit Rerun

Status: **PASS — P10_ENVIRONMENT_READY**

Phase:
`P10 — Codex Dynamic Research Integration`

Authorized gate:
`P10-B — Environment / Accepted Interface Audit`

Amended design baseline:
`ee5ddb9798f45b9abac081fb4f7c2c999c131b6c`

Rerun governance HEAD:
`0b7c414b00b05dddbc97f577477471bf7fbba044`

Authorization:
`development/77-p10-environment-audit-instruction.md`

Historical stopped attempt:
`development/78-p10-environment-interface-audit.md`

The P10-ISSUE-001 rerun was executed read-only after the Design-First source-layout amendment was pushed.

No production, tests, runtime, dependencies, P8/P9 artifacts, Registry, catalog, or source filing was modified.

---

## 1. Git / worktree identity

Worktree:

`D:\\Codex\\FinancialFilingDataFoundation\\worktrees\\active\\p10-dynamic-research-design`

Observed:

```text
BRANCH=design/p10-dynamic-research-integration
HEAD=0b7c414b00b05dddbc97f577477471bf7fbba044
REMOTE=0b7c414b00b05dddbc97f577477471bf7fbba044
MAIN=e9b30626f2b88ac5527d42bd76d0b682efbeef0e
DESIGN_BASELINE_ANCESTOR_EXIT=0
```

The amended design baseline `ee5ddb9...` is an ancestor of the rerun governance HEAD.

Worktree status before the audit:

```text
## design/p10-dynamic-research-integration...origin/design/p10-dynamic-research-integration
```

No tracked or untracked project file was created by the read-only probe itself.

---

## 2. Host identity

Observed:

- OS: Microsoft Windows 11 Home
- OS version: `10.0.26200`
- host architecture: `ARM64`
- system Python: `3.14.9`, ARM64
- Git: `2.55.0.windows.3`
- Node.js: `v24.22.1`
- Node architecture: `arm64 / win32`
- npm: `11.16.0`

Codex:

```text
C:\Users\guoyg\AppData\Local\Programs\OpenAI\Codex\bin\codex.exe
codex-cli 0.149.0
```

Decision:

`REUSE_EXISTING`

---

## 3. P10-ISSUE-001 expected bare-import probe

Before the probe:

```powershell
Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
```

Command:

```powershell
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -B -c "import financial_filing_data_foundation"
```

Observed:

```text
ModuleNotFoundError: No module named 'financial_filing_data_foundation'
BARE_EXIT=1
ffdf_distribution=None
```

Interpretation:

- FFDF is not installed into main-runtime site-packages；
- no editable/install was silently added；
- this is the expected accepted `src/` repository layout after P10-ISSUE-001；
- it is not a missing third-party dependency。

Verdict:

**PASS / EXPECTED**

---

## 4. Exact-candidate source-bound main runtime

The rerun then set exactly:

```powershell
$env:PYTHONPATH="D:\Codex\FinancialFilingDataFoundation\worktrees\active\p10-dynamic-research-design\src"
```

Runtime:

`D:\\Codex\\FinancialFilingDataFoundation\\.venv\\Scripts\\python.exe`

Observed:

```text
main_python=3.14.9 ... 64 bit (ARM64)
main_machine=ARM64
main_platform=win-arm64
ffdf_file=D:\Codex\FinancialFilingDataFoundation\worktrees\active\p10-dynamic-research-design\src\financial_filing_data_foundation\__init__.py
catalog_file=D:\Codex\FinancialFilingDataFoundation\worktrees\active\p10-dynamic-research-design\src\financial_filing_data_foundation\mcp\catalog.py
service_file=D:\Codex\FinancialFilingDataFoundation\worktrees\active\p10-dynamic-research-design\src\financial_filing_data_foundation\mcp\service.py
review_file=D:\Codex\FinancialFilingDataFoundation\worktrees\active\p10-dynamic-research-design\src\financial_filing_data_foundation\review\__init__.py
review_cli_file=D:\Codex\FinancialFilingDataFoundation\worktrees\active\p10-dynamic-research-design\src\financial_filing_data_foundation\review\cli.py
top_level_mcp_sdk=None
p8_main_import=McpCatalog,McpQueryService
p9_version=p9-review-overlay-v1
p9_policy=p9-review-policy-v1
p9_public_api_count=23
p9_cli_count=6
p9_cli_commands=prepare|tasks|submit|resolutions|materialize|report
BOUND_EXIT=0
```

This proves source selection is bound to the exact active P10 candidate worktree rather than shared main or another worktree.

Verdict:

**PASS**

---

## 5. P8 dedicated MCP runtime

Runtime:

`D:\\Codex\\FinancialFilingDataFoundation\\runtimes\\ffdf-mcp-2.3.0\\.venv`

With the same exact-candidate source binding, observed:

```text
mcp_python=3.12.14 ... 64 bit (AMD64)
mcp_machine=ARM64
mcp_platform=win-amd64
mcp=2.3.0
server_file=D:\Codex\FinancialFilingDataFoundation\worktrees\active\p10-dynamic-research-design\src\financial_filing_data_foundation\mcp\server.py
server_name=ffdf-local
server_version=p8-local-mcp-v1
tool_count=11
```

`platform.machine()` reports the ARM64 host while `sysconfig_platform=win-amd64` and the Python build string identify the dedicated runtime as AMD64 under Windows emulation, consistent with accepted P8.

Exact tools:

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

Count:

`11`

Verdict:

**PASS**

---

## 6. P8 runtime lock

Tracked lock:

`runtime-locks/mcp-2.3.0-py312-win-amd64.lock.txt`

SHA256:

`8E958B8ABCFD9B2DE829451FFC253932FA26BB473F73837484B75B1019F092EC`

Accepted P8 value:

`8e958b8abcfD9b2de829451ffc253932fa26bb473f73837484b75b1019f092ec`

Tracked diff check:

`P8_LOCK_DIFF_EXIT=0`

Verdict:

**MATCH / PASS**

---

## 7. Main-runtime SDK boundary

Static main-runtime source scan:

`mcp/catalog.py` and `mcp/service.py`:

```text
P8_MAIN_MCP_IMPORTS=NONE
```

Runtime probe:

```text
top_level_mcp_sdk=None
```

Therefore:

- P8 catalog/service remain usable from main runtime without external MCP SDK；
- external MCP SDK remains isolated to the dedicated P8 server runtime；
- P10 deterministic plumbing requires no MCP SDK installation into main runtime。

Verdict:

**PASS**

---

## 8. P9 accepted interface

Exact CLI commands:

```text
prepare
tasks
submit
resolutions
materialize
report
```

Count:

`6`

Public API exports:

`23`

Key accepted interfaces verified importable:

- `prepare_review_overlay`
- `list_review_tasks`
- `submit_resolution`
- `list_resolutions`
- `active_resolutions`
- `materialize_resolved_view`
- `load_resolved_snapshot`
- `build_resolved_parsed_data_record`

P9 version:

`p9-review-overlay-v1`

P9 policy:

`p9-review-policy-v1`

Verdict:

**PASS / REUSE_EXISTING**

---

## 9. Future-production absence

Under:

`src/financial_filing_data_foundation/`

Observed:

```text
research=ABSENT
semantic=ABSENT
sec=ABSENT
research_mcp=ABSENT
FUTURE_SYMBOLS=NONE
DEPENDENCY_RUNTIME_DIFF=NONE
```

The source scan found no current production implementation of:

- Research MCP renderer；
- HeaderGraph / SemanticResolver；
- SEC provider / Inline XBRL；
- P10 research package。

No dependency/runtime file differs from `origin/main`.

Verdict:

**PASS**

---

## 10. Existing-tools-first decision

| Required capability | Decision | Evidence |
|---|---|---|
| Spec byte hashing / canonical identity | `REUSE_EXISTING` | Python stdlib |
| Project-root path guard | `REUSE_EXISTING` | `pathlib` |
| Deterministic P10 models/manifests | `REUSE_EXISTING` | stdlib dataclasses/typing/json |
| P8 catalog/service | `REUSE_EXISTING` | exact-candidate bound import PASS |
| P8 MCP 11-tool surface | `REUSE_EXISTING` | accepted dedicated runtime |
| P9 review/resolved-view surface | `REUSE_EXISTING` | public API + exact six CLI commands |
| Local Codex reasoning host | `REUSE_EXISTING` | `codex-cli 0.149.0` |
| Evidence-ledger identity validation | `REUSE_EXISTING` | stdlib + accepted P8/P9 identities |
| PDF visual capability if demanded | `INCOMPATIBLE_REQUIRES_DESIGN_AMENDMENT` | deliberately unavailable in P10 v1 |
| Semantic Resolver if demanded | `INCOMPATIBLE_REQUIRES_DESIGN_AMENDMENT` | future-only |
| US SEC provider if demanded | `INCOMPATIBLE_REQUIRES_DESIGN_AMENDMENT` | P11 future-only |

For the next designed Gate, P10-C Models / Spec Freeze:

`INSTALL_REQUIRED = NONE`

No package/runtime install or upgrade is required.

---

## 11. Exact rerun command contract

Baseline:

```powershell
Set-Location "D:\Codex\FinancialFilingDataFoundation\worktrees\active\p10-dynamic-research-design"
git fetch origin
git rev-parse HEAD
git rev-parse origin/design/p10-dynamic-research-integration
git rev-parse origin/main
git merge-base --is-ancestor ee5ddb9798f45b9abac081fb4f7c2c999c131b6c HEAD
git status --short --branch --untracked-files=all
```

Expected bare import:

```powershell
Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -B -c "import financial_filing_data_foundation"
```

Exact-candidate source binding:

```powershell
$env:PYTHONPATH="D:\Codex\FinancialFilingDataFoundation\worktrees\active\p10-dynamic-research-design\src"
```

Main runtime:

```powershell
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -B -c "<P8/P9 import, __file__, policy and CLI probes>"
```

P8 dedicated runtime:

```powershell
D:\Codex\FinancialFilingDataFoundation\runtimes\ffdf-mcp-2.3.0\.venv\Scripts\python.exe -B -c "<server/tool/runtime identity probes>"
```

Lock:

```powershell
Get-FileHash D:\Codex\FinancialFilingDataFoundation\runtime-locks\mcp-2.3.0-py312-win-amd64.lock.txt -Algorithm SHA256
```

Future-scope/dependency scan:

```powershell
git grep -n -i -E "render_table_group|render_page|HeaderGraph|SemanticResolver|SECProvider|Inline XBRL" -- src
git diff --name-only origin/main...HEAD | Select-String -Pattern "pyproject|requirements|runtime-lock|package-lock|package.json|\.venv|Dockerfile"
```

---

## 12. Immutability / worktree result

Final worktree status immediately after all read-only probes:

```text
## design/p10-dynamic-research-integration...origin/design/p10-dynamic-research-integration
```

No production/test/runtime/artifact mutation occurred.

The unrelated pre-rerun draft that had attempted to overwrite historical `development/78` was preserved separately under project-root ignored workspace and was not part of this rerun or its evidence:

`workspace/scratch/p10-audit-rerun-pre79-draft.md`

It is not an accepted project artifact.

---

## 13. Gate verdict

Required P10-B facts:

- project-root boundary: **PASS**
- exact amended design baseline ancestry: **PASS**
- expected bare src-layout behavior: **PASS**
- exact-candidate source binding: **PASS**
- main runtime P8 catalog/service: **PASS**
- main runtime P9 API/CLI: **PASS**
- main runtime external MCP SDK absence: **PASS**
- P8 dedicated runtime: **PASS**
- P8 exact 11 tools: **PASS**
- P8 runtime lock: **MATCH**
- local Codex host: **PASS**
- new dependency/runtime required: **NO**
- future production leakage: **NONE**
- worktree mutation by audit: **NONE**
- blocker: **NONE**

Final P10-B verdict:

# PASS — P10_ENVIRONMENT_READY

P10-C `Models / Spec Freeze` may be considered for authorization only after this evidence is committed/pushed and reviewed.

This result does **not** authorize P10-C production.
