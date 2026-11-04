# 01 — Financial Filing Data Foundation 详细设计书

状态：**DESIGN BASELINE — P9 DONE / P10 DESIGN READY**

仓库：`projectforkk/FinancialFilingDataFoundation`

---

## 1. 背景

本项目的目的不是直接生成财报分析报告，而是为后续财报分析建立长期可复用的数据基础。

目标用户会反复研究同一家公司、不同公司以及多个财年。如果每次研究都重新下载、重新读取、重新解析所有历史财报，会重复消耗：
- 本机 CPU / 内存；
- Codex 上下文 / 视觉用量；
- 网络请求；
- 人工复核时间。

因此系统必须遵循“**每份正式财报只做必要的一次解析，之后长期复用；只对新增/缺失期间做增量补齐**”。

本项目首期最难的问题是 CN/HK 财报 PDF extraction。US 市场后续优先走 SEC HTML / Inline XBRL / XBRL，而非把 PDF 作为默认入口。

---

## 2. 可验证目标

### 2.1 业务目标

输入：

```text
company
market
start_year
end_year
```

系统必须：

1. 构造目标期间所需正式财报集合。
2. 检查 Parsed Data Store 是否已有对应、可复用的数据资产。
3. 已有有效数据 → `REUSE_DATA`，禁止重新解析。
4. 数据缺失时检查本地原始文件。
5. 本地有正式财报 → `PARSE_LOCAL`。
6. 本地没有 → 通过 Acquisition Provider 下载。
7. 下载后解析、验证、持久化。
8. 最终生成完整的 multi-year financial filing dataset。
9. 下游 CRDE / 财报分析只能消费已通过验证的数据资产或明确标记的 unresolved data。

### 2.2 Extraction 目标

CN/HK PDF 必须输出：

- document metadata；
- page metadata；
- native text / blocks / words / bbox；
- section tree；
- table candidates；
- reconstructed tables；
- financial table candidates；
- raw financial facts；
- evidence；
- validation；
- review queue；
- parser / schema / source version 信息。

### 2.3 追溯目标

任意 raw financial value 必须可以追溯：

```text
RawFact
  → Cell
  → Row
  → Table
  → Page
  → Original Document
  → Source Metadata
```

### 2.4 性能目标原则

born-digital PDF 默认不得运行：
- full-document OCR；
- full-document neural layout model；
- full-document TableFormer；
- full-document remote AI API。

代表样本必须记录阶段计时，而不是只记录总耗时。

---

## 3. Non-goals

首期不做：

- 投资分析；
- 估值；
- 目标价；
- 28 个研究问题回答；
- canonical metric 最终映射；
- fiscal period 最终标准化；
- YoY / QoQ / TTM；
- 财务预测；
- 自动修改源 PDF；
- MCP 内部调用任何远程 LLM API。

这些能力属于 CRDE 或更下游分析系统。

---

## 4. 总体架构

```text
                   User / Codex
                        |
              Direct Tool Orchestration
                        |
                     Local MCP
                        |
          +-------------+--------------+
          |                            |
 Incremental Planner             Query / Review API
          |
          v
 Existing Parsed Data?
    | yes              | no
    v                  v
 REUSE_DATA       Local Raw File?
                    | yes       | no
                    v           v
               PARSE_LOCAL   Acquisition
                              Provider
                                 |
               +-----------------+------------------+
               |                 |                  |
              CN                HK                 US
           Dayu/CNINFO       Dayu/HKEX         SEC Provider
               |                 |                  |
             PDF               PDF           HTML/iXBRL/XBRL
               +---------+-------+
                         |
                Native PDF Parser
                         |
                Deterministic Quality Gate
                    |             |
                    | pass        | review
                    v             v
                Persist      Codex local review
                                  |
                            Review Overlay
                                  |
                             Re-validate
                                  |
                                  v
                         ParsedFinancialDocument
                                  |
                                  v
                                CRDE
                                  |
                                  v
                        Financial Analysis
```

---

## 5. 模块与依赖设计

预计 Python package：

```text
financial_filing_data_foundation/
  planner/
  registry/
  acquisition/
  parsing/
    pdf/
    sec/
  sections/
  tables/
  facts/
  evidence/
  quality/
  validation/
  storage/
  review/
  mcp/
  export/
```

### 5.1 Incremental Planner

