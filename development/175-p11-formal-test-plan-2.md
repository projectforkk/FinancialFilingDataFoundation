# 175 — P11 US SEC Provider Formal Test / Acceptance Plan 2

Status: **FORMAL_TEST_PLAN_ISSUED**

Plan owner: ChatGPT independent review  
Execution owner: PC Agent / local Windows environment  
Final result reviewer: ChatGPT independent acceptance review

Exact reviewed production candidate:

`9b7fcc9fc37a423eaafd1dde762e9c81d475df9e`

Code review:

`development/174-p11-code-review-result-9.md`

Code-review commit:

`79f91e0dde8e71547e39229b1118ab553ab4dd38`

Verdict:

`REVIEW_PASS`

Previous failed acceptance candidate:

`2504614265b7a233ef9e4a772544ad63dd6eec37`

Previous failed formal evidence:

`development/171-p11-formal-test-evidence.md`

Acceptance failure review:

`development/172-p11-formal-acceptance-review-1.md`

This plan is a new formal acceptance cycle. The failed execution against the previous candidate remains failed and cannot be reclassified.

## 1. Freeze / governance

Before testing, verify:
- exact candidate exists and is ancestor of branch HEAD;
- all post-candidate changes are documentation-only;
- no dirty production/test changes exist.

Any production/test code drift after the candidate blocks acceptance.

Do not modify production/test code during formal execution. Any defect requiring a code change ends this acceptance cycle with `EXECUTION_FAIL`.

Do not merge main, change `SUPPORTED_MARKETS`, or enable P11 production availability.

## 2. Isolated workspace

Use:

`D:\Codex\FinancialFilingDataFoundation\work\p11-formal-acceptance-9b7fcc9f`

and active worktree source:

`D:\Codex\FinancialFilingDataFoundation\worktrees\active\p11-sec-rebuild-development\src`

Set:
- `FFDF_P11_US_DEV=1`;
- `PYTHONPATH` to active worktree `src`;
- short writable TEMP/TMP directories.

Never use main-checkout source accidentally.

## 3. SEC contact gate

Live SEC requires configured `FFDF_SEC_CONTACT_EMAIL`.

Record only YES/NO. Never record the value.

If missing, run all offline gates and return `EXECUTION_BLOCKED`.

## 4. Frozen live fixtures

Apple FY2025 10-K:
- CIK 0000320193
- period FY
- accession 0000320193-25-000079
- form 10-K
- report period 2025-09-27

Apple FY2025 Q3 10-Q:
- CIK 0000320193
- period Q3
- accession 0000320193-25-000073
- form 10-Q
- report period 2025-06-28

Kellanova FY2024:
- CIK-only 0000055067
- original accession 0001628280-25-007118
- amendment 0000055067-25-000127
- expected controlled result P11_AMENDED_VARIANT_PRESENT

Toyota FY2025:
- CIK 0001094517
- period FY
- accession 0001193125-25-142326
- form 20-F
- report period 2025-03-31

## 5. FT-00 Candidate freeze

PASS requires:
- branch task/p11-sec-rebuild-development;
- candidate SHA exists;
- candidate is ancestor of HEAD;
- post-candidate changes documentation-only;
- no dirty production/test changes;
- git diff --check PASS;
- SUPPORTED_MARKETS remains ("CN","HK");
- P11 production availability remains unavailable.

## 6. FT-01 Deterministic regression

Run:
- Registry focused;
- complete P11 unit suite;
- full unit suite;
- CN/HK regression;
- compileall;
- git diff --check.

Development baselines for this candidate:
- provider/acquisition: 11 passed;
- reviewed FT-08 scope: 84 passed;
- P11 focused: 100 passed;
- full unit: 630 passed;
- CN/HK: 96 passed.

Acceptance requires zero failures.

## 7. FT-02 Registry migration/version gate

Acceptance-only raw SQLite harness must prove:
- early v2-A → v3;
- late v2-B → v3;
- migrated compatibility = INCOMPATIBLE;
- PRAGMA user_version remains 1;
- second reopen idempotent;
- unknown unversioned schema fails closed without mutation;
- future SEC schema version 99 fails closed without mutation.

## 8. FT-03 V3→V4 / reuse

Acceptance-only local harness must prove:

```text
old V3 parsed artifact + local immutable package
→ PARSE_LOCAL
→ network=0
→ V4 produced
→ current PASS+COMPATIBLE+0 blocking
→ REUSE_DATA
→ network=0
→ parser reruns=0
```

Also prove stale parser/schema/wrong-package rows cannot reuse and REVIEW_REQUIRED+COMPATIBLE remains non-reusable.

## 9. FT-04 Apple FY2025 10-K live

Run acquire, ingest, status.

PASS:
- exact frozen accession;
- 10-K;
- report period 2025-09-27;
- company identity US:CIK0000320193;
- VIRTUAL_HTML_V4;
- validation PASS;
- compatibility COMPATIBLE;
- blocking 0;
- research_ready true;
- Raw Facts > 0;
- Evidence > 0;
- package/member hashes verify;
- P8 registration succeeds.

## 10. FT-05 Apple FY2025 Q3 + full P8

Run acquire, ingest, status.

PASS:
- exact frozen accession 0000320193-25-000073;
- 10-Q;
- report period 2025-06-28;
- validation PASS;
- COMPATIBLE;
- blocking 0;
- facts/evidence > 0.

