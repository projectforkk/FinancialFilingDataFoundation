# 128 — P10-N Precheck Stop — P10-ISSUE-008

Status: **STOPPED — P10-ISSUE-008 ACCEPTANCE FIXTURE IDENTITY AMENDMENT REQUIRED**

Phase:
P10 — Codex Dynamic Research Integration

Gate:
P10-N — Independent Acceptance

Corrected acceptance authorization:
development/127-p10-n-corrected-reauthorization.md

Exact detached candidate:
4d1ab46f11d1d7b88934309ce32319e2200f0d8f

Detached worktree:
D:\Codex\FinancialFilingDataFoundation\worktrees\acceptance\p10-n-4d1ab46

## 1. Stop timing

P10-N stopped during the frozen harness precheck.

No focused/full suite, dynamic A/B, live run, or negative gate was executed after the precheck failure.

The detached candidate remained clean and unmodified.

## 2. Observed failure

Frozen harness precheck returned:

fixture size drift: corrupt-p9.md

status=FAIL
phase=pre

## 3. Facts

Repository configuration:

core.autocrlf=true

For all 8 frozen Markdown fixtures:

- manifest size/SHA exactly matches the candidate Git blob bytes;
- candidate Git blob uses LF;
- detached Windows checkout materializes CRLF;
- detached checkout size/SHA therefore differs.

Example:

corrupt-p9.md

manifest/Git blob:
- size=611
- sha256=67bc7b16a5e9bac01dd822a3438301b13d7c48f04a45fdc657d60817bd50d3e2
- CRLF=0

detached checkout:
- size=626
- sha256=0cbcd131706d9712bd603ff013f7a17ee9e95cbabbac401615724479570971d4
- CRLF=15

The same pattern was independently confirmed for drift.md, live-cn.md, missing.md, spec-a.md, spec-b.md, unresolved.md, and visual.md.

## 4. Root cause

acceptance/p10_independent_acceptance_harness.py::validate_and_copy_fixtures currently reads fixture bytes using:

source.read_bytes()

That treats checked-out worktree bytes as frozen identity.

The fixture manifest, however, was generated from LF Git content bytes.

Therefore the harness conflicts with the repository's accepted cross-worktree identity rule under core.autocrlf=true.

This is an acceptance-package/harness defect, not a P10 production defect and not fixture semantic drift.

## 5. Required correction

The frozen fixture identity source must be the exact candidate Git blob bytes.

For:

- acceptance/p10-fixtures/manifest.json
- all 8 acceptance/p10-fixtures/*.md fixtures

the harness must:

1. read exact current candidate Git blob bytes using binary-safe git cat-file via subprocess bytes;
2. parse the fixture manifest from Git blob bytes;
3. validate each fixture size/SHA against its Git blob bytes;
4. copy those exact Git blob bytes into the mutable acceptance workspace;
5. never use arbitrary checkout EOL representation as fixture identity.

Checkout representation may be recorded separately but cannot fail identity when the candidate Git blob matches the frozen manifest.

## 6. Invalidated stages

P10 production candidate remains unchanged.

P10-L production review findings remain valid for production code, but the acceptance-package identity amendment itself requires a new targeted formal review before re-freeze.

The current P10-M freeze and current P10-N authorization are invalidated.

No P10 closeout is authorized.

## 7. Required sequence

STOP P10-N
-> amend design/24 + design/25 + acceptance/38
-> update frozen acceptance harness
-> commit/push new amendment candidate
-> targeted formal review of acceptance-package amendment
-> new P10-M re-freeze
-> new exact-SHA P10-N authorization
-> fresh Independent Acceptance

P11 / Research MCP production / Semantic Resolver production remain closed.
