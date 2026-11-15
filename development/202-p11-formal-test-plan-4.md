# 202 — P11 US SEC Provider Formal Test Plan 4

Status: **FORMAL_TEST_PLAN_FROZEN / EXECUTION_NOT_YET_AUTHORIZED**

Date: 2026-11-16

Plan owner: ChatGPT independent review
Execution owner: PC Agent / local Windows environment
Final result reviewer: ChatGPT independent acceptance review

This plan is a new formal acceptance cycle for the exact Review-7 production candidate. Historical P11 formal plans 156, 170, 175, and 183 are audit history only and are not execution authority for this cycle.

## 1. Exact acceptance authority

Repository:

`projectforkk/FinancialFilingDataFoundation`

Authoritative remote lineage:

`reconcile/p11-140-143-local-chain`

Current design authority chain:

- `design/26-p11-sec-provider-design.md`
- `design/27-p11-implementation-plan.md`
- `design/32-p11-us-scope-reopening.md`
- `design/33-p11-post-acceptance-design-correction.md`
- `design/34-p11-explicit-6k-scope-correction.md`
- `design/35-p11-repair-140-143-design-correction.md`
- `design/36-p11-review5-trust-boundary-correction.md`
- `design/37-p11-review5-freeze-consistency-and-raw-fact-binding.md`
- `design/38-p11-review6-revalidation-planner-correction.md`

Exact final Design 38 freeze:

`92af6205eb8e090994dcece68850eddcd4232392`

Exact production candidate under Formal Test:

`6eaace08c9ba5fb26809a7e02de5835123fb667a`

Development evidence:

`development/200-p11-review6-issue146-evidence.md`

Development evidence commit:

`5ce97e18456c9e877c223df7abf01eec53e1f3ad`

Fresh Full Exact-Candidate Review:

`development/201-p11-fresh-full-exact-candidate-review-7.md = REVIEW_PASS`

Review commit:

`50baac22baf40b29fd08224b883c7b43f06f7736`

The exact production/test bytes under acceptance are frozen at
`6eaace08c9ba5fb26809a7e02de5835123fb667a`.

Any production/test source change after that SHA invalidates this plan.

## 2. Frozen version and reason contract

Formal execution must independently confirm:

```text
REGISTRY_SCHEMA_VERSION = 1
SEC_REGISTRY_SCHEMA_VERSION = 4
SEC_DISCOVERY_SCHEMA = p11-sec-discovery-v1
VIRTUAL_HTML_NORMALIZER_VERSION = VIRTUAL_HTML_V6
SEC_ARTIFACT_SCHEMA = p11-sec-artifacts-v2
SEC_VALIDATION_SCHEMA = p11-sec-validation-v3
```

The blocking source-semantic reason remains:

`P11_RAW_FACT_SOURCE_MISMATCH`

No formal harness may alter these values.

## 3. Current corrected issue matrix

Formal acceptance must independently verify:

```text
ISSUE-140 = compatibility identity / V6 preservation
ISSUE-141 = namespace-authentic semantic references
ISSUE-142 = complete fail-closed history inventory and minimal source selection
ISSUE-143 = immutable source-node fact/context/unit replay
ISSUE-144 = governance correction
ISSUE-145 = full Raw Fact/Evidence source-semantic binding
ISSUE-146 = REVALIDATE_LOCAL planner and validation-v3 migration state
```

The formal run must not rely solely on development test counts.

## 4. Formal execution governance

Formal execution may create acceptance-only harnesses, temporary SQLite databases, copied artifacts, transport wrappers, and raw logs under the isolated acceptance workspace.

It must not modify tracked:

- `src/`;
- `tests/`;
- dependency/lock files;
- runtime production configuration;
- design files.

If any required gate reveals a production/test defect:

```text
EXECUTION_FAIL
STOP
RETURN TO A NEW CANDIDATE CYCLE
```

Do not patch production code during Formal Test.

Forbidden:

- merge main;
- rebase/history rewrite;
- force push / force-with-lease;
- destructive reset/clean;
- amend the candidate;
- weaken expected outcomes;
- enable US using `FFDF_P11_US_DEV`;
- declare ACCEPTANCE_PASS;
- declare P11 DONE.

## 5. Formal acceptance workspace

Use the active P11 worktree source.

Recommended Windows paths:

```text
repository root:
D:\Codex\FinancialFilingDataFoundation

active worktree:
D:\Codex\FinancialFilingDataFoundation\worktrees\active\p11-sec-rebuild-development

formal root:
D:\ffdf-p11-ft4

pytest basetemp:
D:\t\p11f4
```

Use a short basetemp because the exact candidate has already demonstrated Windows path-length sensitivity with long temporary roots.

Before execution:

```powershell
Set-Location 'D:\Codex\FinancialFilingDataFoundation\worktrees\active\p11-sec-rebuild-development'
$env:FFDF_ROOT='D:\ffdf-p11-ft4'
$env:PYTHONPATH=(Join-Path (Get-Location) 'src')
$env:TEMP='D:\t\p11f4'
$env:TMP='D:\t\p11f4'
Remove-Item Env:FFDF_P11_US_DEV -ErrorAction SilentlyContinue
```

Record Windows version, Python version, pytest version, branch, HEAD, candidate SHA, Formal Test Plan SHA, FFDF_ROOT, `FFDF_P11_US_DEV present = NO`, and `FFDF_SEC_CONTACT_EMAIL configured = YES/NO` only.

Never record the SEC contact value.

## 6. Live network gate

Required live SEC gates use the operator-configured SEC contact identity.

If `FFDF_SEC_CONTACT_EMAIL` is absent or invalid:

- execute every offline gate;
- mark required live gates BLOCKED;
- overall result = `EXECUTION_BLOCKED`.

If SEC is externally unavailable/rate-limited while production HTTP behavior remains correct, record controlled reason and attempt counts and mark affected live gates BLOCKED.

If current official metadata for a frozen live slot has legitimately changed:

`EXTERNAL_FIXTURE_DRIFT`

Record observed metadata and block that gate pending plan refresh. Do not alter the expected slot during execution.

## 7. Frozen live slots

### LIVE-A — Apple FY2025 10-K

```text
CIK = 0000320193
ticker = AAPL
fiscal_year = 2025
period = FY
form = 10-K
expected accession = 0000320193-25-000079
expected report period = 2025-09-27
expected primary document = aapl-20250927.htm
```

### LIVE-B — Apple FY2025 Q3 10-Q

```text
CIK = 0000320193
ticker = AAPL
fiscal_year = 2025
period = Q3
form = 10-Q
expected accession = 0000320193-25-000073
expected report period = 2025-06-28
expected primary document = aapl-20250628.htm
```

### LIVE-C — Toyota FY2025 20-F

```text
CIK = 0001094517
ticker = TM
fiscal_year = 2025
period = FY
form = 20-F
expected accession = 0001193125-25-142326
expected report period = 2025-03-31
expected primary document = d925022d20f.htm
```

### LIVE-D — Kellanova FY2024 amendment conflict

```text
CIK = 0000055067
use explicit CIK
original accession = 0001628280-25-007118
amendment accession = 0000055067-25-000127
expected controlled state = P11_AMENDED_VARIANT_PRESENT / REVIEW_REQUIRED
```

No quarterly 6-K auto-mapping is permitted.

## FT-00 — Candidate freeze / post-candidate drift / production-mode preflight

Run:

```powershell
git status --short
git branch --show-current
git rev-parse HEAD
git rev-parse 6eaace08c9ba5fb26809a7e02de5835123fb667a
git merge-base --is-ancestor 6eaace08c9ba5fb26809a7e02de5835123fb667a HEAD
git diff --name-status 6eaace08c9ba5fb26809a7e02de5835123fb667a..HEAD
git diff --check
python --version
python -m pytest --version
```

