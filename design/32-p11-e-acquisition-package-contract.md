# P11-E SEC Acquisition / Source-Package Contract

Status: **NORMATIVE DESIGN CANDIDATE / IMPLEMENTATION CLOSED / FRESH DETACHED DESIGN REVIEW REQUIRED**

Authorization: development/245-p11-e-acquisition-package-design-freeze-authorization.md
Prerequisite: development/244-p11-d-final-detached-code-review-result.md = PASS / P11-D CLOSED

This contract narrows and completes P11-E requirements already frozen by design/26, design/27, design/30, design/31 and acceptance/41. It must not weaken P11-A through P11-D or P0-P10 accepted behavior.

## 1. Scope

P11-E owns only official SEC accession index.json retrieval, filing-directory asset selection, exact-byte primary/structured/requested-exhibit retrieval, immutable source-package identity and manifest creation, content-addressed SEC raw blob storage, acquisition receipts, source-content-drift detection/preservation, and optional registration of the committed primary bytes through existing SQLiteRegistry.register_document().

P11-E does not own discovery/Submissions semantics, HTML/iXBRL/XBRL parsing, external taxonomy/cache resolution, period confirmation, parsed-v2 export, reuse selection, registry schema/API changes, P2 RawDocumentStore changes, or provider-production authorization. P11-F remains the first parser/runtime/taxonomy-cache phase.

## 2. Public module and API

Additive public module: `financial_filing_data_foundation.sec.package`.

The accepted P11-D root `financial_filing_data_foundation.sec.__all__` remains unchanged at its existing eight symbols. P11-E names are not re-exported from the root `sec` package. `financial_filing_data_foundation.sec.package.__all__` is exactly: `SecPackageError`, `SecAssetRole`, `SecPackageOutcome`, `SecPackageAsset`, `SecSourcePackage`, `SecPackageAcquisitionResult`, `SecPackageStore`, `acquire_sec_package`.

Exact public surface:
- `SecPackageError(RuntimeError)`: `reason_code: str`; constructor `(reason_code: str, message: str)`, passes exact message to RuntimeError so `str(exc) == message`. Except for caller-validation ValueError explicitly frozen by this contract, all operational failures exposed by P11-E public package APIs are SecPackageError. Internal/shared SecHttpError is translated once at the P11-E boundary with the same reason_code and sanitized message; P11-D public exception behavior is unchanged. No raw User-Agent/contact text may appear in SecPackageError.
- `SecAssetRole(StrEnum)` exact values: FILING_INDEX, PRIMARY_DOCUMENT, XBRL_INSTANCE, TAXONOMY_SCHEMA, CALCULATION_LINKBASE, DEFINITION_LINKBASE, LABEL_LINKBASE, PRESENTATION_LINKBASE, REQUESTED_EXHIBIT, OTHER_REQUIRED_DEPENDENCY.
- `SecPackageOutcome(StrEnum)` exact values: ACQUIRED_NEW, REUSED_EXACT, SOURCE_CONTENT_DRIFT.
- `@dataclass(frozen=True, slots=True) SecPackageAsset` fields in exact order/types: `role: SecAssetRole`, `asset_sha256: str`, `file_name: str`, `source_url: str`, `byte_size: int`, `primary: bool`, `dependency_depth: int`, `referring_asset_sha256: str | None`.
- `@dataclass(frozen=True, slots=True) SecSourcePackage` fields in exact order/types: `cik: str`, `accession_number: str`, `base_form: str`, `amended: bool`, `filing_date: str`, `report_date: str | None`, `primary_document: str`, `assets: tuple[SecPackageAsset, ...]`, `source_package_sha256: str`, `document_sha256: str`, `manifest_path: Path`.
- `@dataclass(frozen=True, slots=True) SecPackageAcquisitionResult` fields in exact order/types: `package: SecSourcePackage`, `outcome: SecPackageOutcome`, `reason_code: str | None`, `prior_source_package_sha256s: tuple[str, ...]`, `receipt_id: str`.

