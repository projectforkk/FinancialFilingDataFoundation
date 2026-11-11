# 170 — P11 US SEC Provider Revised Formal Test / Acceptance Plan

Status: **FORMAL_TEST_PLAN_ISSUED**

Plan owner: ChatGPT independent review  
Execution owner: PC Agent / local Windows environment  
Final result reviewer: ChatGPT independent acceptance review

Exact reviewed production candidate:

`2504614265b7a233ef9e4a772544ad63dd6eec37`

Code review:

`development/169-p11-code-review-result-8.md`

Code-review commit:

`2d69f1dd9b07fd2a7e9425e26b5c3edb2a8d9abe`

Code-review verdict:

`REVIEW_PASS`

Development branch:

`task/p11-sec-rebuild-development`

This plan supersedes the obsolete acceptance plan `development/156-p11-formal-test-plan.md` for this candidate. It preserves the frozen live SEC fixtures but adds the Registry, parser-upgrade, planner/reuse, P8 full-tool, and corrected CIK-first gates required by reviews 161–169.

## 1. Governance / freeze

The production candidate under formal acceptance is frozen at:

`2504614265b7a233ef9e4a772544ad63dd6eec37`

PC Agent must execute this plan; it must not redesign the plan, substitute easier fixtures, weaken expected outcomes, or declare final acceptance.

Before any test:
- verify the candidate exists exactly;
- verify the candidate is in the development-branch lineage;
- list every path changed after the candidate;
- require every post-candidate change to be documentation/evidence/test-plan only.

If any `src/`, `tests/`, runtime lock, packaging, or other production/test byte changed after the candidate, stop:

```text
EXECUTION_BLOCKED
REASON: PRODUCTION_CODE_DRIFT_AFTER_REVIEW_PASS
```

No production repair is allowed during formal acceptance. Any required production change ends this run and returns to code review with a new candidate.

Do not:
- merge main;
- modify `SUPPORTED_MARKETS`;
- enable P11 production availability;
- edit accepted CN/HK source/raw artifacts;
- reset/clean/force push/history rewrite.

## 2. Acceptance workspace / environment

Use the active development worktree source, not the main checkout source.

```powershell
$root = 'D:\Codex\FinancialFilingDataFoundation'
$wt = 'D:\Codex\FinancialFilingDataFoundation\worktrees\active\p11-sec-rebuild-development'
$py = Join-Path $root '.venv\Scripts\python.exe'
$accept = Join-Path $root 'work\p11-formal-acceptance-25046142'
$tmp = Join-Path $accept 'tmp'
$evidenceRoot = Join-Path $accept 'evidence'

Set-Location $wt

New-Item -ItemType Directory -Force -Path $accept,$tmp,$evidenceRoot | Out-Null

$env:FFDF_ROOT = $accept
$env:FFDF_P11_US_DEV = '1'
$env:PYTHONPATH = (Join-Path $wt 'src')
$env:TEMP = $tmp
$env:TMP = $tmp
```

Do not copy accepted CN/HK production raw/source data into this root.

Record:
- Windows identity/version;
- Python version;
- Git branch/HEAD;
- candidate SHA;
- `FFDF_ROOT`;
- whether `FFDF_SEC_CONTACT_EMAIL` is configured, YES/NO only.

Never record the actual contact address.

## 3. SEC contact precondition

Live SEC tests require the operator-configured monitored contact in:

`FFDF_SEC_CONTACT_EMAIL`

If missing/invalid:
- run every offline gate;
- mark all live gates BLOCKED;
- final execution result = `EXECUTION_BLOCKED`.

Do not invent a contact identity and do not bypass the production check.

## 4. Frozen official SEC fixtures

### FIXTURE-A — Apple FY2025 10-K

- CIK: `0000320193`
- ticker alias: AAPL
- year: 2025
- period: FY
- form: 10-K
- accession: `0000320193-25-000079`
- filing date: 2025-10-31
- report period: 2025-09-27
- primary: `aapl-20250927.htm`

### FIXTURE-B — Apple FY2025 Q3 10-Q

- CIK: `0000320193`
- ticker alias: AAPL
- year: 2025
- period: Q3
- form: 10-Q
- accession: `0000320193-25-000073`
- filing date: 2025-08-01
- report period: 2025-06-28
- primary: `aapl-20250628.htm`
- extension schema: `aapl-20250628.xsd`