职责：
- 计算目标公司/年份范围的 required filing set；
- 查询 Parsed Data Registry；
- 查询 Local Document Registry；
- 决定 action；
- 不执行解析。

输出 action 只能是：

```text
REUSE_DATA
PARSE_LOCAL
DOWNLOAD_AND_PARSE
REVIEW_REQUIRED
BLOCKED
```

### 5.2 Local Document Registry

保存：
- path；
- sha256；
- market；
- company identity；
- filing type；
- fiscal year / raw fiscal period candidate；
- file size；
- mtime；
- source metadata（若已知）。

不得只按文件名判重。

### 5.3 Parsed Data Registry

保存：
- document_key；
- document_sha256；
- parse_run_id；
- parser_version；
- schema_version；
- validation status；
- blocking issue count；
- compatibility status。

只有满足 reuse policy 才能返回 `REUSE_DATA`。

### 5.4 Acquisition Provider

抽象接口：

```python
class AcquisitionProvider(Protocol):
    def discover_documents(self, request) -> list[DocumentCandidate]: ...
    def download_document(self, candidate) -> DownloadedDocument: ...
    def load_source_metadata(self, candidate) -> SourceMetadata: ...
```

首期适配：
- CN：复用 Dayu 的 CNINFO discovery/downloader 能力；
- HK：复用 Dayu 的 HKEX discovery/downloader 能力；
- US：后续 SEC Provider。

Dayu CN/HK 当前高层 `fins download` 会在 PDF 下载后继续 Docling conversion，因此本项目不得把该高层 workflow 当作“纯下载”接口；应通过窄 adapter 复用 discovery/downloader 能力，输出 PDF + provenance 后结束。

P2 已确认 Dayu 正式 package dependency / initializer import graph 会扩大运行时依赖面，因此 FFDF main runtime 不直接安装/import Dayu；采用独立 Dayu acquisition runtime + subprocess JSON boundary。详细见 `design/08-p2-acquisition-provider-design.md`。

### 5.5 Native PDF Parser

职责：
- open PDF；
- metadata / page count / encryption / repair signals；
- native text；
- words / blocks / spans / fonts；
- bbox；
- drawings；
- images；
- page geometry；
- cheap table candidate detection。

默认实现优先考虑 PyMuPDF，但正式依赖需在 P0 PC 环境审计后锁定。

### 5.6 Section Engine

输入 native layout。
输出 heading candidates + section tree。

不得依赖单一“plain text reading order”。

### 5.7 Table Engine

分层：
1. cheap detector；
2. table region；
3. row clustering；
4. column clustering；
5. header tree；
6. merged-cell candidate；
7. continuation / cross-page stitching；
8. financial table candidate classification。

不得对所有页面无条件执行最高复杂度 reconstruction。

### 5.8 Quality Gate

必须是 deterministic quality signals，不得把“模型自报 confidence”当真值。

至少包含：
- text integrity；
- encoding quality；
- reading-order quality；
- layout integrity；
- table structure；
- header alignment；
- cross-page consistency；
- financial consistency checks；
- blocking flags。

### 5.9 Review Overlay

Codex 修复不能覆盖原始 extraction。

数据分层：

```text
RAW
LOCAL_EXTRACTED
REVIEW_OVERLAY
RESOLVED
EXPORT
```

所有 resolution 必须记录：
- target；
- base parse run；
- reason code；
- evidence pages；
- before / after；
- reviewer；
- timestamp；
- validation result。

### 5.10 Local MCP

MCP 是工具接口，不是 parser 本体。

Hard rule：

```text
MCP_AI_API_CALLS = FORBIDDEN
```

MCP 只调用本机代码 / 文件 / SQLite / acquisition adapter。

### 5.11 Codex Dynamic Research Integration

P10 不实现固定业务语义的 Codex Skill。Codex 直接接收用户在每次 research run 提供的运行时研究规范文件，并基于这些文件当前内容动态选择 P8/P9 工具完成信息获取与 review。

