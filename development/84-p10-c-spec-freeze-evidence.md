# 84 — P10-C Models / Spec Freeze Development Evidence

Status: **PASS — P10-C CANDIDATE READY FOR REVIEW**

Phase:
`P10 — Codex Dynamic Research Integration`

Gate:
`P10-C — Models / Spec Freeze`

Design baseline:
`f20e4fd46c8d56e85dce80a16daf91abafd6323f`

Reauthorization:
`development/83-p10-c-spec-freeze-reauthorization.md`

Reauthorization commit:
`24bd4692d8857ca76802b6d0cc7fbbad3e9d2b6a`

Implementation candidate:
`35553df23f58a7f539b7390f98c7f154e42c817e`

Branch:
`design/p10-dynamic-research-integration`

Worktree:
`D:\\Codex\\FinancialFilingDataFoundation\\worktrees\\active\\p10-dynamic-research-design`

All work/temp/test paths remained under:
`D:\\Codex\\FinancialFilingDataFoundation`

## 1. Candidate scope

Exact production/test changes from the P10-C reauthorization parent:

```text
A  src/financial_filing_data_foundation/research/__init__.py
A  src/financial_filing_data_foundation/research/models.py
A  src/financial_filing_data_foundation/research/spec.py
A  tests/unit/research/test_research_spec.py
```

No P8/P9 source or test path changed.

No dependency/runtime file changed.

No context, capability manifest, provenance, CLI, integration instruction, Research MCP, Semantic Resolver, or P11 implementation was added.

## 2. Implemented contract

P10-C adds deterministic:

- `P10Error` with stable `reason_code`；
- `ResearchSpecInput`；
- immutable `ResearchSpecFile`；
- immutable `ResearchSpecBundle`；
- `freeze_research_spec(project_root, files)`；
- `verify_research_spec(project_root, bundle)`；
- schema `p10-research-spec-bundle-v1`。

Bundle serialization stores descriptors only and never copies research instruction contents.

## 3. P10-ISSUE-002 byte identity

Implementation follows design/24 Section 8.1:

- explicit non-empty input list；
- non-blank exact logical names；
- exact duplicate logical names rejected；
- no trim/case-fold identity normalization；
- input paths project-root-relative only；
- resolved target must remain inside resolved project root and be a regular file；
- persisted path = resolved project-root-relative POSIX path；
- size = exact raw-byte length；
- SHA256 = exact raw bytes；
- no UTF-8/BOM/newline normalization；
- descriptors sorted by exact logical name；
- canonical JSON = UTF-8 / sorted keys / compact separators / `allow_nan=False`；
- bundle hash input = descriptor array only；
- caller input order does not affect identity。

Known independent fixture:

```text
alpha:
  relative_path=a.txt
  bytes=41 0a
  sha256=06f961b802bc46ee168555f066d28f4f0e9afdf3f88174c1ee6f9de004fc30a0

beta:
  relative_path=nested/b.txt
  bytes=42 0d 0a
  sha256=65be7a95a3a5b68952c6ee7d6d7429270e8b24f632656ba2bf161885dcdbf6b3

spec_bundle_hash=
b6a725f6545abd35747fc884d0d48b81c42c3746acfa89b985bcbc239a3db5e5
```

The expected hash was calculated independently from the frozen canonical descriptor-array formula and is hard-coded in focused tests.

## 4. Error classification

Verified deterministic reason classes:

- malformed input/bundle/schema/order/hash/tamper:
  `P10_INVALID_SPEC_INPUT`
- absolute/outside/traversal/root escape:
  `P10_SPEC_PATH_OUTSIDE_PROJECT`
- current frozen file missing/deleted/size/hash drift:
  `P10_RESEARCH_SPEC_CHANGED`

No silent refresh is performed.

## 5. Focused tests

Exact candidate:
`35553df23f58a7f539b7390f98c7f154e42c817e`

Exact source binding:

```powershell
$env:PYTHONPATH="D:\Codex\FinancialFilingDataFoundation\worktrees\active\p10-dynamic-research-design\src"
$env:PYTHONDONTWRITEBYTECODE="1"
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -B -m pytest tests\unit\research\test_research_spec.py -q -p no:cacheprovider --basetemp D:\Codex\FinancialFilingDataFoundation\worktrees\t\m
```

Result:

```text
31 passed in 0.10s
```

Focused coverage includes:

- single/multiple files；
- caller-order independence；
- exact logical-name ordering；
- case-distinct logical names；
- empty/blank/duplicate inputs；
- exact raw bytes including BOM/non-UTF8/newline-sensitive bytes；
- independent known-fixture hash；
- missing/directory/absolute/traversal inputs；
- resolved POSIX persisted path；
- symlink escape when supported；
- byte mutation / size-preserving mutation / deletion；
- schema/hash/descriptor/order tamper；
- noncanonical relative path；
- verification root escape；
- descriptor-array-only hash；
- no instruction content persistence；
- dict round-trip；
- exact candidate source import。

## 6. Full unit regression

Exact command:

```powershell
$env:PYTHONPATH="D:\Codex\FinancialFilingDataFoundation\worktrees\active\p10-dynamic-research-design\src"
$env:PYTHONDONTWRITEBYTECODE="1"
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -B -m pytest tests\unit -q -p no:cacheprovider --basetemp D:\Codex\FinancialFilingDataFoundation\worktrees\t\n
```

Result:

```text
339 passed in 23.19s
EXIT_CODE=0
```

P9 closeout baseline was 308 tests; the P10-C candidate adds 31 passing focused cases with no prior regression.

## 7. Compile / import

Exact candidate source binding was used.

Compile:

```text
python -B -m compileall -q src\financial_filing_data_foundation\research tests\unit\research
COMPILE_EXIT=0
```

Import:

```text
IMPORT_OK
...\worktrees\active\p10-dynamic-research-design\src\financial_filing_data_foundation\research\__init__.py
...\worktrees\active\p10-dynamic-research-design\src\financial_filing_data_foundation\research\models.py
...\worktrees\active\p10-dynamic-research-design\src\financial_filing_data_foundation\research\spec.py
p10-research-spec-bundle-v1
IMPORT_EXIT=0
```

All imported modules resolve to the exact candidate worktree.

## 8. Scope / security

`git diff --check 24bd469..35553df`:
**PASS**

Static production scan for network/AI/MCP SDK/subprocess/shell/SQL/environment-execution surfaces:
`FORBIDDEN_SURFACE=NONE`

Production imports are limited to:

- stdlib `hashlib`
- stdlib `json`
- stdlib `re`
- stdlib `dataclasses`
- stdlib `pathlib`
- stdlib `typing`
- local P10 research modules。

P8/P9 source/test diff:
`NONE`

Dependency/runtime diff:
`NONE`

No external MCP SDK is required by P10-C.

No network or remote AI API exists in P10-C production.

## 9. Encoding

New source/test files decode as UTF-8 and contain no UTF-8 BOM.

Git canonicalization warnings are the repository's existing Windows `core.autocrlf` behavior; staged Git blobs passed `git diff --cached --check`.

## 10. Final candidate state

Candidate:
`35553df23f58a7f539b7390f98c7f154e42c817e`

Remote branch matched the candidate during verification.

Final tracked/untracked status immediately after candidate verification:

```text
## design/p10-dynamic-research-integration...origin/design/p10-dynamic-research-integration
```

No source/test/runtime artifact was modified after the exact-candidate test run.

## 11. Gate verdict

# PASS — P10-C CANDIDATE READY FOR REVIEW

P10-C implementation/evidence may be committed/pushed.

After this evidence is pushed:

**STOP P10-C.**

P10-D remains closed until a separate design-owner review and explicit instruction.

Research MCP production, Semantic Resolver production, and P11 production remain closed.
