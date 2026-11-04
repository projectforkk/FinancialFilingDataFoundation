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

Implementation candidate:
`c8b4041c2d06e1d601707ca765ddd9e817f0dfc9`

Branch:
`design/p10-dynamic-research-integration`

Worktree:
`D:\\Codex\\FinancialFilingDataFoundation\\worktrees\\active\\p10-dynamic-research-design`

All work, test temp, and basetemp paths remained under:
`D:\\Codex\\FinancialFilingDataFoundation`

## 1. Candidate scope

Exact P10-D production/test diff from the reauthorization parent:

```text
M  src/financial_filing_data_foundation/research/__init__.py
A  src/financial_filing_data_foundation/research/context.py
A  tests/unit/research/test_research_context.py
```

No P8/P9 source or test path changed.

No dependency/runtime file changed.

No P10-E provenance, P10-F CLI, Research MCP, Semantic Resolver, or P11 production was added.

## 2. Implemented contract

P10-D adds deterministic:

- `ResearchContext`
- `P8ToolContract`
- `P9PolicyContract`
- `build_research_context(spec_bundle, p8_catalog, p9_review_root)`
- exact P8 accepted integration descriptor
- exact P9 public policy descriptor
- raw catalog byte SHA256
- accepted `McpCatalog.load` semantic consistency reload
- canonical project-relative P9 review-root identity
- exact fixed capability manifest
- deterministic `research_context_id`

The builder has no caller capability override.

## 3. P10-ISSUE-003 contract

Implementation follows design/24 Sections 13.1–13.7 and 14.

### 3.1 Spec-first ordering

The builder first derives only the accepted `McpCatalog.project_root`, then calls:

`verify_research_spec(project_root, spec_bundle)`

before reading/reloading the current catalog file.

Focused test independently corrupts both the spec and catalog and verifies the result remains:

`P10_RESEARCH_SPEC_CHANGED`

This freezes the required deterministic error precedence.

### 3.2 P8 descriptor

Exact descriptor:

```text
server_version=p8-local-mcp-v1
catalog_schema_version=p8-mcp-catalog-v1
result_schema_version=p8-mcp-result-v1
tool_count=11
```

Exact accepted tool names:

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

Known independent fingerprint:

`bbeb600e732d5ca567193602d2a2b067fcedeabf9cb5d7cfdf5598671c267bc8`

The main runtime does not import `financial_filing_data_foundation.mcp.server` or the external MCP SDK.

### 3.3 P9 descriptor

Exact public values:

```text
p9_version=p9-review-overlay-v1
policy_version=p9-review-policy-v1
resolution_schema_version=p9-review-resolution-v1
resolved_view_schema_version=p9-resolved-view-v1
```

Known independent fingerprint:

`9b7a1078ab2365862dc5061c3b2a76a43f865553eb4df5938b96ffe9bbd4ff36`

### 3.4 Capability manifest

Exact fixed mapping:

```text
P8_RAW_QUERY=AVAILABLE
P8_PAGE_TEXT=AVAILABLE
P8_TABLE_STRUCTURED=AVAILABLE
P8_EVIDENCE=AVAILABLE
P8_VALIDATION=AVAILABLE
P9_REVIEW=AVAILABLE
P9_RESOLVED_VIEW=AVAILABLE
PDF_VISUAL_EVIDENCE=UNAVAILABLE
SEMANTIC_RESOLVER=UNAVAILABLE
CANONICAL_METRIC_LAYER=UNAVAILABLE
P11_SEC_PROVIDER=UNAVAILABLE
```

Known independent manifest hash:

`30df28e273379e91c245222b751aaab1504b6c725ca4170a8fb6168082735935`

No caller override exists.

## 4. Known research-context fixture

Fixed spec bytes:

```text
logical_name=rules
relative_path=inputs/rules.md
bytes=72 75 6c 65 73 0a
```

Known spec bundle hash:

`021830ab8ded8e8e5eeeef4aa190cf3ffa86ff73a97556f1ebc80f5245288371`

Fixed catalog raw bytes:

```text
{"schema_version":"p8-mcp-catalog-v1","documents":[]}
```

Known raw catalog SHA256:

`149a9ec1ed42763860358d44f5d2f6b65115fc5bcf32190b8ca14e3b457de05d`

Canonical P9 review root:

`reviews/a`

Known exact research context ID:

`a06bbce2a58e6af4b84e5259c41439b4bae0567e3076e2320d26e3d08661d9eb`

The expected values are hard-coded in focused tests and were calculated independently from the frozen design formula.

## 5. Catalog validation

Verified:

- catalog type must be accepted `McpCatalog`
- project root must resolve to an existing directory
- catalog path must resolve inside project root
- current raw bytes are hashed
- current file is reloaded through accepted `McpCatalog.load`
- caller object and reloaded catalog must be semantically equal
- file bytes must not change during validation
- stale caller catalog versus changed current file returns `P10_CATALOG_INVALID`
- malformed current catalog returns `P10_CATALOG_INVALID`
- non-`McpCatalog` caller object returns `P10_CATALOG_INVALID`
- manually malformed `project_root` / `catalog_path` fields return `P10_CATALOG_INVALID` rather than leaking Python type/attribute errors

