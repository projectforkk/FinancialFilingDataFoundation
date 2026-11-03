from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "p4-table-candidates-v1"
DETECTOR_VERSION = "p4-table-candidate-v1"


class TableCandidateError(RuntimeError):
    def __init__(self, reason_code: str, message: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


@dataclass(frozen=True, slots=True)
class TableCandidateArtifact:
    artifact_dir: Path
    document_sha256: str
    candidate_count: int
    detector_version: str
    candidates_path: Path
    manifest_path: Path
    timings_ms: dict[str, float]
    warnings: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "document_sha256": self.document_sha256,
            "candidate_count": self.candidate_count,
            "detector_version": self.detector_version,
            "artifact_dir": str(self.artifact_dir),
            "candidates_path": str(self.candidates_path),
            "manifest_path": str(self.manifest_path),
            "timings_ms": self.timings_ms,
            "warnings": list(self.warnings),
        }
