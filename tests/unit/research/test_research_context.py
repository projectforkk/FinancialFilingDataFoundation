from __future__ import annotations

import hashlib
import importlib.util
import inspect
import json
from pathlib import Path

import pytest

import financial_filing_data_foundation.research as research_package
import financial_filing_data_foundation.research.context as context_module
from financial_filing_data_foundation.mcp import McpCatalog
from financial_filing_data_foundation.research import (
    CAPABILITY_MANIFEST_V1,
    CONTEXT_SCHEMA_VERSION,
    INTEGRATION_POLICY_VERSION,
    P10Error,
    P8ToolContract,
    P9PolicyContract,
    ResearchSpecInput,
    build_research_context,
    freeze_research_spec,
)


P8_FINGERPRINT = "bbeb600e732d5ca567193602d2a2b067fcedeabf9cb5d7cfdf5598671c267bc8"
P9_FINGERPRINT = "9b7a1078ab2365862dc5061c3b2a76a43f865553eb4df5938b96ffe9bbd4ff36"
CAPABILITY_HASH = "30df28e273379e91c245222b751aaab1504b6c725ca4170a8fb6168082735935"
KNOWN_SPEC_HASH = "021830ab8ded8e8e5eeeef4aa190cf3ffa86ff73a97556f1ebc80f5245288371"
KNOWN_CATALOG_HASH = "149a9ec1ed42763860358d44f5d2f6b65115fc5bcf32190b8ca14e3b457de05d"
KNOWN_CONTEXT_ID = "a06bbce2a58e6af4b84e5259c41439b4bae0567e3076e2320d26e3d08661d9eb"


def _write(root: Path, relative: str, data: bytes) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def _fixture_root(tmp_path: Path) -> tuple[Path, McpCatalog]:
    root = tmp_path / "root"
    root.mkdir()
    _write(root, "inputs/rules.md", b"rules\n")
    (root / "reviews/a").mkdir(parents=True)
    (root / "reviews/b").mkdir(parents=True)
    catalog_raw = b'{"schema_version":"p8-mcp-catalog-v1","documents":[]}\n'
    _write(root, "catalog.json", catalog_raw)
    return root, McpCatalog.load(root, "catalog.json")


def _bundle(root: Path):
    return freeze_research_spec(
        root,
        [ResearchSpecInput("rules", "inputs/rules.md")],
    )


def _context(tmp_path: Path, review_root: str = "reviews/a"):
    root, catalog = _fixture_root(tmp_path)
    bundle = _bundle(root)
    return root, catalog, bundle, build_research_context(
        bundle,
        catalog,
        review_root,
    )


def _assert_reason(exc_info: pytest.ExceptionInfo[P10Error], reason: str) -> None:
    assert exc_info.value.reason_code == reason


def _canonical_hash(value: object) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def test_identical_inputs_produce_identical_context(tmp_path: Path) -> None:
    root, catalog = _fixture_root(tmp_path)
    bundle = _bundle(root)

    first = build_research_context(bundle, catalog, "reviews/a")
    second = build_research_context(bundle, catalog, "reviews/a")

    assert first == second
    assert first.to_dict() == second.to_dict()


def test_spec_is_verified_before_catalog_reload(tmp_path: Path) -> None:
    root, catalog = _fixture_root(tmp_path)
    bundle = _bundle(root)
    (root / "inputs/rules.md").write_bytes(b"changed\n")
    (root / "catalog.json").write_text("{not-json", encoding="utf-8")

    with pytest.raises(P10Error) as exc_info:
        build_research_context(bundle, catalog, "reviews/a")

    _assert_reason(exc_info, "P10_RESEARCH_SPEC_CHANGED")