`SecSourcePackage` is immutable package state and deliberately contains no receipt field. `SecPackageStore.load_package(source_package_sha256)` reconstructs only manifest/blob package state. Receipt provenance belongs to an acquisition event/result; one immutable package may have multiple valid receipt identities over time without changing `source_package_sha256`.
- SecPackageStore(project_root: Path), with load_package(source_package_sha256: str) -> SecSourcePackage.
- acquire_sec_package(candidate: SecDiscoveryCandidate, project_root: Path, requested_exhibits: tuple[str, ...] = (), registry: SQLiteRegistry | None = None) -> SecPackageAcquisitionResult.

No caller-supplied arbitrary host, URL, HTTP header, raw root, package/blob path, cap, redirect policy, TLS context or rate-gate path is accepted.

## 3. Caller validation before network

Before any P11-E network request **or** creation/mutation of `workspace/sec/raw` or an attempt staging directory, validate all caller arguments:
- candidate must be a SecDiscoveryCandidate. `cik`, `accession_number`, `filing_date`, non-null `report_date`, and `primary_document` are revalidated through the accepted P11-C/P11-D date/identity rules and the normalized values must equal the candidate's stored canonical values; `primary_document` must additionally satisfy the stricter P11-E Section 5 raw-request-target safe-basename grammar before network.
- `candidate.form` and `candidate.base_form` must be exact `str` and `candidate.amended` exact `bool` (bool/int interchange is forbidden). `normalize_sec_form(candidate.form)` must reproduce exactly `candidate.base_form` and `candidate.amended`; `candidate.form` itself must equal the canonical `base_form` plus `"/A"` iff amended, with no alternate spelling.
- `primary_doc_description`, `is_xbrl`, `is_inline_xbrl`, and `submission_source_urls` remain P11-D discovery/provenance metadata; P11-E does not promote them into package identity, role selection or registry source identity.
- project_root is expanduser().resolve(strict=True) and must be a directory.
- requested_exhibits must be a tuple and every entry must be exact `str` before basename validation.
- registry must be either `None` or an instance of the accepted `SQLiteRegistry`; any other value raises `ValueError("registry must be SQLiteRegistry or None")` before network/filesystem mutation.
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

Top level: JSON object with required directory object. Extra top-level keys are ignored for parsed schema/selection decisions, but the exact index response bytes are preserved as FILING_INDEX; therefore any byte change in ignored metadata may still change the FILING_INDEX SHA and source_package_sha256.

directory required fields:
- name: string exactly /Archives/edgar/data/<cik_int>/<accession_no_dashes>.
- parent-dir: string exactly /Archives/edgar/data/<cik_int>.
- item: array length <=4096.
Extra directory keys are ignored as parsed semantic fields but remain part of the exact FILING_INDEX bytes.

Every item is an object requiring string fields name, size, type and last-modified. Extra item keys are ignored for selection/role logic. type is SEC directory-UI metadata, not MIME; last-modified is provider metadata only. Neither is promoted as a separate parsed identity field, but both plus all ignored item metadata remain in the exact FILING_INDEX bytes and can therefore affect package identity through the index asset SHA.

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

Every requested exhibit, including the literal basename `index.json`, must match exactly one validated provider index item; zero match => P11_PACKAGE_ASSET_MISSING before selected asset downloads. Because any provider item named `index.json` is independently invalid under Section 7, a caller request for `index.json` cannot be satisfied by the synthetic FILING_INDEX and therefore resolves to P11_PACKAGE_ASSET_MISSING after index validation. If a requested provider item is already the primary or a structured asset, the request is satisfied by that existing logical row, no duplicate is added, and the higher-precedence role is retained.

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

`SecPackageStore(project_root)` applies the same canonical project-root validation as acquisition. A missing/non-directory root raises exact `ValueError("project_root must be an existing directory")`.

Canonical root only: <project_root>/workspace/sec/raw

Exact layout:
- assets/sha256/<aa>/<sha>
- packages/<source_package_sha256>/manifest.json
- receipts/<rr>/<receipt_id>.json
- .staging/<attempt_token>/

aa/rr are first two lowercase hex characters. Blob filename is exact 64 lowercase hex SHA and extensionless. attempt_token is 32 lowercase hex generated from 128 bits OS CSPRNG. Attempt directories are exclusive-create and diagnostic only.

