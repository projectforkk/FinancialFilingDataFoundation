from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


SPEC_BUNDLE_SCHEMA_VERSION = "p10-research-spec-bundle-v1"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class P10Error(RuntimeError):
    def __init__(self, reason_code: str, message: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


@dataclass(frozen=True, slots=True)
class ResearchSpecInput:
    logical_name: str
    relative_path: str


@dataclass(frozen=True, slots=True)
class ResearchSpecFile:
    logical_name: str
    relative_path: str
    size: int
    sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "logical_name": self.logical_name,
            "relative_path": self.relative_path,
            "size": self.size,
            "sha256": self.sha256,
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "ResearchSpecFile":
        if not isinstance(raw, Mapping):
            raise P10Error(
                "P10_INVALID_SPEC_INPUT",
                "spec file descriptor must be an object",
            )
        expected = {"logical_name", "relative_path", "size", "sha256"}
        if set(raw) != expected:
            raise P10Error(
                "P10_INVALID_SPEC_INPUT",
                "spec file descriptor fields are invalid",
            )
        logical_name = raw.get("logical_name")
        relative_path = raw.get("relative_path")
        size = raw.get("size")
        sha256 = raw.get("sha256")
        if not isinstance(logical_name, str) or not logical_name.strip():
            raise P10Error(
                "P10_INVALID_SPEC_INPUT",
                "logical_name must be a non-blank string",
            )
        if not isinstance(relative_path, str) or not relative_path:
            raise P10Error(
                "P10_INVALID_SPEC_INPUT",
                "relative_path must be a non-empty string",
            )
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            raise P10Error(
                "P10_INVALID_SPEC_INPUT",
                "spec file size must be a non-negative integer",
            )
        if not isinstance(sha256, str) or not _SHA256_RE.fullmatch(sha256):
            raise P10Error(
                "P10_INVALID_SPEC_INPUT",
                "spec file sha256 must be lowercase hexadecimal",
            )
        return cls(
            logical_name=logical_name,
            relative_path=relative_path,
            size=size,
            sha256=sha256,
        )


@dataclass(frozen=True, slots=True)
class ResearchSpecBundle:
    schema_version: str
    files: tuple[ResearchSpecFile, ...]
    spec_bundle_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "files": [item.to_dict() for item in self.files],
            "spec_bundle_hash": self.spec_bundle_hash,
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "ResearchSpecBundle":
        if not isinstance(raw, Mapping):
            raise P10Error(
                "P10_INVALID_SPEC_INPUT",
                "research spec bundle must be an object",
            )
        expected = {"schema_version", "files", "spec_bundle_hash"}
        if set(raw) != expected:
            raise P10Error(
                "P10_INVALID_SPEC_INPUT",
                "research spec bundle fields are invalid",
            )
        schema_version = raw.get("schema_version")
        files = raw.get("files")
        spec_bundle_hash = raw.get("spec_bundle_hash")
        if not isinstance(schema_version, str):
            raise P10Error(
                "P10_INVALID_SPEC_INPUT",
                "spec bundle schema_version must be a string",
            )
        if not isinstance(files, list):
            raise P10Error(
                "P10_INVALID_SPEC_INPUT",
                "spec bundle files must be a list",
            )
        if not isinstance(spec_bundle_hash, str):
            raise P10Error(
                "P10_INVALID_SPEC_INPUT",
                "spec_bundle_hash must be a string",
            )
        return cls(
            schema_version=schema_version,
            files=tuple(ResearchSpecFile.from_dict(item) for item in files),
            spec_bundle_hash=spec_bundle_hash,
        )


def project_relative_posix(root: Path, resolved: Path) -> str:
    try:
        return resolved.relative_to(root).as_posix()
    except ValueError as exc:
        raise P10Error(
            "P10_SPEC_PATH_OUTSIDE_PROJECT",
            "spec path resolves outside project root",
        ) from exc
