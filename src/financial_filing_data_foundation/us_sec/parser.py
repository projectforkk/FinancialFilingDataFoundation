from __future__ import annotations

import hashlib
import io
import json
import os
import re
import shutil
import uuid
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote

from .errors import P11Reason, SecError
from .package import SecFilingPackage, SecMemberRole


SEC_ARTIFACT_SCHEMA = "p11-sec-artifacts-v1"
VIRTUAL_HTML_NORMALIZER_VERSION = "VIRTUAL_HTML_V3"
_MAX_BLOCKS_PER_PAGE = 48
_MAX_CHARS_PER_PAGE = 6000


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _jsonl_record(row: dict[str, Any]) -> str:
    return json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(_jsonl_record(row) + "\n")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    item = json.loads(line)
                    if not isinstance(item, dict):
                        raise ValueError("JSONL row is not an object")
                    rows.append(item)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise SecError(P11Reason.P11_HTML_PARSE_FAILED, f"SEC artifact JSONL is invalid: {path.name}") from exc
    return rows


@dataclass
class _Node:
    tag: str
    attrs: dict[str, str]
    parent: "_Node | None"
    order: int
    locator: str = ""
    sibling_index: int = 0
    children: list["_Node"] = field(default_factory=list)
    data: list[str] = field(default_factory=list)
    content: list[object] = field(default_factory=list)


