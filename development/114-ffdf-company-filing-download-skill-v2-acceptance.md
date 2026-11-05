# 114 — FFDF公司财报下载 Skill v2 Status-First Optimization Acceptance

## Candidate

Design commits:

- `d4e632f design: add status-first optimization to filing download skill`
- `d3d979a design: refine filing skip and reload semantics`

Implementation commit:

- `9e92bde feat: skip already-ingested filings by default`

## User-confirmed behavior

Final rule:

> 只要当期财报已经入库就跳过，除非明确指定“重新读入”。

## Invocation

Two required parameters remain:

`$FFDF公司财报下载 <company_code> <year_or_range>`

Optional control word:

`重新读入`

Example:

`$FFDF公司财报下载 605117 2021-2026 重新读入`

The control word is not a third required parameter.

## Default status-first behavior

For every requested year/period:

1. run `ffdf status`;
2. if `p8_catalog_registered == true` and local status is not CONFLICT / DRIFTED / AMBIGUOUS:
   - normalize to `SKIPPED_ALREADY_INGESTED`;
   - do not call `ffdf ingest`;
3. otherwise run standard `ffdf ingest`.

This avoids redundant download/parse/validation/catalog work for already-ingested filings.

## Explicit reload behavior

When the exact optional directive `重新读入` is present:

- bypass the already-ingested skip;
- call the standard `ffdf ingest` for requested slots;
- keep FFDF immutable/incremental semantics;
- do not delete Raw;
- do not clear Registry;
- do not delete P3-P7;
- do not force a duplicate same-SHA PDF download.

Thus “重新读入” means re-run the standard ingest flow, not destructive rebuild.

## Integrity exception

Even when P8 catalog contains the slot, do not silently skip if status reports:

- CONFLICT
- DRIFTED
- AMBIGUOUS

These remain blockers.

## Focused test

`tests/unit/skills/test_ffdf_company_filing_download_skill.py`

Result:

**12 PASS / 0 FAIL**

Coverage added for:

- status-first command;
- P8 registered skip;
- SKIPPED_ALREADY_INGESTED;
- explicit 重新读入 directive;
- non-destructive reload semantics;
- conflict/drift/ambiguity fail-closed behavior.

## Full FFDF unit regression

Result:

**526 PASS / 0 FAIL**

## Scope

No production acquisition/parser/Registry/P8 code changed.

Only:

- Skill orchestration;
- Skill UI text;
- Skill README;
- static Skill contract tests;
- design/acceptance evidence.

Existing untracked directories remained untouched:

- `00document/`
- `01prompt/`

## Verdict

**OPTIMIZATION V2 ACCEPTANCE: PASS**
