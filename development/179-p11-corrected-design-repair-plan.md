# 179 — P11 Corrected Design Repair Plan

Status: **READY FOR IMPLEMENTATION — DO NOT START FORMAL ACCEPTANCE**

Corrected design baseline:

`4a99c74714dcbf3d85e5ec57a26369e36ac0d398`

Previous production candidate:

`9b7fcc9fc37a423eaafd1dde762e9c81d475df9e`

Re-audit:

`development/178-p11-full-design-code-consistency-reaudit.md`

Corrected design authority:

- `design/26-p11-sec-provider-design.md`
- `design/27-p11-implementation-plan.md`
- `design/32-p11-us-scope-reopening.md`
- `design/33-p11-post-acceptance-design-correction.md`

Target branch:

`task/p11-sec-rebuild-development`

Target worktree:

`D:\Codex\FinancialFilingDataFoundation\worktrees\active\p11-sec-rebuild-development`

## 1. Objective

Produce one new **merge-ready P11 production candidate** that closes:

- P11-ISSUE-123
- P11-ISSUE-124
- P11-ISSUE-125
- P11-ISSUE-126
- P11-ISSUE-127
- P11-ISSUE-128
- P11-ISSUE-129
- P11-ISSUE-130

The candidate must implement the corrected design exactly and preserve accepted
P0-P10 CN/HK behavior.

This is a repair implementation task, not formal acceptance.

## 2. Non-negotiable compatibility targets

The implementation must end with:

```text
REGISTRY_SCHEMA_VERSION = 1
SEC_REGISTRY_SCHEMA_VERSION = 4
SEC_DISCOVERY_SCHEMA = p11-sec-discovery-v1
VIRTUAL_HTML_NORMALIZER_VERSION = VIRTUAL_HTML_V5
SEC_ARTIFACT_SCHEMA = p11-sec-artifacts-v2
SEC_VALIDATION_SCHEMA = p11-sec-validation-v2
```

Required compatibility behavior:

- SEC Registry v3 → v4 is additive and idempotent;
- legacy SQLite `user_version=1` remains unchanged;
- future/unknown SEC schema is rejected before mutation;
- accepted CN/HK rows and artifacts are untouched;
- V4/v1 US parsed artifacts are incompatible for current reuse;
- old immutable SEC raw packages remain usable as parser input after current
  discovery revalidation;
- no destructive rewrite/reset/clean.

## 3. Workstream A — current discovery observation

### A1. Introduce discovery model/artifact

Add a deterministic model such as `SecDiscoveryObservation`.

Persist at minimum:

- observation_sha256;
- company_id / CIK;
- fiscal_year;
- period;
- retrieved_at;
- source documents:
  - URL;
  - SHA256;
  - exact source bytes or a content-addressed source reference;
- sorted relevant candidates:
  - accession;
  - form;
  - filing_date;
  - report_period;
  - primary_document;
  - amended flag;
- candidate fingerprint;
- selected accession nullable;
- result state:
  - UNAMBIGUOUS;
  - AMENDED_VARIANT_PRESENT;
  - SLOT_CANDIDATE_CONFLICT;
  - NOT_FOUND;
- artifact path.

Canonical observation hash must be deterministic.

### A2. Add Registry v4 storage

Add an additive table for discovery observations.

Do not rewrite legacy v1 tables.

Migration requirements:

- real v3 fixture migrates to v4;
- existing SEC package/binding/parsed rows survive unchanged;
- second reopen is idempotent;
- unknown future version fails closed without DDL/data mutation.

### A3. Change online planner order

For US `acquire` and `ingest`:

```text
resolve CIK
→ current submissions/history discovery
→ persist observation
→ fail on amendment/conflict/not-found
→ then inspect local package/current parsed artifact
→ REUSE_DATA | PARSE_LOCAL | DISCOVER_AND_ACQUIRE
```

Do not return REUSE_DATA/PARSE_LOCAL before current discovery.

If discovery fails while cached data exists, do not silently claim research-ready
reuse.

Use an explicit reason such as `P11_DISCOVERY_FRESHNESS_UNKNOWN`.

### A4. Status semantics

`status --market US` remains local-only.

It must expose:

