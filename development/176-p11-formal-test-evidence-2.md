# P11 Formal Acceptance Cycle 2 Evidence

## 1. Exact identity and execution boundary

- Repository: `D:\Codex\FinancialFilingDataFoundation`
- Active worktree: `D:\Codex\FinancialFilingDataFoundation\worktrees\active\p11-sec-rebuild-development`
- Branch: `task/p11-sec-rebuild-development`
- Exact production candidate: `9b7fcc9fc37a423eaafd1dde762e9c81d475df9e`
- Code review: `development/174-p11-code-review-result-9.md`
- Code review commit: `79f91e0dde8e71547e39229b1118ab553ab4dd38`
- Code review verdict: `REVIEW_PASS`
- Formal test plan: `development/175-p11-formal-test-plan-2.md`
- Formal test plan commit: `0c26d86ce648324ccda8d7c07574df30f1a2c0c3`
- Previous failed candidate: `2504614265b7a233ef9e4a772544ad63dd6eec37`
- Previous failed evidence: `development/171-p11-formal-test-evidence.md`
- Acceptance failure review: `development/172-p11-formal-acceptance-review-1.md`
- Acceptance root: `D:\Codex\FinancialFilingDataFoundation\work\p11-formal-acceptance-9b7fcc9f`
- Raw logs and acceptance-only harnesses: `work/p11-formal-acceptance-9b7fcc9f/evidence/`

The review and plan objects were initially fetched from the GitHub development ref into an independent local ref for read-only verification; before the evidence commit, the active worktree was not reset or checked out to that ref. After the evidence commit, the plan ref was merged with `--no-ff` solely to synchronize the remote branch. That merge contained documentation only. No production/test source was modified during this acceptance execution.

## 2. FT-00 candidate freeze

Authoritative preflight log: `FT-00-preflight-cycle2.txt`.

```text
FFDF_SEC_CONTACT_EMAIL configured: YES
branch: task/p11-sec-rebuild-development
HEAD: bb56952f158e1139b3330546aa37102933251011
candidate: 9b7fcc9fc37a423eaafd1dde762e9c81d475df9e
review: 79f91e0dde8e71547e39229b1118ab553ab4dd38
plan: 0c26d86ce648324ccda8d7c07574df30f1a2c0c3
candidate ancestor exit: 0
git diff --check exit: 0
Python: 3.14.9
SUPPORTED_MARKETS: ('CN', 'HK')
REGISTRY_SCHEMA_VERSION: 1
SEC_REGISTRY_SCHEMA_VERSION: 3
VIRTUAL_HTML_NORMALIZER_VERSION: VIRTUAL_HTML_V4
P11_SEC_PROVIDER: UNAVAILABLE
FFDF_P11_US_DEV: enabled explicitly for execution
working tree before evidence: clean
post-candidate changes: development/173-p11-ft08-acquisition-error-path-repair-evidence.md only
```

Result: `PASS`.

## 3. FT-01 deterministic regression

The first run using the long acceptance-root pytest basetemp reproduced only Windows path failures: full unit `31 failed, 599 passed`, and CN/HK `1 failed, 95 passed`, all at long review/provenance paths. The authoritative rerun used short project-local basetemp directories and is recorded in the `*-short-temp` logs.

| Scope | Command result | Exit |
| --- | --- | ---: |
| Provider/acquisition focused | `11 passed in 2.46s` | 0 |
| Reviewed FT-08 scope | `84 passed in 4.48s` | 0 |
| P11 focused `tests/unit/us_sec` | `100 passed in 4.80s` | 0 |
| Full unit `tests/unit` | `630 passed in 52.84s` | 0 |
| CN/HK regression | `96 passed in 4.21s` | 0 |
| `python -m compileall -q src tests` | PASS | 0 |
| `git diff --check` | PASS | 0 |

Result: `PASS`.

## 4. FT-02 Registry migration/version gate

Acceptance harness: `FT-02-registry-harness-cycle2.py`.

