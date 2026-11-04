# 250 - P11-E ISSUE-047 Amendment Evidence

Status: **PASS - ISSUE-047 REMEDIATED / FINAL PREFLIGHT COMPLETE / NEW EXACT DESIGN CANDIDATE REQUIRED / IMPLEMENTATION CLOSED**

Historical ineligible candidates:
- 78fd91eb257a52b895c2ed357c88c4bf849e640b - ISSUE-046
- d7b0d195511490f049a40e419862e27e62118be8 - ISSUE-047

STOP:
development/249-p11-e-second-preflight-review-stop.md

Current amended contract:
design/32-p11-e-acquisition-package-contract.md

Prior evidence retained:
- development/246-p11-e-acquisition-package-design-evidence.md
- development/248-p11-e-issue046-amendment-evidence.md

## ISSUE-047A requested index.json exhibit

Remediated:
- requested exhibit exactly index.json is satisfied by the synthetic FILING_INDEX logical asset.
- no provider item named index.json is required.
- every other requested exhibit must match exactly one validated provider item.
- primary/structured matches retain the higher role and add no duplicate.
- the separate rule that a provider item named index.json is invalid remains intact, preventing collision with the synthetic filing-index asset.

This reconciles the role-precedence contract with requested-exhibit completeness.

## ISSUE-047B receipt response canonicalization

Remediated:
- one receipt response row remains exactly one successful logical resource, not one retry/redirect attempt.
- requested_url is the exact canonical initial www.sec.gov Archive URL.
- final_url uses the accepted canonical SEC URL identity: https, lowercase host, default 443 omitted, exact validated path, empty query/fragment.
- status is exactly integer 200.
- index declared_content_type is canonical application/json.
- asset declared_content_type is null when absent, otherwise one validated outer-SP/HTAB-trimmed value preserving case/interior visible ASCII.
- ETag and Last-Modified are null when absent, otherwise one outer-SP/HTAB-trimmed non-empty visible-ASCII value preserving case/interior bytes.
- repeated/invalid receipt headers fail before receipt identity construction.
- acquired_at diagnostic format is frozen as UTC YYYY-MM-DDTHH:MM:SS.ffffffZ.

Therefore transport/header spelling decisions that affect receipt_id are no longer left to implementation choice.

## ISSUE-047C current package exclusion from drift scan

Remediated:
- Stage-1 drift scan considers only package hashes different from current source_package_sha256.
- the current package was already fully verified by the Section 13 package commit/reload path and is not peeked again.
- Stage-1 16 MiB peek cap applies only to other package hashes.
- other_hashes semantics now directly mean verified same-accession hashes excluding current.
- with other_hashes empty, current COMMITTED_NEW => ACQUIRED_NEW and exact verified DESTINATION_EXISTS => REUSED_EXACT.
- with other_hashes non-empty, SOURCE_CONTENT_DRIFT overrides either current package commit outcome.

This removes the prior current-package special case and aligns drift classification with the already frozen package commit outcome.

## Public API hardening

Also frozen before formal review:
- SecPackageStore invalid/missing/non-directory project root => exact ValueError("project_root must be an existing directory").
- load_package invalid source package SHA => exact ValueError("source_package_sha256 must be 64 lowercase hex") before filesystem access.
- successful package manifest_path is the resolved final manifest path and remains storage metadata outside package identity.

## Static evidence

PASS:
- git diff --check.
- design headings exactly 1..22.
- mandatory implementation matrix exactly 1..60.
- old "every requested exhibit must match an index item" contradiction absent.
- old current-package drift-peek special case absent.
- ISSUE-047 required contract strings present.
- no src/, tests/, integration/ or runtime-lock production changes.

## Preserved prior evidence

Still PASS and unchanged:
- official SEC 10-K/10-Q/8-K index schema probes.
- exact size="" helper-row observations.
- canonical package identity fixture hash 16e76f846fcdccf44216816148ba346ae5c100f3fcdf6fa170a6f954267bae78.
- receipt diagnostics-exclusion probe.
- file/directory atomic non-replacing commit probes.
- two-writer file/directory convergence.
- junction/reparse and raw-root containment probes.
- ISSUE-046 immutable package/receipt separation, bounded size grammar, two-stage drift validation, receipt aggregation and registry boundary.
- P11-D shared SEC rate/security contract.
- P2 RawDocumentStore and registry schema/API non-expansion.
- P11-E/P11-F separation.

## Verdict

# PASS

P11-ISSUE-047 is REMEDIATED.

Candidate d7b0d195511490f049a40e419862e27e62118be8 remains INELIGIBLE.
The amended design is ready to freeze as a new exact candidate and then enter fresh detached full P11-E design review.

P11-E implementation remains CLOSED.
P11 provider production remains CLOSED.
