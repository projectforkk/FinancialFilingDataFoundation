# 59 — P9-I Live CN/HK Validation Evidence

Status: PASS — P9-I live validation executed; P9-J/K/L/M remain closed.

Date: 2026-11-04 (Asia/Tokyo)

## 1. Candidate and governance identity

- Branch: task/p9-review-overlay
- Local HEAD before synchronization: 8edece62c5f7d6b95da3bab9c346897d8f102a45
- Remote HEAD before synchronization: ce3d0675bd3c7f8e44f7f2e2c5591b896f8bdde8
- Synchronization: safe fast-forward only; incoming commits were governance/review documentation only.
- Candidate HEAD used for live execution: ce3d0675bd3c7f8e44f7f2e2c5591b896f8bdde8
- P9-G corrective production commit: f3b6dcd1b243c7a77734a1cdfa7459f38d91c842
- P9-G corrective evidence commit: 8edece62c5f7d6b95da3bab9c346897d8f102a45
- P9-G corrective GitHub re-review authorization: b3a4ea36b4164746eabbc5860c8ba4fe369ba2e0
- P9-I live validation instruction commit: 9c43e445b3c24360b99f8cdb3c47bdd473fcf504
- Latest P9-I authorization commit: ce3d0675bd3c7f8e44f7f2e2c5591b896f8bdde8
- Runtime: D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe
- PYTHONPATH: D:\Codex\FinancialFilingDataFoundation\worktrees\active\p9-review-overlay\src

No production, test, design, accepted catalog, runtime/dependency, Registry, P0-P8, P9-J/K/L/M, P10, or P11 files were modified.

## 2. Canonical catalog and base identity

Canonical P8 catalog:

- Path: D:\Codex\FinancialFilingDataFoundation\workspace\mcp\p8-live-catalog.json
- SHA256: e493f2f6a951007c1e5ac932268796d35d33386760f4503d48ff0a7f7a148cdc
- Size: 1507 bytes
- mtime_ns: 1793705566383326400
- Internal loader: financial_filing_data_foundation.mcp.catalog.McpCatalog
- Catalog documents: exactly the requested CN and HK documents.

CN 600519 FY2024:

- Document SHA256: 5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30
- P7 base status: REVIEW_REQUIRED
- P7 base validation_report.json SHA256: b30a4aa63cf2d5d33d2f3e3bd146ea9bd37f16858afc59e02834c487f075b0bc
- P7 base issue set: one REVIEW RAW_PERIOD_COVERAGE_LOW plus two WARNING issues.

HK 00700 FY2024:

- Document SHA256: 70f529984a87ef7f46d9e1db26bb9ef27eef9c01d29c59aabf69e557b479a6a0
- P7 base status: REVIEW_REQUIRED
- P7 base validation_report.json SHA256: fbd2d1328f80c17a29d221675c66885c75cc9039fce153cd8adc4f423f06c01b
- P7 base issue set: four requested REVIEW issues plus two WARNING issues.

Fresh candidate-bound review roots, all absent before this run:

- CN A: D:\Codex\FinancialFilingDataFoundation\workspace\p9-live-review\ce3d0675-cn-a
- CN B: D:\Codex\FinancialFilingDataFoundation\workspace\p9-live-review\ce3d0675-cn-b
- HK A: D:\Codex\FinancialFilingDataFoundation\workspace\p9-live-review\ce3d0675-hk-a
- HK B: D:\Codex\FinancialFilingDataFoundation\workspace\p9-live-review\ce3d0675-hk-b

The previously existing document-SHA-named live directories were not reused or deleted.

## 3. Before/after base-artifact fingerprint

The fingerprint set was derived only from the canonical catalog and contains 23 files: the catalog plus the cataloged P3/P5/P6/P7 files for both documents. The values below are the before values and the identical after values for SHA256, size, and mtime_ns.

