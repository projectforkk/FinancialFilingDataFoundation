# 27 — P11 US SEC Provider Implementation Plan

Status: **READY FOR DEVELOPMENT AFTER DESIGN FREEZE**

Detailed design:
`design/26-p11-sec-provider-design.md`

Scope reopening:
`design/32-p11-us-scope-reopening.md`

## 1. Development strategy

P11 is rebuilt from accepted current main.

Historical P11 branches are reference-only.

No gate may import a historical production candidate wholesale.

The implementation is split so that acquisition, package identity, parsing and
integration can be reviewed independently.

## 2. P11-A — Environment / interface audit

Goal:
freeze actual implementation constraints before code.

Tasks:

1. inspect current main package/runtime dependencies;
2. inspect Registry migration mechanism;
3. inspect P3/P5/P6/P7 loaders and required fields;
4. inspect P8 catalog/tool response schemas;
5. verify current SEC public endpoints and Fair Access behavior;
6. select dedicated SEC runtime base;
7. probe representative official SEC filings without writing production workspace;
8. measure HTML/XBRL sizes and parser requirements.

Evidence:
`development/<next>-p11-a-environment-interface-audit.md`

Completion:

- exact runtime/dependency proposal;
- exact compatibility gaps;
- no production code;
- design amendment if audit contradicts design.

STOP if:
an accepted P0-P10 invariant cannot be preserved additively.

## 3. P11-B — US identity + SEC discovery

Implement:

- CIK-backed CompanyRef extension behind P11 feature boundary;
- ticker→CIK resolver;
- SEC submissions client;
- filing form/period policy;
- accession parsing;
- recent + historical submissions pagination;
- amendment detection;
- Fair Access limiter/User-Agent configuration.

Tests:

- ticker/cik normalization;
- ambiguous mapping rejection;
- 10-K/10-Q mapping;
- Q2 supported only for US domestic policy;
- CN/HK period behavior unchanged;
- /A variant handling;
- rate limiter/backoff/host allowlist.

Exit:
deterministic `DocumentCandidate`-equivalent SEC filing candidates, no raw writes.

## 4. P11-C — Immutable SEC package acquisition

Implement:

- archive directory/member discovery;
- minimal required-member selection;
- staging downloads;
- member SHA256;
- canonical package manifest;
- package SHA256;
- atomic package-store commit;
- acquisition receipt;
- source-package Registry records.

Tests:

- same package is reused;
- interrupted staging cannot become committed package;
- path traversal rejected;
- redirect host rejected;
- size/content-type limits;
- same archive member changed bytes → SOURCE_DRIFT;
- original member bytes never modified.

Live acceptance candidate:
one domestic 10-K and one 10-Q.

## 5. P11-D — Registry migration / planner integration

Implement additive schema migration:

- source_packages;
- package_members;
- package binding support;
- accession provenance;
- planner actions REUSE_DATA / PARSE_LOCAL / DISCOVER_AND_ACQUIRE.

Requirements:

- old CN/HK Registry opens successfully;
- migration is transactional/idempotent;
- old rows byte/semantic-equivalent;
- CN/HK planner tests unchanged.

STOP if migration requires destructive table rewrite.

## 6. P11-E — HTML/iXBRL normalization

Implement in dedicated SEC runtime:

- HTML parse with scripts/network resources disabled;
- deterministic DOM normalization;
- headings/source blocks;
- virtual HTML pages;
- block IDs/DOM locators/fragment hashes;
- section extraction;
- primary-document metadata.

Tests:

- identical bytes + same parser version → identical artifact identity;
- DOM locator round-trip;
- virtual pages stable;
- malformed HTML fail/review behavior;
- no JavaScript execution;
- no remote subresource fetch.

Output:
P3-compatible source-aware artifact.

## 7. P11-F — HTML table path

Implement:

- DOM table candidate detection;
- rowspan/colspan handling;
- nested-table signals;
- header tree;
- cell source locators;
- fact-reference attachment.

Outputs:
P4/P5-compatible artifacts.

Tests:
financial statements, note tables, nested formatting, hidden/layout tables.

No OCR/TableFormer.

## 8. P11-G — Inline XBRL/XBRL raw facts + evidence

Implement:

- context/unit collection;
- inline numeric/non-numeric facts;
- raw QName preservation;
- scale/sign/decimals;
- dimensions;
- nil facts;
- custom extension concepts;
- source member/block/DOM evidence;
- unresolved context/unit issue generation.

Do not implement canonical metric mapping.

Output:
P6-compatible raw facts/evidence.

## 9. P11-H — P7 validation

Implement source-aware US checks:

- package hash;
- accession/CIK/form consistency;
- context/unit resolution;
- evidence coverage;
- locator resolution;
- slot conflict;
- source drift;
- period plausibility.

