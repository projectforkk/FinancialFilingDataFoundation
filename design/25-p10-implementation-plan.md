# 25 — P10 Codex Dynamic Research Integration 实施计划

状态：**DESIGN BASELINE — P10 EXECUTION PLAN**

详细设计：
`design/24-p10-codex-dynamic-research-integration-design.md`

前置：
- P9 DONE / PASS；
- P10 DESIGN AUTHORIZED；
- P10 production尚未授权，直到本设计 baseline commit/push。

---

## P10-A — Design Baseline

完成：

- design/24 detailed design；
- design/25 implementation plan；
- acceptance/38 baseline；
- reconcile design/28 semantic architecture；
- reconcile design/29 future Research MCP visual/resolved query；
- update design index；
- update project master design；
- update development roadmap；
- update PROJECT_STATUS；
- UTF-8 no BOM；
- `git diff --check`；
- commit/push。

Gate：

`P10_READY_FOR_DEVELOPMENT`

该 Gate PASS 前不得修改 P10 production/tests。

---

## P10-B — Environment / Accepted Interface Audit

只读确认：

- main/P10 branch baseline identity；
- FFDF main runtime；
- exact-candidate `PYTHONPATH=<worktree>\\src` source binding；
- bare main-runtime import is not used as package-discovery contract；
- P8 MCP runtime lock unchanged；
- exact P8 11 tools；
- P9 CLI/public API；
- local Codex host availability；
- no new dependency required；
- all work/temp paths inside project root。

输出：
`development/<next>-p10-environment-audit.md`

Gate：
`P10_ENVIRONMENT_READY`

若需要新增 dependency/runtime：
STOP → design amendment。

P10-ISSUE-001 已确认：当前不需要 install FFDF package 或新增 dependency；正式执行统一显式绑定 exact candidate `src`。

---

## P10-C — Models / Spec Freeze

实现：

- `research/models.py`
- `research/spec.py`
- ResearchSpecInput；
- ResearchSpecBundle；
- canonical manifest；
- `spec_bundle_hash`；
- project-root path guard；
- duplicate logical-name guard；
- verify drift。

P10-ISSUE-002 identity contract：

- input list non-empty；
- logical_name non-blank / duplicate rejected；
- input path project-root-relative only；
- resolved target must be regular file and remain inside resolved project root；
- persisted relative_path = resolved project-relative `as_posix()`；
- size/hash from exact raw bytes, no decode/BOM/newline normalization；
- descriptors sorted by exact logical_name；
- canonical JSON bytes use `ensure_ascii=False`, `sort_keys=True`, `separators=(",", ":")`, `allow_nan=False`；
- bundle hash input = descriptor array only；
- verify must reject malformed/tampered bundle separately from current-file drift。

禁止：
- recursive prompt discovery；
- external arbitrary path；
- parsing business meaning；
- editable/install workaround for source layout；
- context/provenance/CLI implementation in P10-C。

Focused tests至少覆盖：

1. same explicit files in different caller order → identical bundle/hash；
2. exact raw-byte SHA/size including non-UTF8/BOM/newline-sensitive bytes；
3. canonical descriptor ordering/hash known fixture；
4. empty input rejected；
5. blank/duplicate logical_name rejected；
6. absolute/outside/traversal path rejected；
7. directory input rejected；
8. canonical project-relative POSIX path persisted；
9. changed/missing file → `P10_RESEARCH_SPEC_CHANGED`；
10. tampered descriptor/hash/schema/order → `P10_INVALID_SPEC_INPUT`；
11. root escape during verification → `P10_SPEC_PATH_OUTSIDE_PROJECT`；
12. exact-candidate `PYTHONPATH` source binding retained。

Gate：
spec focused tests PASS。

---

## P10-D — Research Context / Capability Manifest

实现：

- `research/context.py`
- `ResearchContext` / capability state model additions only as required；
- exact P8/P9 contract fingerprints；
- current catalog raw-byte SHA；
- catalog self-consistency reload through accepted `McpCatalog.load`；
- canonical project-relative P9 review-root identity；
- exact fixed capability manifest；
- deterministic `research_context_id`；
- explicit unavailable visual/semantic/canonical/P11 capability。

P10-ISSUE-003 contract：

