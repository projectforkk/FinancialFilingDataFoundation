# 40 — P11 SEC Complete-Submission Source Provenance Correction

Status: **AUTHORITATIVE DESIGN CORRECTION — ISSUE-148**

Development: **NOT YET AUTHORIZED IN THIS DESIGN COMMIT**

This design corrects the immutable-source defect discovered by Independent
Formal Acceptance Review 5.

It supersedes older P11 design text only where this document explicitly changes
the authoritative byte source, package provenance compatibility, Registry
version, and validation version.

ISSUE-140..147 remain regression-preservation scope.

## 1. Trigger

Formal Test 5 compared the same Apple FY2025 accession and the same public
primary member URL across two independent acquisition cycles.

The primary member response changed from:

```text
bytes = 1520312
sha256 = 2e9a48b29574153c8b11f8d070f0198bbad8d53444570e6cefdaf68578f15066
```

to:

```text
bytes = 1520327
sha256 = 7f44c98b2b8d4f0836aac3f151c415149df4a560c4208860a7d2ccfedf9134be
```

The difference was confined to a randomized embedded script path in the direct
HTTP response for the same SEC archive member.

Design 26 requires member bytes to be immutable and requires a changed re-fetch
of the same archive member to be treated as source drift.

The direct member HTTP response therefore cannot remain the unqualified
authoritative filed-member byte source.

## 2. Official SEC basis

The SEC "Accessing EDGAR Data" documentation identifies the accession
`<accession>.txt` file as the raw text version of the complete disseminated
filing content.

Current path form:

```text
https://www.sec.gov/Archives/edgar/data/<CIK-int>/<accession-no-dashes>/<accession-with-dashes>.txt
```

The SEC Public Dissemination Service Technical Specification states that after
acceptance EDGAR reassembles the submission with informative header tags and
the original public documents before dissemination.

The same specification defines repeated document nests containing:

```text
<DOCUMENT>
<TYPE>
<SEQUENCE>
<FILENAME>
<TEXT>
...
</TEXT>
</DOCUMENT>
```

The EDGAR Filer Manual also states that filer-submitted HTML may not contain
active content such as `<SCRIPT>`. Therefore delivery-layer script material
must not be silently accepted as filed source bytes.

Official references:

- https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data
- https://www.sec.gov/files/edgar/pds_dissemination_spec.pdf
- https://www.sec.gov/files/edgar/filermanual/efmvol2-c5.pdf

## 3. ISSUE-148

```text
P11-ISSUE-148
SEC ARCHIVE MEMBER DELIVERY BYTES ARE NOT PROVEN TO BE
STABLE FILED MEMBER BYTES
```

Approved solution:

```text
SEC complete submission text
→ immutable authoritative source container
→ strict SGML document inventory
→ deterministic filed-member byte slices
→ existing package member model
→ immutable package store
```

Direct individual member URLs remain public/logical URLs only.

They no longer supply package identity bytes in the current acquisition path.

## 4. Authoritative source container

For an accession, the current authoritative byte source is exactly one SEC
complete-submission text response at:

```text
https://www.sec.gov/Archives/edgar/data/
  <int(CIK)>/
  <accession-without-dashes>/
  <accession-with-dashes>.txt
```

Define:

```text
source_container_kind = SEC_COMPLETE_SUBMISSION_TEXT
source_container_sha256 = SHA256(exact HTTP response body)
source_container_byte_length = len(exact HTTP response body)
```

No HTML normalization, script stripping, DOM serialization, whitespace
normalization, character transcoding, or browser rendering is allowed before
the container hash is computed.

The HTTP response must pass the existing SEC host/path/redirect/content-encoding
security boundary.

The complete submission request uses the package-size limit, not the individual
member-size limit.

Current target:

```text
PACKAGE_MAX_BYTES = 512 MiB
```

`SecHttpConfig` may expose a deterministic package/container max-bytes setting
whose default remains this frozen constant.

## 5. Container raw-store

Persist exact container bytes atomically under:

