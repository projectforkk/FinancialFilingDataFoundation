from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

import financial_filing_data_foundation.research as research_package

from financial_filing_data_foundation.candidates import detect_table_candidates
from financial_filing_data_foundation.facts import extract_raw_facts
from financial_filing_data_foundation.mcp import McpCatalog, McpQueryService
from financial_filing_data_foundation.native.models import (
    P3_PARSER_VERSION,
    SCHEMA_VERSION as P3_SCHEMA_VERSION,
)
from financial_filing_data_foundation.native.search import build_search_db
from financial_filing_data_foundation.research import (
    LEDGER_SCHEMA_VERSION,
    PROVENANCE_VALIDATION_SCHEMA_VERSION,
    P8_RAW_DIRECT,
    P9_DURABLE_RESOLVED,
    RUN_LOCAL_STRUCTURED_VERIFIED,
    UNRESOLVED,
    EvidenceLedger,
    EvidenceLedgerEntry,
    P10Error,
    ResearchSpecInput,
    build_research_context,
    freeze_research_spec,
    validate_evidence_ledger,
)
from financial_filing_data_foundation.review import (
    ResolutionSubmission,
    load_resolved_snapshot,
    materialize_resolved_view,
    prepare_review_overlay,
    submit_resolution,
)
from financial_filing_data_foundation.review.queue import load_review_base
from financial_filing_data_foundation.tables import reconstruct_tables
from financial_filing_data_foundation.validation import validate_document_artifacts


DOC_SHA = "e" * 64


def _word(
    text: str,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    line_no: int,
    word_no: int,
) -> dict:
    return {
        "text": text,
        "bbox": [x0, y0, x1, y1],
        "block_no": 0,
        "line_no": line_no,
        "word_no": word_no,
    }


def _page() -> dict:
    raw_rows = [("项目", "COL_A", "COL_B")] + [
        (f"项目{i:02d}", str(1000 + i), str(900 + i))
        for i in range(30)
    ]
    words: list[dict] = []
    lines: list[dict] = []
    for row_no, values in enumerate(raw_rows):
        y0 = 60 + row_no * 20
        row_words: list[dict] = []
        for word_no, (text, x0, x1) in enumerate(
            zip(values, (50.0, 300.0, 400.0), (220.0, 340.0, 440.0))
        ):
            word = _word(text, x0, y0, x1, y0 + 10, row_no, word_no)
            words.append(word)
            row_words.append(word)
        lines.append(
            {
                "line_no": row_no,
                "bbox": [50, y0, 440, y0 + 10],
                "text": " ".join(word["text"] for word in row_words),
                "spans": [],
                "repeated_header_footer": False,
            }
        )
    text = "\n".join(line["text"] for line in lines)
    return {
        "page_no": 1,
        "width": 595.0,
        "height": 842.0,
        "rotation": 0,
        "native_text_available": True,
        "native_char_count": len(text),
        "word_count": len(words),
        "block_count": 1,
        "line_count": len(lines),
        "span_count": 0,
        "image_count": 0,
        "drawing_count": 80,
        "text": text,
        "words": words,
        "blocks": [
            {
                "block_no": 0,
                "bbox": [50, 60, 440, 60 + (len(lines) - 1) * 20 + 10],
                "type": "text",
                "text": text,
                "lines": lines,
                "reading_order_index": 0,
            }
        ],
        "warnings": [],
    }


