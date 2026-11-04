# 247 - P11-E Acquisition / Package Design Preflight Review STOP

Status: **STOP - P11-ISSUE-046 OPEN / CANDIDATE 78fd91e INELIGIBLE / DESIGN AMENDMENT REQUIRED / IMPLEMENTATION CLOSED**

Reviewed design candidate:
78fd91eb257a52b895c2ed357c88c4bf849e640b

Evidence:
development/246-p11-e-acquisition-package-design-evidence.md

The candidate passed scope/static/probe checks, but implementation-feasibility review found material contract gaps that must not be guessed during implementation.

## P11-ISSUE-046A - receipt ownership/loadability inconsistency

Candidate SecSourcePackage includes receipt_id while SecPackageStore.load_package(source_package_sha256) is defined to reconstruct a package from immutable manifest/blob state.

receipt_id is deliberately excluded from package identity/manifest, and the same immutable package may legitimately have multiple distinct stable HTTP receipt identities when final URL/ETag/Last-Modified/declared Content-Type changes.

Therefore load_package(package_sha) cannot deterministically produce one receipt_id without an extra mutable selection rule. The package model and acquisition-result model must be separated so receipt_id belongs to acquisition result, not immutable package.

## P11-ISSUE-046B - same-accession drift scan corruption boundary

The candidate says drift classification scans committed package manifests and corrupted existing package encountered during same-accession scan blocks.

It does not define how an unrelated corrupted package is distinguished before its manifest can be trusted. A global full-loader scan could let corruption in an unrelated accession block every acquisition; ignoring all invalid manifests could silently hide a corrupted same-accession version.

The amendment must freeze a two-stage scan:
1. minimal safe JSON peek used only to select candidate manifests whose exact valid cik/accession fields match the current accession;
2. full package loader verification only for those matching candidates.
Unreadable/malformed manifests that cannot establish the same stable provider identity are not drift candidates and do not block unrelated acquisition. A parseable manifest claiming the same cik/accession but failing full validation must block.

## P11-ISSUE-046C - provider size lexical/resource safety

The candidate correctly limits only selected assets to 128 MiB, but permits an arbitrary-length decimal size string for unselected rows. JSON is capped, yet direct arbitrary-size integer conversion is implementation-dependent and can become a CPU/implementation-limit hazard.

Freeze an exact lexical bound before integer conversion. P11-E v1 will accept empty string or 1..20 ASCII decimal digits. Selected assets must additionally parse <=134,217,728; unselected decimal values may exceed that selected cap without invalidating the index.

## P11-ISSUE-046D - receipt row/diagnostic aggregation and registry acquired_at

The candidate does not explicitly say whether receipt response rows represent retries/redirect attempts or final logical resources.

Freeze:
- exactly one response identity row per successfully captured logical requested resource: index.json plus every selected filing asset;
- retry/redirect attempts affect diagnostics only, not response row multiplicity;
- request_count = total emitted HTTP starts across all logical resource fetches;
- retry_count/redirect_count = sums of scheduled retries/followed redirects;
- bytes_downloaded = sum of successful final entity bytes used by the package;
- if an existing receipt identity is reused with different current diagnostics, existing receipt bytes/diagnostics remain authoritative; registry SourceMetadata.acquired_at uses the committed/reused receipt file's acquired_at, not a discarded current-attempt timestamp.

## P11-ISSUE-046E - caller registry validation

registry is a caller argument. Before network it must be either None or an SQLiteRegistry instance; otherwise ValueError. This preserves the candidate's stated caller-validation-before-network boundary.

## Required remediation

- amend design/32 only; preserve all accepted P11-A through P11-D behavior.
- update design evidence with the exact corrections.
- keep src/tests/runtime-locks unchanged.
- freeze a new exact candidate.
- only then authorize fresh detached design review.

# STOP

Candidate 78fd91eb257a52b895c2ed357c88c4bf849e640b is INELIGIBLE.
P11-E implementation remains CLOSED.
P11 provider production remains CLOSED.
