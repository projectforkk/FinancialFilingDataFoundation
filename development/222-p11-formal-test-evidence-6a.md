# P11 Formal Test Evidence 6A — Evidence Remediation

Execution result: `EXECUTION_PASS`

This is the targeted Acceptance/Test Agent evidence remediation authorized by
`development/221-p11-formal-test-execution-authorization-6a.md`. It does not
reopen development, create a production candidate, or make an independent
Formal Acceptance decision.

## 1. Exact authority and freeze

| Authority | Exact value |
|---|---|
| Repository | `projectforkk/FinancialFilingDataFoundation` |
| Authoritative lineage | `reconcile/p11-140-143-local-chain` |
| Design 40 freeze | `db8edabb2630549e2d75a5becaccb15cb1c53749` |
| Frozen production candidate | `7aac34e763b4c9caac24489eb049aa3dc6efb026` |
| Review 9 | `5fe0bc139f9a2b0475a1912c65f40008e84572f4` |
| Formal Test Plan 6 | `31cf1f04bb5ea56409e1e44230460d9b98060833` |
| Formal Test 6 Authorization | `4aaa4b8076546f9daa258e1827cd1a61e3eeffbf` |
| Formal Test 6 Evidence | `01f60a3568c703a988962badbb1f3c74dd84f112` |
| Formal Acceptance Review 6 | `6a021c04d423ce89f1d7c29d1612661906481321` |
| Formal Test 6A Plan | `abccc6618614e7f18be93d56eba952c4f28e30ca` |
| Formal Test 6A Authorization | `36cc8eb37004b1d99584b5c62e585f934ebbbe5b` |
| Execution HEAD before this evidence | `36cc8eb37004b1d99584b5c62e585f934ebbbe5b` |

The historical SHA `09e3174b7e19a60cc5955862670fac8931af67db` is not described
as the Design 40 baseline in this evidence. The exact Design 40 freeze is
`db8edabb2630549e2d75a5becaccb15cb1c53749`.

`git fetch origin` and fast-forward-only synchronization were completed before
execution. The local HEAD and authoritative remote were both
`36cc8eb37004b1d99584b5c62e585f934ebbbe5b` before this evidence commit.

## 2. FT6A-00 — authority and candidate drift

The candidate was verified as an ancestor of HEAD. The pre-evidence worktree
was clean, `git diff --check` exited 0, and `FFDF_P11_US_DEV` was absent.
`FFDF_SEC_CONTACT_EMAIL` was recorded only as `CONFIGURED`; its value was not
recorded.

The complete post-candidate diff before this evidence file was documentation /
governance only:

```text
M  PROJECT_STATUS.md
M  design/00-design-management-index.md
A  development/214-p11-issue148-development-evidence.md
A  development/215-p11-fresh-full-exact-candidate-review-9.md
A  development/216-p11-formal-test-plan-6.md
A  development/217-p11-formal-test-execution-authorization-6.md
A  development/218-p11-formal-test-evidence-6.md
A  development/219-p11-formal-acceptance-review-6.md
A  development/220-p11-formal-test-plan-6a-evidence-remediation.md
A  development/221-p11-formal-test-execution-authorization-6a.md
```

Forbidden `src/`, `tests/`, dependency, and runtime paths in that diff: 0.

FT6A-00: `PASS`.

## 3. Request-capture method and mutually exclusive classifier

Acceptance-only harness:

```text
D:\ffdf-p11-ft6a\FT-6A-url-receipts.py
```

The harness replaced the SEC HTTP client only at the acceptance transport
boundary. It recorded, in chronological order, the sequence number, method,
requested URL, final URL, status, actor (`acquire` or `ingest`), and exactly
one category. P8/MCP was then exercised with the SEC client replaced by a
forbidden client; any network attempt would fail the harness.

Classification order was deliberately:

1. ticker map;
2. current submissions versus history submissions;
3. archive index;
4. complete-submission `.txt`;
5. individual archive member;
6. static/browser asset;
7. other SEC.

Therefore the complete-submission `.txt` URL cannot also be classified as an
individual archive member. All captured final URLs retained the same category
as their requested URL and returned HTTP 200.

## 4. FT6A-01 — Apple FY2025 Q3 fresh root

Fresh root:

```text
D:\ffdf-p11-ft6a\apple-q3
```

Commands:

```text
acquire --market US --ticker AAPL --year 2025 --period Q3
ingest --market US --ticker AAPL --year 2025 --period Q3
```

The expected and actual accession were both
`0000320193-25-000073`. The complete-submission identity was:

