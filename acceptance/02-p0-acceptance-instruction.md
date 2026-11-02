# 02 — P0 Independent Acceptance Instruction

任务：Native PDF Parsing Feasibility Probe

## 输入

使用开发提交指定的代表性 PDF，优先：
600519 / 贵州茅台 FY2024 / 143 pages。

## 验收步骤

1. 核对 Git commit 与设计基线。
2. 核对环境审计。
3. 运行 focused tests。
4. 运行 probe。
5. 检查 JSON schema。
6. 确认 page_count 与已知 PDF 一致。
7. 确认没有 OCR / Torch / Docling / TableFormer / external AI API。
8. 检查阶段计时。
9. 检查是否存在异常页 / warning，禁止静默吞错。
10. 重跑一次，确认输出字段稳定且无源文件修改。

## P0 PASS 条件

- probe 可完成；
- page_count 正确；
- SHA 稳定；
- 143 页全部被枚举；
- native text / word / block 等统计可得；
- no heavy path；
- total native probe <= 120s；
- 无 blocker；
- tests PASS。

## FAIL

任一：
- page count 错误；
- 解析中触发 OCR/Docling；
- >120s；
- 结果 schema 不稳定；
- 源 PDF 被修改；
- tests fail。

## BLOCKED

仅当：
- 代表 PDF 不可访问；
- 运行环境缺少设计批准的必要依赖且无法按 policy 使用；
- 外部系统不可用导致无法完成验收，但代码本身不可判定。

## 输出格式

只给一个最终 verdict：
`PASS` / `FAIL` / `BLOCKED`

并附最小证据摘要。
