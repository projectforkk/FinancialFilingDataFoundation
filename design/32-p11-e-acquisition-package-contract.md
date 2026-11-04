# P11-E SEC Acquisition / Source-Package Contract

Status: **NORMATIVE DESIGN CANDIDATE / IMPLEMENTATION CLOSED / FRESH DETACHED DESIGN REVIEW REQUIRED**

Authorization: development/245-p11-e-acquisition-package-design-freeze-authorization.md
Prerequisite: development/244-p11-d-final-detached-code-review-result.md = PASS / P11-D CLOSED

This contract narrows and completes P11-E requirements already frozen by design/26, design/27, design/30, design/31 and acceptance/41. It must not weaken P11-A through P11-D or P0-P10 accepted behavior.

## 1. Scope

P11-E owns only official SEC accession index.json retrieval, filing-directory asset selection, exact-byte primary/structured/requested-exhibit retrieval, immutable source-package identity and manifest creation, content-addressed SEC raw blob storage, acquisition receipts, source-content-drift detection/preservation, and optional registration of the committed primary bytes through existing SQLiteRegistry.register_document().

P11-E does not own discovery/Submissions semantics, HTML/iXBRL/XBRL parsing, external taxonomy/cache resolution, period confirmation, parsed-v2 export, reuse selection, registry schema/API changes, P2 RawDocumentStore changes, or provider-production authorization. P11-F remains the first parser/runtime/taxonomy-cache phase.

## 2. Public module and API

Additive public module: financial_filing_data_foundation.sec.package

Exact public surface:
- SecPackageError(RuntimeError), storing exact reason_code.
- SecAssetRole values: FILING_INDEX, PRIMARY_DOCUMENT, XBRL_INSTANCE, TAXONOMY_SCHEMA, CALCULATION_LINKBASE, DEFINITION_LINKBASE, LABEL_LINKBASE, PRESENTATION_LINKBASE, REQUESTED_EXHIBIT, OTHER_REQUIRED_DEPENDENCY.
- SecPackageOutcome values: ACQUIRED_NEW, REUSED_EXACT, SOURCE_CONTENT_DRIFT.
- frozen/slots SecPackageAsset fields in order: role, asset_sha256, file_name, source_url, byte_size, primary, dependency_depth, referring_asset_sha256.
- frozen/slots SecSourcePackage fields in order: cik, accession_number, base_form, amended, filing_date, report_date, primary_document, assets, source_package_sha256, document_sha256, manifest_path.
- frozen/slots SecPackageAcquisitionResult fields in order: package, outcome, reason_code, prior_source_package_sha256s, receipt_id.

`SecSourcePackage` is immutable package state and deliberately contains no receipt field. `SecPackageStore.load_package(source_package_sha256)` reconstructs only manifest/blob package state. Receipt provenance belongs to an acquisition event/result; one immutable package may have multiple valid receipt identities over time without changing `source_package_sha256`.
- SecPackageStore(project_root: Path), with load_package(source_package_sha256: str) -> SecSourcePackage.
- acquire_sec_package(candidate: SecDiscoveryCandidate, project_root: Path, requested_exhibits: tuple[str, ...] = (), registry: SQLiteRegistry | None = None) -> SecPackageAcquisitionResult.

No caller-supplied arbitrary host, URL, HTTP header, raw root, package/blob path, cap, redirect policy, TLS context or rate-gate path is accepted.

## 3. Caller validation before network

Before any P11-E request:
- candidate must be a SecDiscoveryCandidate and all identity fields are revalidated through accepted P11-C/P11-D normalization.
- project_root is expanduser().resolve(strict=True) and must be a directory.
- requested_exhibits must be a tuple.
- registry must be either `None` or an instance of the accepted `SQLiteRegistry`; any other value raises `ValueError("registry must be SQLiteRegistry or None")` before network.
- maximum requested exhibit entries before dedupe = 128.
- every requested exhibit must satisfy Section 5 safe-basename grammar.
- exhibit names are exact-case deduped and ASCII-sorted.
- invalid caller arguments raise ValueError before network.

## 4. Shared SEC HTTP/rate boundary

