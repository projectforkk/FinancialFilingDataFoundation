# P11 Formal Test Evidence 6

Status: `EXECUTION_PASS`

This is the PC Acceptance/Test Agent execution record. It is not an
independent Formal Acceptance decision and it does not declare P11 DONE.

## 1. Exact execution identity

| Item | Value |
|---|---|
| Repository | `projectforkk/FinancialFilingDataFoundation` |
| Worktree | `D:\Codex\FinancialFilingDataFoundation\worktrees\active\p11-sec-rebuild-development` |
| Branch | `task/p11-sec-rebuild-development` |
| Authoritative remote | `origin/reconcile/p11-140-143-local-chain` |
| Frozen production candidate | `7aac34e763b4c9caac24489eb049aa3dc6efb026` |
| Corrected Design Baseline | `09e3174b7e19a60cc5955862670fac8931af67db` |
| Design 40 review record | `development/212-p11-design40-freeze-review-result.md` |
| Review 9 | `development/215-p11-fresh-full-exact-candidate-review-9.md` |
| Review 9 commit | `5fe0bc139f9a2b0475a1912c65f40008e84572f4` |
| Development evidence | `development/214-p11-issue148-development-evidence.md` |
| Development evidence commit | `2c68f85199e6e77dc30c37e5e6eb5515b5bd6fe2` |
| Formal Test Plan 6 | `development/216-p11-formal-test-plan-6.md` |
| Formal Test Plan SHA | `31cf1f04bb5ea56409e1e44230460d9b98060833` |
| Execution Authorization 6 | `development/217-p11-formal-test-execution-authorization-6.md` |
| Authorization commit | `4aaa4b8076546f9daa258e1827cd1a61e3eeffbf` |
| Execution HEAD before evidence | `4aaa4b8076546f9daa258e1827cd1a61e3eeffbf` |

`git fetch origin` was run before the fast-forward-only synchronization. The
authoritative `origin/reconcile/p11-140-143-local-chain` resolved to the
authorization commit and the candidate is an ancestor of HEAD. No rebase,
reset, clean, force push, main merge, production candidate creation, or
production/test edit was performed.

## 2. Environment and frozen controls

| Check | Result |
|---|---|
| Python | `3.14.9` |
| pytest | `9.2.0` |
| Project interpreter | `D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe` |
| `FFDF_P11_US_DEV` | `ABSENT` for every formal harness |
| `FFDF_SEC_CONTACT_EMAIL` | `CONFIGURED`; value intentionally not recorded |
| Formal roots | `D:\ffdf-p11-ft6` |
| pytest temporary root | `D:\t\p11f6` |
| Network development bypass | not used |

Frozen constants observed at FT-00/FT-01:

```text
REGISTRY_SCHEMA_VERSION=1
SEC_REGISTRY_SCHEMA_VERSION=5
PACKAGE_MANIFEST_SCHEMA=p11-sec-package-v1
SEC_SOURCE_CONTAINER_SCHEMA=p11-sec-source-container-v1
SEC_PACKAGE_SOURCE_PROVENANCE_SCHEMA=p11-sec-package-source-v1
SEC_DISCOVERY_SCHEMA=p11-sec-discovery-v1
VIRTUAL_HTML_NORMALIZER_VERSION=VIRTUAL_HTML_V6
SEC_ARTIFACT_SCHEMA=p11-sec-artifacts-v2
SEC_VALIDATION_SCHEMA=p11-sec-validation-v4
```

## 3. Gate summary