P10 的固定职责仅包括：
- 验证 Codex 可以发现并调用 P8 read-only MCP；
- 验证 Codex 可以通过 P9 local API/CLI 执行受控 review，而不是修改 raw artifacts；
- 规定“运行时研究规范优先”的集成边界：不得把固定问题数量、日期范围、报告 Schema、章节映射或研究业务规则复制进 P10；
- 允许使用薄层 AGENTS.md / integration instruction 告知 Codex FFDF 工具的能力、边界和禁止事项，但该薄层不得复制研究规则正文；
- 每次 research run 开始时读取并冻结用户提供研究规范文件的内容哈希；同一 run 中不得静默切换到修改后的文件版本；
- Codex 根据当前问题的信息需求动态选择 document / fact / table / evidence / validation 工具，不维护“问题编号 → 固定接口序列”的硬编码映射；
- 当 P8 返回 REVIEW_REQUIRED 时，Codex 必须读取证据并通过 P9 resolution contract 处理；证据不足时保持 unresolved，不得猜测；
- 本地 FFDF 无法提供且运行时研究规范要求补充的外部信息，由 Codex 按当次规范规定的来源边界获取；P10 不固化研究来源策略；
- 对运行时规范提出但当前工具链不具备的能力，显式返回 incompatible / blocked，不得通过猜测或静默降级完成。

P10 不承担 deterministic parsing，不生成或维护固定研究问题清单，也不成为研究业务规则真源。

P10 v1 的 accepted dependency 仅限 P8/P9。P10 可以增加 deterministic run plumbing（runtime spec freeze、capability/context manifest、evidence ledger validation），但不得把 Codex reasoning 写入 Python production。

P10 v1 不实现 PDF visual renderer。若 P8/P9 structured evidence 无法安全满足当前 research need，必须显式返回 `P10_VISUAL_CAPABILITY_REQUIRED`；不得假装 future Research MCP 已存在。design/29 仅作为未来 additive visual/resolved-query reference，design/28 仅作为未来 deterministic semantic architecture reference。

---

## 6. PC 环境与工具设计

开发遵循 existing-tools-first：

1. 检查现有 Python / architecture / Git / Codex / Dayu / PyMuPDF / SQLite。
2. 已有且兼容 → REUSE_EXISTING。
3. 不兼容 → 设计隔离环境。
4. 未安装 → 才允许 INSTALL_REQUIRED。
5. 不得随意替换系统 Python / PATH。

目标 PC 已知存在 Windows ARM64 环境；Dayu 代表测试曾在 AMD64 Python + CPU-only Torch 运行。P0 必须记录实际用于 FFDF 的 Python arch，不得从历史环境推断。

---

## 7. 核心接口

### 7.1 Build Plan

```python
build_plan(
    company: CompanyRef,
    start_year: int,
    end_year: int,
    policy: IncrementalPolicy,
) -> FilingPlan
```

### 7.2 Register Document

```python
register_document(
    path: Path,
    source: SourceMetadata | None,
    expected_identity: FilingIdentity | None,
) -> RegisteredDocument
```

### 7.3 Parse Document

```python
parse_document(
    document_id: str,
    profile: str = "auto",
) -> ParseSummary
```

### 7.4 Query

```python
search_document(document_id: str, query: str, top_k: int = 10)
read_pages(document_id: str, pages: list[int])
list_sections(document_id: str)
list_tables(document_id: str, ...)
get_table(table_id: str, ...)
render_page(document_id: str, page_no: int)
```

### 7.5 Review

```python
submit_resolution(
    target_type: str,
    target_id: str,
    base_run_id: str,
    reason_code: str,
    patch: dict,
    evidence_pages: list[int],
) -> ResolutionResult
```

### 7.6 Validate and Export

```python
validate_document(document_id: str) -> ValidationResult
export_document(document_id: str) -> ExportManifest
```

---

## 8. 数据字段与版本参与

### 8.1 FilingSlotKey / DocumentKey

Planner 的 required filing 业务槽位：

```text
market + company_id + filing_type + fiscal_year + raw_fiscal_period
```

P1 起正式命名为 `FilingSlotKey`；现有 `DocumentKey` 语义与其一致。

`amended` 不进入 required slot 主键，而是具体 filing document variant 的元数据。原版/修订版属于同一 required slot，但可以对应不同 `document_sha256`。

具体文件 identity：

```text
document_sha256
```

不得将 filename 当稳定 identity，也不得把 amended 版本自动当成额外 required filing。

### 8.2 Parse Key

```text
parse_key = SHA256(
    document_sha256
    + parser_version
    + config_hash
)
```

### 8.3 SourceMetadata

