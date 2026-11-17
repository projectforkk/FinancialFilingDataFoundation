# 227 — P11 US SEC Provider Closeout

Status: **DONE / PASS**

P11 is formally closed.

## 1. Final accepted scope

Accepted production markets:

```text
CN
HK
US
```

P11 adds the US SEC/EDGAR provider to the previously accepted CN/HK baseline.

## 2. Exact production identity

Production candidate:

`7aac34e763b4c9caac24489eb049aa3dc6efb026`

Design 40 freeze:

`db8edabb2630549e2d75a5becaccb15cb1c53749`

Fresh Full Review:

`development/215-p11-fresh-full-exact-candidate-review-9.md = REVIEW_PASS`

Formal Test 6:

`development/218-p11-formal-test-evidence-6.md = EXECUTION_PASS`

Formal Test 6A remediation:

`development/222-p11-formal-test-evidence-6a.md = EXECUTION_PASS`

Independent Formal Acceptance:

`development/223-p11-formal-acceptance-review-6-continuation.md = ACCEPTANCE_PASS`

Main merge readiness:

`development/224-p11-main-merge-readiness-review.md = READINESS_PASS`

Main merge authorization:

`development/225-p11-main-merge-authorization.md = AUTHORIZED / FAST_FORWARD_ONLY`

Main integration verification:

`development/226-p11-main-integration-verification.md = INTEGRATION_PASS`

## 3. Main integration

Old main:

`5190e866a4ee55dc8820e63ce3dae8fe3c69dfc8`

Authorized fast-forward target:

`9ffd8fb3ef9765bb39aa02318236f44a2a04b75b`

Main integration verification commit:

`fff237bc7d86771d96292138803881ddcc61c794`

Integration used non-force fast-forward only.

No merge commit, rebase, cherry-pick, conflict resolution or production-content
rewrite occurred.

## 4. Final version contract

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

Production identity contract:

`SUPPORTED_MARKETS = ("CN", "HK", "US")`

## 5. Accepted US behavior

Accepted P11 production includes:

- ticker or explicit-CIK SEC identity;
- current SEC submissions discovery with strict history descriptors;
- deterministic domestic 10-K/10-Q and FPI 20-F slot policy;
- no automatic 6-K quarterly guessing;
- complete-submission `.txt` as authoritative filing source container;
- immutable package-source provenance and replay;
- Registry v5;
- validation-v4;
- incremental PARSE_LOCAL / REVALIDATE_LOCAL / REUSE_DATA planning;
- P8/MCP local no-network reads;
- controlled amendment conflicts;
- deterministic source-drift and provenance mismatch failures.

Direct individual archive-member HTTP responses are not package byte sources.

## 6. Final acceptance evidence

Formal Test 6 demonstrated:

```text
full unit = 813 passed
US SEC = 283 passed
MCP = 65 passed
P0-P10 focused = 371 passed
```

It also demonstrated:

- complete ISSUE-147 nine-case observation matrix;
- complete source-container/provenance tamper gates;
- Apple FY2025 independent fresh-root A/B identity equality;
- Apple Q3 PASS;
- Toyota 20-F PASS;
- Kellanova amendment conflict PASS;
- P0-P10/CN/HK preservation.

Formal Test 6A independently corrected the evidence-classification issue and
proved for Apple Q3 and Toyota 20-F:

```text
COMPLETE_SUBMISSION = 1
INDIVIDUAL_ARCHIVE_MEMBER = 0
ARCHIVE_INDEX = 0
STATIC_OR_BROWSER_ASSET = 0
```

## 7. Issue status

```text
ISSUE-140..148:
FIXED / REGRESSION PRESERVATION
```

No open P11 blocker remains.

## 8. Historical scope

The 2026-11-05 CN/HK closeout remains valid historical evidence.

P11 was explicitly reopened on 2026-11-09, completed a new
design/development/review/acceptance lifecycle, and supersedes the historical
"US out of scope" decision for current production scope.

Research MCP production and Semantic Resolver production remain outside the
accepted production scope and require a new explicit lifecycle.

## 9. Final verdict

```text
P0-P10:
DONE / PASS

P11:
DONE / PASS

P11 FORMAL ACCEPTANCE:
PASS

P11 MAIN INTEGRATION:
PASS

ACCEPTED PRODUCTION MARKETS:
CN / HK / US

MAIN MERGE:
COMPLETE

P11 DONE:
YES
```
