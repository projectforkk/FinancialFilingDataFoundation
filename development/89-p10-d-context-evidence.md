# 89 — P10-D Research Context / Capability Manifest Development Evidence

Status: **PASS — P10-D CANDIDATE READY FOR REVIEW**

Phase:
`P10 — Codex Dynamic Research Integration`

Gate:
`P10-D — Research Context / Capability Manifest`

Design baseline:
`ba962aef818d7a31731637a5cfef1f57020a7d1d`

Reauthorization:
`development/88-p10-d-context-reauthorization.md`

Reauthorization commit:
`8fd2604e912431100d500b358fe54fce7eb0dcf9`

Initial implementation:
`f4b5245` — `feat: implement P10 research context`

Corrective implementation:
`9c3db94` — `fix: harden P10 catalog identity`

Boundary-test correction:
`c8b4041` — `test: harden P10 context boundaries`

Final production/test candidate:
`c8b4041c2d06e1d601707ca765ddd9e817f0dfc9`

Branch:
`design/p10-dynamic-research-integration`

Worktree:
`D:\\Codex\\FinancialFilingDataFoundation\\worktrees\\active\\p10-dynamic-research-design`

All work/temp/test paths remained inside:
`D:\\Codex\\FinancialFilingDataFoundation`

## 1. Candidate scope

Exact P10-D changes from reauthorization baseline:

```text
M  src/financial_filing_data_foundation/research/__init__.py
A  src/financial_filing_data_foundation/research/context.py
A  tests/unit/research/test_research_context.py
```

No P8/P9 source or test path changed.

No dependency/runtime file changed.

No provenance, CLI, integration instruction, Research MCP, Semantic Resolver, or P11 implementation was added.

## 2. Implemented contract

P10-D adds deterministic:

- `P8ToolContract`；
- `P9PolicyContract`；
- immutable `ResearchContext`；
- exact P8 accepted integration descriptor；
- exact P9 public policy descriptor；
- exact fixed capability mapping；
- deterministic catalog raw-byte SHA；
- deterministic P8/P9/capability fingerprints；
- canonical P9 review-root identity；
- deterministic `research_context_id`；
- `build_research_context(spec_bundle, p8_catalog, p9_review_root)`。

Schemas/policy:

```text
context schema = p10-research-context-v1
integration policy = p10-dynamic-research-v1
```

There is no caller capability override.

## 3. P10-ISSUE-003 identity contract

Implementation follows design/24 Section 13:

- exact canonical JSON bytes reuse the P10-C Section 8.1 serializer；
- P8 descriptor freezes accepted server version and exact 11 tool names；
- P8 catalog/result schema values come from main-runtime public P8 constants；
- main runtime does not import dedicated `mcp/server.py`；
- P9 descriptor uses public P9 version/policy/schema constants；
- P8/P9 public contract drift fails closed as `P10_CONTEXT_INCOMPATIBLE`；
- catalog current raw bytes are SHA256-hashed；
- current catalog is semantically reloaded through accepted `McpCatalog.load`；
- caller catalog semantic mismatch/current invalid catalog becomes `P10_CATALOG_INVALID`；
- P9 review-root must be an existing project-relative directory；
- absolute/drive-relative/traversal/symlink escape is rejected；
- persisted review-root is canonical project-relative POSIX text；
- review-root identity participates in `research_context_id`；
- exact capability mapping is frozen, with AVAILABLE/UNAVAILABLE states only；
- absolute project paths are not serialized into shared context。

## 4. Implementation defect found and corrected

A direct adversarial probe against initial candidate `f4b5245` manually constructed:

```python
McpCatalog(
    project_root="not-a-path",
    catalog_path="not-a-path",
    documents=(),
)
```

Initial behavior leaked:

```text
AttributeError
'str' object has no attribute 'resolve'
```

This violated the already-frozen P10 error model; no design amendment was required.

Correction `9c3db94`:

- normalizes catalog root/path through `Path(...)`；
- catches OSError/RuntimeError/TypeError/ValueError；
- maps malformed caller catalog state to `P10_CATALOG_INVALID`；
- preserves the accepted catalog reload/equality contract。

Regression coverage was added in `c8b4041`.

Final direct result:

```text
P10Error
P10_CATALOG_INVALID
catalog project root is invalid
```

No native traceback leaks through this client boundary.

## 5. Known identity fixtures

Independent canonical calculations:

```text
P8_TOOL_CONTRACT_FINGERPRINT =
bbeb600e732d5ca567193602d2a2b067fcedeabf9cb5d7cfdf5598671c267bc8

P9_POLICY_FINGERPRINT =
9b7a1078ab2365862dc5061c3b2a76a43f865553eb4df5938b96ffe9bbd4ff36

CAPABILITY_MANIFEST_HASH =
30df28e273379e91c245222b751aaab1504b6c725ca4170a8fb6168082735935
```

Direct fixture:

- spec logical name: `rules`
- spec path: `inputs/rules.md`
- spec bytes: `rules\n`
- catalog bytes:
  `{"schema_version":"p8-mcp-catalog-v1","documents":[]}\n`
- review root: `reviews/a`

Expected/observed:

```text
SPEC_HASH =
021830ab8ded8e8e5eeeef4aa190cf3ffa86ff73a97556f1ebc80f5245288371

CATALOG_HASH =
149a9ec1ed42763860358d44f5d2f6b65115fc5bcf32190b8ca14e3b457de05d

CONTEXT_ID =
a06bbce2a58e6af4b84e5259c41439b4bae0567e3076e2320d26e3d08661d9eb
```

