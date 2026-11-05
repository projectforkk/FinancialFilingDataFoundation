# 105 — R-G / R-H / R-I Visual Review Evidence

## R-G Visual Trigger

实现 deterministic policy：

- REVIEW_REQUIRED 本身不触发 visual
- structured sufficient → NO_VISUAL
- target-unrelated → NO_VISUAL
- layout/conflict/insufficient + trusted source → VISUAL_REQUIRED
- NEEDS_UPSTREAM_FIX → UPSTREAM_FIX
- invalid/block/missing trusted source → BLOCKED

## R-H PDF Renderer

实现：

- ffdf_render_page
- ffdf_render_table
- ffdf_render_table_group
- NORMAL = 144 DPI
- HIGH_DETAIL = 216 DPI
- RGB / alpha=false / PNG
- P5 bbox + deterministic margin
- no caller bbox/path
- VisualRef + render SHA
- in-run dedupe
- deterministic tiling with fixed 18pt overlap
- payload/pixel budget
- no screenshot persistence

MCP server 返回：
- TextContent metadata
- real ImageContent(image/png)
- HIGH_DETAIL 请求 original image detail metadata

renderer tests：
- deterministic page PNG
- deterministic table crop
- HIGH_DETAIL distinct identity
- table-group routing
- no path leak
- deterministic tiling

最新 renderer suite：6 PASS。

## R-I Decision Policy

四类：

- EXPLICIT_AND_ANCHORABLE
- EXPLICIT_VISUAL_ONLY
- RAW_EXTRACTION_DEFECT
- AMBIGUOUS

RAW numeric mismatch 永远路由 Parser/Extraction Fix，不允许 P9 SET_VALUE。

## live 605117 Visual

2025FY 新能源行业 table p22：
- MCP content types = text + image
- renderer = ffdf-pdf-renderer-v1
- DPI = 144
- VisualRef = 8a94b1fb88cb62c152cae9ce4cb081dbfe980140e333fae6d45ff82073061a8c
- render SHA = 3c5a05b799409c179853d38251d819f3fdcc7c85b19b2388ffccf1bf01f07510

R-G / R-H / R-I：PASS。
