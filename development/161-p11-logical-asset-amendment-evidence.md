# 161 — P11 Logical Asset Identity Amendment Evidence — ISSUE-022

Status: **PASS — AMENDED DESIGN READY FOR FRESH DETACHED REVIEW**

Phase:
P11 — US SEC Provider

Historical reviewed candidate:
`5e1a1b7b39544af6c3ba464fc576174b480bd3ad`

Review stop:
`development/160-p11-logical-asset-review-stop.md`

Production remains CLOSED.

## P11-ISSUE-022 resolution

Package truth now separates logical source identity from content identity.

Content identity:

`asset_sha256`

Logical source identity:

`(file_name, canonical requested source_url)`

Rules:

- logical key unique inside one package;
- multiple logical rows may share one asset_sha256;
- content-addressed blob storage may physically reuse one blob;
- package/source_assets preserve each logical row;
- exact duplicate logical key rejected;
- package asset_count counts logical rows;
- direct accession-directory assets use dependency_depth=0 and referring_asset_sha256=null.

Role precedence:

```text
FILING_INDEX
> PRIMARY_DOCUMENT
> structured suffix classification
> REQUESTED_EXHIBIT
> excluded
```

If an explicit exhibit is already captured at higher precedence, no duplicate logical row is added and its role is unchanged.

Acceptance now covers:

- two logical rows with identical bytes/SHA;
- one physical content blob;
- both logical rows participating in package hash;
- duplicate logical key rejection;
- role precedence;
- dependency depth/referrer rules.

## Prior issue regression

ISSUE-010..021 remediation remains intact.

## Scope

Design/governance only.

No src/tests/integration/runtime-lock change.

## Verdict

# PASS — READY FOR FRESH DETACHED DESIGN REVIEW

P11 production remains CLOSED.


## Additional P11-ISSUE-023 resolution

The same stopped amendment also closes the discovery/final report-date identity gap:

- package identity report_date = normalized immutable Submissions discovery reportDate;
- final periodic v2 report_date = P11-G confirmed discovery/DEI value;
- both present must match;
- one missing may be supplied by the other;
- both missing => P11_PERIOD_UNRESOLVED;
- conflict => P11_PERIOD_CONFLICT;
- package hash is never rewritten by later DEI confirmation.

Parser-contract hardening was also expanded so the mandatory P11-F pre-code freeze must define source_kind/media_type classification, HTML/XML parser normalization/security, segment/section/table extraction rules, transformation behavior and dependency/cache semantics before parser implementation.


## Additional P11-ISSUE-024 resolution

US ticker semantics are now exact:

- CIK is canonical company identity;
- CN/HK CompanyRef ticker remains required;
- US CompanyRef ticker may be null;
- CIK-only operation never fabricates ticker;
- ticker-only zero match => P11_COMPANY_IDENTITY_NOT_FOUND;
- multiple distinct CIK matches or caller ticker/CIK mismatch => P11_COMPANY_IDENTITY_AMBIGUOUS;
- when CIK is known and no ticker was selected, zero/multiple official tickers => ticker=null;
- v2 US ticker is nullable display metadata and is not part of canonical company identity.

## Additional package-hash field hardening

All hash-participating direct asset fields now have one source:

- file_name = exact provider/index spelling;
- asset_sha256 = exact captured bytes SHA256;
- byte_size = exact captured byte length;
- declared index size mismatch blocks;
- primary=true iff role=PRIMARY_DOCUMENT;
- dependency_depth=0 and referring_asset_sha256=null for direct accession assets.

Top-level package filing_date/report_date normalization is also frozen before hash construction.
