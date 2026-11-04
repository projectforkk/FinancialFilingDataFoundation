# 54 — P9-G GitHub Code Review

Status: **CHANGES REQUIRED**

Phase:
`P9 — Codex Review Overlay`

Reviewed remote candidate:
`4207ae0c6eadf63b0c989b432e518f37c292836d`

Preserved implementation candidate:
`e6f83d560822214ab4ede0e317f853d100b6c9ea`

Integration merge:
`efbe17ebd84208c26a5f8c497c39125afada6ca6`

Review basis:
- `design/22-p9-review-overlay-design.md`
- `design/23-p9-implementation-plan.md`
- `development/48-p9-development-instruction.md`
- `development/51-p9-codex-local-execution-instruction.md`
- `development/52-p9-g-development-evidence.md`
- `development/53-p9-local-candidate-integration-instruction.md`
- `acceptance/32-p9-acceptance-instruction.md`

This is a GitHub review of the pushed P9-G candidate. It is **not** the formal P9-J detached Code Review and does not authorize P9-I or later gates.

---

## 1. Integration lineage — PASS

The integration preserved the implementation candidate and incorporated the newer governance lineage without production/test conflicts.

Observed:
- `e6f83d...` remains an ancestor of the final candidate history；
- merge `efbe17e...` contains the remote governance parent；
- the delta from `e6f83d...` to `4207ae0...` is governance/evidence only；
- no P9 production/test file changed during the integration merge；
- `development/52` records focused `29 passed`, full unit `264 passed`, compile/import/scope/immutability/synthetic PASS。

Result: **PASS**

---

## 2. Finding F1 — BLOCKER — immutable resolution history is not semantically revalidated on every loader/submit path

### Design requirement

P9-ISSUE-003 requires historical prior state to be reconstructible from immutable base data plus explicit prior overlay state.

The loader must validate:
- prior-state membership；
- prior-state hash；
- supersession/dependency consistency；
- evidence semantics；
- recomputed `before`；
- tamper detection。

The submission path must not derive a new resolution from semantically unverified historical records.

### Current implementation

`store.list_resolutions()` verifies:
- JSON/canonical bytes；
- filename/id；
- canonical resolution ID。

`store._validate_graph()` verifies:
- prior ID/hash structure；
- supersession graph；
- competing children/cycles。

But it does **not** recompute existing resolution target/evidence/before semantics against the immutable P5/P6/P7 base.

`submit_resolution()` then does:

`existing = list_resolutions(...) → active = _validate_graph(existing) → active_effective_assignments(active)`

before any semantic recomputation of those existing resolutions.

`active_effective_assignments()` trusts persisted `resolution.before["affected_fact_ids"]`.

The semantic recomputation currently lives in `resolve._validate_resolution_semantics()` and is invoked while generating/materializing selected resolutions, not before a new submission derives its prior effective state.

Additionally, `_generate()` semantically validates selected resolutions, but does not independently validate every superseded historical record before historical records are used as dependencies/support.

### Impact

A syntactically canonical, re-signed historical resolution whose `before` / evidence semantics were altered can survive `list_resolutions()` / graph validation and may be consumed by:
- a later `submit_resolution()` prior-state calculation；
- attestation evidence inheritance；
- historical dependency reconstruction。

Materialization catches some active-record tampering, but the design requires the immutable resolution history itself to be semantically validated, not only the currently selected active records.

### Required correction

Create one authoritative semantic history validation path.

It must:
1. load the base bundle/fingerprints；
2. parse/canonical-check all resolution files；
3. graph/prior-state validate all records；
4. recompute every resolution's semantics from its explicit `base_active_resolution_ids`；
5. validate direct evidence or inherited attestation evidence；
6. recompute `before` / `after`；
7. reject any semantic mismatch before the history is used for a new submit/materialization/snapshot load；
8. validate superseded historical records too, not only terminal active records。

Reuse one implementation rather than duplicating semantic validation between store and resolve.

Required tests include:
- re-signed tampered `before.affected_fact_ids` rejected by a subsequent `submit_resolution` before a new record is persisted；
- re-signed tampered superseded historical parent rejected by materialize/load；
- tampered supporting resolution evidence cannot be inherited by a later attestation；
- CLI `resolutions` must not report a semantically corrupt store as successful if it is intended as the validated resolution loader surface。

Verdict: **BLOCKER**

---

## 3. Finding F2 — MAJOR — fill-value persistence violates P9 value-normalization contract

### Design requirement

Section 18 requires:
- trim；
- whitespace collapse **for comparison**；
- preserve submitted value in resolution `value`；
- resolved effective value uses submitted trimmed value；
- no period/unit/scope canonicalization。

### Current implementation

`evidence.normalize_semantic()` collapses whitespace.

`_fill_selection()` assigns:

`wanted = normalize_semantic(value)`

and then stores that collapsed string as `TargetSelection.normalized_value`.

`submit_resolution()` persists:

`value = selection.normalized_value`

and materialization uses that persisted value as the effective field.

### Impact

For a caller value such as:

`"  人民币   百万元  "`

the designed persisted/effective value is the caller's trimmed value:

