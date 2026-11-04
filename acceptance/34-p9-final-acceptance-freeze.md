# 34 — P9 Final Independent Acceptance Freeze

状态：**P9-K FINAL ACCEPTANCE FREEZE**

Phase:
`P9 — Codex Review Overlay`

Repository:
`projectforkk/FinancialFilingDataFoundation`

Branch:
`task/p9-review-overlay`

Accepted baseline before P9:
`ee934ad05812c69b79f76db43e62cfd4050efb8e`

Final production candidate:
`66308627d1dd1f0af2f02ff3f18d3e91f33dcc8d`

Final reviewed/evidence candidate:
`e7822438c80964f29960c3dafa278a5ede8cdc44`

Final formal review result commit:
`d7f0a820633f30136598eb30a2e5b7b9ac868675`

Final formal review result:
`development/74-p9-jr3-formal-rereview-result.md` = **PASS**

Final design amendment baseline:
`4b7a6660f1359ca8badbd0761db747376bcc92e2`

## 1. Frozen candidate

The exact P9 Independent Acceptance candidate is the commit containing this
freeze file and:

`acceptance/p9_independent_acceptance_harness.py`

After committing this freeze, no moving branch HEAD may be substituted.

Independent Acceptance must create a fresh detached acceptance worktree at the
exact freeze commit.

No production, test, design, runtime/dependency, accepted catalog, P3/P5/P6/P7/P8
artifact, or source PDF may be modified during P9-L.

## 2. Project-root boundary

All P9 acceptance work, including detached worktree, pytest temp directories,
live acceptance roots and output reports, must remain inside:

`D:\Codex\FinancialFilingDataFoundation`

Do not use external temp roots.

Use short ignored temp roots under `worktrees/t/` because deep P9
content-addressed snapshot paths approach the Windows path-length boundary.

## 3. Main runtime

`D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe`

Expected:
- Python 3.14.9 ARM64
- no dependency installation/upgrade
- no external MCP SDK requirement for P9

## 4. Acceptance harness

Tracked harness:

`acceptance/p9_independent_acceptance_harness.py`

Frozen normalized-LF SHA256:

`1e07b37e061e5b59f56fdac11c021ebbb843b633162047c8640c7b54c2883146`

Because this Windows repository uses `core.autocrlf=true`, acceptance must
normalize `CRLF -> LF` before hashing this harness. The hash freezes content,
not checkout-specific line endings.

The harness is acceptance-only orchestration. It must not mutate source,
tests, design, runtime/dependencies, Registry, catalog, P3/P5/P6/P7/P8, or
source PDFs.

It must:
- run direct item-55 payload-security probes；
- run raw subprocess item-53 CLI parser/help/runtime probes；
- use the canonical P8 catalog；
- fingerprint exactly 23 canonical catalog/P3/P5/P6/P7 files before/after；
- create fresh CN/HK review roots；
- reproduce the exact CN evidence-grounded resolution；
- keep HK zero-overlay and unresolved honestly；
- assert deterministic queue/resolution/snapshot identities；
- enforce P9 performance gates；
- report `base_changed=[]`。

## 5. Canonical catalog and base identity

Catalog:

`D:\Codex\FinancialFilingDataFoundation\workspace\mcp\p8-live-catalog.json`

SHA256:

`e493f2f6a951007c1e5ac932268796d35d33386760f4503d48ff0a7f7a148cdc`

Exactly:

CN 600519 FY2024:
- document SHA:
  `5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30`
- P7 validation_report SHA:
  `b30a4aa63cf2d5d33d2f3e3bd146ea9bd37f16858afc59e02834c487f075b0bc`
- base status: `REVIEW_REQUIRED`

HK 00700 FY2024:
- document SHA:
  `70f529984a87ef7f46d9e1db26bb9ef27eef9c01d29c59aabf69e557b479a6a0`
- P7 validation_report SHA:
  `fbd2d1328f80c17a29d221675c66885c75cc9039fce153cd8adc4f423f06c01b`
- base status: `REVIEW_REQUIRED`

The complete frozen 23-file SHA256/size/mtime_ns baseline is the table in
`development/59-p9-i-live-evidence.md` section 3.

Acceptance must recompute all 23 fingerprints before/after live operations and
require exact equality. It must not restore or rewrite a changed base artifact.

## 6. Frozen CN live fixture

Queue:
- count: 1
- reason: `RAW_PERIOD_COVERAGE_LOW`
- task ID:
  `59ebac57b61f85d922a66424fa3468e81fdb0773c0bd25c6c350085058b555a2`