| Gate | Verdict | Acceptance receipt |
|---|---|---|
| FT-00 | PASS | Candidate, baseline, branch, clean worktree, constants, and bypass controls verified. |
| FT-01 | PASS | Exact regression commands and counts recorded below; no skips. |
| FT-02 | PASS | ISSUE-147 complete nine-case acceptance-only identity matrix. |
| FT-03 | PASS | Complete-submission URL and source-container identity/tamper harness. |
| FT-04 | PASS | SGML inventory and exact byte-locator harness. |
| FT-05 | PASS | SCRIPT/APPLET/OBJECT/IFRAME/EMBED active-content boundary. |
| FT-06 | PASS | Complete-submission-only package selection/request boundary. |
| FT-07 | PASS | Package-source provenance identity and replay. |
| FT-08 | PASS | Full 20-case provenance/package/member tamper matrix. |
| FT-09 | PASS | Legacy/current migration and external attestation. |
| FT-10 | PASS | Current source conflict and idempotent attestation semantics. |
| FT-11 | PASS | Registry v5 additive migration and future-version rejection. |
| FT-12 | PASS | Validation-v4, provenance replay, no-v3 fallback. |
| FT-13 | PASS | Planner/current-source eligibility matrix. |
| FT-14 | PASS | P8/MCP provenance replay with zero network calls. |
| FT-15 | PASS | Fresh live Apple FY2025 root A. |
| FT-16 | PASS | Independent fresh Apple FY2025 root B exact identity equality. |
| FT-17 | PASS | Direct-member diagnostic isolation. |
| FT-18 | PASS | Corrected online repeat reuse semantics. |
| FT-19 | PASS | Fresh live Apple FY2025 Q3. |
| FT-20 | PASS | Fresh live Toyota FY2025 20-F and 6-K quarterly guard. |
| FT-21 | PASS | Fresh explicit-CIK Kellanova amendment conflict. |
| FT-22 | PASS | Acceptance-only ISSUE-142/143/145/146 regression harness. |
| FT-23 | PASS | P0-P10 and representative CN/HK/MCP regression. |
| FT-24 | PASS | Final drift and evidence-integrity boundary. |

## 4. FT-01 deterministic regression receipts

All commands used the active worktree source and short basetemp paths.

```text
python -m pytest -q tests/unit/us_sec/test_issue148.py --basetemp D:\t\p11f6\i148
20 passed, exit 0

python -m pytest -q tests/unit/us_sec/test_issue147.py tests/unit/us_sec/test_issue146.py --basetemp D:\t\p11f6\i146148
19 passed, exit 0

python -m pytest -q tests/unit/us_sec/test_repair_140_143.py tests/unit/us_sec/test_corrected_repair.py tests/unit/us_sec/test_validation_p8.py --basetemp D:\t\p11f6\repair
92 passed, exit 0

python -m pytest -q tests/unit/us_sec --basetemp D:\t\p11f6\us
283 passed, exit 0

python -m pytest -q tests/unit/mcp --basetemp D:\t\p11f6\mcp
65 passed, exit 0

python -m pytest -q tests/unit/acquisition tests/unit/identity tests/unit/validation tests/unit/registry tests/unit/mcp tests/unit/research tests/unit/review --basetemp D:\t\p11f6\p0p10
371 passed in 77.74s, exit 0

python -m pytest -q tests/unit --basetemp D:\t\p11f6\unit
813 passed in 99.27s, exit 0

python -m compileall -q src tests
exit 0

git diff --check
exit 0
```

No skip was observed in any FT-01 command. The focused ISSUE-146/147/148
total is 39 passed, the US SEC total is 283 passed, the MCP total is 65
passed, and the full unit total is 813 passed.

## 5. FT-02 — ISSUE-147 nine-case acceptance matrix

Acceptance-only harness:
`D:\ffdf-p11-ft6\evidence\FT-02-issue147-matrix.py`, exit 0.

The harness used source SHA
`d586b56f71a06e64ef635672813c8ce349ae1e6ca6e4f54a131f7080556fb6a9` and
two exact retrieval times:

| Retrieval | Snapshot ID |
|---|---|
| `2026-11-17T00:00:01+00:00` | `4d91a61657c4890cf4945993308ced8950bda1264e35fc3bd106ba109f528ffa` |
| `2026-11-17T00:00:02+00:00` | `cb7557641baa97037ad2c453839b049bbd6b08f359a1e9b89cc5a8865f8c5480` |

Both immutable observations coexist with the same source bytes/SHA and
different snapshot IDs. Each ID was independently recomputed from canonical
JSON. Distinct observations were accepted without `P11_SOURCE_DRIFT`.

The remaining seven cases were independently exercised:

| Case | Result |
|---|---|
| Same snapshot-ID path with conflicting canonical payload | `P11_SOURCE_DRIFT` |
| Invalid `retrieved_at` | `P11_TICKER_SNAPSHOT_INVALID` |
| Timezone-naive `retrieved_at` | `P11_TICKER_SNAPSHOT_INVALID` |
| Source bytes tampered without matching SHA | `P11_TICKER_SNAPSHOT_INVALID` |
| Derivative mapping tampered with valid source bytes | `P11_TICKER_SNAPSHOT_INVALID` |
| Current observation path/ID mismatch | `P11_TICKER_SNAPSHOT_INVALID` |
| Both original observation files remain immutable | PASS |