```text
URL: https://www.sec.gov/Archives/edgar/data/320193/000032019325000073/0000320193-25-000073.txt
source-container SHA: 83a65bbe8d3ab67e4f35769cbb56c46eb0b557c2b0890b940b2d76e59548ad87
source-container length: 5304776
package SHA: 194e409b107b8a9014d8d796396f66d602cbdee90ae1bd7681830a960f55cb9a
package-source provenance SHA: 1136c59e7b4495f3fae68c73fe1d9ca624c2f5efeb8c468deb1212671aabd285
```

Validation and P8 receipts:

```text
validation path: p11-sec-validation-v4
validation: PASS
compatibility: COMPATIBLE
blocking issues: 0
reuse_eligible: true
ingest planner action: PARSE_LOCAL
research_ready: true
acquire exit: 0
ingest exit: 0
P8/MCP SEC network attempts: 0
P8 document: 40 pages, 38 tables, 769 Raw Facts, 769 evidence records, 0 validation issues
```

Selected package members:

| Relative name | Role | Length | Member SHA-256 |
|---|---|---:|---|
| `FilingSummary.xml` | FILING_SUMMARY | 27303 | `f087d0ffa4b5d06c2f9530864f211d7d3f7b7ffb0d77fb196eaec5a62cc2b326` |
| `aapl-20250628.htm` | PRIMARY_DOCUMENT | 888048 | `ec86034c4029ea892d587f95cf5c9c2e3a08228929fbabf269dec3c1cb26d768` |
| `aapl-20250628.xsd` | XBRL_SCHEMA | 35427 | `a040fc385608214977377b2408834fda5cec6010e1810d4aaa9f01cd662befa5` |
| `aapl-20250628_cal.xml` | XBRL_CALCULATION | 78163 | `7ca2a1a1fa5302689d66dda5da6df42059422c37c21c9aa5b6c80451e6769e0d` |
| `aapl-20250628_def.xml` | XBRL_DEFINITION | 154707 | `ee4bea096ec2e17cd84c59f9dfbe72513ca7c91345bab9f7abdc77ddf6f597cf` |
| `aapl-20250628_lab.xml` | XBRL_LABEL | 505708 | `7db99a6df6c33277f890f2f29f14f146bfd6b96d2a9c3f631e0772be3e08be0b` |
| `aapl-20250628_pre.xml` | XBRL_PRESENTATION | 322565 | `4e62e7489a364118ae9d94198f4b6944f0b676143e7595fd9537c35c5214e128` |

### Apple chronological SEC URL receipt

| Sequence | Actor | Method | Exact URL | Category | Status |
|---:|---|---|---|---|---:|
| 1 | acquire | GET | `https://www.sec.gov/files/company_tickers.json` | TICKER_MAP | 200 |
| 2 | acquire | GET | `https://data.sec.gov/submissions/CIK0000320193.json` | CURRENT_SUBMISSIONS | 200 |
| 3 | acquire | GET | `https://www.sec.gov/Archives/edgar/data/320193/000032019325000073/0000320193-25-000073.txt` | COMPLETE_SUBMISSION | 200 |
| 4 | ingest | GET | `https://www.sec.gov/files/company_tickers.json` | TICKER_MAP | 200 |
| 5 | ingest | GET | `https://data.sec.gov/submissions/CIK0000320193.json` | CURRENT_SUBMISSIONS | 200 |

Apple mutually exclusive totals:

```text
TICKER_MAP                  = 2
CURRENT_SUBMISSIONS         = 2
HISTORY_SUBMISSIONS         = 0
COMPLETE_SUBMISSION         = 1
INDIVIDUAL_ARCHIVE_MEMBER   = 0
ARCHIVE_INDEX               = 0
STATIC_OR_BROWSER_ASSET     = 0
OTHER_SEC                   = 0
```

FT6A-01: `PASS`.

## 5. FT6A-02 — Toyota FY2025 20-F fresh root

Fresh root:

```text
D:\ffdf-p11-ft6a\toyota-fy
```

Commands:

```text
acquire --market US --ticker TM --year 2025 --period FY
ingest --market US --ticker TM --year 2025 --period FY
```

The expected and actual accession were both
`0001193125-25-142326`. The complete-submission identity was:

```text
URL: https://www.sec.gov/Archives/edgar/data/1094517/000119312525142326/0001193125-25-142326.txt
source-container SHA: b1564b0cd42563fec3fe0fa838b57f3c1c01bb01a48ee445104f211f098ea7e0
source-container length: 44152781
package SHA: 8195c504b7aa9c1ce981dfafd39c73bd799029b6ad14da32855ba7ea3b762e4b
package-source provenance SHA: f02b070a4e59e621db58e388a31c8209c8c6ccf59f5389be4ee6888c6a4ef9f1
```

