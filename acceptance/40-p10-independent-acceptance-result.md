# 40 — P10 Independent Acceptance Result

Status: **PASS — P10-N CLOSED**

Phase:
`P10 — Codex Dynamic Research Integration`

Gate:
`P10-N — Independent Acceptance`

Exact accepted candidate:

`183ca5dc89a606715a3e352bf92a235f7aa31fad`

Detached acceptance worktree:

`D:\\Codex\\FinancialFilingDataFoundation\\worktrees\\acceptance\\p10-n-183ca5d`

Fresh mutable acceptance root:

`D:\\Codex\\FinancialFilingDataFoundation\\workspace\\p10-n\\183ca5d`

## 1. Historical execution stop

The first execution attempt against the same exact candidate stopped because the mutable live P9 submission metadata did not match the frozen acceptance package.

Stop record:

`development/138-p10-n-execution-stop.md`

Fresh rerun authorization:

`development/139-p10-n-rerun-authorization.md`

The failed mutable root was preserved whole at:

`workspace/scratch/p10-n-183ca5d-stopped-metadata-attempt1`

No result from that stopped attempt was reused.

Candidate/package/design were unchanged.

## 2. Frozen package identity

Exact Git-blob identities from candidate `183ca5d...`:

```text
acceptance/39-p10-final-acceptance-freeze.md
  size=15993
  sha256=46156307c295c964f719baf3c979874ca9d714dce7b87c63c0a2aaca81d8e681

acceptance/p10_independent_acceptance_harness.py
  size=24625
  sha256=dba3e7b0cc2e85e9eb65f003421ecd0a19229632b93905d9669421e74d36b9e7

acceptance/p10-base-immutability-manifest.json
  size=12413
  sha256=ae176a49858caabb45e525fbeb9b99eec23e4b5f649dfa584ebe4656c2dba003

acceptance/p10-fixtures/manifest.json
  size=1227
  sha256=345a00660a5e6150d2c1e547133cb9eb28aa39987d77010ce57f8f70f3d6cc3a
```

Fixture/base identity source:

`GIT_BLOB`

P10-G integration Git-blob SHA256:

`ef10406c9957f7a68a9af001c913deef0a057e166100a2d852c0c8fcd2c46296`

## 3. Fresh precheck

Report:

`workspace/p10-n/183ca5d-precheck-rerun.json`

SHA256:

`b8f170113ca3ab09763c7cc00d7b7e8eb552238be2c34c7315e1ca42ab4ebc3c`

Result:

`PASS`

Verified:

- exact detached candidate source binding;
- 47-file immutable base;
- 8 frozen fixtures from exact Git blob bytes;
- source/test/integration/core-design drift = none;
- P8 exact 11 tools;
- P8 runtime lock unchanged;
- P9 public policy/schema contract unchanged;
- main runtime external MCP SDK absent;
- forbidden P10 production surface absent;
- future Research MCP / Semantic Resolver / P11 production absent;
- critical CLI subprocess matrix PASS;
- performance gates PASS.

## 4. Fresh focused / full regression

P10 research suite:

```text
136 passed in 20.80s
exit=0
```

Evidence:

`workspace/p10-n/183ca5d/results/focused-tests.txt`

SHA256:

`b4a7a1d31e8ee67629378a67b63376dead236d47659c933507eb861c5f6381bf`

Full P0-P10 unit suite:

```text
444 passed in 47.05s
exit=0
```

Evidence:

`workspace/p10-n/183ca5d/results/full-tests.txt`

SHA256:

`0f030dda401c355ca24c8885ce346ba0f08475c16bf5e97b013136025c87633d`

## 5. Dynamic Spec A

Frozen raw spec SHA256:

`3c825c79422edac120f45b5c196d4a7e5105298d31df609f6ae3dab1abf09121`

Spec bundle hash:

`6bcf7a18a0bf55a40385dbe2d91825c2c31bd39344e859dd655feaa4659c451a`

Research context ID:

`22f0dcf14301f1bdbae53c39b2080c2b473fe50e28f13c9cb7b7fd95bcb44075`

Selected P8 tools:

```text
ffdf_list_documents
ffdf_list_tables
```

Ledger validation:

`PASS`

Result SHA256:

`275c61c5ed85e1e23c9b843a96c9d5f85da971f115835fdcf7d3c93d27110cc3`

## 6. Dynamic Spec B

Frozen raw spec SHA256:

`abc8ecb590d87945d31969584ee8c0c530f43c25d9b90d3f8a25bbfd81a97f07`

Spec bundle hash:

`ba07145dc82bab87d4bcd836a439d6c376b2306564b94c332b8a73ca39ced7cb`

Research context ID:

`85d9f8c433f71234888d30cf64e819cddf9f4337e3f9f631889d6b9fbeb6ff33`

