# Financial Filing Data Foundation

Financial Filing Data Foundation (FFDF) is a local, deterministic financial-filing data foundation.

Accepted production supports **CN, HK, and US**. The P11 US SEC Provider has completed independent acceptance and main integration.

## Final project status

**P0-P11 DONE / PASS / CN-HK-US ACCEPTED PRODUCTION**

The accepted production baseline now includes P0-P11. The 2026-11-05 CN/HK closeout remains historical evidence; P11 was explicitly reopened on 2026-11-09 and later completed independent acceptance and fast-forward main integration. US production uses official SEC submissions/Archives, complete-submission source provenance, and HTML/Inline-XBRL-first filing packages.

## Supported markets

Accepted production:
- CN — mainland China official filings, acquired through the accepted CNINFO/Dayu path.
- HK — Hong Kong official filings, acquired through the accepted HKEX/Dayu path.
- US — SEC/EDGAR filing packages, accepted through P11.

The production identity contract exposes `SUPPORTED_MARKETS = ("CN", "HK", "US")`.

## What FFDF provides

1. deterministic filing identity, registry and incremental planning;
2. CN/HK official filing acquisition plus accepted US SEC filing-package acquisition with immutable provenance and content-addressed raw storage;
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

P11 has passed independent acceptance and main integration. The legacy `FFDF_P11_US_DEV` helper remains only as a low-level compatibility/testing surface; the accepted production CLI does not depend on that development bypass.

## Project root

All FFDF-owned code, runtimes, worktrees, workspace data and temporary test paths are managed under:

`D:\Codex\FinancialFilingDataFoundation`

## Detailed usage manual

- Markdown: [`docs/FFDF_CN_HK_Usage_Manual.md`](docs/FFDF_CN_HK_Usage_Manual.md)
- Word: [`docs/FFDF_CN_HK_Usage_Manual.docx`](docs/FFDF_CN_HK_Usage_Manual.docx)
- User CLI: [`docs/FFDF_User_CLI.md`](docs/FFDF_User_CLI.md)
- MCP 部署与使用（中文注释）: [`docs/FFDF_MCP_部署与使用.md`](docs/FFDF_MCP_部署与使用.md)

The manuals cover local runtimes, deployment health checks, CN/HK data preparation, the user CLI, P8 MCP, P9 Review Overlay, P10 Research Integration, testing, troubleshooting, backup boundaries, and day-to-day operating workflows. P11 adds accepted US SEC acquisition/ingest/status through the same user CLI surface.

The user CLI provides `ffdf acquire`, `ffdf ingest`, and `ffdf status` for CN/HK/US self-service filing acquisition, parsing, Registry persistence, and non-blocking P8 catalog publication.

## Accepted phase baseline

P0 through P11 are `DONE / PASS`. P11 is formally accepted and integrated into `main`.

Historical P11 repair/test artifacts remain audit history. Future market/provider expansion or Research MCP/Semantic Resolver production work requires a new explicit lifecycle.

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

See `PROJECT_STATUS.md`, the historical `design/30-project-final-cn-hk-scope.md`, the P11 reopening/design chain, and the final closeout/review records under `development/`.
