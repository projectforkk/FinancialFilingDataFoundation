# 163 — P11 US SEC Provider Fifth Exact-Candidate Code Review

Status: **CHANGES_REQUIRED**

Reviewed exact production candidate:

`362877244aa553ca4d76eb71318b116cde04c6a5`

Full design/code audit:

`development/161-p11-full-design-code-consistency-audit.md`

Repair evidence:

`development/162-p11-design-consistency-repair-evidence.md`

Repair evidence commit:

`a9ababd7eaefcb5bace267bb57bb17e0d707e93d`

Development branch:

`task/p11-sec-rebuild-development`

## 1. Exact-candidate lineage gate

PASS.

The reviewed candidate is a descendant of audit commit
`be78d868524afb302091085856e70489bba2db24`.

After exact candidate `362877244aa553ca4d76eb71318b116cde04c6a5`, the evidence commit changes only:

- `development/162-p11-design-consistency-repair-evidence.md`;
- `docs/superpowers/plans/2026-11-10-p11-design-consistency-repair.md`.

No production source or test file changed after the exact candidate.

This review therefore applies to the exact production candidate, not to an unbounded branch state.

## 2. Repair areas accepted in this review

The exact candidate materially fixes the following audit items and no regression was found in their reviewed code paths:

- P11-ISSUE-109: **FIXED** — unrelated safe nested non-periodic primaryDocument rows no longer poison periodic discovery; target periodic paths remain validated.
- P11-ISSUE-110: **FIXED** — a shared canonical Windows-safe archive-relative path policy is used before URL construction and package storage; accession-root URL construction is explicit.
- P11-ISSUE-111: **FIXED** — explicit CIK is authoritative and bypasses ticker-map resolution; stable CIK/company_id is propagated into SEC catalog/status identity; ticker-map source bytes/SHA/time/source URL are persisted when ticker lookup is used; market-specific period validation is present.
- P11-ISSUE-113: **FIXED** — member content type stores the header value, archive index shape is validated, source bytes are checked, and generic/linkbase XML is not blindly classified as an XBRL instance.
- P11-ISSUE-114: **FIXED for the audited minimum contract** — SEC table records now separate package/document identity from source-member identity and expose designed table/cell source, span, heading/caption, nested-table, Inline-XBRL, visibility/style and fact-reference metadata.
- P11-ISSUE-115: **FIXED for the audited minimum contract** — explicit/typed dimensions are distinct, typed-member text is retained, namespaced nil is recognized, and raw QName preservation remains intact.
- P11-ISSUE-117: **FIXED** — P8 SEC raw-fact page and metric filtering is source-kind compatible through virtual_page_no/raw_qname support while preserving CN/HK behavior.
- P11-ISSUE-118: **FIXED for the current stdlib runtime contract** — connect/read/total timeout settings are explicit, positive, bounded and transported through the subprocess boundary.
- P11-ISSUE-119: **FIXED** — history chunk filingFrom/filingTo metadata is retained and unrelated chunks are excluded before network fetch.

The reported live Apple 10-K, Apple Q3 10-Q, Toyota 20-F and Kellanova CIK-only amendment results are internally consistent with these repaired paths.

## 3. P11-ISSUE-112 — STILL OPEN

### 3.1 Parsed-data compatibility is not tied to the current parser/schema

The frozen incremental rule is:

```text
compatible parsed package available?
→ REUSE_DATA

else immutable local SEC package available?
→ PARSE_LOCAL
```

Current `_us_plan_slot()` treats a parsed row as reusable when it has:

- validation_status = PASS;
- compatibility_status = COMPATIBLE;
- zero blocking issues;
- a directory that exists.

It does **not** require:

- `row.package_sha256` to equal the local package selected for the slot;
- `row.parser_version` to equal the current `VIRTUAL_HTML_NORMALIZER_VERSION`;
- `row.schema_version` to equal the current SEC artifact schema.

Therefore a stale parsed row from an older parser/schema can make the planner return `REUSE_DATA` for a different/current package or parser generation.

The new unit test actually encodes this defect: it registers an arbitrary `parser_version="V3"` row with `compatibility_status="COMPATIBLE"` and expects `REUSE_DATA`, without comparing it to the production parser version.