至少：
- provider；
- source_id；
- source_url；
- source_title；
- filing_date；
- report_date；
- provider_company_id；
- acquired_at。

### 8.4 RawFact

至少：
- raw_fact_id；
- raw_metric_name；
- raw_value；
- parsed_numeric_value candidate；
- raw_unit；
- raw_period_label；
- raw_scope；
- table_id；
- page_no；
- row_index；
- column_index；
- evidence_id。

RawFact 不允许直接存 canonical metric 名作为唯一真值。

### 8.5 Evidence

至少：
- evidence_id；
- document_sha256；
- page_no；
- bbox；
- raw_text；
- table_id nullable；
- row/column nullable；
- extraction_run_id。

---

## 9. 正常主流程

```text
REQUEST
  |
  v
build required filing set
  |
  v
for each filing:
  |
  +--> parsed reusable? ---- yes ---> REUSE_DATA
  |
  no
  |
  +--> local raw exists? --- yes ---> REGISTER + PARSE
  |
  no
  |
  +--> ACQUIRE OFFICIAL SOURCE
                         |
                         v
                       PARSE
                         |
                         v
                     QUALITY GATE
                    /            \
                 PASS          REVIEW
                  |              |
                  |              v
                  |            Codex
                  |              |
                  +------> resolution
                               |
                               v
                           VALIDATE
                               |
                               v
                           DATA_READY

all periods ready/known-blocked
  |
  v
MULTI-YEAR DATASET
```

---

## 10. 分支流程

### 10.1 Born-digital

默认：
- OCR OFF；
- native extraction；
- local table detection / reconstruction；
- low-confidence local review only。

### 10.2 Mixed

按页分类。
仅低文本/图像主导页面允许 OCR / Codex visual escalation。

### 10.3 Scanned

标记 `SCAN_HEAVY`。
首期可以进入 `REVIEW_REQUIRED` / `OCR_REQUIRED`，不得假装已可靠解析。

### 10.4 Corrupted

PyMuPDF/MuPDF 若可 repair，应记录 repair signal。
若无法建立完整 page set → BLOCKED。

---

## 11. 错误、重试与阻断

错误必须结构化 reason code，例如：

- PDF_OPEN_FAILED
- PDF_ENCRYPTED_UNSUPPORTED
- PAGE_TEXT_EMPTY
- ENCODING_SUSPECT
- READING_ORDER_SUSPECT
- TABLE_GRID_AMBIGUOUS
- YEAR_COLUMN_AMBIGUOUS
- UNIT_AMBIGUOUS
- CROSS_PAGE_STITCH_AMBIGUOUS
- FINANCIAL_RECONCILIATION_FAILED
- SOURCE_DOWNLOAD_FAILED
- SOURCE_IDENTITY_AMBIGUOUS
- SCAN_OCR_REQUIRED

下载可重试；本地 deterministic parse 的同输入失败不得无限重试。

---

## 12. 版本与兼容

至少版本化：
- schema_version；
- parser_version；
- quality_policy_version；
- acquisition_adapter_version；
- review_schema_version。

parser 升级不得自动导致所有历史财报重解析。

Reuse 判定必须检查：
- data PASS；
- blocking issues = 0；
- schema compatible；
- parser defect policy 未命中；
- source document 未发生 material change。

---

## 13. 幂等与增量

同一：
- document_sha256；
- parser_version；
- config_hash

重复 parse 必须可 REUSE。

正常重复研究同一公司：
- 历史 DATA_READY → 0 parse；
- 仅新增期间进入 acquisition / parse。

不得以“用户再次运行研究”为理由重解析历史全部财报。

---

## 14. 日志与审计

每个 ParseRun 必须记录阶段计时：

- open_pdf_ms；
- preflight_ms；
- native_text_ms；
- layout_ms；
- section_ms；
- table_detection_ms；
- table_reconstruction_ms；
- validation_ms；
- persist_ms；
- total_ms。

另记录：
- peak memory（若可得）；
- page counts；
- local accepted；
- text review；
- vision review；
- errors；
- fallback reason。

不得只记录总耗时。

---

## 15. 安全与禁止事项

禁止：
- 修改源 PDF；
- 通过 AI 自动补数字；
- silent fallback；
- 解析失败仍标 DATA_READY；
- 远程 LLM API hidden call；
- born-digital PDF 默认全量 OCR；
- 只凭“native text exists”判定页面可靠；
- 只凭“table count”判定解析正确。