```text
workspace/ingest/raw-store/
  sec-containers/
    sha256/
      <first-two-hex>/
        <source_container_sha256>/
          source.txt
          metadata.json
```

Container metadata schema:

```text
p11-sec-source-container-v1
```

Required metadata:

```text
schema_version
kind = SEC_COMPLETE_SUBMISSION_TEXT
source_url
source_container_sha256
byte_length
cik
accession
```

The metadata file is not part of container byte identity.

Container rules:

- exact source bytes are immutable;
- same container SHA must reproduce identical metadata identity fields;
- atomic staging → verify → commit;
- container SHA/path mismatch fails closed;
- unsupported/future container schema fails closed;
- local path is never part of source identity.

## 6. Complete-submission validation

Before document extraction, require:

- non-empty bytes;
- exact allowlisted complete-submission URL for the selected CIK/accession;
- recognizable SEC submission/SGML structure;
- one accession identity matching the selected accession;
- one or more document nests;
- no malformed structural nesting;
- no duplicate normalized filename among documents eligible for package use.

Malformed source-container structure is:

```text
P11_PACKAGE_INVALID
```

A changed authoritative complete-submission container for an accession already
attested under the current provenance contract is:

```text
P11_SOURCE_DRIFT
```

Do not overwrite or silently choose the newer bytes.

## 7. Byte-oriented SGML inventory

The inventory parser operates on bytes.

It must not decode the complete submission into Unicode before structural
offsets are established.

Structural tags are ASCII and recognized only as SGML envelope structure, not
through an HTML parser.

For every document nest required for current P11 package selection, record:

```text
document_index
document_type
document_sequence
filename
text_start
text_end
payload_start
payload_end
payload_envelope
```

Required document header fields:

```text
<TYPE>
<SEQUENCE>
<FILENAME>
<TEXT> ... </TEXT>
```

`<DESCRIPTION>` is optional diagnostics only.

Filename is normalized through the existing archive-relative-name safety rule.

Duplicate normalized filenames fail closed.

## 8. Canonical filed-member payload

The authoritative package member body is a deterministic byte slice of the
complete-submission container.

### 8.1 Plain TEXT payload

For normal HTML/ASCII document text:

```text
payload_envelope = TEXT
```

The member body is the exact document-content bytes between the structural
`<TEXT>` and `</TEXT>` envelope boundaries.

Only the SGML structural tag line and its structural line terminator are outside
the payload.

No byte inside the document-content region is normalized.

### 8.2 XML/XBRL envelope

If the document text is structurally enveloped as:

```text
<TEXT>
<XML>
...
</XML>
</TEXT>
```

or:

```text
<TEXT>
<XBRL>
...
</XBRL>
</TEXT>
```

then:

```text
payload_envelope = XML
or
payload_envelope = XBRL
```

The authoritative member body is the exact byte region inside that structural
inner envelope.

The structural wrapper tag lines are excluded.

No bytes inside the inner payload are normalized.

### 8.3 Structural line-boundary rule

Opening/closing SGML envelope tags are structural lines.

A CRLF or LF that terminates the structural tag line belongs to the envelope,
not to the filed payload.

All line endings inside the payload region are preserved exactly.

The extraction algorithm must produce explicit byte offsets so provenance can
be independently replayed without heuristic stripping.

### 8.4 Unsupported envelopes

Current P11 package selection is textual HTML/XML/XBRL only.

If a required selected member is represented through an unsupported binary or
UUencoded envelope, fail closed instead of inventing a decoder contract.

## 9. Active-content boundary

Do not strip active content from an acquired member.

Do not rewrite HTML to remove delivery-layer injections.

For a canonical primary HTML payload extracted from the authoritative complete
submission, filer-prohibited active-content tags such as `<SCRIPT>`,
`<APPLET>`, `<OBJECT>`, `<IFRAME>`, or `<EMBED>` are a source/content
validation failure under the current P11 supported filing contract.

Use:

```text
P11_CONTENT_TYPE_INVALID
```

This rule is evaluated only on the canonical payload extracted from the
complete-submission source.

A direct public member HTTP response containing delivery-layer script material
does not contaminate the package because that response is not fetched for
package bytes.

## 10. Package member selection

Current package acquisition must inventory the complete submission first.

The selected primary document is the document whose normalized `FILENAME`
exactly matches current discovery's `primaryDocument`.

It must occur exactly once.

Required XBRL members are then selected from the same complete-submission
inventory using the existing semantic-reference policy:

- primary Inline XBRL document;
- required schema;
- referenced presentation/calculation/definition/label/reference linkbases;
- FilingSummary.xml when currently required by the existing policy;
- accepted XBRL instance when current source-mode rules require it.

Unrelated exhibits and browser/static assets remain excluded.

Normal current package acquisition must not fetch:

```text
index.json
individual .htm/.xml/.xsd archive member responses
CSS
JavaScript
images
browser subresources
```

for package byte construction.

Expected new archive acquisition pattern:

```text
complete-submission fetches = 1
individual package-member fetches = 0
archive index fetches = 0
unrelated static-asset fetches = 0
```

## 11. Public member URL vs byte provenance

Every package member continues to expose the exact public/logical member URL:

```text
https://www.sec.gov/Archives/edgar/data/
  <int(CIK)>/
  <accession-no-dashes>/
  <relative_name>
```

The existing `source_url` field remains this logical/public URL for
compatibility and citation.

It is no longer sufficient proof of byte origin.

Authoritative byte provenance is instead:

```text
complete-submission source URL
+ complete-submission SHA256
+ deterministic document locator
+ replayed payload bytes
```

## 12. Package manifest remains v1

Do not rewrite existing package manifests.

Keep:

```text
PACKAGE_MANIFEST_SCHEMA = p11-sec-package-v1
```

Keep the package SHA formula unchanged:

```text
package_sha256 =
SHA256(canonical JSON of sorted {
  role,
  relative_name,
  member_sha256,
  byte_length
})
```

This preserves the Design-26 member-byte-set identity.

The source-container correction is represented by a separate immutable
provenance artifact.

## 13. Package-source provenance artifact

Introduce:

```text
SEC_PACKAGE_SOURCE_PROVENANCE_SCHEMA =
p11-sec-package-source-v1
```

Persist outside the immutable package directory:

```text
workspace/ingest/raw-store/
  sec-package-provenance/
    packages/
      <package_sha256>/
        <provenance_sha256>/
          provenance.json
```

Define:

```text
provenance_sha256 =
SHA256(canonical JSON of the provenance payload excluding provenance_sha256)
```

Required payload:

```text
schema_version
provenance_sha256
package_sha256
cik
accession
source_container:
  schema_version
  kind
  source_url
  source_container_sha256
  byte_length
members[] sorted by relative_name:
  relative_name
  role
  public_source_url
  member_sha256
  byte_length
  document_index
  document_type
  document_sequence
  filename
  payload_start
  payload_end
  payload_envelope
```

The artifact is immutable.

No mutable "current pointer" is required for identity.

## 14. Provenance replay

A package is **current-source-attested** only when all of the following pass:

1. package manifest/member bytes load normally;
2. one supported package-source provenance artifact is selected;
3. provenance package SHA equals the loaded package SHA;
4. source-container metadata and raw bytes load;
5. source-container raw bytes rehash to the recorded container SHA;
6. complete-submission accession/CIK identity matches;
7. every recorded member locator replays deterministically from the container;
8. replayed member bytes equal the package member bytes exactly;
9. replayed member SHA/length equal package manifest values;
10. public member URL exactly matches CIK/accession/relative-name policy;
11. role and relative-name sets match the package manifest;
12. provenance hash recomputes exactly.

Any mismatch is:

```text
P11_PROVENANCE_MISMATCH
```

Corrupt/malformed package/container structure may use
`P11_PACKAGE_INVALID`.

