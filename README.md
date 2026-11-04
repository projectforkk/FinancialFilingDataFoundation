# Financial Filing Data Foundation

Financial Filing Data Foundation (FFDF) is a local, deterministic financial-filing data foundation for **CN and HK markets only**.

## Final project status

**PROJECT CLOSED / CN-HK SCOPE COMPLETE / US SEC OUT OF SCOPE**

The accepted production baseline is P0-P10. P11 US SEC Provider was authorized for design exploration only and is now superseded by the final CN/HK scope decision. No SEC provider production is part of this project closeout.

## Supported markets

- CN — mainland China official filings, acquired through the accepted CNINFO/Dayu path.
- HK — Hong Kong official filings, acquired through the accepted HKEX/Dayu path.

The production identity contract exposes `SUPPORTED_MARKETS = ("CN", "HK")`. Other markets are rejected by the accepted identity/planner/acquisition boundary.

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

- US SEC HTML / Inline XBRL / XBRL provider;
- UK filing provider;
- remote AI calls from MCP or production parsing code;
- mutation of original source documents;
- silent guessing of filing identity, periods, facts or evidence;
- production Semantic Resolver or Research MCP beyond the accepted P8/P9/P10 boundary.

The P10 capability manifest intentionally continues to report `P11_SEC_PROVIDER = UNAVAILABLE` for accepted-contract compatibility.

## Project root

All FFDF-owned code, runtimes, worktrees, workspace data and temporary test paths are managed under:

`D:\Codex\FinancialFilingDataFoundation`

## Detailed usage manual

- Markdown: [`docs/FFDF_CN_HK_Usage_Manual.md`](docs/FFDF_CN_HK_Usage_Manual.md)
- Word: [`docs/FFDF_CN_HK_Usage_Manual.docx`](docs/FFDF_CN_HK_Usage_Manual.docx)
- User CLI: [`docs/FFDF_User_CLI.md`](docs/FFDF_User_CLI.md)

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