Validation and P8 receipts:

```text
validation path: p11-sec-validation-v4
validation: PASS
compatibility: COMPATIBLE
blocking issues: 0
reuse_eligible: true
ingest planner action: PARSE_LOCAL
research_ready: true
acquire exit: 0
ingest exit: 0
P8/MCP SEC network attempts: 0
P8 document: 182 pages, 419 tables, 3373 Raw Facts, 3373 evidence records, 0 validation issues
```

Selected package members:

| Relative name | Role | Length | Member SHA-256 |
|---|---|---:|---|
| `FilingSummary.xml` | FILING_SUMMARY | 109770 | `2cd16ed1715a1e3e259993147605c68cd2128f1f05e71a123afd98bade29fd10` |
| `d925022d20f.htm` | PRIMARY_DOCUMENT | 6419260 | `93e4b4e45640b253576af193de6c6711a11902083b2a0e14758089ae6aac48e8` |
| `tm-20250331.xsd` | XBRL_SCHEMA | 3470639 | `1afafd34e4c934bbd1a05f0348ba862168d04a77285a488150387306f30ace9c` |

### Toyota chronological SEC URL receipt

| Sequence | Actor | Method | Exact URL | Category | Status |
|---:|---|---|---|---|---:|
| 6 | acquire | GET | `https://www.sec.gov/files/company_tickers.json` | TICKER_MAP | 200 |
| 7 | acquire | GET | `https://data.sec.gov/submissions/CIK0001094517.json` | CURRENT_SUBMISSIONS | 200 |
| 8 | acquire | GET | `https://www.sec.gov/Archives/edgar/data/1094517/000119312525142326/0001193125-25-142326.txt` | COMPLETE_SUBMISSION | 200 |
| 9 | ingest | GET | `https://www.sec.gov/files/company_tickers.json` | TICKER_MAP | 200 |
| 10 | ingest | GET | `https://data.sec.gov/submissions/CIK0001094517.json` | CURRENT_SUBMISSIONS | 200 |

Toyota mutually exclusive totals:

```text
TICKER_MAP                  = 2
CURRENT_SUBMISSIONS         = 2
HISTORY_SUBMISSIONS         = 0
COMPLETE_SUBMISSION         = 1
INDIVIDUAL_ARCHIVE_MEMBER   = 0
ARCHIVE_INDEX               = 0
STATIC_OR_BROWSER_ASSET     = 0
OTHER_SEC                   = 0
```

FT6A-02: `PASS`.

## 6. FT6A-03 — reconciliation of Evidence 218

Evidence 218 recorded both FT-19 and FT-20 as:

```text
archive member = 1
```

The earlier external harness classifier checked:

```text
if path.startswith("/Archives/") and path.endswith("/index.json"): archive_index
if path.startswith("/Archives/"): archive_member
```

It had no mutually exclusive `COMPLETE_SUBMISSION` branch. Consequently, the
one actual complete-submission `.txt` request in each run was counted under
the broad `/Archives/` member branch. The earlier URL lists contained the
complete `.txt` URL and no individual `.htm`, `.xml`, `.xsd`, or linkbase URL.

The 6A harness corrected the order and captured every request. In both fresh
runs, the `.txt` request is classified only as `COMPLETE_SUBMISSION`, and no
request has an individual member category. The old values are therefore a
`CLASSIFICATION_ERROR`, not a product member fetch. There is no
`REAL_PRODUCT_MEMBER_FETCH`.

FT6A-03: `PASS / CLASSIFICATION_ERROR`.

## 7. Final evidence-integrity boundary

Before creating this file:

```text
git status --short: empty
git diff --check: exit 0
candidate ancestor check: exit 0
forbidden post-candidate source/test/dependency/runtime paths: 0
FFDF_P11_US_DEV: ABSENT
FFDF_SEC_CONTACT_EMAIL: CONFIGURED; value not recorded
```

This is the only tracked file created by Formal Test 6A. The URL harness,
chronological raw receipt, and fresh roots remain outside Git under
`D:\ffdf-p11-ft6a`.

## 8. Final execution result and stop boundary

All targeted gates FT6A-00 through FT6A-03 passed. The execution result is:

```text
EXECUTION_PASS
```

No source, test, dependency, runtime, or production-candidate change was
made. No new candidate was created. Formal Acceptance is not declared here.

After the documentation-only evidence commit is pushed, the fixed next action
is:

```text
STOP FOR CHATGPT FORMAL ACCEPTANCE REVIEW 6 CONTINUATION
```
