# 81 — P10-C Development Instruction — Models / Spec Freeze

Status: **STOPPED — P10-ISSUE-002 DESIGN AMENDMENT PENDING PUSH**

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

P10-ISSUE-002 freezes the byte-level identity contract:

- input list must be non-empty；
- `logical_name` must be a non-blank string and is not trim/case-fold normalized for identity；
- duplicate logical names rejected；
- descriptors sort by exact logical-name Unicode string；
- persisted path = resolved project-root-relative `as_posix()`；
- size = exact raw-byte length；
- SHA256 = exact raw-file bytes；
- no UTF-8 decode / BOM / newline normalization。

Canonical descriptor-array bytes are exactly:

```python
json.dumps(
    descriptors,
    ensure_ascii=False,
    sort_keys=True,
    separators=(",", ":"),
    allow_nan=False,
).encode("utf-8")
```

Bundle hash:

`SHA256(canonical descriptor-array bytes)`

The hash input is the descriptor array only. It does not include `schema_version` or `spec_bundle_hash` itself.

---

## 5. Verification

`verify_research_spec` must re-read exact listed files and confirm:

- containment still valid；
- file still regular；
- size unchanged；
- SHA256 unchanged；
- descriptor set unchanged；
- recomputed bundle hash unchanged。

Error classification is fixed:

- malformed/tampered bundle structure, ordering or stored hash → `P10_INVALID_SPEC_INPUT`；
- current listed file missing, deleted, size changed or bytes/hash changed → `P10_RESEARCH_SPEC_CHANGED`；
- resolved path escapes project root → `P10_SPEC_PATH_OUTSIDE_PROJECT`。

No silent refresh of bundle.

The implementation must validate bundle schema/order/hash self-consistency before trusting stored descriptors.

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
3. empty input list reject；
4. raw byte SHA/size correctness；
5. non-UTF8/BOM/newline-sensitive raw bytes hash without normalization；
6. order-independent bundle identity；
7. deterministic exact-logical-name descriptor ordering；
8. duplicate logical name reject；
9. blank logical name reject；
10. same logical text with different case remains distinct unless exactly duplicated；
11. missing initial file reject；
12. directory input reject；
13. absolute path reject；
14. `../` traversal escape reject；
15. persisted relative path uses resolved project-relative POSIX form；
16. resolved symlink/junction escape when platform fixture permits；
17. file byte mutation detected；
18. file size-preserving byte mutation detected；
19. deleted file after freeze = `P10_RESEARCH_SPEC_CHANGED`；
20. malformed bundle/schema/order reject = `P10_INVALID_SPEC_INPUT`；
21. bundle hash tamper reject = `P10_INVALID_SPEC_INPUT`；
22. descriptor tamper with recomputation mismatch reject；
23. same raw files + same descriptors -> same bundle hash；
24. hash input excludes schema_version/spec_bundle_hash；
25. no instruction content stored in manifest/bundle serialization。

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

P10-ISSUE-002 stop boundary:

This instruction is not active for implementation until the P10-ISSUE-002 amendment to design/24 + design/25 + acceptance/38 + this instruction is committed/pushed and P10-C is explicitly reauthorized against that new baseline.

After the later authorized P10-C candidate/evidence is committed/pushed:

STOP.

P10-D requires a later explicit instruction after review.
