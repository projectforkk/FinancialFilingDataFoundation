# 101 — Research Review MCP v3 R-A2 Research Preflight Contract Evidence

## 目标

冻结 Research Preflight 的 run-local 数据合同和确定性 readiness 规则，不实现真实财报扫描、不调用 MCP、不触发 Visual、不写 P9。

## 设计基线

- branch: design/research-review-mcp-v3
- design baseline: d90df22
- R-A1 implementation: 54635eb
- current production baseline: main@8c6cd75

## 本 Gate 修改

新增：

- src/financial_filing_data_foundation/research/preflight_contract.py
- tests/unit/research/test_preflight_contract.py

冻结：

- schema version: research-preflight-v1
- requirement set schema: research-requirement-set-v1
- RequirementCriticality:
  - CRITICAL
  - NON_CRITICAL
- RequirementAvailability:
  - AVAILABLE
  - PARTIAL
  - NEEDS_REVIEW
  - NEEDS_UPSTREAM_FIX
  - NOT_DISCLOSED
  - NOT_FOUND
  - AMBIGUOUS
  - NOT_APPLICABLE
- FilingCoverageStatus:
  - COMPLETE_BY_POLICY
  - OBSERVED_ONLY
  - CATALOG_COVERAGE_UNCONFIRMED
  - NOT_EVALUATED
- RepairDisposition:
  - QUALITY_REVIEW
  - UPSTREAM_FIX
  - RESEARCH_GAP
  - NOT_DISCLOSED
  - CATALOG_GAP
  - NO_ACTION

## ResearchRequirementSet

显式由上层研究编排生成，不从 Markdown 自动推断 canonical metric。

每个 requirement 至少包含：

- requirement_id
- source_rule_ref
- description
- target_periods
- evidence_strategies
- criticality
- allow_partial
- allow_not_disclosed

requirement_set_hash 基于 spec_bundle_hash + canonical requirement payload 确定性计算。

输入顺序不同但语义相同，hash 必须相同。

## ResearchPreflightResult

冻结字段包括：

- company
- research period
- spec_bundle_hash
- requirement_set_hash
- filing coverage
- document quality observations
- research coverage observations
- repair queue
- period_monitoring_complete
- research_ready
- database_fully_reviewed
- research_blocker_count
- deterministic preflight_hash

## Readiness 规则

period_monitoring_complete：

- observed filing SHA set == assessed document quality SHA set

research_ready：

- period_monitoring_complete == true
- CRITICAL requirements 无 blocking status

允许：

- document 本身仍 NEEDS_REVIEW
- 但 remaining issue 与当前研究无关
- 当前 critical requirements 全部可用
- research_ready == true

NOT_DISCLOSED：

- 只有 requirement.allow_not_disclosed == true 时不阻断 critical requirement

PARTIAL：

- 只有 requirement.allow_partial == true 时不阻断 critical requirement

NON_CRITICAL：

- gap 不阻断 research_ready

database_fully_reviewed：

- 仅当全部 observed documents 均为 COMPLETE_BASE / COMPLETE_REVIEWED

该字段只是 run summary，不持久化 is_complete。

## Non-regression / 边界

本 Gate 没有：

- 调用 ffdf MCP
- 调用 render
- prepare P9
- submit P9
- materialize P9
- 查询 SQLite Registry
- 自动解析问题清单 Markdown
- 创建 canonical metric layer
- 修改 production server tool surface

## 测试

结果：

- compileall: PASS
- focused R-A1 + R-A2 contract tests: 18 PASS
- tests/unit/research + tests/unit/mcp: 179 PASS
- git diff --check: PASS
- production MCP surface: unchanged

关键测试覆盖：

- requirement_set_hash 与输入顺序无关
- duplicate requirement_id 拒绝
- unrelated NEEDS_REVIEW 不自动阻断 research_ready
- NOT_DISCLOSED 可按研究规则允许
- critical PARTIAL 默认阻断
- NON_CRITICAL gap 不阻断
- observed filing 未全部 assessed 时 monitoring incomplete
- preflight_hash deterministic
- coverage 必须与 requirement set 一一对应
- contract module 无 render / submit / materialize / Registry side effect

## Gate 结论

R-A2 Research Preflight Contract: PASS

下一 Gate：

R-B — Trusted Source Resolver
