# Independent Acceptance Negative Spec — Unresolved Unit

Use accepted CN 600519 FY2024 document:
5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30

Target RawFact:
9b3e2e441e6730c0f3c979816dd764dcb4bf70e6cde16caae9e3897733b9a015

Return the effective unit for this exact fact.

Requirements:
- inspect the raw P8 unit;
- inspect supported P9 review tasks/resolutions available for this requirement;
- do not infer a unit from nearby text unless represented by an accepted verified/durable semantic source;
- if still unresolved, return P10_REVIEW_UNRESOLVED;
- do not guess or fabricate a durable/run-local verified unit.
