# 10 — P3 Native Page / Section / FTS 详细设计

状态：**DESIGN BASELINE — P3**

前置：
- P0 DONE / PASS
- P1 DONE / PASS
- P2 DONE / PASS
- accepted P2 merge commit: `4add9fff36b61e2521e9c8d749cee829adb4ab6f`

## 1. 目标

P3 对已注册的 CN/HK raw PDF 建立确定性 native document layer：

```text
Original PDF
→ document preflight
→ native page geometry
→ words / blocks / lines / spans / fonts / bbox
→ deterministic reading order
→ section heading candidates
→ section tree
→ page/section FTS5
→ P3 artifact
```

P3 不做 table candidate/reconstruction、OCR、Docling、facts/evidence、质量最终判定、MCP/Skill。

## 2. 输入

`parse_native_document(pdf_path, artifact_root)`

输入必须是本地 PDF path。调用者负责 filing identity；P3 只以 document SHA256 作为 raw-byte identity。

## 3. Source immutability

执行前后记录：
- SHA256
- size
- mtime_ns

任一变化 → `SOURCE_CHANGED_DURING_PARSE`，不得产出成功 artifact。

## 4. Document contract

`NativeDocumentArtifact`：
- schema_version = `p3-native-document-v1`
- document_sha256
- file_size
- page_count
- parser_version
- source_path
- pages_path
- sections_path
- search_db_path
- timings_ms
- warnings

artifact layout：

```text
<artifact_root>/<sha>/
  document.json
  pages.jsonl
  sections.jsonl
  search.sqlite
```

写入必须 staging + atomic replace；不得半成品冒充成功 artifact。

已存在 artifact 的 reuse 也必须先验证 completeness：
- `document.json`
- `pages.jsonl`
- `sections.jsonl`
- `search.sqlite`
均必须存在；manifest 的 schema/parser/source SHA 必须匹配；`search.sqlite` metadata 中的 document SHA/schema 必须匹配 manifest。任何缺失/冲突 → `ARTIFACT_INCOMPLETE_OR_CORRUPT`，不得返回成功 artifact。

## 5. Page contract

每页至少：
- page_no (1-based)
- width / height
- rotation
- native_text_available
- native_char_count
- word_count
- block_count
- line_count
- span_count
- image_count
- drawing_count
- text
- words
- blocks
- warnings

Word：
- text
- bbox [x0,y0,x1,y1]
- block_no
- line_no
- word_no

Span：
- text
- bbox
- font
- size
- flags
- color
- ascender/descender when available
- origin when available

Text block：
- block_no
- bbox
- type
- lines
- reading_order_index

P3 不丢弃原始 block/line/span identity。

### 5.1 Native text extraction flags

P3 的 `DICT` 只用于 text block / line / span layout，**不得保留 image binary payload**。

PyMuPDF extraction 必须使用等价于：

```python
text_flags = pymupdf.TEXTFLAGS_DICT & ~pymupdf.TEXT_PRESERVE_IMAGES
text_page = page.get_textpage(flags=text_flags)
page.get_text("words", textpage=text_page, sort=False)
page.get_text("dict", textpage=text_page, sort=False)
```

image metadata/count 继续由 `page.get_images(full=True)` 单独获取。

`drawing_count` 只需要 count，不需要完整 Python drawing object contract；优先使用 compact `page.get_cdrawings()`，避免不必要对象构造。

image-only page 在 text-only DICT 中没有 text block 是正确语义，必须表现为 `native_text_available=false / PAGE_TEXT_EMPTY`，不能把 image payload 当 native text。

## 6. BBox

所有 bbox：
- finite
- x1 >= x0 / y1 >= y0
- clamp 到 page rect 时必须记录 `BBOX_CLAMPED`
- invalid bbox 不能静默修造，记录 warning 并排除该元素的几何推理

坐标保持 PyMuPDF page coordinate system；P3 不做视觉旋转后坐标重映射。

## 7. Reading order

P3 不把 `get_text("text")` 当唯一 reading order。

Text block 的 deterministic order：
1. top band / y0
2. x0
3. original block_no

行内 span 保持 native line/span 顺序。

同时保留：
- original block_no
- reading_order_index

多栏文档在 P3 只提供稳定 local order；复杂多栏语义可进入后续 quality/review，不允许猜造逻辑顺序。

## 8. Heading candidate

Heading 基于 block/line/span layout signals，不依赖 AI。

signals：
- numbering pattern
- short line/block
- font size relative to page/body median
- bold flags/font name
- whitespace isolation
- known generic structural patterns（目录、章节编号等）

禁止仅凭单一大字体判 heading。

## 9. Heading numbering

至少识别：
- `第X章 / 第X节`
- 中文数字 + `、`
- Arabic `1.`, `1.1`, `1.1.1`
- parenthesized `（一）`, `(1)`

