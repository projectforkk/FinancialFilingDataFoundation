# P11 US SEC Provider Formal Test Evidence 5

Status: FORMAL_TEST_EXECUTION_COMPLETE

Formal execution result: EXECUTION_PASS

Agent role: Acceptance/Test Agent

Execution date: 2026-11-16 (Asia/Tokyo)

This document records Formal Test Plan 5 execution. It is not an Acceptance PASS declaration and it is not a P11 DONE declaration.

## 1. Exact identity and authority

| Item | Exact value |
|---|---|
| Repository | projectforkk/FinancialFilingDataFoundation |
| Branch | task/p11-sec-rebuild-development |
| Authoritative remote | origin/reconcile/p11-140-143-local-chain |
| Frozen production candidate | f1cc76889718e06fdbdc46926e2b207b740a96e3 |
| Development evidence | f859dc342060d8c534491639d85e7256c4e11a57 |
| Corrected Design Baseline 39 | fad6ee7512ec1f2f3da0c9a24c646959b2f45541 |
| Fresh exact-candidate Review 8 | 56d884f5adfc4f5044f3970c3e43180b658c74a8 |
| Formal Test Plan 5 | 4e20ca77889b9e2f35b470c99ee90c45c7853994 |
| Formal Test Execution Authorization 5 | b46cbd0aaaacd937800d611e7a565f70362e34b8 |
| Authorization-time HEAD | b46cbd0aaaacd937800d611e7a565f70362e34b8 |
| Authorization-time remote tip | b46cbd0aaaacd937800d611e7a565f70362e34b8 |

The execution began with git fetch origin and a fast-forward-only reconciliation from the development evidence to the authorized execution commit. No rebase, reset, clean, force push, main merge, or new production candidate was used.

## 2. Execution safety and environment

- Worktree: D:\Codex\FinancialFilingDataFoundation\worktrees\active\p11-sec-rebuild-development
- Python: 3.14.9; project interpreter: D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe
- pytest: 9.2.0
- FFDF_P11_US_DEV: absent throughout the formal runs.
- FFDF_SEC_CONTACT_EMAIL: configured; its value is intentionally not recorded.
- Acceptance-only live roots and raw logs were outside Git under D:\ffdf-p11-ft5.
- No src/, tests/, production/runtime semantic, or frozen-candidate file was modified.

The FT-00 and FT-18 pre-evidence drift checks reported a clean worktree, git diff --check exit 0, and zero forbidden-path changes. Post-candidate tracked changes before this evidence file were governance/documentation only: PROJECT_STATUS.md, the design-management index, and development documents 206 through 209.

## 3. Gate result summary

| Gate | Result | Primary evidence |
|---|---|---|
| FT-00 | PASS | candidate/branch/remote/drift checks |
| FT-01 | PASS | 793 unit; P0-P10 371; US SEC 263; MCP 93; repair 88; ISSUE-147 10 |
| FT-02 | PASS | 15 descriptor cases; real submissions plus history source set |
| FT-03 | PASS | actual legacy payload without snapshot_id; four tamper cases |
| FT-04 | PASS | newest-only cache; no stale fallback; local status no network |
| FT-05 | PASS | explicit CIK zero ticker-map fetch; online ticker freshness |
| FT-06 | PASS | history inventory, 33 passed |
| FT-07 | PASS | corrected replay/immutable source tests, 97 passed |
| FT-08 | PASS | validation-v3/ISSUE-146/P8 tests, 37 passed |
| FT-09 | PASS | acquisition/provenance/security tests, 55 passed |
| FT-10 | PASS | fresh live Apple FY2025 ticker acquire |
| FT-10A | PASS | Apple package 1196a354... vs d94d8c46... member audit |
| FT-11 | PASS | immediate Apple ticker ingest; fresh discovery, local parse |
| FT-12 | PASS | online repeat; fresh discovery, zero archive redownload/parser rerun |
| FT-13 | PASS | live-artifact REVALIDATE_LOCAL; v2 compatibility and fail-closed v3 |
| FT-14 | PASS | live Apple FY2025 Q3 plus P8/MCP no-network |
| FT-15 | PASS | live Toyota FY2025 20-F and 6-K quarterly guard |
| FT-16 | PASS | explicit-CIK Kellanova amendment conflict |
| FT-17 | PASS | P0-P10 preservation plus CN/HK/MCP representative suite |
| FT-18 | PASS | final pre-evidence drift and integrity check |

