# 195 — P11 Validation-v3 Persistence Design Review

Status: **DESIGN_FREEZE_CHANGES_REQUIRED — DEVELOPMENT NOT AUTHORIZED**

This document records the final persistence-contract finding discovered while
preparing the development instruction for the exact Design 37 freeze
`9d25e3a03c762c4da1986a7ca4be7b98080ffbcf`.

It is not a Formal Test Plan, Formal Acceptance, merge authorization, or P11
DONE record.

## 1. Reviewed freeze

- Repository: `projectforkk/FinancialFilingDataFoundation`
- Lineage: `reconcile/p11-140-143-local-chain`
- Reviewed freeze: `9d25e3a03c762c4da1986a7ca4be7b98080ffbcf`
- Current detailed correction: `design/37-p11-review5-freeze-consistency-and-raw-fact-binding.md`

## 2. Review result

```text
ISSUE-142 TECHNICAL DESIGN: PASS
ISSUE-143 TECHNICAL DESIGN: PASS
ISSUE-145 TECHNICAL DESIGN: PASS
DESIGN 27 / DESIGN 00 GOVERNANCE POINTERS: PASS

VALIDATION-V2 → V3 PERSISTENCE CONTRACT:
INCOMPLETE / BLOCKING

FINAL DESIGN FREEZE:
CHANGES_REQUIRED

DEVELOPMENT_AUTHORIZED:
NO
```

## 3. Finding

Current production validation writes the current SEC validation result into the
flat package directory:

```text
workspace/ingest/us/p7/<package_sha256>/validation.json
workspace/ingest/us/p7/<package_sha256>/issues.jsonl
```

Design 37 simultaneously requires historical validation-v2 bytes to remain
immutable and the new validation-v3 contract to execute.

Changing only `SEC_VALIDATION_SCHEMA` from v2 to v3 would therefore overwrite
the historical v2 files in place. US CLI reuse, US ingest/reuse, and P8 also
derive or load the flat path, so persistence identity cannot be left as an
implementation-time choice.

## 4. Frozen correction

Design 37 now freezes validation identity as:

```text
package_sha256
+
SEC_VALIDATION_SCHEMA
```

Current v3 location:

```text
workspace/ingest/us/p7/
  <package_sha256>/
    p11-sec-validation-v3/
      validation.json
      issues.jsonl
```

Historical flat v2 files remain read-only and byte-immutable.

Current runtime reuse and P8 must resolve v3 through one shared deterministic
versioned-path rule. There is no fallback from missing/corrupt v3 to v2.

A compatible V6 / artifacts-v2 parsed artifact may be reused as local input for
v3 revalidation without a parser rerun solely because validation is old.

## 5. Version contract

```text
SEC_DISCOVERY_SCHEMA = p11-sec-discovery-v1
VIRTUAL_HTML_NORMALIZER_VERSION = VIRTUAL_HTML_V6
SEC_ARTIFACT_SCHEMA = p11-sec-artifacts-v2
SEC_VALIDATION_SCHEMA = p11-sec-validation-v3
SEC_REGISTRY_SCHEMA_VERSION = 4
```

No Registry bump is required.

## 6. Governance state

```text
FORMAL TEST PLAN: NOT CREATED / NOT AUTHORIZED
FORMAL ACCEPTANCE: NOT RUN
MAIN MERGE: NOT AUTHORIZED
P11 DONE: NO
```

The next action is ChatGPT review of the exact documentation-only commit that
contains this persistence correction. Production and test implementation remain
blocked until explicit `DESIGN_FREEZE_PASS / DEVELOPMENT_AUTHORIZED`.