| Path | Before SHA256 = After SHA256 | Before size = After size | Before mtime_ns = After mtime_ns |
|---|---|---:|---:|
| D:\Codex\FinancialFilingDataFoundation\workspace\mcp\p8-live-catalog.json | e493f2f6a951007c1e5ac932268796d35d33386760f4503d48ff0a7f7a148cdc | 1507 | 1793705566383326400 |
| D:\Codex\FinancialFilingDataFoundation\workspace\live\p6-inputs\cn\p3\5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30\document.json | db89f5484b2f7e96b04a5d1977ba065882c7a7ae3669eb9fb9b7717656ac61c2 | 769 | 1793697915215738200 |
| D:\Codex\FinancialFilingDataFoundation\workspace\live\p6-inputs\cn\p3\5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30\pages.jsonl | 9bb06df4ad89bdd5de53d4d3fccba19fdf15cc2725c3776da88cbcc063eea3ae | 8475527 | 1793697915173074000 |
| D:\Codex\FinancialFilingDataFoundation\workspace\live\p6-inputs\cn\p3\5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30\sections.jsonl | 3183fe1f94861b53e8a74ba2e448c40c589013c502297755293212cd64af163f | 520812 | 1793697915183332900 |
| D:\Codex\FinancialFilingDataFoundation\workspace\live\p6-inputs\cn\p5\5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30\table_manifest.json | cebbfcad9f3ed5a46c00dcbbec8dddd9622e942552888adbeabebd3785a14ea2 | 1292 | 1793697915829023200 |
| D:\Codex\FinancialFilingDataFoundation\workspace\live\p6-inputs\cn\p5\5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30\tables.jsonl | 11bfbd19854742401fef58852e9b696fbb9e9b29d742c65a81fcf82e80cd3b4a | 2255574 | 1793697915821596600 |
| D:\Codex\FinancialFilingDataFoundation\workspace\live\p6-inputs\cn\p5\5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30\table_groups.jsonl | e5b6ba7e3a960d487009f935f3755b69536efd85bcee4bd60576f4f8622d9708 | 1993 | 1793697915829023200 |
| D:\Codex\FinancialFilingDataFoundation\workspace\live\p6-facts\cn-a\5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30\fact_manifest.json | d76cc20b29f389d4bc858e005e84a74b804869188d67ee23a653eb1c48677a5d | 1556 | 1793700154669924000 |
| D:\Codex\FinancialFilingDataFoundation\workspace\live\p6-facts\cn-a\5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30\raw_facts.jsonl | 30b9845ecb8b0b9216a6f3fefdd640b9f63fe24fb71984cf1cb44ae0f39cb2c3 | 1769780 | 1793700154590576000 |
| D:\Codex\FinancialFilingDataFoundation\workspace\live\p6-facts\cn-a\5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30\evidence.jsonl | 17d127ba1b37b7f39a1d9dae8336016261cb6b6ec7ac95ed70e97f3b519e39d2 | 1974650 | 1793700154625169300 |
| D:\Codex\FinancialFilingDataFoundation\workspace\live\p7-validation\cn-a\5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30\validation_report.json | b30a4aa63cf2d5d33d2f3e3bd146ea9bd37f16858afc59e02834c487f075b0bc | 2714 | 1793701731839633600 |
| D:\Codex\FinancialFilingDataFoundation\workspace\live\p7-validation\cn-a\5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30\issues.jsonl | f8458ac09ff25cfcac9a9ab550f860c0a90de4493b36c111a179bcd10eadffd6 | 1363 | 1793701731839633600 |
| D:\Codex\FinancialFilingDataFoundation\workspace\live\p6-inputs\hk\p3\70f529984a87ef7f46d9e1db26bb9ef27eef9c01d29c59aabf69e557b479a6a0\document.json | 7021f0782d264b0b5ae897275dae77e1b506381c4ec23b1c42641a786be751c7 | 916 | 1793697918641405500 |
| D:\Codex\FinancialFilingDataFoundation\workspace\live\p6-inputs\hk\p3\70f529984a87ef7f46d9e1db26bb9ef27eef9c01d29c59aabf69e557b479a6a0\pages.jsonl | 1930b9257cc0aa48bca9dc72ecdf2e4557db8d785b81f7f39c2e65c1a9929d0c | 10029168 | 1793697918536491800 |
| D:\Codex\FinancialFilingDataFoundation\workspace\live\p6-inputs\hk\p3\70f529984a87ef7f46d9e1db26bb9ef27eef9c01d29c59aabf69e557b479a6a0\sections.jsonl | 9a74f90ff4a9b8938c45b889ccf679ee117f158ebae67f522b37d53da8f688b8 | 396549 | 1793697918554783300 |
| D:\Codex\FinancialFilingDataFoundation\workspace\live\p6-inputs\hk\p5\70f529984a87ef7f46d9e1db26bb9ef27eef9c01d29c59aabf69e557b479a6a0\table_manifest.json | a8c2bc27ab7285a932d3a7e6a467fb9e15386b94df43c285ea5fc8b571af0827 | 1293 | 1793697919887475200 |
| D:\Codex\FinancialFilingDataFoundation\workspace\live\p6-inputs\hk\p5\70f529984a87ef7f46d9e1db26bb9ef27eef9c01d29c59aabf69e557b479a6a0\tables.jsonl | b58f8bb848f7fa398f9dc860a4d17dbc83a291dc7f2d62a89d19e860852bac20 | 2131661 | 1793697919880987100 |
| D:\Codex\FinancialFilingDataFoundation\workspace\live\p6-inputs\hk\p5\70f529984a87ef7f46d9e1db26bb9ef27eef9c01d29c59aabf69e557b479a6a0\table_groups.jsonl | b3937df8da12d6d84cbfc453b431adc898530728e71a5b47ded98ff981ce26f7 | 9495 | 1793697919887064100 |
| D:\Codex\FinancialFilingDataFoundation\workspace\live\p6-facts\hk-a\70f529984a87ef7f46d9e1db26bb9ef27eef9c01d29c59aabf69e557b479a6a0\fact_manifest.json | d3fdbf40356650cda7dd95f73d98db254d60a3b5d1e782e8f9eba1b7201d97d7 | 1635 | 1793700160363646300 |
| D:\Codex\FinancialFilingDataFoundation\workspace\live\p6-facts\hk-a\70f529984a87ef7f46d9e1db26bb9ef27eef9c01d29c59aabf69e557b479a6a0\raw_facts.jsonl | a35142503ed53eeb57c441d6b69e4ce73e6990f2282d436b0cf20636c2222340 | 2461037 | 1793700160218477100 |
| D:\Codex\FinancialFilingDataFoundation\workspace\live\p6-facts\hk-a\70f529984a87ef7f46d9e1db26bb9ef27eef9c01d29c59aabf69e557b479a6a0\evidence.jsonl | 1bbf8bdd55a78663419ecffbe1471cb59862426bf70ba2831c6444246da79573 | 2676038 | 1793700160280083700 |
| D:\Codex\FinancialFilingDataFoundation\workspace\live\p7-validation\hk-a\70f529984a87ef7f46d9e1db26bb9ef27eef9c01d29c59aabf69e557b479a6a0\validation_report.json | fbd2d1328f80c17a29d221675c66885c75cc9039fce153cd8adc4f423f06c01b | 2740 | 1793701742967613900 |
| D:\Codex\FinancialFilingDataFoundation\workspace\live\p7-validation\hk-a\70f529984a87ef7f46d9e1db26bb9ef27eef9c01d29c59aabf69e557b479a6a0\issues.jsonl | b39e2496c52d1a0dd5ea273258c29b57a02eadfa257b2bbf6ce97f1c70f4ec70 | 2716 | 1793701742967613900 |

