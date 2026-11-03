# 36 — P6 Development Evidence

状态：**P6 DEVELOPMENT COMPLETE / READY FOR CODE REVIEW**

Branch:
`task/p6-raw-facts-evidence`

Initial design baseline:
`8fcd46ab89dfb4c2ffc09af0912c7a3d18bcbda3`

Design amendments:
- P6-ISSUE-001 period-header guard: branch commit `70904fc533bc7b389a67c205d3d2d8645c5e164b`
- P6-ISSUE-002 live-input portability: branch commit `e606a2a60de232c36ee5bc7c9549ca4d9e1ff1ee`
- P6-ISSUE-003 overlapping unit substrings: design commit `dad376f8bc98c5fd4f4724a2425ea15009138ca6`
- P6-ISSUE-004 bare 公司/company scope too broad: design commit `dad376f8bc98c5fd4f4724a2425ea15009138ca6`
- P6-ISSUE-005 overlapping explicit scope phrases: design commit `c8b88c010727e2d932b2e88cc4dbc461a6d5b34e`

Initial production commit:
`ed47132d38c4bfe59fdd81e9848592dec5b29823`

Final hardened production commit:
`11fce802f146b2d8ed064dbe63ec3c81d918be21`

Accepted baseline before P6:
`8ff01cd3feed41c4b81aff88bce6502d50e8f32e`

## 1. Implemented Scope

Added:
- `src/financial_filing_data_foundation/facts/models.py`
- `src/financial_filing_data_foundation/facts/extract.py`
- `src/financial_filing_data_foundation/facts/__init__.py`
- `tests/unit/facts/test_extract.py`

Implemented:
- Decimal raw numeric parser
- raw metric/value preservation
- one fact per eligible VALUE cell
- period-header suppression
- explicit-only raw period/unit/scope
- continuation group context
- P3 source-word validation
- first-class evidence
- stable fact/evidence IDs
- input fingerprints
- atomic persistence
- artifact reuse
- full deterministic semantic recomputation tamper guard

Not implemented:
- canonical metrics
- accounting validation
- DATA_READY
- P7 policy
- OCR/Docling/network/AI
- MCP/Skill

## 2. Focused Tests

P6 focused:

`33 passed`

Coverage includes:
- integer/decimal/thousands
- Unicode minus
- parenthetical negative
- percent
- currency prefix
- placeholders
- period-header suppression
- ordinary metric value 2024/2023 not suppressed
- evidence/source refs
- invalid ref blocking
- unit ambiguity
- longest/non-overlapping unit matching (`百万元`, `千港元`)
- bare 公司/company rejected as scope evidence
- explicit company/parent scope phrases accepted
- longest/non-overlapping scope matching
- no-label row warning
- dual-root byte identity
- reuse
- fact/evidence tamper blocking
- fingerprint mismatch
- no PDF open
- input immutability

## 3. Full Regression

P0–P6:

`189 passed`

Additional:
- compileall PASS
- git diff --check PASS
- no Dayu/Docling/Torch/network/external-AI import in facts package
- no PyMuPDF/PDF open in facts package

## 4. P6-ISSUE-002 Fresh Live Input Rebuild

Accepted raw PDFs were located in archived P2 Independent Acceptance raw store.

CN raw:
- SHA `5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30`
- page_count 143

HK raw:
- SHA `70f529984a87ef7f46d9e1db26bb9ef27eef9c01d29c59aabf69e557b479a6a0`
- page_count 274

Fresh P3→P4→P5 chain created under:
`D:\Codex\FinancialFilingDataFoundation\workspace\live\p6-inputs`

Raw PDFs remained byte/size/mtime immutable.

### CN equivalence

Fresh:
- P3 pages SHA: `9bb06df4ad89bdd5de53d4d3fccba19fdf15cc2725c3776da88cbcc063eea3ae`
- P3 sections SHA: `3183fe1f94861b53e8a74ba2e448c40c589013c502297755293212cd64af163f`
- P4 candidates SHA: `90fc947efc1c7eeabe441b61496e80a7a20c7ad02262706f29137ed48257870f`
- P5 tables SHA: `11bfbd19854742401fef58852e9b696fbb9e9b29d742c65a81fcf82e80cd3b4a`
- P5 groups SHA: `e5b6ba7e3a960d487009f935f3755b69536efd85bcee4bd60576f4f8622d9708`
- candidate/table/group counts: 97 / 97 / 4

These deterministic P3/P4/P5 semantic artifacts match historical accepted P5 evidence.

### HK equivalence

