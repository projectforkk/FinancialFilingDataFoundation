# 150 — P11 Amended Design Review Stop — Package Assembly / Gate Order

Status: **FAIL / STOP — AMENDED CANDIDATE STILL NOT DESIGN READY**

Phase:
P11 — US SEC Provider

Reviewed exact amended candidate:
`11648b22bfe97d88048c2dcf079034c37b3854af`

Fresh detached worktree:
`D:\\Codex\\FinancialFilingDataFoundation\\worktrees\\review\\p11-design-11648b2`

Re-review authorization:
`development/149-p11-amended-design-review-reauthorization.md`

## 1. Prior issue remediation

PASS:

P11-ISSUE-010 through P11-ISSUE-016 are materially remediated in candidate `11648b2...`.

The re-review found new structural gaps outside those issue definitions.

## 2. P11-ISSUE-017 — Final source-package assembly is underspecified

Design says package includes:

- filing index metadata;
- primary document;
- XBRL instance/schema/linkbases;
- requested exhibits;

but does not freeze:

- which exact official filing-index asset is required;
- how package asset discovery is performed;
- which filing-directory XML/XSD assets are automatically captured;
- how optional exhibits are selected without downloading every exhibit.

This leaves package content—and therefore package identity—to implementation discretion.

Official SEC documentation confirms accession directories provide machine-readable `index.json`, and all filing component documents are stored in the accession directory.

Required correction:

- freeze accession-directory `index.json` as required `FILING_INDEX` source asset;
- primary document comes from Submissions metadata and must exist in the index;
- automatically capture all filing-directory `.xsd` and `.xml` assets under deterministic role rules;
- do not auto-download unrelated HTML/text exhibits;
- optional exhibit selection in P11 v1 must be explicit safe basename present in index.json;
- freeze classification/sort/package assembly behavior.

## 3. P11-ISSUE-018 — Implementation gate order is impossible

Current plan:

```text
P11-F Period Binding / Registry
→ P11-G Runtime / Parser
```

But P11-F requires extracting:

- DocumentFiscalYearFocus;
- DocumentFiscalPeriodFocus.

Those are parser outputs.

Required correction:

```text
P11-E package store/assembly
→ P11-F runtime/parser
→ P11-G v2 writer/loader
→ P11-H period binding/registry
→ P11-I validation
...
```

All references to parser preimplementation freeze must move consistently from old P11-G to new P11-F.

## 4. P11-ISSUE-019 — Q2 market guard incomplete

Design says US Q2 is valid and must not alias H1, but does not explicitly freeze:

- CN Q2 rejected;
- HK Q2 rejected.

Simply adding Q2 to a global allowed-period set could accidentally widen accepted CN/HK semantics.

Required correction:

- Q2 allowed iff market=US in P11 v1;
- CN/HK Q2 rejected;
- H1 existing CN/HK semantics unchanged;
- focused/acceptance tests mandatory.

## 5. Candidate integrity

PASS:

- exact detached HEAD;
- production/test/runtime diff = NONE;
- UTF-8/no-BOM;
- git diff --check;
- prior ISSUE-010..016 remediation intact.

## 6. Verdict

# FAIL / STOP

Candidate `11648b22bfe97d88048c2dcf079034c37b3854af` is INELIGIBLE for DESIGN READY.

Required:

STOP → amend design/26, design/27, design/30/acceptance as affected → evidence → new candidate → fresh detached review.

P11 production remains CLOSED.
