# P11-ISSUE-134 Repair Evidence

## 1. Scope and lifecycle position

- Repository: `FinancialFilingDataFoundation`
- Branch: `task/p11-sec-rebuild-development`
- Repair issue: `P11-ISSUE-134 — Reference-based XBRL support acquisition incorrectly depends on semantic SEC index type metadata`
- Corrected design baseline: `09e3174b7e19a60cc5955862670fac8931af67db`
- Cycle starting HEAD: `3945eca3bf5bd363cfcb6ae4c46dc6c0f4625c79`
- Previous CHANGES_REQUIRED candidate: `606e744c99c7d9b46d94415058c6ccc780165a0b`
- Previous evidence commit: `3945eca3bf5bd363cfcb6ae4c46dc6c0f4625c79`
- New production candidate: `c7bcfa6bd3b01a769cc5e3063378c68c7a4dd67b`
- New candidate commit message: `fix: restore deterministic XBRL semantic reference acquisition`

The previous candidate and previous evidence were not modified or amended. A plan-only documentation commit (`0daf731bef4cac48aaacd912d1d8427a1c7c85fe`) preceded the new production candidate in this worktree.

## 2. Root cause and repair

The previous selector collected references with a broad `href`/`xlink:href`/`src` expression and then required the referenced SEC index item to have semantic XBRL metadata. Therefore a valid filing-local XBRL target referenced by an explicit XBRL construct could be dropped when `index.json` reported a generic, blank, or otherwise non-semantic `type` value. The same broad collection also made ordinary browser references part of the candidate path before later filtering.

The candidate repairs the acquisition boundary only:

1. The primary HTML is parsed with a tag-aware parser that records only `link:schemaRef` and `link:linkbaseRef`, using `xlink:href` or `href`.
2. Accepted XBRL XML members are parsed with `ElementTree`; only the XBRL linkbase namespace and the same two local constructs are recognized.
3. A recognized SEC `EX-101.*` index item remains an independent selection path. A validated semantic target is selected independently whenever its canonical name exists in the same accession index, regardless of the SEC index `type` value.
4. Ordinary anchors, generic HTML links, `src` assets, extension-only members, external URLs, traversal, encoded paths, absolute paths, and other unsafe references remain unselected.
5. Newly selected members are fetched through a deterministic set-based fixpoint loop. The loop scans only the primary and accepted XBRL-role members, fetches each canonical target at most once, and terminates on duplicates/cycles.
6. Existing exact accession URL, MIME, size, source-byte, package-provenance, package-SHA, and raw-store immutability checks remain in force. `OTHER` XML is not treated as XBRL truth.

No parser, package schema, validation schema, registry, or version-contract change was made.

## 3. T134 deterministic evidence

All T134 policy tests passed in the new deterministic suite (`7 passed`).

| Test | Result | Evidence |
|---|---|---|
| T134-01 | PASS | `link:schemaRef` selected an `.xsd` whose index type was `text.gif`; it was fetched once and classified `XBRL_SCHEMA`; static siblings were not fetched or packaged. |
| T134-02 | PASS | `link:linkbaseRef` selected a presentation/linkbase target with generic `XML` metadata exactly once; CSS remained absent and unfetched. |
| T134-03 | PASS | An ordinary HTML `<a href="unrelated.xml">` did not authorize selection or fetch. |
| T134-04 | PASS | JPEG, PNG, GIF, CSS, JavaScript, WOFF2, and decorative SVG browser assets remained zero-fetch and absent from the package; the existing ISSUE-133 policy test remains green. |
| T134-05 | PASS | A non-inline primary reached a generic-index-type XBRL instance through an explicit semantic reference; the member was classified `XBRL_INSTANCE`, parsing returned `XBRL_INSTANCE_PRIMARY`, exactly one positive logical fact (`raw_value = "42"`), no duplicate fact universe, and validation reported `blocking_issue_count = 0`. |
| T134-06 | PASS | Recognized `EX-101.SCH` metadata selected its schema without a semantic reference. |
| T134-07 | PASS | Duplicate references and the A→B→A dependency cycle terminated through the bounded set-based queue; A and B were each fetched once and included once. |
| T134-08 | PASS | The semantic member source URL exactly matched `archive_member_url(CIK, accession, relative_name)`; package reload reproduced the manifest and package SHA. Unsafe/external semantic references were rejected by the existing archive path policy. |