`"人民币   百万元"`

while comparison may use:

`"人民币 百万元"`

The current implementation instead persists/effectively exposes the collapsed form, changing source-preserving reviewer semantics.

### Required correction

Separate:
- submitted trimmed value used for persistence/effective output；
- normalized comparison value used only for equality/conflict comparison。

Do not canonicalize period/unit/scope text.

Add tests proving:
- leading/trailing whitespace is trimmed；
- internal whitespace is preserved in persisted resolution value and resolved effective value；
- explicit raw comparison still uses whitespace-collapsed comparison semantics。

Verdict: **MAJOR**

---

## 4. Finding F3 — MAJOR — justification length contract is implemented incorrectly

### Design requirement

Section 49:

`justification仅审计文本，max 4000 chars。`

### Current implementation

`validate_reviewer()`:
- normalizes/collapses justification whitespace；
- permits normalized length up to **4096**；
- `submit_resolution()` persists the original unnormalized justification。

### Impact

Two mismatches:
1. configured maximum is 4096 instead of 4000；
2. validation is against collapsed text while persistence uses raw text, so an arbitrarily large whitespace-heavy payload can pass the validation and then be persisted。

### Required correction

At minimum:
- require justification to contain non-whitespace text；
- enforce **raw persisted string length <= 4000 characters**；
- do not allow whitespace normalization to bypass the persisted-length bound。

Add boundary tests:
- 4000 chars accepted；
- 4001 chars rejected；
- whitespace-heavy raw payload over 4000 rejected even when normalized form is short。

Verdict: **MAJOR**

---

## 5. Finding F4 — MAJOR — production uses random UUID despite explicit determinism prohibition

### Design requirement

Section 44 explicitly states P9 must not use:
- random UUID；
- implicit current time；
- filesystem order。

### Current implementation

`queue.prepare_review_overlay()` imports `uuid` and creates the staging directory with:

`uuid.uuid4().hex`

### Impact

The final persisted artifact is deterministic, but production still directly violates the explicit no-random-UUID rule.

### Required correction

Use a deterministic staging name/strategy consistent with append-only/atomic persistence.

The fix must not introduce destructive cleanup of unrelated state.

If a deterministic stale/in-progress staging directory exists, fail safely with a P9 persistence/corruption reason rather than silently deleting unknown work.

Add a source/scope test proving the P9 package no longer uses `uuid.uuid4` or another random identity source.

Verdict: **MAJOR**

---

## 6. Finding F5 — TEST GAP — development/51 minimum CLI coverage was not completed

`development/51` required tests for:
- deterministic prepare/tasks/resolutions/materialize/report serialization；
- submit via explicit JSON string；
- submit via explicit JSON file；
- malformed/non-object submission rejection。

The pushed focused test file contains only two direct CLI tests:
- tasks success JSON stdout；
- tasks failure JSON stderr。

The implementation exposes all six commands, but the required CLI test matrix is incomplete.

### Required correction

Add direct CLI tests for:
- prepare；
- tasks；
- submit --input-json；
- submit --input-file；
- resolutions；
- materialize；
- report；
- malformed JSON；
- non-object JSON。

For successful calls:
- exactly one JSON stdout document；
- empty stderr。

For handled failures:
- stdout empty；
- one deterministic diagnostic on stderr；
- non-zero exit。

This finding is a test-completeness blocker for P9-G because the active development instruction explicitly required it.

Verdict: **MAJOR / TEST BLOCKER**

---

## 7. Reviewed areas that are acceptable

The GitHub review found the following implementation directions consistent with the current design:

- base catalog/P3/P5/P6/P7 fingerprint validation；
- REVIEW-only deterministic queue generation；
- supported/unsupported reason mapping；
- timezone-aware reviewer validation；
- fill-only raw-field conflict/no-effect behavior；
- P5/P6 evidence target relationship checks；
- attestation direct-evidence rejection and inherited evidence construction；
- explicit `base_active_resolution_ids` and `base_overlay_set_hash_before` persistence；
- supersession graph checks；
- same-value overlap / different-value materialization conflict；
- raw fact preservation in resolved facts；
- zero-overlay snapshot；
- snapshot byte/semantic comparison；
- resolved validation status and reuse eligibility；
- deterministic resolved `ParsedDataRecord` construction；
- JSON-only stdout for the directly tested CLI success path；
- no external AI/network/MCP SDK surface in the candidate；
- no P10/P11 implementation scope creep。

These PASS observations do not override F1-F5.

---

## 8. Review verdict

P9-G GitHub Review:

**CHANGES REQUIRED**

P9-I authorization:

**DENIED / REMAINS CLOSED**

Reason:
- F1 is a correctness/tamper-validation blocker；
- F2-F4 are direct design-contract mismatches；
- F5 leaves explicit P9-G test requirements incomplete。

No design semantic amendment is required for F1-F5: the current design already specifies the required behavior.

Next authorized activity:
- corrective P9-G implementation/tests only；
- full focused/full-unit/compile/diff/scope/immutability/synthetic rerun；
- normal push；
- stop for another GitHub review。

P9-I/J/K/L/M remain unauthorized.
