# 180 — P11 Corrected Design Repair — PC Agent Command Prompt

Status: **READY TO EXECUTE**

Use this prompt as the complete PC Agent implementation instruction.

---

You are the implementation agent for `projectforkk/FinancialFilingDataFoundation`.

Your task is to implement the corrected P11 US SEC design in one coherent repair
wave and produce one new merge-ready production candidate.

## Authoritative baseline

Repository:

`projectforkk/FinancialFilingDataFoundation`

Worktree:

`D:\Codex\FinancialFilingDataFoundation\worktrees\active\p11-sec-rebuild-development`

Branch:

`task/p11-sec-rebuild-development`

Corrected design baseline:

`09e3174b7e19a60cc5955862670fac8931af67db`

Previous production candidate:

`9b7fcc9fc37a423eaafd1dde762e9c81d475df9e`

Mandatory reading before code changes:

- `design/26-p11-sec-provider-design.md`
- `design/27-p11-implementation-plan.md`
- `design/32-p11-us-scope-reopening.md`
- `design/33-p11-post-acceptance-design-correction.md`
- `development/178-p11-full-design-code-consistency-reaudit.md`
- `development/179-p11-corrected-design-repair-plan.md`

The corrected design overrides conflicting older P11 behavior.

Do not ask for confirmation. Do not weaken the design to preserve old tests.

## Preflight

Before editing:

```powershell
git status --short
git branch --show-current
git rev-parse HEAD
git rev-parse 09e3174b7e19a60cc5955862670fac8931af67db
git diff --stat 9b7fcc9fc37a423eaafd1dde762e9c81d475df9e..HEAD
```

Confirm:

- correct branch;
- clean worktree;
- HEAD contains the corrected design baseline;
- no uncommitted source/test changes.

Never use destructive `git reset --hard`, `git clean`, force push or history
rewrite.

## Required target versions

Implement exactly:

```text
REGISTRY_SCHEMA_VERSION = 1
SEC_REGISTRY_SCHEMA_VERSION = 4
SEC_DISCOVERY_SCHEMA = p11-sec-discovery-v1
VIRTUAL_HTML_NORMALIZER_VERSION = VIRTUAL_HTML_V5
SEC_ARTIFACT_SCHEMA = p11-sec-artifacts-v2
SEC_VALIDATION_SCHEMA = p11-sec-validation-v2
```

Do not change the SEC package SHA formula.

## Repair all issues 123–130

### ISSUE-123 — late amendment / discovery freshness

Online US `acquire` and `ingest` must fetch current submissions/history metadata
before any REUSE_DATA/PARSE_LOCAL return.

Persist a deterministic immutable discovery observation with official source
hashes, candidate set, selected accession/conflict state and retrieved_at.

Required sequence:

```text
CIK
→ current SEC discovery
→ persist observation
→ amendment/conflict/not-found gate
→ REUSE_DATA | PARSE_LOCAL | DISCOVER_AND_ACQUIRE
```

A cached original followed by a newly visible /A must become REVIEW_REQUIRED.

If discovery cannot be completed, cached data must not be silently presented as
currently research-ready.

`status` remains local-only and reports discovery-as-of state.

### ISSUE-127 — ticker provenance

For online ticker-based acquire/ingest, use the current official ticker-map bytes.

Cached snapshot lookup must:

1. verify source bytes SHA;
2. reparse mapping from those verified bytes;
3. reject any derivative mapping mismatch.

Explicit CIK bypass remains.

### ISSUE-126 — unrelated XML isolation

Remove "download all XML-family files" behavior.

Use deterministic SEC XBRL attachment metadata and exact filing-local references.

`OTHER` XML must never provide facts, contexts or units.

Add a fixture where unrelated XML contains a colliding context ID and prove it
cannot resolve a primary fact.

### ISSUE-124 — one logical fact source

Implement exactly two modes:

`INLINE_XBRL_PRIMARY`
- logical P6 facts only from primary iXBRL;
- primary iXBRL contexts/units only;
- extracted instance is not another logical fact set.

`XBRL_INSTANCE_PRIMARY`
- only when primary has no supported iXBRL facts;
- exactly one verified instance;
- multiple plausible instances fail closed.

Persist/expose `fact_source_mode`.

Do not implement fuzzy semantic dedupe as a substitute for this source rule.

### ISSUE-125 — continuation/exclude

Implement deterministic Inline XBRL:

- continuedAt;
- ix:continuation;
- chained continuation;
- ix:exclude;
- missing target;
- duplicate target;
- cycle detection.

One logical fact may have ordered multi-fragment evidence.

Every source fragment must round-trip to immutable bytes through its DOM locator and
hash.

Invalid continuation must not fabricate a value.

### ISSUE-128 — provenance

Keep package SHA unchanged.

Verify exact member URL against:

`package CIK + normalized accession + relative_name`.

P7/P8 must compare package + members to Registry source_packages/package_members.

Manifest/Registry/source URL tampering must fail closed.

### ISSUE-129 — tables