## 15. Legacy package compatibility

Existing P11 packages and manifests are immutable historical evidence.

Do not delete or rewrite them.

A legacy package with no current source-provenance artifact is:

```text
LOADABLE FOR AUDIT
NOT CURRENT-REUSE-ELIGIBLE
NOT RESEARCH-READY
```

A fresh complete-submission acquisition may attest an existing package without
changing its package directory when the newly extracted member bytes reproduce
the same package SHA and every member byte exactly.

In that case, write only the external provenance artifact and Registry v5
provenance rows.

If the new authoritative member bytes produce a different package SHA, persist
a new package and leave the old package untouched.

## 16. Same-accession coexistence during migration

The old package store rule "any different package SHA for one accession is
source drift" is superseded for this migration boundary.

Allowed:

```text
legacy unattested package A
+
current-source-attested package B
for the same accession
```

The legacy package remains audit-only.

For current-source-attested packages:

- exactly one attested source container identity is allowed per accession;
- two current provenance records for the same accession with different
  source-container SHA are `P11_SOURCE_DRIFT`;
- the same container SHA yielding different canonical package SHA is
  `P11_PROVENANCE_MISMATCH`;
- duplicate equivalent attestation is idempotent.

## 17. Planner compatibility

Current planner compatibility becomes:

```text
current discovery selects accession
→ current-source-attested package exists?
   → evaluate parsed compatibility
→ else
   → DISCOVER_AND_ACQUIRE complete-submission source
```

A legacy unattested package must not trigger:

```text
PARSE_LOCAL
REUSE_DATA
REVALIDATE_LOCAL
```

unless the same package becomes current-source-attested through a fresh
complete-submission provenance replay first.

If fresh attestation reproduces an existing package SHA, compatible V6/v2
parsed data may remain usable as local parse input because member bytes are
identical.

However old validation-v3 cannot qualify as current acceptance after the
Design-40 provenance upgrade.

## 18. Registry v5

Set:

```text
SEC_REGISTRY_SCHEMA_VERSION = 5
```

Global:

```text
REGISTRY_SCHEMA_VERSION = 1
```

remains unchanged.

Migration v4 → v5 is additive and idempotent.

Add table:

```text
sec_source_containers
---------------------
source_container_sha256 PRIMARY KEY
schema_version
kind
source_url
byte_length
cik
accession
first_seen_at
```

Add table:

```text
sec_package_source_provenance
-----------------------------
provenance_sha256 PRIMARY KEY
package_sha256
source_container_sha256
schema_version
created_at
```

Add table:

```text
sec_package_member_locators
---------------------------
provenance_sha256
package_sha256
relative_name
document_index
document_type
document_sequence
filename
payload_start
payload_end
payload_envelope
public_source_url
member_sha256
byte_length

PRIMARY KEY(provenance_sha256, relative_name)
```

Application-level verification must enforce exact correspondence between these
rows and the immutable provenance artifact.

Legacy v4 rows are preserved.

CN/HK global user_version and accepted rows remain unchanged.

Unknown/future SEC schema fails closed before mutation.

## 19. Validation v4

Set:

```text
SEC_VALIDATION_SCHEMA = p11-sec-validation-v4
```

Parser/artifact versions remain:

```text
VIRTUAL_HTML_NORMALIZER_VERSION = VIRTUAL_HTML_V6
SEC_ARTIFACT_SCHEMA = p11-sec-artifacts-v2
```

Discovery remains:

```text
SEC_DISCOVERY_SCHEMA = p11-sec-discovery-v1
```

Validation-v4 identity must bind:

```text
package_sha256
+
package_source_provenance_sha256
+
SEC_VALIDATION_SCHEMA
```

Validation-v4 first verifies current source provenance replay before accepting
fact/evidence source replay.

Existing validation-v3 remains immutable historical evidence and is not a
current-runtime fallback.

No v4→v3 fallback.

If member bytes are unchanged and an old V6/v2 parsed artifact exists, v4 may
validate that parsed artifact after current provenance attestation without a
parser rerun.

