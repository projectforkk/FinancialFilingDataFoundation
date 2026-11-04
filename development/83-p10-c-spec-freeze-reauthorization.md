# 83 — P10-C Reauthorization — Models / Spec Freeze

Status: **AUTHORIZED — P10-C ONLY / P10-ISSUE-002 AMENDED BASELINE**

Phase:
`P10 — Codex Dynamic Research Integration`

Current design baseline:
`f20e4fd46c8d56e85dce80a16daf91abafd6323f`

P10-B review:
`development/80-p10-b-github-review.md = PASS — P10-B CLOSED`

Historical P10-C authorization:
`development/81-p10-c-spec-freeze-instruction.md`

Design-First stop:
`development/82-p10-c-preimplementation-design-stop.md`

P10-ISSUE-002 amendment:
`f20e4fd46c8d56e85dce80a16daf91abafd6323f`
— `design: freeze P10 spec bundle identity`

Authoritative contracts:
- `design/24-p10-codex-dynamic-research-integration-design.md`
- `design/25-p10-implementation-plan.md`
- `acceptance/38-p10-acceptance-instruction.md`

## 1. Authorization

Only P10-C is authorized.

Allowed production scope:

- `src/financial_filing_data_foundation/research/__init__.py`
- `src/financial_filing_data_foundation/research/models.py`
- `src/financial_filing_data_foundation/research/spec.py`

Allowed test scope:

- `tests/unit/research/test_research_spec.py`
- minimal `tests/unit/research/__init__.py` only if test package layout requires it.

Do not implement:

- research context / capability manifest；
- evidence ledger / provenance validator；
- P10 CLI；
- integration instruction；
- live Codex orchestration；
- Research MCP；
- Semantic Resolver；
- P11；
- any P8/P9 source or semantic change。

P10-D and later Gates remain closed.

## 2. Required public contract

Implement deterministic:

- `P10Error` or equivalent reason-coded error；
- `ResearchSpecInput`；
- `ResearchSpecFile` immutable descriptor；
- `ResearchSpecBundle`；
- `freeze_research_spec(project_root, files)`；
- `verify_research_spec(project_root, bundle)`。

Schema:

`p10-research-spec-bundle-v1`

The bundle stores descriptors only; it must not copy instruction file contents.

## 3. P10-ISSUE-002 byte identity

The implementation MUST follow design/24 Section 8.1 exactly:

1. explicit input list is non-empty；
2. logical name is a non-blank string；
3. no trim/case-fold normalization for identity；
4. exact duplicate logical name rejected；
5. caller path is project-root-relative only；
6. resolved target must be a regular file and remain inside resolved project root；
7. persisted relative path is resolved project-relative `as_posix()`；
8. descriptor size is exact raw-byte length；
9. descriptor SHA256 is over exact raw bytes；
10. no UTF-8 decode/BOM/newline normalization；
11. descriptors sort by exact logical name；
12. canonical descriptor-array bytes are exactly:

```python
json.dumps(
    descriptors,
    ensure_ascii=False,
    sort_keys=True,
    separators=(",", ":"),
    allow_nan=False,
).encode("utf-8")
```

13. `spec_bundle_hash = SHA256(canonical descriptor-array bytes)`；
14. hash input excludes `schema_version` and `spec_bundle_hash` itself；
15. caller input order cannot affect bundle identity。

## 4. Verification / error classification

`verify_research_spec` must first validate the supplied bundle itself before trusting descriptor contents.

Required reason codes:

- malformed schema/descriptor/order/hash/tamper:
  `P10_INVALID_SPEC_INPUT`
- initial or verification path escaping project root:
  `P10_SPEC_PATH_OUTSIDE_PROJECT`
- current frozen file missing/deleted/size changed/hash changed:
  `P10_RESEARCH_SPEC_CHANGED`

Initial missing file / directory / malformed input uses deterministic invalid-spec handling consistent with design/24.

No silent bundle refresh is allowed.

## 5. Exact-candidate runtime

Every Python/test command must bind this worktree source:

```powershell
$env:PYTHONPATH="D:\Codex\FinancialFilingDataFoundation\worktrees\active\p10-dynamic-research-design\src"
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -B ...
```

Do not install FFDF into the main `.venv`.

Do not install/upgrade dependencies.

All basetemp/workspace/temp output must remain under:

`D:\Codex\FinancialFilingDataFoundation`

## 6. Focused test minimum

At minimum cover:

1. valid single file；
2. valid multiple files；
3. same files in different caller order => identical bundle/hash；
4. deterministic exact-logical-name descriptor ordering；
5. empty input list rejected；
6. blank logical name rejected；
7. exact duplicate logical name rejected；
8. case-distinct logical names remain distinct；
9. exact raw-byte size/SHA correctness；
10. non-UTF8/BOM/newline-sensitive bytes remain unnormalized；
11. canonical descriptor-array known-fixture hash；
12. initial missing file rejected；
13. directory input rejected；
14. absolute path rejected；
15. traversal/outside escape rejected；
16. persisted relative path uses resolved project-relative POSIX form；
17. symlink/junction escape when platform fixture permits without admin；
18. current file byte mutation detected；
19. size-preserving mutation detected；
20. deleted frozen file => `P10_RESEARCH_SPEC_CHANGED`；
21. malformed schema/order/hash => `P10_INVALID_SPEC_INPUT`；
22. descriptor tamper => `P10_INVALID_SPEC_INPUT`；
23. root escape during verification => `P10_SPEC_PATH_OUTSIDE_PROJECT`；
24. bundle hash excludes schema_version/spec_bundle_hash；
25. bundle serialization contains descriptors only, never instruction contents；
26. exact-candidate source binding is visible in import path。

## 7. Scope / security

P10-C production must contain no:

- network client；
- AI/OpenAI/Codex API；
- external MCP SDK dependency；
- subprocess/shell；
- SQL；
- environment dump；
- recursive prompt discovery；
- arbitrary filesystem browser。

P8/P9 accepted source/tests/contracts remain unchanged.

## 8. Verification

Required before candidate commit:

- focused P10-C tests PASS；
- full unit suite PASS；
- compile/import PASS；
- `git diff --check` PASS；
- static scope/security scan PASS；
- no dependency/runtime change；
- no P8/P9 unintended source/test diff；
- UTF-8/no-BOM governance evidence；
- exact-candidate source paths recorded。

## 9. Evidence

After implementation, create:

`development/84-p10-c-spec-freeze-evidence.md`

It must record:

- design baseline `f20e4fd46c8d56e85dce80a16daf91abafd6323f`；
- implementation candidate SHA；
- exact changed paths；
- focused/full test results；
- compile/import；
- canonical known-fixture hash；
- path/security negative results；
- scope/dependency checks；
- no P8/P9 changes；
- final worktree state。

## 10. Stop rule

If code work reveals another ambiguity:

`STOP → facts/root cause → design amendment → commit/push → new authorization → code`

After P10-C implementation/evidence is committed/pushed:

**STOP P10-C.**

P10-D requires a separate review and explicit instruction.