This is not the design meaning of “compatible parsed package”.

### 3.2 Direct SecAcquirer local-package reuse is mislabeled

`SecAcquirer.acquire()` checks `SecPackageStore.find_by_slot()` before network discovery.

When a local package exists it returns:

```python
plan_action="REUSE_DATA" if local.period.upper() == str(period).upper() else "PARSE_LOCAL"
```

But `find_by_slot()` already matched that period, so this condition is effectively always true.

The acquirer has no parsed-data/validation knowledge and therefore cannot prove `REUSE_DATA`; package-only local state is, by design, `PARSE_LOCAL`.

Required repair:

1. bind parsed compatibility to the same package SHA selected for the slot;
2. require current parser version and current artifact schema;
3. package-only local state must be `PARSE_LOCAL`;
4. add stale-parser, stale-schema and wrong-package parsed-row regressions.

P11-ISSUE-112 remains **OPEN**.

## 4. P11-ISSUE-120 — STILL OPEN

### 4.1 Normalizer semantics changed without a version bump

Audit 161 explicitly required:

> If normalization behavior changes, bump the normalizer/parser version rather than silently reusing artifacts generated by the previous normalization algorithm.

Previous candidate `05e06096...` used:

`VIRTUAL_HTML_NORMALIZER_VERSION = "VIRTUAL_HTML_V3"`.

The reviewed candidate substantially changes:

- DOM construction/caching;
- visible/hidden text evaluation;
- div/span/section/article block promotion;
- inline-wrapper suppression;
- fact-to-source-block anchoring;
- styled/class heading handling;
- evidence DOM indexing.

But it still declares:

`VIRTUAL_HTML_NORMALIZER_VERSION = "VIRTUAL_HTML_V3"`.

`parse_sec_package()` uses:

```python
final_dir = root / f"{package.package_sha256}.{VIRTUAL_HTML_NORMALIZER_VERSION}"
if final_dir.exists():
    return load_sec_artifacts(final_dir)
```

Therefore an existing V3 artifact produced by the failed pre-repair parser is silently reused and the ISSUE-120 repair is never applied.

The developer live smoke used a fresh isolated root, so it cannot prove upgrade/reuse correctness for an existing P11 workspace.

This is a blocking incremental-compatibility defect.

### 4.2 Ordinary visible HTML <header> is still classified as hidden

The new hidden-state helper treats every node whose local tag is `header` as hidden:

```python
_local(current.tag) in {"script", "style", "header", "hidden"}
```

That correctly catches `ix:header` through the separate explicit tag rule, but it also hides an ordinary visible HTML5 `<header>` element and all of its descendants.

A normal HTML `<header>` is not equivalent to Inline-XBRL `<ix:header>`.

This contradicts the ISSUE-120 requirement to preserve deterministic visible filing narrative.

Required repair:

1. bump the normalizer/parser version (for example V4);
2. force new artifact identity for the changed normalization semantics;
3. make planner compatibility reject prior normalizer versions;
4. distinguish ordinary visible HTML `header` from `ix:header`;
5. add a regression proving an existing V3 artifact is not reused by the repaired normalizer;
6. add a visible HTML5 `<header>` source-block regression.

P11-ISSUE-120 remains **OPEN**.

## 5. P11-ISSUE-116 — PARTIALLY OPEN

The repaired validation now adds materially stronger metadata, period, table/cell and evidence checks, and correctly prevents REVIEW_REQUIRED artifacts from being reuse-eligible.

However `compatibility_status` is still derived from validation outcome:

```python
compatibility_status = "COMPATIBLE"
    if status == "PASS" and blocking == 0
    else "INCOMPATIBLE"
```

Accepted P7 semantics keep two concepts separate:

- validation status describes quality/review/blocking findings;
- compatibility status describes whether the artifact/parser/schema contract is compatible.

A current-format artifact can be structurally compatible while still being `REVIEW_REQUIRED`.

The required reuse rule is:

```text
PASS
AND COMPATIBLE
AND zero blocking issues
→ reusable
```

not:

```text
PASS → COMPATIBLE
non-PASS → INCOMPATIBLE
```