---

## 16. 单元测试

至少覆盖：

- document identity；
- SHA / parse key；
- incremental action decision；
- local registry；
- reuse policy；
- page text extraction；
- bbox normalization；
- table candidate detection；
- row/column grouping；
- unit parsing；
- raw fact construction；
- evidence linking；
- quality flags；
- resolution overlay；
- validation；
- export manifest。

---

## 17. 集成 / Golden / Performance

### Golden

必须有人工确认：
- page count；
- financial statement page ranges；
- headers；
- unit；
- scope；
- selected key rows / values；
- cross-page relation。

### Performance

首个代表样本：
- 600519 / 贵州茅台 FY2024；
- 143 pages；
- born-digital；
- 用于对比 Dayu heavy-path baseline。

P0 不要求完整 table reconstruction，只验证 native path 的性能与可读取性。

---

## 18. 验收标准

阶段验收必须能复现。

首期总目标的最终 acceptance 至少要求：

1. original document SHA 可追溯；
2. page count 100% 正确；
3. required golden statement locations 100% 正确；
4. golden unit / year columns / scope 100% 正确；
5. golden key values 100% 正确；
6. 每个 key value 有 evidence；
7. unresolved blocking issue 不得导出 DATA_READY；
8. 重复执行能正确 REUSE；
9. 已有 parsed data 时不重新 parse；
10. 本地文件存在时不重复下载；
11. 本地缺失时才 download；
12. born-digital representative sample 不得走 full OCR / full heavy neural path。

---

## 19. 开发者提交要求

每个开发阶段提交必须包含：

- design baseline SHA；
- branch；
- commit SHA；
- changed files；
- tests；
- exact commands；
- exact results；
- known limitations；
- no-scope-change statement；
- performance data（若适用）。

开发者不得擅自：
- 增加远程 AI API；
- 将 canonicalization 移入 parser；
- 将 analysis 移入 parser；
- 更改 incremental reuse semantics；
- 用重型 Docling 默认路径替代本设计。

---

## 20. 阶段开发顺序

### P0 — Native PDF Parsing Feasibility Probe

只做 benchmark / feasibility：
- environment audit；
- PDF open；
- page count；
- text / words / blocks；
- bbox / drawings / images；
- cheap table candidate detector；
- per-stage timings。

**不做完整 MCP，不做完整 Skill。**

### P1 — Identity / Registry / Incremental Planner

建立：
- FilingIdentity；
- DocumentRegistry；
- ParsedDataRegistry；
- build_plan；
- reuse/local/download decision。

### P2 — Acquisition Provider

建立 provider contract。
CN/HK 通过 Dayu narrow adapter 实现纯 acquisition，不进入 Docling conversion。

### P3 — Native Page / Section Extraction

完成 page / block / bbox / section / FTS。

### P4 — Table Candidate Detection

仅找候选表区，先不承诺完整财务表恢复。

### P5 — Table Reconstruction

row / column / header / merged cell / cross-page。

### P6 — Financial Raw Facts + Evidence

建立 raw facts / evidence graph。

### P7 — Quality Gate + Validation

deterministic gate、accounting consistency、document completeness。

### P8 — Local MCP

将已验证能力包装为小型稳定 tool surface。

### P9 — Codex Review + Resolution Overlay

仅处理 REVIEW_REQUIRED。

### P10 — Codex Dynamic Research Integration

不实现固定 Codex Skill，也不复制用户研究规则。

建立并验收 Codex 对 FFDF 的直接动态调用模式：
- 用户每次直接提供当前版本的研究 Prompt / constraints / question list 或其他研究规范文件；
- Codex 必须先完整读取当前运行时文件，再根据问题动态推导信息需求；
- 财报结构化数据优先通过 P8 read-only MCP 获取；
- REVIEW_REQUIRED 通过 P9受控 review contract 处理；
- 允许薄层 AGENTS.md / integration instruction 只描述 FFDF 工具能力与边界；
- 对每次 research run 固定输入规范 SHA256，禁止运行中静默切换规则版本；
- 验证不同版本研究规范无需修改 P10 production 即可改变研究任务、查询范围和输出要求；
- 验证工具选择由信息需求驱动，而非由固定问题编号驱动；
- 验证无法支持的新增能力会显式 BLOCKED / INCOMPATIBLE，而不是猜测或静默降级。