Fix DOM table semantics:

- logical grid width honors colspan/rowspan;
- column_count = occupied logical width;
- value_column_count = same logical-width compatibility field for SEC HTML;
- first-row td is not HEADER;
- header_tree comes from real header cells/span coverage.

### ISSUE-130 — production gate

The candidate must be merge-ready.

Normal US CLI and P8 must work when `FFDF_P11_US_DEV` is absent.

Update the feature-branch public supported-market/capability declarations to the
intended production state.

Do not merge main and do not claim accepted production availability.

## Registry v4 requirements

Create a genuine additive v3→v4 migration.

Persist discovery observations.

Tests must prove:

- legacy user_version remains 1;
- existing SEC rows survive;
- migration is idempotent;
- future/unknown SEC schema fails before mutation;
- CN/HK legacy rows are unchanged.

Do not weaken the already-fixed future-schema fail-closed behavior.

## Compatibility requirements

V4 / `p11-sec-artifacts-v1` parsed artifacts are not current-compatible.

Old raw package bytes remain reusable.

After current discovery:

- current V5/v2 artifact → REUSE_DATA;
- local package but stale V4/v1 artifact → PARSE_LOCAL;
- no local package → archive acquisition.

Do not mutate old artifact directories.

## Mandatory tests to add

At minimum:

1. cached original → later amendment → REVIEW_REQUIRED;
2. REUSE_DATA still performs metadata discovery;
3. unchanged accession repeat: zero archive-member download;
4. reusable artifact repeat: zero parser rerun;
5. status: zero network + discovery_checked_at;
6. ticker snapshot derivative tamper;
7. ticker source-byte tamper;
8. unrelated XML not downloaded;
9. unrelated XML context collision ignored;
10. iXBRL + extracted instance → one logical fact set;
11. non-inline + instance path;
12. multiple instance ambiguity;
13. single continuation;
14. chained continuation;
15. ix:exclude;
16. missing/duplicate/cyclic continuation;
17. multi-fragment evidence verification;
18. source URL CIK/accession/name tamper;
19. Registry/package provenance tamper;
20. colspan-only width;
21. rowspan;
22. first-row td body;
23. multi-level th header tree;
24. Registry v3→v4 + idempotence;
25. future Registry no-mutation;
26. US CLI without FFDF_P11_US_DEV;
27. P8 US without FFDF_P11_US_DEV;
28. full CN/HK regression.

## Developer verification

Use the local project Python:

```powershell
$root = "D:\Codex\FinancialFilingDataFoundation"
$wt   = "D:\Codex\FinancialFilingDataFoundation\worktrees\active\p11-sec-rebuild-development"
Set-Location $wt
$py = ".\.venv\Scripts\python.exe"

& $py -m compileall src
& $py -m pytest tests/unit/us_sec -q
& $py -m pytest tests/unit -q
git diff --check
git status --short
```

If the active worktree uses the root virtualenv rather than a worktree-local one,
resolve the correct existing Python path without creating a new uncontrolled runtime.

Run focused CN/HK/P8/P9/P10 tests as needed to make non-regression explicit.

Do not run formal live SEC acceptance in this task.

## Candidate freeze

After all developer tests pass:

1. review `git diff` and `git diff --check`;
2. ensure no unrelated files changed;
3. commit production code + tests only.

Suggested commit:

`fix: implement corrected P11 SEC semantics and production gate`

Record that SHA as:

`NEW_P11_PRODUCTION_CANDIDATE`.

Push the branch.

After this commit, production/test files are frozen.

## Development evidence

Create:

`development/181-p11-corrected-design-repair-evidence.md`

Evidence must include:

- corrected design baseline:
  `09e3174b7e19a60cc5955862670fac8931af67db`;
- previous candidate:
  `9b7fcc9fc37a423eaafd1dde762e9c81d475df9e`;
- NEW_P11_PRODUCTION_CANDIDATE SHA;
- exact changed source/test files;
- version constants;
- Registry migration result;
- ISSUE-123..130 closure table;
- all developer commands/exit codes/pass counts;
- explicit production-mode no-dev-flag test result;
- CN/HK regression result;
- statement that accepted CN/HK raw/artifacts were not mutated;
- statement:
  `FORMAL ACCEPTANCE NOT RUN`.

Commit evidence separately as documentation-only and push.

## Final stop

Do not:

- modify production/test code after candidate freeze;
- create a formal acceptance plan;
- run formal live acceptance;
- merge main;
- declare P11 accepted/DONE.

Final response must report:

```text
CORRECTED DESIGN BASELINE:
09e3174b7e19a60cc5955862670fac8931af67db

NEW P11 PRODUCTION CANDIDATE:
<sha>

DEVELOPMENT EVIDENCE:
development/181-p11-corrected-design-repair-evidence.md
<evidence commit sha>

DEVELOPER TESTS:
<counts>

FORMAL ACCEPTANCE:
NOT RUN

NEXT ACTION:
CHATGPT EXACT-CANDIDATE REVIEW OF <sha>
```
