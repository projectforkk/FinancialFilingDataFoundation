# 196 — P11 Review 5 Development Authorization

Status: **DESIGN_FREEZE_PASS / DEVELOPMENT_AUTHORIZED**

This record authorizes one coherent P11 Review 5 repair implementation. It is
not a Formal Test Plan, Formal Acceptance, main-merge authorization, or P11 DONE
record.

## 1. Exact design baseline

Repository:

`projectforkk/FinancialFilingDataFoundation`

Branch:

`reconcile/p11-140-143-local-chain`

Exact approved design freeze:

`70353788d0b6188e757e24b10b0883b0a9a057dd`

Previous production candidate:

`a65723c3cf17bbccf10748e2c671671a2c7dfb1b`

Review lineage:

- `development/192-p11-fresh-full-exact-candidate-review-5.md`
- `development/193-p11-design-freeze-review-result.md`
- `development/194-p11-design37-final-freeze-review-result.md`
- `development/195-p11-validation-v3-persistence-design-review.md`

Final design authority:

- `design/26-p11-sec-provider-design.md`
- `design/27-p11-implementation-plan.md`
- `design/32-p11-us-scope-reopening.md`
- `design/33-p11-post-acceptance-design-correction.md`
- `design/34-p11-explicit-6k-scope-correction.md`
- `design/35-p11-repair-140-143-design-correction.md`
- `design/36-p11-review5-trust-boundary-correction.md`
- `design/37-p11-review5-freeze-consistency-and-raw-fact-binding.md`

Verdict:

```text
DESIGN_FREEZE_PASS
DEVELOPMENT_AUTHORIZED
```

Any new design ambiguity requires STOP before implementation continues.

## 2. Authorized development scope

Implement only the current Review 5 repair scope:

```text
ISSUE-142 residual history-inventory validation
ISSUE-143 immutable source-node replay
ISSUE-145 Raw Fact/source semantic binding
validation-v3 versioned persistence and migration
```

ISSUE-140 and ISSUE-141 are already fixed and require regression preservation
only. ISSUE-144 is governance-only and has no production implementation.

Do not silently reopen historical ISSUE-123..139.

## 3. Frozen version contract

```text
SEC_DISCOVERY_SCHEMA = p11-sec-discovery-v1
VIRTUAL_HTML_NORMALIZER_VERSION = VIRTUAL_HTML_V6
SEC_ARTIFACT_SCHEMA = p11-sec-artifacts-v2
SEC_VALIDATION_SCHEMA = p11-sec-validation-v3
SEC_REGISTRY_SCHEMA_VERSION = 4
```

Raw Fact/source semantic mismatch reason:

```text
P11_RAW_FACT_SOURCE_MISMATCH
severity = BLOCKING
```

No implementation-time version or reason-code invention is authorized.

## 4. ISSUE-142 implementation

The current submissions `filings.files` inventory must fail closed.

Required behavior:

- absent `filings.files` means valid empty history inventory;
- present `filings.files` must be a list;
- every descriptor must be validated before any history fetch;
- every descriptor must be an object;
- `name` must be a non-empty string and pass the safe relative-name policy;
- duplicate normalized names block;
- malformed descriptors must never be silently skipped;
- `filingFrom` / `filingTo` are optional;
- a present non-empty range value must be a string matching exact
  `YYYY-MM-DD` and a real calendar date;
- no `str()` coercion, `[:10]` truncation, or trailing-garbage acceptance;
- `filingFrom > filingTo` blocks;
- missing range values remain conservative include;
- only valid `filingTo < cutoff` proves irrelevance;
- no upper filing-date cutoff;
- online discovery and observation reconstruction use the same selector.

The fixture containing one valid/selectable descriptor plus one malformed
descriptor must prove zero history fetches before the blocking error.

## 5. ISSUE-143 implementation

P7 must independently replay source semantics from immutable package bytes.

### INLINE_XBRL_PRIMARY

Prove:

- exactly one primary member;
- authentic supported Inline XBRL exists in that member;
- every fact/evidence row is sourced from it;
- the exact fact locator resolves to an authentic Inline fact;
- persisted `context_ref` equals source-node `contextRef`;
- persisted `unit_ref` equals source-node `unitRef`;
- referenced context/unit resolve in the same immutable primary member;
- reconstructed context/unit semantic payload equals the persisted payload;
- no other package member can satisfy context/unit resolution.

### XBRL_INSTANCE_PRIMARY

Scan all package member bytes for authentic XBRL instance roots, not only
members already labeled `XBRL_INSTANCE`.

Require exactly one authentic instance root and require its package role to be
`XBRL_INSTANCE`. Authentic instance bytes under a conflicting role are
blocking.

For every logical XML fact, source-node context/unit references and reconstructed
payloads must equal the persisted values and resolve within the same authentic
instance.

### NO_STRUCTURED_FACTS

Require both fact count and fact-evidence count to be zero.

## 6. ISSUE-145 implementation

For every logical Raw Fact, replay the authoritative source fact from immutable
member bytes and the exact fact locator.

Validate the deterministic source-fact projection frozen by Design 37,
including where applicable:

- source member;
- locator;
- raw QName / raw metric identity;
- logical raw value;
- fact kind;
- contextRef / unitRef;
- decimals / precision / scale / sign / format / nil;
- continuation semantics;
- hidden/source visibility;
- deterministic numeric candidate;
- context/unit semantic payload.

