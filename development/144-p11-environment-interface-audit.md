# 144 — P11 Environment / Accepted Interface Audit

Status: **PASS — P11 DESIGN MAY PROCEED / PRODUCTION REMAINS CLOSED**

Phase:
P11 — US SEC Provider

Design authorization:
`development/143-p11-design-authorization.md`

Design worktree:
`D:\\Codex\\FinancialFilingDataFoundation\\worktrees\\active\\p11-sec-provider-design`

Design branch:
`design/p11-sec-provider`

Design start:
`5f64f7488c4b6558e4b90fb10142b23594785a6d`

## 1. Current environment

FFDF main runtime:

- Python 3.14.9
- Windows ARM64
- `lxml`: absent
- `bs4`: absent
- `html5lib`: absent
- `requests`: absent
- `httpx`: absent
- `arelle`: absent
- `pyxbrl`: absent
- `sec_edgar_downloader`: absent

No dependency manifest is currently used at repository root.

Existing isolated runtimes prove project-local Python 3.12 AMD64 isolation is available.

## 2. Official SEC source facts

Reviewed 2026-11-04 from official SEC documentation:

- `data.sec.gov` exposes public JSON APIs without API keys;
- Submissions API provides filer submission history;
- XBRL APIs cover 10-Q, 10-K, 8-K, 20-F, 40-F, 6-K and variants;
- APIs update throughout the day;
- current automated access maximum is 10 requests/second;
- SEC requires declared automated access / appropriate User-Agent behavior;
- accession number is the EDGAR submission identity;
- CIK is the SEC filer identity;
- ticker/CIK association files exist but SEC does not guarantee their accuracy/scope;
- post-acceptance corrections/deletions can change historical index state;
- Inline XBRL is the normal structured financial statement carrier for domestic operating companies and relevant foreign private issuer forms.

Official references:

- https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data
- https://www.sec.gov/about/webmaster-frequently-asked-questions
- https://www.sec.gov/data-research/structured-data/inline-xbrl
- https://www.sec.gov/file/company-tickers
- https://www.sec.gov/submit-filings/technical-specifications

## 3. XBRL runtime candidate

Current Arelle release observed on 2026-11-04:

- package: `arelle-release`
- version: `2.47.4`
- released: 2026-10-31
- requires Python >=3.11
- wheel: `py3-none-any`
- supports Inline XBRL 1.1 / XBRL 2.1
- supports SEC EDGAR validation tooling
- release wheel SHA256 published by PyPI:
  `366b9ced1a9e5058a31f4ffd347ec6fc6900c6931ade3d97a36d7836151fe3e1`

Arelle is a design candidate only. No runtime/dependency installation is authorized yet.

Recommended implementation boundary:
dedicated project-local P11 SEC runtime, preferably Python 3.12 AMD64, with a locked dependency set.

## 4. Accepted interface audit

### 4.1 Identity

Current P1 constraints:

- markets = `CN/HK` only;
- periods = `Q1/H1/Q3/FY`;
- no `US`;
- no `Q2`.

Therefore existing identity models cannot represent ordinary US 10-Q history without semantic corruption.

Do not map US Q2 to H1.

### 4.2 Acquisition

`AcquisitionProvider` abstraction is reusable in concept.

Current concrete acquisition models/service are not source-neutral:

- AcquisitionRequest rejects non-CN/HK;
- AcquisitionCandidate rejects periods outside Q1/H1/Q3/FY;
- expected providers are hard-coded to cninfo/hkexnews;
- source hosts are hard-coded to CNINFO/HKEX;
- receipt schema is Dayu/PDF-specific;
- candidate selection requires fiscal period before download.

SEC requires provisional discovery because reliable fiscal-period focus may need filing/iXBRL DEI facts after acquisition.

### 4.3 Raw store

Current `RawDocumentStore` is PDF-only:

- staging suffix = .pdf;
- PDF magic required;
- final object suffix = .pdf.

It cannot safely store SEC HTML/XML/JSON source packages.

### 4.4 Registry

Registry document hashing/registration is mostly source-neutral.

Positive facts:

- arbitrary files can be registered;
- non-PDF files receive `page_count=None`;
- SourceMetadata is generic enough for provider/source URL/title/CIK metadata.

Constraints:

- FilingSlotKey still blocks US/Q2;
- ParsedDataRecord remains slot-bound;
- supplemental 8-K/6-K filings need a separate identity path or explicit planner extension.

### 4.5 PDF pipeline

P3 native parser is explicitly PDF-only.

P3/P5/P6 current artifact semantics require physical PDF constructs:

- physical `page_no`;
- bbox;
- word/block/line identities;
- table-cell geometry;
- P6 evidence IDs derived from page/word/bbox refs.

SEC HTML/iXBRL/XBRL must not fabricate virtual physical pages or synthetic bbox merely to satisfy these schemas.

### 4.6 P8/P9/P10

P8 catalog v1 requires P3/P5/P6/P7 directories.
P8 result/tool contract is accepted and frozen.

P10 v1 fingerprints the exact P8/P9 contract and currently reports:
`P11_SEC_PROVIDER = UNAVAILABLE`.

P11 v1 must not silently alter P8/P9/P10 accepted contracts.

Any future direct P10 consumption of SEC-native artifacts requires a separate explicit compatibility design/review/acceptance gate.

## 5. Design issues opened

### P11-ISSUE-001 — US identity gap

Need:

- market US;
- canonical CIK identity;
- Q2 support;
- exact form/amendment semantics;
- separate periodic vs supplemental filing role.

### P11-ISSUE-002 — acquisition core is CN/HK/PDF-specific

Need additive SEC acquisition contract without regressing P2.

### P11-ISSUE-003 — raw store is PDF-only

Need source-package storage for HTML/XML/JSON and exact raw bytes.

### P11-ISSUE-004 — ParsedFinancialDocument v1 is physical-PDF-specific

Need additive source-neutral v2 contract.
Do not rewrite accepted v1 history.

### P11-ISSUE-005 — SEC discovery period binding

Submissions metadata alone is insufficient for a trustworthy US fiscal-quarter slot in all cases.

Use filing facts such as DEI DocumentFiscalPeriodFocus / DocumentFiscalYearFocus for final binding when available.

### P11-ISSUE-006 — ticker is not canonical identity

SEC ticker files are lookup hints, not guaranteed authoritative identity.

CIK is provider canonical company identity.

### P11-ISSUE-007 — companyfacts is not filing truth

SEC companyfacts aggregates standard taxonomy facts and excludes custom-taxonomy facts.

Use exact filing/iXBRL/XBRL assets as primary evidence.
Companyfacts may be cross-check/acceleration only.

### P11-ISSUE-008 — post-acceptance corrections

Accession identity alone is not sufficient for byte identity.

Store exact source bytes + SHA256 + package manifest identity.

### P11-ISSUE-009 — fair access/security

Design must enforce:

- explicit User-Agent;
- <=10 requests/sec globally per process;
- HTTPS;
- strict SEC/FASB allowlist as needed;
- redirect revalidation;
- response-size limits;
- content-type checks;
- no arbitrary URL fetch;
- no archive path traversal.

## 6. Recommended architecture direction

P11 v1 should implement a parallel SEC-native path:

```text
SEC identity resolver
→ Submissions discovery
→ accession package acquisition
→ immutable SEC package store
→ HTML/iXBRL/XBRL parse
→ source-neutral ParsedFinancialDocument v2
→ deterministic SEC validation
→ parsed-data registry/export
```

Do not route SEC HTML through PDF conversion.

Do not create fake page/bbox evidence.

P11 v1 should preserve accepted P8/P9/P10 production unchanged.

## 7. Periodic vs supplemental filing scope

Periodic slot-bound v1 targets:

- 10-K / 10-K/A;
- 10-Q / 10-Q/A;
- 20-F / 20-F/A;
- 40-F / 40-F/A.

Supplemental accession-bound ingestion targets:

- 8-K / 8-K/A;
- 6-K / 6-K/A.

Supplemental filings are not silently forced into Q1/Q2/Q3/FY planner slots.

## 8. Production authorization status

No P11 production code is authorized.

Next design outputs:

- `design/30-parsed-financial-document-v2-contract.md`;
- `design/26-p11-sec-provider-design.md`;
- `design/27-p11-implementation-plan.md`;
- `acceptance/41-p11-acceptance-instruction.md`.

Only after design review + design baseline commit/push may a separate P11 development authorization be considered.