- `build_research_context(spec_bundle, p8_catalog, p9_review_root)` has no caller capability override；
- infer project root from accepted `McpCatalog.project_root`；
- call `verify_research_spec(project_root, spec_bundle)` before context creation；
- P8 descriptor is the exact Section 13.2 object；
- P8 catalog/result schema values come from main-runtime P8 public constants；
- P8 server version/tool names are the frozen accepted integration descriptor and must not import `mcp/server.py`；
- P9 descriptor is built from public `P9_VERSION / POLICY_VERSION / RESOLUTION_SCHEMA_VERSION / RESOLVED_VIEW_SCHEMA_VERSION`；
- all descriptor/capability fingerprints use Section 13.1 canonical JSON；
- current catalog raw bytes produce `p8_catalog_sha256`；
- reload current catalog with accepted `McpCatalog.load` and require semantic equality with caller object；
- P9 review root must be relative, existing directory, inside project root, and persisted as resolved relative POSIX path；
- review-root path is included in context ID；
- capability mapping is exact Section 14 mapping, no caller override；
- context ID exact bytes are Section 13.7；
- no absolute path may appear in serialized context。

禁止：

- import dedicated `mcp/server.py` from main runtime；
- external MCP SDK dependency；
- caller mutation/override of capability state；
- P9 state mutation；
- catalog mutation；
- filesystem creation by context builder；
- P10-E provenance implementation；
- P10-F CLI implementation。

Focused tests至少覆盖：

1. deterministic identical context from identical inputs；
2. spec drift propagates `P10_RESEARCH_SPEC_CHANGED`；
3. P8 tool descriptor exact 11 names / server/schema values；
4. independently known P8 fingerprint fixture；
5. P9 public descriptor exact values；
6. independently known P9 fingerprint fixture；
7. exact fixed capability mapping；
8. independently known capability-manifest hash；
9. exact raw catalog SHA；
10. stale caller catalog vs changed current file → `P10_CATALOG_INVALID`；
11. invalid catalog propagates deterministic P10 catalog error；
12. relative review root persisted as project-relative POSIX；
13. absolute review root rejected；
14. drive-relative / traversal escape review root rejected；
15. missing/not-directory review root → `P10_CONTEXT_INCOMPATIBLE`；
16. two canonical review roots → different context IDs；
17. exact known `research_context_id` fixture；
18. context ID changes when spec/catalog/P8/P9/review-root/capability fingerprint changes；
19. context serialization contains no absolute filesystem path；
20. no external MCP SDK import in main runtime；
21. no P8/P9 source/test modification；
22. exact-candidate source binding retained。

Gate：
context determinism tests PASS。

---

## P10-E — Evidence Ledger / Provenance Validator

实现：

- `research/provenance.py`
- `EvidenceLedgerEntry`
- `EvidenceLedger`
- `ProvenanceValidation`
- `validate_evidence_ledger(context, ledger, spec_bundle, p8_catalog)`
- exact use-class compatibility profiles
- P8 document/table/fact/evidence/page reference validation
- P9 resolution/snapshot/overlay validation
- derived claim DAG validation
- deterministic error mapping
- no financial reasoning

必须复用：

- P10-C `verify_research_spec`
- P10-D context/catalog identity rules
- accepted `McpQueryService`
- accepted P9 `load_resolved_snapshot` / public review API

禁止：

- 复制 P8 parser/fact/evidence truth semantics；
- 复制 P9 resolution/history/hash semantics；
- materialize P9 snapshot during validation；
- 修改 P9 review state；
- caller capability override；
- arbitrary filesystem browse；
- network/AI/subprocess/SQL；
- external-source truth validation。

### P10-E exact focused cases

至少覆盖：

1. valid empty ledger；
2. top-level schema/context/spec identity；
3. duplicate claim key reject；
4. invalid/noncanonical document SHA reject；
5. exact P8 raw-direct page provenance；
6. exact P8 table provenance；
7. exact P8 raw-fact provenance；
8. exact P8 evidence provenance；
9. fact/evidence relation mismatch reject；
10. table/fact/evidence page-scope mismatch reject；
11. table-scope mismatch reject；
12. invalid document reject；
13. invalid page reject；
14. invalid table reject；
15. invalid fact reject；
16. invalid evidence reject；
17. source-backed run-local profile PASS；
18. raw-direct semantic assertions reject；
19. run-local source without semantic assertions reject；
20. valid P9 durable resolution/snapshot PASS；
21. P9 durable without overlay hash reject；
22. P9 resolution not in claimed snapshot reject；
23. missing claimed review/snapshot path reject；
24. corrupt P9 state -> `P10_UPSTREAM_INVALID`；
25. historical validated P9 snapshot remains valid by exact overlay；
26. valid unresolved entry；
27. unresolved/P8 raw direct as derived operand reject；
28. valid derived run-local claim；
29. missing operand reject；
30. self-reference reject；
31. derived cycle reject；
32. entry order does not change graph validity/result；
33. spec drift -> `P10_RESEARCH_SPEC_CHANGED` before later provenance checks；
34. ledger context/spec mismatch -> `P10_PROVENANCE_INVALID`；
35. current catalog/context mismatch -> `P10_CONTEXT_INCOMPATIBLE`；
36. malformed/corrupt P8 upstream state -> `P10_UPSTREAM_INVALID`；
37. validation result exact schema/sorted claim keys；
38. serialized validation contains no absolute path/time/random/hidden reasoning；
39. external-source use class rejected from FFDF ledger v1；
40. exact candidate source binding / main runtime no external MCP SDK。

