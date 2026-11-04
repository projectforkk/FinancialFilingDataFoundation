# 105 — P10-G Detached Documentation Review Stop

Status: **STOPPED — P10-ISSUE-006 ARTIFACT IDENTITY AMENDMENT REQUIRED**

Phase:
`P10 — Codex Dynamic Research Integration`

Gate:
`P10-G — Thin Integration Instruction`

Candidate:
`3a805a8f333ac20770d6aec1c8285d93993d18fc`

Review authorization:
`69644cf659d423aefb1311316a966c00cde40a78`

Detached review worktree:
`D:\\Codex\\FinancialFilingDataFoundation\\worktrees\\review\\p10-g-69644cf`

## 1. Stop timing

The P10-G detached review was in progress.

No candidate artifact modification occurred in the detached worktree.

No P10-H work had started.

The review was stopped before PASS/FAIL because the frozen artifact SHA semantics were ambiguous across Windows worktrees.

## 2. Observed facts

Development evidence recorded:

`ef10406c9957f7a68a9af001c913deef0a057e166100a2d852c0c8fcd2c46296`

as the integration artifact SHA256.

Active worktree bytes:

```text
sha256=ef10406c9957f7a68a9af001c913deef0a057e166100a2d852c0c8fcd2c46296
length=10383
CRLF=0
LF=364
```

Fresh detached worktree bytes for the same tracked candidate:

```text
sha256=4b78fef289f1ba4471240d884127c844cbb36bb1954a7df5d31a05cb06e19c01
length=10747
CRLF=364
LF=364
```

Exact candidate Git blob bytes:

```text
sha256=ef10406c9957f7a68a9af001c913deef0a057e166100a2d852c0c8fcd2c46296
length=10383
CRLF=0
LF=364
```

Detached bytes normalized from CRLF to LF equal the exact candidate Git blob byte-for-byte.

Repository environment:

```text
core.autocrlf=true
integration/p10/FFDF_RESEARCH_INTEGRATION.md: text=unspecified
integration/p10/FFDF_RESEARCH_INTEGRATION.md: eol=unspecified
```

## 3. Root cause

The candidate Markdown is tracked as text without an explicit `.gitattributes` EOL rule.

Git stores the candidate blob with LF bytes.

A freshly checked-out Windows worktree may apply `core.autocrlf=true` and materialize CRLF bytes.

Therefore:

`SHA256(arbitrary checked-out worktree bytes)`

is not a stable cross-worktree identity for this tracked Markdown artifact.

The P10-G design/evidence/review instruction froze an artifact SHA without defining whether the bytes were:

- Git blob bytes;
- active-worktree bytes;
- detached-worktree bytes;
- normalized text bytes.

## 4. Impact

The integration instruction content itself is unchanged and semantically identical.

No P10 production correctness issue was found.

However, Code Review / Acceptance could report a false identity mismatch for the same exact Git candidate depending on checkout EOL conversion.

This makes the P10-G artifact identity contract non-deterministic.

## 5. Design-First correction

Before resuming P10-G review, freeze:

1. tracked integration instruction identity = SHA256 of the exact candidate **Git blob content bytes**;
2. the blob must decode as UTF-8 and contain no UTF-8 BOM;
3. the frozen Git blob SHA256 for candidate `3a805a8...` remains:
   `ef10406c9957f7a68a9af001c913deef0a057e166100a2d852c0c8fcd2c46296`;
4. working-tree EOL smudge is not artifact identity;
5. review/acceptance may inspect worktree text, but identity comparison must use exact Git blob bytes from the frozen candidate;
6. no `.gitattributes` change is required for P10-G because runtime semantics do not depend on Markdown newline style;
7. P10-G candidate content need not change;
8. acceptance must freeze the candidate commit plus Git-blob SHA, not a checkout-specific byte hash;
9. blob extraction for hash verification must be binary-safe; a PowerShell object/text pipeline is not acceptable because it can decode/re-encode Git stdout before hashing.

## 6. Required sequence

```text
STOP P10-G review
→ amend design/24
→ amend design/25
→ amend acceptance/38
→ update governance/status
→ commit/push new design baseline
→ new explicit P10-G review authorization
→ rerun detached review
```

P10-H and later remain closed.

Research MCP production, Semantic Resolver production, and P11 production remain closed.
