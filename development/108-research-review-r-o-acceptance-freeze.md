# 108 — Research Review MCP v3 R-O Acceptance Freeze

## Candidate

Implementation candidate commit:

`99e212d19a0f7b11e7f5718805d55f2ba27b31a3`

Branch:

`design/research-review-mcp-v3`

工作树冻结时只有既存未跟踪目录：

- 00document/
- 01prompt/

它们不属于候选范围。

## Runtime Freeze

Development test Python:

`Python 3.14.9`

Production MCP dedicated runtime:

`Python 3.12.14`

MCP SDK:

`mcp 2.3.0`

PyMuPDF:

`1.28.2`

## Renderer Freeze

- renderer_version = ffdf-pdf-renderer-v1
- NORMAL DPI = 144
- HIGH_DETAIL DPI = 216
- PNG
- RGB
- alpha = false
- max PNG bytes = 10 MiB
- max pixel area = 24,000,000
- deterministic tile overlap = 18 pt
- caller arbitrary bbox = prohibited
- caller filesystem path = prohibited

Renderer behavior changes after this freeze require renderer_version bump and re-acceptance.

## Catalog / Golden Hashes

Live catalog:

`B263C6950C01CCC09230C34DA7947908B80C05F839B399148C533B90C55F524D`

Acceptance catalog:

`E493F2F6A951007C1E5AC932268796D35D33386760F4503D48FF0A7F7A148CDC`

002371 2026Q3 original PDF:

`A0F8D84AB724F7C62B690D6504215602A623FC185C53C9E1079CD40653C600B9`

## Frozen Contracts

- P8_RAW_V1 logical contract: 11 tools
- Report-Safe v1: 3 tools
- Research Review v1: 12 tools
- candidate server surface: 26 tools
- P9 v1 action/schema unchanged
- RESEARCH_FALLBACK default
- QUALITY_REVIEW explicit
- Codex invocation, if any: Luna 5.6 only

## Pre-Freeze Test Evidence

R-N:

- mcp + research + review = 285 PASS / 0 FAIL
- compileall PASS
- Report-Safe private _bundle dependency = none
- stale 14-tool deployment claim = none
- formal review blocking findings = 0

## Freeze Rule

R-P Independent Acceptance may not modify implementation code.

If R-P finds a code defect:

1. mark R-P FAIL;
2. reopen design/implementation Gate;
3. fix;
4. produce a new candidate commit;
5. repeat R-O freeze;
6. rerun R-P from the beginning.

R-O Acceptance Freeze: PASS.