```json
{
  "v2-A": {
    "historical_ref": "05e06096bc8b788d0467a1ce3442829e87727b6",
    "migration_calls": 1,
    "reopen_migration_calls": 0,
    "registry_schema_version": 1,
    "sec_schema_version": 3,
    "compatibility_after": "INCOMPATIBLE",
    "cn_rows_preserved": true,
    "idempotent_reopen": true
  },
  "v2-B": {
    "historical_ref": "362877244aa553ca4d76eb71318b116cde04c6a5",
    "migration_calls": 1,
    "reopen_migration_calls": 0,
    "registry_schema_version": 1,
    "sec_schema_version": 3,
    "compatibility_after": "INCOMPATIBLE",
    "cn_rows_preserved": true,
    "idempotent_reopen": true
  },
  "unknown-unversioned": {
    "reason_code": "REGISTRY_SCHEMA_UNSUPPORTED",
    "migration_calls": 0,
    "no_mutation": true
  },
  "future-metadata-v99": {
    "reason_code": "REGISTRY_SCHEMA_UNSUPPORTED",
    "migration_calls": 0,
    "no_mutation": true
  }
}
```

Result: `PASS`, harness exit 0.

## 5. FT-03 V3 to V4 and planner reuse

Acceptance harness: `FT-03-incremental-harness-cycle2.py`.

```text
old parser: VIRTUAL_HTML_V3
new parser: VIRTUAL_HTML_V4
package_sha256: 1f9e7af01649d60e6ac0a4a991c437f03dacbd424b43a5b401a53e3c5854dd75
first planner action: PARSE_LOCAL
first parser calls: 1
first network calls: 0
old V3 unchanged: true
V4 created: true
second planner action: REUSE_DATA
second parser calls: 0
second network calls: 0
stale parser rejected: true
stale schema rejected: true
wrong package rejected: true
REVIEW_REQUIRED + COMPATIBLE rejected: true
exact PASS + COMPATIBLE + zero blocking reusable: true
```

Result: `PASS`, harness exit 0.

## 6. FT-04 Apple FY2025 10-K

Acquire, ingest, and status each exited 0. The live receipt was:

```text
accession: 0000320193-25-000079
form: 10-K
report period: 2025-09-27
company: US:CIK0000320193
package_sha256: 0569b63bddb33e4bd5966780837a813bb0eb4fceaca306a0fb8f945463a92d1e
parser: VIRTUAL_HTML_V4
validation: PASS
compatibility: COMPATIBLE
blocking: 0
research_ready: true
p8 catalog: ADDED
```

Result: `PASS`.

## 7. FT-05 Apple FY2025 Q3 and full P8

Acquire, ingest, and status each exited 0. The live receipt was:

```text
accession: 0000320193-25-000073
form: 10-Q
report period: 2025-06-28
company: US:CIK0000320193
package_sha256: 08b06ed4f47918f46bf940d965d2535e4b1caaf5957a5ded0f38d799514318e9
parser: VIRTUAL_HTML_V4
validation: PASS
compatibility: COMPATIBLE
blocking: 0
research_ready: true
p8 catalog: ADDED
```

The P8 harness exercised all 11 methods: `list_documents`, `get_document`, `search`, `read_pages`, `list_sections`, `list_tables`, `get_table`, `list_raw_facts`, `get_fact`, `get_evidence`, and `get_validation`.

```text
documents listed: 2
P8 HTTP calls: 0
P8 acquisition calls: 0
FY: pages 81, tables 62, facts 2262, evidence 2262
Q3: pages 40, tables 38, facts 1538, evidence 1538
FY custom aapl facts: 166, PRESENT_AND_RESOLVED
FY hidden facts: 22, PRESENT_AND_RESOLVED
Q3 custom aapl facts: 74, PRESENT_AND_RESOLVED
Q3 hidden facts: 9, PRESENT_AND_RESOLVED
virtual_page_no filtering: PASS
raw_qname filtering: PASS
fact to evidence: PASS
member SHA traceability: PASS
table/cell traceability: PASS
```

Result: `PASS`.

## 8. FT-06 Toyota FY2025 20-F

Acquire, ingest, and status each exited 0. Toyota ingest completed with no blocking issue.

```text
accession: 0001193125-25-142326
form: 20-F
report period: 2025-03-31
company: US:CIK0001094517
package_sha256: 45bc0c747c55f26149a87be6056a8e05b008562c2bda62f717bec7bfee20dc7f
parser: VIRTUAL_HTML_V4
validation: PASS
compatibility: COMPATIBLE
blocking: 0
research_ready: true
facts: 6746
evidence: 6746
members: 4
P8 HTTP calls: 0
P8 acquisition calls: 0
```

The FPI policy test `test_fpi_annual_is_supported_but_quarterly_6k_is_not_assumed` returned `1 passed, 7 deselected` with exit 0. No quarterly 6-K mapping was guessed.

