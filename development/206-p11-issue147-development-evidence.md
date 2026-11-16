# P11 ISSUE-147 Development Evidence

Date: 2026-11-16
Agent role: Development Agent
Authoritative remote: `origin/reconcile/p11-140-143-local-chain`

## Authority and candidate identity

| Item | Exact identity |
|---|---|
| Design 39 | `fad6ee7512ec1f2f3da0c9a24c646959b2f45541` |
| Development authorization | `534a1e64ee549df910ed815f90fde82726b43b1c` |
| Previous production candidate | `6eaace08c9ba5fb26809a7e02de5835123fb667a` |
| New production/test candidate | `f1cc76889718e06fdbdc46926e2b207b740a96e3` |
| Candidate commit | `fix: separate SEC ticker source and observation identity` |

The candidate contains only:

- `src/financial_filing_data_foundation/us_sec/ticker_map.py`;
- `src/financial_filing_data_foundation/user_cli.py`;
- `tests/unit/us_sec/test_issue147.py`.

No Registry schema, parser/artifact/validation schema, or P11 reason code was
changed. The candidate preserves the frozen version contract:

```text
REGISTRY_SCHEMA_VERSION=1
SEC_REGISTRY_SCHEMA_VERSION=4
SEC_DISCOVERY_SCHEMA=p11-sec-discovery-v1
VIRTUAL_HTML_NORMALIZER_VERSION=VIRTUAL_HTML_V6
SEC_ARTIFACT_SCHEMA=p11-sec-artifacts-v2
SEC_VALIDATION_SCHEMA=p11-sec-validation-v3
```

## ISSUE-147 implementation proof

Source identity remains the official URL plus exact source bytes and their
SHA-256. Retrieval observation identity is now:

```text
SHA256(canonical_json({
  "source_url": source_url,
  "source_sha256": lowercase_source_sha256,
  "retrieved_at": normalized_timezone_aware_iso8601,
}))
```

New online observations are immutable at:

```text
workspace/ingest/us/ticker-map/observations/<snapshot_id>.json
```

Legacy `workspace/ingest/us/ticker-map/<source_sha256>.json` files remain
read-only compatibility inputs. Cached resolution independently verifies all
current and legacy candidates, selects the newest verified observation, and
resolves only against that observation. It does not merge historical mappings
or fall back when the newest snapshot lacks the requested ticker.

## T147 focused matrix

Command:

```text
python -m pytest -q tests/unit/us_sec/test_issue147.py --basetemp D:\ffdf-p11t4\candidate-focused
```

Result: exit `0`, `10 passed`.

| Test | Evidence |
|---|---|
| T147-01 | Identical bytes produced equal source SHA, different snapshot IDs, and two verified observation files without `P11_SOURCE_DRIFT`. |
| T147-02 | Deterministic normal ticker-based acquire followed by ingest; ticker map and current submissions were each fetched twice and the second flow passed persistence. |
| T147-03 | Different canonical payload at the same observation identity returned `P11_SOURCE_DRIFT`. |
| T147-04 | Valid legacy file hash remained unchanged while a new file was created below `ticker-map/observations/`. |
| T147-05 | Source-byte tampering returned `P11_TICKER_SNAPSHOT_INVALID`. |
| T147-06 | Derivative mapping tampering returned `P11_TICKER_SNAPSHOT_INVALID`. |
| T147-07 | The newest verified snapshot selected its own CIK and did not merge historical CIKs. |
| T147-08 | A ticker absent from the newest verified snapshot did not fall back to an older legacy snapshot. |
| T147-09 | Explicit CIK resolution constructed no ticker-map client and performed zero ticker-map fetches. |
| T147-10 | The Formal FT-10 boundary was reproduced with two timestamps and identical bytes; both snapshots persisted and the second call passed. |

## Exact-candidate regression

All commands below were rerun after candidate `f1cc76889718e06fdbdc46926e2b207b740a96e3` was created.

