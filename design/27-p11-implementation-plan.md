# 27 — P11 US SEC Provider Implementation Plan

Status: **READY FOR SHORT-CYCLE DEVELOPMENT AFTER DESIGN FREEZE**

Detailed design:
`design/26-p11-sec-provider-design.md`

Scope reopening:
`design/32-p11-us-scope-reopening.md`

## 1. Execution principle

P11 uses a deliberately short development lifecycle.

The default path is:

```text
DESIGN FREEZE
→ PC AGENT ONE-PASS DEVELOPMENT
→ GIT COMMIT / PUSH EXACT CANDIDATE
→ CHATGPT CODE REVIEW
→ CHATGPT TEST PLAN
→ PC AGENT ONE-PASS TEST EXECUTION
→ GIT COMMIT / PUSH TEST EVIDENCE
→ CHATGPT INDEPENDENT VERIFICATION
→ ACCEPT / FIX
→ MAIN INTEGRATION
```

The purpose is to avoid many artificial sub-phases while preserving:

- exact commit traceability;
- Design-First;
- independent code review;
- reproducible test evidence;
- CN/HK non-regression;
- no hidden local-only state.

## 2. Roles

### 2.1 PC Agent

PC Agent is responsible for:

1. reading the frozen P11 design completely;
2. auditing the actual local environment as part of development;
3. implementing the full P11 production candidate in one development pass where practical;
4. writing/adjusting unit and integration tests required by implementation;
5. running developer-focused smoke checks sufficient to avoid submitting obviously broken code;
6. committing and pushing the exact production candidate to Git;
7. after ChatGPT issues the formal test plan, executing that plan on the PC;
8. committing and pushing all formal test evidence to Git.

PC Agent must not declare final acceptance.

### 2.2 ChatGPT

ChatGPT is responsible for:

1. reviewing the exact Git production candidate;
2. checking design/code consistency;
3. identifying correctness, security, compatibility and evidence defects;
4. deciding `REVIEW_PASS` or `CHANGES_REQUIRED`;
5. after review PASS, issuing the exact formal test plan;
6. after PC Agent commits test evidence, independently validating:
   - candidate identity;
   - commands actually executed;
   - outputs/results;
   - evidence completeness;
   - CN/HK regression;
   - live SEC evidence;
7. deciding final `ACCEPTANCE_PASS` or `ACCEPTANCE_FAILED`.

### 2.3 GitHub

GitHub is the only shared source of truth between PC Agent and ChatGPT.

No local-only claim counts as development or acceptance evidence.

## 3. Gate S0 — Design Freeze

Before PC development starts, freeze:

- `design/26-p11-sec-provider-design.md`;
- `design/27-p11-implementation-plan.md`;
- `design/32-p11-us-scope-reopening.md`;
- current accepted main base SHA.

Record:

```text
design_baseline_sha
main_base_sha
development_branch
```

No production code is written before this gate.

## 4. Gate D1 — PC Agent One-Pass Development

PC Agent should implement the entire P11 candidate in one development task unless a genuine STOP condition is found.

The development task includes the formerly separate activities:

- environment/runtime audit;
- US CIK/ticker identity;
- SEC submissions discovery;
- Fair Access / User-Agent / rate limiting;
- accession/form/period policy;
- immutable SEC filing package acquisition;
- package/member SHA identity;
- additive Registry migration;
- incremental planner integration;
- HTML / Inline XBRL normalization;
- virtual HTML pages / DOM locators;
- HTML tables;
- XBRL contexts/units/raw facts;
- evidence;
- P7 US validation;
- P8 US read path;
- user CLI US support;
- foreign issuer annual support;
- focused developer tests.

### 4.1 Development constraints

PC Agent must preserve:

- existing CN/HK behavior;
- P8 tool names;
- P9 overlay semantics;
- P10 responsibilities;
- raw/source immutability;
- no AI/API calls inside FFDF/MCP;
- no guessing;
- evidence traceability.

### 4.2 Historical P11 code

Historical P11 branches/probes may be inspected but must not be merged wholesale.

Any reused code must be reconciled against the new design and current main.

### 4.3 Development STOP conditions

Stop development and submit a design issue instead of guessing if:

