# 82 — P10-C Pre-Implementation Design Stop

Status: **STOPPED — P10-ISSUE-002 DESIGN AMENDMENT REQUIRED**

Phase:
`P10 — Codex Dynamic Research Integration`

Gate:
`P10-C — Models / Spec Freeze`

Historical authorization:
`development/81-p10-c-spec-freeze-instruction.md`

Authorization commit:
`ed8a362` — `docs: authorize P10 spec freeze gate`

P10-B review:
`development/80-p10-b-github-review.md = PASS`

## 1. Stop timing

The issue was found during P10-C pre-implementation contract review.

At discovery time:

- no `src/financial_filing_data_foundation/research/` production existed；
- no P10-C test file existed；
- no dependency/runtime change existed；
- no P8/P9 source/test change existed。

Therefore the historical P10-C authorization can be safely stopped before code.

No reset, clean, rebase, force push, or history rewrite is required.

## 2. Observed design gap

The design required:

`SHA256(canonical JSON of sorted file descriptors)`

but did not freeze the byte-level identity contract for:

- exact JSON serialization；
- hash inclusion/exclusion of bundle metadata；
- canonical persisted `relative_path`；
- raw-byte vs decoded-text hashing；
- empty-bundle behavior；
- malformed/tampered bundle vs changed-file error classification。

These choices directly affect `spec_bundle_hash`.

Leaving them to implementation would violate Design-First because two implementations could produce different bundle identities while both appearing to satisfy the old wording.

## 3. Root cause

The initial P10 design intentionally treats research-spec files as opaque bytes, but the identity definition stopped at the conceptual phrase “canonical JSON” instead of freezing the actual bytes hashed.

## 4. Approved correction

Before P10-C code:

1. amend design/24 with exact Section 8.1 canonicalization；
2. amend design/25 P10-C focused-test contract；
3. amend acceptance/38 items 16–20；
4. persist resolved project-root-relative POSIX paths；
5. hash exact raw bytes without text normalization；
6. sort descriptors by exact logical_name；
7. freeze canonical JSON as UTF-8, sorted keys, compact separators, `allow_nan=False`；
8. hash descriptor array only；
9. distinguish invalid/tampered bundle, current-file drift, and root escape；
10. commit/push the amendment as a new design baseline；
11. only then issue a new explicit P10-C authorization。

## 5. Invalidated authorization boundary

`development/81-p10-c-spec-freeze-instruction.md` remains historical evidence that P10-C was authorized under the earlier baseline.

It is superseded **before any production/test implementation** by P10-ISSUE-002.

No implementation evidence under development/81 is valid or expected.

A later P10-C instruction must bind to the new amendment SHA and use a new evidence filename.

## 6. Gate verdict

# STOPPED

P10-C code remains prohibited until the P10-ISSUE-002 design amendment is committed/pushed.

P10-D and later remain closed.

Research MCP production, Semantic Resolver production, and P11 production remain closed.
