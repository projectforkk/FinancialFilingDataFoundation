# 211 — P11 Independent Formal Acceptance Review 5

Status: **FORMAL_ACCEPTANCE_NOT_PASSED**

This is the independent ChatGPT acceptance review of Formal Test Execution 5.

The Acceptance/Test Agent reported `EXECUTION_PASS`, but independent acceptance
does not accept that execution as sufficient for production acceptance.

No main merge or P11 DONE is authorized.

## 1. Exact authority

Repository:

`projectforkk/FinancialFilingDataFoundation`

Authoritative remote lineage:

`reconcile/p11-140-143-local-chain`

Frozen production candidate:

`f1cc76889718e06fdbdc46926e2b207b740a96e3`

Design 39:

`fad6ee7512ec1f2f3da0c9a24c646959b2f45541`

Fresh Full Exact-Candidate Review PASS:

`56d884f5adfc4f5044f3970c3e43180b658c74a8`

Formal Test Plan 5:

`4e20ca77889b9e2f35b470c99ee90c45c7853994`

Formal Test Execution 5 authorization:

`b46cbd0aaaacd937800d611e7a565f70362e34b8`

Formal Test evidence:

`development/210-p11-formal-test-evidence-5.md`

Evidence commit:

`134b09e51fc5194e5ec42768f0ac8de7c1e5aebe`

The evidence commit is a single documentation-only child of the execution
authorization. No production/test byte changed during Formal Test 5.

## 2. Evidence that is accepted

The following Formal Test 5 results are accepted as useful evidence:

- candidate freeze / documentation-only post-candidate history;
- deterministic regression:
  - ISSUE-147 focused = 10 passed;
  - US SEC = 263 passed;
  - MCP = 93 passed as recorded by the executor;
  - P0-P10 = 371 passed;
  - full unit = 793 passed;
  - compileall PASS;
  - git diff --check PASS;
- historical-format legacy ticker snapshot without `snapshot_id`;
- newest-only cached ticker behavior and no stale fallback;
- explicit-CIK zero ticker-map fetch;
- live Apple ticker observation identity now survives acquire → ingest;
- validation-v3 / REVALIDATE_LOCAL regression;
- Apple Q3;
- Toyota 20-F and quarterly 6-K guard;
- Kellanova amendment conflict;
- CN/HK/P0-P10 preservation;
- P8/MCP no-network evidence.

These results do not by themselves resolve the acceptance blockers below.

## 3. Acceptance blocker A — Plan-208 FT-02 execution mismatch

Formal Test Plan 5 FT-02 required an acceptance-only ISSUE-147 observation
identity proof covering all of the following:

1. same source bytes/SHA + different retrieval times → different snapshot IDs;
2. both observation files coexist;
3. no source drift for distinct retrieval observations;
4. exact canonical snapshot-ID recomputation;
5. same snapshot ID + different canonical payload → `P11_SOURCE_DRIFT`;
6. invalid or timezone-naive `retrieved_at` →
   `P11_TICKER_SNAPSHOT_INVALID`;
7. source-byte tamper fails;
8. derivative tamper fails;
9. current observation path identity mismatch fails.

The evidence section labeled FT-02 instead records:

```text
FT-02-history-harness.py
descriptor_cases=15
malformed_history_fetch_count=0
online_calls=2
reconstructed_source_documents=2
```

That is primarily the history-inventory/source-set acceptance work from the
older formal cycle, not the frozen Plan-208 FT-02 acceptance-only matrix.

Other Formal Test 5 gates and unit tests prove some ISSUE-147 properties, but
the evidence does not independently demonstrate all FT-02 requirements.

In particular, the formal evidence does not provide an acceptance-only receipt
for:

- invalid/timezone-naive `retrieved_at`;
- current observation path identity mismatch;
- complete canonical snapshot-ID recomputation matrix.

Therefore:

```text
FT-02:
NOT SUFFICIENTLY EXECUTED AS FROZEN

FORMAL EXECUTION EVIDENCE:
INCOMPLETE RELATIVE TO PLAN 208
```

This alone prevents Formal Acceptance PASS.

## 4. Acceptance blocker B — immutable package contradiction

Formal Test 5 FT-10A compares the same Apple FY2025 accession and the same
primary archive member URL across two formal cycles.

Old primary member:

```text
relative_name = aapl-20250927.htm
bytes = 1520312
sha256 = 2e9a48b29574153c8b11f8d070f0198bbad8d53444570e6cefdaf68578f15066
```

