# 30 — Project Final CN/HK Scope Contract

Status: **FROZEN FOR PROJECT CLOSEOUT**

## 1. Decision

The Financial Filing Data Foundation production scope is finalized as **CN and HK only**.

The exact supported market identifiers are:

```text
CN
HK
```

Production code exposes this through `financial_filing_data_foundation.identity.SUPPORTED_MARKETS`.

## 2. In-scope production baseline

The accepted P0-P10 baseline remains authoritative:

- P0 native PDF feasibility;
- P1 identity / registry / incremental planner;
- P2 CN/HK acquisition;
- P3 page / section / FTS;
- P4 table candidates;
- P5 table reconstruction;
- P6 raw facts / evidence;
- P7 validation;
- P8 local read-only MCP;
- P9 durable review overlay;
- P10 dynamic research integration.

No accepted P0-P10 behavior is weakened by this closeout.

## 3. Out-of-scope providers

The following are not part of the final production scope:

- US SEC Provider;
- US HTML / Inline XBRL / XBRL acquisition or parsing;
- UK filing provider;
- any other market not explicitly equal to CN or HK.

Unsupported markets must continue to fail closed at the existing identity/planner/acquisition boundary.

## 4. P11 disposition

`development/143-p11-design-authorization.md` and later P11 work on non-main branches are historical design exploration only.

Final disposition:

`P11 = OUT_OF_SCOPE / NOT_REQUIRED_NOT_EXECUTED`

Rules:

1. do not merge unaccepted P11 production branches into the final baseline;
2. do not delete historical P11 design evidence merely to hide history;
3. do not represent P11-A/B/C/D branch work as accepted production on `main`;
4. retain `P11_SEC_PROVIDER = UNAVAILABLE` in the accepted P10 capability manifest for compatibility;
5. a future US initiative requires a new explicit scope authorization and a fresh design/development/review/acceptance lifecycle.

## 5. Code-level scope invariant

`SUPPORTED_MARKETS = ("CN", "HK")` is the public scope declaration.

`CompanyRef` and `FilingSlotKey` continue to enforce the existing closed market set. This closeout adds no fallback mapping and no alias from US/UK to CN/HK.

## 6. Data and runtime boundaries

- original source documents remain immutable;
- FFDF-owned files stay under `D:\Codex\FinancialFilingDataFoundation`;
- main runtime remains separated from the Dayu and MCP runtimes;
- no MCP AI API calls;
- no remote AI API inside production parsing/acquisition code;
- deterministic evidence and validation boundaries remain unchanged.

## 7. Closeout gate

Project closeout requires:

1. documentation state reconciled to CN/HK-only scope;
2. code scope invariant exposed and tested;
3. full unit regression PASS using a short Windows project-local basetemp;
4. integration/smoke and compile checks PASS;
5. repository-wide design/code consistency review;
6. clean Git diff/check before commit.
