# Financial Filing Data Foundation

Financial Filing Data Foundation (FFDF) is a local, deterministic financial-filing data foundation.

Accepted production currently supports **CN and HK**. **P11 US SEC Provider has been reopened for a new design/development lifecycle and is not yet production-available.**

## Final project status

**P0-P10 ACCEPTED / CN-HK PRODUCTION / P11 US SEC REOPENED — DESIGN READY**

The accepted production baseline remains P0-P10 plus the accepted CN/HK user CLI. The 2026-11-05 CN/HK closeout remains historical evidence, but the user reopened P11 on 2026-11-09. Current P11 design uses official SEC submissions/Archives and an HTML/Inline-XBRL-first filing-package model. Production US support remains unavailable until independent P11 acceptance.

## Supported markets

Accepted production:
- CN — mainland China official filings, acquired through the accepted CNINFO/Dayu path.
- HK — Hong Kong official filings, acquired through the accepted HKEX/Dayu path.

Active development target:
- US — SEC/EDGAR filing packages (P11), **not yet accepted production**.

Until P11 acceptance, the production identity contract continues to expose `SUPPORTED_MARKETS = ("CN", "HK")`.

## What FFDF provides

1. deterministic filing identity, registry and incremental planning;
2. CN/HK official filing acquisition with provenance and content-addressed raw storage;
3. native PDF page/section extraction and FTS;
4. table candidate detection and cross-page table reconstruction;
5. raw facts with first-class evidence links;
6. deterministic quality validation and reuse gates;
7. local read-only MCP access to accepted data;
8. durable evidence-grounded review overlay;
9. dynamic Codex research integration over the accepted P8/P9 capabilities.

## Explicit non-goals

- EDGAR filing submission / filer-management APIs;
- treating every SEC filing as a PDF;
- automatic standardized quarterly mapping for every foreign private issuer 6-K without deterministic evidence;
- UK filing provider;
- remote AI calls from MCP or production parsing code;
- mutation of original source documents;
- silent guessing of filing identity, periods, facts or evidence;
- production Semantic Resolver or Research MCP beyond the accepted P8/P9/P10 boundary.

The P10 capability manifest correctly continues to report `P11_SEC_PROVIDER = UNAVAILABLE` until P11 passes independent acceptance and main integration.

## Project root

All FFDF-owned code, runtimes, worktrees, workspace data and temporary test paths are managed under:

`D:\Codex\FinancialFilingDataFoundation`

## Detailed usage manual

- Markdown: [`docs/FFDF_CN_HK_Usage_Manual.md`](docs/FFDF_CN_HK_Usage_Manual.md)
- Word: [`docs/FFDF_CN_HK_Usage_Manual.docx`](docs/FFDF_CN_HK_Usage_Manual.docx)
- User CLI: [`docs/FFDF_User_CLI.md`](docs/FFDF_User_CLI.md)
- MCP 部署与使用（中文注释）: [`docs/FFDF_MCP_部署与使用.md`](docs/FFDF_MCP_部署与使用.md)

The manual covers local runtimes, deployment health checks, CN/HK data preparation, P8 MCP, P9 Review Overlay, P10 Research Integration, testing, troubleshooting, backup boundaries, and day-to-day operating workflows.

The user CLI provides `ffdf acquire`, `ffdf ingest`, and `ffdf status` for self-service filing download, parsing, Registry persistence, and non-blocking P8 catalog publication.

## Accepted phase baseline

P0 through P10 are `DONE / PASS`. The final planned development sequence ends at P10.

Historical P11 design documents and branches are retained as audit history only. They are not production scope and must not be merged into the final CN/HK baseline without a new, explicit scope reopening.

## Verification

On Windows, use a short project-local pytest base path to avoid MAX_PATH false failures:

```powershell
$root='D:\Codex\FinancialFilingDataFoundation'
$tmp="$root\.t\u"
$env:TEMP=$tmp
$env:TMP=$tmp
$env:PYTHONPATH="$root\src"
& "$root\.venv\Scripts\python.exe" -m pytest -q --basetemp "$tmp\b" tests/unit
```

See `PROJECT_STATUS.md`, `design/30-project-final-cn-hk-scope.md`, and the final closeout/review records under `development/`.
