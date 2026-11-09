from __future__ import annotations

import hashlib
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

from .errors import P11Reason, SecError
from .package import SecFilingPackage, SecMemberRole


SEC_ARTIFACT_SCHEMA = "p11-sec-artifacts-v1"
VIRTUAL_HTML_NORMALIZER_VERSION = "VIRTUAL_HTML_V1"
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
    children: list["_Node"] = field(default_factory=list)
    data: list[str] = field(default_factory=list)


class _DomParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = _Node("#document", {}, None, 0)
        self._stack = [self.root]
        self._order = 0

    def _attrs(self, attrs: list[tuple[str, str | None]]) -> dict[str, str]:
        return {str(key).casefold(): "" if value is None else str(value) for key, value in attrs}

    def _start(self, tag: str, attrs: list[tuple[str, str | None]], *, push: bool) -> None:
        self._order += 1
        node = _Node(tag.casefold(), self._attrs(attrs), self._stack[-1], self._order)
        self._stack[-1].children.append(node)
        if push:
            self._stack.append(node)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._start(tag, attrs, push=tag.casefold() not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"})

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._start(tag, attrs, push=False)

    def handle_endtag(self, tag: str) -> None:
        target = tag.casefold()
        for index in range(len(self._stack) - 1, 0, -1):
            if self._stack[index].tag == target:
                del self._stack[index:]
                return

    def handle_data(self, data: str) -> None:
        self._stack[-1].data.append(data)


def _local(tag: str) -> str:
    return tag.rsplit(":", 1)[-1].casefold()


def _attr(node: _Node, name: str) -> str | None:
    return node.attrs.get(name.casefold())


def _text(node: _Node) -> str:
    values: list[str] = []
    values.extend(node.data)
    for child in node.children:
        child_text = _text(child)
        if child_text:
            values.append(child_text)
    return " ".join(" ".join(values).split())


def _descendants(node: _Node) -> Iterable[_Node]:
    for child in node.children:
        yield child
        yield from _descendants(child)


def _path(node: _Node) -> str:
    pieces: list[str] = []
    current: _Node | None = node
    while current is not None and current.tag != "#document":
        if current.parent is None:
            index = 1
        else:
            siblings = [child for child in current.parent.children if child.tag == current.tag]
            index = siblings.index(current) + 1
        pieces.append(f"{current.tag}[{index}]")
        current = current.parent
    return "/" + "/".join(reversed(pieces))


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


def _blocks(root: _Node, member_sha: str) -> list[dict[str, Any]]:
    block_tags = {"h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "caption", "td", "th", "title", "pre"}
    candidates: list[_Node] = []
    for node in _descendants(root):
        if node.tag not in block_tags or _under(node, {"ix:header", "header"}):
            continue
        value = _text(node)
        if not value:
            continue
        if any(child.tag in block_tags for child in node.children):
            continue
        candidates.append(node)
    candidates.sort(key=lambda node: node.order)
    blocks: list[dict[str, Any]] = []
    for index, node in enumerate(candidates):
        locator = _path(node)
        text = _text(node)
        fragment = _sha256(f"{member_sha}|{locator}|{text}".encode())
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
        if node.tag not in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            continue
        title = _text(node)
        if not title:
            continue
        page = _node_page(node, page_by_locator)
        locator = _path(node)
        rows.append(
            {
                "section_id": _sha256(f"{member_sha}|section|{locator}".encode()),
                "title": title,
                "level": int(node.tag[1]),
                "page_start": page,
                "page_end": page,
                "dom_locator": locator,
                "source_member_sha256": member_sha,
            }
        )
    return rows


def _tables(
    root: _Node,
    page_by_locator: dict[str, int],
    member_sha: str,
) -> tuple[list[dict[str, Any]], dict[str, str], dict[str, dict[str, Any]]]:
    tables: list[dict[str, Any]] = []
    cell_by_locator: dict[str, str] = {}
    cell_metadata: dict[str, dict[str, Any]] = {}
    for table_node in (node for node in _descendants(root) if node.tag == "table"):
        locator = _path(table_node)
        table_id = _sha256(f"{member_sha}|table|{locator}".encode())
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
                    "text": _text(cell),
                    "dom_locator": cell_locator,
                    "source_member_sha256": member_sha,
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
                "document_sha256": member_sha,
                "page_no": _node_page(table_node, page_by_locator),
                "dom_locator": locator,
                "bbox": None,
                "row_count": len(row_records),
                "value_column_count": max((len(row["cells"]) for row in row_records), default=0),
                "header_tree": [
                    [{"text": cell["text"], "column_index": cell["column_index"], "col_span": cell["col_span"]} for cell in row["cells"]]
                    for row in row_records if any(cell["role"] == "HEADER" for cell in row["cells"])
                ],
                "rows": row_records,
                "quality_signals": [],
            }
        )
    return tables, cell_by_locator, cell_metadata


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
            dimensions = [
                {
                    "dimension": _attr(child, "dimension"),
                    "member": _text(child),
                    "member_qname": _text(child),
                }
                for child in _descendants(node)
                if _local(child.tag) in {"explicitmember", "typedmember"}
            ]
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
            if not member.relative_name.casefold().endswith(".xml"):
                continue
            try:
                xml_root = ET.fromstring(member.body)
            except ET.ParseError:
                continue
            for element in xml_root.iter():
                local = _local(str(element.tag))
                if local == "context":
                    context_id = element.attrib.get("id")
                    if not context_id or context_id in contexts:
                        continue
                    period: dict[str, Any] = {}
                    identifier: str | None = None
                    dimensions: list[dict[str, Any]] = []
                    for child in element.iter():
                        child_local = _local(str(child.tag))
                        text = "" if child.text is None else " ".join(child.text.split())
                        if child_local in {"instant", "startdate", "enddate"}:
                            period[child_local] = text
                        elif child_local == "identifier":
                            identifier = text
                        elif child_local in {"explicitmember", "typedmember"}:
                            dimensions.append(
                                {
                                    "dimension": child.attrib.get("dimension"),
                                    "member": text,
                                    "member_qname": text,
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
                            if _local(str(child.tag)) == "measure"
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
    contexts: dict[str, dict[str, Any]],
    units: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    primary = next(member for member in package.members if member.role is SecMemberRole.PRIMARY_DOCUMENT)
    facts: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    for index, node in enumerate(_descendants(root)):
        if _local(node.tag) not in {"nonfraction", "nonnumeric"}:
            continue
        locator = _path(node)
        context_ref = _attr(node, "contextref") or _attr(node, "context_ref")
        unit_ref = _attr(node, "unitref") or _attr(node, "unit_ref")
        raw_qname = _attr(node, "name") or ""
        fact_id = _sha256(f"{package.package_sha256}|fact|{locator}|{index}".encode())
        evidence_id = _sha256(f"{fact_id}|evidence|{primary.member_sha256}".encode())
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
        parsed_numeric_candidate: str | None = None
        numeric_text = raw_value.strip().replace(",", "")
        if re.fullmatch(r"\(?[+-]?\d+(?:\.\d+)?\)?", numeric_text):
            parsed_numeric_candidate = (
                "-" + numeric_text[1:-1]
                if numeric_text.startswith("(") and numeric_text.endswith(")")
                else numeric_text
            )
        fragment_hash = _sha256(f"{primary.member_sha256}|{locator}|{raw_value}".encode())
        fact = {
            "raw_fact_id": fact_id,
            "evidence_id": evidence_id,
            "raw_qname": raw_qname,
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
            "nil": (_attr(node, "nil") or "").casefold() in {"true", "1"},
            "continued_at": _attr(node, "continuedat") or _attr(node, "continued_at"),
            "hidden": _under(node, {"hidden", "ix:hidden"}),
            "dom_locator": locator,
            "virtual_page_no": page_no,
            "table_cell_id": cell_id,
            "table_id": table_metadata.get("table_id"),
            "row_index": table_metadata.get("row_index"),
            "column_index": table_metadata.get("column_index"),
            "package_sha256": package.package_sha256,
            "member_sha256": primary.member_sha256,
            "fragment_hash": fragment_hash,
            "source_member_sha256": primary.member_sha256,
            "raw_attributes": raw_attrs,
        }
        evidence.append(
            {
                "evidence_id": evidence_id,
                "source_member_sha256": primary.member_sha256,
                "source_member_relative_name": primary.relative_name,
                "package_sha256": package.package_sha256,
                "member_sha256": primary.member_sha256,
                "dom_locator": locator,
                "virtual_page_no": page_no,
                "block_id": fragment_hash,
                "fragment_hash": fragment_hash,
                "raw_text": raw_value,
                "text": raw_value,
                "raw_fact_id": fact_id,
                "locator_kind": "DOM_PATH",
                "table_id": table_metadata.get("table_id"),
                "row_index": table_metadata.get("row_index"),
                "column_index": table_metadata.get("column_index"),
            }
        )
        facts.append(fact)
    return facts, evidence, issues


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
    final_dir = root / package.package_sha256
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
    tables, cell_by_locator, cell_metadata = _tables(root_node, page_by_locator, primary.member_sha256)
    contexts, units = _contexts_and_units(root_node, package)
    facts, evidence, issues = _facts(root_node, package, page_by_locator, cell_by_locator, cell_metadata, contexts, units)
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
]
