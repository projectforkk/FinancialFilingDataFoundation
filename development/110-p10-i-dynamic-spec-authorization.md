# 110 — P10-I Dynamic Spec Integration Authorization

Status: **AUTHORIZED — P10-I INTEGRATION VALIDATION ONLY / NO PRODUCTION CHANGES**

Phase:
`P10 — Codex Dynamic Research Integration`

Gate:
`P10-I — Dynamic Spec Integration`

Current design baseline:
`d8961731044d6c33c8a9e2cb96820819c3daa275`

P10-H evidence:
`development/109-p10-h-full-regression-scope-evidence.md = PASS`

P10-H evidence commit:
`99b7d25`

P10 source production candidate remains:
`d8e7d81b4bb5a4f06cead9eba0e2d09884094676`

P10-G integration instruction candidate remains:
`3a805a8f333ac20770d6aec1c8285d93993d18fc`

Only P10-I dynamic-spec integration validation is authorized.

## Fixture boundary

Use only project-local workspace:

`D:\\Codex\\FinancialFilingDataFoundation\\workspace\\research-runs\\p10-i`

Do not mutate historical P8/P9 test outputs.

A copied synthetic accepted-style P8 fixture may be used.

Do not use the CN/HK live COMPLETE fixture as the P10-I primary run; that belongs to P10-J.

## Spec A / Spec B

Create at least two materially different runtime specs.

Required development pair:

- Spec A: request a table/page provenance result;
- Spec B: request a raw-fact/evidence provenance result.

The two specs must:

- be separate explicit files;
- be frozen before the run;
- have exact raw-byte SHA recorded;
- produce different `spec_bundle_hash` values;
- be read completely by the reasoning host;
- require different information needs;
- cause different P8 tool selections;
- use the same P10 production code.

No P10 code/instruction change is allowed between A and B.

## Required run evidence

For each spec record:

- frozen file path and raw SHA;
- spec bundle hash;
- full spec text read;
- derived information need;
- exact P8 tool calls chosen by the reasoning host;
- output matching that spec;
- P10 evidence ledger;
- `validate-ledger` PASS;
- research context ID.

The selected tool sets for A and B must be materially different.

A valid outcome example:

- A uses table/page-oriented P8 calls;
- B uses raw-fact/evidence-oriented P8 calls.

Do not create a fixed question-id → tool mapping in production or integration instruction.

## Immutability / scope

Before/after hash the copied P8 base fixture.

No P8/P9 accepted artifact, source, test, runtime, or Registry mutation is authorized.

No P9 mutation is required for P10-I.

No production/tests/design changes are authorized.

## Evidence

Write:

`development/111-p10-i-dynamic-spec-evidence.md`

only after Spec A and Spec B both pass.

PASS closes P10-I and permits a separate P10-J authorization.

P10-J and later remain closed until separately authorized.
