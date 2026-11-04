# 175 — P11 Parsed Artifact Path Amendment Evidence — ISSUE-031

Status: **PASS — AMENDED DESIGN READY FOR CANDIDATE FREEZE**

Phase:
P11 — US SEC Provider

Historical reviewed candidate:
`85df002516d577531e68c303ad86c0903ca813c6`

Review stop:
`development/174-p11-artifact-path-contract-review-stop.md`

Production remains CLOSED.

## P11-ISSUE-031 resolution

For P11 periodic `ParsedDataRecord`:

`artifact_path` has one exact meaning:

`project-root-relative POSIX path to <parsed_root>/<parse_run_id>/export-v2`

The stored path:

- points to the v2 export directory;
- never points to manifest.json or another child file;
- never points to a staging/partial directory;
- contains no trailing slash.

Path construction:

- `parse_run_id` must match lowercase 64-hex;
- `parsed_root` resolves inside project_root;
- complete export-v2 directory is atomically committed before registry persistence.

Failure classification:

- null artifact_path => P11_REUSE_ARTIFACT_MISSING;
- safe expected directory absent => P11_REUSE_ARTIFACT_MISSING;
- absolute/drive-relative/UNC/traversal/outside-root/wrong-layout/child-file path => P11_REUSE_ARTIFACT_PATH_INVALID;
- expected path exists but is not a directory => P11_REUSE_ARTIFACT_INVALID;
- required v2 file missing => P11_REUSE_ARTIFACT_INVALID;
- loader/hash/schema/identity failure => P11_REUSE_ARTIFACT_INVALID.

## Prior issue regression

ISSUE-010..030 remediation remains intact.

No registry schema migration is introduced.

## Scope

Design/governance only.

No src/tests/integration/runtime-lock change.

## Verdict

# PASS — READY FOR CANDIDATE FREEZE AND FRESH DETACHED DESIGN REVIEW

No production authorization is implied.
