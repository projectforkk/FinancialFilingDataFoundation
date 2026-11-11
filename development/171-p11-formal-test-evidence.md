# P11 Revised Formal Test Evidence

## 1. Execution identity

- Project: `FinancialFilingDataFoundation`
- Acceptance workspace: `D:\Codex\FinancialFilingDataFoundation\work\p11-formal-acceptance-25046142`
- Development worktree: `D:\Codex\FinancialFilingDataFoundation\worktrees\active\p11-sec-rebuild-development`
- Branch: `task/p11-sec-rebuild-development`
- Production candidate: `2504614265b7a233ef9e4a772544ad63dd6eec37`
- Code review: `development/169-p11-code-review-result-8.md`
- Review commit: `2d69f1dd9b07fd2a7e9425e26b5c3edb2a8d9abe`
- Review verdict: `REVIEW_PASS`
- Formal plan: `development/170-p11-revised-formal-test-plan.md`
- Formal plan commit: `062c419a40c1b49d83efeca3eaa320a3634b6eda`
- Executor HEAD at completion: `062c419a40c1b49d83efeca3eaa320a3634b6eda`
- Candidate is an ancestor of executor HEAD: `PASS`
- SEC contact gate: `FFDF_SEC_CONTACT_EMAIL_CONFIGURED=YES`; the value was not recorded.
- Python: `3.14.9`

No `src/`, `tests/`, runtime-lock, packaging, supported-market, capability, or main-branch changes were made during formal execution. The only development-worktree file added for this handoff is this evidence document. Acceptance harnesses and raw logs remain under the acceptance workspace and are not committed.

## 2. Gate result

Formal execution rule applied: an executed required-gate failure produces `EXECUTION_FAIL`.

| Gate | Result | Decisive evidence |
|---|---|---|
| FT-00 candidate freeze/preflight | PASS | `evidence/FT-00-preflight.txt` |
| FT-01 deterministic regression | PASS | registry `18 passed`; P11 `94 passed`; final full unit `624 passed`; final CN/HK `96 passed`; compileall and diff check exit 0 |
| FT-02 Registry migration/version acceptance | PASS | `evidence/FT-02-registry-harness-rerun.stdout.txt` |
| FT-03 V3 to V4/incremental acceptance | PASS | `evidence/FT-03-incremental-harness-final.stdout.txt` |
| FT-04 Apple FY2025 10-K live E2E | PASS | `evidence/FT-04-apple-fy2025-fy-*.txt` and P8 verification |
| FT-05 Apple FY2025 Q3/full P8 | PASS | `evidence/FT-05-apple-fy2025-q3-*.txt`, `FT-05-p8-harness-final4.stdout.txt` |
| FT-06 Toyota FY2025 20-F/FPI | PASS | `evidence/FT-06-*.txt` |
| FT-07 Kellanova amendment conflict | PASS | `evidence/FT-07-*.txt` |
| FT-08 security/HTTP/source integrity | **FAIL** | reviewed tests passed, but malformed archive-index harness exposed `UnboundLocalError` instead of the required `P11_SEC_DISCOVERY_FAILED` |
| FT-09 no-AI/runtime boundary | PASS | `evidence/FT-09-runtime-audit.stdout.txt` |
| FT-10 live idempotency/REUSE_DATA | PASS | `evidence/FT-10-idempotency-harness.stdout.txt` |
| FT-11 CN/HK preservation | PASS | `evidence/FT-11-preservation.stdout.txt` |

**Formal execution result: `EXECUTION_FAIL` due to FT-08.**

## 3. FT-01 deterministic regression

The first full-unit and CN/HK attempts used the long acceptance `--basetemp` path and produced only Windows `WinError 206`/path-creation failures in review/MCP tests. They were retained as raw evidence. The same exact test scopes were rerun with short project-local temporary paths, as required by the Windows project instructions:

- `tests/unit/us_sec/test_package_registry.py`: `18 passed in 1.02s`.
- `tests/unit/us_sec`: `94 passed in 3.86s`.
- `tests/unit`: `624 passed in 48.45s`.
- CN/HK scope `tests/unit/identity tests/unit/registry tests/unit/mcp tests/unit/user_cli`: `96 passed in 4.73s`.
- `python -m compileall -q src tests`: exit `0`.
- `git diff --check`: exit `0`.