Result: all 23 paths had identical SHA256, size, and mtime_ns before and after. No catalog, P3, P5, P6, or P7 artifact changed.

## 4. CN 600519 FY2024 live validation

### Base prepare and queue

- Queue count: 1
- Exact reason: RAW_PERIOD_COVERAGE_LOW
- Reviewability: SUPPORTED
- Supported action: SET_PERIOD
- Required evidence types: P5_CELL, P6_EVIDENCE
- Review task ID: 59ebac57b61f85d922a66424fa3468e81fdb0773c0bd25c6c350085058b555a2
- Issue ID: 0a42571e7fd35f3c55f0b7989577d963a6ab39c304e75f4a5e2468c2019662a3
- Queue SHA256: 3fdc6db4fddd3db0620c0aa2db5fdb43f801a00d564a951c3cde61e3f474bd05
- Manifest SHA256: 214714d1be0bc52b0c245c0ac77461295aa5db7a8f376a465ca501f4e79a64e1
- First/reuse queue and manifest bytes were unchanged.

### Evidence-grounded SET_PERIOD

Exactly one resolution was submitted; no mass fill was performed.

- Target: FACT_FIELD raw_fact_id 9b3e2e441e6730c0f3c979816dd764dcb4bf70e6cde16caae9e3897733b9a015, field period
- Fact table/row/column: table 9d9d4afeb104cbcfade4847423919c7b9c60be2efef1011bb4651beb11268075, row 8d5131c633322ad438e43fd5a21b163db00a5b003bede11cca0f2427efcfe807, column 1
- Raw fact: metric 营业收入, raw_value 45,775,517,043.29, raw_period_label null
- Submitted value: 2024
- Evidence ref: P5_CELL table 9d9d4afeb104cbcfade4847423919c7b9c60be2efef1011bb4651beb11268075, cell b44ef475c0de0c3e7241c7990992d63f269254a841fcf93987236d29ca81b046
- Evidence text: 九、 2024 年分季度主要财务数据
- Derived evidence page: 6
- Review resolution ID: 8eece78fbfd7ea8917d0410b8255f0c196d8b7ed29df90b4baad1b19c592f5e9
- Resolution file SHA256: ea8bf0096a9233b0e7f973671cc93726af05dd99d12e479eb3178694820cb3fd
- base_active_resolution_ids: empty list
- base_overlay_set_hash_before: 609b8ac14f871b0fce76203bed7eca1370f8429df39e1436a2bf034452246e56
- Caller reviewed_at: 2026-11-04T09:00:00+09:00

