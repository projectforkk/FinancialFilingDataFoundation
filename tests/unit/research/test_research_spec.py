from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

import financial_filing_data_foundation.research as research_package
from financial_filing_data_foundation.research import (
    P10Error,
    ResearchSpecBundle,
    ResearchSpecFile,
    ResearchSpecInput,
    SPEC_BUNDLE_SCHEMA_VERSION,
    freeze_research_spec,
    verify_research_spec,
)


def _write(root: Path, relative: str, data: bytes) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def _canonical_hash(files: tuple[ResearchSpecFile, ...]) -> str:
    payload = [item.to_dict() for item in files]
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _bundle_with(
    bundle: ResearchSpecBundle,
    *,
    files: tuple[ResearchSpecFile, ...] | None = None,
    schema_version: str | None = None,
    recompute_hash: bool = False,
) -> ResearchSpecBundle:
    selected = bundle.files if files is None else files
    digest = _canonical_hash(selected) if recompute_hash else bundle.spec_bundle_hash
    return ResearchSpecBundle(
        schema_version=(
            bundle.schema_version if schema_version is None else schema_version
        ),
        files=selected,
        spec_bundle_hash=digest,
    )


def _assert_reason(exc_info: pytest.ExceptionInfo[P10Error], reason: str) -> None:
    assert exc_info.value.reason_code == reason


