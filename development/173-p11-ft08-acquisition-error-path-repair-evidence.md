# P11 FT-08 Acquisition Error-Path Repair Evidence

## 1. Lifecycle and exact identities

- Lifecycle before repair: `ACCEPTANCE_FAILED`.
- Failed production candidate: `2504614265b7a233ef9e4a772544ad63dd6eec37`.
- Formal test plan: `development/170-p11-revised-formal-test-plan.md`.
- Formal test plan commit: `062c419a40c1b49d83efeca3eaa320a3634b6eda`.
- Failed formal evidence: `development/171-p11-formal-test-evidence.md`.
- Failed formal evidence commit: `09d9442ac846bf42e0094613c13665d731c5d031`.
- Acceptance failure review: `development/172-p11-formal-acceptance-review-1.md`.
- Acceptance failure review commit: `d28089f4e26749a7209afb2178564a4fbaea76c3`.
- New production candidate: `9b7fcc9fc37a423eaafd1dde762e9c81d475df9e`.
- Branch: `task/p11-sec-rebuild-development`.
- New production candidate push: PASS, fast-forward from `d28089f` to `9b7fcc9`.

The failed formal acceptance was not resumed. This evidence records a new repair execution after the acceptance failure review.

## 2. Scope and root cause

Production scope was limited to:

- `src/financial_filing_data_foundation/us_sec/acquisition.py`
- `tests/unit/us_sec/test_provider_cli.py`

The root cause was confirmed in `SecAcquirer.acquire`: three conditional function-local imports of `P11Reason` and `SecError` shadowed the module-level imports for the entire function. When an invalid archive index reached a structural validation branch without first taking the invalid-JSON exception branch, Python attempted to use an uninitialized local `SecError` and raised `UnboundLocalError` instead of the required deterministic `SecError(P11Reason.P11_SEC_DISCOVERY_FAILED, ...)`.

Repair applied:

- Removed the three duplicate function-local `.errors` imports.
- Preserved the module-level `from .errors import P11Reason, SecError`.
- Preserved all existing reason codes and acquisition behavior outside this name-binding defect.
- Added deterministic regression coverage for invalid main submissions JSON, invalid historical submissions JSON, invalid archive index JSON, invalid archive directory, invalid archive item list, and invalid archive item records.

Audit result: `acquire()` has `0` function-local `.errors` imports; `acquisition.py` has `1` `.errors` import total, at module scope.

## 3. RED to GREEN evidence

### RED before repair

The new regression test fixture was aligned with the existing SEC chronological selection rules and then run against the failed candidate lineage before the production edit:

```text
3 failed, 3 passed, 5 deselected
```

The three structurally malformed archive-index cases failed with:

```text
UnboundLocalError: cannot access local variable 'SecError' where it is not associated with a value
```

The invalid archive-index JSON, invalid main submissions JSON, and invalid historical submissions JSON cases already returned the expected discovery error because their exception branches executed the local import before raising.

### GREEN after repair

The same six regression cases passed without changing the test selection:

```text
6 passed, 5 deselected
```

All six cases raised `SecError` with reason code `P11_SEC_DISCOVERY_FAILED`:

| Input failure path | Observed result after repair |
| --- | --- |
| Invalid main submissions JSON | `P11_SEC_DISCOVERY_FAILED` |
| Invalid historical submissions JSON | `P11_SEC_DISCOVERY_FAILED` |
| Invalid archive index JSON | `P11_SEC_DISCOVERY_FAILED` |
| Invalid archive directory | `P11_SEC_DISCOVERY_FAILED` |
| Invalid archive item list | `P11_SEC_DISCOVERY_FAILED` |
| Invalid archive item record | `P11_SEC_DISCOVERY_FAILED` |

## 4. Targeted FT-08 acceptance harness

The original acceptance harness script was rerun unchanged:

```text
D:\Codex\FinancialFilingDataFoundation\work\p11-formal-acceptance-25046142\evidence\FT-08-security-harness.py
```

Only the disposable root was shortened to avoid deleting the prior acceptance workspace:

```text
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe
D:\Codex\FinancialFilingDataFoundation\work\p11-formal-acceptance-25046142\evidence\FT-08-security-harness.py
--root D:\t\p11-ft08-repair\harness
```

Result: `PASS`.

The harness passed the malformed archive-index path and the deterministic 403/429 simulations. Receipt summary:

```json
{"malformed_index_calls": 2, "redirect_host_and_cap": true, "remote_script_not_executed": true, "retry_after_max_seconds": 29.99998200000846, "safe_nested_path": true, "source_drift_rejected": true, "status": "PASS", "terminal_403_attempts": 2, "terminal_429_attempts": 3, "unsafe_path_cases": 8}
```

## 5. Verification matrix

All commands used the repaired source tree and short writable pytest temporary directories.

| Gate | Command scope | Result |
| --- | --- | --- |
| Focused provider/acquisition | `tests/unit/us_sec/test_provider_cli.py` | `11 passed` |
| Reviewed FT-08 unit scope | `test_http_discovery.py`, `test_provider_cli.py`, `test_parser.py`, `test_package_registry.py`, `test_cli_runtime.py` | `84 passed` |
| P11 focused | `tests/unit/us_sec` | `100 passed` |
| Full unit | `tests/unit` | `630 passed` |
| CN/HK regression | `tests/unit/identity`, `tests/unit/registry`, `tests/unit/mcp`, `tests/unit/user_cli` | `96 passed` |
| Compile | `python -m compileall -q src tests` | `PASS` |
| Whitespace/error check | `git diff --check` | `PASS` |

The reviewed FT-08 scope was the exact prior test-file set from the formal receipt; the count increased from 78 to 84 only because six acquisition error-path regressions were added.

## 6. Governance preservation

- `SUPPORTED_MARKETS`: unchanged, `("CN", "HK")`.
- `REGISTRY_SCHEMA_VERSION`: unchanged, `1`.
- `SEC_REGISTRY_SCHEMA_VERSION`: unchanged, `3`.
- `VIRTUAL_HTML_NORMALIZER_VERSION`: unchanged, `VIRTUAL_HTML_V4`.
- `SEC_ARTIFACT_SCHEMA`: unchanged, `p11-sec-artifacts-v1`.
- P11 production availability: unchanged.
- Main branch merge: not run.
- Live SEC: NOT RE-RUN DURING REPAIR DEVELOPMENT.
- No parser, registry, discovery, HTTP, identity, or runtime production files were changed.
- No production/test source changed after exact candidate `9b7fcc9fc37a423eaafd1dde762e9c81d475df9e`; this evidence document was added afterward as a separate documentation commit.

## 7. Handoff

Required next action:

```text
CHATGPT NINTH EXACT-CANDIDATE CODE REVIEW OF 9b7fcc9fc37a423eaafd1dde762e9c81d475df9e
```

Formal acceptance must remain paused until that review and a new/revised formal test plan authorize the next execution.
