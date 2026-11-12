# P11 Full-Design Repair 135-139 Implementation Plan

> **For inline execution:** Use superpowers:executing-plans to implement this plan task-by-task in the current worktree. Do not create agents or additional threads.

**Goal:** Repair the P11 SEC provider so discovery observations are independently reconstructable, late amendments are not missed, P8 company context uses the same verified source chain, XBRL/Inline XBRL namespaces are authentic, and the explicitly deferred 6-K scope is rejected deterministically.

**Architecture:** Keep SEC discovery as the authoritative source-selection boundary. Persisted observation fields are checked against a fresh reconstruction from the retained official submissions bytes, and the same verifier is used by P7 and the P8 bundle path. Keep package selection and parser layers separate: package roles require authentic namespaces, while custom taxonomy facts remain extractable from a valid XBRL instance. P11 v1 does not acquire or map explicit 6-K/6-K/A requests.

**Tech Stack:** Python 3, pytest, `dataclasses`, `json`, `hashlib`, `xml.etree.ElementTree`, the existing SEC HTTP client/acquirer, P7 validation, P8 catalog service, and the existing CLI.

**Spec:** `design/26-p11-sec-provider-design.md`, `design/27-p11-implementation-plan.md`, `design/32-p11-us-scope-reopening.md`, `design/33-p11-post-acceptance-design-correction.md`, `design/34-p11-explicit-6k-scope-correction.md`, and `development/188-p11-full-design-code-consistency-review-3.md`.

## Global Constraints

- `MCP_AI_API_CALLS = FORBIDDEN`; no remote LLM/API calls.
- Original SEC documents are immutable; corrections are review/validation behavior only.
- No guessing or substitution of period, unit, scope, issuer, accession, or facts.
- Every research-ready fact remains traceable to document, page/table/row/cell or equivalent SEC evidence.
- Extraction does not perform CRDE mapping, fiscal-period inference, YoY/QoQ/TTM, valuation, or investment conclusions.
- Current discovery precedes local reuse; validated artifacts are reused only after the current observation/source chain verifies.
- Born-digital SEC packages use the light path; no unconditional OCR/heavy parser.
- Preserve ISSUE-123 through ISSUE-134 behavior and existing schema/version contracts unless a test proves the repair requires a compatible validation change.
- No formal test plan, formal acceptance, main merge, or P11 DONE transition is authorized in this repair cycle.
- No destructive Git commands, amend, rebase, force push, or agent/thread creation.

## Review Focus

- A persisted observation with a self-consistent forged candidate list, state, selected accession, or canonical SHA must fail because the official retained bytes reconstruct a different result (T135).
- A late amendment in a listed historical submissions chunk must be found even when the current submissions chunk already contains a candidate (T136).
- A cached SEC company summary must re-verify the same package/discovery chain as document retrieval (T137).
- Generic local-name lookalikes, wrong XBRL roots, wrong Inline XBRL namespaces, and namespace-colliding contexts/units must not become truth; valid custom taxonomy facts must still work (T138).
- Explicit 6-K/6-K/A input must be rejected with `P11_UNSUPPORTED_EXPLICIT_6K`, without quarter coercion or acquisition (T139).

### Task 1: Independent discovery reconstruction and complete candidate enumeration

**Files:**
- Modify: `src/financial_filing_data_foundation/us_sec/discovery.py`
- Modify: `src/financial_filing_data_foundation/us_sec/acquisition.py`
- Modify: `src/financial_filing_data_foundation/us_sec/validation.py`
- Modify: `src/financial_filing_data_foundation/us_sec/errors.py`
- Test: `tests/unit/us_sec/test_full_design_repair_135_139.py`
- Update: existing SEC discovery/provider/validation fixtures that currently use unparseable or namespace-free observations

**Interfaces:**
- Produces a shared deterministic discovery-decision helper used by acquisition and observation verification.
- Observation verification accepts only official `data.sec.gov/submissions` URLs, decodes and hashes every retained body, reparses the main and all listed history chunks, reconstructs candidates/state/selection, and compares the reconstructed values with the observation and Registry row.
- History enumeration processes the complete bounded official file list rather than stopping when an early chunk yields a candidate.

- [ ] **Step 1: Write failing tests** for T135-01 through T135-10, including source-body tamper, source URL tamper, forged candidate/state/selected/fingerprint/SHA, candidate form mismatch, missing/extra history source, Registry mismatch, and a valid independently reconstructed observation; add T136-01 through T136-06 for late amendment discovery, deterministic ordering, bounded history, duplicate/conflicting accession behavior, and fail-closed malformed history metadata.
- [ ] **Step 2: Run the focused tests** and record the expected failures against the current verifier and first-history-chunk break.
- [ ] **Step 3: Implement reconstruction and decision derivation** in `discovery.py`; validate source URL identity and body hashes, parse the official bytes, aggregate/deduplicate candidates deterministically, derive state and selected accession from reconstructed candidates, and make `verify_sec_discovery_observation()` compare semantic values before accepting persisted identity fields.
- [ ] **Step 4: Remove the early history break** in `acquisition.py`; use a deterministic bounded policy over all official `filings.files` chunks, fail closed on a bound/metadata violation, and use the shared discovery decision.
- [ ] **Step 5: Add P7 fact-source-mode validation** in `validation.py`, including valid values `INLINE_XBRL_PRIMARY`, `XBRL_INSTANCE_PRIMARY`, and `NO_STRUCTURED_FACTS`; invalid combinations are blocking and `NO_STRUCTURED_FACTS` is not research-ready.
- [ ] **Step 6: Run the focused tests and the existing SEC discovery/provider/validation tests**, then commit the verified repair.

