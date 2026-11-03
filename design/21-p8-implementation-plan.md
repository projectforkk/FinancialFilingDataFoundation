# 21 — P8 Local MCP 实施计划

状态：**DESIGN BASELINE — P8 EXECUTION PLAN**

详细设计：
`design/20-p8-local-mcp-design.md`

## P8-A — Design Baseline
- detailed design
- implementation plan
- dev instruction
- acceptance instruction
- design index/status update
- commit/push

## P8-B — Environment / SDK Audit
- main venv MCP absent
- exact `mcp==2.3.0`
- base Python 3.12.14 AMD64 (approved by P8-ISSUE-001)
- create dedicated project-local runtime
- install mcp + PyMuPDF exact
- freeze tracked runtime lock
- doctor/import

No production code before design baseline.

## P8-C — Catalog
Implement:
- schema
- project-root-relative path guard
- identity uniqueness
- artifact directory validation

Gate: catalog tests PASS.

## P8-D — Query Service
Implement 11 read-only business methods.
No MCP SDK import.

Gate: focused service tests PASS.

## P8-E — MCP Adapter
- MCPServer
- static 11 tools
- stdio only
- no stdout logging
- deterministic error mapping

Gate: server import/tool registration tests PASS.

## P8-F — Deterministic / Security Regression
- full P0–P8 suite
- no upstream mutation
- no network/AI/shell
- no arbitrary path tool
- payload limits
- compile/diff

## P8-G — Live Catalog
Create ignored project-root acceptance catalog for CN/HK accepted artifacts.
Run business service live calls.

## P8-H — Official SDK Protocol Integration
From dedicated MCP runtime:
- stdio spawn server
- SDK client connect
- list exact tools
- call representative tools
- invalid call error
- negotiated protocol evidence
- cold startup performance

## P8-I — Code Review
Detached worktree:
`worktrees/review/p8-<sha>`

Check exact candidate, runtime lock, protocol integration, security/scope.

## P8-J — Acceptance Freeze
Freeze:
- design baseline/amendments
- production candidate
- review commit
- mcp/runtime lock
- catalog SHA
- live expected values/tool names
- commands

## P8-K — Independent Acceptance
Detached project-root acceptance worktree.
No production/design/config/dependency modifications.

## P8-L — Closeout
PASS:
- acceptance evidence
- merge main
- main regression
- PROJECT_STATUS P8_DONE
- authorize P9 design

Issue rule：
problem → STOP → update design → commit → rerun affected gates → continue。
