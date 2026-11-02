# 09 — P2 Acquisition Provider 实施计划

状态：**DESIGN BASELINE — P2 EXECUTION PLAN**

前置：

- P1_DONE
- P2 design authorized
- P2 detailed design: `design/08-p2-acquisition-provider-design.md`

---

## 1. P2-A — Baseline / Branch

1. main 必须包含 P1 closeout。
2. main 工作区必须 clean。
3. P2 design baseline 先提交到 main。
4. 创建正式开发分支：
   `task/p2-acquisition-provider`
5. 分支从 design baseline HEAD 创建。
6. 不使用 destructive reset/clean。

Gate A：

`P2_READY_FOR_ENVIRONMENT_AUDIT`

---

## 2. P2-B — Dayu Source / Runtime Audit

只做环境与依赖事实确认，不写 production adapter。

必须记录：

- upstream repository
- pinned commit
- canonical checkout path
- checkout HEAD
- checkout clean/dirty
- available Python 3.11/3.12 interpreters
- interpreter architecture
- uv/pip
- existing compatible runtime 仅作为参考
- Dayu pyproject dependency tree
- Dayu package initializer import behavior
- CN downloader import feasibility
- HK downloader import feasibility

禁止：

- 修改 upstream；
- 将 Dayu 安装到 FFDF `.venv`；
- 为了让 import 成功而 patch upstream `__init__.py`；
- 开始 live download。

Gate B：

形成 reproducible Dayu runtime decision。

---

## 3. P2-C — Pinned Dayu Checkout

若 canonical checkout 不存在：

1. clone upstream；
2. fetch pinned commit；
3. detached checkout exact commit。

若已存在：

1. 不 reset；
2. 检查 origin；
3. 检查 HEAD；
4. 检查 dirty state。

必须：

- HEAD exact；
- worktree clean。

Dirty / mismatch 先设计处置，不自动覆盖。

Gate C：

`DAYU_SOURCE_PIN_VERIFIED`

---

## 4. P2-D — Dedicated Acquisition Runtime

根据 P2-B 决策创建独立 runtime。

原则：

```text
existing compatible base interpreter
→ project-independent dedicated acquisition venv
→ install pinned Dayu from canonical checkout
```

不复用其它项目 venv 作为正式 dependency。

创建后记录：

- Python executable/version/arch；
- Dayu version；
- installed dependency snapshot；
- source checkout commit；
- direct_url / installation provenance；
- FFDF main venv still Dayu-free。

Gate D：

`DAYU_ACQUISITION_RUNTIME_READY`

---

## 5. P2-E — Runner Doctor Feasibility

先实现/执行最小 doctor，不做 network。

验证：

- runner protocol version；
- pinned source descriptor；
- CN downloader symbols import；
- HK downloader symbols import；
- runtime process boundary；
- explicit safe cwd；
- Dayu module origin == dedicated runtime site-packages；
- doctor timeout = 60s initial gate；
- response JSON atomic write；
- FFDF main runtime 在 FFDF/neutral cwd 下无 Dayu installation/import。

若 import graph / runtime 不可用：

STOP → design update。

Gate E：

`RUNNER_DOCTOR_PASS`

---

## 6. P2-F — Domain / Protocol / Raw Store

实现：

- AcquisitionRequest
- ProviderCompanyProfile
- AcquisitionCandidate
- RunnerDownloadedAsset
- AcquisitionResult
- reason codes
- JSON protocol v1
- URL host guard
- RawDocumentStore
- AcquisitionReceipt

测试：

- validation；
- deterministic serialization；
- receipt id；
- path containment；
- SHA-addressed layout；
- atomic write；
- dedup；
- corruption blocker。

Gate F：

focused tests PASS。

---

## 7. P2-G — Dayu Runner

实现 standalone narrow runner：

operations：

- doctor
- discover
- download

约束：

- only CNINFO/HKEX downloader business calls；
- no high-level workflow；
- no parser；
- no Docling conversion；
- Dayu temp cleanup；
- response JSON file；
- structured error；
- no business result via log scraping。

Gate G：

runner contract tests PASS。

---

## 8. P2-H — FFDF Dayu Adapter

FFDF main runtime 实现：

- subprocess command construction；
- `shell=False`；
- timeout；
- request/response files；
- runtime descriptor validation；
- candidate mapping；
- source URL validation；
- independent staging SHA validation；
- runner error mapping。

FFDF adapter module不得 direct import `dayu`。

Gate H：

adapter unit tests PASS。

---

## 9. P2-I — Acquisition Service + Registry

实现：

`acquire_slot(...)`

流程：

