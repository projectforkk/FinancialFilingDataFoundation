# 214 — P11 ISSUE-148 Development Evidence

Status: **DEVELOPMENT COMPLETE — READY FOR FRESH FULL EXACT-CANDIDATE REVIEW**

This document records development evidence only. It is not Formal Test
authorization, Formal Acceptance, main-merge authorization, or a P11 DONE
record.

## 1. Authority and candidate identity

Repository: `projectforkk/FinancialFilingDataFoundation`

Authoritative remote branch: `reconcile/p11-140-143-local-chain`

Development authorization:

```text
30a34a7e68894cea6cbdea9cbf9bd037e9d97def
```

Design 40 freeze:

```text
db8edabb2630549e2d75a5becaccb15cb1c53749
```

Design review: `762bc471c3fe553496a7ecef73450013d49fd189`

Production/test candidate:

```text
7aac34e763b4c9caac24489eb049aa3dc6efb026
```

The candidate is a descendant of the authorization commit and was pushed
normally, without force, as:

```text
origin/reconcile/p11-140-143-local-chain
30a34a7e..7aac34e7
```

Candidate contents are limited to production source and `tests/unit/us_sec`.
This evidence file is intentionally a separate documentation-only commit.

## 2. Implemented Design 40 scope

- Exact SEC complete-submission `.txt` URL construction and validation.
- Immutable `p11-sec-source-container-v1` storage with SHA-256 and byte length.
- Strict byte-oriented `<DOCUMENT>` / `<TYPE>` / `<SEQUENCE>` / `<FILENAME>` /
  `<TEXT>` inventory and deterministic TEXT/XML/XBRL slices.
- Package member selection from the complete submission only; public member
  URLs remain citation URLs.
- External `p11-sec-package-source-v1` provenance with replayable locators.
- Registry v5 source-container, provenance, and member-locator tables.
- Validation `p11-sec-validation-v4` binding package, provenance, and current
  validation artifact.
- Current planner and P8 eligibility require replayable current provenance and
  Registry verification; legacy unattested packages remain audit-only.
- Existing package SHA, manifest `p11-sec-package-v1`, parser `VIRTUAL_HTML_V6`,
  and parsed artifact `p11-sec-artifacts-v2` remain unchanged.

## 3. Deterministic verification

All commands used the project virtual environment and short project-local
pytest temporary roots.

| Check | Result |
|---|---:|
| T148 focused (`test_issue148.py`) | 20 passed |
| ISSUE-146/147/148 exact-candidate focused rerun | 39 passed |
| Full `tests/unit/us_sec` exact-candidate rerun | 283 passed |
| MCP-focused `tests/unit/mcp` | 65 passed |
| Full `tests/unit` exact-candidate rerun | 813 passed |
| `python -m compileall -q src tests` | PASS |
| `git diff --check` | PASS |

One post-candidate attempt used an unnecessarily long basetemp and produced
four Windows `FileNotFoundError` failures while creating discovery temporary
files; no test body reached an assertion. The rerun with the required short
basetemp passed all 39 ISSUE-146/147/148 tests. No test was skipped.

## 4. Live developer smoke

`FFDF_P11_US_DEV` was absent for every live run. The configured SEC contact
email was present; its value is intentionally not recorded.

### 4.1 Apple FY2025, independent fresh roots A and B

Roots:

```text
D:\Codex\FinancialFilingDataFoundation\w\live-issue148-apple-a
D:\Codex\FinancialFilingDataFoundation\w\live-issue148-apple-b
```

Both roots were empty before ticker-based `ingest --market US --ticker AAPL
--year 2025 --period FY`.

| Identity | Root A | Root B | Equal |
|---|---|---|---|
| Accession | `0000320193-25-000079` | `0000320193-25-000079` | YES |
| Complete-submission SHA-256 | `60f22bb90bb8e46894019fd57c27df69abd192f3f0f4183c4345d786426f3391` | same | YES |
| Complete-submission length | `9392337` | `9392337` | YES |
| Provenance SHA-256 | `e4079ed2fb840c2b781e1042a58470a20894b020f9c16742153a6585c28b221c` | same | YES |
| Package SHA-256 | `339ad69b637803fc7dd8f09a71b151d596c28869e0019a06e6f35e320a0ddc43` | same | YES |
| Validation | `p11-sec-validation-v4`, PASS, 0 blocking | same | YES |
| `research_ready` | `true` | `true` | YES |

Authoritative source URL:

```text
https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/0000320193-25-000079.txt
```

Selected member identity and complete-submission locator replay:

| Member | Role | Type / Seq | Document index | Payload bytes | Member SHA-256 | Payload offsets | Envelope |
|---|---|---|---:|---:|---|---|---|
| `aapl-20250927.htm` | PRIMARY_DOCUMENT | `10-K / 1` | 1 | 1,520,208 | `548ae59778cf08ee0f2ee088e7ece20d947076c3c01f74d2d65db4c2777e436a` | `1254:1521462` | XBRL |
| `aapl-20250927.xsd` | XBRL_SCHEMA | `EX-101.SCH / 8` | 8 | 56,313 | `e697d106fae1543535c634bede6337b8f1ecd987e7655eb91c62913900ab6335` | `1687679:1743992` | XBRL |
| `aapl-20250927_cal.xml` | XBRL_CALCULATION | `EX-101.CAL / 9` | 9 | 153,156 | `314091ba88cd58f392874866c19010ed9facdd643f34f0afbcf37137192c5f05` | `1744173:1897329` | XBRL |
| `aapl-20250927_def.xml` | XBRL_DEFINITION | `EX-101.DEF / 10` | 10 | 224,664 | `6eb3e955297ea510ceaff7331f57dc948cb439e83a634a3882f3806d6fb7434a` | `1897510:2122174` | XBRL |
| `aapl-20250927_lab.xml` | XBRL_LABEL | `EX-101.LAB / 11` | 11 | 763,631 | `9ec8874c0af055946d80061bd5558599c4eb2b56b21e48a4670751097d166118` | `2122350:2885981` | XBRL |
| `aapl-20250927_pre.xml` | XBRL_PRESENTATION | `EX-101.PRE / 12` | 12 | 496,062 | `43ce57fec893a2c2974a043198a3acc105238aaf19cb4a93ba8812d412d0ab7d` | `2886164:3382226` | XBRL |
| `FilingSummary.xml` | FILING_SUMMARY | `XML / 89` | 87 | 42,775 | `f5e632bd6de8965a5251fd590f053553c017396f5ec75b0ddc9e475832a7c0a2` | `6263240:6306015` | XML |

The public citation URL for each member is the accession archive member URL;
none of those individual member responses was fetched during package
construction.

Post-candidate fresh Apple smoke root:

```text
D:\Codex\FinancialFilingDataFoundation\w\live-issue148-apple-candidate
```

It reproduced the same accession, source SHA and length, provenance SHA,
package SHA, all seven member SHA/length pairs, validation-v4 PASS, zero
blocking issues, and `research_ready=true`. Its recorded network requests
were exactly:

```text
1  https://www.sec.gov/files/company_tickers.json
1  https://data.sec.gov/submissions/CIK0000320193.json
1  https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/0000320193-25-000079.txt
```

Request classification: complete-submission `1`, archive index `0`,
individual member `0`, static/browser asset `0`.

### 4.2 Apple FY2025 Q3

Fresh root: `D:\Codex\FinancialFilingDataFoundation\w\live-issue148-q3`

```text
accession       = 0000320193-25-000073
form            = 10-Q
report_period   = 2025-06-28
source_sha256   = 83a65bbe8d3ab67e4f35769cbb56c46eb0b557c2b0890b940b2d76e59548ad87
source_length   = 5304776
provenance_sha  = 1136c59e7b4495f3fae68c73fe1d9ca624c2f5efeb8c468deb1212671aabd285
package_sha256  = 194e409b107b8a9014d8d796396f66d602cbdee90ae1bd7681830a960f55cb9a
members         = 7
validation      = p11-sec-validation-v4 / PASS / 0 blocking
research_ready  = true
```

Selected member SHA/length pairs were independently recorded for
`FilingSummary.xml`, `aapl-20250628.htm`, `aapl-20250628.xsd`, and the CAL,
DEF, LAB, and PRE XML members. Network requests were one submissions request
and one complete-submission request; no archive index or individual member
request was made.

### 4.3 Toyota FY2025 20-F

Fresh root: `D:\Codex\FinancialFilingDataFoundation\w\live-issue148-toyota`

```text
accession       = 0001193125-25-142326
form            = 20-F
report_period   = 2025-03-31
source_sha256   = b1564b0cd42563fec3fe0fa838b57f3c1c01bb01a48ee445104f211f098ea7e0
source_length   = 44152781
provenance_sha  = f02b070a4e59e621db58e388a31c8209c8c6ccf59f5389be4ee6888c6a4ef9f1
package_sha256  = 8195c504b7aa9c1ce981dfafd39c73bd799029b6ad14da32855ba7ea3b762e4b
members         = 3
validation      = p11-sec-validation-v4 / PASS / 0 blocking
research_ready  = true
```

The three selected members were `FilingSummary.xml` (109,770 bytes),
`d925022d20f.htm` (6,419,260 bytes), and `tm-20250331.xsd` (3,470,639
bytes); all member hashes were recorded and replayed from the complete
submission container. Network requests were one submissions request and one
complete-submission request.

### 4.4 Kellanova amendment/conflict regression

Fresh root: `D:\Codex\FinancialFilingDataFoundation\w\live-issue148-kellanova`

Ticker `K`, CIK `0000055067`, FY2024/FY acquisition stopped during discovery
with the expected result:

```text
reason_code = P11_AMENDED_VARIANT_PRESENT
catalog      = absent
package      = not acquired
```

The only network request was the submissions JSON. The original and 10-K/A
variants were not silently selected and no complete-submission package fetch
was attempted.

## 5. Lifecycle boundary

The development candidate and this separate evidence record do not authorize
Formal Test, Formal Acceptance, main merge, or P11 DONE.

```yaml
ISSUE-148: DEVELOPMENT AUTHORIZED
DESIGN 40: DESIGN_FREEZE_PASS
FORMAL TEST: NOT AUTHORIZED
FORMAL ACCEPTANCE: NOT PASSED
MAIN MERGE: NOT AUTHORIZED
P11 DONE: NO
```

Next action: stop for ChatGPT Fresh Full Exact-Candidate Review.
