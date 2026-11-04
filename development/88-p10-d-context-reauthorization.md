# 88 — P10-D Reauthorization — Research Context / Capability Manifest

Status: **AUTHORIZED — P10-D ONLY / P10-ISSUE-003 AMENDED BASELINE**

Design baseline:
`ba962aef818d7a31731637a5cfef1f57020a7d1d`

Prerequisite review:
`development/86-p10-c-detached-code-review-result.md = PASS`

Pre-implementation stop:
`development/87-p10-d-preimplementation-design-stop.md`

Only P10-D is authorized.

Allowed:
- `src/financial_filing_data_foundation/research/context.py`
- minimal context model/export additions in `research/models.py` / `research/__init__.py`
- `tests/unit/research/test_research_context.py`

Required contract:
- `build_research_context(spec_bundle, p8_catalog, p9_review_root)`
- no caller capability override
- verify research spec first
- exact Section 13.2 P8 descriptor/fingerprint
- exact Section 13.3 P9 descriptor/fingerprint
- raw catalog SHA + semantic reload/equality via accepted `McpCatalog.load`
- existing canonical project-relative P9 review-root
- exact Section 14 capability mapping/hash
- exact Section 13.7 context ID
- no absolute path in serialized context
- no import of dedicated `mcp/server.py`
- no new dependency/runtime

Required focused tests are design/25 P10-D items 1–22.

Evidence file:
`development/89-p10-d-context-evidence.md`

Still prohibited:
- P10-E provenance
- P10-F CLI
- Research MCP production
- Semantic Resolver production
- P11 production
- any P8/P9 source/semantic change

If another ambiguity appears:
`STOP → design amendment → commit/push → new authorization → code`.
