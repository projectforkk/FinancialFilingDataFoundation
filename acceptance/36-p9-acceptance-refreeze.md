# 36 — P9 Independent Acceptance Refreeze

状态：**P9-K REFREEZE — SUPERSEDES ACCEPTANCE/34 COMMAND PATHS**

Phase:
`P9 — Codex Review Overlay`

Reason:
`acceptance/35-p9-acceptance-attempt-result.md` = **BLOCKED**

Design amendment:
`2b396a1c6fb1c8738b5e051ec503949429b00212`

Issue:
`P9-ISSUE-011`

## 1. What remains frozen unchanged

All semantic/product/live fixture/security/performance requirements in:

`acceptance/34-p9-final-acceptance-freeze.md`

remain frozen unchanged, including:

- accepted P8 baseline
- production candidate `66308627d1dd1f0af2f02ff3f18d3e91f33dcc8d`
- reviewed/evidence candidate `e7822438c80964f29960c3dafa278a5ede8cdc44`
- formal review PASS `d7f0a820633f30136598eb30a2e5b7b9ac868675`
- canonical catalog SHA
- 23-file base fingerprint contract
- CN/HK queue/reason fixtures
- exact CN resolution submission/ID/hashes
- HK zero-overlay expectations
- synthetic golden expectations
- 55 mandatory acceptance items
- security/CLI probe expectations
- performance gates
- normalized-LF harness SHA:
  `1e07b37e061e5b59f56fdac11c021ebbb843b633162047c8640c7b54c2883146`

No production/test/harness content is changed by this refreeze.

## 2. Superseded command detail

The following original acceptance/34 basetemps are invalid and MUST NOT be
used:

- `worktrees\t\af`
- `worktrees\t\ag`
- `worktrees\t\au`

They are superseded because a representative deep snapshot path reached
260 characters and failed on this Windows environment.

The blocked attempt at frozen SHA
`3c5a632d6026dcb5e388b747d1e6972b15b7776e`
remains historical evidence and must not be reported as a product test failure.

## 3. New frozen candidate

The exact new Independent Acceptance candidate is the commit containing this
refreeze file.

P9-L must create a NEW detached acceptance worktree at that exact commit.
Do not reuse:
`worktrees\acceptance\p9-3c5a632`.

## 4. Required one-character pytest roots

Exactly:

- focused:
  `D:\Codex\FinancialFilingDataFoundation\worktrees\t\a`
- synthetic:
  `D:\Codex\FinancialFilingDataFoundation\worktrees\t\b`
- full:
  `D:\Codex\FinancialFilingDataFoundation\worktrees\t\c`

Each suffix is exactly one character.

These three paths were verified absent before this refreeze.

No longer path may be substituted during acceptance.

## 5. Exact rerun commands

Let:
- `<refrozen-sha>` = commit containing this file
- `<shortsha>` = first 7 chars
- detached acceptance worktree =
  `D:\Codex\FinancialFilingDataFoundation\worktrees\acceptance\p9-<shortsha>`

Create:

```powershell
git worktree add --detach D:\Codex\FinancialFilingDataFoundation\worktrees\acceptance\p9-<shortsha> <refrozen-sha>
```

Set:

```powershell
$env:PYTHONPATH="D:\Codex\FinancialFilingDataFoundation\worktrees\acceptance\p9-<shortsha>\src"
$env:PYTHONDONTWRITEBYTECODE="1"
```

Compile:

```powershell
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -B -m compileall -q src\financial_filing_data_foundation\review
```

Focused:

```powershell
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -B -m pytest tests\unit\review\test_review_overlay.py -q -p no:cacheprovider --basetemp D:\Codex\FinancialFilingDataFoundation\worktrees\t\a
```

Expected:
`73 passed`

Synthetic:

```powershell
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -B -m pytest tests\unit\review\test_review_overlay.py -q -p no:cacheprovider -k "resolved_view_fills_nulls_without_mutating_raw_and_can_reach_pass or synthetic_golden_resolves_period_unit_and_core_to_pass" --basetemp D:\Codex\FinancialFilingDataFoundation\worktrees\t\b
```

Expected:
`2 passed, 71 deselected`

Full:

```powershell
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -B -m pytest tests\unit -q -p no:cacheprovider --basetemp D:\Codex\FinancialFilingDataFoundation\worktrees\t\c
```

Expected:
`308 passed`

Harness normalized-LF SHA and live/security/CLI/immutability/performance
commands remain exactly as acceptance/34, except that `--source-root` must
point to the NEW refrozen detached acceptance worktree and live work/output
paths use the NEW `<shortsha>`.

## 6. Acceptance result

Allowed verdict:
`PASS / FAIL / BLOCKED`

PASS requires every acceptance/34 condition plus:
- all three one-character-root pytest runs PASS；
- no recurrence of Windows path-length failure；
- detached refrozen HEAD stays clean；
- harness returns PASS with `base_changed=[]`.

PASS authorizes P9-M Closeout only.

P9-M/main/P10/P11 remain closed until PASS.