## 6. FT-03 through FT-14 source identity and migration receipts

### FT-03 — complete-submission source container

The exact URL was:

```text
https://www.sec.gov/Archives/edgar/data/320193/000032019325000001/0000320193-25-000001.txt
```

The persisted container had schema `p11-sec-source-container-v1`, kind
`SEC_COMPLETE_SUBMISSION_TEXT`, source SHA
`33e06fa70671a4dfb6f994a7172382131e20cce0b33d6bcf825871718955385c`, and
byte length 198. URL/query/path escape, body/metadata/path tamper, CIK or
accession mismatch, and size-limit cases all failed closed with the expected
source/provenance reason codes. Atomic reload was byte-identical.

### FT-04 — SGML inventory and slicing

The three DOCUMENT records were `annual.htm`, `annual.xml`, and `annual.xbrl`
with indices 1, 2, and 3. The exact payload locators were:

| Filename | Start | End | Length | Envelope |
|---|---:|---:|---:|---|
| `annual.htm` | 155 | 199 | 44 | TEXT |
| `annual.xml` | 301 | 331 | 30 | XML |
| `annual.xbrl` | 444 | 515 | 71 | XBRL |

Missing/duplicate structural fields, duplicate DOCUMENT records, duplicate
normalized filenames, unsafe names, and unsupported binary/UUencoded content
all returned `P11_PACKAGE_INVALID` or `P11_CONTENT_TYPE_INVALID` as required.
CRLF/LF handling and exact byte replay passed without whitespace/entity
normalization.

### FT-05 — active-content boundary

Five independent canonical complete-submission-derived primary fixtures were
run. `SCRIPT`, `APPLET`, `OBJECT`, `IFRAME`, and `EMBED` each failed with
`P11_CONTENT_TYPE_INVALID`. No bytes were stripped. The complete-submission
request count was 1, direct-member count was 0, and the package was not
created. The preserved source SHAs were:

```text
SCRIPT  3c953ca57aafccccffbb293a9f307fdd128cfed11ed00607496b6cf81cb28135
APPLET  80fba1bb41f3dabf6fb7171e9311731ce87f058ab6bc44be28a363b4ae7d3d20
OBJECT  c972a6ef940e0d1120e3e7a92710ceb0a1a1dbc1c16ed57ceda0f89b844b937c
IFRAME  f73c05bcd80df3d85554f344f8c6a07762a8403d9f5e13d0f48e01b3f1b2553a
EMBED   66d8a1a52fddfd7cbb9e1b9dea5161b75a028201567853f475ec606d81acadd2
```

### FT-06 — package request and selection boundary

The exact complete-submission URL was:

```text
https://www.sec.gov/Archives/edgar/data/320193/000032019325000004/0000320193-25-000004.txt
```

Request counts were complete submission 1, archive index 0, archive member 0,
and static/browser 0. The selected package had manifest
`p11-sec-package-v1`, package SHA
`d48799face1138e82e24c3d361a861fbed820503b6b6ade03f1838cf9a024f42`, source
container SHA
`7cbedddfbfb6da81f400ee0de7509afe87975357bafdc1c0faa1efae49700a37`, and
provenance SHA
`c156dbefe66e7b326d10e057bdd5da239722c55bc19fac4ddada3b9b46104512`.
The selected members were `FilingSummary.xml`, `annual.htm`, `annual.xsd`,
`annual_cal.xml`, `annual_def.xml`, `annual_lab.xml`, `annual_pre.xml`, and
`instance.xml`; unrelated exhibits were excluded.

### FT-07 — provenance identity and replay

The acceptance fixture had package SHA
`3b76390b2e11370e5f29f1785080c2e411b18ccc52800b7e9df5983981e19baf`,
provenance SHA
`7667c339d0a7d4f4508d3660b6f983b6868a12b69d2e187918015b47e2c3986f`, and
source-container SHA
`341aec76001207a2cad66bf8526e61782015a4b3272485a314f8d9de107cf381`
(length 383). The exact accession-bound URL and two member locators replayed
to the original bytes. Top-level/path identity changes failed closed with
`P11_PACKAGE_INVALID`.

### FT-08 — complete tamper matrix

