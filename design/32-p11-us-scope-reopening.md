# 32 — P11 US Scope Reopening Contract

Status: **ACTIVE — P11 REOPENED / P0-P10 BASELINE PRESERVED**

Date: 2026-11-09

## 1. Decision

The previous project closeout limited production to CN/HK and explicitly left the
US SEC Provider unavailable. The user has now reopened the US initiative.

Current scope is therefore:

- accepted production baseline: CN + HK;
- active next phase: P11 US SEC Provider;
- P11 production status: NOT YET IMPLEMENTED;
- P0-P10 accepted CN/HK behavior: immutable unless an additive compatibility change
  is explicitly required by P11 and independently reviewed.

`design/30-project-final-cn-hk-scope.md` remains historical truth for the closeout
that occurred on 2026-11-05. This document supersedes it only as the current scope
decision from 2026-11-09 forward.

## 2. P11 objective

Add official SEC/EDGAR filing acquisition and local parsing for US-listed issuers,
with a first-class HTML / Inline XBRL / XBRL path.

P11 is not a PDF-provider retrofit.

The source-of-truth chain is:

```text
SEC filer identity (CIK)
→ SEC submissions metadata / accession
→ SEC Archives filing package
→ immutable raw members
→ deterministic HTML/iXBRL/XBRL normalization
→ page/section/table/raw-fact/evidence compatible research artifacts
→ P7 validation
→ P8 read-only access
```

## 3. Supported market declaration during development

Until P11 acceptance:

```text
accepted SUPPORTED_MARKETS = (CN, HK)
P11 US capability = DEVELOPMENT ONLY
```

The public market tuple must not be changed merely because design work exists.

Only the final P11 integration gate may add `US` after:

- identity tests;
- Registry migration compatibility;
- live SEC acquisition;
- parser/validation acceptance;
- P8 compatibility;
- full CN/HK regression.

## 4. US filing scope

### 4.1 Core periodic filings

Domestic operating companies:

- FY → Form 10-K;
- Q1 → Form 10-Q;
- Q2 → Form 10-Q;
- Q3 → Form 10-Q.

Foreign private issuers:

- FY → Form 20-F or 40-F;
- Form 6-K may be acquired explicitly;
- 6-K MUST NOT be assumed to represent a standardized quarterly filing unless a
  deterministic financial-statement identification rule is proven.

### 4.2 Explicitly not part of the required periodic set

- 8-K is an event filing, not a required periodic slot;
- proxy statements are not periodic financial-statement slots;
- registration statements are not required P11 research filings.

They may be supported later as explicit event/document acquisition without changing
periodic-filing semantics.

## 5. Source priority

P11 uses only official SEC public sources for acquisition truth:

1. `data.sec.gov/submissions/CIK##########.json`;
2. SEC Archives filing directory / filing members;
3. Inline XBRL / XBRL members in the filing package;
4. SEC XBRL companyfacts/companyconcept APIs only as secondary cross-check data.

Companyfacts MUST NOT override the facts in the exact filing being parsed.

## 6. Compatibility promise

P11 must preserve:

- ORIGINAL_DOCUMENT_IMMUTABLE;
- NO_GUESSING;
- EVIDENCE_REQUIRED;
- INCREMENTAL_FIRST;
- MCP_AI_API_CALLS = FORBIDDEN;
- P8 exact accepted tool names;
- P9 overlay semantics;
- P10 dynamic-research responsibilities.

Any necessary schema extension must be additive and versioned.

## 7. Current truth

As of this scope reopening:

`P11_SEC_PROVIDER = UNAVAILABLE`

remains factually correct in accepted production.

The target state after independent P11 acceptance is:

`P11_SEC_PROVIDER = AVAILABLE`

No current document may claim that state before acceptance.
