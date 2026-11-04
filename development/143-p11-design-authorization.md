# 143 — P11 US SEC Provider Design Authorization

Status: **AUTHORIZED — P11 DESIGN ONLY / PRODUCTION CLOSED**

Phase:
P11 — US SEC Provider

User authorization:
2026-11-04 — “继续推进”

Accepted predecessor:

- P10 = DONE / PASS
- P10 closeout = `development/142-p10-closeout.md`
- accepted P10 merge baseline = `a539500ef1fd0036eaa8d79a9bf7cfe78db57185`
- current main before P11 authorization = `2bea0837f5462fcbabe66174721cc604b2e79017`

## 1. Authorized scope

Only P11 design work is authorized:

- current environment/interface audit;
- official SEC/EDGAR source research;
- detailed design `design/26-p11-sec-provider-design.md`;
- implementation plan `design/27-p11-implementation-plan.md`;
- acceptance baseline;
- design reconciliation with P1/P2/P3-P7/P8/P9/P10;
- design-only tests/probes that do not modify production behavior;
- design review and design baseline commit/push.

## 2. Production remains closed

Not authorized yet:

- SEC provider production code;
- HTTP client/runtime/dependency changes;
- registry schema migration;
- non-PDF raw store implementation;
- HTML/iXBRL/XBRL parser implementation;
- P8/P9/P10 contract changes;
- Research MCP production;
- Semantic Resolver production.

Any production change before a frozen P11 design baseline + explicit development authorization is a STOP condition.

## 3. Design questions that must be resolved

P11 design must explicitly settle:

1. CIK / ticker / accession identity mapping;
2. form mapping for 10-K / 10-Q / 8-K and foreign issuer 20-F / 40-F / 6-K;
3. amended forms;
4. SEC Submissions API vs Archives filing artifacts;
5. User-Agent / Fair Access / <=10 req/s behavior;
6. HTML / Inline XBRL / XBRL source-set identity;
7. whether the canonical acquired object is one file or a filing package;
8. existing PDF-only RawStore incompatibility;
9. existing CN/HK-only source-host validation incompatibility;
10. document_sha256 and registry semantics for non-PDF artifacts;
11. parsing path that preserves raw source bytes and Evidence provenance;
12. taxonomy / custom-extension handling;
13. companyfacts role vs filing-primary source truth;
14. no-guessing / fallback rules;
15. incremental reuse semantics;
16. security, size, redirect, content-type, archive-path controls;
17. exact test/live acceptance fixtures and performance gates.

## 4. Source priority

Design facts must prefer official SEC sources:

- SEC EDGAR Data APIs;
- data.sec.gov submissions/XBRL APIs;
- SEC Archives;
- SEC Developer/Fair Access guidance;
- EDGAR technical specifications / XBRL guide.

Secondary sources cannot override official SEC behavior.

## 5. Design-First rule

If audit reveals an assumption conflict:

```text
STOP current sub-gate
→ record facts/root cause
→ amend design
→ commit/push new design baseline
→ only then authorize implementation
```

## 6. Exit condition

P11 production remains closed until all of:

- environment/interface audit = PASS;
- design/26 complete;
- design/27 complete;
- P11 acceptance baseline complete;
- design reconciliation complete;
- design review = PASS;
- design baseline committed/pushed;
- separate P11 development authorization recorded.

This authorization does not authorize P12 or any future optional layer.
