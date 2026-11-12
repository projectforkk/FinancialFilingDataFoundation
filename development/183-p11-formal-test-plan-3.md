# 183 — P11 US SEC Provider Corrected Formal Test / Acceptance Plan 3

Status: **FORMAL_TEST_PLAN_ISSUED**

Date: 2026-11-12

Plan owner: ChatGPT independent review  
Execution owner: PC Agent / local Windows environment  
Final result reviewer: ChatGPT independent acceptance review

## 1. Acceptance authority and exact freeze

Corrected design baseline:

    09e3174b7e19a60cc5955862670fac8931af67db

Exact reviewed production candidate:

    9389d59d68c84762b55b29bedb973db4ea45256a

Development evidence:

    development/182-p11-issue-131-repair-evidence.md

Development evidence commit:

    0478e8fe1cde7ff5a4e30c5c304bd8db63e1b045

Independent exact-candidate review verdict:

    REVIEW_PASS

Previous candidate:

    5a122478b34e5fce7a3a0e198dd40e5cdb14e07c

Previous verdict:

    CHANGES_REQUIRED — P11-ISSUE-131

This is a new formal acceptance cycle. No prior P11 ACCEPTANCE_PASS is carried forward.

The exact production/test bytes under acceptance are frozen at:

    9389d59d68c84762b55b29bedb973db4ea45256a

Any production/test source change after that SHA invalidates this plan and ends the run.

## 2. Corrected design contracts under formal acceptance

Formal execution must independently verify all corrected design decisions:

- DC-01: online acquire/ingest performs current SEC discovery before reuse planning; no TTL shortcut.
- DC-02: online ticker aliases are re-resolved from current official SEC ticker-map bytes; explicit CIK bypasses ticker-map lookup.
- DC-03: exactly one logical fact source is active: INLINE_XBRL_PRIMARY or XBRL_INSTANCE_PRIMARY.
- DC-04: Inline XBRL continuation/exclude semantics and multi-fragment evidence are correct.
- DC-05: generic OTHER XML cannot supply facts, contexts, or units.
- DC-06: package provenance is verified independently from package SHA.
- DC-07: DOM tables use logical rowspan/colspan grid and real header cells.
- DC-08: production US CLI/P8 works with FFDF_P11_US_DEV absent.
- P11-ISSUE-131: P7/P8 research-ready state is bound to one exact, persisted, integrity-verified SEC discovery observation.

Required version baseline:

    REGISTRY_SCHEMA_VERSION = 1
    SEC_REGISTRY_SCHEMA_VERSION = 4
    SEC_DISCOVERY_SCHEMA = p11-sec-discovery-v1
    VIRTUAL_HTML_NORMALIZER_VERSION = VIRTUAL_HTML_V5
    SEC_ARTIFACT_SCHEMA = p11-sec-artifacts-v2
    SEC_VALIDATION_SCHEMA = p11-sec-validation-v2

Package SHA formula remains unchanged.

## 3. Formal execution governance

PC Agent executes this plan exactly. It may create acceptance-only harnesses and raw logs under the isolated work directory, but it must not alter tracked production/test files.

Before any test:

1. verify the candidate exists;
2. verify it is an ancestor of branch HEAD;
3. list all post-candidate changes;
4. require every post-candidate change to be documentation-only;
5. require a clean working tree except acceptance-only ignored work output.

If any src/, tests/, runtime lock, dependency, packaging, or production configuration byte changed after the candidate:

    EXECUTION_BLOCKED
    REASON: PRODUCTION_TEST_DRIFT_AFTER_REVIEW_PASS

If any formal gate reveals a defect requiring a production/test repair:

    EXECUTION_FAIL

Stop. Do not patch production code during formal acceptance.

Forbidden during this run:

- merge main;
- force push or history rewrite;
- destructive reset/clean;
- amend the production candidate;
- change supported-market declarations;
- weaken an expected result;
- substitute an easier fixture without recording plan failure/blockage;
- declare ACCEPTANCE_PASS;
- declare P11 DONE.

## 4. Isolated acceptance workspace

Use the active P11 worktree source, not the main checkout source.

PowerShell baseline:

~~~powershell
$root = 'D:\Codex\FinancialFilingDataFoundation'
$wt = 'D:\Codex\FinancialFilingDataFoundation\worktrees\active\p11-sec-rebuild-development'
$py = Join-Path $root '.venv\Scripts\python.exe'
$accept = Join-Path $root 'work\p11-formal-acceptance-9389d59d'
$tmp = Join-Path $accept 'tmp'
$evidenceRoot = Join-Path $accept 'evidence'

Set-Location $wt
New-Item -ItemType Directory -Force -Path $accept,$tmp,$evidenceRoot | Out-Null

$env:FFDF_ROOT = $accept
Remove-Item Env:FFDF_P11_US_DEV -ErrorAction SilentlyContinue
$env:PYTHONPATH = (Join-Path $wt 'src')
$env:TEMP = $tmp
$env:TMP = $tmp
~~~

FFDF_P11_US_DEV must remain absent throughout production-mode acceptance.

Record:

- Windows version/identity;
- Python version;
- Git branch and HEAD;
- exact candidate SHA;
- exact formal-plan SHA;
- FFDF_ROOT;
- FFDF_P11_US_DEV presence: must be NO;
- FFDF_SEC_CONTACT_EMAIL configured: YES/NO only.

Never record the actual SEC contact value.

Do not copy accepted CN/HK production raw/source data into the acceptance root.

## 5. SEC contact / external-network gate

Required live SEC tests use the operator-configured FFDF_SEC_CONTACT_EMAIL.

If absent or invalid:

- run every offline gate;
- mark required live gates BLOCKED;
- final execution result = EXECUTION_BLOCKED.

Do not invent or expose a contact identity.

If SEC is unavailable because of external outage/rate/access conditions after the production HTTP policy behaves correctly, record the exact reason and attempts. Required live gates that cannot complete produce EXECUTION_BLOCKED, not a fabricated PASS.

If a frozen live fixture has legitimately changed in current SEC metadata, record EXTERNAL_FIXTURE_DRIFT and stop the affected live gate as BLOCKED pending plan refresh; do not silently change the expected fixture.

## 6. Frozen live fixtures

### FIXTURE-A — Apple FY2025 10-K

- CIK: 0000320193
- ticker alias: AAPL
- fiscal year: 2025
- period: FY
- expected form: 10-K
- expected accession: 0000320193-25-000079
- expected report period: 2025-09-27
- primary document: aapl-20250927.htm

### FIXTURE-B — Apple FY2025 Q3 10-Q

- CIK: 0000320193
- ticker alias: AAPL
- fiscal year: 2025
- period: Q3
- expected form: 10-Q
- expected accession: 0000320193-25-000073
- expected report period: 2025-06-28
- primary document: aapl-20250628.htm

### FIXTURE-C — Kellanova FY2024 amendment conflict

- CIK: 0000055067
- use CIK only; do not use ticker K
- original accession: 0001628280-25-007118
- amendment accession: 0000055067-25-000127
- expected controlled outcome: P11_AMENDED_VARIANT_PRESENT

### FIXTURE-D — Toyota FY2025 20-F

- CIK: 0001094517
- ticker alias: TM
- fiscal year: 2025
- period: FY
- expected form: 20-F
- expected accession: 0001193125-25-142326
- expected report period: 2025-03-31
- primary document: d925022d20f.htm

No quarterly 6-K auto-mapping is permitted.

## 7. FT-00 — Candidate freeze / branch / production-mode preflight

Run:

~~~powershell
Set-Location $wt
git branch --show-current
git status --short
git rev-parse HEAD
git rev-parse 9389d59d68c84762b55b29bedb973db4ea45256a
git merge-base --is-ancestor 9389d59d68c84762b55b29bedb973db4ea45256a HEAD
git diff --name-status 9389d59d68c84762b55b29bedb973db4ea45256a..HEAD
git diff --check
& $py --version
~~~

PASS requires:

- branch = task/p11-sec-rebuild-development;
- candidate resolves exactly;
- candidate is ancestor of HEAD;
- all post-candidate files are documentation/evidence/plan/prompt only;
- no dirty production/test changes;
- git diff --check PASS;
- FFDF_P11_US_DEV absent;
- SUPPORTED_MARKETS includes US exactly as reviewed candidate behavior;
- REGISTRY_SCHEMA_VERSION = 1;
- SEC_REGISTRY_SCHEMA_VERSION = 4;
- SEC_DISCOVERY_SCHEMA = p11-sec-discovery-v1;
- VIRTUAL_HTML_NORMALIZER_VERSION = VIRTUAL_HTML_V5;
- SEC_ARTIFACT_SCHEMA = p11-sec-artifacts-v2;
- SEC_VALIDATION_SCHEMA = p11-sec-validation-v2.