class _DomParser(HTMLParser):
    def __init__(self, *, locator_targets: set[str] | None = None) -> None:
        super().__init__(convert_charrefs=True)
        self.root = _Node("#document", {}, None, 0)
        self._stack = [self.root]
        self._order = 0
        self._locator_targets = locator_targets
        self._locator_prefixes: set[str] = set()
        if locator_targets is not None:
            for target in locator_targets:
                prefix = ""
                for component in str(target).strip("/").split("/"):
                    if not component:
                        continue
                    prefix += f"/{component}"
                    self._locator_prefixes.add(prefix)
        self._child_indexes: dict[int, dict[str, int]] = {}
        self.locator_index: dict[str, _Node] = {}

    def _attrs(self, attrs: list[tuple[str, str | None]]) -> dict[str, str]:
        return {str(key).casefold(): "" if value is None else str(value) for key, value in attrs}

    def _start(self, tag: str, attrs: list[tuple[str, str | None]], *, push: bool) -> None:
        self._order += 1
        normalized_tag = tag.casefold()
        parent = self._stack[-1]
        indexes = self._child_indexes.setdefault(id(parent), {})
        child_index = indexes.get(normalized_tag, 0) + 1
        indexes[normalized_tag] = child_index
        if self._locator_targets is None:
            locator = ""
        else:
            candidate = f"{parent.locator}/{normalized_tag}[{child_index}]" if parent.locator else f"/{normalized_tag}[{child_index}]"
            locator = candidate if candidate in self._locator_prefixes else ""
        node = _Node(
            normalized_tag,
            self._attrs(attrs),
            parent,
            self._order,
            locator,
            child_index,
        )
        parent.children.append(node)
        parent.content.append(node)
        if self._locator_targets is not None and locator in self._locator_targets:
            self.locator_index[locator] = node
        if push:
            self._child_indexes.setdefault(id(node), {})
            self._stack.append(node)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._start(tag, attrs, push=tag.casefold() not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"})

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._start(tag, attrs, push=False)

    def handle_endtag(self, tag: str) -> None:
        target = tag.casefold()
        if len(self._stack) > 1 and self._stack[-1].tag == target:
            self._stack.pop()
            return
        for index in range(len(self._stack) - 1, 0, -1):
            if self._stack[index].tag == target:
                del self._stack[index:]
                return

    def handle_data(self, data: str) -> None:
        self._stack[-1].data.append(data)
        self._stack[-1].content.append(data)


def _local(tag: str) -> str:
    return tag.rsplit(":", 1)[-1].casefold()


def _attr(node: _Node, name: str) -> str | None:
    return node.attrs.get(name.casefold())


def _attr_local(node: _Node, name: str) -> str | None:
    wanted = name.casefold()
    for key, value in node.attrs.items():
        if key.casefold() == wanted or key.rsplit(":", 1)[-1].casefold() == wanted:
            return value
    return None


def _text(node: _Node) -> str:
    if node.content:
        values = [item if isinstance(item, str) else _text(item) for item in node.content]
        return " ".join(" ".join(values).split())
    values: list[str] = []
    values.extend(node.data)
    for child in node.children:
        child_text = _text(child)
        if child_text:
            values.append(child_text)
    return " ".join(" ".join(values).split())


def _text_cached(node: _Node, cache: dict[int, str]) -> str:
    cached = cache.get(id(node))
    if cached is not None:
        return cached
    if node.content:
        values = [item if isinstance(item, str) else _text_cached(item, cache) for item in node.content]
        value = " ".join(" ".join(values).split())
    else:
        values = list(node.data)
        for child in node.children:
            child_text = _text_cached(child, cache)
            if child_text:
                values.append(child_text)
        value = " ".join(" ".join(values).split())
    cache[id(node)] = value
    return value


def _is_hidden(node: _Node) -> bool:
    current: _Node | None = node
    while current is not None:
        if _local(current.tag) in {"script", "style", "header", "hidden"} or current.tag in {"ix:header", "ix:hidden"}:
            return True
        aria_hidden = _attr(current, "aria-hidden")
        if _attr(current, "hidden") is not None or (aria_hidden is not None and aria_hidden.casefold() == "true"):
            return True
        style = re.sub(r"\s+", "", _attr(current, "style") or "").casefold()
        classes = (_attr(current, "class") or "").casefold().split()
        if "display:none" in style or "visibility:hidden" in style or "hidden" in classes:
            return True
        current = current.parent
    return False


def _is_hidden_cached(node: _Node, cache: dict[int, bool]) -> bool:
    key = id(node)
    cached = cache.get(key)
    if cached is not None:
        return cached
    chain: list[_Node] = []
    current: _Node | None = node
    result = False
    while current is not None:
        current_cached = cache.get(id(current))
        if current_cached is not None:
            result = current_cached
            break
        chain.append(current)
        if _local(current.tag) in {"script", "style", "header", "hidden"} or current.tag in {"ix:header", "ix:hidden"}:
            result = True
            break
        aria_hidden = _attr(current, "aria-hidden")
        if _attr(current, "hidden") is not None or (aria_hidden is not None and aria_hidden.casefold() == "true"):
            result = True
            break
        style = re.sub(r"\s+", "", _attr(current, "style") or "").casefold()
        classes = (_attr(current, "class") or "").casefold().split()
        if "display:none" in style or "visibility:hidden" in style or "hidden" in classes:
            result = True
            break
        current = current.parent
    for item in reversed(chain):
        cache[id(item)] = result
    return result


def _visible_text(node: _Node) -> str:
    if _is_hidden(node):
        return ""
    if node.content:
        values = [item if isinstance(item, str) else _visible_text(item) for item in node.content]
        return " ".join(" ".join(values).split())
    values = list(node.data)
    for child in node.children:
        child_text = _visible_text(child)
        if child_text:
            values.append(child_text)
    return " ".join(" ".join(values).split())


def _visible_text_cached(
    node: _Node,
    text_cache: dict[int, str],
    hidden_cache: dict[int, bool],
) -> str:
    key = id(node)
    cached = text_cache.get(key)
    if cached is not None:
        return cached
    if _is_hidden_cached(node, hidden_cache):
        text_cache[key] = ""
        return ""
    if node.content:
        values = [
            item if isinstance(item, str) else _visible_text_cached(item, text_cache, hidden_cache)
            for item in node.content
        ]
    else:
        values = list(node.data)
        values.extend(
            child_text
            for child in node.children
            if (child_text := _visible_text_cached(child, text_cache, hidden_cache))
        )
    value = " ".join(" ".join(values).split())
    text_cache[key] = value
    return value


def _descendants(node: _Node) -> Iterable[_Node]:
    for child in node.children:
        yield child
        yield from _descendants(child)


def _path(node: _Node) -> str:
    if node.locator:
        return node.locator
    chain: list[tuple[_Node, int]] = []
    current: _Node | None = node
    while current is not None and current.tag != "#document":
        if current.parent is None:
            index = 1
        elif current.sibling_index:
            index = current.sibling_index
        else:
            index = 0
            for child in current.parent.children:
                if child.tag != current.tag:
                    continue
                index += 1
                if child is current:
                    break
        chain.append((current, index))
        current = current.parent
    prefix = ""
    for item, index in reversed(chain):
        prefix += f"/{item.tag}[{index}]"
        if not item.locator:
            item.locator = prefix
    return node.locator


def _under(node: _Node, tags: set[str]) -> bool:
    current = node.parent
    while current is not None:
        if _local(current.tag) in tags or current.tag in tags:
            return True
        current = current.parent
    return False


def _int_attr(node: _Node, name: str, default: int = 1) -> int:
    value = _attr(node, name)
    try:
        return max(1, int(value)) if value is not None else default
    except ValueError:
        return default


def _node_page(node: _Node, page_by_locator: dict[str, int]) -> int:
    current: _Node | None = node
    while current is not None:
        page = page_by_locator.get(_path(current))
        if page is not None:
            return page
        current = current.parent
    return 1


def _resolve_dom_locator(root: _Node, locator: str) -> _Node | None:
    if not isinstance(locator, str) or not locator.startswith("/"):
        return None
    current = root
    for component in locator.strip("/").split("/"):
        match = re.fullmatch(r"(.+)\[(\d+)\]", component)
        if match is None:
            return None
        tag, raw_index = match.groups()
        index = int(raw_index)
        matching = [child for child in current.children if child.tag == tag]
        if index < 1 or index > len(matching):
            return None
        current = matching[index - 1]
    return current


def _index_dom_locators(root: _Node) -> dict[str, _Node]:
    """Build the canonical DOM-path index once for repeated evidence checks."""

    index: dict[str, _Node] = {}

    def visit(parent: _Node, prefix: str) -> None:
        sibling_indexes: dict[str, int] = {}
        for child in parent.children:
            child_index = sibling_indexes.get(child.tag, 0) + 1
            sibling_indexes[child.tag] = child_index
            locator = child.locator or f"{prefix}/{child.tag}[{child_index}]"
            index[locator] = child
            visit(child, locator)

    visit(root, "")
    return index


def _source_block_for_node(
    node: _Node,
    blocks_by_locator: dict[str, dict[str, Any]],
    blocks_by_prefix: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    current: _Node | None = node
    while current is not None:
        block = blocks_by_locator.get(_path(current))
        if block is not None:
            return block
        current = current.parent
    node_locator = _path(node)
    if blocks_by_prefix is not None:
        return blocks_by_prefix.get(node_locator)
    else:
        prefix = node_locator + "/"
        descendants = [
            block
            for locator, block in blocks_by_locator.items()
            if locator.startswith(prefix)
        ]
    if descendants:
        return min(
            descendants,
            key=lambda block: (len(str(block.get("dom_locator", ""))), int(block.get("source_order_index", 0))),
        )
    return None


def _xml_namespace_map(body: bytes) -> dict[str, str]:
    namespaces: dict[str, str] = {}
    try:
        for _, value in ET.iterparse(io.BytesIO(body), events=("start-ns",)):
            prefix, uri = value
            namespaces.setdefault(str(uri), str(prefix))
    except ET.ParseError:
        return {}
    return namespaces


def _xml_tag_label(tag: str) -> str:
    text = str(tag)
    if text.startswith("{") and "}" in text:
        uri, local = text[1:].split("}", 1)
        return "{" + quote(uri, safe="") + "}" + local
    return text


def _xml_qname(tag: str, namespaces: dict[str, str]) -> str:
    text = str(tag)
    if not text.startswith("{") or "}" not in text:
        return text
    uri, local = text[1:].split("}", 1)
    prefix = namespaces.get(uri)
    return f"{prefix}:{local}" if prefix else local


def _xml_walk(root: ET.Element) -> Iterable[tuple[ET.Element, str]]:
    def walk(node: ET.Element, locator: str) -> Iterable[tuple[ET.Element, str]]:
        yield node, locator
        counts: dict[str, int] = {}
        for child in list(node):
            label = _xml_tag_label(str(child.tag))
            counts[label] = counts.get(label, 0) + 1
            yield from walk(child, f"{locator}/{label}[{counts[label]}]")

    root_label = _xml_tag_label(str(root.tag))
    yield from walk(root, f"/{root_label}[1]")


def _resolve_xml_locator(root: ET.Element, locator: str) -> ET.Element | None:
    if not isinstance(locator, str) or not locator.startswith("/"):
        return None
    current = root
    components = locator.strip("/").split("/")
    if not components:
        return None
    first = re.fullmatch(r"(.+)\[(\d+)\]", components[0])
    if first is None or first.group(1) != _xml_tag_label(str(current.tag)) or int(first.group(2)) != 1:
        return None
    for component in components[1:]:
        match = re.fullmatch(r"(.+)\[(\d+)\]", component)
        if match is None:
            return None
        tag, raw_index = match.groups()
        index = int(raw_index)
        matching = [child for child in list(current) if _xml_tag_label(str(child.tag)) == tag]
        if index < 1 or index > len(matching):
            return None
        current = matching[index - 1]
    return current


def _xml_text(element: ET.Element) -> str:
    return " ".join(" ".join(element.itertext()).split())


def _xml_attr_local(element: ET.Element, name: str) -> str | None:
    wanted = name.casefold()
    for key, value in element.attrib.items():
        text = str(key)
        if text.casefold() == wanted or text.rsplit("}", 1)[-1].rsplit(":", 1)[-1].casefold() == wanted:
            return str(value)
    return None


def _numeric_candidate(raw_value: str) -> str | None:
    numeric_text = raw_value.strip().replace(",", "")
    if not re.fullmatch(r"\(?[+-]?\d+(?:\.\d+)?\)?", numeric_text):
        return None
    if numeric_text.startswith("(") and numeric_text.endswith(")"):
        return "-" + numeric_text[1:-1]
    return numeric_text


@dataclass(frozen=True, slots=True)
class SecParseResult:
    artifact_dir: Path
    package_sha256: str
    parser_version: str
    pages: tuple[dict[str, Any], ...]
    sections: tuple[dict[str, Any], ...]
    tables: tuple[dict[str, Any], ...]
    facts: tuple[dict[str, Any], ...]
    evidence: tuple[dict[str, Any], ...]
    issues: tuple[dict[str, Any], ...]

    @property
    def document_sha256(self) -> str:
        return self.package_sha256


def _primary_member(package: SecFilingPackage) -> tuple[Any, str]:
    members = [member for member in package.members if member.role is SecMemberRole.PRIMARY_DOCUMENT]
    if len(members) != 1:
        raise SecError(P11Reason.P11_PRIMARY_DOCUMENT_MISSING, "SEC package must contain exactly one primary document")
    member = members[0]
    try:
        text = member.body.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise SecError(P11Reason.P11_HTML_PARSE_FAILED, "SEC primary HTML is not valid UTF-8") from exc
    return member, text


def _is_inline_wrapper(node: _Node) -> bool:
    if node.tag not in {"div", "span"}:
        return False
    style = re.sub(r"\s+", "", _attr(node, "style") or "").casefold()
    return re.search(r"(?:^|;)display:inline(?:;|$)", style) is not None


def _under_nested_inline_wrapper(node: _Node, structural_block_tags: set[str]) -> bool:
    current = node.parent
    while current is not None:
        if _is_inline_wrapper(current):
            outer = current.parent
            while outer is not None:
                if outer.tag in structural_block_tags and not _is_inline_wrapper(outer):
                    return True
                outer = outer.parent
            return False
        current = current.parent
    return False


def _blocks(root: _Node, member_sha: str) -> list[dict[str, Any]]:
    block_tags = {
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "p",
        "li",
        "caption",
        "td",
        "th",
        "title",
        "pre",
        "div",
        "section",
        "article",
        "blockquote",
        "dt",
        "dd",
        "tr",
        "span",
    }
    structural_block_tags = block_tags - {"span"}
    fact_tags = {"ix:nonfraction", "ix:nonnumeric"}
    candidates: list[_Node] = []
    visible_text_cache: dict[int, str] = {}
    hidden_cache: dict[int, bool] = {}
    for node in _descendants(root):
        if node.tag not in block_tags and node.tag not in fact_tags or _is_hidden_cached(node, hidden_cache):
            continue
        value = _visible_text_cached(node, visible_text_cache, hidden_cache)
        if not value:
            continue
        if _under_nested_inline_wrapper(node, structural_block_tags):
            continue
        if node.tag in fact_tags and any(ancestor.tag in structural_block_tags for ancestor in _ancestors(node)):
            # A fact inside a paragraph/cell/table block is anchored by that
            # surrounding source block; promoting the fact separately would
            # duplicate the narrative and destabilize evidence selection.
            continue
        # Inline spans are wrappers, not independent blocks when they live
        # under a structural block.  Let the parent retain direct narrative
        # text around inline spans and Inline-XBRL facts, while structural
        # child blocks still suppress the parent to avoid duplicate text.
        if node.tag == "span" and any(ancestor.tag in structural_block_tags for ancestor in _ancestors(node)):
            continue
        if any(
            child.tag in structural_block_tags
            and child.tag not in fact_tags
            and not _is_inline_wrapper(child)
            and _visible_text_cached(child, visible_text_cache, hidden_cache)
            for child in node.children
        ):
            continue
        candidates.append(node)
    candidates.sort(key=lambda node: node.order)
    blocks: list[dict[str, Any]] = []
    for index, node in enumerate(candidates):
        locator = _path(node)
        text = _visible_text_cached(node, visible_text_cache, hidden_cache)
        fragment = _sha256(f"{member_sha}|block|{locator}|{text}".encode())
        blocks.append(
            {
                "block_id": fragment,
                "source_member_sha256": member_sha,
                "dom_locator": locator,
                "text": text,
                "source_order_index": index,
                "fragment_sha256": fragment,
            }
        )
    return blocks


def _pages(blocks: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    pages: list[dict[str, Any]] = []
    page_by_locator: dict[str, int] = {}
    current: list[dict[str, Any]] = []
    chars = 0

    def flush() -> None:
        if not current:
            return
        page_no = len(pages) + 1
        text = "\n".join(str(row["text"]) for row in current)
        page = {
            "page_no": page_no,
            "pagination_kind": "VIRTUAL_HTML",
            "normalizer_version": VIRTUAL_HTML_NORMALIZER_VERSION,
            "width": None,
            "height": None,
            "rotation": 0,
            "native_text_available": True,
            "native_char_count": len(text),
            "word_count": len(text.split()),
            "block_count": len(current),
            "line_count": len(current),
            "span_count": 0,
            "image_count": 0,
            "drawing_count": 0,
            "text": text,
            "blocks": [dict(row, virtual_page_no=page_no, reading_order_index=index) for index, row in enumerate(current)],
            "warnings": [],
        }
        pages.append(page)
        for row in current:
            page_by_locator[str(row["dom_locator"])] = page_no
        current.clear()

    for block in blocks:
        text_len = len(str(block["text"]))
        if current and (len(current) >= _MAX_BLOCKS_PER_PAGE or chars + text_len > _MAX_CHARS_PER_PAGE):
            flush()
            chars = 0
        current.append(block)
        chars += text_len
    flush()
    if not pages:
        pages.append(
            {
                "page_no": 1,
                "pagination_kind": "VIRTUAL_HTML",
                "normalizer_version": VIRTUAL_HTML_NORMALIZER_VERSION,
                "width": None,
                "height": None,
                "rotation": 0,
                "native_text_available": False,
                "native_char_count": 0,
                "word_count": 0,
                "block_count": 0,
                "line_count": 0,
                "span_count": 0,
                "image_count": 0,
                "drawing_count": 0,
                "text": "",
                "blocks": [],
                "warnings": ["PAGE_TEXT_EMPTY"],
            }
        )
    return pages, page_by_locator


def _sections(root: _Node, page_by_locator: dict[str, int], member_sha: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for node in _descendants(root):
        heading_level = _heading_level(node)
        if heading_level is None or _is_hidden(node):
            continue
        title = _visible_text(node)
        if not title:
            continue
        page = _node_page(node, page_by_locator)
        locator = _path(node)
        rows.append(
            {
                "section_id": _sha256(f"{member_sha}|section|{locator}".encode()),
                "title": title,
                "level": heading_level,
                "page_start": page,
                "page_end": page,
                "dom_locator": locator,
                "source_member_sha256": member_sha,
            }
        )
    return rows


def _heading_level(node: _Node) -> int | None:
    if re.fullmatch(r"h[1-6]", node.tag):
        return int(node.tag[1])
    raw_level = _attr(node, "aria-level") or _attr(node, "data-level")
    if raw_level and raw_level.isdigit() and 1 <= int(raw_level) <= 6:
        return int(raw_level)
    classes = (_attr(node, "class") or "").casefold().split()
    if any("heading" in value or value in {"section-title", "sectionheader"} for value in classes):
        return 2
    return None


def _tables(
    root: _Node,
    page_by_locator: dict[str, int],
    member_sha: str,
    document_sha: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, str], dict[str, dict[str, Any]]]:
    document_identity = document_sha or member_sha
    tables: list[dict[str, Any]] = []
    cell_by_locator: dict[str, str] = {}
    cell_metadata: dict[str, dict[str, Any]] = {}
    hidden_cache: dict[int, bool] = {}
    visible_text_cache: dict[int, str] = {}
    source_text_cache: dict[int, str] = {}
    heading_nodes = [
        node
        for node in _descendants(root)
        if _heading_level(node) is not None and not _is_hidden_cached(node, hidden_cache)
    ]
    for table_node in (node for node in _descendants(root) if node.tag == "table"):
        locator = _path(table_node)
        table_id = _sha256(f"{member_sha}|table|{locator}".encode())
        caption_node = next((node for node in _descendants(table_node) if node.tag == "caption"), None)
        heading_context = _nearest_heading_context(
            heading_nodes,
            table_node,
            visible_text_cache=visible_text_cache,
            hidden_cache=hidden_cache,
        )
        nested_table_present = any(node.tag == "table" for node in _descendants(table_node))
        inline_xbrl_fact_present = any(_local(node.tag) in {"nonfraction", "nonnumeric"} for node in _descendants(table_node))
        visibility_signals = _visibility_signals(table_node, hidden_cache=hidden_cache)
        style_signals = _style_signals(table_node)
        candidate_signals: list[str] = []
        if caption_node is not None:
            candidate_signals.append("CAPTION_PRESENT")
        if heading_context is not None:
            candidate_signals.append("HEADING_CONTEXT_PRESENT")
        if nested_table_present:
            candidate_signals.append("NESTED_TABLE")
        if inline_xbrl_fact_present:
            candidate_signals.append("INLINE_XBRL_FACT")
        candidate_signals.extend(visibility_signals)
        row_nodes = [node for node in _descendants(table_node) if node.tag == "tr"]
        # The table itself is an ancestor of every row; remove rows nested inside a nested table.
        row_nodes = [node for node in row_nodes if not any(ancestor.tag == "table" and ancestor is not table_node for ancestor in _ancestors(node))]
        grid: list[dict[tuple[int, int], tuple[_Node, int, int]]] = []
        origin_cells: list[dict[str, Any]] = []
        for row_index, row_node in enumerate(row_nodes):
            if len(grid) <= row_index:
                grid.append({})
            col = 0
            cells = [node for node in _descendants(row_node) if node.tag in {"td", "th"} and not any(ancestor.tag == "tr" and ancestor is not row_node for ancestor in _ancestors(node))]
            for cell in cells:
                while (row_index, col) in grid[row_index]:
                    col += 1
                row_span = _int_attr(cell, "rowspan")
                col_span = _int_attr(cell, "colspan")
                while len(grid) < row_index + row_span:
                    grid.append({})
                cell_locator = _path(cell)
                cell_id = _sha256(f"{table_id}|cell|{cell_locator}".encode())
                row_record = {
                    "cell_id": cell_id,
                    "row_index": row_index,
                    "column_index": col,
                    "row_span": row_span,
                    "col_span": col_span,
                    "role": "HEADER" if cell.tag == "th" or row_index == 0 else "BODY",
                    "text": _visible_text_cached(cell, visible_text_cache, hidden_cache),
                    "source_text": _text_cached(cell, source_text_cache),
                    "dom_locator": cell_locator,
                    "source_member_sha256": member_sha,
                    "visibility_signals": _visibility_signals(cell, hidden_cache=hidden_cache),
                    "style_signals": _style_signals(cell),
                    "inline_xbrl_fact_present": any(_local(child.tag) in {"nonfraction", "nonnumeric"} for child in _descendants(cell)),
                    "raw_fact_ids": [],
                }
                origin_cells.append(row_record)
                cell_by_locator[cell_locator] = cell_id
                cell_metadata[cell_id] = {
                    "table_id": table_id,
                    "row_index": row_index,
                    "column_index": col,
                }
                for r_offset in range(row_span):
                    while len(grid) <= row_index + r_offset:
                        grid.append({})
                    for c_offset in range(col_span):
                        grid[row_index + r_offset][col + c_offset] = (cell, row_span, col_span)
                col += col_span
        row_records: list[dict[str, Any]] = []
        for row_index in range(len(grid)):
            cells = [row for row in origin_cells if row["row_index"] == row_index]
            cells.sort(key=lambda row: int(row["column_index"]))
            row_records.append({"row_index": row_index, "cells": cells})
        tables.append(
            {
                "table_id": table_id,
                "document_sha256": document_identity,
                "source_member_sha256": member_sha,
                "page_no": _node_page(table_node, page_by_locator),
                "dom_locator": locator,
                "bbox": None,
                "heading_context": heading_context,
                "caption": (
                    _visible_text_cached(caption_node, visible_text_cache, hidden_cache)
                    if caption_node is not None
                    else None
                ),
                "nested_table_present": nested_table_present,
                "inline_xbrl_fact_present": inline_xbrl_fact_present,
                "visibility_signals": visibility_signals,
                "style_signals": style_signals,
                "row_count": len(row_records),
                "column_count": max((len(row["cells"]) for row in row_records), default=0),
                "value_column_count": max((len(row["cells"]) for row in row_records), default=0),
                "header_tree": [
                    [{"text": cell["text"], "column_index": cell["column_index"], "col_span": cell["col_span"]} for cell in row["cells"]]
                    for row in row_records if any(cell["role"] == "HEADER" for cell in row["cells"])
                ],
                "rows": row_records,
                "candidate_signals": candidate_signals,
                "quality_signals": list(candidate_signals),
            }
        )
    return tables, cell_by_locator, cell_metadata


def _nearest_heading_context(
    heading_nodes: Iterable[_Node],
    table_node: _Node,
    *,
    visible_text_cache: dict[int, str] | None = None,
    hidden_cache: dict[int, bool] | None = None,
) -> dict[str, Any] | None:
    headings = [node for node in heading_nodes if node.order < table_node.order]
    if not headings:
        return None
    node = max(headings, key=lambda item: item.order)
    if visible_text_cache is not None and hidden_cache is not None:
        title = _visible_text_cached(node, visible_text_cache, hidden_cache)
    else:
        title = _visible_text(node)
    return {"title": title, "level": _heading_level(node), "dom_locator": _path(node)}


def _visibility_signals(
    node: _Node,
    *,
    hidden_cache: dict[int, bool] | None = None,
) -> list[str]:
    signals: list[str] = []
    if (_is_hidden_cached(node, hidden_cache) if hidden_cache is not None else _is_hidden(node)):
        signals.append("HIDDEN")
    if (_attr(node, "aria-hidden") or "").casefold() == "true":
        signals.append("ARIA_HIDDEN")
    return signals


def _style_signals(node: _Node) -> list[str]:
    signals: list[str] = []
    style = (_attr(node, "style") or "").strip()
    classes = (_attr(node, "class") or "").strip()
    if style:
        signals.append(f"STYLE:{style}")
    if classes:
        signals.append(f"CLASS:{classes}")
    return signals


def _ancestors(node: _Node) -> Iterable[_Node]:
    current = node.parent
    while current is not None:
        yield current
        current = current.parent


def _contexts_and_units(
    root: _Node,
    package: SecFilingPackage | None = None,
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    contexts: dict[str, dict[str, Any]] = {}
    units: dict[str, dict[str, Any]] = {}
    for node in _descendants(root):
        local = _local(node.tag)
        if local == "context":
            context_id = _attr(node, "id")
            if not context_id:
                continue
            period: dict[str, Any] = {}
            for child in _descendants(node):
                child_local = _local(child.tag)
                if child_local in {"instant", "startdate", "enddate"}:
                    period[child_local] = _text(child)
            identifier = next((_text(child) for child in _descendants(node) if _local(child.tag) == "identifier"), None)
            dimensions: list[dict[str, Any]] = []
            for child in _descendants(node):
                child_local = _local(child.tag)
                if child_local == "explicitmember":
                    member_qname = _text(child)
                    dimensions.append(
                        {
                            "dimension_kind": "EXPLICIT",
                            "dimension": _attr_local(child, "dimension"),
                            "member": member_qname,
                            "member_qname": member_qname,
                            "typed_value": None,
                        }
                    )
                elif child_local == "typedmember":
                    typed_value = _text(child)
                    dimensions.append(
                        {
                            "dimension_kind": "TYPED",
                            "dimension": _attr_local(child, "dimension"),
                            "member": None,
                            "member_qname": None,
                            "typed_value": typed_value,
                            "typed_member_text": typed_value,
                        }
                    )
            contexts[context_id] = {"id": context_id, "entity_identifier": identifier, "period": period, "dimensions": dimensions}
        elif local == "unit":
            unit_id = _attr(node, "id")
            if not unit_id:
                continue
            measures = [_text(child) for child in _descendants(node) if _local(child.tag) == "measure"]
            units[unit_id] = {"id": unit_id, "measures": measures}
    if package is not None:
        for member in package.members:
            if member.role not in {SecMemberRole.XBRL_INSTANCE, SecMemberRole.OTHER}:
                continue
            if member.role is SecMemberRole.OTHER and not member.relative_name.casefold().endswith((".xml", ".xbrl")):
                continue
            try:
                xml_root = ET.fromstring(member.body)
            except ET.ParseError:
                continue
            for element in xml_root.iter():
                local = _xml_local(str(element.tag))
                if local == "context":
                    context_id = element.attrib.get("id")
                    if not context_id or context_id in contexts:
                        continue
                    period: dict[str, Any] = {}
                    identifier: str | None = None
                    dimensions: list[dict[str, Any]] = []
                    for child in element.iter():
                        child_local = _xml_local(str(child.tag))
                        text = _xml_text(child)
                        if child_local in {"instant", "startdate", "enddate"}:
                            period[child_local] = text
                        elif child_local == "identifier":
                            identifier = text
                        elif child_local in {"explicitmember", "typedmember"}:
                            dimensions.append(
                                {
                                    "dimension_kind": "EXPLICIT" if child_local == "explicitmember" else "TYPED",
                                    "dimension": _xml_attr_local(child, "dimension"),
                                    "member": text if child_local == "explicitmember" else None,
                                    "member_qname": text if child_local == "explicitmember" else None,
                                    "typed_value": text if child_local == "typedmember" else None,
                                    "typed_member_text": text if child_local == "typedmember" else None,
                                }
                            )
                    contexts[context_id] = {
                        "id": context_id,
                        "entity_identifier": identifier,
                        "period": period,
                        "dimensions": dimensions,
                        "source_member_sha256": member.member_sha256,
                    }
                elif local == "unit":
                    unit_id = element.attrib.get("id")
                    if not unit_id or unit_id in units:
                        continue
                    units[unit_id] = {
                        "id": unit_id,
                        "measures": [
                            "" if child.text is None else " ".join(child.text.split())
                            for child in element.iter()
                            if _xml_local(str(child.tag)) == "measure"
                        ],
                        "source_member_sha256": member.member_sha256,
                    }
    return contexts, units


def _facts(
    root: _Node,
    package: SecFilingPackage,
    page_by_locator: dict[str, int],
    cell_by_locator: dict[str, str],
    cell_metadata: dict[str, dict[str, Any]],
    blocks_by_locator: dict[str, dict[str, Any]],
    blocks_by_prefix: dict[str, dict[str, Any]] | None,
    contexts: dict[str, dict[str, Any]],
    units: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    primary = next(member for member in package.members if member.role is SecMemberRole.PRIMARY_DOCUMENT)
    primary_sha = primary.member_sha256
    facts: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    hidden_cache: dict[int, bool] = {}
    for index, node in enumerate(_descendants(root)):
        if _local(node.tag) not in {"nonfraction", "nonnumeric"}:
            continue
        locator = _path(node)
        context_ref = _attr(node, "contextref") or _attr(node, "context_ref")
        unit_ref = _attr(node, "unitref") or _attr(node, "unit_ref")
        raw_qname = _attr(node, "name") or ""
        fact_id = _sha256(f"{package.package_sha256}|fact|{locator}|{index}".encode())
        evidence_id = _sha256(f"{fact_id}|evidence|{primary_sha}".encode())
        page_no = _node_page(node, page_by_locator)
        cell_id = None
        for ancestor in (node, *_ancestors(node)):
            cell_id = cell_by_locator.get(_path(ancestor))
            if cell_id:
                break
        resolved_context = contexts.get(context_ref or "") if context_ref else None
        resolved_unit = units.get(unit_ref or "") if unit_ref else None
        if context_ref and resolved_context is None:
            issues.append({"code": P11Reason.P11_XBRL_CONTEXT_UNRESOLVED.value, "severity": "REVIEW", "dom_locator": locator, "context_ref": context_ref})
        if unit_ref and resolved_unit is None:
            issues.append({"code": P11Reason.P11_XBRL_UNIT_UNRESOLVED.value, "severity": "REVIEW", "dom_locator": locator, "unit_ref": unit_ref})
        raw_attrs = dict(node.attrs)
        context_period = dict((resolved_context or {}).get("period") or {})
        table_metadata = cell_metadata.get(str(cell_id), {}) if cell_id else {}
        raw_value = _text(node)
        parsed_numeric_candidate = _numeric_candidate(raw_value)
        fragment_hash = _sha256(f"{primary_sha}|fact|{locator}|{raw_value}".encode())
        hidden = _is_hidden_cached(node, hidden_cache)
        source_block = None if hidden else _source_block_for_node(node, blocks_by_locator, blocks_by_prefix)
        block_id = source_block.get("block_id") if source_block else None
        block_dom_locator = source_block.get("dom_locator") if source_block else None
        if source_block is None and not hidden:
            issues.append(
                {
                    "code": P11Reason.P11_EVIDENCE_LOCATOR_INVALID.value,
                    "severity": "BLOCKING",
                    "dom_locator": locator,
                    "message": "Inline XBRL fact has no normalized source block",
                }
            )
        fact = {
            "raw_fact_id": fact_id,
            "evidence_id": evidence_id,
            "raw_qname": raw_qname,
            "raw_metric_name": raw_qname,
            "fact_kind": "NUMERIC" if _local(node.tag) == "nonfraction" else "NONNUMERIC",
            "raw_value": raw_value,
            "parsed_numeric_candidate": parsed_numeric_candidate,
            "context_ref": context_ref,
            "context": resolved_context,
            "instant": context_period.get("instant"),
            "start_date": context_period.get("startdate"),
            "end_date": context_period.get("enddate"),
            "entity": (resolved_context or {}).get("entity_identifier"),
            "dimensions": list((resolved_context or {}).get("dimensions") or ()),
            "unit_ref": unit_ref,
            "unit": resolved_unit,
            "decimals": _attr(node, "decimals"),
            "precision": _attr(node, "precision"),
            "scale": _attr(node, "scale"),
            "sign": _attr(node, "sign"),
            "format": _attr(node, "format"),
            "nil": (_attr_local(node, "nil") or "").casefold() in {"true", "1"},
            "continued_at": _attr(node, "continuedat") or _attr(node, "continued_at"),
            "hidden": hidden,
            "dom_locator": locator,
            "virtual_page_no": page_no,
            "page_no": page_no,
            "table_cell_id": cell_id,
            "table_id": table_metadata.get("table_id"),
            "row_index": table_metadata.get("row_index"),
            "column_index": table_metadata.get("column_index"),
            "block_id": block_id,
            "block_dom_locator": block_dom_locator,
            "package_sha256": package.package_sha256,
            "member_sha256": primary_sha,
            "fragment_hash": fragment_hash,
            "source_member_sha256": primary_sha,
            "raw_attributes": raw_attrs,
        }
        evidence.append(
            {
                "evidence_id": evidence_id,
                "source_member_sha256": primary_sha,
                "source_member_relative_name": primary.relative_name,
                "package_sha256": package.package_sha256,
                "member_sha256": primary_sha,
                "dom_locator": locator,
                "fact_dom_locator": locator,
                "block_dom_locator": block_dom_locator,
                "virtual_page_no": page_no,
                "block_id": block_id,
                "fragment_hash": fragment_hash,
                "raw_text": raw_value,
                "text": raw_value,
                "raw_fact_id": fact_id,
                "locator_kind": "DOM_HIDDEN_FACT" if hidden else "DOM_PATH",
                "hidden": hidden,
                "table_id": table_metadata.get("table_id"),
                "row_index": table_metadata.get("row_index"),
                "column_index": table_metadata.get("column_index"),
            }
        )
        facts.append(fact)
    return facts, evidence, issues


def _xml_local(tag: str) -> str:
    text = str(tag)
    if text.startswith("{") and "}" in text:
        return text.split("}", 1)[1].casefold()
    return _local(text)


def _xml_facts(
    package: SecFilingPackage,
    contexts: dict[str, dict[str, Any]],
    units: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    facts: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    ignored_elements = {
        "context",
        "unit",
        "schemaref",
        "linkbaseref",
        "footnotelink",
        "roleref",
        "arcroleref",
    }
    for member in package.members:
        if member.role is not SecMemberRole.XBRL_INSTANCE:
            continue
        member_sha = member.member_sha256
        try:
            xml_root = ET.fromstring(member.body)
        except ET.ParseError:
            continue
        namespaces = _xml_namespace_map(member.body)
        for index, (element, locator) in enumerate(_xml_walk(xml_root)):
            attrs = {str(key).casefold(): str(value) for key, value in element.attrib.items()}
            context_ref = _xml_attr_local(element, "contextref") or _xml_attr_local(element, "context_ref")
            if not context_ref or _xml_local(str(element.tag)) in ignored_elements:
                continue
            unit_ref = _xml_attr_local(element, "unitref") or _xml_attr_local(element, "unit_ref")
            raw_qname = _xml_qname(str(element.tag), namespaces)
            raw_value = _xml_text(element)
            nil = (_xml_attr_local(element, "nil") or "").casefold() in {"true", "1"}
            parsed_numeric_candidate = None if nil else _numeric_candidate(raw_value)
            resolved_context = contexts.get(context_ref)
            resolved_unit = units.get(unit_ref or "") if unit_ref else None
            if resolved_context is None:
                issues.append(
                    {
                        "code": P11Reason.P11_XBRL_CONTEXT_UNRESOLVED.value,
                        "severity": "REVIEW",
                        "xml_locator": locator,
                        "context_ref": context_ref,
                    }
                )
            if unit_ref and resolved_unit is None:
                issues.append(
                    {
                        "code": P11Reason.P11_XBRL_UNIT_UNRESOLVED.value,
                        "severity": "REVIEW",
                        "xml_locator": locator,
                        "unit_ref": unit_ref,
                    }
                )
            context_period = dict((resolved_context or {}).get("period") or {})
            fact_id = _sha256(f"{package.package_sha256}|xml-fact|{member_sha}|{locator}|{index}".encode())
            evidence_id = _sha256(f"{fact_id}|evidence|{member_sha}".encode())
            fragment_hash = _sha256(f"{member_sha}|fact|{locator}|{raw_value}".encode())
            fact = {
                "raw_fact_id": fact_id,
                "evidence_id": evidence_id,
                "raw_qname": raw_qname,
                "raw_metric_name": raw_qname,
                "fact_kind": "NUMERIC" if unit_ref or parsed_numeric_candidate is not None else "NONNUMERIC",
                "raw_value": raw_value,
                "parsed_numeric_candidate": parsed_numeric_candidate,
                "context_ref": context_ref,
                "context": resolved_context,
                "instant": context_period.get("instant"),
                "start_date": context_period.get("startdate"),
                "end_date": context_period.get("enddate"),
                "entity": (resolved_context or {}).get("entity_identifier"),
                "dimensions": list((resolved_context or {}).get("dimensions") or ()),
                "unit_ref": unit_ref,
                "unit": resolved_unit,
                "decimals": _xml_attr_local(element, "decimals"),
                "precision": _xml_attr_local(element, "precision"),
                "scale": _xml_attr_local(element, "scale"),
                "sign": _xml_attr_local(element, "sign"),
                "format": _xml_attr_local(element, "format"),
                "nil": nil,
                "continued_at": _xml_attr_local(element, "continuedat") or _xml_attr_local(element, "continued_at"),
                "hidden": False,
                "dom_locator": None,
                "xml_locator": locator,
                "locator_kind": "XML_PATH",
                "virtual_page_no": None,
                "page_no": None,
                "table_cell_id": None,
                "table_id": None,
                "row_index": None,
                "column_index": None,
                "block_id": None,
                "block_dom_locator": None,
                "package_sha256": package.package_sha256,
                "member_sha256": member_sha,
                "fragment_hash": fragment_hash,
                "source_member_sha256": member_sha,
                "raw_attributes": attrs,
            }
            evidence.append(
                {
                    "evidence_id": evidence_id,
                    "source_member_sha256": member_sha,
                    "source_member_relative_name": member.relative_name,
                    "package_sha256": package.package_sha256,
                    "member_sha256": member_sha,
                    "xml_locator": locator,
                    "fragment_hash": fragment_hash,
                    "raw_text": raw_value,
                    "text": raw_value,
                    "raw_fact_id": fact_id,
                    "locator_kind": "XML_PATH",
                    "block_id": None,
                    "table_id": None,
                    "row_index": None,
                    "column_index": None,
                }
            )
            facts.append(fact)
    return facts, evidence, issues


def verify_sec_evidence(
    package: SecFilingPackage,
    pages: Iterable[dict[str, Any]],
    evidence: dict[str, Any],
    *,
    source_cache: dict[tuple[str, str], object] | None = None,
) -> None:
    """Verify one P11 evidence row against immutable package bytes and anchors."""

    member_sha = str(evidence.get("member_sha256") or evidence.get("source_member_sha256") or "")
    member_map = source_cache.get(("MEMBER_MAP", package.package_sha256)) if source_cache is not None else None
    if not isinstance(member_map, dict):
        member_map = {item.member_sha256: item for item in package.members}
        if source_cache is not None:
            source_cache[("MEMBER_MAP", package.package_sha256)] = member_map
    member = member_map.get(member_sha)
    if member is None:
        raise SecError(P11Reason.P11_MEMBER_HASH_MISMATCH, "evidence member is not present in SEC package")
    source_member_sha = str(evidence.get("source_member_sha256") or member_sha)
    if source_member_sha != member_sha or str(evidence.get("package_sha256") or package.package_sha256) != package.package_sha256:
        raise SecError(P11Reason.P11_EVIDENCE_LOCATOR_INVALID, "evidence package/member identity is invalid")

    locator_kind = str(evidence.get("locator_kind") or "DOM_PATH").upper()
    expected_text = str(evidence.get("raw_text", evidence.get("text", "")))
    if locator_kind == "XML_PATH":
        locator = str(evidence.get("xml_locator") or "")
        cache_key = ("XML", member_sha)
        root = source_cache.get(cache_key) if source_cache is not None else None
        if root is None:
            try:
                root = ET.fromstring(member.body)
            except ET.ParseError as exc:
                raise SecError(P11Reason.P11_EVIDENCE_LOCATOR_INVALID, "XML evidence source is not parseable") from exc
            if source_cache is not None:
                source_cache[cache_key] = root
        node = _resolve_xml_locator(root, locator)
        if node is None:
            raise SecError(P11Reason.P11_EVIDENCE_LOCATOR_INVALID, "XML evidence locator does not resolve")
        actual_text = _xml_text(node)
    elif locator_kind in {"DOM_PATH", "DOM_HIDDEN_FACT"}:
        locator = str(evidence.get("dom_locator") or "")
        cache_key = ("DOM", member_sha)
        dom_root = source_cache.get(cache_key) if source_cache is not None else None
        if dom_root is None:
            try:
                html = member.body.decode("utf-8-sig")
            except UnicodeDecodeError as exc:
                raise SecError(P11Reason.P11_EVIDENCE_LOCATOR_INVALID, "HTML evidence source is not UTF-8") from exc
            targets = source_cache.get(("DOM_TARGETS", member_sha)) if source_cache is not None else None
            locator_targets = targets if isinstance(targets, set) else None
            dom_parser = _DomParser(locator_targets=locator_targets)
            try:
                dom_parser.feed(html)
                dom_parser.close()
            except (AssertionError, ValueError) as exc:
                raise SecError(P11Reason.P11_EVIDENCE_LOCATOR_INVALID, "HTML evidence source is not parseable") from exc
            dom_root = dom_parser.root
            if source_cache is not None:
                source_cache[cache_key] = dom_root
                dom_index = dom_parser.locator_index
                if not dom_index:
                    dom_index = _index_dom_locators(dom_root)
                source_cache[("DOM_INDEX", member_sha)] = dom_index
        index_key = ("DOM_INDEX", member_sha)
        dom_index = source_cache.get(index_key) if source_cache is not None else None
        if dom_index is None and source_cache is not None:
            dom_index = _index_dom_locators(dom_root)
            source_cache[index_key] = dom_index
        node = (
            dom_index.get(locator)
            if isinstance(dom_index, dict)
            else _resolve_dom_locator(dom_root, locator)
        )
        if node is None:
            raise SecError(P11Reason.P11_EVIDENCE_LOCATOR_INVALID, "HTML evidence locator does not resolve")
        text_cache = source_cache.get(("DOM_TEXT", member_sha)) if source_cache is not None else None
        if not isinstance(text_cache, dict):
            text_cache = {}
            if source_cache is not None:
                source_cache[("DOM_TEXT", member_sha)] = text_cache
        actual_text = _text_cached(node, text_cache)
        if locator_kind == "DOM_HIDDEN_FACT":
            if _local(node.tag) not in {"nonfraction", "nonnumeric"} or not _is_hidden(node):
                raise SecError(P11Reason.P11_EVIDENCE_LOCATOR_INVALID, "hidden evidence locator does not resolve to a hidden Inline XBRL fact")
        else:
            block_id = str(evidence.get("block_id") or "")
            blocks = [block for page in pages for block in (page.get("blocks") or [])]
            block = next((row for row in blocks if str(row.get("block_id")) == block_id), None)
            if block is None or str(block.get("source_member_sha256")) != member_sha:
                raise SecError(P11Reason.P11_EVIDENCE_LOCATOR_INVALID, "evidence block_id does not resolve to a source block")
            block_locator = str(evidence.get("block_dom_locator") or "")
            if not block_locator.startswith("/"):
                raise SecError(P11Reason.P11_EVIDENCE_LOCATOR_INVALID, "evidence block locator is missing")
            block_node = (
                dom_index.get(block_locator)
                if isinstance(dom_index, dict)
                else _resolve_dom_locator(dom_root, block_locator)
            )
            if block_node is None or _text_cached(block_node, text_cache) != str(block.get("text", "")):
                raise SecError(P11Reason.P11_EVIDENCE_LOCATOR_INVALID, "evidence block locator does not resolve")
            expected_block_fragment = _sha256(f"{member_sha}|block|{block_locator}|{block.get('text', '')}".encode())
            if str(block.get("fragment_sha256", "")) != expected_block_fragment:
                raise SecError(P11Reason.P11_EVIDENCE_LOCATOR_INVALID, "source block fragment hash is invalid")
    else:
        raise SecError(P11Reason.P11_EVIDENCE_LOCATOR_INVALID, "unsupported SEC evidence locator kind")

    if actual_text != expected_text:
        raise SecError(P11Reason.P11_EVIDENCE_LOCATOR_INVALID, "evidence raw text does not match source node")
    expected_fragment = _sha256(f"{member_sha}|fact|{locator}|{actual_text}".encode())
    if str(evidence.get("fragment_hash", "")) != expected_fragment:
        raise SecError(P11Reason.P11_EVIDENCE_LOCATOR_INVALID, "evidence fragment hash does not match source node")


def _attach_facts_to_tables(tables: list[dict[str, Any]], facts: list[dict[str, Any]]) -> None:
    by_cell = {str(fact["table_cell_id"]): [] for fact in facts if fact.get("table_cell_id")}
    for fact in facts:
        cell_id = fact.get("table_cell_id")
        if cell_id:
            by_cell.setdefault(str(cell_id), []).append(str(fact["raw_fact_id"]))
    for table in tables:
        for row in table["rows"]:
            for cell in row["cells"]:
                cell["raw_fact_ids"] = sorted(by_cell.get(str(cell["cell_id"]), []))


def _write_artifacts(
    directory: Path,
    package: SecFilingPackage,
    pages: list[dict[str, Any]],
    sections: list[dict[str, Any]],
    tables: list[dict[str, Any]],
    facts: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    issues: list[dict[str, Any]],
) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    _write_jsonl(directory / "pages.jsonl", pages)
    _write_jsonl(directory / "sections.jsonl", sections)
    _write_jsonl(directory / "tables.jsonl", tables)
    _write_jsonl(directory / "raw_facts.jsonl", facts)
    _write_jsonl(directory / "evidence.jsonl", evidence)
    _write_jsonl(directory / "issues.jsonl", issues)
    file_names = {
        "pages_file": "pages.jsonl",
        "sections_file": "sections.jsonl",
        "tables_file": "tables.jsonl",
        "facts_file": "raw_facts.jsonl",
        "evidence_file": "evidence.jsonl",
        "issues_file": "issues.jsonl",
    }
    artifact_hashes = {
        key: _sha256((directory / name).read_bytes()) for key, name in file_names.items()
    }
    manifest = {
        "schema_version": SEC_ARTIFACT_SCHEMA,
        "parser_version": VIRTUAL_HTML_NORMALIZER_VERSION,
        "package_sha256": package.package_sha256,
        "document_sha256": package.package_sha256,
        "pagination_kind": "VIRTUAL_HTML",
        "normalizer_version": VIRTUAL_HTML_NORMALIZER_VERSION,
        **file_names,
        "artifact_hashes": artifact_hashes,
        "page_count": len(pages),
        "section_count": len(sections),
        "table_count": len(tables),
        "fact_count": len(facts),
        "evidence_count": len(evidence),
        "issue_count": len(issues),
    }
    (directory / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def load_sec_artifacts(artifact_dir: str | Path) -> SecParseResult:
    directory = Path(artifact_dir).expanduser().resolve()
    try:
        manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC parse manifest is invalid") from exc
    if manifest.get("schema_version") != SEC_ARTIFACT_SCHEMA or manifest.get("parser_version") != VIRTUAL_HTML_NORMALIZER_VERSION:
        raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC parse artifact schema/version mismatch")
    package_sha = str(manifest.get("package_sha256", ""))
    file_names = {
        "pages_file": "pages.jsonl",
        "sections_file": "sections.jsonl",
        "tables_file": "tables.jsonl",
        "facts_file": "raw_facts.jsonl",
        "evidence_file": "evidence.jsonl",
        "issues_file": "issues.jsonl",
    }
    hashes = manifest.get("artifact_hashes")
    if not isinstance(hashes, dict):
        raise SecError(P11Reason.P11_PACKAGE_INVALID, "SEC artifact hashes are missing")
    for key, name in file_names.items():
        path = directory / name
        if not path.is_file() or str(hashes.get(key, "")) != _sha256(path.read_bytes()):
            raise SecError(P11Reason.P11_PACKAGE_INVALID, f"SEC artifact hash mismatch: {name}")
    rows = {
        "pages": tuple(_read_jsonl(directory / "pages.jsonl")),
        "sections": tuple(_read_jsonl(directory / "sections.jsonl")),
        "tables": tuple(_read_jsonl(directory / "tables.jsonl")),
        "facts": tuple(_read_jsonl(directory / "raw_facts.jsonl")),
        "evidence": tuple(_read_jsonl(directory / "evidence.jsonl")),
        "issues": tuple(_read_jsonl(directory / "issues.jsonl")),
    }
    counts = {"pages": "page_count", "sections": "section_count", "tables": "table_count", "facts": "fact_count", "evidence": "evidence_count", "issues": "issue_count"}
    for key, manifest_key in counts.items():
        if int(manifest.get(manifest_key, -1)) != len(rows[key]):
            raise SecError(P11Reason.P11_PACKAGE_INVALID, f"SEC artifact count mismatch: {key}")
    return SecParseResult(directory, package_sha, VIRTUAL_HTML_NORMALIZER_VERSION, **rows)


def parse_sec_package(package: SecFilingPackage, artifact_root: str | Path) -> SecParseResult:
    root = Path(artifact_root).expanduser().resolve()
    final_dir = root / f"{package.package_sha256}.{VIRTUAL_HTML_NORMALIZER_VERSION}"
    if final_dir.exists():
        loaded = load_sec_artifacts(final_dir)
        if loaded.package_sha256 != package.package_sha256:
            raise SecError(P11Reason.P11_SOURCE_DRIFT, "SEC parse artifact identity drift")
        return loaded
    primary, html = _primary_member(package)
    parser = _DomParser()
    try:
        parser.feed(html)
        parser.close()
    except (AssertionError, ValueError) as exc:
        raise SecError(P11Reason.P11_HTML_PARSE_FAILED, "SEC HTML parser failed") from exc
    root_node = parser.root
    if not any(node.tag == "html" for node in _descendants(root_node)):
        raise SecError(P11Reason.P11_HTML_PARSE_FAILED, "SEC primary document has no html root")
    blocks = _blocks(root_node, primary.member_sha256)
    pages, page_by_locator = _pages(blocks)
    sections = _sections(root_node, page_by_locator, primary.member_sha256)
    tables, cell_by_locator, cell_metadata = _tables(root_node, page_by_locator, primary.member_sha256, package.package_sha256)
    contexts, units = _contexts_and_units(root_node, package)
    blocks_by_locator = {str(row["dom_locator"]): row for row in blocks}
    blocks_by_prefix: dict[str, dict[str, Any]] = {}
    for locator, block in blocks_by_locator.items():
        prefix = ""
        for component in locator.strip("/").split("/"):
            if not component:
                continue
            prefix += f"/{component}"
            existing = blocks_by_prefix.get(prefix)
            if existing is None or (
                len(str(block.get("dom_locator", ""))),
                int(block.get("source_order_index", 0)),
            ) < (
                len(str(existing.get("dom_locator", ""))),
                int(existing.get("source_order_index", 0)),
            ):
                blocks_by_prefix[prefix] = block
    facts, evidence, issues = _facts(
        root_node,
        package,
        page_by_locator,
        cell_by_locator,
        cell_metadata,
        blocks_by_locator,
        blocks_by_prefix,
        contexts,
        units,
    )
    xml_facts, xml_evidence, xml_issues = _xml_facts(package, contexts, units)
    facts.extend(xml_facts)
    evidence.extend(xml_evidence)
    issues.extend(xml_issues)
    _attach_facts_to_tables(tables, facts)
    root.mkdir(parents=True, exist_ok=True)
    temp_dir = root / f".{package.package_sha256}.{uuid.uuid4().hex}.tmp"
    temp_dir.mkdir(parents=True, exist_ok=False)
    try:
        _write_artifacts(temp_dir, package, pages, sections, tables, facts, evidence, issues)
        try:
            os.replace(temp_dir, final_dir)
        except FileExistsError:
            shutil.rmtree(temp_dir, ignore_errors=True)
        return load_sec_artifacts(final_dir)
    except Exception:
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        raise


__all__ = [
    "SEC_ARTIFACT_SCHEMA",
    "SecParseResult",
    "VIRTUAL_HTML_NORMALIZER_VERSION",
    "load_sec_artifacts",
    "parse_sec_package",
    "verify_sec_evidence",
]