No required assertion failed, no production/test repair was required, and no external/contact unavailability occurred.

## 4. FT-00 — candidate freeze and documentation-only history

Commands executed included:

~~~text
git fetch origin
git status --short
git rev-parse --abbrev-ref HEAD
git rev-parse HEAD
git rev-parse origin/reconcile/p11-140-143-local-chain
git merge-base --is-ancestor f1cc76889718e06fdbdc46926e2b207b740a96e3 HEAD
git diff --check
git diff --name-status f1cc76889718e06fdbdc46926e2b207b740a96e3..HEAD
~~~

Results:

- branch was task/p11-sec-rebuild-development;
- HEAD and the authoritative remote were both b46cbd0aaaacd937800d611e7a565f70362e34b8;
- the frozen candidate was an ancestor;
- worktree was clean;
- diff check exited 0;
- the post-candidate tracked set was documentation/governance only;
- forbidden-path count was 0;
- FFDF_P11_US_DEV=ABSENT.

The constants observed at the candidate boundary were:

~~~text
REGISTRY_SCHEMA_VERSION=1
SEC_REGISTRY_SCHEMA_VERSION=4
SEC_DISCOVERY_SCHEMA=p11-sec-discovery-v1
VIRTUAL_HTML_NORMALIZER_VERSION=VIRTUAL_HTML_V6
SEC_ARTIFACT_SCHEMA=p11-sec-artifacts-v2
SEC_VALIDATION_SCHEMA=p11-sec-validation-v3
~~~

## 5. FT-01 — full deterministic regression

The formal regression commands were run with the project interpreter. Raw outputs were captured under D:\ffdf-p11-ft5\evidence:

| Scope/log | Result |
|---|---:|
| FT-01-issue147.txt | 10 passed, exit 0 |
| FT-01-repair.txt | 88 passed, exit 0 |
| FT-01-us.txt, tests/unit/us_sec | 263 passed, exit 0 |
| FT-01-mcp.txt | 93 passed, exit 0 |
| FT-01-p0p10.txt | 371 passed, exit 0 |
| FT-01-unit.txt, tests/unit | 793 passed, exit 0 |
| FT-01-compileall.txt | exit 0 |
| FT-01-diff-check.txt | exit 0 |

There were no failed or skipped tests in the recorded formal outputs.

The ISSUE-147 regression set independently covered source observation identity conflict, same-observation source drift, legacy/new observation separation, source/derivative tamper fail-closed behavior, newest-only resolution, explicit-CIK zero ticker-map behavior, and the formal FT-10 boundary.

## 6. FT-02 — observation identity and true history source set

Acceptance harness command:

~~~text
python D:\ffdf-p11-ft5\evidence\FT-02-history-harness.py
~~~

Recorded result:

~~~text
FT-02 PASS
descriptor_cases=15
malformed_history_fetch_count=0
online_calls=2
reconstructed_source_documents=2
EXIT_CODE=0
~~~

The online discovery used the actual current submissions URL and actual issuer history URL. The reconstructed observation source set contained both source documents and passed observation verification. The ISSUE-147 test test_t147_03_same_observation_identity_conflict_is_source_drift returned the controlled source-drift result for an identity conflict; it did not silently overwrite an existing observation.

## 7. FT-03 — historical legacy snapshot without snapshot_id

Acceptance harness command:

~~~text
python D:\ffdf-p11-ft5\evidence\FT-03-legacy-harness.py
~~~

Recorded result:

~~~text
FT-03 PASS
historical_snapshot_id_present=NO
legacy_local_resolution=0000320193
legacy_hash_unchanged=YES
new_observations=1
tamper_cases=4
EXIT_CODE=0
~~~

