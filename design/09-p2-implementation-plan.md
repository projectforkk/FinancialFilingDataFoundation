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
- response JSON atomic write；
- no FFDF main-runtime Dayu import。

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

## 20. Issue Rule

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
