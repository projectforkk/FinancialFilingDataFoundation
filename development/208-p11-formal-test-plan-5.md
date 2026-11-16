# 208 — P11 US SEC Provider Formal Test Plan 5

Status: **FORMAL_TEST_PLAN_FROZEN / EXECUTION_NOT_YET_AUTHORIZED**

Date: 2026-11-16

Plan owner: ChatGPT independent review
Execution owner: Acceptance/Test Agent
Final result reviewer: ChatGPT independent acceptance review

This is a new full Formal Test cycle for the exact ISSUE-147 production
candidate. Formal Test 4 is historical failure evidence only and must not be
resumed from FT-11.

## 1. Exact authority

Repository:

`projectforkk/FinancialFilingDataFoundation`

Authoritative remote lineage:

`reconcile/p11-140-143-local-chain`

Design 39 freeze:

`fad6ee7512ec1f2f3da0c9a24c646959b2f45541`

Development authorization:

`534a1e64ee549df910ed815f90fde82726b43b1c`

Frozen production candidate:

`f1cc76889718e06fdbdc46926e2b207b740a96e3`

Development evidence:

`development/206-p11-issue147-development-evidence.md`

Evidence commit:

`f859dc342060d8c534491639d85e7256c4e11a57`

Fresh Full Exact-Candidate Review:

`development/207-p11-fresh-full-exact-candidate-review-8.md = REVIEW_PASS`

Review commit:

`56d884f5adfc4f5044f3970c3e43180b658c74a8`

Any production/test change after the frozen candidate invalidates this plan.

## 2. Frozen version contract

Formal execution must independently confirm:

```text
REGISTRY_SCHEMA_VERSION = 1
SEC_REGISTRY_SCHEMA_VERSION = 4
SEC_DISCOVERY_SCHEMA = p11-sec-discovery-v1
VIRTUAL_HTML_NORMALIZER_VERSION = VIRTUAL_HTML_V6
SEC_ARTIFACT_SCHEMA = p11-sec-artifacts-v2
SEC_VALIDATION_SCHEMA = p11-sec-validation-v3
```

No new P11 reason code is authorized.

## 3. Formal execution governance

The Acceptance/Test Agent may create acceptance-only harnesses, copied
workspaces, temporary SQLite databases, transport wrappers and raw logs outside
tracked production/test paths.

It must not modify:

- `src/`;
- `tests/`;
- dependency/lock files;
- runtime production configuration;
- design files.

If any gate exposes a production/test defect:

```text
EXECUTION_FAIL
STOP
RETURN TO A NEW CANDIDATE CYCLE
```

Do not repair code during Formal Test.

## 4. Environment

Use the active P11 worktree and short Windows paths.

Recommended:

```text
worktree:
D:\Codex\FinancialFilingDataFoundation\worktrees\active\p11-sec-rebuild-development

formal root:
D:\ffdf-p11-ft5

pytest temp:
D:\t\p11f5
```

`FFDF_P11_US_DEV` must remain absent.

Record only whether `FFDF_SEC_CONTACT_EMAIL` is configured; never record its
value.

## 5. Result classification

Each gate is:

`PASS / FAIL / BLOCKED`

Overall:

- any executed required assertion failure → `EXECUTION_FAIL`;
- any production/test repair requirement → `EXECUTION_FAIL`;
- required live gate unavailable because of external/contact conditions →
  `EXECUTION_BLOCKED`;
- all required gates pass → `EXECUTION_PASS`.

Execution PASS is not Acceptance PASS.

# FT-00 — Candidate freeze / documentation-only post-candidate history

Verify:

- exact candidate exists;
- candidate is ancestor of HEAD;
- every post-candidate tracked change is documentation/governance only;
- worktree has no tracked production/test modifications;
- `git diff --check` passes;
- frozen constants match §2;
- `FFDF_P11_US_DEV` absent.

Any production/test drift after candidate = EXECUTION_BLOCKED.

# FT-01 — Full deterministic regression

Run with short basetemp:

```powershell
python -m pytest -q tests/unit/us_sec/test_issue147.py --basetemp D:\t\p11f5\i147
python -m pytest -q tests/unit/us_sec/test_issue146.py tests/unit/us_sec/test_repair_140_143.py tests/unit/us_sec/test_validation_p8.py --basetemp D:\t\p11f5\repair
python -m pytest -q tests/unit/us_sec --basetemp D:\t\p11f5\us
python -m pytest -q tests/unit/mcp --basetemp D:\t\p11f5\mcp
python -m pytest -q tests/unit/acquisition tests/unit/identity tests/unit/validation tests/unit/registry tests/unit/mcp tests/unit/research tests/unit/review --basetemp D:\t\p11f5\p0p10
python -m pytest -q tests/unit --basetemp D:\t\p11f5\unit
python -m compileall -q src tests
git diff --check
```