All paths are internally derived and must resolve inside canonical project root. Symlink/junction/reparse/non-regular final components fail closed. Staging and final are under the same raw root/filesystem. Local paths never enter package identity.

Provider/caller `file_name` is URL/package metadata only and MUST NEVER be joined as a local filesystem path component. Per-resource staged download filenames use only implementation-internal safe ASCII ordinals/tokens under the current `.staging/<attempt_token>` tree; final blob/package/receipt components use only fixed internal names and validated lowercase hashes. This rule is mandatory even when a provider basename contains a character legal in an HTTP path but illegal/reserved in Windows filenames.

## 12. Staging and blob commit

One attempt writes only inside its own staging directory until each object is validated. Every selected asset is fully written, flushed, closed, size-checked and SHA-checked before blob commit.

Blob final commit uses the P11-B-proven Windows same-filesystem atomic non-replacing MoveFileExW(..., flags=0) semantics with COMMITTED_NEW, DESTINATION_EXISTS, COMMIT_ERROR.

COMMITTED_NEW: reload/re-hash final blob and require expected SHA/size; mismatch => P11_PACKAGE_HASH_MISMATCH.

DESTINATION_EXISTS: if the destination or any traversed final-path component is a symlink/junction/reparse point, fail `P11_PATH_OUTSIDE_PROJECT`. Otherwise the destination must be a regular file; non-regular layout or SHA/size mismatch => P11_PACKAGE_HASH_MISMATCH. Exact SHA/size => idempotent reuse and only this attempt's staged duplicate may be removed. Existing blob is never overwritten/deleted/replaced.

COMMIT_ERROR => P11_PACKAGE_INVALID. Later destination existence never converts an unknown commit failure to success.

Equal-content logical assets share one physical blob while remaining separate manifest rows. Orphan immutable content-addressed blobs caused by later failure are safe and may be reused after exact verification; normal runtime does not auto-delete foreign/orphan blobs.

## 13. Package-directory atomic commit and loader verification

After all selected blobs are committed/reused:
1. build staged package directory containing exactly manifest.json.
2. write Section 10 exact bytes, flush/fsync, and load/validate staging against committed blobs.
3. final path = packages/<source_package_sha256>.
4. perform one atomic non-replacing directory commit.

COMMITTED_NEW: reload final through SecPackageStore.load_package() and verify identity/hash/blob semantics.

DESTINATION_EXISTS: never mutate existing final. If the package directory, manifest path, or any traversed final-path component is a symlink/junction/reparse point, fail `P11_PATH_OUTSIDE_PROJECT`. Otherwise final must be a directory containing exactly one regular manifest.json. Full loader verification must pass; final manifest bytes must equal current staged manifest bytes exactly; referenced blobs must verify. Exact match => idempotent reuse. Any non-reparse layout/content/hash difference or corruption => P11_PACKAGE_HASH_MISMATCH.

COMMIT_ERROR => P11_PACKAGE_INVALID and cannot be reclassified from later existence observation.

Normal cleanup removes only the current attempt staging. Foreign-attempt staging is never automatically removed.

## 14. Package loader invariants

`load_package(sha)` first requires exact `^[0-9a-f]{64}$`; invalid input raises exact `ValueError("source_package_sha256 must be 64 lowercase hex")` before filesystem access.

