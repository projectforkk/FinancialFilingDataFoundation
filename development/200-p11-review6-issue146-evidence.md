# P11 Review 6 ISSUE-146 Development Evidence

## Status

This is development evidence only. The implementation is stopped at the exact
candidate handoff for fresh ChatGPT review. No design file was modified, no
formal test plan was created, no formal acceptance was run, and no main-branch
merge was performed.

## Authority and exact lineage

| Item | Value |
| --- | --- |
| Repository | `projectforkk/FinancialFilingDataFoundation` |
| Worktree | `D:\Codex\FinancialFilingDataFoundation\worktrees\active\p11-sec-rebuild-development` |
| Authorized remote | `origin/reconcile/p11-140-143-local-chain` |
| Design 38 freeze | `92af6205eb8e090994dcece68850eddcd4232392` |
| Development authorization | `48ff2dc3ff3219fe6811b2ce4a169bf7b480e00e` |
| Authorization document | `development/199-p11-review6-development-reauthorization.md` |
| Prior production candidate | `35e2b70c78b6cff931c8484dc38f2eb7349735f5` |
| Prior evidence commit | `93027f60be96f3998fb041ac6ad65bcf31c55834` |
| New production candidate | `6eaace08c9ba5fb26809a7e02de5835123fb667a` |

The new candidate was created as a normal child of the development
authorization and pushed normally to the authorized remote. Source and test
paths were frozen after this candidate. This evidence commit is documentation
only and follows the candidate.

## ISSUE-146 implementation scope

The candidate implements only the frozen validation-v3 revalidation planner
correction:

- `SecPlanAction.REVALIDATE_LOCAL` is selected when compatible V6/v2 parsed
  artifacts exist but current validation-v3 is absent or not reuse-eligible.
- Parsed compatibility is evaluated independently from current validation-v3
  reuse eligibility.
- A present but corrupt current validation-v3 remains fail-closed through the
  existing `P11_PACKAGE_INVALID` loader path; legacy flat v2 is never a
  fallback and the parser is not called.
- `REVALIDATE_LOCAL` loads the existing parsed artifact, validates directly,
  writes versioned v3, preserves raw/package/parsed/legacy-v2 bytes, refreshes
  the slot and P8 catalog, and updates the existing parse-run Registry row.
- `REUSE_DATA` fresh validation now also refreshes the same parse-run Registry
  fields using `sha256(package_sha256 + "|" + parser_version)`.

Frozen identifiers remain unchanged:

```text
SEC_DISCOVERY_SCHEMA = p11-sec-discovery-v1
VIRTUAL_HTML_NORMALIZER_VERSION = VIRTUAL_HTML_V6
SEC_ARTIFACT_SCHEMA = p11-sec-artifacts-v2
SEC_VALIDATION_SCHEMA = p11-sec-validation-v3
SEC_REGISTRY_SCHEMA_VERSION = 4
```

Candidate source/test paths:

```text
src/financial_filing_data_foundation/us_sec/ingest.py
src/financial_filing_data_foundation/us_sec/planner.py
src/financial_filing_data_foundation/user_cli.py
tests/unit/us_sec/test_issue146.py
tests/unit/us_sec/test_package_registry.py
```

No design path was changed.

## Deterministic verification at exact candidate

The required migration, corruption, reuse-refresh, planner matrix, and Review 5
regression tests passed:

```text
tests/unit/us_sec/test_issue146.py             9 passed
tests/unit/us_sec                               253 passed
tests/unit                                      783 passed
python -m compileall -q src tests               exit 0
git diff --check                                exit 0
```

The first full-unit attempt used a longer temporary root and hit the known
Windows path-length failure in unrelated deep P9/SEC temporary paths. It had
19 path-construction failures and 764 passes. The exact candidate was then
rerun with the shorter project-local temporary root
`D:\Codex\FinancialFilingDataFoundation\w\u` and passed 783/783. No source
or test change was made to obtain that pass. The temporary root was removed
after verification.

The complete US SEC result includes the focused Review 5 regressions:

```text
tests/unit/us_sec/test_package_registry.py        18 passed
tests/unit/us_sec/test_cli_runtime.py             12 passed
tests/unit/us_sec/test_issue131.py                15 passed
tests/unit/us_sec/test_repair_140_143.py          69 passed
tests/unit/us_sec/test_validation_p8.py           10 passed
```

## Apple FY2025 developer smoke

The normal production CLI path was run at exact candidate
`6eaace08c9ba5fb26809a7e02de5835123fb667a` with `FFDF_P11_US_DEV` absent and
isolated root:

```text
D:\Codex\FinancialFilingDataFoundation\work\review6-live-20261115
```

Command:

```text
python -m financial_filing_data_foundation.user_cli ingest --market US --cik 320193 --ticker AAPL --year 2025 --period FY
```

Observed result:

```text
planner_action: DISCOVER_AND_ACQUIRE
accession: 0000320193-25-000079
package_sha256: 1196a354461ac65afa4ce7f1c67b2d65b04c1e496f521f34a139c6d6e5872d3d
discovery_observation_sha256: a17eeff0d7e52d1ff9abfcff20c62fb545f28568facbf6a3153405ee021c7e32
discovery_state: UNAMBIGUOUS
fact_source_mode: INLINE_XBRL_PRIMARY
fact_count: 1131
validation_schema: p11-sec-validation-v3
validation_status: PASS
blocking_issue_count: 0
review_issue_count: 0
p8_catalog: ADDED
research_ready: true
```

The validation artifact is below the versioned current-v3 path under the
isolated smoke root. The raw package and V6 parsed artifact were created in
that isolated root; this smoke was not a formal acceptance run.

## MCP stdio smoke

The fixed MCP stdio smoke passed using the existing compatible
`runtimes\ffdf-mcp-2.3.0\.venv` (Python 3.12.14) and the repository's two-document
acceptance catalog. The current 70-document live catalog was not modified.

Observed result:

```text
protocol_version: 2026-07-28
document_count: 2
tool_count: 26
CN/HK list, document, search, pages, sections, tables, facts, evidence, and
validation calls: PASS
invalid document handling: PASS
```

The untracked smoke receipt was written under:

```text
D:\Codex\FinancialFilingDataFoundation\work\review6-mcp-smoke-acceptance.json
```

The acceptance fixtures preserve their own `REVIEW_REQUIRED` validation states;
the smoke verifies MCP routing and evidence relationships, not a new P11
acceptance decision.

## Governance boundary

```text
FORMAL TEST PLAN: NOT CREATED / NOT AUTHORIZED
FORMAL TEST EXECUTION: NOT AUTHORIZED
FORMAL ACCEPTANCE: NOT RUN
MAIN MERGE: NOT AUTHORIZED
P11 DONE: NO
REVIEW_PASS: NOT DECLARED
STOP FOR CHATGPT FRESH FULL EXACT-CANDIDATE REVIEW
```

Candidate-to-evidence scope:

```text
candidate: 6eaace08c9ba5fb26809a7e02de5835123fb667a
candidate -> evidence: development/200-p11-review6-issue146-evidence.md only
CANDIDATE -> EVIDENCE: DOCUMENTATION ONLY — YES
```
