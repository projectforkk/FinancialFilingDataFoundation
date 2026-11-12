# P11 Live FT-10 Acquisition Repair Evidence

Date: 2026-11-12

## 1. Scope and lifecycle boundary

This record documents a new production-candidate repair cycle for the failed FT-10 acquisition. It is not a Formal Acceptance record and does not authorize reuse of Formal Test Plan 183.

| Item | Value |
| --- | --- |
| Branch | `task/p11-sec-rebuild-development` |
| Starting HEAD | `aa54e38591d5ea003fcae5a1c6a3109f10f0bf94` |
| Corrected design baseline | `09e3174b7e19a60cc5955862670fac8931af67db` |
| Failed formal candidate | `9389d59d68c84762b55b29bedb973db4ea45256a` |
| Failed formal evidence | `development/185-p11-formal-test-evidence-3.md` |
| Failed formal evidence commit | `58927c656a47c46f0f574dc9d11b58be707fe33c` |
| New P11 production candidate | `606e744c99c7d9b46d94415058c6ccc780165a0b` |
| New candidate parent | `58927c656a47c46f0f574dc9d11b58be707fe33c` |
| Formal Test Plan for new candidate | NOT CREATED |
| Formal Acceptance for new candidate | NOT RUN |
| Main merge | NOT RUN |
| P11 DONE | NO |

The historical candidate `9389d59d68c84762b55b29bedb973db4ea45256a` was not amended, rebased, or repaired in place.

## 2. Failed FT-10 and blocking issue

The failed formal execution was bound to:

- Formal Test Plan: `development/183-p11-formal-test-plan-3.md`
- Plan commit: `4e4961dd4b37b2bd50c2d162ea99fa155fbfff27`
- Execution prompt: `development/184-p11-formal-test-execution-prompt-3.md`
- Prompt/current-head commit: `aa54e38591d5ea003fcae5a1c6a3109f10f0bf94`
- Formal result: FT-00–FT-09 PASS; FT-10 FAIL; FT-11–FT-15 BLOCKED
- Observed accession: `0000320193-25-000079`
- Failed observation SHA: `684038711efc8eef02b3540cc2aca7f5edda55987727da08cd4c15932b700dd0`
- Failing member: `aapl-20250927_g1.jpg`
- SEC response content type: `image/jpeg`
- Failure reason: `P11_CONTENT_TYPE_INVALID`
- `FFDF_P11_US_DEV`: ABSENT

New blocking issue:

```text
P11-ISSUE-133 — Primary HTML static-asset references are over-selected into
the SEC package, causing valid live filings to fail acquisition on unrelated
MIME types.
```

The independent root cause is in `src/financial_filing_data_foundation/us_sec/acquisition.py`: after selecting the primary, recognized EX-101 members, and `FilingSummary.xml`, the previous implementation added every filing-local `href`, `xlink:href`, or `src` target found in the primary HTML when that name appeared in `index.json`. A browser image therefore became a package acquisition request even though it had no semantic filing-data inclusion reason. The fail-closed MIME policy then correctly rejected SEC's `image/jpeg` response because JPEG was not an allowed member type.

## 3. Repair and design alignment

Design 26 §7.3 remains controlling: acquire the exact primary and filing-local XBRL support members identified by recognized EX-101 metadata or exact accepted semantic references, without downloading unrelated exhibits by default.

The frozen candidate makes the minimum selection repair:

1. It keeps recognized `EX-101.INS`, `EX-101.SCH`, `EX-101.PRE`, `EX-101.CAL`, `EX-101.LAB`, `EX-101.DEF`, and `EX-101.REF` selection unchanged.
2. It keeps the current `FilingSummary.xml` selection unchanged.
3. It adds an explicit semantic reference-type gate for primary HTML references. A referenced index item is selected only when its reviewed metadata is an explicit XBRL/support type (`XBRL`, `XBRL_INSTANCE`, `XBRL_SCHEMA`, `XBRL_PRESENTATION`, `XBRL_CALCULATION`, `XBRL_LABEL`, `XBRL_DEFINITION`, `XBRL_REFERENCE`, `XBRL_LINKBASE`, `XBRL_SUPPORT`) or a recognized EX-101 type.
4. It does not select ordinary XML merely because its extension is `.xml`, and it does not select browser assets merely because they are present in `index.json` and referenced by HTML.
5. It does not add `image/jpeg` or any other static MIME type to the global content-type policy. Path, host, MIME, byte-size, and raw-store validation remain fail-closed.

No parser, artifact, Registry, package, or schema version was changed. Package SHA and source/provenance binding remain governed by the existing `p11-sec-package-v1` implementation.

## 4. Regression evidence

The new deterministic test file is `tests/unit/us_sec/test_acquisition_reference_policy.py`.

### Apple/static-asset reproduction

