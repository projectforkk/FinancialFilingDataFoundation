# 62 — P9-J Formal Detached Code Review Result

Status: **FAIL — CHANGES REQUIRED**

Date: 2026-11-04 (Asia/Tokyo)

This document records the detached formal review only. No production code,
tests, design documents, accepted catalog, P0–P8 artifacts, or runtime files
were modified by this review.

## 1. Review identity and isolation

- Repository: `projectforkk/FinancialFilingDataFoundation`
- Branch under review: `task/p9-review-overlay`
- Exact reviewed candidate:
  `5a4b46e8e0ac2f6b2003d8c858a5606a3f1e11cc`
- Candidate parent:
  `345b8322e9a15fbc850b7f48fa17536c9b6ffded`
- Candidate subject: `docs: pass P9-I live evidence review`
- Accepted P8 baseline:
  `ee934ad05812c69b79f76db43e62cfd4050efb8e`
- Detached review worktree:
  `D:\Codex\FinancialFilingDataFoundation\worktrees\review\p9-5a4b46e8`
- Detached worktree HEAD was verified equal to the exact candidate SHA.
- Detached worktree status was clean: `## HEAD (no branch)`.

The active branch was synchronized separately to the then-current governance
HEAD `14ce4ba03418a61242e6b7706b772750f1738b87` by fast-forward only. The
active worktree's pre-existing untracked internal plan was preserved and was
not included in this result.

The accepted-P8-to-candidate diff contains 28 paths. Production changes are
limited to `src/financial_filing_data_foundation/review/*.py`; test changes
are limited to `tests/unit/review/test_review_overlay.py`. No P0–P8 source or
test path is in the diff, and no P10/P11 path is present.

## 2. Detached verification

Runtime:

`D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe`

Commands and fresh results in the exact detached worktree:

| Check | Result |
|---|---|
| `python -B -m compileall -q src/financial_filing_data_foundation/review` | PASS, exit 0 |
| import of all seven P9 review modules | PASS, `IMPORT_OK` |
| `python -B -m pytest tests/unit/review/test_review_overlay.py -q -p no:cacheprovider` | **40 passed** in 8.90s |
| `python -B -m pytest tests/unit -q -p no:cacheprovider` | **275 passed** in 17.84s |
| `git diff --check ee934ad..5a4b46e` | PASS, exit 0 |
| detached worktree status after verification | clean |

The source/scope scan found no OpenAI/Anthropic/network/MCP SDK imports, no
PDF/source reopen path, no Registry mutation, no UUID/random identity
surface, and no P10/P11 production path.

## 3. Review areas that passed

The following areas were independently inspected against `design/22`,
`development/61`, and `acceptance/32` and had no open finding in this review:

- exact candidate isolation and accepted-P8 scope boundary;
- append-only resolution files, deterministic SHA-256 IDs, exclusive-create
  behavior, and idempotent canonical payload handling;
- store-computed prior active IDs and prior overlay hash;
- dependency-ordered semantic recomputation for every historical resolution,
  including superseded records, before submit, list, materialize, snapshot
  load, and CLI resolution listing;
- direct P5/P6 evidence relationship and derived evidence pages;
- supersession, unknown-parent, cycle, competing-child, same-value overlap,
  and conflicting-value behavior;
- raw-field preservation and explicit effective overlay fields;
- P7 threshold/status logic and unsupported/unresolved issue behavior;
- deterministic staging paths, stale staging refusal, and cleanup ownership;
- snapshot content addressing and semantic/tamper validation;
- no source PDF open, no network/AI/Codex API, no external MCP SDK, and no
  implicit Registry write;
- equivalent whitespace comparison versus submitted trimmed-value
  preservation;
- P9-I live evidence and synthetic evidence as recorded by the prior
  governance documents.

## 4. Open findings

### P9-J-F1 — Resolution payload security contract is not enforced

- Severity: **MAJOR**
- Category: **SECURITY / IMPLEMENTATION DEFECT**
- Affected acceptance item: `acceptance/32` item 49; also affects the
  security/scope requirements in `development/61`.
- Status: **OPEN**

