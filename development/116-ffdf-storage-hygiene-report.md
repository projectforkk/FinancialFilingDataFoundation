# FFDF Storage Hygiene / 存储空间整理与治理报告

## 1. 审计范围与结论

- 项目：FinancialFilingDataFoundation
- 根目录：D:/Codex/FinancialFilingDataFoundation
- 审计日期：2026-11-05
- 清理前 Git 基线：main @ 426121b4d360802f391e49a295e305e4ad26f6bd
- 结果：PASS（未知用途内容按 KEEP + REPORT 处理）
- 本次没有删除正式财报、raw-store PDF、Registry、P3-P9 artifacts、P8 live catalog、overlay/resolved view、活动 worktree、受保护 runtime、.venv 或 dependencies。
- 没有执行 full pytest、production/test 重建、reset、clean、rebase、merge main 或 force push。

清理遵循以下顺序：先做目录、Git、Registry、P8 catalog、raw-store、runtime 和 worktree 只读盘点；再对每个候选目标核对 tracked 状态、Registry/P8/P9 引用、worktree 注册状态和可恢复性；最后只删除明确可重建的测试残留，以及已经 clean、merged、非 active、非 locked 的历史 worktree。

## 2. 清理前后空间概览

清理前数字来自删除前盘点，按 GB（1024^3 bytes）或 MB（1024^2 bytes）四舍五入；清理后为删除完成后的独立复核值。

| 范围 | 清理前 | 清理后 | 释放量（约） | 处理 |
|---|---:|---:|---:|---|
| workspace | 约 1.931 GB / 84,313 files | 1.198 GB / 22,400 files | 约 0.733 GB | 仅删除明确测试残留 |
| workspace/ingest | 818.1 MB / 1,609 files | 818.07 MB / 1,609 files | 0 | 保留正式数据及解析产物 |
| workspace/scratch | 651.3 MB / 49,412 files | 1.07 MB / 229 files | 约 650.2 MB | 删除 42 个明确可重建目录；未知内容保留 |
| workspace/t | 约 100.9 MB | 不存在 | 约 100.9 MB | 删除 P8/P9 测试 staging |
| workspace/current | 87.7 MB / 10,700 files | 87.67 MB / 10,700 files | 0 | 保留当前正式工作集 |
| workspace/live | 42.2 MB / 41 files | 42.22 MB / 41 files | 0 | 保留 live 输入和验证数据 |
| runtimes | 约 1.296 GB / 38,465 files | 1.287 GB / 37,707 files | 约 9.2 MB | 只删除无引用的 P9-JR test runtime |
| worktrees | 约 1.144 GB / 95,008 files | 237.30 MB / 21,530 files | 约 0.912 GB | 删除 52 个安全历史 worktree；活动/脏/未合并保留 |
| .venv | 未作为候选 | 65.27 MB / 803 files | 0 | 受保护 |
| dependencies | 未作为候选 | 43.07 MB / 1,658 files | 0 | 受保护 |

## 3. DELETE PLAN 与实际删除

以下目标在删除前已完成 exact-path 复核。所有候选目标均没有 tracked file，也没有 Registry、P8 catalog、P9 production/evidence 或活动 worktree 引用；不确定对象没有进入删除集合。

| 目标 | 删除前规模 | tracked / Registry / P8-P9 / registered worktree | 决策与执行 |
|---|---:|---|---|
| workspace/scratch 下 42 个匹配目录：p11-b-probe、pytest-*、p11-c-pytest*、p10-*-preserved*、p10-n-failed*、p10-n-183ca5d-stopped*、p9-jr-invalid-full、tmp-p11c*、__pycache__、p10-invalid-path-probe | 650.24 MB | 无 tracked file / 无 Registry / 无 P8-P9 引用 / 非 worktree | DELETE；均为可重建测试输出、basetemp 或 probe 产物 |
| workspace/t | 约 100.9 MB | 无 tracked file / 无 Registry / 无 P8-P9 引用 / 非 worktree | DELETE；P8/P9 test staging |
| worktrees/t | 约 584 MB | 无 tracked file / 无 Registry / 无 P8-P9 引用 / 未注册为正式 Git worktree | DELETE；fixture/probe 测试工作区 |
| runtimes/p9-jr-tests | 约 9.2 MB | 无 runtime lock / 无当前脚本引用 / 无 Registry / 无 P8-P9 正式引用 | DELETE；历史 focused test JSONL/SQLite 输出 |
| 52 个历史 registered worktrees | 合计约 350.4 MB | 每一个均在删除前复核为 clean、HEAD 是 main ancestor、无 untracked、非 active、非 locked、非 prunable | DELETE；使用 git worktree remove --force；不删除 branch ref 或 commit object |

本次删除没有使用 git reset --hard 或 git clean。worktree 删除完成后执行 git worktree prune，元数据复核为 PASS。

### 3.1 已删除的 52 个历史 worktree

这些路径按原注册目录记录如下；它们的 Git 分支和 commit lineage 保留在仓库对象/refs 中。

- acceptance：p10-n-183ca5d、p10-n-4d1ab46、p6-07cb425、p7-8edb68a、p8-3152523、p8-fd8dccc、p9-3c5a632、p9-926c665
- archive/clean：p1-acceptance-3b382f4、p1-final-review、p1-review-20587f2、p1-review-f5c5cd7、p1-schema-fix、p2-acceptance-803fe3d、p2-review-881c80b、p3-acceptance-7b81c97、p3-review-3c3536d、p4-acceptance-647d617、p4-dev、p4-review-7e60bdd、p4-review-ea78b2f、p5-acceptance-44ddd73、p5-dev、p5-review-2c4bafd、p5-review-d73df92
- integration：p10-closeout-v2、p8-closeout
- review：p10-acceptance-package-114d38c、p10-c-b290f73、p10-d-a63ec33、p10-e-fd71ada、p10-f-13e5a09、p10-g-69644cf、p10-g-fb0dc90、p10-issue008-harness-9621f20、p10-issue009-harness-db06b7a、p10-l-ea763c9、p6-7031c38、p6-bb31515、p7-0b1ffce、p7-938f528、p8-537ebbd、p8-599db48、p8-d31a585、p8-e8ca4a9、p8-e9755b6、p8-lock-e8ca4a9、p9-5a4b46e8、p9-jr-65d29cb、p9-jr2-e010d61、p9-jr3-e782243、p9-main-e9b3062

## 4. 明确保留的内容