Development reference counts:

```text
ISSUE-147 focused = 10
US SEC = 263
MCP = 65
P0-P10 = 371
full unit = 793
```

Zero failures required. Record all skips.

# FT-02 — ISSUE-147 observation identity

Acceptance-only proof must independently verify:

1. same official bytes + same source SHA + different retrieval times produce
   different snapshot IDs;
2. both observation files coexist under
   `ticker-map/observations/<snapshot_id>.json`;
3. no `P11_SOURCE_DRIFT` occurs for distinct retrieval observations;
4. canonical snapshot identity recomputes exactly;
5. same snapshot ID + different canonical payload produces
   `P11_SOURCE_DRIFT`;
6. invalid/non-timezone-aware retrieved_at fails as
   `P11_TICKER_SNAPSHOT_INVALID`;
7. source-byte tamper fails;
8. derivative mapping tamper fails;
9. current observation path identity mismatch fails.

# FT-03 — Historical legacy snapshot compatibility

This gate must use an actual historical-format legacy payload that does NOT
contain `snapshot_id`.

Place it at:

`workspace/ingest/us/ticker-map/<source_sha256>.json`

Require:

- filename SHA matches payload SHA;
- source bytes rehash correctly;
- official URL verified;
- derivative mapping re-parses exactly;
- historical retrieved_at is usable;
- local status can use it if it is the newest verified snapshot;
- online refresh never rewrites/renames/deletes it;
- its byte hash is unchanged after a fresh online observation is persisted.

Also test legacy source-byte, mapping, filename and URL tamper fail closed.

# FT-04 — Newest-only cached status / no stale fallback

Create multiple independently verified snapshots:

- older AAPL→CIK1;
- newer AAPL→CIK2.

Require local cached status resolves CIK2 only and does not combine historical
CIKs.

Then create:

- older snapshot contains AAPL;
- newest verified snapshot does not contain AAPL.

Require no fallback to the older alias and the controlled cached-resolution
unavailable behavior.

Within one selected snapshot, one ticker→multiple CIKs must still be controlled
ambiguity.

# FT-05 — Explicit CIK / online ticker freshness

Require:

- explicit CIK online acquire/ingest ticker-map fetch count = 0;
- ticker-based online acquire/ingest fetch current official ticker map every
  invocation;
- cached ticker map never silently substitutes for failed online current lookup;
- local-only status performs no network I/O.

# FT-06 — ISSUE-142 history inventory

Re-run acceptance-only strict history inventory checks:

- all descriptors validated before fetch;
- malformed descriptor → zero history fetches;
- exact YYYY-MM-DD dates only;
- no coercion/truncation;
- reversed ranges block;
- missing ranges conservatively select;
- ancient irrelevant chunks exclude;
- late/relevant chunks include;
- online and reconstructed source sets match.

# FT-07 — ISSUE-143 / ISSUE-145 immutable source replay

Re-run positive and negative acceptance checks for Inline and XBRL-instance
source modes, context/unit same-source replay, Raw Fact/source projection,
fact↔evidence binding, continuation/source fragments, authentic instance-role
rules and frozen mismatch reasons.

# FT-08 — validation-v3 / ISSUE-146 regression

Prove:

- current validation-v3 versioned path;
- legacy validation-v2 byte immutability;
- no v2 fallback;
- corrupt v3 fail closed;
- REVALIDATE_LOCAL parser count = 0;
- REUSE_DATA fresh discovery refresh;
- same deterministic parse_run_id refreshed;
- no fake parse run.

# FT-09 — acquisition / provenance / security / static assets

Re-run package provenance, URL/path/host, MIME/actual-byte, size, malformed
source, redirect, 403/429, retry/timeout and static-asset selection boundaries.

Unrelated browser/static assets must not be fetched as package members.

# FT-10 — Fresh live Apple FY2025 ticker-based acquire

Use a brand-new Formal Test 5 root.

Run ticker-based:

`acquire --market US --ticker AAPL --year 2025 --period FY`

Require expected accession
`0000320193-25-000079` unless EXTERNAL_FIXTURE_DRIFT.

Record:

- ticker snapshot ID;
- ticker retrieved_at;
- ticker source SHA;
- current submissions count;
- selected history chunks;
- history fetch count;
- archive member fetch count;
- unrelated static-asset fetch count;
- complete selected package member list;
- each member relative name, role, byte length, member SHA;
- resulting package SHA;
- observation SHA.

Static-asset fetch count must be 0.

## FT-10A — Mandatory Apple package identity audit

Historical Formal Test 4 package SHA:

`1196a354461ac65afa4ce7f1c67b2d65b04c1e496f521f34a139c6d6e5872d3d`

ISSUE-147 developer smoke package SHA:

`d94d8c46e34ce25af8d42279dbb4a370b1e617d7daf421743f29468b77d19568`

The candidate changed no package/acquisition code.

Formal Test 5 must compare the current package member records against any
available receipts/artifacts for both historical SHAs.

If the current SHA differs, record exactly which member name/role/byte length or
member SHA differs.

Allowed outcomes:

- explainable current official-byte/member drift with verifiable SEC source;
- explainable prior disposable-workspace/receipt difference;
- same current package SHA as one historical receipt.

Unexplained package identity drift is FAIL, not silently accepted.

# FT-11 — Live Apple ticker-based ingest immediately after FT-10

Run ticker-based ingest in the same root.

This gate is the exact ISSUE-147 formal boundary.

Require:

- second ticker-map fetch occurs;
- source SHA may equal FT-10;
- second retrieved_at differs;
- second snapshot ID differs if retrieved_at differs;
- both snapshot files remain immutable;
- no `P11_SOURCE_DRIFT`;
- current discovery continues;
- normal ingest succeeds;
- validation-v3 PASS/COMPATIBLE/blocking=0;
- research_ready=true.

Record both ticker snapshot IDs and timestamps.

# FT-12 — Live Apple repeat reuse

Run online ingest again.

Require:

- current ticker map fetched;
- current discovery fetched;
- planner = REUSE_DATA when local state is current/reusable;
- archive redownloads = 0;
- parser reruns = 0;
- P7 v3 refresh executes;
- raw/parsed bytes unchanged;
- Registry validation fields refreshed;
- status network calls = 0.

# FT-13 — Acceptance-only live-artifact REVALIDATE_LOCAL

Using a disposable copy of successful Apple state, create the historical
validation-v2/no-current-v3 transition and prove:

- REVALIDATE_LOCAL;
- parser=0;
- raw/parsed/v2 bytes unchanged;
- new v3 generated;
- Registry/catalog refreshed;
- corrupt-v3 retry fails closed with no v2 fallback.

# FT-14 — Live Apple FY2025 Q3 + P8/MCP no-network

Run Q3 expected accession
`0000320193-25-000073` unless external drift.

Require V6/artifacts-v2/validation-v3, PASS/COMPATIBLE/zero blocking,
research_ready=true.

Exercise P8/MCP document/fact/evidence/validation paths and prove P8 acquisition
network calls = 0.

# FT-15 — Live Toyota FY2025 20-F

Run expected accession `0001193125-25-142326` unless external drift.

Require current discovery, V6/v2/v3, PASS/COMPATIBLE/zero blocking,
facts/evidence>0, research_ready=true and P8 no-network.

Also prove quarterly 6-K is not guessed into a quarterly slot.

# FT-16 — Live Kellanova amendment conflict

Use explicit CIK `0000055067`.

Require controlled current amendment/review outcome, no arbitrary candidate,
no research-ready publication and no stale local reuse overriding discovery.

# FT-17 — CN/HK + P0-P10 preservation

Run P0-P10 focused suite and representative accepted CN/HK operational/MCP
smoke without mutating accepted source data.

# FT-18 — Final drift / evidence integrity

Before evidence creation:

```powershell
git status --short
git diff --check
git diff --name-status f1cc76889718e06fdbdc46926e2b207b740a96e3..HEAD
```

All post-candidate tracked changes must be documentation only.

## 6. Formal evidence

After execution create exactly:

`development/210-p11-formal-test-evidence-5.md`

Do not use 209 for evidence; 209 is reserved for execution authorization.

Evidence must include:

- candidate/design/review/plan/authorization SHAs;
- FT-00..FT-18 verdicts;
- exact commands, exit codes, pass/fail/skip counts;
- ISSUE-147 snapshot IDs, timestamps and source SHAs;
- true same-observation conflict proof;
- historical no-snapshot_id legacy compatibility proof;
- newest-only/no-stale-fallback proof;
- explicit-CIK zero-fetch proof;
- Apple package member-by-member identity audit;
- history/archive/static/ticker/submissions request counts;
- validation-v3/REVALIDATE_LOCAL evidence;
- P8/MCP no-network evidence;
- CN/HK/P0-P10 preservation;
- explicit production/test drift declaration.

Raw logs remain outside Git.

## 7. Stop boundary

After the documentation-only Formal Test evidence commit is pushed, STOP.

Do not merge main, modify production/test code, declare Acceptance PASS, or
declare P11 DONE.

Next action:

`CHATGPT INDEPENDENT FORMAL ACCEPTANCE REVIEW 5`.
