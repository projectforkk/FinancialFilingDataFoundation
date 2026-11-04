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

禁止：
- recursive prompt discovery；
- external arbitrary path；
- parsing business meaning。

Gate：
spec focused tests PASS。

---

## P10-D — Research Context / Capability Manifest

实现：

- `research/context.py`
- exact P8/P9 contract fingerprints；
- catalog SHA；
- P9 policy identity；
- exact capability manifest；
- deterministic `research_context_id`；
- explicit unavailable visual/semantic/canonical/P11 capability。

Gate：
context determinism tests PASS。

---

## P10-E — Evidence Ledger / Provenance Validator

实现：

- `research/provenance.py`
- P8 document/table/fact/evidence/page identity validation；
- P9 resolution/snapshot identity validation；
- use-class checks；
- derived operand reference checks；
- no financial reasoning。

必须复用 accepted P8/P9 loaders/services，禁止复制其 truth semantics。

Gate：
provenance focused tests PASS。

---

## P10-F — Deterministic CLI

实现：

`python -m financial_filing_data_foundation.research.cli`

commands：

- freeze-spec；
- verify-spec；
- build-context；
- validate-ledger。

要求：

- success stdout exactly one JSON；
- diagnostics stderr exactly one JSON；
- parser failures deterministic JSON；
- no argparse help prose；
- no AI/network/subprocess。

Gate：
CLI matrix PASS。

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

Gate：
instruction scope review PASS。

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
