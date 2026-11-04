# 27 — P11 US SEC Provider Implementation Plan

Status: **DESIGN BASELINE CANDIDATE / PRODUCTION CLOSED**

Detailed design:
`design/26-p11-sec-provider-design.md`

Source-neutral contract:
`design/30-parsed-financial-document-v2-contract.md`

Acceptance baseline:
`acceptance/41-p11-acceptance-instruction.md`

Authorization:
`development/143-p11-design-authorization.md`

## P11-A — Design Baseline

Deliver:

- environment/interface audit;
- design/30 v2 contract;
- design/26 detailed design;
- design/27 implementation plan;
- acceptance/41 baseline;
- status/index/master/roadmap reconciliation;
- UTF-8 no BOM;
- git diff --check;
- design review;
- commit/push.

Gate:

`P11_READY_FOR_DEVELOPMENT`

No production code before PASS + explicit development authorization.

## P11-B — Environment / SEC Runtime Probe

Read-only / isolated probe only.

Confirm:

- main Python architecture/version;
- project-local Python 3.12 AMD64 viability;
- Arelle candidate exact version and package provenance;
- lxml wheel viability;
- runtime lock strategy;
- SEC TLS/network reachability;
- explicit User-Agent configuration path;
- no root/global Python mutation;
- all temp/runtime paths under project root.

No permanent runtime install until this gate is separately authorized.

Evidence:
`development/<next>-p11-environment-runtime-probe.md`

## P11-C — Identity / Period Contract

Implement only:

- US market support;
- Q2 support;
- CIK normalization/validation;
- periodic form normalization;
- amended form normalization;
- supplemental accession identity model;
- deterministic accession helpers.

Must retain CN/HK behavior byte/semantic compatible.

Focused tests:

1. CN/HK unchanged;
2. US CompanyRef with zero-padded CIK;
3. invalid CIK rejected;
4. Q2 valid for US;
5. H1 remains valid for existing markets;
6. 10-K/A normalization;
7. 10-Q/A normalization;
8. 20-F/A normalization;
9. 40-F/A normalization;
10. 8-K/6-K supplemental identity;
11. no forced 8-K/6-K periodic slot.

STOP before acquisition changes if identity design assumption fails.

## P11-D — SEC HTTP / Discovery Client

**Preimplementation Design-First freeze required before any P11-D code.**

That amendment must freeze exact:

- User-Agent grammar/config source;
- timeout values;
- response-size limits by endpoint/content class;
- retry counts/backoff ceilings;
- redirect count;
- cross-process aggregate rate-gate lock/state format;
- failure recovery for stale/crashed lock holder.

The implementation must use one project-root-shared no-burst limiter with >=125 ms between outbound SEC request starts, giving <=8 requests/sec aggregate inside the supported single-installation boundary. If shared coordination is unavailable, block with `P11_RATE_LIMIT_SCOPE_UNSAFE`.

Implement dedicated SEC client contract:

- Submissions API;
- historical shard following;
- ticker lookup helper;
- strict HTTPS/host rules;
- explicit User-Agent;
- rate limiter;
- bounded timeout/retry;
- redirect revalidation;
- response-size caps;
- structured deterministic errors.

No package writes yet except isolated test fixtures if explicitly authorized.

Focused tests include:

- no User-Agent => block;
- >10 rps impossible;
- 429 Retry-After;
- 404 no retry storm;
- 5xx bounded retry;
- redirect to non-allowlisted host blocked;
- file:// rejected;
- malformed JSON rejected;
- current/historical submissions merged deterministically.

## P11-E — SEC Package Store

Implement:

- content-addressed assets;
- source package manifest;
- atomic staging/commit;
- exact SHA/size verification;
- package hash;
- receipt;
- source drift preservation;
- path traversal rejection;
- package/asset count/size caps.

Do not modify P2 RawDocumentStore behavior.

Focused tests:

- exact-byte identity;
- exact known `p11-sec-source-package-identity-v1` hash fixture;
- asset caller/order independence under canonical sort;
- excluded URL/media/local-path/timestamp/HTTP metadata does not change package identity;
- changed role/hash/file_name/size/dependency topology does change package identity;
- project-root-relative POSIX `local_content_path` round-trip;
- absolute/drive-relative/traversal local path reject;
- duplicate asset SHA reuse;
- same accession/new bytes => new package;
- existing package collision mismatch blocked;
- atomic failure leaves no partial accepted package;
- path escape blocked;
- timestamps excluded from package identity.

## P11-F — Period Binding / Registry Integration

Implement provisional discovery -> final identity binding.

Extract/confirm:

- DocumentFiscalYearFocus;
- DocumentFiscalPeriodFocus;
- form/report date consistency.

Register primary asset only after final periodic binding.

Rules tested:

- 10-K FY;
- 10-Q Q1/Q2/Q3;
- Q2 never H1;
- 20-F/40-F FY;
- DEI conflict => review/block;
- amendment remains distinct accession variant;
- multiple variants do not silently canonicalize.

## P11-G — SEC Runtime / Parser

Create isolated P11 runtime only after P11-B PASS.

**Before any P11-G parser production code, perform a Design-First parser-contract freeze.**

It must record:

- exact runtime Python/version/architecture;
- exact Arelle/parser version and dependency lock;
- exact Inline XBRL transformation registry behavior;
- `continuedAt` and `ix:exclude` behavior;
- canonical QName/DOM/XML locator golden fixtures;
- exact raw_value whitespace rule fixtures;
- exact parsed-decimal golden cases for format/scale/sign/nil;
- external taxonomy resolution/cache behavior;
- proof that deterministic parse performs no unrecorded network.

