# 33 — P11 Post-Acceptance Design Correction

Status: **AUTHORITATIVE DESIGN CORRECTION — MUST BE READ WITH DESIGN 26/27/32**

Date: 2026-11-11

Trigger:
`development/178-p11-full-design-code-consistency-reaudit.md`

Prior production candidate:
`9b7fcc9fc37a423eaafd1dde762e9c81d475df9e`

Prior acceptance record:
`development/177-p11-final-acceptance-review-2.md`

## 1. Purpose

A fresh design/code audit after formal acceptance found scenarios that the previous
test plan did not cover.

The previous test outputs remain historical evidence for the commands that actually
ran. The acceptance verdict is insufficient for main integration because the
underlying design contract omitted important lifecycle and semantic rules.

This document freezes those corrected decisions.

Where an older P11 document conflicts with this correction, the corrected text in
design 26/27/32 and this document governs.

## 2. DC-01 — Online discovery precedes reuse

Decision:

- immutable package/parser reuse remains;
- current mutable SEC submissions metadata is revalidated on every online
  `acquire` / `ingest`;
- reuse planning occurs only after a current candidate decision;
- no TTL shortcut is used for these online commands;
- `status` remains local-only and explicitly reports discovery as-of time.

Reason:

A cached original filing must not permanently hide an amendment filed later.

Required persisted object:

`SEC discovery observation`.

It binds slot identity, official source hashes, candidate set, selected accession,
conflict/amendment state and retrieved_at.

## 3. DC-02 — Ticker aliases are re-resolved online

Decision:

- explicit CIK remains authoritative and bypasses ticker-map lookup;
- online ticker-based acquire/ingest fetches the current official SEC ticker map;
- cached ticker source bytes are evidence, not a silent current-identity substitute;
- any cached lookup reparses verified source bytes;
- a derivative serialized mapping cannot disagree with those bytes.

## 4. DC-03 — Exactly one logical fact source

Decision:

### INLINE_XBRL_PRIMARY

If primary HTML contains supported Inline XBRL facts:

- P6 logical facts come only from primary iXBRL;
- extracted instance facts do not create additional logical P6 rows;
- primary iXBRL contexts/units are authoritative for those facts.

### XBRL_INSTANCE_PRIMARY

If there are no primary Inline XBRL facts:

- exactly one verified XBRL instance may become the logical fact source;
- multiple plausible instances are REVIEW_REQUIRED/fail closed.

There is no "concatenate both sources" mode.

Reason:

Source duplication is not equivalent to two economic facts.

## 5. DC-04 — Inline XBRL continuation/exclude is part of fact correctness

Reference basis:

XBRL International Inline XBRL 1.1 defines `ix:continuation` as the mechanism for
splitting text content within a document.

Decision:

- resolve continuedAt chains deterministically;
- support chained continuations;
- reject missing/duplicate/cyclic continuation references;
- remove ix:exclude content from the logical fact value;
- retain all source fragments for evidence;
- one logical fact may therefore have multi-fragment evidence.

This is a parser-semantics change and requires compatibility invalidation.

## 6. DC-05 — Generic XML is not XBRL truth

Decision:

- no acquisition sweep of every XML-family filename;
- use deterministic SEC XBRL attachment metadata and filing-local references;
- `OTHER` XML never supplies facts, contexts or units;
- primary iXBRL facts cannot borrow a same-ID context/unit from another member.

Reason:

An unrelated XML exhibit must not repair or alter a filing fact.

## 7. DC-06 — Package provenance is verified separately from package SHA

Decision:

The existing package SHA formula remains unchanged.

Provenance integrity is enforced by:

- exact source URL ↔ package CIK/accession/relative-name verification;
- manifest ↔ Registry `source_packages` comparison;
- member ↔ Registry `package_members` comparison;
- P7 and P8 fail-closed behavior on mismatch.

The package hash continues to identify the immutable member-byte set.

## 8. DC-07 — DOM tables use logical span grid

Decision:

- column_count comes from occupied logical grid width;
- colspan/rowspan affect grid width/occupancy;
- row 0 is not automatically a header;
- header_tree is based on actual header cells and span coverage.

## 9. DC-08 — Formal acceptance must test production behavior

Decision:

The merge-ready feature-branch candidate contains all production enablement.

It must:

- run US CLI/P8 without `FFDF_P11_US_DEV`;
- contain intended US supported-market/capability declarations;
- remain unmerged until acceptance.

After ACCEPTANCE_PASS, Gate I1 is an exact-candidate merge gate, not a production
implementation gate.

Any production/test source change after acceptance invalidates acceptance.

## 10. Version correction

Required target baseline:

```text
REGISTRY_SCHEMA_VERSION = 1
SEC_REGISTRY_SCHEMA_VERSION = 4
SEC_DISCOVERY_SCHEMA = p11-sec-discovery-v1
VIRTUAL_HTML_NORMALIZER_VERSION = VIRTUAL_HTML_V5
SEC_ARTIFACT_SCHEMA = p11-sec-artifacts-v2
SEC_VALIDATION_SCHEMA = p11-sec-validation-v2
```

Consequences:

- old V4/v1 US parsed artifacts are incompatible;
- old immutable SEC raw packages can be reused after current discovery and reparsed;
- SEC Registry v3 migrates additively to v4;
- accepted CN/HK data and legacy Registry version remain unchanged.

## 11. Issue mapping

```text
P11-ISSUE-123 → DC-01
P11-ISSUE-124 → DC-03
P11-ISSUE-125 → DC-04
P11-ISSUE-126 → DC-05
P11-ISSUE-127 → DC-02
P11-ISSUE-128 → DC-06
P11-ISSUE-129 → DC-07
P11-ISSUE-130 → DC-08
```

## 12. Acceptance invalidation boundary

The prior acceptance record remains immutable historical evidence.

It no longer authorizes:

- main merge;
- US production availability;
- production capability declaration.

A new merge-ready production candidate must pass:

```text
exact-candidate review
→ new formal test plan
→ new formal execution/evidence
→ independent verification
→ ACCEPTANCE_PASS
```

before main integration.