Baseline package SHA was
`3b76390b2e11370e5f29f1785080c2e411b18ccc52800b7e9df5983981e19baf`,
provenance SHA
`4f54cf9ea4f541914a1628f97c9946e1f80dbebbf2733d7a9e8d6b5e9c48445a`, and
source-container SHA
`e76a060e2eac10eb56e071372fbac2dfef630e4765c7d4d31fa8fcaf8c299dba`.
All 20 independent tamper cases failed closed:

```text
provenance_sha, package_sha, CIK, accession, container metadata,
container SHA, relative name, role, public URL, document index,
document type, document sequence, filename, payload start, payload end,
envelope, member SHA, member length, package manifest SHA, package member bytes
```

The provenance/identity cases returned `P11_PROVENANCE_MISMATCH`, the manifest
case returned `P11_PACKAGE_INVALID`, and the member-byte case returned
`P11_MEMBER_HASH_MISMATCH`.

### FT-09 — legacy/current migration

The unattested audit-only package had SHA
`5d28f9289c022f5079046d759f540b2c4caf595469f9a0f52f1487ff1a614570` and was
not eligible for local parsing, revalidation, or reuse. In the coexistence
fixture, legacy SHA was
`d3941b73929475d893f78b012a82ad0cd799c3a1e9340a8cd42d68f128bfbc7b` and
current attested SHA was
`74ed9b22cd68f9d993a958f2b0808ec451b27fd7fb2c93c51c208aaf13c6ef55`;
both directories remained immutable and only the attested package was
plannable. Same-byte external attestation added provenance without changing
package bytes; resulting package SHA was
`1a441a2ba63d75789b197db415a475a412094937640528bb9c424fc92145377b`.

### FT-10 — current source conflicts

The three conflict cases failed closed as required:

```text
same accession, different current container       P11_SOURCE_DRIFT
same container, different package                 P11_PROVENANCE_MISMATCH
same package/container, different provenance      P11_PROVENANCE_MISMATCH
equivalent repeated attestation                   idempotent PASS
```

The fixture package SHAs were
`5a6cfe38143f5f3da2b2f65141960e77e591931f5b274e5852b9709ae4b81981` and
`f67ccd28a76433feeb026174a31efce2ed05d9680471c25c00739fb2e0913d1f`;
container SHAs were
`917993dad0e9dc84dac4498360836e04908faa8c72e36f73c8fc908499ca07eb` and
`a9ad6d5a758e8079b7064597980d4e7a8f3079695f7dd6a99f40d6dceb0a2b61`.

### FT-11 — Registry v5

The true v4 fixture migrated additively to SEC schema v5. All v4 SEC
source/binding/parsed/discovery rows and generic CN/HK rows were preserved;
the new tables were `sec_source_containers`,
`sec_package_source_provenance`, and `sec_package_member_locators`.
`PRAGMA user_version` remained 1. Round-trip values were package SHA
`48493d7d9a1eac2b0fb8a736cf5188559d237592261bd77544a64a61e4cd664d`, source
SHA `4f38df26f367ff3d99587b40b0325fb455ed794cf4f80fefb0fa162e3119b488`,
provenance SHA
`1287492a21cf38635ce9d025deeecfa9688e23a944d5bbd3cb68e47a8411e54f`, and
two locator rows. A future SEC schema version 6 was rejected before any
mutation with `SEC registry schema version 6 is newer than supported 5`.

### FT-12 — validation-v4 and no-v3 fallback

The acceptance root used current schema `p11-sec-validation-v4`, package SHA
`00741ec2e9e4dccd57bcbc0a6bd26650f0e0bcdd9355a523e99e80782efd2dfb`, and
provenance SHA
`4613c8c9375bee4b60f62f25f7a96f4c1854a356255eb17c9f26726182ee6ed2`.
Initial validation was `REVIEW_REQUIRED` with `research_ready=false` because
the fixture intentionally had no structured facts. Missing provenance and
tampered source both became `BLOCKED` with `research_ready=false`; a
v3-only path was not accepted as current. Same-byte revalidation had parser
count 0. Historical v3 bytes remained untouched.

### FT-13 — planner and incremental reuse

The planner truth table and runtime matrix passed:

```text
reuse parsed/current v4       REUSE_DATA
parsed/no current v4           REVALIDATE_LOCAL
package/no parsed              PARSE_LOCAL
no current package             DISCOVER_AND_ACQUIRE
amendment conflict             REVIEW_REQUIRED
```