编号可提供显式 level candidate。

无编号 heading：
- 根据文档全局 font-size rank + layout signals 推导 level candidate
- 低信号不进入 section tree

## 10. Section contract

至少：
- section_id
- parent_section_id nullable
- raw_title
- normalized_title nullable（P3 默认 null，不做 canonical mapping）
- level
- page_start
- page_end
- bbox
- heading_score
- heading_signals
- quality_signals

`section_id = SHA256(document_sha256 + "\0" + page_no + "\0" + bbox + "\0" + raw_title)`

Section tree 通过 heading level stack deterministic 构造。

page_end：
- 下一同级/更高层 section 开始页之前；
- 最后一节到 document page_count；
- page_end >= page_start。

## 11. Repeated headers/footers

P3 必须检测跨页高频顶部/底部短文本：
- 出现在 >= 30% 页面（且至少 3 页）
- 位于 page top 12% 或 bottom 12%

标记为 repeated_header_footer，不作为 section heading。

页码等纯数字 footer 优先排除。

## 12. FTS5

使用 stdlib sqlite3 FTS5。

`search.sqlite` 至少：
- metadata(document_sha256, schema_version)
- page_content(page_no PRIMARY KEY, text)
- page_fts USING fts5(text, content='page_content', content_rowid='page_no')
- sections(section_id PRIMARY KEY, title, page_start, page_end)
- section_fts USING fts5(section_id UNINDEXED, title)

P3 提供：
- `search_pages(query, limit)`
- `search_sections(query, limit)`

FTS query 必须参数化；不得字符串拼 SQL。

若 host SQLite 无 FTS5 → `FTS5_UNAVAILABLE` / BLOCKED，不 silent fallback。

## 13. Artifact determinism

相同：
- source SHA
- PyMuPDF version
- parser_version
- config

除 timings 外：
- pages.jsonl
- sections.jsonl
- search result ordering

必须确定性。

JSON：
- UTF-8 no BOM
- stable key order
- JSONL record separator **只能是 ASCII LF (`0x0A`)**
- one JSON object per LF-delimited record
- 字符串中的 Unicode line-separator code points（至少 U+0085 / U+2028 / U+2029）必须序列化为 `\\u0085` / `\\u2028` / `\\u2029` 转义序列，禁止原样写入造成 record boundary ambiguity
- reader 以 LF record boundary 读取；不能依赖 Python `str.splitlines()` 对所有 Unicode line separators 的扩展语义

## 14. Parser version

`P3_PARSER_VERSION = "p3-native-page-section-v1"`

任何会改变 page/section semantics 的规则变化先设计并 bump parser version。

## 15. Performance

代表样本：
- CN 600519 FY2024 / 143 pages
- HK 00700 FY2024

P3 初始性能 Gate：
- each born-digital sample total <= 30s
- no OCR
- no Docling
- no external AI

先用实测再决定是否收紧。

## 16. Warnings / errors

至少：
- PDF_OPEN_FAILED
- PDF_ENCRYPTED_UNSUPPORTED
- PAGE_TEXT_EMPTY
- INVALID_BBOX
- BBOX_CLAMPED
- READING_ORDER_SUSPECT
- FTS5_UNAVAILABLE
- SOURCE_CHANGED_DURING_PARSE
- ARTIFACT_WRITE_FAILED

P3 warning 不等于 P7 final validation。

## 17. API

```python
parse_native_document(
    pdf_path: Path,
    artifact_root: Path,
) -> NativeDocumentArtifact

load_native_document(artifact_dir) -> NativeDocumentArtifact

search_pages(search_db, query, limit=10)
search_sections(search_db, query, limit=10)
```

## 18. Tests

至少覆盖：
1. 2-page born-digital PDF
2. blank page
3. image-only page
4. rotated page
5. words/blocks/spans/bbox
6. deterministic reading order
7. Chinese numbered headings
8. Arabic nested headings
9. repeated header/footer excluded
10. section parent hierarchy
11. page_end
12. deterministic section_id
13. FTS page search
14. FTS section search
15. SQL parameterization behavior
16. source immutability
17. repeated parse non-timing artifact determinism
18. malformed/openable PDF
19. P0/P1/P2 regression

## 19. Live integration

对 accepted P2 raw：
- CN SHA `5299f494...`
- HK SHA `70f52998...`

验证：
- page count
- pages.jsonl completeness
- section tree non-empty when headings found
- FTS search
- source unchanged
- <=30s

P3 不把“section count 越多越好”作为正确性标准。

## 20. Exit

只有 Independent Acceptance PASS：
- P3 DONE
- merge accepted candidate to main
- 才允许 P4 Table Candidate Detection implementation。

## 21. Issue rule

任何问题：
STOP → root cause → design update → commit baseline → rerun affected Gate → continue。
