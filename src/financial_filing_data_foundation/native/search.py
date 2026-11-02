from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from .models import NativeParseError, SCHEMA_VERSION


def build_search_db(
    db_path: Path,
    document_sha256: str,
    pages: list[dict[str, Any]],
    sections: list[dict[str, Any]],
) -> None:
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA journal_mode=OFF")
        conn.execute("PRAGMA synchronous=OFF")
        conn.execute(
            "CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        conn.execute(
            "CREATE TABLE page_content(page_no INTEGER PRIMARY KEY, text TEXT NOT NULL)"
        )
        conn.execute(
            """
            CREATE VIRTUAL TABLE page_fts USING fts5(
                text,
                content='page_content',
                content_rowid='page_no'
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE sections(
                section_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                page_start INTEGER NOT NULL,
                page_end INTEGER NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE VIRTUAL TABLE section_fts USING fts5(section_id UNINDEXED, title)"
        )
        conn.executemany(
            "INSERT INTO metadata(key,value) VALUES(?,?)",
            (
                ("document_sha256", document_sha256),
                ("schema_version", SCHEMA_VERSION),
            ),
        )
        for page in pages:
            page_no = int(page["page_no"])
            text = str(page.get("text", ""))
            conn.execute(
                "INSERT INTO page_content(page_no,text) VALUES(?,?)",
                (page_no, text),
            )
            conn.execute(
                "INSERT INTO page_fts(rowid,text) VALUES(?,?)",
                (page_no, text),
            )
        for section in sections:
            values = (
                str(section["section_id"]),
                str(section["raw_title"]),
                int(section["page_start"]),
                int(section["page_end"]),
            )
            conn.execute(
                "INSERT INTO sections(section_id,title,page_start,page_end) VALUES(?,?,?,?)",
                values,
            )
            conn.execute(
                "INSERT INTO section_fts(section_id,title) VALUES(?,?)",
                (values[0], values[1]),
            )
        conn.commit()
    except sqlite3.OperationalError as exc:
        raise NativeParseError("FTS5_UNAVAILABLE", str(exc)) from exc
    finally:
        try:
            conn.close()
        except UnboundLocalError:
            pass


def search_pages(
    db_path: str | Path,
    query: str,
    limit: int = 10,
) -> tuple[dict[str, Any], ...]:
    if limit < 1:
        raise ValueError("limit must be >= 1")
    conn = sqlite3.connect(Path(db_path))
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT pc.page_no AS page_no, pc.text AS text,
                   bm25(page_fts) AS score
            FROM page_fts
            JOIN page_content pc ON pc.page_no = page_fts.rowid
            WHERE page_fts MATCH ?
            ORDER BY score ASC, pc.page_no ASC
            LIMIT ?
            """,
            (query, int(limit)),
        ).fetchall()
        return tuple(
            {
                "page_no": int(row["page_no"]),
                "text": str(row["text"]),
                "score": float(row["score"]),
            }
            for row in rows
        )
    finally:
        conn.close()


def search_sections(
    db_path: str | Path,
    query: str,
    limit: int = 10,
) -> tuple[dict[str, Any], ...]:
    if limit < 1:
        raise ValueError("limit must be >= 1")
    conn = sqlite3.connect(Path(db_path))
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT sf.section_id, sf.title, s.page_start, s.page_end,
                   bm25(section_fts) AS score
            FROM section_fts sf
            JOIN sections s ON s.section_id = sf.section_id
            WHERE section_fts MATCH ?
            ORDER BY score ASC, s.page_start ASC, sf.section_id ASC
            LIMIT ?
            """,
            (query, int(limit)),
        ).fetchall()
        return tuple(
            {
                "section_id": str(row["section_id"]),
                "title": str(row["title"]),
                "page_start": int(row["page_start"]),
                "page_end": int(row["page_end"]),
                "score": float(row["score"]),
            }
            for row in rows
        )
    finally:
        conn.close()