The acceptance root had `FFDF_P11_US_DEV` absent, package SHA
`384c2cbe158eaff37543db05ce12f1fa78d68f3c953c3e201c293ecee72501cd`, and
provenance SHA
`f80dfd9ce6975dfaa8511470aee0890e7cfc076ccec268a5da21f95515fd83d6`.
Removing attestation forced discovery; a corrupt v4 failed closed with
`SEC validation schema mismatch`.

### FT-14 — P8/MCP provenance and no network

All supported SEC read paths were exercised from a current attested package:
`list_documents`, `get_document`, `search_document`, `read_pages`,
`list_sections`, `list_tables`, `get_table`, `list_raw_facts`, `get_fact`,
`get_evidence`, and `get_validation`. Provenance replay, Registry/catalog/
validation agreement, and local-only access passed with network calls 0.
The cached P8 copy was first successful; appending to the source bytes then
failed closed as `P8_UPSTREAM_ARTIFACT_INVALID` with the source-container
hash/length mismatch. No network fallback occurred.

## 7. FT-15/FT-16 — Apple two-root exact identity gate

The two roots were independently empty before their respective fresh runs.
The current live accession was `0000320193-25-000079` in both roots. This
execution did not substitute the historical package values
`1196a354...` or `d94d8c46...`; the current complete-submission-derived
identity was independently computed in both fresh roots and compared
member-by-member.

### Root A

```text
root: D:\ffdf-p11-ft6\live-a
accession: 0000320193-25-000079
complete-submission URL: https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/0000320193-25-000079.txt
complete-submission SHA: 60f22bb90bb8e46894019fd57c27df69abd192f3f0f4183c4345d786426f3391
complete-submission length: 9392337
provenance SHA: e4079ed2fb840c2b781e1042a58470a20894b020f9c16742153a6585c28b221c
package SHA: 339ad69b637803fc7dd8f09a71b151d596c28869e0019a06e6f35e320a0ddc43
discovery state: UNAMBIGUOUS
validation: p11-sec-validation-v4 / PASS / COMPATIBLE / blocking 0 / reuse_eligible true
parser: VIRTUAL_HTML_V6, one parse on fresh ingest
research_ready: true
Registry SEC schema: 5
P8/MCP network calls: 0
```

The ticker-map source SHA was
`29e8eee5a85a68e837628b0e9623870af68db41e5427a154d17fe3b1af0a1b9a`.
The initial live run produced immutable snapshot IDs
`4e058236c140abb0f266f9103e9cbfa4721ae0bd2979af9292693c50e5e2442a` and
`7fca92c374b1c51e1787ec75f6470de22367d7a4d4f02a7b85865d5e2b0da6e0`.
The later repeat added a third current observation
`f89a47b60aa4aacc3881078ca143d474c921eaea988a0415037a7c5978b6c5e8`.

Fresh A request counts were ticker map 1, submissions 1, complete submission
1, archive index 0, archive member 0, and static/browser 0. The ingest side
performed current ticker-map/submissions discovery again, with no complete or
member download; parser count was 1.

### Root A selected member inventory and locators

The public URL base is
`https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/`.

| Relative name | Role | Document index/type/sequence | Payload start-end | Envelope | Length | Member SHA |
|---|---|---|---:|---|---:|---|
| `FilingSummary.xml` | FILING_SUMMARY | 87 / XML / 89 | 6263240-6306015 | XML | 42775 | `f5e632bd6de8965a5251fd590f053553c017396f5ec75b0ddc9e475832a7c0a2` |
| `aapl-20250927.htm` | PRIMARY_DOCUMENT | 1 / 10-K / 1 | 1254-1521462 | XBRL | 1520208 | `548ae59778cf08ee0f2ee088e7ece20d947076c3c01f74d2d65db4c2777e436a` |
| `aapl-20250927.xsd` | XBRL_SCHEMA | 8 / EX-101.SCH / 8 | 1687679-1743992 | XBRL | 56313 | `e697d106fae1543535c634bede6337b8f1ecd987e7655eb91c62913900ab6335` |
| `aapl-20250927_cal.xml` | XBRL_CALCULATION | 9 / EX-101.CAL / 9 | 1744173-1897329 | XBRL | 153156 | `314091ba88cd58f392874866c19010ed9facdd643f34f0afbcf37137192c5f05` |
| `aapl-20250927_def.xml` | XBRL_DEFINITION | 10 / EX-101.DEF / 10 | 1897510-2122174 | XBRL | 224664 | `6eb3e955297ea510ceaff7331f57dc948cb439e83a634a3882f3806d6fb7434a` |
| `aapl-20250927_lab.xml` | XBRL_LABEL | 11 / EX-101.LAB / 11 | 2122350-2885981 | XBRL | 763631 | `9ec8874c0af055946d80061bd5558599c4eb2b56b21e48a4670751097d166118` |
| `aapl-20250927_pre.xml` | XBRL_PRESENTATION | 12 / EX-101.PRE / 12 | 2886164-3382226 | XBRL | 496062 | `43ce57fec893a2c2974a043198a3acc105238aaf19cb4a93ba8812d412d0ab7d` |