For valid SHA, load_package validates:
- sha is 64 lowercase hex.
- exact final layout/project containment.
- manifest byte size <=16 MiB, UTF-8/no-BOM/LF-only/exactly one final LF.
- exact final manifest key set and exact schema_version `p11-sec-source-package-identity-v1`.
- exact JSON types matching the Section 10 identity contract: strings remain strings, `amended`/`primary` are JSON bool, `byte_size`/`dependency_depth` are JSON integers with bool explicitly rejected, nullable fields are string-or-null as frozen, assets is an array, and all numeric bounds/invariants are checked before object construction.
- after parsing and type validation, reconstruct the complete final manifest object, canonical-serialize it under Section 10 plus exactly one LF, and require those bytes to equal the stored manifest bytes exactly; semantically equal noncanonical whitespace/key-order/number encoding is invalid.
- recomputed canonical identity after removing only source_package_sha256 equals directory/hash value.
- source_package_sha256 field equals directory/hash.
- accepted P11 identity validation.
- exact asset row keys/types/roles and canonical row order.
- exactly one FILING_INDEX and one PRIMARY_DOCUMENT; FILING_INDEX file_name is exactly `index.json` and its primary flag is false.
- primary filename equals top-level primary_document; primary=true iff PRIMARY_DOCUMENT.
- every row depth=0/referring=null.
- every source_url is exact canonical requested accession URL: FILING_INDEX uses the exact index URL; every other row uses the exact asset URL formed from that row's file_name.
- file_name/logical source keys are unique; equal SHA across different logical rows remains allowed.
- every blob is regular non-reparse and exact SHA/size.
- the FILING_INDEX blob is independently parsed under the complete Section 7 index schema with no network; its directory identity must equal the package cik/accession.
- the primary manifest row must correspond to the exact primary_document index item and its byte_size must equal that item's bounded decimal declared size.
- every validated index .xsd/.xml automatic structured item other than the exact primary_document item must appear exactly once in manifest assets with the exact Section 8 derived structured role and declared byte_size; none may be omitted. If primary_document itself has a structured suffix, PRIMARY_DOCUMENT role wins and there is no duplicate structured row.
- every manifest REQUESTED_EXHIBIT row must correspond to exactly one otherwise-nonprimary/nonstructured index item with matching declared byte_size; loader need not know the historical caller request list, but it MUST reject a REQUESTED_EXHIBIT role on index/primary/structured items.
- no manifest non-index row may name an asset absent from the index.
- FILING_INDEX byte_size <=16 MiB; every non-index asset byte_size <=128 MiB; selected logical count <=1024; exact aggregate asset byte_size <=512 MiB; manifest bytes <=16 MiB.

On success `manifest_path` is the resolved final `<project_root>/workspace/sec/raw/packages/<sha>/manifest.json` path; it is storage metadata only and never enters package identity. Manifest/blob/hash/layout mismatch => P11_PACKAGE_HASH_MISMATCH, except project-root escape or any symlink/junction/reparse containment violation => P11_PATH_OUTSIDE_PROJECT.

## 15. Receipt identity, schema and collision behavior

Receipt is provenance/diagnostic evidence, never package identity.

Receipt identity object exact keys:
- schema_version = p11-sec-acquisition-receipt-identity-v1
- source_package_sha256
- responses

Receipt `responses` contains exactly one identity row for each successfully captured logical requested resource used by the package: one row for accession `index.json` plus one row for every selected filing asset. Retry attempts and redirect hops never add extra response identity rows; they contribute only to diagnostics. Each row describes the final successful response for that logical requested resource.

Response identity normalization is exact:
- `requested_url` = exact canonical initial `https://www.sec.gov/Archives/...` URL constructed by Section 5.
- `final_url` = accepted canonical SEC URL identity form after redirects: scheme `https`, lowercase allowed SEC host, default port 443 omitted, exact validated path equal to the requested resource path, empty query and fragment.
- `status` = integer 200.
- index `declared_content_type` = canonical string `application/json`.
- asset `declared_content_type` = null when absent; otherwise the single validated header value after outer ASCII SP/HTAB trim, preserving case and interior visible-ASCII bytes.
- `etag` and `last_modified` = null when absent; otherwise the single header value after outer ASCII SP/HTAB trim, preserving case/interior visible-ASCII bytes.
- any present receipt header value must be non-empty after trim and contain only visible ASCII bytes `0x20..0x7e`; repeated or invalid values fail `P11_HTTP_FAILED` before receipt identity construction.

Each response identity row exact keys: requested_url, final_url, status, declared_content_type (string/null), etag (string/null), last_modified (string/null), asset_sha256, byte_size.
Rows sort by (requested_url, asset_sha256, byte_size, final_url).

receipt_id = SHA256(canonical JSON bytes of the receipt identity object).

Final receipt exact keys:
- schema_version = p11-sec-acquisition-receipt-v1
- receipt_id
- identity
- diagnostics