Persisted semantic before state:

- affected_count: 1
- affected_fact_ids: 9b3e2e441e6730c0f3c979816dd764dcb4bf70e6cde16caae9e3897733b9a015
- base raw period: null
- current effective period before overlay: null

Persisted semantic after state:

- expected_affected_fact_count: 1
- submitted/effective period value: 2024

### Materialized CN result

- Raw period remains null on the targeted fact.
- effective_period_label is 2024 on the targeted fact.
- overlay_resolution_ids contains exactly 8eece78fbfd7ea8917d0410b8255f0c196d8b7ed29df90b4baad1b19c592f5e9.
- Period non-null ratio before: 0.061093.
- Period non-null ratio after: 0.061553.
- Because effective coverage remains below 0.10, resolved status remains REVIEW_REQUIRED.
- resolved_reuse_eligible: false.
- Active resolution count: 1.
- overlay_set_hash: 2f7f092a9c91091586704dfe5c1c042055ccf00fe6cf20e80600b87ffa41ea80
- resolved_facts.jsonl SHA256: 9f2a104241b5acf8ea8e1ad44905e8b94931a604cf915607f4d4b162a86214d0
- resolved_issues.jsonl SHA256: 221928af579380f3dc47684edc1e55470bd546edffc84bf175bb3e394a6c143b
- resolution_report.json SHA256: f9659d7ded671b817c8b712e3bc46719ccc5fea536286181825b5e95e5538778
- snapshot_manifest.json SHA256: d1a8f92ce5ec9c57b657c60abd1fc1010f6d67cc7a6b30d8d7f3eb722b68c505
- Report counts: base review 1, resolved review 0, unresolved review 1, unsupported 0, conflict 0.
- CN snapshot was materialized and loaded through the semantic loader in both roots.

## 5. HK 00700 FY2024 live validation

### Base prepare and queue

- Queue count: 4.
- Exact reason set:
  - CORE_STATEMENT_COVERAGE_LOW
  - RAW_PERIOD_COVERAGE_LOW
  - RAW_UNIT_AMBIGUOUS
  - RAW_UNIT_COVERAGE_LOW
- Action mapping:
  - CORE_STATEMENT_COVERAGE_LOW -> CLASSIFY_TABLE_STATEMENT
  - RAW_PERIOD_COVERAGE_LOW -> SET_PERIOD
  - RAW_UNIT_AMBIGUOUS -> SET_UNIT, ATTEST_ISSUE_RESOLVED
  - RAW_UNIT_COVERAGE_LOW -> SET_UNIT
- All four tasks were SUPPORTED.
- Queue SHA256: c3f427b1148851e00e06d48d11717f917af69695dbd37f2267daa151659989c5
- Manifest SHA256: 8ce58c8be36772dac3b2b489195c1315aa2176116cf7042225a4f5360b215fc8
- First/reuse queue and manifest bytes were unchanged.

