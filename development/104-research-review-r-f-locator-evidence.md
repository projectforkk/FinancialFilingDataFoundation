# 104 — R-F Missing-Fact / Evidence Locator Evidence

## 实现

`ffdf_locate_evidence` 使用：

1. P3 FTS
2. casefold literal page scan
3. matched P3 page
4. same-page P5 tables
5. same-page P6 facts
6. recommended table/page visual targets

Locator hit 只是 evidence candidate，不创建 RawFact。

若 PDF 明确存在披露而 P6 无对应事实：
`P6_MISSING_FACT_CANDIDATE → UPSTREAM_FIX`

## 验证

unit locator test：
- page candidate
- table candidate
- RawFact candidate
- recommended TABLE visual target
- no durable mutation

605117 2025FY live：
query = `关键审计事项`
命中 page 105、106，证明跨页 KAM context 可定位。

R-F：PASS。