### FIXTURE-C — Kellanova FY2024 amendment conflict

- CIK: `0000055067`
- year: 2024
- period: FY
- original 10-K accession: `0001628280-25-007118`
- amendment 10-K/A accession: `0000055067-25-000127`

Important: formal command is **CIK-only**. Do not use ticker K; current SEC ticker mapping no longer contains historical K after delisting/acquisition.

Expected controlled outcome:
`P11_AMENDED_VARIANT_PRESENT`

### FIXTURE-D — Toyota FY2025 20-F

- CIK: `0001094517`
- ticker alias: TM
- year: 2025
- period: FY
- form: 20-F
- accession: `0001193125-25-142326`
- filing date: 2025-06-18
- report period: 2025-03-31
- primary: `d925022d20f.htm`

No quarterly 6-K auto-mapping is permitted.

## 5. FT-00 — candidate freeze / preflight

Run:

```powershell
Set-Location $wt

git branch --show-current
git status --short
git rev-parse HEAD
git rev-parse 2504614265b7a233ef9e4a772544ad63dd6eec37
git merge-base --is-ancestor 2504614265b7a233ef9e4a772544ad63dd6eec37 HEAD
git diff --name-status 2504614265b7a233ef9e4a772544ad63dd6eec37..HEAD
git diff --check
& $py --version
```

PASS:
- branch = `task/p11-sec-rebuild-development`;
- candidate exists and is ancestor of HEAD;
- all post-candidate paths are documentation-only;
- no dirty production/test changes;
- diff-check PASS.

Also verify:
- `SUPPORTED_MARKETS == ("CN","HK")`;
- P11 dev gate default remains off without environment enablement;
- P11 production capability remains unavailable.

## 6. FT-01 — complete deterministic regression gate

Run:

```powershell
& $py -m pytest -q --basetemp (Join-Path $tmp 'registry') tests/unit/us_sec/test_package_registry.py
& $py -m pytest -q --basetemp (Join-Path $tmp 'p11') tests/unit/us_sec
& $py -m pytest -q --basetemp (Join-Path $tmp 'unit') tests/unit
& $py -m pytest -q --basetemp (Join-Path $tmp 'cnhk') tests/unit/identity tests/unit/registry tests/unit/mcp tests/unit/user_cli
& $py -m compileall -q src tests
git diff --check
```

Expected development baselines:
- Registry focused: 18 passed;
- P11 focused: 94 passed;
- full unit: 624 passed;
- CN/HK regression: 96 passed.

Formal PASS requires zero failures. Higher pass counts are allowed only if no production/test code changed after candidate; explain collection differences if any.

## 7. FT-02 — Registry migration/version acceptance

This is mandatory even though unit tests already cover it.

Use an acceptance-only Python harness under `$evidenceRoot`; do not alter tracked source/tests.

The harness must exercise current production `SQLiteRegistry` with raw SQLite fixtures for:

### FT-02A early v2-A
Historical reference:
`05e06096bc8b788d0467a1ce3442829e87727b6b`

Before:
- PRAGMA user_version = 1;
- SEC core tables;
- no sec_schema_metadata;
- no compatibility_status.

PASS:
- migrates to SEC schema 3;
- PRAGMA remains 1;
- compatibility becomes INCOMPATIBLE;
- source/member/binding/parsed identity preserved;
- second reopen idempotent.

### FT-02B late v2-B
Historical reference:
`362877244aa553ca4d76eb71318b116cde04c6a5`

Before:
- PRAGMA user_version = 1;
- no sec_schema_metadata;
- compatibility_status present;
- seed a parsed row with compatibility_status = COMPATIBLE.

PASS:
- migrates to SEC schema 3;
- compatibility forced to INCOMPATIBLE;
- other parsed fields unchanged;
- source/member/binding rows unchanged;
- second reopen idempotent.

### FT-02C unknown unversioned shape
Take a valid historical v2 fixture and add one unknown column.

PASS:
- `RegistrySchemaUnsupported`;
- migration not executed;
- table SQL, columns, indexes, metadata, rows, and PRAGMA unchanged.

### FT-02D future version
Create SEC metadata version 99 on a deliberately non-current shape.

PASS:
- `RegistrySchemaUnsupported`;
- no current-version DDL executes first;
- logical DB state unchanged.

Record before/after snapshots and exact version values.