diagnostics exact keys:
- acquired_at exact UTC form `YYYY-MM-DDTHH:MM:SS.ffffffZ`
- request_count non-negative int = sum of actual emitted HTTP request starts across all logical index/asset fetches in this acquisition attempt
- retry_count non-negative int = sum of scheduled retries across all logical resource fetches
- redirect_count non-negative int = sum of followed redirects across all logical resource fetches
- bytes_downloaded non-negative int = sum of final successful entity bytes used by the package, including index.json, counted once per logical resource rather than per retry/redirect attempt
- download_ms non-negative int
- package_commit_ms non-negative int

Timing/acquired_at never enter receipt_id/package identity. Receipt bytes are canonical JSON plus exactly one LF and MUST be <=16 MiB before receipt commit.

Before receipt commit, build the complete receipt as a regular file under this attempt's `.staging/<attempt_token>/receipt/<receipt_id>.json`, enforce the 16 MiB local cap, flush/fsync, then reload and validate it against the already verified current package.

Before any receipt final-path access, the receipt parent/path components are containment-checked; any symlink/junction/reparse violation => `P11_PATH_OUTSIDE_PROJECT`, while an existing non-reparse nonregular receipt destination => `P11_PACKAGE_INVALID`. Receipt final commit then uses the same P11-B-proven same-filesystem atomic non-replacing file primitive under `receipts/<rr>/<receipt_id>.json`, with exact outcomes COMMITTED_NEW, DESTINATION_EXISTS, COMMIT_ERROR.

COMMITTED_NEW => reload and fully validate the final receipt before continuing.

DESTINATION_EXISTS => load/validate the existing receipt. Existing receipt_id and identity must equal current identity. Diagnostics may differ and are ignored for idempotency; existing receipt bytes, including their original diagnostics/acquired_at, remain authoritative and unchanged. Identity mismatch/corruption under the same ID => P11_PACKAGE_INVALID. The staged duplicate may be removed only after existing-final verification succeeds.

COMMIT_ERROR => P11_PACKAGE_INVALID / BLOCKED. It MUST NOT be converted to idempotent success merely because the final receipt path is later observed to exist.

Receipt validation requires: byte size <=16 MiB; strict UTF-8/no-BOM/LF-only/exactly one final LF; exact final/identity/response/diagnostics key sets and types; exact response canonical order; identity.source_package_sha256 equal to the verified package; exactly one response row per package asset with requested_url/asset_sha256/byte_size equal to that asset row; status exactly 200; URL/header normalization from this section; recomputed receipt_id from canonical identity bytes equal to stored receipt_id; bytes_downloaded equal to the sum of package asset byte_size; request_count >= response count and request_count <= response count + retry_count + redirect_count; acquired_at exact UTC grammar and valid timestamp; and exact stored receipt bytes equal to canonical serialization of the complete validated final receipt object plus one LF.

Receipt validation requires: byte size <=16 MiB; strict UTF-8/no-BOM/LF-only/exactly one final LF; exact final/identity/response/diagnostics key sets and types; exact response canonical order; identity.source_package_sha256 equal to the verified package; exactly one response row per package asset with requested_url/asset_sha256/byte_size equal to that asset row; status exactly 200; URL/header normalization from this section; recomputed receipt_id from canonical identity bytes equal to stored receipt_id; bytes_downloaded equal to the sum of package asset byte_size; request_count >= response count and request_count <= response count + retry_count + redirect_count; acquired_at exact UTC grammar and valid timestamp; and exact stored receipt bytes equal to canonical serialization of the complete validated final receipt object plus one LF.

After commit/reuse, P11-E reloads the committed receipt and returns that exact `receipt_id` in `SecPackageAcquisitionResult`. If registry persistence follows, `SourceMetadata.acquired_at` comes from this committed/reused receipt file, never from diagnostics of a discarded current attempt.

Receipt commit failure never mutates an already committed package. Normal cleanup removes only this attempt's staged receipt; foreign-attempt staging is never removed. Normal cleanup removes only this attempt's staged receipt; foreign-attempt staging is never removed.

## 16. Source-content drift and idempotency

Stable provider identity = (cik, accession_number). Immutable content identity = source_package_sha256.

After the current package and authoritative receipt have both been committed/reused and reloaded successfully, outcome classification performs a two-stage committed-package scan under `packages/`.