### Task 2: Make SEC company context use the verified P8 bundle chain

**Files:**
- Modify: `src/financial_filing_data_foundation/mcp/service.py`
- Test: `tests/unit/mcp/test_catalog_service.py` and `tests/unit/mcp/test_full_design_repair_135_139.py`

**Interfaces:**
- `get_document_summary_internal()` for SEC documents obtains summary data from `_bundle()` and its verified artifacts rather than loading a summary shortcut independently.
- Cached SEC bundles still re-run the source-chain verification before returning context.

- [ ] **Step 1: Write failing tests** T137-01 through T137-06 for equivalent bundle/context identity, source-chain tamper rejection through `ffdf_get_company_report_context`, cached re-verification, and no bypass through the summary path.
- [ ] **Step 2: Run the focused tests** and observe the current shortcut accept tampered SEC context.
- [ ] **Step 3: Route the SEC summary branch through `_bundle()`** and read catalog/native/table/fact/validation fields from that verified bundle without changing CN/HK behavior.
- [ ] **Step 4: Run all MCP catalog-service tests and the new T137 tests**, then commit the verified repair.

### Task 3: Enforce namespace-authentic XBRL and Inline XBRL parsing

**Files:**
- Modify: `src/financial_filing_data_foundation/us_sec/parser.py`
- Modify: `src/financial_filing_data_foundation/us_sec/acquisition.py`
- Modify: `src/financial_filing_data_foundation/us_sec/validation.py` if package-role authenticity needs a P7 issue
- Test: `tests/unit/us_sec/test_full_design_repair_135_139.py`
- Update: existing SEC parser fixtures to declare the namespaces they claim to use

**Interfaces:**
- DOM nodes retain namespace URI information for prefixed and default declarations.
- XBRL instance roots require `http://www.xbrl.org/2003/instance`.
- Context/unit and dimension semantics require their reviewed namespaces; Inline `nonfraction`, `nonnumeric`, `continuation`, `exclude`, `header`, and `hidden` require an accepted Inline XBRL namespace.
- Valid XBRL custom taxonomy facts remain accepted when their instance root and context references are authentic.

- [ ] **Step 1: Write failing tests** T138-01 through T138-07 for valid namespaced roots, wrong-root namespace, generic local-name collisions, namespace-aware contexts/units/dimensions, alternate Inline prefix, continuation/exclude handling, and custom taxonomy preservation.
- [ ] **Step 2: Run the focused parser/acquisition tests** and observe local-name lookalikes being accepted or a generic `<xbrl />` being classified as an instance.
- [ ] **Step 3: Add namespace tracking and replace local-name-only truth checks** in the DOM parser, XML fact/context/unit parsing, Inline fact/continuation/exclude handling, package role detection, and evidence checks; keep ordinary HTML visibility behavior separate from Inline XBRL semantics.
- [ ] **Step 4: Update only fixtures that intentionally represent XBRL/Inline XBRL** with their declared namespaces; leave negative lookalike fixtures namespace-invalid.
- [ ] **Step 5: Run all SEC parser, semantic-reference, corrected-repair, issue131, provider-CLI, and P8 validation tests**, then commit the verified repair.

### Task 4: Enforce the corrected explicit 6-K scope

**Files:**
- Modify: `src/financial_filing_data_foundation/user_cli.py`
- Modify: `src/financial_filing_data_foundation/us_sec/errors.py`
- Test: `tests/unit/us_sec/test_full_design_repair_135_139.py` and `tests/unit/us_sec/test_provider_cli.py`

**Interfaces:**
- US `--filing-type 6-K` and `6-K/A` requests fail deterministically with `P11_UNSUPPORTED_EXPLICIT_6K` before acquisition/status/ingest can create a package.
- No quarter mapping, silent ignore, package, Registry row, P8 artifact, or research-ready result is produced for deferred 6-K scope.

- [ ] **Step 1: Write failing T139 tests** for both `6-K` and `6-K/A`, including the no-acquisition/no-quarter-coercion assertion.
- [ ] **Step 2: Run the tests** and observe the current US path accept or ignore the generic filing type.
- [ ] **Step 3: Add the error code and early US CLI guard** while leaving CN/HK filing-type behavior unchanged.
- [ ] **Step 4: Run the focused CLI tests and the full US SEC test set**, then commit the verified repair.

### Task 5: Freeze the candidate and produce repair evidence

**Files:**
- Create: `development/189-p11-full-design-repair-135-139-evidence.md` (or the next unused `development/` evidence number)
- No source or test edits after candidate freeze

- [ ] **Step 1: Run the complete focused repair suite, all unit tests, P0-P10 focused tests, compileall, and `git diff --check`; capture exact exit codes and counts.**
- [ ] **Step 2: Run a fresh isolated production-shaped Apple FY acquisition/ingest smoke test** with the real SEC contact identity, proving source URLs, package roles, XSD/linkbase counts, facts, P7 status, research readiness, and zero JPEG/static browser-asset fetching; retain the isolated root and logs.
- [ ] **Step 3: Inspect the final diff and history**, verify no remote AI calls or unauthorized scope changes, then create the new production candidate commit and record its SHA.
- [ ] **Step 4: Freeze source/tests at the candidate SHA and create only the evidence document** linking the candidate, design correction, test outputs, smoke evidence, and unresolved formal gates.
- [ ] **Step 5: Commit the evidence document only, verify candidate-to-evidence is documentation-only, push both commits normally, and report the exact receipt with `P11 DONE = NO`.**