Gate：

- provenance focused tests PASS；
- full `tests/unit` PASS；
- compile/import PASS；
- P8/P9 source/tests zero diff；
- dependency/runtime zero diff；
- forbidden surface scan NONE；
- evidence committed/pushed；
- separate detached P10-E Code Review required before P10-F。

P10-F and later remain closed until review PASS + separate explicit authorization.

---

## P10-F — Deterministic CLI

实现：

```powershell
$env:PYTHONPATH="<exact-candidate-worktree>\src"
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -B -m financial_filing_data_foundation.research.cli <command> ...
```

禁止以 editable/install 代替 exact-candidate source binding。

只允许新增：

- `research/cli.py`；
- minimal `research/__init__.py` export only if needed；
- `tests/unit/research/test_research_cli.py`。

P10-ISSUE-005 exact contract：

- commands exactly `freeze-spec / verify-spec / build-context / validate-ledger`；
- argv exactly follows design/24 Section 31.1；
- request transport = stdin JSON object only；
- stdin max = 16 MiB；
- no request-file option；
- exact request object keys follow Section 31.3；
- catalog argument must be project-root-relative；
- P9 review-root remains project-root-relative existing directory；
- `build-context` verifies spec before catalog/context semantic validation；
- `validate-ledger` verifies spec, loads catalog, deterministically rebuilds context, then parses/validates ledger；
- no `ResearchContext.from_dict` in P10-F；
- success stdout exactly one canonical JSON line / stderr empty / exit 0；
- handled failure stdout empty / stderr exactly one canonical JSON line / exit 1；
- parser failure reason = `P10_CLI_ARGUMENT_ERROR`, exit 2；
- transport/envelope failure reason = `P10_CLI_INPUT_INVALID`, exit 1；
- unexpected failure = `P10_CLI_FAILED` + fixed message, exit 1；
- no argparse usage/help prose；
- no traceback；
- no AI/network/external MCP SDK/subprocess/shell/SQL；
- no P8 MCP business-call proxy；
- no P9 mutation call；
- no implicit artifact write。

Focused subprocess matrix至少覆盖：

1. `freeze-spec` success exact envelope；
2. `verify-spec` success exact envelope；
3. `build-context` success exact envelope；
4. `validate-ledger` success exact envelope；
5. success stdout one line / stderr empty / exit 0；
6. missing command parser error；
7. unknown command parser error；
8. `--help` parser error without prose；
9. missing required arg parser error；
10. unknown arg parser error；
11. empty stdin；
12. malformed JSON；
13. non-UTF8 stdin；
14. non-object JSON root；
15. extra request key；
16. missing request key；
17. >16 MiB stdin；
18. malformed freeze files item；
19. accepted P10-C domain error propagation；
20. spec drift on verify；
21. spec drift precedes invalid catalog on build-context；
22. spec drift precedes invalid ledger on validate-ledger；
23. absolute/drive-relative/outside catalog rejected；
24. invalid catalog maps `P10_CATALOG_INVALID`；
25. invalid review-root preserves P10-D reason code；
26. malformed ledger preserves P10-E reason code；
27. unexpected failure has fixed `P10_CLI_FAILED` envelope；
28. no traceback/usage text on any error path；
29. output JSON canonical/sorted/compact；
30. exact candidate source binding；
31. no forbidden production surface；
32. no P8/P9 source/test/runtime modification。

Gate：

- CLI focused matrix PASS；
- full unit regression PASS；
- compile/import PASS；
- scope/security scan PASS。

After evidence commit/push：

STOP P10-F → separate detached Code Review before P10-G。

---

## P10-G — Thin Integration Instruction

新增：

`integration/p10/FFDF_RESEARCH_INTEGRATION.md`

只允许记录：

- read frozen runtime spec first；
- P8/P9 capability/boundary；
- provenance；
- no guessing；
- run-local vs durable；
- capability gap handling。

静态检查禁止复制：

- 固定用户问题；
- 固定章节；
- 固定公司/期间；
- 固定估值规则。

P10-ISSUE-006 artifact identity：

