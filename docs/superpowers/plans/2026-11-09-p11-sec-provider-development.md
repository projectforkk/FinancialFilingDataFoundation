# P11 US SEC Provider Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the gated P11 US SEC provider candidate from the accepted `c970d63c2699d016c1696451d2a66fc42850b4f1` design baseline without changing accepted CN/HK production behavior.

**Architecture:** Add a source-aware `us_sec` package. The main FFDF runtime owns identity, Registry, planning, artifact orchestration, and the read-only P8 route; a stdlib-only subprocess runner owns controlled SEC HTTP/HTML/XML work. SEC filings are immutable packages keyed by deterministic member manifests, and their artifacts are lazy-loaded by the existing P8 tool family.

**Tech Stack:** Python stdlib (`urllib`, `html.parser`, `xml.etree`, `sqlite3`, `hashlib`), existing FFDF/PyMuPDF main runtime, pytest, JSONL artifacts, SQLite schema v2, Windows subprocess boundary.

**Spec:** `design/26-p11-sec-provider-design.md`, `design/27-p11-implementation-plan.md`, `design/32-p11-us-scope-reopening.md`, `development/147-p11-us-scope-reopening-authorization.md`, and `docs/superpowers/specs/2026-11-09-p11-sec-provider-development-design.md`

## Global Constraints

- `SUPPORTED_MARKETS` remains exactly `("CN", "HK")` until independent P11 acceptance; US is development-only behind `FFDF_P11_US_DEV=1`.
- `MCP_AI_API_CALLS = FORBIDDEN`; no OpenAI, Anthropic, Gemini, Codex API, MCP sampling, or remote LLM call enters FFDF code.
- `ORIGINAL_DOCUMENT_IMMUTABLE`, `NO_GUESSING`, `EVIDENCE_REQUIRED`, and `INCREMENTAL_FIRST` remain hard rules.
- Official acquisition hosts are SEC hosts only; callers cannot provide arbitrary URLs, and redirect hosts are revalidated.
- User-Agent contact information is configuration/environment injected; no private email is committed to source.
- Shared SEC limiter defaults to 8 requests/second; retries are bounded and deterministic; submissions/member/package limits are 32 MiB/128 MiB/512 MiB.
- CN/HK period policy remains Q1/H1/Q3/FY; US alone supports Q1/Q2/Q3/FY and FPI annual 20-F/40-F.
- P8 keeps the exact accepted 11 tool names and remains local, read-only, no-network, and no-acquisition.
- No canonical metric mapping, fiscal-period guessing, YoY/QoQ/TTM, valuation, or investment analysis is added to extraction.
- No destructive Git operation, force push, main merge, Raw/P3-P10 artifact deletion, or history rewrite is allowed.

## Review Focus

- A redirect or archive member with a lookalike/non-SEC host must fail closed; owned by Task 2 tests.
- The same accession/member URL returning different bytes must produce source drift and never overwrite a package; owned by Task 3 tests.
- Inline XBRL with custom concepts and unresolved context/unit references must retain raw evidence while producing explicit validation issues; owned by Task 4/5 tests.
- A package with an amendment and original in one required slot must be `REVIEW_REQUIRED`, not silently selected; owned by Task 2/3 tests.
- The public CLI must reject US by default and accept Q2 only under the explicit development gate; owned by Task 6 tests.

---

### Task 1: US identity, policy, reason codes, and feature gate

**Files:**
- Modify: `src/financial_filing_data_foundation/identity/models.py`, `src/financial_filing_data_foundation/identity/__init__.py`
- Create: `src/financial_filing_data_foundation/us_sec/__init__.py`, `us_sec/errors.py`, `us_sec/identity.py`, `us_sec/policy.py`, `us_sec/models.py`, `us_sec/feature_gate.py`
- Test: `tests/unit/us_sec/test_identity_policy.py`

**Interfaces:**
- Consumes: existing `CompanyRef`, `FilingSlotKey`, `FilingIdentity`, `SUPPORTED_MARKETS`.
- Produces: `SecCompanyRef`, `SecFilingSlot`, `SecFilingCandidate`, `SecFormPolicy`, `P11Reason`, `is_us_development_enabled()`, and explicit CIK/ticker normalization used by later tasks.