- issue ID:
  `0a42571e7fd35f3c55f0b7989577d963a6ab39c304e75f4a5e2468c2019662a3`
- queue SHA256:
  `3fdc6db4fddd3db0620c0aa2db5fdb43f801a00d564a951c3cde61e3f474bd05`

Exact submission:
- action: `SET_PERIOD`
- target: FACT_FIELD
- raw_fact_id:
  `9b3e2e441e6730c0f3c979816dd764dcb4bf70e6cde16caae9e3897733b9a015`
- field: period
- value: `2024`
- P5 table:
  `9d9d4afeb104cbcfade4847423919c7b9c60be2efef1011bb4651beb11268075`
- P5 cell:
  `b44ef475c0de0c3e7241c7990992d63f269254a841fcf93987236d29ca81b046`
- reviewer_type: `CODEX`
- reviewer_id: `p9-live-validation`
- reviewed_at: `2026-11-04T09:00:00+09:00`
- justification:
  `P5 同表标题明确包含 2024，支持该 raw-null fact 的有效期间标签。`

Expected:
- resolution ID:
  `8eece78fbfd7ea8917d0410b8255f0c196d8b7ed29df90b4baad1b19c592f5e9`
- resolution file SHA256:
  `ea8bf0096a9233b0e7f973671cc93726af05dd99d12e479eb3178694820cb3fd`
- overlay_set_hash:
  `2f7f092a9c91091586704dfe5c1c042055ccf00fe6cf20e80600b87ffa41ea80`
- raw_period_label remains null
- effective_period_label = `2024`
- final status remains `REVIEW_REQUIRED`
- resolved_reuse_eligible = false
- active resolution count = 1
- resolved_facts SHA256:
  `9f2a104241b5acf8ea8e1ad44905e8b94931a604cf915607f4d4b162a86214d0`
- resolved_issues SHA256:
  `221928af579380f3dc47684edc1e55470bd546edffc84bf175bb3e394a6c143b`
- resolution_report SHA256:
  `f9659d7ded671b817c8b712e3bc46719ccc5fea536286181825b5e95e5538778`
- snapshot_manifest SHA256:
  `d1a8f92ce5ec9c57b657c60abd1fc1010f6d67cc7a6b30d8d7f3eb722b68c505`

## 7. Frozen HK live fixture

Queue:
- count: 4
- exact reasons:
  - `CORE_STATEMENT_COVERAGE_LOW`
  - `RAW_PERIOD_COVERAGE_LOW`
  - `RAW_UNIT_AMBIGUOUS`
  - `RAW_UNIT_COVERAGE_LOW`
- queue SHA256:
  `c3f427b1148851e00e06d48d11717f917af69695dbd37f2267daa151659989c5`

Acceptance must submit no fabricated HK resolution.

Expected:
- active resolution count = 0
- overlay_set_hash:
  `ecd91784868125f55c65e43cb60eb60debd94cc3c19fe61604b4cff323b70981`
- final status = `REVIEW_REQUIRED`
- resolved_reuse_eligible = false
- all four REVIEW tasks remain unresolved
- resolved_facts SHA256:
  `08b6cca367119964669bdc9097e33dec8451b54d9f14fd110d237bd0a0d6470c`
- resolved_issues SHA256:
  `a4fb351895909b7c5f494bf8b6c4d5413069ab291bd7af6d747a35796b22688b`
- resolution_report SHA256:
  `cac2f94f3d1c2eb4add0de138182b19f1020c7ef33ff56e5988b683a03b09b8f`
- snapshot_manifest SHA256:
  `ea19aef05c941de97fe6b71b36a038ab29e69249c091b75f5ae2ade79a320ed8`

## 8. Synthetic golden

Independent Acceptance must run the focused synthetic tests:

`resolved_view_fills_nulls_without_mutating_raw_and_can_reach_pass`

and

`synthetic_golden_resolves_period_unit_and_core_to_pass`

Expected current result:

`2 passed, 71 deselected`

They must independently prove:
- base `REVIEW_REQUIRED`
- supported period/unit/core review
- evidence-grounded resolutions
- resolved materialization
- all base REVIEW issues resolved
- final `PASS`
- `resolved_reuse_eligible=true`
- deterministic resolved ParsedDataRecord
- raw source unchanged

## 9. Current regression counts

Frozen current counts:

- focused P9 suite: `73 passed`
- full unit suite: `308 passed`

