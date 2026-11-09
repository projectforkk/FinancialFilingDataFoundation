# 149 — P11 US SEC Provider Exact-Candidate Code Review Result

Status: **CHANGES_REQUIRED**

Reviewed candidate:

`529376cc084bd9990c144102fa723822b5229e1a`

Design baseline:

`c970d63c2699d016c1696451d2a66fc42850b4f1`

Development evidence:

`development/148-p11-development-evidence.md`

Review scope:

- exact candidate lineage;
- SEC identity/discovery;
- HTTP/Fair Access/security;
- immutable package acquisition;
- Registry/planner;
- HTML/Inline XBRL parser;
- Raw Facts/Evidence;
- P7 validation;
- P8 read path;
- CLI;
- CN/HK compatibility.

## 1. Lineage / evidence integrity

PASS.

The candidate is exactly 5 commits ahead of the frozen design baseline and 0 behind.

The development branch is exactly one evidence-only commit ahead of the production
candidate. That post-candidate commit only adds
`development/148-p11-development-evidence.md`; no production code changed after
the reviewed SHA.

## 2. Blocking review findings

### P11-ISSUE-101 — Fiscal-period discovery assumes calendar-year quarter ends

Severity: **BLOCKING**

Observed implementation:

`us_sec/discovery.py::_period_for_report_date()` maps report-period month directly:

```text
03 → Q1
06 → Q2
09 → Q3
12 → FY
```

and `discover_filings()` additionally requires:

```text
candidate.report_period[:4] == requested fiscal_year
```

Impact:

This is incorrect for non-calendar fiscal-year issuers.

Example class:

- fiscal year ending September;
- FY2025 Q1 may end in December 2024;
- FY2025 Q2 may end in March 2025;
- FY2025 Q3 may end in June 2025;
- FY may end in September 2025.

The current logic can reject Q1 entirely and shift Q2/Q3/FY labels.

The public development examples explicitly use AAPL-like US issuers, so this is not
an edge-only issue.

Required fix:

- remove calendar-month quarter mapping;
- derive fiscal slot deterministically using SEC fiscal-year metadata and filing
  chronology / fiscal-year-end semantics, or another design-consistent official
  SEC basis;
- support 52/53-week and non-December fiscal years without guessing;
- add fixtures covering at least:
  - December fiscal year;
  - September fiscal year;
  - fiscal Q1 ending in the prior calendar year;
  - Q2/Q3/FY for the same non-calendar issuer;
  - FPI non-December FY.

Acceptance condition:

The same requested `fiscal_year + Q1/Q2/Q3/FY` must resolve correctly for both
calendar and non-calendar issuers.

### P11-ISSUE-102 — P7 can PASS a periodic filing with zero XBRL Raw Facts

Severity: **BLOCKING**

Observed implementation:

`validate_sec_artifacts()` verifies identity consistency among existing facts and
evidence but does not require any facts/evidence to exist.

The current unit test intentionally builds a 10-Q-like package containing only:

```html
<h1>Revenue</h1>
<p>Revenue was 100.</p>
```

with no Inline XBRL fact and asserts:

```text
validation_status == PASS
research_ready == True
P8 publication == ADDED
```

Impact:

A parser that fails to detect all Inline XBRL facts can still be marked PASS and
published as research-ready.

Required fix:

For P11 targeted periodic forms (10-K, 10-Q, 20-F, 40-F), validation must fail
closed when the structured-fact extraction result is implausibly empty.

At minimum:

- zero Raw Facts must not produce PASS;
- zero Evidence paired to structured facts must not produce PASS;
- use an explicit reason code;
- classify as REVIEW_REQUIRED or BLOCKED according to the final policy;
- a positive acceptance fixture must contain real filing facts/evidence.

Do not solve this by fabricating facts from plain HTML text.

### P11-ISSUE-103 — Client requests gzip but runtime does not decode Content-Encoding

Severity: **HIGH / LIVE BLOCKER**

Observed implementation:

`SecHttpClient.fetch()` sends:

```text
Accept-Encoding: gzip
```

The stdlib transport reads response bytes directly and neither
`_network_transport()` nor the subprocess runner performs gzip decompression.

Impact:

If SEC returns gzip-encoded content, downstream JSON decode / HTML parsing receives
compressed bytes and fails. Size limits also apply to compressed bytes rather than
the decoded payload.

Required fix:

Choose one deterministic policy:

1. simplest preferred fix: do not advertise gzip unless decoding is implemented; or
2. implement bounded gzip decoding with both compressed and decompressed size
   limits.

Add tests for Content-Encoding behavior.

### P11-ISSUE-104 — Configured redirect limit is not enforced

Severity: **HIGH**

Observed implementation:

`SecHttpConfig.max_redirects` exists and is validated, but the value is not wired
into `_AllowlistedRedirectHandler`.

The code validates redirect hosts, which is good, but the configured redirect-count
contract is currently ineffective.

Required fix:

- enforce the configured redirect limit;
- preserve per-hop SEC host/path validation;
- add tests for:
  - allowed SEC redirect;
  - non-SEC redirect rejection;
  - redirect chain exceeding configured maximum.

