# 215 — P11 Fresh Full Exact-Candidate Review 9

Status: **REVIEW_PASS**

This is the fresh full review of exact production candidate
`7aac34e763b4c9caac24489eb049aa3dc6efb026` and its documentation-only
evidence child `2c68f85199e6e77dc30c37e5e6eb5515b5bd6fe2`.

This review does not authorize Formal Test execution, Formal Acceptance, main
merge, or P11 DONE.

## 1. Exact authority

- Repository: `projectforkk/FinancialFilingDataFoundation`
- Authoritative lineage: `reconcile/p11-140-143-local-chain`
- Design 40 freeze: `db8edabb2630549e2d75a5becaccb15cb1c53749`
- Design 40 review: `762bc471c3fe553496a7ecef73450013d49fd189`
- ISSUE-148 development authorization:
  `30a34a7e68894cea6cbdea9cbf9bd037e9d97def`
- Previous production candidate:
  `f1cc76889718e06fdbdc46926e2b207b740a96e3`
- Exact reviewed production candidate:
  `7aac34e763b4c9caac24489eb049aa3dc6efb026`
- Development evidence:
  `development/214-p11-issue148-development-evidence.md`
- Evidence commit:
  `2c68f85199e6e77dc30c37e5e6eb5515b5bd6fe2`

Authorization → candidate is one production/test commit.
Candidate → evidence is one documentation-only commit.

## 2. Candidate scope

The candidate changes the Design-40 implementation surfaces only:

- SEC complete-submission source/container handling;
- package acquisition and migration coexistence;
- Registry v5;
- package-source provenance;
- validation-v4;
- planner/current-reuse eligibility;
- P8/MCP provenance enforcement;
- corresponding US SEC tests.

No design document is changed by the production candidate.

## 3. ISSUE-148 verdict

```text
ISSUE-148:
FIXED

AUTHORITATIVE PACKAGE BYTE SOURCE:
SEC complete-submission text

DIRECT MEMBER HTTP RESPONSES:
PUBLIC/CITATION SURFACE ONLY
NOT PACKAGE BYTE SOURCE

PACKAGE MANIFEST:
p11-sec-package-v1

PACKAGE SHA FORMULA:
UNCHANGED

SOURCE CONTAINER:
p11-sec-source-container-v1

PACKAGE SOURCE PROVENANCE:
p11-sec-package-source-v1

SEC REGISTRY:
v5

VALIDATION:
p11-sec-validation-v4
```

## 4. Complete-submission source review

PASS.

Current package construction performs one complete-submission fetch and builds
member bytes from the byte-oriented SGML inventory.

The reviewed acquisition path no longer fetches archive index.json or individual
member responses for package-byte construction.

`archive_member_url(...)` remains only the logical/public member URL stored in
the package and provenance.

The source-container object verifies:

- exact CIK/accession complete-submission URL;
- exact raw bytes;
- SHA256;
- byte length;
- package-size limit;
- current source-container schema.

## 5. SGML byte extraction review

PASS.

The parser establishes document and payload offsets against raw bytes before
payload decoding.

It requires strict DOCUMENT/TEXT structure and exact TYPE, SEQUENCE and
FILENAME fields.

It rejects malformed/overlapping document structure, duplicate normalized
filenames and unsafe names.

TEXT payloads preserve their internal bytes exactly.

XML/XBRL structural wrappers are excluded by deterministic byte offsets while
inner bytes remain unchanged.

Canonical primary active-content tags are rejected rather than stripped.

No DOM serialization, browser rendering or arbitrary whitespace/script
normalization is introduced.

## 6. Package/provenance review

PASS.

Package manifest remains v1 and the package SHA remains the sorted immutable
member-byte-set identity.

Package-source provenance is external to the package directory and binds:

- package SHA;
- CIK/accession;
- source-container metadata;
- public member URL;
- document index/type/sequence/filename;
- payload offsets/envelope;
- member SHA/length.

Provenance payload fields are exact, its hash is canonical, and replay
reconstructs each member directly from stored complete-submission bytes.

The immutable package directory is not rewritten by same-byte re-attestation.

## 7. Legacy migration review

PASS.

The package store now supports an explicit migration-only accession-coexistence
path.

A legacy unattested package remains loadable for audit but is removed from the
planner's current package set before PARSE_LOCAL, REVALIDATE_LOCAL or
REUSE_DATA eligibility is evaluated.

An attested current package may coexist with the legacy package for the same
accession.

Tests prove the planner selects only the attested current package.

