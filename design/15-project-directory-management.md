# 15 — Project Directory / Workspace Management 详细设计

状态：**ACTIVE GOVERNANCE BASELINE**

适用阶段：P6–P11 及后续维护。

## 1. 唯一项目根

FFDF 在目标 PC 的唯一项目管理根：

`D:\Codex\FinancialFilingDataFoundation`

除操作系统/用户级工具外，**所有 FFDF 自有文件与目录必须位于该根目录以内**。

禁止继续新增：
- `D:\Codex\FinancialFilingDataFoundation-*`
- `D:\Codex\dependencies\<FFDF dependency>`
- `D:\Codex\runtimes\<FFDF runtime>`

## 2. Canonical Layout

```text
D:\Codex\FinancialFilingDataFoundation\
  .git/
  src/
  tests/
  design/
  development/
  acceptance/

  dependencies/
    dayu-agent/

  runtimes/
    ffdf-dayu-2115c86/
      .venv/

  worktrees/
    active/
    review/
    acceptance/
    archive/

  workspace/
    current/
    live/
    acceptance/
    archive/

  data/
```

## 3. Tracked / Untracked Boundary

Git tracked：
- src
- tests
- design
- development
- acceptance
- PROJECT_STATUS.md
- AGENTS.md
- configuration / source code

Git ignored operational roots：
- `/dependencies/`
- `/runtimes/`
- `/worktrees/`
- `/workspace/`
- `/data/`

这些目录虽然位于 project root，但不是 source-of-truth Git artifacts。

## 4. Main Checkout

项目根自身是 canonical Git checkout。

目标稳态：
- `D:\Codex\FinancialFilingDataFoundation` checkout `main`
- 不再使用 `FinancialFilingDataFoundation-main-sync-*` sibling 目录作为 main
- phase branch 在需要时使用 project-contained isolated worktree

## 5. Phase Worktree Naming

Active development：

`worktrees\active\p<phase>-<short-name>`

Code Review：

`worktrees\review\p<phase>-<shortsha>`

Independent Acceptance：

`worktrees\acceptance\p<phase>-<shortsha>`

历史需要保留的 checkout：

`worktrees\archive\<historical-name>`

所有 path 使用小写 phase prefix；SHA 只用作路径标签，不作为业务 identity。

## 6. Historical Worktree Policy

P0–P5 已完成阶段：
- Git commit/history 是正式真源；
- ignored workspace/live evidence 若仅存在本地，迁移到 `workspace\archive\<phase-or-worktree>`；
- clean、无独有本地 evidence 的 historical worktree 可安全退役；
- **dirty historical worktree 不得删除、reset、clean 或自动提交；允许使用 `git worktree move` 原样迁移到 `worktrees\archive\dirty\<name>`，前提是先记录 dirty file list，移动后再次验证 dirty status 完全一致**；
- 不使用 `git reset --hard` / `git clean`；
- worktree 退役前必须检查 tracked status 和 ignored evidence。

## 7. Dependency Layout

Dayu pinned checkout：

旧：
`D:\Codex\dependencies\dayu-agent`

新：
`D:\Codex\FinancialFilingDataFoundation\dependencies\dayu-agent`

要求：
- exact pinned commit
- detached or otherwise explicitly pinned
- clean worktree
- 不修改 upstream
- move/reclone 后重新核对 HEAD/status

## 8. Runtime Layout

Dayu runtime：

旧：
`D:\Codex\runtimes\ffdf-dayu-2115c86\.venv`

新：
`D:\Codex\FinancialFilingDataFoundation\runtimes\ffdf-dayu-2115c86\.venv`

Windows Python venv **不得直接文件搬迁作为正式迁移方式**，因为 launcher/metadata 可能含原路径。

迁移必须：
1. 保留旧 runtime；
2. 从已验收旧 runtime 导出完整 package freeze；
3. 生成 tracked runtime lock：`runtime-locks/dayu-2115c86-py312-win-amd64.lock.txt`；
4. 在新路径从 approved base Python 重建 venv；
5. 先按 runtime lock 安装全部第三方依赖；
6. 再以 `--no-deps` 从新 Dayu checkout 安装 pinned Dayu source，避免 resolver 漂移；
7. 新旧 package snapshot 除 source path 外必须一致；
8. doctor/import tests；
9. live/no-network smoke；
10. FFDF main runtime isolation check；
11. 新 runtime PASS 后旧 runtime 才可退役。

## 9. External Tools Exception

以下不属于 FFDF 自有目录，不要求搬入项目根：
- system/user Python base interpreter
- uv-managed base Python
- Git installation
- VS Code/Codex
- OS package caches
- unrelated project repositories，例如 FIReport

FFDF design 只记录 executable path，不复制这些系统工具。

## 10. Workspace / Evidence

