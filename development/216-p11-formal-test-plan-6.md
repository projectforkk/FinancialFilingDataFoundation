# 216 — P11 US SEC Provider Formal Test Plan 6

Status: **FORMAL_TEST_PLAN_FROZEN / EXECUTION_NOT_YET_AUTHORIZED**

Plan owner: ChatGPT independent review
Execution owner: Acceptance/Test Agent
Final verdict owner: ChatGPT independent Formal Acceptance Review

This is a fresh full Formal Test cycle for exact production candidate
`7aac34e763b4c9caac24489eb049aa3dc6efb026`.

Formal Test 5 is historical evidence only and must not be resumed.

## 1. Exact authority

Repository:

`projectforkk/FinancialFilingDataFoundation`

Authoritative lineage:

`reconcile/p11-140-143-local-chain`

Design 40 freeze:

`db8edabb2630549e2d75a5becaccb15cb1c53749`

Design 40 review:

`762bc471c3fe553496a7ecef73450013d49fd189`

Development authorization:

`30a34a7e68894cea6cbdea9cbf9bd037e9d97def`

Frozen production candidate:

`7aac34e763b4c9caac24489eb049aa3dc6efb026`

Development evidence:

`2c68f85199e6e77dc30c37e5e6eb5515b5bd6fe2`

Fresh Full Exact-Candidate Review 9:

`development/215-p11-fresh-full-exact-candidate-review-9.md = REVIEW_PASS`

Review commit:

`5fe0bc139f9a2b0475a1912c65f40008e84572f4`

Any production/test change after the frozen candidate invalidates this plan.

## 2. Frozen version contract

Formal execution must independently confirm:

```text
REGISTRY_SCHEMA_VERSION = 1
SEC_REGISTRY_SCHEMA_VERSION = 5

PACKAGE_MANIFEST_SCHEMA = p11-sec-package-v1
SEC_SOURCE_CONTAINER_SCHEMA = p11-sec-source-container-v1
SEC_PACKAGE_SOURCE_PROVENANCE_SCHEMA = p11-sec-package-source-v1

SEC_DISCOVERY_SCHEMA = p11-sec-discovery-v1
VIRTUAL_HTML_NORMALIZER_VERSION = VIRTUAL_HTML_V6
SEC_ARTIFACT_SCHEMA = p11-sec-artifacts-v2
SEC_VALIDATION_SCHEMA = p11-sec-validation-v4
```

No new P11 reason code is authorized.

## 3. Formal execution governance

The Acceptance/Test Agent may create acceptance-only harnesses, disposable
workspaces, copied registries, temporary files and raw logs outside tracked
production/test paths.

It must not modify:

- `src/`;
- `tests/`;
- design files;
- dependency/lock/runtime files;
- production configuration.

Any required code/test repair means:

```text
EXECUTION_FAIL
STOP
RETURN TO NEW CANDIDATE CYCLE
```

Do not patch production during Formal Test.

## 4. Environment

Recommended short paths:

```text
worktree:
D:\Codex\FinancialFilingDataFoundation\worktrees\active\p11-sec-rebuild-development

formal root:
D:\ffdf-p11-ft6

pytest temp:
D:\t\p11f6
```

`FFDF_P11_US_DEV` must remain absent.

Record only whether SEC contact configuration is present; never record its
value.

## 5. Result classification

Each gate:

`PASS / FAIL / BLOCKED`

Overall:

- required assertion failure → `EXECUTION_FAIL`;
- required production/test repair → `EXECUTION_FAIL`;
- external SEC/contact unavailability → `EXECUTION_BLOCKED`;
- every required gate passes → `EXECUTION_PASS`.

Execution PASS is not Formal Acceptance PASS.

# FT-00 — Candidate freeze and drift boundary

Verify:

- exact candidate exists;
- candidate is ancestor of HEAD;
- candidate → HEAD tracked changes are documentation/governance only;
- worktree clean;
- `git diff --check` clean;
- frozen constants match §2;
- `FFDF_P11_US_DEV` absent.

Any post-candidate source/test/dependency/runtime drift = BLOCKED.

# FT-01 — Deterministic full regression

Run with short basetemp:

```powershell
python -m pytest -q tests/unit/us_sec/test_issue148.py --basetemp D:\t\p11f6\i148
python -m pytest -q tests/unit/us_sec/test_issue147.py tests/unit/us_sec/test_issue146.py --basetemp D:\t\p11f6\i146148
python -m pytest -q tests/unit/us_sec/test_repair_140_143.py tests/unit/us_sec/test_corrected_repair.py tests/unit/us_sec/test_validation_p8.py --basetemp D:\t\p11f6\repair
python -m pytest -q tests/unit/us_sec --basetemp D:\t\p11f6\us
python -m pytest -q tests/unit/mcp --basetemp D:\t\p11f6\mcp
python -m pytest -q tests/unit/acquisition tests/unit/identity tests/unit/validation tests/unit/registry tests/unit/mcp tests/unit/research tests/unit/review --basetemp D:\t\p11f6\p0p10
python -m pytest -q tests/unit --basetemp D:\t\p11f6\unit
python -m compileall -q src tests
git diff --check
```

Development references:

```text
T148 focused = 20
ISSUE-146/147/148 focused = 39
US SEC = 283
MCP-focused = 65
full unit = 813
```

Record exact counts and all skips.

# FT-02 — ISSUE-147 complete acceptance-only matrix

This gate corrects the Formal-Test-5 evidence defect.

Use an acceptance-only harness independent from tracked unit tests.

Prove all nine cases:

1. identical ticker-map source bytes and SHA + retrieval time T1/T2 →
   distinct snapshot IDs;
2. both immutable observation files coexist;
3. distinct observations do not trigger SOURCE_DRIFT;
4. independently recompute each snapshot ID from canonical JSON and prove exact
   equality;
5. exact same snapshot ID path with conflicting canonical payload →
   `P11_SOURCE_DRIFT`;
6. invalid and timezone-naive `retrieved_at` →
   `P11_TICKER_SNAPSHOT_INVALID`;
7. source bytes tampered without matching SHA → fail closed;
8. derivative mapping tampered while source bytes valid → fail closed;
9. current observation path/snapshot-ID mismatch → fail closed.

Record all exact IDs, timestamps, source SHA values and reason codes.

Unit-test output is not a substitute.

# FT-03 — Complete-submission URL and container identity

Acceptance-only proof:

- exact URL from CIK/accession;
- HTTPS/sec.gov allowlist;
- no query/fragment/path escape;
- exact source bytes hashed before extraction;
- source-container SHA/length/path match;
- schema = `p11-sec-source-container-v1`;
- atomic persistence/idempotent reload;
- tampered body, metadata, path SHA, CIK/accession or source URL fail closed;
- package/container size limit enforced.

# FT-04 — Strict SGML inventory and exact payload slicing

Acceptance-only fixtures must prove:

- repeated DOCUMENT parsing;
- required TYPE/SEQUENCE/FILENAME/TEXT;
- missing/duplicate structural fields fail;
- malformed/overlapping DOCUMENT/TEXT fail;
- duplicate normalized filename fails;
- unsafe filename fails;
- CRLF and LF structural tag lines;
- TEXT payload exact bytes;
- XML envelope exact inner bytes;
- XBRL envelope exact inner bytes;
- internal whitespace/line endings/entities untouched;
- payload offsets replay exact original bytes;
- unsupported required binary/UUencoded envelope fails closed.

# FT-05 — Canonical active-content boundary

Prove:

- canonical complete-submission-derived primary containing SCRIPT fails;
- APPLET fails;
- OBJECT fails;
- IFRAME fails;
- EMBED fails;
- no stripping/normalization occurs;
- direct-member diagnostic response with injected script is not package input.

# FT-06 — Package selection and request boundary

Acceptance-only transport must prove normal package acquisition performs:

```text
complete submission = 1
archive index = 0
individual package members = 0
unrelated static/browser assets = 0
```

Require primary match exactly current discovery `primaryDocument`.

Required XBRL/schema/linkbase/FilingSummary selection must come only from the
complete-submission inventory.

Unrelated exhibits remain excluded.

# FT-07 — Package-source provenance artifact

Independently verify:

- schema `p11-sec-package-source-v1`;
- canonical provenance SHA recomputation;
- exact package SHA/CIK/accession;
- exact source-container metadata;
- sorted complete member locator set;
- exact public member URLs;
- document index/type/sequence/filename;
- payload start/end/envelope;
- member SHA/length;
- immutable path identity;
- unexpected/missing top-level fields fail closed.