1. accepted P0-P10 behavior cannot be preserved additively;
2. Registry migration requires destructive rewrite;
3. SEC filing semantics contradict the frozen identity/period design;
4. a required SEC source interface no longer behaves as designed;
5. evidence cannot be traced to immutable source bytes;
6. a security boundary requires arbitrary URL/filesystem execution;
7. implementation would require remote AI.

If none occurs, complete the full implementation in one pass.

## 5. Development Candidate Commit

At the end of D1, PC Agent must commit and push one exact candidate.

Required development record:

`development/<next>-p11-development-evidence.md`

It must include:

- design baseline SHA;
- starting main SHA;
- production candidate SHA;
- branch;
- changed file list;
- runtime/dependency changes;
- Registry migration version;
- SEC runtime lock/pin;
- developer smoke commands;
- developer smoke results;
- known limitations;
- explicit statement that no accepted CN/HK raw data was mutated.

Developer smoke is not final acceptance.

## 6. Gate R1 — ChatGPT Code Review

ChatGPT reviews the exact candidate SHA from Git.

Review scope:

### 6.1 Architecture

- CIK is stable US company identity;
- accession is provider filing identity;
- SEC filing is modeled as a package;
- HTML/Inline XBRL first;
- companyfacts is secondary cross-check only;
- no PDF-only shortcut.

### 6.2 Acquisition/security

- SEC host allowlist;
- declared User-Agent;
- rate limiter;
- retry/backoff;
- redirect validation;
- content-size limits;
- no arbitrary caller URL;
- no JavaScript execution;
- no remote subresource loading;
- staging/atomic commit;
- source drift detection.

### 6.3 Registry/incremental behavior

- migration additive and idempotent;
- old CN/HK Registry remains readable;
- same accession/package is reused;
- package/member hashes are stable;
- amendment handling fails closed where ambiguous.

### 6.4 Parser/evidence

- virtual pages explicitly marked as virtual;
- DOM locators deterministic;
- contextRef/unitRef resolution;
- custom XBRL QName preserved;
- raw facts are not canonicalized;
- evidence resolves to immutable member bytes.

### 6.5 Integration

- CN/HK policy unchanged;
- US domestic Q2 support isolated by market;
- P8 exact tool names unchanged;
- P9/P10 semantics unchanged;
- CLI does not accept arbitrary SEC URLs;
- public `SUPPORTED_MARKETS` is not prematurely changed before acceptance unless the candidate design explicitly uses a gated development mechanism.

### 6.6 Review verdict

Exactly one:

```text
REVIEW_PASS
CHANGES_REQUIRED
```

If `CHANGES_REQUIRED`, ChatGPT provides a compact issue list.

PC Agent should fix all review issues in one repair pass and push a new exact candidate SHA.

No formal acceptance testing starts before `REVIEW_PASS`.

## 7. Gate T0 — ChatGPT Formal Test Plan

After `REVIEW_PASS`, ChatGPT creates the exact test plan.

Test plan is committed to Git as:

`development/<next>-p11-formal-test-plan.md`

The plan must identify the exact reviewed candidate SHA and contain executable commands and expected outcomes.

The formal plan covers only tests needed to accept the completed candidate; it does not reopen development design.

## 8. Required Formal Test Groups

The exact commands are written after code review, but acceptance must cover these groups.

### T1 — Compile / static / contract

- compile;
- focused P11 unit tests;
- reason-code/schema tests;
- runtime lock validation;
- Git diff/check.

### T2 — Identity / discovery

- ticker → CIK;
- explicit CIK;
- 10-K;
- 10-Q Q1/Q2/Q3;
- amendment case;
- not-found;
- ambiguous identity;
- SEC rate/access failure simulation.

### T3 — Package acquisition

- live official SEC filing discovery;
- primary document + required XBRL members;
- member SHA;
- package SHA;
- repeat acquisition reuse;
- source drift negative fixture;
- host/path/content-type/size negative fixtures.

### T4 — Registry / migration

- open old CN/HK Registry;
- migrate;
- reopen;
- migration idempotence;
- old rows preserved;
- US package records persisted;
- planner REUSE/PARSE_LOCAL/DOWNLOAD behavior.

