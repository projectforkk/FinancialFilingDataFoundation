# 204 — P11-B Environment / SEC Runtime Probe Authorization

Status: **AUTHORIZED — P11-B ISOLATED PROBE ONLY / PRODUCTION CLOSED**

Phase:
P11 — US SEC Provider

Accepted P11-A design baseline:
`5877a238f5af6102ef48e56141cdb893590b6aab`

P11-A result:
`development/203-p11-final-detached-design-review-result.md = PASS`

## Authorized scope

P11-B only.

Read-only / isolated environment and runtime viability probe.

Allowed project-local mutable area:
`D:\Codex\FinancialFilingDataFoundation\workspace\scratch\p11-b-probe`

Allowed evidence output:
`development/205-p11-environment-runtime-probe.md`

Confirm:

1. main FFDF Python architecture/version;
2. project-local Python 3.12 AMD64 viability;
3. `arelle-release==2.47.4` exact candidate provenance/availability;
4. lxml CPython 3.12 Windows AMD64 wheel viability;
5. candidate runtime-lock strategy;
6. SEC TCP/TLS reachability to accepted SEC host(s);
7. explicit User-Agent configuration path without fabricating/defaulting contact identity;
8. all temp/cache/download paths remain below project root;
9. no root/global Python mutation;
10. target filesystem supports an atomic same-filesystem non-replacing directory commit primitive with distinguishable destination-exists behavior.

## Allowed probe actions

- inspect installed interpreters and architecture read-only;
- create/delete disposable files/directories only under the authorized scratch path;
- create a disposable project-local Python 3.12 virtual environment under the authorized scratch path if an existing Python 3.12 AMD64 interpreter is available;
- query package metadata and download wheel artifacts to authorized scratch with cache/temp redirected under project root;
- compute SHA256/inspect wheel metadata without installing it into production/runtime;
- perform raw TCP/TLS handshake to accepted SEC hosts;
- inspect whether a P11 SEC User-Agent configuration value/path already exists;
- exercise scratch-only filesystem commit primitives.

## Explicitly prohibited

- no permanent P11 runtime installation;
- no package install into root/global Python;
- no modification of `src/`, `tests/`, `integration/`, `runtime-locks/`, P0-P10 accepted files, or main environment dependency state;
- no SEC HTTP request using fabricated/default contact identity;
- no arbitrary host access;
- no production code;
- no P11-C or later implementation;
- no Research MCP / Semantic Resolver production.

If no legitimate configured SEC User-Agent value exists, record HTTP request execution as intentionally NOT_EXECUTED; this does not substitute a fake identity. P11-D must separately freeze exact User-Agent grammar/config source before HTTP production code.

Verdict:
- PASS = environment/runtime viability proven within this scope;
- BLOCKED = a required viability property cannot be proven safely;
- FAIL = probe contradicts accepted design assumptions.

P11 provider production remains CLOSED.