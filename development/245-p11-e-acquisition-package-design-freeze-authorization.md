# 245 - P11-E SEC Acquisition / Package Design Freeze Authorization

Status: **AUTHORIZED - DESIGN/PROBE ONLY / P11-E IMPLEMENTATION CLOSED / PROVIDER PRODUCTION CLOSED**

Prerequisite:
`development/244-p11-d-final-detached-code-review-result.md = PASS / P11-D CLOSED`

Phase:
P11-E - SEC Package Store / Acquisition

Authorized design work:

- create exact P11-E acquisition/package contract in `design/32-p11-e-acquisition-package-contract.md`;
- reconcile existing `design/26`, `design/27` and `acceptance/41` package requirements without weakening them;
- run read-only project-local live SEC probes necessary to freeze actual accession `index.json` schema and response behavior;
- inspect existing registry/P2 raw-store interfaces for compatibility boundaries;
- run project-local semantic/static/concurrency probes under `workspace/scratch/p11-e-design/`;
- update design/governance evidence only.

Live SEC probe constraints:

- use only the already configured `SEC_USER_AGENT`; never print or persist its value;
- read-only GET only against accepted SEC hosts;
- no provider production authorization implied;
- persist only normalized schema/size/hash observations, never contact identity.

Design must freeze before any production code:

1. exact accession `index.json` schema/type validation;
2. exact Archive URL and safe-basename rules;
3. asset selection/role precedence and optional exhibit semantics;
4. HTTP/content framing and per-response/package resource caps;
5. canonical source-package identity and exact on-disk manifest bytes;
6. content-addressed blob/package/receipt layout and project-root containment;
7. staging, atomic no-replace commit, concurrent-writer and existing-destination verification semantics;
8. exact receipt identity/schema/collision behavior;
9. source-drift preservation and idempotency semantics;
10. primary raw-byte registry registration ordering/failure boundary without modifying P2 RawDocumentStore;
11. exact focused implementation matrix and failure reason mapping;
12. P11-E/P11-F boundary: no parser/runtime/taxonomy-cache implementation.

Forbidden during this gate:

- no `src/` or `tests/` production implementation change;
- no registry schema/API change;
- no P2 RawDocumentStore behavior change;
- no runtime-lock dependency change;
- no P11-F or later implementation;
- no provider production authorization.

Any material unresolved provider/schema/concurrency choice requires STOP rather than implementation-time guessing.
