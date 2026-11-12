# P11 Formal Test Execution 3 — Failure Evidence

Date: 2026-11-12

Status: `EXECUTION_FAIL`

This is a failure record for the completed formal execution. It is not an acceptance record and does not authorize a production merge or P11 DONE.

## Frozen execution inputs

| Item | Exact value |
|---|---|
| Production candidate | `9389d59d68c84762b55b29bedb973db4ea45256a` |
| Corrected design baseline | `09e3174b7e19a60cc5955862670fac8931af67db` |
| Formal Test Plan | `development/183-p11-formal-test-plan-3.md` |
| Formal Test Plan commit | `4e4961dd4b37b2bd50c2d162ea99fa155fbfff27` |
| Formal execution prompt | `development/184-p11-formal-test-execution-prompt-3.md` |
| Prompt commit / execution HEAD | `aa54e38591d5ea003fcae5a1c6a3109f10f0bf94` |
| Branch | `task/p11-sec-rebuild-development` |
| `FFDF_P11_US_DEV` | absent |
| `FFDF_SEC_CONTACT_EMAIL` | configured; value intentionally not recorded |
| Main merge | not run |

The execution started from the reviewed candidate with documentation-only post-candidate history. The formal execution stopped at the first required live defect and did not patch production or test files.

## Formal gate result

| Gate group | Result |
|---|---|
| FT-00 candidate freeze / production-mode preflight | `PASS` |
| FT-01 deterministic regression / compile | `PASS` |
| FT-02 ISSUE-131 trust boundary | `PASS` |
| FT-03 Registry v3 → v4 | `PASS` |
| FT-04 V4/v1 → V5/v2 compatibility | `PASS` |
| FT-05 discovery freshness / ticker | `PASS` |
| FT-06 fact-source / continuation / OTHER XML | `PASS` |
| FT-07 DOM table semantics | `PASS` |
| FT-08 provenance / HTTP / security | `PASS` |
| FT-09 production capability / no-AI / P8 no-network | `PASS` |
| FT-10 Apple FY2025 10-K | `FAIL` |
| FT-11 Apple FY2025 Q3 + P8 | `BLOCKED` |
| FT-12 Toyota FY2025 20-F | `BLOCKED` |
| FT-13 Kellanova amendment | `BLOCKED` |
| FT-14 repeat online discovery + reuse | `BLOCKED` |
| FT-15 CN/HK + P0-P10 preservation | `BLOCKED` by the formal stop boundary |

Developer-regression records retained under the disposable formal workspace include:

- `work/p11-formal-acceptance-9389d59d/evidence/FT-00-preflight.txt`
- `work/p11-formal-acceptance-9389d59d/evidence/FT-01-issue131-p8-focused.txt`
- `work/p11-formal-acceptance-9389d59d/evidence/FT-01-us-sec.txt`
- `work/p11-formal-acceptance-9389d59d/evidence/FT-01-full-unit.txt`
- `work/p11-formal-acceptance-9389d59d/evidence/FT-01-p0p10-focused.txt`
- `work/p11-formal-acceptance-9389d59d/evidence/FT-01-compileall.txt`
- `work/p11-formal-acceptance-9389d59d/evidence/FT-01-git-diff-check.txt`

These raw logs remain outside Git and contain no committed source/test changes or SEC contact value.

## FT-10 failure receipt

| Field | Observed value |
|---|---|
| Company | Apple Inc. |
| CIK | `0000320193` |
| Accession | `0000320193-25-000079` |
| Form / period | `10-K` / FY2025 |
| Primary document | `aapl-20250927.htm` |
| Discovery observation SHA | `684038711efc8eef02b3540cc2aca7f5edda55987727da08cd4c15932b700dd0` |
| Failing filing-local member | `aapl-20250927_g1.jpg` |
| Actual response content type | `image/jpeg` |
| Reason code | `P11_CONTENT_TYPE_INVALID` |
| Execution result | `EXECUTION_FAIL` |

The observation artifact for this receipt is retained outside Git at:

`work/p11-formal-acceptance-9389d59d/workspace/ingest/us/discovery/684038711efc8eef02b3540cc2aca7f5edda55987727da08cd4c15932b700dd0.json`

It records the expected accession, primary document, stable CIK identity, observation SHA and source-document hash.

## Independently confirmed root cause

`src/financial_filing_data_foundation/us_sec/acquisition.py::_select_archive_members()` correctly selects the primary document, recognized EX-101 members and `FilingSummary.xml`, but then treats every canonical filing-local value found in primary HTML `href`, `xlink:href` or `src` attributes as an acquisition authorization. Apple’s ordinary `<img src="aapl-20250927_g1.jpg">` therefore enters the selected member list. The member is fetched using the fallback MIME policy, which does not permit `image/jpeg`, and the SEC response is correctly rejected as `P11_CONTENT_TYPE_INVALID`.

The repair boundary is member selection, not a global MIME allowlist. The corrected implementation must continue to validate MIME, bytes, size, path and host for members that are legitimately selected while refusing unrelated browser/static subresources.

## Lifecycle consequence

- Candidate `9389d59d68c84762b55b29bedb973db4ea45256a` remains historical: `REVIEW_PASS` followed by `EXECUTION_FAIL`.
- Formal Acceptance = `NOT PASSED`.
- Main merge = `NOT AUTHORIZED`.
- P11 DONE = `NO`.
- New blocking issue: `P11-ISSUE-133` — primary HTML static-asset references are over-selected into the SEC package, causing valid live filings to fail acquisition on unrelated MIME types.

The next step is a new repair candidate cycle. No production or test file was modified during formal execution.
