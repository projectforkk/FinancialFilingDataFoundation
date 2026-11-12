# 184 — P11 Formal Test Execution Prompt 3

You are the PC Agent responsible for executing the independent formal validation of the frozen P11 US SEC provider candidate.

This is an execution task, not a development task.

## 1. Exact authority

Repository:

    projectforkk/FinancialFilingDataFoundation

Branch:

    task/p11-sec-rebuild-development

Corrected design baseline:

    09e3174b7e19a60cc5955862670fac8931af67db

Frozen production candidate under acceptance:

    9389d59d68c84762b55b29bedb973db4ea45256a

Development evidence:

    development/182-p11-issue-131-repair-evidence.md

Evidence commit:

    0478e8fe1cde7ff5a4e30c5c304bd8db63e1b045

Formal Test Plan:

    development/183-p11-formal-test-plan-3.md

Formal Test Plan commit:

    4e4961dd4b37b2bd50c2d162ea99fa155fbfff27

Independent review verdict:

    REVIEW_PASS

You must execute the plan exactly as written at the exact plan commit above.

Do not redesign, weaken, substitute, or skip required gates.

## 2. Lifecycle boundary

Formal Acceptance is NOT yet granted.

Your role is to execute tests and produce evidence only.

You must not:

- modify src/ or tests/;
- repair production defects;
- amend the frozen candidate;
- create a replacement production candidate;
- merge main;
- force push;
- reset/clean destructively;
- change supported-market semantics;
- set FFDF_P11_US_DEV to enable US;
- declare ACCEPTANCE_PASS;
- declare P11 DONE.

If a production/test repair becomes necessary:

    EXECUTION_FAIL
    STOP
    RETURN TO NEW CANDIDATE CYCLE

## 3. Start by synchronizing the documentation-only branch state

Worktree:

    D:\Codex\FinancialFilingDataFoundation\worktrees\active\p11-sec-rebuild-development

Repository root:

    D:\Codex\FinancialFilingDataFoundation

First run:

~~~powershell
Set-Location 'D:\Codex\FinancialFilingDataFoundation\worktrees\active\p11-sec-rebuild-development'

git status --short
git branch --show-current
git rev-parse HEAD
git log -8 --oneline --decorate
git remote -v
git fetch origin
git rev-parse origin/task/p11-sec-rebuild-development
~~~

Expected remote history includes:

    9389d59d... production candidate
      ↓
    0478e8fe... ISSUE-131 development evidence
      ↓
    4e4961dd4b37b2bd50c2d162ea99fa155fbfff27 formal plan

If local branch is behind and the worktree is clean, synchronize only by safe fast-forward:

~~~powershell
git merge --ff-only origin/task/p11-sec-rebuild-development
~~~

Do not use reset, rebase, checkout-overwrite, force, or clean.

If local and remote diverge:

    EXECUTION_BLOCKED
    REASON: BRANCH_DIVERGENCE

Stop and report.

## 4. Verify the exact plan before execution

Run:

~~~powershell
git cat-file -t 9389d59d68c84762b55b29bedb973db4ea45256a
git cat-file -t 4e4961dd4b37b2bd50c2d162ea99fa155fbfff27
git merge-base --is-ancestor 9389d59d68c84762b55b29bedb973db4ea45256a HEAD
git diff --name-status 9389d59d68c84762b55b29bedb973db4ea45256a..HEAD
git status --short
~~~

PASS requires:

- candidate object exists;
- plan commit exists;
- candidate is ancestor of HEAD;
- every post-candidate path is documentation only;
- no src/, tests/, runtime lock, dependency, packaging, or production-config drift;
- working tree is clean before acceptance execution.

If production/test drift is present:

    EXECUTION_BLOCKED
    REASON: PRODUCTION_TEST_DRIFT_AFTER_REVIEW_PASS

Do not continue.

## 5. Read the authority files before running tests

Read completely:

    design/26-p11-sec-provider-design.md
    design/27-p11-implementation-plan.md
    design/32-p11-us-scope-reopening.md
    design/33-p11-post-acceptance-design-correction.md
    development/178-p11-full-design-code-consistency-reaudit.md
    development/182-p11-issue-131-repair-evidence.md
    development/183-p11-formal-test-plan-3.md

Do not rely on older formal plans 156/170/175 as current authority. They are historical evidence only.

## 6. Acceptance environment

Use:

    D:\Codex\FinancialFilingDataFoundation\work\p11-formal-acceptance-9389d59d

Use the project venv:

    D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe

Set PYTHONPATH to the active worktree src.

Critically:

    FFDF_P11_US_DEV MUST BE ABSENT

Remove it explicitly before testing.

Do not record the value of FFDF_SEC_CONTACT_EMAIL; record only configured YES/NO.

Raw logs and acceptance-only harnesses go under:

    D:\Codex\FinancialFilingDataFoundation\work\p11-formal-acceptance-9389d59d\evidence\

Do not place acceptance harnesses into tracked src/ or tests/.

## 7. Execute every formal gate in Plan 183

Execute FT-00 through FT-15 exactly.

Required groups are:

    FT-00 Candidate freeze / production-mode preflight
    FT-01 Deterministic regression and compile
    FT-02 ISSUE-131 exact discovery-observation trust boundary
    FT-03 Registry v3→v4 migration / compatibility
    FT-04 V4/v1→V5/v2 current-state compatibility
    FT-05 Current discovery / late amendment / ticker freshness
    FT-06 Fact-source / continuation / OTHER XML / evidence
    FT-07 DOM table logical grid/header semantics
    FT-08 Package provenance / HTTP / security / malformed source
    FT-09 Production capability / no-dev-flag / no-AI / P8 no-network
    FT-10 Live Apple FY2025 10-K
    FT-11 Live Apple FY2025 Q3 + complete P8
    FT-12 Live Toyota FY2025 20-F
    FT-13 Live Kellanova amendment conflict
    FT-14 Repeat online discovery + immutable reuse classification
    FT-15 CN/HK and P0-P10 preservation

