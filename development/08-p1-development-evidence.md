# 08 — P1 Development Evidence

状态：**P1-B / C / D / E / F / G COMPLETE**

Branch:

\`task/p1-identity-registry-planner\`

P1 initial design baseline:

\`68708cea38ff8374f602f7e0db5531eddca9bbef\`

Reuse ambiguity design correction:

\`58a76cea863f4345bde0e56e320a35645d6c979f\`

Public surface design correction:

\`c4e71075353543c2677b748dbf1c179454fc05e8\`

Production commit:

\`444f3411a9c57b619be839e0088bddee13dd3d93\`

---

## 1. Implemented Scope

Implemented only P1:

- CompanyRef
- FilingRequirement / FilingPolicy
- FilingSlotKey
- FilingIdentity
- SourceMetadata
- SQLite registry schema v1
- content-addressed documents
- multi-location document registry
- filing bindings
- parsed-data registry
- explicit PlannerReusePolicy
- deterministic reuse evaluation
- deterministic build_plan
- stable reason codes
- source material change handling
- multiple local SHA ambiguity
- multiple reusable parsed SHA ambiguity
- binding conflict blocking

Not implemented:

- Dayu
- network acquisition
- P2 provider
- PDF extraction pipeline
- Docling / Torch / OCR
- external AI
- table extraction
- MCP
- Skill

---

## 2. Runtime

Reused P0 project runtime:

- Python 3.14.9 ARM64
- PyMuPDF 1.28.2
- pytest 9.2.0
- sqlite3: Python stdlib

No new third-party runtime dependency added.

---

## 3. P1-ISSUE-001

Initial P1-G collection failed because:

\`ValidationStatus\`

was implemented in \`registry.models\` but not exported from the stable \`financial_filing_data_foundation.registry\` package surface.

Per project governance:

1. test execution stopped;
2. root cause identified;
3. design updated first;
4. design commit \`c4e7107\` created and pushed;
5. public re-export corrected;
6. affected tests rerun.

The fix did not alter registry schema or planner semantics.

---

## 4. Concurrent Design Correction Reconciled

Before production commit, GitHub main added design commit:

\`58a76ce — docs: resolve P1 reuse ambiguity\`

It clarified:

- explicit PlannerReusePolicy;
- empty accepted schema set means no reuse;
- defect invalidation uses explicit parser-version list;
- multiple distinct reusable parsed document SHA with no unique local active-source evidence must produce REVIEW_REQUIRED;
- same SHA multiple reusable runs choose deterministic parse_run_id.

Implementation and tests were reconciled to this design before production commit.

---

## 5. Test Command

PowerShell:

\`\`\`text
Set-Location D:\\Codex\\FinancialFilingDataFoundation
$env:PYTHONPATH=src
.\\.venv\\Scripts\\python.exe -m pytest tests\\unit\\identity tests\\unit\\registry tests\\unit\\planner tests\\unit\\probes -q --basetemp D:\\Codex\\FinancialFilingDataFoundation\\workspace\\pytest-p1-rerun
\`\`\`

Result:

\`\`\`text
45 passed in 1.36s
\`\`\`

Includes P0 regression tests.

---

## 6. Static Verification

\`py_compile\`: PASS

\`git diff --check\`: PASS

Forbidden import scan across P1 production modules found no imports of:

- dayu
- httpx
- requests
- urllib/socket networking
- docling
- torch
- openai
- anthropic
- google.generativeai

---

## 7. Key Acceptance Matrix Covered

- FilingSlotKey deterministic
- amended does not change slot
- policy order deterministic
- duplicate filing requirement rejected
- SQLite schema v1
- newer unknown schema rejected
- register same file idempotent
- same SHA multi-path shares one content record
- changed path content updates current location SHA while retaining historical content
- unbound document is not local candidate
- source-confirmed binding supported
- conflicting cross-slot binding blocked
- removed file not treated live
- parsed record idempotency
- parse_run_id cannot silently change content
- source PDF immutable
- valid parsed data reuse
- validation/blocking/incompatible/unknown schema prevents reuse
- empty accepted schema set prevents reuse
- parser version difference alone does not invalidate
- explicit invalidated parser version prevents reuse
- one local raw -> PARSE_LOCAL
- same local SHA + reusable parse -> REUSE_DATA
- material source SHA change -> PARSE_LOCAL
- no data/local -> DOWNLOAD_AND_PARSE
- multiple local distinct SHA -> REVIEW_REQUIRED
- multiple reusable parsed distinct SHA without local evidence -> REVIEW_REQUIRED
- multiple reusable runs same SHA deterministic
- binding conflict -> BLOCKED
- plan deterministic across repeated calls and DB reopen
- no network / Dayu / heavy imports

---

## 8. Gate Results

- P1-B Domain Models: PASS
- P1-C SQLite Registry: PASS
- P1-D Document Registration: PASS
- P1-E Parsed Registry / Reuse: PASS
- P1-F Incremental Planner: PASS
- P1-G Tests: PASS

Next:

**P1-H — Code Review**