P11-E Archive requests use the same accepted User-Agent validation, verified TLS/direct-no-proxy policy, retry/deadline rules, redirect limits, canonical redirect-loop identity, RESERVED/READY Windows byte-range rate gate and workspace/sec/rate state as P11-D.

P11-D and P11-E therefore share one cross-process aggregate maximum of 8 actual SEC starts/second and minimum 125 ms actual-start spacing. Per logical resource fetch: maximum 3 retries, maximum 3 followed redirects, and no valid path emits an eighth start. Unsafe shared coordination maps P11_RATE_LIMIT_SCOPE_UNSAFE before request bytes.

Archive initial host is exactly lowercase www.sec.gov over HTTPS, port absent or 443, no userinfo/query/fragment. Redirects may move only within the accepted SEC host allowlist and must retain the exact normalized Archive path and empty query. Package identity always uses the canonical initial www.sec.gov requested URL.

## 5. Archive path and safe-basename grammar

For normalized CIK/accession:
- cik_int = ASCII decimal CIK with leading zeroes removed.
- accession_no_dashes = exactly 18 ASCII digits.
- archive directory = /Archives/edgar/data/<cik_int>/<accession_no_dashes>.
- index URL = https://www.sec.gov/Archives/edgar/data/<cik_int>/<accession_no_dashes>/index.json.
- asset URL = https://www.sec.gov/Archives/edgar/data/<cik_int>/<accession_no_dashes>/<file_name>.

Every index-derived or caller-requested asset basename must be non-empty ASCII, contain only bytes 0x21..0x7e, not equal . or .., contain none of slash, backslash, ?, # or %, and be used as exactly one raw HTTP path segment after validation. P11-E never percent-encodes/decodes or Unicode-normalizes provider filenames.

Invalid provider item name => P11_PACKAGE_INVALID before that asset is fetched. Invalid caller exhibit name => ValueError before network.

## 6. HTTP content classes and hard caps

P11-E uses two internal content classes and does not widen the closed P11-D SecContentClass enum:
- ACCESSION_INDEX_JSON: 16 MiB = 16,777,216 bytes.
- ACCESSION_ASSET: 128 MiB = 134,217,728 bytes per response.

Package limits:
- raw directory.item count <= 4096.
- selected logical asset count including FILING_INDEX <= 1024.
- exact selected package bytes including index.json <= 512 MiB = 536,870,912.
- final/staged `manifest.json` bytes <=16 MiB = 16,777,216.
- acquisition receipt JSON bytes <=16 MiB = 16,777,216.
- requested exhibit entries before dedupe <= 128.

Declared selected sizes are preflighted before asset downloads. Declared sum plus exact index bytes >512 MiB blocks before selected asset downloads. Actual streamed aggregate is counted again and >512 MiB blocks immediately.

P11-E sends Accept-Encoding: identity. Content-Encoding may be absent or exactly one identity. Transparent decompression is forbidden.

Transfer-Encoding/Content-Length rules are exactly P11-D: repeated TE/CL fail; TE if present is exactly chunked; TE+CL forbidden; non-chunked CL is decimal and must equal EOF entity bytes; chunked counts dechunked entity bytes; streaming caps always apply.

ACCESSION_INDEX_JSON requires exactly one normalized application/json Content-Type, strict UTF-8, no BOM and valid JSON.

For ACCESSION_ASSET:
- Content-Type may be absent or exactly one non-empty visible-ASCII field; repeated fails P11_HTTP_FAILED.
- Content-Type is receipt metadata only and never determines role or package identity.
- ETag and Last-Modified may each be absent or exactly one field; repeated fails P11_HTTP_FAILED.
- exact bytes are preserved without text/newline/encoding transformation.

## 7. Accession index.json provider schema

Live SEC probes on domestic 10-K, 10-Q and 8-K freeze required-field validation while allowing ignored forward-compatible extra metadata.

Top level: JSON object with required directory object. Extra top-level keys ignored.

directory required fields:
- name: string exactly /Archives/edgar/data/<cik_int>/<accession_no_dashes>.
- parent-dir: string exactly /Archives/edgar/data/<cik_int>.
- item: array length <=4096.
Extra directory keys ignored.

Every item is an object requiring string fields name, size, type and last-modified. Extra item keys ignored. type is SEC directory-UI metadata, not MIME. last-modified is provider metadata only. Neither enters package identity.

