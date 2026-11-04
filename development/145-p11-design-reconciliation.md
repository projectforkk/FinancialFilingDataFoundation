# 145 — P11 Design Reconciliation

Status: **PASS — DESIGN CANDIDATE RECONCILED / PRODUCTION CLOSED**

Phase:
P11 — US SEC Provider

Design start baseline:
`5f64f7488c4b6558e4b90fb10142b23594785a6d`

Inputs reconciled:

- accepted P1 identity/registry contract;
- accepted P2 acquisition provider contract;
- accepted P3-P7 PDF artifact pipeline;
- accepted P8 MCP v1;
- accepted P9 review overlay;
- accepted P10 dynamic research integration;
- `design/03-parsed-financial-document-contract.md` v1;
- current official SEC/EDGAR developer documentation;
- current Arelle release metadata.

## 1. Reconciliation verdict

P11 cannot be implemented as a simple new provider plugged into current P2 production because the accepted P2/P3/P6 path is intentionally CN/HK PDF-specific.

Required P11 behavior is additive.

No accepted P0-P10 production contract is silently redefined.

## 2. P1 reconciliation

Accepted P1:

- markets CN/HK;
- periods Q1/H1/Q3/FY.

P11 needs:

- market US;
- Q2;
- CIK canonical identity.

Resolution:

- additive identity model extension in P11 development;
- CN/HK exact behavior retained;
- no Q2->H1 alias.

## 3. P2 reconciliation

Reusable:

- provider abstraction idea;
- source metadata;
- local-first/reuse-first acquisition policy;
- content SHA verification;
- registry handoff;
- project-local raw storage;
- explicit reason codes.

Not reusable as-is:

- CN/HK-only request validation;
- provider/host map;
- Dayu runtime receipt fields;
- PDF-only staging/validation;
- pre-download fiscal-period equality requirement.

Resolution:

P11 adds SEC-specific acquisition/runtime/package path while preserving P2 production semantics for CN/HK.

## 4. P3-P7 reconciliation

Accepted P3-P7 evidence model is physical-PDF-oriented.

P11 HTML/iXBRL/XBRL has no honest physical PDF page/bbox source geometry.

Resolution:

- do not fabricate v1 page/bbox;
- do not convert source HTML to PDF to fake compatibility;
- add source-neutral ParsedFinancialDocument v2 in design/30;
- P0-P10 v1 artifacts remain accepted history.

## 5. ParsedFinancialDocument reconciliation

`design/03` v1 remains unchanged.

P11 adds:

`design/30-parsed-financial-document-v2-contract.md`

v2 changes evidence coordinate system from PDF-only to source-native locator union.

This is additive, not a migration of accepted v1 artifacts.

## 6. P8 reconciliation

P8 v1 requires P3/P5/P6/P7 directories and exact accepted schemas.

Resolution:

- P11 v1 does not change P8;
- no fake v1 artifacts are generated for SEC;
- direct SEC query through P8 is explicitly outside P11 v1;
- future compatibility work requires separate authorization.

## 7. P9 reconciliation

P9 operates over accepted P8/P7 review surfaces.

Resolution:

- P11 v1 does not alter P9;
- P11 v2 validation/review gaps remain P11-native unless/until a future compatibility layer is authorized;
- no P9 raw correction semantics are copied into P11.

## 8. P10 reconciliation

P10 v1 capability manifest freezes:
`P11_SEC_PROVIDER=UNAVAILABLE`

Resolution:

After P11 exists, this continues to mean:
“P11 provider is unavailable to P10 v1’s accepted integration surface.”

P11 v1 does not silently mutate P10 context fingerprints.

A future P10/P11 compatibility extension must be explicit and independently accepted.

## 9. SEC official source reconciliation

Canonical filing evidence:

- exact EDGAR filing source assets;
- accession identity;
- CIK identity.

Auxiliary only:

- companyfacts/companyconcept/frames.

Ticker mapping:

- lookup aid;
- not canonical identity.

## 10. Runtime reconciliation

Main runtime intentionally has no HTML/XBRL stack.

Resolution:

- prefer isolated P11 runtime;
- candidate Arelle 2.47.4;
- exact runtime/version/lock not frozen until P11-B probe;
- no dependency installation authorized by design candidate itself.

## 11. Supplemental filings

8-K/6-K do not fit periodic slot semantics.

Resolution:

- accession-bound supplemental ingestion;
- no forced Q/FY slot;
- no planner pollution in P11 v1.