- freeze exact candidate commit SHA；
- compute SHA256 from exact Git blob content bytes for `integration/p10/FFDF_RESEARCH_INTEGRATION.md`；
- do not use arbitrary checked-out worktree bytes as the cross-worktree identity；
- Git blob must decode UTF-8 and contain no BOM；
- record worktree EOL representation separately if relevant；
- extract Git blob bytes with a binary-safe method; do not hash a PowerShell text/object pipeline representation；
- candidate `3a805a8...` known Git-blob SHA256 =
  `ef10406c9957f7a68a9af001c913deef0a057e166100a2d852c0c8fcd2c46296`。

Gate：

- instruction scope review PASS；
- exact Git-blob SHA identity PASS；
- detached review distinguishes checkout EOL from Git blob identity。

---

## P10-H — Full Regression / Scope

执行：

- P10 focused；
- full P0-P10 unit；
- compile/import；
- `git diff --check`；
- P0-P9 production/test accepted paths zero unintended change；
- P8 11-tool contract unchanged；
- P9 source/test unchanged；
- no AI/network/subprocess/new MCP mutation；
- no Research MCP/Semantic Resolver/P11 production。

Gate：
PASS。

---

## P10-I — Dynamic Spec Integration

准备至少两套 runtime spec：

- Spec A；
- Spec B，内容实质不同。

要求：

- same P10 production candidate；
- different spec hashes；
- Codex完整读取当前 frozen spec；
- information needs/tool selection按 spec变化；
- 无固定 question-id mapping；
- evidence ledger valid。

Gate：
PASS。

---

## P10-J — Live P8/P9 Research Run

使用 accepted CN/HK live artifacts。

至少一个 COMPLETE run：

1. freeze spec；
2. discover P8 tools；
3. locate document；
4. read validation；
5. dynamic fact/table/evidence queries；
6. relevant P9 state/review；
7. produce spec-required output；
8. validate evidence ledger；
9. prove raw/base immutability。

P9 mutation只能写 isolated P10 review_root。

Gate：
PASS。

---

## P10-K — Negative Capability Gates

必须证明：

### missing filing

→ `P10_DATA_PREPARATION_REQUIRED`

### structured evidence insufficient / needs visual

→ `P10_VISUAL_CAPABILITY_REQUIRED`

### P9 store invalid

→ BLOCK，不 silent raw fallback。

### spec mutated mid-run

→ `P10_RESEARCH_SPEC_CHANGED`

### unresolved semantic requirement

→ `P10_REVIEW_UNRESOLVED` / explicit gap。

Gate：
所有 negative cases诚实 PASS。

---

## P10-L — Formal Code Review

创建 exact detached review worktree：

`worktrees/review/p10-<sha>`

审：

- exact design baseline；
- no fixed Skill/business rules；
- spec freeze；
- capability manifest；
- provenance validator；
- P8/P9 reuse；
- no semantic duplication；
- dynamic/live evidence；
- negative gaps；
- security/scope。

Verdict：
PASS / FAIL / BLOCKED。

FAIL → Design-First corrective loop。

---

## P10-M — Acceptance Freeze

冻结：

- exact design baseline；
- exact production candidate；
- formal review PASS；
- P8 accepted tool fingerprint；
- P9 policy/baseline；
- runtime locks；
- Spec A/B exact hashes；
- live catalog；
- isolated P9 review root fixture；
- evidence ledger expectations；
- negative capability fixtures；
- exact commands；
- Windows basetemp path。

任何 design/production change后原 freeze失效。

---

## P10-N — Independent Acceptance

fresh detached worktree。

必须：

- 不改 production/tests/design；
- 不改 accepted P8/P9 artifacts；
- 所有 temp/workspace在 project root；
- fresh focused/full suite；
- fresh dynamic Spec A/B；
- fresh live run；
- fresh negative capability run；
- immutability snapshot。

Verdict：
PASS / FAIL / BLOCKED。

---

## P10-O — Closeout

仅 P10-N PASS 后：

- acceptance result；
- merge accepted P10 branch to main；
- post-merge full regression；
- PROJECT_STATUS P10_DONE；
- design index/master/roadmap同步；
- 评估下一阶段授权。

P10 closeout **不会自动授权**：

- Research MCP production；
- Semantic Resolver production；
- P11 production。

下一授权必须由 design owner明确记录。

---

## Issue Rule

任何问题：

```text
STOP
→ facts/root cause
→ design/24 amendment
→ design/25 / acceptance同步
→ commit/push new baseline
→ invalidate affected evidence
→ implementation
→ rerun
```

禁止 code-first / design-later。
