# 37 — P11 Review 5 Freeze Consistency and Raw Fact Binding

Status: **AUTHORITATIVE DESIGN CORRECTION — REVIEW 5 DESIGN FREEZE CORRECTION**

Development: **NOT YET AUTHORIZED**

Design 36 remains an immutable historical Design Freeze attempt. This forward
correction does not modify Design 36 in place and does not authorize production
or test implementation.

## 1. Authority chain and lifecycle

The complete authority chain for the next P11 development cycle is:

```text
design/26-p11-sec-provider-design.md
design/27-p11-implementation-plan.md
design/32-p11-us-scope-reopening.md
design/33-p11-post-acceptance-design-correction.md
design/34-p11-explicit-6k-scope-correction.md
design/35-p11-repair-140-143-design-correction.md
design/36-p11-review5-trust-boundary-correction.md
development/192-p11-fresh-full-exact-candidate-review-5.md
development/193-p11-design-freeze-review-result.md
design/37-p11-review5-freeze-consistency-and-raw-fact-binding.md
```

The required lifecycle is:

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
candidate commit. Development remains blocked until ChatGPT reviews this exact
Design 37 freeze and explicitly returns:

```text
DESIGN_FREEZE_PASS
DEVELOPMENT_AUTHORIZED
```

## 2. ISSUE-142 — preserve the fail-closed history contract

Design 37 affirms Design 36 ISSUE-142 unchanged.

For the authenticated current submissions response:

```text
filings.files absent
→ valid empty history inventory

filings.files present
→ MUST be a list

every descriptor
→ MUST be validated before any history fetch
```

Every descriptor must be an object with a non-empty string `name` passing the
existing safe relative-name policy. Invalid, non-object, missing-name,
non-string-name, empty-name, and unsafe-name descriptors are blocking. No
descriptor may be silently skipped. Duplicate normalized names are blocking.

For `filingFrom` and `filingTo`:

```text
missing / null / empty
→ unknown range component

present
→ string only
→ exact YYYY-MM-DD only
→ valid calendar date only
```

No `str()` coercion, `[:10]` truncation, trailing garbage, or other repair of a
malformed value is allowed. A valid `filingFrom > filingTo` range is blocking.
All descriptors must be validated before any selected history chunk is fetched.

The shared online/P7 selector remains mandatory:

- FY cutoff is January 1 of the requested fiscal year;
- quarterly selection uses the day after the prior fiscal-year endpoint from
  valid official `fiscalYearEnd`, with the existing preceding-year fallback
  only when that field is absent;
- an invalid non-empty `fiscalYearEnd` fails closed;
- only a valid `filingTo < cutoff` proves irrelevance;
- there is no upper filing-date cutoff;
- missing range metadata is conservatively included;
- all selected chunks are processed before candidate state is derived.

## 3. ISSUE-143 — preserve immutable source-node replay

Design 37 affirms that immutable source-node replay is authoritative for:

```text
contextRef
unitRef
context
unit
source member
locator model
```

Persisted metadata and source-member declarations are assertions, not proof.
P7 must resolve each logical fact locator against immutable package bytes and
use the resolved source node as the authority.

For `INLINE_XBRL_PRIMARY`, the existing Design 36 requirements remain:

- exactly one primary member with authentic supported Inline XBRL;
- every fact/evidence row uses the primary member;
- every fact locator resolves to an authentic Inline fact;
- source-node `contextRef` and `unitRef` equal persisted references;
- referenced contexts and units resolve in the same primary source;
- reconstructed context/unit semantics equal persisted payloads;
- another package member cannot satisfy context/unit resolution.

For `XBRL_INSTANCE_PRIMARY`, the existing Design 36 requirements remain:

- scan all member bytes for authentic instance roots;
- require exactly one authentic root with package role `XBRL_INSTANCE`;
- a conflicting role is blocking;
- every XML locator resolves to a source fact in that instance;
- source references and reconstructed context/unit semantics equal persisted
  values;
- DOM/Inline rows cannot enter the XML fact universe.

For `NO_STRUCTURED_FACTS`, fact count and fact evidence count must both be zero.

## 4. ISSUE-145 — Raw Fact semantic payload is independently bound

### 4.1 Principle

For every logical Raw Fact:

```text
immutable package member bytes
+ exact fact locator
= authoritative source fact
```