- [ ] **Step 1: Write failing tests** for CIK normalization, exact ticker ambiguity, US CIK company identity, domestic Q1/Q2/Q3/FY form mapping, annual 20-F/40-F mapping, unsupported FPI quarterly mapping, amendment flags, and default-disabled feature gate.
- [ ] **Step 2: Run `pytest tests/unit/us_sec/test_identity_policy.py -q`** and confirm failure because the new US module/types are absent.
- [ ] **Step 3: Implement** the additive models and policy. Existing identity constructors remain CN/HK by default; a separate explicit development allowance is required for US slots and `SUPPORTED_MARKETS` is unchanged.
- [ ] **Step 4: Run the focused test and the existing identity tests**; expected: all new tests and prior identity tests pass.
- [ ] **Step 5: Commit** `feat: add gated US SEC identity and filing policy`.

### Task 2: SEC HTTP fair access and filing discovery

**Files:**
- Create: `src/financial_filing_data_foundation/us_sec/http.py`, `us_sec/discovery.py`, `us_sec/ticker_map.py`
- Test: `tests/unit/us_sec/test_http_discovery.py`

**Interfaces:**
- Consumes: Task 1 policy/models and injected transport fixtures.
- Produces: `SecHttpClient`, `SecHttpConfig`, `SecRateLimiter`, `SecDiscovery`, `discover_filings()`, and deterministic candidate selection/error outcomes.

- [ ] **Step 1: Write failing tests** for configured User-Agent/contact, 8 req/s limiter, bounded 429/403/Retry-After retry, max response size, allowed SEC hosts, redirect rejection, submissions parsing, historical chunk selection, Q2, amendment conflict, not-found, ambiguous ticker, and FPI quarterly fail-closed behavior.
- [ ] **Step 2: Run the focused test and verify expected red failures.**
- [ ] **Step 3: Implement** guarded stdlib HTTP with TLS verification, bounded retries, and no arbitrary caller URL; parse submissions JSON and apply form/period/amendment policy using official metadata only.
- [ ] **Step 4: Run focused HTTP/discovery tests plus `tests/unit/identity/test_models.py`; expected: all pass and no live network is used.**
- [ ] **Step 5: Commit** `feat: add guarded SEC HTTP and filing discovery`.

### Task 3: Immutable SEC package store, Registry v2, and incremental planner

**Files:**
- Modify: `src/financial_filing_data_foundation/registry/models.py`, `registry/sqlite_registry.py`, `registry/__init__.py`
- Create: `src/financial_filing_data_foundation/us_sec/package.py`, `us_sec/registry.py`, `us_sec/planner.py`
- Test: `tests/unit/us_sec/test_package_registry_planner.py`, `tests/unit/registry/test_sqlite_registry.py` additions

**Interfaces:**
- Consumes: Task 1/2 filing candidates and package member bytes.
- Produces: `SecFilingPackage`, `SecPackageStore`, `canonical_package_sha256()`, additive schema v2 migration, package/member registration, and `SecIncrementalPlanner` with `REUSE_DATA`, `PARSE_LOCAL`, `DISCOVER_AND_ACQUIRE`, `REVIEW_REQUIRED`, and `BLOCKED` outcomes.

- [ ] **Step 1: Write failing tests** for deterministic package SHA, safe member paths, atomic package layout, same-SHA reuse, source drift, member hash mismatch, 128/512 MiB limits, v1→v2 migration/idempotence, CN/HK row preservation, package binding, and planner precedence.
- [ ] **Step 2: Run focused package/Registry/planner tests and confirm red.**
- [ ] **Step 3: Implement** content-addressed package storage under `raw-store/packages/sha256`, Registry v2 additive tables/methods, and planner reuse based only on validated package artifacts.
- [ ] **Step 4: Run focused tests plus all existing Registry/planner tests; expected: pass with old Registry behavior unchanged.**
- [ ] **Step 5: Commit** `feat: add immutable SEC packages and incremental Registry support`.

### Task 4: HTML/iXBRL normalization, virtual pages, tables, raw facts, and evidence

**Files:**
- Create: `src/financial_filing_data_foundation/us_sec/html_parser.py`, `us_sec/xbrl.py`, `us_sec/artifacts.py`
- Test: `tests/unit/us_sec/test_html_xbrl_artifacts.py`

**Interfaces:**
- Consumes: Task 3 `SecFilingPackage` and immutable member bytes.
- Produces: deterministic SEC artifact bundle with manifest, `pagination_kind=VIRTUAL_HTML`, blocks/sections/tables, raw XBRL facts, evidence locators, and `parse_sec_package()`.

