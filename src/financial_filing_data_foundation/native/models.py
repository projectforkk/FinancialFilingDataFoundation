from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "p3-native-document-v1"
P3_PARSER_VERSION = "p3-native-page-section-v1"


class NativeParseError(RuntimeError):
    def __init__(self, reason_code: str, message: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


@dataclass(frozen=True, slots=True)
class NativeDocumentArtifact:
    artifact_dir: Path
    document_sha256: str
    file_size: int
    page_count: int
    parser_version: str
    pages_path: Path
    sections_path: Path
    search_db_path: Path
    document_path: Path
    timings_ms: dict[str, float]
    warnings: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "document_sha256": self.document_sha256,
            "file_size": self.file_size,
            "page_count": self.page_count,
            "parser_version": self.parser_version,
            "artifact_dir": str(self.artifact_dir),
            "pages_path": str(self.pages_path),
            "sections_path": str(self.sections_path),
            "search_db_path": str(self.search_db_path),
            "document_path": str(self.document_path),
            "timings_ms": self.timings_ms,
            "warnings": list(self.warnings),
        }