P10 acceptance 必须包含至少一个完整 live research run，证明 Codex 能直接读取动态研究规范、调用 P8/P9、取得可追溯证据，并按运行时规范完成信息查询。

同时必须包含 negative capability case：如果 structured evidence不足且需要未验收的 PDF visual capability，P10 必须显式 BLOCK/GAP，不得猜测或越权实现 Research MCP。

### P11 — US SEC Provider

接入 HTML / Inline XBRL / XBRL，复用统一 ParsedFinancialDocument Contract。

---

## 21. 问题处置与设计回写规则

执行任何阶段时，如果发现设计假设、环境假设、依赖边界、实现方式或验收路径存在问题，必须执行以下流程：

```text
发现问题
↓
停止当前 Gate 继续推进
↓
确认事实与根因
↓
找到可执行解决方案
↓
先更新对应设计书
↓
提交并形成新的 Git 设计基线
↓
评估受影响的开发 / 测试 / Code Review / Acceptance Gate
↓
必要时重新执行受影响 Gate
↓
再继续后续步骤
```

强制要求：

- 不得先修改 production code，事后再补设计；
- 不得仅在聊天记录中记录方案而不更新 Git 设计基线；
- 问题、根因、解决方案、影响范围必须可从设计变更追溯；
- 若问题发生在 acceptance input freeze 之后，原冻结输入失效，必须更新设计后重新 freeze；
- 若解决方案会改变外部依赖版本、运行时、数据契约或验收标准，必须重新执行相应 Gate；
- 若确认问题只影响文档/治理且不影响 production candidate，也必须形成新的设计 baseline，并在验收冻结中明确记录该结论。

### 21.1 Design / directory governance

设计书统一索引：`design/00-design-management-index.md`。

项目目录统一治理：`design/15-project-directory-management.md`。

从 P6 起，所有 FFDF 自有 dependency/runtime/worktree/workspace/data 必须位于：