At scan start, enumerate the direct child names of `packages/` exactly once and freeze an ASCII-sorted snapshot. Package directories committed after this snapshot are intentionally outside the current attempt's outcome; immutable preservation is strong while cross-process drift notification is snapshot-based/eventually complete rather than globally linearizable. A later acquisition MUST observe later-committed package directories and surface drift when applicable.

Stage 1 is a minimal identity peek only over the frozen snapshot. Consider only snapshot names that are exactly 64 lowercase hex, differ from the current `source_package_sha256`, and currently expose a regular non-reparse `manifest.json` inside the raw root. Read at most the frozen 16 MiB manifest cap plus one sentinel byte; over-cap input cannot establish drift identity and is not a Stage-2 candidate. For in-cap input require strict UTF-8/no-BOM/valid JSON object and inspect only `cik` and `accession_number`. A manifest that cannot establish both as valid normalized strings equal to the current `(cik, accession_number)` is not a drift candidate and does not block an unrelated filing acquisition. Stage 1 never treats unverified package fields as reusable/valid package state.

Stage 2 fully loads every Stage-1 same-accession candidate through `SecPackageStore.load_package()`. A manifest that claims the current valid cik/accession but fails full package/hash/blob/layout validation blocks with the loader's package failure; it MUST NOT be ignored as unrelated corruption.

Classification uses the current package-directory commit outcome plus fully verified same-accession packages, but caller-driven optional exhibit selection is not provider drift.

For each verified package derive an in-memory comparison view only; this view is never persisted and never changes source_package_sha256:
- `provider_core` = the exact package identity top-level fields (`schema_version`, `cik`, `accession_number`, `base_form`, `amended`, `filing_date`, `report_date`, `primary_document`) plus the already canonical-sorted asset identity rows whose role is not REQUESTED_EXHIBIT.
- `requested_exhibit_map` = exact REQUESTED_EXHIBIT asset identity rows keyed by case-sensitive file_name; duplicate file_name is already forbidden by loader invariants.

A verified prior same-accession package is a `drift_evidence_package` iff either:
1. its `provider_core` differs from the current package provider_core; or
2. at least one case-sensitive requested-exhibit file_name exists in both requested_exhibit_map values and the full asset identity row for that shared name differs.

A difference caused only by REQUESTED_EXHIBIT file_names present on one side and absent on the other is caller selection-profile variation and is NOT provider source drift. This rule means adding/removing an optional exhibit alone may create a different immutable source_package_sha256 without producing P11_SOURCE_CONTENT_DRIFT.

Let `drift_hashes` be the ASCII-sorted unique source_package_sha256 values of drift_evidence_package rows:
- if `drift_hashes` is non-empty => SOURCE_CONTENT_DRIFT, reason_code P11_SOURCE_CONTENT_DRIFT, prior_source_package_sha256s = drift_hashes, regardless of whether the current package directory was newly committed or exactly reused.
- else if the current package-directory commit outcome was COMMITTED_NEW => ACQUIRED_NEW, reason_code null, prior_source_package_sha256s = (), including a new package caused only by a different optional-exhibit selection profile.
- else if the current package-directory outcome was exact verified DESTINATION_EXISTS reuse => REUSED_EXACT, reason_code null, prior_source_package_sha256s = ().
- COMMIT_ERROR never reaches outcome classification.
- current new package is committed/preserved before drift is surfaced.
- prior packages/blobs/receipts are never overwritten/deleted.
- drift never rewrites discovery metadata or guesses authority.

A later exact reacquisition continues surfacing SOURCE_CONTENT_DRIFT whenever at least one then-visible prior package remains drift evidence under the provider-core/shared-requested-exhibit rule. Selection-profile-only historical variants do not by themselves force drift.

Missing-current-source drift is a separate no-current-package path required by design/26 Section 25. If current acquisition cannot produce a package because (a) the accession `index.json` returns HTTP 404, (b) an otherwise valid current index has no exact `primary_document` item, or (c) the indexed PRIMARY_DOCUMENT or automatically selected structured asset returns HTTP 404, P11-E captures one ASCII-sorted snapshot of committed package directory names and runs the same safe Stage-1/Stage-2 validation without a current-hash exclusion. If at least one fully verified package with the same `(cik, accession_number)` exists, raise `SecPackageError("P11_SOURCE_CONTENT_DRIFT", "current SEC source is missing relative to a prior verified package")`; no `SecPackageAcquisitionResult` exists because there is no valid current package. Prior immutable packages/receipts/blobs remain unchanged. If no verified prior same-accession package exists, preserve the original 404/asset-missing mapping.

