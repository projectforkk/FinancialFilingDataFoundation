# 174 — P11 Registry-Parity Final Design Review Stop — Parsed Artifact Path Contract

Status: **FAIL / STOP — P11-ISSUE-031 / PRODUCTION CLOSED**

Phase:
P11 — US SEC Provider

Reviewed exact candidate:
`85df002516d577531e68c303ad86c0903ca813c6`

Fresh detached review:
`D:\\Codex\\FinancialFilingDataFoundation\\worktrees\\review\\p11-design-85df002`

Automated ISSUE-010..030 contract matrix:
`PASS`

## Finding

Manual review of accepted P1 `ParsedDataRecord.artifact_path: str | None` found one remaining P11 implementation ambiguity.

Current P11 design freezes:

- artifact_path non-null for periodic SEC reuse;
- project-root-relative POSIX;
- resolved inside configured parsed_root.

But it does not freeze whether artifact_path points to:

- the ParsedFinancialDocument v2 export directory;
- `manifest.json`;
- another file inside the export.

It also does not freeze the deterministic persistence layout under parsed_root.

Therefore P11-K persistence and the reuse selector/loader would have to invent incompatible path semantics.

## P11-ISSUE-031 — parsed artifact path / storage layout

Required correction:

### Stored path meaning

For P11 periodic ParsedDataRecord:

`artifact_path` MUST point to the **ParsedFinancialDocument v2 export directory**, never to manifest.json or another child file.

### Exact layout

Given configured project-local `parsed_root` and `parse_run_id`:

```text
<parsed_root>/<parse_run_id>/export-v2/
  manifest.json
  document.json
  source_assets.jsonl
  source_segments.jsonl
  sections.jsonl
  tables.jsonl
  raw_facts.jsonl
  evidence.jsonl
  validation.json
```

`parse_run_id` must satisfy lowercase 64-hex before use as a path component.

Registry stores `artifact_path` as normalized project-root-relative POSIX directory path to that exact `export-v2` directory.

No trailing slash is stored.

### Reuse path classification

- artifact_path null => P11_REUSE_ARTIFACT_MISSING;
- resolved safe path does not exist => P11_REUSE_ARTIFACT_MISSING;
- absolute/drive-relative/UNC/traversal/outside parsed_root => P11_REUSE_ARTIFACT_PATH_INVALID;
- existing path is not a directory => P11_REUSE_ARTIFACT_INVALID;
- directory exists but any required v2 file is missing => P11_REUSE_ARTIFACT_INVALID;
- loader/hash/schema/identity failure => P11_REUSE_ARTIFACT_INVALID.

### Persistence

P11-K writes the artifact atomically under the exact parse_run layout before registering ParsedDataRecord.

Registry write must never point to a staging/partial directory.

Acceptance must prove exact path round-trip and each failure classification.

## Scope

No production/test/runtime changes.

ISSUE-010..030 remediation remains valid.

## Verdict

# FAIL / STOP

Candidate `85df002...` is INELIGIBLE for DESIGN READY.

P11 production remains CLOSED.
