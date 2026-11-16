# 213 — P11 ISSUE-148 Development Authorization

Status: **DEVELOPMENT_AUTHORIZED**

Agent role: **Development Agent**

This authorization is limited to implementing the exact Design 40 freeze.

It is not a Formal Test authorization, Formal Acceptance declaration, main
merge authorization, or P11 DONE record.

## 1. Exact authority

Repository:

`projectforkk/FinancialFilingDataFoundation`

Authoritative remote lineage:

`reconcile/p11-140-143-local-chain`

Independent Formal Acceptance Review 5:

`development/211-p11-formal-acceptance-review-5.md = NOT_PASSED`

Exact Design 40 freeze:

`db8edabb2630549e2d75a5becaccb15cb1c53749`

Design freeze review:

`development/212-p11-design40-freeze-review-result.md = DESIGN_FREEZE_PASS`

Review commit:

`762bc471c3fe553496a7ecef73450013d49fd189`

Previous production candidate:

`f1cc76889718e06fdbdc46926e2b207b740a96e3`

Current issue:

```text
P11-ISSUE-148
SEC ARCHIVE MEMBER DELIVERY BYTES ARE NOT PROVEN
TO BE STABLE FILED MEMBER BYTES
```

## 2. Authorized development scope

Implement Design 40 exactly:

```text
complete submission text
→ immutable source container
→ strict byte-oriented SGML inventory
→ deterministic member payload slices
→ package bytes
→ external immutable package-source provenance
→ Registry v5
→ validation-v4
→ current planner/P8 provenance eligibility
```

ISSUE-140..147 are regression-preservation scope.

Do not redesign them.

## 3. Frozen source-of-truth rule

For current package construction, authoritative bytes come only from:

```text
https://www.sec.gov/Archives/edgar/data/
<int(CIK)>/<accession-no-dashes>/<accession-with-dashes>.txt
```

Direct individual archive member responses are not package byte sources.

Do not solve ISSUE-148 by:

- stripping random script from direct member responses;
- DOM normalization;
- browser rendering;
- accepting changed member bytes;
- weakening SOURCE_DRIFT;
- silently overwriting a package;
- changing package SHA formula.

## 4. Frozen versions

Implement:

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

No new P11 reason code is authorized.

## 5. Required implementation capabilities

### Complete-submission URL and fetch

Add exact URL construction/validation for the selected CIK/accession.

Use package/container max bytes.

Normal package construction fetch classification must become:

```text
complete-submission = 1
archive index = 0
individual package members = 0
unrelated static/browser = 0
```

### Immutable container store

Implement the exact Design-40
`sec-containers/sha256/<aa>/<sha>/` store and metadata schema.

Atomic persist/load and hash/path/schema validation are required.

### SGML inventory

Implement byte-oriented strict DOCUMENT parsing with:

```text
TYPE
SEQUENCE
FILENAME
TEXT
```

and exact deterministic offsets.

Do not establish offsets after Unicode transcoding.

### Payload extraction

Implement exact TEXT/XML/XBRL envelope rules and structural-line handling from
Design 40.

No arbitrary normalization.

### Package selection

Select primary and required semantic XBRL members exclusively from the
complete-submission inventory.

Existing semantic-reference and source-mode rules remain controlling.

### Package-source provenance

Implement:

`p11-sec-package-source-v1`

outside the immutable package directory.

Its canonical hash and locator replay must be deterministic.

### Legacy packages

Do not rewrite/delete old package directories or manifests.

Legacy unattested package:

```text
audit readable
current reuse ineligible
```

Fresh same-byte attestation may add only external provenance.

Different current container-derived package may coexist with the historical
unattested package for the same accession.

### Planner

Legacy unattested packages must not independently trigger:

```text
PARSE_LOCAL
REVALIDATE_LOCAL
REUSE_DATA
```

After fresh same-byte attestation, compatible V6/v2 parsed artifacts may be
local input, but current validation-v4 is mandatory.

### Registry v5

Implement the exact additive tables frozen in Design 40:

```text
sec_source_containers
sec_package_source_provenance
sec_package_member_locators
```

v4→v5 must be idempotent.

Unknown/future schema fails before mutation.

CN/HK global schema/rows remain unchanged.

### Validation-v4

Validation identity binds:

```text
package_sha256
+
package_source_provenance_sha256
+
p11-sec-validation-v4
```

Validation first verifies current provenance replay.

No v4→v3 fallback.

### P8/MCP

Current US P8 eligibility requires current provenance + Registry v5 +
validation-v4.