### 4.1 正式数据与 artifacts

- workspace/ingest：保留 CN/HK 正式下载、raw-store、Registry、P3-P7 artifacts。
- workspace/ingest/raw-store/sha256：82 个原始 PDF，完整审计见第 7 节；本次删除数为 0。
- workspace/ingest/registry.sqlite：保留；只读复核通过。
- workspace/mcp/p8-live-catalog.json：保留；只读复核通过。
- workspace/current、workspace/live：保留，分别为当前正式工作集和 live 输入/验证目录。
- workspace/scratch 中剩余的未知/治理输入/设计 patch/issue 目录和根级脚本：KEEP + REPORT，不因名称相似而删除。
- 00document 与 01prompt 下的 5 个已有 untracked 文件：未读取修改、未删除、未加入本次 commit。

### 4.2 Runtimes

| runtime | 清理后规模 | 结论 |
|---|---:|---|
| runtimes/ffdf-dayu-2115c86 | 1,219.56 MB / 35,545 files | KEEP；Dayu acquisition runtime，存在 lock file 和当前文档/CLI 引用 |
| runtimes/ffdf-mcp-2.3.0 | 97.94 MB / 2,162 files | KEEP；FFDF MCP runtime，存在 lock file、部署文档和当前路径引用 |
| runtimes/p9-jr-tests | 不存在 | DELETE；仅历史测试输出，无 lock、无当前引用 |

### 4.3 Git worktrees

清理后仍注册 52 个 worktree（包括根 main worktree）；没有 locked 或 prunable entry。

- worktrees/active：10 个全部保留，包括 P10、P11、P6、P7、P8、P9 活动工作区。
- worktrees/archive：6 个保留；含脏或未合并的 P1 历史审查工作区。
- worktrees/integration：2 个保留；p10-closeout 有未提交修改，p9-closeout 未合并。
- worktrees/review：33 个 P11 review/design 工作区保留；P11 属于历史/当前治理范围外，且未合并。
- 当前根 main worktree 的未提交内容没有被清理或覆盖；活动 p9 worktree 也没有被清理。

## 5. Raw-store 审计摘要

- raw-store 根：workspace/ingest/raw-store/sha256
- 原始 PDF：82 个
- 总大小：239,124,645 bytes = 228.047 MB
- Registry documents：82
- Registry filing_bindings：82
- Registry document_sources：82
- Registry document_locations：82
- parsed_data：68
- Registry binding 覆盖：82/82
- orphan candidates：0
- P8 catalog：schema p8-mcp-catalog-v1，共 70 个 document
- raw-store 与 P8 catalog 重叠：68/82
- catalog live-only（不是 raw-store orphan）：5299f4940e2ce4e91084b73dc457d558b9d335fa76fbfee6227e4254eb7f4a30、70f529984a87ef7f46d9e1db26bb9ef27eef9c01d29c59aabf69e557b479a6a0
- 已解析的 68 个文件：PASS 4、REVIEW_REQUIRED 64；blocking_issue_count 均为 0
- 未解析的 14 个文件：均属于 CN:600048；没有因为未解析而删除 raw PDF
- market：CN 82
- provider：cninfo 82
- Registry/source report_date：当前均为空；本报告不推断 report_date
- filing type：ANNUAL_REPORT 19、INTERIM_REPORT 21、QUARTERLY_REPORT 42

### 5.1 Registry company 聚合

| Registry company_id | source title 可确认的名称 | PDF 数 | 年份范围 | 总大小 |
|---|---|---:|---|---:|
| CN:002371 | 未在当前 source metadata 中可靠确认 | 15 | 2023-2026 | 20.952 MB |
| CN:300308 | 未在当前 source metadata 中可靠确认 | 15 | 2023-2026 | 39.084 MB |
| CN:600048 | 保利发展控股集团股份有限公司 | 14 | 2021-2026 | 71.751 MB |
| CN:605117 | 宁波德业科技股份有限公司 | 23 | 2021-2026 | 33.263 MB |
| CN:688012 | 未在当前 source metadata 中可靠确认 | 15 | 2023-2026 | 62.997 MB |

### 5.2 年份与 raw period 聚合

| fiscal_year | FY | H1 | Q1 | Q3 |
|---:|---:|---:|---:|---:|
| 2021 | 2 | 1 | 1 | 1 |
| 2022 | 2 | 1 | 1 | 1 |
| 2023 | 5 | 4 | 4 | 4 |
| 2024 | 5 | 5 | 5 | 5 |
| 2025 | 5 | 5 | 5 | 5 |
| 2026 | 0 | 5 | 5 | 5 |

## 6. 逻辑重复与 orphan 决策

- orphan candidate：0。82/82 raw PDF 都存在 Registry binding、source metadata 和 document location；没有文件进入自动删除候选。
- multi-SHA logical filing group：0。按 market + Registry company_id + fiscal_year + raw_fiscal_period 聚合时，没有出现同一逻辑 filing 对应多个 SHA-256 的组。
- 因此没有执行基于“看起来重复”、文件名、source title 或报告日期推断的删除。
- 两个 catalog live-only SHA 是 P9-I live validation 产物的 catalog 项，不是 raw-store 中可删除的 orphan；不触碰。

## 7. Raw-store 82 文件逐项清单

字段说明：Registry/P8 为当前只读复核状态；runs/latest validation/blocking 为 parsed_data 运行次数、最新 validation_status 和最新 blocking_issue_count；report_date 的 — 表示 Registry/source 当前为空，不是推断值。

