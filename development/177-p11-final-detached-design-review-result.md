# 177 — P11 Final Detached Design Review Result

Status: **INVALID / SUPERSEDED BY P11-ISSUE-032 STOP / NOT AUTHORITATIVE**

> Governance notice: this PASS was committed before the manual cross-gate review completed. `development/178-p11-validation-finalization-review-stop.md` subsequently found P11-ISSUE-032 on the same exact candidate. This file is retained only as historical premature-review evidence and MUST NOT close P11-A or authorize P11-B.

Phase:
P11 — US SEC Provider

Review authorization:
`development/176-p11-artifact-path-final-review-authorization.md`

Exact reviewed candidate:
`b0424620f4b7e6fc0b898c657166b171fc35e7a7`

Fresh detached worktree:
`D:\\Codex\\FinancialFilingDataFoundation\\worktrees\\review\\p11-design-b042462`

Accepted predecessor main:
`5f64f7488c4b6558e4b90fb10142b23594785a6d`

## 1. Candidate integrity

PASS:

- detached HEAD exact candidate;
- detached worktree clean;
- git diff --check PASS;
- UTF-8/no-BOM candidate documents;
- candidate diff is design/governance only;
- src diff = NONE;
- tests diff = NONE;
- integration diff = NONE;
- runtime-locks diff = NONE.

## 2. Automated contract matrix

Result:

`P11_FINAL_DESIGN_MATRIX_010_031=PASS`

Known package fixture independently reproduced:

`16e76f846fcdccf44216816148ba346ae5c100f3fcdf6fa170a6f954267bae78`

Known logical source asset fixture independently reproduced:

`41183564053cd4f7be5c66d4ed4e7c44d72ad137f9aaf60e7f5bf30c9ef41fa2`

## 3. Historical issue closure

Fresh review verified the candidate resolves P11-ISSUE-010 through P11-ISSUE-031, including:

- aggregate SEC fair-access scope;
- exact source-package identity;
- project-relative path semantics;
- canonical HTML/XML/iXBRL locators;
- deterministic v2 IDs;
- Inline XBRL raw/transformed value boundary;
- CIK/accession/path grammar;
- deterministic accession package assembly;
- parser/period-binding/writer gate order;
- US-only Q2;
- supplemental nullability/registry boundary;
- logical source asset vs content blob;
- immutable discovery reportDate vs final DEI report date;
- nullable US ticker / CIK-only flow;
- source_asset_id provenance;
- immutable source package after P11-E;
- package-aware periodic reuse;
- reuse-before-parser runtime position;
- exact reuse public API/error surface;
- registry/artifact metadata parity;
- exact ParsedDataRecord artifact_path/export-v2 storage contract.

Historical failed/partial/premature candidates remain retained and ineligible.

The historical uncommitted premature PASS for d47a0b5 is retained as:

`development/172-p11-d47a0b5-stale-pass-result-invalid.md = INVALID / NOT AUTHORITATIVE`

## 4. Identity / filing semantics

PASS:

- canonical US company identity = normalized 10-digit CIK;
- ticker is lookup/display metadata and may be null for US;
- CIK-only flow never fabricates ticker;
- CN/HK ticker behavior remains unchanged;
- Q2 iff market=US;
- CN/HK Q2 rejected;
- accession/form/amendment grammar exact;
- periodic vs supplemental identity explicit;
- 8-K/6-K supplemental filings do not enter the existing periodic registry/reuse path.

## 5. Source/package semantics

PASS:

- official accession index.json is required package inventory;
- primaryDocument must be listed in the same accession index;
- deterministic .xsd/.xml capture;
- unrelated exhibits not auto-downloaded;
- requested exhibit rule explicit;
- package manifest separated from acquisition receipt;
- canonical requested URL participates in package identity;
- logical source asset identity separate from content blob SHA;
- source_asset_id preserves same-content/different-source provenance;
- role precedence exact;
- parser/runtime cannot mutate a committed P11-E source package.

