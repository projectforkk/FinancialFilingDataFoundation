# 20 — P2 Pre-Code-Review Amendment Evidence

状态：**P2-ISSUE-006 / P2-ISSUE-007 CLOSED**

Branch:

`task/p2-acquisition-provider`

Design correction baseline:

`752c6148fd06604384189572f0cd630a82b13a6d`

---

## 1. P2-ISSUE-006 — Receipt request_id / runner_version

Problem:

The P2 receipt contract required actual runner request identity and runner version, but the initial service receipt omitted both fields.

Correction:

- runner constant:
  `RUNNER_VERSION = p2-dayu-runner-v1`
- doctor/discover/download responses include runner_version;
- `RunnerDownloadedAsset` retains:
  - request_id
  - runner_version
- service receipt writes both fields;
- receipt_id formula remains unchanged.

Focused deterministic tests verify fake runner receipt fields.

---

## 2. P2-ISSUE-007 — Duplicate source metadata conflict

Problem:

Exact candidate dedup used dict last-wins for identical `(source_id, source_url)`.

Correction:

- candidates are grouped by source identity;
- key metadata is compared;
- identical duplicate records dedup deterministically;
- conflicting metadata returns:
  `REVIEW_REQUIRED / ACQUISITION_CANDIDATE_METADATA_CONFLICT`
- no download occurs for conflict.

Focused tests verify:

- identical duplicate → one download;
- conflicting title metadata → REVIEW_REQUIRED;
- provider order does not determine the semantic result.

---

## 3. Deterministic Regression

P2 acquisition focused:

```text
33 passed
```

Full P0 + P1 + P2 unit/regression suite:

```text
87 passed in 2.56s
```

Additional:

- compileall: PASS
- git diff --check: PASS

---

## 4. Fresh Live Re-run

A new isolated live workspace was used so the prior Registry could not short-circuit before generating the corrected receipt:

`workspace/p2-live-acquisition-v2`

### CN 600519 FY2024

First:

`DOWNLOADED`

SHA:

`5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30`

Receipt:

- request_id begins `download-`
- runner_version = `p2-dayu-runner-v1`

Second:

`REUSED_LOCAL`

### HK 00700 FY2024

First:

`DOWNLOADED`

SHA:

`70f529984a87ef7f46d9e1db26bb9ef27eef9c01d29c59aabf69e557b479a6a0`

Receipt:

- request_id begins `download-`
- runner_version = `p2-dayu-runner-v1`

Second:

`REUSED_LOCAL`

### Upstream

After fresh CN/HK live rerun:

- Dayu checkout clean: true
- Dayu HEAD:
  `2115c86d5a9027bb51cbbc8a4d0175080732e4e6`

Machine evidence:

`workspace/p2-live-acquisition-v2/live-acquisition-evidence.json`

---

## 5. Gate Impact

Revalidated:

- P2-G runner contract: PASS
- P2-I service/receipt: PASS
- P2-J deterministic mocked integration: PASS
- P2-K full regression: PASS
- P2-M live CN: PASS
- P2-N live HK: PASS
- P2-O incremental rerun: PASS

Next:

**P2-P Code Review**
