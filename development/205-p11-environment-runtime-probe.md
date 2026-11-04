# 205 — P11-B Environment / SEC Runtime Probe

Status: **PASS — P11-B CLOSED / P11-C NEXT / PRODUCTION CLOSED**

Phase:
P11 — US SEC Provider

Authorization:
`development/204-p11-b-environment-runtime-probe-authorization.md`

Accepted P11-A baseline:
`5877a238f5af6102ef48e56141cdb893590b6aab`

Accepted probe scratch:
`D:\Codex\FinancialFilingDataFoundation\workspace\scratch\p11-b-probe\accepted`

## 1. Scope / mutation guard

PASS.

- no P11 production code changed;
- `src/`, `tests/`, `integration/`, production `runtime-locks/` diff = NONE;
- main FFDF `.venv` was not mutated and still has no pip;
- existing project-local Python 3.12 runtime was not mutated, still has no pip, and does not contain Arelle;
- no root/global Python package install;
- all accepted probe temp/cache/report/filesystem artifacts are under the FFDF project root.

Earlier exploratory disposable scratch venvs were excluded from formal acceptance and were deleted after the accepted probe. Their install/HTTP diagnostic results are not used for this PASS.

## 2. Main FFDF runtime

Observed only:

- Python `3.14.9`;
- 64-bit ARM64 build;
- Windows 11 ARM64 host.

Result: **PASS / unchanged**.

## 3. Existing project-local Python 3.12 AMD64 viability

Accepted runtime observed at:

`runtimes/ffdf-mcp-2.3.0/.venv/Scripts/python.exe`

Runtime identity:

- CPython `3.12.14`;
- `sys.version` = `MSC v.1944 64 bit (AMD64)`;
- `sysconfig.get_platform()` = `win-amd64`;
- 64-bit runtime;
- native Windows machine = ARM64.

The venv launcher PE itself is ARM64 (`0xaa64`) on this host; this is a Windows ARM64 redirector/launcher detail and is not the CPython wheel ABI. The authoritative runtime/wheel ABI signals are the Python build identity and `sysconfig` platform, both AMD64/win-amd64.

Result: **PASS**.

## 4. Arelle / lxml package viability without runtime install

Exact downloaded artifacts were inspected directly from wheel metadata; no package install is part of the accepted probe.

Arelle:

- `arelle-release==2.47.4`;
- `arelle_release-2.47.4-py3-none-any.whl`;
- SHA256 `366b9ced1a9e5058a31f4ffd347ec6fc6900c6931ade3d97a36d7836151fe3e1`;
- `Requires-Python >=3.11`;
- hash matches `development/144-p11-environment-interface-audit.md`.

lxml:

- `lxml==6.1.3`;
- `lxml-6.1.3-cp312-cp312-win_amd64.whl`;
- SHA256 `3e9a00d1c2c30936f7add097c41afc5da6556c580909104aafd382cac92a855c`;
- `Requires-Python >=3.8`.

A disposable resolver venv under project scratch was created only to obtain pip. Using only the already-downloaded local wheels:

`pip install --dry-run --ignore-installed --no-index --find-links ... arelle-release==2.47.4`

resolved the complete 23-package candidate set successfully and installed nothing.

Dry-run report:

- `arelle-dry-run-report.json` SHA256 = `a153221560563a4bbaa7f625ef4ddc4e1ed708207966570bc5bc8d49ce1e6fa7`.

The resolver venv was deleted after the report was created.

Result: **PASS**.

## 5. Runtime-lock strategy

PASS.

The accepted probe demonstrates that the P11 runtime can be frozen using:

- exact CPython 3.12 / `win-amd64` identity;
- exact `package==version` set from the 23-package dry-run;
- exact wheel filenames and SHA256 values already captured project-locally;
- existing FFDF runtime-lock conventions as the production format precedent.

No P11 production runtime lock was created or modified by P11-B. Final parser dependency/runtime lock remains subject to the later authorized P11-F parser-contract freeze.

## 6. SEC network / TLS reachability

PASS without HTTP content acquisition.

Raw TLS handshakes succeeded:

- `www.sec.gov:443` => TLS 1.3 / `TLS_AES_256_GCM_SHA384` / certificate CN `www.sec.gov`;
- `data.sec.gov:443` => TLS 1.3 / `TLS_AES_256_GCM_SHA384` / certificate CN `www.sec.gov`.

This proves target host/network/TLS reachability required by P11-B.

## 7. Explicit User-Agent configuration boundary

PASS for configuration-path viability.

A pre-existing explicit configuration path is present:

`environment:SEC_USER_AGENT`

Only non-secret shape was inspected and persisted:

- present = true;
- non-empty = true;
- length = 32;
- ASCII = true;
- contains whitespace = true;
- contains `@` = true.

The value itself was neither printed nor persisted in accepted evidence.

Accepted P11-B HTTP behavior:

`NOT_EXECUTED_BY_DESIGN`

P11-B does not need to expose or transmit the configured contact identity. Exact production User-Agent grammar/config source, rate gate, timeout, retry and response-size rules remain gated by the mandatory P11-D Design-First HTTP-contract freeze.

Earlier exploratory scratch HTTP diagnostics are not P11-B acceptance evidence.

## 8. Atomic same-filesystem non-replacing directory commit

PASS.

Target primitive:

`kernel32.MoveFileExW(source, destination, flags=0)`

Properties:

- source and final paths on the same project-local `D:` filesystem;
- no `MOVEFILE_REPLACE_EXISTING`;
- no `MOVEFILE_COPY_ALLOWED`;
- no copy/delete/replace fallback.

Exact outcome classes observed:

- destination absent => `COMMITTED_NEW`, WinError `0`;
- destination already exists => `DESTINATION_EXISTS`, WinError `183`;
- missing source => `COMMIT_ERROR`, WinError `2`.

Concurrency proof on the accepted project-local Python 3.12 runtime:

- 20 independent two-process races;
- 20/20 produced exactly one `COMMITTED_NEW` + one `DESTINATION_EXISTS`;
- final directory contained winner content only;
- losing source/staging directory remained intact;
- no merge/overwrite/replacement.

Accepted result:

- `no-replace-result.json` SHA256 = `cb57348e585ee368e49eecb5e6d769cc78b3d50d4d52da5bbd4e29d877a672d4`.

Result: **PASS**.

## Verdict

# PASS

P11-B Environment / SEC Runtime Probe is CLOSED / PASS.

P11-C Identity / Period Contract is NEXT and requires separate authorization.

P11 provider production remains CLOSED.

Research MCP production remains NOT AUTHORIZED.

Semantic Resolver production remains NOT AUTHORIZED.