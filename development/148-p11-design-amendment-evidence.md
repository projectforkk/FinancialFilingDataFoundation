# 148 — P11 Design Amendment Evidence — ISSUE-010..016

Status: **PASS — AMENDED DESIGN CANDIDATE READY FOR FRESH DETACHED REVIEW**

Phase:
P11 — US SEC Provider

Historical/ineligible candidate:
`3ccaedc14a4c0f3f222cd192c8b7e1479d787ccd`

Review stop:
`development/147-p11-detached-design-review-stop.md`

Production status:
`CLOSED`

## 1. Remediated issues

### P11-ISSUE-010 — aggregate SEC fair access

Resolved:

- per-process-only interpretation removed;
- cross-process shared project-root rate gate required;
- no-burst >=125 ms between SEC request starts;
- supported single-installation aggregate ceiling <=8 req/s;
- unsafe/unavailable shared coordination => `P11_RATE_LIMIT_SCOPE_UNSAFE`;
- retries use same gate;
- concurrent-process acceptance probe added.

### P11-ISSUE-011 — package identity

Resolved:

- exact schema = `p11-sec-source-package-identity-v1`;
- exact top-level keys frozen;
- exact asset identity keys frozen;
- exact asset sort frozen;
- canonical requested source URL participates;
- redirect final URL/HTTP Content-Type/time/request/ETag diagnostics excluded;
- identity manifest separated from acquisition receipts;
- package hash excludes itself;
- known canonical fixture SHA frozen:
  `16e76f846fcdccf44216816148ba346ae5c100f3fcdf6fa170a6f954267bae78`.

### P11-ISSUE-012 — local path

Resolved:

- project-root-relative POSIX only;
- absolute/drive-relative/UNC/traversal rejected;
- resolved path must stay inside configured SEC raw-assets root;
- path excluded from all deterministic identities and semantic equality.

### P11-ISSUE-013 — source locator

Resolved:

- HTML lowercase-tag same-tag-sibling-index path;
- XML/iXBRL expanded Clark-QName same-QName-sibling-index path;
- exact locator objects for HTML_DOM, IXBRL_DOM, XML_NODE, IXBRL_FACT, XBRL_FACT, SOURCE_ASSET;
- optional keys represented by explicit null;
- exact-one-node resolution required;
- namespace prefixes excluded from QName identity.

### P11-ISSUE-014 — deterministic IDs

Resolved exact formulas for:

- config_hash;
- parse_run_id;
- segment_id;
- section_id;
- table_id;
- cell_id;
- evidence_id;
- raw_fact_id.

No path/time/random/HTTP diagnostics participate.

### P11-ISSUE-015 — Inline XBRL raw/transformed value

Resolved baseline semantics:

- continuedAt chain;
- ix:exclude handling;
- character-data source order;
- Unicode whitespace-run -> U+0020;
- outer-space trim;
- raw_value before format/scale/sign;
- nil -> parsed numeric null;
- transformation only in parsed_numeric_value;
- no unit conversion/canonicalization;
- invalid transform => null + explicit issue.

Exact runtime transformation implementation is intentionally a mandatory Design-First P11-G pre-code freeze after P11-B runtime probe.

### P11-ISSUE-016 — CIK/accession/path grammar

Resolved:

- CIK lexical regex `^[0-9]{1,10}$` after surrounding ASCII whitespace trim;
- numeric value > 0;
- normalized 10-digit zero padded;
- accession regex `^[0-9]{10}-[0-9]{2}-[0-9]{6}$`;
- no-dash form 18 digits;
- primaryDocument is provider-metadata safe basename only.

## 2. Additional consistency correction

Cross-review found a package-store determinism collision:

If source URL was excluded from package identity while immutable manifest/source-assets preserved it, one package SHA could map to multiple manifest byte variants.

Resolution:

- canonical requested source URL now participates in package identity;
- redirect-final URL remains receipt-only;
- immutable identity manifest is single-valued by package SHA;
- HTTP-declared media type remains receipt-only;
- v2 `media_type` is deterministic parser classification.

This is part of ISSUE-011 remediation.

## 3. P11-D/P11-G deferred exact parameters

No implementation freedom is introduced by deferral.

Before P11-D code, Design-First amendment must freeze:

- User-Agent grammar/config;
- timeout;
- response-size caps;
- retry/backoff;
- redirect count;
- rate-lock state/recovery.

Before P11-G code, Design-First amendment must freeze:

- exact runtime lock;
- Arelle/parser version;
- transform registry;
- continuation/exclude goldens;
- locator goldens;
- raw-value/decimal goldens;
- dependency/cache behavior;
- no-network parse proof.

Code before either required freeze is forbidden.

## 4. Official-source fact recheck

Current SEC official developer/fair-access documentation was rechecked during review:

- <=10 requests/sec is aggregate guidance regardless number of machines;
- CIK is unique filer identity;
- 10-digit zero-padded CIK is used in Submissions API URL;
- ticker mappings are not guaranteed accurate/scope-complete;
- XBRL APIs aggregate standard-taxonomy entity-wide facts and are auxiliary for P11 filing evidence;
- Inline XBRL covers operating-company 10-K/10-Q and relevant 8-K plus foreign 20-F/40-F and relevant 6-K.

The amended design remains aligned with these facts.

## 5. Static evidence

PASS:

- UTF-8 decode for all P11 candidate docs;
- BOM absent;
- U+FFFD absent;
- `git diff --check`;
- no `src/` change;
- no `tests/` change;
- no `integration/` change;
- no `runtime-locks/` change;
- old per-process-only rate wording absent;
- old source-URL exclusion absent;
- ambiguous old raw-value wording absent;
- fake `USD or null` exact-object example absent;
- rate-scope reason code present;
- package known-hash fixture present;
- canonical locator contract present;
- exact parse-run ID contract present;
- P11-D pre-code freeze present;
- P11-G pre-code freeze present.

## 6. Scope

Changed design/governance only:

- design/26;
- design/27;
- design/30;
- acceptance/41;
- development/144;
- development/145;
- PROJECT_STATUS;
- design index;
- this evidence.

No accepted P0-P10 production/test/runtime artifact changed.

## 7. Verdict

# PASS — READY FOR FRESH DETACHED DESIGN REVIEW

The prior candidate remains ineligible.

The amended candidate is not DESIGN READY until a fresh detached review passes.

P11 production remains CLOSED.