## 20. P8 / MCP boundary

P8 current US document resolution requires:

- current discovery identity;
- current-source-attested package;
- Registry v5 provenance match;
- current validation-v4 PASS/COMPATIBLE;
- zero blocking issues.

P8 must not fetch SEC network data.

P8 must fail closed on:

- missing provenance artifact;
- missing source container;
- provenance/container hash mismatch;
- locator replay mismatch;
- legacy unattested package;
- validation-v3-only state.

## 21. Direct member URLs

Direct archive member URLs remain useful for:

- human navigation;
- citations;
- optional acceptance diagnostics.

Production package acquisition must not use their response bytes.

Formal acceptance may fetch the same direct member URL repeatedly as a
diagnostic to demonstrate delivery-layer variability, but those diagnostic
bytes:

- are not persisted as package members;
- are not hashed into package identity;
- cannot override the complete-submission source.

## 22. Source drift semantics

Do not weaken `P11_SOURCE_DRIFT`.

Current exact meanings include:

### Complete-submission drift

Same accession already has current provenance for container SHA A, but a fresh
authoritative complete-submission fetch yields SHA B:

```text
P11_SOURCE_DRIFT
```

### Same source / different deterministic extraction

Same container SHA and same extraction contract yield a different package SHA:

```text
P11_PROVENANCE_MISMATCH
```

### Direct member delivery variation

Different bytes from repeated direct public member URL diagnostics do not
constitute package source drift because that endpoint is not the authoritative
package byte source.

No direct-member bytes may silently update an attested package.

## 23. Required development tests

### T148-01 complete-submission URL

Exact CIK/accession path generation and host/path safety.

### T148-02 source-container store

Atomic persist/load, hash/path verification, same-hash idempotency, corrupt
metadata/body fail closed.

### T148-03 SGML document inventory

Strict repeated DOCUMENT parsing with TYPE/SEQUENCE/FILENAME/TEXT.

Malformed nesting, missing fields, duplicate normalized filename and unsafe
filename fail closed.

### T148-04 payload extraction

Deterministic byte offsets for:

- TEXT HTML;
- XML envelope;
- XBRL envelope;
- CRLF structural tags;
- LF structural tags.

Replayed payload bytes must be exact.

### T148-05 no normalization

Internal whitespace, line endings, entities and arbitrary non-envelope bytes are
preserved exactly.

### T148-06 active content

Canonical primary payload containing SCRIPT/APPLET/OBJECT/IFRAME/EMBED fails
closed.

No stripping is permitted.

### T148-07 package selection from container

Primary + semantic XBRL dependencies + FilingSummary selection operates from
the container inventory.

No index/member/static fetch is required.

### T148-08 request classification

Normal package acquisition:

```text
complete submission = 1
index.json = 0
individual package members = 0
static/browser assets = 0
```

### T148-09 provenance artifact

Canonical provenance hash, immutable persistence, complete member locator set.

### T148-10 provenance replay

Container → locator → member bytes exactly reproduces package.

Tamper every provenance dimension and require fail closed.

### T148-11 legacy unattested package

Legacy package remains readable for audit but planner cannot use it for
PARSE_LOCAL/REUSE_DATA/REVALIDATE_LOCAL.

### T148-12 re-attestation same package

Fresh container extraction reproduces existing package SHA.

Require:

- no package directory mutation;
- new external provenance record;
- V6/v2 parsed artifact may remain local input;
- validation-v4 required.

### T148-13 migration different package

Legacy direct-response package differs from container-derived package.

Require both immutable packages to coexist and only the attested current package
to qualify.

### T148-14 current provenance conflict

Same accession + different current container SHA → SOURCE_DRIFT.

Same container SHA + different extracted package SHA → PROVENANCE_MISMATCH.

### T148-15 Registry v5

v4→v5 additive/idempotent, future schema fail-before-mutate, legacy rows
preserved, CN/HK unchanged.

### T148-16 validation-v4