The fixture primary HTML references the exact Apple-style JPEG name plus CSS, JavaScript, PNG, GIF, and WOFF2 assets. All six assets are present in the fake SEC index. The transport raises if any static asset is requested. The same fixture includes `EX-101.SCH`, `FilingSummary.xml`, and an explicitly typed `XBRL_INSTANCE` reference.

Result: PASS.

- acquisition succeeded;
- primary, FilingSummary, EX-101 schema, and semantic XBRL support were fetched;
- each static asset fetch count was `0`;
- no static asset was present in package members;
- the semantic XBRL support member was fetched once and retained role `XBRL_INSTANCE`.

The focused regression result after the candidate's final test content was `3 passed in 1.08s`.

### Ordinary XML and security boundaries

The regression suite also proves that a referenced `type=XML` member is not selected without semantic metadata. Existing path-policy coverage remains active for `../` traversal, absolute paths, Windows drive paths, backslash escapes, and encoded traversal; the new selection test covers external-host, `javascript:`, and `data:` references. These references are ignored and do not become archive fetches.

The existing incremental acquisition regression `test_sec_acquirer_downloads_primary_and_xbrl_members_incrementally` remains green and continues to prove primary and recognized XBRL acquisition, exclusion of unrelated XML/PDF, and local package reuse.

## 5. Developer verification

All required developer commands were run from the frozen candidate worktree with the project virtual environment:

| Check | Result |
| --- | --- |
| `tests/unit/us_sec/test_provider_cli.py` | `11 passed in 2.60s` |
| `tests/unit/us_sec/test_http_discovery.py` | `26 passed in 0.36s` |
| `tests/unit/us_sec` | `133 passed in 11.25s` |
| `tests/unit` | `663 passed in 81.34s (0:01:21)` |
| P0–P10 focused suites | `371 passed in 63.76s (0:01:03)` |
| `python -m compileall -q src tests` | exit `0` |
| `git diff --check` | exit `0` |

The six static asset and semantic-reference assertions are included in the US SEC and full-unit counts above. No test failure, warning, or skipped result was used as a pass.

## 6. Live Apple developer smoke

`FFDF_SEC_CONTACT_EMAIL` was already configured. The smoke ran in the disposable root:

```text
D:\Codex\FinancialFilingDataFoundation\work\p11-issue133-live-smoke-20261112
```

`FFDF_P11_US_DEV` was absent before and after the run. The production-shaped CLI command completed with `DOWNLOADED` for Apple FY2025:

- accession: `0000320193-25-000079`;
- discovery state: `UNAMBIGUOUS`;
- discovery observation SHA: `e6e2cc7ce5a6a996e4ddc09e96f9bca1bbfbc8c5fde0321272c3702214083500`;
- package SHA: `9487613e0f9375226b9efb116f9ec79e3081c171fced9799c533284fb7c9fbea`;
- package schema: `p11-sec-package-v1`.

The live manifest contains exactly two members:

```text
FilingSummary.xml       FILING_SUMMARY    text/xml
aapl-20250927.htm       PRIMARY_DOCUMENT  text/html
```

`aapl-20250927_g1.jpg` is absent, and the manifest contains zero static-asset members. The primary body is Inline XBRL (local inspection found `969` `ix:nonfraction` markers and `162` `ix:nonNumeric` markers), so this filing's semantic XBRL facts remain in the primary document; no separate XBRL instance attachment was required for this package. `FilingSummary.xml` remains present. This live smoke is developer evidence only and does not replace Formal Acceptance.

## 7. Regression and provenance status

| Contract | Status | Evidence |
| --- | --- | --- |
| Apple JPEG regression | PASS | deterministic transport asserted zero JPEG fetches; live manifest excludes JPEG |
| CSS/JS/static-asset non-fetch | PASS | deterministic fixture asserted zero fetches and no package members |
| Reference-discovered XBRL support | PASS | typed XBRL reference fetched once and assigned `XBRL_INSTANCE`; EX-101 selection remains green |
| Package provenance | PASS | package SHA/provenance code unchanged; live package manifest is `p11-sec-package-v1` with SHA `9487613e...` |
| P11-ISSUE-123–131 regression | PASS | P0–P10 focused suites: 371 passed |

The repair does not make static assets XBRL instances, schemas, context sources, unit sources, or fact sources. Original-document immutability and Registry/package provenance semantics were not changed.

## 8. Candidate and next lifecycle step

The new production candidate is commit `606e744c99c7d9b46d94415058c6ccc780165a0b`, parent `58927c656a47c46f0f574dc9d11b58be707fe33c`. Its source/test diff contains only:

- `src/financial_filing_data_foundation/us_sec/acquisition.py`;
- `tests/unit/us_sec/test_acquisition_reference_policy.py`.

This evidence file is intentionally created after candidate freeze. The candidate-to-evidence commit must therefore be documentation-only. No new Formal Test Plan was created, Formal Acceptance was not run, and no main merge was performed.

Next action:

```text
CHATGPT EXACT-CANDIDATE REVIEW OF 606e744c99c7d9b46d94415058c6ccc780165a0b
```