Result: `PASS`.

## 9. FT-07 Kellanova CIK-only amendment gate

The acquire command used CIK `55067`, year `2024`, period `FY`, and no ticker argument. It exited 10 with the controlled result:

```text
reason_code: P11_AMENDED_VARIANT_PRESENT
```

The verification harness exited 0 and found:

```text
original: 0001628280-25-007118, 10-K, amended=false, report_period=2024-12-28
amendment: 0000055067-25-000127, 10-K/A, amended=true, report_period=2024-12-28
ticker_argument: null
active_bindings: 0
active_catalog_rows: 0
local_packages_for_slot: 0
```

Result: `PASS`.

## 10. FT-08 security, HTTP, and malformed source

The reviewed scope returned `84 passed` with exit 0. The explicit malformed-case selection returned `6 passed, 5 deselected` with exit 0. Verbose case names and results were recorded in `FT-08-malformed-cases-verbose-cycle2.txt`:

| Malformed input | Observed result |
| --- | --- |
| Invalid main submissions JSON | `P11_SEC_DISCOVERY_FAILED` |
| Invalid historical submissions JSON | `P11_SEC_DISCOVERY_FAILED` |
| Invalid archive index JSON | `P11_SEC_DISCOVERY_FAILED` |
| Invalid archive directory | `P11_SEC_DISCOVERY_FAILED` |
| Invalid archive item list | `P11_SEC_DISCOVERY_FAILED` |
| Invalid archive item record | `P11_SEC_DISCOVERY_FAILED` |

The original acceptance-only security harness also exited 0:

```text
malformed_index_calls: 2
terminal_403_attempts: 2
terminal_429_attempts: 3
retry_after_max_seconds: <= 30
redirect_host_and_cap: true
safe_nested_path: true
unsafe_path_cases: 8
source_drift_rejected: true
remote_script_not_executed: true
```

No `UnboundLocalError`, `NameError`, or uncontrolled generic exception occurred.

Result: `PASS`.

## 11. FT-09 no-AI and runtime boundary

The runtime audit exited 0:

```text
forbidden_ai_hits: 0
sec_runtime_lock: stdlib-only
runtime_argv_allowlist: true
runtime_shell_false: true
filing_content_arbitrary_shell_paths: 0
Apple P8 HTTP/acquisition calls: 0/0
Toyota P8 HTTP/acquisition calls: 0/0
```

Result: `PASS`.

## 12. FT-10 idempotent REUSE_DATA

The acceptance-only idempotency harness exited 0:

```text
acquire status: REUSED_LOCAL
planner action: REUSE_DATA
package_sha256: 0569b63bddb33e4bd5966780837a813bb0eb4fceaca306a0fb8f945463a92d1e
repeat HTTP calls: 0
repeat acquisition calls: 0
repeat parser reruns: 0
fact count: 2262
evidence count: 2262
table count: 62
before_after_identity_unchanged: true
```

Result: `PASS`.

## 13. FT-11 CN/HK preservation

The preservation harness exited 0:

```text
SUPPORTED_MARKETS: ["CN", "HK"]
REGISTRY_SCHEMA_VERSION: 1
PRAGMA user_version: 1
CN/HK legacy bindings: 0
non-SEC document sources: 0
non-US SEC bindings: 0
catalog markets: ["US"]
CN/HK acceptance directories present: false
CN/HK regression: 96 passed
```

Result: `PASS`.

## 14. Live package and member hash inventory

The read-only inventory was recorded in `FT-04-05-06-hash-inventory.stdout.txt`.

### Apple FY2025 FY

```text
package_sha256: 0569b63bddb33e4bd5966780837a813bb0eb4fceaca306a0fb8f945463a92d1e
manifest_sha256: 37afb8b6138b972182f5c6f07f99b71c75536badbce65b4b25961297f0767399
FilingSummary.xml: f5e632bd6de8965a5251fd590f053553c017396f5ec75b0ddc9e475832a7c0a2
aapl-20250927.htm: bd5b457d90e590f8634576712488821595ee663f424e1ee3f7b54ff61d471c33
aapl-20250927.xsd: e697d106fae1543535c634bede6337b8f1ecd987e7655eb91c62913900ab6335
aapl-20250927_cal.xml: 314091ba88cd58f392874866c19010ed9facdd643f34f0afbcf37137192c5f05
aapl-20250927_def.xml: 6eb3e955297ea510ceaff7331f57dc948cb439e83a634a3882f3806d6fb7434a
aapl-20250927_htm.xml: e1076735f1c81bc96d5c1ff6e1a9d23515d6eacf52b405cb1f7da3e379ac533b
aapl-20250927_lab.xml: 9ec8874c0af055946d80061bd5558599c4eb2b56b21e48a4670751097d166118
aapl-20250927_pre.xml: 43ce57fec893a2c2974a043198a3acc105238aaf19cb4a93ba8812d412d0ab7d
```

