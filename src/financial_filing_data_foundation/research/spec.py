from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Sequence

from .models import (
    P10Error,
    ResearchSpecBundle,
    ResearchSpecFile,
    ResearchSpecInput,
    SPEC_BUNDLE_SCHEMA_VERSION,
    project_relative_posix,
)


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _descriptor_payload(files: Sequence[ResearchSpecFile]) -> list[dict[str, Any]]:
    return [item.to_dict() for item in files]


def _bundle_hash(files: Sequence[ResearchSpecFile]) -> str:
    return _sha256_bytes(_canonical_json_bytes(_descriptor_payload(files)))


def _resolve_root(project_root: str | Path) -> Path:
    try:
        root = Path(project_root).expanduser().resolve(strict=True)
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        raise P10Error(
            "P10_INVALID_SPEC_INPUT",
            "project root does not exist",
        ) from exc
    if not root.is_dir():
        raise P10Error(
            "P10_INVALID_SPEC_INPUT",
            "project root must be a directory",
        )
    return root


def _assert_within(root: Path, candidate: Path) -> None:
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise P10Error(
            "P10_SPEC_PATH_OUTSIDE_PROJECT",
            "spec path resolves outside project root",
        ) from exc


def _relative_input_path(value: object) -> Path:
    if not isinstance(value, str) or not value:
        raise P10Error(
            "P10_INVALID_SPEC_INPUT",
            "spec relative_path must be a non-empty string",
        )
    path = Path(value)
    if path.is_absolute():
        raise P10Error(
            "P10_SPEC_PATH_OUTSIDE_PROJECT",
            "spec path must be project-root-relative",
        )
    return path


def _resolve_initial_file(root: Path, relative_path: object) -> tuple[Path, str]:
    path = _relative_input_path(relative_path)
    pre_resolved = (root / path).resolve(strict=False)
    _assert_within(root, pre_resolved)
    try:
        resolved = (root / path).resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise P10Error(
            "P10_INVALID_SPEC_INPUT",
            "spec file does not exist",
        ) from exc
    _assert_within(root, resolved)
    if not resolved.is_file():
        raise P10Error(
            "P10_INVALID_SPEC_INPUT",
            "spec input must be a regular file",
        )
    return resolved, project_relative_posix(root, resolved)


def _resolve_frozen_file(root: Path, relative_path: str) -> tuple[Path, str]:
    path = _relative_input_path(relative_path)
    pre_resolved = (root / path).resolve(strict=False)
    _assert_within(root, pre_resolved)
    try:
        resolved = (root / path).resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise P10Error(
            "P10_RESEARCH_SPEC_CHANGED",
            "frozen spec file is missing",
        ) from exc
    _assert_within(root, resolved)
    if not resolved.is_file():
        raise P10Error(
            "P10_RESEARCH_SPEC_CHANGED",
            "frozen spec path is no longer a regular file",
        )
    return resolved, project_relative_posix(root, resolved)


def _read_initial(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise P10Error(
            "P10_INVALID_SPEC_INPUT",
            "cannot read spec file",
        ) from exc


def _read_frozen(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise P10Error(
            "P10_RESEARCH_SPEC_CHANGED",
            "cannot read frozen spec file",
        ) from exc


def _validate_logical_name(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise P10Error(
            "P10_INVALID_SPEC_INPUT",
            "logical_name must be a non-blank string",
        )
    return value


def _validate_bundle_structure(bundle: ResearchSpecBundle) -> None:
    if not isinstance(bundle, ResearchSpecBundle):
        raise P10Error(
            "P10_INVALID_SPEC_INPUT",
            "research spec bundle type is invalid",
        )
    if bundle.schema_version != SPEC_BUNDLE_SCHEMA_VERSION:
        raise P10Error(
            "P10_INVALID_SPEC_INPUT",
            "research spec bundle schema mismatch",
        )
    if not isinstance(bundle.files, tuple) or not bundle.files:
        raise P10Error(
            "P10_INVALID_SPEC_INPUT",
            "research spec bundle files must be a non-empty tuple",
        )
    if (
        not isinstance(bundle.spec_bundle_hash, str)
        or len(bundle.spec_bundle_hash) != 64
        or any(ch not in "0123456789abcdef" for ch in bundle.spec_bundle_hash)
    ):
        raise P10Error(
            "P10_INVALID_SPEC_INPUT",
            "spec_bundle_hash is invalid",
        )

    names: list[str] = []
    for item in bundle.files:
        if not isinstance(item, ResearchSpecFile):
            raise P10Error(
                "P10_INVALID_SPEC_INPUT",
                "research spec bundle contains an invalid descriptor",
            )
        ResearchSpecFile.from_dict(item.to_dict())
        names.append(item.logical_name)

    if names != sorted(names):
        raise P10Error(
            "P10_INVALID_SPEC_INPUT",
            "spec file descriptors are not canonically ordered",
        )
    if len(set(names)) != len(names):
        raise P10Error(
            "P10_INVALID_SPEC_INPUT",
            "duplicate logical_name in research spec bundle",
        )
    if _bundle_hash(bundle.files) != bundle.spec_bundle_hash:
        raise P10Error(
            "P10_INVALID_SPEC_INPUT",
            "research spec bundle hash mismatch",
        )


def freeze_research_spec(
    project_root: str | Path,
    files: Sequence[ResearchSpecInput],
) -> ResearchSpecBundle:
    root = _resolve_root(project_root)
    if isinstance(files, (str, bytes)) or not isinstance(files, Sequence) or not files:
        raise P10Error(
            "P10_INVALID_SPEC_INPUT",
            "research spec input list must be non-empty",
        )

    descriptors: list[ResearchSpecFile] = []
    seen_names: set[str] = set()
    for item in files:
        if not isinstance(item, ResearchSpecInput):
            raise P10Error(
                "P10_INVALID_SPEC_INPUT",
                "research spec inputs must be ResearchSpecInput values",
            )
        logical_name = _validate_logical_name(item.logical_name)
        if logical_name in seen_names:
            raise P10Error(
                "P10_INVALID_SPEC_INPUT",
                "duplicate logical_name in research spec inputs",
            )
        seen_names.add(logical_name)

        resolved, relative_path = _resolve_initial_file(root, item.relative_path)
        raw = _read_initial(resolved)
        descriptors.append(
            ResearchSpecFile(
                logical_name=logical_name,
                relative_path=relative_path,
                size=len(raw),
                sha256=_sha256_bytes(raw),
            )
        )

    descriptors.sort(key=lambda item: item.logical_name)
    frozen = tuple(descriptors)
    return ResearchSpecBundle(
        schema_version=SPEC_BUNDLE_SCHEMA_VERSION,
        files=frozen,
        spec_bundle_hash=_bundle_hash(frozen),
    )


def verify_research_spec(
    project_root: str | Path,
    bundle: ResearchSpecBundle,
) -> None:
    root = _resolve_root(project_root)
    _validate_bundle_structure(bundle)

    for item in bundle.files:
        resolved, canonical_relative = _resolve_frozen_file(root, item.relative_path)
        if canonical_relative != item.relative_path:
            raise P10Error(
                "P10_INVALID_SPEC_INPUT",
                "stored spec relative_path is not canonical",
            )
        raw = _read_frozen(resolved)
        if len(raw) != item.size or _sha256_bytes(raw) != item.sha256:
            raise P10Error(
                "P10_RESEARCH_SPEC_CHANGED",
                "frozen spec file bytes changed",
            )