| Scope | Command/result | Exit |
|---|---|---:|
| US SEC focused | `python -m pytest -q tests/unit/us_sec` — `263 passed` | 0 |
| Review-5/6 focused | `python -m pytest -q tests/unit/us_sec/test_repair_140_143.py tests/unit/us_sec/test_validation_p8.py` — `79 passed` | 0 |
| MCP focused | `python -m pytest -q tests/unit/mcp` — `65 passed` | 0 |
| P0-P10 focused | `python -m pytest -q tests/unit/acquisition tests/unit/identity tests/unit/validation tests/unit/registry tests/unit/mcp tests/unit/research tests/unit/review` — `371 passed` | 0 |
| Full unit | `python -m pytest -q tests/unit` — `793 passed` | 0 |
| Compileall | `python -m compileall -q src tests` | 0 |
| Git diff check | `git diff --check` | 0 |

The focused and full results contain no failed or skipped tests. The working
tree was clean after candidate creation before this evidence document was
added.

## Apple FY2025 developer smoke

The smoke was run against candidate `f1cc76889718e06fdbdc46926e2b207b740a96e3`
with `FFDF_P11_US_DEV` absent and SEC contact configuration present; the
contact email value is intentionally not recorded here.

Commands:

```text
python -m financial_filing_data_foundation.user_cli acquire --market US --ticker AAPL --year 2025 --period FY
python -m financial_filing_data_foundation.user_cli ingest --market US --ticker AAPL --year 2025 --period FY
```

The candidate smoke ran the required ticker-based acquire→ingest sequence.
The local package was already available on this final exact-candidate rerun,
so the planner selected `REUSE_DATA`; the earlier clean run on the same source
and test tree performed the initial download and selected accession unchanged.

| Field | Final exact-candidate smoke |
|---|---|
| Acquire result | `REUSED_LOCAL`, planner `REUSE_DATA`, exit `0` |
| Ingest result | planner `REUSE_DATA`, exit `0` |
| CIK / ticker / FY / period | `0000320193` / `AAPL` / `2025` / `FY` |
| Accession | `0000320193-25-000079` |
| Ticker snapshot 1 ID | `0bcabed41fb8fe66911b5968c93859f116dbd8b379808cae999ef50ed0b1b828` |
| Ticker snapshot 1 retrieved_at | `2026-11-16T04:38:13.666757+00:00` |
| Ticker snapshot 2 ID | `e8d9da32d79f3de540bad0cb76077871269728aacf789f45c70b0adab7e36819` |
| Ticker snapshot 2 retrieved_at | `2026-11-16T04:38:14.996786+00:00` |
| Source SHA 1 | `29e8eee5a85a68e837628b0e9623870af68db41e5427a154d17fe3b1af0a1b9a` |
| Source SHA 2 | `29e8eee5a85a68e837628b0e9623870af68db41e5427a154d17fe3b1af0a1b9a` |
| Source SHA equal | `YES` |
| Snapshot IDs differ | `YES` |
| Discovery observation SHA | `ec1fe626cbd962be2a2e5701304e72c5867b1e8c45ffea8bbddcb1cda468a384` |
| Package SHA | `d94d8c46e34ce25af8d42279dbb4a370b1e617d7daf421743f29468b77d19568` |
| Discovery state | `UNAMBIGUOUS` |
| Current submissions fetches | `1` per invocation |
| History fetch count | `0` |
| Archive member fetch count | `0` on final reuse rerun; `7` on the earlier clean acquire |
| Static-asset fetch count | `0` |
| Validation-v3 path | `workspace/ingest/us/p7/d94d8c46e34ce25af8d42279dbb4a370b1e617d7daf421743f29468b77d19568/p11-sec-validation-v3` |
| Validation status / blocking / review | `PASS` / `0` / `0` |
| P8 catalog result | `ALREADY_REGISTERED` |
| Research ready | `true` |

The earlier clean acquire returned `DOWNLOADED`, planner
`DISCOVER_AND_ACQUIRE`, the same accession and package SHA, and fetched seven
selected archive members. Neither the clean run nor the final exact-candidate
rerun produced `P11_SOURCE_DRIFT`.

## Development lifecycle boundary

```text
ISSUE-147: FIXED
SOURCE IDENTITY / OBSERVATION IDENTITY: SEPARATED
FORMAL TEST PLAN 5: NOT CREATED
FORMAL TEST EXECUTION: NOT RUN
FORMAL ACCEPTANCE: NOT PASSED
MAIN MERGE: NOT RUN
P11 DONE: NO
```

This is development evidence only. The candidate is stopped for ChatGPT Fresh
Full Exact-Candidate Review.
