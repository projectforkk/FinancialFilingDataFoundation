# 09 — P1 Development Amendment Evidence

状态：**P1-B / C / D / E / F / G REVALIDATED**

Branch:

`task/p1-identity-registry-planner`

Current branch candidate before Code Review:

`03fe9adb691f5d43401fef9ac672bea39f35d26b`

---

## 1. Reason for Amendment

Initial P1 development evidence was recorded in:

`development/08-p1-development-evidence.md`

After that evidence, design-first review identified additional P1 issues that materially affected registry correctness and review governance.

This amendment records the updated implementation and rerun evidence.

---

## 2. Design Corrections Applied

### P1-ISSUE-002 — Source provenance independent of filing binding

Design correction:

- source provenance must persist even when `expected_identity` is unavailable;
- new `document_sources` table;
- source provenance does not infer a filing slot.

Design baseline:

`bd15ececeac5eb7ce30d0355faf2b389526e30f1`

Production correction:

`4072642b9cdf0085c418ce9679e886529f1483ff`

### P1-ISSUE-003 — Unsupported registry schema is plan-level blocker

Design correction:

- unsupported newer SQLite schema is a structured plan-level blocker;
- no silent downgrade.

Production correction:

`3fe1b11523d9d38dc9e9d8e3fa0fc8b0f2c464c8`

`RegistrySchemaUnsupported.reason_code == "REGISTRY_SCHEMA_UNSUPPORTED"`.

### P1-ISSUE-004 — Pre-acceptance commits entered main

Governance correction:

- accepted baseline remains P0 closeout until P1 acceptance PASS;
- main HEAD is not treated as accepted baseline while P1 is unaccepted;
- no reset / force push / history rewrite.

Accepted baseline remains:

`edff06b2b1138b50d742e92ce8b8df628c6d2c61`

### P1-ISSUE-005 — Shared review worktree race

Governance correction:

- Code Review / Independent Acceptance must run in an isolated Git worktree;
- candidate HEAD must be checked before and after each critical command group.

### P1-ISSUE-006 — Registered local content drift

Correctness issue:

A registered bound path could be replaced in place after registration. The prior local resolver checked only path existence, so it could continue treating the old registered SHA as current.

Design correction:

- re-hash each existing bound local path during local resolution;
- only current SHA == registered SHA is a verified live location;
- do not auto-rebind drifted content;
- if no verified live copy remains, return `LocalDocumentStatus.DRIFTED`;
- planner returns `BLOCKED / LOCAL_CONTENT_DRIFT`;
- if another same-SHA duplicate remains verified, use the verified copy.

Production correction:

`dbc67bda0c00804622e87ce83cdba653d1a366f4`

### P1-ISSUE-007 — Isolated worktree pytest workspace

Governance correction:

- isolated review/acceptance worktree must explicitly create its ignored `workspace/` parent before pytest;
- this is execution preparation only and does not alter production semantics.

---

## 3. Current Implemented Scope

P1 implementation now covers:

- CompanyRef
- FilingRequirement / FilingPolicy
- FilingSlotKey
- FilingIdentity
- SourceMetadata
- SQLite registry schema v1
- content-addressed documents
- document locations
- independent document source provenance
- filing bindings
- parsed-data registry
- explicit PlannerReusePolicy
- deterministic required filing set
- deterministic incremental planner
- reuse policy
- material source change handling
- multiple local SHA ambiguity
- multiple reusable parsed SHA ambiguity
- binding conflict blocking
- local registered-path content drift blocking
- same-SHA verified duplicate fallback
- structured unsupported-schema blocker

Not implemented:

- P2 acquisition
- Dayu invocation
- network access
- Docling / Torch / OCR
- external AI
- full parser execution
- tables
- MCP
- Skill

---

## 4. Runtime

Reused project runtime:

- Python 3.14.9 ARM64
- PyMuPDF 1.28.2
- pytest 9.2.0
- sqlite3 stdlib

No new third-party runtime dependency was added.

---

## 5. Final Development Test Command

```powershell
Set-Location "D:\Codex\FinancialFilingDataFoundation"
New-Item -ItemType Directory -Force "workspace" | Out-Null
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe -m pytest tests\unit -q --basetemp "D:\Codex\FinancialFilingDataFoundation\workspace\pytest-p1-final-dev2"
```

Result:

```text
51 passed in 1.74s
```

This includes all P1 unit tests and P0 regression tests.

Candidate HEAD immediately after the test:

`03fe9adb691f5d43401fef9ac672bea39f35d26b`

Working tree: clean.

---

## 6. Earlier Focused Reruns

After source provenance correction:

- P1 focused: 38 PASS
- P0 regression: 9 PASS

After local content drift correction:

- P1 focused: 42 PASS
- P0 regression: 9 PASS

Final combined unit suite:

- 51 PASS

---

## 7. Static Verification

Verified before the final development rerun:

- `py_compile`: PASS
- `git diff --check`: PASS
- forbidden P1 production import scan: no imports of Dayu, httpx, requests, urllib/socket networking, Docling, Torch, OpenAI, Anthropic or Google generative AI SDKs.

---

## 8. Key New Regression Coverage

Additional coverage after the original P1 evidence includes:

- source metadata persists without expected filing identity;
- repeated identical source provenance is idempotent;
- unsupported registry schema exposes structured reason code;
- registered path replaced in place is detected as content drift;
- drifted bound path blocks stale parsed reuse;
- one drifted duplicate does not hide another verified same-SHA copy.

---

## 9. Gate Result

Revalidated:

- P1-B Domain Models: PASS
- P1-C SQLite Registry: PASS
- P1-D Document Registration: PASS
- P1-E Parsed Registry / Reuse: PASS
- P1-F Incremental Planner: PASS
- P1-G Focused + Regression Tests: PASS

Next:

**P1-H — Code Review in isolated candidate worktree**
