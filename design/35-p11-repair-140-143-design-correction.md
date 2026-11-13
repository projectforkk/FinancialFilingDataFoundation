# 35 — P11 Repair 140–143 Design Correction

Status: **AUTHORITATIVE DESIGN CORRECTION — P11 REPAIR 140–143**

Date: 2026-11-13

Authority:

- `design/26-p11-sec-provider-design.md`
- `design/27-p11-implementation-plan.md`
- `design/32-p11-us-scope-reopening.md`
- `design/33-p11-post-acceptance-design-correction.md`
- `design/34-p11-explicit-6k-scope-correction.md`
- `development/190-p11-fresh-full-exact-candidate-review-4.md`

## 1. Purpose and boundary

Fresh exact-candidate review 4 found four blocking gaps in the reviewed
`55fc575cdaaeebd8b686ce76120978c714ca1a28` candidate:

- namespace-authentic parser semantics were still identified as V5/v2;
- primary HTML semantic references trusted prefix spellings;
- historical submissions selection fetched every listed chunk rather than the
  chunks required to prove the requested slot;
- P7 checked `fact_source_mode` as an enum/count combination, but not as a
  source-origin invariant.

This correction freezes the contracts needed to repair P11-ISSUE-140 through
P11-ISSUE-143. It does not authorize a Formal Test Plan, Formal Acceptance,
main merge, or P11 DONE.

## 2. Parser/artifact compatibility identity (P11-ISSUE-140)

The namespace-authentic repair changed parser meaning, including the qualifying
of Inline XBRL facts, XBRL instance roots, contexts, units, dimensions,
continuations and exclusions. An artifact produced under the previous V5/v2
identity is therefore not a current artifact, even when its manifest shape and
package bytes are otherwise valid.

The new compatibility identity is:

```text
VIRTUAL_HTML_NORMALIZER_VERSION = VIRTUAL_HTML_V6
SEC_ARTIFACT_SCHEMA = p11-sec-artifacts-v2
SEC_VALIDATION_SCHEMA = p11-sec-validation-v2
SEC_REGISTRY_SCHEMA_VERSION = 4
```

`SEC_ARTIFACT_SCHEMA` remains v2 because this repair does not add, remove, or
reinterpret a persisted field layout independently of the parser identity. The
normalizer/parser version is the compatibility boundary for the changed
semantic result. `SEC_VALIDATION_SCHEMA` and the additive SEC Registry schema
remain unchanged because their stored shapes and migrations do not change.

Consequences:

1. V5/v2 parsed artifacts are `INCOMPATIBLE` and cannot qualify for
   `REUSE_DATA`.
2. A `PARSE_LOCAL` operation must execute the V6 parser and write a separate
   `<package_sha256>.VIRTUAL_HTML_V6` artifact directory.
3. Existing V5/v2 artifact files are immutable and are never edited or deleted.
4. The immutable raw SEC package remains reusable after fresh current
   discovery; archive members need not be downloaded again.
5. P7 revalidates the new artifact under the existing validation schema.
6. Accepted CN/HK Registry/data/artifact versions remain unchanged.

## 3. Namespace-authentic semantic references (P11-ISSUE-141)

Primary HTML semantic references are XBRL support references only when:

- the element local name is `schemaRef` or `linkbaseRef`; and
- the element namespace resolves to
  `http://www.xbrl.org/2003/linkbase`; and
- the reference attribute local name is `href` and its prefix resolves to
  `http://www.w3.org/1999/xlink`.

The algorithm resolves declarations in scope, supports arbitrary legal
prefixes, and rejects unbound or wrong-namespace lookalikes. XML semantic
references use the same namespace URI requirements. Unprefixed generic `href`
attributes do not authorize XBRL support acquisition.

Reference extraction remains narrowly scoped to XBRL semantic support members;
generic XML links, browser/static assets and foreign/unsafe paths remain
non-authoritative and must cause zero member fetches.

## 4. Complete-but-minimal history source selection (P11-ISSUE-142)

Online discovery and observation reconstruction use one shared deterministic
selector over the current submissions `filings.files` descriptors.

The selector:

1. always retains/fetches the current `CIK##########.json` document;
2. validates every listed history descriptor before selecting any history
   source, rejecting duplicate names, malformed dates, reversed ranges and an
   excessive selected count;
3. derives an earliest possible filing-date boundary for the requested slot:
   - FY: January 1 of the requested fiscal year;
   - Q1/Q2/Q3: the day after the prior fiscal-year endpoint from the official
     `fiscalYearEnd` metadata when valid, otherwise January 1 of the preceding
     calendar year;
4. excludes a history chunk only when its valid `filingTo` is strictly earlier
   than that boundary;
5. includes every chunk whose range can reach the boundary or later, with no
   upper filing-date cutoff, because a delayed amendment or conflicting filing
   can be filed long after the original;
6. includes a chunk with missing range metadata conservatively because its
   irrelevance cannot be proven;
7. sorts selected chunks by normalized name and applies
   `SEC_MAX_HISTORY_CHUNKS` to the selected set;
8. processes every selected chunk before deriving the candidate state; there is
   no early success break;
9. persists exactly the current source plus selected history source bytes.

This is minimal with respect to the official range metadata: a chunk is omitted
only when its upper bound proves that no filing for the requested slot could be
in it. The no-upper-bound rule is deliberate and is what preserves late-
amendment correctness. The same selector is called by online discovery and by
P7 observation reconstruction, so the selected source URL set is independently
reproducible.

## 5. P7 fact-source semantic invariants (P11-ISSUE-143)

`fact_source_mode` is a persisted semantic invariant.

For `INLINE_XBRL_PRIMARY`, P7 independently verifies that:

- the package has exactly one primary member;
- every logical fact and its evidence use the primary member SHA;
- every fact/evidence locator is the DOM/Inline model and resolves to an
  authentic Inline XBRL fact in the primary bytes;
- no logical fact/evidence row uses an XML instance member;
- contexts and units used by those rows are not borrowed from another member.

For `XBRL_INSTANCE_PRIMARY`, P7 independently verifies that:

- exactly one package member has an authentic XBRL instance root;
- every logical fact and its evidence use that one instance member SHA;
- every fact/evidence locator is the XML-path model and resolves in that member;
- no logical fact/evidence row uses the primary DOM/Inline source.

For `NO_STRUCTURED_FACTS`, the logical fact count (and fact evidence count) is
zero. No `OTHER` XML member can satisfy this mode or supply fallback facts.

Any violation is a blocking P7 issue and therefore cannot enter the reusable
P8 chain.

## 6. Governance

This correction is a development design freeze for the next candidate only.

```text
FORMAL TEST PLAN: NOT CREATED
FORMAL ACCEPTANCE: NOT RUN
MAIN MERGE: NOT RUN
P11 DONE: NO
```

The repaired candidate must still undergo a fresh exact-candidate design/code
review before any later formal lifecycle step.