Any mismatch = FAIL/BLOCKED as appropriate.

## 8. FT-01 — Deterministic regression and compile gate

Run with short basetemp paths to avoid Windows path-length noise:

~~~powershell
& $py -m pytest -q tests/unit/us_sec/test_issue131.py tests/unit/us_sec/test_validation_p8.py --basetemp D:\t\p11-ft-issue131
& $py -m pytest -q tests/unit/us_sec --basetemp D:\t\p11-ft-us
& $py -m pytest -q tests/unit --basetemp D:\t\p11-ft-unit
& $py -m pytest -q tests/unit/acquisition tests/unit/identity tests/unit/validation tests/unit/registry tests/unit/mcp tests/unit/research tests/unit/review --basetemp D:\t\p11-ft-p0p10
& $py -m compileall -q src tests
git diff --check
~~~

Reviewed development baselines:

- ISSUE-131/P8 focused: 23 passed;
- complete US SEC: 130 passed;
- full unit: 660 passed;
- P0-P10 focused compatibility: 371 passed;
- compileall: exit 0;
- git diff --check: PASS.

Formal PASS requires zero failures. Higher pass counts are allowed only when collection changed because of documentation/non-production environment reasons; explain every count difference.

No test may be skipped merely because it is inconvenient. Record skips explicitly.

## 9. FT-02 — P11-ISSUE-131 exact discovery-observation trust boundary

This is a mandatory acceptance-only gate even though unit tests cover it.

Use production functions from the frozen candidate and an acceptance-only harness under $evidenceRoot.

### FT-02A valid observation

Construct/register a valid observation and package.

Require:

    P7 validation = PASS
    compatibility = COMPATIBLE
    blocking = 0
    reuse_eligible = true
    research_ready = true
    catalog = ADDED
    P8 get_document succeeds

Record:

- observation SHA;
- source URL(s);
- source SHA(s);
- candidate fingerprint;
- selected accession;
- retrieved_at;
- stable company_id;
- package SHA.

### FT-02B missing observation

Require:

    P7 != PASS
    reuse_eligible = false
    ingest research_ready = false
    catalog not published

### FT-02C missing Registry observation

Delete the exact observation row after successful ingest.

Require subsequent P8 access to fail closed with P8_UPSTREAM_ARTIFACT_INVALID or the reviewed equivalent.

### FT-02D source bytes/hash tamper

After a successful P8 read, mutate Registry source_documents_json body bytes without updating the source hash.

Require the next cached-bundle P8 read to fail closed.

This proves cached P8 access revalidates the Registry chain rather than trusting the first load.

### FT-02E candidate fingerprint / canonical SHA tamper

Independently alter:

- candidate payload while preserving old fingerprint;
- retrieved_at or another canonical field while preserving old observation SHA.

Both must fail closed.

### FT-02F slot/accession/state identity

Prove failures for:

- company_id/CIK mismatch;
- fiscal-year mismatch;
- period mismatch;
- selected accession missing;
- selected accession != package accession;
- state != UNAMBIGUOUS;
- ticker-only company identity such as US:AAPL.

No case may produce research_ready or successful P8 serving.

## 10. FT-03 — Registry v3 → v4 migration / compatibility

Use acceptance-only raw SQLite fixtures.

Mandatory cases:

### FT-03A true current historical SEC Registry v3 → v4

Before:

- legacy PRAGMA user_version = 1;
- SEC metadata version = 3;
- representative source_packages/package_members/bindings/parsed rows.

PASS:

- SEC schema becomes 4;
- PRAGMA remains 1;
- new sec_discovery_observations structure exists;
- existing package/member/binding/parsed identities preserved;
- old parsed V4/v1 artifacts are not falsely considered current V5/v2;
- second reopen is idempotent.

### FT-03B unknown/future shape

Test:

- future SEC schema version 99;
- unknown unversioned SEC shape.

PASS:

- RegistrySchemaUnsupported or reviewed equivalent;
- no migration is performed first;
- tables/indexes/rows/PRAGMA remain unchanged.

### FT-03C CN/HK preservation

Seed representative legacy CN/HK rows before migration and prove byte/logical identity preserved after SEC v4 initialization.

## 11. FT-04 — Old US parsed artifact → V5/v2 current state

Acceptance-only local harness, no SEC network required.

Prove:

    immutable raw SEC package
    + historical VIRTUAL_HTML_V4 / p11-sec-artifacts-v1 parsed state
    + valid current discovery observation
    → old parsed state not reusable
    → PARSE_LOCAL/current reparse path
    → VIRTUAL_HTML_V5 / p11-sec-artifacts-v2
    → P7 PASS + COMPATIBLE + observation-bound
    → later reusable current state

Also prove:

- raw package bytes unchanged;
- old parsed artifact bytes unchanged;
- stale parser row cannot trigger REUSE_DATA;
- stale schema row cannot trigger REUSE_DATA;
- wrong-package parsed row cannot trigger reuse;
- REVIEW_REQUIRED remains non-reusable.

## 12. FT-05 — Deterministic current-discovery lifecycle / ISSUE-123 and ISSUE-127

Use an acceptance-only transport; do not depend on live SEC for this gate.

### FT-05A late amendment after local reuse exists

Stage 1:

    submissions = original filing only
    acquire/ingest succeeds
    package + parsed artifact become reusable

Stage 2:

    same local package/artifact remain
    submissions now include original + amendment

Run online ingest/acquire path again.

PASS requires:

- current submissions metadata fetched before reuse planning;
- local package does not suppress discovery;
- result becomes controlled amendment conflict / REVIEW_REQUIRED;
- no research-ready active binding is published;
- parser/package reuse does not override the fresh conflict.

### FT-05B multiple current non-amendment candidates

Must fail closed / require review; no arbitrary selection.

### FT-05C not found

Must return controlled not-found result and no research-ready publication.

### FT-05D discovery network failure with local reusable data

Must not silently reuse stale local metadata.

### FT-05E status

status is local-only:

- zero network calls;
- reports persisted discovery_checked_at / observation identity.

### FT-05F ticker alias freshness

For ticker-based online acquire/ingest:

- fetch current official company_tickers.json;
- reparse authenticated source bytes;
- derivative mapping tamper is rejected;
- explicit CIK path performs zero ticker-map fetches.

## 13. FT-06 — Fact-source, Inline XBRL, OTHER XML, and evidence semantics

Run reviewed deterministic tests plus acceptance-only spot checks.

PASS must prove:

- INLINE_XBRL_PRIMARY emits logical facts only from primary Inline XBRL;
- extracted instance does not duplicate those facts;
- XBRL_INSTANCE_PRIMARY uses exactly one verified instance when no supported inline facts exist;
- multiple plausible instances fail closed/review;
- chained continuation resolves deterministically;
- ix:exclude content is removed from logical value;
- missing continuation fails;
- duplicate continuation target fails;
- cyclic continuation fails;
- all source fragments are ordered and re-resolve to immutable member bytes;
- custom QName retained;
- dimensions/context/unit semantics preserved;
- OTHER XML cannot supply facts, contexts, or units;
- primary inline fact cannot borrow same-ID context/unit from another member.

Record logical fact counts by fact_source_mode.

## 14. FT-07 — DOM table logical grid/header semantics

Acceptance must prove:

- colspan expands logical width correctly;
- rowspan occupies subsequent logical grid slots;
- first-row td is not automatically HEADER;
- actual th cells drive header_tree;
- multi-row th + span coverage is deterministic;
- cell/source-member locators resolve;
- table/fact/evidence traceability remains valid.

## 15. FT-08 — Package provenance / HTTP / security / malformed-source gate

Run reviewed security/acquisition scope and acceptance-only harnesses.

Mandatory:

- exact source URL ↔ CIK/accession/relative-name binding;
- Registry source_packages and package_members comparisons;
- source drift cannot silently overwrite;
- package/member path safety;
- SEC host allowlist;
- redirect host validation;
- redirect cap;
- encoded traversal/backslash/Windows drive path rejection;
- valid nested SEC relative path acceptance;
- content-type header validation;
- actual-byte validation;
- bounded response/member/package sizes;
- invalid main submissions JSON;
- invalid historical submissions JSON;
- malformed archive index JSON/directory/item list/item record;
- terminal 403 → controlled P11_SEC_ACCESS_DENIED;
- terminal 429 → controlled P11_SEC_RATE_LIMITED;
- bounded Retry-After behavior;
- connect/read/total timeout contract;
- no JS execution / no filing-controlled remote subresource execution;
- no uncontrolled NameError/UnboundLocalError/generic crash in malformed-source cases.

Record attempt counts for simulated 403/429.

## 16. FT-09 — Production capability and P8 no-network boundary

FFDF_P11_US_DEV must remain absent.

Prove in production mode:

- CompanyRef/FilingSlotKey accepts reviewed US cases;
- Q2 remains US-only;
- normal US CLI acquire/ingest/status is not dev-flag gated;
- P8 accepts valid US catalog entries;
- P8 does not perform SEC acquisition/network I/O;
- CN/HK paths retain existing behavior.

Also audit production imports/source for forbidden remote AI/LLM calls:

- OpenAI;
- Anthropic;
- Gemini;
- Codex API;
- MCP sampling;
- other remote LLM services.

SEC subprocess/runtime path must remain reviewed and not permit filing-controlled arbitrary shell execution.

## 17. FT-10 — Live Apple FY2025 10-K production-mode E2E

Requires SEC contact configured.

Run with FFDF_P11_US_DEV absent:

~~~powershell
& $py -m financial_filing_data_foundation.user_cli acquire --market US --cik 320193 --ticker AAPL --year 2025 --period FY
& $py -m financial_filing_data_foundation.user_cli ingest  --market US --cik 320193 --ticker AAPL --year 2025 --period FY
& $py -m financial_filing_data_foundation.user_cli status  --market US --cik 320193 --ticker AAPL --year 2025 --period FY
~~~

PASS requires:

- current discovery observation persisted;
- official discovery source bytes/hash recorded and verifiable;
- stable company_id US:CIK0000320193;
- exact expected accession/form/report period unless external fixture drift is documented;
- package/member hashes verify;
- parser = VIRTUAL_HTML_V5;
- artifact schema = p11-sec-artifacts-v2;
- validation schema = p11-sec-validation-v2;
- validation PASS;
- compatibility COMPATIBLE;
- blocking = 0;
- reuse_eligible = true;
- research_ready = true;
- observation SHA in validation/catalog/Registry is identical;
- selected accession matches package;
- Raw Facts > 0;
- Evidence > 0;
- P8 catalog registration succeeds.

Record package SHA, member count, member SHAs, observation SHA, discovery source SHA(s), fact_source_mode, fact/evidence/table counts.

## 18. FT-11 — Live Apple FY2025 Q3 + complete P8 family

Run acquire/ingest/status in production mode with the frozen Q3 slot.

PASS requires the same trust requirements as FT-10 and expected accession 0000320193-25-000073 unless external fixture drift is documented.

Exercise all accepted P8 tools:

- list_documents;
- get_document;
- search_document;
- read_pages;
- list_sections;
- list_tables;
- get_table;
- list_raw_facts;
- get_fact;
- get_evidence;
- get_validation.

Instrument network/acquisition entry points.

P8 PASS requires:

- HTTP/acquisition calls = 0;
- virtual HTML pagination explicit;
- raw_qname filtering works;
- fact ↔ evidence round-trip;
- evidence member SHA belongs to verified package;
- table/cell locators resolve when tables exist;
- discovery_checked_at and observation identity exposed;
- Registry observation is verified on access.

For custom aapl: facts and hidden Inline XBRL facts, record actual counts and verify evidence when present.

## 19. FT-12 — Live Toyota FY2025 20-F

Run acquire/ingest/status with FFDF_P11_US_DEV absent.

PASS requires:

- current observation persisted/verified;
- expected accession 0001193125-25-142326 unless external fixture drift;
- form 20-F;
- report period 2025-03-31;
- V5/v2;
- validation PASS / COMPATIBLE / zero blocking;
- research_ready true;
- facts/evidence > 0;
- P8 read works with zero network.

Also run deterministic FPI policy test proving quarterly 6-K is not guessed.

## 20. FT-13 — Live Kellanova amendment conflict / CIK-first