P8 remains SEC-network-free.

## 6. Required deterministic tests

Implement all Design-40 tests T148-01 through T148-18.

At minimum prove:

- complete-submission exact URL;
- container atomic persistence;
- malformed SGML fail closed;
- duplicate/unsafe filenames fail closed;
- TEXT/XML/XBRL exact byte slicing;
- CRLF and LF structural framing;
- no internal byte normalization;
- canonical PDS primary active-content rejection;
- primary/XBRL selection from container;
- zero index/member/static fetch package construction;
- provenance hash/artifact/replay;
- provenance tamper matrix;
- legacy unattested planner rejection;
- same-byte external re-attestation;
- different-package migration coexistence;
- current container drift;
- same-container/different-package mismatch;
- Registry v5 migration;
- validation-v4 identity/no fallback;
- P8 no-network;
- direct-member response randomization isolation.

Preserve all ISSUE-140..147 tests.

## 7. Required regression

Run at minimum:

- T148 focused tests;
- ISSUE-147 focused;
- ISSUE-146 / Review-5 source-replay focused;
- full `tests/unit/us_sec`;
- MCP-focused;
- P0-P10 focused;
- full `tests/unit`;
- `python -m compileall -q src tests`;
- `git diff --check`.

Use short Windows pytest temp paths.

Record every failure/skip.

## 8. Required live developer smoke

After deterministic regression passes, with `FFDF_P11_US_DEV` absent:

### Apple FY2025 — fresh root A

Ticker-based acquire + ingest.

Record:

- complete-submission URL/SHA/byte length;
- provenance SHA;
- complete selected member inventory;
- every locator;
- every member SHA/length;
- package SHA;
- request classifications;
- validation-v4 path/status;
- research_ready.

### Apple FY2025 — independent fresh root B

Repeat from no local US package state.

Require exact equality with root A:

```text
accession
complete-submission SHA
provenance SHA
selected member set
every member SHA/length
package SHA
```

This is mandatory before candidate evidence.

### Delivery-layer diagnostic

Optionally fetch the public primary member URL separately.

If its bytes differ/randomize, prove those bytes never enter the package or
provenance identity.

Do not use that diagnostic fetch as package input.

### Additional live smoke

Run:

- Apple FY2025 Q3;
- Toyota FY2025 20-F;
- Kellanova amendment/conflict regression.

## 9. Formal-Test-5 FT-02 evidence gap

Do not alter production semantics merely to compensate for the old Formal Test
harness gap.

Preserve ISSUE-147 behavior and focused tests.

A future ChatGPT-authored Formal Test plan will independently restore the full
nine-case ISSUE-147 acceptance-only matrix.

## 10. Candidate discipline

Create one new production/test candidate descending from this authorization.

Do not amend:

`f1cc76889718e06fdbdc46926e2b207b740a96e3`

After the exact production/test candidate is frozen, rerun exact-candidate
regression/live smoke as required.

Then create a separate documentation-only evidence file:

`development/214-p11-issue148-development-evidence.md`

Candidate → evidence must contain no source/test changes.

Push normally to:

`origin/reconcile/p11-140-143-local-chain`

No force push.

## 11. Stop conditions

STOP and return to ChatGPT if implementation requires:

- changing the authoritative-source decision;
- changing the package SHA formula;
- changing package manifest schema;
- a new P11 reason code;
- parser V7 or parsed artifact v3;
- destructive package migration;
- modifying accepted CN/HK semantics;
- arbitrary HTML/script normalization;
- weakening source drift;
- formal-test execution before Fresh Full Review.

A new design correction is required in those cases.

## 12. Git safety

Forbidden:

- force / force-with-lease;
- rebase/history rewrite;
- reset --hard;
- clean -fd / clean -fdx;
- main merge;
- unauthorized divergent-route merge/cherry-pick.

## 13. Lifecycle boundary

After candidate + development evidence push:

```text
STOP FOR CHATGPT FRESH FULL EXACT-CANDIDATE REVIEW
```

Do not create a Formal Test Plan.

Do not execute Formal Test.

Do not declare Acceptance PASS.

Do not merge main.

Do not declare P11 DONE.

Current lifecycle:

```text
DESIGN 40 = PASS
ISSUE-148 DEVELOPMENT = AUTHORIZED
FORMAL TEST = NOT AUTHORIZED
FORMAL ACCEPTANCE = NOT PASSED
MAIN MERGE = NOT AUTHORIZED
P11 DONE = NO
```
