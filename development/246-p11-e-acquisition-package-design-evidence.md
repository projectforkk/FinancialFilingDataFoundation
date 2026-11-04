# 246 - P11-E SEC Acquisition / Package Design Evidence

Status: **PASS - DESIGN CANDIDATE READY FOR EXACT DETACHED REVIEW / IMPLEMENTATION CLOSED / PROVIDER PRODUCTION CLOSED**

Authorization: development/245-p11-e-acquisition-package-design-freeze-authorization.md
Contract: design/32-p11-e-acquisition-package-contract.md
Prerequisite: development/244-p11-d-final-detached-code-review-result.md = PASS

## Baseline reconciliation

PASS:
- design/26 Source Package and Package Identity requirements retained.
- design/27 parser/taxonomy-cache work remains outside P11-E.
- design/30 immutable source-package references retained.
- design/31 closed SEC User-Agent/TLS/rate/retry/redirect security model retained and shared.
- acceptance/41 package/drift/security/non-expansion requirements retained.
- P2 RawDocumentStore is not modified or redefined.
- existing SQLiteRegistry.register_document is sufficient for primary exact-byte registration with page_count=None for non-PDF; no registry schema/API change is required in P11-E.

## Official SEC live index probe

Read-only GET only, using already configured SEC_USER_AGENT without printing or persisting its value.

Apple CIK 0000320193 current official Submissions selected:
- 10-K: accession 0000320193-26-000026, filing date 2026-11-03.
- 10-Q: accession 0000320193-26-000020, filing date 2026-07-31.
- 8-K: accession 0000320193-26-000024, filing date 2026-11-02.

For all three accession index.json responses:
- HTTP 200.
- top-level exact observed key set: directory.
- directory observed keys: item, name, parent-dir.
- item is an array.
- every observed item is a JSON object.
- every observed item exact key set: last-modified, name, size, type.
- name/size/type/last-modified were JSON strings in all observed rows.
- primaryDocument matched exactly one item.
- XSD and XML rows were present.
- every observed selected-style filename passed the P11-E 0x21..0x7e safe-basename rules.
- Content-Type and Content-Length were each observed once.

Observed index sizes/item counts:
- 10-K index: 10,411 bytes / 108 items.
- 10-Q index: 6,311 bytes / 65 items.
- 8-K index: 1,890 bytes / 17 items.

Observed primary declared sizes:
- 10-K: 1,650,003 bytes.
- 10-Q: 1,018,210 bytes.
- 8-K: 38,214 bytes.

The SEC item size field is a JSON string, not an integer.
Each sampled accession contained exactly three size="" helper rows:
- <accession>-index-headers.html
- <accession>-index.html
- <accession>.txt

Those rows are directory helper/submission-text metadata and are not automatically selected by P11 v1. Decimal selected sizes remain required and actual captured byte size must equal the parsed declared integer.

Observed item type values such as text.gif/compressed.gif/image2.gif demonstrate that directory item.type is SEC UI metadata, not MIME. design/32 therefore excludes it from role/media identity.

## Security/resource-cap freeze

The contract freezes:
- index response 16 MiB.
- per selected filing asset 128 MiB.
- selected aggregate package 512 MiB including index.json.
- raw directory item count 4096.
- selected logical asset count 1024.
- requested exhibits before dedupe 128.
- Accept-Encoding identity only; no decompression.
- selected declared-size preflight plus streaming actual-byte enforcement.

The sampled official filings are far below these bounds while the limits remain explicit DoS/resource gates.

## Deterministic package identity probe

Project-local probe independently reproduced the accepted design/26 canonical identity fixture:

16e76f846fcdccf44216816148ba346ae5c100f3fcdf6fa170a6f954267bae78

Result: CANONICAL_PACKAGE_FIXTURE=PASS.

## Receipt identity probe

Two receipt objects with identical stable receipt identity but different acquired_at/download_ms diagnostics produced the same receipt_id while final receipt bytes differed.

Frozen probe receipt_id:
b9f1279124dd74118b0127fd86b3985b870302a09992bf712c6472efee815e0c

Result: RECEIPT_DIAGNOSTICS_EXCLUDED=PASS.

This proves diagnostics can remain outside receipt identity and package identity while exact stable response provenance remains hashed.

## Windows atomic non-replacing commit probes

Using kernel32 MoveFileExW(source, destination, flags=0) under project-local scratch:

Single file:
- first commit = COMMITTED_NEW.
- second equal-content commit = DESTINATION_EXISTS.
- loser staging remained.
- destination bytes remained unchanged.

Single directory:
- first commit = COMMITTED_NEW.
- second equal-content commit = DESTINATION_EXISTS.
- loser staging directory remained.
- destination manifest bytes remained unchanged.

Two-process races:
- file race = exactly one COMMITTED_NEW + one DESTINATION_EXISTS.
- directory race = exactly one COMMITTED_NEW + one DESTINATION_EXISTS.
- winner content verified.

Results:
- FILE_NO_REPLACE=PASS.
- DIR_NO_REPLACE=PASS.
- TWO_WRITER_FILE=PASS.
- TWO_WRITER_DIR=PASS.

This is compatible with the P11-B primitive and supports both content-addressed blob commit and package-directory commit without replace/merge/delete fallback.

## Containment/reparse probes

A project-local PowerShell junction was created under workspace/scratch and its Windows reparse attribute was detected successfully.

Result: JUNCTION_REPARSE_DETECTION=PASS.

A path outside the canonical workspace/sec/raw subtree failed the containment relation.

Result: RAW_ROOT_CONTAINMENT_NEGATIVE=PASS.

## Scope guard

During P11-E design freeze:
- no src/ production file changed.
- no tests/ implementation file changed.
- no registry schema/API change.
- no RawDocumentStore change.
- no runtime-lock change.
- all mutable probe data remained under D:\Codex\FinancialFilingDataFoundation.

## Verdict

# PASS

design/32 is ready to freeze as an exact P11-E design candidate and enter fresh detached design review.

P11-E implementation remains CLOSED.
P11 provider production remains CLOSED.
