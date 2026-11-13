# Project Status

Updated: 2026-11-13

Repository:

`projectforkk/FinancialFilingDataFoundation`

Current development branch:

`task/p11-sec-rebuild-development`

This file is the concise current-state index. Historical development/review/acceptance documents remain the audit trail and must not be rewritten to match the latest state.

---

# 1. Executive state

```text
P0-P10:
DONE / ACCEPTED / PRODUCTION BASELINE PRESERVED

P11 US SEC PROVIDER:
REOPENED
IMPLEMENTED THROUGH MULTIPLE REPAIR CYCLES
NOT ACCEPTED
CURRENT FULL REVIEW = CHANGES_REQUIRED

FORMAL TEST PLAN FOR CURRENT CANDIDATE:
NOT AUTHORIZED

FORMAL ACCEPTANCE:
NOT RUN FOR CURRENT CANDIDATE

MAIN MERGE:
NOT AUTHORIZED

P11 DONE:
NO
```

Accepted production markets on main remain:

`CN`, `HK`

US SEC is still under the reopened P11 lifecycle and is not yet accepted into production main.

---

# 2. Accepted production baseline — completed

P0 through P10 are complete and accepted.

Final accepted P10 production baseline:

- frozen acceptance candidate:
  `183ca5dc89a606715a3e352bf92a235f7aa31fad`
- accepted integration merge:
  `a539500ef1fd0036eaa8d79a9bf7cfe78db57185`
- main integration evidence:
  `230968937a8ebdcbde56982a22b37125e4aefff4`
- independent acceptance:
  `acceptance/40-p10-independent-acceptance-result.md = PASS`
- final closeout:
  `development/142-p10-closeout.md = DONE / PASS`
- final accepted P10 research regression:
  `136 passed`
- final accepted full unit regression:
  `444 passed`
- CN 600519 FY2024 live acceptance:
  `PASS`
- P10 K1-K5 negative capability gates:
  `PASS`

P0-P10 accepted behavior is a compatibility boundary for P11.

P11 must not weaken accepted:

- CN/HK acquisition/ingest/status;
- Registry behavior;
- P3-P7 artifact/evidence semantics;
- P8 read-only contract;
- P9 review overlay;
- P10 research integration;
- runtime/security/immutability guarantees.

---

# 3. P11 scope / design authority

P11 was historically closed as out of scope, then explicitly reopened.

Historical CN/HK closeout remains accepted history, but no longer represents current P11 scope.

P11 active design lineage includes:

- `design/26-p11-sec-provider-design.md`
- `design/27-p11-implementation-plan.md`
- `design/32-p11-us-scope-reopening.md`
- `design/33-p11-post-acceptance-design-correction.md`
- `design/34-p11-explicit-6k-scope-correction.md`

Original corrected P11 design baseline:

`09e3174b7e19a60cc5955862670fac8931af67db`

Current design freeze including Design 34:

`4bf644374af3a0585453379fcc185d6464105776`

After Design 34, `09e3174...` is still the corrected-design ancestry but must not be treated as the complete current design freeze by itself.

Design 34 resolves explicit Form 6-K scope for P11 v1:

- no 6-K → standardized quarter coercion;
- explicit 6-K/6-K/A acquisition is deferred;
- explicit requests are deterministically rejected.

---

# 4. P11 lifecycle completed so far

## 4.1 Reopening / architecture / implementation

Completed:

- P11 scope reopening;
- dedicated SEC package/provider architecture;
- current ticker→CIK and explicit CIK identity model;
- SEC current submissions/history discovery;
- SEC package store and package/member provenance;
- dedicated HTML/iXBRL/XBRL parser;
- P7 SEC validation;
- P8 SEC catalog/query integration;
- production CLI US paths;
- runtime/Fair Access/security implementation;
- developer live SEC testing.

## 4.2 Historical formal execution

A prior Formal Test Plan existed for an older candidate:

- plan:
  `development/183-p11-formal-test-plan-3.md`
- execution prompt:
  `development/184-p11-formal-test-execution-prompt-3.md`
- execution evidence:
  `development/185-p11-formal-test-evidence-3.md`
- exact old candidate:
  `9389d59d68c84762b55b29bedb973db4ea45256a`

That formal execution failed at live Apple FT-10 because static JPEG assets were incorrectly selected into the SEC package.

That old Formal Plan is historical only.

It must never be resumed for a later candidate.

---

# 5. P11 repaired issue history — completed or materially closed

Fresh review history currently considers the following repaired/closed or materially corrected:

```text
P11-ISSUE-123  current discovery before reuse
P11-ISSUE-124  exactly one logical fact source
P11-ISSUE-125  Inline continuation / exclude correctness
P11-ISSUE-126  OTHER XML semantic isolation
P11-ISSUE-127  ticker source provenance / current refresh
P11-ISSUE-128  package/member provenance
P11-ISSUE-129  logical DOM table grid / header semantics
P11-ISSUE-130  production enablement without dev flag
P11-ISSUE-131  exact discovery observation trust boundary
P11-ISSUE-133  browser/static asset over-selection
P11-ISSUE-134  semantic XBRL references independent of SEC index type
P11-ISSUE-135  persisted observation semantics independently reconstructed
P11-ISSUE-136  early history termination / split-candidate correctness fixed
P11-ISSUE-137  report-safe P8 summary now uses verified SEC trust chain
P11-ISSUE-138  parser namespace authenticity implemented
P11-ISSUE-139  explicit 6-K scope design-corrected and rejected deterministically
```

Important nuance:

- ISSUE-136 core correctness is fixed, but the current “fetch all history” implementation created ISSUE-142.
- ISSUE-138 parser authenticity is implemented, but compatibility/acquisition cross-boundary gaps created ISSUE-140 and ISSUE-141.

---

# 6. Latest reviewed production candidate

Latest production candidate reviewed by ChatGPT:

`55fc575cdaaeebd8b686ce76120978c714ca1a28`

Developer evidence:

`development/189-p11-full-design-repair-135-139-evidence.md`

Evidence commit:

`21962b8e4748cb8f800ad75be904624508d84ae8`

Candidate → evidence:

`DOCUMENTATION ONLY — PASS`

Latest fresh full exact-candidate review:

`development/190-p11-fresh-full-exact-candidate-review-4.md`

Review commit:

`adac1075a71881dc5aec41049ead3b03d1933d4c`

Review verdict:

```text
CHANGES_REQUIRED
REVIEW_PASS = NO
FORMAL TEST PLAN = NOT AUTHORIZED
```

---

# 7. Latest developer verification on 55fc575...

Developer evidence for the latest reviewed candidate recorded:

- focused ISSUE-135..139:
  `33 passed`
- US SEC + MCP related:
  `193 passed`
- full unit:
  `703 passed`
- compileall:
  `PASS`
- git diff --check:
  `PASS`

Apple FY2025 developer smoke:

- CIK:
  `0000320193`
- accession:
  `0000320193-25-000079`
- structured facts:
  `1,131`
- XSD:
  `1`
- linkbases:
  `4`
- static/browser asset requests:
  `0`
- P7:
  `PASS`
- research_ready:
  `true`
- `FFDF_P11_US_DEV`:
  `ABSENT`

These are developer verification results only.

They are not Formal Acceptance.

---

# 8. Current work — in progress

Current authorized work is a coherent repair cycle for:

```text
P11-ISSUE-140
P11-ISSUE-141
P11-ISSUE-142
P11-ISSUE-143
```

No current repair candidate exists yet after Review 190.

## P11-ISSUE-140 — parser/artifact compatibility invalidation

Status:

`OPEN / BLOCKING`

Problem:

ISSUE-138 changed parser semantics to namespace-authentic behavior, but the reviewed candidate still uses the previous V5/v2 compatibility identity.

Therefore a pre-ISSUE-138 V5/v2 artifact can still qualify for reuse and bypass the corrected parser.

Required:

- design-corrected compatibility/version freeze;
- previous affected parsed artifacts become incompatible;
- immutable raw package remains reusable;
- parser must actually re-run;
- new artifact written separately;
- old artifact remains immutable;
- current artifact reusable after reparse.

## P11-ISSUE-141 — namespace-authentic semantic-reference acquisition

Status:

`OPEN / BLOCKING`

Problem:

Primary HTML semantic-reference acquisition still recognizes literal `link:schemaRef` / `link:linkbaseRef` prefix strings instead of authentic XBRL linkbase/XLink namespace semantics.

Required:

- namespace URI based linkbase reference recognition;
- prefix independence;
- authentic XLink reference handling;
- wrong/unbound lookalikes rejected;
- ISSUE-133 static-asset zero-fetch preserved;
- ISSUE-134 generic-index-type semantic XBRL support preserved.

## P11-ISSUE-142 — complete but minimal history source selection

Status:

`OPEN / BLOCKING`

Problem:

The previous repair removed early history termination but now fetches every listed SEC history chunk.

This preserves completeness but conflicts with the design requirement to fetch only history required for the requested slot.

Required:

- complete candidate coverage;
- late amendments remain discoverable;
- provably irrelevant history not fetched;
- incomplete metadata handled conservatively;
- deterministic bound/fail-closed behavior;
- online discovery and P7 reconstruction use exactly the same selection rule.

If a safe minimal rule cannot be established from official metadata, return to design rather than guess.

## P11-ISSUE-143 — P7 fact-source semantic invariants

Status:

`OPEN / BLOCKING`

Problem:

P7 validates the fact_source_mode enum and basic fact counts but does not fully prove that logical facts/evidence come from the source mandated by the mode.

Required:

- INLINE_XBRL_PRIMARY → logical facts only from authentic primary iXBRL;
- XBRL_INSTANCE_PRIMARY → logical facts only from exactly one verified XBRL instance;
- NO_STRUCTURED_FACTS → zero logical facts;
- internally self-consistent mode/source tampering fails closed.

---

# 9. Not completed / not authorized

The following are not complete:

- ISSUE-140 repair;
- ISSUE-141 repair;
- ISSUE-142 repair;
- ISSUE-143 repair;
- new post-140..143 production candidate;
- developer evidence for that new candidate;
- fresh full exact-candidate review of that new candidate;
- new Formal Test Plan;
- new formal execution;
- independent final acceptance review;
- P11 acceptance;
- exact main integration;
- P11 closeout.

The following are explicitly not authorized now:

```text
NEW FORMAL TEST PLAN
FORMAL ACCEPTANCE
MAIN MERGE
P11 DONE
```

A Formal Test Plan can be created only after a fresh full exact-candidate design/code review returns:

`REVIEW_PASS`

---

# 10. Required next lifecycle

```text
READ CURRENT DESIGN / REVIEW 190
→ DESIGN CORRECTION FOR ISSUE-140 IF REQUIRED
→ REPAIR ISSUE-140..143
→ FOCUSED REGRESSION
→ FULL US SEC REGRESSION
→ FULL UNIT REGRESSION
→ P0-P10 COMPATIBILITY REGRESSION
→ LIVE APPLE DEVELOPER SMOKE
→ FREEZE NEW EXACT PRODUCTION CANDIDATE
→ DOCUMENTATION-ONLY DEVELOPER EVIDENCE
→ STOP
→ CHATGPT FRESH FULL EXACT-CANDIDATE DESIGN/CODE REVIEW
→ only if REVIEW_PASS:
   NEW FORMAL TEST PLAN
→ separate Formal Execution
→ ChatGPT independent final acceptance review
→ acceptance
→ explicit main integration authorization
→ closeout
```

Any production/test/design change after candidate freeze creates a new candidate and invalidates the previous review boundary.

---

# 11. Current compatibility / governance constraints

Current known pre-repair values on the reviewed candidate:

```text
REGISTRY_SCHEMA_VERSION = 1
SEC_REGISTRY_SCHEMA_VERSION = 4
SEC_DISCOVERY_SCHEMA = p11-sec-discovery-v1
VIRTUAL_HTML_NORMALIZER_VERSION = VIRTUAL_HTML_V5
SEC_ARTIFACT_SCHEMA = p11-sec-artifacts-v2
SEC_VALIDATION_SCHEMA = p11-sec-validation-v2
```

ISSUE-140 is expected to require a new parser compatibility identity.

Do not change version numbers merely because code changed.

A version change must be design-grounded and preserve old artifacts immutably.

---

# 12. Project-wide unauthorized future scope

Unless separately authorized, the following remain outside the current production task:

- Research MCP production expansion beyond accepted P8/P9/P10 contracts;
- Semantic Resolver production;
- remote AI/LLM APIs inside FFDF extraction;
- weakening P8 read-only behavior;
- weakening P9 durable-review boundaries;
- automatic 6-K quarterly mapping.

---

# 13. Session handoff

A full-project new-session handoff prompt is tracked at:

`docs/P11_SESSION_HANDOFF_PROMPT.md`

The new session must not jump straight into ISSUE-140..143.

It must first:

1. read governance/status;
2. read every tracked design document;
3. read the complete production source tree;
4. read tests as executable contracts;
5. understand P0-P10 accepted history;
6. understand current P11 trust boundaries and lifecycle;
7. summarize the project as a whole;
8. only then continue the current repair.

Git is the source of truth if this status file and later commits ever differ.
