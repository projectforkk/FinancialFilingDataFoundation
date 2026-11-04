# 114 — P10-J Live Run Reauthorization

Status: **AUTHORIZED — P10-J RERUN ONLY / P10-ISSUE-007 AMENDED BASELINE**

Phase:
`P10 — Codex Dynamic Research Integration`

Gate:
`P10-J — Live P8/P9 Research Run`

Amended design baseline:
`668269e`

Historical authorization:
`development/112-p10-j-live-run-authorization.md`

Stop record:
`development/113-p10-j-live-run-stop.md`

Only the P10-J live rerun is authorized.

## Primary filing

Use accepted CN live filing:

- market `CN`
- ticker `600519`
- fiscal year `2024`
- filing type `ANNUAL`
- document SHA
  `5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30`

## Runtime spec

Reuse the already frozen/read P10-J runtime spec if it still verifies byte-for-byte:

`workspace/research-runs/p10-j/inputs/live-cn-spec.md`

If the spec changed, STOP.

## Isolated P9 root

Do not reuse the invalid copied review root.

Preserve it as stopped-run evidence.

Use a new final isolated root:

`workspace/research-runs/p10-j/review-v2`

Construct it only through accepted P9 APIs:

1. `prepare_review_overlay`;
2. inspect current generated tasks;
3. identify the supported `RAW_PERIOD_COVERAGE_LOW / SET_PERIOD` task relevant to the target raw fact;
4. submit only the evidence-grounded period value `2024` using accepted P5 evidence;
5. materialize;
6. load/validate the new isolated snapshot.

Do not copy/move/edit an existing P9 review store.

## Immutability

Source live P9 root:

`workspace/p9-live-review`

must remain byte-identical.

Accepted P8 catalog/P3/P5/P6/P7 base must remain byte-identical.

Raw fact metric/value/parsed numeric value must remain unchanged.

## Resume requirements

Rebuild P10 ResearchContext using:

`p9_review_root=workspace/research-runs/p10-j/review-v2`

Then complete the frozen live spec:

- P8 document/validation;
- target fact/evidence/table/page;
- isolated P9 resolution/snapshot;
- raw period vs effective period;
- explicit REVIEW_REQUIRED usability boundary;
- explicit non-canonical reuse;
- evidence ledger with P8_RAW_DIRECT + P9_DURABLE_RESOLVED;
- fresh P10 ledger validation PASS;
- run_status=COMPLETE only if every required field is supported.

## Evidence

On PASS write:

`development/115-p10-j-live-research-evidence.md`

P10-K and later remain closed until P10-J evidence is committed/pushed and separately authorized.