`D:\Codex\FinancialFilingDataFoundation\`

历史 sibling path 只作为历史 evidence，不再作为 active default。

### 21.2 Governance text encoding

所有 tracked Markdown / JSON governance artifacts 统一使用 `UTF-8 without BOM`。

禁止使用会按宿主默认代码页重新编码 Unicode 的写回方式。Windows PowerShell 仅可用于只读展示或显式 UTF-8 no-BOM 写入；正式文档修改优先使用能够明确保持 UTF-8 的工具/代码路径。

若发现治理文档出现乱码/替换字符：

1. STOP 当前 closeout；
2. 确认事实来源；
3. 以已验收 Git evidence 重建受损文案；
4. 保存为 UTF-8 no-BOM；
5. `git diff --check` + UTF-8 decode validation；
6. 再继续 phase closeout。

### 21.3 Accepted baseline 与 main HEAD

正常规则：阶段 implementation 通过 Independent Acceptance 后才进入 `main`。

`main HEAD` 与“当前已验收 baseline”必须在 `PROJECT_STATUS.md` 中分别可识别；正常情况下二者一致。

若发生误将未验收阶段提交推入 `main` 的治理异常：

1. 禁止通过 `reset --hard`、force push 或历史重写隐藏问题；
2. 立即停止后续 Gate，并记录 incident、涉及 commit、根因和影响范围；
3. `PROJECT_STATUS.md` 必须显式固定 `accepted_baseline_sha`，此时不得把 `main HEAD` 当作 accepted baseline；
4. 正式开发/验收仍以阶段 task branch 的冻结 candidate 为准；
5. 若该阶段最终 PASS，closeout 将新的 accepted baseline 更新到验收通过后的 phase closeout commit；若 phase commits 已经是 main 的祖先，则无需为了形式再制造重复 merge；
6. 若该阶段 FAIL / ABORT，必须通过可追踪的 revert commit 撤销未验收 implementation，不得改写历史；
7. 后续阶段恢复“acceptance PASS 后再进入 main”的正常规则。

### 21.4 Candidate Worktree 隔离规则

Code Review / Independent Acceptance 的证据必须绑定到固定 candidate SHA，不得依赖可能被其他进程切换分支的共享开发工作树。

当存在并发开发、自动同步或多个会话同时操作同一仓库时，必须：

1. 创建独立 Git worktree；
2. worktree 使用 detached HEAD 或专用 review branch，并固定到 frozen candidate SHA；
3. 每组关键 review/acceptance 命令执行前后都记录 `git rev-parse HEAD`；
4. 若 HEAD 与 frozen candidate 不一致，该组结果立即作废；
5. review/acceptance 过程中不得通过共享主工作树的当前 branch 推断 candidate；
6. 生成的临时 DB、pytest basetemp、machine-readable acceptance artifacts 仅写入 ignored workspace；
7. production/tests/design 若需修改，必须退出 acceptance，回到 design-first / development 流程并重新 freeze。

此规则只用于隔离执行环境，不改变 candidate 的 Git 内容。

---

## 22. 当前批准结论

P0 已完成并收口为 `P0_DONE`。

P1 已完成 Independent Acceptance 并收口为 `P1_DONE`。

P2 已完成 Independent Acceptance 并收口为 `P2_DONE`。

P3 已完成 Independent Acceptance 并收口为 `P3_DONE`。

P4 已完成 Independent Acceptance 并收口为 `P4_DONE`。

P5 已完成 Independent Acceptance 并收口为 `P5_DONE`。

P6 已完成 Independent Acceptance 并收口为 `P6_DONE`。

P7 已完成 Independent Acceptance 并收口为 `P7_DONE`。

P8 已完成 Independent Acceptance 并收口为 `P8_DONE`。

P8 accepted capabilities：
- official MCP Python SDK 2.3.0；
- protocol `2026-07-28`；
- stdio-only local transport；
- exact 11 read-only deterministic FFDF tools；
- dedicated Python 3.12.14 AMD64 MCP runtime；
- tracked reproducible runtime lock；
- MCP AI API calls strictly FORBIDDEN；
- no acquisition / parse / mutation / arbitrary filesystem / SQL / shell / remote AI surface。

P9 已完成 Independent Acceptance 并收口为 `P9_DONE`。

P9 accepted capabilities：
- deterministic REVIEW-only queue over P7 `REVIEW_REQUIRED` issues；
- evidence-grounded immutable resolution records；
- explicit prior-overlay identity / deterministic history recomputation；
- raw P3/P5/P6/P7 and source PDF remain immutable；
- effective period/unit/scope and statement-class overlay remain separate from raw；
- deterministic resolved snapshot / status / reuse eligibility；
- local six-command JSON-only CLI；
- deterministic payload security boundary for URL/path/shell/SQL/Python/credential content；
- no network / AI / external MCP SDK / Registry mutation；
- CN/HK live acceptance, synthetic golden, base immutability and performance gates PASS。

P9 accepted identity：
- final production candidate = `66308627d1dd1f0af2f02ff3f18d3e91f33dcc8d`；
- final formal review = `development/74-p9-jr3-formal-rereview-result.md` = PASS；
- frozen acceptance candidate = `926c665f5dd667765781630638c62239b267ceb7`；
- acceptance evidence = `acceptance/37-p9-acceptance-result.md` = PASS；
- accepted merge = `58a1d2236b68a56fc66ddf8b97603e7232c87265`；
- post-merge full regression = `308 passed`。

当前 P10 状态：

**P10 — Codex Dynamic Research Integration（DESIGN READY）**

Design candidate：
- `design/24-p10-codex-dynamic-research-integration-design.md`；
- `design/25-p10-implementation-plan.md`；
- `acceptance/38-p10-acceptance-instruction.md`；
- `development/76-p10-design-reconciliation.md`；
- reconciled `design/28` future semantic reference；
- reconciled `design/29` future Research MCP reference。

P10 production 在该 exact design baseline commit/push 到 GitHub 且后续 development instruction 明确授权前不得开始。

继续保持职责边界：

```text
P8
= Raw Data & Evidence

Codex
= 财务理解 / 当前研究

P9
= Durable Reviewed Decision Store

Research MCP
= future Resolved Query + PDF Visual Evidence

Semantic Resolver
= future deterministic semantic automation
```

P9 不是 `REVIEW_REQUIRED` 的强制修复器；不得用 overlay 掩盖 raw extraction defect。

P11 US SEC provider、Research MCP production 与 Semantic Resolver production 均未获授权，不得提前进入。