size is either empty string or an ASCII decimal string matching `^[0-9]{1,20}$`. No integer conversion occurs before this lexical bound passes. The bounded decimal is parsed as a non-negative integer; unselected items are not rejected solely because that integer exceeds the selected per-asset cap. A selected package asset must have decimal size <=134,217,728. Selected item with size empty => P11_PACKAGE_INVALID before asset download. Unselected helper rows with empty size are permitted. Any non-empty size outside the 1..20-digit grammar => P11_PACKAGE_INVALID. Provider-declared size never substitutes for captured actual bytes.

Every item name is validated before selection. Duplicate exact item names make the index P11_PACKAGE_INVALID. First/last wins is forbidden. An item named index.json is P11_PACKAGE_INVALID because it collides with the synthetic required FILING_INDEX logical asset.

## 8. Selection and role precedence

P11-E always selects synthetic FILING_INDEX for exact fetched index.json bytes:
- file_name = index.json.
- source_url = exact canonical index URL.
- primary=false, dependency_depth=0, referring_asset_sha256=null.

candidate.primary_document must match exactly one case-sensitive item; zero match => P11_PACKAGE_ASSET_MISSING. The selected primary item must have decimal size and role PRIMARY_DOCUMENT.

Automatic structured selection includes every validated item whose lowercase name ends .xsd or .xml. Exact structured classification:
1. *_cal.xml => CALCULATION_LINKBASE
2. *_def.xml => DEFINITION_LINKBASE
3. *_lab.xml => LABEL_LINKBASE
4. *_pre.xml => PRESENTATION_LINKBASE
5. *_htm.xml => XBRL_INSTANCE
6. other .xml => OTHER_REQUIRED_DEPENDENCY
7. .xsd => TAXONOMY_SCHEMA

Final role precedence remains:
1. synthetic index.json => FILING_INDEX
2. exact primary filename => PRIMARY_DOCUMENT
3. structured suffix role
4. explicit requested exhibit => REQUESTED_EXHIBIT
5. otherwise excluded

An exhibit already satisfied by 1-3 adds no duplicate and retains the higher role. Every requested exhibit must match exactly one validated index item; zero match => P11_PACKAGE_ASSET_MISSING before selected asset downloads.

No unrelated HTML/text/image exhibits are auto-selected. No recursive link following. No external taxonomy resource is added by P11-E.

Selected filing assets download in exact file_name ASCII order. Package identity later uses the design/26 identity-row sort.

## 9. Declared-size and exact-byte validation

Before selected filing downloads:
- each selected index item has decimal size <=128 MiB.
- selected logical count including index <=1024.
- declared selected sum + exact index response size <=512 MiB.

For every fetched filing asset:
- asset_sha256 = SHA256(exact entity bytes).
- byte_size = exact entity length.
- actual size must equal index-declared numeric size exactly; mismatch => P11_PACKAGE_INVALID.
- per-response/aggregate cap violation => P11_RESPONSE_TOO_LARGE.
- partial/truncated data never enters a valid package.

## 10. Canonical package identity and exact manifest bytes

Identity payload is exactly design/26 Section 15 and uses design/26 Section 28 canonical JSON: UTF-8, ensure_ascii=False, sort_keys=True, separators comma/colon without spaces, allow_nan=False, no trailing LF in the hashed identity bytes.

Exact identity top-level keys: schema_version, cik, accession_number, base_form, amended, filing_date, report_date, primary_document, assets.
schema_version = p11-sec-source-package-identity-v1.

Every asset identity row exact keys: role, asset_sha256, file_name, source_url, byte_size, primary, dependency_depth, referring_asset_sha256.
dependency_depth is always 0 and referring_asset_sha256 always null in P11-E.

Asset rows sort exactly by (role, file_name, source_url, asset_sha256, byte_size, primary, dependency_depth, referring_asset_sha256-or-empty).

source_package_sha256 = SHA256(exact canonical identity payload bytes). It is not included in its own identity payload.

Final manifest.json object is exactly the identity payload plus source_package_sha256. Final manifest bytes are canonical JSON of that final object plus exactly one LF byte, UTF-8/no BOM/no CRLF/no indentation.

The unique PRIMARY_DOCUMENT asset SHA is document_sha256. No top-level document_sha256 is added to manifest.json.

