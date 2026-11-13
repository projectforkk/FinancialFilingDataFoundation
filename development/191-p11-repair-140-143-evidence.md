# P11-ISSUE-140..143 Repair Development Evidence

Status: **DEVELOPMENT EVIDENCE ONLY / READY FOR FRESH EXACT-CANDIDATE DESIGN-CODE REVIEW**

This document records the repair candidate and development verification. It is
not a Formal Test Plan, Formal Acceptance, merge authorization, REVIEW_PASS, or
P11 DONE record.

## 1. Exact authority and candidate identity

- Repository: `projectforkk/FinancialFilingDataFoundation`
- Branch: `task/p11-sec-rebuild-development`
- Worktree: `D:\Codex\FinancialFilingDataFoundation\worktrees\active\p11-sec-rebuild-development`
- Starting HEAD for this repair wave: `adac1075a71881dc5aec41049ead3b03d1933d4c`
- Original corrected design baseline: `09e3174b7e19a60cc5955862670fac8931af67db`
- Pre-repair current design freeze: `4bf644374af3a0585453379fcc185d6464105776`
- Previous CHANGES_REQUIRED production candidate: `55fc575cdaaeebd8b686ce76120978c714ca1a28`
- Fresh exact-candidate review: `development/190-p11-fresh-full-exact-candidate-review-4.md`
- Review commit: `adac1075a71881dc5aec41049ead3b03d1933d4c`
- New design correction: `design/35-p11-repair-140-143-design-correction.md`
- New design correction/freeze is included in candidate:
  `a65723c3cf17bbccf10748e2c671671a2c7dfb1b`
- New production candidate: `a65723c3cf17bbccf10748e2c671671a2c7dfb1b`
- Candidate commit message: `fix: repair P11 compatibility and SEC trust boundaries`

The design correction was written before the implementation changes. It freezes
the V6 compatibility boundary, namespace-authentic semantic references, a
shared complete-but-minimal history selector, and independent P7 fact-source
semantic invariants. CN/HK accepted behavior, the original SEC package bytes,
and the P8 governance boundary were not changed.

## 2. Repair disposition

- P11-ISSUE-140: **IMPLEMENTED** — namespace-semantic parser meaning is now
  identified as `VIRTUAL_HTML_V6`; V5/v2 parsed artifacts cannot qualify for
  `REUSE_DATA`, while the immutable raw package remains reusable for
  `PARSE_LOCAL`.
- P11-ISSUE-141: **IMPLEMENTED** — HTML and XML semantic references require the
  authentic XBRL linkbase namespace and XLink namespace URI, with arbitrary
  legal prefixes supported and wrong/unbound lookalikes rejected.
- P11-ISSUE-142: **IMPLEMENTED** — online discovery and P7 reconstruction share
  one deterministic history selector; ancient ranges are excluded only when
  their valid `filingTo` proves irrelevance, missing metadata is retained
  conservatively, and all selected chunks are processed before slot decision.
- P11-ISSUE-143: **IMPLEMENTED** — P7 independently verifies the persisted
  `fact_source_mode` against package member identity, locator model, source
  hashes, authentic source nodes, and the zero-fact rule for
  `NO_STRUCTURED_FACTS`.

## 3. Compatibility and immutability contract

| Contract | Value |
|---|---|
| `VIRTUAL_HTML_NORMALIZER_VERSION` | `VIRTUAL_HTML_V6` |
| `SEC_ARTIFACT_SCHEMA` | `p11-sec-artifacts-v2` |
| `SEC_VALIDATION_SCHEMA` | `p11-sec-validation-v2` |
| `SEC_REGISTRY_SCHEMA_VERSION` | `4` |
| Legacy CN/HK artifact/registry versions | unchanged (`1`) |

The dedicated repair suite proves that a legacy
`<package_sha256>.VIRTUAL_HTML_V5` artifact with the existing v2 manifest is
incompatible, the V6 parser executes and writes a separate V6 directory, the
old manifest hash is unchanged, the raw package is reused, and the operation
is `PARSE_LOCAL` with no archive fetch. A legacy V5/v2 Registry row also cannot
select `REUSE_DATA`.

## 4. Development verification

All commands ran from the candidate worktree with
`PYTHONPATH=<worktree>\src`, `PYTHONUTF8=1`, and the project-local Python
runtime. The test basetemp directories were outside the repository. No test
was skipped.

Focused repair suite:

```text
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -m pytest -q --basetemp D:\ffdf-final-r140-143 tests/unit/us_sec/test_repair_140_143.py
23 passed in 0.40s
EXIT=0
```

US SEC regression:

```text
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -m pytest -q --basetemp D:\ffdf-final-ussec-r140-143 tests/unit/us_sec
196 passed in 16.75s
EXIT=0
```