# FT-08 — Full provenance replay/tamper matrix

From persisted complete-submission bytes replay every selected package member.

Tamper independently:

- provenance SHA;
- package SHA;
- CIK;
- accession;
- container SHA;
- container metadata;
- relative name;
- role;
- public URL;
- document index;
- document type;
- document sequence;
- filename;
- payload start;
- payload end;
- envelope;
- member SHA;
- member length;
- package member bytes.

Every mismatch must fail closed with package/provenance/source reason consistent
with Design 40.

# FT-09 — Legacy package migration

Construct:

A. historical unattested package only;

B. historical unattested package + current attested package with different SHA;

C. historical package whose member bytes exactly reproduce current container.

Require:

- A is audit-readable but cannot PARSE_LOCAL/REVALIDATE_LOCAL/REUSE_DATA;
- B both package directories remain immutable and only current attested package
  is plannable;
- C package directory/manifest bytes remain unchanged while external
  provenance is added;
- no destructive migration or overwrite.

# FT-10 — Current source conflicts

Acceptance-only checks:

- same accession + existing current container A + new current container B →
  `P11_SOURCE_DRIFT`;
- same container SHA + deterministic extraction producing another package SHA →
  `P11_PROVENANCE_MISMATCH`;
- same package/container + different extraction/provenance →
  `P11_PROVENANCE_MISMATCH`;
- equivalent repeated attestation is idempotent.

# FT-11 — Registry v5

Verify from a true v4 fixture:

- v4→v5 additive migration;
- all v4 source/binding/parsed/discovery rows preserved;
- new three tables exactly present;
- v5 reopen idempotent;
- source/provenance/locator round-trip;
- Registry provenance replay equality;
- global `PRAGMA user_version=1` unchanged;
- CN/HK rows unchanged;
- future SEC schema fails before mutation.

# FT-12 — validation-v4 / no-v3-fallback

Prove:

- path is current versioned validation-v4 path;
- validation report binds package SHA and provenance SHA;
- source provenance replay happens before current PASS;
- missing provenance → blocking;
- corrupt provenance/container → blocking;
- validation-v3 only → no current reuse;
- no v4→v3 fallback;
- validation-v3 historical bytes remain unchanged;
- same-byte newly attested package may validate existing V6/v2 parsed data with
  parser count 0.

# FT-13 — Planner and incremental reuse

Prove current-source-attested package requirement for all local actions.

Required states:

- unattested package only → DISCOVER_AND_ACQUIRE;
- attested package + no parsed → PARSE_LOCAL;
- attested package + compatible parsed + no v4 → REVALIDATE_LOCAL;
- attested package + compatible parsed + reusable v4 → REUSE_DATA;
- provenance SHA mismatch in validation → no REUSE_DATA;
- corrupt v4 → fail closed;
- amendment/conflict → REVIEW_REQUIRED.

# FT-14 — P8/MCP provenance/no-network

Use a current attested package.

Exercise all supported P8/MCP SEC read paths.

Require:

- raw package provenance verification;
- package-source provenance replay;
- Registry v5 provenance agreement;
- catalog provenance SHA agreement;
- validation-v4 provenance SHA agreement;
- no SEC network calls.

Negative cases: missing provenance, tampered container/locator, catalog mismatch,
validation mismatch and validation-v3-only all fail closed.

# FT-15 — Fresh live Apple FY2025 root A

Use brand-new formal root A.

Ticker-based acquire/ingest.

Expected accession:

`0000320193-25-000079`

unless independently classified external fixture drift.

Record:

- ticker snapshot identity;
- discovery observation identity;
- exact complete-submission URL;
- source-container SHA and byte length;
- full SGML selected document inventory;
- provenance SHA;
- every selected locator;
- every member SHA/length;
- package SHA;
- request counts/classification;
- parser action/count;
- validation-v4 path/status;
- Registry v5 state;
- P8 result;
- research_ready.

Required request classification:

```text
ticker map = 1 per ticker resolution
current submissions = 1 per discovery
complete submission = 1 for fresh acquisition
archive index = 0
individual member = 0
static/browser = 0
```

# FT-16 — Independent fresh Apple FY2025 root B

Use a completely independent empty root B.

Repeat the same ticker-based fresh acquisition/ingest.