Exercise complete P8 family:
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

P8 must use zero HTTP/acquisition calls.

Check custom aapl: facts and hidden facts when present.

## 11. FT-06 Toyota 20-F

Run acquire, ingest, status.

PASS:
- exact accession 0001193125-25-142326;
- form 20-F;
- report period 2025-03-31;
- facts/evidence > 0;
- PASS/COMPATIBLE/0 blocking;
- P8 read without network;
- deterministic FPI tests prove no automatic quarterly 6-K mapping.

## 12. FT-07 Kellanova amendment / CIK-first

Use CIK only:

`--cik 55067 --year 2024 --period FY`

Do not use ticker K.

PASS only when:
- both frozen original and amendment are discovered;
- result is P11_AMENDED_VARIANT_PRESENT;
- no silent selection;
- no active research-ready conflicted binding.

## 13. FT-08 Security / HTTP / malformed source

This gate MUST rerun in full because it failed the previous formal cycle.

Run the reviewed FT-08 unit scope and the original acceptance-only FT-08 harness.

Mandatory malformed archive-index cases:
- invalid archive JSON;
- invalid directory;
- invalid item list;
- invalid item record.

All must return:

`SecError(P11_SEC_DISCOVERY_FAILED)`

and must never raise:
- UnboundLocalError;
- NameError;
- generic uncontrolled exception.

Also rerun:
- invalid main submissions JSON;
- invalid historical submissions JSON;
- SEC host allowlist;
- redirect host/cap;
- unsafe path cases;
- safe nested path;
- source drift;
- 403 terminal case;
- 429 terminal case;
- Retry-After;
- content-type/byte validation;
- remote script not executed.

Expected focused regression baseline:
- reviewed FT-08 scope: 84 passed.

## 14. FT-09 No-AI/runtime boundary

Verify no production calls/import paths for OpenAI/Anthropic/Gemini/Codex API/MCP sampling/remote LLM.

Verify:
- reviewed SEC runtime dependency boundary;
- shell=False / no filing-controlled shell execution;
- P8 remains read-only and cannot acquire.

## 15. FT-10 Idempotent REUSE_DATA

Use Apple FY after successful live ingest.

Capture package/member/artifact/catalog/Registry state.

Repeat acquire/ingest/status with acceptance-only instrumentation.

PASS:
- same package SHA and member hashes;
- planner/ingest reuses current data;
- HTTP calls = 0;
- acquisition calls = 0;
- parser reruns = 0;
- artifact hashes/counts unchanged;
- no conflicting active binding.

## 16. FT-11 CN/HK preservation

PASS:
- SUPPORTED_MARKETS == ("CN","HK");
- REGISTRY_SCHEMA_VERSION == 1;
- CN/HK regression 96 tests with zero failures;
- no accepted CN/HK raw/source mutation;
- P8 CN/HK behavior unchanged through regression suite.

## 17. Formal result rules

Any required executed gate fails → `EXECUTION_FAIL`.

Required live gate cannot run due to environment/contact/network → `EXECUTION_BLOCKED`.

Only all required gates passing → `EXECUTION_PASS`.

PC Agent must not declare `ACCEPTANCE_PASS`.

## 18. Evidence

Create:

`development/176-p11-formal-test-evidence-2.md`

Evidence commit must be documentation/evidence only.

Raw logs/harness output stay under:

`work/p11-formal-acceptance-9b7fcc9f/evidence/`

Evidence must include:
- exact candidate/review/plan SHA;
- commands and exit codes;
- FT-00..FT-11 results;
- live accessions/forms/report periods;
- package/member hashes;
- V4 parser;
- fact/evidence/table counts;
- P7 compatibility/reuse values;
- P8 results;
- Registry migration results;
- V3→V4 result;
- malformed archive-index exact result;
- 403/429 attempt counts/reason codes;
- reuse network/parser call counts;
- no-AI audit;
- regression counts;
- compileall/diff check;
- explicit declaration of production/test source drift.

## 19. Final handoff

Return:

```text
P11 FORMAL TEST EXECUTION 2: COMPLETE

Production candidate:
9b7fcc9fc37a423eaafd1dde762e9c81d475df9e

Code review:
development/174-p11-code-review-result-9.md

Code review commit:
79f91e0dde8e71547e39229b1118ab553ab4dd38

Formal test plan:
development/175-p11-formal-test-plan-2.md

Formal test plan commit:
<exact SHA>

Formal test evidence:
development/176-p11-formal-test-evidence-2.md

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

FT-08 Security / malformed source:
<PASS/FAIL/BLOCKED>

Malformed archive index result:
<value>

FT-09 No-AI / runtime:
<PASS/FAIL/BLOCKED>

FT-10 Idempotent REUSE_DATA:
<PASS/FAIL/BLOCKED>

Repeat HTTP calls:
<count>

Repeat acquisition calls:
<count>

Repeat parser reruns:
<count>

FT-11 CN/HK preservation:
<PASS/FAIL/BLOCKED>

Provider/acquisition focused:
<actual result>

Reviewed FT-08 scope:
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
CHATGPT INDEPENDENT FINAL ACCEPTANCE REVIEW 2
```

## 20. Stop

After pushing the evidence commit, stop.

Do not merge main, enable US, change supported markets, or declare P11 DONE.
