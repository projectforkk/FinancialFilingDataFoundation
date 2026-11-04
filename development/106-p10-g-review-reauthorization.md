# 106 — P10-G Detached Documentation Review Reauthorization

Status: **AUTHORIZED — P10-G REVIEW RERUN ONLY / P10-ISSUE-006 AMENDED BASELINE**

Phase:
`P10 — Codex Dynamic Research Integration`

Gate:
`P10-G — Thin Integration Instruction`

Design baseline:
`d896173`

Exact candidate artifact commit:
`3a805a8f333ac20770d6aec1c8285d93993d18fc`

Artifact:
`integration/p10/FFDF_RESEARCH_INTEGRATION.md`

Frozen Git-blob SHA256:
`ef10406c9957f7a68a9af001c913deef0a057e166100a2d852c0c8fcd2c46296`

Original evidence:
`development/103-p10-g-integration-instruction-evidence.md = PASS`

Historical stopped review:
`development/105-p10-g-detached-review-stop.md`

Only the P10-G detached documentation review rerun is authorized.

## Identity contract

Review must freeze both:

- exact candidate commit `3a805a8f333ac20770d6aec1c8285d93993d18fc`;
- SHA256 of the exact Git blob content bytes for
  `integration/p10/FFDF_RESEARCH_INTEGRATION.md`.

Do not use arbitrary checked-out worktree bytes as artifact identity.

Blob extraction must be binary-safe.

On Windows, an acceptable pattern is:

```text
cmd /d /c "git cat-file blob <candidate>:integration/p10/FFDF_RESEARCH_INTEGRATION.md > <project-local-temp-file>"
```

Then hash the temp file bytes.

Do not hash Git output after routing it through a PowerShell object/text pipeline that can decode/re-encode bytes.

The exact Git blob must:

- SHA256 = `ef10406c9957f7a68a9af001c913deef0a057e166100a2d852c0c8fcd2c46296`;
- length = 10383 bytes;
- decode as UTF-8;
- contain no UTF-8 BOM;
- contain LF representation in the blob.

A detached Windows checkout may materialize CRLF because `core.autocrlf=true`; record that as checkout representation only.

## Review scope

Create a fresh detached worktree under:

`D:\\Codex\\FinancialFilingDataFoundation\\worktrees\\review\\p10-g-<authorization-sha>`

Review:

- design/24 Section 29 / 29.1;
- design/25 P10-G;
- acceptance/38 items 43–45, 70, and Section 2.2;
- development/102;
- development/103;
- development/105;
- exact candidate artifact.

Verify all original P10-G documentation/scope requirements plus the amended Git-blob identity contract.

## Forbidden

Do not:

- modify candidate artifact;
- modify detached worktree;
- add `.gitattributes` merely for this issue;
- start P10-H;
- start Research MCP production;
- start Semantic Resolver production;
- start P11 production.

## Result

Write rerun result only after independent review completes.

Allowed verdict:

`PASS / FAIL / BLOCKED`

PASS closes P10-G review and permits a separate P10-H authorization.
