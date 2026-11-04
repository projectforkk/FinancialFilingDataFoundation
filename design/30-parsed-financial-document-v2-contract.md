# 30 — ParsedFinancialDocument v2 Source-Neutral Contract

Status: **P11 DESIGN BASELINE CANDIDATE**

Purpose:
Define an additive source-neutral parsed-financial-document contract for non-PDF sources, starting with SEC HTML / Inline XBRL / XBRL.

The accepted `design/03-parsed-financial-document-contract.md` v1 remains unchanged as accepted PDF history.

## 1. Core rule

v2 MUST represent evidence using the source's real coordinate system.

Forbidden:

- fake PDF page numbers for HTML;
- synthetic bbox used as if it were physical source geometry;
- conversion of HTML/iXBRL into PDF solely to satisfy v1 schemas;
- loss of exact source bytes;
- replacing filing-specific source evidence with an aggregate API result.

## 2. Document identity

`document_sha256` is SHA256 of the exact primary source asset bytes.

For SEC:

- primary source asset = EDGAR `primaryDocument`;
- source identity = accession number;
- provider company identity = CIK;
- a multi-asset filing package has a separate `source_package_sha256`.

The package hash MUST NOT replace `document_sha256`.

## 3. Export layout

```text
export-v2/
  manifest.json
  document.json
  source_assets.jsonl
  source_segments.jsonl
  sections.jsonl
  tables.jsonl
  raw_facts.jsonl
  evidence.jsonl
  validation.json
```

`tables.jsonl` may be empty when the source contains no reliable table structure.

## 4. manifest.json

Required fields:

```json
{
  "schema_version": "parsed-financial-document-v2",
  "parser_version": "...",
  "quality_policy_version": "...",
  "document_sha256": "...",
  "source_package_sha256": "...",
  "parse_run_id": "...",
  "source_kind": "SEC_INLINE_XBRL",
  "source_asset_count": 0,
  "segment_count": 0,
  "table_count": 0,
  "fact_count": 0,
  "evidence_count": 0,
  "blocking_issue_count": 0,
  "validation_status": "PASS"
}
```

No timestamps participate in deterministic IDs.

## 5. document.json

Required:

- document_sha256;
- source_package_sha256 nullable;
- market;
- company_id;
- ticker;
- filing_type;
- fiscal_year;
- raw_fiscal_period nullable for supplemental filings;
- amended;
- filing_role = PERIODIC | SUPPLEMENTAL;
- filing_date;
- report_date;
- source_provider;
- source_id;
- source_url;
- source_title;
- provider_company_id;
- source_kind;
- primary_asset_sha256;
- primary_asset_name;
- primary_media_type;
- file_size;
- accession_number nullable outside SEC.

For SEC, `company_id` and `provider_company_id` are canonical normalized CIK unless a later design explicitly changes this rule.

## 6. source_assets.jsonl

One row per captured source asset:

- asset_sha256;
- source_package_sha256;
- role;
- file_name;
- media_type;
- source_url;
- byte_size;
- primary boolean;
- local_content_path;
- dependency_depth;
- referring_asset_sha256 nullable.

Allowed SEC roles include:

- PRIMARY_DOCUMENT;
- FILING_INDEX;
- XBRL_INSTANCE;
- TAXONOMY_SCHEMA;
- PRESENTATION_LINKBASE;
- CALCULATION_LINKBASE;
- DEFINITION_LINKBASE;
- LABEL_LINKBASE;
- REQUESTED_EXHIBIT;
- OTHER_REQUIRED_DEPENDENCY.

Every stored row is exact-byte-addressed.

## 7. source_segments.jsonl

A segment is a source-native text/navigation unit, not a fake PDF page.

Required:

- segment_id;
- document_sha256;
- ordinal;
- locator_type;
- raw_text;
- normalized_text;
- source_asset_sha256;
- dom_path nullable;
- html_id nullable;
- xml_id nullable;
- start_offset nullable;
- end_offset nullable;
- section_hint nullable.

Allowed locator types:

- HTML_DOM;
- IXBRL_DOM;
- XML_NODE;
- SOURCE_ASSET.

## 8. sections.jsonl

Required:

- section_id;
- parent_section_id nullable;
- raw_title;
- normalized_title candidate nullable;
- level;
- segment_start;
- segment_end;
- source_asset_sha256;
- locator_type;
- locator;
- quality_signals.

No page_start/page_end is required for HTML/XML sources.

## 9. tables.jsonl

For HTML-origin tables:

- table_id;
- raw_title nullable;
- source_asset_sha256;
- dom_path;
- html_id nullable;
- raw_unit nullable;
- raw_scope nullable;
- header_tree;
- rows;
- raw_cells;
- reconstruction_signals;
- blocking_flags.

