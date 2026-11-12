# 32 — P11 US Scope Reopening Contract

Status: **ACTIVE — P11 REPAIR REQUIRED / PRIOR ACCEPTANCE SUSPENDED**

Date opened: 2026-11-09
Design correction: 2026-11-11

Detailed correction authority:
`design/33-p11-post-acceptance-design-correction.md`

Re-audit:
`development/178-p11-full-design-code-consistency-reaudit.md`

## 1. Decision

The accepted production baseline remains CN + HK.

P11 US remains an active feature-branch initiative and is not accepted production
until the corrected design is implemented, independently reviewed, formally tested
and merged.

The previous P11 formal acceptance is retained as historical evidence for the
scenarios it executed, but it does not authorize main integration after the
2026-11-11 re-audit.

`design/30-project-final-cn-hk-scope.md` remains historical truth for the CN/HK
closeout.

## 2. P11 objective

Add official SEC/EDGAR filing acquisition and deterministic local parsing for
US-listed issuers, with a first-class HTML / Inline XBRL / XBRL path.

Source-of-truth chain:

```text
CIK identity
→ current SEC ticker mapping when ticker is used
→ current submissions/history discovery observation
→ accession candidate decision
→ SEC Archives filing package
→ immutable raw members
→ exactly one logical fact-source mode
→ deterministic page/section/table/raw-fact/evidence artifacts
→ P7 validation bound to the discovery observation
→ P8 read-only snapshot access
```

## 3. Accepted main vs merge-ready feature branch

Until corrected P11 acceptance and merge:

```text
accepted main SUPPORTED_MARKETS = (CN, HK)
accepted main P11_SEC_PROVIDER = UNAVAILABLE
```

The P11 feature branch may contain the complete merge-ready production behavior,
including US public market declarations, before acceptance.

That does not make US accepted production because the branch is not main.

This rule exists so formal acceptance tests the exact production behavior that will
be merged. No production-enablement source edit is permitted after ACCEPTANCE_PASS.

The merge-ready candidate must not require `FFDF_P11_US_DEV=1` for normal US
CLI/P8 behavior.

## 4. US filing scope

Domestic operating companies:

- FY → Form 10-K;
- Q1 → Form 10-Q;
- Q2 → Form 10-Q;
- Q3 → Form 10-Q.

Foreign private issuers:

- FY → Form 20-F or 40-F;
- explicit Form 6-K acquisition is deferred from P11 v1 under
  `design/34-p11-explicit-6k-scope-correction.md`;
- `6-K`/`6-K/A` must not be auto-mapped to a standardized quarterly slot, ignored as
  an override, or acquired through the periodic-slot path.

Not required periodic slots:

- 8-K;
- proxy statements;
- registration statements.

## 5. Current discovery requirement

For online US `acquire` and `ingest`, current SEC submissions metadata is checked
before local reuse planning.

This is required even when a package and compatible parsed artifact already exist.

The purpose is to detect:

- a later /A amendment;
- another conflicting filing candidate;
- current not-found/identity changes.

Repeat runs may still avoid archive member downloads and parser work.

`status` is local-only and reports state as of the latest discovery observation.

## 6. Fact-source rule

Every package uses exactly one logical fact-source mode:

- `INLINE_XBRL_PRIMARY` when the primary document contains supported Inline XBRL
  facts;
- `XBRL_INSTANCE_PRIMARY` only when there is no Inline XBRL fact source and one
  verified instance is unambiguous.

An extracted instance must not duplicate the primary Inline XBRL logical fact set.

## 7. Compatibility promise

P11 must preserve:

- ORIGINAL_DOCUMENT_IMMUTABLE;
- NO_GUESSING;
- EVIDENCE_REQUIRED;
- INCREMENTAL_FIRST;
- MCP_AI_API_CALLS = FORBIDDEN;
- P8 exact accepted tool names;
- P9 overlay semantics;
- P10 dynamic-research responsibilities;
- accepted CN/HK source/artifact behavior.

Incremental-first now explicitly means avoiding redundant archive-byte/parser work
after current mutable discovery metadata is checked.

## 8. Current truth

As of this correction:

```text
P11 prior ACCEPTANCE_PASS = SUSPENDED FOR MERGE
P11 corrected design = FROZEN WHEN DESIGN-CORRECTION COMMIT IS RECORDED
P11 repair implementation = REQUIRED
P11 main merge = NOT AUTHORIZED
P11 accepted production availability = UNAVAILABLE
```

Target state after corrected independent acceptance and exact-candidate merge:

`P11_SEC_PROVIDER = AVAILABLE`.