Persisted Raw Fact fields are assertions. P7 must independently replay the
source node and compare the persisted Raw Fact against a deterministic
source-fact projection. A valid Evidence object must not validate a
semantically altered Raw Fact.

### 4.2 Canonical source-fact projection

For `INLINE_XBRL_PRIMARY`, derive from the authentic Inline source node at
minimum:

```text
source_member_sha256
fact locator
raw_qname / raw metric identity
logical raw value including continuation chain
fact kind
contextRef
unitRef
decimals
precision
scale
sign
format
nil
continuedAt / continuation semantics
hidden/source visibility classification where persisted
```

For `XBRL_INSTANCE_PRIMARY`, derive from the authentic XML source fact at
minimum:

```text
source_member_sha256
XML locator
raw QName
raw value
fact kind
contextRef
unitRef
decimals
precision
scale
sign
nil
```

Fields not applicable to a source model use the deterministic null/empty
representation already defined by the parser contract.

### 4.3 Required Raw Fact equality

P7 must prove:

```text
fact.raw_value == replayed source logical value
fact.raw_qname == replayed source QName
fact.raw_metric_name == expected raw metric identity
fact.context_ref == actual source contextRef
fact.unit_ref == actual source unitRef
source-derived attributes == replayed attributes
fact.source_member_sha256 == actual source member
fact member locator == replayed source locator
```

Where `parsed_numeric_candidate` is persisted, it must equal a deterministic
recomputation from authoritative raw-value and nil semantics. The persisted
numeric candidate must never be trusted as independent evidence.

### 4.4 Raw Fact and Evidence semantic equality

For each fact/evidence pair, P7 must require at minimum:

```text
fact.raw_fact_id ↔ evidence.raw_fact_id
fact.evidence_id ↔ evidence.evidence_id
fact source member == evidence source member
fact source locator == evidence fact locator
fact.raw_value == evidence authoritative logical raw_text
fact.fragment_hash == evidence.fragment_hash
```

For continuation-backed Inline facts:

```text
fact.source_fragments
== evidence.source_fragments
== source-replayed continuation chain
```

Any mismatch is blocking. Validation must not silently repair persisted Raw
Facts.

### 4.5 Context and unit canonical comparison

P7 must reconstruct deterministic context semantics from the same immutable
source member and compare them with the persisted context payload. Context
comparison covers:

```text
id
entity_identifier
period.instant
period.startdate
period.enddate
dimensions in deterministic source order:
  dimension_kind
  dimension
  member
  member_qname
  typed_value
  typed_member_text
```

Unit comparison covers:

```text
id
measures in deterministic source order
```

Existing parser text-normalization rules remain authoritative. A new persisted
`source_member_sha256` field inside Inline context/unit dictionaries is not
required merely to prove source origin; replay from the same immutable primary
member establishes origin.

### 4.6 Fail-closed reason

Freeze this exact reason code for Raw Fact/source replay inequality:

```text
P11_RAW_FACT_SOURCE_MISMATCH
```

Meaning:

```text
A persisted logical Raw Fact does not semantically equal the authoritative
fact reconstructed from its immutable package member and exact source locator.
```

Severity:

```text
BLOCKING
```

Use this reason for ISSUE-145 semantic mismatches including, where applicable:

```text
raw_value mismatch
raw_qname mismatch
raw_metric_name mismatch
parsed_numeric_candidate mismatch
fact_kind mismatch
context_ref mismatch
unit_ref mismatch
source-derived attribute mismatch
source member mismatch
fact locator mismatch
fact/evidence semantic mismatch
fragment_hash mismatch
source_fragments mismatch
persisted context semantic payload mismatch
persisted unit semantic payload mismatch
```

More specific existing errors remain authoritative for their existing domains.
For example, use `P11_EVIDENCE_LOCATOR_INVALID` when an evidence locator itself
does not resolve, and `P11_FACT_SOURCE_MODE_INVALID` when the declared logical
source mode itself is invalid.

Raw Fact/source replay inequality is always:

```text
P11_RAW_FACT_SOURCE_MISMATCH
```

The PC Agent must not invent or rename reason codes during implementation. Any
future need for another reason code requires:

```text
STOP
→ design amendment
→ Git design freeze
→ ChatGPT review
→ development reauthorization
```

## 5. Compatibility contract

No additional parser bump is required. Freeze:

```text
SEC_DISCOVERY_SCHEMA = p11-sec-discovery-v1
VIRTUAL_HTML_NORMALIZER_VERSION = VIRTUAL_HTML_V6
SEC_ARTIFACT_SCHEMA = p11-sec-artifacts-v2
SEC_VALIDATION_SCHEMA = p11-sec-validation-v3
SEC_REGISTRY_SCHEMA_VERSION = 4
```

`p11-sec-validation-v3` covers the stronger ISSUE-143 and ISSUE-145 validation
semantics. Existing validation-v2 results must not qualify for current
`REUSE_DATA`. A current V6/v2 parsed artifact may be loaded as local parse input
and revalidated under v3 without rewriting the parsed artifact solely because
the validation version changed. Immutable raw package reuse remains allowed.

## 6. Required next-cycle development verification

These are development tests, not Formal Acceptance.

### 6.1 ISSUE-142

The focused suite must cover:

```text
filings.files absent → valid empty inventory
filings.files non-list → BLOCK
descriptor non-object → BLOCK
name missing → BLOCK
name non-string → BLOCK
name empty → BLOCK
unsafe name → BLOCK
duplicate normalized name → BLOCK
filingFrom non-string → BLOCK
filingTo non-string → BLOCK
trailing date garbage → BLOCK
invalid calendar date → BLOCK
reversed range → BLOCK
missing ranges → conservatively selected
ancient provably irrelevant → excluded
late amendment range → selected
all descriptors validated before first history fetch
online source set == P7 reconstruction source set
```

The validated-before-fetch fixture must contain one apparently selectable valid
descriptor and one malformed descriptor, and must prove history fetch count is
zero before the blocking error.

### 6.2 ISSUE-143

The focused suite must cover:

```text
valid Inline source chain → PASS
valid instance source chain → PASS
fact context_ref tamper → BLOCK
fact unit_ref tamper → BLOCK
persisted context semantic payload tamper → BLOCK
persisted unit semantic payload tamper → BLOCK
context/unit present only in another member → BLOCK
authentic XBRL instance bytes with OTHER/wrong role → BLOCK
two authentic instance roots across package members → BLOCK
DOM fact in instance mode → BLOCK
XML fact in Inline mode → BLOCK
```

### 6.3 ISSUE-145

The focused suite must cover both source modes where the field applies:

```text
fact raw_value tamper while evidence remains valid → BLOCK
fact raw_qname tamper while evidence remains valid → BLOCK
raw_metric_name tamper → BLOCK
parsed_numeric_candidate tamper → BLOCK
decimals/precision/scale/sign/nil source-attribute tamper → BLOCK as applicable
fact fragment_hash differs from evidence/source → BLOCK
fact source_fragments differ from evidence/source continuation chain → BLOCK
fact/evidence locator divergence → BLOCK
```

### 6.4 Validation migration

The development suite must prove:

```text
existing V6 / artifacts-v2 + validation-v2
→ REUSE_DATA denied

same raw package + same V6 parsed artifact
→ no parsed artifact mutation required
→ P7 validation-v3 executes
→ valid result becomes reusable only after v3 PASS
```

Old validation-v2 artifact bytes remain immutable.

## 7. Validation-v3 Artifact Persistence and Migration

### 7.1 Validation artifact identity

The current SEC validation artifact identity is:

```text
package_sha256
+
SEC_VALIDATION_SCHEMA
```

The current schema is:

```text
p11-sec-validation-v3
```

A result written under another validation schema is not the current validation
artifact and cannot establish current reuse eligibility.

### 7.2 Current v3 storage path

The current validation artifact path is schema-versioned:

```text
workspace/ingest/us/p7/
  <package_sha256>/
    <SEC_VALIDATION_SCHEMA>/
      validation.json
      issues.jsonl
```

For the current contract:

```text
workspace/ingest/us/p7/
  <package_sha256>/
    p11-sec-validation-v3/
      validation.json
      issues.jsonl
```

A newly generated `SecValidationResult.artifact_dir` for v3 is therefore the
schema-versioned directory
`.../p7/<package_sha256>/p11-sec-validation-v3`.

Current v3 validation files must not be written directly into
`.../p7/<package_sha256>/`.

### 7.3 Historical flat validation-v2 artifact

Historical validation-v2 artifacts may exist at the legacy flat path:

```text
workspace/ingest/us/p7/
  <package_sha256>/
    validation.json
    issues.jsonl
```

Those legacy files are:

```text
HISTORICAL
READ-ONLY
INCOMPATIBLE FOR CURRENT REUSE
```

They must not be overwritten, deleted, renamed, moved, rewritten, or converted
in place. Adding the child directory `p11-sec-validation-v3/` is allowed
because the legacy files themselves remain byte-for-byte unchanged.

### 7.4 Shared current-validation path resolver

Production code must use one shared deterministic resolver for the current SEC
validation artifact directory. Conceptually:

```text
current_validation_dir(
    validation_root,
    package_sha256,
    SEC_VALIDATION_SCHEMA
)
=
validation_root
/ package_sha256
/ SEC_VALIDATION_SCHEMA
```

The exact Python function name is an implementation detail.

US ingest, US reuse, US CLI reusable-artifact planning, P8 US loading, and
migration tests must use this same rule. No current production call site may
independently reconstruct the legacy flat path
`p7/<package_sha256>/validation.json`.

### 7.5 Loader and reuse semantics

Current runtime reuse logic loads only the current expected validation schema:

```text
expected schema = p11-sec-validation-v3
```

If current v3 is absent while a legacy flat validation-v2 artifact exists:

```text
current reusable validation = unavailable
REUSE_DATA = denied
revalidation = required
```

This condition is not corruption. The immutable raw package and compatible
V6/v2 parsed artifact remain eligible as local inputs for revalidation.

A current runtime must not silently upgrade, reinterpret, or fall back to a
legacy v2 artifact.

### 7.6 V2-to-v3 revalidation transition

The required transition is:

```text
raw package exists
+
VIRTUAL_HTML_V6 / p11-sec-artifacts-v2 parsed artifact exists
+
only validation-v2 exists

→ fresh current discovery
→ do not rerun the parser solely because validation is old
→ load the existing V6/v2 parsed artifact
→ execute P7 validation-v3
→ write the new versioned validation-v3 artifact
→ leave validation-v2 bytes unchanged
→ update current Registry/runtime validation state from the v3 result
→ REUSE_DATA becomes eligible only after v3 PASS
```

No parsed artifact mutation is permitted solely because the validation schema
changed.

### 7.7 Repeated v3 validation and atomicity

If a current v3 validation directory already exists, a refreshed validation
must not expose partial state. The project must use atomic artifact replacement
semantics so the visible current v3 result is internally consistent:

```text
validation.json
issues.jsonl
schema_version = p11-sec-validation-v3
artifact_hashes
issue_count
reuse_eligible
```

Fresh discovery may require a refreshed current v3 result because the discovery
observation identity changed. A missing or invalid v3 result must never cause
fallback to validation-v2.

### 7.8 Registry contract

No Registry schema bump is required:

```text
SEC_REGISTRY_SCHEMA_VERSION = 4
```

The current Registry validation fields represent the current v3 result.
Historical v2 files remain audit artifacts only and do not become current
Registry validation truth.

### 7.9 P8 contract

P8 US must resolve and verify current validation through the same deterministic
versioned path rule. P8 must not:

```text
load legacy flat validation-v2 as current
search arbitrary validation directories
choose a validation directory by timestamp
fall back from v3 to v2
```

Current validation identity is determined by:

```text
package_sha256
+
SEC_VALIDATION_SCHEMA
```

P8 remains read-only and does not execute revalidation.

## 8. Governance state

```text
P11 REVIEW 5 VALIDATION-V3 PERSISTENCE DESIGN FREEZE
ISSUE-140 = FIXED
ISSUE-141 = FIXED
ISSUE-142 = DESIGN FROZEN / IMPLEMENTATION REQUIRED
ISSUE-143 = DESIGN FROZEN / IMPLEMENTATION REQUIRED
ISSUE-144 = GOVERNANCE CORRECTED
ISSUE-145 = DESIGN FROZEN / IMPLEMENTATION REQUIRED
DEVELOPMENT AUTHORIZED = NO
FORMAL TEST PLAN = NOT CREATED / NOT AUTHORIZED
FORMAL ACCEPTANCE = NOT RUN
MAIN MERGE = NOT AUTHORIZED
P11 DONE = NO
```

No `src/`, `tests/`, runtime, workflow, or configuration implementation is
authorized in this design-only cycle.
