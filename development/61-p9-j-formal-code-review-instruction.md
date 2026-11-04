# 61 — P9-J Formal Detached Code Review Instruction

Status: **ACTIVE — P9-J ONLY**

Phase:
`P9 — Codex Review Overlay`

Target branch:
`task/p9-review-overlay`

Exact review candidate SHA:

`5a4b46e8e0ac2f6b2003d8c858a5606a3f1e11cc`

Production implementation commit under review:

`f3b6dcd1b243c7a77734a1cdfa7459f38d91c842`

P9-I evidence commit included in candidate history:

`345b8322e9a15fbc850b7f48fa17536c9b6ffded`

Authorization:
`development/60-p9-i-github-live-review.md`

This is the formal P9-J review gate.

It is a **review-only** gate.

Do not fix production, tests, or design during this review.

---

## 1. Hard boundary

The formal reviewer must review an exact detached worktree, not the active development worktree.

Do NOT:
- edit P9 production；
- edit tests；
- edit design；
- change catalog/P3/P5/P6/P7；
- run live writes against accepted base artifacts outside designated temporary review roots；
- reset/rebase/force push；
- merge main；
- enter P9-K/L/M；
- enter P10/P11。

If a defect/design gap is found:
- record it precisely；
- verdict cannot be PASS；
- STOP after the review result is recorded；
- do not implement the fix in P9-J。

---

## 2. Establish exact detached review worktree

From the repository root, fetch first:

```powershell
cd D:\Codex\FinancialFilingDataFoundation
git fetch origin
git cat-file -e 5a4b46e8e0ac2f6b2003d8c858a5606a3f1e11cc^{commit}
git show --no-patch --format=fuller 5a4b46e8e0ac2f6b2003d8c858a5606a3f1e11cc
```

Create a new detached review worktree:

```text
D:\Codex\FinancialFilingDataFoundation\worktrees\review\p9-5a4b46e8
```

If that path already exists:
- do not delete or reuse blindly；
- inspect whether it is already an exact clean detached worktree at the same SHA；
- otherwise choose another deterministic review-only suffix and record it。

The review worktree must resolve exactly to:

`5a4b46e8e0ac2f6b2003d8c858a5606a3f1e11cc`

Record:

```powershell
git rev-parse HEAD
git status --short --branch --untracked-files=all
```

Expected: detached exact SHA with no tracked modifications.

---

## 3. Read authoritative review basis in full

From the detached candidate, read:

- `design/00-design-management-index.md`
- `design/01-project-detailed-design.md`
- `design/22-p9-review-overlay-design.md`
- `design/23-p9-implementation-plan.md`
- `development/48-p9-development-instruction.md`
- `development/52-p9-g-development-evidence.md`
- `development/54-p9-g-github-code-review.md`
- `development/56-p9-g-corrective-evidence.md`
- `development/57-p9-g-corrective-github-rereview.md`
- `development/58-p9-i-live-instruction.md`
- `development/59-p9-i-live-evidence.md`
- `development/60-p9-i-github-live-review.md`
- `acceptance/32-p9-acceptance-instruction.md`
- `PROJECT_STATUS.md`

Do not review from old handoff summaries when exact repository text is available.

---

## 4. Scope/diff review

Confirm accepted P8 baseline:

`ee934ad05812c69b79f76db43e62cfd4050efb8e`

Review the exact delta from accepted P8 to the P9 candidate:

```powershell
git diff --name-status ee934ad05812c69b79f76db43e62cfd4050efb8e..5a4b46e8e0ac2f6b2003d8c858a5606a3f1e11cc
git diff --stat ee934ad05812c69b79f76db43e62cfd4050efb8e..5a4b46e8e0ac2f6b2003d8c858a5606a3f1e11cc
```

Confirm:
- no unintended P0-P8 production/test changes；
- no P8 MCP mutation；
- no Registry write path；
- no P10/P11 implementation；
- all P9 production is limited to the designed `review/` package and authorized tests/governance evidence。

Any unexplained accepted-scope change is a blocker.

---

## 5. Review every P9 production module

