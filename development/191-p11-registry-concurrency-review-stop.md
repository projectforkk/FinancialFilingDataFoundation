# 191 — P11 Final Design Review Stop — Concurrent Registry Persistence

Status: **FAIL / STOP — P11-ISSUE-036 / PRODUCTION CLOSED**

Phase:
P11 — US SEC Provider

Reviewed exact candidate:
`2ef1e8ced4b5c3d7103c73bdc8cc532882fa7d47`

Fresh detached review:
`D:\\Codex\\FinancialFilingDataFoundation\\worktrees\\review\\p11-design-2ef1e8c`

Review authorization:
`development/190-p11-final-path-concurrency-final-review-authorization.md`

## Automated review

PASS:

- exact HEAD = `2ef1e8ced4b5c3d7103c73bdc8cc532882fa7d47`;
- detached worktree clean;
- `git diff --check` = PASS;
- P0-P10 production/test/runtime-lock diff = NONE;
- ISSUE-010..031 matrix = PASS;
- ISSUE-032..033 guard = PASS after updating review-probe wording only;
- ISSUE-034 byte-determinism guard = PASS;
- ISSUE-035 concurrency guard = PASS;
- known package/source-asset fixture hashes remain stable;
- JSON/JSONL deterministic sample hashes remain stable.

## Finding

Manual cross-gate review found a remaining concurrency defect at the P11-I -> P11-K boundary.

ISSUE-035 now correctly allows two concurrent attempts for the same deterministic `parse_run_id` to converge on the same immutable final `export-v2`. The losing final-path writer may complete exact existing-final verification and then proceed to P11-K.

The accepted `SQLiteRegistry.register_parsed_data()` implementation is not atomic across its idempotency check:

1. `SELECT * FROM parsed_data WHERE parse_run_id = ?`;
2. if absent, `INSERT INTO parsed_data(...)`;
3. commit.

`parsed_data.parse_run_id` is the primary key.

Two processes can therefore both observe the row as absent before either inserts. One insert wins; the other receives a uniqueness failure rather than the accepted exact-record idempotent result.

## Reproduced evidence

Project-local probe:
`workspace/scratch/p11-registry-concurrency-probe.py`

The probe executes the accepted `register_parsed_data()` method while synchronizing two independent SQLite connections after the initial SELECT so the check-then-insert race is forced without modifying production code.

Observed result:

```text
RESULTS=[('T0', 'IntegrityError', 'UNIQUE constraint failed: parsed_data.parse_run_id'), ('T1', 'PASS', None)]
ROW_COUNT=1
EXACT_ROW=True
P11_REGISTRY_CONCURRENT_CHECK_THEN_INSERT_RACE=REPRODUCED
```

The final registry state is correct, but one otherwise valid concurrent run fails. The P11 design does not currently define whether this uniqueness race is retried, re-read, treated as idempotent success, or surfaced as a registry failure.

Because the final artifact commit protocol explicitly permits concurrent same-`parse_run_id` attempts to reach P11-K, this is a material implementation-time ambiguity and cannot be deferred silently.

## P11-ISSUE-036 — concurrent exact registry persistence

Required correction:

### 1. Exact-record concurrency must be idempotent

After a successful P11-I final reload, two or more concurrent P11-K attempts persisting the exact same deterministic `ParsedDataRecord` MUST converge to:

- exactly one physical `parsed_data` row;
- every caller receives exact idempotent success;
- no duplicate row;
- no uniqueness exception leaks merely because another exact writer won the race.

### 2. Different-content collision must fail closed

If the same `parse_run_id` already resolves to any different persisted field, the operation MUST fail closed and MUST NOT overwrite or mutate the existing row.

The design must freeze an exact P11 reason/error surface for this conflict.

### 3. Atomicity boundary must be explicit

The Design-First amendment must define the exact transaction/concurrency algorithm, not leave it to implementation choice.

It must prevent the current `SELECT absent -> concurrent INSERT` race and must state how lock/busy/I/O failures are classified.

### 4. P0-P10 compatibility

The correction MUST NOT silently change accepted P0-P10 behavior.

Preferred boundary is additive P11-specific registry persistence or an explicitly reviewed backward-compatible strengthening of the accepted registry API. No registry schema migration is required unless separately designed and accepted.

### 5. Artifact/registry ordering remains unchanged

- final `export-v2` remains immutable;
- P11-K still runs only after successful final reload;
- registry persistence never mutates final artifact bytes;
- registry failure does not delete the final artifact;
- package-aware reuse still discovers only valid registry rows.

### 6. Acceptance

Acceptance must prove at least:

- two concurrent exact P11-K writers for the same `parse_run_id` both return idempotent success;
- exactly one row exists afterward and equals the requested record;
- a third exact retry is idempotent;
- a same-`parse_run_id` / different-content attempt fails with the frozen conflict reason and leaves the original row unchanged;
- database busy/lock/I/O failure is not misclassified as exact idempotent success;
- no hidden schema migration;
- CN/HK existing planner/reuse behavior remains unchanged;
- no final artifact mutation occurs.

## Scope

No production/test/runtime changes were made during this review.

P11-ISSUE-010..035 remediation remains valid.

## Verdict

# FAIL / STOP

Candidate `2ef1e8ced4b5c3d7103c73bdc8cc532882fa7d47` is INELIGIBLE for DESIGN READY.

P11-A remains OPEN/STOPPED.

P11-B remains NOT AUTHORIZED.

P11 production remains CLOSED.