Candidate:

- Python 3.12 AMD64;
- arelle-release pinned;
- lxml pinned transitively/explicitly;
- lock file with hashes;
- source/runtime descriptor.

Parser operations:

- exact primary HTML/iXBRL parse;
- filing-local XML/XBRL parse;
- source segment extraction;
- section extraction;
- DOM table extraction;
- raw iXBRL/XBRL fact extraction;
- Arelle/local XBRL validation where frozen.

No network during deterministic parse.

Focused tests use local frozen fixtures.

## P11-H — ParsedFinancialDocument v2 Writer/Loader

Implement design/30.

Required artifacts:

- manifest;
- document;
- source assets;
- segments;
- sections;
- tables;
- raw facts;
- evidence;
- validation.

Loaders must verify:

- schema;
- counts;
- hashes;
- IDs;
- locator integrity;
- asset references;
- package/document identity.

No v1 masquerading.

## P11-I — SEC Validation

Implement deterministic validation layers:

1. source/package integrity;
2. CIK/accession/form/report-date consistency;
3. DEI identity/period consistency;
4. fact/context/unit integrity;
5. duplicate/conflicting facts;
6. parser/Arelle validation mapping;
7. completeness signals;
8. compatibility/reuse status.

Companyfacts cross-check is optional/auxiliary and cannot turn invalid filing evidence into PASS.

## P11-J — Supplemental 8-K / 6-K

Implement accession-bound supplemental ingest.

No periodic slot forcing.

Primary document mandatory.

Requested exhibit acquisition is explicit and allowlisted by filing directory metadata.

Tests:

- 8-K primary only;
- 8-K/A;
- 6-K;
- requested exhibit;
- unrelated exhibit not downloaded by default;
- supplemental export retains accession identity.

## P11-K — Registry / Parsed Data / Incremental Reuse

Integrate periodic SEC v2 results into existing registry with additive compatibility.

Reuse requires:

- exact document/package identity;
- parser version compatible;
- schema v2 compatible;
- PASS;
- blocking issue count 0;
- no source drift.

Existing CN/HK reuse semantics unchanged.

## P11-L — Full Regression / Security

Run:

- P11 focused;
- full P0-P11 unit;
- compile/import;
- git diff --check;
- CN/HK acquisition regression;
- P8/P9/P10 zero unintended diff;
- dependency/runtime audit;
- runtime lock verification;
- arbitrary network/path negative scan;
- no remote AI.

Gate: PASS.

## P11-M — Live SEC Runs

At minimum:

1. domestic 10-K Inline XBRL;
2. domestic 10-Q Inline XBRL;
3. Q2 period case;
4. foreign issuer 20-F or 40-F;
5. supplemental 8-K or 6-K;
6. amendment;
7. custom taxonomy fact.

For each live run:

- official SEC discovery;
- exact source package;
- exact hashes;
- v2 parse;
- evidence link;
- validation result;
- registry/reuse behavior where periodic;
- request count/rate;
- source bytes immutable.

No live test may exceed SEC fair-access ceiling.

## P11-N — Negative Capability Gates

Must prove:

- ticker/CIK ambiguity => explicit block/review;
- missing filing => P11_FILING_NOT_FOUND;
- missing User-Agent => P11_USER_AGENT_REQUIRED;
- hostile redirect => P11_REDIRECT_NOT_ALLOWED;
- oversized response => P11_RESPONSE_TOO_LARGE;
- source-content drift => P11_SOURCE_CONTENT_DRIFT;
- missing dependency => P11_DEPENDENCY_UNRESOLVED;
- visual-only interpretation => P11_VISUAL_RENDERING_REQUIRED;
- period conflict => P11_PERIOD_CONFLICT;
- custom taxonomy not silently dropped;
- companyfacts mismatch cannot override filing source.

## P11-O — Formal Code Review

Fresh detached exact-candidate worktree.

Review:

- design baseline;
- identity/period semantics;
- official-source boundary;
- security/fair access;
- package identity;
- parser evidence integrity;
- v2 contract;
- no synthetic PDF evidence;
- CN/HK regression;
- P8/P9/P10 unchanged;
- runtime lock;
- live/negative evidence.

Verdict:
PASS / FAIL / BLOCKED.

## P11-P — Acceptance Freeze

Freeze:

- exact design baseline;
- exact production candidate;
- formal review PASS;
- runtime lock;
- official source fixtures;
- live accession targets;
- expected source/package hashes where stable;
- test commands;
- security limits;
- basetemp paths;
- accepted P0-P10 immutability manifest.

Any production/design/acceptance-package change invalidates freeze.

## P11-Q — Independent Acceptance

Fresh detached worktree.

Must independently repeat:

- focused/full regression;
- identity/period cases;
- SEC package acquisition from official endpoints;
- v2 parse/evidence;
- periodic live cases;
- supplemental case;
- amendment case;
- custom taxonomy preservation;
- negative security/capability gates;
- immutable P0-P10 base.

No production/test/design edits during acceptance.

## P11-R — Closeout

Only after Independent Acceptance PASS:

- acceptance result;
- fresh integration branch from current accepted main;
- post-merge regression;
- final main verification;
- P11_DONE governance sync.

P11 closeout does not automatically authorize:

- P8/P10 SEC query compatibility extension;
- Research MCP;
- Semantic Resolver;
- later phase production.

## Issue Rule

Any material issue:

```text
STOP
→ facts/root cause
→ amend design/26 + design/27 + acceptance/41 (+ design/30 if contract affected)
→ commit/push new baseline
→ invalidate affected evidence
→ reauthorize
```

No code-first/design-later.