Raw command receipts are in the `FT-01-*.stdout.txt`, `FT-01-*.stderr.txt`, and `FT-01-*.meta.txt` files under the acceptance evidence directory.

## 4. FT-02 Registry migration acceptance

The acceptance-only SQLite harness used the reviewed historical shapes:

- v2-A ref `05e06096bc8b788d0467a1ce3442829e87727b6`: migration called once; SEC schema became v3; legacy `PRAGMA user_version` remained `1`; parsed compatibility became `INCOMPATIBLE`; CN legacy rows and non-SEC schema were preserved; second reopen called migration zero times and was byte/snapshot-idempotent.
- v2-B ref `362877244aa553ca4d76eb71318b116cde04c6a5`: existing compatibility column was preserved; prior `COMPATIBLE` value was reset to fail-closed `INCOMPATIBLE`; all other rows/schema were preserved; second reopen was idempotent.
- Unknown unversioned shape with `future_unknown_field`: `RegistrySchemaUnsupported`, zero migration calls, no mutation.
- Future metadata version `99`: `RegistrySchemaUnsupported`, zero migration calls, no DDL/mutation.

The final harness output is `status=PASS` for all four cases.

## 5. FT-03 incremental acceptance

Acceptance fixture result:

- immutable local package plus old `VIRTUAL_HTML_V3` artifact/Registry row planned `PARSE_LOCAL`;
- V4 artifact was created with one parser call and zero HTTP/acquisition calls;
- old V3 manifest remained byte-identical;
- current `PASS` + `COMPATIBLE` + zero blocking row planned `REUSE_DATA`;
- second ingest used zero parser calls and zero HTTP/acquisition calls;
- stale parser, stale schema, wrong package, and `REVIEW_REQUIRED` + `COMPATIBLE` rows were all rejected as non-reusable;
- exact current `PASS` + `COMPATIBLE` + zero-blocking row was reusable.

Package SHA in this local fixture was `1f9e7af01649d60e6ac0a4a991c437f03dacbd424b43a5b401a53e3c5854dd75`.

## 6. Live filing results

### Apple FY2025 10-K

- accession: `0000320193-25-000079`
- form: `10-K`
- report period: `2025-09-27`
- company: `US:CIK0000320193`
- package SHA: `0569b63bddb33e4bd5966780837a813bb0eb4fceaca306a0fb8f945463a92d1e`
- primary member SHA: `bd5b457d90e590f8634576712488821595ee663f424e1ee3f7b54ff61d471c33`
- members: `8`
- virtual pages: `81`
- tables: `62`
- Raw Facts: `2262`
- Evidence: `2262`
- parser: `VIRTUAL_HTML_V4`
- validation: `PASS`
- compatibility: `COMPATIBLE`
- blocking issues: `0`
- `research_ready`: `true`
- P8 catalog registration: successful.

### Apple FY2025 Q3

- accession: `0000320193-25-000073`
- form: `10-Q`
- report period: `2025-06-28`
- company: `US:CIK0000320193`
- package SHA: `08b06ed4f47918f46bf940d965d2535e4b1caaf5957a5ded0f38d799514318e9`
- primary member SHA: `b6b6de2bda6e9d82844bfe661e8b29124ba4ff483e927bd3d57387326597bca5`
- members: `8`
- virtual pages: `40`
- tables: `38`
- Raw Facts: `1538`
- Evidence: `1538`
- parser: `VIRTUAL_HTML_V4`
- validation: `PASS`
- compatibility: `COMPATIBLE`
- blocking issues: `0`
- `research_ready`: `true`
- P8 catalog registration: successful.

The full P8 family was exercised against the acceptance catalog: `list_documents`, `get_document`, `search`, `read_pages`, `list_sections`, `list_tables`, `get_table`, `list_raw_facts`, `get_fact`, `get_evidence`, and `get_validation`. All passed with zero HTTP and zero acquisition calls. Virtual HTML pagination was explicit; page filtering used `virtual_page_no`; raw QName filtering matched; fact-to-evidence round-trip resolved; evidence member SHAs belonged to the immutable package; and table/cell source traceability resolved.

