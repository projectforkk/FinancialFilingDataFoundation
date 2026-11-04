# 205 — P11-B Environment / SEC Runtime Probe

Status: **PASS — P11-B ENVIRONMENT READY / PRODUCTION CLOSED**

Phase:
P11 — US SEC Provider

Authorization:
`development/204-p11-b-environment-runtime-probe-authorization.md`

Accepted P11-A design baseline:
`5877a238f5af6102ef48e56141cdb893590b6aab`

Formal probe root:
`D:\Codex\FinancialFilingDataFoundation\workspace\scratch\p11-b-probe\formal`

## 1. Scope integrity

PASS:

- all formal venv/cache/temp/download/probe files are below the authorized project-local scratch path;
- no root/global Python package mutation;
- no main FFDF venv dependency mutation;
- no `src/`, `tests/`, `integration/` or production `runtime-locks/` change;
- no P11 production code;
- no P11-C or later implementation during this probe.

The main FFDF venv still reports `pip` absent after the probe.

## 2. Main environment

Observed FFDF main runtime:

- Python `3.14.9`;
- 64-bit ARM64 build;
- Windows 11 ARM64 host.

This runtime was observed only and was not mutated.

## 3. Project-local Python 3.12 AMD64 viability

An already-present Astral CPython `3.12.14` x86_64 interpreter was used only as the base interpreter for the disposable project-local probe venv.

Formal probe venv:
`D:\Codex\FinancialFilingDataFoundation\workspace\scratch\p11-b-probe\formal\venv`

Proof:

- Python `3.12.14`;
- `sys.version` reports `MSC v.1944 64 bit (AMD64)`;
- pointer width = 64-bit;
- executable PE machine = `0x8664` / AMD64;
- base interpreter was not modified.

Result: **PASS**.

## 4. Arelle / lxml candidate viability

Formal binary-only resolution under project-local TEMP/cache/download paths succeeded.

Resolved 23 wheels.

Exact identities:

- `arelle-release==2.47.4`;
- wheel `arelle_release-2.47.4-py3-none-any.whl`;
- SHA256 `366b9ced1a9e5058a31f4ffd347ec6fc6900c6931ade3d97a36d7836151fe3e1`;
- this matches the Arelle wheel hash previously recorded in `development/144-p11-environment-interface-audit.md`;
- `lxml==6.1.3`;
- wheel `lxml-6.1.3-cp312-cp312-win_amd64.whl`;
- SHA256 `3e9a00d1c2c30936f7add097c41afc5da6556c580909104aafd382cac92a855c`.

The wheel set was installed only into the disposable formal probe venv. Import verification:

- Arelle metadata version = `2.47.4`;
- lxml distribution version = `6.1.3`;
- lxml runtime version = `6.1.3.0`.

Result: **PASS**.

## 5. Runtime-lock strategy

Formal reproducibility evidence:

- `pip-freeze.txt` SHA256 = `c8702ce815f1218e0fda3f3d58d027c90bee7f379602c3dfc93b9b6493d3e544`;
- `wheel-hashes.txt` SHA256 = `eb743523c99d390a34609ff3590e86dec2a148c08e89452b16a49dd83d9cdbd6`;
- 23 exact downloaded wheel artifacts are available under the project-local formal download directory;
- wheel filenames and SHA256 values are sufficient to construct a future hash-locked runtime descriptor.

This is evidence of lock viability only. It is not the production P11 runtime lock.

Result: **PASS**.

## 6. SEC network/TLS and configured User-Agent path

Raw TLS probe:

- `www.sec.gov` => TLS 1.3 / `TLS_AES_256_GCM_SHA384` / certificate CN `www.sec.gov`;
- `data.sec.gov` => TLS 1.3 / `TLS_AES_256_GCM_SHA384` / certificate CN `www.sec.gov`.

A pre-existing `SEC_USER_AGENT` configuration was present. Its value was deliberately neither printed nor stored in evidence.

The formal HTTP probe consumed that configured value directly and sent requests only to accepted SEC hosts.

Results:

- `https://data.sec.gov/submissions/CIK0000320193.json` => HTTP `200`, `application/json`;
- `https://www.sec.gov/files/company_tickers.json` => HTTP `200`, `application/json`.

Formal result file:

- `sec-http-result.json` SHA256 = `3e631f4f30e3424d990323b8a51d855ee640b8d174b751dd326c098510433769`.

This proves both SEC network/TLS reachability and viability of an explicit configured User-Agent route without inventing or exposing contact identity.

The exact production User-Agent grammar/config source, timeout, retry, response-size and rate-lock behavior remain intentionally deferred to the mandatory P11-D Design-First HTTP-contract freeze.

An earlier scratch diagnostic using a non-contact project-label probe User-Agent returned HTTP 403. That diagnostic predates the reconciled formal probe boundary and is **not** acceptance evidence. No production conclusion is based on it.

Result: **PASS**.

## 7. Atomic same-filesystem non-replacing directory commit

Formal runtime primitive:
`kernel32.MoveFileExW(source, destination, flags=0)`

Properties tested:

- project-local `D:` source/destination;
- same-filesystem identity confirmed;
- no `MOVEFILE_REPLACE_EXISTING`;
- no `MOVEFILE_COPY_ALLOWED`;
- no copy/delete/replace fallback.

Exact outcome mapping:

- absent destination => `COMMITTED_NEW`, WinError `0`;
- existing destination => `DESTINATION_EXISTS`, WinError `183`;
- missing source => `COMMIT_ERROR`, WinError `2`.

Concurrency:

- 20 independent two-process races;
- 20/20 produced exactly one `COMMITTED_NEW` and one `DESTINATION_EXISTS`;
- destination contained only winner content;
- loser source/staging directory remained intact;
- no merge, overwrite or replacement.

Formal result:

- `no-replace-result.json` SHA256 = `e8bbb64573bd2887be6a02098edb81d77398882256241e90268800e4d529cc1c`.

Result: **PASS**.

## 8. Gate verdict

# PASS

P11-B Environment / SEC Runtime Probe is **CLOSED / PASS**.

Proven environment capabilities:

- project-local Python 3.12 AMD64 viability on the Windows ARM64 host;
- Arelle 2.47.4 and lxml 6.1.3 viable with exact wheel/hash capture;
- reproducible hash-lock strategy viable;
- SEC TLS and configured-User-Agent HTTP access viable;
- target filesystem exposes the required same-filesystem no-replace directory commit primitive with distinguishable destination-exists semantics.

This PASS does not authorize a permanent P11 runtime installation and does not authorize P11 provider production.

P11-C Identity / Period Contract may be separately authorized next.