The existing design/26 canonical identity fixture must continue to hash exactly 16e76f846fcdccf44216816148ba346ae5c100f3fcdf6fa170a6f954267bae78.

## 11. Dedicated source-package store layout

P11-E does not modify or reuse P2 PDF RawDocumentStore semantics.

Canonical root only: <project_root>/workspace/sec/raw

Exact layout:
- assets/sha256/<aa>/<sha>
- packages/<source_package_sha256>/manifest.json
- receipts/<rr>/<receipt_id>.json
- .staging/<attempt_token>/

aa/rr are first two lowercase hex characters. Blob filename is exact 64 lowercase hex SHA and extensionless. attempt_token is 32 lowercase hex generated from 128 bits OS CSPRNG. Attempt directories are exclusive-create and diagnostic only.

All paths are internally derived and must resolve inside canonical project root. Symlink/junction/reparse/non-regular final components fail closed. Staging and final are under the same raw root/filesystem. Local paths never enter package identity.

## 12. Staging and blob commit

One attempt writes only inside its own staging directory until each object is validated. Every selected asset is fully written, flushed, closed, size-checked and SHA-checked before blob commit.

Blob final commit uses the P11-B-proven Windows same-filesystem atomic non-replacing MoveFileExW(..., flags=0) semantics with COMMITTED_NEW, DESTINATION_EXISTS, COMMIT_ERROR.

COMMITTED_NEW: reload/re-hash final blob and require expected SHA/size; mismatch => P11_PACKAGE_HASH_MISMATCH.

DESTINATION_EXISTS: existing destination must be regular non-reparse; re-hash/re-size it. Exact SHA/size => idempotent reuse and only this attempt's staged duplicate may be removed. Mismatch/non-regular => P11_PACKAGE_HASH_MISMATCH. Existing blob is never overwritten/deleted/replaced.

COMMIT_ERROR => P11_PACKAGE_INVALID. Later destination existence never converts an unknown commit failure to success.

Equal-content logical assets share one physical blob while remaining separate manifest rows. Orphan immutable content-addressed blobs caused by later failure are safe and may be reused after exact verification; normal runtime does not auto-delete foreign/orphan blobs.

## 13. Package-directory atomic commit and loader verification

After all selected blobs are committed/reused:
1. build staged package directory containing exactly manifest.json.
2. write Section 10 exact bytes, flush/fsync, and load/validate staging against committed blobs.
3. final path = packages/<source_package_sha256>.
4. perform one atomic non-replacing directory commit.

COMMITTED_NEW: reload final through SecPackageStore.load_package() and verify identity/hash/blob semantics.

DESTINATION_EXISTS: never mutate existing final. It must be a non-reparse directory containing exactly one regular manifest.json. Full loader verification must pass; final manifest bytes must equal current staged manifest bytes exactly; referenced blobs must verify. Exact match => idempotent reuse. Any difference/corruption => P11_PACKAGE_HASH_MISMATCH.

COMMIT_ERROR => P11_PACKAGE_INVALID and cannot be reclassified from later existence observation.

Normal cleanup removes only the current attempt staging. Foreign-attempt staging is never automatically removed.

## 14. Package loader invariants

load_package(sha) validates:
- sha is 64 lowercase hex.
- exact final layout/project containment.
- manifest byte size <=16 MiB, UTF-8/no-BOM/LF-only/exactly one final LF.
- exact final manifest key set.
- recomputed canonical identity after removing only source_package_sha256 equals directory/hash value.
- source_package_sha256 field equals directory/hash.
- accepted P11 identity validation.
- exact asset row keys/types/roles and canonical row order.
- exactly one FILING_INDEX and one PRIMARY_DOCUMENT.
- primary filename equals top-level primary_document; primary=true iff PRIMARY_DOCUMENT.
- every row depth=0/referring=null.
- every source_url is exact canonical requested accession URL.
- every blob is regular non-reparse and exact SHA/size.
- count and aggregate caps still hold.

Manifest/blob/hash/layout mismatch => P11_PACKAGE_HASH_MISMATCH, except explicit root escape => P11_PATH_OUTSIDE_PROJECT.

## 15. Receipt identity, schema and collision behavior

