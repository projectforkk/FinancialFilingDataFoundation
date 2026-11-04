# 172 — INVALID Historical P11 Review Artifact — d47a0b5 Premature PASS

Status: **INVALID / NOT AUTHORITATIVE / RETAINED FOR AUDIT**

Reason: this uncommitted PASS artifact was produced before manual review completed. The same exact candidate was subsequently stopped by development/170-p11-registry-artifact-parity-review-stop.md for P11-ISSUE-030. It MUST NOT be used to authorize development or mark P11-A PASS.

The original uncommitted content is preserved below verbatim for audit context.

---

# 170 — P11 Final Detached Design Review Result

Status: **PASS — P11 DESIGN GATE CLOSED / PRODUCTION REMAINS CLOSED**

Phase:
P11 — US SEC Provider

Review authorization:
`development/169-p11-reuse-api-final-review-authorization.md`

Exact reviewed candidate:
`d47a0b5de5c2b3e88a5df629476d05d26e7d83fb`

Detached review worktree:
`D:\\Codex\\FinancialFilingDataFoundation\\worktrees\\review\\p11-design-d47a0b5`

Accepted predecessor main:
`5f64f7488c4b6558e4b90fb10142b23594785a6d`

## 1. Candidate integrity

PASS:

- detached HEAD exact candidate;
- detached worktree clean;
- `git diff --check` PASS;
- UTF-8 decode PASS;
- BOM absent;
- U+FFFD absent;
- candidate diff is design/governance only;
- `src/` diff = NONE;
- `tests/` diff = NONE;
- `integration/` diff = NONE;
- `runtime-locks/` diff = NONE.

## 2. Automated contract matrix

Result:

`P11_FINAL_DESIGN_MATRIX_010_029=PASS`

Verified known package fixture:

`16e76f846fcdccf44216816148ba346ae5c100f3fcdf6fa170a6f954267bae78`

Verified known logical source asset fixture:

`41183564053cd4f7be5c66d4ed4e7c44d72ad137f9aaf60e7f5bf30c9ef41fa2`

## 3. Historical issue closure

Fresh review verified the current exact candidate resolves the material design findings opened before production:

- P11-ISSUE-010 — aggregate SEC fair-access scope;
- P11-ISSUE-011 — exact package identity;
- P11-ISSUE-012 — local path semantics;
- P11-ISSUE-013 — canonical source locator;
- P11-ISSUE-014 — deterministic v2 IDs;
- P11-ISSUE-015 — Inline XBRL raw/transformed value boundary;
- P11-ISSUE-016 — CIK/accession/path grammar;
- P11-ISSUE-017 — deterministic accession package assembly;
- P11-ISSUE-018 — parser/period-binding gate dependency;
- P11-ISSUE-019 — Q2 market guard;
- P11-ISSUE-020 — final identity before v2 writer;
- P11-ISSUE-021 — supplemental identity nullability / registry boundary;
- P11-ISSUE-022 — logical source asset vs content blob;
- P11-ISSUE-023 — immutable discovery reportDate vs final DEI report date;
- P11-ISSUE-024 — nullable US ticker / CIK-only identity;
- P11-ISSUE-025 — same-content logical-source provenance collision;
- P11-ISSUE-026 — immutable package after P11-E;
- P11-ISSUE-027 — package-aware periodic reuse;
- P11-ISSUE-028 — package-aware reuse runtime position before parser;
- P11-ISSUE-029 — exact reuse public API / error surface.

Historical failed/partial candidates remain retained and ineligible.

## 4. Identity / filing semantics

PASS:

- US canonical identity = normalized 10-digit CIK;
- ticker is lookup/display only and may be null for US;
- CN/HK ticker behavior remains non-empty;
- CIK-only US flow never fabricates ticker;
- Q2 iff market=US;
- CN/HK Q2 rejected;
- amendment normalization explicit;
- accession identity exact;
- 8-K/6-K supplemental identity remains accession-bound;
- supplemental fiscal/period/date nullability is explicit;
- supplemental filings do not enter periodic SQLiteRegistry/ParsedDataRecord in P11 v1.

## 5. Source/package semantics

PASS:

- official SEC accession index.json is required package inventory;
- exact primaryDocument must be present in index;
- deterministic .xsd/.xml capture;
- unrelated exhibits not auto-downloaded;
- exact requested exhibit rule;
- package manifest separated from acquisition receipt;
- canonical requested source URL participates in package identity;
- source-package hash known fixture independently reproduced;
- logical source assets are distinct from content blobs;
- role precedence exact;
- source_asset_id known fixture independently reproduced;
- source-referencing v2 artifacts carry logical source ID + content SHA;
- parser/runtime cannot mutate committed source package;
- external taxonomy/cache material stays outside P11 v1 filing package.

## 6. ParsedFinancialDocument v2

PASS:

- source-neutral v2 is additive;
- accepted PDF v1 remains unchanged;
- no fake page/bbox for HTML/iXBRL;
- canonical HTML/XML/iXBRL locator algorithms exact;
- deterministic evidence/raw-fact/segment/section/table/cell/parse-run IDs exact;
- raw_value / parsed_numeric boundary explicit;
- periodic identity confirmed before v2 serialization;
- supplemental nullable fields round-trip without placeholder inference.

## 7. Planner / registry / reuse

Manual review inspected accepted P1 code.

Accepted facts:

- FilingSlotKey filing_type is open normalized text, not a hidden enum;
- generic IncrementalPlanner reuse is document-SHA oriented;
- ParsedDataRecord stores parse_run_id/document_sha/artifact_path but not source_package_sha;
- document_sources can retain multiple provider/source_id rows for one document SHA.

Final P11 contract is therefore internally consistent:

- generic IncrementalPlanner remains CN/HK;
- US generic call fails fast with exact `PackageAwarePlannerRequired`;
- SEC package-aware selector runs after current package assembly and before parser;
- exact current source_package_sha is mandatory for reuse;
- exact v2 artifact is reloaded and verified;
- same document SHA / different package cannot reuse;
- successful reuse skips P11-F/G/H/I;
- existing registry schema is sufficient as candidate pointer storage;
- CN/HK planner behavior remains unchanged.

## 8. Public API

PASS.

Exact generic planner exception:

`PackageAwarePlannerRequired(RuntimeError)`

Exact reason:

`P11_PACKAGE_AWARE_PLANNER_REQUIRED`

Exact public SEC reuse module:

`financial_filing_data_foundation.sec.reuse`

Exact selector:

`select_sec_reuse(registry, slot, document_sha256, source_package_sha256, reuse_policy, project_root, parsed_root) -> SecReuseDecision`

Exact action/reason enums, decision field order, invariants, no-candidate behavior, rejection priority and input validation are frozen.

No implementation-time API choice remains.

## 9. Explicit future pre-code freezes

Two areas intentionally remain unavailable to production until their own Design-First freeze:

### P11-D HTTP

Before any HTTP/discovery production code:

- exact User-Agent grammar/config;
- timeout;
- response-size caps;
- retry/backoff;
- redirect count;
- cross-process rate lock/state/recovery.

### P11-F parser/runtime

Before any parser production code:

- exact Python/runtime/dependency lock;
- Arelle/parser/HTML/XML versions;
- source_kind/media_type rules;
- HTML recovery/tree behavior;
- XML security;
- segment/section/table extraction;
- iXBRL transformation behavior;
- continuation/exclude behavior;
- locator/value goldens;
- taxonomy/cache behavior;
- no-network parse proof.

These explicit pre-code gates are intentional design controls, not unresolved implementation freedom.

## 10. P8/P9/P10 boundary

PASS:

- P8 production/tool/schema contract unchanged;
- P9 review contract unchanged;
- P10 capability/context contract unchanged;
- P10 v1 continues to report `P11_SEC_PROVIDER=UNAVAILABLE` to P10 v1;
- no Research MCP production;
- no Semantic Resolver production.

## 11. Manual ambiguity review

No remaining material field/API/ordering ambiguity was found that would require P11-B environment/runtime probe implementation to guess production behavior.

The next permitted work is environment/runtime probing only.

## 12. Verdict

# PASS — P11 DESIGN READY / PRODUCTION CLOSED

Exact accepted design candidate:

`d47a0b5de5c2b3e88a5df629476d05d26e7d83fb`

This PASS closes P11-A Design Baseline only.

It does **not** authorize:

- P11 provider production;
- permanent runtime installation;
- P11-C identity production code;
- P11-D HTTP code;
- P11-E package code;
- P11-F parser code;
- P8/P10 SEC compatibility expansion.

P11-B Environment / SEC Runtime Probe requires a separate explicit authorization.
