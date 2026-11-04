# 186 — P11 Final Export Byte Determinism Amendment Evidence — ISSUE-034

Status: **PASS — AMENDED DESIGN READY FOR CANDIDATE FREEZE / PRODUCTION CLOSED**

Phase:
P11 — US SEC Provider

Historical reviewed candidate:
`866e07025e53b2da852700d2e688b3a3af0bc39a`

Authoritative stop:
`development/185-p11-final-export-byte-determinism-review-stop.md`

## P11-ISSUE-034 resolution

The final `export-v2` byte contract is now deterministic, not merely semantically deterministic.

### Exact JSON bytes

`manifest.json`, `document.json`, and `validation.json` use:

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
- no indentation/trailing spaces;
- LF only;
- exactly one final LF;
- no platform-native newline conversion.

### Exact JSONL bytes

Every row uses the same canonical JSON encoder and one LF.

- no BOM;
- LF only;
- no blank lines;
- final row has one LF;
- empty JSONL = zero bytes.

Top-level row order:

- source_assets: source_asset_id;
- source_segments: (ordinal, segment_id);
- sections: section_id;
- tables: table_id;
- raw_facts: raw_fact_id;
- evidence: evidence_id.

Nested source-order collections preserve the frozen parser/source order.
Semantically unordered issue/warning/set-like arrays sort by canonical JSON bytes.

### Diagnostic isolation

Final export forbids:

- wall-clock timestamps;
- durations/elapsed values;
- request/retry timing;
- request/process/attempt IDs;
- absolute/staging/temp paths;
- random values/nonces;
- acquired_at;
- performance-only diagnostics.

Such values may exist only in separate project-local receipts outside `export-v2` and outside registry artifact_path.

### Raw blob path determinism

P11 v1 physical raw blob path is now extensionless SHA-only:

`workspace/sec/raw/assets/sha256/<aa>/<sha>`

Thus identical bytes under different logical filenames/extensions always use the same physical blob path and cannot make `source_assets.jsonl.local_content_path` depend on discovery/input order.

### Acceptance

Acceptance now proves:

- same semantic inputs serialized twice under different wall-clock/performance receipt values produce identical SHA256 for all nine final files;
- CRLF/native newline environment does not affect bytes;
- JSON insertion order does not affect bytes;
- shuffled caller/input row order does not affect JSONL output;
- empty JSONL is zero bytes;
- forbidden diagnostics do not enter final export;
- semantic changes still change relevant bytes;
- ISSUE-033 idempotent retry succeeds when only external diagnostic receipts differ.

## Regression boundary

PASS:

- ISSUE-010..033 remediation remains intact;
- no src change;
- no tests change;
- no integration change;
- no runtime-lock change;
- P0-P10 accepted contracts unchanged.

## Verdict

# PASS — READY FOR CANDIDATE FREEZE AND FRESH DETACHED DESIGN REVIEW

No P11 production authorization is implied.

P11-B remains NOT AUTHORIZED until the amended exact candidate passes fresh detached design review and P11-A is formally closed.