| # | SHA-256 | MB | market | company_id / source name | year | period | filing_type | provider / source_id | filing_date | report_date | raw path | Registry | P8 | runs / latest validation / blocking |
|---:|---|---:|---|---|---:|---|---|---|---|---|---|:---:|:---:|---|
| 1 | 0290f380253dde79613d43a1c6203674ae36cb89f849f063668ccde9a8789b5e | 5.866 | CN | CN:300308 | 2025 | FY | ANNUAL_REPORT | cninfo / 1225056459 | 2026-03-30 | — | workspace/ingest/raw-store/sha256/02/0290f380253dde79613d43a1c6203674ae36cb89f849f063668ccde9a8789b5e.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 2 | 0abde5c47d25b9d20643ab30162b00472d00b93ff430529bc9cee05cded11df9 | 0.428 | CN | CN:688012 | 2023 | Q3 | QUARTERLY_REPORT | cninfo / 1218169256 | 2023-10-26 | — | workspace/ingest/raw-store/sha256/0a/0abde5c47d25b9d20643ab30162b00472d00b93ff430529bc9cee05cded11df9.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 3 | 1617071cca8de69d77372327af649e76bc23d55a27c4adf725a5dc3d7f7aa0b4 | 0.188 | CN | CN:605117 / 宁波德业科技股份有限公司 | 2025 | Q3 | QUARTERLY_REPORT | cninfo / 1224768213 | 2025-10-29 | — | workspace/ingest/raw-store/sha256/16/1617071cca8de69d77372327af649e76bc23d55a27c4adf725a5dc3d7f7aa0b4.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 4 | 173a88a01df4b6c0807b213214c550d6ac5500923a5af4cd99eed69607eece39 | 0.450 | CN | CN:688012 | 2023 | Q1 | QUARTERLY_REPORT | cninfo / 1216684138 | 2023-04-28 | — | workspace/ingest/raw-store/sha256/17/173a88a01df4b6c0807b213214c550d6ac5500923a5af4cd99eed69607eece39.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 5 | 17fe5dc32e6e4a684b2a771eded096b492975720214b36ba7f188be72c5449b4 | 3.516 | CN | CN:600048 / 保利发展控股集团股份有限公司 | 2022 | FY | ANNUAL_REPORT | cninfo / 1216282876 | 2023-03-30 | — | workspace/ingest/raw-store/sha256/17/17fe5dc32e6e4a684b2a771eded096b492975720214b36ba7f188be72c5449b4.pdf | yes | no | 0 / — / — |
| 6 | 182e2062fed950cd32310099cdf47f392c791440ce251f5e3bab7137dbc932fe | 3.004 | CN | CN:688012 | 2026 | H1 | INTERIM_REPORT | cninfo / 1225482884 | 2026-08-19 | — | workspace/ingest/raw-store/sha256/18/182e2062fed950cd32310099cdf47f392c791440ce251f5e3bab7137dbc932fe.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 7 | 1aae1eb7241f53d1f4ab3655738159164190222cd5d6dfe5c61d297f59e6550a | 0.635 | CN | CN:300308 | 2024 | Q1 | QUARTERLY_REPORT | cninfo / 1219703023 | 2024-04-21 | — | workspace/ingest/raw-store/sha256/1a/1aae1eb7241f53d1f4ab3655738159164190222cd5d6dfe5c61d297f59e6550a.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 8 | 1b392ffeba7ef5ea84c05cfe4f64f91ef3aa9a90662b3764bbeaa743d4339d5c | 0.581 | CN | CN:300308 | 2023 | Q1 | QUARTERLY_REPORT | cninfo / 1216523567 | 2023-04-23 | — | workspace/ingest/raw-store/sha256/1b/1b392ffeba7ef5ea84c05cfe4f64f91ef3aa9a90662b3764bbeaa743d4339d5c.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 9 | 1bd5c259056e43b05792d715f52825e158dc3f811fc301175f85a45719a3718a | 4.118 | CN | CN:605117 / 宁波德业科技股份有限公司 | 2023 | FY | ANNUAL_REPORT | cninfo / 1219796690 | 2024-04-24 | — | workspace/ingest/raw-store/sha256/1b/1bd5c259056e43b05792d715f52825e158dc3f811fc301175f85a45719a3718a.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 10 | 1c13639ab218395ef3c81bfbcddb64ba48262d2afcc8ac9ed1588a9dbd4a513f | 6.644 | CN | CN:300308 | 2024 | FY | ANNUAL_REPORT | cninfo / 1223155483 | 2025-04-20 | — | workspace/ingest/raw-store/sha256/1c/1c13639ab218395ef3c81bfbcddb64ba48262d2afcc8ac9ed1588a9dbd4a513f.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 11 | 1e4a675545bc02df75ad3fe6b86571436fabf84297324fa3d20e3682c75b6865 | 4.038 | CN | CN:002371 | 2024 | H1 | INTERIM_REPORT | cninfo / 1221004535 | 2024-08-27 | — | workspace/ingest/raw-store/sha256/1e/1e4a675545bc02df75ad3fe6b86571436fabf84297324fa3d20e3682c75b6865.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 12 | 2276f88c03aca66b37e4d7a03c88df1dfa7eb6bdf1487bf7d3a76d21b84948a9 | 6.392 | CN | CN:300308 | 2023 | FY | ANNUAL_REPORT | cninfo / 1219703026 | 2024-04-21 | — | workspace/ingest/raw-store/sha256/22/2276f88c03aca66b37e4d7a03c88df1dfa7eb6bdf1487bf7d3a76d21b84948a9.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 13 | 261737c48b72a7450333544d4c65718ecbc8f60c05ac7225557bfeb080ee4e0d | 0.754 | CN | CN:300308 | 2025 | Q1 | QUARTERLY_REPORT | cninfo / 1223155474 | 2025-04-20 | — | workspace/ingest/raw-store/sha256/26/261737c48b72a7450333544d4c65718ecbc8f60c05ac7225557bfeb080ee4e0d.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 14 | 29609018fb57d916a005980c357b184d95e889b6c35b9d94c0494f0338206633 | 9.003 | CN | CN:688012 | 2023 | H1 | INTERIM_REPORT | cninfo / 1217637243 | 2023-08-24 | — | workspace/ingest/raw-store/sha256/29/29609018fb57d916a005980c357b184d95e889b6c35b9d94c0494f0338206633.pdf | yes | yes | 1 / PASS / 0 |
| 15 | 3273711fbb79fa6ee5e9a3b2f0eea7d5a1dfa0d305721c61e5af251f9addf399 | 13.624 | CN | CN:688012 | 2024 | FY | ANNUAL_REPORT | cninfo / 1223127191 | 2025-04-17 | — | workspace/ingest/raw-store/sha256/32/3273711fbb79fa6ee5e9a3b2f0eea7d5a1dfa0d305721c61e5af251f9addf399.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 16 | 32f43bf0ef3f2452ca2a9a1f1b5cfa81757f01f146fce825405b7000f5c5ff36 | 0.701 | CN | CN:300308 | 2023 | Q3 | QUARTERLY_REPORT | cninfo / 1218110303 | 2023-10-22 | — | workspace/ingest/raw-store/sha256/32/32f43bf0ef3f2452ca2a9a1f1b5cfa81757f01f146fce825405b7000f5c5ff36.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 17 | 368d692a28d64ed68926140402ed28da05cd2c30d291d6f8452f8f29719e093b | 0.186 | CN | CN:605117 / 宁波德业科技股份有限公司 | 2025 | Q1 | QUARTERLY_REPORT | cninfo / 1223427128 | 2025-04-29 | — | workspace/ingest/raw-store/sha256/36/368d692a28d64ed68926140402ed28da05cd2c30d291d6f8452f8f29719e093b.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 18 | 39c519ec7ff2cc15b06d458f659cd0e807d84b2021c25f4e8b64df0648a9ce50 | 0.174 | CN | CN:600048 / 保利发展控股集团股份有限公司 | 2025 | Q1 | QUARTERLY_REPORT | cninfo / 1223382880 | 2025-04-28 | — | workspace/ingest/raw-store/sha256/39/39c519ec7ff2cc15b06d458f659cd0e807d84b2021c25f4e8b64df0648a9ce50.pdf | yes | no | 0 / — / — |
| 19 | 3a1bb4ea0893d4232c2c7f8f2ad23fe99d3307f6c17e27ed145c96df026a0d6b | 0.426 | CN | CN:605117 / 宁波德业科技股份有限公司 | 2021 | Q3 | QUARTERLY_REPORT | cninfo / 1211418358 | 2021-10-28 | — | workspace/ingest/raw-store/sha256/3a/3a1bb4ea0893d4232c2c7f8f2ad23fe99d3307f6c17e27ed145c96df026a0d6b.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 20 | 40b5547c5c92b662627d1b93564a6aba71a1f8ed0c08fd804c50a360ffad56fe | 0.479 | CN | CN:688012 | 2024 | Q1 | QUARTERLY_REPORT | cninfo / 1219837692 | 2024-04-25 | — | workspace/ingest/raw-store/sha256/40/40b5547c5c92b662627d1b93564a6aba71a1f8ed0c08fd804c50a360ffad56fe.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 21 | 411d219085c216161087705c594769df6cd4e7e9faf32ed4f92b8c0bff2ff3cf | 0.172 | CN | CN:600048 / 保利发展控股集团股份有限公司 | 2026 | Q1 | QUARTERLY_REPORT | cninfo / 1225214016 | 2026-04-27 | — | workspace/ingest/raw-store/sha256/41/411d219085c216161087705c594769df6cd4e7e9faf32ed4f92b8c0bff2ff3cf.pdf | yes | no | 0 / — / — |
| 22 | 49b6ed4ca0345cac83e34eeb886f4567c6ddd73233a3cde870885b3d3f6785f3 | 0.209 | CN | CN:600048 / 保利发展控股集团股份有限公司 | 2025 | Q3 | QUARTERLY_REPORT | cninfo / 1224724077 | 2025-10-21 | — | workspace/ingest/raw-store/sha256/49/49b6ed4ca0345cac83e34eeb886f4567c6ddd73233a3cde870885b3d3f6785f3.pdf | yes | no | 0 / — / — |
| 23 | 59f0076b1b450a4a5fe3f2fdcaaa875fee20c8b80fa1701568f592a95e5263aa | 5.052 | CN | CN:600048 / 保利发展控股集团股份有限公司 | 2024 | FY | ANNUAL_REPORT | cninfo / 1223382905 | 2025-04-28 | — | workspace/ingest/raw-store/sha256/59/59f0076b1b450a4a5fe3f2fdcaaa875fee20c8b80fa1701568f592a95e5263aa.pdf | yes | no | 0 / — / — |
| 24 | 5de4b69d1fdabce4212a8821f794e815f586f26fbdd2a5260b188cd97d64f9c7 | 3.234 | CN | CN:002371 | 2023 | H1 | INTERIM_REPORT | cninfo / 1217693132 | 2023-08-29 | — | workspace/ingest/raw-store/sha256/5d/5de4b69d1fdabce4212a8821f794e815f586f26fbdd2a5260b188cd97d64f9c7.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 25 | 5e37220662c1fea7c9286a9410dbcef20ce83f70329ba3b44f2bf733459aa1af | 0.757 | CN | CN:300308 | 2026 | Q1 | QUARTERLY_REPORT | cninfo / 1225111941 | 2026-04-16 | — | workspace/ingest/raw-store/sha256/5e/5e37220662c1fea7c9286a9410dbcef20ce83f70329ba3b44f2bf733459aa1af.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 26 | 6b7e95f17ca0a52a4d4fb599114509e66bae35e528e74bac2ee11d3134cb3e84 | 0.421 | CN | CN:605117 / 宁波德业科技股份有限公司 | 2022 | Q3 | QUARTERLY_REPORT | cninfo / 1214959547 | 2022-10-28 | — | workspace/ingest/raw-store/sha256/6b/6b7e95f17ca0a52a4d4fb599114509e66bae35e528e74bac2ee11d3134cb3e84.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 27 | 70168364fd518323effa2d11ff337a172783e3597ed6f896353ca62ea3f75cfe | 1.908 | CN | CN:002371 | 2024 | FY | ANNUAL_REPORT | cninfo / 1223309278 | 2025-04-25 | — | workspace/ingest/raw-store/sha256/70/70168364fd518323effa2d11ff337a172783e3597ed6f896353ca62ea3f75cfe.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 28 | 73d56e64225daa03befa7a1d9db886cd8312bdd201469831a80b495408a83acb | 1.616 | CN | CN:605117 / 宁波德业科技股份有限公司 | 2024 | FY | ANNUAL_REPORT | cninfo / 1223427135 | 2025-04-29 | — | workspace/ingest/raw-store/sha256/73/73d56e64225daa03befa7a1d9db886cd8312bdd201469831a80b495408a83acb.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 29 | 7654715a5317a71401953432eaa2fb0886fc970449d5e2567c38a6ae8d4bcce0 | 3.568 | CN | CN:605117 / 宁波德业科技股份有限公司 | 2022 | FY | ANNUAL_REPORT | cninfo / 1216442355 | 2023-04-17 | — | workspace/ingest/raw-store/sha256/76/7654715a5317a71401953432eaa2fb0886fc970449d5e2567c38a6ae8d4bcce0.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 30 | 7a133d74da02f470eea4bd237b1f9285b3656368fee247dc3bdfacf55ee495c8 | 0.852 | CN | CN:300308 | 2026 | Q3 | QUARTERLY_REPORT | cninfo / 1225643953 | 2026-10-29 | — | workspace/ingest/raw-store/sha256/7a/7a133d74da02f470eea4bd237b1f9285b3656368fee247dc3bdfacf55ee495c8.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 31 | 7b12b2c3f6c43bc1ca8dc8bd779612128d9a2791441413ec349a7409954b0276 | 0.505 | CN | CN:002371 | 2023 | Q3 | QUARTERLY_REPORT | cninfo / 1218199156 | 2023-10-30 | — | workspace/ingest/raw-store/sha256/7b/7b12b2c3f6c43bc1ca8dc8bd779612128d9a2791441413ec349a7409954b0276.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 32 | 81115ea06c53d24cfa9a6c081be36e9a7bdbe456192805c08030e815921957b6 | 0.694 | CN | CN:300308 | 2024 | Q3 | QUARTERLY_REPORT | cninfo / 1221474464 | 2024-10-22 | — | workspace/ingest/raw-store/sha256/81/81115ea06c53d24cfa9a6c081be36e9a7bdbe456192805c08030e815921957b6.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 33 | 8275075b87564df7662aa691aaa3a0254379dca416ed4e13a787c894542f6c24 | 0.628 | CN | CN:688012 | 2024 | Q3 | QUARTERLY_REPORT | cninfo / 1221555993 | 2024-10-29 | — | workspace/ingest/raw-store/sha256/82/8275075b87564df7662aa691aaa3a0254379dca416ed4e13a787c894542f6c24.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 34 | 830b11815f1d493465a8913335c5937b06d6221797a59e9256db00a4746c59c8 | 6.475 | CN | CN:600048 / 保利发展控股集团股份有限公司 | 2025 | FY | ANNUAL_REPORT | cninfo / 1225123569 | 2026-04-17 | — | workspace/ingest/raw-store/sha256/83/830b11815f1d493465a8913335c5937b06d6221797a59e9256db00a4746c59c8.pdf | yes | no | 0 / — / — |
| 35 | 8981d8298a8aaf202847a3b326175987b1491e98b41a6f96de52a4162ec16ffd | 2.649 | CN | CN:605117 / 宁波德业科技股份有限公司 | 2023 | H1 | INTERIM_REPORT | cninfo / 1217707634 | 2023-08-30 | — | workspace/ingest/raw-store/sha256/89/8981d8298a8aaf202847a3b326175987b1491e98b41a6f96de52a4162ec16ffd.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 36 | 8d8efde894019e65919f8b7e1b389d5945d0b4e79e6ffad6f43ca8727c43be1f | 0.541 | CN | CN:002371 | 2024 | Q3 | QUARTERLY_REPORT | cninfo / 1221555085 | 2024-10-29 | — | workspace/ingest/raw-store/sha256/8d/8d8efde894019e65919f8b7e1b389d5945d0b4e79e6ffad6f43ca8727c43be1f.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 37 | 91ae4978b694ef8361195e50a414e00d071c835d1d6e9f60bccc75dc22175cdd | 6.067 | CN | CN:688012 | 2025 | H1 | INTERIM_REPORT | cninfo / 1224606011 | 2025-08-28 | — | workspace/ingest/raw-store/sha256/91/91ae4978b694ef8361195e50a414e00d071c835d1d6e9f60bccc75dc22175cdd.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 38 | 93d5d7ae724ae6b3d429aa258059bacaa304a6ec7f1dc5ed69bac102c7cdde1d | 1.147 | CN | CN:605117 / 宁波德业科技股份有限公司 | 2026 | H1 | INTERIM_REPORT | cninfo / 1225509880 | 2026-08-26 | — | workspace/ingest/raw-store/sha256/93/93d5d7ae724ae6b3d429aa258059bacaa304a6ec7f1dc5ed69bac102c7cdde1d.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 39 | 9eb470ce8311c111d4311f9888807168f7e2e9b14143e7df184bc5ea02899347 | 7.198 | CN | CN:688012 | 2024 | H1 | INTERIM_REPORT | cninfo / 1220950845 | 2024-08-22 | — | workspace/ingest/raw-store/sha256/9e/9eb470ce8311c111d4311f9888807168f7e2e9b14143e7df184bc5ea02899347.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 40 | a0f8d84ab724f7c62b690d6504215602a623fc185c53c9e1079cd40653c600b9 | 0.221 | CN | CN:002371 | 2026 | Q3 | QUARTERLY_REPORT | cninfo / 1225641389 | 2026-10-29 | — | workspace/ingest/raw-store/sha256/a0/a0f8d84ab724f7c62b690d6504215602a623fc185c53c9e1079cd40653c600b9.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 41 | a182c1719a46ce08771a70ffb31506375369fa246800115ccf96cbfa9c18b98d | 0.367 | CN | CN:002371 | 2025 | Q1 | QUARTERLY_REPORT | cninfo / 1223309242 | 2025-04-25 | — | workspace/ingest/raw-store/sha256/a1/a182c1719a46ce08771a70ffb31506375369fa246800115ccf96cbfa9c18b98d.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 42 | a23f3295b463d1cea81a9793821c6eba27f15be47c55a917e8ff8220dd978eda | 0.461 | CN | CN:605117 / 宁波德业科技股份有限公司 | 2024 | Q1 | QUARTERLY_REPORT | cninfo / 1219796686 | 2024-04-24 | — | workspace/ingest/raw-store/sha256/a2/a23f3295b463d1cea81a9793821c6eba27f15be47c55a917e8ff8220dd978eda.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 43 | a2867db790631d690b5830490682417bcb8ebee100102ac731e624a70599d32e | 0.444 | CN | CN:605117 / 宁波德业科技股份有限公司 | 2023 | Q3 | QUARTERLY_REPORT | cninfo / 1218187481 | 2023-10-27 | — | workspace/ingest/raw-store/sha256/a2/a2867db790631d690b5830490682417bcb8ebee100102ac731e624a70599d32e.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 44 | a77e961613d745816657c3db3787748a1832b38df499c6eee360b42ca9133784 | 0.533 | CN | CN:002371 | 2023 | Q1 | QUARTERLY_REPORT | cninfo / 1216690527 | 2023-04-28 | — | workspace/ingest/raw-store/sha256/a7/a77e961613d745816657c3db3787748a1832b38df499c6eee360b42ca9133784.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 45 | a9ff6683ed5d4fea2b23e0b046d7a9f9ca725d59c02661e308fb3cb5f2ffb04a | 0.437 | CN | CN:605117 / 宁波德业科技股份有限公司 | 2022 | Q1 | QUARTERLY_REPORT | cninfo / 1213195458 | 2022-04-28 | — | workspace/ingest/raw-store/sha256/a9/a9ff6683ed5d4fea2b23e0b046d7a9f9ca725d59c02661e308fb3cb5f2ffb04a.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 46 | ab7bb0076b2a3fb42ebca7b54d1b167a790221e394613ce544e275b249eb3268 | 0.207 | CN | CN:688012 | 2026 | Q1 | QUARTERLY_REPORT | cninfo / 1225215453 | 2026-04-27 | — | workspace/ingest/raw-store/sha256/ab/ab7bb0076b2a3fb42ebca7b54d1b167a790221e394613ce544e275b249eb3268.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 47 | af09ac4951073e650f8d4f428a7eaea6977e18a162cfb042000408a3fc49d50f | 1.773 | CN | CN:002371 | 2025 | FY | ANNUAL_REPORT | cninfo / 1225122918 | 2026-04-17 | — | workspace/ingest/raw-store/sha256/af/af09ac4951073e650f8d4f428a7eaea6977e18a162cfb042000408a3fc49d50f.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 48 | b11508ae70b92134daacf84b5a2e2cacb4331c354b1d9c52004d8362166d9a3b | 0.200 | CN | CN:688012 | 2025 | Q1 | QUARTERLY_REPORT | cninfo / 1223281418 | 2025-04-24 | — | workspace/ingest/raw-store/sha256/b1/b11508ae70b92134daacf84b5a2e2cacb4331c354b1d9c52004d8362166d9a3b.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 49 | b19afb6a99fce2f37e22e1e4fecb0fd85465ac8af4dfd136a55af60f72dd58da | 0.463 | CN | CN:605117 / 宁波德业科技股份有限公司 | 2024 | Q3 | QUARTERLY_REPORT | cninfo / 1221559696 | 2024-10-29 | — | workspace/ingest/raw-store/sha256/b1/b19afb6a99fce2f37e22e1e4fecb0fd85465ac8af4dfd136a55af60f72dd58da.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 50 | b206dde596f60293303b88ee12dabb4531a49a7e8add6d1d0d8ad277e639245f | 0.818 | CN | CN:300308 | 2025 | Q3 | QUARTERLY_REPORT | cninfo / 1224773075 | 2025-10-30 | — | workspace/ingest/raw-store/sha256/b2/b206dde596f60293303b88ee12dabb4531a49a7e8add6d1d0d8ad277e639245f.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 51 | b4bfb2f7b05657593f954839576307391ccf1bfc0292178044e1575926fe4ddc | 0.207 | CN | CN:688012 | 2025 | Q3 | QUARTERLY_REPORT | cninfo / 1224763575 | 2025-10-29 | — | workspace/ingest/raw-store/sha256/b4/b4bfb2f7b05657593f954839576307391ccf1bfc0292178044e1575926fe4ddc.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 52 | b56805b049af56b7c786a9c457d4ce585cfe91d83c00a213e5c188cc918e0118 | 2.669 | CN | CN:605117 / 宁波德业科技股份有限公司 | 2021 | H1 | INTERIM_REPORT | cninfo / 1210875566 | 2021-08-26 | — | workspace/ingest/raw-store/sha256/b5/b56805b049af56b7c786a9c457d4ce585cfe91d83c00a213e5c188cc918e0118.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 53 | b66c8433df124a3ea53126a6bc186c21946881e37af377f5880a091f559e2f79 | 4.804 | CN | CN:002371 | 2023 | FY | ANNUAL_REPORT | cninfo / 1219908921 | 2024-04-29 | — | workspace/ingest/raw-store/sha256/b6/b66c8433df124a3ea53126a6bc186c21946881e37af377f5880a091f559e2f79.pdf | yes | yes | 1 / PASS / 0 |
| 54 | bda9be18e45ee027492a061e1600e6e4fc072c8691251d04246aec53baf81a0d | 5.147 | CN | CN:600048 / 保利发展控股集团股份有限公司 | 2021 | FY | ANNUAL_REPORT | cninfo / 1212964021 | 2022-04-18 | — | workspace/ingest/raw-store/sha256/bd/bda9be18e45ee027492a061e1600e6e4fc072c8691251d04246aec53baf81a0d.pdf | yes | no | 0 / — / — |
| 55 | be61b02069c49a983b3555d79723a2bf20353595a8f3f5f28eea84b4d34534f6 | 4.373 | CN | CN:300308 | 2023 | H1 | INTERIM_REPORT | cninfo / 1217655323 | 2023-08-27 | — | workspace/ingest/raw-store/sha256/be/be61b02069c49a983b3555d79723a2bf20353595a8f3f5f28eea84b4d34534f6.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 56 | c452b2c873207f753aef09a2e17b95599733031110fe131ff56c348e2e86f624 | 37.219 | CN | CN:600048 / 保利发展控股集团股份有限公司 | 2026 | H1 | INTERIM_REPORT | cninfo / 1225515370 | 2026-08-26 | — | workspace/ingest/raw-store/sha256/c4/c452b2c873207f753aef09a2e17b95599733031110fe131ff56c348e2e86f624.pdf | yes | no | 0 / — / — |
| 57 | c586a006edbf5455695236dea16513c47e6f1d5b4a96caee168f6fd14637edf8 | 0.198 | CN | CN:002371 | 2026 | Q1 | QUARTERLY_REPORT | cninfo / 1225259650 | 2026-04-29 | — | workspace/ingest/raw-store/sha256/c5/c586a006edbf5455695236dea16513c47e6f1d5b4a96caee168f6fd14637edf8.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 58 | c5df515c5f8d1dfdc77d95333f73fdb0cd1bc7caffc497036de5363b98d6a52a | 1.143 | CN | CN:605117 / 宁波德业科技股份有限公司 | 2025 | H1 | INTERIM_REPORT | cninfo / 1224571841 | 2025-08-25 | — | workspace/ingest/raw-store/sha256/c5/c5df515c5f8d1dfdc77d95333f73fdb0cd1bc7caffc497036de5363b98d6a52a.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 59 | c6895b0e353e3c55178856ce93e5ec056ed105773207a77875f87f83f29ae7f5 | 0.194 | CN | CN:605117 / 宁波德业科技股份有限公司 | 2026 | Q1 | QUARTERLY_REPORT | cninfo / 1225254498 | 2026-04-29 | — | workspace/ingest/raw-store/sha256/c6/c6895b0e353e3c55178856ce93e5ec056ed105773207a77875f87f83f29ae7f5.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 60 | c748eafa16eef8bb5a3502d32f639d4ca5deacb6a16201cb46e6476bd203262f | 5.175 | CN | CN:300308 | 2024 | H1 | INTERIM_REPORT | cninfo / 1220965278 | 2024-08-25 | — | workspace/ingest/raw-store/sha256/c7/c748eafa16eef8bb5a3502d32f639d4ca5deacb6a16201cb46e6476bd203262f.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 61 | c80a3432a0cf77741a057be9cf108a5985a23565840ab7362c8453e06feb6832 | 0.216 | CN | CN:600048 / 保利发展控股集团股份有限公司 | 2026 | Q3 | QUARTERLY_REPORT | cninfo / 1225638174 | 2026-10-28 | — | workspace/ingest/raw-store/sha256/c8/c80a3432a0cf77741a057be9cf108a5985a23565840ab7362c8453e06feb6832.pdf | yes | no | 0 / — / — |
| 62 | cb1fb93301dec2bf6bcb0e02ab1d92883908ced8d5481a7785a7a493d68041e7 | 0.195 | CN | CN:605117 / 宁波德业科技股份有限公司 | 2026 | Q3 | QUARTERLY_REPORT | cninfo / 1225642304 | 2026-10-29 | — | workspace/ingest/raw-store/sha256/cb/cb1fb93301dec2bf6bcb0e02ab1d92883908ced8d5481a7785a7a493d68041e7.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 63 | d00cbd52839d343257a4b9c1fbf297fe14aa198d64226541c48e234de50aa070 | 0.589 | CN | CN:605117 / 宁波德业科技股份有限公司 | 2021 | Q1 | QUARTERLY_REPORT | cninfo / 1209877295 | 2021-04-29 | — | workspace/ingest/raw-store/sha256/d0/d00cbd52839d343257a4b9c1fbf297fe14aa198d64226541c48e234de50aa070.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 64 | d01725adb30800574e074e146548810c04861328b85070a68a07aebc1ca3b648 | 0.580 | CN | CN:600048 / 保利发展控股集团股份有限公司 | 2024 | Q1 | QUARTERLY_REPORT | cninfo / 1219910220 | 2024-04-29 | — | workspace/ingest/raw-store/sha256/d0/d01725adb30800574e074e146548810c04861328b85070a68a07aebc1ca3b648.pdf | yes | no | 0 / — / — |
| 65 | d106465e50d2a96c7d93a486f183ce8d91f50a3da42e168abc2633f6acbc726f | 4.486 | CN | CN:600048 / 保利发展控股集团股份有限公司 | 2023 | FY | ANNUAL_REPORT | cninfo / 1219740785 | 2024-04-22 | — | workspace/ingest/raw-store/sha256/d1/d106465e50d2a96c7d93a486f183ce8d91f50a3da42e168abc2633f6acbc726f.pdf | yes | no | 0 / — / — |
| 66 | d1126db582cc8521907d9c6b5cca767c94606e8d15b19a0672235550b9cc88e2 | 1.037 | CN | CN:002371 | 2026 | H1 | INTERIM_REPORT | cninfo / 1225501903 | 2026-08-25 | — | workspace/ingest/raw-store/sha256/d1/d1126db582cc8521907d9c6b5cca767c94606e8d15b19a0672235550b9cc88e2.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 67 | d40513c66998f2ccb3faadb8b99818aaf1f8bfeedc2b7e7a961e111541379d1e | 0.203 | CN | CN:688012 | 2026 | Q3 | QUARTERLY_REPORT | cninfo / 1225646685 | 2026-10-30 | — | workspace/ingest/raw-store/sha256/d4/d40513c66998f2ccb3faadb8b99818aaf1f8bfeedc2b7e7a961e111541379d1e.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 68 | d405552a7ce24fa775ad0cef33e9398acadd31ef08e065e6d27003560356ad7e | 0.604 | CN | CN:002371 | 2024 | Q1 | QUARTERLY_REPORT | cninfo / 1219908881 | 2024-04-29 | — | workspace/ingest/raw-store/sha256/d4/d405552a7ce24fa775ad0cef33e9398acadd31ef08e065e6d27003560356ad7e.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 69 | d64c410832f22f5127277bad6dc357c664aede523561af99150c494857fd3aa5 | 8.741 | CN | CN:688012 | 2025 | FY | ANNUAL_REPORT | cninfo / 1225062431 | 2026-03-30 | — | workspace/ingest/raw-store/sha256/d6/d64c410832f22f5127277bad6dc357c664aede523561af99150c494857fd3aa5.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 70 | d8ea2cb4b252d0e30e034f699e61985e607e6bbbd16d10760bdf5e7d3943ef05 | 4.088 | CN | CN:600048 / 保利发展控股集团股份有限公司 | 2025 | H1 | INTERIM_REPORT | cninfo / 1224571945 | 2025-08-25 | — | workspace/ingest/raw-store/sha256/d8/d8ea2cb4b252d0e30e034f699e61985e607e6bbbd16d10760bdf5e7d3943ef05.pdf | yes | no | 0 / — / — |
| 71 | db5239be68e8fa825ad49b5a8efdb45cc7b32eaf34512f8a6c818a093f402925 | 12.558 | CN | CN:688012 | 2023 | FY | ANNUAL_REPORT | cninfo / 1219329946 | 2024-03-18 | — | workspace/ingest/raw-store/sha256/db/db5239be68e8fa825ad49b5a8efdb45cc7b32eaf34512f8a6c818a093f402925.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 72 | de9b2d950ca5b63aab35f28fdb6ce78e7c4214b02973a269c553e0f612774f56 | 2.373 | CN | CN:605117 / 宁波德业科技股份有限公司 | 2022 | H1 | INTERIM_REPORT | cninfo / 1214316268 | 2022-08-17 | — | workspace/ingest/raw-store/sha256/de/de9b2d950ca5b63aab35f28fdb6ce78e7c4214b02973a269c553e0f612774f56.pdf | yes | yes | 1 / PASS / 0 |
| 73 | e0ecd7c365c65e90b1fa4b4616ba3f4649449d64451e0ba0b1b78ba9ce3170bf | 2.847 | CN | CN:300308 | 2026 | H1 | INTERIM_REPORT | cninfo / 1225491753 | 2026-08-21 | — | workspace/ingest/raw-store/sha256/e0/e0ecd7c365c65e90b1fa4b4616ba3f4649449d64451e0ba0b1b78ba9ce3170bf.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 74 | e494ef5bc14ea12b6942bab2b165212c81fbeffefec58eab0b3ee2f04d10af39 | 4.615 | CN | CN:605117 / 宁波德业科技股份有限公司 | 2021 | FY | ANNUAL_REPORT | cninfo / 1212999292 | 2022-04-20 | — | workspace/ingest/raw-store/sha256/e4/e494ef5bc14ea12b6942bab2b165212c81fbeffefec58eab0b3ee2f04d10af39.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 75 | e4a48d45f47089f9240059bb0fd6736bfa19583e35585f716467f75b1da671f5 | 3.318 | CN | CN:605117 / 宁波德业科技股份有限公司 | 2024 | H1 | INTERIM_REPORT | cninfo / 1220989603 | 2024-08-26 | — | workspace/ingest/raw-store/sha256/e4/e4a48d45f47089f9240059bb0fd6736bfa19583e35585f716467f75b1da671f5.pdf | yes | yes | 1 / PASS / 0 |
| 76 | e6025b022613cd1e1efd0cc44e6f891ca2e71ff383b493ec628c6707e41e4912 | 1.994 | CN | CN:300308 | 2025 | H1 | INTERIM_REPORT | cninfo / 1224585964 | 2025-08-26 | — | workspace/ingest/raw-store/sha256/e6/e6025b022613cd1e1efd0cc44e6f891ca2e71ff383b493ec628c6707e41e4912.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 77 | e681f3552fe772589226cb9ed2be79bb88af80097c78dee3568fc92b13c512b6 | 3.957 | CN | CN:600048 / 保利发展控股集团股份有限公司 | 2024 | H1 | INTERIM_REPORT | cninfo / 1220911436 | 2024-08-19 | — | workspace/ingest/raw-store/sha256/e6/e681f3552fe772589226cb9ed2be79bb88af80097c78dee3568fc92b13c512b6.pdf | yes | no | 0 / — / — |
| 78 | e7baf814a3bd7edd93be9c37bcd0ee74792f8406d87a13fb056c769c68f07285 | 0.460 | CN | CN:600048 / 保利发展控股集团股份有限公司 | 2024 | Q3 | QUARTERLY_REPORT | cninfo / 1221543180 | 2024-10-28 | — | workspace/ingest/raw-store/sha256/e7/e7baf814a3bd7edd93be9c37bcd0ee74792f8406d87a13fb056c769c68f07285.pdf | yes | no | 0 / — / — |
| 79 | e9ad46964c5595c7a6bd2ddfbf1b2e5cc3f85747fe86c0821ce8d689b9fd1e11 | 0.985 | CN | CN:002371 | 2025 | H1 | INTERIM_REPORT | cninfo / 1224615664 | 2025-08-28 | — | workspace/ingest/raw-store/sha256/e9/e9ad46964c5595c7a6bd2ddfbf1b2e5cc3f85747fe86c0821ce8d689b9fd1e11.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 80 | f59647db168aa6bb30cc9934b011f80a8ff170ec11750bc57b69f54dd98e1339 | 1.596 | CN | CN:605117 / 宁波德业科技股份有限公司 | 2025 | FY | ANNUAL_REPORT | cninfo / 1225089135 | 2026-04-09 | — | workspace/ingest/raw-store/sha256/f5/f59647db168aa6bb30cc9934b011f80a8ff170ec11750bc57b69f54dd98e1339.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 81 | f7a3f8c12b1fac000887b96b7a27a1150aad4677dff052ce9a753a259a826382 | 0.204 | CN | CN:002371 | 2025 | Q3 | QUARTERLY_REPORT | cninfo / 1224774311 | 2025-10-30 | — | workspace/ingest/raw-store/sha256/f7/f7a3f8c12b1fac000887b96b7a27a1150aad4677dff052ce9a753a259a826382.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |
| 82 | f9f2f24088e1f641a3a57c9572825203e8947a09caa8515e8f400070baafbfdf | 0.446 | CN | CN:605117 / 宁波德业科技股份有限公司 | 2023 | Q1 | QUARTERLY_REPORT | cninfo / 1216657175 | 2023-04-27 | — | workspace/ingest/raw-store/sha256/f9/f9f2f24088e1f641a3a57c9572825203e8947a09caa8515e8f400070baafbfdf.pdf | yes | yes | 1 / REVIEW_REQUIRED / 0 |