Each raw cell:

- cell_id;
- raw_text;
- row_index;
- column_index;
- rowspan;
- colspan;
- dom_path;
- html_id nullable.

No bbox is required for non-visual sources.

## 10. raw_facts.jsonl

Required source-neutral fields:

- raw_fact_id;
- document_sha256;
- raw_metric_name;
- raw_value;
- parsed_numeric_value nullable;
- raw_unit nullable;
- raw_period_label nullable;
- raw_scope nullable;
- evidence_id;
- source_asset_sha256;
- locator_type;
- source_locator.

SEC/XBRL optional fields:

- concept_qname;
- concept_namespace;
- context_ref;
- unit_ref;
- decimals;
- precision;
- scale;
- sign;
- format;
- nil;
- period_start;
- period_end;
- instant;
- entity_identifier;
- dimensions;
- table_id nullable;
- raw_label nullable.

`raw_metric_name` is source truth and MUST NOT be replaced by a canonical metric name.

For Inline XBRL:

- `raw_value` preserves the filing-visible lexical text or exact source lexical content according to the parser rule frozen by P11;
- any transformed XBRL value must be separately represented or used only to derive `parsed_numeric_value`;
- scale/sign/format transformations must be auditable.

## 11. evidence.jsonl

Required:

- evidence_id;
- document_sha256;
- extraction_version;
- source_asset_sha256;
- locator_type;
- source_locator;
- raw_text;
- table_id nullable;
- raw_fact_id nullable.

Allowed locator types:

### HTML_DOM

```json
{
  "dom_path": "...",
  "html_id": null,
  "start_offset": null,
  "end_offset": null
}
```

### IXBRL_FACT

```json
{
  "dom_path": "...",
  "xml_id": "...",
  "concept_qname": "...",
  "context_ref": "...",
  "unit_ref": "..."
}
```

### XBRL_FACT

Same logical fields, pointing to the exact XBRL instance node.

### SOURCE_ASSET

Used only for whole-asset metadata claims, never to substitute for a fact locator.

## 12. evidence_id

`evidence_id` is SHA256 of canonical JSON containing:

- document_sha256;
- source_asset_sha256;
- locator_type;
- canonical source_locator;
- raw_fact_id nullable;
- extraction_version.

Canonical JSON:

```python
json.dumps(
    value,
    ensure_ascii=False,
    sort_keys=True,
    separators=(",", ":"),
    allow_nan=False,
).encode("utf-8")
```

## 13. raw_fact_id

For XBRL/iXBRL facts:

SHA256 of canonical JSON containing at minimum:

- document_sha256;
- source_asset_sha256;
- concept_qname;
- context_ref;
- unit_ref nullable;
- exact source node identity;
- extractor_version.

Two facts with the same concept/value but different contexts MUST remain different raw facts.

## 14. validation.json

Required:

- schema_version;
- document_sha256;
- source_package_sha256;
- status = PASS | FAIL | REVIEW_REQUIRED | BLOCKED;
- compatibility_status;
- structural_checks;
- source_integrity_checks;
- xbrl_checks;
- financial_consistency_checks;
- completeness_checks;
- blocking_issues;
- warnings;
- validator_version.

Wall-clock validation time may be diagnostic but MUST NOT participate in identity.

## 15. DATA_READY gate

Same semantic rule as v1:

```text
validation_status == PASS
AND blocking_issue_count == 0
AND compatibility_status == COMPATIBLE
```

Only then can a parsed record be reusable/canonical.

`REVIEW_REQUIRED` may still be usable for evidence-grounded run-local research under an explicitly accepted downstream contract, but is not reusable/canonical by default.

## 16. v1 compatibility

- v1 PDF artifacts are not migrated;
- v1 IDs remain stable;
- P0-P10 accepted artifacts remain byte-identical;
- v2 consumers must explicitly declare v2 support;
- a v2 producer MUST NOT pretend its output is `p3-native-document-v1`, `p6-raw-facts-evidence-v1`, or any other accepted v1 artifact.

## 17. P8/P9/P10 boundary

P11 v1 does not modify accepted P8/P9/P10 contracts.

Therefore P11 v1 v2 artifacts are not automatically exposed through P8 MCP.

Future SEC query/research integration requires a separately authorized compatibility phase and must not silently alter P8 schema/version or P10 capability fingerprints.

## 18. Security

All source locators must point to assets already captured in the accepted source package.

No evidence locator may trigger network access.

No arbitrary local filesystem path may be serialized as source truth.

## 19. Exit condition

This contract becomes active for P11 only after:

- design/26;
- design/27;
- acceptance/41;
- design review;
- design baseline commit/push.

Production remains unauthorized until a separate P11 development authorization.
