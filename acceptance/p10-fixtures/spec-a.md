# Independent Acceptance Spec A — Table/Page Provenance

Use the accepted CN 600519 FY2024 filing from the supplied FFDF catalog.

Task:
- Confirm the exact accepted document.
- Identify the first reconstructed table for that document.
- Return document_sha256, table_id, and page_no.
- Use table/page provenance.
- Do not query raw facts or evidence unless required by this task.

Evidence:
- Create one P10 evidence-ledger claim named table_claim.
- Classify it as P8_RAW_DIRECT.
- Bind the exact document, table, and page used.

Output:
- only the requested research fields;
- the exact P8 tools selected;
- ledger validation status.