Every member public URL is the base above plus its relative name. The
complete-submission locator, member SHA, length, and package manifest were
replayed from the persisted source bytes.

### Root B and exact comparison

```text
root: D:\ffdf-p11-ft6\live-b
accession: 0000320193-25-000079
complete-submission URL: https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/0000320193-25-000079.txt
complete-submission SHA: 60f22bb90bb8e46894019fd57c27df69abd192f3f0f4183c4345d786426f3391
complete-submission length: 9392337
provenance SHA: e4079ed2fb840c2b781e1042a58470a20894b020f9c16742153a6585c28b221c
package SHA: 339ad69b637803fc7dd8f09a71b151d596c28869e0019a06e6f35e320a0ddc43
validation: p11-sec-validation-v4 / PASS / COMPATIBLE / blocking 0 / reuse_eligible true
research_ready: true
P8/MCP network calls: 0
```

Root B ticker-map source SHA was the same
`29e8eee5a85a68e837628b0e9623870af68db41e5427a154d17fe3b1af0a1b9a` and its
fresh snapshot IDs were
`b66245644e2c9677ebfd59a591ae9989597467fef811c66e8e31ee513c61b4a4` and
`e8e298c5649cff0add351f23bb3e5334a66302e4964a466dc221b02381a85824`.

The independent comparison receipt was `equal=true` with
`difference_fields=[]`. Exact equality covered accession, complete-submission
URL/SHA/length, provenance SHA, selected member set, every member locator
semantic field (document index, type, sequence, filename, offsets, envelope,
role, URL), every member SHA/length, and package SHA. Discovery observation
IDs/timestamps differed as expected because the roots were independent; the
source/package/provenance identity did not.

## 8. FT-17/FT-18 repeat and diagnostic isolation

### FT-17 — direct member diagnostic

The diagnostic URL was:

```text
https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm
```

Two direct 200 responses were identical, SHA
`7f44c98b2b8d4f0836aac3f151c415149df4a560c4208860a7d2ccfedf9134be`, length
1520327. Both contained the active marker `<script` and neither matched the
canonical complete-submission member payload. Package SHA, source-container
SHA, provenance file/SHA, validation, catalog, and raw package bytes were
unchanged before and after. No direct response was promoted to package input.

### FT-18 — corrected online repeat semantics

The valid rerun used `FFDF_ROOT=D:\ffdf-p11-ft6\live-a` explicitly. Its online
repeat request counts were:

```text
ticker-map=1
current submissions=1
complete submission=0
archive index=0
archive member=0
static/browser=0
```

The planner action was `REUSE_DATA`; parser reruns were 0; status network
calls were 0; P8 validation remained PASS/reuse-eligible with network calls 0.
Raw package, source container, provenance, parsed artifacts, and the prior
package identity were unchanged. The ticker snapshot count changed from 2 to
3 because current ticker discovery was intentionally repeated.

One earlier harness invocation omitted `FFDF_ROOT` and therefore used the
default project root; it was an invalid runner invocation and its result was
discarded. No FT-18 verdict was based on it, and the explicit-root rerun above
is the formal result.

## 9. FT-19 — Apple FY2025 Q3

Commands:

```text
acquire --market US --ticker AAPL --year 2025 --period Q3
ingest --market US --ticker AAPL --year 2025 --period Q3
```

The fresh root was `D:\ffdf-p11-ft6\live-q3`. The selected accession was
`0000320193-25-000073` (10-Q), package SHA
`194e409b107b8a9014d8d796396f66d602cbdee90ae1bd7681830a960f55cb9a`, source
container SHA
`83a65bbe8d3ab67e4f35769cbb56c46eb0b557c2b0890b940b2d76e59548ad87`
(length 5304776), and provenance SHA
`1136c59e7b4495f3fae68c73fe1d9ca624c2f5efeb8c468deb1212671aabd285`.
The exact complete-submission URL was
`https://www.sec.gov/Archives/edgar/data/320193/000032019325000073/0000320193-25-000073.txt`.

