# Independent Acceptance Negative Spec — Corrupt P9

Use accepted CN 600519 FY2024 document:
5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30

Construct a fresh isolated P9 store at its final acceptance path through accepted P9 APIs.
Create one supported evidence-grounded period resolution for the target RawFact.
First prove P10 P9_DURABLE_RESOLVED provenance validates PASS.

Then tamper only the isolated negative snapshot fixture.

Required result:
- fresh P10 ledger validation blocks with P10_UPSTREAM_INVALID;
- no silent raw fallback;
- accepted/source P8/P9 state remains unchanged.
