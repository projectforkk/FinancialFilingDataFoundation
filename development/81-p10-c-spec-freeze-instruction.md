# 81 — P10-C Development Instruction — Models / Spec Freeze

Status: **AUTHORIZED — P10-C ONLY**

Phase:
`P10 — Codex Dynamic Research Integration`

Amended design baseline:
`ee5ddb9798f45b9abac081fb4f7c2c999c131b6c`

P10-B evidence:
`development/79-p10-environment-interface-audit-rerun.md`

P10-B review:
`development/80-p10-b-github-review.md = PASS — P10-B CLOSED`

Current governance head before this instruction:
`b894394af13c6ba806f1156b1e00c85ee58db2e3`

Authoritative contracts:
- `design/24-p10-codex-dynamic-research-integration-design.md`
- `design/25-p10-implementation-plan.md`
- `acceptance/38-p10-acceptance-instruction.md`

---

## 1. Authorization

Only P10-C is authorized.

Implement only:

- `src/financial_filing_data_foundation/research/__init__.py` if required for public P10-C exports；
- `src/financial_filing_data_foundation/research/models.py`；
- `src/financial_filing_data_foundation/research/spec.py`；
- focused tests for P10-C spec/model behavior。

Do not implement:

- research context；
- capability manifest；
- evidence ledger/provenance；
- P10 CLI；
- integration instruction；
- live Codex orchestration；
- Research MCP；
- Semantic Resolver；
- P11。

P10-D and later Gates remain closed.

---

## 2. Required P10-C contract

Implement deterministic:

- `ResearchSpecInput`；
- `ResearchSpecFile` / equivalent immutable descriptor；
- `ResearchSpecBundle`；
- P10 error type/reason codes needed by this Gate；
- `freeze_research_spec(project_root, files)`；
- `verify_research_spec(project_root, bundle)`。

Schema:

`p10-research-spec-bundle-v1`

The bundle must preserve descriptors, not copy instruction file contents.

---

## 3. Input boundary

Caller must explicitly list every spec file.

Each input must provide:

- logical name；
- project-root-relative path。

Rules:

- root resolved first；
- candidate path resolved after joining root；
- resolved path must remain inside resolved project root；
- file must exist and be a regular file；
- duplicate logical name rejected；
- logical name must be non-empty and bounded；
- no directory auto-discovery；
- no recursive glob；
- no URL；
- no external absolute path；
- traversal escape rejected；
- symlink/junction escape rejected by resolved containment check。

Do not infer file type/business meaning from filename.

---

## 4. Byte identity

Hash exact file bytes with SHA256.

Descriptor records at least:

- logical_name；
- normalized project-relative path；
- size；
- sha256。

Bundle ordering:

- deterministic by logical name；
- caller ordering must not affect identity。

Bundle hash:

`SHA256(canonical JSON of sorted descriptors)`

Canonical JSON:

- UTF-8；
- sorted keys；
- compact separators；
- `allow_nan=False`。

---

## 5. Verification

`verify_research_spec` must re-read exact listed files and confirm:

- containment still valid；
- file still regular；
- size unchanged；
- SHA256 unchanged；
- descriptor set unchanged；
- recomputed bundle hash unchanged。

Any byte drift:

`P10_RESEARCH_SPEC_CHANGED`

Invalid initial input uses deterministic P10 invalid/path reason code per design.

No silent refresh of bundle.

---

## 6. Exact-candidate runtime rule

Every test/import command must use:

```powershell
$env:PYTHONPATH="<P10 task worktree>\src"
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -B ...
```

Do not install FFDF into main `.venv`.

Do not install or upgrade dependencies.

All test basetemp/workspace paths must remain under:

`D:\\Codex\\FinancialFilingDataFoundation`

---

## 7. Focused tests

At minimum directly test:

1. valid single file；
2. valid multiple files；
3. raw byte SHA correctness；
4. order-independent bundle identity；
5. deterministic descriptor ordering；
6. duplicate logical name reject；
7. empty logical name reject；
8. missing file reject；
9. directory input reject；
10. absolute path reject；
11. `../` traversal escape reject；
12. resolved symlink/junction escape when platform fixture permits；
13. file byte mutation detected；
14. file size-preserving byte mutation detected；
15. deleted file after freeze detected；
16. bundle tamper/hash mismatch rejected；
17. same bytes + same descriptors -> same bundle hash；
18. no instruction content stored in manifest/bundle serialization。

Windows-specific tests must not require Administrator privileges.

---

## 8. Scope / security

P10-C production must have no:

- network；
- AI/OpenAI/Codex API；
- MCP SDK dependency；
- subprocess/shell；
- SQL；
- environment dump；
- arbitrary recursive filesystem browse。

Do not modify P8/P9 source/tests/contracts.

---

## 9. Evidence

After implementation, record:

`development/82-p10-c-spec-freeze-evidence.md`

Include:

- exact candidate SHA；
- exact changed paths；
- focused test count/result；
- full unit regression count/result；
- compile/import；
- diff check；
- source/security scan；
- P8/P9 zero unintended diff；
- exact-candidate `PYTHONPATH`；
- no dependency/runtime change；
- worktree clean after commit。

---

## 10. Stop rule

If implementation reveals ambiguity or requires new dependency:

`STOP → facts/root cause → design amendment → commit/push → then code`

No code-first design change.

After P10-C candidate/evidence is committed/pushed:

STOP.

P10-D requires a later explicit instruction after review.
