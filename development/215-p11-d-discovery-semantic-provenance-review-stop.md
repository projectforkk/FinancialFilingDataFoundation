# 215 — P11-D Discovery Candidate Semantic / Provenance Review STOP

Status: **STOP — P11-ISSUE-040 OPEN / CANDIDATE INELIGIBLE / P11-D IMPLEMENTATION CLOSED**

Reviewed exact candidate:
`54d132024065f02e92621a68aabd1da278da5c9a`

Authorization:
`development/214-p11-d-http-discovery-final-design-review-authorization.md`

Fresh detached worktree:
`D:\Codex\FinancialFilingDataFoundation\worktrees\review\p11-d-design-54d1320`

## Integrity checks before STOP

PASS:

- exact HEAD = candidate;
- detached branch = empty;
- worktree clean;
- `git diff --check` = PASS;
- candidate scope since `65a6da25a0608f6de0b08278fcc094ca68b57829` = design/governance/acceptance only;
- no `src/`, `tests/`, `integration/`, `runtime-locks/` change;
- development/213 contract SHA matches the canonical Git blob SHA256 `30aa7a1b90a54577bc4a501e7417199c8f4b1238bddc5f50f245b04e271865de` (Windows checkout CRLF changes the filesystem-byte hash only; committed blob is exact).

## P11-ISSUE-040

Manual semantic/cross-gate review found two material public-contract inconsistencies.

### A. Provenance field participates in duplicate semantic equality

`SecDiscoveryCandidate` contains:

`submission_source_url: str`

Section 17 then says same-accession duplicates dedupe only if **every SecDiscoveryCandidate field is equal**.

That is incorrect for a filing appearing in both current Submissions and a historical shard:

- filing semantics may be identical;
- current source URL and historical-shard source URL are necessarily different;
- exact dataclass-field equality therefore produces a false `P11_SUBMISSIONS_INVALID` conflict.

This also contradicts the accepted requirement that source/shard order and provenance-only diagnostics are not identity inputs.

### B. XBRL boolean nullability contradicts the frozen validator

Public API declares:

- `is_xbrl: bool | None`;
- `is_inline_xbrl: bool | None`.

But the same contract requires:

- both parallel arrays to exist for every accepted current/history row;
- values to be JSON integer exactly 0 or 1;
- normalized accepted candidate booleans to be non-null.

The public type permits a state that the frozen validator says cannot exist.

## Required Design-First remediation

Before another candidate can be frozen:

1. separate filing semantic equality/order from discovery provenance;
2. provenance must remain inspectable but must not cause a false semantic conflict;
3. duplicate same-accession equal-semantic rows from different source URLs must dedupe deterministically;
4. contributing provenance URLs must have one exact canonical representation/order;
5. a differing semantic filing field must still fail closed with `P11_SUBMISSIONS_INVALID`;
6. XBRL boolean public fields must match the accepted non-null validator contract;
7. add mandatory tests for current/history duplicate provenance, source-order invariance, provenance union/order and non-null booleans;
8. preserve all previously frozen HTTP/security/rate-gate behavior unchanged.

## Verdict

# STOP

Candidate `54d132024065f02e92621a68aabd1da278da5c9a` is INELIGIBLE.

P11-ISSUE-040 is OPEN.

P11-D implementation remains NOT AUTHORIZED.
P11 provider production remains CLOSED.