## 8. FT-03 — parser V3→V4 / planner incremental-state acceptance

Use acceptance-only local fixtures; no SEC network.

Mandatory state transition:

```text
local immutable SEC package
+ historical VIRTUAL_HTML_V3 parsed artifact/Registry row
→ planner = PARSE_LOCAL
→ network requests = 0
→ create VIRTUAL_HTML_V4
→ current PASS/COMPATIBLE parsed registration
→ planner = REUSE_DATA
→ second ingest parser reruns = 0
→ second ingest network requests = 0
```

PASS also requires:
- old V3 artifact bytes remain unchanged;
- current V4 artifact loads successfully;
- stale parser row cannot trigger REUSE_DATA;
- stale schema row cannot trigger REUSE_DATA;
- wrong-package parsed row cannot trigger REUSE_DATA;
- REVIEW_REQUIRED + COMPATIBLE remains not reusable;
- exact current PASS + COMPATIBLE + zero blocking is reusable.

Use production functions and monkeypatch/instrument only from the acceptance harness. Do not edit production code.

## 9. FT-04 — live Apple FY2025 10-K E2E

Require SEC contact configured.

Run on clean isolated acceptance root:

```powershell
& $py -m financial_filing_data_foundation.user_cli acquire --market US --cik 320193 --ticker AAPL --year 2025 --period FY
& $py -m financial_filing_data_foundation.user_cli ingest  --market US --cik 320193 --ticker AAPL --year 2025 --period FY
& $py -m financial_filing_data_foundation.user_cli status  --market US --cik 320193 --ticker AAPL --year 2025 --period FY
```

PASS requires:
- exact accession `0000320193-25-000079`;
- form 10-K;
- report period 2025-09-27;
- stable CIK company identity `US:CIK0000320193`;
- one valid package SHA;
- immutable member hashes verify;
- parser version `VIRTUAL_HTML_V4`;
- validation PASS;
- compatibility COMPATIBLE;
- blocking count 0;
- research_ready true;
- non-zero Raw Facts;
- non-zero Evidence;
- status sees the persisted package/parsed state;
- P8 catalog registration succeeds.

Record accession, package SHA, primary member SHA, member count, fact count, evidence count, table count, validation status and artifact paths.

## 10. FT-05 — live Apple FY2025 Q3 + full P8 tool family

Run:

```powershell
& $py -m financial_filing_data_foundation.user_cli acquire --market US --cik 320193 --ticker AAPL --year 2025 --period Q3
& $py -m financial_filing_data_foundation.user_cli ingest  --market US --cik 320193 --ticker AAPL --year 2025 --period Q3
& $py -m financial_filing_data_foundation.user_cli status  --market US --cik 320193 --ticker AAPL --year 2025 --period Q3
```

PASS requires exact:
- accession `0000320193-25-000073`;
- form 10-Q;
- report period 2025-06-28;
- validation PASS;
- compatibility COMPATIBLE;
- zero blocking;
- research_ready true;
- non-zero facts/evidence;
- V4 parser.

Then exercise the complete accepted P8 tool family against this SEC document **without network acquisition**:
- list_documents;
- get_document;
- search;
- read_pages;
- list_sections;
- list_tables;
- get_table;
- list_raw_facts;
- get_fact;
- get_evidence;
- get_validation.

Mandatory P8 assertions:
- virtual HTML pagination is explicit;
- page filter returns SEC facts using virtual_page_no;
- metric filter matches raw_qname;
- get_fact round-trips to get_evidence;
- evidence source member SHA belongs to immutable package;
- table/cell source traceability resolves where tables are present;
- P8 causes zero HTTP/acquisition calls.

### FT-05A custom extension
Require at least one filing-local `aapl:` raw QName if present in the frozen fixture. If present:
- raw QName retained;
- no guessed canonical standard metric replaces it;
- evidence resolves.

If none exists, record exact count/result and rely on deterministic custom-extension unit coverage; do not substitute a different live filing.

### FT-05B hidden Inline XBRL
If hidden facts exist:
- locator kind = DOM_HIDDEN_FACT;
- node resolves below ix:hidden;
- raw text/fragment hash verify.

If zero hidden facts exist, record `LIVE_HIDDEN_FACT_NOT_PRESENT_IN_FROZEN_FIXTURE`; deterministic hidden-fact unit coverage remains mandatory.