This was an actual historical-format payload with no snapshot_id, not a new payload with the field removed only for display. Legacy verification and local resolution succeeded, the legacy source hash remained unchanged, and a new online observation was stored separately. Four tamper cases (source bytes, mapping, filename, and official URL) failed closed.

## 8. FT-04 / FT-05 — cache and identity boundaries

FT-04 command:

~~~text
python D:\ffdf-p11-ft5\evidence\FT-04-cache-harness.py
~~~

Result:

~~~text
FT-04 PASS
newest_cik=0000000002
stale_fallback=NO
local_status_network_calls=0
within_snapshot_ambiguity=P11_TICKER_CIK_AMBIGUOUS
EXIT_CODE=0
~~~

FT-05 command:

~~~text
python D:\ffdf-p11-ft5\evidence\FT-05-ticker-harness.py
~~~

Result:

~~~text
FT-05 PASS
explicit_cik_ticker_fetches=0
ticker_online_fetches_per_invocation=1
online_failure_cached_substitution=NO
local_status_network_calls=0
EXIT_CODE=0
~~~

These gates proved newest-only resolution, no stale cached substitution after an online failure, explicit-CIK ticker-map suppression, and network-free local status.

## 9. FT-06 through FT-09 — deterministic repair, validation, provenance, and security gates

Commands and outputs:

~~~text
python -m pytest -q tests/unit/us_sec/test_full_design_repair_135_139.py
FT-06: 33 passed, exit 0

python -m pytest -q tests/unit/us_sec/test_corrected_repair.py tests/unit/us_sec/test_repair_140_143.py tests/unit/us_sec/test_issue131.py
FT-07: 97 passed, exit 0

python -m pytest -q tests/unit/us_sec/test_issue146.py tests/unit/us_sec/test_validation_p8.py tests/unit/us_sec/test_package_registry.py
FT-08: 37 passed, exit 0

python -m pytest -q tests/unit/us_sec/test_acquisition_reference_policy.py tests/unit/us_sec/test_semantic_reference_acquisition.py tests/unit/us_sec/test_http_discovery.py tests/unit/us_sec/test_provider_cli.py tests/unit/us_sec/test_identity_policy.py
FT-09: 55 passed, exit 0
~~~

The raw outputs are ft06-history.txt, ft07-replay.txt, ft08-validation.txt, and ft09-security.txt. All four gates passed with no failed or skipped tests.

## 10. FT-10 — fresh live Apple FY2025 ticker acquire

Command:

~~~text
acquire --market US --ticker AAPL --year 2025 --period FY
~~~

The fresh root was D:\ffdf-p11-ft5\live-a. Result:

| Field | Value |
|---|---|
| CIK | 0000320193 |
| accession | 0000320193-25-000079 |
| form | 10-K |
| report period | 2025-09-27 |
| primary document | aapl-20250927.htm |
| package SHA | d94d8c46e34ce25af8d42279dbb4a370b1e617d7daf421743f29468b77d19568 |
| planner action | DISCOVER_AND_ACQUIRE |
| status | DOWNLOADED |

Request counts were: ticker map 1, current submissions 1, history 0, archive index 1, archive members 7, static/other 0.

Ticker snapshot and discovery identity:

| Observation | ID/SHA | Retrieved at | Source SHA |
|---|---|---|---|
| ticker snapshot | 5c4f8a03d4978cf9499c77f32e1534bad5208b75f876f969840a08caf0a8e752 | 2026-11-16T06:45:01.889895+00:00 | 29e8eee5a85a68e837628b0e9623870af68db41e5427a154d17fe3b1af0a1b9a |
| discovery observation | 636fb352e4d75c7942f78394d31ff976ba94edaec5b150c127b13c585e557e25 | 2026-11-16T06:45:02.535161+00:00 | submissions d7c4a3c888fe60da97ceef8f9b80da4c205e82440c1bc3ba9dcc7316a482a6b1 |

