# Independent Acceptance Live Spec — CN 600519 FY2024

Use only the accepted FFDF local catalog and the isolated Independent Acceptance P9 review root.

Target:
- market: CN
- ticker: 600519
- fiscal year: 2024
- filing type: ANNUAL
- document_sha256: 5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30
- raw_fact_id: 9b3e2e441e6730c0f3c979816dd764dcb4bf70e6cde16caae9e3897733b9a015

Task:
1. Confirm document and P8 validation state.
2. Retrieve the target RawFact, linked Evidence, source table, and page.
3. Build the isolated P9 review store at its final acceptance path through accepted P9 APIs.
4. If supported by the generated review task and accepted evidence, resolve only the target fact period to 2024.
5. Validate the exact isolated P9 resolution and snapshot.
6. Keep raw period separate from effective reviewed period.
7. Do not alter raw metric text, raw value, or parsed numeric value.
8. Treat REVIEW_REQUIRED as not equal to DATA_UNUSABLE for this specifically supported claim.
9. Do not claim canonical reuse if resolved_reuse_eligible is false.

Required output:
- run_status
- document_sha256
- base_validation_status
- base_compatibility_status
- raw_fact_id
- raw_metric_name
- raw_value
- parsed_numeric_value
- raw_period
- effective_period
- page_no
- table_id
- evidence_id
- p9_resolution_id
- overlay_set_hash
- resolved_validation_status
- resolved_reuse_eligible
- review_required_data_usable_for_claim
- canonical_reuse_eligible
- raw_numeric_value_changed
- evidence_ledger_validation

Completion:
Return COMPLETE only if every required field is supported by fresh validated P8/P9/P10 provenance. Otherwise return an explicit gap and do not guess.