## 6. Exact-candidate focused tests

Exact candidate:

`c8b4041c2d06e1d601707ca765ddd9e817f0dfc9`

Exact source binding:

```powershell
$env:PYTHONPATH="D:\Codex\FinancialFilingDataFoundation\worktrees\active\p10-dynamic-research-design\src"
$env:PYTHONDONTWRITEBYTECODE="1"
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -B -m pytest tests\unit\research\test_research_context.py -q -p no:cacheprovider --basetemp D:\Codex\FinancialFilingDataFoundation\worktrees\t\0
```

Result:

```text
29 passed in 0.30s
```

Focused coverage includes:

- identical-context determinism；
- spec verification/drift；
- exact P8 descriptor + known fingerprint；
- exact P9 descriptor + known fingerprint；
- exact capability mapping + known hash；
- no capability override in API；
- raw catalog SHA + known context fixture；
- stale/invalid/malformed/non-catalog inputs；
- canonical review-root persistence；
- absolute/drive-relative/traversal/symlink escape rejection；
- missing/file review-root rejection；
- different review roots -> different context IDs；
- context ID sensitivity to spec/catalog/P8/P9/capability changes；
- no absolute path serialization；
- P8/P9 public-contract drift fail-closed；
- main runtime external MCP SDK absence；
- exact candidate source binding。

## 7. Exact-candidate full regression

Command:

```powershell
$env:PYTHONPATH="D:\Codex\FinancialFilingDataFoundation\worktrees\active\p10-dynamic-research-design\src"
$env:PYTHONDONTWRITEBYTECODE="1"
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -B -m pytest tests\unit -q -p no:cacheprovider --basetemp D:\Codex\FinancialFilingDataFoundation\worktrees\t\1
```

Result:

```text
368 passed in 25.07s
EXIT_CODE=0
```

P10-C baseline was 339 tests. P10-D adds 29 passing context cases with no prior regression.

Historical/transient runs during concurrent worktree changes are excluded from formal evidence.

## 8. Compile / import / static checks

Compile:
**PASS**

Import:
**PASS**

Exact imports resolve to:

```text
D:\Codex\FinancialFilingDataFoundation\worktrees\active\p10-dynamic-research-design\src\financial_filing_data_foundation\research\__init__.py
D:\Codex\FinancialFilingDataFoundation\worktrees\active\p10-dynamic-research-design\src\financial_filing_data_foundation\research\context.py
```

`git diff --check 8fd2604..c8b4041`:
**PASS**

Forbidden production surface scan:
`NONE`

P8/P9 source/test diff:
`NONE`

Dependency/runtime diff:
`NONE`

No network, OpenAI/Codex/remote AI API, external MCP SDK, subprocess/shell, SQL, environment dump, or recursive prompt discovery is present in P10-D production.

## 9. Dedicated P8 runtime cross-check

Using:

`D:\\Codex\\FinancialFilingDataFoundation\\runtimes\\ffdf-mcp-2.3.0\\.venv`

with exact candidate source binding:

```text
SERVER_VERSION=p8-local-mcp-v1
TOOL_COUNT=11
TOOLS=ffdf_list_documents|ffdf_get_document|ffdf_search_document|ffdf_read_pages|ffdf_list_sections|ffdf_list_tables|ffdf_get_table|ffdf_list_raw_facts|ffdf_get_fact|ffdf_get_evidence|ffdf_get_validation
P8_DEDICATED_RUNTIME_CROSSCHECK=PASS
```

This independently confirms the frozen main-runtime P8 integration descriptor still matches the accepted dedicated MCP runtime without importing the server into the main runtime.

## 10. Direct context probe

Independent direct build result:

```text
SPEC_HASH=021830ab8ded8e8e5eeeef4aa190cf3ffa86ff73a97556f1ebc80f5245288371
CATALOG_HASH=149a9ec1ed42763860358d44f5d2f6b65115fc5bcf32190b8ca14e3b457de05d
P8_FINGERPRINT=bbeb600e732d5ca567193602d2a2b067fcedeabf9cb5d7cfdf5598671c267bc8
P9_FINGERPRINT=9b7a1078ab2365862dc5061c3b2a76a43f865553eb4df5938b96ffe9bbd4ff36
CAPABILITY_HASH=30df28e273379e91c245222b751aaab1504b6c725ca4170a8fb6168082735935
CONTEXT_ID=a06bbce2a58e6af4b84e5259c41439b4bae0567e3076e2320d26e3d08661d9eb
MALFORMED_CATALOG=PASS
NO_ABSOLUTE_PATH=PASS
DIRECT_CONTEXT_PROBE=PASS
```

## 11. Final candidate state

Production/test candidate:
`c8b4041c2d06e1d601707ca765ddd9e817f0dfc9`

Remote branch matched the candidate for formal runs.

No P10-D source/test/runtime artifact was modified after the exact-candidate run.

## 12. Gate verdict

# PASS — P10-D CANDIDATE READY FOR REVIEW

After this evidence is committed/pushed:

**STOP P10-D.**

P10-E remains closed until a separate detached review result PASS and explicit authorization.

Research MCP production, Semantic Resolver production, and P11 production remain closed.