The discovery state was UNAMBIGUOUS; candidate fingerprint was 5b6e2ce3f72872f6d811093b1eb91641f3b6a9a4a9c1c2b566cd4e79b91b5742 and the selected accession was the expected accession above.

Complete selected package member records:

| Relative name | Role | Bytes | Member SHA256 |
|---|---|---:|---|
| FilingSummary.xml | FILING_SUMMARY | 42775 | f5e632bd6de8965a5251fd590f053553c017396f5ec75b0ddc9e475832a7c0a2 |
| aapl-20250927.htm | PRIMARY_DOCUMENT | 1520327 | 7f44c98b2b8d4f0836aac3f151c415149df4a560c4208860a7d2ccfedf9134be |
| aapl-20250927.xsd | XBRL_SCHEMA | 56313 | e697d106fae1543535c634bede6337b8f1ecd987e7655eb91c62913900ab6335 |
| aapl-20250927_cal.xml | XBRL_CALCULATION | 153156 | 314091ba88cd58f392874866c19010ed9facdd643f34f0afbcf37137192c5f05 |
| aapl-20250927_def.xml | XBRL_DEFINITION | 224664 | 6eb3e955297ea510ceaff7331f57dc948cb439e83a634a3882f3806d6fb7434a |
| aapl-20250927_lab.xml | XBRL_LABEL | 763631 | 9ec8874c0af055946d80061bd5558599c4eb2b56b21e48a4670751097d166118 |
| aapl-20250927_pre.xml | XBRL_PRESENTATION | 496062 | 43ce57fec893a2c2974a043198a3acc105238aaf19cb4a93ba8812d412d0ab7d |

## 11. FT-10A — mandatory Apple package identity audit

The historical Formal Test 4 package was:

~~~text
1196a354461ac65afa4ce7f1c67b2d65b04c1e496f521f34a139c6d6e5872d3d
~~~

The current Formal Test 5 package was:

~~~text
d94d8c46e34ce25af8d42279dbb4a370b1e617d7daf421743f29468b77d19568
~~~

Both available historical manifests for the old SHA were independently identical. The member-by-member audit was:

| Relative name | Role | Old bytes/SHA | Current bytes/SHA | Result |
|---|---|---|---|---|
| FilingSummary.xml | FILING_SUMMARY | 42775 / f5e632bd6de8965a5251fd590f053553c017396f5ec75b0ddc9e475832a7c0a2 | 42775 / f5e632bd6de8965a5251fd590f053553c017396f5ec75b0ddc9e475832a7c0a2 | EQUAL |
| aapl-20250927.htm | PRIMARY_DOCUMENT | 1520312 / 2e9a48b29574153c8b11f8d070f0198bbad8d53444570e6cefdaf68578f15066 | 1520327 / 7f44c98b2b8d4f0836aac3f151c415149df4a560c4208860a7d2ccfedf9134be | DIFFERS |
| aapl-20250927.xsd | XBRL_SCHEMA | 56313 / e697d106fae1543535c634bede6337b8f1ecd987e7655eb91c62913900ab6335 | 56313 / e697d106fae1543535c634bede6337b8f1ecd987e7655eb91c62913900ab6335 | EQUAL |
| aapl-20250927_cal.xml | XBRL_CALCULATION | 153156 / 314091ba88cd58f392874866c19010ed9facdd643f34f0afbcf37137192c5f05 | 153156 / 314091ba88cd58f392874866c19010ed9facdd643f34f0afbcf37137192c5f05 | EQUAL |
| aapl-20250927_def.xml | XBRL_DEFINITION | 224664 / 6eb3e955297ea510ceaff7331f57dc948cb439e83a634a3882f3806d6fb7434a | 224664 / 6eb3e955297ea510ceaff7331f57dc948cb439e83a634a3882f3806d6fb7434a | EQUAL |
| aapl-20250927_lab.xml | XBRL_LABEL | 763631 / 9ec8874c0af055946d80061bd5558599c4eb2b56b21e48a4670751097d166118 | 763631 / 9ec8874c0af055946d80061bd5558599c4eb2b56b21e48a4670751097d166118 | EQUAL |
| aapl-20250927_pre.xml | XBRL_PRESENTATION | 496062 / 43ce57fec893a2c2974a043198a3acc105238aaf19cb4a93ba8812d412d0ab7d | 496062 / 43ce57fec893a2c2974a043198a3acc105238aaf19cb4a93ba8812d412d0ab7d | EQUAL |