Use CIK only:

~~~powershell
& $py -m financial_filing_data_foundation.user_cli acquire --market US --cik 55067 --year 2024 --period FY
~~~

Do not pass ticker K.

Expected controlled non-success:

    P11_AMENDED_VARIANT_PRESENT

PASS requires:

- discovery sees original 0001628280-25-007118;
- discovery sees amendment 0000055067-25-000127;
- exact discovery observation is persisted with non-UNAMBIGUOUS conflict state as appropriate;
- no silent accession selection;
- no ticker-map dependency;
- no research-ready binding/catalog row for conflicted slot.

A normal successful research-ready acquisition is FAIL.

## 21. FT-14 — Online repeat discovery + immutable reuse classification

This gate replaces the obsolete pre-correction expectation that repeat online ingest has zero HTTP calls.

Use FIXTURE-A after FT-10.

Capture before:

- package SHA;
- manifest/member SHAs;
- V5/v2 artifact hashes;
- fact/evidence/table counts;
- Registry parsed row;
- catalog identity;
- previous discovery observation SHA.

Instrument calls by category:

1. ticker-map discovery;
2. submissions/history discovery;
3. archive-index/member acquisition;
4. parser execution.

### FT-14A explicit CIK repeat acquire/ingest

Run repeat online acquire/ingest for the same slot.

PASS:

- current submissions/history discovery is fetched again before reuse planning;
- discovery call count > 0;
- ticker-map calls = 0 for explicit CIK;
- if selected accession remains unchanged: archive member redownload = 0;
- if parsed artifact remains current: parser reruns = 0;
- same package/member bytes;
- same V5/v2 artifact bytes;
- new or revalidated discovery observation is bound to P7/catalog;
- result remains research-ready only if current state is UNAMBIGUOUS.

### FT-14B ticker-based repeat

Run ticker-based online path.

PASS:

- current ticker map is fetched again;
- current submissions metadata is fetched again;
- archive member redownload = 0 when accession unchanged;
- parser reruns = 0 when current artifact reusable.

### FT-14C status

Run status.

PASS:

- total network calls = 0;
- parser calls = 0;
- persisted discovery as-of identity is reported.

If current discovery reveals an amendment/conflict, the correct PASS behavior is fail-closed/review, not forced reuse.

## 22. FT-15 — CN/HK and P0-P10 preservation

In addition to FT-01:

- verify REGISTRY_SCHEMA_VERSION remains 1;
- verify Q2 remains US-only;
- verify representative CN/HK Registry rows survive SEC v4 operations;
- run existing CN/HK/P8/P9/P10 deterministic tests;
- confirm acceptance root contains no copied/mutated accepted CN/HK production source data;
- confirm no accepted CN/HK raw/artifact mutation.

No live CN/HK acquisition is required if it risks accepted production state.

## 23. Formal execution result rules

For each FT gate record exactly:

    PASS
    FAIL
    BLOCKED

Rules:

- any required executed assertion fails → EXECUTION_FAIL;
- production/test code change becomes necessary → EXECUTION_FAIL and stop;
- required live gate unavailable due to contact/network/external fixture drift → EXECUTION_BLOCKED;
- only every required offline and live gate passing → EXECUTION_PASS.

PC Agent does not decide ACCEPTANCE_PASS.

Only ChatGPT independent final review may issue:

    ACCEPTANCE_PASS
    ACCEPTANCE_FAILED

## 24. Formal evidence artifact

PC Agent must create:

    development/185-p11-formal-test-evidence-3.md

The evidence commit must be documentation/evidence only.

Raw logs and acceptance-only harness outputs stay under:

    D:\Codex\FinancialFilingDataFoundation\work\p11-formal-acceptance-9389d59d\evidence\

Do not commit:

- SEC contact value;
- secrets;
- production source/test changes;
- large raw SEC filing bodies unless already tracked by project policy.

Evidence must include:

- exact candidate SHA;
- corrected design baseline;
- exact formal-plan path and plan commit SHA;
- exact execution-prompt path and prompt commit SHA;
- environment details;
- all commands and exit codes;
- FT-00 through FT-15 results;
- focused/full test counts;
- all skips;
- live accessions/forms/report periods;
- package/member hashes;
- discovery observation SHA(s);
- discovery source URL/hash inventory;
- candidate fingerprint;
- fact_source_mode and logical fact counts;
- validation status/compatibility/reuse/blocking;
- P8 tool results and network call count;
- Registry v3→v4 migration results;
- old V4/v1 → V5/v2 transition;
- ISSUE-131 tamper results;
- late-amendment lifecycle result;
- ticker freshness result;
- malformed-source/security results;
- 403/429 reason/attempt counts;
- repeat online call classification: discovery vs archive vs parser;
- status network count;
- CN/HK/P0-P10 regression result;
- compileall and diff-check;
- explicit statement whether production/test source changed during formal execution.

## 25. Required final PC Agent handoff

Return exactly this structure:

~~~text
P11 FORMAL TEST EXECUTION 3: COMPLETE

Branch:
task/p11-sec-rebuild-development

Corrected design baseline:
09e3174b7e19a60cc5955862670fac8931af67db

Production candidate:
9389d59d68c84762b55b29bedb973db4ea45256a

Formal test plan:
development/183-p11-formal-test-plan-3.md

Formal test plan commit:
<exact SHA>

Execution prompt:
development/184-p11-formal-test-execution-prompt-3.md

Execution prompt commit:
<exact SHA>

Formal test evidence:
development/185-p11-formal-test-evidence-3.md

Evidence commit:
<exact SHA>

FT-00 Candidate freeze:
<PASS/FAIL/BLOCKED>

FT-01 Regression / compile:
<PASS/FAIL/BLOCKED>

FT-02 ISSUE-131 trust boundary:
<PASS/FAIL/BLOCKED>

FT-03 Registry v3→v4:
<PASS/FAIL/BLOCKED>

FT-04 V4/v1→V5/v2 compatibility:
<PASS/FAIL/BLOCKED>

FT-05 Discovery freshness / ticker:
<PASS/FAIL/BLOCKED>

FT-06 Fact-source / continuation / OTHER XML:
<PASS/FAIL/BLOCKED>

FT-07 DOM table semantics:
<PASS/FAIL/BLOCKED>

FT-08 Provenance / HTTP / security:
<PASS/FAIL/BLOCKED>

FT-09 Production capability / no-AI / P8 no-network:
<PASS/FAIL/BLOCKED>

FT-10 Apple FY2025 10-K:
<PASS/FAIL/BLOCKED>

Observed accession:
<value>

Observation SHA:
<value>

FT-11 Apple FY2025 Q3 + P8:
<PASS/FAIL/BLOCKED>

Observed accession:
<value>

P8 HTTP/acquisition calls:
<count>/<count>

FT-12 Toyota FY2025 20-F:
<PASS/FAIL/BLOCKED>

Observed accession:
<value>

FT-13 Kellanova amendment:
<PASS/FAIL/BLOCKED>

Observed reason:
<value>

FT-14 Repeat online discovery + reuse:
<PASS/FAIL/BLOCKED>

Explicit-CIK discovery calls:
<count>

Explicit-CIK ticker-map calls:
<count>

Repeat archive member downloads:
<count>

Repeat parser reruns:
<count>

Ticker-based ticker-map calls:
<count>

Status network calls:
<count>

FT-15 CN/HK + P0-P10:
<PASS/FAIL/BLOCKED>

ISSUE-131/P8 focused:
<actual result>

US SEC:
<actual result>

Full unit:
<actual result>

P0-P10 focused:
<actual result>

Compileall:
<PASS/FAIL>

git diff --check:
<PASS/FAIL>

FFDF_P11_US_DEV present:
NO

Live SEC:
<RUN/BLOCKED>

Production/test code changed during formal acceptance:
NO

Execution result:
<EXECUTION_PASS/EXECUTION_FAIL/EXECUTION_BLOCKED>

Main merge:
NOT RUN

P11 DONE:
NO

Next action:
CHATGPT INDEPENDENT FINAL ACCEPTANCE REVIEW 3
~~~

## 26. Stop boundary

After creating and pushing the evidence commit, stop.

Do not:

- merge main;
- modify production/test code;
- create a new candidate;
- declare ACCEPTANCE_PASS;
- declare P11 DONE.

The next lifecycle action is exclusively:

    CHATGPT INDEPENDENT FINAL ACCEPTANCE REVIEW 3