Require exact equality A vs B:

```text
accession
complete-submission URL
complete-submission SHA
complete-submission byte length
provenance SHA
selected member set
every locator semantic field
every member SHA/length
package SHA
```

Any unexplained difference is FAIL.

# FT-17 — Direct-member delivery diagnostic isolation

After FT-15/16 package identity is frozen, optionally fetch the public Apple
primary member URL twice as an acceptance diagnostic.

If bytes differ or contain delivery-layer active content, record the diagnostic
SHA/length difference.

Regardless of whether they differ:

- those bytes must not appear in source-container storage;
- must not alter any member SHA;
- must not alter package SHA;
- must not alter provenance SHA;
- must not alter validation-v4 identity.

If diagnostic access is unavailable, this sub-diagnostic may be marked
NOT_OBSERVED while the isolation proof must still pass via transport
instrumentation.

# FT-18 — Apple repeat online reuse

On root A after current ingestion:

run online ingest again.

Require:

- current ticker map/discovery refresh;
- no complete-submission redownload if planner is REUSE_DATA;
- parser rerun = 0;
- current provenance unchanged;
- package/member/container bytes unchanged;
- validation-v4 refresh remains bound to same provenance;
- research_ready=true;
- local status performs zero network calls.

# FT-19 — Apple FY2025 Q3

Expected accession:

`0000320193-25-000073`

Require complete-submission source, provenance replay, validation-v4,
research_ready, request classification with no index/member/static fetch.

Exercise P8/MCP no-network.

# FT-20 — Toyota FY2025 20-F and 6-K guard

Expected FY accession:

`0001193125-25-142326`

Require complete-submission source, provenance replay, validation-v4,
research_ready and P8 no-network.

Then verify current 6-K/6-K-A filings are not guessed into a quarterly slot.

# FT-21 — Kellanova amendment conflict

Explicit CIK `0000055067`, FY2024.

Require controlled `P11_AMENDED_VARIANT_PRESENT`/review outcome.

Ticker-map fetch count = 0.

No package acquisition and no research-ready publication.

# FT-22 — ISSUE-142/143/145/146 regression

Re-run acceptance-level checks for:

- strict history descriptor validation before fetch;
- exact date semantics;
- source-set identity;
- immutable context/unit replay;
- Raw Fact source binding;
- wrong-role and multi-root failures;
- validation migration/revalidation;
- corrupt current validation fail closed;
- parser=0 for revalidation;
- no legacy fallback.

# FT-23 — CN/HK and P0-P10 preservation

Run P0-P10 focused regression and representative accepted CN/HK operational/MCP
smoke.

No accepted CN/HK source or Registry semantic mutation.

# FT-24 — Final drift and evidence integrity

Before evidence creation:

```powershell
git status --short
git diff --check
git diff --name-status 7aac34e763b4c9caac24489eb049aa3dc6efb026..HEAD
```

All post-candidate tracked changes must be documentation/governance only.

## 6. Formal evidence

After all required gates pass, create exactly:

`development/218-p11-formal-test-evidence-6.md`

Do not use 217 for evidence; 217 is reserved for execution authorization.

Evidence must include:

- all exact authority SHAs;
- FT-00..FT-24 verdicts;
- commands/exit codes/pass/fail/skip counts;
- complete ISSUE-147 nine-case acceptance matrix;
- source-container identity/tamper receipts;
- SGML locator extraction receipts;
- active-content acceptance matrix;
- package request classification;
- full package-source provenance replay/tamper matrix;
- migration coexistence receipts;
- Registry v5 migration evidence;
- validation-v4/no-v3-fallback evidence;
- planner-state matrix;
- P8/MCP no-network evidence;
- Apple root A and B complete identities and equality comparison;
- direct-member diagnostic isolation result;
- repeat reuse result;
- Apple Q3 / Toyota / Kellanova live results;
- CN/HK/P0-P10 preservation;
- final documentation-only drift proof.

Raw logs/harnesses remain outside Git.

## 7. Stop boundary

After a documentation-only evidence commit and normal push:

```text
STOP FOR CHATGPT INDEPENDENT FORMAL ACCEPTANCE REVIEW 6
```

Do not modify production/test code.
Do not merge main.
Do not declare Formal Acceptance.
Do not declare P11 DONE.
