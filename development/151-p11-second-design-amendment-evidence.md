# 151 — P11 Second Design Amendment Evidence — ISSUE-017..019

Status: **PASS — THIRD DESIGN CANDIDATE READY FOR FRESH DETACHED REVIEW**

Phase:
P11 — US SEC Provider

Historical ineligible candidates:

- `3ccaedc14a4c0f3f222cd192c8b7e1479d787ccd`
- `11648b22bfe97d88048c2dcf079034c37b3854af`

Stops:

- `development/147-p11-detached-design-review-stop.md`
- `development/150-p11-amended-design-review-stop.md`

Production remains CLOSED.

## P11-ISSUE-017 — deterministic package assembly

Resolved:

- required official accession-directory `index.json` asset;
- primaryDocument from validated Submissions metadata must be listed in same index;
- all safe index-listed `.xsd` and `.xml` assets captured automatically;
- deterministic role classification:
  - .xsd => TAXONOMY_SCHEMA
  - _cal.xml => CALCULATION_LINKBASE
  - _def.xml => DEFINITION_LINKBASE
  - _lab.xml => LABEL_LINKBASE
  - _pre.xml => PRESENTATION_LINKBASE
  - _htm.xml => XBRL_INSTANCE
  - other .xml => OTHER_REQUIRED_DEPENDENCY
- unrelated HTML/text exhibits are not auto-downloaded;
- optional exhibit requires exact safe basename present in index.json;
- external taxonomy/cache behavior stays behind the mandatory parser preimplementation freeze.

## P11-ISSUE-018 — implementation gate order

Resolved sequence:

```text
P11-E package store/assembly
→ P11-F runtime/parser + DEI extraction
→ P11-G v2 writer/loader
→ P11-H final period binding/registry
→ P11-I validation
```

All parser-preimplementation references now point to P11-F.

## P11-ISSUE-019 — Q2 market guard

Resolved:

- Q2 valid iff market=US;
- CN Q2 rejected;
- HK Q2 rejected;
- US Q2 never aliased to H1;
- existing CN/HK H1 behavior unchanged;
- focused and acceptance cases added.

## Static verification

PASS:

- stale old P11-G parser references = none;
- package index/asset-selection design and acceptance align;
- Q2 guards align across design/plan/acceptance;
- git diff --check;
- production/test/runtime diff = NONE;
- P11-ISSUE-010..016 prior remediation remains intact.

## Verdict

# PASS — READY FOR FRESH DETACHED DESIGN REVIEW

No development authorization is implied.

P11 production remains CLOSED.
