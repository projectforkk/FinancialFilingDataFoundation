# AGENTS.md

## 1. Project role

Financial Filing Data Foundation（FFDF）是“多年份财报数据基础引擎”，不是投资分析 Agent。

首要职责：

- 发现 / 复用 / 下载正式财报；
- 本机解析 CN/HK PDF；
- 建立 page / section / table / raw fact / evidence；
- 做确定性质量门控与验证；
- 持久化可复用数据；
- 为 CRDE / 财报分析提供稳定上游数据源。

## 2. Hard architecture rules

1. **MCP_AI_API_CALLS = FORBIDDEN**
   - 本项目本地 MCP Server 不得调用 OpenAI / Anthropic / Gemini 或其他远端 LLM API。
   - AI 推理由宿主 Codex 使用用户已有的 ChatGPT/Codex 权益完成。

2. **ORIGINAL_DOCUMENT_IMMUTABLE**
   - 原始财报文件不可修改。
   - 所有修正通过 review overlay / resolution 记录完成。

3. **NO_GUESSING**
   - 不得补造缺失数字。
   - 不得以推算值替换无法读取的原始值。
   - 低质量结果必须升级为 REVIEW_REQUIRED / BLOCKED。

4. **EVIDENCE_REQUIRED**
   - 每条财务原始事实必须能追溯至 document → page → table → row → cell/bbox。

5. **PARSER ≠ CRDE**
   - Extraction 层不负责 Canonical Metric Mapping。
   - Extraction 层不负责 Fiscal Period Engine。
   - Extraction 层不计算 YoY / QoQ / TTM / 估值。
   - Extraction 层不生成投资结论。

6. **INCREMENTAL_FIRST**
   - 已有通过验证的数据必须优先 REUSE。
   - 没有数据时优先复用本地原始文件。
   - 本地缺失时才下载。
   - 未明确要求时不得无条件重解析历史财报。

7. **BORN_DIGITAL_LIGHT_PATH**
   - born-digital PDF 默认禁止全量 OCR、全量 neural layout、全量 TableFormer。
   - OCR / heavy parser 只能作为显式 fallback，且必须有原因代码与证据。

## 3. Governance workflow

正式任务依次经过：

DESIGN → DEVELOPMENT → CODE REVIEW → ACCEPTANCE → DONE

详细状态：

- NOT_STARTED
- READY_FOR_DEVELOPMENT
- IN_DEVELOPMENT
- IN_REVIEW
- CHANGES_REQUIRED
- READY_FOR_ACCEPTANCE
- IN_ACCEPTANCE
- ACCEPTANCE_FAILED
- DONE
- BLOCKED

设计、开发、验收材料分别进入：

- `design/`
- `development/`
- `acceptance/`

不得 code-first / design-later。

## 4. PC environment rule

开发优先复用现有 PC 工具：

1. 检查已安装软件、版本、架构、能力。
2. 已存在且兼容 → REUSE_EXISTING。
3. 不存在 → INSTALL_REQUIRED。
4. 存在但不兼容 → 先设计隔离环境或升级策略。
5. 不得仅因“不是最新版”擅自升级 Python / Git / Node / PATH。

## 5. Git safety

- 禁止破坏性 `git reset --hard` / `git clean -fd`，除非用户明确授权。
- GitHub 为项目状态与设计基线唯一真源。
- 设计基线、开发提交、验收证据必须可追溯到 commit SHA。


## 6. FFDF MCP 使用规则（中文注释）

### 6.1 何时优先使用 FFDF MCP

进行本地财报研究时，优先通过 FFDF MCP 读取已经完成下载、解析和验证的财报数据。

推荐顺序：

1. 先调用 ffdf_list_documents，确认目标公司、年份和期间是否已经入库；
2. 再调用 ffdf_get_document，查看页数、表格数、Raw Facts 数以及 Validation 状态；
3. 调用 ffdf_get_validation，确认是否存在 blocking issue；
4. 需要查原文时使用 ffdf_search_document / ffdf_read_pages；
5. 需要结构化表格时使用 ffdf_list_tables / ffdf_get_table；
6. 需要财务原始事实时使用 ffdf_list_raw_facts / ffdf_get_fact；
7. 对关键结论使用 ffdf_get_evidence 追溯证据。

### 6.2 中文注释：REVIEW_REQUIRED 的使用边界

REVIEW_REQUIRED 不等于解析失败。

当 blocking_issue_count = 0 时，允许继续用于研究，但必须保留以下边界：

- 不得把 REVIEW_REQUIRED 静默改成 PASS；
- 不得猜测 period、unit、scope 或 statement classification；
- 不得用推导值覆盖原始 Raw Fact；
- 关键结论必须能回溯到 page / table / fact / evidence；
- 需要语义确认时进入 P9 Review，而不是直接修改原始数据。

### 6.3 中文注释：MCP 与 ingest 的职责分工

FFDF MCP 是只读研究入口，不负责下载新财报。

下载和解析新财报使用：

    ffdf ingest --market CN --ticker <代码> --year <年份> --period <Q1|H1|Q3|FY>

成功并且 P7 无 blocking issue 后，ingest 会把财报加入 P8 live catalog。

MCP Server 启动时读取 catalog，所以 ingest 新财报后，如果当前 Codex 会话仍看不到最新数据，应重新启动 Codex 会话。

### 6.4 当前 MCP 部署信息

Codex MCP 名称：ffdf

Server：ffdf-local

Catalog：

    workspace/mcp/p8-live-catalog.json

当前提供 11 个只读工具，不允许：

- 网络下载；
- 远端 AI/API 调用；
- 任意文件系统访问；
- 修改 Raw PDF；
- 修改 P3-P7 artifacts；
- 修改 Registry；
- 修改 P8 Catalog。

完整中文部署说明见：

    docs/FFDF_MCP_部署与使用.md
