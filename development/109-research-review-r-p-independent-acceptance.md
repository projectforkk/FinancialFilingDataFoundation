# 109 — Research Review MCP v3 R-P Independent Acceptance

## Acceptance Candidate

Implementation commit frozen by R-O:

`99e212d19a0f7b11e7f5718805d55f2ba27b31a3`

Freeze metadata commit:

`d4bd383`

R-P did not modify implementation code.

## 1. FFDF Full Unit Suite

Command scope:

`pytest tests/unit -q --basetemp .t/rp-unit`

Result:

**504 PASS / 0 FAIL**

Runtime:

- Development Python 3.14.9
- short basetemp used to avoid known Windows long-path P9 snapshot issue

## 2. MCP stdio Independent Acceptance

Dedicated MCP runtime:

- Python 3.12.14
- mcp 2.3.0
- PyMuPDF 1.28.2

Result:

- protocol: 2026-07-28
- exact tool count: 26
- CN accepted document checks: PASS
- HK accepted document checks: PASS
- invalid document fail-closed: PASS
- legacy P8/Report-Safe behavior: PASS

Observed performance:
- cold connect ~1.29s
- warm MCP calls remain millisecond-level after bundle load

## 3. 605117 Live Golden

Research period 2021–2026:

- periodic filings observed: 23
- latest filing: 2026Q3
- 2025FY quality_state: NEEDS_REVIEW
- default write_enabled: false

Direct disclosure:
- 新能源行业
- Revenue 10,180,522,048.26
- Cost 5,942,388,719.41
- GM 41.63
- source label preserved

KAM locator:
- page 105
- page 106

Visual:
- MCP returned TextContent + ImageContent
- renderer ffdf-pdf-renderer-v1
- page 22
- DPI 144
- VisualRef 8a94b1fb88cb62c152cae9ce4cb081dbfe980140e333fae6d45ff82073061a8c
- Render SHA 3c5a05b799409c179853d38251d819f3fdcc7c85b19b2388ffccf1bf01f07510

Default RESEARCH_FALLBACK P9 write:
- correctly rejected with RESEARCH_MCP_WRITE_DISABLED

Result: PASS.

## 4. 002371 2026Q3 Golden

Original PDF SHA:
`a0f8d84ab724f7c62b690d6504215602a623fc185c53c9e1079cd40653c600b9`

Verified:
- pages 10
- tables 10
- facts 315
- evidence 315
- blocking 0

Revenue quartet:
- 11,305,675,488.89
- 1.31%
- 31,467,092,379.45
- 15.26%

P5 current numeric roles are four VALUE cells, so structured role alone cannot prove current-quarter/YTD/yoy semantics.

Policy result:
`MISSING_LAYOUT_CONTEXT → VISUAL_REQUIRED`

Result: PASS.

## 5. P9 Durable Reuse Golden

Verified via full P9 review fixture:

- SET_PERIOD
- SET_UNIT
- materialize
- resolved_validation_status PASS
- resolved_reuse_eligible true
- ResearchReviewService returns COMPLETE_REVIEWED
- subsequent resolved fact uses durable effective fields
- RawFact remains immutable
- no renderer dependency on reuse path

Result: PASS.

## 6. Security / Immutability

PASS:

- no arbitrary filesystem path tool
- no arbitrary bbox input
- trusted raw-store boundary
- Registry path binding
- SHA drift fail-closed
- page_count check
- default research profile read-only
- no P9 SET_VALUE
- VisualRef not P9 evidence
- parser defect routes upstream
- P8 11-tool logical contract remains frozen
- P9 v1 schema/action remains frozen

## 7. Repository-root pytest note

An exploratory `pytest` from repository root also collected vendored:

`dependencies/dayu-agent/tests`

The FFDF development .venv intentionally does not contain Dayu's independent test dependencies such as:
- typing_extensions
- requests

Those dependency-project collection errors occurred before FFDF test execution and are not part of the FFDF acceptance suite.

Authoritative FFDF acceptance scope remains:
- `tests/unit`
- FFDF integration MCP stdio check
- project live Golden checks

No Dayu dependency failure was reclassified as an FFDF PASS.

## 8. Codex constraint

No Codex invocation was used during implementation or Independent Acceptance.

Therefore the user restriction “if Codex is called, only Luna 5.6” was fully respected.

## Conclusion

**R-P Independent Acceptance: PASS**

- FFDF unit: 504 PASS
- MCP stdio: PASS
- CN/HK compatibility: PASS
- 605117 live visual: PASS
- 002371 Golden: PASS
- P9 durable reuse: PASS
- security/immutability: PASS

Next and final Gate:

R-Q — P10 Capability Reconciliation v2.