The official URL was identical in both manifests:

~~~text
https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm
~~~

The byte comparison found 81 differing positions and a +15 byte length change, limited to the embedded script path at the end of the same official primary document. The old tail path was /88tBY8S3XMefkGGxldET/LibicttbL2JzSXaz/MClz/Zw0JQ/FMmAWE; the current tail path was /rHDPm5/Qtwj/aVO/qje/CZYtj1h_Cz4/YOOVJwmbcpbzGz/H0YtIFFvSg/CkRqf/XsaECs.

Therefore the SHA difference is explained by a verifiable official SEC byte change. There was no member-set, role, or non-primary-member drift, and the difference was not ignored.

## 12. FT-11 — immediate Apple ticker ingest

Command:

~~~text
ingest --market US --ticker AAPL --year 2025 --period FY
~~~

The current ticker map and current submissions were fetched again: ticker map 1, submissions 1, archive index/member 0, other 0. The first ticker snapshot file remained byte-identical; snapshot count changed from 1 to 2.

The new snapshot was:

~~~text
snapshot_id=ff151476622314af7aee0a3c0e7ce60fc46e80df8a0e0c41014b36c0267f6670
retrieved_at=2026-11-16T06:49:02.691921+00:00
source_sha256=29e8eee5a85a68e837628b0e9623870af68db41e5427a154d17fe3b1af0a1b9a
~~~

The new discovery observation was 8438db2093ea2fac0be83aa434bccc4a3d5e2cd2f1e6faf6ada4f5d0ca9a13ec, retrieved at 2026-11-16T06:49:03.180254+00:00, with the same selected accession and source submissions SHA as FT-10. The ingest result was PARSE_LOCAL, validation-v3 PASS / COMPATIBLE / blocking 0 / review 0, P8 ADDED, and research_ready=true.

## 13. FT-12 — online repeat and local status

The same online ticker ingest was run again. Current ticker-map and current submissions discovery each occurred once; archive index/member calls were both 0. The third ticker snapshot was:

~~~text
snapshot_id=10962c814c831ac2c61ab63e9d514aa69743484262eefd108c4ceffc1c95ad7a
retrieved_at=2026-11-16T06:51:06.881230+00:00
source_sha256=29e8eee5a85a68e837628b0e9623870af68db41e5427a154d17fe3b1af0a1b9a
~~~

The repeat discovery observation was 927d48349181859b33f08bc334b09a4fda7af1c149e83370936ed019d30da2c0, retrieved at 2026-11-16T06:51:07.226799+00:00, state UNAMBIGUOUS, with the same selected accession, source submissions SHA, and candidate fingerprint as FT-10.

The repeat result was REUSE_DATA, P8 ALREADY_REGISTERED, validation-v3 PASS / COMPATIBLE / blocking 0 / review 0, and research_ready=true. Raw and parsed bytes were unchanged, parser reruns were 0, and the deterministic parse run ID remained e276b8bc023b496ed6a7aa6961db9394b252f576a520e9951f1fc64a32f2108e. Validation was refreshed while issues.jsonl remained unchanged and empty.

The local status call had network calls 0 and parser reruns 0. All previously created ticker snapshot files remained unchanged.

## 14. FT-13 — live-artifact REVALIDATE_LOCAL

The acceptance-only copy was D:\ffdf-p11-ft5\live-a-revalidate. It was prepared with legacy validation-v2 flat files and v3 temporarily absent. The online repeat used current ticker-map/submissions discovery (one each), no archive calls, and produced:

- planner action REVALIDATE_LOCAL;
- exit 0;
- parser reruns 0;
- raw and parsed bytes unchanged;
- legacy v2 bytes unchanged;
- new validation-v3 present and PASS / COMPATIBLE / blocking 0;
- P8 ALREADY_REGISTERED, research_ready=true.

The subsequent corrupt-v3 retry wrote not-json to the disposable v3 validation file. It failed closed with SecError, reason P11_PACKAGE_INVALID, message SEC validation artifact is invalid; parser reruns remained 0, the corrupt file remained unchanged, legacy v2 bytes remained unchanged, and there was no v2 fallback.

An initial disposable-copy harness attempt exposed an absolute artifact-path issue in the copied Registry fixture. That was diagnosed and corrected only in the acceptance-only disposable harness; no production or test file was modified. The final FT-13 rerun is the result recorded above.

## 15. FT-14 — live Apple FY2025 Q3 and P8/MCP no-network

Commands:

~~~text
acquire --market US --ticker AAPL --year 2025 --period Q3
ingest --market US --ticker AAPL --year 2025 --period Q3
~~~

Result:

| Field | Value |
|---|---|
| accession | 0000320193-25-000073 |
| form | 10-Q |
| report period | FY2025 Q3, 2025-06-28 primary document |
| observation SHA | d1758dbe90fdc15ff61c3167ec6f0a4bfea304d8e0af6d73f1f23f1ddc0ba371 |
| retrieved at | 2026-11-16T06:56:28.120503+00:00 |
| package SHA | 75562f95d2b743809a0eac468fb3b364a38261f59a026d096277faf9f1b43188 |
| planner/ingest | DISCOVER_AND_ACQUIRE / PARSE_LOCAL |
| validation | PASS / COMPATIBLE / blocking 0 |
| P8 | ADDED, research_ready=true |

Combined acquire/ingest request counts were ticker map 2, submissions 2, archive index 1, archive members 7, other 0. The selected package had the seven expected members, including primary aapl-20250628.htm, XSD, FilingSummary, calculation, definition, label, and presentation members.

The MCP/P8 local-only run monkeypatched network access and exercised all eleven read paths: ffdf_list_documents, ffdf_get_document, ffdf_search_document, ffdf_read_pages, ffdf_list_sections, ffdf_list_tables, ffdf_get_table, ffdf_list_raw_facts, ffdf_get_fact, ffdf_get_evidence, and ffdf_get_validation. Blocked network calls were 0; the document returned 40 pages, 38 tables, 769 raw facts, 769 evidence records, and validation issues 0.

## 16. FT-15 — live Toyota FY2025 20-F and 6-K boundary

Commands:

~~~text
acquire --market US --ticker TM --year 2025 --period FY
ingest --market US --ticker TM --year 2025 --period FY
acquire --market US --ticker TM --year 2025 --period Q1
~~~

FY result:

| Field | Value |
|---|---|
| CIK | 0001094517 |
| accession | 0001193125-25-142326 |
| form | 20-F |
| report period | 2025-03-31 |
| observation SHA | 1e8e0e400a4395f26d4e984d8922050f0c33e5b318a66c55b95b540e1f0ca21b |
| source submissions SHA | 98e586d56a649aec761b4808ec6ac3f18da756418ccd7e795fdf46bc5b198f5b |
| package SHA | 184f2d3ca87b806325639ecc6fb8b5594654a93594750fda39787c8f940b53a5 |
| validation/P8 | PASS / ADDED / research_ready=true |

FY request counts were ticker map 2, submissions 2, archive index 1, archive members 3, other 0. The no-network P8/MCP run returned 182 pages, 419 tables, 3373 raw facts, 3373 evidence records, and validation issues 0.

The Q1 command observed current 6-K and 6-K/A submissions but did not create a quarterly slot. It returned controlled P11_FILING_NOT_FOUND; ticker map 1, submissions 1, archive calls 0; Q1 Registry bindings and catalog documents were empty. The independent form-policy check returned P11_UNSUPPORTED_FPI_PERIODIC_MAPPING with message 6-K is not automatically mapped to a US quarterly slot. Toyota 6-K filings were not guessed into a Q1 slot.