```text
defensive local recheck
→ discover
→ exact slot filtering
→ download
→ FFDF independent validation
→ raw store commit/dedup
→ registry register_document
→ receipt
→ STOP
```

必须验证：

- local exists → no runner/network；
- source mapping；
- amended mapping；
- receipt；
- registry local state after acquisition。

Gate I：

service integration tests PASS。

---

## 10. P2-J — Deterministic Mocked Integration

不用公网。

CN fake runner：

- profile
- candidate
- PDF download result

HK fake runner：

同上。

覆盖：

- 0 candidate；
- 1 candidate；
- >1 candidate；
- bad host；
- SHA mismatch；
- bad PDF magic；
- timeout；
- runner error；
- raw-store existing same SHA；
- raw-store corruption；
- registry failure；
- rerun local reuse。

Gate J：

CN/HK mocked end-to-end PASS。

---

## 11. P2-K — Full Regression Before Live

执行：

- P0 tests
- P1 tests
- P2 tests
- compile
- diff check
- forbidden imports
- FFDF main venv module check

Gate K：

全 deterministic suite PASS。

---

## 12. P2-L — Live Sample Confirmation

只有 P2-K PASS 后允许。

### CN

首选：

- 600519
- FY2024
- CNINFO

确认：

- exact target window；
- official source；
- Dayu discovery result。

### HK

通过 HKEX 官方来源实际 discovery 选择代表样本。

必须冻结：

- ticker
- slot
- window
- provider
- expected source identity constraints

若 sample 选择或 provider 行为暴露设计问题：

先更新设计。

Gate L：

`LIVE_SAMPLES_FROZEN`

---

## 13. P2-M — Live CN Acquisition

在 dedicated Dayu runtime：

1. doctor；
2. CN discovery；
3. exact candidate；
4. PDF download；
5. raw store；
6. receipt；
7. registry；
8. source immutability；
9. Dayu checkout clean after run。

验收事实：

- official source；
- SHA；
- file size；
- no Docling JSON；
- no parser output。

Gate M：

CN LIVE PASS。

---

## 14. P2-N — Live HK Acquisition

同 P2-M。

Gate N：

HK LIVE PASS。

---

## 15. P2-O — Incremental Re-run

对已 acquisition 的 slot：

P1 registry 必须 resolve local raw。

再次请求 acquisition service：

- 不启动 Dayu runner；
- 不 network；
- `REUSED_LOCAL`；
- raw file SHA 不变。

Gate O：

incremental acquisition idempotency PASS。

---

## 16. P2-P — Code Review

必须在 isolated detached worktree。

检查：

- P2 scope；
- main runtime隔离；
- upstream pin；
- upstream checkout未修改；
- subprocess安全；
- protocol；
- URL allowlist；
- candidate exact match；
- independent SHA validation；
- raw store atomicity；
- receipt；
- registry；
- no Docling conversion；
- no parser；
- no SEC/P11；
- tests/live evidence。

发现新问题：

设计优先。

Gate P：

`P2_READY_FOR_ACCEPTANCE`

---

## 17. P2-Q — Acceptance Freeze

固定：

- design baseline SHA；
- production candidate SHA；
- Code Review SHA；
- P1 accepted baseline；
- Dayu repository/commit；
- Dayu checkout path；
- Dayu runtime Python；
- exact test commands；
- live CN sample；
- live HK sample；
- raw-store acceptance root；
- expected protocol version。

Freeze 后 design change → freeze失效。

---

## 18. P2-R — Independent Acceptance

在新的 detached worktree 执行。

必须独立验证：

- P0/P1/P2 suite；
- runtime isolation；
- source pin；
- checkout cleanliness；
- doctor；
- mocked CN/HK；
- live CN；
- live HK；
- raw store；
- receipt；
- registry；
- incremental rerun；
- no Docling conversion；
- no parser；
- no US SEC。

Verdict：

`PASS / FAIL / BLOCKED`

---

## 19. P2-S — Closeout

仅 Independent Acceptance PASS：

- evidence commit；
- PROJECT_STATUS → P2_DONE；
- merge accepted P2 to main；
- verify main src/tests == frozen candidate；
- rerun deterministic suite；
- accepted_baseline_sha update；
- 才允许 P3 design。

---

## 20. P2 Issue Log

### P2-ISSUE-005 — Windows console encoding 不得影响 live evidence

P2-L 首次 CN live discovery 已进入 provider，但测试 harness 直接 `print()` 含中文公司名的 dataclass，Windows 控制台 CP932 无法编码字符，导致证据脚本中断。

批准解决方案：