The frozen Apple fixtures contained custom extensions and hidden Inline XBRL facts:

- FY 10-K: `aapl:` facts `166`, hidden facts `22`, all resolved.
- Q3 10-Q: `aapl:` facts `74`, hidden facts `9`, all resolved.

### Toyota FY2025 20-F

- accession: `0001193125-25-142326`
- form: `20-F`
- report period: `2025-03-31`
- company: `US:CIK0001094517`
- package SHA: `45bc0c747c55f26149a87be6056a8e05b008562c2bda62f717bec7bfee20dc7f`
- members: `4`
- Raw Facts: `6746`
- Evidence: `6746`
- parser: `VIRTUAL_HTML_V4`
- validation: `PASS`
- compatibility: `COMPATIBLE`
- blocking issues: `0`
- P8 source verification: successful; HTTP/acquisition calls `0/0`.
- deterministic FPI policy test: `1 passed, 7 deselected`; annual 20-F is supported and quarterly 6-K mapping is not assumed.

## 7. FT-07 amendment conflict

The CIK-only command omitted `--ticker K` and returned controlled exit code `10` with `P11_AMENDED_VARIANT_PRESENT`.

Discovery captured both variants for the same FY slot:

- original: `0001628280-25-007118`, form `10-K`, `amended=false`;
- amendment: `0000055067-25-000127`, form `10-K/A`, `amended=true`.

No silent selection occurred. There were zero local packages, zero Registry bindings, and zero catalog rows for `US:CIK0000055067` FY2024.

## 8. FT-08 failure detail

The reviewed security/HTTP/provider/parser/registry/runtime test scope passed `78 tests`.

The acceptance-only harness then exercised a malformed SEC archive index after a valid annual candidate had been discovered. The required behavior was `P11_SEC_DISCOVERY_FAILED`. The candidate instead raised:

```text
UnboundLocalError: cannot access local variable 'SecError' where it is not associated with a value
```

The failing path is `src/financial_filing_data_foundation/us_sec/acquisition.py:181`, where the malformed `directory.item` shape reaches the intended `raise SecError(...)`. The function contains a conditional local import of `SecError` in the preceding JSON-decode exception branch, which makes `SecError` local to the function; that branch was not taken for the malformed-shape fixture. This is a production-candidate defect, not an acceptance harness pass condition.

Evidence: `FT-08-reviewed-security-http-tests.meta.txt` and `FT-08-security-harness-rerun.stderr.txt` / `.meta.txt`.

No production fix was applied during formal acceptance.

## 9. FT-09, FT-10, and FT-11

FT-09 passed with zero forbidden AI/API hits, stdlib-only SEC runtime lock, explicit argv allowlist, `shell=False`, zero arbitrary-shell paths for filing content, and zero P8 HTTP/acquisition calls.

FT-10 passed with:

- acquire status `REUSED_LOCAL`;
- planner/ingest action `REUSE_DATA`;
- package SHA unchanged;
- 2262 facts, 2262 evidence, 62 tables unchanged;
- parser calls `0`;
- HTTP calls `0`;
- acquisition calls `0`;
- before/after package, manifest, member, V4 artifact, Registry parsed-row, and catalog identity snapshot unchanged.

FT-11 passed with:

- `SUPPORTED_MARKETS == ('CN', 'HK')`;
- `REGISTRY_SCHEMA_VERSION == 1`;
- acceptance Registry `PRAGMA user_version == 1`;
- CN/HK legacy bindings `0`;
- non-SEC legacy source rows `0`;
- non-US SEC bindings `0`;
- acceptance catalog markets `['US']`;
- no acceptance CN/HK ingest directories.

## 10. Handoff boundary

- Main merge: `NOT RUN`.
- Production capability availability: `NOT CHANGED`; `P11_SEC_PROVIDER` remains `UNAVAILABLE`.
- Candidate remains unaccepted because FT-08 failed.
- Next action: independent formal acceptance review must assess the FT-08 defect and decide whether a new repair candidate and a new formal acceptance cycle are required.