PASS requires candidate existence/ancestry, documentation-only post-candidate history, clean tracked production/test state, `FFDF_P11_US_DEV` absent, and exact frozen constants.

Any production/test drift = `EXECUTION_BLOCKED: PRODUCTION_TEST_DRIFT_AFTER_REVIEW_PASS`.

## FT-01 — Exact deterministic regression / compile gate

Run with short basetemp:

```powershell
python -m pytest -q tests/unit/us_sec/test_issue146.py --basetemp D:\t\p11f4\i146
python -m pytest -q tests/unit/us_sec/test_repair_140_143.py tests/unit/us_sec/test_validation_p8.py --basetemp D:\t\p11f4\r5145
python -m pytest -q tests/unit/us_sec --basetemp D:\t\p11f4\us
python -m pytest -q tests/unit/mcp tests/unit/us_sec/test_validation_p8.py tests/unit/us_sec/test_package_registry.py --basetemp D:\t\p11f4\mcp
python -m pytest -q tests/unit/acquisition tests/unit/identity tests/unit/validation tests/unit/registry tests/unit/mcp tests/unit/research tests/unit/review --basetemp D:\t\p11f4\p0p10
python -m pytest -q tests/unit --basetemp D:\t\p11f4\unit
python -m compileall -q src tests
git diff --check
```

Reviewed development baselines:

```text
ISSUE-146 focused = 9 passed
complete US SEC = 253 passed
complete full unit = 783 passed
```

Zero failures are required. Record every skip explicitly. Different pass counts require a complete explanation and proof that no accepted test disappeared.

## FT-02 — ISSUE-142 complete history-inventory trust boundary

Using current production discovery functions and an acceptance transport, prove:

1. missing `filings.files` is valid empty history;
2. present `filings.files` must be a list;
3. every descriptor is validated before the first history request;
4. non-object descriptor blocks;
5. missing/non-string/empty/unsafe name blocks;
6. duplicate normalized name blocks;
7. missing/null/empty filingFrom/filingTo are unknown;
8. non-empty date values require exact valid `YYYY-MM-DD`;
9. no truncation/coercion/trailing-garbage acceptance;
10. reversed range blocks;
11. missing range conservatively selects;
12. ancient `filingTo < cutoff` excludes;
13. late/relevant amendment history selects;
14. one valid selectable descriptor plus one malformed descriptor yields history fetch count 0;
15. online discovery and P7 reconstruction choose the same source set.

Record selected names and request counts.

## FT-03 — ISSUE-143 / ISSUE-145 immutable source replay

Use acceptance-only copies of parsed artifacts and immutable source packages.

Inline positive/negative proof must cover source member, locator, raw QName, metric identity, raw value, fact kind, contextRef, unitRef, decimals, precision, scale, sign, format, nil, parsed numeric candidate, fragment hash, continuation/source_fragments, context payload, unit payload, evidence raw text, and evidence locator.

Require same-primary context/unit resolution and no borrowing from another member.

XBRL instance proof must scan all package member bytes for authentic instance roots, require exactly one authentic instance with role XBRL_INSTANCE, resolve XML locators/context/unit from that same instance, and reject wrong-role/two-instance/cross-source cases.

NO_STRUCTURED_FACTS requires facts=0 and fact evidence=0.

Frozen Raw Fact/source mismatches must be BLOCKING and use `P11_RAW_FACT_SOURCE_MISMATCH` where specified by Design 37.

## FT-04 — validation-v3 persistence / legacy-v2 immutability

Build an isolated fixture:

```text
immutable raw package
compatible VIRTUAL_HTML_V6 / p11-sec-artifacts-v2 parsed artifact
legacy flat validation-v2
no current p11-sec-validation-v3 directory
```

Hash raw, parsed, legacy validation.json, and legacy issues.jsonl before execution.

Run the production planner/ingest path.

PASS:

```text
planner_action = REVALIDATE_LOCAL
parser invocation count = 0
validation-v3 executes
current path = p7/<package_sha>/p11-sec-validation-v3/
legacy v2 bytes unchanged
parsed bytes unchanged
raw bytes unchanged
v3 schema = p11-sec-validation-v3
Registry current validation fields = v3
catalog/research_ready = v3
```

Also prove no REUSE_DATA before v3, valid v3 loads, corrupt v3 + valid v2 fails closed, corrupt v3 is not overwritten, no v2 fallback, and no timestamp-based directory choice.

## FT-05 — ISSUE-146 planner state and execution

Independently verify:

```text
compatible parsed + reusable current v3 → REUSE_DATA
compatible parsed + v3 absent → REVALIDATE_LOCAL
compatible parsed + valid non-reusable v3 → REVALIDATE_LOCAL
no compatible parsed + local package → PARSE_LOCAL
no local package → DISCOVER_AND_ACQUIRE
amendment/conflict → REVIEW_REQUIRED
```

For REVALIDATE_LOCAL prove parser=0, stale Registry validation does not hide compatible parsed data, fresh discovery is registered, P7 v3 runs directly, same parse_run_id is updated, slot/P8 catalog refresh, and research_ready derives from current discovery + v3.

For REUSE_DATA fresh discovery prove parser=0, P7 refresh executes, Registry v3 fields refresh, and parsed bytes remain unchanged.

## FT-06 — current discovery lifecycle / ticker freshness / conflict

Acceptance transport cases:

- late amendment after reusable local state;
- multiple non-amendment current candidates;
- not found;
- discovery network failure with local reusable bytes;
- status local-only with network calls=0;
- ticker-based online path re-resolves current official ticker mapping;
- explicit CIK path performs ticker-map calls=0.

Current discovery must precede reuse planning.

## FT-07 — Registry schema / current parsed-run refresh

Acceptance-only SQLite fixtures prove supported SEC Registry migration to schema 4, global PRAGMA remains 1, future/unknown shapes fail before mutation, migration is idempotent, representative CN/HK rows are preserved, and P7 revalidation updates the same deterministic `sha256(package_sha + "|" + parser_version)` row rather than creating a fake parse identity.

## FT-08 — package provenance / HTTP / member-selection / security

Run reviewed security/acquisition tests plus acceptance spot checks for URL identity, source/package/member hashes, source drift, path safety, SEC host/redirect policy, response/member/package size bounds, content type and actual bytes, malformed submissions/history/archive index, controlled 403/429, Retry-After and timeout policy, and no JS/filing-controlled remote execution.

Re-prove static-asset selection:

- ordinary image/CSS/browser subresources are not package-authorized solely by primary HTML href/src;
- Apple-like static image references produce unrelated static-asset fetch count 0;
- legitimate primary/XBRL/FilingSummary members remain selected;
- strict MIME checking remains for selected members.

## FT-09 — P8 current-validation boundary / MCP no-network

Prove P8 resolves only versioned validation-v3, never flat v2, fails on missing/corrupt current v3, performs no SEC acquisition/network, revalidates discovery identity, and supports fact/evidence round trip.

Exercise supported document operations and MCP stdio initialization. Record protocol version, tool count, document count, representative CN/HK and US calls where available, and invalid-document handling.

## FT-10 — Live Apple FY2025 10-K fresh production E2E

Use a fresh isolated live root with `FFDF_P11_US_DEV` absent.

Run acquire, ingest, status for LIVE-A.

PASS requires current discovery, expected slot identity unless EXTERNAL_FIXTURE_DRIFT, verifiable observation/package/member hashes, V6/artifacts-v2/validation-v3, versioned v3 path, PASS/COMPATIBLE/blocking=0/review=0, reuse_eligible=true, research_ready=true, facts/evidence>0, and P8 catalog ADDED.

Instrument and record:

- selected history chunks;
- history fetch count;
- archive-member fetch count;
- unrelated static-asset fetch count;
- ticker-map fetch count;
- current submissions fetch count;
- fact_source_mode;
- fact/evidence/table counts.

