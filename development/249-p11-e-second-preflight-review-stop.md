# 249 - P11-E Second Design Preflight Review STOP

Status: **STOP - P11-ISSUE-047 OPEN / CANDIDATE d7b0d19 INELIGIBLE / DESIGN HARDENING REQUIRED / IMPLEMENTATION CLOSED**

Reviewed amended candidate:
d7b0d195511490f049a40e419862e27e62118be8

ISSUE-046 amendment evidence:
development/248-p11-e-issue046-amendment-evidence.md = PASS

The ISSUE-046 remediation is coherent, but final implementation-feasibility review before detached-review authorization found three remaining exactness gaps.

## P11-ISSUE-047A - requested index.json exhibit contradiction

design/32 currently says a requested exhibit already included by role rules 1-3 is satisfied without a duplicate, but also says every requested exhibit must match exactly one index item. The accession index itself is a synthetic FILING_INDEX asset and design/32 separately forbids an item named index.json.

Freeze:
- requested exhibit name exactly index.json is satisfied by the synthetic FILING_INDEX asset and requires no index item.
- every other requested exhibit must match exactly one validated item.
- primary/structured matches retain their higher role and add no duplicate.

## P11-ISSUE-047B - receipt response normalization affects receipt_id

receipt_id hashes requested_url, final_url and selected response headers, but their exact canonical representation is not yet frozen.

Freeze:
- requested_url is exact canonical initial www.sec.gov Archive URL.
- final_url uses the accepted canonical SEC URL identity form: https, lowercase host, default :443 omitted, exact validated path, empty query/fragment.
- successful receipt row status is exactly 200.
- index declared_content_type is canonical application/json.
- asset declared_content_type is null when absent, otherwise outer ASCII SP/HTAB trimmed validated value preserving case/interior bytes.
- ETag and Last-Modified are null when absent, otherwise outer SP/HTAB trimmed validated visible-ASCII values preserving case/interior bytes.
- repeated/invalid values fail before receipt identity construction.
- acquired_at diagnostic format is exact UTC YYYY-MM-DDTHH:MM:SS.ffffffZ.

## P11-ISSUE-047C - current package must be excluded from drift Stage-1 scan

The current package has already passed Section 13 full verification. Drift scanning should enumerate only other package hashes. This removes an unnecessary special case for over-cap/current manifest peeking and makes other_hashes semantics direct.

Freeze:
- Stage 1 skips the directory whose hash equals current source_package_sha256.
- all Stage-1 rules apply only to other package hashes.
- current package commit outcome remains the exact ACQUIRED_NEW vs REUSED_EXACT discriminator when other_hashes is empty.

## Additional public API exactness

Before formal review also freeze:
- SecPackageStore constructor invalid project_root exact ValueError.
- load_package invalid SHA exact ValueError.
- returned manifest_path is the resolved final manifest path and is storage metadata only.

# STOP

Candidate d7b0d195511490f049a40e419862e27e62118be8 is INELIGIBLE.
P11-E implementation remains CLOSED.
P11 provider production remains CLOSED.