Fresh:
- P3 pages SHA: `1930b9257cc0aa48bca9dc72ecdf2e4557db8d785b81f7f39c2e65c1a9929d0c`
- P3 sections SHA: `9a74f90ff4a9b8938c45b889ccf679ee117f158ebae67f522b37d53da8f688b8`
- P4 candidates SHA: `6ed15a62dbd5d4cd4b07180e85e1c25ad5c2de25b89b16862b6684ac3a173a22`
- P5 tables SHA: `b58f8bb848f7fa398f9dc860a4d17dbc83a291dc7f2d62a89d19e860852bac20`
- P5 groups SHA: `b3937df8da12d6d84cbfc453b431adc898530728e71a5b47ded98ff981ce26f7`
- candidate/table/group counts: 97 / 97 / 18

These deterministic P3/P4/P5 semantic artifacts match historical accepted P5 evidence.

P4 manifest hashes differ because manifests contain artifact paths/timings; deterministic candidates JSONL is identical.

## 5. Live P6 — CN

600519 FY2024:

- fact_count: **2177**
- evidence_count: **2177**
- tables_with_facts: 80
- page 60: 51 facts
- page 61: 34
- page 62: 42
- page 63: 41
- page 64: 8
- page 65: 28
- page 66: 6
- page 67: 31
- dual-root raw_facts byte-identical: PASS
- dual-root evidence byte-identical: PASS
- input immutability: PASS
- final hardened timings: 1864.482 / 2708.921 ms
- raw_facts SHA: `30b9845ecb8b0b9216a6f3fefdd640b9f63fe24fb71984cf1cb44ae0f39cb2c3`
- evidence SHA: `17d127ba1b37b7f39a1d9dae8336016261cb6b6ec7ac95ed70e97f3b519e39d2`
- non-null raw period: 133
- non-null raw unit: 91
- non-null raw scope: 154
- warning: ROW_WITHOUT_LABEL = 353

Performance <=10s: PASS.

## 6. Live P6 — HK

00700 FY2024:

- fact_count: **2989**
- evidence_count: **2989**
- tables_with_facts: 86
- page 124: 49 facts
- page 126: 69
- page 133: 52
- dual-root raw_facts byte-identical: PASS
- dual-root evidence byte-identical: PASS
- input immutability: PASS
- final hardened timings: 4241.041 / 4252.186 ms
- raw_facts SHA: `a35142503ed53eeb57c441d6b69e4ce73e6990f2282d436b0cf20636c2222340`
- evidence SHA: `1bbf8bdd55a78663419ecffbe1471cb59862426bf70ba2831c6444246da79573`
- non-null raw period: 0
- non-null raw unit: 45
- non-null raw scope: 0
- warnings:
  - AMBIGUOUS_RAW_UNIT = 2
  - ROW_WITHOUT_LABEL = 388

Null period/scope is allowed by design: P6 does not guess absent/ambiguous semantics.

Performance <=15s: PASS.

## 7. Raw-Fact Sampling

ASCII-safe sampling verified:
- CN examples include raw metrics such as 总资产 / 营业收入 and original numeric strings
- HK examples include 收入 / 毛利 and original numeric strings
- header-marker facts (项目/科目/item/items/particulars): **0**
- unique raw metrics:
  - CN: 598
  - HK: 474

No canonical metric field exists.

## 8. Gate Result

- P6-B Models/Numeric: PASS
- P6-C Evidence Validation: PASS
- P6-D Fact Extraction: PASS
- P6-E Persistence/Reuse/Tamper: PASS
- P6-F Full Regression: PASS
- P6-G Live CN/HK: PASS
- P6-ISSUE-003/004/005 regression: PASS

## 9. Final Hardening Result

After Code Review identified unit/scope evidence overlap risks:

- unit matching now uses longest/most-specific non-overlapping spans;
- `百万元` is not double-counted as `万元`;
- `千港元` is not double-counted as `港元`;
- bare `公司` / `company` is not scope evidence;
- explicit `母公司财务报表`, `公司财务报表`, `company only`, `company financial statements`, `separate financial statements` remain supported;
- overlapping `母公司财务报表` no longer self-conflicts with substring `公司财务报表`.

Final focused suite: `33 passed`.
Final full P0–P6 suite: `189 passed`.

Final live raw fact/evidence SHA remained unchanged after hardening:
- CN facts: `30b9845ecb8b0b9216a6f3fefdd640b9f63fe24fb71984cf1cb44ae0f39cb2c3`
- CN evidence: `17d127ba1b37b7f39a1d9dae8336016261cb6b6ec7ac95ed70e97f3b519e39d2`
- HK facts: `a35142503ed53eeb57c441d6b69e4ce73e6990f2282d436b0cf20636c2222340`
- HK evidence: `1bbf8bdd55a78663419ecffbe1471cb59862426bf70ba2831c6444246da79573`

This confirms the hardening changes corrected matcher semantics without changing accepted live fact/evidence output.

Next:
**P6-H — Code Review**
