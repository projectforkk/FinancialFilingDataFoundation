# FFDF 用户命令行：下载、解析与入库

适用范围：CN / HK
项目根目录：D:\Codex\FinancialFilingDataFoundation

## 1. 一次性启用 ffdf 命令

打开 PowerShell：

~~~powershell
Set-Location D:\Codex\FinancialFilingDataFoundation
powershell -ExecutionPolicy Bypass -File .\scripts\install-user-cli.ps1
~~~

关闭当前 PowerShell，重新打开一个窗口。

验证：

~~~powershell
ffdf --help
~~~

如果不想修改 User PATH，也可以始终从项目根目录直接使用：

~~~powershell
.\ffdf.cmd --help
~~~

卸载 PATH 入口：

~~~powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install-user-cli.ps1 -Remove
~~~

## 2. 只下载财报

标准命令：

~~~powershell
ffdf acquire --market CN --ticker 600519 --year 2026 --period Q3
~~~

系统自动完成：

1. 构造 canonical filing identity；
2. 检查本地 Registry；
3. 已存在则返回 REUSED_LOCAL；
4. 运行 Dayu doctor；
5. 从 CNINFO/HKEX 查询官方候选；
6. 精确匹配 ticker/year/period；
7. 下载 PDF 到 staging；
8. 验证 PDF、size、SHA256；
9. 写入 content-addressed Raw Store；
10. 写入 Registry；
11. 保存 Acquisition Receipt。

只下载不会运行 P3-P7。

### 香港示例

~~~powershell
ffdf acquire --market HK --ticker 00700 --year 2024 --period FY
~~~

## 3. 下载并完整解析入库

标准命令：

~~~powershell
ffdf ingest --market CN --ticker 600519 --year 2026 --period Q3
~~~

自动执行：

~~~text
Acquire
  -> Raw Store
  -> Registry
  -> P3 Native Page / Section / FTS
  -> P4 Table Candidate
  -> P5 Table Reconstruction
  -> P6 Raw Fact + Evidence
  -> P7 Validation
  -> Parsed Registry
  -> P8 MCP Catalog
~~~

P8 Catalog 只有在 P7 blocking_issue_count == 0 时才登记。

因此：

- PASS + blocking=0：Research Ready；
- REVIEW_REQUIRED + blocking=0：Research Ready，但保留 review 边界；
- blocking > 0：解析记录保留在 Registry，不进入 P8 live catalog。

## 4. 查看状态

~~~powershell
ffdf status --market CN --ticker 600519 --year 2026 --period Q3
~~~

会显示：

- Raw 是否已经存在；
- document SHA256；
- Raw 文件路径；
- Parsed runs；
- validation status；
- blocking issue count；
- 是否已经加入 P8 MCP Catalog。

## 5. 支持的期间

| 参数 | 含义 |
|---|---|
| Q1 | 一季度 |
| H1 | 半年度 |
| Q3 | 三季度 |
| FY | 年度 |

当前没有 Q2 参数。

## 6. 公告搜索窗口

财报所属期间与公告发布时间是两个概念。

如果不指定窗口，CLI 自动使用：

| Period | 默认公告搜索窗口 |
|---|---|
| Q1 | 当年 03-01 ～ 05-31 |
| H1 | 当年 06-01 ～ 09-30 |
| Q3 | 当年 09-01 ～ 11-30 |
| FY | 下一年 01-01 ～ 06-30 |

若默认结束日在未来，会自动截到当前日期。

需要覆盖默认窗口时，必须同时指定。最简单可靠的方式是直接写成一行：

~~~powershell
ffdf acquire --market CN --ticker 600519 --year 2026 --period Q3 --window-start 2026-10-01 --window-end 2026-11-05
~~~

解析入库：

~~~powershell
ffdf ingest --market CN --ticker 600519 --year 2026 --period Q3 --window-start 2026-10-01 --window-end 2026-11-05
~~~

## 7. 数据保存位置

用户 CLI 的持久数据放在：

~~~text
workspace/ingest/
~~~

主要包括：

~~~text
workspace/ingest/
  raw-store/
  registry.sqlite
  acquisition-workspace/
  cn/
    p3/
    p4/
    p5/
    p6/
    p7/
  hk/
    p3/
    p4/
    p5/
    p6/
    p7/
~~~

研究入口仍然是：

~~~text
workspace/mcp/p8-live-catalog.json
~~~

## 8. 常见返回状态

Acquisition：

- DOWNLOADED：新下载成功；
- REUSED_LOCAL：本地已有，未重复下载；
- NOT_FOUND：官方源未发现精确候选；
- REVIEW_REQUIRED：候选冲突/歧义，需要检查；
- BLOCKED：本地状态冲突或 drift。

Ingest 最终 JSON 会列出：

- acquisition_status；
- P3 page_count；
- P4 candidate_count；
- P5 table_count；
- P6 fact_count/evidence_count；
- P7 validation_status；
- blocking/review/warning issue count；
- Registry 状态；
- P8 Catalog 状态；
- research_ready。

## 9. 最常用的三条命令

只下载：

~~~powershell
ffdf acquire --market CN --ticker 600519 --year 2026 --period Q3
~~~

下载并解析入库：

~~~powershell
ffdf ingest --market CN --ticker 600519 --year 2026 --period Q3
~~~

查看状态：

~~~powershell
ffdf status --market CN --ticker 600519 --year 2026 --period Q3
~~~
