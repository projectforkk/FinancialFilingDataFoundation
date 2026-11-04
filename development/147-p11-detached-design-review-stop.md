# 147 — P11 Detached Design Review Stop

Status: **FAIL / STOP — DESIGN CONTRACT INCOMPLETE / PRODUCTION CLOSED**

Phase:
P11 — US SEC Provider

Reviewed exact candidate:
`3ccaedc14a4c0f3f222cd192c8b7e1479d787ccd`

Detached review worktree:
`D:\\Codex\\FinancialFilingDataFoundation\\worktrees\\review\\p11-design-3ccaedc`

Review authorization:
`development/146-p11-detached-design-review-instruction.md`

## 1. Candidate integrity

PASS:

- detached HEAD exact candidate;
- clean detached worktree;
- candidate diff vs `5f64f748...` contains design/governance only;
- `src/tests/integration/runtime-locks` diff = NONE;
- `git diff --check` = PASS;
- UTF-8 decode = PASS;
- BOM = absent;
- U+FFFD replacement character = absent.

The stop is caused by design-contract gaps, not repository drift.

## 2. Official-source spot check

Current SEC official documentation confirms:

- current fair-access guideline is <=10 requests/sec in aggregate for a user, regardless of number of machines;
- automated tools may be blocked for excessive/unclassified access;
- Submissions API uses 10-digit zero-padded CIK;
- current submissions may reference historical JSON shards;
- ticker/CIK mapping accuracy/scope is not guaranteed;
- Inline XBRL applies to 10-K/10-Q and relevant 8-K, and to 20-F/40-F and relevant 6-K;
- SEC XBRL APIs aggregate standard-taxonomy/entity-wide facts and therefore cannot replace filing-local custom-taxonomy evidence.

## 3. Material findings

### P11-ISSUE-010 — Rate-limit scope is unsafe

Candidate says:
`hard per-process ceiling <=10 requests/sec`.

SEC guidance is aggregate, not per-process.

Two simultaneous FFDF processes could each comply with the candidate while collectively violating SEC fair access.

Required correction:

- freeze a cross-process project-local limiter;
- no burst behavior above frozen ceiling;
- define behavior when aggregate coordination is unavailable;
- acceptance must run concurrent-process probe.

### P11-ISSUE-011 — Source-package identity payload is underspecified

Candidate defines:

`source_package_sha256 = SHA256(canonical package manifest identity payload)`

but does not freeze the exact identity object/keys, sorting, normalization or whether source URLs/media types/dependency relations participate.

Implementation would have to invent a hash contract.

Required correction:

- exact package identity schema;
- exact asset identity keys;
- exact sort;
- exact canonical JSON;
- exact exclusion list.

### P11-ISSUE-012 — Persisted local-content path semantics are underspecified

`source_assets.jsonl` requires `local_content_path`, but does not state:

- absolute vs relative;
- root of resolution;
- separator normalization;
- traversal rules;
- whether it participates in semantic equality/identity.

Required correction:

- project-root-relative POSIX only;
- resolved target must remain inside configured P11 raw root;
- no absolute/drive-relative/traversal;
- excluded from all deterministic IDs/package identity.

### P11-ISSUE-013 — DOM/source-node locator identity is not frozen

Candidate uses:

- `dom_path`;
- `source_locator`;
- `exact source node identity`;

but gives no canonical path algorithm.

Different parsers/implementers can generate different IDs for the same source node.

Required correction:

- canonical HTML DOM path algorithm;
- canonical XML/iXBRL expanded-QName path algorithm;
- exact locator object per locator_type;
- exact source-node identity used by fact/evidence/table/cell/segment IDs.

### P11-ISSUE-014 — Deterministic v2 ID formulas are incomplete

Candidate states IDs use canonical JSON but does not freeze exact formulas for:

- `parse_run_id`;
- `segment_id`;
- `section_id`;
- `table_id`;
- `cell_id`.

Required correction:
freeze exact input object for each ID and config hash semantics.

### P11-ISSUE-015 — Inline XBRL raw/transformed value rule is ambiguous

Candidate says `raw_value` is filing-visible lexical text “or exact source lexical content according to the parser rule frozen by P11”, but no exact rule is actually frozen.

This affects raw truth and numeric evidence.

Required correction:

- exact raw_value text-content rule;
- exact transformed numeric boundary;
- preserve scale/sign/format and source locator;
- if Arelle-dependent transformation details cannot be frozen before P11-B, explicitly require a Design-First P11-G parser-contract freeze before parser implementation.

### P11-ISSUE-016 — CIK/accession/path validation grammar is incomplete

Design gives conceptual normalization but not exact grammar.

Required correction:

- CIK accepted input grammar and normalized form;
- accession grammar;
- primaryDocument safe-basename grammar/path rules;
- test/acceptance cases.

## 4. Classification

These are pre-production design defects.

No production/test/runtime code exists or was changed.

No P0-P10 contract was affected.

## 5. Required Design-First action

```text
STOP detached design review
→ amend design/26
→ amend design/27
→ amend design/30
→ amend acceptance/41
→ amend audit/reconciliation issue log
→ commit/push new design candidate
→ create fresh detached review of new exact candidate
```

No P11 development authorization may be issued from candidate `3ccaedc...`.

## 6. Verdict

# FAIL / STOP

Candidate `3ccaedc14a4c0f3f222cd192c8b7e1479d787ccd` is INELIGIBLE for `P11_READY_FOR_DEVELOPMENT`.

P11 production remains CLOSED.