For current expected Apple FY2025 metadata, ancient irrelevant history should not be fetched. If official descriptor metadata changes, record and apply the frozen selector rather than forcing an obsolete count.

Unrelated browser/static asset fetch count must be 0.

## FT-11 — Live Apple FY2025 repeat / REUSE_DATA classification

Using FT-10 root, run online ingest again.

PASS:

```text
planner_action = REUSE_DATA
current discovery requests > 0
archive redownloads = 0
parser reruns = 0
P7 v3 refresh executes
raw/parsed bytes unchanged
Registry current validation refreshed
research_ready = true
status network calls = 0
```

For explicit CIK, ticker-map calls=0. Record package/observation identity before and after.

## FT-12 — Acceptance-only REVALIDATE_LOCAL from live Apple artifacts

Copy the successful FT-10/11 workspace to a disposable migration root. Preserve raw/parsed hashes and the original v3 receipt. Create an acceptance-only flat v2 fixture in the copy, remove only the copied current v3, then run the normal online ingest path.

PASS requires REVALIDATE_LOCAL, parser=0, archive redownloads=0, raw/parsed/legacy-v2 bytes unchanged, new v3 generated, current discovery bound, Registry refreshed, research_ready=true.

Then corrupt the copied current v3 and rerun. Require controlled fail-closed, no v2 fallback, no parser rerun, and no silent overwrite.

## FT-13 — Live Apple FY2025 Q3 + P8

Run acquire/ingest/status for LIVE-B. Require current discovery, expected accession unless external drift, V6/artifacts-v2/validation-v3, PASS/COMPATIBLE/zero blocking, research_ready=true, and P8 network calls=0. Record fact/evidence/table counts and source mode.

## FT-14 — Live Toyota FY2025 20-F

Run LIVE-C. Require 20-F, expected accession/report period unless external drift, current discovery, V6/v2/v3, PASS/COMPATIBLE/zero blocking, facts/evidence>0, research_ready=true, P8 no-network. Also prove quarterly 6-K is not guessed into a quarter slot.

## FT-15 — Live Kellanova amendment conflict

Run current discovery for LIVE-D by explicit CIK. Require controlled amendment/review state, no arbitrary candidate, no research-ready publication, and no stale local reuse overriding current discovery.

## FT-16 — CN/HK and P0-P10 preservation

Run:

```powershell
python -m pytest -q tests/unit/acquisition tests/unit/identity tests/unit/validation tests/unit/registry tests/unit/mcp tests/unit/research tests/unit/review --basetemp D:\t\p11f4\p0p10-final
```

Also run representative CN/HK operational/MCP smoke using accepted fixtures without mutating source data.

## FT-17 — Final drift / evidence integrity

Before evidence creation:

```powershell
git status --short
git diff --check
git diff --name-status 6eaace08c9ba5fb26809a7e02de5835123fb667a..HEAD
```

Every post-candidate change must be documentation only. No tracked source/test change is allowed during Formal Test.

## 8. Overall result classification

Each FT gate is PASS, FAIL, or BLOCKED.

Overall:

- any required executed assertion failure = `EXECUTION_FAIL`;
- production/test repair required = `EXECUTION_FAIL`;
- required live gate unavailable because of contact/external conditions = `EXECUTION_BLOCKED`;
- every required gate passes = `EXECUTION_PASS`.

PC Agent does not convert EXECUTION_PASS to ACCEPTANCE_PASS.

## 9. Formal evidence requirements

After execution create exactly:

`development/204-p11-formal-test-evidence-4.md`

Number 203 is reserved for execution authorization if this plan passes exact-plan review.

