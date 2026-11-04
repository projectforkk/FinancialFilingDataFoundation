# 253 - P11-E ISSUE-048 Amendment Evidence

Status: **PASS - ISSUE-048 A-L REMEDIATED / FINAL AMENDED DESIGN READY FOR NEW EXACT-CANDIDATE REVIEW / IMPLEMENTATION CLOSED**

Historical ineligible candidates:
- 78fd91eb257a52b895c2ed357c88c4bf849e640b - ISSUE-046
- d7b0d195511490f049a40e419862e27e62118be8 - ISSUE-047
- bc57207c4989c8500fcd8fda8910d783b42e1daa - ISSUE-048 formal detached review

Formal STOP:
development/252-p11-e-final-detached-design-review-stop.md

Amended contract:
design/32-p11-e-acquisition-package-contract.md

Prior evidence retained:
- development/246-p11-e-acquisition-package-design-evidence.md
- development/248-p11-e-issue046-amendment-evidence.md
- development/250-p11-e-issue047-amendment-evidence.md

## A - canonical immutable bytes

PASS:
- stored manifest must equal canonical reserialization of the complete validated final object plus exactly one LF.
- semantically equal but noncanonical whitespace/key-order/number encoding is rejected.
- manifest exact JSON types/schema are frozen; bool/int interchange is rejected.
- loader independently re-parses the exact FILING_INDEX blob under the complete index schema.
- loader proves primary/automatic structured completeness, exact role precedence, source URLs, declared sizes, blob hashes and caps.
- exact FILING_INDEX bytes retain ignored provider metadata, so any byte change can affect package identity through the index asset SHA.

## B - receipt atomic commit

PASS:
- receipt is built under this attempt's staging tree.
- local 16 MiB cap, flush/fsync and precommit reload/validation are required.
- final commit uses the P11-B-proven non-replacing file primitive.
- exact outcomes: COMMITTED_NEW, DESTINATION_EXISTS, COMMIT_ERROR.
- COMMITTED_NEW reloads/validates final.
- DESTINATION_EXISTS validates existing identity/canonical bytes and preserves authoritative existing diagnostics/acquired_at.
- COMMIT_ERROR never becomes success from a later existence observation.
- only own staging is cleaned.

## C - local generated-artifact and I/O mapping

PASS:
- remote response/per-asset/streamed aggregate cap => P11_RESPONSE_TOO_LARGE.
- locally generated manifest/receipt >16 MiB => P11_PACKAGE_INVALID.
- project-root escape or symlink/junction/reparse containment => P11_PATH_OUTSIDE_PROJECT.
- verified existing non-reparse content/hash mismatch => P11_PACKAGE_HASH_MISMATCH.
- other local root/staging/file creation/write/flush/fsync/close/atomic commit I/O => P11_PACKAGE_INVALID.

## D - concurrent drift snapshot

PASS:
- after current package + authoritative receipt verification, direct package child names are captured once and ASCII-sorted.
- later concurrent package commits are intentionally outside this attempt's outcome.
- later acquisition observes them; drift notification is snapshot-based/eventually complete rather than globally linearizable.
- current package hash is excluded from normal Stage-1 candidates.

## E - exact finalization order

PASS:
- finalization starts only after index and all selected assets have fetched/validated successfully.
- exact order: blobs -> package -> authoritative receipt -> drift snapshot/classification -> optional registry -> result.
- failure stops later steps and never mutates already committed immutable earlier objects.

## F - optional exhibit selection versus source drift

PASS:
- package identity continues including REQUESTED_EXHIBIT rows.
- provider_core comparison excludes REQUESTED_EXHIBIT rows while retaining all top-level identity and automatic/core assets.
- shared requested-exhibit filename with different full asset row is drift evidence.
- requested-exhibit presence/absence only is caller selection-profile variation, not provider source drift.
- drift result prior hashes contain only verified packages that actually demonstrate provider/shared-exhibit drift.
- a new package caused only by a different optional-exhibit profile can be ACQUIRED_NEW; exact current package reuse can be REUSED_EXACT.

## G - public exception boundary

PASS:
- explicit caller-validation failures remain ValueError before network/raw-root mutation.
- all operational failures from P11-E package APIs surface as SecPackageError with exact reason_code.
- internal/shared SecHttpError is translated at the P11-E boundary without changing P11-D public behavior.
- raw User-Agent/contact text is forbidden from SecPackageError messages.

## H - additive public API compatibility

