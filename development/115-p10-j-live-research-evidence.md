# 115 — P10-J Live P8/P9 Research Run Evidence

Status: **PASS — P10-J CLOSED**

Phase:
`P10 — Codex Dynamic Research Integration`

Gate:
`P10-J — Live P8/P9 Research Run`

Amended design baseline:
`668269e87774730ade03afb4b7564256671eb31f`

Rerun authorization:
`development/114-p10-j-live-run-reauthorization.md`

Rerun authorization commit:
`da076d105564b4fca90a88560fc4571b57aaac3c`

Historical authorization:
`development/112-p10-j-live-run-authorization.md`

Historical stop:
`development/113-p10-j-live-run-stop.md`

Workspace:
`D:\\Codex\\FinancialFilingDataFoundation\\workspace\\research-runs\\p10-j`

No P10 production/test code changed during P10-J.

## 1. Primary accepted live filing

Catalog:
`workspace/mcp/p8-live-catalog.json`

Fixture:

```text
market=CN
ticker=600519
fiscal_year=2024
filing_type=ANNUAL
document_sha256=5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30
```

Accepted P8 base paths:

- P3: `workspace/live/p6-inputs/cn/p3/<document_sha256>`
- P5: `workspace/live/p6-inputs/cn/p5/<document_sha256>`
- P6: `workspace/live/p6-facts/cn-a/<document_sha256>`
- P7: `workspace/live/p7-validation/cn-a/<document_sha256>`

No filing download/reparse/re-extraction was performed.

## 2. Frozen runtime spec

File:
`workspace/research-runs/p10-j/inputs/live-cn-spec.md`

Raw identity:

```text
SPEC_RAW_SHA256=60c533dd8b1c607c23819592aebb1bfc390ec8a21f7d71a03566b7c4c63aeb91
SPEC_SIZE=1820
SPEC_BUNDLE_HASH=d8213caba81b8181c58bbfc095972c3fbf6a7280c329cbc9efccdc3510fc86c3
```

The frozen spec was verified before the live run, read completely, and reverified after the run:

```text
SPEC_VERIFY=PASS
SPEC_POST_VERIFY=PASS
```

The spec required:

- exact accepted filing identity;
- P8 validation state;
- one target reviewed RawFact;
- linked Evidence/table/page;
- raw period separate from effective reviewed period;
- P9 resolution/overlay identity;
- explicit REVIEW_REQUIRED usability boundary;
- explicit non-canonical reuse;
- no raw numeric mutation;
- fresh evidence-ledger validation;
- final `COMPLETE` only when all required fields were supported.

## 3. P10-ISSUE-007 stopped first attempt

The first live attempt copied an existing P9 live review store into a new isolated path.

Accepted:

`load_resolved_snapshot(...)`

correctly rejected that copied state with:

`review manifest differs from deterministic manifest`

Root cause:

accepted P9 `review_manifest.json` binds project-relative `review_dir`.

The run stopped before any COMPLETE verdict.

No source P9/P8 state was mutated.

Design-First correction:

- design/24, design/25, acceptance/38 amended;
- amended baseline `668269e...`;
- isolated P9 store must be built at its final path through accepted P9 APIs;
- copy/move + manifest-edit workarounds forbidden.

## 4. Isolated P9 construction

Final isolated review root:

`workspace/research-runs/p10-j/review-v2`

Accepted P9 flow:

```text
prepare_review_overlay
→ load_review_base / inspect tasks
→ submit_resolution
→ materialize_resolved_view
→ load_resolved_snapshot
```

Prepared manifest correctly persisted:

`workspace/research-runs/p10-j/review-v2/<document_sha256>`

Base:

```text
base_validation_status=REVIEW_REQUIRED
base_compatibility_status=COMPATIBLE
review_task_count=1
supported_task_count=1
```

Generated task:

```text
reason_code=RAW_PERIOD_COVERAGE_LOW
reviewability=SUPPORTED
supported_actions=SET_PERIOD
review_task_id=59ebac57b61f85d922a66424fa3468e81fdb0773c0bd25c6c350085058b555a2
required_evidence_types=P5_CELL|P6_EVIDENCE
```

