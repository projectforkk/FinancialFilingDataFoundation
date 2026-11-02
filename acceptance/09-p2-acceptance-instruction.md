# 09 — P2 Independent Acceptance Instruction

状态：**DESIGN BASELINE — P2 ACCEPTANCE**

最终 verdict：

- PASS
- FAIL
- BLOCKED

验收过程中不得修改：

- production code
- tests
- design
- config
- dependency versions
- Dayu upstream checkout

---

## 1. Mandatory Inputs

Acceptance freeze 必须提供：

- exact FFDF candidate SHA；
- accepted P1 baseline；
- Dayu repository；
- Dayu pinned commit；
- Dayu checkout path；
- Dayu runtime Python；
- runtime descriptor；
- deterministic test commands；
- CN live sample；
- HK live sample；
- raw-store root；
- protocol version。

---

## 2. Candidate Isolation

必须使用新的 detached Git worktree。

每组关键命令前后：

- `git rev-parse HEAD`
- `git status --short --branch`

HEAD 漂移则该组证据作废。

---

## 3. Regression

必须：

- P0 tests PASS；
- P1 tests PASS；
- P2 tests PASS；
- P0/P1 accepted source semantics 未被破坏。

---

## 4. Runtime Isolation

FFDF main runtime：

- dayu absent；
- docling absent；
- torch absent。

Dayu acquisition runtime：

- exact configured Python；
- pinned Dayu package/source；
- source checkout clean。

不得在 FFDF main interpreter 直接 import Dayu。

---

## 5. Dayu Source Pin

必须独立验证：

- remote/source repo；
- HEAD == pinned commit；
- worktree clean；
- no local patch。

Mismatch / dirty：

BLOCKED 或 FAIL，按 freeze 定义，不得自动修复。

---

## 6. Runner Doctor

无网络 doctor 必须 PASS。

验证：

- protocol version；
- Dayu version；
- CN downloader import；
- HK downloader import；
- runtime descriptor；
- no high-level workflow invocation。

---

## 7. Subprocess Safety

验证：

- `shell=False`；
- args list；
- timeout；
- response JSON file；
- stdout/stderr 不是业务唯一真源；
- path containment；
- structured errors。

---

## 8. Candidate / Source Safety

验证：

- exact fiscal year；
- exact fiscal period；
- provider-market match；
- source host allowlist；
- 0 candidate → NOT_FOUND；
- >1 exact candidate → REVIEW_REQUIRED；
- 不猜 candidate。

---

## 9. Download Validation

必须由 FFDF main process 独立验证：

- PDF magic；
- file size；
- SHA256；
- Dayu SHA == FFDF SHA；
- staging containment；
- source URL；
- source bytes unchanged。

SHA mismatch / corrupt raw store 不得继续注册。

---

## 10. Raw Store

验证：

- SHA-addressed；
- atomic staging → final；
- same SHA dedup；
- existing corrupted object BLOCK；
- receipt atomic；
- deterministic receipt id。

---

## 11. Registry Integration

验证：

- SourceMetadata；
- provider_company_id；
- amended；
- filing slot；
- final path；
- SHA；
- document_sources provenance；
- local resolution。

Acquisition 后 P1 planner 应看到 local raw。

---

## 12. Incremental Re-run

已 acquisition slot 再次执行：

- no Dayu runner；
- no network；
- no redownload；
- result = REUSED_LOCAL 或等价设计状态；
- raw SHA/mtime stable。

---

## 13. No Parser / No Docling Conversion

必须验证：

- runner 不调用 high-level download workflow；
- runner 不调用 `convert_pdf_to_docling_json`；
- 无 Docling JSON artifact；
- P2 无 parser output；
- P2 不调用 P0/P3 parsing path。

Dayu acquisition runtime 中 Docling package 可能因 upstream dependency 存在，不等于 conversion used。

---

## 14. No P11 SEC

P2 candidate 不得实现 SEC provider。

Dayu package initializer 可能 transitively import `SecDownloader`，但 FFDF P2 runner不得主动调用 SEC downloader。

---

## 15. Deterministic CN/HK Mocked Integration

必须覆盖：

- CN success；
- HK success；
- no candidate；
- ambiguous candidate；
- host rejection；
- SHA mismatch；
- bad PDF；
- timeout；
- runner failure；
- same SHA dedup；
- raw corruption；
- local short-circuit。

全部 PASS。

---

## 16. Live CN

必须从 acceptance freeze 指定 official sample。

验证：

- official discovery；
- official source URL；
- downloaded PDF；
- SHA；
- receipt；
- registry；
- no Docling conversion。

---

## 17. Live HK

同 CN。

样本必须由开发阶段通过 HKEX 官方 discovery 确认并冻结，不得凭记忆指定 source id。

---

## 18. Upstream Immutability

live runs 后：

- Dayu checkout HEAD unchanged；
- `git status --porcelain` empty。

---

## 19. PASS Conditions

全部满足：

- exact candidate；
- tests PASS；
- P0/P1 regression PASS；
- runtime isolation PASS；
- Dayu pin PASS；
- checkout clean；
- doctor PASS；
- mocked CN/HK PASS；
- raw-store/receipt PASS；
- registry PASS；
- incremental no-redownload PASS；
- live CN PASS；
- live HK PASS；
- no Docling conversion；
- no P2 parser；
- no P11 implementation；
- no blocker。

---

## 20. FAIL

产品/设计条件失败，包括：

- wrong candidate；
- wrong source；
- SHA mismatch accepted；
- corrupt raw object overwritten；
- local exists but network still invoked；
- Docling conversion invoked；
- parser invoked；
- P2 SEC implementation；
- deterministic test failure。

---

## 21. BLOCKED

仅用于无法判断的外部执行 blocker，例如：

- pinned dependency unavailable；
- official source temporarily inaccessible；
- target PC cannot create approved runtime；
- HKEX/CNINFO externally unavailable。

不能用 BLOCKED 代替普通产品失败。

---

## 22. Issue Rule

验收发现设计问题：

- stop；
- verdict 暂不 PASS；
- 回到 design-first；
- 更新设计；
- 重新开发/review/freeze。

不得在 acceptance worktree 修代码。