Combined acquire/ingest counts were ticker map 2, submissions 2, complete
submission 1, archive index 0, archive member 1, and other/static 0. The
ingest action was `PARSE_LOCAL` after fresh acquisition and parser count was 1.
Validation was `p11-sec-validation-v4 / PASS / COMPATIBLE / blocking 0`,
`research_ready=true`, and P8/MCP exercised all read paths with network 0.
The document summary was 40 pages, 38 tables, 769 raw facts, 769 evidence
records, and validation issues 0. The selected package had seven members,
including the primary `aapl-20250628.htm`, XSD, FilingSummary, calculation,
definition, label, and presentation members.

The first live harness invocation lacked the active worktree `PYTHONPATH` and
exited with `ModuleNotFoundError` before the formal root was created. The
explicit-source-path rerun above is the formal FT-19 result; no production or
tracked test file was changed.

## 10. FT-20 — Toyota FY2025 20-F and 6-K guard

Commands:

```text
acquire --market US --ticker TM --year 2025 --period FY
ingest --market US --ticker TM --year 2025 --period FY
acquire --market US --ticker TM --year 2025 --period Q1
```

The fresh root was `D:\ffdf-p11-ft6\live-toyota`. FY selected accession
`0001193125-25-142326`, CIK `0001094517`, form `20-F`, report period
`2025-03-31`, package SHA
`8195c504b7aa9c1ce981dfafd39c73bd799029b6ad14da32855ba7ea3b762e4b`, source
container SHA
`b1564b0cd42563fec3fe0fa838b57f3c1c01bb01a48ee445104f211f098ea7e0`
(length 44152781), and provenance SHA
`f02b070a4e59e621db58e388a31c8209c8c6ccf59f5389be4ee6888c6a4ef9f1`.
The complete-submission URL was
`https://www.sec.gov/Archives/edgar/data/1094517/000119312525142326/0001193125-25-142326.txt`.

FY combined counts were ticker map 2, submissions 2, complete submission 1,
archive index 0, archive member 1, and other/static 0. Ingest was
`PARSE_LOCAL`, parser count 1, validation was
`p11-sec-validation-v4 / PASS / COMPATIBLE / blocking 0`, and
`research_ready=true`. P8/MCP network attempts were 0; the document summary
was 182 pages, 419 tables, 3373 raw facts, 3373 evidence records, and 0
validation issues.

The Q1 guard observed current submissions containing 6-K/6-K/A but returned
controlled `P11_FILING_NOT_FOUND`; it made ticker-map 1 and submissions 1,
with archive index/member 0. Q1 Registry bindings and catalog documents were
empty. The independent FPI policy check returned
`P11_UNSUPPORTED_FPI_PERIODIC_MAPPING` with message `6-K is not automatically
mapped to a US quarterly slot`. No 6-K was guessed into a quarterly slot.

## 11. FT-21 — Kellanova current amendment conflict

Command:

```text
acquire --market US --cik 0000055067 --year 2024 --period FY
```

Ticker-map fetches were 0; current submissions fetches were 1; archive
index/member fetches were 0. The current observation was
`AMENDED_VARIANT_PRESENT`, observation SHA
`e4ae4f5684f2d84519c09ae447aab6755359978964d233f31b888fdf9be8a94d`, and
the controlled reason was `P11_AMENDED_VARIANT_PRESENT`.

| Accession | Form | Amended | Filing date | Report period |
|---|---|---:|---|---|
| `0000055067-25-000127` | 10-K/A | yes | 2025-03-07 | 2024-12-28 |
| `0001628280-25-007118` | 10-K | no | 2025-02-21 | 2024-12-28 |

An acceptance-only stale local package fixture had SHA
`142cc3d28560d5af9c22a9cddafc2821e33aa53200058c62fef24058835c7a50` and a
binding before the conflict check. After current discovery the binding
remained only as a non-published fixture, catalog slot documents were empty,
`research_ready_publication=false`, and no candidate package was acquired.

## 12. FT-22 — ISSUE-142/143/145/146 acceptance regression