Receipt is provenance/diagnostic evidence, never package identity.

Receipt identity object exact keys:
- schema_version = p11-sec-acquisition-receipt-identity-v1
- source_package_sha256
- responses

Receipt `responses` contains exactly one identity row for each successfully captured logical requested resource used by the package: one row for accession `index.json` plus one row for every selected filing asset. Retry attempts and redirect hops never add extra response identity rows; they contribute only to diagnostics. Each row describes the final successful response for that logical requested resource.

Each response identity row exact keys: requested_url, final_url, status, declared_content_type (string/null), etag (string/null), last_modified (string/null), asset_sha256, byte_size.
Rows sort by (requested_url, asset_sha256, byte_size, final_url).

receipt_id = SHA256(canonical JSON bytes of the receipt identity object).

Final receipt exact keys:
- schema_version = p11-sec-acquisition-receipt-v1
- receipt_id
- identity
- diagnostics

diagnostics exact keys:
- acquired_at UTC ISO-8601 string
- request_count non-negative int = sum of actual emitted HTTP request starts across all logical index/asset fetches in this acquisition attempt
- retry_count non-negative int = sum of scheduled retries across all logical resource fetches
- redirect_count non-negative int = sum of followed redirects across all logical resource fetches
- bytes_downloaded non-negative int = sum of final successful entity bytes used by the package, including index.json, counted once per logical resource rather than per retry/redirect attempt
- download_ms non-negative int
- package_commit_ms non-negative int

Timing/acquired_at never enter receipt_id/package identity. Receipt bytes are canonical JSON plus exactly one LF and MUST be <=16 MiB before receipt commit.

Receipt commit is atomic non-replacing under receipts/<rr>/<receipt_id>.json.

If destination exists, load/validate it. Existing receipt_id and identity must equal current identity. Diagnostics may differ and are ignored for idempotency; existing receipt bytes, including their original diagnostics/acquired_at, remain authoritative and unchanged. Identity mismatch/corruption under the same ID => P11_PACKAGE_INVALID.

After commit/reuse, P11-E reloads the committed receipt and returns that exact `receipt_id` in `SecPackageAcquisitionResult`. If registry persistence follows, `SourceMetadata.acquired_at` comes from this committed/reused receipt file, never from diagnostics of a discarded current attempt.

Receipt commit failure never mutates an already committed package.

## 16. Source-content drift and idempotency

Stable provider identity = (cik, accession_number). Immutable content identity = source_package_sha256.

Before outcome classification P11-E performs a two-stage committed-package scan under `packages/`.

Stage 1 is a minimal identity peek only. Consider only child directories whose name is exactly 64 lowercase hex and whose `manifest.json` is a regular non-reparse file inside the raw root. Read at most the frozen 16 MiB manifest cap plus one sentinel byte; over-cap input cannot establish drift identity and is not fully loaded unless it is already the exact current package path verified by Section 13. For in-cap input require strict UTF-8/no-BOM/valid JSON object and inspect only `cik` and `accession_number`. A manifest that cannot establish both as valid normalized strings equal to the current `(cik, accession_number)` is not a drift candidate and does not block an unrelated filing acquisition. Stage 1 never treats unverified package fields as reusable/valid package state.

Stage 2 fully loads every Stage-1 same-accession candidate through `SecPackageStore.load_package()`. A manifest that claims the current valid cik/accession but fails full package/hash/blob/layout validation blocks with the loader's package failure; it MUST NOT be ignored as unrelated corruption.

Classification uses the current package-directory commit outcome plus fully verified same-accession packages. Let `other_hashes` be the ASCII-sorted unique verified same-accession package hashes excluding the current `source_package_sha256`:
- if `other_hashes` is non-empty => SOURCE_CONTENT_DRIFT, reason_code P11_SOURCE_CONTENT_DRIFT, prior_source_package_sha256s = other_hashes, regardless of whether the current package directory was newly committed or exactly reused.
- else if the current package-directory commit outcome was COMMITTED_NEW => ACQUIRED_NEW, reason_code null, prior_source_package_sha256s = ().
- else if the current package-directory outcome was exact verified DESTINATION_EXISTS reuse => REUSED_EXACT, reason_code null, prior_source_package_sha256s = ().
- COMMIT_ERROR never reaches outcome classification.
- current new package is committed/preserved before drift is surfaced.
- prior packages/blobs/receipts are never overwritten/deleted.
- drift never rewrites discovery metadata or guesses authority.

