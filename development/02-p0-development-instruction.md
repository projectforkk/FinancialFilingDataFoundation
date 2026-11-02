# 02 — P0 Development Instruction

任务：Native PDF Parsing Feasibility Probe

设计基线：
- `design/01-project-detailed-design.md`
- `design/04-pdf-quality-gate-design.md`
- `development/01-development-roadmap.md`

## 开发者角色

只实现 P0 probe。
不得提前实现 P1+。

## 开始前必须完成 PC 环境审计

记录：
- OS
- CPU / architecture
- Python executable
- Python version
- Python architecture
- pip/uv
- PyMuPDF 是否已存在
- pypdf 是否已存在
- Dayu 环境位置（只记录，不依赖）
- Git
- Codex

现有工具兼容则复用；不得为了 P0 擅自升级系统 Python。

## P0 产物

建议：
`src/financial_filing_data_foundation/probes/native_pdf_probe.py`

输出 JSON 必须至少包含：

```json
{
  "file": "...",
  "sha256": "...",
  "file_size": 0,
  "page_count": 0,
  "timings_ms": {
    "open": 0,
    "text": 0,
    "layout": 0,
    "drawings_images": 0,
    "table_candidate_signals": 0,
    "total": 0
  },
  "totals": {
    "native_chars": 0,
    "words": 0,
    "blocks": 0,
    "drawings": 0,
    "images": 0
  },
  "pages": []
}
```

每页至少：
- page_no
- native_char_count
- word_count
- block_count
- drawing_count
- image_count
- width / height / rotation
- cheap table candidate signals
- elapsed_ms

## 禁止

- OCR
- Torch
- Docling
- TableFormer
- external AI API
- Codex vision
- 修改原 PDF

## 测试

单元：
- valid tiny PDF
- empty-text/image-only page
- rotated page
- malformed-but-openable fixture（若可安全构造）
- deterministic JSON schema

性能：
- 600519 FY2024 代表文件

## 开发者回执

必须提交：
- environment audit
- commit SHA
- exact command
- exact timings
- exact page count
- errors/warnings
- no-OCR/no-AI/no-Docling assertion