- last discovery observation SHA;
- discovery_checked_at;
- selected accession/state;
- a clear local/as-of semantic.

It performs zero network.

## 4. Workstream B — ticker identity provenance

For online ticker-based acquire/ingest:

- fetch current SEC ticker-map source;
- resolve ticker from those current bytes;
- persist exact source bytes + SHA + URL + retrieved_at.

For cached snapshots:

- verify source bytes SHA;
- reparse ticker mapping from verified bytes;
- never trust the serialized derivative `mapping` independently;
- if retained derivative mapping differs from reparsed bytes, fail closed.

Explicit CIK still bypasses ticker map.

Add tests for:

- valid cached snapshot;
- mapping field tampered but source bytes unchanged;
- source bytes tampered;
- two verified historical snapshots mapping one ticker to different CIKs;
- explicit CIK bypass.

## 5. Workstream C — XBRL acquisition isolation

Remove generic "all .xml/.xbrl/.xsd" acquisition behavior.

Use deterministic SEC filing-directory XBRL metadata and exact filing-local
references.

Recognize appropriate XBRL roles, including definition linkbase if required.

Rules:

- PRIMARY_DOCUMENT always exact;
- XBRL support members must belong to the same accession;
- `OTHER` XML is never a source of XBRL facts/contexts/units;
- unrelated XML exhibits are not downloaded by default;
- extension alone is insufficient authorization.

Add an acquisition fixture containing an unrelated XML exhibit and prove it is not
downloaded.

## 6. Workstream D — one logical fact-source mode

Add artifact-level `fact_source_mode`.

### D1. INLINE_XBRL_PRIMARY

When primary HTML contains supported Inline XBRL facts:

- emit P6 logical facts only from primary iXBRL;
- resolve contexts/units only from primary iXBRL resources;
- do not emit extracted-instance facts as another logical fact set;
- extracted instance may be retained only for deterministic cross-check/provenance.

### D2. XBRL_INSTANCE_PRIMARY

When primary has no supported iXBRL facts:

- require exactly one verified XBRL instance;
- emit facts/contexts/units from that instance;
- multiple plausible instances → `P11_XBRL_INSTANCE_AMBIGUOUS`.

### D3. Compatibility

Change parser/artifact versions to V5/v2.

V4/v1 parsed artifacts must fail current compatibility and trigger PARSE_LOCAL after
fresh discovery.

## 7. Workstream E — Inline XBRL continuation/exclude

Implement:

- continuation ID index;
- exact continuedAt resolution;
- chained continuation;
- duplicate continuation target detection;
- missing continuation target detection;
- cycle detection;
- ix:exclude omission from logical fact value.

Evidence must support ordered `source_fragments` for one logical fact.

Every fragment must carry enough identity for round-trip verification:

- member SHA;
- DOM locator;
- fragment hash;
- source-order index;
- raw source text.

Validation must verify every fragment.

Add tests for:

- single continuation;
- chained continuation;
- ix:exclude;
- missing target;
- duplicate target;
- cycle;
- evidence round trip.

Do not fabricate a value when continuation semantics are invalid.

## 8. Workstream F — provenance hardening

Keep the package SHA formula unchanged.

On package construction/load verify:

```text
member.source_url
==
SEC archive URL derived from package.cik + package.accession + member.relative_name
```

P7 and P8 must compare loaded package metadata against Registry:

- source_packages:
  - package SHA;
  - accession;
  - CIK;
  - form;
  - primary_document;
- package_members:
  - role;
  - relative_name;
  - member SHA;
  - byte length;
  - source URL.

Mismatch fails closed with explicit provenance/source-drift reason.

Add tamper tests for:

- manifest CIK;
- manifest accession;
- member source URL;
- Registry member metadata.

## 9. Workstream G — table structural repair

Use occupied logical grid width.

Required:

- `column_count` = max occupied grid width;
- SEC `value_column_count` = same logical width compatibility field;
- row 0 `td` is BODY, not automatically HEADER;
- header tree derives from real header cells and span coverage.

Add fixtures:

- colspan-only maximum width;
- rowspan occupancy;
- body-only first row;
- two-level spanning headers;
- fact-to-cell references.

## 10. Workstream H — P7/P8 discovery binding