### T5 — HTML / Inline XBRL parsing

- deterministic virtual pages;
- sections;
- DOM table reconstruction;
- context/unit resolution;
- custom extension facts;
- raw fact → evidence locator round trip;
- malformed/unresolved negative fixtures.

### T6 — P7 / P8

For a live US filing verify:

- validation result;
- no blocking issue for the accepted positive fixture;
- P8 list/get/search/pages/sections/tables/facts/evidence/validation;
- P8 has no network acquisition.

### T7 — CLI

At least:

```text
ffdf acquire --market US ...
ffdf ingest  --market US ...
ffdf status  --market US ...
```

Repeat command proves incremental reuse.

### T8 — Foreign private issuer

At minimum one official annual:

- 20-F or 40-F.

6-K quarterly auto-mapping is tested only if implemented under deterministic rules.
Otherwise verify explicit fail-closed behavior.

### T9 — CN/HK regression

Mandatory:

- existing full unit suite;
- CN CLI smoke;
- HK CLI smoke;
- P8 CN/HK smoke;
- no accepted CN/HK artifact mutation.

### T10 — No-AI / security boundary

Verify production code does not call:

- OpenAI;
- Anthropic;
- Gemini;
- Codex API;
- MCP sampling;
- arbitrary shell/network targets from filing content.

## 9. Gate T1 — PC Agent One-Pass Formal Testing

PC Agent executes the complete ChatGPT-authored test plan in one test task.

It may rerun failed tests after correcting only:

- test harness errors;
- environment setup mistakes explicitly permitted by the plan.

If production code must change, formal testing stops.

The flow returns to:

```text
code fix
→ new candidate SHA
→ ChatGPT review
→ revised test plan
```

This prevents testing evidence from silently referring to different code.

## 10. Test Evidence Commit

PC Agent commits and pushes:

`development/<next>-p11-formal-test-evidence.md`

Evidence must include:

- exact candidate SHA;
- exact test-plan SHA/file;
- environment/runtime identity;
- every command;
- exit code;
- concise result;
- focused pass counts;
- full regression pass counts;
- live SEC CIK/accession/form/period;
- source URLs;
- package/member hashes;
- validation status;
- P8 query results;
- repeat-run/reuse result;
- negative-gate results;
- any skipped test with explicit reason.

Large raw logs may be stored as tracked evidence artifacts when practical; summaries must point to them.

No screenshots alone count as test evidence when machine-readable output exists.

## 11. Gate V1 — ChatGPT Independent Verification

ChatGPT verifies from Git:

1. test evidence references the exact reviewed candidate;
2. candidate did not change after review;
3. commands correspond to the formal test plan;
4. expected positive and negative cases are present;
5. live SEC evidence is internally consistent;
6. hashes/identities are coherent;
7. failures/skips are not hidden;
8. CN/HK regression passed;
9. no production-code changes are mixed into the test-evidence commit.

ChatGPT may inspect relevant source/tests/evidence directly from Git.

Verdict:

```text
ACCEPTANCE_PASS
ACCEPTANCE_FAILED
```

## 12. Gate I1 — Main Integration

Only after `ACCEPTANCE_PASS`:

- merge the exact accepted candidate lineage;
- update current project status;
- enable US in public supported-market declarations as required;
- change P11 capability from unavailable to available;
- update user documentation;
- run a final minimal main smoke if merge metadata changed files.

Record merge SHA.

## 13. Gate C1 — Closeout

Create one final closeout record containing:

- design baseline SHA;
- reviewed candidate SHA;
- code review result;
- formal test plan;
- formal test evidence commit;
- ChatGPT verification verdict;
- merge SHA;
- supported US forms/periods;
- explicit unsupported cases.

Final state only after this:

`P11 DONE / PASS`

## 14. Short-path target

Normal successful P11 execution should require only:

```text
1 design PR
1 PC development pass
1 production candidate push
1 ChatGPT review
1 ChatGPT test plan
1 PC formal test pass
1 test-evidence push
1 ChatGPT verification
1 merge/closeout
```

A repair loop is allowed only when a real defect is found.

The workflow must not create separate development phases merely to mirror architecture components.