Acceptance-only harness:
`D:\ffdf-p11-ft6\evidence\FT-22-source-regression.py`, final fresh root
`D:\ffdf-p11-ft6\ft22-regression-final3`, exit 0.

The independent harness verified strict history descriptor validation before
fetch, exact date semantics, source-set identity, immutable context/unit
replay, Raw Fact source binding, wrong-role and multi-root failure, and a valid
positive path. Results included:

```text
source-set calls:
  https://data.sec.gov/submissions/CIK0000320193.json
  https://data.sec.gov/submissions/CIK0000320193-submissions-002.json
malformed history fetch count: 1 (main submissions only; no history fetch)
valid inline path: PASS
context tamper: P11_RAW_FACT_SOURCE_MISMATCH
wrong-role instance: P11_FACT_SOURCE_MODE_INVALID
multi-root instance: P11_FACT_SOURCE_MODE_INVALID
valid package SHA: 533ab077476bcadb348fcaf57e677ae1f81bbfd8f0570ed9c9bc60603d8be7a0
valid source SHA: 31f9662031163a4cf2c50d096e7af0f5a8610006d9b22519c1f77e4e9bb22277
valid provenance SHA: db1641611478e383be79b03ae17791aa192f84a3a8840d5657d4c982288e83f2
```

The validation-v4 migration/revalidation, parser-count-0, corrupt-current-
validation, and no-legacy-fallback portions were independently covered by
the FT-12 and FT-13 acceptance harnesses above; no unit-test output was used
as a substitute for this FT-22 harness.

The first external FT-22 harness attempts exposed only harness-local assertion
and fixture-store path mistakes; they were corrected outside Git and rerun on
fresh roots. No production/test semantics or tracked files were changed.

## 13. FT-23 — P0-P10 and CN/HK/MCP preservation

P0-P10 command:

```text
python -m pytest -q tests/unit/acquisition tests/unit/identity tests/unit/validation tests/unit/registry tests/unit/mcp tests/unit/research tests/unit/review --basetemp D:\t\p11f6\ft23-p0p10
371 passed in 72.77s, exit 0
```

Representative accepted CN/HK/MCP smoke:

```text
python -m pytest -q tests/unit/acquisition/test_service_raw_store.py tests/unit/acquisition/test_dayu_runner_extra.py tests/unit/identity/test_models.py tests/unit/mcp/test_catalog_service.py tests/unit/mcp/test_trusted_source.py tests/unit/research/test_research_context.py --basetemp D:\t\p11f6\ft23-cnhk-mcp
85 passed in 4.61s, exit 0
```

No accepted CN/HK source or Registry semantic mutation was observed. No skip
was observed in these runs.

## 14. FT-24 — final drift and evidence integrity

The final pre-evidence commands were:

```text
git status --short --branch
git diff --check
git diff --name-status 7aac34e763b4c9caac24489eb049aa3dc6efb026..HEAD
```

Results:

```text
git diff --check: exit 0
forbidden src/tests/dependency/runtime paths in post-candidate diff: 0
candidate ancestor check: exit 0
FFDF_P11_US_DEV: ABSENT
FFDF_SEC_CONTACT_EMAIL: CONFIGURED (value not recorded)
HEAD: 4aaa4b8076546f9daa258e1827cd1a61e3eeffbf
origin/reconcile/p11-140-143-local-chain: 4aaa4b8076546f9daa258e1827cd1a61e3eeffbf
```

The complete post-candidate tracked diff before this evidence file consisted
only of the following documentation/governance paths:

```text
M  PROJECT_STATUS.md
M  design/00-design-management-index.md
A  development/214-p11-issue148-development-evidence.md
A  development/215-p11-fresh-full-exact-candidate-review-9.md
A  development/216-p11-formal-test-plan-6.md
A  development/217-p11-formal-test-execution-authorization-6.md
```

No production or test path was changed. This evidence file is the only
tracked file created for Formal Test 6. Raw harnesses, logs, live roots, and
temporary outputs remain outside Git under `D:\ffdf-p11-ft6` and
`D:\t\p11f6`.

## 15. Execution classification and stop boundary

All FT-00 through FT-24 gates passed. The final PC execution result is:

```text
EXECUTION_PASS
```

This record does not declare `ACCEPTANCE_PASS` and does not declare `P11 DONE`.

The fixed next action is:

```text
STOP FOR CHATGPT INDEPENDENT FORMAL ACCEPTANCE REVIEW 6
```