def test_p8_descriptor_and_known_fingerprint(tmp_path: Path) -> None:
    _, _, _, context = _context(tmp_path)

    assert context.p8_tool_contract.to_dict() == {
        "server_version": "p8-local-mcp-v1",
        "catalog_schema_version": "p8-mcp-catalog-v1",
        "result_schema_version": "p8-mcp-result-v1",
        "tool_names": [
            "ffdf_list_documents",
            "ffdf_get_document",
            "ffdf_search_document",
            "ffdf_read_pages",
            "ffdf_list_sections",
            "ffdf_list_tables",
            "ffdf_get_table",
            "ffdf_list_raw_facts",
            "ffdf_get_fact",
            "ffdf_get_evidence",
            "ffdf_get_validation",
        ],
    }
    assert context.p8_tool_contract_fingerprint == P8_FINGERPRINT
    assert _canonical_hash(context.p8_tool_contract.to_dict()) == P8_FINGERPRINT


def test_p9_descriptor_and_known_fingerprint(tmp_path: Path) -> None:
    _, _, _, context = _context(tmp_path)

    assert context.p9_policy_contract.to_dict() == {
        "p9_version": "p9-review-overlay-v1",
        "policy_version": "p9-review-policy-v1",
        "resolution_schema_version": "p9-review-resolution-v1",
        "resolved_view_schema_version": "p9-resolved-view-v1",
    }
    assert context.p9_policy_fingerprint == P9_FINGERPRINT
    assert _canonical_hash(context.p9_policy_contract.to_dict()) == P9_FINGERPRINT


def test_exact_fixed_capability_mapping_and_hash(tmp_path: Path) -> None:
    _, _, _, context = _context(tmp_path)
    expected = {
        "P8_RAW_QUERY": "AVAILABLE",
        "P8_PAGE_TEXT": "AVAILABLE",
        "P8_TABLE_STRUCTURED": "AVAILABLE",
        "P8_EVIDENCE": "AVAILABLE",
        "P8_VALIDATION": "AVAILABLE",
        "P9_REVIEW": "AVAILABLE",
        "P9_RESOLVED_VIEW": "AVAILABLE",
        "PDF_VISUAL_EVIDENCE": "UNAVAILABLE",
        "SEMANTIC_RESOLVER": "UNAVAILABLE",
        "CANONICAL_METRIC_LAYER": "UNAVAILABLE",
        "P11_SEC_PROVIDER": "UNAVAILABLE",
    }

    assert dict(CAPABILITY_MANIFEST_V1) == expected
    assert context.to_dict()["capabilities"] == expected
    assert context.capability_manifest_hash == CAPABILITY_HASH
    assert _canonical_hash(expected) == CAPABILITY_HASH


def test_build_api_has_no_capability_override() -> None:
    assert list(inspect.signature(build_research_context).parameters) == [
        "spec_bundle",
        "p8_catalog",
        "p9_review_root",
    ]


def test_raw_catalog_sha_and_known_context_fixture(tmp_path: Path) -> None:
    root, _, bundle, context = _context(tmp_path)

    assert bundle.spec_bundle_hash == KNOWN_SPEC_HASH
    assert hashlib.sha256((root / "catalog.json").read_bytes()).hexdigest() == KNOWN_CATALOG_HASH
    assert context.p8_catalog_sha256 == KNOWN_CATALOG_HASH
    assert context.research_context_id == KNOWN_CONTEXT_ID
    assert context.schema_version == CONTEXT_SCHEMA_VERSION == "p10-research-context-v1"
    assert (
        context.integration_policy_version
        == INTEGRATION_POLICY_VERSION
        == "p10-dynamic-research-v1"
    )


def test_stale_caller_catalog_vs_changed_file_rejected(tmp_path: Path) -> None:
    root, catalog = _fixture_root(tmp_path)
    bundle = _bundle(root)
    for relative in ("p3", "p5", "p6", "p7"):
        (root / relative).mkdir()
    payload = {
        "schema_version": "p8-mcp-catalog-v1",
        "documents": [
            {
                "document_sha256": "1" * 64,
                "market": "CN",
                "ticker": "600000",
                "fiscal_year": 2024,
                "filing_type": "ANNUAL",
                "p3_artifact_dir": "p3",
                "p5_artifact_dir": "p5",
                "p6_artifact_dir": "p6",
                "p7_artifact_dir": "p7",
            }
        ],
    }
    (root / "catalog.json").write_text(
        json.dumps(payload, separators=(",", ":")),
        encoding="utf-8",
    )

    with pytest.raises(P10Error) as exc_info:
        build_research_context(bundle, catalog, "reviews/a")

    _assert_reason(exc_info, "P10_CATALOG_INVALID")