Read line-by-line:

- `src/financial_filing_data_foundation/review/__init__.py`
- `models.py`
- `queue.py`
- `evidence.py`
- `store.py`
- `resolve.py`
- `cli.py`

Review implementation against exact design, not only tests.

Mandatory review domains:

### A. Base discovery / immutability
- internal P8 catalog only；
- project-root/path guards；
- P3/P5/P6/P7 fingerprint validation；
- FAIL/BLOCKED rejection；
- no source PDF reopen；
- no base artifact write。

### B. Queue
- REVIEW only；
- one task per REVIEW issue；
- deterministic IDs/order/bytes；
- supported/unsupported mappings；
- WARNING/INFO excluded。

### C. Evidence / target
- P5/P6 evidence identity；
- evidence-to-target relationship；
- evidence page derivation；
- fill-only behavior；
- period/unit/scope value normalization contract；
- statement classification；
- attestation support/evidence inheritance。

### D. Immutable resolution history
- canonical ID/bytes；
- append-only persistence；
- idempotency；
- store-computed prior active set/hash；
- complete semantic history validation；
- historical before-state recomputation；
- supersession graph；
- cycles/competing children；
- support dependencies；
- tamper rejection；
- no timestamp ordering semantics。

### E. Materialization / snapshot
- active terminal set；
- overlap same/different value；
- raw fields preserved；
- effective values overlay-only；
- statement overlay-only；
- content-addressed snapshot；
- snapshot semantic/tamper validation；
- zero-overlay determinism。

### F. Resolved status
- P7 threshold reuse；
- ambiguity requires explicit attestation；
- unsupported remains unresolved/unsupported；
- core statement augmentation only；
- honest PASS / REVIEW_REQUIRED；
- reuse eligibility；
- deterministic ParsedDataRecord。

### G. CLI
- six designed commands；
- JSON stdout only；
- diagnostics stderr；
- deterministic output；
- explicit JSON string/file input；
- no business-logic duplication；
- no secret/arbitrary execution path。

### H. Scope/security
- no network；
- no AI/OpenAI/Codex API；
- no external MCP SDK；
- no Registry mutation；
- no P10/P11 implementation；
- no random identity/time dependence。

---

## 6. Explicit adversarial review items

Do not assume existing unit tests are sufficient.

### 6.1 Resolution payload security contract

Design section 49 says P9 resolution payload must not contain:
- file paths；
- URLs；
- shell commands；
- SQL；
- Python code；
- credentials。

Review whether the current implementation actually enforces the intended security boundary across free-text/string fields.

Distinguish:
- structured identifiers/semantic values that legitimately contain ordinary text；
- audit-only justification that is never executed；
- prohibited executable/secret/path/URL payload content。

If the design wording is too ambiguous to implement or test without inventing semantics, record a **DESIGN GAP** rather than guessing.

If the design is clear and implementation lacks the required guard, record an **IMPLEMENTATION DEFECT**.

Do not patch it during review.

### 6.2 CLI parser-level failures

Review behavior not only after successful argparse parsing, but also:
- no subcommand；
- unknown subcommand；
- missing required arguments；
- mutually exclusive input misuse。

Determine whether these satisfy the current design/instruction contract for:
- JSON stdout only；
- diagnostics stderr；
- deterministic reason code/message。

If argparse's default usage/SystemExit behavior violates the authoritative contract, record the finding.

Do not change CLI during review.

### 6.3 Deterministic staging/concurrency

Review deterministic staging behavior for:
- existing final dir；
- existing stale temp dir；
- concurrent preparation race；
- cleanup ownership。

Ensure the code never deletes unknown staging state.

### 6.4 Historical semantic validation

Confirm a tampered superseded/non-terminal historical resolution cannot be consumed by:
- submit；
- active loader；
- attestation；
- materialization；
- snapshot load；
- CLI resolutions。

### 6.5 Equivalent whitespace overlaps

Review two active overlay resolutions that are equivalent under comparison normalization but preserve different trimmed internal whitespace.

