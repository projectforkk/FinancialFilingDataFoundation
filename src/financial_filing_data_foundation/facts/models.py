from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "p6-raw-facts-evidence-v1"
EXTRACTOR_VERSION = "p6-raw-fact-extractor-v1"


class RawFactError(RuntimeError):
    def __init__(self, reason_code: str, message: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


@dataclass(frozen=True, slots=True)
class RawFactArtifact:
    artifact_dir: Path
    document_sha256: str
    fact_count: int
    evidence_count: int
    extractor_version: str
    facts_path: Path
    evidence_path: Path
    manifest_path: Path
    timings_ms: dict[str, float]
    warnings: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "extractor_version": self.extractor_version,
            "document_sha256": self.document_sha256,
            "fact_count": self.fact_count,
            "evidence_count": self.evidence_count,
            "artifact_dir": str(self.artifact_dir),
            "facts_path": str(self.facts_path),
            "evidence_path": str(self.evidence_path),
            "manifest_path": str(self.manifest_path),
            "timings_ms": self.timings_ms,
            "warnings": list(self.warnings),
        }
