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

For SEC, `source_package_sha256` uses the exact `p11-sec-source-package-identity-v1` payload frozen in design/26 Section 15. That payload is normative for v2 as well.

The package identity includes the canonical requested `source_url` for each asset as frozen in design/26 Section 15.

The package identity excludes only acquisition/runtime diagnostics:

- redirect final URL;
- declared HTTP media/content type;
- local paths;
- timestamps;
- request IDs;
- ETag/Last-Modified;
- retry/status diagnostics.

Those excluded values belong to acquisition receipts and do not affect `source_package_sha256`.

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

### Final export byte serialization contract

Every file under final `export-v2` is deterministic semantic output. Per-attempt diagnostics are forbidden from the final export.

Forbidden final-export values include:

- wall-clock timestamps;
- elapsed/duration values;
- request/retry timing;
- request/process/attempt IDs;
- host-specific absolute paths;
- staging/temp paths;
- random values/nonces;
- `acquired_at`;
- any value whose only purpose is runtime/performance diagnostics.

Such values may exist only in separate project-local receipt/diagnostic files outside `export-v2` and outside registry `artifact_path`.

#### JSON files

For exactly:

- `manifest.json`;
- `document.json`;
- `validation.json`;

the complete file bytes are:

```python
json.dumps(
    value,
    ensure_ascii=False,
    sort_keys=True,
    separators=(",", ":"),
    allow_nan=False,
).encode("utf-8") + b"\n"
```

Required byte rules:

- UTF-8 only;
- no BOM;
- no indentation;
- no trailing spaces;
- U+000A LF only;
- exactly one final LF;
- no platform-native newline conversion.

The final LF is part of file bytes. It is not part of canonical-object ID/hash payloads unless an individual ID contract explicitly says otherwise.

#### JSONL files

For:

- `source_assets.jsonl`;
- `source_segments.jsonl`;
- `sections.jsonl`;
- `tables.jsonl`;
- `raw_facts.jsonl`;
- `evidence.jsonl`;

each row is encoded with the same canonical JSON encoder above, without an embedded terminator, followed by exactly one byte `0x0A`.

Rules:

- no BOM;
- LF only;
- no blank lines;
- one LF after every row, including the last row;
- an empty JSONL file is exactly zero bytes.

Top-level row order is exact:

- `source_assets.jsonl`: ascending `source_asset_id`;
- `source_segments.jsonl`: ascending `(ordinal, segment_id)`;
- `sections.jsonl`: ascending `section_id`;
- `tables.jsonl`: ascending `table_id`;
- `raw_facts.jsonl`: ascending `raw_fact_id`;
- `evidence.jsonl`: ascending `evidence_id`.

Caller/input container order MUST NOT change those top-level output orders.

#### Nested collection order

No unordered Python/container iteration may affect final bytes.

- schema fields whose semantics are source order preserve the exact frozen source/parser order;
- table `rows` are ascending `row_index`;
- table `raw_cells` are ascending `(row_index, column_index, cell_id)`;
- ordered source-node/header child arrays preserve deterministic DOM/XML source order frozen by the P11-F parser contract;
- semantically unordered issue/warning/set-like arrays are sorted ascending by each element's canonical JSON bytes;
- JSON object/map key order is always the canonical `sort_keys=True` order.

If a later schema adds a collection whose semantic ordering is not explicit, that schema is incomplete and MUST NOT be serialized until a Design-First amendment freezes its order.

### P11 persisted export directory binding

For P11 periodic registry persistence, the v2 artifact is the **directory** shown above, not an individual child file.

Exact storage location:

`<parsed_root>/<parse_run_id>/export-v2`

Registry `artifact_path` stores the normalized project-root-relative POSIX path to that directory, without a trailing slash.

The directory must contain every required file listed in this section before it may be registered. A staging/partial directory is never a valid artifact_path.

### Finalization order

A final registry-eligible v2 export does not exist until validation is complete.

Normative order:

1. P11-F produces deterministic parser outputs;
2. P11-G confirms final filing identity;
3. P11-H computes the final validation model;
4. P11-I serializes all non-validation artifacts;
5. P11-I serializes final `validation.json` from the P11-H validation model;
6. P11-I derives manifest `validation_status` and `blocking_issue_count` from that same final validation model and serializes final `manifest.json`;
7. P11-I writes to an exclusive attempt staging directory `<parsed_root>/.staging/<parse_run_id>/<attempt_token>/export-v2` and runs the complete v2 loader against it;
8. P11-I evaluates the deterministic final path `<parsed_root>/<parse_run_id>/export-v2`:
   - if already present, never overwrite it and enter existing-final verification;
   - if absent, perform exactly one atomic same-filesystem **non-replacing** directory commit;
9. commit outcomes are exact:
   - `COMMITTED_NEW` => this attempt created final;
   - `DESTINATION_EXISTS` => another attempt/earlier run created final; transition to existing-final verification;
   - `COMMIT_ERROR` => `P11_FINAL_ARTIFACT_COMMIT_FAILED` / BLOCKED;
10. existing-final verification loads final and compares every required artifact file byte-for-byte with this attempt's validated staging export plus exact identity/validation semantics;
11. any existing-final mismatch/missing/invalid state => `P11_FINAL_ARTIFACT_COLLISION` / BLOCKED;
12. after a new atomic commit or idempotent existing-final match, reload the final path successfully;
13. only then may P11-K persist `ParsedDataRecord.artifact_path`.

A successful existing-final match is idempotent success and keeps the original final directory byte-unchanged.

Concurrent attempts for the same `parse_run_id` MUST use distinct staging directories. A losing no-replace commit is not a collision merely because the destination now exists; it is idempotent success only after the exact existing-final loader/identity/all-nine-byte comparison passes. An unrelated commit failure cannot be converted to success by a later existence check.

If registry persistence later fails, the valid final export remains immutable and unregistered. A retry may verify the same final export and retry registry persistence; the orphan final export is not reusable without a registry row.

Forbidden:

- provisional/fabricated validation status;
- a final `manifest.json` written before validation;
- a registry-eligible final export missing `validation.json`;
- P11-H committing the final export;
- overwriting/deleting/replacing an existing final export directory;
- treating staging presence as committed success;
- P11-K mutating final export bytes after registration.

The final `manifest.json.validation_status` MUST equal `validation.json.status`.
The final `manifest.json.blocking_issue_count` MUST equal the length of `validation.json.blocking_issues`.

## 4. manifest.json

Allowed `source_kind` values for P11 v1:

- `SEC_INLINE_XBRL` — primary HTML contains Inline XBRL facts;
- `SEC_HTML` — primary HTML without Inline XBRL facts;
- `SEC_XBRL` — XML/XBRL primary structured source when explicitly supported by the filing/package.

No caller-defined source_kind is allowed.

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
- ticker nullable for US;
- filing_type;
- fiscal_year nullable only for supplemental filings;
- raw_fiscal_period nullable only for supplemental filings;
- amended;
- filing_role = PERIODIC | SUPPLEMENTAL;
- filing_date;
- report_date nullable only for supplemental filings;
- source_provider;
- source_id;
- source_url;
- source_title;
- provider_company_id;
- source_kind;
- primary_source_asset_id;
- primary_asset_sha256;
- primary_asset_name;
- primary_media_type;
- file_size;
- accession_number nullable outside SEC.

For SEC, `company_id` and `provider_company_id` are canonical normalized CIK unless a later design explicitly changes this rule.

US `ticker` is display/lookup metadata only:

- it may be null;
- it MUST NOT be fabricated when CIK is known;
- when non-null it follows design/26 Section 4 normalized/validated ticker rules;
- multiple official tickers without a caller-selected validated ticker remain null rather than selecting one arbitrarily.

Filing-role nullability:

### PERIODIC

