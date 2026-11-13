# 36 — P11 Review 5 Trust-Boundary Correction

Status: **AUTHORITATIVE DESIGN CORRECTION — REVIEW 5**
Development: **NOT YET AUTHORIZED**

This document is a design/governance freeze only. It does not authorize source
changes, test changes, a Formal Test Plan, Formal Acceptance, main integration,
or a P11 DONE declaration.

## 1. Authority and lifecycle boundary

The authority chain for the next P11 development cycle is:

```text
design/26-p11-sec-provider-design.md
design/27-p11-implementation-plan.md
design/32-p11-us-scope-reopening.md
design/33-p11-post-acceptance-design-correction.md
design/34-p11-explicit-6k-scope-correction.md
design/35-p11-repair-140-143-design-correction.md
development/192-p11-fresh-full-exact-candidate-review-5.md
design/36-p11-review5-trust-boundary-correction.md
```

The required lifecycle is now explicitly:

```text
DESIGN-ONLY COMMIT/FREEZE
→ CHATGPT DESIGN REVIEW
→ DEVELOPMENT INSTRUCTION
→ CODE CANDIDATE
→ DEVELOPMENT TESTS
→ EXACT PRODUCTION CANDIDATE FREEZE
→ DEVELOPMENT EVIDENCE
→ CHATGPT FRESH FULL EXACT-CANDIDATE REVIEW
```

Design and implementation must not first appear together in one production
candidate commit. Development of the ISSUE-142 and ISSUE-143 repairs remains
blocked until ChatGPT reviews this exact Design 36 freeze and issues explicit
development authorization.

## 2. ISSUE-142 — authenticated history inventory is fail-closed

### 2.1 Current submissions inventory

For the authenticated current SEC submissions response:

- If `filings.files` is absent, the history inventory is empty. This is valid.
- If `filings.files` is present, it must be a list.
- Every element must be validated before selection or fetch.
- Every descriptor must be an object with a non-empty string `name` passing the
  existing safe relative-name policy.
- A non-object descriptor, a descriptor with a non-string name, an empty name,
  or an unsafe name is a blocking discovery error. No descriptor may be
  silently skipped.
- Duplicate normalized names are a blocking discovery error.

### 2.2 Strict history range syntax

`filingFrom` and `filingTo` are optional range components. For either field:

```text
missing / null / empty  = unknown range component
present non-empty       = string required
syntax                  = exact YYYY-MM-DD
calendar                = real calendar date required
```

The parser must not coerce values with `str()`, truncate to the first ten
characters, accept trailing characters, or otherwise normalize malformed input
into an apparently valid date. If both dates are present, the invariant
`filingFrom <= filingTo` is required; otherwise discovery blocks.

All descriptors are validated before any selected history source is fetched.
This ensures an invalid, unauthenticated-to-the-contract inventory cannot be
partially accepted merely because another chunk contains a candidate.

### 2.3 Complete-but-minimal selection

The existing selector remains shared by online discovery and P7 observation
reconstruction.

For FY:

```text
cutoff = January 1 of the requested fiscal year
```

For Q1/Q2/Q3:

```text
cutoff = the day after the prior fiscal-year endpoint
```

The quarterly endpoint comes from valid official `fiscalYearEnd`. If that field
is absent, the existing conservative fallback is January 1 of
`fiscal_year - 1`. A non-empty invalid `fiscalYearEnd` remains a blocking
submissions parse error.

A history chunk is excluded only when its valid `filingTo` is strictly earlier
than the cutoff:

```text
valid filingTo < cutoff  → proven irrelevant → exclude
otherwise                → retain/select
```

There is deliberately no upper filing-date cutoff. Delayed amendments and
conflicting filings can occur after the original filing period. Missing range
metadata remains conservatively selected. Every selected chunk is processed
before candidate state is derived, and the shared selector is the only source
of truth for both online and reconstructed observations.

## 3. ISSUE-143 — immutable source-node replay is authoritative

`fact_source_mode` remains a persisted semantic invariant, but persisted
metadata is not proof. For every logical fact, P7 must resolve its immutable
locator against package member bytes and treat the resolved source node as the
authority for references and semantics.