### Apple FY2025 Q3

```text
package_sha256: 08b06ed4f47918f46bf940d965d2535e4b1caaf5957a5ded0f38d799514318e9
manifest_sha256: bfd4a6781561915bcf6797ead7ca3e23efe1ad2d5fb61d8cebb16682b337a45e
FilingSummary.xml: f087d0ffa4b5d06c2f9530864f211d7d3f7b7ffb0d77fb196eaec5a62cc2b326
aapl-20250628.htm: b6b6de2bda6e9d82844bfe661e8b29124ba4ff483e927bd3d57387326597bca5
aapl-20250628.xsd: a040fc385608214977377b2408834fda5cec6010e1810d4aaa9f01cd662befa5
aapl-20250628_cal.xml: 7ca2a1a1fa5302689d66dda5da6df42059422c37c21c9aa5b6c80451e6769e0d
aapl-20250628_def.xml: ee4bea096ec2e17cd84c59f9dfbe72513ca7c91345bab9f7abdc77ddf6f597cf
aapl-20250628_htm.xml: a33da25d38ddc3c39fcb80b996a26fb562b8938f942f7a41a5f156339a7d70c9
aapl-20250628_lab.xml: 7db99a6df6c33277f890f2f29f14f146bfd6b96d2a9c3f631e0772be3e08be0b
aapl-20250628_pre.xml: 4e62e7489a364118ae9d94198f4b6944f0b676143e7595fd9537c35c5214e128
```

### Toyota FY2025 FY

```text
package_sha256: 45bc0c747c55f26149a87be6056a8e05b008562c2bda62f717bec7bfee20dc7f
manifest_sha256: 91bdf731c037fe428781f19d923dd50f223ac79772f973d35bb500f3a2e5f57f
FilingSummary.xml: 2cd16ed1715a1e3e259993147605c68cd2128f1f05e71a123afd98bade29fd10
d925022d20f.htm: 0868c7b7a6a7c884123b4aca04d99e330ed1ada524ff56badc45f78d51d4dacf
d925022d20f_htm.xml: 15874b00e2a27ac40f0b5f5775cfb7a5af049422d6c5c0107d93787fbb3c98a7
tm-20250331.xsd: 1afafd34e4c934bbd1a05f0348ba862168d04a77285a488150387306f30ace9c
```

## 15. Non-authoritative command retries

These were operator/environment command corrections, not production/test failures:

- The first FT-00 constants probe imported a non-existent helper; the corrected preflight exited 0.
- The first full/CN-HK run used the long acceptance-root basetemp and reproduced path-only failures; the prescribed short-temp reruns passed with zero failures.
- The first reviewed-scope probe used an obsolete test filename and exited 4 before collection; the actual reviewed five-file scope returned 84 passed.
- The first live CLI wrapper used a PowerShell automatic-parameter name and exited 2 before command parsing; the corrected acquire/ingest/status commands all exited 0.
- The first FPI probe used the main checkout working directory and exited 4 before collection; the active-worktree rerun returned 1 passed, 7 deselected.

## 16. Final execution boundary

- FT-00: `PASS`
- FT-01: `PASS`
- FT-02: `PASS`
- FT-03: `PASS`
- FT-04: `PASS`
- FT-05: `PASS`
- FT-06: `PASS`
- FT-07: `PASS`
- FT-08: `PASS`
- FT-09: `PASS`
- FT-10: `PASS`
- FT-11: `PASS`
- Production/test code changed during formal acceptance: `NO`
- Post-evidence branch synchronization: docs-only `--no-ff` merge `cd3bc21cdfc1e22c240512e2b0e546e3b90e914d`
- Main merge: `NOT RUN`
- P11 production availability: `NOT CHANGED`
- Execution result: `EXECUTION_PASS`
- Next action: `CHATGPT INDEPENDENT FINAL ACCEPTANCE REVIEW 2`