- [ ] **Step 1: Write failing fixture tests** for stable virtual pages/DOM locators, headings, visible/nested HTML tables, rowspan/colspan/header tree, inline numeric and nonnumeric facts, custom QNames, context/unit resolution, dimensions/nil/scale/sign, and raw fact→evidence round-trip.
- [ ] **Step 2: Run focused parser tests and verify red.**
- [ ] **Step 3: Implement** a deterministic stdlib DOM normalizer and filing-local XBRL resolver. Preserve raw text/QName and emit unresolved-reference evidence/issues instead of guesses; do not import the PDF parser or canonical mapping layer.
- [ ] **Step 4: Run focused parser tests and existing `native`, `tables`, and `facts` tests; expected: all pass.**
- [ ] **Step 5: Commit** `feat: parse SEC HTML and Inline XBRL into traceable artifacts`.

### Task 5: P7 validation and additive P8 SEC read path

**Files:**
- Modify: `src/financial_filing_data_foundation/mcp/catalog.py`, `mcp/service.py`
- Create: `src/financial_filing_data_foundation/us_sec/validation.py`, `us_sec/p8.py`
- Test: `tests/unit/us_sec/test_validation_p8.py`, `tests/unit/mcp/test_catalog_service.py` additions

**Interfaces:**
- Consumes: Task 3 package metadata and Task 4 SEC artifact bundle.
- Produces: `validate_sec_artifacts()`, P11 issue/status report, SEC catalog source-kind parsing, and all existing P8 query families for SEC virtual pages/tables/facts/evidence/validation without acquisition.

- [ ] **Step 1: Write failing tests** for package/member integrity, metadata consistency, primary HTML parse, context/unit resolution, slot conflict, period plausibility, DOM/table/fact/evidence traceability, source drift/path safety, lazy P8 SEC loading, virtual pagination, and no-network P8 behavior.
- [ ] **Step 2: Run focused tests and verify red.**
- [ ] **Step 3: Implement** source-aware validation and route SEC catalog entries through lazy P8 bundle loading while preserving the exact 11 tool names and existing PDF behavior.
- [ ] **Step 4: Run focused P8/validation tests plus all existing MCP tests; expected: pass and no catalog/PDF regressions.**
- [ ] **Step 5: Commit** `feat: expose SEC artifacts through P7 and P8 read paths`.

### Task 6: SEC runtime boundary, CLI, development evidence, and candidate verification

**Files:**
- Modify: `src/financial_filing_data_foundation/user_cli.py`, `src/financial_filing_data_foundation/us_sec/__init__.py`
- Create: `src/financial_filing_data_foundation/us_sec/runtime.py`, `us_sec/runner.py`, `runtime-locks/sec-stdlib-py314-win-arm64.lock.txt`, `tests/unit/us_sec/test_cli_runtime.py`
- Create: `development/<next>-p11-development-evidence.md`

**Interfaces:**
- Consumes: Tasks 1–5 public interfaces.
- Produces: explicit-gated US `acquire`/`ingest`/`status`, `--cik`, Q2 support, subprocess-safe SEC runtime invocation, focused smoke suite, and tracked development evidence with exact candidate SHA.

- [ ] **Step 1: Write failing CLI/runtime tests** for default US rejection, explicit gate acceptance, `--cik` precedence, Q2 validation, secure runner argv/cwd/shell behavior, no remote AI/arbitrary URL, and CN/HK parser compatibility.
- [ ] **Step 2: Run focused CLI/runtime tests and verify red.**
- [ ] **Step 3: Implement** gated CLI routing and stdlib-only runtime descriptor/runner. Do not install into the main venv; live calls require a configured monitored contact email.
- [ ] **Step 4: Run focused P11 tests, `python -m compileall`, `git diff --check`, and the full short-basetemp suite; expected: all pass, with live SEC smoke reported separately if not configured.**
- [ ] **Step 5: Write tracked development evidence** listing design/start/candidate SHAs, changed files, runtime lock, all implemented areas, tests, limitations, and explicit `formal acceptance performed = NO`.
- [ ] **Step 6: Commit** production implementation and evidence as a small number of clear commits, then push `task/p11-sec-rebuild-development` and stop for independent Code Review.

## Self-review checklist

- [ ] Every design/26 requirement maps to a task or an explicit documented limitation.
- [ ] Cross-task interfaces use the exact names above.
- [ ] Review Focus cases have named tests in their owning tasks.
- [ ] No task adds a dependency to the accepted main runtime without an environment audit and lock.
- [ ] CN/HK full regression and `git diff --check` are run before any completion claim.
