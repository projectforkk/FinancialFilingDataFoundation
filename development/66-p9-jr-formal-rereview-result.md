# 66 — P9-JR Formal Detached Re-Review Result

Status: **FAIL / CHANGES REQUIRED**

Phase:
`P9 — Codex Review Overlay / P9-JR`

## 1. Exact review identity

- target branch: `task/p9-review-overlay`
- exact reviewed candidate:
  `65d29cb7d41ab46fb898c1f0bc557537ab48421c`
- corrective production commit:
  `2d42c02c4e5dc7026b50c6928a57b1781ba0d831`
- design corrective baseline:
  `d668c6e21cba8ae274ebbb786ccb70e55c9e04c2`
- accepted P8 baseline:
  `ee934ad05812c69b79f76db43e62cfd4050efb8e`
- detached review worktree:
  `D:\Codex\FinancialFilingDataFoundation\worktrees\review\p9-jr-65d29cb`
- detached HEAD:
  `65d29cb7d41ab46fb898c1f0bc557537ab48421c`
- detached status:
  clean, `## HEAD (no branch)`

The detached worktree and all review/test temporary paths remained inside
`D:\Codex\FinancialFilingDataFoundation`.

## 2. Verification results

Exact detached candidate:

| Check | Result |
|---|---|
| object type / detached HEAD | PASS, exact commit |
| compileall review package | PASS |
| import all seven review modules | PASS, `IMPORT_OK` |
| focused P9 unit tests | **52 passed** |
| full unit suite | **287 passed** |
| `git diff --check` accepted-P8→candidate | PASS |
| `git diff --check` corrective production delta | PASS |
| accepted-P8 source/test scope | PASS |
| P0-P8 unintended source/test changes | none |
| network/AI/MCP/Registry static scan | no prohibited import/mutation surface |
| detached status after verification | clean |

Short project-local basetemp roots were used because deep P9 snapshot paths
approach the Windows path-length boundary.

## 3. What the corrective candidate successfully fixed

### Prior P9-J-F1 original proofs

The two exact prior proofs are now rejected:

- URL in `justification`；
- SQL `SELECT * FROM secrets` in `value`。

The rejection is deterministic:

- `P9_RESOLUTION_CONTENT_FORBIDDEN`
- `resolution payload contains forbidden content`

and does not echo the offending content.

Historical re-signed forbidden content is also rejected by semantic history
validation.

### Prior P9-J-F2 required parser failures

Raw subprocess review confirmed all four required parser-level cases now
satisfy the amended contract:

1. no subcommand；
2. unknown subcommand；
3. missing required argument；
4. mutually-exclusive `--input-json` + `--input-file`。

For each:

- exit 2；
- stdout empty；
- stderr exactly one JSON object；
- no argparse `usage:` / `error:` prose；
- stable `P9_CLI_ARGUMENT_ERROR` / `invalid command line arguments`。

Therefore the exact original F1/F2 reproductions are closed.

## 4. New open findings

### P9-JR-F1 — Security content classifier does not faithfully implement amended Section 49

- Severity: **MAJOR**
- Category: **SECURITY / IMPLEMENTATION DEFECT**
- Status: **OPEN**
- Affected contract:
  `design/22` Section 49.2 / 49.3 and `acceptance/32` item 55

The amended design explicitly requires deterministic coverage of Windows
drive-root paths and POSIX absolute paths, while also requiring ordinary
natural-language financial text not to be rejected merely because it contains
keywords.

Fresh detached probes found both false negatives and a false positive:

| Probe | Required | Observed |
|---|---|---|
| `/tmp` | reject POSIX absolute path | **ALLOWED** |
| `path=C:\secrets\payload.txt` | reject Windows drive-root path | **ALLOWED** |
| `Select revenue from the annual report evidence.` | allow ordinary natural language | **REJECTED as forbidden SQL** |

Root cause in the exact candidate:

- POSIX path regex requires an additional slash-delimited segment and therefore
  misses a valid single-segment absolute path；
- Windows drive path regex requires start/whitespace/quote/parenthesis before
  the drive letter and therefore misses assignment/punctuation contexts；
- SQL `select ... from` matching is too lexical and treats an ordinary English
  sentence as executable SQL syntax。

This is not a design ambiguity for the observed cases: the amended design
explicitly requires these path classes to be rejected and natural language not
to be falsely rejected.

P9-J-F1 is therefore only partially remediated and acceptance item 55 remains
unsatisfied.

### P9-JR-F2 — argparse help still violates the JSON-only success contract

- Severity: **MAJOR**
- Category: **CLI CONTRACT / IMPLEMENTATION DEFECT**
- Status: **OPEN**
- Affected contract:
  `design/22` Section 41 and `acceptance/32` item 53

The four required parser failures are fixed, but argparse's built-in help path
still bypasses P9 JSON output semantics.

Fresh raw subprocess probes:

- `--help` → exit 0, stderr empty, **plain argparse help text on stdout**；
- `tasks --help` → exit 0, stderr empty, **plain argparse help text on stdout**。

Section 41 states that a successful CLI invocation must be exit 0 with stdout
exactly one JSON document and stderr empty. These two successful invocations
are not JSON.

Root cause:

- custom `error()` only normalizes parser failures；
- argparse's built-in help action still calls its normal formatter/exit path。