Evidence must contain candidate SHA, Design 38 SHA, Review PASS commit, Formal Plan path/SHA, execution authorization path/SHA, environment, every command/exit code, FT-00..FT-17 verdicts, exact pass/fail/skip counts, live receipts and hashes, history selection/fetch counts, archive/static/ticker/submissions request classification, fact/evidence/table counts, exact v3 path, legacy-v2 immutability proof, REVALIDATE_LOCAL parser count, corrupt-v3 receipt, Registry parse-run before/after, P8 no-network, MCP stdio, CN/HK/P0-P10 preservation, and explicit production/test drift declaration.

Raw logs stay outside Git. Never record secrets or SEC contact value.

## 10. Evidence commit rule

Formal evidence must be documentation-only. Before committing evidence, verify candidate ancestry, post-candidate documentation-only diff, clean production/test worktree, and `git diff --check`.

Suggested evidence commit:

`docs: record P11 formal test evidence 4`

Push by normal fast-forward only.

## 11. Stop boundary

After evidence is pushed, STOP.

Do not merge main, modify production/test code, create a new production candidate, declare ACCEPTANCE_PASS, or declare P11 DONE.

Next action:

`CHATGPT INDEPENDENT FORMAL ACCEPTANCE REVIEW 4`.

## 12. Required final handoff

```text
P11 FORMAL TEST EXECUTION 4 COMPLETE

REMOTE LINEAGE:
reconcile/p11-140-143-local-chain

DESIGN 38:
92af6205eb8e090994dcece68850eddcd4232392

PRODUCTION CANDIDATE:
6eaace08c9ba5fb26809a7e02de5835123fb667a

REVIEW PASS:
development/201-p11-fresh-full-exact-candidate-review-7.md
50baac22baf40b29fd08224b883c7b43f06f7736

FORMAL TEST PLAN:
development/202-p11-formal-test-plan-4.md

FORMAL TEST PLAN SHA:
<exact SHA>

EXECUTION AUTHORIZATION:
development/203-p11-formal-test-execution-authorization-4.md

EXECUTION AUTHORIZATION SHA:
<exact SHA>

FORMAL EVIDENCE:
development/204-p11-formal-test-evidence-4.md

EVIDENCE COMMIT:
<exact SHA>

FT-00..FT-17:
<each PASS/FAIL/BLOCKED>

ISSUE-146 REVALIDATE_LOCAL PARSER COUNT:
<value>

LEGACY V2 BYTE IMMUTABILITY:
<PASS/FAIL/BLOCKED>

CORRUPT V3 FAIL-CLOSED:
<PASS/FAIL/BLOCKED>

APPLE FY2025 ACCESSION:
<value>

APPLE FY2025 OBSERVATION SHA:
<value>

APPLE FY2025 PACKAGE SHA:
<value>

APPLE FY2025 SELECTED HISTORY:
<value>

APPLE FY2025 HISTORY FETCH COUNT:
<count>

APPLE FY2025 ARCHIVE FETCH COUNT:
<count>

APPLE FY2025 STATIC-ASSET FETCH COUNT:
<count>

APPLE REPEAT PLANNER ACTION:
<value>

APPLE REPEAT PARSER RERUNS:
<count>

APPLE REPEAT ARCHIVE REDOWNLOADS:
<count>

APPLE Q3 ACCESSION:
<value>

TOYOTA ACCESSION:
<value>

KELLANOVA RESULT:
<value>

US SEC TESTS:
<result>

FULL UNIT:
<result>

P0-P10:
<result>

COMPILEALL:
<PASS/FAIL>

GIT DIFF --CHECK:
<PASS/FAIL>

FFDF_P11_US_DEV PRESENT:
NO

LIVE SEC:
<RUN/BLOCKED>

PRODUCTION/TEST CODE CHANGED DURING FORMAL TEST:
NO

EXECUTION RESULT:
<EXECUTION_PASS/EXECUTION_FAIL/EXECUTION_BLOCKED>

FORMAL ACCEPTANCE:
NOT YET DECLARED

MAIN MERGE:
NOT RUN

P11 DONE:
NO

STOPPED FOR CHATGPT INDEPENDENT FORMAL ACCEPTANCE REVIEW 4.
```
