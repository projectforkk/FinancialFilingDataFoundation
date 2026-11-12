# P11-ISSUE-131 Repair Development Evidence

Date: 2026-11-12

Status: IMPLEMENTATION COMPLETE / DEVELOPER TESTS PASS / READY FOR CHATGPT EXACT-CANDIDATE REVIEW

This document records the development result only. It does not authorize a formal test plan, formal acceptance, production US acceptance, a main merge, or P11 DONE.

## 1. Exact candidate chain

| Item | Exact value |
|---|---|
| Branch | `task/p11-sec-rebuild-development` |
| Starting HEAD | `69d4c16bef9f501653d272efd904909301a468f4` |
| Corrected design baseline | `09e3174b7e19a60cc5955862670fac8931af67db` |
| Previous failed candidate | `5a122478b34e5fce7a3a0e198dd40e5cdb14e07c` |
| Previous evidence commit | `69d4c16bef9f501653d272efd904909301a468f4` |
| New production candidate | `9389d59d68c84762b55b29bedb973db4ea45256a` |
| New candidate parent | `69d4c16bef9f501653d272efd904909301a468f4` |
| Candidate commit | `fix: enforce P11 SEC discovery observation trust boundary` |
| Candidate → evidence | `DOCUMENTATION ONLY — YES` |

The new production candidate contains the source and regression-test changes. No source or test file was changed after that commit. The following evidence commit adds documentation only.

## 2. P11-ISSUE-131 repair

The SEC P7/P8 research-ready path now fails closed unless it has an exact, persisted and verified discovery observation.

- `verify_sec_discovery_observation` re-canonicalizes the observation, verifies its canonical SHA, re-hashes persisted source bytes after base64 decoding, recomputes the candidate fingerprint, and checks stable CIK slot identity, selected accession and `UNAMBIGUOUS` state.
- P7 validation blocks when the observation is missing, missing from Registry, malformed, stale, tampered, or inconsistent with the package slot.
- Ingest and reuse require the verified observation, `PASS`, `COMPATIBLE`, zero blocking issues, and matching selected accession before setting `research_ready=True` or publishing the P8 catalog entry.
- SEC P8 catalog parsing requires `US:CIK##########`, CIK/provider identity, observation SHA, checked-at timestamp, selected accession, `UNAMBIGUOUS` state and a supported fact-source mode. Ticker-only SEC identity is rejected.
- P8 service serving verifies catalog/validation binding, the Registry observation, raw package provenance, evidence provenance, and the observation again on cached bundle reuse. No network acquisition was added.
- `SEC_DISCOVERY_SCHEMA`, `SEC_ARTIFACT_SCHEMA`, `SEC_VALIDATION_SCHEMA`, Registry schema versions, and CN/HK semantics were not bumped or changed.

## 3. Files changed in the production candidate

### Production source

- `src/financial_filing_data_foundation/us_sec/discovery.py`
- `src/financial_filing_data_foundation/us_sec/validation.py`
- `src/financial_filing_data_foundation/us_sec/ingest.py`
- `src/financial_filing_data_foundation/registry/sqlite_registry.py`
- `src/financial_filing_data_foundation/mcp/catalog.py`
- `src/financial_filing_data_foundation/mcp/service.py`

### Regression tests

- `tests/unit/us_sec/test_issue131.py`
- `tests/unit/us_sec/test_validation_p8.py`
- `tests/unit/us_sec/test_parser.py`
- `tests/unit/us_sec/test_corrected_repair.py`
- `tests/unit/us_sec/test_cli_runtime.py`

## 4. Mandatory ISSUE-131 coverage

`tests/unit/us_sec/test_issue131.py` covers T131-01 through T131-13, including:

- missing observation at P7, ingest and reuse;
- missing catalog discovery fields;
- fake observation SHA;
- source bytes/SHA mismatch;
- candidate fingerprint mismatch;
- canonical observation SHA mismatch;
- slot identity mismatch;
- missing or mismatched selected accession;
- non-`UNAMBIGUOUS` state;
- ticker-only company identity;
- valid observation + Registry + package + catalog + P8 serving;
- missing Registry observation;
- Registry source-byte tampering after a cached P8 read.

Existing positive validation/P8 tests were rewritten to provide a valid `SecDiscoveryObservation`; negative tests remain fail-closed rather than being deleted.

## 5. Required developer verification

All commands used the active worktree source through `PYTHONPATH=...\src`, the project `.venv` Python, and short writable Windows pytest basetemp paths.

| Check | Exact result |
|---|---|
| `& 'D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe' -m compileall src tests` | exit `0` |
| `pytest tests/unit/us_sec/test_validation_p8.py -q --basetemp D:\t\p11-issue131-validation-p8` | `8 passed in 1.29s` |
| `pytest tests/unit/us_sec -q --basetemp D:\t\p11-issue131-us` | `130 passed in 9.38s` |
| `pytest tests/unit -q --basetemp D:\t\p11-issue131-unit` | `660 passed in 79.91s` |
| `pytest -q tests/unit/acquisition tests/unit/identity tests/unit/validation tests/unit/registry tests/unit/mcp tests/unit/research tests/unit/review --basetemp D:\t\p11-issue131-cnhk-p0p10` | `371 passed in 62.95s` |
| `git diff --check` before candidate freeze | exit `0` |

The final production candidate freeze was performed only after these checks passed. The focused ISSUE-131/P8 regression run also passed at `23 passed in 4.09s`.

## 6. Known remaining issues and lifecycle boundary

- Legacy SEC catalog entries that do not contain the current trust fields are intentionally rejected fail-closed; they must be regenerated through the current SEC ingest path if needed.
- Independent exact-candidate review is still pending.
- Formal Test Plan = NOT CREATED.
- Formal Acceptance = NOT RUN.
- Main merge = NOT PERFORMED.
- P11 DONE = NO.

Next action: CHATGPT EXACT-CANDIDATE REVIEW OF `9389d59d68c84762b55b29bedb973db4ea45256a`.
