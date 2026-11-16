# 207 — P11 Fresh Full Exact-Candidate Review 8

Status: **REVIEW_PASS**

This is the fresh full review of exact production candidate
`f1cc76889718e06fdbdc46926e2b207b740a96e3` and its documentation-only
evidence child `f859dc342060d8c534491639d85e7256c4e11a57`.

It is not a Formal Test Plan, Formal Acceptance, main-merge authorization, or
P11 DONE record.

## 1. Exact authority

- Repository: `projectforkk/FinancialFilingDataFoundation`
- Authoritative remote lineage: `reconcile/p11-140-143-local-chain`
- Design 39 freeze: `fad6ee7512ec1f2f3da0c9a24c646959b2f45541`
- Development authorization:
  `534a1e64ee549df910ed815f90fde82726b43b1c`
- Previous production candidate:
  `6eaace08c9ba5fb26809a7e02de5835123fb667a`
- Exact reviewed candidate:
  `f1cc76889718e06fdbdc46926e2b207b740a96e3`
- Development evidence:
  `development/206-p11-issue147-development-evidence.md`
- Evidence commit:
  `f859dc342060d8c534491639d85e7256c4e11a57`

Candidate → evidence changes exactly one documentation file.

## 2. Git scope

The production candidate changes only:

```text
src/financial_filing_data_foundation/us_sec/ticker_map.py
src/financial_filing_data_foundation/user_cli.py
tests/unit/us_sec/test_issue147.py
```

No Registry, parser, acquisition, package, validation, MCP, CN/HK, dependency,
runtime, or schema file changed in the candidate.

## 3. ISSUE-147 verdict

```text
ISSUE-147:
FIXED

SOURCE IDENTITY / RETRIEVAL-OBSERVATION IDENTITY:
SEPARATED

NEW CURRENT SNAPSHOT PATH:
workspace/ingest/us/ticker-map/observations/<snapshot_id>.json

LEGACY SOURCE-SHA SNAPSHOTS:
READ-ONLY COMPATIBILITY

NEWEST VERIFIED SNAPSHOT ONLY:
PASS

NO STALE HISTORICAL FALLBACK:
PASS

SAME SOURCE BYTES + DIFFERENT RETRIEVED_AT:
VALID DISTINCT OBSERVATIONS

TRUE SAME-OBSERVATION CONFLICT:
P11_SOURCE_DRIFT

EXPLICIT CIK:
TICKER-MAP BYPASS PRESERVED
```

## 4. Code findings

The candidate introduces deterministic timezone-aware `retrieved_at`
normalization and computes:

```text
ticker_snapshot_id =
SHA256(canonical_json({
  source_url,
  lowercase source_sha256,
  normalized retrieved_at
}))
```

New online snapshots are persisted below the Design-39 observation directory.

Current observation loading verifies:

- current path identity;
- official source URL;
- snapshot identity;
- source bytes SHA;
- derivative mapping rebuilt from source bytes;
- retrieval timestamp validity.

Legacy root-level `<source_sha>.json` snapshots remain readable without
requiring a new `snapshot_id`, and their filename is checked against the source
SHA.

Local cached resolution now verifies all candidate snapshots, selects one newest
verified snapshot deterministically, and resolves the ticker only within that
selected snapshot. It no longer merges historical CIKs or falls back to an
older snapshot when the newest map lacks the ticker.

Online ticker resolution writes only the new observation path. Explicit CIK
returns before creating/fetching ticker-map state.

## 5. Design-39 test coverage

Focused development coverage reports 10/10 tests covering:

- identical bytes at two retrieval times;
- production acquire→ingest repetition;
- true same-observation conflict;
- legacy byte immutability;
- source-byte tamper;
- derivative tamper;
- newest snapshot selection;
- no stale fallback;
- explicit-CIK zero ticker-map fetch;
- Formal-Test-4 failure-boundary reproduction.

The test named T147-10 directly exercises the ticker-persistence boundary,
while T147-02 exercises the complete acquire→ingest production flow. Together
they satisfy the frozen behavior requirement.

A historical-format legacy file without `snapshot_id` is accepted by the
loader design; Formal Test 5 must independently exercise that exact legacy
shape rather than relying only on the development fixture helper.

## 6. Regression evidence accepted for code review

Exact-candidate development evidence reports:

```text
ISSUE-147 focused = 10 passed
US SEC = 263 passed
MCP = 65 passed
P0-P10 = 371 passed
full unit = 793 passed
compileall = PASS
git diff --check = PASS
```

No failures or skips were reported.

Apple FY2025 ticker-based developer smoke reports two snapshots with the same
source SHA and different observation IDs/timestamps, and the second online
ingest no longer raises `P11_SOURCE_DRIFT`.

## 7. Live package-identity observation for Formal Test 5

Formal Test 4 recorded Apple FY2025 package SHA:

`1196a354461ac65afa4ce7f1c67b2d65b04c1e496f521f34a139c6d6e5872d3d`

The ISSUE-147 developer smoke records:

`d94d8c46e34ce25af8d42279dbb4a370b1e617d7daf421743f29468b77d19568`

Candidate f1cc768 changes no package/acquisition code.

The package SHA is derived only from the canonical package member records
(relative name, role, member SHA, byte length). Therefore this SHA difference is
not attributable to the ISSUE-147 code path itself.

Formal Test 5 must compare the live member sets and member SHAs against both
receipts and classify the difference explicitly as current official-byte/member
change, prior workspace difference, or a newly discovered defect. It must not
silently accept unexplained package identity drift.

This observation does not block code REVIEW_PASS because the production code
that computes/selects the package did not change in this candidate and the
development smoke completed with valid package/validation/research-ready state.

## 8. Frozen version contract

Unchanged:

```text
REGISTRY_SCHEMA_VERSION = 1
SEC_REGISTRY_SCHEMA_VERSION = 4
SEC_DISCOVERY_SCHEMA = p11-sec-discovery-v1
VIRTUAL_HTML_NORMALIZER_VERSION = VIRTUAL_HTML_V6
SEC_ARTIFACT_SCHEMA = p11-sec-artifacts-v2
SEC_VALIDATION_SCHEMA = p11-sec-validation-v3
```

No new P11 reason code is introduced.

ISSUE-140..146 remain regression-preservation scope.

## 9. Lifecycle verdict

```text
FRESH FULL EXACT-CANDIDATE REVIEW:
REVIEW_PASS

FORMAL TEST PLAN 5:
AUTHORIZED TO CREATE / NOT YET FROZEN IN THIS COMMIT

FORMAL TEST EXECUTION:
NOT YET AUTHORIZED

FORMAL ACCEPTANCE:
NOT PASSED

MAIN MERGE:
NOT AUTHORIZED

P11 DONE:
NO
```
