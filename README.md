# Financial Filing Data Foundation

Financial Filing Data Foundation（FFDF，多市场财报数据基础引擎）用于读取指定公司的多年份正式财报，建立可复用、可追溯、增量更新的财报分析数据源。

## 核心目标

输入“公司 + 市场 + 年份范围”，系统按以下优先级工作：

1. **已有解析数据优先复用**：若目标财报已有有效、通过验证的数据资产，则直接复用，不重新解析。
2. **本地原始文件优先**：若数据尚不存在，但本地已有对应正式财报文件，则直接使用本地文件。
3. **缺失时才下载**：仅当数据不存在且本地没有原始文件时，才通过 Acquisition Provider 下载正式财报。
4. **解析一次，长期复用**：解析结果持久化为带 Evidence 的结构化数据资产，供 CRDE 或其他财报分析流程重复使用。
5. **财报分析不是本项目第一阶段职责**：本项目首先解决 acquisition / extraction / validation / persistence / incremental reuse。

## 首期范围

- CN：A 股正式财报 PDF。
- HK：港股正式财报 PDF。
- US：后续通过 SEC HTML / Inline XBRL / XBRL Provider 接入。
- CN/HK PDF 默认采用本机轻量 native parser；禁止 born-digital PDF 全量 OCR / 全量重型神经网络解析。
- Codex 仅处理本机 Quality Gate 无法可靠解决的局部文本或疑难页面。
- 本地 MCP Server **不得调用任何 AI API**。

## 顶层目录

```text
design/       详细设计、接口契约、架构决策
development/  开发计划、任务指令、实现交付记录
acceptance/   验收计划、验收指令、验收证据
src/          生产代码（后续开发阶段实现）
tests/        单元、集成、golden、性能测试
.agents/      Codex Skill（后续阶段）
```

## 当前阶段

**PROJECT_BOOTSTRAP / DESIGN_BASELINE**

当前仅完成项目初始化与详细设计准备，不代表生产代码已实现，也不代表任何功能已验收。