Any fail blocks acceptance.

Count increases caused only by acceptance infrastructure are not expected,
because the harness is outside tests.

## 10. Performance gates

From design/22:

- prepare first <= 20s
- prepare reuse <= 2s
- submit one resolution <= 2s
- materialize <= 10s
- semantic snapshot load <= 10s

P9-I historical measurements are in
`development/59-p9-i-live-evidence.md` section 7.

P9-L must measure them again in the fresh acceptance roots and all must PASS.

## 11. Exact acceptance commands

Let:
- `<frozen-sha>` = commit containing this file
- `<shortsha>` = first 7 hex chars of frozen SHA
- acceptance worktree =
  `D:\Codex\FinancialFilingDataFoundation\worktrees\acceptance\p9-<shortsha>`

Create detached acceptance worktree from canonical repo root:

```powershell
git worktree add --detach D:\Codex\FinancialFilingDataFoundation\worktrees\acceptance\p9-<shortsha> <frozen-sha>
```

Set:

```powershell
$env:PYTHONPATH="D:\Codex\FinancialFilingDataFoundation\worktrees\acceptance\p9-<shortsha>\src"
$env:PYTHONDONTWRITEBYTECODE="1"
```

Compile/import:

```powershell
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -B -m compileall -q src\financial_filing_data_foundation\review
```

Focused:

```powershell
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -B -m pytest tests\unit\review\test_review_overlay.py -q -p no:cacheprovider --basetemp D:\Codex\FinancialFilingDataFoundation\worktrees\t\af
```

Synthetic:

```powershell
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -B -m pytest tests\unit\review\test_review_overlay.py -q -p no:cacheprovider -k "resolved_view_fills_nulls_without_mutating_raw_and_can_reach_pass or synthetic_golden_resolves_period_unit_and_core_to_pass" --basetemp D:\Codex\FinancialFilingDataFoundation\worktrees\t\ag
```

Full:

```powershell
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -B -m pytest tests\unit -q -p no:cacheprovider --basetemp D:\Codex\FinancialFilingDataFoundation\worktrees\t\au
```

Harness normalized-LF SHA:

```powershell
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -c "from pathlib import Path; import hashlib; b=Path(r'acceptance\p9_independent_acceptance_harness.py').read_bytes().replace(b'\r\n',b'\n'); print(hashlib.sha256(b).hexdigest())"
```

Expected:
`1e07b37e061e5b59f56fdac11c021ebbb843b633162047c8640c7b54c2883146`

Live/security/CLI/immutability/performance harness:

```powershell
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -B acceptance\p9_independent_acceptance_harness.py --project-root D:\Codex\FinancialFilingDataFoundation --source-root D:\Codex\FinancialFilingDataFoundation\worktrees\acceptance\p9-<shortsha> --catalog D:\Codex\FinancialFilingDataFoundation\workspace\mcp\p8-live-catalog.json --work-root D:\Codex\FinancialFilingDataFoundation\workspace\p9-acceptance\<shortsha> --output D:\Codex\FinancialFilingDataFoundation\workspace\p9-acceptance\<shortsha>-result.json
```

Static/scope:

```powershell
git diff --check
git status --short --branch --untracked-files=all
```

Additionally compare accepted P8 `ee934ad...` to frozen candidate and require
no unintended source/test path outside:
- `src/financial_filing_data_foundation/review/*`
- `tests/unit/review/test_review_overlay.py`

## 12. Security / scope

Acceptance must independently verify:
- no source PDF open
- no network/AI/OpenAI/Codex API
- no external MCP SDK
- no Registry mutation
- no P8 tool mutation
- no P10/P11 implementation
- no arbitrary executable/storage bypass in resolution payload
- CLI JSON contract, including help/parser failures
- P9 review roots only are mutated

## 13. Acceptance 55 items

`acceptance/32-p9-acceptance-instruction.md` items 1-55 are all mandatory.

The formal review PASS does not replace Independent Acceptance.

## 14. Verdict

Allowed final verdict:

`PASS / FAIL / BLOCKED`

PASS requires:
- exact frozen HEAD remains stable/clean
- focused/full/synthetic tests PASS
- all 55 mandatory items have credible evidence
- harness returns `status=PASS`
- `base_changed=[]`
- all performance gates PASS
- no blocker/new correctness/security finding

PASS authorizes P9-M Closeout only.

P10/P11/Research MCP production/Semantic Resolver production remain prohibited
during P9-L.