Formal Test 5 primary member:

```text
relative_name = aapl-20250927.htm
bytes = 1520327
sha256 = 7f44c98b2b8d4f0836aac3f151c415149df4a560c4208860a7d2ccfedf9134be
```

The same evidence states:

- member set unchanged;
- roles unchanged;
- every non-primary member unchanged;
- the only primary difference is an embedded script path at the end of the
  same official URL;
- 81 byte positions differ;
- length changes by 15 bytes.

Design 26 is explicit:

```text
package_sha256 identifies the immutable member-byte set
member bytes are immutable
a source re-fetch that yields changed bytes for the same SEC archive member
is SOURCE_DRIFT, never silent overwrite
```

Therefore the FT-10A acceptance rule cannot simply classify changed primary
member bytes as an acceptable official-byte change.

Formal Test Plan 5's allowance for an "explainable current official-byte/member
drift" was too permissive relative to the higher Design-26 authority.

## 5. Independent SEC source check

The SEC EDGAR Filer Manual, Volume II, section 5.2.2 states that HTML documents
included in an EDGAR submission may not contain active content, explicitly
including `<SCRIPT>`.

It also states that EDGAR suspends submissions containing such active content.

Official reference:

`https://www.sec.gov/files/edgar/filermanual/efmvol2-v76-d.pdf`

Relevant section:

`5.2.2 HTML / page 5-14`

This means the randomized embedded script path observed by Formal Test 5 cannot
be treated, without further proof, as ordinary filer-submitted Apple filing
content.

The most likely boundary is:

```text
filed archive member bytes
!=
delivery-layer HTTP response bytes after SEC/security infrastructure handling
```

The current acquisition implementation stores the direct HTTP response body as
the immutable package member body.

That makes delivery-layer byte variation part of `member_sha256` and therefore
part of `package_sha256`.

This violates the current immutable-package contract when the delivery layer
changes bytes without a filing/amendment change.

## 6. New blocking issue

```text
P11-ISSUE-148
SEC ARCHIVE MEMBER DELIVERY BYTES ARE NOT PROVEN TO BE STABLE FILED MEMBER BYTES
```

Blocking facts:

- same accession;
- same relative member name;
- same archive URL;
- no amendment;
- non-primary members unchanged;
- primary raw response changes only in randomized embedded script material;
- package SHA changes because package identity includes raw member SHA/length.

The correction must establish an authoritative stable filed-member byte source
or an equally strong deterministic provenance boundary before those bytes are
allowed to define `member_sha256` and `package_sha256`.

Do not solve this by silently accepting changed bytes.

Do not solve this by weakening `SOURCE_DRIFT`.

Do not blindly strip arbitrary filing content without a frozen design proving
why the removed bytes cannot be filer-submitted filing bytes.

## 7. Required design work before development

A new design correction must decide and freeze:

1. what exact byte stream is the authoritative immutable SEC filing member;
2. how transport/delivery-layer bytes are distinguished from filed bytes;
3. whether the canonical source is the archive member response, the complete
   dissemination submission, another SEC-native immutable representation, or a
   deterministic verified extraction from one of those sources;
4. how source URL and provenance are represented if bytes are extracted from a
   container source;
5. whether package/member schema or Registry provenance must evolve;
6. how legacy P11 packages remain readable/auditable;
7. how a genuine filed-member source drift is detected;
8. how dynamic delivery-layer script/security material is detected and handled
   without executing or trusting it;
9. how Apple FY2025 reproduces stable member/package identity across independent
   fresh acquisitions.

The correction must also restore the missing FT-02 acceptance-only matrix in the
next Formal Test plan.

## 8. Lifecycle verdict

```text
FORMAL TEST EXECUTOR RESULT:
EXECUTION_PASS

CHATGPT INDEPENDENT FORMAL ACCEPTANCE REVIEW 5:
NOT_PASSED

FORMAL ACCEPTANCE:
NO

ISSUE-147:
FIXED / REGRESSION PRESERVATION

ISSUE-148:
OPEN / BLOCKING / DESIGN CORRECTION REQUIRED

CANDIDATE f1cc7688:
HISTORICAL REVIEW_PASS / FORMAL ACCEPTANCE NOT PASSED

MAIN MERGE:
NOT AUTHORIZED

P11 DONE:
NO
```

The next lifecycle action is design work for ISSUE-148. Development is not yet
authorized.
