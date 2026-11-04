# 70 — P9-JR2 Formal Detached Re-Review Result

Status: **FAIL / CHANGES REQUIRED**

Exact reviewed candidate:
`e010d61c2227a3496b51cb8cc5f54df7e550cb6d`

Production correction:
`f02504a69d7bc454b674a4ad347aaeecad38f6be`

Detached worktree:
`D:\Codex\FinancialFilingDataFoundation\worktrees\review\p9-jr2-e010d61`

Detached status remained clean.

## Verification

- compile/import: PASS / `IMPORT_OK`
- focused P9: **64 passed**
- full unit: **299 passed**
- accepted-P8 scope: PASS
- `git diff --check`: PASS
- prior P9-J and P9-JR path/SQL/help probes: PASS
- raw parser/help/runtime diagnostic probes: PASS
- broad URL/path/SQL/Python/credential probes: PASS

The candidate successfully closes the findings recorded in
`development/66-p9-jr-formal-rereview-result.md`:

- `/tmp` rejected；
- `path=C:\\secret.txt` rejected；
- natural-language SELECT allowed；
- root/subcommand help normalized to JSON parser error。

## New finding

### P9-JR2-F1 — Bare shell executable tokens remain allowed

- Severity: **MAJOR**
- Category: **SECURITY / IMPLEMENTATION DEFECT**
- Status: **OPEN**
- Contract: `design/22` Section 49.2 / acceptance item 55

Section 49 explicitly lists shell-command examples including:

- `powershell`
- `pwsh`
- `bash`
- `curl`
- `wget`

Fresh detached probes against the exact candidate observed:

| payload string | observed |
|---|---|
| `powershell` | ALLOWED |
| `pwsh` | ALLOWED |
| `bash` | ALLOWED |
| `curl` | ALLOWED |
| `wget` | ALLOWED |

The implementation currently recognizes these executables only for selected
argument forms, for example `powershell -...`, `bash -lc`, or
`curl <arg>`.

A bare executable token is itself a valid shell command-launch form and is
within the explicit Section 49 examples. Therefore this is an implementation
defect, not a design ambiguity.

Required correction:

- freeze executable-token boundary in design/acceptance；
- reject exact/boundary command tokens and their argument forms；
- retain benign natural-language false-positive protection；
- add direct tests for bare and argument forms；
- perform another detached review。

## Acceptance 55-item status

Items 1-52 retain the COVERED status documented in
`development/66-p9-jr-formal-rereview-result.md` and were not invalidated by
this narrowly scoped correction.

| # | Item | Status |
|---:|---|---|
| 1-52 | prior mandatory contracts | COVERED |
| 53 | deterministic JSON CLI incl. root/subcommand help | **SATISFIED** |
| 54 | performance gates | COVERED by prior live evidence |
| 55 | payload security invariant | **NOT SATISFIED — P9-JR2-F1** |

## Verdict

**FAIL / CHANGES REQUIRED**

P9-K is not authorized.

Next:
`STOP review → design amendment → commit/push → implementation/tests → fresh detached review`.

No P9-L/M, main merge, P10/P11, Research MCP production, or Semantic Resolver
production is authorized.