## 8. Source-drift review

PASS.

Registry v5 and acquisition both enforce:

```text
same accession + second current container SHA
→ P11_SOURCE_DRIFT

same current container SHA + different package SHA
→ P11_PROVENANCE_MISMATCH

same package/container + different provenance extraction
→ P11_PROVENANCE_MISMATCH
```

The old direct-member delivery variation no longer changes package identity.

SOURCE_DRIFT is not weakened.

## 9. Registry v5 review

PASS.

The migration adds:

```text
sec_source_containers
sec_package_source_provenance
sec_package_member_locators
```

The v4→v5 migration is additive in the candidate and preserves the global
Registry version.

Provenance registration checks same-accession current-source conflicts before
committing the source/provenance/locator chain.

Locator rows are verified byte-for-byte against the provenance payload.

Current constants:

```text
REGISTRY_SCHEMA_VERSION = 1
SEC_REGISTRY_SCHEMA_VERSION = 5
```

## 10. Validation-v4 review

PASS.

Current validation schema:

`p11-sec-validation-v4`

Validation replays package-source provenance before completing package/fact
validation.

The result persists the exact
`package_source_provenance_sha256`.

A provenance replay or Registry mismatch adds a BLOCKING issue.

Validation-v3 is not accepted as current validation.

## 11. Planner / P8 / MCP review

PASS.

The planner filters out packages without replayable Design-40 provenance and
Registry agreement before choosing a local action.

Current validation must bind the same provenance SHA as the current package
provenance before reuse eligibility is accepted.

P8 catalog records the provenance SHA.

MCP reload independently verifies the raw package, Registry package provenance,
source provenance replay, catalog provenance identity and validation provenance
identity.

No SEC network access is introduced into P8/MCP.

## 12. Development tests and live smoke

Development evidence reports:

```text
T148 focused = 20 passed
ISSUE-146/147/148 focused = 39 passed
full US SEC = 283 passed
MCP-focused = 65 passed
full unit = 813 passed
compileall = PASS
git diff --check = PASS
no skips
```

The only failed post-candidate attempt was a Windows long-basetemp filesystem
construction failure before test assertions; the required short-basetemp rerun
passed.

Live Apple FY2025 independent roots A and B reported identical:

- accession;
- complete-submission SHA and byte length;
- provenance SHA;
- selected member set;
- every selected member SHA/length;
- package SHA;
- validation-v4 result;
- research-ready state.

The post-candidate fresh Apple run also reproduced the same identities and
recorded exactly:

```text
ticker map = 1
current submissions = 1
complete submission = 1
archive index = 0
individual package members = 0
static/browser assets = 0
```

Apple Q3 and Toyota 20-F passed with validation-v4 and zero blocking issues.
Kellanova preserved the controlled amended-variant result.

## 13. Frozen versions confirmed

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

No new P11 reason code was required.

## 14. Mandatory next Formal Test correction

Formal Test 6 must not repeat the Formal-Test-5 FT-02 evidence error.

It must independently execute all nine ISSUE-147 observation-identity
acceptance checks:

1. same source bytes/SHA + different retrieval times → different snapshot IDs;
2. both observations coexist;
3. distinct observations do not source-drift;
4. canonical snapshot-ID recomputation;
5. same observation identity + conflicting payload → SOURCE_DRIFT;
6. invalid/timezone-naive retrieved_at → TICKER_SNAPSHOT_INVALID;
7. source-byte tamper fails;
8. derivative-map tamper fails;
9. current observation path identity mismatch fails.

Unit tests do not substitute for this acceptance-only gate.

## 15. Formal Test 6 mandatory ISSUE-148 identity gate

Formal Test 6 must independently create two fresh Apple FY2025 roots and prove
exact equality of:

```text
complete-submission SHA
complete-submission byte length
package-source provenance SHA
selected member set
every member SHA/length
package SHA
```

It must also replay every locator from the persisted source container and verify
the exact request classification.

## 16. Lifecycle verdict

```text
FRESH FULL EXACT-CANDIDATE REVIEW 9:
REVIEW_PASS

ISSUE-148:
FIXED / REGRESSION PRESERVATION

FORMAL TEST PLAN 6:
AUTHORIZED TO CREATE
NOT YET FROZEN IN THIS COMMIT

FORMAL TEST EXECUTION:
NOT AUTHORIZED

FORMAL ACCEPTANCE:
NOT PASSED

MAIN MERGE:
NOT AUTHORIZED

P11 DONE:
NO
```