Only the frozen-spec-required target period was resolved.

## 5. Evidence-grounded isolated P9 resolution

Target RawFact:

`9b3e2e441e6730c0f3c979816dd764dcb4bf70e6cde16caae9e3897733b9a015`

Raw P8 values:

```text
raw_metric_name=营业收入
raw_value=45,775,517,043.29
parsed_numeric_value=45775517043.29
raw_period_label=null
page_no=6
table_id=9d9d4afeb104cbcfade4847423919c7b9c60be2efef1011bb4651beb11268075
evidence_id=70635d645488a336a0faa32813a497cd48d09c8879a1b5ae68810c6bb3a779c8
```

P5 evidence cell:

```text
cell_id=561a43ea9a394dc90fedd52f8a14d279d22147ba52ccabf9a9c61847ec074d0b
table_id=9d9d4afeb104cbcfade4847423919c7b9c60be2efef1011bb4651beb11268075
page_no=6
text=2024
```

Submitted isolated action:

```text
action=SET_PERIOD
target=FACT_FIELD / period
value=2024
affected_fact_count=1
```

New isolated resolution:

`a315e963a7b41a3af54ea3eeb7f0c010083642aab364474b906d3e1039e967b2`

New isolated overlay:

`94391a32568c2d48fd6fe82bab5042568361ce46685e13ba5df41f542776dc1e`

Accepted P9 loader validated the materialized snapshot.

Resolved target fact:

```text
raw_period_label=null
effective_period_label=2024
raw_value=45,775,517,043.29
parsed_numeric_value=45775517043.29
raw_metric_name=营业收入
```

Therefore raw numeric/metric state remained unchanged.

## 6. P8 live calls

The reasoning host selected the following P8 calls according to the frozen live spec:

```text
ffdf_list_documents
ffdf_get_document
ffdf_get_validation
ffdf_get_fact
ffdf_get_evidence
ffdf_get_table
ffdf_read_pages
```

Recorded call count:

`7`

The selected page text directly contains the relevant quarterly revenue row on page 6.

P8 document state:

```text
validation_status=REVIEW_REQUIRED
compatibility_status=COMPATIBLE
blocking_issue_count=0
failure_issue_count=0
review_issue_count=1
warning_issue_count=2
reuse_eligible=false
```

No P8 mutation occurred.

## 7. Research context

Final P10 context binds the isolated P9 root:

```text
research_context_id=3b301ee303dfecfea77e45900cdcc996d5a66c04ff24679383097c6b65dfa47c
spec_bundle_hash=d8213caba81b8181c58bbfc095972c3fbf6a7280c329cbc9efccdc3510fc86c3
p8_catalog_sha256=e493f2f6a951007c1e5ac932268796d35d33386760f4503d48ff0a7f7a148cdc
p9_review_root=workspace/research-runs/p10-j/review-v2
```

## 8. Evidence ledger

The final ledger contains exactly two claims:

1. `raw_fact_claim / P8_RAW_DIRECT`
   - document
   - page 6
   - source table
   - exact RawFact
   - exact Evidence

2. `reviewed_period_claim / P9_DURABLE_RESOLVED`
   - document
   - isolated resolution ID
   - isolated overlay-set hash

Fresh P10 provenance validation:

```text
status=PASS
entry_count=2
validated_claim_keys=raw_fact_claim|reviewed_period_claim
```

Ledger SHA256:

`2fd715ae8e6d8fad435ca67dd59cda9968c29321112966d606e892ec90c0ce3c`

Validation SHA256:

`f3b62c90abc43ea341f1b8f3f5e6c7c7609fcbab7369cef853d00dc3c54e1129`

## 9. Final research output

Output:
`workspace/research-runs/p10-j/output/research-output.json`

SHA256:

`3f8064b8a751c478a00cc7eb024a06ee514ec7680cb59033c8314c2925062fcb`

Final required behavior:

```text
run_status=COMPLETE
base_validation_status=REVIEW_REQUIRED
base_compatibility_status=COMPATIBLE
raw_period=null
effective_period=2024
resolved_validation_status=REVIEW_REQUIRED
resolved_reuse_eligible=false
review_required_data_usable_for_claim=true
canonical_reuse_eligible=false
raw_numeric_value_changed=false
evidence_ledger_validation=PASS
```

This proves:

- `REVIEW_REQUIRED != DATA_UNUSABLE`;
- the specific claim is supportable by exact evidence;
- unrelated unresolved review state does not make the supported claim unusable;
- document-level canonical reuse remains false;
- P9 effective period does not rewrite the P8 raw numeric value.

## 10. P9 final state

Isolated snapshot:

```text
active_resolution_count=1
resolved_validation_status=REVIEW_REQUIRED
resolved_reuse_eligible=false
unresolved_review_issue_count=1
```

No unrelated issue was force-closed to obtain COMPLETE.

Isolated P9 result SHA256:

`8f8dbcf3df9afd3814cbcb05de620f2c2a6b21aad2090f9e9c0a1c13a0315e10`

Isolated P9 store:

```text
FILE_COUNT=7
MANIFEST_SHA256=19ee3f6b92704c2c6c4ee90ec2375673d1be5f4eae35c3f596af951228ac536a
```

## 11. Accepted-base immutability

Accepted P8 base before:

```text
FILE_COUNT=13
MANIFEST_SHA256=80d0d84ea1e9349ac18d6446bf7380a2a9cc62bd28bcd552c9759cca2b0cb6ad
```

Accepted P8 base after:

```text
FILE_COUNT=13
MANIFEST_SHA256=80d0d84ea1e9349ac18d6446bf7380a2a9cc62bd28bcd552c9759cca2b0cb6ad
P8_UNCHANGED=True
```

Source P9 live review before:

```text
FILE_COUNT=7
MANIFEST_SHA256=e3cde7918a5225e6cc541db949464783a06e5989f9d65bcbf68cac8abc181371
```

Source P9 live review after:

```text
FILE_COUNT=7
MANIFEST_SHA256=e3cde7918a5225e6cc541db949464783a06e5989f9d65bcbf68cac8abc181371
P9_SOURCE_UNCHANGED=True
```

Only isolated:
`workspace/research-runs/p10-j/review-v2`
was mutated by authorized P9 operations.

## 12. Artifact identities

```text
live-cn-spec.md
  60c533dd8b1c607c23819592aebb1bfc390ec8a21f7d71a03566b7c4c63aeb91

research-output.json
  3f8064b8a751c478a00cc7eb024a06ee514ec7680cb59033c8314c2925062fcb

evidence-ledger.json
  2fd715ae8e6d8fad435ca67dd59cda9968c29321112966d606e892ec90c0ce3c

provenance-validation.json
  f3b62c90abc43ea341f1b8f3f5e6c7c7609fcbab7369cef853d00dc3c54e1129

isolated-p9-result.json
  8f8dbcf3df9afd3814cbcb05de620f2c2a6b21aad2090f9e9c0a1c13a0315e10

p8-calls-v2.json
  ce1e64755129d83eb6ee15016cfe1e7649cda4ea551ab840c5e2ec92eb45b277

context-v2.json
  e9b917606a713a50a175729280fe2418c693f02e6555222425b5df4e6de7c91a
```

## 13. Branch state

During final run completion:

```text
HEAD=da076d105564b4fca90a88560fc4571b57aaac3c
REMOTE=da076d105564b4fca90a88560fc4571b57aaac3c
```

Final tracked/untracked status before evidence creation:

```text
## design/p10-dynamic-research-integration...origin/design/p10-dynamic-research-integration
```

All run artifacts are under ignored project-local workspace.

## 14. Verdict

# PASS — COMPLETE

P10-J Live P8/P9 Research Run is closed.

A separate explicit authorization may begin:

`P10-K — Negative Capability Gates`

P10-K and later remain closed until separately authorized.

Research MCP production, Semantic Resolver production, and P11 production remain closed.