A later exact reacquisition with known historical different versions continues surfacing SOURCE_CONTENT_DRIFT.

## 17. Registry ordering and failure boundary

P11-E never changes registry schema/API and never calls P2 RawDocumentStore.

If registry is supplied, registration occurs only after blobs, final package loader, and receipt all pass.

Call existing SQLiteRegistry.register_document(primary_blob_path, source=SourceMetadata(...), expected_identity=None).

Exact SourceMetadata:
- provider = sec-edgar
- source_id = candidate.accession_number
- source_url = canonical requested primary Archive URL
- source_title = SEC <candidate.form> <candidate.cik> <candidate.accession_number>
- filing_date = candidate.filing_date
- report_date = candidate.report_date
- provider_company_id = candidate.cik
- acquired_at = `acquired_at` read from the committed/reused receipt file after receipt verification (never a discarded current-attempt timestamp)

expected_identity=None is mandatory because periodic binding is not yet filing-native confirmed and supplemental filings must never receive a synthetic slot.

Returned document SHA must equal package document_sha256. Any registry exception/mismatch maps P11_REGISTRY_PERSISTENCE_FAILED. Immutable package/blob/receipt bytes remain unchanged. Outer retry reloads/verifies package/receipt then retries register_document. No hidden registry retry. registry=None performs no registry mutation.

## 18. Security and containment

Mandatory:
- no remote AI API, arbitrary shell input, arbitrary local path, arbitrary host/URL/header/TLS context.
- no HTML/script execution.
- no XML parsing/entity resolution in P11-E.
- no archive extraction/decompression.
- no automatic external taxonomy download.
- no percent-decoded path construction.
- all staging/final paths remain under resolved project root.
- reparse/symlink/junction final escapes fail closed.
- exact item/asset/package caps enforced before and during download.
- P11-D and P11-E share the same rate coordination.

## 19. Failure mapping

- invalid caller argument => ValueError before network.
- bad Archive scheme/host/path/port => P11_SOURCE_HOST_NOT_ALLOWED.
- hostile/loop/excess redirect => P11_REDIRECT_NOT_ALLOWED.
- missing/invalid User-Agent => P11_USER_AGENT_REQUIRED.
- rate coordination unavailable => P11_RATE_LIMIT_SCOPE_UNSAFE.
- exhausted 429 => P11_RATE_LIMITED.
- other transport/status/framing/header/UTF-8/JSON failure => P11_HTTP_FAILED.
- response/per-asset/aggregate size cap => P11_RESPONSE_TOO_LARGE.
- bad/missing index JSON Content-Type => P11_CONTENT_TYPE_INVALID.
- invalid index schema/item/name/size/duplicate/declared-size mismatch => P11_PACKAGE_INVALID.
- required primary/requested exhibit missing => P11_PACKAGE_ASSET_MISSING.
- manifest/package/blob/hash/idempotent-existing mismatch => P11_PACKAGE_HASH_MISMATCH.
- project-root escape => P11_PATH_OUTSIDE_PROJECT.
- same-accession different immutable package => result reason P11_SOURCE_CONTENT_DRIFT.
- registry failure => P11_REGISTRY_PERSISTENCE_FAILED.

No silent fallback or guessed asset/period/role.

## 20. Mandatory focused implementation matrix

