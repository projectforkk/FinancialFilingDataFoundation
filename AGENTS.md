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
