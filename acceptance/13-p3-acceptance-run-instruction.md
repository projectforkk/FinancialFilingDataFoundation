# 13 — P3 Independent Acceptance Run Instruction

状态：**P3-I ACCEPTANCE INPUT FREEZE**

Final verdict only:

- PASS
- FAIL
- BLOCKED

Acceptance must not modify production code, tests, design, dependencies, or source PDFs.

Do not start P4.

## 1. Repository / Phase

Repository:

`projectforkk/FinancialFilingDataFoundation`

Phase:

`P3 — Native Page / Section / FTS`

Formal branch:

`task/p3-native-page-section`

Accepted P2 baseline:

`4add9fff36b61e2521e9c8d749cee829adb4ab6f`

Reviewed P3 production candidate:

`3c3536db0bdfdfbc5300004731b04d992930904f`

Code Review commit:

`f86868b47ad4dd74b3c277cb2436cbb615073e13`

Code Review verdict:

`PASS`

## 2. Frozen Candidate

The commit containing this file is the exact frozen acceptance candidate.

After commit, write that SHA to PROJECT_STATUS in a later status-only commit.

Acceptance uses the exact frozen commit in a fresh detached worktree.

## 3. Mandatory Read

- AGENTS.md
- PROJECT_STATUS.md
- design/03-parsed-financial-document-contract.md
- design/10-p3-native-page-section-design.md
- design/11-p3-implementation-plan.md
- development/22-p3-development-instruction.md
- development/23-p3-development-evidence.md
- development/24-p3-pre-review-amendment.md
- development/25-p3-code-review.md
- acceptance/12-p3-acceptance-instruction.md
- this file

## 4. Isolation

Fresh detached worktree:

`D:\Codex\FinancialFilingDataFoundation-P3Acceptance-<shortsha>`

Create ignored workspace explicitly.

Before/after every critical command group:
- git rev-parse HEAD
- git status --short --branch

HEAD must remain exact frozen SHA.

## 5. Runtime

Use existing FFDF runtime:

`D:\Codex\FinancialFilingDataFoundation\.venv\Scripts\python.exe`

Expected:
- Python 3.14.9 ARM64
- PyMuPDF 1.28.2
- sqlite3 with FTS5
- no Dayu
- no Docling
- no Torch

No package changes during acceptance.

## 6. Full Suite

Run all unit tests.

Expected current count:

`104 passed`

Any product test failure = FAIL.

## 7. P0-P2 Integrity

Against accepted P2 baseline:

`4add9fff36b61e2521e9c8d749cee829adb4ab6f`

P0-P2 source/tests must have no differences.

## 8. Static P3 Scope

Verify:
- no Dayu
- no Docling
- no Torch
- no OCR
- no external AI/network
- no P4 table candidate/reconstruction implementation

## 9. CN Frozen Raw

Source path:

`D:\Codex\FinancialFilingDataFoundation\workspace\p2-live-acquisition-v2\raw\sha256\52\5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30.pdf`

Expected:
- SHA = `5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30`
- size = 3,626,217
- page_count = 143
- total <= 30000 ms

## 10. HK Frozen Raw

Source path:

`D:\Codex\FinancialFilingDataFoundation\workspace\p2-live-acquisition-v2\raw\sha256\70\70f529984a87ef7f46d9e1db26bb9ef27eef9c01d29c59aabf69e557b479a6a0.pdf`

Expected:
- SHA = `70f529984a87ef7f46d9e1db26bb9ef27eef9c01d29c59aabf69e557b479a6a0`
- size = 5,241,364
- page_count = 274
- total <= 30000 ms

## 11. Fresh Artifact Acceptance

For each raw sample use two fresh independent artifact roots A/B.

Verify:
- page sequence exactly 1..N
- pages.jsonl physical LF records == page_count
- no UTF-8 BOM
- no raw U+0085/U+2028/U+2029 bytes in JSONL
- words/blocks/spans/bbox present
- image-only/empty native text pages are explicit
- source SHA/size/mtime unchanged
- pages.jsonl A == B byte-for-byte
- sections.jsonl A == B byte-for-byte
- section IDs/page ranges valid
- performance Gate PASS

Timings/document.json paths are excluded from byte determinism requirement.

## 12. FTS5

Verify:
- page_content canonical table
- page_fts uses:
  - content='page_content'
  - content_rowid='page_no'
- FTS metadata SHA/schema match manifest
- page search works after DB reopen
- section search works on a known section title from produced artifact or deterministic unit fixture
- query values parameterized

## 13. Artifact Corruption Guard

On a disposable copied/fresh artifact:
- delete a core file → load/reuse must raise ARTIFACT_INCOMPLETE_OR_CORRUPT
- tamper search metadata SHA → must raise ARTIFACT_INCOMPLETE_OR_CORRUPT
- damaged final artifact must not be silently replaced/deleted by reuse path

## 14. Reading / Section Contract

Spot-check:
- original block_no retained
- reading_order_index deterministic
- span font/size/flags/bbox available
- repeated header/footer flags exist where detected
- section parent IDs reference earlier valid sections or null
- page_start/page_end valid
- section_id stable

No requirement on absolute section count.

## 15. PASS

PASS requires:
- exact frozen candidate
- 104 tests PASS
- P0-P2 integrity
- runtime/heavy-path scope PASS
- fresh CN PASS
- fresh HK PASS
- source immutability
- JSONL line safety
- semantic artifact determinism
- FTS external-content contract
- corruption guard
- <=30s each
- no blocker

## 16. FAIL

FAIL for:
- missing pages
- wrong ordering/identity
- source mutation
- JSONL record corruption
- FTS contract mismatch
- incomplete artifact reused as success
- performance >30s on frozen born-digital sample
- P4/heavy-path scope intrusion
- test failure

## 17. BLOCKED

Only for external inability to judge, such as source file/runtime/FTS5 unexpectedly unavailable and not caused by candidate.

Final output:

`PASS / FAIL / BLOCKED`