def test_freeze_single_file_and_verify(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    raw = b"current research rules\n"
    _write(root, "inputs/rules.md", raw)

    bundle = freeze_research_spec(
        root,
        [ResearchSpecInput("rules", "inputs/rules.md")],
    )

    assert bundle.schema_version == SPEC_BUNDLE_SCHEMA_VERSION
    assert len(bundle.files) == 1
    descriptor = bundle.files[0]
    assert descriptor.logical_name == "rules"
    assert descriptor.relative_path == "inputs/rules.md"
    assert descriptor.size == len(raw)
    assert descriptor.sha256 == hashlib.sha256(raw).hexdigest()
    assert bundle.spec_bundle_hash == _canonical_hash(bundle.files)
    verify_research_spec(root, bundle)


def test_multiple_files_order_independent_and_sorted(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    _write(root, "a.bin", b"A")
    _write(root, "b.bin", b"B")

    first = freeze_research_spec(
        root,
        [
            ResearchSpecInput("zeta", "b.bin"),
            ResearchSpecInput("alpha", "a.bin"),
        ],
    )
    second = freeze_research_spec(
        root,
        [
            ResearchSpecInput("alpha", "a.bin"),
            ResearchSpecInput("zeta", "b.bin"),
        ],
    )

    assert [item.logical_name for item in first.files] == ["alpha", "zeta"]
    assert first == second
    assert first.spec_bundle_hash == second.spec_bundle_hash


def test_case_distinct_logical_names_remain_distinct(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    _write(root, "a", b"a")
    _write(root, "b", b"b")

    bundle = freeze_research_spec(
        root,
        [
            ResearchSpecInput("Rules", "a"),
            ResearchSpecInput("rules", "b"),
        ],
    )

    assert [item.logical_name for item in bundle.files] == ["Rules", "rules"]


def test_non_utf8_bom_and_newline_bytes_are_not_normalized(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    raw = b"\xef\xbb\xbfline1\r\nline2\n\xff\x00"
    _write(root, "opaque.bin", raw)

    bundle = freeze_research_spec(
        root,
        [ResearchSpecInput("opaque", "opaque.bin")],
    )
    descriptor = bundle.files[0]

    assert descriptor.size == len(raw)
    assert descriptor.sha256 == hashlib.sha256(raw).hexdigest()


def test_known_fixture_canonical_descriptor_hash(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    _write(root, "a.txt", b"A\n")
    _write(root, "nested/b.txt", b"B\r\n")

    bundle = freeze_research_spec(
        root,
        [
            ResearchSpecInput("beta", "nested/b.txt"),
            ResearchSpecInput("alpha", "a.txt"),
        ],
    )

    assert bundle.spec_bundle_hash == _canonical_hash(bundle.files)
    assert bundle.spec_bundle_hash == "b6a725f6545abd35747fc884d0d48b81c42c3746acfa89b985bcbc239a3db5e5"


@pytest.mark.parametrize("inputs", [[], (), "not-a-sequence-of-inputs"])
def test_empty_or_invalid_input_collection_rejected(
    tmp_path: Path,
    inputs: object,
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    with pytest.raises(P10Error) as exc_info:
        freeze_research_spec(root, inputs)  # type: ignore[arg-type]
    _assert_reason(exc_info, "P10_INVALID_SPEC_INPUT")


@pytest.mark.parametrize("logical_name", ["", " ", "\t\r\n"])
def test_blank_logical_name_rejected(tmp_path: Path, logical_name: str) -> None:
    root = tmp_path / "root"
    root.mkdir()
    _write(root, "a", b"a")
    with pytest.raises(P10Error) as exc_info:
        freeze_research_spec(
            root,
            [ResearchSpecInput(logical_name, "a")],
        )
    _assert_reason(exc_info, "P10_INVALID_SPEC_INPUT")


def test_duplicate_logical_name_rejected(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    _write(root, "a", b"a")
    _write(root, "b", b"b")
    with pytest.raises(P10Error) as exc_info:
        freeze_research_spec(
            root,
            [
                ResearchSpecInput("same", "a"),
                ResearchSpecInput("same", "b"),
            ],
        )
    _assert_reason(exc_info, "P10_INVALID_SPEC_INPUT")


def test_missing_initial_file_rejected(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    with pytest.raises(P10Error) as exc_info:
        freeze_research_spec(
            root,
            [ResearchSpecInput("missing", "missing.txt")],
        )
    _assert_reason(exc_info, "P10_INVALID_SPEC_INPUT")


def test_directory_input_rejected(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    (root / "dir").mkdir()
    with pytest.raises(P10Error) as exc_info:
        freeze_research_spec(
            root,
            [ResearchSpecInput("directory", "dir")],
        )
    _assert_reason(exc_info, "P10_INVALID_SPEC_INPUT")


def test_absolute_input_path_rejected(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    outside = _write(tmp_path, "outside.txt", b"x")
    with pytest.raises(P10Error) as exc_info:
        freeze_research_spec(
            root,
            [ResearchSpecInput("outside", str(outside.resolve()))],
        )
    _assert_reason(exc_info, "P10_SPEC_PATH_OUTSIDE_PROJECT")


def test_traversal_escape_rejected_even_when_target_missing(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    with pytest.raises(P10Error) as exc_info:
        freeze_research_spec(
            root,
            [ResearchSpecInput("escape", "../missing.txt")],
        )
    _assert_reason(exc_info, "P10_SPEC_PATH_OUTSIDE_PROJECT")


def test_persisted_path_is_resolved_project_relative_posix(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    _write(root, "nested/value.txt", b"x")
    bundle = freeze_research_spec(
        root,
        [ResearchSpecInput("value", "nested/../nested/value.txt")],
    )
    assert bundle.files[0].relative_path == "nested/value.txt"
    assert "\\" not in bundle.files[0].relative_path


def test_symlink_escape_rejected_when_supported(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    outside = _write(tmp_path, "outside.bin", b"outside")
    link = root / "link.bin"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation is unavailable without elevated privileges")

    with pytest.raises(P10Error) as exc_info:
        freeze_research_spec(
            root,
            [ResearchSpecInput("link", "link.bin")],
        )
    _assert_reason(exc_info, "P10_SPEC_PATH_OUTSIDE_PROJECT")


def test_file_byte_mutation_detected(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    path = _write(root, "rules.bin", b"before")
    bundle = freeze_research_spec(
        root,
        [ResearchSpecInput("rules", "rules.bin")],
    )
    path.write_bytes(b"after-longer")

    with pytest.raises(P10Error) as exc_info:
        verify_research_spec(root, bundle)
    _assert_reason(exc_info, "P10_RESEARCH_SPEC_CHANGED")


def test_size_preserving_file_mutation_detected(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    path = _write(root, "rules.bin", b"ABCDEF")
    bundle = freeze_research_spec(
        root,
        [ResearchSpecInput("rules", "rules.bin")],
    )
    path.write_bytes(b"FEDCBA")

    with pytest.raises(P10Error) as exc_info:
        verify_research_spec(root, bundle)
    _assert_reason(exc_info, "P10_RESEARCH_SPEC_CHANGED")


def test_deleted_frozen_file_is_changed(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    path = _write(root, "rules.bin", b"rules")
    bundle = freeze_research_spec(
        root,
        [ResearchSpecInput("rules", "rules.bin")],
    )
    path.unlink()

    with pytest.raises(P10Error) as exc_info:
        verify_research_spec(root, bundle)
    _assert_reason(exc_info, "P10_RESEARCH_SPEC_CHANGED")


def test_bundle_schema_tamper_rejected(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    _write(root, "a", b"a")
    bundle = freeze_research_spec(root, [ResearchSpecInput("a", "a")])
    tampered = _bundle_with(bundle, schema_version="wrong-schema")

    with pytest.raises(P10Error) as exc_info:
        verify_research_spec(root, tampered)
    _assert_reason(exc_info, "P10_INVALID_SPEC_INPUT")


def test_bundle_hash_tamper_rejected(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    _write(root, "a", b"a")
    bundle = freeze_research_spec(root, [ResearchSpecInput("a", "a")])
    tampered = replace(bundle, spec_bundle_hash="0" * 64)

    with pytest.raises(P10Error) as exc_info:
        verify_research_spec(root, tampered)
    _assert_reason(exc_info, "P10_INVALID_SPEC_INPUT")


def test_descriptor_tamper_without_rehash_rejected(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    _write(root, "a", b"a")
    bundle = freeze_research_spec(root, [ResearchSpecInput("a", "a")])
    changed = replace(bundle.files[0], size=bundle.files[0].size + 1)
    tampered = _bundle_with(bundle, files=(changed,))

    with pytest.raises(P10Error) as exc_info:
        verify_research_spec(root, tampered)
    _assert_reason(exc_info, "P10_INVALID_SPEC_INPUT")


def test_noncanonical_descriptor_order_rejected_even_with_matching_hash(
    tmp_path: Path,
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    _write(root, "a", b"a")
    _write(root, "b", b"b")
    bundle = freeze_research_spec(
        root,
        [
            ResearchSpecInput("alpha", "a"),
            ResearchSpecInput("beta", "b"),
        ],
    )
    reversed_files = tuple(reversed(bundle.files))
    tampered = _bundle_with(
        bundle,
        files=reversed_files,
        recompute_hash=True,
    )

    with pytest.raises(P10Error) as exc_info:
        verify_research_spec(root, tampered)
    _assert_reason(exc_info, "P10_INVALID_SPEC_INPUT")


def test_noncanonical_relative_path_rejected_with_matching_hash(
    tmp_path: Path,
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    _write(root, "a", b"a")
    bundle = freeze_research_spec(root, [ResearchSpecInput("a", "a")])
    descriptor = replace(bundle.files[0], relative_path="nested/../a")
    tampered = _bundle_with(
        bundle,
        files=(descriptor,),
        recompute_hash=True,
    )

    with pytest.raises(P10Error) as exc_info:
        verify_research_spec(root, tampered)
    _assert_reason(exc_info, "P10_INVALID_SPEC_INPUT")


def test_root_escape_during_verification_has_path_reason(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    outside = _write(tmp_path, "outside.bin", b"outside")
    descriptor = ResearchSpecFile(
        logical_name="outside",
        relative_path="../outside.bin",
        size=outside.stat().st_size,
        sha256=hashlib.sha256(outside.read_bytes()).hexdigest(),
    )
    bundle = ResearchSpecBundle(
        schema_version=SPEC_BUNDLE_SCHEMA_VERSION,
        files=(descriptor,),
        spec_bundle_hash=_canonical_hash((descriptor,)),
    )

    with pytest.raises(P10Error) as exc_info:
        verify_research_spec(root, bundle)
    _assert_reason(exc_info, "P10_SPEC_PATH_OUTSIDE_PROJECT")


def test_bundle_hash_input_is_descriptor_array_only(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    _write(root, "a", b"a")
    bundle = freeze_research_spec(root, [ResearchSpecInput("a", "a")])

    assert bundle.spec_bundle_hash == _canonical_hash(bundle.files)
    whole_bundle_without_hash = {
        "schema_version": bundle.schema_version,
        "files": [item.to_dict() for item in bundle.files],
    }
    whole_hash = hashlib.sha256(
        json.dumps(
            whole_bundle_without_hash,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    assert bundle.spec_bundle_hash != whole_hash


def test_bundle_serialization_contains_descriptors_not_file_contents(
    tmp_path: Path,
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    secret_instruction = b"UNIQUE-INSTRUCTION-CONTENT-DO-NOT-COPY-918273645"
    _write(root, "rules.bin", secret_instruction)
    bundle = freeze_research_spec(
        root,
        [ResearchSpecInput("rules", "rules.bin")],
    )

    serialized = json.dumps(bundle.to_dict(), sort_keys=True)
    assert secret_instruction.decode("ascii") not in serialized
    assert set(bundle.to_dict()) == {
        "schema_version",
        "files",
        "spec_bundle_hash",
    }


def test_bundle_from_dict_round_trip(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    _write(root, "a", b"a")
    bundle = freeze_research_spec(root, [ResearchSpecInput("a", "a")])

    loaded = ResearchSpecBundle.from_dict(bundle.to_dict())
    assert loaded == bundle
    verify_research_spec(root, loaded)


def test_import_resolves_to_exact_candidate_source() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    source_path = Path(research_package.__file__).resolve()
    expected = (
        repository_root
        / "src"
        / "financial_filing_data_foundation"
        / "research"
        / "__init__.py"
    ).resolve()
    assert source_path == expected