P7 validation must receive/use the exact discovery observation.

Replace the design role of a free `amendment_conflict: bool` with a verified
observation/slot state.

Validation v2 records:

- discovery_observation_sha256;
- discovery_checked_at;
- selected_accession;
- fact_source_mode.

P8 remains no-network.

P8 must expose as-of discovery metadata and verify:

- package ↔ Registry;
- member ↔ Registry;
- fact/evidence ↔ immutable member bytes;
- continuation source fragments.

## 11. Workstream I — production enablement

The new candidate must be merge-ready.

Normal US CLI and P8 must work with:

`FFDF_P11_US_DEV` absent.

Update the intended public supported-market/capability declarations on the feature
branch.

Do not merge.

Do not claim accepted production availability.

Formal acceptance will test this exact production behavior before merge.

## 12. Expected production-file scope

Inspect first; do not force changes where unnecessary.

Likely production files include:

- `src/financial_filing_data_foundation/us_sec/acquisition.py`
- `.../us_sec/discovery.py`
- `.../us_sec/models.py`
- `.../us_sec/package.py`
- `.../us_sec/parser.py`
- `.../us_sec/validation.py`
- `.../us_sec/compatibility.py`
- `.../us_sec/ticker_map.py`
- `.../us_sec/feature_gate.py`
- `.../registry/sqlite_registry.py`
- `.../user_cli.py`
- `.../mcp/catalog.py`
- `.../mcp/service.py`
- public capability/supported-market declaration files actually found in the repo.

Do not edit CN/HK parser/acquisition behavior unless an additive shared-contract
change is strictly required and independently covered.

## 13. Required developer tests before candidate freeze

Use the project virtual environment.

Minimum:

```powershell
$py = ".\.venv\Scripts\python.exe"

& $py -m compileall src
& $py -m pytest tests/unit/us_sec -q
& $py -m pytest tests/unit -q
git diff --check
```

Also run focused CN/HK/P8/P9/P10 regressions if the full unit suite does not already
cover them clearly.

Mandatory new regression themes:

- cached original → later amendment;
- metadata revalidation before REUSE_DATA;
- repeat run: metadata fetch yes, archive fetch no, parser no;
- ticker snapshot tamper;
- unrelated XML collision;
- dual iXBRL/instance one logical fact set;
- continuation/exclude;
- package/Registry provenance tamper;
- span/header table correctness;
- Registry v3→v4;
- future Registry no-mutation;
- US CLI/P8 with dev flag absent.

No formal live acceptance is performed in this task.

## 14. Candidate/evidence commit protocol

### Commit A — production candidate

Commit only production code + tests.

Suggested message:

`fix: implement corrected P11 SEC semantics and production gate`

Record exact candidate SHA.

After this commit, do not modify production/test files.

### Commit B — development evidence only

Create:

`development/181-p11-corrected-design-repair-evidence.md`

It must include:

- corrected design baseline SHA:
  `4a99c74714dcbf3d85e5ec57a26369e36ac0d398`;
- previous candidate:
  `9b7fcc9fc37a423eaafd1dde762e9c81d475df9e`;
- new production candidate SHA;
- candidate changed-file list;
- version constants;
- Registry migration facts;
- issue 123–130 closure matrix;
- every developer test command/result;
- full unit pass count;
- CN/HK non-mutation statement;
- explicit statement:
  `FORMAL ACCEPTANCE NOT RUN`.

Evidence commit must contain documentation only.

## 15. STOP conditions

Stop and report a design conflict instead of guessing if:

- exact XBRL source selection cannot be made without unrelated XML sweep;
- continuation semantics would require remote AI;
- Registry v4 requires destructive rewrite;
- production enablement cannot be isolated to the feature branch;
- corrected fact semantics require mutating old raw packages;
- CN/HK accepted behavior would need a breaking change.

## 16. Handoff

After Commit A + evidence Commit B, stop.

Required next action:

`CHATGPT EXACT-CANDIDATE REVIEW OF <NEW_PRODUCTION_CANDIDATE_SHA>`

Do not:

- issue a formal test plan yourself;
- run formal live acceptance;
- merge main;
- declare P11 PASS;
- change historical evidence.