def test_manually_malformed_catalog_fields_map_to_p10_error(
    tmp_path: Path,
) -> None:
    root, _ = _fixture_root(tmp_path)
    bundle = _bundle(root)

    bad_root = McpCatalog(
        project_root="not-a-path",  # type: ignore[arg-type]
        catalog_path="catalog.json",  # type: ignore[arg-type]
        documents=(),
    )
    with pytest.raises(P10Error) as exc_info:
        build_research_context(bundle, bad_root, "reviews/a")
    _assert_reason(exc_info, "P10_CATALOG_INVALID")

    bad_path = McpCatalog(
        project_root=root.resolve(),
        catalog_path=123,  # type: ignore[arg-type]
        documents=(),
    )
    with pytest.raises(P10Error) as exc_info:
        build_research_context(bundle, bad_path, "reviews/a")
    _assert_reason(exc_info, "P10_CATALOG_INVALID")


def test_non_catalog_object_maps_to_p10_catalog_error(
    tmp_path: Path,
) -> None:
    root, _ = _fixture_root(tmp_path)
    bundle = _bundle(root)

    with pytest.raises(P10Error) as exc_info:
        build_research_context(
            bundle,
            object(),  # type: ignore[arg-type]
            "reviews/a",
        )
    _assert_reason(exc_info, "P10_CATALOG_INVALID")


def test_invalid_current_catalog_maps_to_p10_error(tmp_path: Path) -> None:
    root, catalog = _fixture_root(tmp_path)
    bundle = _bundle(root)
    (root / "catalog.json").write_text("{not-json", encoding="utf-8")

    with pytest.raises(P10Error) as exc_info:
        build_research_context(bundle, catalog, "reviews/a")

    _assert_reason(exc_info, "P10_CATALOG_INVALID")


def test_review_root_persisted_project_relative_posix(tmp_path: Path) -> None:
    _, _, _, context = _context(tmp_path, "reviews/../reviews/a")

    assert context.p9_review_root == "reviews/a"
    assert "\\" not in context.p9_review_root


def test_absolute_review_root_rejected(tmp_path: Path) -> None:
    root, catalog = _fixture_root(tmp_path)
    bundle = _bundle(root)

    with pytest.raises(P10Error) as exc_info:
        build_research_context(bundle, catalog, (root / "reviews/a").resolve())

    _assert_reason(exc_info, "P10_CONTEXT_PATH_OUTSIDE_PROJECT")


@pytest.mark.parametrize("review_root", ["../outside", "C:reviews"])
def test_drive_relative_and_traversal_review_root_rejected(
    tmp_path: Path,
    review_root: str,
) -> None:
    root, catalog = _fixture_root(tmp_path)
    bundle = _bundle(root)

    with pytest.raises(P10Error) as exc_info:
        build_research_context(bundle, catalog, review_root)

    _assert_reason(exc_info, "P10_CONTEXT_PATH_OUTSIDE_PROJECT")


def test_missing_review_root_rejected(tmp_path: Path) -> None:
    root, catalog = _fixture_root(tmp_path)
    bundle = _bundle(root)

    with pytest.raises(P10Error) as exc_info:
        build_research_context(bundle, catalog, "reviews/missing")

    _assert_reason(exc_info, "P10_CONTEXT_INCOMPATIBLE")


def test_review_root_file_rejected(tmp_path: Path) -> None:
    root, catalog = _fixture_root(tmp_path)
    bundle = _bundle(root)
    _write(root, "reviews/not-a-dir", b"x")

    with pytest.raises(P10Error) as exc_info:
        build_research_context(bundle, catalog, "reviews/not-a-dir")

    _assert_reason(exc_info, "P10_CONTEXT_INCOMPATIBLE")


