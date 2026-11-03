from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "p5-reconstructed-tables-v1"
RECONSTRUCTION_VERSION = "p5-table-reconstruction-v1"


class TableReconstructionError(RuntimeError):
    def __init__(self, reason_code: str, message: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


@dataclass(frozen=True, slots=True)
class ReconstructedTableArtifact:
    artifact_dir: Path
    document_sha256: str
    table_count: int
    group_count: int
    reconstruction_version: str
    tables_path: Path
    groups_path: Path
    manifest_path: Path
    timings_ms: dict[str, float]
    warnings: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "reconstruction_version": self.reconstruction_version,
            "document_sha256": self.document_sha256,
            "table_count": self.table_count,
            "group_count": self.group_count,
            "artifact_dir": str(self.artifact_dir),
            "tables_path": str(self.tables_path),
            "groups_path": str(self.groups_path),
            "manifest_path": str(self.manifest_path),
            "timings_ms": self.timings_ms,
            "warnings": list(self.warnings),
        }
