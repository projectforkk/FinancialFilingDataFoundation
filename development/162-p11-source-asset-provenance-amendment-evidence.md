# 162 — P11 Logical Source Provenance / Package Immutability Amendment Evidence — ISSUE-025..026

Status: **PASS — DESIGN AMENDMENT READY FOR CANDIDATE FREEZE**

Phase:
P11 — US SEC Provider

Production:
`CLOSED`

## P11-ISSUE-025 — logical source provenance collision

Resolved with deterministic logical-source identity.

`source_asset_id`:

- schema = `p11-source-asset-id-v1`;
- exact payload = file_name + canonical requested source_url + asset_sha256;
- canonical JSON + SHA256;
- known fixture:
  `41183564053cd4f7be5c66d4ed4e7c44d72ad137f9aaf60e7f5bf30c9ef41fa2`.

v2 now requires:

- source_assets row: source_asset_id + asset_sha256;
- document: primary_source_asset_id + primary_asset_sha256;
- segment/section/table/raw-fact/evidence: source_asset_id + source_asset_sha256;
- SOURCE_ASSET locator: source_asset_id + asset_sha256;
- evidence/raw-fact/segment/section/table deterministic ID payloads include source_asset_id.

Therefore two logical source files with identical bytes/SHA remain distinct throughout provenance and deterministic IDs.

Loader rules:

- recompute each source_asset_id;
- source_asset_id resolves exactly one source-assets row;
- referenced source_asset_sha256 matches that row;
- primary_source_asset_id resolves the unique PRIMARY_DOCUMENT row.

## P11-ISSUE-026 — package mutation after P11-E

Resolved:

- P11-E is the only P11 v1 filing-package construction gate;
- every P11 v1 package row comes from the accession directory;
- every row uses dependency_depth=0 / referring_asset_sha256=null;
- P11-F cannot append external taxonomy/runtime-cache assets;
- parser/runtime work cannot rewrite source_package_sha256;
- external taxonomy/cache belongs to the separately frozen parser/runtime contract;
- future package inclusion of external dependencies requires a new versioned package identity design before package construction.

## Prior amendment regression

Still intact:

- ISSUE-010 aggregate SEC fair-access contract;
- ISSUE-011 package identity/hash/receipt split;
- ISSUE-012 project-relative path semantics;
- ISSUE-013 canonical source locators;
- ISSUE-014 deterministic IDs;
- ISSUE-015 raw/transformed iXBRL value boundary;
- ISSUE-016 CIK/accession/primaryDocument grammar;
- ISSUE-017 deterministic index.json package assembly;
- ISSUE-018/020 stage ordering;
- ISSUE-019 Q2 iff US;
- ISSUE-021 supplemental nullability/registry boundary;
- ISSUE-022 logical asset vs blob/role precedence;
- ISSUE-023 discovery vs final report-date separation;
- ISSUE-024 nullable US ticker / CIK-only identity.

## Scope

Design/governance only.

No changes under:

- src/
- tests/
- integration/
- runtime-locks/

## Verdict

# PASS — READY FOR CANDIDATE FREEZE AND FRESH DETACHED DESIGN REVIEW

No production authorization is implied.
