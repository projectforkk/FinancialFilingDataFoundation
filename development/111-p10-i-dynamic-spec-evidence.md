# 111 — P10-I Dynamic Spec Integration Evidence

Status: **PASS — P10-I CLOSED**

Phase:
`P10 — Codex Dynamic Research Integration`

Gate:
`P10-I — Dynamic Spec Integration`

Authorization:
`development/110-p10-i-dynamic-spec-authorization.md`

Authorization commit:
`43053d6`

P10 source production candidate:
`d8e7d81b4bb5a4f06cead9eba0e2d09884094676`

P10-G integration instruction candidate:
`3a805a8f333ac20770d6aec1c8285d93993d18fc`

Workspace:
`D:\\Codex\\FinancialFilingDataFoundation\\workspace\\research-runs\\p10-i\\fixture`

No production/tests/design changes were made during P10-I.

## 1. Fixture isolation

A synthetic accepted-style P8 fixture was copied from:

`workspace/current/p8/pytest3/focused/test_facts_and_evidence_relati0`

into the isolated P10-I workspace.

Original source fixture before-run manifest:

```text
FILE_COUNT=15
MANIFEST_SHA256=1ed59b1a5f0b15e6b43e0cd8661137ab3cd57ec80698322865b42c8b6e0d636d
```

The source fixture was not modified.

## 2. Runtime Spec A

File:

`inputs/spec-a.md`

Intent:

- first available document;
- first reconstructed table;
- output document SHA, table ID, page;
- table/page provenance only;
- no raw-fact/evidence query unless required.

Raw file:

```text
SPEC_A_RAW_SHA256=23e5fcaae2b960625580f19023c98026a40466a2a977bf3e37f09074ab0a0af1
SPEC_A_SIZE=688
```

Frozen bundle:

`8c2e86d49403f056280d344be4b39ec914d224bf7e41e38ec31d278fe3dd9797`

Research context:

`0fd8cbc0704f0af2dc349c6a7332376befe9a7a6ef694771eca4769bbcc15dc7`

The reasoning host read the entire frozen spec before selecting P8 calls.

Derived information need:
table identity + physical page.

Selected research P8 tools:

```text
ffdf_list_documents
ffdf_list_tables
```

Output:

```json
{"document_sha256":"dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd","page_no":1,"table_id":"9cd612992b2a676e7198f411cb3fad632120f44b41cbb8d0280206651a16eb31","tools_selected":["ffdf_list_documents","ffdf_list_tables"]}
```

Ledger claim:

`table_claim / P8_RAW_DIRECT`

Provenance validation:

```text
status=PASS
entry_count=1
validated_claim_keys=table_claim
```

## 3. Runtime Spec B

File:

`inputs/spec-b.md`

Intent:

- first available document;
- first RawFact;
- exact Evidence referenced by that RawFact;
- output document SHA, fact ID, raw metric name/value, evidence ID;
- no table-detail query unless required.

Raw file:

```text
SPEC_B_RAW_SHA256=a15c2b0713609c7a1133043c32e53141532a086c411b91122d19e02e64357547
SPEC_B_SIZE=775
```

Frozen bundle:

`00ccdb034ddddc48e1fb038ecae9bebf1eb9540a8406a263057c136319e417e0`

Research context:

`53ffa5ab181073a9c5d940320b6ab8452224377e061f4ff3ce490b0828d507a5`

The reasoning host read the entire frozen spec before selecting P8 calls.

Derived information need:
raw fact + exact evidence relation.

Selected research P8 tools:

```text
ffdf_list_documents
ffdf_list_raw_facts
ffdf_get_fact
ffdf_get_evidence
```

Output:

```json
{"document_sha256":"dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd","evidence_id":"2584cbaae5e129a463f004e5e9c0e3d8dbe964a095273a30a8c93171e84e55a4","raw_fact_id":"0a93b448657447cf57e2d5c812f431ddec1381631aed68602d42714264abe491","raw_metric_name":"营业收入","raw_value":"1000","tools_selected":["ffdf_list_documents","ffdf_list_raw_facts","ffdf_get_fact","ffdf_get_evidence"]}
```

Ledger claim:

`fact_claim / P8_RAW_DIRECT`

Provenance validation:

```text
status=PASS
entry_count=1
validated_claim_keys=fact_claim
```

## 4. Dynamic behavior proof

Observed:

```text
SPEC_A_BUNDLE_HASH=8c2e86d49403f056280d344be4b39ec914d224bf7e41e38ec31d278fe3dd9797
SPEC_B_BUNDLE_HASH=00ccdb034ddddc48e1fb038ecae9bebf1eb9540a8406a263057c136319e417e0
TOOLSETS_DIFFER=True
OUTPUT_SHAPES_DIFFER=True
```

Spec A selected:

`ffdf_list_documents | ffdf_list_tables`

Spec B selected:

`ffdf_list_documents | ffdf_list_raw_facts | ffdf_get_fact | ffdf_get_evidence`

No P10 production or integration instruction changed between runs.

No fixed question-id → tool mapping was used.

## 5. Post-run spec verification

After both research runs:

```text
SPEC_A_VERIFY=PASS
SPEC_B_VERIFY=PASS
```

No runtime spec byte drift occurred.

## 6. Immutability

Original historical source fixture after run:

```text
SOURCE_FILE_COUNT=15
SOURCE_UNCHANGED=True
```

Copied P8 base files:

```text
COPIED_BASE_FILE_COUNT=15
COPIED_BASE_EQUALS_SOURCE=True
```

P10-I P9 review root:

```text
REVIEW_FILE_COUNT=0
```

No P8/P9 base artifact mutation occurred.

## 7. Harness observations

Two non-product harness issues occurred and did not require design/product changes.

First, an initial Windows `cmd` quoting attempt failed before the CLI ran.

Second, a later diagnostic print of the Chinese raw metric name hit the host console CP932 encoding. The UTF-8 run artifacts had already been written and were read back successfully.

Neither issue changed P10/P8 data or validation results.

P10-I final validation used exact-candidate P10 public APIs with explicit source binding.

## 8. Branch state

Final active branch status:

```text
## design/p10-dynamic-research-integration...origin/design/p10-dynamic-research-integration
```

No tracked production/test/design file changed during P10-I execution.

## 9. Verdict

# PASS

P10-I Dynamic Spec Integration is closed.

A separate explicit authorization may begin:

`P10-J — Live P8/P9 Research Run`

P10-J and later remain closed until separately authorized.

Research MCP production, Semantic Resolver production, and P11 production remain closed.