MCP/P8 regression:

```text
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -m pytest -q --basetemp D:\ffdf-final-mcp-p8-r140-143 tests/unit/mcp tests/unit/us_sec/test_validation_p8.py tests/unit/us_sec/test_package_registry.py
91 passed in 8.71s
EXIT=0
```

P0-P10 focused regression:

```text
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -m pytest -q --basetemp D:\ffdf-final-p0-p10-r140-143 tests/unit/acquisition tests/unit/identity tests/unit/validation tests/unit/registry tests/unit/mcp tests/unit/research tests/unit/review
371 passed in 80.67s
EXIT=0
```

Full unit regression:

```text
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -m pytest -q --basetemp D:\ffdf-final-full-unit-r140-143 tests/unit
726 passed in 88.57s
EXIT=0
```

Static checks:

- `python -m compileall -q src`: **PASS / EXIT=0**
- `git diff --check`: **PASS / EXIT=0** before candidate freeze
- candidate diff check `git diff --check HEAD^ HEAD`: **PASS / EXIT=0**
- candidate worktree immediately after the production candidate commit:
  **clean**

## 5. Apple FY2025 isolated live developer smoke

The production `user_cli` ingest path was run against a new isolated root with
the following exact CLI arguments:

```text
FFDF_ROOT=D:\ffdf-p11-repair-140-143-live-20261113-v1
ingest --market US --cik 320193 --ticker AAPL --year 2025 --period FY
```

The invocation used the project-local Python entry point and only wrapped the
SEC transport method to record request URLs; acquisition, parsing, validation,
Registry, and P8 execution remained the production code path.

`FFDF_P11_US_DEV` was absent. The CLI returned exit code 0 with:

```text
accession: 0000320193-25-000079
package_sha256: 079185e72f20bd4fc1a2a19b2c57430390b2fb5482403b51752525a0264ff131
validation_status: PASS
blocking_issue_count: 0
review_issue_count: 0
p8_catalog: ADDED
research_ready: true
artifact_dir: ...079185e72f20bd4fc1a2a19b2c57430390b2fb5482403b51752525a0264ff131.VIRTUAL_HTML_V6
CLI_EXIT=0
SMOKE_EXIT=0
```

The transport trace was captured around the production CLI path without
changing production behavior. It made 9 SEC requests: 1 current submissions
request, 0 history requests, and 8 exact-accession archive requests. The exact
request URLs were:

```text
https://data.sec.gov/submissions/CIK0000320193.json
https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/index.json
https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm
https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.xsd
https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/FilingSummary.xml
https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927_cal.xml
https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927_def.xml
https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927_lab.xml
https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927_pre.xml
```

The current submissions response listed exactly one history descriptor:

```text
CIK0000320193-submissions-001.json
filingFrom=1994-01-26
filingTo=2015-10-05
```

For FY2025 the selector cutoff is `2025-01-01`; this descriptor was therefore
correctly excluded. No history chunk was fetched, and the persisted discovery
observation contains only the current submissions source:

```text
observation_sha256: b2ceb298377abf7402dc0db8da4182e347c60ce8ede1a868f662d01dc463d7f2
state: UNAMBIGUOUS
source_documents: 1
source_url: https://data.sec.gov/submissions/CIK0000320193.json
```

The live package contained:

- 1 `PRIMARY_DOCUMENT`: `aapl-20250927.htm`;
- 1 `FILING_SUMMARY`: `FilingSummary.xml`;
- 1 XBRL schema: `aapl-20250927.xsd`;
- 4 XBRL linkbases: calculation, definition, label, and presentation;
- 0 XBRL instance members;
- 0 static assets (no JPEG, JPG, PNG, GIF, or SVG request).

The V6 artifact manifest reports `fact_source_mode=INLINE_XBRL_PRIMARY`,
`fact_count=1131`, `issue_count=0`, and `table_count=62`. P7 reports
`PASS`, 0 blocking issues, and 0 review issues. P8 reports `ADDED` and the
CLI reports `research_ready=true`.

## 6. Governance boundary and handoff

- Formal Test Plan created: **NO**
- Formal acceptance executed: **NO**
- Main merge performed: **NO**
- `REVIEW_PASS` declared: **NO**
- P11 DONE claimed: **NO**
- Source/test/design modified after candidate freeze: **NO**
- Work after candidate freeze: documentation-only evidence preparation
- Evidence commit: the dedicated documentation-only child of
  `a65723c3cf17bbccf10748e2c671671a2c7dfb1b`; its SHA is recorded in the
  final handoff

Next required action:

```text
CHATGPT FRESH FULL EXACT-CANDIDATE DESIGN/CODE REVIEW OF a65723c3cf17bbccf10748e2c671671a2c7dfb1b
```