Do not collapse FT groups merely because unit tests overlap them. Acceptance-only trust-boundary and lifecycle harnesses are mandatory where Plan 183 requires them.

## 8. Mandatory corrected repeat-run semantics

This is a critical corrected-design acceptance point.

Do NOT use the obsolete expectation:

    repeat online ingest → HTTP calls = 0

That expectation is invalid after DC-01/DC-02.

For repeat online acquire/ingest you must classify calls.

Expected for explicit-CIK repeat when the accession is unchanged:

    current submissions/history discovery calls > 0
    ticker-map calls = 0
    archive member redownloads = 0
    parser reruns = 0

Expected for ticker-based repeat when the accession is unchanged:

    current ticker-map fetch > 0
    current submissions/history discovery calls > 0
    archive member redownloads = 0
    parser reruns = 0

Expected for status:

    network calls = 0
    parser reruns = 0

A run that skips current discovery because reusable local data exists is FAIL.

## 9. Mandatory ISSUE-131 formal trust-boundary proof

Do not treat the existing 130/660 unit results alone as sufficient.

The formal run must independently prove, using frozen production functions:

- P7 cannot PASS with no exact observation;
- missing observation cannot become research_ready;
- exact observation must exist in Registry;
- source bytes are base64-decoded and rehashed;
- candidate fingerprint is recomputed;
- canonical observation SHA is recomputed;
- stable CIK slot identity is enforced;
- selected accession must match package;
- non-UNAMBIGUOUS state cannot become research-ready;
- ticker-only company identity is rejected;
- P8 fails if Registry observation is deleted;
- P8 fails if Registry source bytes are tampered after an initial successful cached read;
- valid exact observation positive path still serves successfully.

Record exact reason/status for every negative case.

## 10. Live SEC execution policy

Live gates require FFDF_SEC_CONTACT_EMAIL to be configured.

If it is absent:

- run all offline gates;
- mark live gates BLOCKED;
- final result = EXECUTION_BLOCKED.

If SEC itself is unavailable/rate-blocked despite correct production handling:

- record exact controlled reason and attempt count;
- do not fake a successful live receipt;
- mark required live gate BLOCKED where appropriate.

If a frozen fixture has legitimately changed in current SEC metadata:

    EXTERNAL_FIXTURE_DRIFT

Record the observed current metadata and mark the affected live gate BLOCKED pending plan refresh.

Do not alter Plan 183 expectations during the run.

## 11. Regression baselines

Reviewed development baselines:

    ISSUE-131/P8 focused: 23 passed
    US SEC: 130 passed
    full unit: 660 passed
    P0-P10 focused: 371 passed
    compileall: exit 0
    git diff --check: PASS

Formal execution requires zero failures.

Use short pytest basetemp paths as prescribed by Plan 183.

Every skipped test must be listed and justified.

Do not silently ignore collection or path failures.

## 12. Formal result classification

Each FT gate:

    PASS
    FAIL
    BLOCKED

Overall:

- any required executed assertion fails → EXECUTION_FAIL;
- production/test repair required → EXECUTION_FAIL and stop;
- required live gate unavailable → EXECUTION_BLOCKED;
- all required gates pass → EXECUTION_PASS.

You do NOT convert EXECUTION_PASS into ACCEPTANCE_PASS.

## 13. Evidence document

After execution create exactly:

    development/185-p11-formal-test-evidence-3.md

It must contain the full evidence required by Plan 183, including:

- candidate SHA;
- design baseline;
- plan path + plan commit;
- prompt path + prompt commit;
- environment;
- every command and exit code;
- FT-00..FT-15 verdicts;
- exact unit/compile counts;
- live filing receipts;
- package/member hashes;
- observation/source hashes;
- candidate fingerprints;
- Registry migration results;
- ISSUE-131 tamper evidence;
- late-amendment evidence;
- ticker freshness evidence;
- fact_source_mode counts;
- security/403/429 results;
- P8 no-network evidence;
- repeat discovery/archive/parser call classification;
- status network count;
- CN/HK/P0-P10 preservation;
- explicit production/test drift declaration.

Before committing evidence, run:

~~~powershell
git status --short
git diff --check
git diff --name-status 9389d59d68c84762b55b29bedb973db4ea45256a..HEAD
~~~

No production/test changes are allowed.

Commit only the evidence document:

    docs: record P11 formal test evidence 3

Do not commit raw logs, secrets, source/test modifications, or SEC contact data.

Push by normal fast-forward only.

No force push.

## 14. Post-evidence verification

After push:

~~~powershell
git fetch origin
git rev-parse HEAD
git rev-parse origin/task/p11-sec-rebuild-development
git log -8 --oneline --decorate
git diff --name-status 9389d59d68c84762b55b29bedb973db4ea45256a..HEAD
~~~

Require all post-candidate changes to remain documentation-only.

Record the exact evidence commit SHA.

## 15. Required final handoff

Return exactly:

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
4e4961dd4b37b2bd50c2d162ea99fa155fbfff27

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

## 16. Stop

After the evidence commit is pushed and the final handoff is returned, STOP.

Do not merge main.
Do not change production/test code.
Do not declare acceptance.
Do not declare P11 DONE.

The next action belongs exclusively to ChatGPT independent final acceptance review.