Identity binds package + provenance + v4.

No v3 fallback.

Same-byte re-attestation may revalidate without parser rerun.

### T148-17 P8 no-network

Current provenance required; P8 never downloads container/member bytes.

### T148-18 direct-member diagnostic isolation

Inject/randomize a direct member HTTP response.

Prove package/container/member identities are unchanged because direct member
response is not used.

## 24. Required live development smoke

After deterministic regression, run a clean Apple FY2025 ticker-based smoke.

Fresh root A:

1. ticker discovery;
2. current submissions discovery;
3. fetch complete submission exactly once;
4. build package exclusively from extracted container payloads;
5. parse/validate-v4/P8.

Fresh root B:

repeat independently.

Required:

```text
same accession
same complete-submission SHA
same provenance SHA
same selected member set
same member SHA/length for every member
same package SHA
```

The Apple primary canonical payload must not contain the randomized delivery
script observed in direct-member HTTP responses.

Optional diagnostic:

fetch the public primary URL separately and show that its response may contain
different delivery-layer bytes without affecting package identity.

Also run Apple Q3 and Toyota 20-F current-source smokes.

Kellanova amendment behavior remains unchanged.

## 25. Formal Test correction from Review 5

The next Formal Test Plan must restore the complete ISSUE-147 acceptance-only
observation identity matrix that Plan 208 FT-02 failed to execute.

It must independently prove all nine frozen ISSUE-147 checks, including:

- canonical snapshot-ID recomputation;
- invalid/timezone-naive retrieved_at;
- current observation path identity mismatch.

Unit-test counts cannot substitute for this acceptance-only gate.

## 26. Formal acceptance requirements for ISSUE-148

A future Formal Test must include two independent fresh Apple FY2025 roots and
prove:

```text
complete-submission SHA A == B
provenance SHA A == B
package SHA A == B
all selected member SHA/length A == B
```

It must record:

- complete-submission URL/SHA/bytes;
- selected document inventory;
- every locator;
- every canonical member SHA/length;
- package SHA;
- provenance SHA;
- request classification counts;
- parser count;
- validation-v4 path;
- P8/MCP no-network.

Any unexplained complete-submission or package identity drift is FAIL.

## 27. Version contract

Current Design-40 target:

```text
REGISTRY_SCHEMA_VERSION = 1
SEC_REGISTRY_SCHEMA_VERSION = 5

PACKAGE_MANIFEST_SCHEMA = p11-sec-package-v1
SEC_SOURCE_CONTAINER_SCHEMA = p11-sec-source-container-v1
SEC_PACKAGE_SOURCE_PROVENANCE_SCHEMA = p11-sec-package-source-v1

SEC_DISCOVERY_SCHEMA = p11-sec-discovery-v1

VIRTUAL_HTML_NORMALIZER_VERSION = VIRTUAL_HTML_V6
SEC_ARTIFACT_SCHEMA = p11-sec-artifacts-v2
SEC_VALIDATION_SCHEMA = p11-sec-validation-v4
```

No new P11 reason code is required.

Existing reasons are sufficient:

```text
P11_SOURCE_DRIFT
P11_PROVENANCE_MISMATCH
P11_PACKAGE_INVALID
P11_CONTENT_TYPE_INVALID
P11_MEMBER_HASH_MISMATCH
```

## 28. Governance state

```text
FORMAL TEST 5 EXECUTOR:
EXECUTION_PASS

FORMAL ACCEPTANCE REVIEW 5:
NOT_PASSED

ISSUE-147:
FIXED / REGRESSION PRESERVATION

ISSUE-148:
DESIGN FROZEN / IMPLEMENTATION REQUIRED

PREVIOUS PRODUCTION CANDIDATE:
f1cc76889718e06fdbdc46926e2b207b740a96e3

DEVELOPMENT:
NOT YET AUTHORIZED IN THIS DESIGN COMMIT

MAIN MERGE:
NOT AUTHORIZED

P11 DONE:
NO
```
