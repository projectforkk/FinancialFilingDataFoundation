# 160 — P11 Supplemental-Final Design Review Stop — Logical Asset Identity

Status: **FAIL / STOP — P11-ISSUE-022 / PRODUCTION CLOSED**

Phase:
P11 — US SEC Provider

Reviewed exact candidate:
`5e1a1b7b39544af6c3ba464fc576174b480bd3ad`

Fresh detached review:
`D:\\Codex\\FinancialFilingDataFoundation\\worktrees\\review\\p11-design-5e1a1b7`

Automated contract matrix:
`PASS`

## Finding

The package design currently states:

`The same asset SHA may be referenced once only in the manifest`

and separately defines one source-assets row per captured source asset.

This conflates:

- physical content blob identity (SHA256);
- logical accession-directory asset identity (filename/source URL/role).

Two distinct SEC directory entries can legitimately contain identical bytes and therefore the same SHA256. Collapsing them by SHA changes filing-package truth and package identity.

The design also does not freeze role precedence when one logical asset is simultaneously:

- the primaryDocument;
- an automatically captured .xml/.xsd asset;
- an explicitly requested exhibit.

Finally, P11-E does not freeze `dependency_depth` / `referring_asset_sha256` for direct accession-directory assets even though those fields participate in package identity.

## P11-ISSUE-022 — logical asset vs content blob / role precedence

Required correction:

1. Raw blob store deduplicates by `asset_sha256`.

2. Package manifest/source_assets represent logical source assets, not unique content hashes.

3. Multiple logical rows MAY share the same `asset_sha256` when filename/source_url differ.

4. Exact duplicate logical asset key is forbidden:
   `(file_name, canonical requested source_url)`
   must be unique in one package.

5. Role precedence for one logical asset:
   - FILING_INDEX for index.json;
   - PRIMARY_DOCUMENT if exact filename equals validated primaryDocument;
   - otherwise structured suffix classification;
   - otherwise REQUESTED_EXHIBIT only when explicitly requested;
   - unrelated assets excluded.

6. An explicit exhibit request for an asset already included as PRIMARY_DOCUMENT or structured asset is satisfied by the existing logical row; role does not change and no duplicate row is added.

7. All P11-E accession-directory direct assets use:
   - dependency_depth = 0;
   - referring_asset_sha256 = null.

8. Future externally resolved dependencies may use depth >0 only after the P11-F parser-contract freeze defines that behavior.

Acceptance must include:
- two logical files with identical bytes/SHA survive as two manifest/source-assets rows;
- blob store stores bytes once;
- package hash includes both logical rows;
- role precedence tests;
- duplicate logical key rejected;
- direct package assets depth=0/referrer=null.

## Scope

No production/test/runtime changes.

ISSUE-010..021 remediation remains valid.

## Verdict

# FAIL / STOP

Candidate `5e1a1b7...` is INELIGIBLE.

P11 production remains CLOSED.
