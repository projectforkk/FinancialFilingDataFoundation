# 48 — P8 Code Review After Dual-Runtime Test Boundary Amendment

状态：**PASS — READY FOR ACCEPTANCE REFREEZE**

Phase:
`P8 — Local MCP`

Reviewed candidate:
`537ebbd17454f80c8838f58abbbd02d5994f8716`

Accepted baseline before P8:
`5f314bab9d88fb16b4b46c662e0a9f1b8f1a9b13`

P8-ISSUE-006 design:
`bdab6a81bea6597ab2c12256497ed68d04363ea2`

Test amendment:
`f41e6a1eea1f2f60fc9b70ed5a5aa7b76f59562b`

Development amendment evidence:
`development/47-p8-dual-runtime-test-amendment.md`

Review worktree:
`worktrees/review/p8-537ebbd`

## 1. Review Isolation

Detached HEAD before/after critical groups:

`537ebbd17454f80c8838f58abbbd02d5994f8716`

Tracked worktree remained clean.

Result: **PASS**

## 2. Full Regression

Project-root short basetemp used.

Result:

`235 passed in 5.81s`

P0–P7 accepted source/tests remain unchanged outside the new P8 MCP package/tests.

Result: **PASS**

## 3. P8-ISSUE-006 Test Boundary

Verified:

- main ARM64 runtime does not require external MCP SDK;
- main pytest suite executes SDK-free static Catalog/Service/server-surface checks;
- dedicated MCP runtime remains production-only and does not require pytest;
- tracked standalone `tests/integration/mcp_stdio_check.py` executes under the dedicated runtime;
- dedicated runtime lock was not changed.

Result: **PASS**

## 4. Official SDK Integration

Runtime:
- Python 3.12.14 AMD64
- mcp 2.3.0

Observed:
- protocol: `2026-07-28`
- cold connect/list-tools: `1169.508 ms`
- exact tools: `11 / 11 PASS`
- CN first trusted bundle: `10401.029 ms`
- HK first trusted bundle: `15434.089 ms`
- invalid document -> MCP tool error: PASS
- CN/HK live calls: PASS

Warm:
- list_documents: 3.061 ms
- get_document: 2.791 ms
- search: 6.467 ms
- read_pages: 2.985 ms
- get_table: 3.974 ms
- fact/evidence: 5.647 ms
- validation: 2.251 ms

All frozen performance gates PASS.

## 5. Runtime Lock

Tracked lock:
`runtime-locks/mcp-2.3.0-py312-win-amd64.lock.txt`

Expected / observed SHA256:

`8e958b8abcfd9b2de829451ffc253932fa26bb473f73837484b75b1019f092ec`

Verified in fresh detached worktree:
- Git blob SHA: MATCH
- working-tree SHA: MATCH
- bytes equal: true
- BOM: false
- CRLF: false
- git attributes: text=set, eol=lf

Installed package set:
- lock count: 30
- installed count: 30
- exact normalized match: true

Result: **PASS**

## 6. Runtime / Security Scope

Verified:
- FFDF main runtime external mcp: absent
- dedicated runtime isolated
- server transport: stdio only
- no HTTP/SSE invocation
- no arbitrary filesystem/SQL/Python/shell tool
- no network/AI imports in P8 business/server code
- no mutation tool
- no P9/P10/P11 implementation

Result: **PASS**

## 7. Findings

Blocking findings:

**NONE**

P8-ISSUE-006:
**CLOSED / PASS**

The previous Independent Acceptance result predates P8-ISSUE-006 and is historical for final closeout purposes.

## 8. Conclusion

# P8-I CODE REVIEW = PASS

Authorized transition:

`P8_IN_REVIEW → P8_READY_FOR_ACCEPTANCE_REFREEZE`

A new acceptance freeze is mandatory because the design changed after the earlier PASS.