The existing ISSUE-133 test was repinned from an ordinary browser hyperlink to an explicit `link:schemaRef`, because ISSUE-134 requires ordinary browser references to remain non-authorizing. Its static-asset zero-fetch assertions remain unchanged.

## 4. Developer verification

The required commands were run with the repository virtual environment and isolated basetemp directories:

| Command scope | Result |
|---|---:|
| `tests/unit/us_sec/test_semantic_reference_acquisition.py` | `7 passed in 2.96s` |
| `tests/unit/us_sec/test_provider_cli.py` | `11 passed in 2.58s` |
| `tests/unit/us_sec/test_http_discovery.py` | `26 passed in 0.32s` |
| `tests/unit/us_sec` | `140 passed in 14.32s` |
| `tests/unit` | `670 passed in 87.35s` |
| P0–P10 focused suites (`acquisition identity validation registry mcp research review`) | `371 passed in 67.43s` |
| `python -m compileall -q src tests` | PASS, exit code 0 |
| `git diff --check` before candidate freeze | PASS, exit code 0 |
| candidate staged diff check | PASS, exit code 0 |

The full `tests/unit/us_sec` result includes the existing US SEC provider and ISSUE-133 regression coverage.

## 5. Apple live developer smoke

The smoke used the isolated root:

`D:\Codex\FinancialFilingDataFoundation\work\p11-issue134-live-smoke-20261112-v1`

`FFDF_SEC_CONTACT_EMAIL` was configured (value not recorded). `FFDF_P11_US_DEV` was absent before and after the run. The production-shaped CLI returned `DOWNLOADED`, selected accession `0000320193-25-000079`, and produced:

- package SHA-256: `ddd759bd959bb20c75e9d2b77a33b8ad5e34597e652c742d863264d6848cae77`
- discovery observation SHA-256: `1b405da2763b780ddaf4d9a715352d892a553579e54948f560f873b60667afd1`
- JPEG member count: `0`

Complete live package member inventory (`relative_name | role | content_type`):

```text
aapl-20250927_cal.xml | XBRL_CALCULATION | text/xml
aapl-20250927_def.xml | XBRL_DEFINITION | text/xml
aapl-20250927_lab.xml | XBRL_LABEL | text/xml
aapl-20250927_pre.xml | XBRL_PRESENTATION | text/xml
aapl-20250927.htm | PRIMARY_DOCUMENT | text/html
aapl-20250927.xsd | XBRL_SCHEMA | text/xml
FilingSummary.xml | FILING_SUMMARY | text/xml
```

## 6. Contract and governance checks

The following version and identity contracts were unchanged:

- `REGISTRY_SCHEMA_VERSION = 1`
- `SEC_REGISTRY_SCHEMA_VERSION = 4`
- `SEC_DISCOVERY_SCHEMA = p11-sec-discovery-v1`
- `VIRTUAL_HTML_NORMALIZER_VERSION = VIRTUAL_HTML_V5`
- `SEC_ARTIFACT_SCHEMA = p11-sec-artifacts-v2`
- `SEC_VALIDATION_SCHEMA = p11-sec-validation-v2`
- `PACKAGE_MANIFEST_SCHEMA = p11-sec-package-v1`
- package SHA remains the existing canonical member-record SHA formula

The new candidate contains only the acquisition implementation and US SEC tests. After candidate freeze, no source or test file was changed. The next commit is documentation-only and adds this evidence file.

- Formal Test Plan: NOT CREATED
- Formal Acceptance: NOT RUN
- Main merge: NOT RUN
- P11 DONE: NO

## 7. Handoff

P11-ISSUE-134 status: `FIXED` for exact-candidate review.

Next action: ChatGPT exact-candidate review of `c7bcfa6bd3b01a769cc5e3063378c68c7a4dd67b`.