- `fiscal_year` MUST be a confirmed integer;
- `raw_fiscal_period` MUST be one of the confirmed periodic values allowed by market/form;
- `report_date` MUST be a valid official filing report date;
- provisional/null periodic identity is invalid.

### SUPPLEMENTAL

- `fiscal_year` is null unless exact filing-native evidence explicitly establishes a fiscal year;
- `raw_fiscal_period` MUST be null;
- `report_date` is the official SEC reportDate only when non-empty and valid, otherwise null;
- filing_date MUST NOT be used to infer fiscal_year or report_date;
- no calendar-year inference is allowed merely to populate a field.

P11 v1 supplemental identity remains accession-bound even when all three periodic/date fields above are null except filing_date.

For periodic SEC filings, `document.json.report_date` is the final P11-G confirmed report date from design/26 Section 7. It may differ from the immutable package-identity discovery `report_date` only when the discovery value was null and DEI supplies the exact final date. This never changes `source_package_sha256`.

## 6. source_assets.jsonl

One row per captured **logical source asset**.

Logical asset identity follows design/26:

`(file_name, canonical requested source_url)`

Two logical rows may share the same `asset_sha256` and may therefore share the same `local_content_path` content-addressed blob. They remain separate source-assets rows because source path/role provenance is distinct.

`source_asset_id` is the stable logical-source identifier. It is SHA256 of canonical JSON of this exact object:

```json
{
  "schema_version": "p11-source-asset-id-v1",
  "file_name": "example.htm",
  "source_url": "https://www.sec.gov/Archives/.../example.htm",
  "asset_sha256": "<lowercase sha256>"
}
```

Known fixture using the package example in design/26:

`41183564053cd4f7be5c66d4ed4e7c44d72ad137f9aaf60e7f5bf30c9ef41fa2`

Rules:

- role, local path, media type, timestamps and HTTP diagnostics do not participate in `source_asset_id`;
- changing logical filename, canonical requested source URL or exact bytes changes `source_asset_id`;
- same bytes under different logical names/URLs produce different `source_asset_id` values;
- loader recomputes and verifies `source_asset_id` for every row.

Required fields:

- source_asset_id;
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

Cross-artifact source reference rule:

- every segment/section/table/raw-fact/evidence row that references a source asset carries both `source_asset_id` and `source_asset_sha256`;
- `source_asset_id` MUST resolve to exactly one row in `source_assets.jsonl`;
- the resolved row's `asset_sha256` MUST equal the referencing `source_asset_sha256`;
- a matching content SHA alone is insufficient provenance when multiple logical source rows share bytes;
- `document.json.primary_source_asset_id` MUST resolve to the unique `PRIMARY_DOCUMENT` row and its SHA/name/media type/size must match the corresponding `primary_*` document fields.

`source_url` is the canonical requested URL from the immutable package identity, not a redirect-final URL.

`media_type` is a deterministic parser classification from the captured asset bytes/name under the frozen parser version. The HTTP-declared Content-Type is acquisition receipt metadata and MUST NOT be copied into this field merely because the server sent it.

`local_content_path` contract:

- persisted value is project-root-relative POSIX text only;
- for P11 v1 content blobs it uses the extensionless SHA-only path frozen in design/26; filename/extension does not participate in physical blob-path selection;
- absolute, drive-relative, UNC, empty, `.`, `..` and traversal-containing paths are rejected;
- loader resolves `project_root / local_content_path`, then requires the resolved file to remain inside the configured P11 SEC raw-assets root;
- the file's SHA256/size must match the row;
- `local_content_path` is storage metadata only and is excluded from package identity, fact/evidence IDs, semantic equality and cross-machine identity.

Example:

`workspace/sec/raw/assets/sha256/ab/<sha>`

## 7. source_segments.jsonl

A segment is a source-native text/navigation unit, not a fake PDF page.

Required:

- segment_id;
- document_sha256;
- ordinal;
- locator_type;
- source_locator;
- raw_text;
- normalized_text;
- source_asset_id;
- source_asset_sha256;
- section_hint nullable.

The canonical locator object is stored only in `source_locator`; duplicate top-level DOM/XML locator fields are forbidden.

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
- source_asset_id;
- source_asset_sha256;
- locator_type;
- source_locator;
- quality_signals.

No page_start/page_end is required for HTML/XML sources.

## 9. tables.jsonl

For HTML-origin tables:

- table_id;
- raw_title nullable;
- source_asset_id;
- source_asset_sha256;
- locator_type = HTML_DOM;
- source_locator;
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
- locator_type = HTML_DOM;
- source_locator.

The table/cell `source_locator` objects use Section 11.1 exactly.

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
- source_asset_id;
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

For Inline XBRL/XBRL:

- `raw_value` follows design/26 Section 22 exactly;
- resolve a valid `continuedAt` chain in source order and exclude `ix:exclude` descendants;
- concatenate descendant character data after standards-required entity decoding;
- normalize every Unicode whitespace run to one U+0020 SPACE and trim leading/trailing U+0020;
- do not apply `format`, `scale`, `sign`, unit conversion, period inference or canonical metric semantics to `raw_value`;
- `parsed_numeric_value` is the only field allowed to carry standards-defined numeric transformation;
- `nil=true` forces `parsed_numeric_value=null`;
- scale/sign/format/continuation locators remain auditable source metadata;
- invalid/unsupported transformation => parsed value null + explicit validation issue, never guess.

The exact parser/runtime transformation registry implementation MUST be frozen by the required P11-F preimplementation Design-First parser-contract amendment after P11-B; P11-F production cannot begin before that freeze.

## 11. evidence.jsonl

Required:

- evidence_id;
- document_sha256;
- extraction_version;
- source_asset_id;
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

## 11.1 Canonical source locator contract

Locator identity is parser-independent at the contract level.

### HTML_DOM path

Canonical HTML path:

- start at the document element;
- each step is `lowercase-ascii-tag-name[index]`;
- `index` is 1-based among element siblings having the same lowercase ASCII tag name;
- only element nodes participate in sibling indexing;
- root is included;
- no CSS selector shorthand, class name or volatile presentation attribute participates.

Example:

`/html[1]/body[1]/div[3]/table[1]/tr[2]/td[4]`

### XML / Inline XBRL path

Canonical XML/iXBRL path:

- each element name uses expanded Clark QName `{namespace-uri}local-name[index]`;
- empty namespace is `{}local-name[index]`;
- index is 1-based among element siblings with the exact same expanded QName;
- root is included;
- namespace prefixes are never identity inputs.

Example:

`/{http://www.w3.org/1999/xhtml}html[1]/{http://www.w3.org/1999/xhtml}body[1]/{http://www.xbrl.org/2013/inlineXBRL}nonFraction[2]`

### Canonical locator objects

`HTML_DOM`:

```json
{
  "dom_path": "/html[1]/body[1]/...",
  "html_id": null,
  "start_offset": null,
  "end_offset": null
}
```

`IXBRL_DOM` and `XML_NODE`:

```json
{
  "dom_path": "/{uri}root[1]/.../{uri}node[2]",
  "xml_id": null,
  "start_offset": null,
  "end_offset": null
}
```

`IXBRL_FACT`:

```json
{
  "dom_path": "/{uri}html[1]/.../{ix-uri}nonFraction[2]",
  "xml_id": null,
  "concept_qname": "{namespace-uri}LocalName",
  "context_ref": "ctx",
  "unit_ref": null
}
```

`XBRL_FACT` uses the same exact keys and XML path rule.

`SOURCE_ASSET`:

```json
{
  "source_asset_id": "<lowercase sha256>",
  "asset_sha256": "<lowercase sha256>"
}
```

The pair must resolve to exactly one logical source-assets row. `source_asset_id` is the logical provenance key; `asset_sha256` independently confirms the referenced content bytes.