This matters directly to the planner repair above.

Required repair:

- derive compatibility from parser/schema/policy compatibility, independently of validation issues;
- keep `reuse_eligible = PASS && COMPATIBLE && zero blocking`;
- add a REVIEW_REQUIRED-but-COMPATIBLE regression.

P11-ISSUE-116 is **PARTIALLY OPEN**.

## 6. New blocking finding — P11-ISSUE-121

### SEC Registry schema changed without advancing its version

The candidate adds a new required column:

`sec_parsed_data.compatibility_status`

and migrates pre-existing SEC registries using:

```sql
ALTER TABLE sec_parsed_data
ADD COLUMN compatibility_status TEXT NOT NULL DEFAULT 'INCOMPATIBLE'
```

But the public extension version remains:

```python
SEC_REGISTRY_SCHEMA_VERSION = 2
```

So two materially different SEC schema shapes are both called version 2.

This violates the P11 design requirement that Registry extensions/migrations be additive **and versioned**.

It also prevents callers/evidence from distinguishing:

- old SEC schema v2 without compatibility_status;
- repaired schema with compatibility_status.

Required repair:

1. advance the SEC extension schema version;
2. migrate the prior P11 development schema deterministically and idempotently;
3. keep legacy CN/HK `PRAGMA user_version = 1` unchanged;
4. add an old-SEC-schema → new-SEC-schema migration test;
5. prove repeated open/migration is idempotent and old CN/HK rows remain unchanged.

P11-ISSUE-121 is **OPEN / BLOCKING**.

## 7. Development evidence assessment

Repair evidence reports:

- P11 focused: 78 passed;
- full unit: 608 passed;
- CN/HK regression: 96 passed;
- compileall: PASS;
- git diff --check: PASS;
- Apple FY2025 10-K live: PASS;
- Apple FY2025 Q3 live: PASS;
- Toyota FY2025 20-F live: PASS;
- Kellanova CIK-only amendment: expected controlled P11_AMENDED_VARIANT_PRESENT;
- P8 SEC tool smoke: PASS.

These are valuable development results and confirm that the repaired fresh-workspace path is much stronger.

They do not override the exact-source defects above, especially because the normalizer-version defect appears specifically on an existing-artifact upgrade/reuse path not covered by the fresh live root.

## 8. Fifth review verdict

```text
P11 FIFTH CODE REVIEW: CHANGES_REQUIRED

P11-ISSUE-109: FIXED
P11-ISSUE-110: FIXED
P11-ISSUE-111: FIXED
P11-ISSUE-112: STILL OPEN
P11-ISSUE-113: FIXED
P11-ISSUE-114: FIXED
P11-ISSUE-115: FIXED
P11-ISSUE-116: PARTIALLY OPEN
P11-ISSUE-117: FIXED
P11-ISSUE-118: FIXED
P11-ISSUE-119: FIXED
P11-ISSUE-120: STILL OPEN

P11-ISSUE-121: NEW BLOCKER

EXACT PRODUCTION CANDIDATE:
362877244aa553ca4d76eb71318b116cde04c6a5

FORMAL TEST PLAN:
NOT ISSUED

FORMAL ACCEPTANCE:
NOT RESUMED

MAIN MERGE:
NOT AUTHORIZED

P11 PRODUCTION AVAILABILITY:
NOT CHANGED
```

## 9. Required next action

Perform one minimal consistency repair focused only on:

- P11-ISSUE-112;
- remaining P11-ISSUE-116 compatibility semantics;
- remaining P11-ISSUE-120 parser/normalizer invalidation and HTML header visibility;
- P11-ISSUE-121 Registry extension versioning.

Do not reopen the already accepted 109/110/111/113/114/115/117/118/119 implementations unless required by regression.

After repair:

1. focused P11 tests;
2. full unit suite;
3. CN/HK regression;
4. compileall;
5. git diff --check;
6. targeted incremental upgrade test from an existing V3 artifact/old SEC registry;
7. new exact production candidate commit;
8. separate development evidence commit;
9. stop for ChatGPT exact-candidate review.

No formal acceptance plan is authorized before REVIEW_PASS.