## 11. FT-06 — live Toyota FY2025 20-F / FPI gate

Run:

```powershell
& $py -m financial_filing_data_foundation.user_cli acquire --market US --cik 1094517 --ticker TM --year 2025 --period FY
& $py -m financial_filing_data_foundation.user_cli ingest  --market US --cik 1094517 --ticker TM --year 2025 --period FY
& $py -m financial_filing_data_foundation.user_cli status  --market US --cik 1094517 --ticker TM --year 2025 --period FY
```

PASS:
- exact accession `0001193125-25-142326`;
- form 20-F;
- report period 2025-03-31;
- package/member hashes verify;
- non-zero facts/evidence;
- validation PASS;
- compatibility COMPATIBLE;
- zero blocking;
- research_ready true;
- P8 read works without network.

Also run/record deterministic FPI unit gate proving 6-K quarterly mapping is not guessed.

## 12. FT-07 — live Kellanova amendment conflict / CIK-first

Formal command is CIK-only:

```powershell
& $py -m financial_filing_data_foundation.user_cli acquire --market US --cik 55067 --year 2024 --period FY
```

Do not add `--ticker K`.

Expected controlled non-success:
`P11_AMENDED_VARIANT_PRESENT`

PASS:
- discovery sees original `0001628280-25-007118`;
- discovery sees amendment `0000055067-25-000127`;
- no silent selection;
- no false ticker-map dependency;
- no active research-ready binding for the conflicted slot;
- amendment is a variant, not an extra fiscal slot.

A normal successful acquisition is FAIL.

## 13. FT-08 — deterministic security / HTTP / source-integrity gates

Do not intentionally provoke SEC with bad live traffic.

Run the reviewed unit tests and an acceptance-only harness sufficient to prove:
- SEC host allowlist;
- arbitrary URL rejection;
- canonical archive-relative path handling;
- Windows drive/traversal/backslash/encoded traversal rejection;
- safe nested SEC relative paths allowed when canonical;
- redirect host validation;
- redirect cap;
- content-type header value handling;
- actual-byte validation;
- bounded response/member/package sizes;
- archive-index malformed-shape failure;
- 429 → `P11_SEC_RATE_LIMITED`;
- 403 → `P11_SEC_ACCESS_DENIED`;
- Retry-After deterministic bounded behavior;
- connect/read/total timeout contract;
- source drift cannot silently overwrite;
- no JS execution / no remote filing subresource execution.

For simulated terminal 429/403, record attempt count and final reason.

## 14. FT-09 — no-AI / dependency / runtime boundary

Search production source and runtime lock.

PASS requires no production calls/import paths that invoke:
- OpenAI;
- Anthropic;
- Gemini;
- Codex API;
- MCP sampling;
- remote AI/LLM services.

Also verify:
- dedicated SEC runtime remains stdlib-only if that is the reviewed lock;
- production filing content cannot trigger arbitrary shell execution;
- P8 remains read-only and does not acquire from SEC.

Record the exact search commands/results.

## 15. FT-10 — live idempotency / REUSE_DATA zero-network

Use FIXTURE-A after FT-04.

Capture before:
- accession;
- package SHA;
- package manifest SHA;
- all member SHAs;
- current V4 artifact hashes;
- fact/evidence/table counts;
- Registry parsed row;
- catalog identity.

Then instrument production HTTP/acquisition/parser entry points from an acceptance-only harness so any network request or parser rerun during reuse fails the harness.

Run repeat acquire/ingest/status for the same slot.

PASS:
- planner/result = REUSE_DATA where applicable;
- known local package is not redownloaded;
- network calls = 0;
- parser reruns = 0;
- package manifest/member hashes unchanged;
- V4 artifact unchanged;
- counts unchanged;
- same package/catalog identity;
- no conflicting active binding.

Record exact before/after hashes and call counts.

## 16. FT-11 — CN/HK preservation

In addition to the 96-test regression gate:
- verify `SUPPORTED_MARKETS == ("CN","HK")` before acceptance decision;
- verify legacy Registry `PRAGMA user_version = 1`;
- verify acceptance root contains no copied/mutated accepted CN/HK source data;
- if project has existing deterministic CN/HK CLI smoke fixtures that do not require touching accepted production data, run them;
- P8 CN/HK tool behavior must remain unchanged through the full unit suite.