Acceptance item 53 therefore remains unsatisfied despite the four original
parser-failure cases passing.

## 5. Acceptance 55-item coverage map

Legend:
- `U` detached unit/full-unit evidence
- `S` static/diff review
- `L` previously accepted live evidence
- `Y` synthetic evidence
- `A` design/acceptance evidence

| # | Mandatory item | Evidence | Status |
|---:|---|---|---|
| 1 | frozen candidate stable | S exact detached SHA/status | COVERED |
| 2 | accepted P8 baseline | A/S exact baseline diff | COVERED |
| 3 | P0-P8 zero unintended diff | S | COVERED |
| 4 | full P0-P9 suite | U 287 passed + prior live | COVERED |
| 5 | manifest/input fingerprints | U/L | COVERED |
| 6 | P7 PASS -> empty queue | S/A; same evidence status as prior review | COVERED, no new finding |
| 7 | REVIEW_REQUIRED one task per REVIEW issue | U/L | COVERED |
| 8 | WARNING/INFO excluded | U/L | COVERED |
| 9 | FAIL/BLOCKED not dismissible | U | COVERED |
| 10 | deterministic task IDs | U/L | COVERED |
| 11 | support mapping | U/L/S | COVERED |
| 12 | reviewer metadata | U/S | COVERED |
| 13 | caller timezone-aware timestamp | U/L | COVERED |
| 14 | deterministic resolution ID | U/L/S | COVERED |
| 15 | immutable/idempotent resolution | U/S/L | COVERED |
| 16 | P5 evidence | U/Y | COVERED |
| 17 | P6 evidence | U/Y | COVERED |
| 18 | derived evidence pages | U/S | COVERED |
| 19 | attestation evidence inheritance | U | COVERED |
| 20 | target/evidence relationship | U/S | COVERED |
| 21 | raw non-null never overwritten | U/L | COVERED |
| 22 | raw value/numeric unchanged | U/Y/L | COVERED |
| 23 | raw metric unchanged | U/Y/S | COVERED |
| 24 | no-op rejected | U | COVERED |
| 25 | raw conflict rejected | U | COVERED |
| 26 | store-computed prior IDs/history | U/S | COVERED |
| 27 | prior overlay hash tamper check | U/S | COVERED |
| 28 | supersession graph | U/S | COVERED |
| 29 | unknown/cycle/competing child | U | COVERED |
| 30 | same-value overlap | U | COVERED |
| 31 | conflicting overlap | U | COVERED |
| 32 | zero-overlay deterministic | U/L | COVERED |
| 33 | overlay hash deterministic | U/L | COVERED |
| 34 | resolved facts preserve raw fields | U/Y | COVERED |
| 35 | effective fields overlay-only | U/L | COVERED |
| 36 | statement class overlay-only | U/Y | COVERED |
| 37 | period P7 threshold reuse | U/Y/L/S | COVERED |
| 38 | unit P7 threshold reuse | U/Y/S | COVERED |
| 39 | ambiguity explicit attestation | U/S | COVERED |
| 40 | core statement augmentation | U/Y/S | COVERED |
| 41 | unsupported stays unresolved | U | COVERED |
| 42 | resolved status priority | U/Y/L | COVERED |
| 43 | reuse only PASS/compatible | U/Y/L | COVERED |
| 44 | ParsedDataRecord deterministic | U/Y | COVERED |
| 45 | no implicit Registry write | S/U | COVERED |
| 46 | snapshot tamper guard | U/S | COVERED |
| 47 | base artifacts immutable | U/Y/L | COVERED |
| 48 | no source PDF open | S/L | COVERED |
| 49 | no network/AI/Codex API | S/U/L | COVERED |
| 50 | no external MCP SDK | S/U | COVERED |
| 51 | no P8 tool mutation | S/L | COVERED |
| 52 | no P10/P11 implementation | S | COVERED |
| 53 | deterministic JSON CLI contract | original four failure cases pass, but help success is plain text | **NOT SATISFIED — P9-JR-F2** |
| 54 | performance gates | L prior live evidence; no corrective performance regression indicated | COVERED |
| 55 | payload security invariant | original probes pass; fresh path false negatives + natural-language false positive | **NOT SATISFIED — P9-JR-F1** |

## 6. Live/synthetic evidence

The corrective changes are limited to P9 security validation, CLI argument
handling, and direct tests. No live CN/HK base artifact was modified.

Previously reviewed P9-I evidence remains applicable for:

- CN 600519 FY2024 honest `REVIEW_REQUIRED` after one grounded period overlay；
- HK 00700 FY2024 four unresolved review reasons；
- dual-root determinism；
- 23-file catalog/P3/P5/P6/P7 immutability；
- performance gates。

Synthetic golden remains unit-covered and passed in the detached focused/full
suite.

## 7. Final verdict / stop boundary

Final verdict:

**FAIL / CHANGES REQUIRED**

The candidate is test-green but does not satisfy mandatory acceptance items
53 and 55.

Required next action:

`STOP P9-JR review → root-cause/design amendment → commit/push new design baseline → then implementation/tests → new detached formal review`.

P9-K is **not authorized**.

Do not enter P9-L/P9-M, main merge, P10, P11, Research MCP production, or
Semantic Resolver production from this candidate.