Optional:
companyfacts cross-check for standard concepts.

Companyfacts mismatch cannot overwrite filing-local facts.

Focused negative fixtures required.

## 10. P11-I — P8 US read path

Extend catalog/service additively:

- market=US entries;
- virtual page metadata;
- HTML evidence locators;
- SEC package identity.

Keep exact accepted P8 tool names.

Required tests:

- all existing CN/HK P8 tests unchanged;
- US list/get/search/pages/sections/tables/facts/evidence/validation;
- startup remains lazy;
- no acquisition/network inside MCP.

## 11. P11-J — User CLI US integration

Extend:

`ffdf acquire`
`ffdf ingest`
`ffdf status`

US examples:

```text
ffdf acquire --market US --ticker AAPL --year 2026 --period Q3
ffdf ingest  --market US --ticker AAPL --year 2026 --period Q3
ffdf status  --market US --ticker AAPL --year 2026 --period Q3
```

Add market-specific period rules:

- CN/HK unchanged;
- US domestic adds Q2.

Support explicit CIK.

Do not expose arbitrary SEC URLs.

## 12. P11-K — Foreign private issuer gate

Required annual support:

- 20-F;
- 40-F if representative fixture is available and parser semantics are compatible.

6-K:

- explicit acquisition may be supported;
- automatic Q1/Q2/Q3 required-slot mapping remains closed unless deterministic
  financial-statement identification is proven and designed.

If not proven:
return `P11_UNSUPPORTED_FPI_PERIODIC_MAPPING` rather than guess.

## 13. P11-L — Full regression / compatibility

Run:

- P11 focused unit;
- Registry migration tests;
- SEC runtime tests;
- P3-P8 US integration;
- P9/P10 compatibility;
- full existing unit suite;
- compile;
- CLI smoke;
- diff/check.

Hard requirement:
CN/HK accepted behavior unchanged.

## 14. P11-M — Live evidence package

Freeze exact official SEC accessions for acceptance.

Minimum:

- domestic 10-K;
- domestic 10-Q;
- custom-extension Inline XBRL;
- amended-form negative/review case;
- foreign 20-F or 40-F;
- repeated acquire proving no re-download;
- repeated ingest proving incremental reuse.

Evidence records:

- URLs;
- accession;
- CIK;
- member hashes;
- package hash;
- artifact counts;
- validation result;
- P8 query evidence.

## 15. P11-N — Formal detached code review

Review exact candidate against:

- design/26;
- design/27;
- P0-P10 invariants;
- security/Fair Access;
- Registry compatibility;
- evidence traceability.

Any design defect:
STOP → update design → invalidate affected evidence → rerun.

## 16. P11-O — Acceptance freeze

Freeze:

- design baseline SHA;
- production candidate SHA;
- SEC runtime lock;
- fixture accessions/member hashes;
- commands;
- expected reason codes;
- full regression results.

No candidate mutation after freeze.

## 17. P11-P — Independent acceptance

Independent acceptance must verify:

1. official SEC discovery;
2. immutable package acquisition;
3. local re-use;
4. HTML/iXBRL parsing;
5. raw facts/evidence;
6. negative gates;
7. P8 access;
8. CLI US flow;
9. CN/HK non-regression;
10. no remote AI calls.

PASS is required before public US market enablement.

## 18. P11-Q — Main integration

Only after acceptance PASS:

- merge exact accepted candidate;
- set supported-market declaration to include US where required;
- update capability manifest from unavailable to available;
- update README/user manual;
- run final main regression;
- record integration commit.

No rebase/squash that changes accepted candidate semantics unless re-accepted.

## 19. P11-R — Closeout

Closeout records:

- final design SHA;
- accepted candidate;
- merge SHA;
- runtime lock;
- supported filing forms;
- explicit unsupported cases;
- live acceptance fixtures;
- known non-blockers.

Final state:

`P11 DONE / PASS`

only if all previous gates close.

## 20. Planned acceptance quality bar

P11 is not successful merely because a 10-K downloads.

Success requires:

```text
official discovery
+ immutable package
+ deterministic parse
+ exact raw-fact evidence
+ validation
+ P8 queryability
+ incremental reuse
+ CN/HK non-regression
```

## 21. Development order

Exact order:

```text
A audit
→ B identity/discovery
→ C package acquisition
→ D Registry/planner
→ E HTML normalization
→ F tables
→ G XBRL facts/evidence
→ H validation
→ I P8
→ J CLI
→ K foreign issuer
→ L regression
→ M live evidence
→ N review
→ O freeze
→ P acceptance
→ Q integration
→ R closeout
```

No later gate may be used to justify skipping an earlier gate.
