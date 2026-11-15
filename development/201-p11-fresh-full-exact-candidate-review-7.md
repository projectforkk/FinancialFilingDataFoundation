# 201 — P11 Fresh Full Exact-Candidate Review 7

Status: **REVIEW_PASS**

This is the fresh full review of exact production candidate
`6eaace08c9ba5fb26809a7e02de5835123fb667a` and documentation-only evidence
child `5ce97e18456c9e877c223df7abf01eec53e1f3ad`.

It is not a Formal Test Plan, Formal Acceptance, main-merge authorization, or
P11 DONE record.

## 1. Exact authority

- Repository: `projectforkk/FinancialFilingDataFoundation`
- Authoritative remote lineage: `reconcile/p11-140-143-local-chain`
- Design 38 baseline: `92af6205eb8e090994dcece68850eddcd4232392`
- Development reauthorization:
  `48ff2dc3ff3219fe6811b2ce4a169bf7b480e00e`
- Previous candidate:
  `35e2b70c78b6cff931c8484dc38f2eb7349735f5`
- Exact reviewed production candidate:
  `6eaace08c9ba5fb26809a7e02de5835123fb667a`
- Development evidence:
  `development/200-p11-review6-issue146-evidence.md`
- Evidence commit:
  `5ce97e18456c9e877c223df7abf01eec53e1f3ad`

Candidate → evidence changes exactly one documentation file:

`development/200-p11-review6-issue146-evidence.md`

No production/test bytes changed after the candidate.

## 2. Git lineage

```text
48ff2dc3ff3219fe6811b2ce4a169bf7b480e00e
  ↓ one production/test commit
6eaace08c9ba5fb26809a7e02de5835123fb667a
  ↓ one documentation-only commit
5ce97e18456c9e877c223df7abf01eec53e1f3ad
```

The authoritative remote branch points at the evidence child.

## 3. Review result

```text
ISSUE-140: FIXED / PRESERVED
ISSUE-141: FIXED / PRESERVED
ISSUE-142: FIXED / PRESERVED
ISSUE-143: FIXED / PRESERVED
ISSUE-144: GOVERNANCE CORRECTED
ISSUE-145: FIXED / PRESERVED
ISSUE-146: FIXED

VALIDATION-V3 PERSISTENCE:
PASS

REVALIDATE_LOCAL:
PASS

CORRUPT V3 FAIL-CLOSED:
PASS

REGISTRY CURRENT-V3 REFRESH:
PASS

FRESH FULL EXACT-CANDIDATE REVIEW:
REVIEW_PASS
```

## 4. ISSUE-146 code findings

The candidate separates compatible parsed-artifact discovery from current
validation-v3 reuse eligibility.

`SecPlanAction.REVALIDATE_LOCAL` is present and the planner implements the
Design 38 state machine:

- compatible parsed + reusable current v3 → REUSE_DATA;
- compatible parsed + absent current v3 → REVALIDATE_LOCAL;
- compatible parsed + valid non-reusable current v3 → REVALIDATE_LOCAL;
- no compatible parsed + local package → PARSE_LOCAL;
- no local package → DISCOVER_AND_ACQUIRE.

The current v3 loader is evaluated separately and a present corrupt v3 raises
the current integrity error rather than falling back to legacy v2.

The normal CLI acquire→ingest path carries REVALIDATE_LOCAL through without
invoking the parser.

`revalidate_sec_package()` loads the existing V6/v2 parsed artifact, executes
P7 validation-v3 directly, refreshes Registry/slot/catalog state, and computes
research readiness from the new current validation.

Both REVALIDATE_LOCAL and REUSE_DATA fresh-discovery refresh update the same
deterministic parsed-run identity:

`sha256(package_sha256 + "|" + parser_version)`.

The Registry upsert updates validation status, compatibility, blocking count,
and parsed artifact path without fabricating a new parse identity.

## 5. Regression preservation

Relative to candidate
`35e2b70c78b6cff931c8484dc38f2eb7349735f5`, the Review-6 production change
does not modify the Review-5 source-replay implementation in discovery,
validation, or parser.

Therefore the previously reviewed ISSUE-142/143/145 semantics remain unchanged,
with the development regression suite providing additional preservation
evidence.

## 6. Development verification accepted for code review

Evidence at exact candidate reports:

```text
ISSUE-146 focused:
9 passed

complete tests/unit/us_sec:
253 passed

complete tests/unit:
783 passed

compileall:
PASS

git diff --check:
PASS
```

The first long-basetemp full-unit run hit Windows path-length failures; the same
exact candidate was rerun with a short temporary root and passed 783/783 with no
source/test modification.

Apple FY2025 developer smoke at the exact candidate reports:

- planner action: DISCOVER_AND_ACQUIRE;
- accession: `0000320193-25-000079`;
- discovery state: UNAMBIGUOUS;
- fact source mode: INLINE_XBRL_PRIMARY;
- fact count: 1131;
- validation schema: p11-sec-validation-v3;
- validation PASS;
- blocking=0;
- review=0;
- P8 catalog ADDED;
- research_ready=true.

MCP stdio developer smoke reports protocol operation with 26 tools and two
acceptance documents.

The developer Apple receipt did not capture all transport-classification counts
required for Formal Acceptance, including selected history chunks/history fetch
count and static-asset fetch count. Those are mandatory Formal Test evidence
items and are not treated as a production-candidate defect.

## 7. Frozen versions

```text
SEC_DISCOVERY_SCHEMA = p11-sec-discovery-v1
VIRTUAL_HTML_NORMALIZER_VERSION = VIRTUAL_HTML_V6
SEC_ARTIFACT_SCHEMA = p11-sec-artifacts-v2
SEC_VALIDATION_SCHEMA = p11-sec-validation-v3
SEC_REGISTRY_SCHEMA_VERSION = 4
```

`P11_RAW_FACT_SOURCE_MISMATCH` remains the frozen blocking Raw Fact/source
semantic mismatch reason.

## 8. Formal lifecycle decision

```text
REVIEW_PASS:
YES

FORMAL TEST PLAN:
AUTHORIZED TO CREATE / NOT YET FROZEN IN THIS COMMIT

FORMAL TEST EXECUTION:
NOT YET AUTHORIZED

FORMAL ACCEPTANCE:
NOT RUN

MAIN MERGE:
NOT AUTHORIZED

P11 DONE:
NO
```

The next action is a separate Git commit containing the Formal Test Plan. Formal
execution may begin only after ChatGPT reviews and accepts that exact plan SHA.