## 17. FT-16 — explicit-CIK Kellanova amendment conflict

Command:

~~~text
acquire --market US --cik 0000055067 --year 2024 --period FY
~~~

Results:

- ticker-map fetches: 0;
- current submissions fetches: 1;
- archive index/member fetches: 0;
- observation SHA: 96f4547b05ba0162141f824e1d48f27922d937f985681e5d5d36c4309aeb714c;
- retrieved at: 2026-11-16T07:22:32.651352+00:00;
- state: AMENDED_VARIANT_PRESENT;
- controlled reason: P11_AMENDED_VARIANT_PRESENT;
- selected original accession: 0001628280-25-007118.

The current observation contained both variants:

| Accession | Form | Amended | Filing date | Report period |
|---|---|---:|---|---|
| 0000055067-25-000127 | 10-K/A | yes | 2025-03-07 | 2024-12-28 |
| 0001628280-25-007118 | 10-K | no | 2025-02-21 | 2024-12-28 |

An acceptance-only stale original binding/package fixture was present before the conflict check. After current discovery the stale binding remained only as a non-published fixture; catalog slot documents were empty, research_ready_publication=false, and stale local reuse was overridden. No candidate package was acquired.

## 18. FT-17 — P0-P10 preservation and CN/HK/MCP representative coverage

The corrected formal P0-P10 command used the active worktree source path:

~~~text
PYTHONPATH=D:\Codex\FinancialFilingDataFoundation\worktrees\active\p11-sec-rebuild-development\src
python -m pytest -q tests/unit/acquisition tests/unit/identity tests/unit/validation tests/unit/registry tests/unit/mcp tests/unit/research tests/unit/review --basetemp D:\t\p11f5\ft17-p0p10-rerun
~~~

Result: 371 passed in 61.84s, exit 0.

Representative CN/HK/MCP command:

~~~text
python -m pytest -q tests/unit/acquisition/test_service_raw_store.py tests/unit/acquisition/test_dayu_runner_extra.py tests/unit/identity/test_models.py tests/unit/mcp/test_catalog_service.py tests/unit/mcp/test_trusted_source.py tests/unit/research/test_research_context.py --basetemp D:\t\p11f5\ft17-cnhk-mcp
~~~

Result: 85 passed in 4.20s, exit 0.

The first collection attempt omitted the explicit worktree PYTHONPATH and returned exit 2 with 21 import errors before tests executed. This was a runner-environment invocation issue, corrected by the command above; it did not modify source, tests, or accepted source data. The corrected formal run passed.

## 19. FT-18 — final drift and evidence integrity boundary

Before creating this evidence file, the following were rerun:

~~~text
git status --short
git diff --check
git diff --name-status f1cc76889718e06fdbdc46926e2b207b740a96e3..HEAD
~~~

Results:

- status output was empty;
- diff check exited 0;
- post-candidate changes were documentation/governance only;
- forbidden-path count was 0;
- branch, HEAD, and authoritative remote matched the authorized identity;
- FFDF_P11_US_DEV was absent;
- SEC contact configuration was present without recording its value.

The only file created by this evidence step is:

~~~text
development/210-p11-formal-test-evidence-5.md
~~~

All raw logs remain outside Git at D:\ffdf-p11-ft5\evidence, including the FT-00 through FT-18 gate logs and acceptance-only harness scripts. No raw live package or temporary harness output is being added to the repository.

## 20. Final execution classification

All required FT-00 through FT-18 gates passed. No production/test drift, required repair, external unavailability, unexplained Apple package identity drift, stale fallback, legacy compatibility failure, or P8/MCP network violation was observed.

~~~text
EXECUTION_PASS
~~~

This PC Acceptance/Test Agent execution does not declare Formal Acceptance or P11 DONE. The next fixed action is:

~~~text
CHATGPT INDEPENDENT FORMAL ACCEPTANCE REVIEW 5
~~~