Caller-specific requested exhibit absence is not upgraded to source drift: an exhibit absent from the index remains `P11_PACKAGE_ASSET_MISSING`, and an otherwise optional requested exhibit URL that returns 404 retains the ordinary HTTP failure mapping. 403/access denial, TLS/DNS/timeout, malformed index/schema/framing/content, size mismatch/cap, hash mismatch and local storage failures likewise retain their specific non-drift reason codes. If the missing-source prior scan finds a parseable same-cik/accession package that fails full loader validation, that package failure blocks rather than being converted to drift.

## 17. Registry ordering and failure boundary

P11-E never changes registry schema/API and never calls P2 RawDocumentStore.

If registry is supplied, registration occurs only after blobs, final package loader, and receipt all pass.

Call existing `SQLiteRegistry.register_document(primary_blob_path, source=SourceMetadata(...), expected_identity=None)` using the verified final extensionless content-addressed primary blob path. P11-E MUST NOT create an extension-bearing alias/hardlink/copy solely for registry registration.

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

Returned document SHA must equal package document_sha256. P11-E does not require, rewrite or reinterpret the returned registry `file_path` or `page_count`: a newly created record from an extensionless SEC blob may have page_count=None, while an already-existing same-SHA document record may retain its earlier accepted file_path/page_count. P11-F uses the source-package manifest/file_name/blob identity rather than registry path suffix for SEC parsing. Any registry exception/mismatch maps P11_REGISTRY_PERSISTENCE_FAILED. Immutable package/blob/receipt bytes remain unchanged. Outer retry reloads/verifies package/receipt then retries register_document. No hidden registry retry. registry=None performs no registry mutation.

Exact post-download finalization order is normative:
1. commit/reuse and verify every selected content-addressed blob.
2. build, commit/reuse and reload the final immutable package directory.
3. build, commit/reuse and reload the authoritative acquisition receipt.
4. capture the one drift directory-name snapshot, run Stage 1/Stage 2, and classify SecPackageOutcome/reason/prior hashes.
5. if registry is supplied, register the primary document using the committed receipt acquired_at.
6. return SecPackageAcquisitionResult containing the verified package, classified outcome/reason/prior hashes, and committed receipt_id.

Failure at any step stops later steps. Already committed immutable objects from earlier steps remain unchanged and are safely re-verified by an outer retry; no later step retroactively mutates an earlier blob/package/receipt.

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
- remote response/per-asset/streamed aggregate response-byte cap => P11_RESPONSE_TOO_LARGE.
- locally generated staged/final manifest or receipt exceeding its frozen 16 MiB local JSON cap => P11_PACKAGE_INVALID.
- bad/missing index JSON Content-Type => P11_CONTENT_TYPE_INVALID.
- invalid index schema/item/name/size/duplicate/declared-size mismatch => P11_PACKAGE_INVALID.
- required primary/requested exhibit missing => P11_PACKAGE_ASSET_MISSING.
- manifest/package/blob/hash/idempotent-existing mismatch => P11_PACKAGE_HASH_MISMATCH.
- project-root escape or unsafe reparse/junction/symlink containment violation => P11_PATH_OUTSIDE_PROJECT.
- other local raw-root/directory/staging/file creation, write, flush, fsync, close or atomic-commit I/O failure not already classified above => P11_PACKAGE_INVALID; later destination existence never reclassifies an unknown commit error as success.
- same-accession prior package that is drift evidence under the exact provider-core/shared-requested-exhibit comparison => result reason P11_SOURCE_CONTENT_DRIFT; selection-profile-only package differences are not drift.
- current index/primary/automatic-structured source missing under the exact Section 16 conditions with at least one verified prior same-accession package => raised P11_SOURCE_CONTENT_DRIFT; without such prior package preserve the underlying ordinary failure.
- registry failure => P11_REGISTRY_PERSISTENCE_FAILED.