## 6. ParsedFinancialDocument v2

PASS:

- additive source-neutral v2;
- accepted PDF v1 unchanged;
- no fake page/bbox;
- source-native locator contract exact;
- exact deterministic ID formulas;
- raw_value/parsed_numeric boundary explicit;
- final periodic identity before v2 serialization;
- supplemental nullable fields explicit;
- persisted periodic artifact is the complete v2 export directory.

Exact periodic artifact layout:

`<parsed_root>/<parse_run_id>/export-v2`

Registry artifact_path:

- project-root-relative POSIX;
- no trailing slash;
- never points to manifest.json/child/staging;
- complete directory atomically committed before registry write.

## 7. Planner / registry / reuse

Manual review inspected accepted P1 identity/planner/registry code.

PASS:

- generic IncrementalPlanner remains CN/HK;
- US generic planner fails fast with exact PackageAwarePlannerRequired;
- current exact SEC package is assembled before reuse selection;
- selector executes before parser;
- selector uses requested target slot;
- exact source_package_sha256 required;
- artifact path is safe and exact-layout-bound;
- v2 artifact reload required;
- parse_run/document/package/slot identity verified;
- registry/artifact parser/schema/validation/blocking/compatibility metadata parity required;
- parity mismatch => P11_REUSE_ARTIFACT_INVALID;
- policy/validation reasons apply only after parity;
- multiple exact reusable runs select lexicographically smallest parse_run_id;
- exact reuse skips P11-F/G/H/I;
- document SHA alone is never enough for US reuse;
- existing registry schema is sufficient as pointer/index storage;
- CN/HK planner/reuse semantics unchanged.

## 8. Public API

PASS:

- PackageAwarePlannerRequired(RuntimeError) contract exact;
- exact exception module/re-export/reason/message/guard order;
- public module = financial_filing_data_foundation.sec.reuse;
- SecReuseAction exact;
- SecReuseReason exact;
- frozen/slots SecReuseDecision exact;
- select_sec_reuse signature exact;
- input ValueError surfaces exact;
- no-candidate behavior exact;
- rejection priority exact;
- selector read-only / no network.

## 9. Intentional future pre-code freezes

Two implementation areas remain intentionally closed until their own Design-First freeze:

### P11-D HTTP

Before HTTP/discovery production code, exact:

- User-Agent grammar/config;
- timeout;
- response-size caps;
- retry/backoff;
- redirect count;
- cross-process rate lock/state/recovery.

### P11-F parser/runtime

Before parser production code, exact:

- runtime Python/architecture;
- package/dependency lock;
- Arelle/parser/HTML/XML versions;
- source_kind/media_type;
- HTML recovery/tree behavior;
- XML security;
- segment/section/table rules;
- iXBRL transform/continuation/exclude behavior;
- locator/value goldens;
- taxonomy/cache behavior;
- no-network parse proof.

These are explicit future design gates, not unresolved implementation choices.

## 10. P8/P9/P10 boundary

PASS:

- P8 production/tool/schema unchanged;
- P9 review contract unchanged;
- P10 capability/context contract unchanged;
- P10 v1 continues to report P11_SEC_PROVIDER=UNAVAILABLE to P10 v1;
- Research MCP production absent;
- Semantic Resolver production absent.

## 11. Manual ambiguity review

No remaining material field/API/path/ordering ambiguity was found that would require P11-B environment/runtime probing to guess production behavior.

## 12. Verdict

# INVALID — SUPERSEDED BY development/178 / DO NOT USE AS PASS

Exact accepted P11-A design candidate:

`b0424620f4b7e6fc0b898c657166b171fc35e7a7`

This closes P11-A Design Baseline only.

It does NOT authorize provider/identity/HTTP/package/parser production.

Next permitted work is P11-B Environment / SEC Runtime Probe after a separate authorization.