### 3.1 INLINE_XBRL_PRIMARY

P7 must independently prove:

1. exactly one package member has the primary-document role;
2. its immutable bytes contain authentic supported Inline XBRL;
3. every logical fact and evidence row uses that primary member SHA;
4. every fact locator resolves to an authentic Inline XBRL fact node;
5. persisted `context_ref` equals the source node's actual `contextRef`;
6. persisted `unit_ref` equals the source node's actual `unitRef`;
7. when `contextRef` exists, its ID resolves to an authentic XBRL context in
   the same primary source;
8. when `unitRef` exists, its ID resolves to an authentic XBRL unit in the same
   primary source;
9. the persisted context/unit semantic payload equals the payload reconstructed
   from those immutable source nodes;
10. no context or unit from another package member can satisfy the resolution.

A persisted `source_member_sha256`, `context_ref`, `unit_ref`, `context`, or
`unit` declaration by itself never proves the source semantics.

### 3.2 XBRL_INSTANCE_PRIMARY

P7 must independently scan all package member bytes for an authentic XBRL
instance root:

```text
namespace = http://www.xbrl.org/2003/instance
local name = xbrl
```

Exactly one authentic instance is required, and that member's package role must
be `XBRL_INSTANCE`. An authentic instance with a conflicting role is a
blocking package/source-semantic inconsistency; it must not be ignored.

For every logical XML fact, P7 must prove:

1. the member is the unique authentic instance;
2. the XML locator resolves to an authentic source fact node;
3. source-node `contextRef` equals persisted `context_ref`;
4. source-node `unitRef` equals persisted `unit_ref`;
5. referenced context and unit IDs resolve in that same authentic instance;
6. persisted context/unit semantics equal reconstructed values from those
   immutable nodes;
7. DOM/primary Inline rows cannot enter the XML fact universe.

### 3.3 NO_STRUCTURED_FACTS

The mode requires:

```text
fact count = 0
fact evidence count = 0
```

No `OTHER` member, generic XML, or persisted metadata can supply fallback
facts.

## 4. Compatibility identity for the next repair

P7 hardening changes validation acceptance semantics. It does not change the
parser's semantic identity or the persisted artifact layout. Keep:

```text
SEC_DISCOVERY_SCHEMA = p11-sec-discovery-v1
VIRTUAL_HTML_NORMALIZER_VERSION = VIRTUAL_HTML_V6
SEC_ARTIFACT_SCHEMA = p11-sec-artifacts-v2
SEC_REGISTRY_SCHEMA_VERSION = 4
```

Change the next validation compatibility identity to:

```text
SEC_VALIDATION_SCHEMA = p11-sec-validation-v3
```

Reason: a V6/v2 parsed artifact validated under the weaker
`p11-sec-validation-v2` contract must not silently qualify for `REUSE_DATA`
after source-node replay is introduced.

Expected migration behavior:

```text
existing V6 parsed artifact:
  may remain reusable as local parse input

old validation-v2 result:
  INCOMPATIBLE / must not qualify for REUSE_DATA

raw SEC package:
  reusable

new P7:
  must execute

new validation result:
  p11-sec-validation-v3
```

No parsed artifact rewrite is required solely because the validation contract
changed. Original SEC package bytes remain immutable. Discovery observation
layout remains `p11-sec-discovery-v1`, provided current verification rejects a
source set that does not match the current shared history selector.

## 5. Governance and authorization

Design 36 is frozen for ChatGPT design review only:

```text
P11 Review 5 = CHANGES_REQUIRED
ISSUE-140 = FIXED
ISSUE-141 = FIXED
ISSUE-142 = OPEN / PARTIAL
ISSUE-143 = OPEN / PARTIAL
ISSUE-144 = DESIGN GOVERNANCE CORRECTION
DEVELOPMENT = NOT AUTHORIZED
FORMAL TEST PLAN = NOT CREATED / NOT AUTHORIZED
FORMAL ACCEPTANCE = NOT RUN
MAIN MERGE = NOT AUTHORIZED
P11 DONE = NO
```

The next action is ChatGPT review of this exact Design 36 commit. No source,
test, runtime, workflow, or configuration implementation may begin before that
review authorizes development.