## 12. Design outputs

Candidate set:

- `development/144-p11-environment-interface-audit.md`;
- `design/30-parsed-financial-document-v2-contract.md`;
- `design/26-p11-sec-provider-design.md`;
- `design/27-p11-implementation-plan.md`;
- `acceptance/41-p11-acceptance-instruction.md`;
- this reconciliation.

## 13. Production status

`CLOSED`

No P11 production/test/runtime change is authorized until detached design review PASS + design-ready baseline + separate development authorization.


## 14. Detached review remediation reconciliation

Candidate `3ccaedc...` is historical/ineligible because detached review exposed P11-ISSUE-010..016 before any production authorization.

The amended design reconciles those findings without changing accepted P0-P10 production:

1. SEC fair access is aggregate: one project-root-shared cross-process gate, <=8 req/s no-burst supported boundary; no per-process-only interpretation.
2. source-package hash now has an exact identity schema/sort/exclusion contract.
3. persisted asset paths are project-root-relative POSIX storage metadata and do not enter identity.
4. HTML/XML/iXBRL locators now have exact canonical path algorithms and locator object shapes.
5. v2 deterministic IDs now have exact canonical input objects.
6. Inline XBRL raw_value has a frozen whitespace/continuation/exclude boundary; parser-specific transform implementation requires a P11-G pre-code Design-First freeze after the runtime probe.
7. CIK/accession/primaryDocument input grammar is exact.
8. P11-D exact network tuning is explicitly a pre-code Design-First freeze, not an implementation choice.

The amended candidate remains additive:

- CN/HK P1/P2 behavior unchanged;
- PDF ParsedFinancialDocument v1 unchanged;
- P8/P9/P10 accepted contracts unchanged;
- no source/test/runtime file changed.

Fresh detached design review is required before `P11_READY_FOR_DEVELOPMENT`.


## 15. Package assembly / gate-order reconciliation

Fresh review of `11648b2...` found P11-ISSUE-017..019 and stopped.

The current amendment reconciles them as follows:

- P11-E assembles the deterministic accession package from official accession-directory index.json + primaryDocument + all index-listed .xsd/.xml + explicit safe-basename requested exhibits only;
- P11-F is now the parser/runtime gate and includes DEI extraction;
- P11-G writes/loads ParsedFinancialDocument v2;
- P11-H performs final DEI-based period binding and registry binding after parser output exists;
- Q2 is legal only for market US; CN/HK Q2 remains rejected.

This resolves the circular dependency without changing accepted P0-P10 contracts.


## 16. Period-binding / v2-writer reconciliation

P11-ISSUE-020 is resolved by moving final period/identity binding before v2 serialization.

The canonical implementation order is now:

```text
P11-E package assembly
→ P11-F parser + DEI extraction
→ P11-G confirmed filing identity
→ P11-H ParsedFinancialDocument v2 writer/loader
→ P11-I validation
→ P11-K registry/reuse persistence
```

This satisfies design/30 periodic document identity without provisional/null field fabrication and preserves registry validation-before-reuse semantics.


## 17. Supplemental identity / registry reconciliation

P11-ISSUE-021 is resolved additively:

- periodic SEC filings continue into the existing periodic registry only after confirmed identity + v2 + validation;
- supplemental 8-K/6-K do not enter the periodic registry in P11 v1;
- v2 supports nullable supplemental fiscal_year/report_date/raw_fiscal_period without placeholder or calendar-derived inference;
- accession remains the supplemental source identity.

A generic supplemental registry, if needed later, is a separate additive design rather than a silent widening of accepted periodic registry semantics.


## 18. Logical source asset / content blob reconciliation

P11-ISSUE-022 is resolved by separating two identities:

- content identity = asset_sha256, used by content-addressed blob storage;
- logical source identity = (file_name, canonical requested source_url), used by package/source-assets provenance.

The same content may therefore be referenced by multiple logical source rows without duplicating blob bytes. Package identity preserves all logical rows. This avoids provenance loss while retaining storage deduplication.


## 19. Discovery report-date / final report-date reconciliation

P11-ISSUE-023 separates immutable acquisition identity from later semantic confirmation:

- package report_date = Submissions discovery metadata normalized before parsing;
- final periodic v2 report_date = P11-G confirmed value using DEI consistency;
- package hash is never rewritten by parser output.

This preserves stage ordering and immutable source-package identity while still allowing a null discovery reportDate to be completed by filing-native DEI evidence.


