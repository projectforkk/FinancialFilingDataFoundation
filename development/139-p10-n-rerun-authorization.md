# 139 — P10-N Fresh Rerun Authorization — Same Exact Candidate

Status: **AUTHORIZED — FRESH P10-N RERUN ONLY**

Phase:
P10 — Codex Dynamic Research Integration

Gate:
P10-N — Independent Acceptance

Exact candidate:
183ca5dc89a606715a3e352bf92a235f7aa31fad

Detached worktree:
D:\Codex\FinancialFilingDataFoundation\worktrees\acceptance\p10-n-183ca5d

Prior execution stop:
development/138-p10-n-execution-stop.md

The candidate/package/design remain unchanged.

## 1. Failed workspace preservation

Move the entire stopped mutable root:

D:\Codex\FinancialFilingDataFoundation\workspace\p10-n\183ca5d

to:

D:\Codex\FinancialFilingDataFoundation\workspace\scratch\p10-n-183ca5d-stopped-metadata-attempt1

Do not delete or edit it.

After the move, the canonical work root must be absent.

## 2. Fresh canonical work root

Rerun with:

D:\Codex\FinancialFilingDataFoundation\workspace\p10-n\183ca5d

The frozen harness precheck must create this root fresh.

## 3. Full rerun required

Repeat all development/137 requirements from the beginning:

- precheck;
- focused research suite;
- full unit suite;
- complete read and dynamic execution of Spec A/B;
- fresh live CN COMPLETE run;
- fresh isolated P9 review store;
- exact frozen P9 submission metadata;
- K1-K5 negative gates;
- postcheck;
- immutable base check;
- detached clean status.

No results from the stopped workspace may be copied into the fresh rerun.

## 4. Frozen live submission metadata

Use exactly:

reviewer_type=CODEX
reviewer_id=p10-independent-acceptance
reviewed_at=2026-11-04T12:00:00+09:00
justification=P10 Independent Acceptance isolated review: same-table P5 cell explicitly identifies period 2024 for the target raw fact.

## 5. Scope

No P10 production/test/design/package change is authorized.

No main integration is authorized.

P11 / Research MCP production / Semantic Resolver production remain closed.

Only an actual fresh P10-N PASS may permit later closeout authorization.