1. live discovery/download 的完整机器证据写入 UTF-8 no-BOM JSON 文件；
2. console 只输出 ASCII-safe status / counts / file path；
3. provider/company/title 原文必须保留在 UTF-8 JSON，不做丢失性转码；
4. console encoding failure 不作为 provider 产品失败，但该次 Gate 证据作废并重跑；
5. Acceptance 采用 JSON evidence，而不是控制台可显示性作为真值。

### P2-ISSUE-004 — same-SHA 测试 fixture 不得通过重复生成 PDF 构造

P2-J 首轮 raw-store dedup test 发现：用 PyMuPDF 分别生成两份“文本内容相同”的 PDF，字节结构/SHA256 不保证一致，因此不能作为 same-SHA fixture。

批准解决方案：

1. same-SHA / multi-path / dedup 测试必须复制同一份已生成 PDF bytes；
2. 不用“相同可见文本”推断 raw document identity；
3. 这与项目 content-addressed identity 原则一致：只有字节 SHA 相同才是同一 raw document；
4. 首轮失败作废，修正 fixture 后重跑 P2-F/J tests。

### P2-ISSUE-003 — Dayu initializer 会 transitively load 高层 workflow/Docling 模块

P2-E doctor 实测发现：仅 import CN/HK downloader 后，`sys.modules` 中已经出现 `cn_download_filing_workflow`、`cn_download_workflow`、`docling_export`。根因不是 runner 主动调用，而是 Dayu package initializer/import graph 自动加载。

批准解决方案：

1. 不把 `sys.modules` 是否出现这些模块作为失败条件；
2. doctor 改为报告 `transitively_loaded_modules`；
3. 强制验证 runner 源码/业务调用路径不主动 import/call high-level workflow / `convert_pdf_to_docling_json`；
4. live/mock 验收继续要求没有 Docling conversion output / Docling JSON artifact；
5. 不修改 upstream initializer 来规避加载。

### P2-ISSUE-002 — JSON request encoding 在手工 doctor harness 中产生 BOM

首次 P2-E doctor 手工请求由 PowerShell `Set-Content -Encoding UTF8` 生成，在当前宿主环境写入 UTF-8 BOM。Runner 按 `encoding="utf-8"` 严格读取并返回 `RUNNER_PROTOCOL_INVALID`，因此该次 doctor 未进入 Dayu import。

批准解决方案：

1. P2 JSON protocol 明确为 `UTF-8 without BOM`；
2. 正式 adapter/runner 使用 Python 写入 request/response；
3. manual/live acceptance harness 也必须使用 no-BOM writer；
4. runner 对 BOM/非法 UTF-8 保持结构化 protocol error，不猜编码；
5. 首次 BOM doctor 结果作废，设计提交后重新执行 P2-E。

### P2-ISSUE-001 — cwd 可把 upstream source 暴露给 FFDF main interpreter

P2-E no-network import doctor 中，检查流程在 `cd D:\Codex\dependencies\dayu-agent` 后直接使用 FFDF main `.venv` 执行 `find_spec('dayu')`，结果能够发现 Dayu source。重新从 FFDF repo cwd 执行时：

- `dayu_spec=None`
- `docling_spec=None`
- `torch_spec=None`
- `pip show dayu-agent` not found

根因：Python 将当前工作目录放入 `sys.path`，并非 FFDF main venv 被安装/污染。

批准解决方案：

1. adapter subprocess 必须显式设置 neutral `cwd`；
2. 禁止把 Dayu source checkout 作为 runner/main cwd；
3. runner 应从 dedicated runtime `site-packages` 加载 Dayu；
4. doctor 验证 Dayu module origin；
5. FFDF main-runtime pollution check 必须从 FFDF/neutral cwd 执行；
6. pinned Dayu 首次 CN downloader import 实测约 10.3s，因此 doctor timeout 初始设为 60s。

该问题不改变 runtime 隔离架构，但会影响 doctor/adapter implementation 与 acceptance checks。

---

## 21. Issue Rule

任一 Gate：

```text
problem found
→ STOP
→ root cause
→ solution
→ update design
→ commit design baseline
→ assess affected gates
→ rerun
→ continue
```

禁止先修代码后补设计。

---

## 21. 顺序

```text
P2-A  Baseline / Branch
P2-B  Source / Runtime Audit
P2-C  Pinned Checkout
P2-D  Dedicated Runtime
P2-E  Runner Doctor
P2-F  Models / Protocol / Raw Store
P2-G  Runner
P2-H  Adapter
P2-I  Service / Registry
P2-J  Mocked Integration
P2-K  Full Regression
P2-L  Live Sample Freeze
P2-M  Live CN
P2-N  Live HK
P2-O  Incremental Re-run
P2-P  Code Review
P2-Q  Acceptance Freeze
P2-R  Independent Acceptance
P2-S  Closeout
```

禁止跨 Gate。
