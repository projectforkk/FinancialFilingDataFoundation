# 252 - P11-E Final Detached Design Review STOP

Status: **STOP - P11-ISSUE-048 OPEN / CANDIDATE bc57207 INELIGIBLE / DESIGN AMENDMENT REQUIRED / IMPLEMENTATION CLOSED**

Reviewed exact candidate:
bc57207c4989c8500fcd8fda8910d783b42e1daa

Authorization:
development/251-p11-e-final-design-review-authorization.md

Fresh detached worktree:
D:\Codex\FinancialFilingDataFoundation\worktrees\review\p11-e-design-bc57207

Integrity before STOP:
- exact detached HEAD = PASS.
- branchless/clean = PASS.
- design candidate already passed git diff --check.
- design/governance/evidence-only scope = PASS.
- headings 1..22 and mandatory cases 1..60 = PASS.
- ISSUE-046 and ISSUE-047 remediations are coherent and remain accepted design intent.

Full design review found remaining material finalization/storage ambiguities.

## P11-ISSUE-048A - canonical immutable byte validation incomplete

design/32 freezes canonical manifest/receipt serialization but the package loader does not yet explicitly require exact manifest bytes to equal reserialized canonical final-object bytes plus LF.

Without this, semantically equivalent JSON with altered whitespace/key order could pass parsed identity/hash checks while violating immutable byte determinism.

Freeze:
- package loader reconstructs final manifest object, canonical-serializes it plus exactly one LF, and requires exact byte equality with stored manifest.
- existing receipt validation does the same for the complete receipt object.
- receipt validator recomputes receipt_id from the canonical identity subobject and validates exact response ordering/schema/diagnostics types.

## P11-ISSUE-048B - receipt atomic commit semantics incomplete

Receipt says atomic non-replacing but does not freeze staging source, exact three outcomes, post-commit reload or COMMIT_ERROR semantics.

Freeze:
- receipt is fully built/validated under this attempt's project-local staging directory.
- same P11-B MoveFileExW non-replacing file primitive.
- COMMITTED_NEW => reload/validate final receipt.
- DESTINATION_EXISTS => exact existing identity/canonical validation, retain existing diagnostics/bytes.
- COMMIT_ERROR => fail closed and never reclassify from later destination existence.
- only own staging may be cleaned.

## P11-ISSUE-048C - local generated-artifact cap/I-O failure mapping

Response size violations already map P11_RESPONSE_TOO_LARGE, but local generated manifest/receipt 16 MiB cap and staging/write/fsync/local commit failures lack exact mapping.

Freeze:
- generated manifest or receipt exceeding its 16 MiB local cap => P11_PACKAGE_INVALID.
- local directory/staging/write/flush/fsync/rename errors that are not explicit path escape/hash mismatch => P11_PACKAGE_INVALID.
- path escape/reparse containment failure retains P11_PATH_OUTSIDE_PROJECT.
- verified existing-content mismatch retains P11_PACKAGE_HASH_MISMATCH.

## P11-ISSUE-048D - concurrent drift observation semantics

Atomic packages are safe, but package directories may be committed concurrently while Stage-1 drift enumeration runs.

Freeze a deterministic observation boundary:
- after current package and receipt are committed/reloaded, enumerate the direct package-directory names exactly once and ASCII-sort that snapshot.
- only snapshot entries are considered in this attempt.
- package directories committed after snapshot capture are intentionally outside the current outcome and will be observed by a later acquisition.
- immutable preservation is strong; drift notification is snapshot-based/eventually complete, not a global linearizable lock.
- the current package hash is excluded from the snapshot candidates.
- later exact reacquisition must surface any now-visible historical other hash.

## P11-ISSUE-048E - finalization order

Freeze one exact post-download order:
1. commit/reuse/verify all blobs.
2. build/commit/reload final package.
3. build/commit/reload authoritative receipt.
4. capture one drift package-directory snapshot, fully verify matching same-accession candidates, classify outcome.
5. if registry supplied, register primary through existing register_document using committed receipt acquired_at.
6. return SecPackageAcquisitionResult.

Any failure stops at its step; already committed immutable earlier objects remain unchanged. No later step retroactively mutates earlier objects.

## P11-ISSUE-048F - optional exhibit selection must not masquerade as provider source drift

Package identity correctly includes REQUESTED_EXHIBIT rows, so changing caller requested exhibits can create a different source_package_sha256 even when SEC provider content is unchanged. Treating every same-accession different package hash as P11_SOURCE_CONTENT_DRIFT would therefore be a false positive.

Freeze a derived comparison rule that does not change package identity:
- provider core = all top-level package identity fields plus every asset row whose role is not REQUESTED_EXHIBIT.
- requested-exhibit comparison = exact REQUESTED_EXHIBIT rows keyed by file_name.
- a prior same-accession package demonstrates provider drift if provider core differs, or if a requested exhibit present in both packages has a different identity row/bytes.
- a package difference caused only by requested exhibits present on one side and absent on the other is selection-profile variation, not source drift.
- prior_source_package_sha256s in a drift result contains only prior hashes that actually demonstrate drift under this rule.
- a newly committed package created only because the caller requested a different optional exhibit set is ACQUIRED_NEW when no drift-evidence prior exists; an exact existing current package is REUSED_EXACT when no drift-evidence prior exists.

