# 102 — R-B Trusted Source Resolver Evidence

## 目标

只允许通过 document_sha256 解析 FFDF 已登记的原始 PDF，不允许 caller 传入任意 filesystem path。

## 实现

- 新增 `mcp/trusted_source.py`
- P3 document.json 只提供候选 source_path
- Registry 必须确认该 path 绑定到相同 document_sha256
- source 必须位于 configured trusted raw-store root
- 实时校验 file_size、SHA256、PDF 可打开性、page_count
- public metadata 不返回 path/source_path
- Registry 文件不存在时 fail closed，不创建空数据库

## 验证

`tests/unit/mcp/test_trusted_source.py`：

- registered immutable PDF resolves
- outside trusted root rejected
- SHA drift rejected
- unregistered path rejected
- unknown document rejected

结果：5 PASS。

605117 live source 使用：
`workspace/ingest/raw-store/sha256/.../<sha>.pdf`

R-B：PASS。