## 8. 收尾完整性核验

| 检查 | 结果 |
|---|---|
| 计划内 workspace/scratch 目录是否仍存在 | PASS；全部不存在 |
| workspace/t 是否仍存在 | PASS；不存在 |
| worktrees/t 是否仍存在 | PASS；不存在 |
| runtimes/p9-jr-tests 是否仍存在 | PASS；不存在 |
| workspace/ingest/raw-store 是否存在 | PASS |
| raw PDF 数量与 Registry binding 数量 | PASS；82 / 82 |
| Registry documents / sources / locations | PASS；82 / 82 / 82 |
| P8 catalog | PASS；70 entries，raw overlap 68 |
| raw orphan candidate | PASS；0 |
| multi-SHA logical filing group | PASS；0 |
| git worktree metadata | PASS；52 registered，0 locked，0 prunable |
| git ls-files --deleted | PASS；0 |
| tracked file count | PASS；清理前后均为 396 |
| git diff --check | PASS；本次报告没有 whitespace error |
| full pytest | 未执行；本任务明确禁止/不需要 |

收尾时发现一个独立的当前未提交修改：.agents/skills/FFDF财报数据查询/SKILL.md；以及 00document/01prompt 下的 5 个 untracked 文件。它们不属于 Storage Hygiene 删除范围，本次没有修改、stage 或 commit。最终 commit 只包含本报告。

## 9. 后续建议

1. workspace/scratch 剩余 1.07 MB 的设计输入、issue 证据、probe 脚本和历史 patch 继续由治理流程决定，不自动清理。
2. P11 review worktrees 保持到对应治理流程明确关闭并确认无未合并价值后，再单独执行一次 worktree audit。
3. Dayu/MCP runtime 继续由 lock file 和部署文档管理；不要因体积大而删除或重建。
4. raw-store 继续以 Registry binding、P8 catalog 和 evidence lineage 为删除前置条件；当前 0 orphan，不做数据删除。
