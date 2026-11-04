# 104 — P10-G Detached Documentation Review Instruction

Status: **AUTHORIZED — P10-G REVIEW ONLY**

Phase:
`P10 — Codex Dynamic Research Integration`

Gate under review:
`P10-G — Thin Integration Instruction`

Candidate:
`3a805a8f333ac20770d6aec1c8285d93993d18fc`

Artifact:
`integration/p10/FFDF_RESEARCH_INTEGRATION.md`

Artifact SHA256:
`ef10406c9957f7a68a9af001c913deef0a057e166100a2d852c0c8fcd2c46296`

Development evidence:
`development/103-p10-g-integration-instruction-evidence.md`

Evidence commit:
`241055f`

## 1. Isolation

Create a fresh detached review worktree under:

`D:\\Codex\\FinancialFilingDataFoundation\\worktrees\\review\\p10-g-<authorization-sha>`

Review the authorization HEAD and exact candidate artifact above.

Do not modify the detached worktree.

No reset/clean/rebase/force push.

## 2. Mandatory review

Read and compare:

- design/24 Section 29;
- design/25 P10-G;
- acceptance/38 items 43–45 and relevant provenance/capability rules;
- development/102;
- development/103;
- exact candidate artifact.

Verify that the instruction:

- treats runtime spec as primary;
- does not hardcode research questions;
- does not map fixed question numbers to tools;
- does not hardcode a report schema;
- does not hardcode a company/ticker/period;
- does not hardcode a valuation or investment rule;
- accurately states P8/P9/P10 responsibilities;
- preserves `REVIEW_REQUIRED != DATA_UNUSABLE`;
- preserves run-local/durable/unresolved distinctions;
- preserves P9 no-raw-numeric-correction boundary;
- accurately separates external runtime sources from FFDF ledger provenance;
- honestly marks visual/semantic/canonical/P11 capabilities unavailable;
- requires explicit capability gaps rather than guessing;
- preserves exact-candidate source binding;
- contains no hidden chain-of-thought requirement/artifact.

## 3. Scope / static checks

Independently verify:

- candidate diff is only the integration document;
- artifact SHA256 matches frozen value;
- UTF-8/no-BOM;
- `git diff --check` PASS;
- no `src/tests` diff;
- no dependency/runtime diff;
- no fixed question-number pattern;
- no specific fiscal-year pattern;
- no six-digit security-code pattern;
- no named valuation-model pattern;
- no specific company/ticker example.

Generic boundary words such as company, period, valuation, or investment are allowed only where the instruction says those rules come from the runtime specification.

## 4. Verdict

Allowed:

`PASS / FAIL / BLOCKED`

PASS closes P10-G review only.

P10-H requires a separate authorization.

Research MCP production, Semantic Resolver production, and P11 production remain closed.