Rules:

- optional values are present as explicit JSON null, not omitted;
- QName identity uses expanded Clark form, never source prefix spelling;
- source locator keys are exact; extra keys are invalid;
- `html_id`/`xml_id` are corroborating source attributes and do not replace `dom_path`;
- locator resolution must produce exactly one node in the captured source asset;
- zero or multiple matches => artifact invalid;
- canonical source-node identity is the canonical JSON object:
  `{"locator_type": <type>, "source_locator": <exact-object>}`.

## 12. evidence_id

`evidence_id` is SHA256 of canonical JSON of this exact object and no extra keys:

```json
{
  "document_sha256": "<lowercase sha256>",
  "source_asset_id": "<lowercase sha256>",
  "source_asset_sha256": "<lowercase sha256>",
  "locator_type": "IXBRL_FACT",
  "source_locator": {},
  "raw_fact_id": "<lowercase sha256 or null>",
  "extraction_version": "..."
}
```

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

For XBRL/iXBRL facts, `raw_fact_id` is SHA256 of canonical JSON of this exact object and no extra keys:

```json
{
  "document_sha256": "<lowercase sha256>",
  "source_asset_id": "<lowercase sha256>",
  "source_asset_sha256": "<lowercase sha256>",
  "concept_qname": "{namespace-uri}LocalName",
  "context_ref": "ctx",
  "unit_ref": null,
  "locator_type": "IXBRL_FACT",
  "source_locator": {},
  "extractor_version": "..."
}
```

`source_locator` is the exact canonical object from Section 11.1.

Two facts with the same concept/value but different contexts or different source nodes MUST remain different raw facts.

## 13.1 Other deterministic IDs

All IDs below use the Section 12 canonical JSON encoder and SHA256 of the exact object shown.

### config_hash

```json
{
  "schema_version": "p11-parser-config-v1",
  "options": {}
}
```

`options` is the explicitly frozen parser configuration object. Absolute paths, timestamps, environment-specific executable paths and secrets are forbidden. Unknown keys are invalid.

### parse_run_id

```json
{
  "document_sha256": "<sha>",
  "source_package_sha256": "<sha>",
  "schema_version": "parsed-financial-document-v2",
  "parser_version": "...",
  "config_hash": "<sha>"
}
```

### segment_id

```json
{
  "document_sha256": "<sha>",
  "source_asset_id": "<sha>",
  "source_asset_sha256": "<sha>",
  "locator_type": "HTML_DOM",
  "source_locator": {},
  "ordinal": 0,
  "parser_version": "..."
}
```

### section_id

```json
{
  "document_sha256": "<sha>",
  "source_asset_id": "<sha>",
  "source_asset_sha256": "<sha>",
  "locator_type": "HTML_DOM",
  "source_locator": {},
  "level": 1,
  "raw_title": "...",
  "parser_version": "..."
}
```

### table_id

```json
{
  "document_sha256": "<sha>",
  "source_asset_id": "<sha>",
  "source_asset_sha256": "<sha>",
  "locator_type": "HTML_DOM",
  "source_locator": {},
  "parser_version": "..."
}
```

### cell_id

```json
{
  "table_id": "<sha>",
  "row_index": 0,
  "column_index": 0,
  "locator_type": "HTML_DOM",
  "source_locator": {},
  "parser_version": "..."
}
```

Rules:

- integer ordinals/indices are zero-based in artifact data and ID payloads;
- no local path, URL, timestamp, random value, HTTP header or parser-process identity participates;
- the same exact source package + parser/config produces identical IDs;
- any parser/config change that can change semantic artifact output must change `parser_version` or `config_hash`.

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

Wall-clock validation time, elapsed duration and other per-attempt diagnostics MUST NOT appear in final `validation.json` or any other final `export-v2` file. If collected, they are stored only in a separate project-local diagnostic/performance receipt outside `export-v2` and outside registry `artifact_path`.

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
