# FFDF MCP Report-Safe Interface v1

## 目的

在不修改 P3/P5/P6/P7 解析产物、不破坏既有 11 个 MCP 工具的前提下，增加面向研究报告生成的只读接口，降低以下错误：

- 把正确的产品行重新组合成错误的“逆变器收入”或“新能源收入”；
- 使用旧年度报告中的“拟分红”状态，而忽略后续 H1/Q3 已披露的新状态；
- 搜索“关键审计事项”后只读取命中页，漏掉跨页的下一项；
- 将“外销”擅自改写成“海外收入”等语义扩大；
- 在最终报告中无法说明数值来自直接披露还是二次计算。

## 兼容性原则

1. 原有 11 个 P8 MCP 工具名称、参数和返回结构保持不变。
2. 新接口为向后兼容扩展，不修改 P3/P5/P6/P7 artifact。
3. 新接口只做确定性查询、排序、上下文扩展和源标签保留，不引入 AI 语义推断。
4. 新接口不得把“最新定期报告”自动解释为“最新临时公告状态”；如当前目录仅含定期报告，必须显式暴露这一限制。

## 新增接口

### ffdf_get_company_report_context

输入：market、ticker，可选 fiscal_year_from / fiscal_year_to。

输出：
- 公司全部已入库定期报告，按研究使用顺序（最新优先）排列；
- 每份报告的 validation_status、blocking/review/warning 数量；
- latest_filing；
- report_guardrails：
  - direct_disclosure_preferred
  - preserve_source_labels
  - newer_filing_state_overrides_older_filing_state
  - section_search_requires_neighbor_context
  - derived_values_must_declare_components
- chronology_basis 与 limitations。

用途：报告开始前先获取完整研究上下文，避免只看最新一份或沿用旧状态。

### ffdf_search_company

输入：market、ticker、query，可选年份范围、每份报告命中数、报告数、page_window。

行为：
- 对同一公司全部报告执行本地 P3 FTS；
- 按最新报告优先；
- 对每个命中自动附带前后页面窗口；
- 返回命中文档的 fiscal_year / filing_type / validation 状态。

用途：
- 分红、经营计划、关键审计事项等跨期检索；
- 避免只读一个命中页造成跨页遗漏；
- 让报告生成器看到较新的披露并覆盖旧状态。

### ffdf_find_table_rows

输入：market、ticker、label、match_mode(exact/contains)，可选年份、filing_type、limit。

行为：
- 在公司 P5 重建表中直接按“源表行标签”搜索；
- 返回原始 disclosure_label、整行 cells、page_no、table_id、filing identity；
- exact 命中优先于 contains；
- 明确 direct_disclosure=true。

用途：
- 优先使用公司直接披露的“新能源行业”“外销”等行；
- 防止 AI 自行把多个产品重新拼成一个未经披露的聚合指标；
- 保留源标签，避免“外销→海外”等语义扩大。

## 605117 验收场景

1. 搜索 label=新能源行业，必须直接返回 2025FY P5 行 10,180,522,048.26。
2. 搜索 label=外销，必须保留 disclosure_label=外销，不改写为海外收入。
3. 搜索 query=利润分配，应优先看到 2026H1 中关于 2025 年度利润分配已通过/实施的信息，而不是停留在 2025FY 的拟分红状态。
4. 搜索 query=关键审计事项 且 page_window=1，应包含 2025FY p105 与相邻 p106，从而同时覆盖收入确认与应收账款减值。
5. MCP 必须明确：当前 catalog 若未包含临时公告，不能据此证明 2026H1 分红在 2026-10 的最终实施状态。
