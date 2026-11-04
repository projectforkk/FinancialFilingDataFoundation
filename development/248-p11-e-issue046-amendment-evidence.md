# 248 - P11-E ISSUE-046 Amendment Evidence

Status: **PASS - ISSUE-046 REMEDIATED / AMENDED DESIGN READY FOR EXACT-CANDIDATE REVIEW / IMPLEMENTATION CLOSED**

Historical ineligible candidate:
78fd91eb257a52b895c2ed357c88c4bf849e640b

STOP:
development/247-p11-e-design-preflight-review-stop.md

Amended contract:
design/32-p11-e-acquisition-package-contract.md

Initial design evidence retained as historical baseline:
development/246-p11-e-acquisition-package-design-evidence.md

## ISSUE-046A receipt ownership/loadability

Remediated:
- immutable SecSourcePackage no longer contains receipt_id.
- SecPackageStore.load_package(source_package_sha256) reconstructs only immutable manifest/blob package state.
- SecPackageAcquisitionResult now contains receipt_id.
- one immutable source package may have multiple valid acquisition receipt identities over time without changing source_package_sha256.

This removes the impossible requirement for load_package(package_sha) to choose one receipt.

## ISSUE-046B drift scan corruption boundary

Remediated with a two-stage committed-package scan.

Stage 1:
- considers only exact 64-lowercase-hex package directories with regular non-reparse manifest.json inside raw root.
- reads at most the frozen 16 MiB manifest cap plus one sentinel byte.
- requires in-cap strict UTF-8/no-BOM/JSON object before inspecting only cik and accession_number.
- manifests unable to establish both exact valid current stable identity fields are not drift candidates and do not block unrelated acquisition.
- no Stage-1 peek is treated as reusable/valid package state.

Stage 2:
- every Stage-1 same-accession candidate is fully loaded through SecPackageStore.load_package().
- any parseable same-cik/accession candidate that fails full package/hash/blob/layout validation blocks and cannot be ignored as unrelated corruption.

Classification is now exact:
- other verified same-accession hashes non-empty => SOURCE_CONTENT_DRIFT, reason P11_SOURCE_CONTENT_DRIFT, sorted unique other hashes.
- otherwise current package COMMITTED_NEW => ACQUIRED_NEW with empty prior tuple.
- otherwise exact verified DESTINATION_EXISTS reuse => REUSED_EXACT with empty prior tuple.
- COMMIT_ERROR never reaches outcome classification.

This fixes the prior ambiguity caused by scanning after the current package is already committed.

## ISSUE-046C provider size lexical safety

Remediated:
- raw item.size is accepted only as empty string or ASCII decimal matching ^[0-9]{1,20}$.
- no integer conversion occurs before that lexical bound passes.
- selected items additionally require parsed size <=134,217,728.
- unselected bounded-decimal values may exceed the selected asset cap without invalidating the index.
- selected empty size remains P11_PACKAGE_INVALID before asset download.

This preserves official observed size="" helper rows while bounding conversion/resource behavior.

## ISSUE-046D receipt aggregation and authoritative diagnostics

Remediated:
- receipt responses contain exactly one row per successful logical resource used by the package: index.json plus each selected filing asset.
- retry attempts/redirect hops never create extra receipt identity rows.
- request_count = sum of actual emitted request starts across all logical resource fetches.
- retry_count = sum of scheduled retries.
- redirect_count = sum of followed redirects.
- bytes_downloaded = sum of final successful entity bytes used by the package, once per logical resource.
- receipt identity remains independent of timing/acquired_at diagnostics.
- receipt JSON has a frozen 16 MiB cap.
- same receipt identity with different current diagnostics reuses existing authoritative receipt bytes without overwrite.
- acquisition result returns the committed/reused receipt_id.
- registry SourceMetadata.acquired_at comes from the committed/reused receipt file, never a discarded current-attempt timestamp.

## ISSUE-046E caller registry validation

Remediated:
- registry must be None or the accepted SQLiteRegistry instance.
- any other value raises exact ValueError("registry must be SQLiteRegistry or None") before network.

## Additional preflight hardening

The amendment also freezes:
- manifest.json byte cap = 16 MiB.
- drift Stage-1 uses that same manifest cap.
- mandatory matrix remains exactly cases 1..60 with updated traceability for size lexical bound, immutable package/receipt separation, receipt aggregation, drift scan, and registry acquired_at.
- headings remain exactly 1..22.

Mechanical checks:
- git diff --check = PASS.
- headings 1..22 = PASS.
- mandatory cases 1..60 = PASS.
- ISSUE-046 contract invariant scan = PASS.
- no src/, tests/, integration/ or runtime-lock production change = PASS.

## Preserved evidence/contracts

Unchanged and still PASS from development/246:
- official live 10-K/10-Q/8-K SEC index schema observations.
- canonical package fixture hash 16e76f846fcdccf44216816148ba346ae5c100f3fcdf6fa170a6f954267bae78.
- receipt diagnostics-exclusion semantic probe.
- Windows file and directory atomic non-replacing commit.
- two-writer file/directory convergence.
- junction/reparse detection.
- project-root containment negative probe.
- P2 RawDocumentStore immutability and registry schema/API non-expansion.
- P11-D shared rate/security boundary.
- P11-E/P11-F separation.

## Verdict

# PASS

P11-ISSUE-046 is REMEDIATED at design level.

The historical candidate 78fd91eb257a52b895c2ed357c88c4bf849e640b remains INELIGIBLE.
A new exact amended design candidate must be committed and pass a fresh detached design review before any P11-E implementation authorization.

P11-E implementation remains CLOSED.
P11 provider production remains CLOSED.