Missing-current-source drift remains accession-level because no valid current package exists for profile comparison.

## P11-ISSUE-048G - public exception boundary

P11-E defines SecPackageError but does not yet freeze whether internal/shared SecHttpError may leak from acquire_sec_package. That would make caller behavior implementation-dependent.

Freeze:
- invalid caller arguments remain ValueError before network/filesystem mutation as already specified.
- every operational P11-E failure after caller validation, including shared HTTP/rate/path/package/drift-missing/registry failures, is surfaced by P11-E public package APIs as SecPackageError carrying the exact mapped reason_code.
- shared internal SecHttpError is translated at the P11-E boundary with the same reason_code and sanitized message; P11-D public behavior is unchanged.
- raw User-Agent/contact text never appears in SecPackageError messages.

## P11-ISSUE-048H - exact additive public API compatibility

P11-D already froze the root financial_filing_data_foundation.sec public export set. P11-E must not silently widen that accepted root API, and the package dataclass/enum field annotations must be exact rather than inferred from prose names.

Freeze:
- financial_filing_data_foundation.sec.__all__ remains exactly the accepted P11-D eight-symbol set.
- P11-E public symbols live only in financial_filing_data_foundation.sec.package with its own exact eight-symbol __all__.
- SecAssetRole and SecPackageOutcome are StrEnum.
- all public dataclass field annotations/types/order are exact.

## P11-ISSUE-048I - caller candidate cross-field consistency

SecDiscoveryCandidate is a frozen data object but P11-E accepts it as caller input. Revalidating fields independently is insufficient if form/base_form/amended can disagree, because package identity and registry source_title would then diverge.

Freeze exact caller checks before network:
- normalized CIK/accession/date/report-date/primary basename must equal the candidate's canonical stored values.
- normalize_sec_form(candidate.form) must reproduce candidate.base_form and candidate.amended, and candidate.form must equal the canonical base form plus optional /A spelling.
- discovery provenance URLs, primary_doc_description and XBRL hint booleans are not package identity/selection inputs in P11-E and are not promoted into package identity.

## P11-ISSUE-048J - provider filename must never become a local path component

The accepted Archive basename grammar intentionally permits some visible ASCII characters that Windows forbids in filenames. P11-E final blobs are SHA-addressed, but staging path semantics must explicitly prevent implementation from joining provider file_name into local paths.

Freeze:
- provider/caller file_name is identity/URL metadata only and is never used as a local filesystem component.
- staged download filenames are internally generated safe ordinals/tokens beneath the current attempt directory.
- final blob/package/receipt filesystem components remain hashes/fixed internal names only.

## P11-ISSUE-048K - registry path/page-count boundary for extensionless blobs

P11-E final raw blobs are extensionless SHA-addressed files, while existing SQLiteRegistry.register_document derives PDF page counting from the supplied local path suffix. Creating a temporary/persistent provider-extension alias would expand storage semantics and can leave registry file_path pointing outside the immutable blob layout.

Freeze:
- pass the verified final extensionless content-addressed primary_blob_path directly to existing register_document.
- do not create extension-bearing aliases/hardlinks/copies solely for registry registration.
- require only returned document_sha256 equality; P11-E does not require or reinterpret returned registry file_path/page_count.
- a newly created registry record from an extensionless SEC blob may naturally have page_count=None; an already-existing same-SHA document record may retain its prior accepted file_path/page_count.
- P11-F consumes package manifest/file_name/blob identity, not registry filename suffix, for SEC parsing.

## P11-ISSUE-048L - requested index.json special case conflicts with accepted exhibit gate

Cross-check against design/26 Section 14 and acceptance/41 found that an explicitly requested exhibit must be an exact safe basename listed in the accession index. The temporary design/32 exception that treated requested `index.json` as automatically satisfied by the synthetic FILING_INDEX would weaken that accepted gate because SEC `index.json` is synthetic package inventory, not an `item` row.

Freeze:
- every requested exhibit, including the literal name `index.json`, must match exactly one validated provider `item` row before it can be satisfied as a requested exhibit.
- because a provider `item` named `index.json` is independently invalid to prevent collision with the synthetic FILING_INDEX, a caller request for `index.json` can never be satisfied and maps `P11_PACKAGE_ASSET_MISSING` after index validation.
- the accepted higher-role no-duplicate rule remains for requested filenames that are actual provider items already selected as PRIMARY_DOCUMENT or structured assets.

Also remove the duplicate finalization-order paragraph introduced during amendment editing; the normative sequence must appear exactly once.

## Required remediation

- amend design/32 only plus governance/evidence.
- preserve all ISSUE-046/047 and earlier P11 contracts.
- keep src/tests/integration/runtime-locks unchanged.
- freeze a new exact candidate.
- fresh detached full P11-E design review required.

# STOP

Candidate bc57207c4989c8500fcd8fda8910d783b42e1daa is INELIGIBLE.
P11-E implementation remains CLOSED.
P11 provider production remains CLOSED.
