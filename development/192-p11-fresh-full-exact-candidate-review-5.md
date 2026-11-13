# 192 — P11 Fresh Full Exact-Candidate Review 5

Status: **CHANGES_REQUIRED — DESIGN/GOVERNANCE CORRECTION REQUIRED BEFORE DEVELOPMENT**

This is a fresh exact-candidate review record. It is not a Formal Test Plan,
not Formal Acceptance, not a merge authorization, and not a P11 DONE record.

## 1. Exact review identity

- Repository: `projectforkk/FinancialFilingDataFoundation`
- Current review lineage: `reconcile/p11-140-143-local-chain`
- Reviewed production candidate: `a65723c3cf17bbccf10748e2c671671a2c7dfb1b`
- Candidate parent / Review 190: `adac1075a71881dc5aec41049ead3b03d1933d4c`
- Development evidence: `development/191-p11-repair-140-143-evidence.md`
- Evidence commit: `d86c3dcec3b16ed6b528b9ef31a4a1ebe042842c`
- Candidate to evidence relation: **DOCUMENTATION ONLY — PASS**

The candidate was reviewed from the exact Git object. The evidence commit adds
only the development evidence document and does not modify `src/`, `tests/`,
`design/`, `pyproject.toml`, workflow/configuration, or runtime behavior.

## 2. Review verdict

```text
P11-ISSUE-140: FIXED
P11-ISSUE-141: FIXED
P11-ISSUE-142: PARTIAL / BLOCKING
P11-ISSUE-143: PARTIAL / BLOCKING
P11-ISSUE-144: OPEN / BLOCKING — DESIGN AUTHORITY / FREEZE GOVERNANCE

FRESH FULL EXACT-CANDIDATE REVIEW: CHANGES_REQUIRED
REVIEW_PASS: NO
FORMAL TEST PLAN: NOT AUTHORIZED
FORMAL ACCEPTANCE: NOT RUN
MAIN MERGE: NOT AUTHORIZED
P11 DONE: NO
```

The candidate's deterministic tests and Apple smoke do not close the residual
trust-boundary defects below. Green tests are not sufficient to promote this
candidate to `REVIEW_PASS`.

## 3. P11-ISSUE-142 residual defect — authenticated history inventory

`parse_submissions()` must fail closed for every entry in the authenticated
current submissions `filings.files` inventory. The candidate still has a path
that silently continues when a descriptor is not an object or when `name` is
not a string. That behavior makes history completeness unprovable and is not
an acceptable interpretation of the complete-but-minimal history contract.

The next design must freeze these rules before implementation:

- if `filings.files` is absent, the history inventory is empty and valid;
- if `filings.files` is present, it must be a list;
- every element must be an object with a non-empty string `name` passing the
  existing safe relative-name policy;
- no descriptor may be silently skipped;
- duplicate normalized names are blocking;
- `filingFrom` and `filingTo` may be missing, null, or empty as unknown range
  components, but every present non-empty value must be a string matching the
  exact `YYYY-MM-DD` syntax and a real calendar date;
- no coercion, first-ten-character truncation, trailing-garbage acceptance, or
  other normalization of malformed dates is permitted;
- when both dates are known, `filingFrom <= filingTo` is required;
- every descriptor is validated before any history selection or fetch;
- the existing complete-but-minimal selector remains: FY cutoff is January 1
  of the requested fiscal year; Q1/Q2/Q3 cutoff is the day after the prior
  fiscal-year endpoint from valid `fiscalYearEnd`, with the existing January 1
  preceding-year fallback when it is absent;
- only a valid `filingTo < cutoff` proves irrelevance; there is no upper
  filing-date cutoff because delayed amendments and conflicts can arrive later;
- missing range metadata remains conservatively selected;
- every selected chunk is processed, and online discovery and P7 observation
  reconstruction call the same selector.

## 4. P11-ISSUE-143 residual defect — immutable source-node replay

P7 must independently replay context and unit bindings from immutable package
bytes. The candidate checks source-member and locator relationships, but the
persisted `context_ref`, `unit_ref`, `context`, `unit`, and source hash fields
cannot themselves be treated as proof of the source semantics.

For every logical fact, the node resolved by its immutable locator is the
authority. The next design must require:

### INLINE_XBRL_PRIMARY

1. exactly one primary member and authentic supported Inline XBRL;
2. every logical fact and evidence row points to that primary member;
3. the fact locator resolves to an authentic Inline fact;
4. persisted `context_ref` equals the source node's actual `contextRef`;
5. persisted `unit_ref` equals the source node's actual `unitRef`;
6. every referenced context and unit ID resolves to an authentic XBRL context
   or unit in the same primary source;
7. persisted context/unit semantic payloads equal values reconstructed from
   those immutable source nodes;
8. no context or unit from another package member can satisfy the check.

### XBRL_INSTANCE_PRIMARY

1. package bytes are independently scanned for authentic
   `http://www.xbrl.org/2003/instance` / `xbrl` roots;
2. exactly one authentic instance exists and its package role is
   `XBRL_INSTANCE`;
3. an authentic instance with a conflicting package role is blocking;
4. every XML fact locator resolves to a source fact in that unique instance;
5. source-node `contextRef` and `unitRef` equal persisted references;
6. referenced contexts and units resolve in that same instance and their
   reconstructed semantics equal the persisted payloads;
7. DOM/primary Inline rows cannot appear in the XML fact universe.

### NO_STRUCTURED_FACTS

Fact count and fact evidence count must both be zero.

## 5. P11-ISSUE-144 — design authority and lifecycle freeze governance

`design/35-p11-repair-140-143-design-correction.md` is authoritative in
content, but the candidate's `design/00-design-management-index.md` still
registers only the older P11 chain and its truth matrix still presents P11 as
`26 + 32` / `DESIGN READY`. The design inventory and current P11 truth matrix
must register Design 33, Design 34, Design 35, and the new Design 36 before
further development.

The project lifecycle must explicitly prevent design and implementation from
first appearing together in one production candidate:

```text
DESIGN-ONLY COMMIT/FREEZE
→ CHATGPT DESIGN REVIEW
→ DEVELOPMENT INSTRUCTION
→ CODE CANDIDATE
```

Until ChatGPT reviews and authorizes that design freeze, no implementation of
the ISSUE-142 or ISSUE-143 repairs is authorized.

## 6. Required design-only correction

The next allowed work product is a documentation-only freeze consisting of:

- `design/36-p11-review5-trust-boundary-correction.md`;
- registration of the complete P11 design chain in
  `design/00-design-management-index.md`;
- an authoritative Review-5 section and next-cycle version contract in
  `design/27-p11-implementation-plan.md`;
- optional synchronization of the current P11 section in `PROJECT_STATUS.md`;
- this review record, `development/192-p11-fresh-full-exact-candidate-review-5.md`.

The correction must keep `VIRTUAL_HTML_V6`, `p11-sec-artifacts-v2`, and SEC
Registry version `4`, while changing the next validation compatibility identity
to `p11-sec-validation-v3` because the acceptance semantics become stronger.

No `src/`, `tests/`, runtime, workflow, or configuration change is permitted in
this cycle. No Formal Test Plan, Formal Acceptance, main merge, or P11 DONE
declaration is permitted.

## 7. Handoff

```text
STOPPED FOR DESIGN 36 FREEZE AND CHATGPT DESIGN REVIEW.
NO DEVELOPMENT IMPLEMENTATION AUTHORIZED.
NO RECONCILIATION MERGE PERFORMED.
```
