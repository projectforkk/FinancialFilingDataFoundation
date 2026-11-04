# 185 — P11 Final Design Review Stop — Final Export Byte Determinism

Status: **FAIL / STOP — P11-ISSUE-034 / PRODUCTION CLOSED**

Phase:
P11 — US SEC Provider

Reviewed exact candidate:
`866e07025e53b2da852700d2e688b3a3af0bc39a`

Fresh detached review:
`D:\\Codex\\FinancialFilingDataFoundation\\worktrees\\review\\p11-design-866e070`

Review authorization:
`development/184-p11-final-artifact-idempotency-final-review-authorization.md`

Automated review:

- ISSUE-010..031 matrix = PASS;
- ISSUE-032..033 guard = PASS;
- P0-P10 production/test/runtime diff = NONE;
- git diff --check = PASS.

## Finding

ISSUE-033 now requires an existing deterministic final export to be reusable idempotently only when every required artifact file is byte-identical to newly generated staging.

However the current v2 contract still permits:

`Wall-clock validation time may be diagnostic`

and does not fully freeze:

- whether such diagnostics can appear inside final `validation.json`;
- exact JSON file serialization bytes;
- exact JSONL row serialization bytes;
- exact row ordering for every JSONL artifact;
- final newline / LF-vs-CRLF behavior.

Therefore two semantically identical runs may generate different final bytes and falsely trigger:

`P11_FINAL_ARTIFACT_COLLISION`.

## P11-ISSUE-034 — final export byte determinism

Required correction:

### 1. Final export contains deterministic semantic data only

No final `export-v2` file may serialize:

- wall-clock timestamps;
- durations / elapsed milliseconds;
- request IDs;
- retry timing;
- process IDs;
- host-specific absolute paths;
- staging/temp paths;
- random/nonces;
- `acquired_at`;
- runtime attempt IDs;
- any other per-attempt diagnostic value.

Those values belong only in separate acquisition/runtime/performance receipts outside the final v2 export.

### 2. Exact JSON byte encoding

For:

- manifest.json;
- document.json;
- validation.json;

serialize exactly as:

```python
json.dumps(
    value,
    ensure_ascii=False,
    sort_keys=True,
    separators=(",", ":"),
    allow_nan=False,
).encode("utf-8") + b"\n"
```

Rules:

- UTF-8;
- no BOM;
- LF only;
- exactly one final LF;
- no indentation;
- no trailing spaces;
- no platform-native newline conversion.

The final LF is part of file bytes but not part of ID/hash canonical-object payloads unless a design explicitly says otherwise.

### 3. Exact JSONL byte encoding

Each non-empty JSONL file:

- each row uses the same canonical JSON encoder above, without embedded line terminator;
- one U+000A LF follows every row, including the final row;
- no blank lines;
- no BOM;
- no CRLF.

Empty JSONL file = exactly zero bytes.

### 4. Exact row order

Freeze:

- source_assets.jsonl: ascending `source_asset_id`;
- source_segments.jsonl: ascending `(ordinal, segment_id)`;
- sections.jsonl: ascending `section_id`;
- tables.jsonl: ascending `table_id`;
- raw_facts.jsonl: ascending `raw_fact_id`;
- evidence.jsonl: ascending `evidence_id`.

Nested arrays/maps inside rows must follow their own frozen semantic order; JSON object key order is canonical sort_keys.

### 5. Validation diagnostics

Wall-clock validation/performance diagnostics MUST NOT be fields in final `validation.json`.

If collected, store them in a separate project-local diagnostic/performance receipt outside:

`<parsed_root>/<parse_run_id>/export-v2`

and outside registry artifact_path.

### 6. Acceptance

Acceptance must prove:

- same exact source package/parser/config serialized twice with different wall-clock times yields byte-identical SHA256 for all 9 required files;
- CRLF/native-newline environment does not alter artifact bytes;
- JSON key insertion order does not alter artifact bytes;
- caller/input row ordering does not alter JSONL output order;
- empty JSONL files are zero bytes;
- no diagnostic timestamp/duration/request/process/temp-path field appears in final export;
- changing actual semantic artifact content changes relevant bytes/IDs as expected;
- ISSUE-033 idempotent retry succeeds under intentionally different wall-clock/performance diagnostics.

## Scope

No production/test/runtime changes.

P11-ISSUE-010..033 remediation remains valid.

## Verdict

# FAIL / STOP

Candidate `866e070...` is INELIGIBLE for DESIGN READY.

P11 production remains CLOSED.