PASS:
- accepted P11-D root financial_filing_data_foundation.sec.__all__ remains unchanged.
- P11-E names live only in financial_filing_data_foundation.sec.package.
- sec.package.__all__ is exactly eight frozen symbols.
- SecAssetRole/SecPackageOutcome are StrEnum.
- public dataclass field types/order are exact.

## I - caller candidate cross-field consistency

PASS:
- CIK/accession/dates/primary are canonical and primary also satisfies stricter P11-E raw-request-target basename rules.
- form/base_form are exact str, amended exact bool.
- normalize_sec_form(form) must exactly reproduce base_form/amended and canonical form spelling.
- P11-D description/XBRL hints/provenance URLs are not promoted into P11-E package identity.

## J - provider filename local-path safety

PASS:
- provider/caller file_name is URL/package metadata only, never a local filesystem component.
- staged resource filenames use internal safe ordinals/tokens.
- final blob/package/receipt components use hashes/fixed internal names only.
- Windows-invalid filename characters that are legal HTTP basename bytes cannot escape into local paths.

## K - extensionless registry blob boundary

PASS:
- registry receives the verified final extensionless SHA-addressed primary blob directly.
- no extension alias/hardlink/copy is created for registration.
- P11-E validates only returned document SHA equality; it does not rewrite/interprete registry file_path/page_count.
- new extensionless document record may naturally have page_count=None; existing same-SHA record may retain prior accepted path/page_count.
- P11-F uses package manifest/file_name/blob identity, not registry suffix.

## L - requested index.json exhibit compatibility

PASS after cross-check with design/26 and acceptance/41:
- every requested exhibit must match exactly one validated provider index item.
- synthetic FILING_INDEX does not satisfy a caller request for literal index.json.
- a provider item named index.json is independently invalid, so requested index.json resolves to P11_PACKAGE_ASSET_MISSING after index validation.
- higher-role no-duplicate behavior remains for actual provider items already selected as primary/structured.

## Additional loader/receipt/drift hardening

PASS:
- FILING_INDEX <=16 MiB, every other asset <=128 MiB, selected count <=1024, aggregate <=512 MiB, manifest <=16 MiB.
- FILING_INDEX is exactly one non-primary index.json row; PRIMARY_DOCUMENT exactly one.
- receipt exact schema versions/types/order are validated; bool is never accepted as int.
- receipt response rows form a package-resource bijection.
- receipt counters obey response_count <= request_count <= response_count + retry_count + redirect_count and per-resource retry/redirect upper bounds.
- acquired_at exact UTC YYYY-MM-DDTHH:MM:SS.ffffffZ.
- missing current index/primary/automatic-structured source becomes raised P11_SOURCE_CONTENT_DRIFT only when a fully verified prior same-accession package exists; caller optional-exhibit absence never upgrades to drift.
- caller validation completes before any network request or raw-root/staging creation.

## Semantic and concurrency probes

Project-local probes PASS:
- canonical package fixture = 16e76f846fcdccf44216816148ba346ae5c100f3fcdf6fa170a6f954267bae78.
- receipt diagnostics excluded from receipt identity.
- file/dir non-replacing commit.
- two-writer file race = exactly one COMMITTED_NEW + one DESTINATION_EXISTS.
- two-writer directory race = exactly one COMMITTED_NEW + one DESTINATION_EXISTS.
- junction/reparse detection.
- raw-root containment negative.
- selection-only package difference is not drift.
- shared requested-exhibit byte change is drift.
- provider-core change is drift.
- drift outcome precedence PASS.
- canonical versus noncanonical receipt bytes distinguishable.
- receipt_id recomputation PASS.
- drift snapshot eventual visibility PASS.
- missing-current-source with verified prior => drift PASS.

## Mechanical review gates

PASS:
- git diff --check.
- design headings exactly 1..22.
- mandatory cases exactly 1..60.
- finalization-order normative paragraph appears exactly once.
- stale requested-index special case count = 0.
- P11-ISSUE-048 headings A through L are present in development/252.
- no src/, tests/, integration/ or runtime-lock changes.

## Verdict

# PASS

P11-ISSUE-048 A-L is REMEDIATED at design level.

Candidate bc57207c4989c8500fcd8fda8910d783b42e1daa remains INELIGIBLE.
The amended design must be frozen as a new exact candidate and pass another fresh detached full P11-E design review before implementation authorization.

P11-E implementation remains CLOSED.
P11 provider production remains CLOSED.
