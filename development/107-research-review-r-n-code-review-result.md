# 107 — Research Review MCP v3 R-N Formal Code Review Result

## Review scope

Candidate branch: design/research-review-mcp-v3

Reviewed components:

- Research Preflight contract
- Trusted PDF Source Resolver
- Review State / Resolved Query
- Review Context / Evidence Locator
- Controlled P9 write-through
- Visual Trigger / Renderer / Decision Policy
- 26-tool MCP server adapter
- Report-Safe compatibility
- P9 durable reuse Golden
- deployment documentation

本次 Formal Code Review 未调用 Codex；因此“若调用 Codex 只能 Luna 5.6”的约束没有被触发。

## Finding 1 — Report-Safe private service dependency

Severity: MEDIUM

发现：
- Report-Safe v1 仍有两处直接访问 service._bundle。

风险：
- 扩展层依赖 private loader；
- 不利于后续接口冻结和独立测试。

修复：
- 新增内部 defensive accessors：
  - all_pages_internal
  - all_tables_internal
  - table_group_map_internal
  - validation_status_internal
- Report-Safe 不再直接调用 service._bundle。
- 新增静态回归测试。

状态：RESOLVED。

## Finding 2 — Deployment documentation stale

Severity: MEDIUM

发现：
- 部署文档仍描述 14 tools / TOOLS=14。

风险：
- 实际 candidate server 已为 26 tools；
- 运维人员可能误判 Research Review 是否部署。

修复：
- 更新为 26-tool surface；
- 明确 11 P8 + 3 Report-Safe + 12 Research Review；
- 明确默认 RESEARCH_FALLBACK；
- 新增 docs/FFDF_MCP_Research_Review_v1.md。

状态：RESOLVED。

## Security / governance review

PASS：

- caller 无 arbitrary file path；
- caller 无 arbitrary bbox；
- trusted source 受 Registry + raw-store root + SHA256 + page_count 约束；
- default research profile 无 P9 durable mutation；
- P9 v1 schema/action 未扩展；
- 无 SET_VALUE；
- VisualRef 未伪装为 P9 evidence；
- raw extraction mismatch 路由 upstream；
- P8 11-tool logical contract 保持冻结；
- server extension additive；
- temporary announcement coverage 不被误当成 complete event feed；
- no network / AI inside FFDF MCP implementation。

## Performance review

发现并修复 live 605117 company context 性能问题：

旧实现：
- 对 23 份 filings 逐份完整加载 P3/P5/P6/P7；
- live MCP 60 秒超时。

修复：
- get_document_summary_internal 读取 manifest-level summary；
- Report-Safe company context 语义不变；
- live 23-document check 后续通过。

## Test evidence

R-N rerun：

- tests/unit/mcp
- tests/unit/research
- tests/unit/review

结果：

285 PASS / 0 FAIL

其他：

- compileall PASS
- git diff --check PASS（仅 Windows LF/CRLF warning）
- REPORT_SAFE_PRIVATE_BUNDLE=False
- STALE_14_DOC=False

## Review conclusion

R-N Formal Code Review: PASS

Open blocking findings: 0

下一 Gate：R-O Acceptance Freeze。
