# P11-ISSUE-133 SEC Acquisition Reference Policy Repair Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop primary-document browser/static references from authorizing SEC archive downloads while preserving explicitly identified filing/XBRL support references.

**Architecture:** Keep the repair at the deterministic archive-member selection boundary in `us_sec/acquisition.py`. Recognized EX-101 metadata and FilingSummary selection remain unchanged; primary HTML references are admitted only when the corresponding index metadata explicitly identifies a semantic XBRL/support member. HTTP MIME validation, path policy, package hashing, provenance and parser semantics remain unchanged.

**Tech Stack:** Python standard library, `SecAcquirer`, `SecHttpClient`, pytest, JSON archive-index fixtures, SQLite/package store only through existing test helpers.

**Spec:** `design/26-p11-sec-provider-design.md` §7.3, `development/183-p11-formal-test-plan-3.md` FT-08/FT-10, and the P11-ISSUE-133 repair request.

## Global Constraints

- Do not modify or amend `9389d59d68c84762b55b29bedb973db4ea45256a`.
- `P11-ISSUE-133` remains OPEN/BLOCKING until the new candidate is reviewed.
- Do not globally allowlist `image/jpeg` or weaken MIME/path/size/security validation.
- Do not sweep all `.xml`, `.xbrl` or `.xsd` files by extension alone.
- Do not execute JavaScript or fetch arbitrary browser subresources.
- Preserve package SHA, Registry package provenance, raw-store immutability and schema/version constants.
- Do not create a Formal Test Plan for the new candidate; Formal Acceptance is not run in this cycle.
- No source/test changes after the new production candidate is frozen; the next commit is documentation-only evidence.

## Review Focus

- A referenced JPEG/PNG/GIF/CSS/JS/font must remain unselected and unfetched; test with all five extensions.
- A referenced semantic XBRL support member must still be selected only with explicit index metadata; test a positive reference-based inclusion.
- A referenced generic XML member must not be selected merely because it is XML; test the existing unrelated-XML exclusion.
- Unsafe or external primary references must not escape the accession root or trigger transport calls; test traversal, absolute, external, `javascript:` and `data:` forms.
- Recognized EX-101 members must remain selected independently of primary HTML references; preserve the existing incremental acquisition test.

### Task 1: Failure evidence and candidate freeze boundary

**Files:**
- Create: `development/185-p11-formal-test-evidence-3.md`
- Create: this plan file
- Test: none

- [ ] **Step 1: Record the failed formal execution**

Record candidate `9389d59d68c84762b55b29bedb973db4ea45256a`, Plan 183, Prompt 184, FT-00–FT-09 PASS, FT-10 FAIL, FT-11–FT-15 BLOCKED, Apple accession `0000320193-25-000079`, observation SHA `684038711efc8eef02b3540cc2aca7f5edda55987727da08cd4c15932b700dd0`, member `aapl-20250927_g1.jpg`, actual MIME `image/jpeg`, reason `P11_CONTENT_TYPE_INVALID`, and execution stop boundary.

- [ ] **Step 2: Commit failure evidence only**

Run `git diff --check`, stage only the plan and failure evidence, and commit `docs: record P11 formal test execution 3 failure`. No production or test path may be staged.

### Task 2: Red regression tests for reference selection

**Files:**
- Modify: `tests/unit/us_sec/test_provider_cli.py` or create a focused acquisition-policy test beside it
- Test: the deterministic fake SEC transport and package assertions named below

- [ ] **Step 1: Add the failing Apple-JPEG/static-asset reproduction**

Create one archive-index fixture with primary HTML referencing `aapl-20250927_g1.jpg`, `style.css`, `script.js`, `graphic.png`, `graphic.gif`, and `font.woff2`; include each in `index.json`. The transport must raise if any asset URL is requested. Assert the acquisition succeeds, primary and required semantic members are present, every asset fetch count is zero, and no asset is a package member.

- [ ] **Step 2: Add the failing semantic reference-positive case**

Create a primary HTML reference to a filing-local support member whose index metadata explicitly declares a semantic XBRL role (for example `XBRL_INSTANCE` or an equivalent reviewed metadata value). Assert it is selected, fetched once, assigned the expected role, and included in valid package provenance.

- [ ] **Step 3: Add unsafe-reference non-fetch assertions**

Include traversal, absolute, external-host, `javascript:` and `data:` references in primary HTML with matching or nonmatching index entries. Assert none produces an archive fetch or package member.

- [ ] **Step 4: Run the new tests before production changes**

Run the focused tests and confirm they fail because ordinary primary references are still selected by the current implementation. Fix fixture/test errors until the failure is the expected policy failure.

### Task 3: Minimal production selection repair

**Files:**
- Modify: `src/financial_filing_data_foundation/us_sec/acquisition.py`
- Test: the red tests from Task 2 and the existing acquisition regression suite

- [ ] **Step 1: Implement explicit semantic reference filtering**

Change only `_select_archive_members()` and small local helpers if needed. Preserve primary, recognized EX-101 and FilingSummary selections. For references discovered from the primary body, admit only canonical filing-local names whose index metadata explicitly marks a semantic XBRL/support role; ignore ordinary browser/static references and generic XML metadata.

- [ ] **Step 2: Run the focused tests to green**

Run the new focused acquisition-policy tests and the existing `test_sec_acquirer_downloads_primary_and_xbrl_members_incrementally` test. Confirm static assets are not fetched and explicit semantic support still is.

- [ ] **Step 3: Run the security and acquisition regressions**

Run `tests/unit/us_sec/test_provider_cli.py` and `tests/unit/us_sec/test_http_discovery.py`; confirm path, host, MIME, size and retry behavior remains unchanged.

### Task 4: Candidate verification and evidence

**Files:**
- Modify: none after candidate freeze
- Create after freeze: `development/186-p11-live-ft10-acquisition-repair-evidence.md`

- [ ] **Step 1: Run required developer verification**

Run the exact provider/acquisition-focused, US SEC, full-unit, P0–P10, compileall and diff-check commands from the repair request. Record exact counts and exit codes.

- [ ] **Step 2: Run the Apple live developer smoke when configured**

With `FFDF_P11_US_DEV` absent, run Apple FY2025 FY acquisition in the isolated disposable root if `FFDF_SEC_CONTACT_EMAIL` is configured. Record only configured YES/NO, accession and package-member selection; never record the contact value.

- [ ] **Step 3: Freeze one production/test candidate**

Commit source and regression tests once as `fix: restrict SEC reference acquisition to filing semantic members`. Do not modify source/tests afterward.

- [ ] **Step 4: Write and commit documentation-only evidence**

Create `development/186-p11-live-ft10-acquisition-repair-evidence.md`, run final diff checks, commit `docs: record P11 live FT10 acquisition repair evidence`, push normally, verify the remote candidate/evidence lineage, and stop before Formal Acceptance.

## Completion Contract

- The old candidate remains unchanged and historical.
- The new candidate passes developer tests and explicitly proves static assets are not fetched.
- Candidate → evidence contains documentation only.
- Formal Test Plan = NOT CREATED for the new candidate.
- Formal Acceptance = NOT RUN for the new candidate.
- Main merge = NOT RUN.
- P11 DONE = NO.
