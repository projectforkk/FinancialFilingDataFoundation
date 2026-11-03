# 57 — P9-G Corrective GitHub Re-Review

Status: **PASS — P9-G / P9-H CLOSED, P9-I AUTHORIZED**

Reviewed remote HEAD:
`8edece62c5f7d6b95da3bab9c346897d8f102a45`

Corrective implementation commit:
`f3b6dcd1b243c7a77734a1cdfa7459f38d91c842`

Corrective evidence:
`development/56-p9-g-corrective-evidence.md`

Review basis:
- `design/22-p9-review-overlay-design.md`
- `design/23-p9-implementation-plan.md`
- `development/54-p9-g-github-code-review.md`
- `development/55-p9-g-corrective-instruction.md`
- `development/56-p9-g-corrective-evidence.md`
- `acceptance/32-p9-acceptance-instruction.md`

This review is a GitHub design/code re-review of the corrective P9-G candidate. It is not P9-J formal detached review and is not Independent Acceptance.

---

## 1. Scope / lineage

Remote branch advanced by exactly two commits from the prior review/status baseline:
1. `f3b6dcd...` corrective source/tests；
2. `8edece62...` corrective evidence。

Changed production/test scope:
- `review/evidence.py`
- `review/queue.py`
- `review/resolve.py`
- `review/store.py`
- `tests/unit/review/test_review_overlay.py`

No P0–P8 source/test change, raw/source artifact, P9-I live artifact, P10 or P11 production was included.

Result: **PASS**

---

## 2. F1 — complete immutable resolution-history semantic validation

Previous finding:
historical resolution files could pass canonical/graph checks and be consumed by submit/active paths before full semantic recomputation.

Corrective implementation:
- authoritative semantic recomputation moved to `evidence.validate_resolution_semantics()`；
- `validate_resolution_history()` validates every persisted record dependency-first；
- `store.list_resolutions()` now performs:
  1. canonical file/id validation；
  2. graph/prior-state validation；
  3. base bundle/fingerprint reload；
  4. index reconstruction；
  5. complete semantic-history validation；
- `submit_resolution()`, `active_resolutions()`, materialization, snapshot loading, and CLI `resolutions` all traverse the validated loader path；
- superseded historical records are included, not only active terminal records；
- resolver reuses the same semantic validation implementation instead of maintaining a second semantic copy。

Corrective tests cover:
- re-signed historical before-state tamper before later submit；
- re-signed superseded-parent semantic tamper；
- support-resolution evidence tamper before attestation inheritance；
- semantically corrupt resolution store via public list/CLI surfaces。

Re-review result: **F1 CLOSED / PASS**

---

## 3. F2 — submitted trimmed fill-value preservation

Previous finding:
period/unit/scope values were whitespace-collapsed for persistence/effective output instead of only for comparison.

Correction:
- `TargetSelection.submitted_value` stores trim-only value；
- `normalized_value` remains comparison-only；
- resolution persistence uses `submitted_value`；
- resolved effective output uses `submitted_value`；
- explicit raw equivalence/conflict logic continues to use normalized comparison。

Coverage verifies internal whitespace preservation and normalized raw comparison behavior.

Re-review result: **F2 CLOSED / PASS**

---

## 4. F3 — justification max 4000 raw characters

Previous finding:
validation allowed normalized length 4096 and persisted unnormalized input.

Correction:
- raw persisted justification must be a string；
- must contain non-whitespace content；
- raw length must be <= 4000；
- no truncation；
- whitespace normalization cannot bypass the persisted-length bound。

Boundary coverage includes 4000 accepted, 4001 rejected, oversized whitespace-heavy rejected, whitespace-only rejected.

Re-review result: **F3 CLOSED / PASS**

---

## 5. F4 — no random UUID/random identity

Previous finding:
`prepare_review_overlay()` used `uuid.uuid4()` for staging.

Correction:
- random UUID import/call removed；
- deterministic staging path `.<document_sha256>.tmp` used；
- pre-existing unknown deterministic staging state fails safely；
- cleanup applies only after the current invocation created its own staging directory；
- scope test now rejects random/UUID surface in P9 production。

Re-review result: **F4 CLOSED / PASS**

---

## 6. F5 — complete direct CLI matrix

Previous finding:
only direct CLI tasks success/error tests existed.

Correction now directly exercises:
- prepare；
- tasks；
- submit --input-json；
- submit --input-file；
- resolutions；
- materialize；
- report；
- malformed JSON；
- non-object JSON。

Success paths prove:
- return code 0；
- one valid JSON stdout document；
- empty stderr。

Handled failure paths prove:
- stdout empty；
- deterministic JSON diagnostic on stderr；
- non-zero return code。

Re-review result: **F5 CLOSED / PASS**

---

## 7. Regression / P9-H

Corrective evidence records:
- focused P9: `40 passed`；
- full unit: `275 passed`；
- corrective F1-F5 subset: `11 passed`；
- compileall/import: PASS；
- git diff --check: PASS；
- scope: PASS；
- no network/AI/OpenAI/Codex API: PASS；
- no external MCP SDK: PASS；
- no PDF/OCR/source reopen: PASS；
- no Registry mutation: PASS；
- no random UUID/random identity: PASS；
- no P10/P11 production: PASS；
- 25 catalog/P3/P5/P6/P7 immutability snapshot: PASS；
- synthetic REVIEW_REQUIRED → PASS: `2 passed`；
- resolved ParsedDataRecord construction: PASS。

These satisfy the P9-H design gate requirements.

Result: **P9-H PASS**

---

## 8. Re-review verdict

P9-G corrective GitHub re-review:

**PASS**

P9-H:

**PASS**

Open blockers from F1-F5:

**NONE**

Next authorized gate:

**P9-I — Live CN/HK**

Still unauthorized:
- P9-J formal Code Review；
- P9-K Acceptance Freeze；
- P9-L Independent Acceptance；
- P9-M Closeout；
- main merge；
- P10；
- P11。

P9-I must use the canonical P8 catalog, snapshot catalog/P3/P5/P6/P7 SHA256+size+mtime_ns before/after, keep all base artifacts immutable, and write only to designated review_root.
