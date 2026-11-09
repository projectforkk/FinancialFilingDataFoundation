# P11 SEC Review Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repair the reviewed P11 US SEC provider so fiscal slots, structured facts, HTTP safety, evidence round-trips, raw-package trust, and XBRL scope are deterministic and fail closed.

**Architecture:** Keep the stdlib-only SEC path and accepted CN/HK/P8 contracts. Add official fiscal-year-end metadata and chronology-based slot resolution, source-aware HTML/XML fact extraction, bounded HTTP behavior, and deterministic raw-package verification at P8 load time.

**Tech Stack:** Python standard library, pytest, SQLite-backed registry, JSON/JSONL artifacts, existing P8 catalog/service.

**Spec:** `development/149-p11-code-review-result.md` and the repair execution instruction supplied with this task.

## Global Constraints

- Do not mutate original filing bytes or accepted CN/HK artifacts.
- Do not add remote AI/API calls or third-party SEC/XBRL runtime dependencies.
- Keep US behind `FFDF_P11_US_DEV=1` and keep P8 tool names unchanged.
- Do not merge `main`, force-push, or run formal acceptance.
- Every new positive path must retain immutable member identity and source evidence.

## Review Focus

- A September/52-week fiscal year must map Q1–FY by fiscal-year-end metadata and chronology, not calendar months.
- Empty periodic structured extraction and facts without evidence must never publish as research-ready.
- Redirect hops, non-SEC redirects, HTTP error bodies, and unsupported encodings must fail within configured bounds.
- HTML and XML evidence must resolve against the exact member bytes, including block and locator integrity.
- P8 must re-read the content-addressed package so tampering after ingest fails closed.

### Task 1: Fiscal-slot discovery

**Files:**
- Modify: `src/financial_filing_data_foundation/us_sec/discovery.py`
- Modify: `src/financial_filing_data_foundation/us_sec/acquisition.py`
- Test: `tests/unit/us_sec/test_http_discovery.py`

- [ ] Add metadata/chronology fixtures for December, September, 52/53-week, and FPI non-December issuers.
- [ ] Replace month mapping and calendar-year prefix checks with fiscal-year-end classification and ordered quarterly slots.
- [ ] Run focused discovery tests.

### Task 2: HTTP contract and redirect limits

**Files:**
- Modify: `src/financial_filing_data_foundation/us_sec/errors.py`
- Modify: `src/financial_filing_data_foundation/us_sec/http.py`
- Modify: `src/financial_filing_data_foundation/us_sec/runtime.py`
- Modify: `src/financial_filing_data_foundation/us_sec/runner.py`
- Test: `tests/unit/us_sec/test_http_discovery.py`

- [ ] Stop advertising gzip unless decoding exists; reject unexpected content encodings.
- [ ] Wire `max_redirects` through the network and subprocess transports, preserve per-hop allowlisting, and bound HTTPError reads.
- [ ] Run encoding, redirect, and bounded-body tests.

### Task 3: Source-aware parser and validation

**Files:**
- Modify: `src/financial_filing_data_foundation/us_sec/errors.py`
- Modify: `src/financial_filing_data_foundation/us_sec/parser.py`
- Modify: `src/financial_filing_data_foundation/us_sec/validation.py`
- Modify: `src/financial_filing_data_foundation/us_sec/ingest.py`
- Test: `tests/unit/us_sec/test_parser.py`
- Test: `tests/unit/us_sec/test_validation_p8.py`

- [ ] Make HTML Evidence reference an actual normalized page block and retain a separate fact locator/fragment hash.
- [ ] Add deterministic XML instance fact extraction with XML locators, contexts, units, numeric candidates, nil/custom QName preservation, and duplicate source retention.
- [ ] Validate HTML/XML locators, block identity, source member hash, fragment hash, fact/evidence coverage, and periodic zero-fact completeness.
- [ ] Make `research_ready` require a true PASS with complete structured facts/evidence.
- [ ] Run parser/validation tests, including deliberately corrupted anchors.

### Task 4: Trusted raw package at P8

**Files:**
- Modify: `src/financial_filing_data_foundation/mcp/service.py`
- Modify: `tests/unit/us_sec/test_validation_p8.py`

- [ ] Resolve the standard project-root-relative raw-store path from the catalog project root.
- [ ] Verify package manifest, package identity, every member hash/size, and every Evidence member before serving SEC bundles.
- [ ] Revalidate on cached bundle access so post-ingest tamper/delete fails closed.
- [ ] Run P8 positive and tamper tests.

### Task 5: Evidence and regression evidence

**Files:**
- Modify/Create: `tests/unit/us_sec/*` as needed for the above groups.
- Create: `development/150-p11-repair-development-evidence.md` (or next free number).

- [ ] Run P11 focused tests, full unit suite, CN/HK regression, compileall, and `git diff --check` with a short temporary path.
- [ ] Commit production code and tests as the frozen new candidate.
- [ ] Record exact candidate SHA, issue-by-issue evidence, full commands/results, and safety declarations in a separate evidence commit.
- [ ] Push `task/p11-sec-rebuild-development`; do not run formal acceptance.