No P8 catalog parsing/truth semantics are copied into P10.

## 6. P9 review-root identity

Verified:

- caller input is project-root-relative
- absolute path rejected
- Windows drive-relative path rejected
- traversal escape rejected
- resolved path must remain within project root
- target must already exist
- target must be a directory
- persisted form is canonical project-relative POSIX
- no filesystem creation occurs
- different canonical review roots produce different context IDs

Reason classes:

- outside/absolute/drive-relative/traversal:
  `P10_CONTEXT_PATH_OUTSIDE_PROJECT`
- missing/not-directory:
  `P10_CONTEXT_INCOMPATIBLE`

## 7. Context identity dimensions

Focused tests prove `research_context_id` changes when any of these change:

- spec bundle hash
- raw P8 catalog SHA
- P8 contract fingerprint
- P9 policy fingerprint
- canonical P9 review root
- capability manifest hash

The exact design formula includes:

- context schema version
- integration policy version
- all identity dimensions above

It excludes:

- current time
- random UUID
- Codex output
- tool order
- absolute filesystem paths

## 8. Focused tests

Exact candidate:

`c8b4041c2d06e1d601707ca765ddd9e817f0dfc9`

Exact command:

```powershell
$env:PYTHONPATH="D:\Codex\FinancialFilingDataFoundation\worktrees\active\p10-dynamic-research-design\src"
$env:PYTHONDONTWRITEBYTECODE="1"
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -B -m pytest tests\unit\research\test_research_context.py -q -p no:cacheprovider --basetemp D:\Codex\FinancialFilingDataFoundation\worktrees\t\u
```

Result:

```text
29 passed in 0.29s
FOCUSED_EXIT=0
```

The focused set covers all design/25 P10-D required items 1–22, with some items split into separate negative cases. Additional hardening verifies P8/P9 public-contract drift fails closed and a review-root symlink escape is rejected.

## 9. Full unit regression

Exact candidate command:

```powershell
$env:PYTHONPATH="D:\Codex\FinancialFilingDataFoundation\worktrees\active\p10-dynamic-research-design\src"
$env:PYTHONDONTWRITEBYTECODE="1"
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -B -m pytest tests\unit -q -p no:cacheprovider --basetemp D:\Codex\FinancialFilingDataFoundation\worktrees\t\v
```

Result:

```text
368 passed in 25.18s
FULL_EXIT=0
```

P10-C exact candidate baseline had 339 passing unit tests.
P10-D adds 29 passing context tests with no previous-stage regression.

## 10. Compile / import

Compile:

```text
python -B -m compileall -q src\financial_filing_data_foundation\research tests\unit\research
COMPILE_EXIT=0
```

Exact-candidate import:

```text
IMPORT_OK
D:\Codex\FinancialFilingDataFoundation\worktrees\active\p10-dynamic-research-design\src\financial_filing_data_foundation\research\__init__.py
D:\Codex\FinancialFilingDataFoundation\worktrees\active\p10-dynamic-research-design\src\financial_filing_data_foundation\research\context.py
p10-research-context-v1
p10-dynamic-research-v1
```

The production fingerprint probe returned exactly:

```text
bbeb600e732d5ca567193602d2a2b067fcedeabf9cb5d7cfdf5598671c267bc8
9b7a1078ab2365862dc5061c3b2a76a43f865553eb4df5938b96ffe9bbd4ff36
30df28e273379e91c245222b751aaab1504b6c725ca4170a8fb6168082735935
```

## 11. Scope / security

`git diff --check 8fd2604..c8b4041`:
**PASS**

P8/P9 source/test diff:
`NONE`

Dependency/runtime diff:
`NONE`

Forbidden P10 research production surface scan:
`NONE`

No:

- external MCP SDK import
- dedicated `mcp/server.py` import
- network client
- OpenAI/Codex/remote AI API
- subprocess/shell
- SQL execution
- Research MCP production
- Semantic Resolver production
- P11 production

## 12. Encoding

The three candidate paths decode as UTF-8 and contain no UTF-8 BOM:

- `research/context.py`
- `research/__init__.py`
- `test_research_context.py`

Repository Windows line-ending canonicalization warnings do not affect the Git blobs; `git diff --check` passed.

## 13. Final candidate state

Implementation candidate:

`c8b4041c2d06e1d601707ca765ddd9e817f0dfc9`

Remote branch matched this exact candidate during candidate verification.

No production/test/runtime artifact was modified after the exact-candidate verification.

## 14. Gate verdict

# PASS — P10-D CANDIDATE READY FOR REVIEW

P10-D implementation candidate is complete.

P10-E remains closed until P10-D receives an independent detached Code Review PASS and a later explicit authorization.

Research MCP production, Semantic Resolver production, and P11 production remain closed.