def test_two_review_roots_produce_different_context_ids(tmp_path: Path) -> None:
    root, catalog = _fixture_root(tmp_path)
    bundle = _bundle(root)

    a = build_research_context(bundle, catalog, "reviews/a")
    b = build_research_context(bundle, catalog, "reviews/b")

    assert a.research_context_id != b.research_context_id


def test_context_id_changes_when_spec_changes(tmp_path: Path) -> None:
    root, catalog = _fixture_root(tmp_path)
    first = build_research_context(_bundle(root), catalog, "reviews/a")
    (root / "inputs/rules.md").write_bytes(b"different rules\n")
    second = build_research_context(_bundle(root), catalog, "reviews/a")

    assert first.research_context_id != second.research_context_id


def test_context_id_changes_when_catalog_bytes_change_but_semantics_match(
    tmp_path: Path,
) -> None:
    root, _ = _fixture_root(tmp_path)
    bundle = _bundle(root)
    first_catalog = McpCatalog.load(root, "catalog.json")
    first = build_research_context(bundle, first_catalog, "reviews/a")

    (root / "catalog.json").write_bytes(
        b'{ "schema_version": "p8-mcp-catalog-v1", "documents": [] }\n'
    )
    second_catalog = McpCatalog.load(root, "catalog.json")
    second = build_research_context(bundle, second_catalog, "reviews/a")

    assert first_catalog == second_catalog
    assert first.p8_catalog_sha256 != second.p8_catalog_sha256
    assert first.research_context_id != second.research_context_id


def test_context_id_changes_when_p8_fingerprint_changes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, catalog = _fixture_root(tmp_path)
    bundle = _bundle(root)
    original = build_research_context(bundle, catalog, "reviews/a")

    changed = P8ToolContract(
        server_version="p8-local-mcp-v1-test",
        catalog_schema_version="p8-mcp-catalog-v1",
        result_schema_version="p8-mcp-result-v1",
        tool_names=context_module.P8_TOOL_NAMES_V1,
    )
    monkeypatch.setattr(context_module, "_accepted_p8_contract", lambda: changed)
    modified = build_research_context(bundle, catalog, "reviews/a")

    assert original.p8_tool_contract_fingerprint != modified.p8_tool_contract_fingerprint
    assert original.research_context_id != modified.research_context_id


def test_context_id_changes_when_p9_fingerprint_changes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, catalog = _fixture_root(tmp_path)
    bundle = _bundle(root)
    original = build_research_context(bundle, catalog, "reviews/a")

    changed = P9PolicyContract(
        p9_version="p9-review-overlay-v1-test",
        policy_version="p9-review-policy-v1",
        resolution_schema_version="p9-review-resolution-v1",
        resolved_view_schema_version="p9-resolved-view-v1",
    )
    monkeypatch.setattr(context_module, "_accepted_p9_contract", lambda: changed)
    modified = build_research_context(bundle, catalog, "reviews/a")

    assert original.p9_policy_fingerprint != modified.p9_policy_fingerprint
    assert original.research_context_id != modified.research_context_id


def test_context_id_changes_when_capability_hash_changes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, catalog = _fixture_root(tmp_path)
    bundle = _bundle(root)
    original = build_research_context(bundle, catalog, "reviews/a")

    changed = tuple(
        (key, "AVAILABLE" if key == "PDF_VISUAL_EVIDENCE" else state)
        for key, state in CAPABILITY_MANIFEST_V1
    )
    monkeypatch.setattr(context_module, "CAPABILITY_MANIFEST_V1", changed)
    modified = build_research_context(bundle, catalog, "reviews/a")

    assert original.capability_manifest_hash != modified.capability_manifest_hash
    assert original.research_context_id != modified.research_context_id


def test_serialized_context_contains_no_absolute_project_path(tmp_path: Path) -> None:
    root, _, _, context = _context(tmp_path)
    serialized = json.dumps(context.to_dict(), sort_keys=True)

    assert str(root.resolve()) not in serialized
    assert context.p9_review_root == "reviews/a"


def test_main_runtime_has_no_external_mcp_sdk() -> None:
    assert importlib.util.find_spec("mcp") is None


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