Selected P8 tools:

```text
ffdf_list_documents
ffdf_get_fact
ffdf_get_evidence
```

Ledger validation:

`PASS`

Result SHA256:

`713fed09104ee37896bddbe0b4c2812bb3613b0762ff8250d5e39aff184e08d7`

Dynamic requirements:

```text
spec_bundle_hashes_differ=true
selected_tool_sets_differ=true
same_P10_production_candidate=true
```

## 7. Fresh live CN COMPLETE run

Filing:

```text
market=CN
ticker=600519
fiscal_year=2024
document_sha256=5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30
```

Target RawFact:

`9b3e2e441e6730c0f3c979816dd764dcb4bf70e6cde16caae9e3897733b9a015`

Fresh isolated P9 review root:

`workspace/p10-n/183ca5d/review-live`

It was created at its final path through accepted P9 APIs. No existing P9 store was copied or relocated.

Frozen submission metadata was used exactly:

```text
reviewer_type=CODEX
reviewer_id=p10-independent-acceptance
reviewed_at=2026-11-04T12:00:00+09:00
justification=P10 Independent Acceptance isolated review: same-table P5 cell explicitly identifies period 2024 for the target raw fact.
```

Fresh isolated resolution ID:

`acf0c1eb48a196818c04c346468b363e91d83b78b5a8e0a3ecd482b0e661aff1`

Fresh overlay-set hash:

`c674530a7dbb472f6e3a40e9b0d70aeb5697db126dd7928c0d9337c632969a4b`

Final behavior:

```text
run_status=COMPLETE
base_validation_status=REVIEW_REQUIRED
base_compatibility_status=COMPATIBLE
raw_period=null
effective_period=2024
raw_metric_name=营业收入
raw_value=45,775,517,043.29
parsed_numeric_value=45775517043.29
resolved_validation_status=REVIEW_REQUIRED
resolved_reuse_eligible=false
review_required_data_usable_for_claim=true
canonical_reuse_eligible=false
raw_numeric_value_changed=false
evidence_ledger_validation=PASS
```

Live research context ID:

`2a986b7f398104852f4bd988f273c7deb3488cf4fbb4892018121315ca1040fb`

Live spec bundle hash:

`350441480780538b222fbc2a4c73a36ab63800b9694407d7b61904084342c996`

Artifacts:

```text
live.json
  sha256=10610a736b72223e9a1fd9de24e6afc3a3ec7d26dba026674c99d852d61b9f82

live-ledger.json
  sha256=24609fdf1d30e02d517adde5e10df94b5a6bbde0fef4acd1e6e92ca38375b740

live-validation.json
  sha256=f73c178ae0068a2d4e74ee7d14ad79871c13728761ee4817c6daa2c66f8b0328
```

## 8. Fresh negative capability gates

Exact outcomes:

```text
K1=P10_DATA_PREPARATION_REQUIRED
K2=P10_VISUAL_CAPABILITY_REQUIRED
K3=P10_UPSTREAM_INVALID
K4=P10_RESEARCH_SPEC_CHANGED
K5=P10_REVIEW_UNRESOLVED
```

Safety boundaries:

```text
k1_download_attempted=false
k2_guessed_visual=false
k3_silent_raw_fallback=false
k4_silent_refresh=false
k5_guessed_semantic=false
```

K3 proved valid durable provenance PASS before tampering only the isolated negative snapshot.

Negative result SHA256:

`c5ac97a078f34fcbabead830d60231e90647aff67de15c3327b4d3c70d4277be`

## 9. Fresh postcheck

Report:

`workspace/p10-n/183ca5d-postcheck.json`

SHA256:

`8ee9c1806e94fc04b4b3267e9f137aaf6a4d6b4bd5939170312a674cce8a980a`

Result:

`PASS`

Postcheck independently verified:

- immutable base 47/47 PASS after all acceptance runs;
- dynamic Spec A/B hashes differ;
- dynamic tool sets differ;
- both dynamic ledgers PASS;
- live run COMPLETE;
- live ledger PASS;
- raw numeric unchanged;
- REVIEW_REQUIRED claim usability boundary;
- non-canonical reuse boundary;
- K1-K5 exact reason codes;
- no silent fallback/refresh/guessing;
- no hidden reasoning artifact names.

## 10. Detached candidate status

Final detached acceptance state:

```text
HEAD=183ca5dc89a606715a3e352bf92a235f7aa31fad
## HEAD (no branch)
```

The detached candidate remained clean and immutable.

No P10 production/test/design/package change was made during Independent Acceptance.

## 11. Verdict

# PASS

P10-N Independent Acceptance is closed.

This PASS authorizes **no automatic main integration**.

A separate explicit authorization is required for:

`P10-O — Closeout`

P11 production, Research MCP production, and Semantic Resolver production remain closed.