Fact and Evidence must agree on fact identity, source member, source locator,
raw value, fragment hash, and continuation fragments.

Any Raw Fact/source replay semantic mismatch uses:

`P11_RAW_FACT_SOURCE_MISMATCH`

and is blocking.

Validation must not mutate or repair the persisted Raw Fact.

## 7. Validation-v3 persistence implementation

Current validation identity is:

`package_sha256 + SEC_VALIDATION_SCHEMA`

Current v3 path is exactly:

```text
workspace/ingest/us/p7/
  <package_sha256>/
    p11-sec-validation-v3/
      validation.json
      issues.jsonl
```

Historical flat v2 files at
`p7/<package_sha256>/validation.json` and `issues.jsonl` are read-only
historical artifacts and must remain byte-for-byte unchanged.

Implement one shared deterministic current-validation path resolver used by:

- US ingest;
- US reuse;
- US CLI reusable-artifact planning;
- P8 US loading;
- migration tests.

No current runtime fallback from missing/corrupt v3 to legacy v2 is allowed.

A compatible V6/v2 parsed artifact may be reused as local input for v3
revalidation without a parser rerun solely because validation is old.

A refreshed current v3 result must use atomic artifact replacement semantics so
no partial current validation artifact becomes visible.

No Registry schema bump is authorized.

## 8. Required development tests

Implement all focused matrices frozen by Design 37 / Design 27.

At minimum include:

### ISSUE-142

- absent/non-list `filings.files`;
- malformed/non-object descriptors;
- missing/non-string/empty/unsafe names;
- duplicate normalized names;
- non-string, malformed, trailing-garbage, invalid-calendar, reversed ranges;
- missing ranges conservative include;
- ancient irrelevant exclusion;
- late amendment inclusion;
- zero fetch before malformed-inventory rejection;
- online/P7 selected-source-set equality.

### ISSUE-143

- valid Inline and instance chains;
- context_ref tamper;
- unit_ref tamper;
- context payload tamper;
- unit payload tamper;
- context/unit available only from another member;
- authentic instance bytes under wrong role;
- two authentic instance roots;
- DOM fact in instance mode;
- XML fact in Inline mode.

### ISSUE-145

- raw_value tamper while Evidence remains valid;
- raw_qname tamper;
- raw_metric_name tamper;
- parsed_numeric_candidate tamper;
- source-attribute tamper;
- fragment_hash mismatch;
- continuation/source_fragments mismatch;
- fact/evidence locator divergence;
- both source modes where applicable.

### Validation persistence

- legacy flat v2 hashes captured before revalidation;
- current v3 missing + v2 present denies REUSE_DATA;
- V6/v2 parsed artifact reused without parser rerun;
- v3 written only to versioned path;
- legacy v2 hashes unchanged afterward;
- v3 schema is `p11-sec-validation-v3`;
- valid v3 restores current reuse eligibility;
- missing/corrupt v3 never falls back to v2;
- CLI / ingest / P8 resolve the identical v3 artifact;
- refreshed v3 write is atomic;
- current production code no longer independently hard-codes legacy flat
  validation lookup.

## 9. Regression requirements

After focused repair tests, run the canonical development regression used for
the prior candidate, including:

- complete `tests/unit/us_sec`;
- US SEC + MCP focused suite;
- full unit suite;
- P0-P10 focused regression;
- `compileall`;
- `git diff --check`.

Preserve ISSUE-123..141 behavior and accepted CN/HK/P0-P10 boundaries.

## 10. Live developer smoke

After deterministic development regression passes, run the existing Apple
FY2025 developer smoke against the exact new candidate.

Record:

- exact candidate SHA;
- accession;
- observation SHA;
- selected history chunks / fetch count;
- package SHA;
- fact_source_mode;
- logical fact count;
- static-asset fetch count;
- P7 status/blocking count;
- research_ready;
- validation artifact path and schema;
- proof that no legacy validation-v2 bytes were modified if a migration fixture
  is exercised.

This is developer smoke, not Formal Acceptance.

## 11. Candidate and evidence discipline

Production/test implementation must be committed before development evidence.

The exact production candidate must contain implementation + tests only for the
authorized repair. No Formal Test Plan or Formal Acceptance artifact belongs in
the production candidate.

After tests/live smoke:

1. freeze exact production candidate SHA;
2. create a documentation-only development evidence commit;
3. prove candidate → evidence is documentation only;
4. stop for ChatGPT Fresh Full Exact-Candidate Review.

If implementation exposes a design conflict, STOP. Do not self-amend Design 37.

## 12. Git safety

Forbidden:

- force push / force-with-lease;
- rebase;
- history rewrite;
- `reset --hard`;
- `clean -fd` / `clean -fdx`;
- main merge;
- automatic merge/cherry-pick of the divergent `c8d8ea...` repair route.

## 13. Lifecycle boundaries

```text
FORMAL TEST PLAN:
NOT CREATED / NOT AUTHORIZED

FORMAL ACCEPTANCE:
NOT RUN

MAIN MERGE:
NOT AUTHORIZED

P11 DONE:
NO
```

Stop after development candidate + documentation-only evidence are pushed for
ChatGPT review.