`design/22` section 49 explicitly states that a P9 resolution payload must
not contain file paths, URLs, shell commands, SQL, Python code, or
credentials, while `justification` is audit-only text with a raw maximum of
4000 characters. `development/61` explicitly requires adversarial review of
this boundary across free-text/string fields.

The implementation only checks `reviewer_id` for three literal markers and
checks that `justification` is non-empty and at most 4000 raw characters
(`src/financial_filing_data_foundation/review/evidence.py:805-834`). The
resolution construction then persists the submitted effective value and
justification (`src/financial_filing_data_foundation/review/store.py:366-386`).
There is no payload-wide rejection of URLs, paths, SQL, Python, shell text,
or credential material.

Fresh adversarial probes against the exact candidate accepted both of these
valid evidence-grounded submissions:

- `justification = "https://attacker.example/path"` — accepted as
  resolution `c8b2d33c59d7f28d224eea1f79b7d4b542597e4577bfe6c6c69d706f521f110b`;
- `value = "SELECT * FROM secrets"` — accepted as resolution
  `7611a820d23b6ecf28d9b612bcb06d56a5fb5246b91b19be6b40781601678711`.

The fact that `justification` is not executed does not satisfy the explicit
storage contract: the forbidden content is still accepted into an immutable
resolution payload. The design is sufficiently clear; this is an
implementation defect, not a design ambiguity. Do not promote P9-J to PASS
until the payload boundary is implemented and adversarially tested across
the intended fields.

### P9-J-F2 — Parser-level CLI failures violate the JSON diagnostic contract

- Severity: **MAJOR**
- Category: **CLI CONTRACT / IMPLEMENTATION DEFECT**
- Affected acceptance item: `acceptance/32` item 53, plus the explicit
  parser-level requirements in `development/61`.
- Status: **OPEN**

The current CLI uses required argparse subparsers and required arguments
(`src/financial_filing_data_foundation/review/cli.py:51-82`). `main()` calls
`parser.parse_args(argv)` before entering the `ReviewError`/generic exception
JSON handling (`src/financial_filing_data_foundation/review/cli.py:123-153`).
Therefore parser failures bypass the JSON diagnostic path.

Fresh subprocess probes against the exact candidate produced the following
for every case:

| Case | Exit | stdout | stderr |
|---|---:|---|---|
| no subcommand | 2 | empty | plain `usage:` plus argparse `error:` |
| unknown subcommand | 2 | empty | plain `usage:` plus argparse `error:` |
| missing required `--review-dir` | 2 | empty | plain `usage:` plus argparse `error:` |
| `--input-json` and `--input-file` together | 2 | empty | plain `usage:` plus argparse `error:` |

The existing direct CLI tests cover successful commands and handled
post-parse errors, but do not cover these parser-level cases. `development/61`
requires the parser-level cases to satisfy JSON stdout-only, diagnostics on
stderr, and deterministic reason-code/message behavior. The observed plain
argparse text and `SystemExit(2)` do not satisfy that contract. The design is
clear enough to classify this as an implementation defect, not a design gap.

## 5. Live and synthetic evidence review

### Synthetic evidence

`development/56-p9-g-corrective-evidence.md` records the synthetic golden
path and its exact-candidate verification: evidence-grounded period/unit/core
overlays, `REVIEW_REQUIRED -> PASS`, `resolved_reuse_eligible=true`, a
deterministic `ParsedDataRecord`, and unchanged base artifacts. The detached
focused test also passed
`test_synthetic_golden_resolves_period_unit_and_core_to_pass`.

### P9-I live evidence

`development/59-p9-i-live-evidence.md`, reviewed by
`development/60-p9-i-github-live-review.md`, records:

- CN 600519 FY2024 queue 1 with exact `RAW_PERIOD_COVERAGE_LOW`, one
  evidence-grounded `SET_PERIOD`, raw period still null, effective period
  `2024`, coverage `0.061093 -> 0.061553`, and honest final
  `REVIEW_REQUIRED`;
- HK 00700 FY2024 queue 4 with the exact required reason set, zero forced
  resolutions, and honest unresolved `REVIEW_REQUIRED`;