Also bound HTTP error-body reads; the current `HTTPError.read()` path is not
limited by `max_bytes`.

### P11-ISSUE-105 — Evidence locator/block identity is not actually round-trip validated

Severity: **BLOCKING**

Observed implementation:

- page blocks receive `block_id` from block locator/text;
- fact Evidence independently sets `block_id = fragment_hash` for the iXBRL fact
  locator/value;
- that Evidence block ID is not guaranteed to exist in
  `pages[].blocks[].block_id`;
- P7 considers a DOM locator valid if it merely starts with `/`.

Impact:

The design requires deterministic:

```text
RawFact
→ Evidence
→ source block / DOM node
→ immutable source member
```

Current validation proves field shape, not resolvability.

Required fix:

- make Evidence reference a real normalized source block, or explicitly model the
  fact-node locator separately from its enclosing block;
- P7 must verify the block reference exists;
- P7 must verify the DOM/source locator can be resolved against the exact immutable
  source member;
- add positive and deliberately corrupted locator tests.

### P11-ISSUE-106 — P8 does not revalidate immutable SEC source package/member bytes

Severity: **HIGH**

Observed implementation:

P8 SEC loading validates parsed artifact hashes and validation artifact hashes, but
the SEC catalog entry contains only the parsed artifact directory/package SHA.
`_load_sec_bundle()` does not load/verify the immutable raw package before serving
facts/evidence.

Impact:

A raw SEC member can be deleted or modified after ingest while P8 continues serving
evidence from derived artifacts. This conflicts with the P11 design requirement
that Evidence be tied to verified immutable source bytes.

Required fix:

At SEC bundle load, verify the canonical raw package for `package_sha256`, or use
an equivalent project-root-relative trusted package locator.

The verification must include:

- package manifest identity;
- member SHA/size;
- every evidence member SHA is present in the verified package.

Add a negative test:

```text
ingest
→ tamper/delete raw SEC member
→ P8 get_fact/get_evidence must fail closed
```

## 3. Important non-blocking design gap

### P11-ISSUE-107 — XML XBRL facts are not extracted; only contexts/units are read

Severity: **MEDIUM / MUST BE RESOLVED BEFORE ACCEPTANCE SCOPE FREEZE**

`_contexts_and_units()` reads contexts/units from filing-local XML members, but
`_facts()` extracts facts only from Inline XBRL nodes in the primary HTML.

This is acceptable only if P11 v1 explicitly freezes its positive parsing scope to
Inline-XBRL periodic filings.

If P11 claims general `HTML / Inline XBRL / XBRL` support, then filing-local XBRL
instance facts must also be extracted with source-aware Evidence.

Required action:

Either:

- implement XML instance fact extraction; or
- narrow the P11 acceptance scope/design truth to Inline-XBRL filings and make
  unsupported non-inline XBRL fail closed rather than PASS.

## 4. Review observations that passed

The following design areas are directionally correct in the reviewed candidate:

- `SUPPORTED_MARKETS` remains CN/HK;
- US is behind explicit development gating;
- CIK-based US identity exists;
- accession is retained as SEC filing identity;
- callers cannot supply arbitrary SEC URLs through CLI;
- SEC host/path allowlisting exists;
- User-Agent contact is environment/config injected;
- 8 req/s shared limiter exists;
- bounded retries exist;
- package/member SHA identities exist;
- package storage is content-addressed and immutable-oriented;
- accession drift detection exists;
- Registry additions are additive and legacy rows are not rewritten;
- CN/HK period set remains unchanged while US adds Q2;
- amendment presence fails closed;
- 20-F / 40-F annual discovery exists;
- 6-K quarterly auto-mapping is not guessed;
- P8 exact public tool families remain unchanged;
- MCP does not perform SEC acquisition;
- remote AI/API functionality was not introduced.

These PASS observations do not override the blocking issues above.

## 5. Test-quality assessment

Developer tests are useful but currently overfit simplified calendar-year and
synthetic HTML fixtures.

The reported:

- P11 focused: 25 passed;
- full suite: 555 passed;
- CN/HK focused regression: 96 passed;

are accepted as developer evidence, but they are not sufficient for formal
acceptance because the current test set does not detect the blocking findings in
this review.

## 6. Verdict

```text
CODE REVIEW: CHANGES_REQUIRED
FORMAL TEST PLAN: NOT ISSUED
FORMAL ACCEPTANCE: NOT STARTED
```

Do not start the formal acceptance run on candidate
`529376cc084bd9990c144102fa723822b5229e1a`.

## 7. Required next action

PC Agent performs **one repair pass** covering P11-ISSUE-101 through 106.

P11-ISSUE-107 must either be implemented or explicitly resolved through a narrow
accepted scope/design amendment.

After repair:

1. run focused developer tests;
2. run full CN/HK/full-unit regression;
3. update development evidence;
4. push a new exact production candidate SHA;
5. stop.

ChatGPT will review only the new exact candidate.

A formal test plan will be created only after `REVIEW_PASS`.