### Honest zero-overlay result

- No HK resolution was manufactured or submitted.
- No issue was forcibly dismissed or attested.
- Active resolution count: 0.
- overlay_set_hash: ecd91784868125f55c65e43cb60eb60debd94cc3c19fe61604b4cff323b70981
- Resolved status: REVIEW_REQUIRED.
- resolved_reuse_eligible: false.
- All four requested review issues remain UNRESOLVED and SUPPORTED.
- Report counts: base review 4, resolved review 0, unresolved review 4, unsupported 0, conflict 0.
- resolved_facts.jsonl SHA256: 08b6cca367119964669bdc9097e33dec8451b54d9f14fd110d237bd0a0d6470c
- resolved_issues.jsonl SHA256: a4fb351895909b7c5f494bf8b6c4d5413069ab291bd7af6d747a35796b22688b
- resolution_report.json SHA256: cac2f94f3d1c2eb4add0de138182b19f1020c7ef33ff56e5988b683a03b09b8f
- snapshot_manifest.json SHA256: ea19aef05c941de97fe6b71b36a038ab29e69249c091b75f5ae2ade79a320ed8
- HK snapshot was materialized and loaded through the semantic loader in both roots.

## 6. Dual-root and repeated-operation determinism

CN root A/B:

- Queue bytes: identical.
- Manifest semantics: identical after excluding only the designed root-location field review_dir.
- Deterministic task IDs: identical.
- Same caller submission, same caller reviewed_at, target, value, evidence, and justification.
- Resolution ID: identical.
- Canonical resolution payload bytes: identical.
- overlay_set_hash: identical.
- resolved_facts.jsonl bytes: identical.
- resolved_issues.jsonl bytes: identical.
- resolution_report semantic content: identical.
- snapshot_manifest.json bytes: identical.

HK root A/B:

- Queue bytes: identical.
- Manifest semantics: identical after excluding only review_dir.
- Zero-overlay task identity and base semantics: identical.
- overlay_set_hash: identical.
- resolved_facts.jsonl, resolved_issues.jsonl, resolution_report.json, and snapshot_manifest.json bytes: identical.
- Both roots remained REVIEW_REQUIRED with zero active resolutions.

All semantic loader calls succeeded.

## 7. Timings

All timings are wall-clock seconds from the candidate runtime:

| Operation | CN A | CN B | HK A | HK B |
|---|---:|---:|---:|---:|
| prepare first | 3.169458 | 3.160424 | 3.594621 | 3.610157 |
| prepare reuse | 0.144816 | not applicable | 0.159334 | not applicable |
| submit one resolution | 0.281065 | 0.271689 | not applicable | not applicable |
| materialize | 0.599528 | 0.603528 | 0.724056 | 0.728217 |
| semantic snapshot load | 0.604252 | 0.598368 | 0.752219 | 0.736702 |

All measured operations were within the design targets: first prepare <=20s, reuse <=2s, submit <=2s, materialize <=10s, semantic load <=10s.

## 8. Scope and stop conditions

- git status after live execution: no tracked changes; only the pre-existing untracked internal plan docs/superpowers/plans/2026-11-03-p9-recovery-closeout.md.
- git diff --check: PASS.
- tracked diff names before this evidence file: empty.
- P9 review production static scope scan: no network, AI/OpenAI/Codex API, external MCP SDK, UUID/random identity surface.
- No PDF files were created in any candidate-bound live root.
- The live driver used only the canonical catalog and internal P3/P5/P6/P7/P9 loaders; no source PDF was opened, no OCR was invoked, and no network/AI/MCP call was made.
- Only the four fresh candidate-bound review roots changed during live execution.
- No P9-I live artifacts are staged or committed from the workspace roots.
- No design gap or production defect was exposed.
- Blocker: NONE.

## 9. Gate result and next stop

P9-I live validation result: PASS.

This evidence records live validation only. Do not enter P9-J formal Code Review, P9-K Acceptance Freeze, P9-L Independent Acceptance, P9-M Closeout, main merge, P10, or P11. Wait for GitHub review of this evidence.
