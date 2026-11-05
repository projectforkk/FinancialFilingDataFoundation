# 113 — FFDF公司财报下载 Skill Acceptance

## Candidate

Design commit:

`5268099 design: define FFDF company filing download skill`

Implementation commit:

`a9b9d01 feat: add FFDF company filing download skill`

## Delivered Skill

Path:

`.agents/skills/FFDF公司财报下载/`

Files:

- `SKILL.md`
- `agents/openai.yaml`

Static contract test:

- `tests/unit/skills/test_ffdf_company_filing_download_skill.py`

## Parameter Contract

Exactly two logical parameters:

1. `company_code`
2. `year_or_range`

Invocation:

`$FFDF公司财报下载 <company_code> <year_or_range>`

Examples:

`$FFDF公司财报下载 605117 2021`

`$FFDF公司财报下载 605117 2021-2026`

## Market inference

Deterministic:

- exactly 6 numeric digits -> CN
- 1-5 numeric digits -> HK, left-pad to 5 digits
- otherwise fail closed

No company-name inference and no model use.

## Year expansion

Supported:

- `YYYY`
- `YYYY-YYYY` inclusive

The Skill does not expand beyond the requested interval.

## Filing orchestration

For every requested year, fixed period order:

`Q1 -> H1 -> Q3 -> FY`

Each slot calls the existing FFDF ingest path:

`ffdf ingest --market <market> --ticker <ticker> --year <year> --period <period>`

No duplicate downloader/parser implementation was introduced.

Existing ingest remains responsible for:

Acquire -> Raw Store -> Registry -> P3 -> P4 -> P5 -> P6 -> P7 -> Parsed Registry -> P8 live catalog when non-blocking.

## Gap / error behavior

Locked statuses include:

- INGESTED
- REUSED_LOCAL
- NOT_FOUND
- FUTURE_WINDOW_NOT_STARTED
- REVIEW_REQUIRED
- BLOCKED
- INGEST_BLOCKED
- ERROR

NOT_FOUND does not fabricate a filing.

FUTURE_WINDOW_NOT_STARTED is treated as a non-error gap and does not force an overridden publication window.

P7 blocking > 0 is never reported as successful P8 publication.

## Focused test

`tests/unit/skills/test_ffdf_company_filing_download_skill.py`

Result:

**9 PASS / 0 FAIL**

Coverage includes:

- Skill and agent files
- exact two-parameter contract
- single-year and year-range forms
- deterministic CN/HK inference
- fixed period order
- existing ffdf ingest pipeline
- incremental REUSED_LOCAL behavior
- non-blocking P8 publication boundary
- NOT_FOUND behavior
- future publication-window behavior
- no AI / destructive bypass
- explicit Skill invocation UI

## Full FFDF unit regression

Command used short Windows-safe basetemp.

Result:

**523 PASS / 0 FAIL**

## Scope / safety

This change does not modify:

- acquisition provider implementation
- Registry behavior
- Raw Store
- P3/P4/P5/P6/P7 parsers
- P8 MCP production contract
- P9
- Research Review MCP

It adds Codex orchestration only.

The Skill does not:

- call AI models
- call external AI APIs
- replace CNINFO/HKEX providers with web downloads
- alter official PDFs
- force publication windows
- perform destructive Git operations

## Git hygiene

Existing untracked directories remain untouched:

- `00document/`
- `01prompt/`

## Verdict

**ACCEPTANCE: PASS**

The `FFDF公司财报下载` Skill is ready for merge to main and Git-managed use.