Confirm:
- conflict policy follows Section 18/19；
- output remains deterministic；
- resolution IDs remain correctly distinct/identical according to canonical payload rules。

If contract is ambiguous, record design gap rather than infer a policy.

---

## 7. Review tests against acceptance/32

Read the complete P9 test file.

Create a mapping from all 54 Mandatory acceptance items to:
- direct unit test；
- live evidence；
- synthetic evidence；
- static/code-review evidence；
- still missing。

Do not mark an item covered merely because a nearby test exists.

Highlight any mandatory acceptance item with no credible evidence path.

---

## 8. Read-only verification commands

Use main runtime:

`D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe`

Set detached PYTHONPATH and suppress worktree bytecode/cache writes:

```powershell
$env:PYTHONPATH="D:\Codex\FinancialFilingDataFoundation\worktrees\review\p9-5a4b46e8\src"
$env:PYTHONDONTWRITEBYTECODE="1"
New-Item -ItemType Directory -Force D:\Codex\FFDF-t\p9-j | Out-Null
```

Run at least:

```powershell
D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -B -m pytest tests\unit\review\test_review_overlay.py -q -p no:cacheprovider --basetemp D:\Codex\FFDF-t\p9-j\focused

D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe -B -m pytest tests\unit -q -p no:cacheprovider --basetemp D:\Codex\FFDF-t\p9-j\full

git diff --check
git status --short --branch --untracked-files=all
```

The detached worktree must remain free of tracked modifications.

If Python/pytest creates an unexpected untracked file inside the review worktree, record it; do not use destructive clean.

---

## 9. Reconcile live/synthetic evidence

Review, do not rerun destructively:

### Synthetic
Confirm pushed evidence supports:
- base REVIEW_REQUIRED；
- period/unit/core resolutions；
- final PASS；
- reuse eligible true；
- resolved ParsedDataRecord；
- raw unchanged。

### CN live
Confirm:
- exact queue count/reason；
- evidence-grounded single period resolution；
- raw null unchanged；
- effective value visible；
- honest REVIEW_REQUIRED；
- no guessed mass fill。

### HK live
Confirm:
- exact 4 reasons；
- no forced dismissal；
- honest unresolved REVIEW_REQUIRED。

### Immutability/performance/determinism
Confirm evidence is internally consistent with design gates.

If a claim cannot be supported from committed evidence, record it as evidence insufficiency.

---

## 10. Formal review verdict

Allowed verdict:

- `PASS`
- `FAIL`
- `BLOCKED`

PASS requires:
- no open correctness/security/design finding that affects P9 acceptance；
- no missing mandatory acceptance evidence path；
- detached full unit/focused verification PASS；
- exact candidate remains unchanged。

Any substantive issue:
- verdict FAIL or BLOCKED；
- categorize each finding as:
  - implementation defect；
  - design gap；
  - evidence gap；
  - environment blocker；
- include severity and exact file/contract references。

Do not fix findings during P9-J.

---

## 11. Review result artifact

After the detached review is complete, switch back to the **active P9 worktree only for documentation**.

Do not modify source/tests/design.

Create:

`development/62-p9-j-formal-code-review-result.md`

Record:
- exact reviewed SHA；
- detached worktree path；
- accepted P8 comparison baseline；
- reviewed files；
- test commands/results；
- acceptance-54 coverage mapping/summary；
- live/synthetic evidence review；
- findings with severity/category；
- final verdict；
- whether P9-K is authorized。

If verdict is PASS:
- state `P9-K may be authorized by the design owner after GitHub review of this result`；
- do **not** execute P9-K。

If verdict is FAIL/BLOCKED:
- state exact required next action；
- do not implement fixes。

Commit only the review result documentation and push normally to:

`origin/task/p9-review-overlay`

Suggested message:

`review: record P9 formal detached code review`

No force push.

If remote advances before push:
STOP and report; do not self-authorize merge.

---

## 12. Stop point

After pushing `development/62-p9-j-formal-code-review-result.md`:

STOP.

Do not execute:
- P9-K；
- P9-L；
- P9-M；
- main merge；
- P10；
- P11。