所有新 generated evidence：
- development smoke
- live samples
- review helper
- acceptance helper
- temporary DB
- generated PDFs for unit tests

必须位于 project-root `workspace/` 或 isolated checkout 自身被忽略的 workspace。

阶段结束后需要保留的本地-only evidence迁入：
`workspace\archive\P<phase>\...`

## 11. Raw Data

项目正式 raw/document store 必须位于：
`data/`
或用户明确配置的 project-root 子目录。

不得恢复到 `D:\Codex\<other-root>`。

## 12. Path Configuration

代码/设计中不得再把旧 sibling paths 写成新的默认值。

允许：
- historical evidence 保留旧 path，明确标注 historical
- migration receipt 记录 old_path/new_path

新 active configuration 必须使用 project-root layout。

## 13. Migration Safety

目录迁移顺序：

1. commit 本设计；
2. update .gitignore；
3. verify all source Git worktrees；
4. archive local-only evidence；
5. consolidate canonical main checkout；
6. migrate Dayu source；
7. rebuild Dayu runtime；
8. migrate/retire historical worktrees；
9. verify no FFDF-owned sibling directories remain；
10. run regression + Dayu doctor；
11. write migration receipt。

任何 dirty worktree：
`BLOCKED_DIRECTORY_MIGRATION_DIRTY_WORKTREE`

含义：禁止删除/清理/覆盖/自动提交。若是历史 worktree 且仅执行 Git-aware relocation，可在记录 dirty manifest 后原样移动到 `worktrees\\archive\\dirty`；移动前后 status 必须一致，否则立即停止。

## 14. Git-aware Move

Linked worktree 优先：
`git worktree move`

若 Git 不允许 nested linked worktree：
- 先 archive local-only evidence；
- remove clean historical worktree through `git worktree remove`；
- future isolated Review/Acceptance 使用 project-contained ignored Git checkout/clone strategy；
- 必须先更新本设计记录实际机制。

禁止用普通 `Move-Item` 搬一个 active linked worktree 然后手改 .git metadata。

## 15. Acceptance

目录迁移 PASS 必须满足：

1. canonical root = `D:\Codex\FinancialFilingDataFoundation`
2. root checkout main and clean
3. no project-owned `FinancialFilingDataFoundation-*` sibling dirs
4. Dayu source under project `dependencies`
5. Dayu runtime under project `runtimes`
6. Dayu pin/clean PASS
7. Dayu doctor PASS
8. FFDF main venv remains Dayu/Docling/Torch-free
9. historical local-only evidence preserved
10. full unit regression PASS
11. no source/history loss
12. PROJECT_STATUS records migration result

## 16. Directory Migration Issue Log

### DIR-ISSUE-001 — Historical P1 worktrees remain dirty

Migration audit found four historical P1 worktrees with tracked/untracked local changes:

- P1FinalReview2
- P1Freeze
- P1Review
- P1SchemaReview

These are historical local states, not accepted Git truth. Approved handling:

1. do not commit them into current main;
2. do not reset/clean/delete them;
3. record pre-move `git status --porcelain`;
4. relocate intact with `git worktree move` to `worktrees/archive/dirty/`;
5. verify post-move status byte-for-byte equivalent;
6. keep them until user explicitly authorizes retirement.

Clean historical worktrees can move to `worktrees/archive/clean/`.

### DIR-ISSUE-002 — Rebuilding Dayu runtime without a lock changed transitive dependencies

After relocating the pinned Dayu source checkout, an initial rebuild of the dedicated runtime from the same Dayu commit resolved newer transitive packages:

- `docling 2.145.0 -> 2.146.0`
- `docling-slim 2.145.0 -> 2.146.0`
- `filelock 4.2.6 -> 4.2.7`

Other checked core packages remained unchanged. Root cause: Dayu source commit was pinned, but the accepted runtime's transitive dependency set was not locked.

Approved solution:

1. old accepted runtime remains authoritative until migration completes;
2. export the old runtime's complete package freeze;
3. create tracked `runtime-locks/dayu-2115c86-py312-win-amd64.lock.txt` excluding the local `dayu-agent @ file://...` line;
4. rebuild the new runtime strictly from this lock;
5. install pinned Dayu from the new project-local checkout with `--no-deps`;
6. compare old/new package snapshots and require exact equality except the local Dayu source path;
7. rerun Dayu doctor and FFDF runtime-isolation checks;
8. only then retire the old runtime.

The first resolver-drifted runtime build is not accepted as the migrated runtime.

---

## 17. P6–P11 Rule

从 P6 起：
- development/review/acceptance worktree/checkout path 必须位于 project root
- all phase helper/evidence paths must remain under project root
- no new FFDF-owned sibling directory under `D:\Codex`

该规则优先于历史阶段文档中的旧绝对路径。