def _write_native(root: Path) -> Path:
    page = _page()
    sections = [
        {
            "section_id": "section-1",
            "raw_title": "财务报表",
            "normalized_title": None,
            "level": 1,
            "page_start": 1,
            "page_end": 1,
            "parent_section_id": None,
            "bbox": [50, 40, 180, 52],
            "heading_score": 5.0,
            "heading_signals": ["TEST"],
            "quality_signals": [],
        }
    ]
    artifact = root / "p3" / DOC_SHA
    artifact.mkdir(parents=True)
    (artifact / "pages.jsonl").write_text(
        json.dumps(page, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (artifact / "sections.jsonl").write_text(
        json.dumps(sections[0], ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (artifact / "document.json").write_text(
        json.dumps(
            {
                "schema_version": P3_SCHEMA_VERSION,
                "document_sha256": DOC_SHA,
                "file_size": 123,
                "page_count": 1,
                "parser_version": P3_PARSER_VERSION,
                "timings_ms": {},
                "warnings": [],
            }
        ),
        encoding="utf-8",
    )
    build_search_db(
        artifact / "search.sqlite",
        DOC_SHA,
        [page],
        sections,
    )
    return artifact


def _relative(root: Path, value: Path) -> str:
    return value.resolve().relative_to(root.resolve()).as_posix()


def _build_artifacts(root: Path) -> tuple[Path, dict[str, Path]]:
    p3 = _write_native(root)
    p4 = detect_table_candidates(p3, root / "p4").artifact_dir
    p5 = reconstruct_tables(p3, p4, root / "p5").artifact_dir
    p6 = extract_raw_facts(p3, p5, root / "p6").artifact_dir
    p7 = validate_document_artifacts(p3, p5, p6, root / "p7").artifact_dir

    catalog_path = root / "catalog.json"
    catalog_path.write_text(
        json.dumps(
            {
                "schema_version": "p8-mcp-catalog-v1",
                "documents": [
                    {
                        "document_sha256": DOC_SHA,
                        "market": "CN",
                        "ticker": "SYNTH",
                        "fiscal_year": 2024,
                        "filing_type": "ANNUAL",
                        "p3_artifact_dir": _relative(root, p3),
                        "p5_artifact_dir": _relative(root, p5),
                        "p6_artifact_dir": _relative(root, p6),
                        "p7_artifact_dir": _relative(root, p7),
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return catalog_path, {"p3": p3, "p4": p4, "p5": p5, "p6": p6, "p7": p7}


@pytest.fixture()
def provenance_fixture(tmp_path: Path):
    root = tmp_path
    catalog_path, artifacts = _build_artifacts(root)
    (root / "inputs").mkdir()
    (root / "inputs" / "rules.md").write_bytes(b"rules\n")
    (root / "review").mkdir()

    catalog = McpCatalog.load(root, catalog_path)
    spec_bundle = freeze_research_spec(
        root,
        [ResearchSpecInput("rules", "inputs/rules.md")],
    )
    context = build_research_context(spec_bundle, catalog, "review")
    service = McpQueryService(catalog)

    table_summary = service.list_tables(DOC_SHA, page_no=1, limit=10)["data"]["tables"][0]
    table_id = str(table_summary["table_id"])
    fact_summary = service.list_raw_facts(DOC_SHA, limit=10)["data"]["facts"][0]
    fact_id = str(fact_summary["raw_fact_id"])
    evidence_id = str(fact_summary["evidence_id"])

    return {
        "root": root,
        "catalog_path": catalog_path,
        "catalog": catalog,
        "context": context,
        "spec_bundle": spec_bundle,
        "service": service,
        "artifacts": artifacts,
        "table_id": table_id,
        "fact_id": fact_id,
        "evidence_id": evidence_id,
    }


def _ledger(context, spec_bundle, *entries: EvidenceLedgerEntry) -> EvidenceLedger:
    return EvidenceLedger(
        schema_version=LEDGER_SCHEMA_VERSION,
        research_context_id=context.research_context_id,
        spec_bundle_hash=spec_bundle.spec_bundle_hash,
        entries=tuple(entries),
    )


def _raw_entry(fx, *, claim_key: str = "raw", **changes) -> EvidenceLedgerEntry:
    values = {
        "claim_key": claim_key,
        "use_class": P8_RAW_DIRECT,
        "document_sha256": DOC_SHA,
        "page_nos": (1,),
        "table_ids": (fx["table_id"],),
        "raw_fact_ids": (fx["fact_id"],),
        "evidence_ids": (fx["evidence_id"],),
        "p9_resolution_ids": (),
        "overlay_set_hash": None,
        "semantic_assertions": {},
        "derived_from_claim_keys": (),
    }
    values.update(changes)
    return EvidenceLedgerEntry(**values)


def _run_local_source(fx, *, claim_key: str = "verified") -> EvidenceLedgerEntry:
    return EvidenceLedgerEntry(
        claim_key=claim_key,
        use_class=RUN_LOCAL_STRUCTURED_VERIFIED,
        document_sha256=DOC_SHA,
        page_nos=(1,),
        table_ids=(fx["table_id"],),
        raw_fact_ids=(fx["fact_id"],),
        evidence_ids=(fx["evidence_id"],),
        semantic_assertions={"period": "current"},
    )


def _derived(*operands: str, claim_key: str = "derived") -> EvidenceLedgerEntry:
    return EvidenceLedgerEntry(
        claim_key=claim_key,
        use_class=RUN_LOCAL_STRUCTURED_VERIFIED,
        document_sha256=None,
        semantic_assertions={"operation": "derived"},
        derived_from_claim_keys=tuple(operands),
    )


def _assert_reason(exc_info: pytest.ExceptionInfo[P10Error], reason: str) -> None:
    assert exc_info.value.reason_code == reason


def _validate(fx, ledger: EvidenceLedger):
    return validate_evidence_ledger(
        fx["context"],
        ledger,
        fx["spec_bundle"],
        fx["catalog"],
    )


def _p9_submission(task, table: dict, cell: dict, *, value: str, reviewed_at: str, supersedes: str | None = None):
    return ResolutionSubmission.from_dict(
        {
            "review_task_id": task.review_task_id,
            "action": "SET_PERIOD",
            "target": {
                "target_type": "TABLE_COLUMN_FIELD",
                "table_id": table["table_id"],
                "column_index": 1,
                "field": "period",
            },
            "value": value,
            "evidence_refs": [
                {
                    "type": "P5_CELL",
                    "table_id": table["table_id"],
                    "cell_id": cell["cell_id"],
                }
            ],
            "reviewer_type": "HUMAN",
            "reviewer_id": "p10-e-test",
            "reviewed_at": reviewed_at,
            "justification": "P10-E deterministic provenance fixture.",
            "supersedes_resolution_id": supersedes,
        }
    )


def _create_p9_snapshot(fx):
    overlay = prepare_review_overlay(
        fx["root"],
        fx["catalog_path"],
        DOC_SHA,
        fx["root"] / "review",
    )
    _, bundle, tasks = load_review_base(overlay.review_dir)
    task = next(item for item in tasks if item.reason_code == "RAW_PERIOD_COVERAGE_LOW")
    table = bundle.context.tables[0]
    cell = next(
        cell
        for row in table["rows"]
        for cell in row["cells"]
        if int(cell["column_index"]) == 1
    )
    resolution = submit_resolution(
        overlay.review_dir,
        _p9_submission(
            task,
            table,
            cell,
            value="PERIOD_A",
            reviewed_at="2026-11-04T10:00:00+09:00",
        ),
    )
    snapshot = materialize_resolved_view(overlay.review_dir)
    loaded = load_resolved_snapshot(snapshot.snapshot_dir, overlay.review_dir)
    assert resolution.resolution_id in loaded.report["active_resolution_ids"]
    return overlay, bundle, task, table, cell, resolution, snapshot


def _durable_entry(resolution, snapshot, *, claim_key: str = "durable") -> EvidenceLedgerEntry:
    return EvidenceLedgerEntry(
        claim_key=claim_key,
        use_class=P9_DURABLE_RESOLVED,
        document_sha256=DOC_SHA,
        p9_resolution_ids=(resolution.resolution_id,),
        overlay_set_hash=snapshot.overlay_set_hash,
    )


def test_empty_ledger_passes(provenance_fixture) -> None:
    fx = provenance_fixture
    result = _validate(fx, _ledger(fx["context"], fx["spec_bundle"]))

    assert result.to_dict() == {
        "schema_version": PROVENANCE_VALIDATION_SCHEMA_VERSION,
        "status": "PASS",
        "research_context_id": fx["context"].research_context_id,
        "spec_bundle_hash": fx["spec_bundle"].spec_bundle_hash,
        "entry_count": 0,
        "validated_claim_keys": [],
    }


def test_raw_direct_full_relation_passes(provenance_fixture) -> None:
    fx = provenance_fixture
    result = _validate(
        fx,
        _ledger(fx["context"], fx["spec_bundle"], _raw_entry(fx)),
    )
    assert result.validated_claim_keys == ("raw",)


@pytest.mark.parametrize(
    "field,value",
    [
        ("document_sha256", "A" * 64),
        ("overlay_set_hash", "A" * 64),
    ],
)
def test_noncanonical_sha_rejected(provenance_fixture, field: str, value: str) -> None:
    fx = provenance_fixture
    kwargs = {field: value}
    entry = _raw_entry(fx, **kwargs)
    with pytest.raises(P10Error) as exc_info:
        _validate(fx, _ledger(fx["context"], fx["spec_bundle"], entry))
    _assert_reason(exc_info, "P10_PROVENANCE_INVALID")


def test_duplicate_claim_key_rejected(provenance_fixture) -> None:
    fx = provenance_fixture
    ledger = _ledger(
        fx["context"],
        fx["spec_bundle"],
        _raw_entry(fx, claim_key="same"),
        _raw_entry(fx, claim_key="same"),
    )
    with pytest.raises(P10Error) as exc_info:
        _validate(fx, ledger)
    _assert_reason(exc_info, "P10_PROVENANCE_INVALID")


@pytest.mark.parametrize(
    "entry",
    [
        EvidenceLedgerEntry(
            claim_key="external",
            use_class="EXTERNAL_RUNTIME_SOURCE",
        ),
        EvidenceLedgerEntry(
            claim_key="raw-assert",
            use_class=P8_RAW_DIRECT,
            document_sha256=DOC_SHA,
            page_nos=(1,),
            semantic_assertions={"x": 1},
        ),
        EvidenceLedgerEntry(
            claim_key="source-no-assert",
            use_class=RUN_LOCAL_STRUCTURED_VERIFIED,
            document_sha256=DOC_SHA,
            page_nos=(1,),
        ),
        EvidenceLedgerEntry(
            claim_key="durable-no-overlay",
            use_class=P9_DURABLE_RESOLVED,
            document_sha256=DOC_SHA,
            p9_resolution_ids=("resolution",),
        ),
    ],
)
def test_use_class_shape_rejections(provenance_fixture, entry) -> None:
    fx = provenance_fixture
    with pytest.raises(P10Error) as exc_info:
        _validate(fx, _ledger(fx["context"], fx["spec_bundle"], entry))
    _assert_reason(exc_info, "P10_PROVENANCE_INVALID")


def test_source_backed_run_local_passes(provenance_fixture) -> None:
    fx = provenance_fixture
    result = _validate(
        fx,
        _ledger(fx["context"], fx["spec_bundle"], _run_local_source(fx)),
    )
    assert result.validated_claim_keys == ("verified",)


def test_valid_unresolved_entry_passes(provenance_fixture) -> None:
    fx = provenance_fixture
    unresolved = EvidenceLedgerEntry(
        claim_key="unknown",
        use_class=UNRESOLVED,
        document_sha256=DOC_SHA,
        page_nos=(1,),
    )
    result = _validate(
        fx,
        _ledger(fx["context"], fx["spec_bundle"], unresolved),
    )
    assert result.validated_claim_keys == ("unknown",)


@pytest.mark.parametrize(
    "mutator",
    [
        lambda fx: _raw_entry(fx, page_nos=(2,)),
        lambda fx: _raw_entry(fx, table_ids=("missing-table",), raw_fact_ids=(), evidence_ids=()),
        lambda fx: _raw_entry(fx, raw_fact_ids=("missing-fact",), table_ids=(), evidence_ids=()),
        lambda fx: _raw_entry(fx, evidence_ids=("missing-evidence",), table_ids=(), raw_fact_ids=()),
    ],
)
def test_missing_or_invalid_p8_refs_rejected(provenance_fixture, mutator) -> None:
    fx = provenance_fixture
    with pytest.raises(P10Error) as exc_info:
        _validate(
            fx,
            _ledger(fx["context"], fx["spec_bundle"], mutator(fx)),
        )
    _assert_reason(exc_info, "P10_PROVENANCE_INVALID")


def test_fact_evidence_relation_mismatch_rejected(provenance_fixture) -> None:
    fx = provenance_fixture
    entry = _raw_entry(fx, evidence_ids=("missing-evidence",))
    with pytest.raises(P10Error) as exc_info:
        _validate(fx, _ledger(fx["context"], fx["spec_bundle"], entry))
    _assert_reason(exc_info, "P10_PROVENANCE_INVALID")


def test_table_scope_mismatch_rejected(provenance_fixture) -> None:
    fx = provenance_fixture
    entry = _raw_entry(fx, table_ids=("wrong-table",))
    with pytest.raises(P10Error) as exc_info:
        _validate(fx, _ledger(fx["context"], fx["spec_bundle"], entry))
    _assert_reason(exc_info, "P10_PROVENANCE_INVALID")


def test_valid_derived_graph_is_order_independent(provenance_fixture) -> None:
    fx = provenance_fixture
    source = _run_local_source(fx, claim_key="source")
    derived = _derived("source", claim_key="calc")

    first = _validate(
        fx,
        _ledger(fx["context"], fx["spec_bundle"], source, derived),
    )
    second = _validate(
        fx,
        _ledger(fx["context"], fx["spec_bundle"], derived, source),
    )

    assert first.to_dict() == second.to_dict()
    assert first.validated_claim_keys == ("calc", "source")


@pytest.mark.parametrize(
    "entries",
    [
        (
            _derived("missing", claim_key="calc"),
        ),
        (
            _derived("calc", claim_key="calc"),
        ),
        (
            _derived("b", claim_key="a"),
            _derived("a", claim_key="b"),
        ),
    ],
)
def test_invalid_derived_graph_rejected(provenance_fixture, entries) -> None:
    fx = provenance_fixture
    with pytest.raises(P10Error) as exc_info:
        _validate(fx, _ledger(fx["context"], fx["spec_bundle"], *entries))
    _assert_reason(exc_info, "P10_PROVENANCE_INVALID")


def test_raw_and_unresolved_cannot_be_derived_operands(provenance_fixture) -> None:
    fx = provenance_fixture
    raw = _raw_entry(fx, claim_key="raw")
    unresolved = EvidenceLedgerEntry(claim_key="unknown", use_class=UNRESOLVED)

    for operand in (raw, unresolved):
        with pytest.raises(P10Error) as exc_info:
            _validate(
                fx,
                _ledger(
                    fx["context"],
                    fx["spec_bundle"],
                    operand,
                    _derived(operand.claim_key),
                ),
            )
        _assert_reason(exc_info, "P10_PROVENANCE_INVALID")


def test_spec_drift_precedes_later_provenance_error(provenance_fixture) -> None:
    fx = provenance_fixture
    (fx["root"] / "inputs" / "rules.md").write_bytes(b"changed\n")
    bad_ledger = EvidenceLedger(
        schema_version="bad-ledger",
        research_context_id=fx["context"].research_context_id,
        spec_bundle_hash=fx["spec_bundle"].spec_bundle_hash,
        entries=(),
    )

    with pytest.raises(P10Error) as exc_info:
        _validate(fx, bad_ledger)
    _assert_reason(exc_info, "P10_RESEARCH_SPEC_CHANGED")


def test_ledger_context_or_spec_mismatch_rejected(provenance_fixture) -> None:
    fx = provenance_fixture
    for ledger in (
        EvidenceLedger(
            schema_version=LEDGER_SCHEMA_VERSION,
            research_context_id="0" * 64,
            spec_bundle_hash=fx["spec_bundle"].spec_bundle_hash,
            entries=(),
        ),
        EvidenceLedger(
            schema_version=LEDGER_SCHEMA_VERSION,
            research_context_id=fx["context"].research_context_id,
            spec_bundle_hash="0" * 64,
            entries=(),
        ),
    ):
        with pytest.raises(P10Error) as exc_info:
            _validate(fx, ledger)
        _assert_reason(exc_info, "P10_PROVENANCE_INVALID")


def test_current_catalog_context_mismatch_rejected(provenance_fixture) -> None:
    fx = provenance_fixture
    raw = fx["catalog_path"].read_text(encoding="utf-8")
    fx["catalog_path"].write_text(raw + " ", encoding="utf-8")
    current = McpCatalog.load(fx["root"], fx["catalog_path"])

    with pytest.raises(P10Error) as exc_info:
        validate_evidence_ledger(
            fx["context"],
            _ledger(fx["context"], fx["spec_bundle"]),
            fx["spec_bundle"],
            current,
        )
    _assert_reason(exc_info, "P10_CONTEXT_INCOMPATIBLE")


def test_corrupt_p8_artifact_maps_to_upstream_invalid(provenance_fixture) -> None:
    fx = provenance_fixture
    facts_path = fx["artifacts"]["p6"] / "raw_facts.jsonl"
    facts_path.write_text("{not-json\n", encoding="utf-8")

    with pytest.raises(P10Error) as exc_info:
        _validate(
            fx,
            _ledger(fx["context"], fx["spec_bundle"], _raw_entry(fx)),
        )
    _assert_reason(exc_info, "P10_UPSTREAM_INVALID")


def test_valid_p9_durable_snapshot_passes(provenance_fixture) -> None:
    fx = provenance_fixture
    _, _, _, _, _, resolution, snapshot = _create_p9_snapshot(fx)
    result = _validate(
        fx,
        _ledger(
            fx["context"],
            fx["spec_bundle"],
            _durable_entry(resolution, snapshot),
        ),
    )
    assert result.validated_claim_keys == ("durable",)


def test_p9_resolution_not_in_claimed_snapshot_rejected(provenance_fixture) -> None:
    fx = provenance_fixture
    _, _, _, _, _, resolution, snapshot = _create_p9_snapshot(fx)
    entry = EvidenceLedgerEntry(
        claim_key="durable",
        use_class=P9_DURABLE_RESOLVED,
        document_sha256=DOC_SHA,
        p9_resolution_ids=("f" * 64,),
        overlay_set_hash=snapshot.overlay_set_hash,
    )
    with pytest.raises(P10Error) as exc_info:
        _validate(fx, _ledger(fx["context"], fx["spec_bundle"], entry))
    _assert_reason(exc_info, "P10_PROVENANCE_INVALID")


def test_missing_claimed_p9_snapshot_rejected(provenance_fixture) -> None:
    fx = provenance_fixture
    entry = EvidenceLedgerEntry(
        claim_key="durable",
        use_class=P9_DURABLE_RESOLVED,
        document_sha256=DOC_SHA,
        p9_resolution_ids=("f" * 64,),
        overlay_set_hash="1" * 64,
    )
    with pytest.raises(P10Error) as exc_info:
        _validate(fx, _ledger(fx["context"], fx["spec_bundle"], entry))
    _assert_reason(exc_info, "P10_PROVENANCE_INVALID")


def test_corrupt_p9_snapshot_maps_to_upstream_invalid(provenance_fixture) -> None:
    fx = provenance_fixture
    overlay, _, _, _, _, resolution, snapshot = _create_p9_snapshot(fx)
    report_path = snapshot.snapshot_dir / "resolution_report.json"
    report_path.write_text("{not-json", encoding="utf-8")

    with pytest.raises(P10Error) as exc_info:
        _validate(
            fx,
            _ledger(
                fx["context"],
                fx["spec_bundle"],
                _durable_entry(resolution, snapshot),
            ),
        )
    _assert_reason(exc_info, "P10_UPSTREAM_INVALID")


def test_historical_p9_snapshot_remains_valid_after_supersession(
    provenance_fixture,
) -> None:
    fx = provenance_fixture
    overlay, _, task, table, cell, first, first_snapshot = _create_p9_snapshot(fx)

    second = submit_resolution(
        overlay.review_dir,
        _p9_submission(
            task,
            table,
            cell,
            value="PERIOD_B",
            reviewed_at="2026-11-04T10:01:00+09:00",
            supersedes=first.resolution_id,
        ),
    )
    second_snapshot = materialize_resolved_view(overlay.review_dir)
    assert second.resolution_id != first.resolution_id
    assert second_snapshot.overlay_set_hash != first_snapshot.overlay_set_hash

    result = _validate(
        fx,
        _ledger(
            fx["context"],
            fx["spec_bundle"],
            _durable_entry(first, first_snapshot, claim_key="historical"),
        ),
    )
    assert result.validated_claim_keys == ("historical",)


def test_p9_durable_can_be_derived_operand(provenance_fixture) -> None:
    fx = provenance_fixture
    _, _, _, _, _, resolution, snapshot = _create_p9_snapshot(fx)
    durable = _durable_entry(resolution, snapshot, claim_key="durable")
    derived = _derived("durable", claim_key="calc")

    result = _validate(
        fx,
        _ledger(fx["context"], fx["spec_bundle"], durable, derived),
    )
    assert result.validated_claim_keys == ("calc", "durable")


def test_validation_serialization_has_no_absolute_path_or_runtime_noise(
    provenance_fixture,
) -> None:
    fx = provenance_fixture
    result = _validate(fx, _ledger(fx["context"], fx["spec_bundle"]))
    serialized = json.dumps(result.to_dict(), sort_keys=True)

    assert str(fx["root"].resolve()) not in serialized
    assert "time" not in serialized.lower()
    assert "uuid" not in serialized.lower()
    assert "reasoning" not in serialized.lower()


def test_models_round_trip_canonical_entry_order(provenance_fixture) -> None:
    fx = provenance_fixture
    source = _run_local_source(fx, claim_key="b")
    other = _run_local_source(fx, claim_key="a")
    ledger = _ledger(fx["context"], fx["spec_bundle"], source, other)

    restored = EvidenceLedger.from_dict(ledger.to_dict())
    assert [item["claim_key"] for item in restored.to_dict()["entries"]] == ["a", "b"]


def test_bad_top_level_schema_rejected(provenance_fixture) -> None:
    fx = provenance_fixture
    ledger = EvidenceLedger(
        schema_version="bad-ledger-schema",
        research_context_id=fx["context"].research_context_id,
        spec_bundle_hash=fx["spec_bundle"].spec_bundle_hash,
        entries=(),
    )
    with pytest.raises(P10Error) as exc_info:
        _validate(fx, ledger)
    _assert_reason(exc_info, "P10_PROVENANCE_INVALID")


def test_canonical_missing_document_rejected(provenance_fixture) -> None:
    fx = provenance_fixture
    entry = EvidenceLedgerEntry(
        claim_key="missing-doc",
        use_class=P8_RAW_DIRECT,
        document_sha256="f" * 64,
        page_nos=(1,),
    )
    with pytest.raises(P10Error) as exc_info:
        _validate(fx, _ledger(fx["context"], fx["spec_bundle"], entry))
    _assert_reason(exc_info, "P10_PROVENANCE_INVALID")


def test_valid_page_number_but_fact_page_relation_mismatch_rejected(
    provenance_fixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fx = provenance_fixture

    monkeypatch.setattr(
        McpQueryService,
        "get_document",
        lambda self, sha: {
            "schema_version": "p8-mcp-result-v1",
            "tool": "ffdf_get_document",
            "document_sha256": sha,
            "data": {"document_sha256": sha, "page_count": 2},
        },
    )
    monkeypatch.setattr(
        McpQueryService,
        "get_fact",
        lambda self, sha, fact_id: {
            "schema_version": "p8-mcp-result-v1",
            "tool": "ffdf_get_fact",
            "document_sha256": sha,
            "data": {
                "document_sha256": sha,
                "raw_fact_id": fact_id,
                "page_no": 1,
                "table_id": fx["table_id"],
                "evidence_id": fx["evidence_id"],
            },
        },
    )
    entry = EvidenceLedgerEntry(
        claim_key="page-mismatch",
        use_class=P8_RAW_DIRECT,
        document_sha256=DOC_SHA,
        page_nos=(2,),
        raw_fact_ids=(fx["fact_id"],),
    )
    with pytest.raises(P10Error) as exc_info:
        _validate(fx, _ledger(fx["context"], fx["spec_bundle"], entry))
    _assert_reason(exc_info, "P10_PROVENANCE_INVALID")


def test_existing_declared_table_but_fact_table_relation_mismatch_rejected(
    provenance_fixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fx = provenance_fixture
    declared_table = "declared-table"

    monkeypatch.setattr(
        McpQueryService,
        "get_document",
        lambda self, sha: {
            "schema_version": "p8-mcp-result-v1",
            "tool": "ffdf_get_document",
            "document_sha256": sha,
            "data": {"document_sha256": sha, "page_count": 1},
        },
    )
    monkeypatch.setattr(
        McpQueryService,
        "get_table",
        lambda self, sha, table_id, max_rows=100: {
            "schema_version": "p8-mcp-result-v1",
            "tool": "ffdf_get_table",
            "document_sha256": sha,
            "data": {
                "document_sha256": sha,
                "table_id": table_id,
                "page_no": 1,
            },
        },
    )
    monkeypatch.setattr(
        McpQueryService,
        "get_fact",
        lambda self, sha, fact_id: {
            "schema_version": "p8-mcp-result-v1",
            "tool": "ffdf_get_fact",
            "document_sha256": sha,
            "data": {
                "document_sha256": sha,
                "raw_fact_id": fact_id,
                "page_no": 1,
                "table_id": "actual-table",
                "evidence_id": fx["evidence_id"],
            },
        },
    )
    entry = EvidenceLedgerEntry(
        claim_key="table-mismatch",
        use_class=P8_RAW_DIRECT,
        document_sha256=DOC_SHA,
        table_ids=(declared_table,),
        raw_fact_ids=(fx["fact_id"],),
    )
    with pytest.raises(P10Error) as exc_info:
        _validate(fx, _ledger(fx["context"], fx["spec_bundle"], entry))
    _assert_reason(exc_info, "P10_PROVENANCE_INVALID")


def test_exact_candidate_source_binding_and_no_external_mcp_sdk() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    expected = (
        repository_root
        / "src"
        / "financial_filing_data_foundation"
        / "research"
        / "__init__.py"
    ).resolve()

    assert Path(research_package.__file__).resolve() == expected
    assert importlib.util.find_spec("mcp") is None


@pytest.mark.parametrize(
    "direct_kwargs",
    [
        {"page_nos": (1,)},
        {"table_ids": ("TABLE",)},
        {"raw_fact_ids": ("FACT",)},
        {"evidence_ids": ("EVIDENCE",)},
    ],
)
def test_single_kind_direct_p8_provenance_passes(
    provenance_fixture,
    direct_kwargs: dict,
) -> None:
    fx = provenance_fixture
    resolved = dict(direct_kwargs)
    if "table_ids" in resolved:
        resolved["table_ids"] = (fx["table_id"],)
    if "raw_fact_ids" in resolved:
        resolved["raw_fact_ids"] = (fx["fact_id"],)
    if "evidence_ids" in resolved:
        resolved["evidence_ids"] = (fx["evidence_id"],)
    entry = EvidenceLedgerEntry(
        claim_key="direct",
        use_class=P8_RAW_DIRECT,
        document_sha256=DOC_SHA,
        **resolved,
    )
    result = _validate(
        fx,
        _ledger(fx["context"], fx["spec_bundle"], entry),
    )
    assert result.validated_claim_keys == ("direct",)


def test_nonfinite_semantic_assertion_rejected(provenance_fixture) -> None:
    fx = provenance_fixture
    entry = EvidenceLedgerEntry(
        claim_key="bad-json",
        use_class=RUN_LOCAL_STRUCTURED_VERIFIED,
        document_sha256=DOC_SHA,
        page_nos=(1,),
        semantic_assertions={"value": float("nan")},
    )
    with pytest.raises(P10Error) as exc_info:
        _validate(fx, _ledger(fx["context"], fx["spec_bundle"], entry))
    _assert_reason(exc_info, "P10_PROVENANCE_INVALID")