- dual-root determinism, unchanged SHA/size/mtime for all 23 base files, and
  timings within the design gates.

P9-I was not rerun during this detached code review; the pushed evidence and
the prior GitHub review were inspected as historical live evidence.

## 6. Acceptance/32 mandatory 54-item coverage map

Legend: `U` = detached unit/full-unit verification; `Y` = synthetic evidence;
`L` = pushed live evidence/review; `S` = static code/scope review; `A` =
acceptance/design document evidence; `MISSING` identifies a direct coverage
gap rather than claiming it was tested.

| # | Mandatory item | Evidence mapping | Review status |
|---:|---|---|---|
| 1 | frozen candidate HEAD stable | S: exact detached HEAD `5a4b46e...`, clean status | COVERED |
| 2 | accepted P8 baseline | S/A: `ee934ad...`, acceptance/33, exact diff base | COVERED |
| 3 | P0–P8 zero unintended diff | S: accepted-P8 diff has no source/test path outside P9 review | COVERED |
| 4 | full P0–P9 suite PASS | U/L: full unit `275 passed`; P9-I live evidence in 59/60 | COVERED for authorized review scope |
| 5 | manifest/input fingerprints valid | U/L: queue/base fingerprint tests; 59 base fingerprint record | COVERED |
| 6 | P7 PASS -> empty queue | S: queue status gate in queue.py | COVERED statically; MISSING dedicated unit fixture |
| 7 | P7 REVIEW_REQUIRED -> one task per REVIEW issue | U: `test_prepare_queue_contains_only_review_severity_and_is_deterministic`; L: 59 CN/HK queues | COVERED |
| 8 | WARNING/INFO excluded | U: same queue test; L: 59 issue sets | COVERED |
| 9 | FAIL/BLOCKED cannot be dismissed | U: `test_fail_and_blocked_base_statuses_are_rejected` | COVERED |
| 10 | task IDs deterministic | U: deterministic queue test; L: 59 dual-root task IDs | COVERED |
| 11 | supported/unsupported reason mapping | U: `test_unsupported_review_reason_remains_unresolved`; S: action map; L: 59 | COVERED |
| 12 | reviewer metadata validated | U: `test_reviewer_timestamp_must_be_timezone_aware`, justification boundary; S: model/evidence | COVERED |
| 13 | caller-supplied timezone-aware timestamp | U: timestamp test; L: 59 caller timestamp | COVERED |
| 14 | resolution ID deterministic | U/S: canonical payload/hash construction; L: 59 same-submission dual-root ID | COVERED |
| 15 | resolution JSON immutable/idempotent | U/S: exclusive-create and canonical payload paths; L: 59 repeat/reuse evidence | COVERED |
| 16 | P5 cell evidence resolves | U: CLI matrix, golden, overlap/conflict tests | COVERED |
| 17 | P6 evidence resolves | U: attestation/support and raw-fact tests; S: evidence validator | COVERED |
| 18 | evidence pages derived | U/S: evidence validator and attestation inherited-page assertions | COVERED |
| 19 | attestation evidence rejection/inheritance | U: `test_attestation_rejects_direct_evidence_and_inherits_supporting_evidence` | COVERED |
| 20 | target/evidence relationship | U/S: target selection and direct-evidence validation paths | COVERED |
| 21 | raw non-null never overwritten | U: `test_raw_nonnull_same_value_is_noop`, resolved-view tests; L: CN raw null preserved | COVERED |
| 22 | raw value/numeric unchanged | U/Y/L: resolved-facts raw preservation and golden/live evidence | COVERED |
| 23 | raw metric unchanged | S/Y: resolved fact copy preserves raw fields; golden tree/hash checks | COVERED |
| 24 | no-op rejected | U: `test_raw_nonnull_same_value_is_noop`, whitespace no-effect test | COVERED |
| 25 | raw patch conflict rejected | U: `test_raw_nonnull_conflict_is_rejected` | COVERED |
| 26 | store-computed prior IDs/history | U: `test_caller_cannot_override_prior_overlay_state`; F1 historical tests; S | COVERED |
| 27 | overlay hash deterministic/tamper-checked | U: payload/prior/before tamper tests; L: dual-root hashes | COVERED |
| 28 | supersession graph valid | U: prior/supersession and competing-child tests | COVERED |
| 29 | unknown/cycle/competing-child errors | U: invalid parent, cycle, and competing-child tests | COVERED |
| 30 | same-value overlap deterministic | U: `test_same_value_overlaps_are_deterministic`; L: dual-root determinism | COVERED |
| 31 | different-value overlap conflict | U: `test_conflicting_active_overlay_values_fail_materialization` | COVERED |
| 32 | zero-overlay snapshot deterministic | U: `test_zero_overlay_snapshot_is_deterministic`; L: HK zero overlay | COVERED |
| 33 | overlay hash deterministic | U/S: snapshot generation; L: CN/HK dual-root hashes | COVERED |
| 34 | resolved facts preserve every raw field | U/Y: resolved-view and synthetic golden raw/tree checks | COVERED |
| 35 | effective period/unit/scope only explicit overlay | U: fill/effective-field tests; S: resolver assignment paths | COVERED |
| 36 | statement classification overlay-only | U/Y: synthetic golden statement-class submissions | COVERED |
| 37 | period coverage uses P7 PERIOD_REVIEW | S/Y/L: policy path, golden, CN live threshold result | COVERED |
| 38 | unit coverage uses P7 UNIT_REVIEW | S/Y: policy path and synthetic unit resolution | COVERED |
| 39 | ambiguity requires explicit attestation | U: attestation evidence/observed-count tests; S | COVERED |
| 40 | core review augments base signals | U/Y: synthetic golden core classifications; S | COVERED |
| 41 | unsupported stays unresolved | U: `test_unsupported_review_reason_remains_unresolved` | COVERED |
| 42 | resolved validation priority | U/Y/L: resolved status tests, golden PASS, CN/HK honest REVIEW_REQUIRED | COVERED |
| 43 | reuse eligibility only PASS/compatible | U/Y/L: golden true; CN/HK false; unsupported false | COVERED |
| 44 | ParsedDataRecord deterministic | U: `test_resolved_parsed_data_record_is_deterministic`; Y | COVERED |
| 45 | no implicit Registry write | S/U: source scan and no `register_parsed_data` | COVERED |
| 46 | snapshot recomputation/tamper guard | U: `test_snapshot_semantic_tamper_is_rejected`; S | COVERED |
| 47 | base catalog/P3/P5/P6/P7 immutable | U/Y/L: fixture tree hashes; 59 23-file SHA/size/mtime | COVERED |
| 48 | no source PDF open | S/L: source scan; 59 live scope record | COVERED |
| 49 | no network/AI/Codex API | S/U/L: import scan, source test, 59 scope | COVERED |
| 50 | no external MCP SDK | S/U: import/scope scan | COVERED |
| 51 | no P8 tool mutation | S/L: accepted-P8 scope and live scope | COVERED |
| 52 | no P10/P11 implementation | S: candidate diff and source scan contain no P10/P11 path | COVERED |
| 53 | local CLI JSON stdout only | U: success/handled-error tests pass; adversarial parser probe **FAIL** for all 4 parser cases | **NOT SATISFIED — F2** |
| 54 | performance gates | L: 59 timings all below design thresholds; no new performance regression observed | COVERED by live evidence |

The direct P7-PASS empty-queue fixture is not present in the candidate unit
file; implementation and accepted evidence were statically reviewed. This is
not the current FAIL cause. The current FAIL cause is the two open findings
above, especially item 49 and the incomplete item 53 contract.

## 7. Final verdict and stop boundary

Final verdict: **FAIL / CHANGES REQUIRED**.

Open findings:

1. `P9-J-F1` — MAJOR security payload boundary defect.
2. `P9-J-F2` — MAJOR parser-level CLI JSON diagnostic defect.

There is no environmental or detached-worktree blocker. The blocker to a
P9-J PASS is the two implementation defects. P9-K is **not authorized**.
This review does not modify or fix the defects. No P9-K/L/M, main merge, P10,
or P11 work is performed.