## 20. US CIK / optional ticker reconciliation

P11-ISSUE-024 keeps accepted CN/HK identity semantics while allowing correct SEC CIK-only operation:

- CN/HK CompanyRef still requires ticker;
- US CompanyRef may have ticker=null because CIK is canonical;
- registry slot identity remains market + company_id + filing identity and does not require ticker;
- v2 US ticker is optional display metadata only;
- no placeholder ticker is introduced.


## 20. Logical source provenance / immutable package reconciliation

P11-ISSUE-025 separates:

- content blob identity = asset_sha256;
- logical source identity = source_asset_id derived from file_name + canonical source_url + asset_sha256.

All source-native v2 provenance and deterministic IDs use the logical ID together with the content SHA, so identical bytes in different SEC logical files remain distinguishable.

P11-ISSUE-026 freezes P11 v1 package immutability across stage boundaries: P11-E is the only package-construction gate; P11-F parser/runtime dependencies cannot mutate the filing package or package hash.


## 21. Package-aware SEC reuse reconciliation

P11-ISSUE-027 reconciles P11 source-package identity with accepted P1 incremental planning without weakening CN/HK behavior.

Accepted generic IncrementalPlanner remains document-SHA based for CN/HK. It is not a valid SEC package-aware reuse engine and therefore must fail closed for market=US.

P11-K uses the existing periodic registry records only as candidate pointers. The authoritative package identity is reloaded from each candidate's v2 artifact and compared with the current source_package_sha256 before reuse.

This avoids an additive registry migration solely for package identity while preventing stale same-document/different-package reuse.


## 22. Package-aware reuse runtime-position reconciliation

P11-ISSUE-028 distinguishes implementation-gate order from runtime orchestration order.

Implementation still develops components through E/F/G/H/I/K, but runtime reuse is checked immediately after current source-package assembly and before parser execution. A previously validated exact-package artifact can therefore satisfy the requested slot without redundant parsing.


## 23. Package-aware reuse public API reconciliation

P11-ISSUE-029 closes the final API ambiguity between accepted P1 planner behavior and P11 SEC package-aware reuse.

- CN/HK retain the existing FilingPlan/PlannerItem planner result contract.
- US calls to the generic planner fail fast with one exact exception before any planning/registry side effect.
- the SEC-specific reuse layer returns a dedicated deterministic SecReuseDecision rather than overloading P1 PlannerItem or exposing raw ParsedDataRecord selection.

This keeps the accepted P1 API stable for CN/HK while giving P11 one exact package-aware contract.


## 22. Registry / artifact reuse metadata reconciliation

P11-ISSUE-030 closes the remaining metadata-binding gap in package-aware reuse.

P11-K may use existing ParsedDataRecord without adding source_package_sha256 to the registry only because every reuse decision now re-loads the v2 artifact and verifies both package identity and exact parity of parser/schema/validation/blocking/compatibility metadata against the registry row.

A parity mismatch invalidates the registry/artifact binding itself and is classified as P11_REUSE_ARTIFACT_INVALID before ordinary validation/reuse reasons are considered.


## 23. Parsed artifact path / v2 loader reconciliation

P11-ISSUE-031 binds the generic P1 artifact_path field to one exact P11 meaning:

`artifact_path = project-root-relative POSIX path to <parsed_root>/<parse_run_id>/export-v2`

This allows the existing ParsedDataRecord schema to remain unchanged while making P11-K persistence and package-aware reuse deterministic. The registry never points to a manifest child or staging directory, and the loader always receives the complete v2 export directory.


## 24. Final validation / export / registry reconciliation — ISSUE-032

P11-ISSUE-032 supersedes the earlier historical gate-order mappings in Sections 15/16 for the final P11 v1 implementation contract.

The authoritative current order is:

```text
P11-E source package
→ package-aware reuse selector
→ P11-F parser
→ P11-G confirmed filing identity
→ P11-H final validation model
→ P11-I final v2 serialization / loader verification / atomic export commit
→ P11-K registry persistence
```

Responsibilities are now disjoint:

- P11-H computes validation only and creates no registry-eligible export;
- P11-I is the only gate that creates the final complete `export-v2` directory;
- P11-K persists only after P11-I commit and successful reload;
- no provisional validation placeholder or post-registration artifact mutation is allowed.

The older H-writer/I-validation wording in historical reconciliation sections records prior issue chronology only and is not normative after this section.

This closes P11-ISSUE-032 in the amended design, pending fresh detached review.