No live CN/HK acquisition is required if it would mutate or depend on accepted production state.

## 17. Formal execution result

Any required executed gate failure:
`EXECUTION_FAIL`

Required live gate unable to execute because contact/network environment is unavailable:
`EXECUTION_BLOCKED`

Only if every required offline and live gate passes:
`EXECUTION_PASS`

PC Agent does not decide `ACCEPTANCE_PASS`; ChatGPT does that at Gate V1.

If production code must change at any time:
- stop formal testing;
- do not patch it;
- report `EXECUTION_FAIL`;
- return to a new candidate/review/test-plan cycle.

## 18. Evidence artifact

Create:

`development/171-p11-formal-test-evidence.md`

Evidence commit must contain documentation/evidence only and no `src/` or `tests/` changes.

Preserve raw logs/harness outputs under:

`work/p11-formal-acceptance-25046142/evidence/`

Do not commit secrets or the SEC contact value.

Evidence must include:
- exact candidate SHA;
- exact plan file and plan commit;
- review file/commit;
- environment identity;
- every command;
- exit code;
- FT-00 through FT-11 PASS/FAIL/BLOCKED;
- exact observed live accessions/forms/report periods;
- package/member hashes;
- V4 parser version;
- fact/evidence/table counts;
- P7 validation/compatibility/reuse values;
- P8 full-tool results;
- Registry v2-A/v2-B/future/unknown results;
- V3→V4 state-transition result;
- repeat REUSE_DATA network/parser call counts;
- 403/429 reason/attempt results;
- no-AI/runtime audit;
- focused/full/CN-HK pass counts;
- compileall/diff-check;
- explicit declaration whether production/test source changed during acceptance.

## 19. Required final PC Agent handoff

Return exactly:

```text
P11 REVISED FORMAL TEST EXECUTION: COMPLETE

Production candidate:
2504614265b7a233ef9e4a772544ad63dd6eec37

Code review:
development/169-p11-code-review-result-8.md

Code review commit:
2d69f1dd9b07fd2a7e9425e26b5c3edb2a8d9abe

Formal test plan:
development/170-p11-revised-formal-test-plan.md

Formal test plan commit:
<exact SHA>

Formal test evidence:
development/171-p11-formal-test-evidence.md

Evidence commit:
<exact SHA>

FT-00 Candidate freeze:
<PASS/FAIL/BLOCKED>

FT-01 Deterministic regression:
<PASS/FAIL/BLOCKED>

FT-02 Registry migrations/version gate:
<PASS/FAIL/BLOCKED>

FT-03 V3→V4 / planner reuse:
<PASS/FAIL/BLOCKED>

FT-04 Apple FY2025 10-K:
<PASS/FAIL/BLOCKED>

Observed accession:
<value>

FT-05 Apple FY2025 Q3 + full P8:
<PASS/FAIL/BLOCKED>

Observed accession:
<value>

FT-06 Toyota FY2025 20-F:
<PASS/FAIL/BLOCKED>

Observed accession:
<value>

FT-07 Kellanova CIK-only amendment:
<PASS/FAIL/BLOCKED>

Observed reason:
<value>

FT-08 Security / HTTP:
<PASS/FAIL/BLOCKED>

FT-09 No-AI / runtime:
<PASS/FAIL/BLOCKED>

FT-10 Idempotent REUSE_DATA:
<PASS/FAIL/BLOCKED>

Repeat network calls:
<count>

Repeat parser reruns:
<count>

FT-11 CN/HK preservation:
<PASS/FAIL/BLOCKED>

Registry focused:
<actual result>

P11 focused:
<actual result>

Full unit:
<actual result>

CN/HK regression:
<actual result>

Compileall:
<PASS/FAIL>

git diff --check:
<PASS/FAIL>

Live SEC:
<RUN/BLOCKED>

Production/test code changed during formal acceptance:
NO

Execution result:
<EXECUTION_PASS/EXECUTION_FAIL/EXECUTION_BLOCKED>

Main merge:
NOT RUN

P11 production availability:
NOT CHANGED

Next action:
CHATGPT INDEPENDENT FINAL ACCEPTANCE REVIEW
```

## 20. Stop

After pushing the evidence commit, stop.

Do not:
- merge main;
- enable US publicly;
- update production capability;
- declare P11 DONE.

Only ChatGPT independent verification may issue `ACCEPTANCE_PASS`.
