# 16 — P4 Independent Acceptance Run Instruction

状态：**P4-H ACCEPTANCE INPUT FREEZE**

最终 verdict：
PASS / FAIL / BLOCKED

不得修改 production/tests/design/config。

## 1. Phase

P4 — Table Candidate Detection

Accepted baseline before P4:
`24cb4571a9d9f97b4b963d6339970c931d979c4d`

Reviewed candidate:
`ea78b2f9adbf0ad6564146ba166da85d1085bf81`

Final Code Review:
- commit: `7ce5aec201b5af6ed475c9e858652e1015b1d147`
- verdict: PASS
- evidence: `development/29-p4-code-review.md`

Frozen acceptance candidate:
**the Git commit containing this file**.
Exact SHA is recorded in PROJECT_STATUS after this freeze commit.

## 2. Isolation

Create fresh detached worktree:
`D:\Codex\FinancialFilingDataFoundation-P4Acceptance-<shortsha>`

Record HEAD before/after every critical group.

## 3. Runtime

Use:
`D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe`

No dependency changes.

## 4. Full Suite

Run all:
`tests/unit`

Expected current count:
`133 passed`

## 5. Prior-phase Integrity

P0–P3 source/tests must have zero diff versus:
`24cb4571a9d9f97b4b963d6339970c931d979c4d`

except P4 candidate package/tests.

## 6. Live P3 Inputs

CN:
`D:\Codex\FinancialFilingDataFoundation-P3Acceptance-7b81c97\workspace\p3-live\cn-a\5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30`

HK:
`D:\Codex\FinancialFilingDataFoundation-P3Acceptance-7b81c97\workspace\p3-live\hk-a\70f529984a87ef7f46d9e1db26bb9ef27eef9c01d29c59aabf69e557b479a6a0`

## 7. Live Acceptance

Use two fresh candidate roots per market.

Verify:
- candidates.jsonl A == B byte-for-byte
- CN candidate_count > 0
- HK candidate_count > 0
- HK pages 124 / 126 / 133 each have candidate
- CN <= 5s
- HK <= 10s
- P3 artifacts unchanged
- source PDF bytes/size/mtime unchanged

## 8. Artifact Integrity

Independently verify:
- valid reuse
- corrupt manifest blocked
- corrupt JSONL blocked
- count mismatch blocked
- page out of range blocked
- changed/invalid bbox blocked
- noncanonical block_nos blocked
- forged candidate_id blocked by recomputation

## 9. Scope

Verify no:
- source PDF open from P4
- OCR
- Dayu
- Docling
- network
- Torch
- external AI
- cells / reconstructed rows / columns
- cross-page reconstruction

## 10. PASS

PASS requires all frozen conditions above.

P4 PASS authorizes only P4 closeout and P5 design.

Do not implement P5 during P4 acceptance.