No silent fallback or guessed asset/period/role.

## 20. Mandatory focused implementation matrix

Before P11-E implementation can close, tests must directly trace these exact 60 numbered cases. Except where a case explicitly requires caller-validation `ValueError`, every operational failure reason in this matrix is asserted on `SecPackageError`; P11-E tests MUST NOT accept leaked `SecHttpError` as equivalent:
1. invalid root/candidate or candidate form/base/amended/date/primary cross-field inconsistency, invalid exhibits, or non-None non-SQLiteRegistry registry fail ValueError before network.
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
37. specific XML linkbase/instance precedence is exact and PRIMARY_DOCUMENT wins if the primary file itself has a structured suffix.
38. generic .xml role.
39. unrelated HTML/text/image not auto-selected.
40. requested exhibit role requires an exact validated provider item; literal requested `index.json` is never satisfied by synthetic FILING_INDEX and maps P11_PACKAGE_ASSET_MISSING.
41. requested primary/structured exhibit already higher-role adds no duplicate.
42. requested exhibit absent blocks pre-download.
43. actual size equals declared.
44. actual aggregate >512 MiB blocks streaming.
45. equal bytes different logical rows share one blob but multiple manifest rows.
46. blob new commit reload/hash/size.
47. concurrent exact blob writers converge without overwrite.
48. existing wrong bytes or nonregular non-reparse blob blocks P11_PACKAGE_HASH_MISMATCH; blob/path symlink/junction/reparse blocks P11_PATH_OUTSIDE_PROJECT.
49. design/26 identity fixture reproduces 16e76f...ae78.
50. manifest exact canonical bytes + one LF; loader rejects semantically equal noncanonical JSON bytes and independently revalidates FILING_INDEX schema, automatic selection completeness, roles, index-declared sizes and source URLs.
51. package new non-replacing directory commit reloads.
52. concurrent exact package writers: one new, loser exact-verifies.
53. existing package difference/corruption blocks without mutation.
54. store/root and loader public validation has exact ValueErrors; loader rejects wrong hash/key/order/primary/count/path/blob/index-selection semantics and any per-asset/aggregate/manifest cap violation, returns resolved final manifest_path, and returns immutable package state without receipt selection.
55. receipt ID excludes diagnostics but includes exactly one stable final response row per logical index/selected-asset resource; requested/final URL and header values follow exact canonical/trim rules, retries/redirects affect diagnostics only, and aggregate counters exactly.
56. receipt staging/non-replacing COMMITTED_NEW/DESTINATION_EXISTS/COMMIT_ERROR paths are exact; loader recomputes receipt_id, requires canonical final bytes and package-response bijection; same identity/different current diagnostics reuses existing authoritative bytes/acquired_at without overwrite.
57. two-stage drift scan skips the already verified current package hash, enforces the 16 MiB peek cap on other hashes, ignores unrelated/unidentifiable corruption, but a parseable same-cik/accession manifest that fails full loader blocks; with no other hashes COMMITTED_NEW => ACQUIRED_NEW and exact verified DESTINATION_EXISTS => REUSED_EXACT, both with empty prior tuple.
58. drift snapshot is captured once after package+receipt verification; later concurrent commits become visible on later acquisition; provider-core change or shared requested-exhibit row change yields drift hashes, optional-exhibit presence/absence alone is selection variation (new package may be ACQUIRED_NEW), and exact missing-current index/primary/automatic-structured conditions raise P11_SOURCE_CONTENT_DRIFT only when a verified prior same-accession package exists.
59. exact finalization order is blobs -> package -> authoritative receipt -> drift snapshot/classification -> optional registry -> result; registry receives the final extensionless primary blob with no extension alias, uses committed receipt acquired_at and expected_identity=None, validates only returned SHA, and any later failure leaves earlier immutable objects unchanged.
60. P11-D root sec.__all__ remains unchanged, sec.package exposes exactly its eight frozen symbols, provider file_name is never a local path component, and there is no P11-F parser/taxonomy-cache behavior or P2 RawDocumentStore mutation/substitution.

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
