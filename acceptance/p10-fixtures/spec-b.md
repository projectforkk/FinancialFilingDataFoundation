# Independent Acceptance Spec B — RawFact/Evidence Provenance

Use the accepted CN 600519 FY2024 filing from the supplied FFDF catalog.

Task:
- Confirm the exact accepted document.
- Retrieve the target RawFact:
  9b3e2e441e6730c0f3c979816dd764dcb4bf70e6cde16caae9e3897733b9a015
- Resolve the exact linked Evidence.
- Return document_sha256, raw_fact_id, raw_metric_name, raw_value, and evidence_id.
- Do not query table detail unless required by this task.

Evidence:
- Create one P10 evidence-ledger claim named fact_claim.
- Classify it as P8_RAW_DIRECT.
- Bind the exact document, RawFact, and Evidence.

Output:
- only the requested research fields;
- the exact P8 tools selected;
- ledger validation status.