Before P11-E implementation can close, tests must directly trace these exact 60 numbered cases:
1. invalid root/candidate/exhibits or non-None non-SQLiteRegistry registry fail ValueError before network.
2. requested exhibit tuple >128 fails before network.
3. invalid exhibit basename SP/control/non-ASCII/%/slash/query/fragment fails before network.
4. P11-E uses same rate directory as P11-D.
5. missing/invalid User-Agent blocks before Archive network.
6. initial Archive host/scheme/port/query/fragment violations block.
7. exact cik-int/accession/index URL construction.
8. exact raw asset basename URL and no percent encoding.
9. canonical-equivalent redirect loop rejected before extra start.
10. redirect non-SEC host or changed Archive path rejected.
11. retry/redirect/start counters preserve P11-D contract.
12. index 16 MiB cap by CL/streaming.
13. asset 128 MiB cap by CL/streaming.
14. TE/CL ambiguity/unsupported coding rejected.
15. non-identity/repeated Content-Encoding rejected; no decompression.
16. index Content-Type exact application/json.
17. asset Content-Type absent/single accepted; repeated rejected and never role identity.
18. repeated ETag/Last-Modified rejected.
19. index strict UTF-8/no-BOM/valid JSON.
20. top-level directory required; extras ignored.
21. directory.name exact accession path.
22. parent-dir exact filer path.
23. item array and <=4096.
24. item requires string name/size/type/last-modified; size is empty or 1..20 ASCII digits before integer conversion; extras ignored.
25. every item name safe grammar before selection.
26. duplicate item name fails.
27. item named index.json fails.
28. unselected helper size empty accepted.
29. selected size empty fails before asset download.
30. bounded decimal size leading zero accepted/numeric comparison; >20 decimal digits fails without integer conversion while an unselected <=20-digit value may exceed 128 MiB.
31. declared selected asset >128 MiB blocks pre-download.
32. selected logical count >1024 blocks.
33. declared selected total + index >512 MiB blocks pre-download.
34. synthetic FILING_INDEX exact bytes/hash/source_url.
35. primary exact match and missing primary reason.
36. .xsd role.
37. specific XML linkbase/instance precedence.
38. generic .xml role.
39. unrelated HTML/text/image not auto-selected.
40. requested exhibit role.
41. requested exhibit already higher-role adds no duplicate.
42. requested exhibit absent blocks pre-download.
43. actual size equals declared.
44. actual aggregate >512 MiB blocks streaming.
45. equal bytes different logical rows share one blob but multiple manifest rows.
46. blob new commit reload/hash/size.
47. concurrent exact blob writers converge without overwrite.
48. existing wrong/nonregular/reparse blob blocks hash mismatch.
49. design/26 identity fixture reproduces 16e76f...ae78.
50. manifest exact canonical bytes + one LF.
51. package new non-replacing directory commit reloads.
52. concurrent exact package writers: one new, loser exact-verifies.
53. existing package difference/corruption blocks without mutation.
54. loader rejects wrong hash/key/order/primary/count/path/blob semantics and returns immutable package state without any receipt selection.
55. receipt ID excludes diagnostics but includes exactly one stable final response row per logical index/selected-asset resource; retries/redirects affect diagnostics only and aggregate counters exactly.
56. same receipt identity/different current diagnostics reuses existing authoritative receipt bytes/acquired_at without overwrite; identity collision blocks and acquisition result carries the committed receipt_id.
57. two-stage drift scan enforces the 16 MiB peek cap, ignores unrelated/unidentifiable corruption, but a parseable same-cik/accession manifest that fails full loader blocks; with no other hashes COMMITTED_NEW => ACQUIRED_NEW and exact verified DESTINATION_EXISTS => REUSED_EXACT, both with empty prior tuple.
58. same accession different verified package is preserved and surfaced as drift with ASCII-sorted unique other hashes, including later exact reacquisition when historical drift exists.
59. registry occurs only after package+receipt verification, exact SourceMetadata uses committed receipt acquired_at and expected_identity=None; failure leaves package immutable.
60. no P11-F parser/taxonomy-cache behavior and no P2 RawDocumentStore mutation/substitution.

## 21. Design probes/evidence required before implementation authorization

Evidence must include:
- official live SEC index schema observations for 10-K, 10-Q and 8-K.
- field-type and empty-size observations without persisting User-Agent.
- canonical design/26 package hash reproduction.
- Windows file and directory non-replacing commit probe under project-local scratch.
- two-writer blob/package convergence semantic probe.
- receipt identity diagnostics-exclusion probe.
- project-root containment/reparse negative probe.
- no src/tests production changes during design freeze.

## 22. Implementation authorization gate

P11-E production implementation remains CLOSED until:
1. exact design candidate committed/pushed.
2. design evidence committed/pushed.
3. fresh detached exact-candidate design review PASS.
4. governance current-state reconciled.
5. separate P11-E implementation authorization freezes exact source/test scope.

Provider production remains CLOSED throughout P11-E design and implementation review.
